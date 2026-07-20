"""Optional MCP server exposing peekdocs read-only document search.

This is a thin adapter over :mod:`peekdocs.api` — the same engine the CLI
and GUI call — that speaks the Model Context Protocol (MCP) so any
MCP-capable AI assistant can search a user's local documents. It is
deliberately **read-only**: it never creates, moves, renames, or deletes
files, never writes reports, and never shells out except through the
already-sandboxed OCR path. Report-writing and file-mutation surfaces
(``reporter``, collection writers) are simply never imported here.

Run it over stdio — the transport every MCP client speaks::

    peekdocs-mcp --root ~/Documents

The ``mcp`` package is an optional dependency (``pip install peekdocs[mcp]``).
The tool *logic* in this module imports without it; only :func:`build_server`
requires it, so the guardrail helpers stay importable and testable on a base
install.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from peekdocs import api
from peekdocs.paths import format_bytes


# ── Server configuration + guardrails ──────────────────────────────

@dataclass
class _Config:
    """Server-level policy set once at startup by :func:`main`."""

    roots: list[str] = field(default_factory=list)  # canonical allowed roots; empty = unrestricted
    max_results: int = 200                           # cap on matches/files per response
    recursive_default: bool = False                  # default for tools' `recursive` when unset
    ocr_default: bool = False                        # default for tools' `use_ocr` when unset
    allow_index_default: bool = False                # default for `allow_index_write` when unset


_CONFIG = _Config()


class PathNotAllowedError(ValueError):
    """Raised when a requested path falls outside the ``--root`` allowlist."""


def _resolve_within_roots(path: str) -> str:
    """Canonicalize ``path`` and confirm it is inside an allowed root.

    Blocks ``..`` traversal and symlink escapes by resolving the real path
    first. When no roots are configured the server is unrestricted and the
    canonical path is returned unchecked.
    """
    real = os.path.realpath(os.path.expanduser(path))
    if not _CONFIG.roots:
        return real
    for root in _CONFIG.roots:
        if real == root or real.startswith(root + os.sep):
            return real
    raise PathNotAllowedError(
        f"Path {real!r} is outside the allowed root(s): {', '.join(_CONFIG.roots)}"
    )


def _resolve_dir(directory: Optional[str]) -> str:
    """Resolve a tool's ``directory`` argument, defaulting sensibly.

    Defaults to the first configured root, or the current working directory
    when the server is unrestricted.
    """
    if directory is None:
        directory = _CONFIG.roots[0] if _CONFIG.roots else os.getcwd()
    return _resolve_within_roots(directory)


def _cap(items: list, *, detail_hint: bool = False) -> tuple[list, dict[str, Any]]:
    """Truncate ``items`` to ``max_results`` and describe what was dropped.

    On truncation the envelope carries a plain-language ``note`` alongside the
    machine fields, stating the real reason (the ``max_results`` cap). Assistants
    reliably relay a ready-made sentence but tend to invent a cause when handed
    only the numbers — the note keeps their narration honest.

    ``detail_hint`` adds a pointer to the ``detail=locations`` output mode — set
    it only for tools that actually accept ``detail`` (currently
    ``search_documents``), so the note never suggests a parameter the calling
    tool doesn't support.
    """
    total = len(items)
    cap = _CONFIG.max_results
    if total > cap:
        note = (
            f"Showing {cap} of {total} results — capped by max_results "
            f"({cap}). To see more, ask to narrow the request (e.g. a more "
            "specific term or folder) or raise the max_results limit."
        )
        if detail_hint:
            note += (
                " Or, if you only need to know which files match, re-run with "
                "detail=locations to fit many more."
            )
        return items[:cap], {
            "truncated": True,
            "total": total,
            "returned": cap,
            "note": note,
        }
    return items, {"truncated": False, "total": total, "returned": total}


#: Valid values for the ``detail`` output mode.
_DETAIL_MODES = ("full", "locations")


def _match_dicts(matches, detail: str = "full") -> list[dict[str, Any]]:
    """Serialize matches to dicts at the requested ``detail`` level.

    ``full`` (default) includes each match's text; ``locations`` returns only
    ``file`` + ``line`` (no text), which is far more token-efficient — useful
    when a small local model's context window can't hold many full matches, or
    for a broad "which files mention X?" pass before drilling in with
    :func:`get_document_context`. Unknown values fall back to ``full``.
    """
    if detail not in _DETAIL_MODES:
        detail = "full"
    out: list[dict[str, Any]] = []
    for m in matches:
        d: dict[str, Any] = {
            "file": os.path.join(m.file_dir, m.filename),
            "line": m.line_num,
        }
        if detail == "full":
            d["text"] = m.text
        out.append(d)
    return out


# ── Tool implementations (plain functions — no MCP dependency) ──────

def search_documents(
    query: list[str],
    directory: Optional[str] = None,
    match_all: bool = False,
    recursive: Optional[bool] = None,
    use_regex: bool = False,
    use_fuzzy: bool = False,
    use_whole_word: bool = False,
    file_types: Optional[list[str]] = None,
    exclude_terms: Optional[list[str]] = None,
    context_before: int = 0,
    context_after: int = 0,
    expression: Optional[str] = None,
    range_filters: Optional[list[str]] = None,
    use_ocr: Optional[bool] = None,
    allow_index_write: Optional[bool] = None,
    detail: str = "full",
) -> dict[str, Any]:
    """Search local documents for text and return matching lines.

    Call this when the user wants to find a word, phrase, or pattern across
    their local files (Word, PDF, Excel, code, and 100+ other formats).
    Returns each matching line with its file and line number. The response's
    ``searched_directory`` field reports the exact folder that was searched
    (the server's ``--root`` unless you pass ``directory``); describe the
    search scope from that value, not from any assumed or working directory.
    If ``truncated`` is true, relay the ``note`` verbatim — it gives the real
    reason (the ``max_results`` cap) — rather than guessing why results were cut.

    query: one or more search terms (OR by default; set match_all for AND).
    directory: folder to search (defaults to the server's root).
    recursive: include subfolders. use_regex/use_fuzzy/use_whole_word: match modes.
    file_types: limit to extensions like [".pdf", ".docx"]. exclude_terms: drop
    lines containing these. context_before/after: extra surrounding lines.
    expression: a boolean query like "(alice AND bob) OR carol". use_ocr: read
    scanned PDFs and images (requires Tesseract). allow_index_write: opt in to
    using/refreshing the on-disk search index (writes .peekdocs.db); off by
    default to keep the search purely read-only.
    detail: how much to return per match. "full" (default) includes each
    match's text. "locations" returns only file + line, no text — far more
    token-efficient; use it for a broad "which files mention X?" pass, or when
    results are being truncated and you want to fit more, then call
    get_document_context on the files you care about to read their text. Only
    request "locations" when the user's question doesn't need the matched text
    itself; if you use it, say so — you have not seen the surrounding wording.
    """
    recursive = _CONFIG.recursive_default if recursive is None else recursive
    use_ocr = _CONFIG.ocr_default if use_ocr is None else use_ocr
    allow_index_write = (
        _CONFIG.allow_index_default if allow_index_write is None else allow_index_write
    )
    d = _resolve_dir(directory)
    result = api.search(
        query,
        directory=d,
        match_all=match_all,
        recursive=recursive,
        use_regex=use_regex,
        use_fuzzy=use_fuzzy,
        use_whole_word=use_whole_word,
        file_types=file_types,
        exclude_terms=exclude_terms,
        context_before=context_before,
        context_after=context_after,
        expression=expression,
        range_filters=range_filters,
        use_ocr=use_ocr,
        use_index=None if allow_index_write else False,
    )
    matches, envelope = _cap(_match_dicts(result.matches, detail), detail_hint=True)
    return {
        "searched_directory": d,
        "matches": matches,
        "files_searched": len(result.files_searched),
        "skipped_files": [{"file": f, "error": e} for f, e in result.skipped_files],
        "elapsed_seconds": round(result.elapsed, 3),
        **envelope,
    }


def get_document_context(
    file: str,
    query: list[str],
    directory: Optional[str] = None,
    context_before: int = 3,
    context_after: int = 3,
    use_regex: bool = False,
    use_ocr: Optional[bool] = None,
) -> dict[str, Any]:
    """Return the lines surrounding matches of a query within one file.

    Call this to see a match in context — the lines before and after it —
    inside a specific document. ``file`` is matched by filename; the search
    runs recursively under ``directory`` to locate it.
    """
    use_ocr = _CONFIG.ocr_default if use_ocr is None else use_ocr
    d = _resolve_dir(directory)
    result = api.search(
        query,
        directory=d,
        recursive=True,
        file_names=[os.path.basename(file)],
        context_before=context_before,
        context_after=context_after,
        use_regex=use_regex,
        use_ocr=use_ocr,
        use_index=False,
    )
    matches, envelope = _cap(_match_dicts(result.matches))
    return {"file": file, "searched_directory": d, "matches": matches, **envelope}


def inventory_folder(
    directory: Optional[str] = None,
    recursive: Optional[bool] = None,
    use_ocr: Optional[bool] = None,
    file_types: Optional[list[str]] = None,
) -> dict[str, Any]:
    """List the searchable files in a folder without reading their contents.

    Call this to see what documents exist in a folder — each file's path,
    size, last-modified time, and type. This is a read-only listing; it does
    not open, index, or modify any file.
    """
    recursive = _CONFIG.recursive_default if recursive is None else recursive
    use_ocr = _CONFIG.ocr_default if use_ocr is None else use_ocr
    d = _resolve_dir(directory)
    items = api.inventory_folder(
        d, recursive=recursive, use_ocr=use_ocr, file_types=file_types
    )
    rows, envelope = _cap([
        {
            "path": it.path,
            "size_bytes": it.size_bytes,
            "size_human": format_bytes(it.size_bytes),
            "modified": datetime.fromtimestamp(it.modified).isoformat(timespec="seconds"),
            "extension": it.extension,
        }
        for it in items
    ])
    return {"searched_directory": d, "files": rows, **envelope}


def list_supported_file_types(include_ocr: bool = False) -> dict[str, Any]:
    """List the file extensions peekdocs can search.

    Call this to check whether a given file type is searchable. Set
    ``include_ocr`` to also list image types that need OCR enabled.
    """
    exts = api.list_supported_file_types(include_ocr=include_ocr)
    return {"extensions": exts, "count": len(exts)}


def list_search_suites(directory: Optional[str] = None) -> dict[str, Any]:
    """List the saved search suites available in a folder.

    A suite is a named group of saved searches. Returns a mapping of suite
    name to the saved-search names it contains.
    """
    d = _resolve_dir(directory)
    return {"suites": api.list_suites(directory=d)}


def run_search_suite(name: str, directory: Optional[str] = None) -> dict[str, Any]:
    """Run a saved search suite by name and return per-search match counts.

    Running a suite only performs searches — it is read-only. Returns each
    saved search's match and file counts plus a capped flat list of matches.
    """
    d = _resolve_dir(directory)
    result = api.run_suite(name, directory=d)
    matches, envelope = _cap([
        m
        for sr in result.search_results
        for m in _match_dicts(sr.matches)
    ])
    return {
        "searched_directory": d,
        "suite": result.suite,
        "total_matches": result.total_matches,
        "elapsed_seconds": round(result.elapsed, 3),
        "searches": [
            {
                "name": sr.search_name,
                "terms": sr.search_terms,
                "mode": sr.mode,
                "match_count": len(sr.matches),
                "file_count": len(sr.files_searched),
            }
            for sr in result.search_results
        ],
        "skipped_searches": [{"name": n, "reason": r} for n, r in result.skipped_searches],
        "matches": matches,
        **envelope,
    }


def list_regex_collections() -> dict[str, Any]:
    """List the names of saved regex collections (global, folder-independent)."""
    names = api.list_regex_collections()
    return {"collections": names, "count": len(names)}


def run_regex_collection(
    name: str,
    directory: Optional[str] = None,
    recursive: Optional[bool] = None,
) -> dict[str, Any]:
    """Run a saved regex collection by name and return per-pattern match counts.

    Running a collection only performs regex searches — it is read-only.
    Returns each pattern's match and file counts plus a capped flat list of
    matches.
    """
    recursive = _CONFIG.recursive_default if recursive is None else recursive
    d = _resolve_dir(directory)
    result = api.run_regex_collection(name, directory=d, recursive=recursive)
    matches, envelope = _cap([
        m
        for pr in result.pattern_results
        for m in _match_dicts(pr.matches)
    ])
    return {
        "searched_directory": d,
        "collection": result.collection,
        "total_matches": result.total_matches,
        "elapsed_seconds": round(result.elapsed, 3),
        "patterns": [
            {
                "name": pr.name,
                "regex": pr.regex,
                "match_count": len(pr.matches),
                "file_count": pr.files_matched,
            }
            for pr in result.pattern_results
        ],
        "skipped_patterns": [{"name": n, "error": e} for n, e in result.skipped_patterns],
        "matches": matches,
        **envelope,
    }


# The read-only tool set. Order is display order.
_TOOLS = [
    search_documents,
    get_document_context,
    inventory_folder,
    list_supported_file_types,
    list_search_suites,
    run_search_suite,
    list_regex_collections,
    run_regex_collection,
]


# ── Server construction (requires the optional `mcp` package) ───────

def build_server():
    """Create and return a FastMCP server with the read-only tools registered.

    Imports ``mcp`` lazily so the rest of this module (and its guardrails)
    stays importable without the optional dependency.
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover - exercised via main()
        raise ImportError(
            "The MCP server requires the 'mcp' package. "
            "Install it with:  pip install peekdocs[mcp]"
        ) from exc

    server = FastMCP("peekdocs")
    for tool in _TOOLS:
        server.tool()(tool)
    return server


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point for the ``peekdocs-mcp`` console script."""
    parser = argparse.ArgumentParser(
        prog="peekdocs-mcp",
        description="Read-only MCP server for local document search (peekdocs).",
    )
    parser.add_argument(
        "--root",
        action="append",
        default=[],
        metavar="DIR",
        help="Restrict all searches to this folder (required; repeatable "
             "to allow more than one folder). An AI assistant using this "
             "server can only search inside the folders you name here.",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=None,
        metavar="N",
        help="Maximum matches/files returned per tool call. The running server "
             "defaults to 200; a generated config (--print-config / --setup) "
             "suggests 25 — small enough to fit a local model's context window.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Make searches include subfolders by default (tools can still "
             "override per call).",
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Read scanned PDFs and images with OCR by default (requires "
             "Tesseract; slower). Tools can still override per call.",
    )
    parser.add_argument(
        "--allow-index",
        action="store_true",
        help="Allow using/refreshing the on-disk search index by default "
             "(writes a .peekdocs.db to searched folders). Off by default to "
             "keep the server read-only.",
    )
    parser.add_argument(
        "--print-config",
        action="store_true",
        help="Print the LM Studio mcp.json config for these settings and exit "
             "(writes nothing).",
    )
    parser.add_argument(
        "--write-lmstudio-config",
        action="store_true",
        help="Merge this server into LM Studio's mcp.json (~/.lmstudio/mcp.json) "
             "and exit.",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Interactive setup: pick a folder (if none given) and write the "
             "LM Studio config, printing it if LM Studio isn't installed.",
    )
    parser.add_argument(
        "--config-path",
        default=None,
        metavar="FILE",
        help="Write the config to this mcp.json path instead of LM Studio's "
             "default (parent folders are created).",
    )
    args = parser.parse_args(argv)

    from peekdocs import mcp_setup

    roots = [os.path.realpath(os.path.expanduser(r)) for r in args.root]

    is_setup_mode = args.print_config or args.write_lmstudio_config or args.setup

    if args.setup and not roots:
        picked = mcp_setup.pick_folder()
        if picked:
            roots = [picked]

    if not roots and not is_setup_mode:
        parser.error(
            "--root is required. Name at least one folder the assistant may "
            "search, e.g.  peekdocs-mcp --root ~/Documents"
        )

    _CONFIG.roots = roots
    # --max-results serves two masters with different sensible defaults: the
    # running server caps at 200, but a generated config suggests the smaller,
    # local-model-friendly 25. An explicit value wins for both.
    _CONFIG.max_results = (
        args.max_results
        if args.max_results is not None
        else mcp_setup.SERVER_DEFAULT_MAX_RESULTS
    )
    _CONFIG.recursive_default = args.recursive
    _CONFIG.ocr_default = args.ocr
    _CONFIG.allow_index_default = args.allow_index

    setup = mcp_setup.McpSetup(
        roots=roots,
        max_results=(
            args.max_results
            if args.max_results is not None
            else mcp_setup.SUGGESTED_MAX_RESULTS
        ),
        recursive=args.recursive,
        ocr=args.ocr,
        allow_index=args.allow_index,
    )

    if args.print_config:
        print(mcp_setup.render_json(setup))
        return 0

    if args.write_lmstudio_config or args.setup:
        config_path = args.config_path
        if config_path:
            path = Path(config_path)
        else:
            path = mcp_setup.lmstudio_config_path()
            if not mcp_setup.lmstudio_installed():
                # Failsafe: don't create ~/.lmstudio behind the user's back.
                print(mcp_setup.render_json(setup))
                print(
                    "\nLM Studio not found (no ~/.lmstudio). Config shown "
                    "above; install LM Studio and re-run, or use "
                    "--print-config / --config-path.",
                    file=sys.stderr,
                )
                return 0 if args.setup else 2
        try:
            written = mcp_setup.write_config(
                setup, path, backup=True, create_parent=bool(config_path)
            )
        except mcp_setup.SetupError as e:
            print(str(e), file=sys.stderr)
            return 2
        print(f"Wrote {written}. Restart LM Studio to load it.")
        return 0

    build_server().run()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
