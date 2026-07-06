"""``peekdocs --list-files`` — enumerate peekdocs files in the cwd.

Lists every peekdocs-authored file in the current directory (results,
saved reports, accumulated reports, error log, index, saved-searches
JSON) with per-file sizes. Non-destructive — a companion to ``--clear``
which does delete.
"""
from __future__ import annotations

import os

from peekdocs.paths import format_bytes


def handle_list_files() -> int:
    """Handle ``peekdocs --list-files``.

    Enumerates peekdocs-authored files in the current working directory
    (the caller has already stripped the ``--list-files`` token from
    args, so this handler needs no argv). Returns ``0`` unconditionally.
    """
    from peekdocs.scanner import RESULT_FILE_PREFIXES

    cwd = os.getcwd()
    found: list[tuple[str, str]] = []
    for f in sorted(os.listdir(cwd)):
        if (f.startswith(RESULT_FILE_PREFIXES) or
            f.startswith("peekdocs_report_") or
            f.startswith("peekdocs_accumulated_") or
            f in ("peekdocs_errors.log", ".peekdocs.db", ".peekdocs.db-wal",
                   ".peekdocs.db-shm", ".peekdocs_collection.json")):
            size = os.path.getsize(os.path.join(cwd, f))
            found.append((f, format_bytes(size)))
    if found:
        print(f"\npeekdocs files in {cwd}:\n")
        for f, size_str in found:
            print(f"  {f}  ({size_str})")
        print(f"\n{len(found)} file(s). Use --clear to delete results, --clear-all to delete everything.")
    else:
        print(f"\nNo peekdocs files found in {cwd}.")
    print()
    return 0
