"""
Cross-platform desktop notification for peekdocs.

Best-effort, dependency-free, fire-and-forget. Never raises; returns
``None`` on success or a short error string on failure. Callers are
expected to swallow failures silently — desktop notifications are
nice-to-have polish, not load-bearing functionality.

Platform mechanisms:
  - macOS:    ``terminal-notifier`` (preferred — Homebrew install,
              first-class Cocoa app with its own notification
              identity), falling back to ``osascript`` AppleScript
              ``display notification`` if terminal-notifier isn't
              installed. The osascript path is unreliable on macOS
              Sequoia (15+) because notifications are attributed to
              Script Editor and silently dropped unless that app has
              been explicitly approved in System Settings →
              Notifications.
  - Linux:    ``notify-send`` from ``libnotify-bin`` (pre-installed on
              most GNOME / KDE / XFCE desktops).
  - Windows:  PowerShell + ``System.Windows.Forms.NotifyIcon`` balloon
              (works on Windows 10 / 11 without third-party modules
              like BurntToast).

The subprocess is always spawned fire-and-forget — we do not block the
caller waiting for the notification to dismiss.
"""

import shutil
import subprocess
import sys

_MAX_LEN = 240


def desktop_notify(title: str, body: str, timeout_seconds: int = 5):
    """Fire a system desktop notification.

    Args:
        title: Short headline.
        body: One- to three-line body text.
        timeout_seconds: Best-effort display duration. Honored on Linux;
            macOS Notification Center decides on its own; Windows balloon
            uses this as the lifetime of the PowerShell-spawned tray icon.

    Returns:
        ``None`` on success, or a short string describing the failure.
        The caller may log but should not surface failures to the user.
    """
    title = _scrub(title)
    body = _scrub(body)
    try:
        if sys.platform == "darwin":
            return _notify_macos(title, body)
        if sys.platform.startswith("linux"):
            return _notify_linux(title, body, timeout_seconds)
        if sys.platform.startswith("win"):
            return _notify_windows(title, body, timeout_seconds)
        return f"unsupported platform: {sys.platform}"
    except Exception as e:
        return f"notification failed: {e}"


def _scrub(s):
    s = (s or "").replace("\r", " ").replace("\x00", "")
    if len(s) > _MAX_LEN:
        s = s[: _MAX_LEN - 3] + "..."
    return s


def _spawn(cmd, hide_window=False):
    """Fire-and-forget subprocess. Discard I/O; do not wait."""
    kwargs = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "close_fds": True,
    }
    if hide_window:
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    subprocess.Popen(cmd, **kwargs)


def _notify_macos(title, body):
    # Preferred path: terminal-notifier. It's a real Cocoa app with
    # its own bundle ID, properly registered for notification
    # permissions on modern macOS — unlike osascript, which is
    # attributed to Script Editor and silently dropped on Sequoia
    # (15+) when Script Editor hasn't been explicitly approved.
    # Install: `brew install terminal-notifier`. `-group` collapses
    # repeated completion notifications into the most recent one so
    # they don't pile up in Notification Center after a long session.
    if shutil.which("terminal-notifier"):
        _spawn([
            "terminal-notifier",
            "-title", title,
            "-message", body,
            "-sound", "default",
            "-group", "com.peekdocs.search-complete",
        ])
        return None
    # Fallback: osascript. Less reliable but works when the user
    # hasn't installed terminal-notifier.
    safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
    safe_body = body.replace("\\", "\\\\").replace('"', '\\"')
    script = (
        f'display notification "{safe_body}" with title "{safe_title}"'
    )
    _spawn(["osascript", "-e", script])
    return None


def _notify_linux(title, body, timeout_seconds):
    if not shutil.which("notify-send"):
        return "notify-send not installed (apt-get install libnotify-bin)"
    _spawn([
        "notify-send",
        "--expire-time", str(timeout_seconds * 1000),
        "--app-name", "peekdocs",
        title, body,
    ])
    return None


def _notify_windows(title, body, timeout_seconds):
    if not shutil.which("powershell"):
        return "powershell not available"
    # PowerShell single-quoted strings escape ' as ''. Doing the same
    # for both title and body so embedded quotes can't break the
    # script. timeout_seconds is bounded so the spawned tray icon
    # lives just long enough to show the balloon, then disposes.
    safe_title = title.replace("'", "''")
    safe_body = body.replace("'", "''")
    lifetime_ms = max(1000, timeout_seconds * 1000)
    ps_script = (
        "[reflection.assembly]::loadwithpartialname('System.Windows.Forms') | Out-Null;"
        "[reflection.assembly]::loadwithpartialname('System.Drawing') | Out-Null;"
        "$notify = New-Object System.Windows.Forms.NotifyIcon;"
        "$notify.Icon = [System.Drawing.SystemIcons]::Information;"
        "$notify.Visible = $true;"
        f"$notify.ShowBalloonTip({lifetime_ms}, '{safe_title}', '{safe_body}', "
        "[System.Windows.Forms.ToolTipIcon]::Info);"
        f"Start-Sleep -Milliseconds {lifetime_ms};"
        "$notify.Dispose();"
    )
    _spawn(
        ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script],
        hide_window=True,
    )
    return None
