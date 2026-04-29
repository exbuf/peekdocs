"""Command-line interface for PeekDocs."""

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


try:
    VERSION = pkg_version("peekdocs")
except Exception:
    VERSION = "0.3.0"  # fallback for PyInstaller builds

HIGHLIGHT = "\033[1;94m"
RESET = "\033[0m"

from peekdocs.constants import (  # noqa: E402
    SUPPORTED_TYPES, OCR_IMAGE_TYPES, FUZZY_THRESHOLD, INDEX_FILENAME,
    _default_cores, TESTED_PYTHON_MIN, TESTED_PYTHON_MAX,
)

BANNER_TOP = (
    '\npeekdocs — search Word docs, PDFs, spreadsheets, emails, source code, and 80+ other file types, all at once, all offline.\n'
    'Results are saved to highlighted .docx and .txt reports. GUI available: run peekdocs-gui\n'
    '\n'
    'Supported file types (100+):\n'
    '  Documents:    .doc .docx .epub .html .key .md .odp .odt .pages .pdf .ppt .pptx .rst .rtf .tex\n'
    '  Spreadsheets: .csv .numbers .ods .tsv .xls .xlsx\n'
    '  Email:        .eml .mbox .msg .pst\n'
    '  Archives:     .7z .bz2 .gz .rar .tar .tgz .zip\n'
    '  Calendar/Contacts: .ics .vcf\n'
    '  Source Code:  .asm .bat .c .cmake .cpp .cs .css .f .f90 .go .gradle .h .hpp .java .js .kt .lua\n'
    '                .pl .ps1 .py .r .rb .rs .s .scala .scss .sh .swift .tcl .ts .vb\n'
    '  Engineering:  .cir .dxf .m .sp .spice .sv .v .vhd .vhdl .vsdx\n'
    '  Data/Config:  .cfg .conf .dockerfile .env .graphql .gql .ini .json .jsonl .log .makefile\n'
    '                .ndjson .properties .proto .sql .tf .toml .txt .xml .yaml .yml\n'
    '  Notebooks:    .ipynb (Jupyter)\n'
    '  Images (OCR): .bmp .jpg .jpeg .png .tif .tiff (requires -O flag)\n'
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
    '  -o csv,json,pdf,html  Additional output formats (any combination)\n'
    '  -s my_report       Save/archive the report with a name\n'
    '  -sa my_report      Append results to a named file across searches\n'
    '  --output-dir PATH  Write all output files to a specific folder\n'
    '  --timestamp        Add timestamp to report filenames\n'
    '  --max-file-size N  Skip files larger than N MB (default 100, 0 = no limit)\n'
    '  --open FMT         Automatically open the report when search finishes:\n'
    '                       docx, txt, csv, json, pdf, html\n'
    '                       (csv/json/pdf/html are auto-generated if not already enabled)\n'
    '\n'
    '── Index (optional, for faster repeated searches) ──────────────\n'
    '  --index            Build/rebuild the search index (includes all subfolders)\n'
    '  --index-refresh    Incrementally update the index\n'
    '  --index-status     Show index file count, size, last updated\n'
    '  --index-clear      Delete the search index\n'
    '  --no-index         Skip the index for this search (direct scan)\n'
    '\n'
    '── Settings & Info ──────────────────────────────────────────────\n'
    '  --suite NAME       Run a search suite (group of saved searches) by name\n'
    '  --config KEY=VAL   Save a default setting (e.g., --config recursive=true)\n'
    '  --config           Show all saved settings\n'
    '\n'
    '  Config keys (boolean — true/false):\n'
    '    recursive, match_all, regex, fuzzy, wildcard, whole_word, ocr, inverse,\n'
    '    index_search, output_csv, output_json, output_pdf, output_html, timestamp, quiet\n'
    '  Config keys (integer):\n'
    '    cores, context_before, context_after, proximity, max_matches, max_file_size_mb\n'
    '  Config keys (string):\n'
    '    file_types, search_terms, folder, exclude, specific_files, save_name,\n'
    '    append_name, output_dir, range, text_size, preview_size, appearance_mode\n'
    '  --check            Verify Python, dependencies, Tesseract, and disk space\n'
    '  --clear            Delete peekdocs_results* files in the current directory\n'
    '  --clear-all        Delete all peekdocs output files (results, saved reports, error log, index)\n'
    '  -c 4               Number of CPU cores to use\n'
    '  -q                 Suppress the output banner\n'
    '  -qq                Minimal output — show only Found/Elapsed lines (no file list, warnings, or report paths)\n'
    '  -v                 Show version\n'
    '  -h                 Show this help\n'
    '\n'
    'All flags can be combined freely except: -x (regex), -z (fuzzy), and -w (wildcard)\n'
    'are mutually exclusive (pick one); and -e (expression) cannot be combined with\n'
    '-a (AND), -n (exclude), or -p (word proximity) — those are built into expression syntax.\n'
    '\n'
    'Special characters (<, >, [, ], *, ?, $, |, etc.) must be enclosed in quotes.\n'
    '\n'
    'Usage: cd /path/to/your/documents && peekdocs [OPTIONS] TERM [TERM ...]\n'
    '       Navigate to the folder you want to search, then run peekdocs.\n'
    '\n'
    '── Search Modes (examples) ──────────────────────────────────────\n'
    '  peekdocs term1 term2           OR search (any term matches)\n'
    '  peekdocs -a term1 term2        AND search (all terms required in same line)\n'
    '  peekdocs -e "(A AND B) OR C"   Boolean expression with AND, OR, NOT, parens\n'
    '  peekdocs -x "\\d{3}-\\d{4}"      Regex pattern matching\n'
    '  peekdocs -w "budg*"            Wildcard (* = any chars, ? = one char)\n'
    '  peekdocs -z budgt              Fuzzy matching (typo-tolerant)\n'
    '  peekdocs -W bob                Whole-word only (not "bobcat")\n'
    '  peekdocs -p 5 budget revenue   Word proximity (terms within 5 words of each other)\n'
    '  peekdocs -P 3 budget acme      Line proximity (terms within 3 lines of each other)\n'
    '  peekdocs --inverse budget      Find files that do NOT contain "budget"\n'
    '  peekdocs -n draft budget       Find "budget" but exclude lines containing "draft"\n'
    '  peekdocs -f report.pdf budget  Search only report.pdf for "budget"\n'
    '  peekdocs -s quarterly budget   Save a named copy of the report as peekdocs_report_quarterly\n'
    '  peekdocs -sa archive budget    Append results to peekdocs_accumulated_archive\n'
    '  peekdocs --open docx budget    Search and auto-open the highlighted Word report\n'
    '  peekdocs --open html budget    Search, generate HTML, and open it in your browser\n'
    '  peekdocs --open csv budget     Search, generate CSV, and open it in Excel/LibreOffice\n'
    '  peekdocs --open pdf budget     Search, generate PDF, and open it in a PDF viewer\n'
    '  peekdocs --open json budget    Search, generate JSON, and open it in a text editor\n'
    '  peekdocs -sa archive --open docx budget  Append to accumulated report and open it\n'
    '  peekdocs -sa archive --open html budget  Append and open accumulated report in browser\n'
    '\n'
    '── Common Options ───────────────────────────────────────────────\n'
    '  peekdocs -r budget               Search all subfolders recursively\n'
    '  peekdocs -t pdf,docx budget      Search only PDF and Word files\n'
    '  peekdocs -A 5 -B 5 budget        Show 5 lines before and after each match\n'
    '  peekdocs -R amount:1000..5000 "" Filter by dollar range (empty search = range only)\n'
    '  peekdocs -O budget               Enable OCR for scanned PDFs and images\n'
    '  peekdocs --index                 Build search index for faster repeated searches\n'
    '  peekdocs -r -a -t pdf budget revenue  Combine: recursive, AND, PDF only\n'
    '\n'
    '── Cleanup ──────────────────────────────────────────────────────\n'
    '  peekdocs --clear               Delete peekdocs_results* files in the current directory\n'
    '  peekdocs --clear-all           Delete all peekdocs output files (results, saved reports,\n'
    '                                   accumulated reports, error log, and search index)\n'
    '\n'
    '  See Advanced Search Options in the GUI for the full list of search settings.'
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


CONFIG_BOOL_KEYS = {"recursive", "quiet", "match_all", "regex", "ocr", "fuzzy", "wildcard", "whole_word", "index_search", "output_csv", "output_json", "output_pdf", "output_html", "inverse", "timestamp", "hover_text", "pii_scan_custom_enabled", "pii_scan_custom2_enabled", "delete_reports_on_close", "clear_history_on_close", "restrict_permissions"}
CONFIG_INT_KEYS = {"cores", "context_before", "context_after", "proximity", "max_matches", "max_file_size_mb"}
CONFIG_STR_KEYS = {"file_types", "search_terms", "folder", "exclude", "specific_files", "save_name", "append_name", "output_dir", "range", "refresh_interval", "text_size", "preview_size", "appearance_mode", "pii_scan_folder", "assistant_history", "pii_scan_custom_name", "pii_scan_custom_regex", "pii_scan_custom_severity", "pii_scan_custom2_name", "pii_scan_custom2_regex", "pii_scan_custom2_severity"}
CONFIG_ALL_KEYS = CONFIG_BOOL_KEYS | CONFIG_INT_KEYS | CONFIG_STR_KEYS


def _config_path():
    """Return the path to ~/.peekdocsrc."""
    return os.path.join(os.path.expanduser("~"), ".peekdocsrc")


def _load_config():
    """Load defaults from ~/.peekdocsrc if it exists."""
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
            elif key == "recent_searches":
                try:
                    import json as _json_rc
                    config[key] = _json_rc.loads(value)
                except Exception:
                    pass
    return config


def _save_config(settings):
    """Write settings dict to ~/.peekdocsrc with restricted permissions."""
    path = _config_path()
    with open(path, "w", encoding="utf-8") as f:
        f.write("# ~/.peekdocsrc - peekdocs defaults\n")
        f.write("# Command-line flags always override these settings\n\n")
        for key in sorted(settings):
            value = settings[key]
            if isinstance(value, bool):
                f.write(f"{key} = {'true' if value else 'false'}\n")
            elif isinstance(value, list):
                import json as _json_sv
                f.write(f"{key} = {_json_sv.dumps(value)}\n")
            else:
                f.write(f"{key} = {value}\n")
    # Restrict to owner read-write only (config may contain custom PII patterns)
    try:
        import stat
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass  # Windows may not support Unix permissions


# Re-export from scanner so tests can monkeypatch via peekdocs.cli
from peekdocs.scanner import _process_file, _ocr_image, discover_files, _extract_lines, _search_file_lines  # noqa: E402
from peekdocs.parser import parse_flags  # noqa: E402
from peekdocs.indexer import (  # noqa: E402
    index_exists, build_index, refresh_index, clear_index,
    index_status, search_with_index,
)
from peekdocs.reporter import (  # noqa: E402
    fmt_size, write_txt_report, write_docx_report,
    insert_file_sizes, write_csv_report, write_json_report,
    write_pdf_report, write_html_report, append_results,
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
    ("customtkinter", "customtkinter", "GUI (peekdocs-gui)"),
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
                "peekdocs may not work correctly.")
    if v > TESTED_PYTHON_MAX:
        return (f"Warning: peekdocs has not been tested with Python {v[0]}.{v[1]}. "
                "If you experience issues, check peekdocs_errors.log.")
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
                    "Try: pip install --upgrade peekdocs")
        return ("A required module could not be imported. "
                "A dependency may be missing or incompatible with your Python version. "
                "Try reinstalling: pip install --upgrade peekdocs")

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
            "Please report this at https://github.com/exbuf/peekdocs/issues")


def main(argv=None):
    # Force UTF-8 output on Windows to prevent UnicodeEncodeError
    # when printing Unicode characters (progress bars, filenames, etc.)
    # Only reconfigure when connected to a real terminal (not piped by GUI)
    import sys as _sys
    if _sys.stdout and _sys.stdout.isatty() and hasattr(_sys.stdout, 'reconfigure'):
        try:
            _sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    if _sys.stderr and _sys.stderr.isatty() and hasattr(_sys.stderr, 'reconfigure'):
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
        error_log_path = os.path.join(os.getcwd(), "peekdocs_errors.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        diagnosis = _diagnose(exc)
        with open(error_log_path, "a", encoding="utf-8") as log_f:
            log_f.write(f"\n{'='*60}\n")
            log_f.write(f"{timestamp}  CRASH REPORT\n")
            log_f.write(f"peekdocs {VERSION}\n")
            log_f.write(f"Python {sys.version}\n")
            log_f.write(f"OS: {platform.system()} {platform.release()}\n")
            cmd = " ".join(argv) if argv else " ".join(sys.argv[1:])
            log_f.write(f"Command: peekdocs {cmd}\n")
            log_f.write(f"\nDiagnosis: {diagnosis}\n")
            log_f.write(f"\nDependency versions:\n")
            try:
                log_f.write(_dep_versions_str() + "\n")
            except Exception:
                log_f.write("  (could not determine)\n")
            log_f.write(f"{'='*60}\n")
            traceback.print_exc(file=log_f)
            log_f.write("\n")
        print(f"\nError: An unexpected error occurred. Details logged to peekdocs_errors.log")
        print(f"Run 'peekdocs --check' to verify your installation.\n")
        return 2


def _main_inner(argv=None):
    if argv is None:
        args = sys.argv[1:]
    else:
        args = list(argv)

    # Python version guard — hard block if below minimum
    v = sys.version_info[:2]
    if v < TESTED_PYTHON_MIN:
        print(f"Error: peekdocs requires Python {TESTED_PYTHON_MIN[0]}.{TESTED_PYTHON_MIN[1]} or later. "
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
        print(f"\nOr reinstall peekdocs: pip install --upgrade peekdocs\n")
        return 2

    original_args = list(args)

    config = {}  # CLI uses only explicit flags; config is for GUI only

    minimal = "-qq" in args
    if "-qq" in args:
        args.remove("-qq")
    quiet = minimal or "-q" in args
    if "-q" in args:
        args.remove("-q")

    cpu_count = os.cpu_count() or 1
    is_help = args and args[0] in ("-h", "-help", "--help")
    if not quiet:
        print(f'\npeekdocs v{VERSION}')
        print(f'Your system has {cpu_count} CPU cores (default for -c: {max(1, cpu_count // 2)})')
        print('Readme documentation: https://github.com/exbuf/peekdocs/blob/main/README.md')
        print(BANNER_TOP)
        print(BANNER_BOTTOM)
        print('-------------------------------------------------------------------------')
        print()

    if args and args[0] in ("-v", "-version"):
        print(f"peekdocs {VERSION}\n")
        return 0

    if is_help:
        if quiet:
            print(f'\npeekdocs v{VERSION}')
            print(f'Your system has {cpu_count} CPU cores (default for -c: {max(1, cpu_count // 2)})')
            print('Readme documentation: https://github.com/exbuf/peekdocs/blob/main/README.md')
            print(BANNER_TOP)
            print(BANNER_BOTTOM)
            print('-------------------------------------------------------------------------')
            print()
        print(REGEX_PATTERNS)
        print()
        print('Type peekdocs to see examples directly over the command line.')
        return 0

    if args and args[0] == "--check":
        import sqlite3
        print(f"peekdocs {VERSION}")
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
            print("Fix missing dependencies with: pip install --upgrade peekdocs")
            print()

        return 0 if all_ok else 2

    if args and args[0] in ("--clear", "--clear-all"):
        cwd = os.getcwd()
        clear_all = args[0] == "--clear-all"
        deleted = []

        # Always delete results files
        for f in os.listdir(cwd):
            if f.startswith("peekdocs_results"):
                os.remove(os.path.join(cwd, f))
                deleted.append(f)

        if clear_all:
            # Also delete saved reports, error log, and index
            for f in os.listdir(cwd):
                if f.startswith(("peekdocs_report_", "peekdocs_accumulated_")):
                    os.remove(os.path.join(cwd, f))
                    deleted.append(f)
            for f in ("peekdocs_errors.log", ".peekdocs.db", ".peekdocs.db-wal", ".peekdocs.db-shm"):
                path = os.path.join(cwd, f)
                if os.path.exists(path):
                    os.remove(path)
                    deleted.append(f)

        if deleted:
            print(f"Deleted {len(deleted)} file(s) from {cwd}:")
            for f in sorted(deleted):
                print(f"  {f}")
        else:
            print("No peekdocs output files found in the current directory.")
        if not clear_all:
            print("\nTo also delete saved reports, error log, and index: peekdocs --clear-all")
        return 0

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
            print("No index found. Build one with: peekdocs --index\n")
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
        print(f"  peekdocs ver:  {status.get('peekdocs_version', '?')}")
        print()
        return 0

    if args and args[0] == "--index-refresh":
        cwd = os.getcwd()
        if not index_exists(cwd):
            print("No index found. Build one first with: peekdocs --index\n")
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
            print("Error: No filename provided. Usage: peekdocs -s name_of_your_file\n")
            return 2
        name = "_".join(args[1:]).replace(" ", "_")
        cwd = os.getcwd()
        save_dir = _load_config().get("output_dir", cwd)
        src_docx = os.path.join(save_dir, "peekdocs_results.docx")
        src_txt = os.path.join(save_dir, "peekdocs_results.txt")
        dest_docx = os.path.join(save_dir, f"peekdocs_report_{name}.docx")
        dest_txt = os.path.join(save_dir, f"peekdocs_report_{name}.txt")
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
                print("Current settings (~/.peekdocsrc):\n")
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

    # ── --suite NAME: run a search suite ──
    if args and args[0] == "--suite":
        if len(args) < 2:
            print("Error: --suite requires a suite name. Usage: peekdocs --suite \"My Suite\"\n")
            return 2
        suite_name = args[1]
        cwd = os.getcwd()
        from peekdocs.collection import get_suite, get_search_params, load_collection
        suite_searches = get_suite(cwd, suite_name)
        if suite_searches is None:
            available = list(load_collection(cwd).get("suites", {}).keys())
            print(f"Suite '{suite_name}' not found in {cwd}")
            if available:
                print(f"Available suites: {', '.join(available)}")
            else:
                print("No suites defined. Create one in the GUI (Tools → Search Suites).")
            return 2

        if not suite_searches:
            print(f"Suite '{suite_name}' has no searches.")
            return 2

        from peekdocs.api import search as api_search
        from peekdocs.reporter import write_suite_txt_report, write_suite_docx_report

        sections = []
        for i, search_name in enumerate(suite_searches, 1):
            params = get_search_params(cwd, search_name)
            if params is None:
                print(f"  Warning: saved search '{search_name}' not found — skipping.")
                continue

            print(f"  [{i}/{len(suite_searches)}] Running: {search_name}")

            # Convert saved-search params to api.search() kwargs
            terms_str = params.get("search_text", "")
            import shlex as _shlex
            try:
                search_terms = _shlex.split(terms_str) if terms_str else []
            except ValueError:
                search_terms = terms_str.split() if terms_str else []

            expr = params.get("expression") if params.get("expression") else None
            kwargs = {
                "directory": cwd,
                "match_all": params.get("and_mode", False),
                "recursive": params.get("recursive", False),
                "use_fuzzy": params.get("fuzzy", False),
                "use_wildcard": params.get("wildcard", False),
                "use_regex": params.get("regex", False),
                "use_ocr": params.get("ocr", False),
                "use_whole_word": params.get("whole_word", False),
                "use_index": params.get("index_search", False),
                "expression": expr,
            }
            if params.get("exclude"):
                kwargs["exclude_terms"] = [t.strip() for t in params["exclude"].split(",") if t.strip()]
            if params.get("file_types"):
                kwargs["file_types"] = [t.strip() for t in params["file_types"].split(",") if t.strip()]
            if params.get("proximity"):
                kwargs["proximity"] = int(params["proximity"])
            if params.get("context_before"):
                kwargs["context_before"] = int(params["context_before"])
            if params.get("context_after"):
                kwargs["context_after"] = int(params["context_after"])
            if params.get("range_filters"):
                rf = params["range_filters"]
                kwargs["range_filters"] = rf if isinstance(rf, list) else [r.strip() for r in rf.split(",") if r.strip()]

            result = api_search(search_terms if not expr else [], **kwargs)

            mode = "ALL" if params.get("and_mode") else "ANY"
            display_terms = search_terms if not expr else [expr]
            sections.append({
                "search_name": search_name,
                "search_terms": display_terms,
                "matches": [(m.file_dir, m.filename, m.line_num, m.text) for m in result.matches],
                "all_files": result.files_searched,
                "elapsed": result.elapsed,
                "report_mode": mode,
                "params": params,
            })
            print(f"           {len(result.matches)} match(es) in {len(result.files_searched)} file(s)")

        if not sections:
            print("No searches were run.")
            return 2

        txt_path = os.path.join(cwd, "peekdocs_suite_results.txt")
        docx_path = os.path.join(cwd, "peekdocs_suite_results.docx")
        write_suite_txt_report(txt_path, suite_name, sections)
        write_suite_docx_report(docx_path, txt_path, sections)

        total_matches = sum(len(s["matches"]) for s in sections)
        print(f"\nSuite '{suite_name}': {len(sections)} search(es), {total_matches} total match(es)")
        print(f"Reports: {txt_path}")
        print(f"         {docx_path}")
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
    line_proximity = parsed.get("line_proximity", 0)
    append_name = parsed["append_name"]
    cores = parsed["cores"]
    output_formats = parsed["output_formats"]
    inverse = parsed["inverse"]
    open_report = parsed.get("open_report", False)
    # --open csv automatically enables -o csv (same for json, pdf, html)
    if open_report and open_report not in ("docx", "txt"):
        if open_report not in output_formats:
            output_formats.append(open_report)
    expression = parsed.get("expression")
    mode = parsed["mode"]
    report_mode = parsed["report_mode"]

    command_str = "peekdocs " + " ".join(f'"{a}"' if " " in a else a for a in original_args)
    print('-------------------------------------------------------------------------')
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
        from peekdocs.range_query import parse_range
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
        from peekdocs.api import search as _api_search
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
            line_proximity=line_proximity,
            cores=cores,
            use_index=None if not no_index else False,
            progress=_cli_progress,
            expression=expression,
            range_filters=range_specs_raw or None,
            max_file_size_mb=parsed.get("max_file_size_mb", 100),
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

    # Write errors to log immediately; print warnings after results (below)
    if skipped_files:
        error_log_path = os.path.join(output_dir, "peekdocs_errors.log")
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
    output_path = os.path.join(output_dir, f"peekdocs_results{ts_suffix}.txt")
    docx_output_path = os.path.join(output_dir, f"peekdocs_results{ts_suffix}.docx")

    idx_meta = index_status(cwd) if use_index else None

    # Set restrictive file permissions if enabled in config
    import peekdocs.reporter as _reporter_mod
    _reporter_mod.restrict_permissions = _load_config().get("restrict_permissions", False)

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
    pdf_output_path = None

    if "csv" in output_formats:
        csv_output_path = os.path.join(output_dir, f"peekdocs_results{ts_suffix}.csv")
        write_csv_report(csv_output_path, matches, inverse_files=inverse_files)

    if "json" in output_formats:
        json_output_path = os.path.join(output_dir, f"peekdocs_results{ts_suffix}.json")
        write_json_report(
            json_output_path, matches, search_terms, report_mode,
            len(all_files), search_elapsed,
            inverse_files=inverse_files,
        )

    if "pdf" in output_formats:
        pdf_output_path = os.path.join(output_dir, f"peekdocs_results{ts_suffix}.pdf")
        try:
            write_pdf_report(
                pdf_output_path, matches, search_terms=search_terms,
                report_mode=report_mode, inverse_files=inverse_files,
            )
        except Exception as pdf_err:
            print(f"Warning: PDF report could not be generated ({pdf_err})")
            pdf_output_path = None

    html_output_path = None
    if "html" in output_formats:
        html_output_path = os.path.join(output_dir, f"peekdocs_results{ts_suffix}.html")
        try:
            write_html_report(
                html_output_path, matches, search_terms=search_terms,
                report_mode=report_mode, inverse_files=inverse_files,
            )
        except Exception as html_err:
            print(f"Warning: HTML report could not be generated ({html_err})")
            html_output_path = None

    if append_name is not None:
        append_results(append_name, output_dir, output_path, docx_output_path)

    elapsed = time.time() - start_time
    # Count unique files with matches
    matched_file_count = len({os.path.join(fd, fn) for fd, fn, _ln, _tx in matches})
    print()
    if inverse:
        print(f"Found {HIGHLIGHT}{len(inverse_files)}{RESET} file(s) WITHOUT matches. Files searched: {len(all_files)} ({size_str}).")
    elif capped:
        print(f"Found {HIGHLIGHT}{total_match_count}{RESET} match(es) in {matched_file_count} file(s). Files searched: {len(all_files)} ({size_str}). Reports capped at {max_matches:,}.")
    else:
        print(f"Found {HIGHLIGHT}{len(matches)}{RESET} match(es) in {matched_file_count} file(s). Files searched: {len(all_files)} ({size_str}).")
    print(f"Elapsed time: {elapsed:.2f} seconds, Cores used: {cores} of {cpu_count}")
    if not minimal:
        if inverse:
            for f in inverse_files:
                print(f"  {os.path.basename(f)}")
        else:
            # Per-file match counts
            file_counts = {}
            for fd, fn, _ln, _tx in matches:
                key = (fd, fn)
                if key not in file_counts:
                    file_counts[key] = 0
                file_counts[key] += 1
            for (_fd, fn), count in sorted(file_counts.items(), key=lambda x: x[0][1].lower()):
                print(f"  {fn}: {count}")
        print(f"Results ==> {output_dir}")
        print(f"  {os.path.basename(output_path)} ({fmt_size(txt_size)}), {os.path.basename(docx_output_path)} ({fmt_size(docx_size)})")
        if csv_output_path:
            print(f"  {os.path.basename(csv_output_path)} ({fmt_size(os.path.getsize(csv_output_path))})")
        if json_output_path:
            print(f"  {os.path.basename(json_output_path)} ({fmt_size(os.path.getsize(json_output_path))})")
        if pdf_output_path:
            print(f"  {os.path.basename(pdf_output_path)} ({fmt_size(os.path.getsize(pdf_output_path))})")
        if append_name is not None:
            print(f"Results appended to peekdocs_accumulated_{append_name}.txt and peekdocs_accumulated_{append_name}.docx")
        if skipped_files:
            print()
            for skipped_name, error_msg in skipped_files:
                print(f"  Warning: Could not read {skipped_name} ({error_msg})")
            print(f"\n  Errors logged to peekdocs_errors.log ({len(skipped_files)} error(s))")
    print()
    if open_report:
        # If -sa was used, point docx/txt to the accumulated files
        if append_name is not None and open_report in ("docx", "txt"):
            _append_ext = "docx" if open_report == "docx" else "txt"
            _append_path = os.path.join(output_dir, f"peekdocs_accumulated_{append_name}.{_append_ext}")
        else:
            _append_path = None
        # Map format to the corresponding output path
        _open_paths = {
            "docx": _append_path or docx_output_path,
            "txt": _append_path or output_path,
            "csv": csv_output_path,
            "json": json_output_path,
            "pdf": pdf_output_path,
            "html": html_output_path,
        }
        open_path = _open_paths.get(open_report)
        if open_path and os.path.exists(open_path):
            from peekdocs.gui._helpers import safe_open_file
            warning = safe_open_file(open_path)
            if warning:
                print(f"\n{warning}")
        elif open_path is None:
            print(f"Note: Unknown format '{open_report}'.")
        else:
            print(f"Note: {open_report} report file not found.")
    if inverse:
        return 0 if inverse_files else 1
    return 0 if matches else 1


if __name__ == "__main__":
    sys.exit(main())
