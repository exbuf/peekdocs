"""``peekdocs --diff`` — compare two peekdocs JSON snapshots.

Takes two JSON files produced by ``peekdocs --stdout`` or ``-o json``
and reports what changed between them: new files, removed files,
files whose match count went up or down, and lines that were modified.
Returns exit 1 if anything actionable changed, 0 if all changes were
"just removals" or nothing changed.
"""
from __future__ import annotations

import json
import os
import sys


# Common source-document extensions — used to detect the "user passed
# me a document instead of a JSON snapshot" mistake and print a
# targeted hint. Kept private to this module because it's a UX hint
# only, not a semantic filter.
_DOC_EXTS = {
    ".odt", ".ods", ".odp", ".doc", ".docx", ".xls", ".xlsx",
    ".ppt", ".pptx", ".pdf", ".rtf", ".pages", ".numbers",
    ".key", ".txt", ".md", ".html", ".htm",
}


def _diff_input_hint(path: str) -> None:
    """Print a hint to stderr when *path* looks like a source document
    rather than a peekdocs JSON snapshot. Called after a JSON read
    failure so the user learns to produce a snapshot first."""
    ext = os.path.splitext(path)[1].lower()
    if ext in _DOC_EXTS:
        print(
            f"\nHint: '{os.path.basename(path)}' looks like a document, not a peekdocs JSON snapshot.\n"
            "      --diff compares two scan results, not two source documents.\n"
            "      Produce a snapshot first, e.g.:\n"
            "          peekdocs <terms> -r --stdout > peekdocs_snapshot_yesterday.json\n"
            "          peekdocs <terms> -r --stdout > peekdocs_snapshot_today.json\n"
            "          peekdocs --diff peekdocs_snapshot_yesterday.json peekdocs_snapshot_today.json\n"
            "      To compare two documents directly, use a document comparison tool\n"
            "      (LibreOffice: Edit → Track Changes → Compare Document).",
            file=sys.stderr,
        )
    else:
        print(
            "\nHint: --diff expects JSON files produced by peekdocs --stdout or -o json.",
            file=sys.stderr,
        )


def handle_diff(args: list[str]) -> int:
    """Handle ``peekdocs --diff OLD NEW [--json]``.

    *args* is the full argv-after-``peekdocs`` list; the caller has
    already confirmed ``args[0] == "--diff"``.

    Returns ``2`` on usage error or unreadable input, ``0`` if the diff
    is empty or contains only removals, ``1`` if anything actionable
    changed (new files, more matches, content modified).
    """
    if len(args) < 3:
        print("Error: --diff requires two JSON file paths.", file=sys.stderr)
        print("Usage: peekdocs --diff peekdocs_snapshot_old.json peekdocs_snapshot_new.json [--json]\n", file=sys.stderr)
        return 2

    old_path = args[1]
    new_path = args[2]
    emit_json = "--json" in args[3:]

    from peekdocs.diff import load_json, compute_diff, format_human, is_actionable

    old_data, err = load_json(old_path)
    if err:
        print(f"Error reading old file: {err}", file=sys.stderr)
        _diff_input_hint(old_path)
        return 2
    new_data, err = load_json(new_path)
    if err:
        print(f"Error reading new file: {err}", file=sys.stderr)
        _diff_input_hint(new_path)
        return 2

    diff = compute_diff(old_data, new_data)
    if emit_json:
        sys.stdout.write(json.dumps(diff, indent=2, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(format_human(diff, old_path, new_path))
    # Exit 1 if anything actionable changed (new files, more matches,
    # content modified). Exit 0 if only removals or all unchanged.
    return 1 if is_actionable(diff) else 0
