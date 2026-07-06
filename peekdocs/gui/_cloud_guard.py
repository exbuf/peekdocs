"""Cloud-synced folder detection + policy for report output.

Splitting concern from the former `gui/_helpers.py` grab-bag. Every
report-write site (Standard / Suite / Regex Search across CLI, GUI,
and Python API) routes through :func:`cloud_output_guard` before any
write. GUI callers additionally use :func:`gui_cloud_guard` for the
interactive modal path.

Companion doc: README's *Auditor bullet* + USER_GUIDE's *Cloud-synced
folder policy* — this module is the enforcement point for the
"peekdocs won't silently upload your reports" claim.
"""
from __future__ import annotations

import os
import platform


def check_cloud_folder(path):
    """Return a warning string if *path* is inside a known cloud-sync
    folder (OneDrive, Google Drive, iCloud Drive, Dropbox).  Returns
    ``None`` if the path appears safe.

    Call this before writing report files so the user can choose a
    different output directory.
    """
    if not path:
        return None

    resolved = os.path.realpath(os.path.expanduser(path))
    norm = resolved.replace("\\", "/").lower()
    system = platform.system()

    # Patterns that indicate cloud-synced folders.
    # Checked against the lowercase, forward-slash-normalised path.
    cloud_indicators = [
        # OneDrive
        "/onedrive",
        "/onedrive - ",
        # Google Drive
        "/google drive/",
        "/googledrive/",
        "/my drive/",
        # iCloud Drive (macOS)
        "/library/mobile documents/",
        "/icloud drive/",
        # Dropbox
        "/dropbox/",
        "/dropbox (", # Dropbox Business uses "Dropbox (Company Name)"
    ]

    # Windows-specific: OneDrive env var may point anywhere.
    if system == "Windows":
        for env_var in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
            od = os.environ.get(env_var, "")
            if od:
                od_norm = os.path.realpath(od).replace("\\", "/").lower()
                if norm.startswith(od_norm):
                    return _cloud_folder_warning("OneDrive", path)

    for indicator in cloud_indicators:
        if indicator in norm:
            # Determine which service for the message.
            ind_lower = indicator.strip("/").split("/")[0].split(" (")[0]
            if "onedrive" in ind_lower:
                service = "OneDrive"
            elif "google" in ind_lower or "my drive" in indicator:
                service = "Google Drive"
            elif "mobile documents" in indicator or "icloud" in ind_lower:
                service = "iCloud Drive"
            elif "dropbox" in ind_lower:
                service = "Dropbox"
            else:
                service = ind_lower.title()
            return _cloud_folder_warning(service, path)

    return None


def _cloud_folder_warning(service, path):
    """Build the user-facing warning for a cloud-synced output folder."""
    return (
        f"Your output folder is inside {service}:\n"
        f"{path}\n\n"
        f"peekdocs will not write report files to cloud-synced folders "
        f"because they are automatically uploaded, which could expose "
        f"your search results to anyone with access to the cloud account.\n\n"
        f"Would you like peekdocs to save reports to a safe local "
        f"folder instead? Your documents will still be searched — "
        f"only the report output location changes."
    )


def detect_cloud_service(path):
    """Return the cloud-sync service name for *path*, or None if not cloud.

    Companion to :func:`check_cloud_folder` — same detection logic but
    returns a structured string ("iCloud Drive" / "OneDrive" / "Google
    Drive" / "Dropbox") suitable for programmatic policy decisions and
    building CLI-vs-GUI-specific messages, rather than a pre-formatted
    warning paragraph.

    Used by the cloud-output guard at every report-write site so that
    peekdocs's "no-cloud confidentiality" claim (README auditor bullet
    + USER_GUIDE) is enforced at write time, not just at search-folder
    detection time.
    """
    if not path:
        return None
    resolved = os.path.realpath(os.path.expanduser(path))
    norm = resolved.replace("\\", "/").lower()
    system = platform.system()

    if system == "Windows":
        for env_var in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
            od = os.environ.get(env_var, "")
            if od:
                od_norm = os.path.realpath(od).replace("\\", "/").lower()
                if norm.startswith(od_norm):
                    return "OneDrive"

    indicators = [
        ("onedrive", "OneDrive"),
        ("google drive", "Google Drive"),
        ("googledrive", "Google Drive"),
        ("my drive/", "Google Drive"),
        ("library/mobile documents/", "iCloud Drive"),
        ("icloud drive/", "iCloud Drive"),
        ("dropbox/", "Dropbox"),
        ("dropbox (", "Dropbox"),
    ]
    for needle, service in indicators:
        if needle in norm:
            return service
    return None


def get_safe_output_dir():
    """Return a safe local directory for report output.

    Creates ~/peekdocs_reports if it doesn't exist. This folder is
    outside any cloud-synced directory on standard configurations.
    """
    safe_dir = os.path.join(os.path.expanduser("~"), "peekdocs_reports")
    os.makedirs(safe_dir, exist_ok=True)
    # Verify the safe dir itself isn't cloud-synced
    if check_cloud_folder(safe_dir) is not None:
        # Home dir is synced — fall back to system temp
        import tempfile
        safe_dir = os.path.join(tempfile.gettempdir(), "peekdocs_reports")
        os.makedirs(safe_dir, exist_ok=True)
    return safe_dir


# Sentinel outcomes returned by cloud_output_guard.
CLOUD_GUARD_SAFE = "safe"              # not cloud-synced; proceed
CLOUD_GUARD_REDIRECTED = "redirected"  # cloud-synced, redirected to safe dir per config
CLOUD_GUARD_ALLOWED = "allowed"        # cloud-synced, explicitly allowed via CLI flag or GUI choice
CLOUD_GUARD_PROMPT = "prompt"          # cloud-synced, no policy set — caller must ask user
CLOUD_GUARD_BLOCKED = "blocked"        # cloud-synced, no policy and no interactive path — abort


def gui_cloud_guard(parent, output_dir, redirect_to_safe=False):
    """GUI-side cloud-output guard with an interactive modal for the
    PROMPT case.

    Wraps :func:`cloud_output_guard` so GUI callers get back a resolved
    directory (or None if the user cancels). The modal offers three
    choices when a cloud-synced output_dir is detected and no policy
    is set:

      • Redirect to ~/peekdocs_reports (safe local folder)
      • Write here anyway (proceed with cloud upload)
      • Cancel the search

    Returns ``(final_dir, decision)`` where ``decision`` is one of the
    CLOUD_GUARD_* sentinels above, or ``(None, "cancelled")`` if the
    user chose Cancel.
    """
    final_dir, outcome, service = cloud_output_guard(
        output_dir, redirect_to_safe=redirect_to_safe, allow_cloud=False,
    )
    if outcome != CLOUD_GUARD_PROMPT:
        return (final_dir, outcome)

    # Interactive modal — build a tk.Toplevel with three buttons and
    # block until the user picks.
    import tkinter as tk

    safe_alt = get_safe_output_dir()
    choice = {"value": None}
    win = tk.Toplevel(parent)
    win.title("Cloud-synced output folder detected")
    win.transient(parent)
    win.resizable(False, False)
    try:
        win.grab_set()
    except tk.TclError:
        pass

    msg = (
        f"Your output folder is inside {service}:\n\n"
        f"    {output_dir}\n\n"
        f"Reports written there will be uploaded to {service}, which "
        f"could expose your search results to anyone with access to "
        f"the account.\n\n"
        f"How would you like to proceed?"
    )
    tk.Label(win, text=msg, wraplength=520, justify="left",
             font=("TkDefaultFont", 12), padx=20, pady=15).pack()

    btn_row = tk.Frame(win)
    btn_row.pack(pady=(0, 15))

    def _pick(v):
        choice["value"] = v
        win.destroy()

    tk.Button(
        btn_row, text=f"Redirect to {safe_alt}", width=32,
        command=lambda: _pick("redirect"),
    ).pack(side="left", padx=6)
    tk.Button(
        btn_row, text="Write here anyway", width=20,
        command=lambda: _pick("allow"),
    ).pack(side="left", padx=6)
    tk.Button(
        btn_row, text="Cancel", width=12,
        command=lambda: _pick("cancel"),
    ).pack(side="left", padx=6)

    win.protocol("WM_DELETE_WINDOW", lambda: _pick("cancel"))
    win.update_idletasks()
    # Center on parent
    try:
        px = parent.winfo_rootx() + (parent.winfo_width() - win.winfo_reqwidth()) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - win.winfo_reqheight()) // 2
        win.geometry(f"+{max(px, 0)}+{max(py, 0)}")
    except tk.TclError:
        pass
    parent.wait_window(win)

    if choice["value"] == "redirect":
        return (safe_alt, CLOUD_GUARD_REDIRECTED)
    if choice["value"] == "allow":
        return (output_dir, CLOUD_GUARD_ALLOWED)
    return (None, "cancelled")


def cloud_output_guard(output_dir, redirect_to_safe=False, allow_cloud=False):
    """Central policy decision for report-write paths.

    Every report-write site (Standard / Suite / Regex Search across
    CLI, GUI, and Python API) calls this once before any write. The
    outcome tells the caller how to proceed.

    Args:
        output_dir: the intended output directory (where the reports
            would land absent this guard).
        redirect_to_safe: True if the user has opted into the sticky
            'Redirect cloud-synced output paths to safe folder' setting
            (Advanced Search Options checkbox, saved as
            ``redirect_cloud_output`` in ``~/.peekdocsrc``).
        allow_cloud: True if the caller has explicit permission to
            write to a cloud-synced path — CLI ``--allow-cloud-output``
            flag, or the GUI modal's 'Write here anyway' button.

    Returns:
        (final_dir, outcome, service_name):

          final_dir     — the directory the caller should actually
                          write reports into (may be a redirected path)
          outcome       — one of the CLOUD_GUARD_* sentinels above
          service_name  — the cloud service detected (e.g. "iCloud
                          Drive") or None if outcome is SAFE

    Policy resolution:
      1. If output_dir is not cloud-synced → (output_dir, SAFE, None)
      2. If cloud AND redirect_to_safe    → (safe_dir, REDIRECTED, service)
      3. If cloud AND allow_cloud         → (output_dir, ALLOWED, service)
      4. If cloud AND neither             → (output_dir, PROMPT, service)
                                             (caller shows modal / asks user)
    """
    service = detect_cloud_service(output_dir)
    if service is None:
        return (output_dir, CLOUD_GUARD_SAFE, None)
    if redirect_to_safe:
        return (get_safe_output_dir(), CLOUD_GUARD_REDIRECTED, service)
    if allow_cloud:
        return (output_dir, CLOUD_GUARD_ALLOWED, service)
    return (output_dir, CLOUD_GUARD_PROMPT, service)
