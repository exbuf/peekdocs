"""``peekdocs --runs`` — show recent run-log entries.

Reads the ndjson run log written after every non-``--no-log`` search
and renders either a human-readable table or the raw JSON Lines
(``--json`` flag), truncating to the last N entries (default 20).
"""
from __future__ import annotations

import json
import sys


def handle_runs(args: list[str]) -> int:
    """Handle ``peekdocs --runs [N] [--json]``.

    *args* is the full argv-after-``peekdocs`` list; the caller has
    already confirmed ``args[0] == "--runs"``.

    Returns ``0`` on success (including "no entries yet"), ``2`` if
    ``N`` isn't a valid integer.
    """
    from peekdocs.run_log import read_recent, log_path

    emit_json = "--json" in args[1:]
    limit = 20
    for tok in args[1:]:
        if tok == "--json":
            continue
        try:
            limit = max(0, int(tok))
            break
        except ValueError:
            print(f"Error: --runs argument must be a positive integer. Got: {tok}\n", file=sys.stderr)
            return 2

    entries = read_recent(limit=limit if limit > 0 else 0)
    if emit_json:
        for e in entries:
            sys.stdout.write(json.dumps(e, ensure_ascii=False) + "\n")
        return 0

    if not entries:
        print(f"No run log entries found. Log file: {log_path()}")
        print("(The log is written automatically after every search; use --no-log to skip a single run.)")
        return 0

    print(f"Run log: {log_path()}")
    print()
    print(f"{'Time':<19}  {'Exit':>4}  {'Matches':>8}  {'Files':>6}  {'Errors':>6}  {'Elapsed':>8}  Command")
    print(f"{'-'*19}  {'-'*4}  {'-'*8}  {'-'*6}  {'-'*6}  {'-'*8}  {'-'*40}")
    for e in entries:
        ts = (e.get("timestamp") or "")[:19]
        ec = e.get("exit_code", "")
        mc = e.get("match_count", 0)
        fc = e.get("file_count", 0)
        er = e.get("error_count", 0)
        el = e.get("elapsed_seconds", 0)
        cmd = " ".join(e.get("argv", []))
        if len(cmd) > 80:
            cmd = cmd[:77] + "..."
        print(f"{ts:<19}  {str(ec):>4}  {mc:>8}  {fc:>6}  {er:>6}  {el:>8.2f}  {cmd}")
    print()
    print(f"{len(entries)} run(s). --runs N for more, --runs --json for raw JSON Lines.")
    return 0
