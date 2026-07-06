"""Public library API for peekdocs — call search() programmatically."""

from __future__ import annotations

import multiprocessing
import os
import platform
import re
import signal
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable

# On Linux, the default multiprocessing start method is "fork", which can
# deadlock when a multiprocessing.Pool is created from within a thread (e.g.
# a GUI daemon thread). Using "forkserver" avoids this by spawning worker
# processes from a clean, non-threaded server process.
if platform.system() == "Linux":
    try:
        multiprocessing.set_start_method("forkserver", force=False)
    except RuntimeError:
        pass  # Already set — ignore

from peekdocs.constants import _default_cores
from peekdocs.indexer import index_exists, refresh_index, search_with_index
from peekdocs.scanner import _process_file, _ocr_image, discover_files


@dataclass
class SearchMatch:
    """A single search match."""

    file_dir: str
    filename: str
    line_num: int
    text: str

    def __iter__(self) -> Any:
        """Allow tuple unpacking: fd, fn, ln, tx = match."""
        return iter((self.file_dir, self.filename, self.line_num, self.text))

    def __len__(self) -> int:
        return 4

    def __getitem__(self, index: int) -> Any:
        return (self.file_dir, self.filename, self.line_num, self.text)[index]


@dataclass
class SearchResult:
    """Complete result of a search operation."""

    matches: list[SearchMatch]
    files_searched: list[str]           # absolute paths
    skipped_files: list[tuple[str, str]]  # (filename, error_msg)
    elapsed: float                       # seconds
    used_index: bool                     # whether the indexed path was used
    index_bypass_reason: str = ""        # non-empty when user requested index but it was bypassed
    index_stale_notice: str = ""         # non-empty when index metadata doesn't match current params


def search(
    search_terms: list[str],
    *,
    directory: str | None = None,
    match_all: bool = False,
    recursive: bool = False,
    use_regex: bool = False,
    use_fuzzy: bool = False,
    use_wildcard: bool = False,
    use_whole_word: bool = False,
    use_ocr: bool = False,
    exclude_terms: list[str] | None = None,
    file_types: list[str] | None = None,
    file_names: list[str] | None = None,
    context_before: int = 0,
    context_after: int = 0,
    proximity: int = 0,
    line_proximity: int = 0,
    cores: int | None = None,
    use_index: bool | None = None,
    progress: Callable[[int, int], None] | None = None,
    expression: str | None = None,
    range_filters: list[str] | None = None,
    max_file_size_mb: int = 100,
) -> SearchResult:
    """Search documents and return structured results.

    Parameters
    ----------
    search_terms : list[str]
        Terms to search for.
    directory : str, optional
        Directory to search in. Defaults to current working directory.
    match_all : bool
        If True, require ALL terms to match (AND mode). Default is OR mode.
    recursive : bool
        Search subdirectories.
    use_regex : bool
        Treat search terms as regex patterns.
    use_fuzzy : bool
        Use fuzzy/approximate matching.
    use_wildcard : bool
        Treat search terms as wildcard patterns (* and ?).
    use_whole_word : bool
        Match complete words only (won't match "bob" inside "bobcat").
    use_ocr : bool
        Enable OCR for scanned PDFs and images.
    exclude_terms : list[str], optional
        Exclude lines matching these terms.
    file_types : list[str], optional
        Limit to these file extensions (e.g. [".pdf", ".docx"]).
    file_names : list[str], optional
        Search only these specific filenames.
    context_before : int
        Number of lines to include before each match.
    context_after : int
        Number of lines to include after each match.
    proximity : int
        If > 0, require all terms within this many words of each other.
    line_proximity : int
        If > 0, require all terms within this many lines of each other
        (the line-proximity counterpart to ``proximity``, which is word-proximity).
    cores : int, optional
        Number of CPU cores. None = auto-detect.
    use_index : bool, optional
        True = use index, False = direct scan, None = auto-detect.
    progress : callable, optional
        Callback ``progress(done, total, filename)`` called as files are processed.
    expression : str, optional
        Boolean expression string (e.g. "(bob AND amy) OR fred"). Mutually exclusive
        with match_all, exclude_terms, and proximity.
    range_filters : list[str], optional
        Range filter specs (e.g. ["amount:1000..5000", "date:2024-01-01..2024-12-31"]).
        Content ranges filter matched lines; metadata ranges filter files.

    Returns
    -------
    SearchResult
        Structured results with matches, files_searched, skipped_files, elapsed, used_index.

    Raises
    ------
    ValueError
        For invalid parameter combinations (e.g. regex + fuzzy).
    """
    # ── Parse range filters ────────────────────────────────────
    from peekdocs.range_query import parse_range, split_ranges
    parsed_ranges = []
    if range_filters:
        for spec_str in range_filters:
            parsed_ranges.append(parse_range(spec_str))
    content_ranges, metadata_ranges, filename_ranges = split_ranges(parsed_ranges)

    # ── Validate parameters ─────────────────────────────────────
    if expression is not None:
        if match_all:
            raise ValueError("Cannot combine expression with match_all. Use AND/OR in the expression.")
        if exclude_terms:
            raise ValueError("Cannot combine expression with exclude_terms. Use NOT in the expression.")
        if proximity > 0:
            raise ValueError("Cannot combine expression with proximity search.")
        from peekdocs.expr_parser import parse_expression, extract_terms
        expression_ast = parse_expression(expression)
        if not search_terms:
            search_terms = extract_terms(expression_ast)
        if use_regex:
            for term in extract_terms(expression_ast):
                try:
                    re.compile(term)
                except re.error as e:
                    raise ValueError(f"Invalid regex pattern '{term}' in expression: {e}")
    else:
        expression_ast = None
        if not search_terms and not range_filters:
            raise ValueError("No search terms provided.")
    if use_fuzzy and use_regex:
        raise ValueError("Cannot combine fuzzy and regex search modes.")
    if use_wildcard and use_regex:
        raise ValueError("Cannot combine wildcard and regex search modes.")
    if use_wildcard and use_fuzzy:
        raise ValueError("Cannot combine wildcard and fuzzy search modes.")
    if expression is None and use_regex:
        for term in search_terms:
            try:
                re.compile(term)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern '{term}': {e}")
    if proximity > 0 and len(search_terms) < 2:
        raise ValueError("Proximity search requires at least 2 search terms.")

    # ── Resolve defaults ────────────────────────────────────────
    if directory is None:
        directory = os.getcwd()
    if exclude_terms is None:
        exclude_terms = []
    if cores is None:
        cores = _default_cores()

    use_proximity = proximity > 0
    if use_proximity:
        match_all = True
    use_context = context_before > 0 or context_after > 0

    # Convert file_types list to set if provided
    ft_set = set(file_types) if file_types else None

    start_time = time.time()

    # ── Build search config dict (used by scanner/indexer) ──────
    search_config = {
        "search_terms": search_terms,
        "use_regex": use_regex,
        "match_all": match_all,
        "use_proximity": use_proximity,
        "proximity": proximity,
        "line_proximity": line_proximity,
        "use_context": use_context,
        "context_before": context_before,
        "context_after": context_after,
        "use_ocr": use_ocr,
        "use_fuzzy": use_fuzzy,
        "exclude_terms": exclude_terms,
        "use_wildcard": use_wildcard,
        "use_whole_word": use_whole_word,
        "expression_ast": expression_ast,
        "_ocr_image_func": _ocr_image,
        "content_ranges": content_ranges,
        "metadata_ranges": metadata_ranges,
        "filename_ranges": filename_ranges,
        "max_file_size_mb": max_file_size_mb,
    }

    # ── Determine search path ───────────────────────────────────
    matches = []
    skipped_files = []
    all_files = []
    indexed = False

    if use_index is None:
        use_index = index_exists(directory)
    elif use_index:
        use_index = index_exists(directory)

    # Performance bypass: regex / fuzzy / wildcard / proximity queries
    # can't be accelerated by FTS5 (the token-based index can't filter
    # pattern matches), and the indexed parse-cache path scans paragraphs
    # serially while the direct-scan path uses multiprocessing.Pool. On
    # multi-core machines the direct path is several times faster for
    # these modes — observed 23s vs 3s on a phone-number wizard search
    # on a 14-core Mac. Silently fall through to the direct path so the
    # user gets the faster behavior; the index is still used the moment
    # they run a literal / Boolean / whole-word query. The reason is
    # surfaced via SearchResult.index_bypass_reason so the CLI / GUI
    # can show a one-line note explaining what happened.
    index_bypass_reason = ""
    if use_index and (use_regex or use_fuzzy or use_wildcard or use_proximity):
        use_index = False
        if use_regex:
            index_bypass_reason = "regex query — direct scan is faster than the index"
        elif use_fuzzy:
            index_bypass_reason = "fuzzy query — direct scan is faster than the index"
        elif use_wildcard:
            index_bypass_reason = "wildcard query — direct scan is faster than the index"
        elif use_proximity:
            index_bypass_reason = "proximity query — direct scan is faster than the index"

    index_stale_notice = ""
    if use_index:
        indexed = True
        # Detect parameter mismatch with stored index metadata and surface a
        # notice rather than auto-rebuilding silently. Previous behavior was
        # to fire a full rebuild every time max_file_size_mb didn't match the
        # stored value; on large folders (or folders with filename quirks
        # that interact badly with build_index), that rebuild could fail
        # silently inside `except Exception: pass`, wasting time on every
        # search without any visible signal. The user can rebuild
        # explicitly with `peekdocs --index` when they're ready.
        try:
            from peekdocs.indexer import index_status as _status
            status = _status(directory)
            if status is not None:
                stored_mfs = status.get("max_file_size_mb")
                if stored_mfs is None:
                    index_stale_notice = (
                        "index lacks max-file-size metadata (built by an older peekdocs); "
                        "run `peekdocs --index` to rebuild with metadata"
                    )
                else:
                    try:
                        stored_int = int(stored_mfs)
                        if stored_int != max_file_size_mb:
                            index_stale_notice = (
                                f"index built with max-file-size={stored_int} MB; current "
                                f"setting is {max_file_size_mb} MB. Files outside the indexed "
                                f"range are not in the index. Run `peekdocs --index` to rebuild"
                            )
                    except (ValueError, TypeError):
                        index_stale_notice = (
                            f"index has unparseable max-file-size metadata "
                            f"({stored_mfs!r}); run `peekdocs --index` to rebuild"
                        )
        except Exception as exc:
            # Surface the actual error rather than swallowing it. Useful for
            # debugging future regressions in index_status.
            index_stale_notice = f"could not inspect index metadata: {exc}"
        try:
            refresh_index(directory, recursive=True, use_ocr=use_ocr, max_file_size_mb=max_file_size_mb)
        except Exception:
            pass  # Search with existing index if refresh fails (e.g. DB locked)
        idx_matches, idx_skipped, indexed_files = search_with_index(
            directory, search_config, ft_set, file_names,
        )
        matches = [SearchMatch(*m) for m in idx_matches]
        skipped_files = list(idx_skipped)
        # For file count reporting, use the actual folder discovery (includes
        # oversized files that were skipped) so indexed and non-indexed searches
        # report consistent file counts.
        try:
            disc = discover_files(directory, True, use_ocr, ft_set, file_names)
            if not isinstance(disc, tuple):
                all_files = disc
            else:
                all_files = indexed_files
        except Exception:
            all_files = indexed_files

        # If index was corrupt and deleted, fall back to direct scan
        if not index_exists(directory):
            indexed = False
            matches = []
            skipped_files = []

    if not indexed:
        result = discover_files(directory, recursive, use_ocr, ft_set, file_names)
        if isinstance(result, tuple):
            raise FileNotFoundError(result[1])
        all_files = result
        total = len(all_files)

        if total < 10 or cores == 1:
            for i, filepath in enumerate(all_files):
                filename = os.path.relpath(filepath, directory)
                if progress:
                    progress(i, total, filename)
                file_matches, file_skipped = _process_file((filepath, search_config))
                matches.extend(SearchMatch(*m) for m in file_matches)
                skipped_files.extend(file_skipped)
        else:
            pool = multiprocessing.Pool(
                processes=cores,
                initializer=signal.signal,
                initargs=(signal.SIGINT, signal.SIG_IGN),
            )
            try:
                result_iter = pool.imap(
                    _process_file, [(f, search_config) for f in all_files]
                )
                for i in range(total):
                    filename = os.path.relpath(all_files[i], directory)
                    if progress:
                        progress(i, total, filename)
                    file_matches, file_skipped = next(result_iter)
                    matches.extend(SearchMatch(*m) for m in file_matches)
                    skipped_files.extend(file_skipped)
            finally:
                pool.terminate()
                pool.join()

        if progress and total > 0:
            progress(total, total, "done")

    elapsed = time.time() - start_time

    return SearchResult(
        matches=matches,
        files_searched=all_files,
        skipped_files=skipped_files,
        elapsed=elapsed,
        used_index=indexed,
        index_bypass_reason=index_bypass_reason,
        index_stale_notice=index_stale_notice,
    )


# ── Search suites ──────────────────────────────────────────────────


@dataclass
class SuiteSearchResult:
    """Result for a single saved search within a suite run."""

    search_name: str                 # name of the saved search
    search_terms: list[str]          # list of search terms or [expression]
    matches: list[SearchMatch]
    files_searched: list[str]
    elapsed: float                   # seconds
    mode: str                        # "ALL" or "ANY"


@dataclass
class SuiteResult:
    """Complete result of running a search suite."""

    suite: str                                 # suite name
    search_results: list[SuiteSearchResult]
    total_matches: int                         # sum of all search match counts
    elapsed: float                             # total seconds
    skipped_searches: list[tuple[str, str]]    # (name, reason)


def list_suites(directory: str | None = None) -> dict[str, list[str]]:
    """Return a dict of suite names to their search name lists for a directory.

    Parameters
    ----------
    directory : str, optional
        Directory containing the collection file. Defaults to current directory.

    Returns
    -------
    dict[str, list[str]]
        Mapping of suite names to lists of saved search names.
        Empty dict if no suites exist.
    """
    from peekdocs.collection import load_collection
    if directory is None:
        directory = os.getcwd()
    data = load_collection(directory)
    return dict(data.get("suites", {}))


def run_suite(
    name: str,
    *,
    directory: str | None = None,
    progress: Callable[[int, int, str], None] | None = None,
    max_file_size_mb: int = 100,
) -> SuiteResult:
    """Run a saved search suite by name.

    Each saved search in the suite is executed with its original settings
    (AND/OR, regex, recursive, etc.).  Suites are stored per-folder in
    ``.peekdocs_collection.json``.

    Parameters
    ----------
    name : str
        Name of a saved search suite (created in the GUI via
        Tools → Search Suites).
    directory : str, optional
        Directory containing the suite and its saved searches.
        Defaults to current working directory.
    progress : callable, optional
        Callback ``progress(search_index, total_searches, search_name)``
        called before each search starts.
    max_file_size_mb : int
        Skip files larger than this (MB). 0 = no limit.

    Returns
    -------
    SuiteResult
        Per-search results and aggregate totals.

    Raises
    ------
    FileNotFoundError
        If no collection file exists in the directory.
    KeyError
        If the named suite is not found.
    ValueError
        If the suite has no searches.
    """
    import shlex
    from peekdocs.collection import load_collection, get_suite, get_search_params

    if directory is None:
        directory = os.getcwd()

    # Validate suite exists
    data = load_collection(directory)
    suite_searches = get_suite(directory, name)
    if suite_searches is None:
        available = sorted(data.get("suites", {}).keys())
        raise KeyError(
            f"Suite '{name}' not found in {directory}. "
            f"Available: {', '.join(available) if available else '(none)'}"
        )
    if not suite_searches:
        raise ValueError(f"Suite '{name}' has no searches.")

    start_time = time.time()
    search_results = []
    skipped = []

    for i, search_name in enumerate(suite_searches):
        if progress:
            progress(i, len(suite_searches), search_name)

        params = get_search_params(directory, search_name)
        if params is None:
            skipped.append((search_name, "saved search not found"))
            continue

        # Convert saved-search params to search() kwargs.
        # Regex and wildcard patterns are single tokens — shlex would
        # treat their backslashes as escapes and silently corrupt the
        # pattern (e.g. r"print\(" -> "print(" with an unbalanced
        # paren), so we use the raw search_text as one term in those
        # modes. Plain-text searches still go through shlex so quoted
        # phrases like '"insecure core"' get respected.
        # Three modes: expression (search_text is the boolean
        # expression string, goes to `expression=` kwarg with empty
        # terms), regex/wildcard (single-token pattern, no shlex),
        # plain text (shlex-split for quoted phrases). Historic bug:
        # `expr = params.get("expression") if params.get(...)` treated
        # the schema's boolean expression flag as the expression string
        # and passed True to api_search, which raised inside tokenize()
        # trying to .strip() a boolean.
        terms_str = params.get("search_text", "")
        if params.get("expression"):
            search_terms = []
            expr = terms_str or None
        elif params.get("regex") or params.get("wildcard"):
            search_terms = [terms_str] if terms_str else []
            expr = None
        else:
            try:
                search_terms = shlex.split(terms_str) if terms_str else []
            except ValueError:
                search_terms = terms_str.split() if terms_str else []
            expr = None
        kwargs = {
            "directory": directory,
            "match_all": params.get("and_mode", False),
            "recursive": params.get("recursive", False),
            "use_fuzzy": params.get("fuzzy", False),
            "use_wildcard": params.get("wildcard", False),
            "use_regex": params.get("regex", False),
            "use_ocr": params.get("ocr", False),
            "use_whole_word": params.get("whole_word", False),
            "use_index": params.get("index_search", False),
            "max_file_size_mb": max_file_size_mb,
        }
        if params.get("exclude"):
            kwargs["exclude_terms"] = [t.strip() for t in params["exclude"].split(",") if t.strip()]
        if params.get("file_types"):
            kwargs["file_types"] = [t.strip() for t in params["file_types"].split(",") if t.strip()]
        if params.get("proximity"):
            kwargs["proximity"] = int(params["proximity"])
        if params.get("context_before"):
            kwargs["context_before"] = int(params["context_before"])
        if params.get("context_after"):
            kwargs["context_after"] = int(params["context_after"])
        if params.get("range_filters"):
            rf = params["range_filters"]
            kwargs["range_filters"] = rf if isinstance(rf, list) else [r.strip() for r in rf.split(",") if r.strip()]

        result = search(search_terms if not expr else [], expression=expr, **kwargs)

        mode = "ALL" if params.get("and_mode") else "ANY"
        display_terms = search_terms if not expr else [expr]

        search_results.append(SuiteSearchResult(
            search_name=search_name,
            search_terms=display_terms,
            matches=result.matches,
            files_searched=result.files_searched,
            elapsed=result.elapsed,
            mode=mode,
        ))

    if progress:
        progress(len(suite_searches), len(suite_searches), "done")

    elapsed = time.time() - start_time
    total = sum(len(sr.matches) for sr in search_results)

    return SuiteResult(
        suite=name,
        search_results=search_results,
        total_matches=total,
        elapsed=elapsed,
        skipped_searches=skipped,
    )


# ── Regex collections ──────────────────────────────────────────────

def _collections_path():
    """Return the path to the global regex-collections file.

    Resolved fresh on each call rather than cached at import time so test
    suites that redirect HOME / USERPROFILE see the redirected path.
    """
    return os.path.join(os.path.expanduser("~"), ".peekdocs_regex_collections.json")


@dataclass
class PatternResult:
    """Result for a single regex pattern within a collection run."""

    name: str                       # pattern label (e.g. "Passwords")
    regex: str                      # the regex string
    matches: list[SearchMatch]
    files_matched: int              # number of distinct files with matches


@dataclass
class CollectionResult:
    """Complete result of running a regex collection."""

    collection: str                          # collection name
    pattern_results: list[PatternResult]
    total_matches: int                       # sum of all pattern match counts
    files_searched: list[str]                # absolute paths (from last pattern run)
    elapsed: float                           # seconds
    skipped_patterns: list[tuple[str, str]]  # (name, error_msg)


def list_regex_collections() -> list[str]:
    """Return a list of saved regex collection names.

    Returns
    -------
    list[str]
        Sorted list of collection names. Empty list if no collections exist.
    """
    import json as _json
    path = _collections_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = _json.load(f)
        return sorted(data.keys())
    except Exception:
        return []


def run_regex_collection(
    name: str,
    *,
    directory: str | None = None,
    recursive: bool = False,
    progress: Callable[[int, int, str], None] | None = None,
    max_file_size_mb: int = 100,
) -> CollectionResult:
    """Run a saved regex collection by name.

    Each enabled pattern in the collection is executed separately as an
    independent regex search.  Results are returned per-pattern and also
    aggregated.

    Parameters
    ----------
    name : str
        Name of a saved regex collection (created in the GUI via
        Regex Search → Save Collection As).
    directory : str, optional
        Directory to search in. Defaults to current working directory.
    recursive : bool
        Search subdirectories.
    progress : callable, optional
        Callback ``progress(pattern_index, total_patterns, pattern_name)``
        called before each pattern starts.
    max_file_size_mb : int
        Skip files larger than this (MB). 0 = no limit.

    Returns
    -------
    CollectionResult
        Per-pattern results and aggregate totals.

    Raises
    ------
    FileNotFoundError
        If no collections file exists.
    KeyError
        If the named collection is not found.
    ValueError
        If the collection has no enabled patterns.
    """
    import json as _json

    if directory is None:
        directory = os.getcwd()

    # Load collection
    path = _collections_path()
    if not os.path.exists(path):
        raise FileNotFoundError(
            "No saved regex collections found. "
            "Create one in the GUI (Regex Search \u2192 Save Collection As)."
        )
    with open(path, "r", encoding="utf-8") as f:
        all_collections = _json.load(f)

    if name not in all_collections:
        available = sorted(all_collections.keys())
        raise KeyError(
            f"Collection '{name}' not found. "
            f"Available: {', '.join(available) if available else '(none)'}"
        )

    patterns = all_collections[name]
    active = [
        (p.get("name", ""), p["regex"])
        for p in patterns
        if p.get("enabled") and p.get("regex", "").strip()
    ]
    if not active:
        raise ValueError(f"Collection '{name}' has no enabled patterns.")

    start_time = time.time()
    pattern_results = []
    skipped = []
    files_searched = []

    for i, (pname, regex) in enumerate(active):
        if progress:
            progress(i, len(active), pname)

        # Validate regex
        try:
            re.compile(regex)
        except re.error as exc:
            skipped.append((pname, str(exc)))
            continue

        result = search(
            [regex],
            directory=directory,
            recursive=recursive,
            use_regex=True,
            use_index=False,
            max_file_size_mb=max_file_size_mb,
        )
        files_searched = result.files_searched

        pattern_results.append(PatternResult(
            name=pname,
            regex=regex,
            matches=result.matches,
            files_matched=len({m.filename for m in result.matches}),
        ))

    if progress:
        progress(len(active), len(active), "done")

    elapsed = time.time() - start_time
    total = sum(len(pr.matches) for pr in pattern_results)

    return CollectionResult(
        collection=name,
        pattern_results=pattern_results,
        total_matches=total,
        files_searched=files_searched,
        elapsed=elapsed,
        skipped_patterns=skipped,
    )
