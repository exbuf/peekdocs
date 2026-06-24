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


# Report extensions that must only open in known-safe local apps.
# The system default handler is never used for these — it could route
# to Google Docs, Apple Pages, or a cloud-syncing browser.
_PROTECTED_EXTENSIONS = {".docx", ".pdf", ".csv", ".json"}


def safe_open_file(filepath):
    """Open *filepath* in a safe local application.

    For .docx and .pdf files, only known-safe local applications are
    used — the system default handler is never called, preventing any
    possibility of data being uploaded to the cloud.

    Returns ``None`` on success or a warning string if the file could not
    be opened safely.  The caller should display the warning to the user.
    """
    system = platform.system()
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".docx":
        return _safe_open_docx(filepath, system)
    if ext == ".pdf":
        return _safe_open_pdf(filepath, system)
    if ext == ".csv":
        return _safe_open_csv(filepath, system)
    if ext == ".json":
        return _safe_open_json(filepath, system)

    # --- Non-protected files: open normally -----------------------------
    if system == "Windows":
        os.startfile(filepath)  # type: ignore[attr-defined]
    elif system == "Darwin":
        subprocess.Popen(["open", filepath])
    else:
        subprocess.Popen(["xdg-open", filepath])
    return None


_DOCX_WARNING = (
    "Your default .docx application was blocked as it may upload "
    "your data to the cloud (Google Docs uploads to Google servers; "
    "Apple Pages may sync to iCloud). peekdocs blocks .docx files "
    "from opening in any application that may upload your data.\n\n"
    "Please install Microsoft Word or LibreOffice (free) to view "
    ".docx files."
)

_PDF_WARNING = (
    "Your default PDF application was blocked as it may be a web "
    "browser that syncs data to the cloud, or a cloud-based PDF "
    "viewer. peekdocs blocks PDF files from opening in any "
    "application that may upload your data.\n\n"
    "Please install Adobe Acrobat Reader (free) or another local "
    "PDF viewer."
)

_CSV_WARNING = (
    "Your default CSV application was blocked as it may be Google "
    "Sheets or another cloud spreadsheet that uploads your data. "
    "peekdocs blocks CSV files from opening in any application "
    "that may upload your data.\n\n"
    "Please install Microsoft Excel or LibreOffice Calc (free) to "
    "view CSV files."
)

_JSON_WARNING = (
    "Your default JSON application was blocked as it may be a "
    "cloud-based editor that uploads your data. peekdocs blocks "
    "JSON files from opening in any application that may upload "
    "your data.\n\n"
    "Please install a local text editor to view JSON files."
)


def _safe_open_docx(filepath, system):
    """Open a .docx in Word or LibreOffice only — never in an app that
    may upload to the cloud (Google Docs, Apple Pages)."""

    # --- macOS -----------------------------------------------------------
    if system == "Darwin":
        for app in ("Microsoft Word", "LibreOffice"):
            result = subprocess.run(
                ["open", "-a", app, filepath],
                capture_output=True,
            )
            if result.returncode == 0:
                return None
        return _DOCX_WARNING

    # --- Windows ---------------------------------------------------------
    if system == "Windows":
        import glob as _glob
        import shutil
        # Try winword on PATH (rare but possible).
        winword = shutil.which("winword")
        if winword:
            subprocess.Popen([winword, filepath])
            return None
        # Check common Office install locations.
        for pattern in (
            r"C:\Program Files\Microsoft Office\root\Office*\WINWORD.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office*\WINWORD.EXE",
            r"C:\Program Files\Microsoft Office*\root\Office*\WINWORD.EXE",
        ):
            hits = _glob.glob(pattern)
            if hits:
                subprocess.Popen([hits[0], filepath])
                return None
        # Try LibreOffice.
        soffice = shutil.which("soffice")
        if soffice:
            subprocess.Popen([soffice, "--writer", filepath])
            return None
        for pattern in (
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ):
            hits = _glob.glob(pattern)
            if hits:
                subprocess.Popen([hits[0], "--writer", filepath])
                return None
        return _DOCX_WARNING

    # --- Linux -----------------------------------------------------------
    import shutil
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice:
        subprocess.Popen([soffice, "--writer", filepath])
        return None
    return _DOCX_WARNING


def _safe_open_pdf(filepath, system):
    """Open a PDF in a known-safe local viewer only — never through the
    system default handler, which could be a cloud-syncing browser."""

    # --- macOS -----------------------------------------------------------
    if system == "Darwin":
        # Preview is Apple's built-in local PDF viewer — no cloud upload.
        # Also try Adobe Acrobat Reader and Skim (popular local viewer).
        for app in ("Preview", "Adobe Acrobat Reader", "Skim"):
            result = subprocess.run(
                ["open", "-a", app, filepath],
                capture_output=True,
            )
            if result.returncode == 0:
                return None
        return _PDF_WARNING

    # --- Windows ---------------------------------------------------------
    if system == "Windows":
        import glob as _glob
        import shutil
        # Adobe Acrobat Reader
        for exe_name in ("AcroRd32.exe", "Acrobat.exe"):
            acrobat = shutil.which(exe_name)
            if acrobat:
                subprocess.Popen([acrobat, filepath])
                return None
        for pattern in (
            r"C:\Program Files\Adobe\Acrobat*\Acrobat\Acrobat.exe",
            r"C:\Program Files (x86)\Adobe\Acrobat*\Acrobat\Acrobat.exe",
            r"C:\Program Files\Adobe\Acrobat*\Reader\AcroRd32.exe",
            r"C:\Program Files (x86)\Adobe\Acrobat*\Reader\AcroRd32.exe",
        ):
            hits = _glob.glob(pattern)
            if hits:
                subprocess.Popen([hits[0], filepath])
                return None
        # SumatraPDF (popular free local viewer)
        sumatra = shutil.which("SumatraPDF")
        if sumatra:
            subprocess.Popen([sumatra, filepath])
            return None
        for pattern in (
            r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
            r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
        ):
            hits = _glob.glob(pattern)
            if hits:
                subprocess.Popen([hits[0], filepath])
                return None
        # Foxit Reader
        for pattern in (
            r"C:\Program Files\Foxit Software\Foxit*Reader\Foxit*Reader.exe",
            r"C:\Program Files (x86)\Foxit Software\Foxit*Reader\Foxit*Reader.exe",
        ):
            hits = _glob.glob(pattern)
            if hits:
                subprocess.Popen([hits[0], filepath])
                return None
        # LibreOffice Draw can open PDFs
        soffice = shutil.which("soffice")
        if soffice:
            subprocess.Popen([soffice, "--draw", filepath])
            return None
        for pattern in (
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ):
            hits = _glob.glob(pattern)
            if hits:
                subprocess.Popen([hits[0], "--draw", filepath])
                return None
        return _PDF_WARNING

    # --- Linux -----------------------------------------------------------
    import shutil
    # Common local-only PDF viewers
    for viewer in ("evince", "okular", "xreader", "atril", "mupdf", "zathura"):
        exe = shutil.which(viewer)
        if exe:
            subprocess.Popen([exe, filepath])
            return None
    # LibreOffice Draw as fallback
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice:
        subprocess.Popen([soffice, "--draw", filepath])
        return None
    return _PDF_WARNING


def _safe_open_csv(filepath, system):
    """Open a CSV in Excel or LibreOffice Calc only — never through the
    system default handler, which could be Google Sheets or a cloud app."""

    # --- macOS -----------------------------------------------------------
    if system == "Darwin":
        for app in ("Microsoft Excel", "LibreOffice", "Numbers"):
            # Numbers is local-only for CSV (unlike .docx in Pages).
            result = subprocess.run(
                ["open", "-a", app, filepath],
                capture_output=True,
            )
            if result.returncode == 0:
                return None
        # TextEdit as last resort — CSV is plain text.
        result = subprocess.run(
            ["open", "-a", "TextEdit", filepath],
            capture_output=True,
        )
        if result.returncode == 0:
            return None
        return _CSV_WARNING

    # --- Windows ---------------------------------------------------------
    if system == "Windows":
        import glob as _glob
        import shutil
        # Microsoft Excel
        excel = shutil.which("EXCEL")
        if excel:
            subprocess.Popen([excel, filepath])
            return None
        for pattern in (
            r"C:\Program Files\Microsoft Office\root\Office*\EXCEL.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office*\EXCEL.EXE",
            r"C:\Program Files\Microsoft Office*\root\Office*\EXCEL.EXE",
        ):
            hits = _glob.glob(pattern)
            if hits:
                subprocess.Popen([hits[0], filepath])
                return None
        # LibreOffice Calc
        soffice = shutil.which("soffice")
        if soffice:
            subprocess.Popen([soffice, "--calc", filepath])
            return None
        for pattern in (
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ):
            hits = _glob.glob(pattern)
            if hits:
                subprocess.Popen([hits[0], "--calc", filepath])
                return None
        # Notepad as last resort — CSV is plain text.
        notepad = shutil.which("notepad")
        if notepad:
            subprocess.Popen([notepad, filepath])
            return None
        return _CSV_WARNING

    # --- Linux -----------------------------------------------------------
    import shutil
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice:
        subprocess.Popen([soffice, "--calc", filepath])
        return None
    # CSV is plain text — any local text editor works.
    for editor in ("xed", "gedit", "mousepad", "kate", "xdg-open"):
        exe = shutil.which(editor)
        if exe:
            subprocess.Popen([exe, filepath])
            return None
    return _CSV_WARNING


def _safe_open_json(filepath, system):
    """Open a JSON file in a local text editor only — never through the
    system default handler, which could be a cloud-based editor."""

    # --- macOS -----------------------------------------------------------
    if system == "Darwin":
        # TextEdit is built-in and local-only.
        result = subprocess.run(
            ["open", "-a", "TextEdit", filepath],
            capture_output=True,
        )
        if result.returncode == 0:
            return None
        return _JSON_WARNING

    # --- Windows ---------------------------------------------------------
    if system == "Windows":
        import shutil
        # Notepad is always available on Windows and is local-only.
        notepad = shutil.which("notepad")
        if notepad:
            subprocess.Popen([notepad, filepath])
            return None
        return _JSON_WARNING

    # --- Linux -----------------------------------------------------------
    import shutil
    for editor in ("xed", "gedit", "mousepad", "kate", "nano", "xdg-open"):
        exe = shutil.which(editor)
        if exe:
            subprocess.Popen([exe, filepath])
            return None
    return _JSON_WARNING


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
