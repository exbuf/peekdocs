"""Graphical interface for PeekDocs."""

import os
import platform
import re
import shlex
import subprocess
import sys


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
        f"your search results — including any sensitive data such as "
        f"SSNs, credit card numbers, and passwords.\n\n"
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
    # Lead with Found count, then files searched
    if inverse_match:
        parts.append(f"Found {inverse_match.group(1)} file(s) WITHOUT matches")
    elif found_match:
        count = found_match.group(1)
        in_files = f" in {matched_files_match.group(1)} file(s)" if matched_files_match else ""
        if capped_match:
            parts.append(f"Found {count} match(es){in_files} — reports capped at {capped_match.group(1)}")
        else:
            parts.append(f"Found {count} match(es){in_files}")
    if files_match:
        file_part = f"— {files_match.group(1)} file(s) searched"
        if size_match:
            file_part += f" ({size_match.group(1)})"
        parts.append(file_part)
    if elapsed_match:
        parts.append(f"in {elapsed_match.group(1)}s")

    errors_match = re.search(r"(\d+)\s+error\(s\)", clean)
    if errors_match:
        err_count = errors_match.group(1)
        parts.append(f"— {err_count} file(s) could not be read")

    return " ".join(parts) if parts else ""


def _parse_matched_files(results_dir, results_filename="peekdocs_results.txt"):
    """Parse peekdocs_results.txt and return a list of (filepath, filename, count, line_nums) tuples.

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


def _parse_inverse_files(results_dir, results_filename="peekdocs_results.txt"):
    """Parse peekdocs_results.txt for inverse search and return (filepath, filename, 0, []) tuples."""
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
