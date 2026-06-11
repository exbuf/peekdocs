"""Folder-watcher mode for peekdocs.

Long-running mode that watches a folder via the watchdog library, re-runs a
named regex collection on every file create / modify / move event, and emits
one NDJSON line per match to stdout. The headline use case is real-time
pattern detection across the 100+ file types peekdocs supports:

    peekdocs --watch -d /path/to/folder --regex-collection NAME

Each match emits a single self-contained JSON record on its own line — the
standard "JSON Lines" / NDJSON shape that any log shipper (Filebeat, Vector,
Fluent Bit, Splunk Universal Forwarder, etc.) and any shell pipeline (`jq`,
`grep`, `awk`) consume natively:

    {
        "timestamp": "2026-06-11T14:23:18",
        "file": "/abs/path/to/notes.docx",
        "line": 12,
        "matched_text": "contact alice@example.com about the schedule",
        "pattern_name": "Email address",
        "pattern_regex": "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\\b",
        "collection": "Examples"
    }

## Design constraints

The watcher is a deliberate, late-arrived addition to peekdocs's surface, and
the constraints below are load-bearing — change them only with clear-eyed
reasoning, not as drive-by cleanup:

- **Default to stdout-only.** The watcher exists to *stream* matches into
  whatever pipeline the caller chooses, not to accumulate disk artifacts.
  No `peekdocs_*_results.*` files are written; the caller redirects stdout
  (`> matches.ndjson`, `| log-shipper`, `| jq …`) if they want persistence.
- **Refuse to run as root by default.** The dual-use concern is real: a
  privileged watcher can read content the operator may not be authorized
  to access (other users' home dirs, system config, etc.). Forcing the
  caller to opt in via `--allow-root` narrows the legitimate use case to
  callers who have thought about why root is needed.
- **Warn (don't refuse) on system-path or other-user-home targets.**
  Honest mis-clicks get a heads-up at startup; deliberate use is one
  `--allow-system-paths` flag away.
- **Reuse `api.search()` per-file** rather than re-implementing format
  extraction. This keeps the 100-format matrix consistent between the
  one-shot search path and the watcher path, and inherits the
  `(?-i:...)` case-intent + finditer-based highlighter fixes that the
  one-shot path already carries.
- **Clean Ctrl-C shutdown.** SIGINT/SIGTERM stop the observer thread,
  flush stdout, exit 0. No half-written NDJSON lines downstream.
- **Errors go to stderr, never to the NDJSON stream.** A consumer running
  `peekdocs --watch … | jq` must never see a non-JSON line on stdout, or
  the pipeline fails. Per-file extraction errors are logged to stderr
  and the watcher continues.

## Not implemented in v1, deliberately

- Debouncing of rapid same-file modify events (a save can fire multiple
  modifies on some platforms). Same line will appear in NDJSON twice;
  downstream consumers can dedupe by (file, line, matched_text).
- Backpressure / queueing if matches arrive faster than the consumer
  drains them. Pipe to a fast sink (file, log shipper) for now.
- Cloud-synced folder detection. Pointing the watcher at a OneDrive /
  Dropbox / iCloud folder will produce false events on hydration churn;
  document this in the user guide rather than try to filter heuristically.
"""

from __future__ import annotations

import json
import os
import signal
import sys
import time
from dataclasses import dataclass, field


# System-path prefixes that trigger a startup warning. Not exhaustive —
# representative enough that an honest mis-click ("did I really mean
# /etc?") gets a heads-up. Casing is normalized at compare time.
_SYSTEM_PATH_PREFIXES_UNIX = (
    "/etc", "/var", "/usr", "/bin", "/sbin",
    "/Library", "/System", "/private", "/tmp",
)
_SYSTEM_PATH_PREFIXES_WIN = (
    "c:\\windows",
    "c:\\program files",
    "c:\\program files (x86)",
    "c:\\programdata",
)


@dataclass
class WatcherConfig:
    folder: str
    patterns: list  # list of dicts: {"name": str, "regex": str, "enabled": bool|str}
    collection_name: str = ""
    recursive: bool = False
    allow_root: bool = False
    allow_system_paths: bool = False
    # Internal: a list to collect emitted record dicts for testing.
    # When None (default), records go to stdout as NDJSON. When set, the
    # records are appended to the list and stdout is left alone.
    _emit_sink: list | None = field(default=None, repr=False)


def _is_system_path(path: str) -> bool:
    """True if *path* looks like a system path we should warn about."""
    abs_path = os.path.abspath(path)
    if sys.platform.startswith("win"):
        norm = abs_path.lower()
        return any(norm.startswith(p) for p in _SYSTEM_PATH_PREFIXES_WIN)
    return any(
        abs_path == p or abs_path.startswith(p + os.sep)
        for p in _SYSTEM_PATH_PREFIXES_UNIX
    )


def _is_other_user_home(path: str) -> bool:
    """True if *path* looks like another user's home directory on Unix-like
    OSes. Windows home-directory layout is complex enough that this check
    just returns False there; the system-path warning catches the worst
    Windows mis-clicks (C:\\Users\\<other> is the closest analogue and
    isn't a system path)."""
    if sys.platform.startswith("win"):
        return False
    home = os.path.abspath(os.path.expanduser("~"))
    abs_path = os.path.abspath(path)
    for users_root in ("/Users", "/home"):
        if abs_path.startswith(users_root + os.sep) and not (
            abs_path == home or abs_path.startswith(home + os.sep)
        ):
            return True
    return False


def safety_checks(config: WatcherConfig) -> tuple[bool, list[str], list[str]]:
    """Validate the watcher's startup conditions.

    Returns (proceed, errors, warnings). `proceed` is False iff there's at
    least one error. Caller is responsible for emitting the messages to
    stderr — this function builds the lists and returns them so the same
    code path can be tested without capturing stderr.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Refuse to run as root by default
    if (not config.allow_root
            and hasattr(os, "geteuid")
            and os.geteuid() == 0):
        errors.append(
            "Refusing to run --watch as root. A privileged watcher can read "
            "files the operator may not be authorized to access. Re-run as "
            "a regular user, or pass --allow-root if you genuinely need it."
        )

    # Warn (don't refuse) on system paths
    if not config.allow_system_paths and _is_system_path(config.folder):
        warnings.append(
            f"The watch target '{config.folder}' looks like a system path. "
            "peekdocs will still run, but make sure this is what you "
            "intended. Pass --allow-system-paths to suppress this warning."
        )

    # Warn on another user's home directory
    if not config.allow_system_paths and _is_other_user_home(config.folder):
        warnings.append(
            f"The watch target '{config.folder}' looks like another user's "
            "home directory. On a shared machine, watching another user's "
            "files without their authorization can look like surveillance. "
            "Make sure you have permission."
        )

    # Folder must exist
    if not os.path.isdir(config.folder):
        errors.append(
            f"Folder does not exist or is not a directory: {config.folder}"
        )

    return (len(errors) == 0, errors, warnings)


def _enabled_patterns(patterns):
    """Filter the patterns list to entries that are both enabled and have
    a non-empty regex. Mirrors the GUI's filter logic so the watcher and
    the Save Collection As path agree on what 'enabled' means (the GUI
    can save with `enabled: "on"` or `enabled: true` depending on
    version; both are honored)."""
    result = []
    for p in patterns:
        v = p.get("enabled")
        if isinstance(v, bool):
            enabled = v
        elif isinstance(v, str):
            enabled = v.lower() in ("on", "true", "1", "yes")
        else:
            enabled = bool(v)
        if not enabled:
            continue
        if not (p.get("regex") or "").strip():
            continue
        result.append(p)
    return result


def _emit_match(config, file_path, line_num, matched_text, pattern_name,
                pattern_regex):
    """Emit a single NDJSON record. Goes to stdout in production; goes to
    config._emit_sink in tests."""
    record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "file": os.path.abspath(file_path),
        "line": line_num,
        "matched_text": matched_text,
        "pattern_name": pattern_name,
        "pattern_regex": pattern_regex,
        "collection": config.collection_name,
    }
    if config._emit_sink is not None:
        config._emit_sink.append(record)
        return
    sys.stdout.write(json.dumps(record, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def scan_file(config: WatcherConfig, file_path: str) -> None:
    """Run every enabled pattern in `config.patterns` against `file_path`
    via peekdocs's existing search engine. Emits one NDJSON record per
    match. Exceptions during extraction or matching are logged to stderr
    and swallowed so a single bad file doesn't take down the watcher.

    Public so tests can call it directly without spinning up a real
    watchdog observer.
    """
    from peekdocs.api import search as api_search

    if not os.path.isfile(file_path):
        # File may have been deleted between event firing and our scan,
        # or it's a special file (socket, FIFO). Skip silently.
        return

    folder = os.path.dirname(file_path) or "."
    filename = os.path.basename(file_path)

    for p in _enabled_patterns(config.patterns):
        regex = p["regex"].strip()
        pattern_name = (p.get("name") or "Pattern").strip()
        try:
            result = api_search(
                [regex],
                directory=folder,
                recursive=False,
                use_regex=True,
                use_index=False,
                file_names=[filename],
            )
        except Exception as exc:
            sys.stderr.write(
                f"watcher: error scanning {file_path!r} with pattern "
                f"{pattern_name!r}: {exc}\n"
            )
            sys.stderr.flush()
            continue

        for match in result.matches:
            if match.filename != filename:
                # Defensive: specific_files should restrict scope, but
                # if a future api change loosens it, we still only emit
                # the file we actually watched.
                continue
            _emit_match(
                config,
                file_path,
                match.line_num,
                match.text,
                pattern_name,
                regex,
            )


def run_watch(config: WatcherConfig) -> int:
    """Main entry point. Validates config, sets up the watchdog observer,
    runs until SIGINT / SIGTERM, returns a CLI-style exit code.

    Exit codes:
      0 = clean shutdown after Ctrl-C
      2 = configuration error (bad folder, no enabled patterns, missing
          watchdog dep, refused-root-without-flag)
    """
    proceed, errors, warnings = safety_checks(config)

    for w in warnings:
        sys.stderr.write(f"warning: {w}\n")
    if warnings:
        sys.stderr.flush()

    if not proceed:
        for e in errors:
            sys.stderr.write(f"error: {e}\n")
        sys.stderr.flush()
        return 2

    enabled = _enabled_patterns(config.patterns)
    if not enabled:
        sys.stderr.write(
            "error: no enabled patterns in the collection — nothing to watch "
            "for. Check the collection's contents in the GUI (Regex Search → "
            "Restore From Collection).\n"
        )
        sys.stderr.flush()
        return 2

    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        sys.stderr.write(
            "error: --watch requires the 'watchdog' library, which should "
            "have been installed alongside peekdocs. Reinstall with:\n"
            "  pipx install --force git+https://github.com/exbuf/peekdocs.git\n"
            "or pip install watchdog if running from a development checkout.\n"
        )
        sys.stderr.flush()
        return 2

    # Per-file debounce. A single file save fires both on_created and
    # on_modified on most platforms, and macOS FSEvents in particular
    # likes to coalesce / replay events on a short delay. Without this,
    # one save emits every match 2-3x. _DEBOUNCE_SEC is a per-path
    # cooldown — within the window we silently skip re-scans.
    _last_scan: dict[str, float] = {}
    _DEBOUNCE_SEC = 0.5

    def _maybe_scan(path):
        now = time.monotonic()
        prev = _last_scan.get(path, 0.0)
        if now - prev < _DEBOUNCE_SEC:
            return
        _last_scan[path] = now
        scan_file(config, path)

    # Handler closes over `config` so scan_file picks up the same patterns
    # and emit-sink. Each event triggers a scan synchronously on the
    # observer's dispatch thread — no queue. The performance assumption is
    # "regex collection over a single file is fast enough not to back up
    # the event stream on realistic workloads"; if that stops being true
    # we add a bounded queue + worker thread here.
    class _Handler(FileSystemEventHandler):
        def on_created(self, event):
            if not event.is_directory:
                _maybe_scan(event.src_path)

        def on_modified(self, event):
            if not event.is_directory:
                _maybe_scan(event.src_path)

        def on_moved(self, event):
            # Moves with a destination inside the watched tree are
            # effectively a create. Moves out-of-tree are silently
            # dropped — the file is gone from our perspective.
            if not event.is_directory and getattr(event, "dest_path", None):
                _maybe_scan(event.dest_path)

    observer = Observer()
    observer.schedule(_Handler(), config.folder, recursive=config.recursive)
    observer.start()

    sys.stderr.write(
        f"peekdocs --watch active on {os.path.abspath(config.folder)} "
        f"({len(enabled)} pattern(s)"
        + (f" from collection '{config.collection_name}'"
           if config.collection_name else "")
        + f"). Recursive: {config.recursive}. "
        f"Press Ctrl-C to stop.\n"
    )
    sys.stderr.flush()

    # Stop on SIGINT or SIGTERM. Observer.stop() is idempotent; the join
    # below picks up the stopped state and returns cleanly.
    def _shutdown(signum, frame):
        observer.stop()

    signal.signal(signal.SIGINT, _shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _shutdown)

    try:
        # observer.join() blocks until observer.stop() is called. The
        # KeyboardInterrupt catch is a belt-and-braces fallback for
        # platforms where the signal handler doesn't unblock the join.
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
        observer.join()

    sys.stderr.write("peekdocs --watch stopped.\n")
    sys.stderr.flush()
    return 0
