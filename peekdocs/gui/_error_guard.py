"""Context managers for controlled exception swallowing in the GUI.

The GUI mixins used to be dense with ``except Exception: pass`` — real
defensive Tk guards (widget-destroyed races, focus timing) mixed
indistinguishably with silent bug swallowers. When something broke,
the user saw "nothing happened" and the maintainer got no signal.

The two context managers below let the caller communicate intent:

* :func:`gui_guard` — expected-but-worth-logging failure. Swallows the
  exception AND appends a line to ``peekdocs_errors.log`` with the
  operation name and stack location. Use for config writes, file
  operations, and best-effort widget updates where a persistent
  problem would matter but a single occurrence shouldn't crash the UI.

* :func:`gui_race_guard` — known-race silent failure. Swallows without
  logging. Use only for Tk timing races (``grab_set`` on
  not-yet-viewable window, ``focus_set`` on destroyed widget) where
  a companion retry pattern (``self.after(150, ...)``) handles
  correctness and logging would be pure noise.

Migration pattern for the existing ~149 bare ``except Exception: pass``
sites across the mixins is one-at-a-time by category; see
docs/ARCHITECTURE.md's *Known weaknesses* list.
"""
from __future__ import annotations

import contextlib
import os
import sys
import traceback
from datetime import datetime
from typing import Iterator


def _log_swallow(operation: str, exc: BaseException) -> None:
    """Append a swallowed-exception line to ``peekdocs_errors.log``.

    Best-effort — if the log write itself fails (read-only cwd, no
    disk space) we don't cascade. That's fine: this is diagnostic
    telemetry, not primary error handling.
    """
    try:
        error_log_path = os.path.join(os.getcwd(), "peekdocs_errors.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(error_log_path, "a", encoding="utf-8") as log_f:
            log_f.write(
                f"[{timestamp}] gui_guard swallowed: {operation} — "
                f"{type(exc).__name__}: {exc}\n"
            )
            # One-line traceback tail — the deepest frame is usually
            # the load-bearing one.
            tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
            for line in tb[-3:]:  # last 3 lines = deepest frame + msg
                log_f.write(f"    {line.rstrip()}\n")
    except Exception:
        # Log-write failure. Nothing to do.
        pass


@contextlib.contextmanager
def gui_guard(operation: str) -> Iterator[None]:
    """Swallow exceptions from a GUI operation, logging what happened.

    Replaces the ambient ``except Exception: pass`` pattern in GUI
    mixins where a persistent failure would matter but a single
    occurrence shouldn't crash the UI. The user-visible behavior is
    unchanged from the raw pattern — the exception is still swallowed
    — but the maintainer's error log now shows what got swallowed and
    where.

    Parameters
    ----------
    operation :
        Short human-readable description of what was attempted, used
        as the log-line prefix. Examples: ``"save config"``,
        ``"remove stale rc"``, ``"restore theme"``. Keep specific
        enough to grep for.

    Example::

        with gui_guard("save config"):
            _save_config(cfg)

    is equivalent to::

        try:
            _save_config(cfg)
        except Exception:
            pass

    plus a line in ``peekdocs_errors.log`` if it does fail.
    """
    try:
        yield
    except Exception as exc:
        _log_swallow(operation, exc)


@contextlib.contextmanager
def gui_race_guard() -> Iterator[None]:
    """Swallow known-race exceptions silently without logging.

    Use only for Tk timing races where the exception is *expected*
    and a companion retry pattern (``self.after(150, ...)``) handles
    correctness. Logging every occurrence would drown the error log
    in noise.

    Example — the canonical Tk grab-race pattern::

        try:
            win.grab_set()
        except Exception:
            win.after(150, lambda: win.grab_set() if win.winfo_exists() else None)

    stays the same shape but reads more intentional as::

        with gui_race_guard():
            win.grab_set()
        # ... plus the after() retry as before

    Prefer :func:`gui_guard` unless the exception is genuinely
    expected and the operation genuinely retries — silent swallowing
    is the pattern we're moving away from.
    """
    try:
        yield
    except Exception:
        pass
