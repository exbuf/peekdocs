"""Graphical interface for PeekDocs."""

import os
import platform
import re
import shlex
import subprocess
import sys


def _run_peekdocs_cli(cmd, folder, env=None, on_process_started=None, on_stderr_line=None):
    """Run a peekdocs CLI command and return ``(stdout, stderr, returncode)``.

    ``on_process_started`` is an optional callback invoked with the
    live ``subprocess.Popen`` object immediately after spawn on the
    subprocess path — the caller can stash it (``self.process = proc``)
    so a Cancel button can ``proc.terminate()`` mid-flight. Ignored on
    the in-process (PyInstaller) path because there's no subprocess to
    expose. Exceptions raised by the callback are swallowed so a buggy
    caller can't break the search.

    Two paths, chosen by ``sys.frozen``:

    * **Normal pip / pipx install** — spawn a subprocess via the cmd list
      (typically ``[sys.executable, "-m", "peekdocs", "-q", ...flags...]``).
      stdout / stderr are captured through pipes, env is the inherited
      environment with UTF-8 encoding forced.

    * **PyInstaller-bundled standalone exe** — call
      ``peekdocs.cli.main()`` directly, in-process, with stdout / stderr
      redirected to string buffers. The first three elements of ``cmd``
      (``[sys.executable, "-m", "peekdocs"]``) are stripped — they're
      meaningless inside the bundle because ``sys.executable`` IS the
      GUI exe. Re-launching it via subprocess just opens another GUI
      window (which is exactly the bug that prompted this helper); the
      in-process call sidesteps that entirely.

    Notes:

    * Cancellation only works on the subprocess path. In frozen mode the
      caller cannot kill an in-flight search; the GUI's Cancel button
      becomes a no-op for the duration of the search. Acceptable
      trade-off for the standalone build's first release.
    * Working directory is restored on the way out even if the CLI
      raises.
    * SystemExit from the CLI is caught and converted to a return code.
    """
    if getattr(sys, "frozen", False):
        # PyInstaller bundle: run in-process. The CLI module already
        # accepts an argv list and returns an exit code.
        import io
        import contextlib
        from peekdocs.cli import main as _cli_main

        cli_argv = list(cmd[3:])  # drop [sys.executable, "-m", "peekdocs"]
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        old_cwd = os.getcwd()
        rc = 0
        try:
            os.chdir(folder)
            with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
                try:
                    rc = _cli_main(cli_argv)
                except SystemExit as e:
                    rc = e.code if isinstance(e.code, int) else 0
                except Exception:
                    # Surface any exception in stderr so the GUI's
                    # existing "show stderr if stdout is empty" path
                    # picks it up.
                    import traceback as _tb
                    _tb.print_exc()
                    rc = 2
        finally:
            try:
                os.chdir(old_cwd)
            except Exception:
                pass
        return buf_out.getvalue(), buf_err.getvalue(), int(rc or 0)

    # Normal pip / pipx install: subprocess path.
    if env is None:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
    proc = subprocess.Popen(
        cmd, cwd=folder,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace", env=env,
    )
    if on_process_started is not None:
        try:
            on_process_started(proc)
        except Exception:
            pass
    if on_stderr_line is None:
        stdout, stderr = proc.communicate()
        return stdout, stderr, proc.returncode

    # Streaming mode: read stderr line-by-line in a background thread
    # so the caller can react to phase markers (e.g. 'PHASE: writing-docx')
    # while the subprocess is still running. stdout is collected
    # synchronously via proc.stdout.read() at the end. Exceptions in
    # the callback are swallowed so a buggy caller can't deadlock the
    # subprocess.
    import threading as _threading
    stderr_buf = []

    def _stderr_reader():
        try:
            for raw_line in proc.stderr:
                stderr_buf.append(raw_line)
                line = raw_line.rstrip("\r\n")
                try:
                    on_stderr_line(line)
                except Exception:
                    pass
        except Exception:
            pass

    t = _threading.Thread(target=_stderr_reader, daemon=True)
    t.start()
    stdout = proc.stdout.read() if proc.stdout else ""
    proc.wait()
    t.join(timeout=2.0)
    return stdout, "".join(stderr_buf), proc.returncode


def themed_ask_string(parent, title, prompt, initial=""):
    """Modal text-input dialog centered over *parent*.

    Replacement for ``tkinter.simpledialog.askstring`` that uses
    ``CTkToplevel`` plus manual centering so the popup reliably appears
    over the parent window. ``simpledialog.askstring`` on macOS can
    position the dialog far from the parent (or near a screen edge),
    depending on Tk version and HiDPI scaling — observed in practice
    with the Save Collection As dialog appearing partly off-screen.

    Returns the entered string (an empty string is a valid result), or
    ``None`` if the user cancelled / closed the dialog.
    """
    import customtkinter as ctk
    import tkinter as tk

    parent.update_idletasks()
    w, h = 380, 160
    result = [None]

    win = ctk.CTkToplevel(parent)
    win.title(title)
    win.geometry(f"{w}x{h}")
    win.resizable(False, False)

    # Center on parent (manually — no reliance on Tk's positioning).
    px = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
    py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
    win.geometry(f"+{px}+{py}")
    win.transient(parent)

    # X11 / Linux: grab_set fails on a not-yet-viewable window. Wait
    # for visibility, then grab as best-effort.
    win.update_idletasks()
    try:
        win.wait_visibility()
    except tk.TclError:
        pass
    try:
        win.grab_set()
    except tk.TclError:
        pass

    ctk.CTkLabel(win, text=prompt, font=ctk.CTkFont(size=12)).pack(
        padx=15, pady=(15, 5), anchor="w")
    entry = ctk.CTkEntry(win, font=ctk.CTkFont(size=12))
    entry.pack(padx=15, fill="x")
    if initial:
        entry.insert(0, initial)
    entry.focus_set()

    def _ok(_event=None):
        result[0] = entry.get()
        win.destroy()

    def _cancel(_event=None):
        result[0] = None
        win.destroy()

    btn_row = tk.Frame(win)
    btn_row.pack(side="bottom", pady=(0, 12))
    ctk.CTkButton(btn_row, text="OK", width=80,
                  font=ctk.CTkFont(size=12),
                  command=_ok).pack(side="left", padx=4)
    ctk.CTkButton(btn_row, text="Cancel", width=80,
                  font=ctk.CTkFont(size=12),
                  fg_color="transparent", text_color=("gray30", "gray70"),
                  hover_color=("gray90", "gray25"),
                  command=_cancel).pack(side="left", padx=4)

    entry.bind("<Return>", _ok)
    entry.bind("<Escape>", _cancel)
    win.protocol("WM_DELETE_WINDOW", _cancel)

    # Bring to front and focus the entry on first render.
    win.lift()
    win.focus_force()
    entry.focus_set()

    parent.wait_window(win)
    return result[0]


def safe_open_file(filepath):
    """Open *filepath* with the OS default handler for its extension.

    Always returns ``None``. The return value exists for backwards
    compatibility with callers that historically displayed a warning
    string when the open failed; today the OS surfaces its own error
    if no handler is registered.
    """
    system = platform.system()
    if system == "Windows":
        os.startfile(filepath)  # type: ignore[attr-defined]
    elif system == "Darwin":
        subprocess.Popen(["open", filepath])
    else:
        subprocess.Popen(["xdg-open", filepath])
    return None


# ── Cloud-synced folder detection ──────────────────────────────────────

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


def _build_command_from_values(
    search_text,
    folder,
    and_mode,
    recursive,
    fuzzy,
    wildcard,
    ocr,
    regex,
    exclude,
    file_types,
    proximity,
    context_before,
    context_after,
    cores="",
    specific_files="",
    append_name="",
    output_docx=False,
    output_csv=False,
    output_json=False,
    output_pdf=False,
    output_html=False,
    index_search=False,
    inverse=False,
    expression=False,
    whole_word=False,
    max_matches="",
    max_file_size_mb="",
    timestamp_suffix="",
    output_dir="",
    range_filters="",
):
    """Build a peekdocs CLI command list from GUI values.

    Returns None on validation error, or "FLAGS_IN_SEARCH" if flags are
    detected in the search text.
    """
    if not search_text.strip() and not range_filters.strip():
        return None

    if not folder or not os.path.isdir(folder):
        return None

    # Block flags typed into the search box
    _CLI_FLAGS = {"-a", "-A", "-B", "-c", "-e", "-f", "-h", "-m", "-n", "-o", "-O", "-p", "-q", "-r", "-R", "-s", "-sa", "-t", "-v", "-w", "-W", "-x", "-z", "--config", "--inverse", "--range", "--timestamp", "--ts-suffix", "--output-dir"}
    if not expression:
        tokens = search_text.strip().split()
        if any(token in _CLI_FLAGS for token in tokens):
            return "FLAGS_IN_SEARCH"

    cmd = [sys.executable, "-m", "peekdocs", "-q"]

    if not index_search:
        cmd.append("--no-index")

    # DOCX is opt-in via -o docx as of peekdocs 1.2.6 (the CLI default
    # is now TXT-only). Plumbed below alongside csv/json/pdf/html.

    if expression:
        cmd.append("-e")
        cmd.append(search_text.strip())
    if not expression and and_mode:
        cmd.append("-a")
    if recursive:
        cmd.append("-r")
    if fuzzy:
        cmd.append("-z")
    if wildcard:
        cmd.append("-w")
    if ocr:
        cmd.append("-O")
    if regex:
        cmd.append("-x")
    if whole_word:
        cmd.append("-W")
    if inverse:
        cmd.append("--inverse")

    if not expression and exclude.strip():
        cmd.extend(["-n", exclude.strip()])

    if file_types.strip():
        cmd.extend(["-t", file_types.strip()])

    if not expression and proximity.strip():
        if not proximity.strip().isdigit() or int(proximity.strip()) < 1:
            return None
        cmd.extend(["-p", proximity.strip()])

    if context_before.strip():
        if not context_before.strip().isdigit():
            return None
        cmd.extend(["-B", context_before.strip()])

    if context_after.strip():
        if not context_after.strip().isdigit():
            return None
        cmd.extend(["-A", context_after.strip()])

    if cores.strip():
        if not cores.strip().isdigit() or int(cores.strip()) < 1:
            return None
        cmd.extend(["-c", cores.strip()])

    if specific_files.strip():
        cmd.extend(["-f", specific_files.strip()])

    if append_name.strip():
        cmd.extend(["-sa", append_name.strip()])

    output_parts = []
    if output_docx:
        output_parts.append("docx")
    if output_csv:
        output_parts.append("csv")
    if output_json:
        output_parts.append("json")
    if output_pdf:
        output_parts.append("pdf")
    if output_html:
        output_parts.append("html")
    if output_parts:
        cmd.extend(["-o", ",".join(output_parts)])

    mm_val = str(max_matches).strip()
    if mm_val and mm_val != "1000":
        cmd.extend(["-m", mm_val])

    if str(max_file_size_mb).strip() and str(max_file_size_mb).strip() != "100":
        cmd.extend(["--max-file-size", str(max_file_size_mb).strip()])

    if timestamp_suffix:
        cmd.extend(["--ts-suffix", timestamp_suffix])

    if output_dir.strip():
        cmd.extend(["--output-dir", output_dir.strip()])

    if range_filters.strip():
        for spec in range_filters.split(","):
            spec = spec.strip()
            if spec:
                cmd.extend(["-R", spec])

    if expression:
        pass  # already appended right after -e
    elif regex:
        # Preserve backslashes for regex patterns (shlex.split eats them)
        lex = shlex.shlex(search_text.strip(), posix=True)
        lex.escape = ""
        lex.commenters = ""
        lex.whitespace_split = True
        try:
            terms = list(lex)
        except ValueError:
            terms = search_text.strip().split()
        cmd.extend(terms)
    else:
        try:
            terms = shlex.split(search_text.strip())
        except ValueError:
            terms = search_text.strip().split()
        cmd.extend(terms)

    return cmd


def _parse_summary_text(stdout):
    """Parse CLI summary output into a short status string."""
    if not stdout:
        return ""
    clean = re.sub(r"\033\[[0-9;]*m", "", stdout)
    files_match = re.search(r"Files searched:\s*(\d+)", clean)
    size_match = re.search(r"Files searched:\s*\d+\s*\(([\d.]+ [KMGT]?B)\)", clean)
    found_match = re.search(r"Found\s+(\d+)\s+match", clean)
    matched_files_match = re.search(r"match\(es\)\s+in\s+(\d+)\s+file\(s\)", clean)
    capped_match = re.search(r"Reports capped at ([\d,]+)", clean)
    inverse_match = re.search(r"Found\s+(\d+)\s+file\(s\)\s+WITHOUT\s+matches", clean)
    elapsed_match = re.search(r"Elapsed time:\s*([\d.]+)\s*seconds", clean)

    parts = []
    # Lead with files searched + elapsed time so the headline metric
    # ('N files searched in T seconds') reads first — that's the
    # impressive number for the hero video and the most useful
    # 'is this fast?' signal for everyday use. Match count and the
    # report cap follow as secondary information.
    if files_match:
        try:
            files_n_str = f"{int(files_match.group(1)):,}"
        except (TypeError, ValueError):
            files_n_str = files_match.group(1)
        file_part = f"{files_n_str} file(s) searched"
        if size_match:
            file_part += f" ({size_match.group(1)})"
        parts.append(file_part)
    if elapsed_match:
        parts.append(f"in {elapsed_match.group(1)}s")
    if inverse_match:
        parts.append(f"— found {inverse_match.group(1)} file(s) WITHOUT matches")
    elif found_match:
        count = found_match.group(1)
        in_files = f" in {matched_files_match.group(1)} file(s)" if matched_files_match else ""
        parts.append(f"— found {count} match(es){in_files}")
        if capped_match:
            parts.append(f"— reports capped at {capped_match.group(1)}")

    errors_match = re.search(r"(\d+)\s+error\(s\)", clean)
    if errors_match:
        err_count = errors_match.group(1)
        parts.append(f"— {err_count} file(s) could not be read")

    # Surface the "Note: index bypassed — …" line emitted by the CLI when
    # the user asked for the index but the engine fell through to direct
    # scan (regex / fuzzy / wildcard / proximity queries). The bypass is
    # silent on disk; here we keep the user informed about what happened.
    bypass_match = re.search(r"Note: index bypassed — ([^\n.]+)", clean)
    if bypass_match:
        parts.append(f"— index bypassed ({bypass_match.group(1).strip()})")

    # Surface the "Note: index built with max-file-size=N MB; …" stale-index
    # notice emitted when the saved index parameters don't match the current
    # search settings. The condensed status-line version just calls it out
    # as "stale" — the user can re-run `peekdocs --index` for the full text.
    stale_match = re.search(r"Note: index (built with max-file-size|lacks max-file-size|has unparseable)", clean)
    if stale_match:
        parts.append("— index settings out of sync (run --index to refresh)")

    return " ".join(parts) if parts else ""


def _parse_matched_files(results_dir, results_filename="peekdocs_standard_results.txt"):
    """Parse a .txt result report and return a list of (filepath, filename, count, line_nums) tuples.

    Handles both normal results (Document: ..., Line: ...) and inverse results
    (Files WITHOUT matches: ... followed by filename/directory pairs).
    """
    results_path = os.path.join(results_dir, results_filename)
    if not os.path.exists(results_path):
        return []
    data = {}  # filepath -> {"filename": ..., "count": int, "lines": [int, ...]}
    order = []
    with open(results_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    i = 0
    in_inverse = False
    while i < len(lines):
        line = lines[i].strip()

        # Detect inverse results section
        if line.startswith("Files WITHOUT matches:"):
            in_inverse = True
            i += 1
            continue

        # Parse inverse file list: filename on one line, (directory) on next
        if in_inverse:
            if line and not line.startswith("("):
                filename = line
                if i + 1 < len(lines):
                    dir_line = lines[i + 1].strip()
                    if dir_line.startswith("(") and dir_line.endswith(")"):
                        file_dir = dir_line[1:-1]
                        filepath = os.path.join(file_dir, filename)
                        if filepath not in data:
                            data[filepath] = {
                                "filename": filename,
                                "count": 0,
                                "lines": [],
                            }
                            order.append(filepath)
                        i += 2
                        continue
            i += 1
            continue

        # Parse normal results: Document: ..., Line: ...
        if line.startswith("Document: ") and ", Line: " in line:
            if i + 1 < len(lines):
                dir_line = lines[i + 1].strip()
                if dir_line.startswith("(") and dir_line.endswith(")"):
                    file_dir = dir_line[1:-1]
                    raw_name = line.split("Document: ")[1].split(", Line: ")[0]
                    filename = re.sub(r"\s+\(\d+ match(?:es)?\)$", "", raw_name)
                    line_num_str = line.split(", Line: ")[1].strip()
                    line_num_match = re.match(r"(\d+)", line_num_str)
                    line_num = int(line_num_match.group(1)) if line_num_match else None
                    filepath = os.path.join(file_dir, filename)
                    if filepath in data:
                        data[filepath]["count"] += 1
                        if line_num is not None:
                            data[filepath]["lines"].append(line_num)
                    else:
                        data[filepath] = {
                            "filename": filename,
                            "count": 1,
                            "lines": [line_num] if line_num is not None else [],
                        }
                        order.append(filepath)
        i += 1
    return [(fp, data[fp]["filename"], data[fp]["count"], data[fp]["lines"]) for fp in order]


def _parse_inverse_files(results_dir, results_filename="peekdocs_standard_results.txt"):
    """Parse a .txt result report for inverse search and return (filepath, filename, 0, []) tuples."""
    results_path = os.path.join(results_dir, results_filename)
    if not os.path.exists(results_path):
        return []
    result = []
    with open(results_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    in_inverse = False
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("Files WITHOUT matches:"):
            in_inverse = True
            i += 1
            continue
        if in_inverse:
            # Stop at the first Document: line (match details section)
            if line.startswith("Document:"):
                break
            # Each inverse file is two lines: "  filename" then "  (directory)"
            if line and not line.startswith("("):
                if i + 1 < len(lines):
                    dir_line = lines[i + 1].strip()
                    if dir_line.startswith("(") and dir_line.endswith(")"):
                        file_dir = dir_line[1:-1]
                        filename = line
                        filepath = os.path.join(file_dir, filename)
                        result.append((filepath, filename, 0, []))
                        i += 2
                        continue
        i += 1
    return result


def _build_wizard_regex(selected_patterns):
    """Combine selected (label, regex) tuples into a single regex.

    Returns a regex string joining patterns with '|' (OR).
    """
    if not selected_patterns:
        return ""
    return "|".join(f"({regex})" for _, regex in selected_patterns)
