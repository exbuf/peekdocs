"""``peekdocs --clear`` / ``--clear-all`` — remove peekdocs files.

``--clear`` deletes result files only (peekdocs_standard_results.*,
peekdocs_suite_results.*, peekdocs_regex_results.*). ``--clear-all``
additionally removes saved reports, accumulated reports, the error
log, and the search index. Neither touches saved searches
(``.peekdocs_collection.json``), user settings (``~/.peekdocsrc``),
or bookmarks — those live in the user's home directory rather than
the working directory and are the persistent-config surface.
"""
from __future__ import annotations

import os


def handle_clear(args: list[str]) -> int:
    """Handle ``peekdocs --clear`` and ``peekdocs --clear-all``.

    *args* is the full argv-after-``peekdocs`` list; the caller has
    already confirmed ``args[0]`` is one of ``"--clear"`` or
    ``"--clear-all"``.

    Returns ``0`` unconditionally (including "no files to delete" — an
    empty cwd is not an error state).
    """
    from peekdocs.scanner import RESULT_FILE_PREFIXES

    cwd = os.getcwd()
    clear_all = args[0] == "--clear-all"
    deleted: list[str] = []

    # Always delete results files
    for f in os.listdir(cwd):
        if f.startswith(RESULT_FILE_PREFIXES):
            os.remove(os.path.join(cwd, f))
            deleted.append(f)

    if clear_all:
        # Also delete saved reports, error log, and index
        for f in os.listdir(cwd):
            if f.startswith(("peekdocs_report_", "peekdocs_accumulated_")):
                os.remove(os.path.join(cwd, f))
                deleted.append(f)
        for f in ("peekdocs_errors.log", ".peekdocs.db", ".peekdocs.db-wal", ".peekdocs.db-shm"):
            path = os.path.join(cwd, f)
            if os.path.exists(path):
                os.remove(path)
                deleted.append(f)

    if deleted:
        print(f"Deleted {len(deleted)} file(s) from {cwd}:")
        for f in sorted(deleted):
            print(f"  {f}")
    else:
        print("No peekdocs output files found in the current directory.")
    if not clear_all:
        print("\nTo also delete saved reports, error log, and index: peekdocs --clear-all")
    else:
        print("\nPreserved (not deleted): saved searches (.peekdocs_collection.json),")
        print("settings (~/.peekdocsrc), and bookmarks. Remove manually if needed.")
        print()
    return 0
