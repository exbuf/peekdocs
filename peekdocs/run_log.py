"""Per-run structured log for peekdocs CLI invocations.

Each search-mode CLI invocation appends one JSON object (JSON Lines / NDJSON
format) to a per-user log file — by default ``~/.peekdocs_runs.log``. IT can
``tail -f`` it, grep across days of runs, or ship the file straight into
syslog / Splunk / Elastic via Filebeat or any other JSON-aware shipper.

Logged events:
  - Standard search (``peekdocs <terms>`` and any flag variant)
  - ``peekdocs --suite NAME``
  - ``peekdocs --regex-collection NAME``

Informational commands (``--help``, ``--version``, ``--check``, ``--list-*``,
``--clear*``, ``--index*``, ``--config``, ``--runs``) are NOT logged — the
log is for search activity only.

Defaults:
  - Enabled out of the box. Opt out per-run with ``--no-log`` or
    permanently with ``--config run_log=false`` (or
    ``--config run_log_path=`` to blank the path).
  - Path: ``~/.peekdocs_runs.log``. Override with
    ``--config run_log_path=/path/to/file`` — useful when IT wants to route
    into ``/var/log/peekdocs/`` or a tmpfs.

Each line is one self-contained JSON object so a malformed line never breaks
later ones, and ``tail | jq`` works without any aggregation step.
"""

import json
import os
import time
from datetime import datetime


DEFAULT_LOG_FILENAME = ".peekdocs_runs.log"

# Stats populated by each search code path before main() exits. Reset at the
# start of each run, read at the end. Module-level mutable state is the
# simplest way to thread these out of deep code paths without changing every
# function signature.
_RUN_STATS = {
    "match_count": 0,
    "file_count": 0,
    "error_count": 0,
    "report_paths": {},   # {"txt": "...", "docx": "...", "json": "...", ...}
}


def reset_stats():
    """Clear the run-stats slate at the start of a new invocation."""
    global _RUN_STATS
    _RUN_STATS = {
        "match_count": 0,
        "file_count": 0,
        "error_count": 0,
        "report_paths": {},
    }


def set_stats(match_count=None, file_count=None, error_count=None):
    """Populate one or more stat fields from a search code path.

    Each search mode calls this just before its final return so the
    main()-level logger can include accurate counts. Unspecified fields
    keep whatever value they already had (default zero).
    """
    if match_count is not None:
        _RUN_STATS["match_count"] = int(match_count)
    if file_count is not None:
        _RUN_STATS["file_count"] = int(file_count)
    if error_count is not None:
        _RUN_STATS["error_count"] = int(error_count)


def set_report_paths(**paths):
    """Record absolute paths of report files written this run.

    Keys (txt, docx, json, csv, pdf, html) are exposed as env vars
    (PEEKDOCS_REPORT_TXT, etc.) to any --on-match hook so the hook
    can mail/upload/process the report without having to compute the
    filename itself.
    """
    bucket = _RUN_STATS.setdefault("report_paths", {})
    for key, value in paths.items():
        if value:
            bucket[key] = value


def get_stats():
    """Return a copy of the current stats dict."""
    return dict(_RUN_STATS)


def _config_value(key, default=None):
    """Read a key from ~/.peekdocsrc without importing cli (avoids a cycle)."""
    rc_path = os.path.join(os.path.expanduser("~"), ".peekdocsrc")
    if not os.path.exists(rc_path):
        return default
    try:
        with open(rc_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" not in line or line.startswith("#"):
                    continue
                k, _, v = line.partition("=")
                if k.strip() == key:
                    return v.strip()
    except OSError:
        pass
    return default


def is_enabled():
    """True unless the user has explicitly disabled run logging."""
    val = _config_value("run_log")
    if val is not None and val.lower() in ("false", "0", "off", "no"):
        return False
    # An empty run_log_path is treated as opt-out as well.
    path = _config_value("run_log_path", "")
    if path is not None and path == "" and _config_value("run_log_path") is not None:
        # Key is present but empty — explicit opt-out.
        return False
    return True


def log_path():
    """Return the absolute path to the run log file."""
    path = _config_value("run_log_path")
    if path:
        return os.path.expanduser(path)
    return os.path.join(os.path.expanduser("~"), DEFAULT_LOG_FILENAME)


def record_run(argv, cwd, exit_code, elapsed_seconds,
               match_count=0, file_count=0, error_count=0,
               peekdocs_version=None, on_match_fired=None):
    """Append one JSON line to the run log. Silently no-ops on write failure.

    The log is best-effort observability — a write failure (disk full,
    permission denied, file locked on Windows) must never abort the
    user's search.
    """
    if peekdocs_version is None:
        try:
            from peekdocs.cli import VERSION
            peekdocs_version = VERSION
        except ImportError:
            peekdocs_version = "unknown"

    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "peekdocs_version": peekdocs_version,
        "argv": list(argv),
        "cwd": cwd,
        "exit_code": int(exit_code),
        "match_count": int(match_count),
        "file_count": int(file_count),
        "error_count": int(error_count),
        "elapsed_seconds": round(float(elapsed_seconds), 3),
    }
    # Only include the on-match outcome if --on-match was actually used
    # this run, so absent fields stay absent for normal searches.
    if on_match_fired is not None:
        entry["on_match_fired"] = bool(on_match_fired)

    try:
        path = log_path()
        # Append mode is atomic for small writes on Unix; on Windows it's
        # close-to-atomic for our line lengths. The trailing newline must
        # be inside the same write() call so a JSONL line is never split.
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        # Disk full, no write permission, etc. Don't crash the search.
        pass


def fire_on_match(command, argv, cwd, match_count, file_count, error_count,
                  elapsed_seconds, report_paths, timeout=30):
    """Run *command* as a subprocess with PEEKDOCS_* env vars set.

    Called by main() after a search finishes with matches (exit code 0).
    Splits *command* via shlex so quoted args work and there is no shell —
    no shell injection from user args, no implicit pipes/redirects.
    Returns True on success (hook exited 0 within timeout), False on any
    failure. Failures are non-fatal — the user's search succeeded; their
    hook script breaking shouldn't penalize the exit code.
    """
    import shlex
    import subprocess

    try:
        parts = shlex.split(command)
    except ValueError as exc:
        _log_hook_error(f"--on-match command could not be parsed: {exc}")
        return False
    if not parts:
        return False

    env = os.environ.copy()
    env["PEEKDOCS_EXIT_CODE"] = "0"
    env["PEEKDOCS_MATCH_COUNT"] = str(match_count)
    env["PEEKDOCS_FILE_COUNT"] = str(file_count)
    env["PEEKDOCS_ERROR_COUNT"] = str(error_count)
    env["PEEKDOCS_ELAPSED_SECONDS"] = f"{elapsed_seconds:.3f}"
    env["PEEKDOCS_ARGV"] = " ".join(argv) if argv else ""
    env["PEEKDOCS_CWD"] = cwd or ""
    for key, val in (report_paths or {}).items():
        env[f"PEEKDOCS_REPORT_{key.upper()}"] = val

    try:
        result = subprocess.run(
            parts,
            env=env,
            timeout=timeout,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        _log_hook_error(f"--on-match command not found: {parts[0]}")
        return False
    except subprocess.TimeoutExpired:
        _log_hook_error(
            f"--on-match command timed out after {timeout}s: {' '.join(parts)}"
        )
        return False
    except OSError as exc:
        _log_hook_error(f"--on-match command failed to launch: {exc}")
        return False

    if result.returncode != 0:
        _log_hook_error(
            f"--on-match command exited with code {result.returncode}: {' '.join(parts)}\n"
            f"  stdout: {result.stdout[:500] if result.stdout else '(empty)'}\n"
            f"  stderr: {result.stderr[:500] if result.stderr else '(empty)'}"
        )
        return False
    return True


def _log_hook_error(message):
    """Print a hook-related warning to stderr and append it to peekdocs_errors.log."""
    import sys
    sys.stderr.write(f"Warning: {message}\n")
    try:
        error_log = os.path.join(os.getcwd(), "peekdocs_errors.log")
        from datetime import datetime
        with open(error_log, "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now().isoformat(timespec='seconds')}] {message}\n")
    except OSError:
        pass


def read_recent(limit=20):
    """Return up to *limit* most-recent entries from the log, oldest first.

    Malformed lines are skipped silently. Returns [] if the log doesn't exist.
    """
    path = log_path()
    if not os.path.exists(path):
        return []
    entries = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return entries[-limit:] if limit > 0 else entries


# Commands that produce a logged entry. Everything else (--help, --version,
# --check, --list-*, --clear*, --index*, --config, --runs, etc.) is skipped.
_SEARCH_COMMAND_FLAGS = ("--suite", "--regex-collection")


def is_search_invocation(argv):
    """Decide whether this argv represents a search-mode run that should be logged."""
    if not argv:
        return False
    # Skip if any informational / non-search command flag is present in the
    # leading position. We use the same dispatch rule the CLI uses: the very
    # first arg determines the mode for non-positional commands.
    first = argv[0] if argv else ""
    _NOT_LOGGED = {
        "-h", "-help", "--help",
        "-v", "-version",
        "--check",
        "--list-files",
        "--list-suites",
        "--clear", "--clear-all",
        "--index", "--index-clear", "--index-status", "--index-refresh",
        "--config",
        "--runs",
        "--regex-collection-list",  # paranoia; --regex-collection --list is handled below
        "-s", "-save",
    }
    if first in _NOT_LOGGED:
        return False
    # `--regex-collection --list` is informational.
    if first == "--regex-collection" and len(argv) >= 2 and argv[1] == "--list":
        return False
    # Dry-run is preflight, not a search. Skip the log.
    if "--dry-run" in argv:
        return False
    return True
