"""Command-line interface for DocSearch."""

import logging
import multiprocessing
import os
import platform
import re
import shutil
import signal
import sys
import threading
import time
import traceback
from datetime import datetime
from importlib.metadata import version as pkg_version

logging.getLogger("pymupdf").setLevel(logging.ERROR)

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


VERSION = pkg_version("docsearch")

HIGHLIGHT = "\033[1;94m"
RESET = "\033[0m"

from docsearch.constants import (  # noqa: E402
    SUPPORTED_TYPES, OCR_IMAGE_TYPES, FUZZY_THRESHOLD, INDEX_FILENAME,
    _default_cores, TESTED_PYTHON_MIN, TESTED_PYTHON_MAX,
)

BANNER_TOP = (
    '\ndocsearch — search Word docs, PDFs, spreadsheets, emails, and 38 other file types, all at once, all offline.\n'
    'Results are saved to highlighted .docx and .txt reports. GUI available: run docsearch-gui\n'
    '\n'
    'Usage: docsearch [OPTIONS] TERM [TERM ...]\n'
    '\n'
    'Supported file types:\n'
    '  Documents:  .doc .docx .pdf .odt .rtf .epub .pptx .ppt .html .md .rst .tex\n'
    '  Spreadsheets: .xlsx .xls .ods .csv .tsv\n'
    '  Email:      .eml .msg .pst\n'
    '  Archives:   .zip .tar .gz .bz2 .tgz .7z .rar\n'
    '  Data/Config: .json .xml .yaml .yml .toml .ini .cfg .sql .log .txt\n'
    '  Images (OCR): .bmp .jpg .jpeg .png .tif .tiff (requires -O flag)\n'
    '\n'
    '── Search Modes ─────────────────────────────────────────────────\n'
    '  docsearch term1 term2           OR search (any term matches)\n'
    '  docsearch -a term1 term2        AND search (all terms required in same line)\n'
    '  docsearch -e "(A AND B) OR C"   Boolean expression with AND, OR, NOT, parens\n'
    '  docsearch -x "\\d{3}-\\d{4}"      Regex pattern matching\n'
    '  docsearch -w "budg*"            Wildcard (* = any chars, ? = one char)\n'
    '  docsearch -z budgt              Fuzzy matching (typo-tolerant)\n'
    '  docsearch -W bob                Whole-word only (not "bobcat")\n'
    '  docsearch -p 5 budget revenue   Proximity (terms within 5 words of each other)'
)

BANNER_BOTTOM = (
    '\n── Filters ──────────────────────────────────────────────────────\n'
    '  -t pdf,docx        Search only these file types\n'
    '  -f report.pdf      Search only specific files (comma-separated)\n'
    '  -r                 Search subdirectories recursively\n'
    '  -n draft           Exclude lines matching these terms\n'
    '  -R amount:1000..5000  Range filter (fields: date, amount, number, percent,\n'
    '                        age, time, filesize, filedate). Repeatable.\n'
    '                        Use fn: prefix for filename values\n'
    '  --inverse          List files that do NOT contain the search terms\n'
    '  -O                 Enable OCR for scanned PDFs and images\n'
    '\n'
    '── Output ───────────────────────────────────────────────────────\n'
    '  -A 5               Show 5 lines after each match\n'
    '  -B 5               Show 5 lines before each match\n'
    '  -m 5000            Max matches in reports (0 = no limit, default: 1000)\n'
    '  -o csv,json        Additional output formats (csv, json, or both)\n'
    '  -s my_report       Save/archive the report with a name\n'
    '  -sa my_report      Append results to a named file across searches\n'
    '  --output-dir PATH  Write all output files to a specific folder\n'
    '  --timestamp        Add timestamp to report filenames\n'
    '\n'
    '── Index (optional, for faster repeated searches) ──────────────\n'
    '  --index            Build/rebuild the search index (includes all subfolders)\n'
    '  --index-refresh    Incrementally update the index\n'
    '  --index-status     Show index file count, size, last updated\n'
    '  --index-clear      Delete the search index\n'
    '  --no-index         Skip the index for this search (direct scan)\n'
    '\n'
    '── Settings & Info ──────────────────────────────────────────────\n'
    '  --config KEY=VAL   Save a default setting (e.g., --config recursive=true)\n'
    '  --config           Show all saved settings\n'
    '  --check            Verify Python, dependencies, Tesseract, and disk space\n'
    '  -c 4               Number of CPU cores to use\n'
    '  -q                 Suppress the output banner\n'
    '  -v                 Show version\n'
    '  -h                 Show this help\n'
    '\n'
    'Special characters (<, >, [, ], *, ?, $, |, etc.) must be enclosed in quotes.\n'
    'Full documentation: https://github.com/exbuf/docsearch/blob/main/README.md'
)

REGEX_PATTERNS = (
    '\nCommon Regex Search Patterns (enclose in quotes):\n'
    '  \\d{3}-\\d{3}-\\d{4}                              US phone numbers (555-123-4567)\n'
    '  [A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z]{2,}    Email addresses (jane@example.com)\n'
    '  \\d{4}-\\d{2}-\\d{2}                              Dates, YYYY-MM-DD (2026-03-17)\n'
    '  \\$\\d+(\\.\\d{2})?                                 Dollar amounts ($45.99)\n'
    '  \\d{3}-\\d{2}-\\d{4}                              SSN format (123-45-6789)\n'
    '  \\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}              IP addresses (192.168.1.1)\n'
    '  https?://\\S+                                    URLs (https://example.com)\n'
    '  \\b[A-Z]{2,}\\b                                   Acronyms, all caps (NASA, FBI)\n'
    '  \\b\\d{5}(-\\d{4})?\\b                              US ZIP codes (12345 or 12345-6789)\n'
    '  \\(\\d{3}\\)\\s?\\d{3}-\\d{4}                         Phone with area code parens ((555) 123-4567)\n'
    '  \\b[A-Z][a-z]+\\s[A-Z][a-z]+\\b                    Proper names (John Smith)\n'
    '  \\b\\d+%                                          Percentages (92%)\n'
    '  Q[1-4]\\s?\\d{4}                                  Fiscal quarters (Q1 2026)\n'
)


CONFIG_BOOL_KEYS = {"recursive", "quiet", "match_all", "regex", "ocr", "fuzzy", "wildcard", "whole_word", "index_search", "output_csv", "output_json", "inverse", "timestamp", "suite_timestamp"}
CONFIG_INT_KEYS = {"cores", "context_before", "context_after", "proximity", "max_matches"}
CONFIG_STR_KEYS = {"file_types", "search_terms", "folder", "exclude", "specific_files", "save_name", "append_name", "output_dir", "suite_output_dir", "range", "refresh_interval", "smtp_host", "smtp_port", "smtp_user", "smtp_password", "email_from", "email_to", "email_on", "text_size"}
CONFIG_ALL_KEYS = CONFIG_BOOL_KEYS | CONFIG_INT_KEYS | CONFIG_STR_KEYS


def _config_path():
    """Return the path to ~/.docsearchrc."""
    return os.path.join(os.path.expanduser("~"), ".docsearchrc")


def _load_config():
    """Load defaults from ~/.docsearchrc if it exists."""
    path = _config_path()
    if not os.path.exists(path):
        return {}
    config = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key in CONFIG_BOOL_KEYS:
                config[key] = value.lower() in ("true", "yes", "1")
            elif key in CONFIG_INT_KEYS:
                try:
                    config[key] = int(value)
                except ValueError:
                    pass
            elif key in CONFIG_STR_KEYS:
                if value:
                    config[key] = value
    return config


def _save_config(settings):
    """Write settings dict to ~/.docsearchrc."""
    path = _config_path()
    with open(path, "w", encoding="utf-8") as f:
        f.write("# ~/.docsearchrc - docsearch defaults\n")
        f.write("# Command-line flags always override these settings\n\n")
        for key in sorted(settings):
            value = settings[key]
            if isinstance(value, bool):
                f.write(f"{key} = {'true' if value else 'false'}\n")
            else:
                f.write(f"{key} = {value}\n")


# Re-export from scanner so tests can monkeypatch via docsearch.cli
from docsearch.scanner import _process_file, _ocr_image, discover_files, _extract_lines, _search_file_lines  # noqa: E402
from docsearch.parser import parse_flags  # noqa: E402
from docsearch.indexer import (  # noqa: E402
    index_exists, build_index, refresh_index, clear_index,
    index_status, search_with_index,
)
from docsearch.reporter import (  # noqa: E402
    fmt_size, write_txt_report, write_docx_report,
    insert_file_sizes, write_csv_report, write_json_report,
    append_results,
)


_REQUIRED_MODULES = [
    ("fitz", "pymupdf", "PDF files"),
    ("docx", "python-docx", "Word documents (.docx)"),
    ("openpyxl", "openpyxl", "Excel spreadsheets (.xlsx)"),
    ("pptx", "python-pptx", "PowerPoint files (.pptx)"),
    ("ebooklib", "ebooklib", "EPUB e-books"),
    ("striprtf.striprtf", "striprtf", "RTF files"),
    ("odf.opendocument", "odfpy", "ODF files (.odt, .ods, .odp)"),
]


_OPTIONAL_MODULES = [
    ("rapidfuzz", "rapidfuzz", "Fuzzy matching (-z)"),
    ("pytesseract", "pytesseract", "OCR engine (-O)"),
    ("PIL", "Pillow", "OCR image processing (-O)"),
    ("customtkinter", "customtkinter", "GUI (docsearch-gui)"),
]


def _get_pkg_version(package):
    """Return the installed version of a package, or '?' if unavailable."""
    try:
        return pkg_version(package)
    except Exception:
        return "?"


def _check_dependencies():
    """Check that all required modules can be imported.

    Returns list of (module_display, package, status, version) tuples.
    """
    results = []
    for module_name, package, description in _REQUIRED_MODULES:
        try:
            __import__(module_name)
            ver = _get_pkg_version(package)
            results.append((description, package, "ok", ver))
        except ImportError as e:
            results.append((description, package, "MISSING", str(e)))
    return results


def _check_optional_dependencies():
    """Check optional modules. Returns list of (description, package, status, version) tuples."""
    results = []
    for module_name, package, description in _OPTIONAL_MODULES:
        try:
            __import__(module_name)
            ver = _get_pkg_version(package)
            results.append((description, package, "ok", ver))
        except ImportError:
            results.append((description, package, "not installed", ""))
    return results


def _dep_versions_str():
    """Return a formatted string of all dependency versions for crash reports."""
    import sqlite3
    lines = []
    for desc, pkg, status, ver in _check_dependencies():
        lines.append(f"  {pkg}: {ver}" if status == "ok" else f"  {pkg}: MISSING")
    for desc, pkg, status, ver in _check_optional_dependencies():
        if status == "ok":
            lines.append(f"  {pkg}: {ver}")
    lines.append(f"  sqlite3: {sqlite3.sqlite_version}")
    return "\n".join(lines)


def _check_python_version():
    """Return a warning string if Python version is outside tested range, or None."""
    v = sys.version_info[:2]
    if v < TESTED_PYTHON_MIN:
        return (f"Warning: Python {v[0]}.{v[1]} is below the minimum tested version "
                f"({TESTED_PYTHON_MIN[0]}.{TESTED_PYTHON_MIN[1]}). "
                "docsearch may not work correctly.")
    if v > TESTED_PYTHON_MAX:
        return (f"Warning: docsearch has not been tested with Python {v[0]}.{v[1]}. "
                "If you experience issues, check docsearch_errors.log.")
    return None


def _diagnose(exc):
    """Return a plain-English diagnosis based on the exception type and message."""
    name = type(exc).__name__
    msg = str(exc).lower()

    if isinstance(exc, ImportError):
        module = getattr(exc, "name", "") or ""
        if module:
            return (f"The Python module '{module}' could not be loaded. "
                    "This is usually caused by a missing or incompatible dependency. "
                    "Try: pip install --upgrade docsearch")
        return ("A required module could not be imported. "
                "A dependency may be missing or incompatible with your Python version. "
                "Try reinstalling: pip install --upgrade docsearch")

    if isinstance(exc, MemoryError):
        return ("The system ran out of memory. "
                "This may happen when searching very large files. "
                "Try searching fewer files or use -t to limit file types.")

    if isinstance(exc, PermissionError):
        return ("A file or directory could not be accessed due to permissions. "
                "Check that you have read access to the files being searched.")

    if isinstance(exc, OSError):
        if "no space" in msg:
            return ("The disk is full. Free up space and try again.")
        if "too many open files" in msg:
            return ("Too many files open at once. "
                    "Try reducing the number of CPU cores with -c 1.")
        return (f"An operating system error occurred: {exc}. "
                "This may indicate a file access or disk problem.")

    if isinstance(exc, UnicodeDecodeError):
        return ("A file contained unexpected character encoding. "
                "The file may be corrupted or in an unsupported format.")

    if "fitz" in msg or "pymupdf" in msg:
        return ("An error occurred in the PDF processing library (PyMuPDF). "
                "The PDF file may be corrupted, or the library may need updating. "
                "Try: pip install --upgrade pymupdf")

    if "docx" in msg or "opc" in msg:
        return ("An error occurred reading a Word document. "
                "The .docx file may be corrupted or password-protected.")

    if "openpyxl" in msg:
        return ("An error occurred reading an Excel file. "
                "The .xlsx file may be corrupted or password-protected.")

    return (f"An unexpected {name} occurred. "
            "This may be a bug or a compatibility issue with your Python version. "
            "Please report this at https://github.com/exbuf/docsearch/issues")


def main(argv=None):
    # Force UTF-8 output on Windows to prevent UnicodeEncodeError
    # when printing Unicode characters (progress bars, filenames, etc.)
    import sys as _sys
    if _sys.stdout and hasattr(_sys.stdout, 'reconfigure'):
        try:
            _sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    if _sys.stderr and hasattr(_sys.stderr, 'reconfigure'):
        try:
            _sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    try:
        return _main_inner(argv)
    except KeyboardInterrupt:
        print("\nSearch cancelled.\n")
        return 2
    except Exception as exc:
        error_log_path = os.path.join(os.getcwd(), "docsearch_errors.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        diagnosis = _diagnose(exc)
        with open(error_log_path, "a", encoding="utf-8") as log_f:
            log_f.write(f"\n{'='*60}\n")
            log_f.write(f"{timestamp}  CRASH REPORT\n")
            log_f.write(f"docsearch {VERSION}\n")
            log_f.write(f"Python {sys.version}\n")
            log_f.write(f"OS: {platform.system()} {platform.release()}\n")
            cmd = " ".join(argv) if argv else " ".join(sys.argv[1:])
            log_f.write(f"Command: docsearch {cmd}\n")
            log_f.write(f"\nDiagnosis: {diagnosis}\n")
            log_f.write(f"\nDependency versions:\n")
            try:
                log_f.write(_dep_versions_str() + "\n")
            except Exception:
                log_f.write("  (could not determine)\n")
            log_f.write(f"{'='*60}\n")
            traceback.print_exc(file=log_f)
            log_f.write("\n")
        print(f"\nError: An unexpected error occurred. Details logged to docsearch_errors.log")
        print(f"Run 'docsearch --check' to verify your installation.\n")
        return 2


def _main_inner(argv=None):
    if argv is None:
        args = sys.argv[1:]
    else:
        args = list(argv)

    # Python version guard — hard block if below minimum
    v = sys.version_info[:2]
    if v < TESTED_PYTHON_MIN:
        print(f"Error: docsearch requires Python {TESTED_PYTHON_MIN[0]}.{TESTED_PYTHON_MIN[1]} or later. "
              f"You are running Python {v[0]}.{v[1]}.\n")
        print("To upgrade Python:")
        print("  macOS:   brew install python@3.12")
        print("  Ubuntu:  sudo apt install python3.12")
        print("  Windows: Download from https://www.python.org/downloads/")
        print()
        return 2
    version_warning = _check_python_version()
    if version_warning:
        print(version_warning)

    # Startup dependency check (blocks if critical deps missing)
    dep_results = _check_dependencies()
    missing = [(desc, pkg) for desc, pkg, status, _ in dep_results if status == "MISSING"]
    if missing:
        print("Error: Required dependencies are missing:\n")
        for desc, pkg in missing:
            print(f"  {desc} — install with: pip install {pkg}")
        print(f"\nOr reinstall docsearch: pip install --upgrade docsearch\n")
        return 2

    original_args = list(args)

    config = {}  # CLI uses only explicit flags; config is for GUI only

    quiet = "-q" in args
    if "-q" in args:
        args.remove("-q")

    cpu_count = os.cpu_count() or 1
    is_help = args and args[0] in ("-h", "-help", "--help")
    if not quiet:
        print(BANNER_TOP)
        print(BANNER_BOTTOM)
        print(f'Your system has {cpu_count} CPU cores (default for -c: {max(1, cpu_count // 2)})')
        print()

    if args and args[0] in ("-v", "-version"):
        print(f"docsearch {VERSION}\n")
        return 0

    if is_help:
        if quiet:
            print(BANNER_TOP)
            print(BANNER_BOTTOM)
            print(f'Your system has {cpu_count} CPU cores (default for -c: {max(1, cpu_count // 2)})')
            print()
        print(REGEX_PATTERNS)
        return 0

    if args and args[0] == "--check":
        import sqlite3
        print(f"docsearch {VERSION}")
        print(f"Python {sys.version}")
        print(f"OS: {platform.system()} {platform.release()}")
        print()

        # Python version
        v = sys.version_info[:2]
        if v < TESTED_PYTHON_MIN:
            print(f"Python version:  {v[0]}.{v[1]} (BELOW minimum {TESTED_PYTHON_MIN[0]}.{TESTED_PYTHON_MIN[1]}) — upgrade Python to {TESTED_PYTHON_MIN[0]}.{TESTED_PYTHON_MIN[1]} or later")
        elif v > TESTED_PYTHON_MAX:
            print(f"Python version:  {v[0]}.{v[1]} (above maximum tested {TESTED_PYTHON_MAX[0]}.{TESTED_PYTHON_MAX[1]}) — should work, but not yet verified")
        else:
            print(f"Python version:  {v[0]}.{v[1]} (ok)")
        print()

        # Required dependencies
        print("Required dependencies:")
        all_ok = True
        for desc, pkg, status, ver in dep_results:
            if status == "ok":
                print(f"  {desc} ({pkg}): ok ({ver})")
            else:
                print(f"  {desc} ({pkg}): MISSING — install with: pip install {pkg}")
                all_ok = False
        print()

        # Optional dependencies
        print("Optional dependencies:")
        opt_results = _check_optional_dependencies()
        for desc, pkg, status, ver in opt_results:
            if status == "ok":
                print(f"  {desc} ({pkg}): ok ({ver})")
            else:
                print(f"  {desc} ({pkg}): not installed — install with: pip install {pkg}")
        print()

        # Tesseract binary (separate from Python package)
        if shutil.which("tesseract"):
            print("Tesseract OCR:   installed (OCR available with -O flag)")
        else:
            print("Tesseract OCR:   not installed (optional — needed only for -O flag)")

        # SQLite
        print(f"SQLite version:  {sqlite3.sqlite_version}")
        print()

        # Disk space
        cwd = os.getcwd()
        free = shutil.disk_usage(cwd).free
        print(f"Disk space:      {fmt_size(free)} free")
        if free < 10_000_000:
            print("  Warning: Low disk space. Reports may fail to write.")
        print()

        if not all_ok:
            print("Fix missing dependencies with: pip install --upgrade docsearch")
            print()

        return 0 if all_ok else 2

    if args and args[0] == "--index":
        cwd = os.getcwd()
        remaining = args[1:]
        use_ocr = "-O" in remaining
        print(f"Building index in {cwd} (including all subfolders)")
        if use_ocr:
            print("  OCR enabled (-O)")
        print()

        def _index_progress(done, total_count, filename):
            if total_count == 0:
                return
            pct = done / total_count
            filled = int(40 * pct)
            bar = "█" * filled + "░" * (40 - filled)
            line = f"\r  [{bar}] {done}/{total_count} {filename}"
            try:
                tw = os.get_terminal_size().columns
            except OSError:
                tw = 80
            line = line.ljust(tw)[:tw]
            sys.stdout.write(line)
            sys.stdout.flush()

        result = build_index(cwd, recursive=True, use_ocr=use_ocr,
                             progress_callback=_index_progress)

        # Clear progress line
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()

        if result["errors"]:
            for err in result["errors"]:
                if isinstance(err, tuple):
                    print(f"Warning: Could not read {err[0]} ({err[1]})")
                else:
                    print(f"Error: {err}")

        db_path = os.path.join(cwd, INDEX_FILENAME)
        print(f"Index built: {result['file_count']} files, {result['line_count']} lines")
        print(f"Index file:  {db_path}")
        print(f"Elapsed:     {result['elapsed']:.2f} seconds")
        print()
        print(f"Note: The index file ({INDEX_FILENAME}) is hidden by default on macOS/Linux.")
        print(f"Use 'ls -a' or Cmd+Shift+. in Finder to see it.")
        print()
        return 0

    if args and args[0] == "--index-clear":
        cwd = os.getcwd()
        if clear_index(cwd):
            print("Index removed.\n")
        else:
            print("No index found.\n")
        return 0

    if args and args[0] == "--index-status":
        cwd = os.getcwd()
        status = index_status(cwd)
        if status is None:
            print("No index found. Build one with: docsearch --index\n")
            return 0
        db_path = os.path.join(cwd, INDEX_FILENAME)
        print("Index status:")
        print(f"  Index file:     {INDEX_FILENAME}")
        print(f"  Folder:         {cwd}")
        print(f"  Full path:      {db_path}")
        print(f"  Files indexed:  {status.get('file_count', '?')}")
        print(f"  Lines indexed:  {status.get('line_count', '?')}")
        print(f"  Database size:  {fmt_size(status.get('db_size', 0))}")
        print(f"  Created:        {status.get('created_at', '?')}")
        print(f"  Last updated:   {status.get('last_updated', status.get('created_at', '?'))}")
        print(f"  Recursive:      {status.get('recursive', '?')}")
        print(f"  OCR:            {status.get('use_ocr', '?')}")
        print(f"  docsearch ver:  {status.get('docsearch_version', '?')}")
        print()
        return 0

    if args and args[0] == "--index-refresh":
        cwd = os.getcwd()
        if not index_exists(cwd):
            print("No index found. Build one first with: docsearch --index\n")
            return 0
        use_ocr = "-O" in args[1:]
        print(f"Refreshing index in {cwd} ...")
        result = refresh_index(cwd, recursive=True, use_ocr=use_ocr)
        print(f"Index refreshed: {result['added']} added, {result['updated']} updated, "
              f"{result['removed']} removed")
        print(f"Elapsed: {result['elapsed']:.2f} seconds\n")
        return 0

    if not args:
        return 0

    if args and args[0] in ("-s", "-save"):
        if len(args) < 2:
            print("Error: No filename provided. Usage: docsearch -s name_of_your_file\n")
            return 2
        name = "_".join(args[1:]).replace(" ", "_")
        cwd = os.getcwd()
        save_dir = _load_config().get("output_dir", cwd)
        src_docx = os.path.join(save_dir, "docsearch_results.docx")
        src_txt = os.path.join(save_dir, "docsearch_results.txt")
        dest_docx = os.path.join(save_dir, f"DO_NOT_SEARCH_{name}.docx")
        dest_txt = os.path.join(save_dir, f"DO_NOT_SEARCH_{name}.txt")
        if not os.path.exists(src_docx) or not os.path.exists(src_txt):
            print("Error: No search results found. Run a search first.\n")
            return 2
        shutil.copy2(src_docx, dest_docx)
        shutil.copy2(src_txt, dest_txt)
        print(f"Results saved to {os.path.basename(dest_docx)} and {os.path.basename(dest_txt)}\n")
        return 0

    if args and args[0] == "--config":
        config_args = args[1:]
        if not config_args:
            # Show current config
            current = _load_config()
            if not current:
                print("No config file found.\n")
            else:
                print("Current settings (~/.docsearchrc):\n")
                for key in sorted(current):
                    print(f"  {key} = {current[key]}")
                print()
            return 0
        # Set or remove values
        current = _load_config()
        bool_values = {"true", "false", "yes", "no", "1", "0"}
        for pair in config_args:
            if "=" not in pair:
                print(f"Error: Invalid format: {pair}. Use key=value (e.g., --config recursive=true)\n")
                return 2
            key, _, value = pair.partition("=")
            key = key.strip()
            value = value.strip()
            if key not in CONFIG_ALL_KEYS:
                valid = ", ".join(sorted(CONFIG_ALL_KEYS))
                print(f"Error: Unknown setting: {key}. Valid settings: {valid}\n")
                return 2
            if not value:
                # Remove the key
                current.pop(key, None)
                print(f"Removed: {key}")
            elif key in CONFIG_BOOL_KEYS:
                if value.lower() not in bool_values:
                    print(f"Error: Invalid value for {key}: {value}. Use true or false.\n")
                    return 2
                current[key] = value.lower() in ("true", "yes", "1")
                print(f"Set: {key} = {current[key]}")
            elif key in CONFIG_INT_KEYS:
                try:
                    int_val = int(value)
                    if int_val < 1:
                        raise ValueError
                except ValueError:
                    print(f"Error: Invalid value for {key}: {value}. Must be a positive integer.\n")
                    return 2
                current[key] = int_val
                print(f"Set: {key} = {int_val}")
            elif key in CONFIG_STR_KEYS:
                current[key] = value
                print(f"Set: {key} = {value}")
        if current:
            _save_config(current)
        else:
            # All keys removed — delete the file
            path = _config_path()
            if os.path.exists(path):
                os.remove(path)
        print()
        return 0

    no_index = "--no-index" in args
    if no_index:
        args.remove("--no-index")

    ts_suffix = ""
    if "--timestamp" in args:
        args.remove("--timestamp")
        ts_suffix = "_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    if "--ts-suffix" in args:
        idx = args.index("--ts-suffix")
        if idx + 1 < len(args):
            ts_suffix = "_" + args[idx + 1]
            del args[idx:idx + 2]
        else:
            args.remove("--ts-suffix")

    output_dir = None
    if "--output-dir" in args:
        idx = args.index("--output-dir")
        if idx + 1 < len(args):
            output_dir = args[idx + 1]
            del args[idx:idx + 2]
        else:
            args.remove("--output-dir")

    # Range filters (-R / --range), repeatable
    range_specs_raw = []
    while "-R" in args or "--range" in args:
        flag = "-R" if "-R" in args else "--range"
        idx = args.index(flag)
        if idx + 1 < len(args):
            range_specs_raw.append(args[idx + 1])
            del args[idx:idx + 2]
        else:
            args.remove(flag)

    # Parse all flags
    parsed = parse_flags(args, config)
    if isinstance(parsed, tuple):
        print(f"Error: {parsed[1]}")
        return parsed[0]

    search_terms = parsed["search_terms"]
    match_all = parsed["match_all"]
    recursive = parsed["recursive"]
    use_regex = parsed["use_regex"]
    use_ocr = parsed["use_ocr"]
    use_fuzzy = parsed["use_fuzzy"]
    use_wildcard = parsed["use_wildcard"]
    use_whole_word = parsed.get("use_whole_word", False)
    exclude_terms = parsed["exclude_terms"]
    file_types = parsed["file_types"]
    file_names = parsed["file_names"]
    context_before = parsed["context_before"]
    context_after = parsed["context_after"]
    use_context = parsed["use_context"]
    proximity = parsed["proximity"]
    use_proximity = parsed["use_proximity"]
    append_name = parsed["append_name"]
    cores = parsed["cores"]
    output_formats = parsed["output_formats"]
    inverse = parsed["inverse"]
    expression = parsed.get("expression")
    mode = parsed["mode"]
    report_mode = parsed["report_mode"]

    command_str = "docsearch " + " ".join(f'"{a}"' if " " in a else a for a in original_args)
    print(command_str)
    start_time = time.time()
    cwd = os.getcwd()
    if output_dir is None:
        output_dir = cwd
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Determine index mode for display
    _will_use_index = index_exists(cwd) and not no_index
    display_label = expression if expression else ' '.join(search_terms)
    if not display_label and range_specs_raw:
        display_label = " ".join(range_specs_raw)
    # Parse range specs for reporter display
    parsed_range_specs = []
    if range_specs_raw:
        from docsearch.range_query import parse_range
        for spec_str in range_specs_raw:
            parsed_range_specs.append(parse_range(spec_str))
    if _will_use_index:
        print(f"Searching ({mode}, indexed) on [{HIGHLIGHT}{display_label}{RESET}] ...")
    else:
        print(f"Searching ({mode}) on [{HIGHLIGHT}{display_label}{RESET}] ...")
    if exclude_terms:
        print(f"Excluding [{' '.join(exclude_terms)}]")

    # Set up CLI progress bar / spinner
    bar_width = 40
    spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    try:
        term_width = os.get_terminal_size().columns
    except OSError:
        term_width = 80

    spinner_lock = threading.Lock()
    spinner_stop = threading.Event()
    spinner_state = {"done": 0, "total": 0, "filename": ""}

    def _render_progress(done, total_count, filename, spinner=""):
        if total_count == 0:
            return
        pct = done / total_count
        filled = int(bar_width * pct)
        bar = "█" * filled + "░" * (bar_width - filled)
        if spinner:
            line = f"\r  [{bar}] {done}/{total_count} {filename} {spinner}"
        else:
            line = f"\r  [{bar}] {done}/{total_count} {filename}"
        line = line.ljust(term_width)[:term_width]
        sys.stdout.write(line)
        sys.stdout.flush()

    def _spinner_thread_func():
        idx = 0
        while not spinner_stop.is_set():
            with spinner_lock:
                done = spinner_state["done"]
                total_count = spinner_state["total"]
                filename = spinner_state["filename"]
            _render_progress(done, total_count, filename, spinner_chars[idx % len(spinner_chars)])
            idx += 1
            spinner_stop.wait(0.15)

    def _cli_progress(done, total_count, filename):
        with spinner_lock:
            spinner_state["done"] = done
            spinner_state["total"] = total_count
            spinner_state["filename"] = filename
        _render_progress(done, total_count, filename)

    spinner_t = threading.Thread(target=_spinner_thread_func, daemon=True)
    spinner_t.start()

    try:
        from docsearch.api import search as _api_search
        search_result = _api_search(
            search_terms,
            directory=cwd,
            match_all=match_all,
            recursive=recursive,
            use_regex=use_regex,
            use_fuzzy=use_fuzzy,
            use_wildcard=use_wildcard,
            use_whole_word=use_whole_word,
            use_ocr=use_ocr,
            exclude_terms=exclude_terms,
            file_types=file_types,
            file_names=file_names,
            context_before=context_before,
            context_after=context_after,
            proximity=proximity,
            cores=cores,
            use_index=None if not no_index else False,
            progress=_cli_progress,
            expression=expression,
            range_filters=range_specs_raw or None,
        )
    except KeyboardInterrupt:
        spinner_stop.set()
        spinner_t.join()
        sys.stdout.write("\n")
        print("\nSearch cancelled.\n")
        return 2
    except (ValueError, FileNotFoundError) as e:
        spinner_stop.set()
        spinner_t.join()
        print(f"\nError: {e}")
        return 2

    spinner_stop.set()
    spinner_t.join()

    if spinner_state["total"] > 0:
        _render_progress(spinner_state["total"], spinner_state["total"], "done")
        sys.stdout.write("\n")
        sys.stdout.flush()

    matches = search_result.matches
    all_files = search_result.files_searched
    skipped_files = search_result.skipped_files
    search_elapsed = search_result.elapsed
    use_index = search_result.used_index

    for skipped_name, error_msg in skipped_files:
        print(f"Warning: Could not read {skipped_name} ({error_msg})")

    if skipped_files:
        error_log_path = os.path.join(output_dir, "docsearch_errors.log")
        with open(error_log_path, "a", encoding="utf-8") as log_f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for skipped_name, error_msg in skipped_files:
                log_f.write(f"{timestamp}  Could not read {skipped_name} ({error_msg})\n")

    search_elapsed = time.time() - start_time

    # Compute inverse file list if requested
    inverse_files = None
    if inverse:
        matched_paths = {os.path.join(fd, fn) for fd, fn, _ln, _tx in matches}
        inverse_files = [f for f in all_files if f not in matched_paths]

    # Cap matches for report generation to avoid minutes-long DOCX writes
    max_matches = parsed.get("max_matches", 1000)
    total_match_count = len(matches)
    capped = False
    if max_matches > 0 and total_match_count > max_matches:
        capped = True
        matches = matches[:max_matches]

    # Check disk space before writing reports
    free_space = shutil.disk_usage(output_dir).free
    if free_space < 10_000_000:
        print(f"\nWarning: Low disk space ({fmt_size(free_space)} free). Cannot write reports.")
        print("Free up disk space and try again.\n")
        return 2

    # Generate reports
    output_path = os.path.join(output_dir, f"docsearch_results{ts_suffix}.txt")
    docx_output_path = os.path.join(output_dir, f"docsearch_results{ts_suffix}.docx")

    idx_meta = index_status(cwd) if use_index else None

    total_bytes, size_str = write_txt_report(
        output_path, matches, all_files, search_terms, command_str,
        report_mode, use_ocr, exclude_terms, use_context,
        use_fuzzy, use_regex, use_wildcard,
        search_elapsed, cores, cpu_count,
        inverse_files=inverse_files,
        recursive=recursive,
        file_types=",".join(file_types) if file_types else None,
        proximity=proximity if use_proximity else None,
        context_before=context_before,
        context_after=context_after,
        specific_files=",".join(file_names) if file_names else None,
        use_index=use_index,
        inverse=inverse,
        output_csv="csv" in output_formats,
        output_json="json" in output_formats,
        expression=expression,
        use_whole_word=use_whole_word,
        total_matches=total_match_count if capped else None,
        max_matches=max_matches if capped else None,
        range_specs=parsed_range_specs or None,
        index_meta=idx_meta,
    )

    result_doc = write_docx_report(
        docx_output_path, output_path,
        search_terms=search_terms,
        use_regex=use_regex,
        use_wildcard=use_wildcard,
        use_whole_word=use_whole_word,
        use_fuzzy=use_fuzzy,
        expression=expression,
    )
    txt_size, docx_size = insert_file_sizes(output_path, docx_output_path, result_doc)

    csv_output_path = None
    json_output_path = None

    if "csv" in output_formats:
        csv_output_path = os.path.join(output_dir, f"docsearch_results{ts_suffix}.csv")
        write_csv_report(csv_output_path, matches, inverse_files=inverse_files)

    if "json" in output_formats:
        json_output_path = os.path.join(output_dir, f"docsearch_results{ts_suffix}.json")
        write_json_report(
            json_output_path, matches, search_terms, report_mode,
            len(all_files), search_elapsed,
            inverse_files=inverse_files,
        )

    if append_name is not None:
        append_results(append_name, output_dir, output_path, docx_output_path)

    elapsed = time.time() - start_time
    print()
    if inverse:
        print(f"Files searched: {len(all_files)} ({size_str}) — Found {HIGHLIGHT}{len(inverse_files)}{RESET} file(s) WITHOUT matches.")
    elif capped:
        print(f"Files searched: {len(all_files)} ({size_str}) — Found {HIGHLIGHT}{total_match_count}{RESET} match(es). Reports capped at {max_matches:,}.")
    else:
        print(f"Files searched: {len(all_files)} ({size_str}) — Found {HIGHLIGHT}{len(matches)}{RESET} match(es).")
    print(f"Elapsed time: {elapsed:.2f} seconds, Cores used: {cores} of {cpu_count}")
    if inverse:
        if not quiet:
            for f in inverse_files:
                print(f"  {os.path.basename(f)}")
    else:
        if not quiet:
            # Per-file match counts
            file_counts = {}
            for fd, fn, _ln, _tx in matches:
                key = (fd, fn)
                if key not in file_counts:
                    file_counts[key] = 0
                file_counts[key] += 1
            for (_fd, fn), count in file_counts.items():
                print(f"  {fn}: {count}")
    print(f"Results ==> {output_dir}")
    print(f"  {os.path.basename(output_path)} ({fmt_size(txt_size)}), {os.path.basename(docx_output_path)} ({fmt_size(docx_size)})")
    if csv_output_path:
        print(f"  {os.path.basename(csv_output_path)} ({fmt_size(os.path.getsize(csv_output_path))})")
    if json_output_path:
        print(f"  {os.path.basename(json_output_path)} ({fmt_size(os.path.getsize(json_output_path))})")
    if append_name is not None:
        print(f"Results appended to DO_NOT_SEARCH_ACCUMULATED_{append_name}.txt and DO_NOT_SEARCH_ACCUMULATED_{append_name}.docx")
    if skipped_files:
        print(f"Errors logged to docsearch_errors.log ({len(skipped_files)} error(s))")
    print()
    if inverse:
        return 0 if inverse_files else 1
    return 0 if matches else 1


if __name__ == "__main__":
    sys.exit(main())
