"""``peekdocs --list-suites`` — global suite index dump.

Reads the ~/.peekdocs_suites_index.json cache and prints a table of
every named search suite peekdocs knows about, across all folders.
With ``--rescan`` in args, rebuilds the index before printing.
"""
from __future__ import annotations


def handle_list_suites(args: list[str]) -> int:
    """Handle ``peekdocs --list-suites [--rescan]``.

    *args* is the full argv-after-``peekdocs`` list; the caller has
    already confirmed ``args[0] == "--list-suites"``.

    Returns ``0`` on success (including "no suites found" — that's an
    empty index, not an error).
    """
    from peekdocs.suite_index import list_suites_global, rescan

    if "--rescan" in args[1:]:
        rescan()

    entries = list_suites_global()
    if not entries:
        print("No suites found.")
        print()
        print("Create one in the GUI (Tools → Search Suites), or run a search")
        print("first so peekdocs learns which folders to look in.")
        return 0

    name_w = max(len(e["name"]) for e in entries)
    name_w = max(name_w, len("Suite"))
    print(f"{'Suite'.ljust(name_w)}  Searches  Folder")
    print(f"{'-' * name_w}  --------  ------")
    for e in entries:
        print(f"{e['name'].ljust(name_w)}  {str(e['search_count']).rjust(8)}  {e['folder']}")
    print()
    print(f"{len(entries)} suite(s).  Run with:  peekdocs --suite \"<name>\"")
    return 0
