"""Command-line interface for PeekDocs."""
from __future__ import annotations

import json
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
from typing import Any

logging.getLogger("pymupdf").setLevel(logging.ERROR)

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


try:
    VERSION = pkg_version("peekdocs")
except Exception:
    VERSION = "1.0.4"  # fallback for PyInstaller builds

HIGHLIGHT = "\033[1;94m"
RESET = "\033[0m"

from peekdocs.constants import (  # noqa: E402
    SUPPORTED_TYPES, OCR_IMAGE_TYPES, FUZZY_THRESHOLD, INDEX_FILENAME,
    _default_cores, TESTED_PYTHON_MIN, TESTED_PYTHON_MAX,
)

BANNER_TOP = (
    '\npeekdocs — privacy-first local document search and analysis platform for Windows, macOS, and Linux.\n'
    'Search 100+ file types using keyword, fuzzy, OCR, and advanced regex workflows.\n'
    'Features batch analysis, highlighted reports, automated reporting, and reusable search profiles.\n'
    'Free and open-source under the MIT license.\n'
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
    '\n── Search Modes ─────────────────────────────────────────────────\n'
    '  (default)          OR search — find lines containing any search term\n'
    '  -a                 AND search — all terms must appear in the same line\n'
    '  -e "EXPR"          Boolean expression with AND, OR, NOT, and parentheses\n'
    '  -x "PATTERN"       Regex pattern matching\n'
    '  -w "PATTERN"       Wildcard matching (* = any chars, ? = one char)\n'
    '  -z                 Fuzzy matching (typo-tolerant)\n'
    '  -W                 Whole-word matching (won\'t match "bob" inside "bobcat")\n'
    '  -p 5 term1 term2   Word proximity — terms within 5 words of each other\n'
    '  -P 3 term1 term2   Line proximity — terms within 3 lines of each other\n'
    '\n'
    '── Filters ──────────────────────────────────────────────────────\n'
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
    '  -A 5               Show 5 lines after each match (paragraph in Word/PDF; row in Excel)\n'
    '  -B 5               Show 5 lines before each match (paragraph in Word/PDF; row in Excel)\n'
    '  -m 5000            Max matches in reports (0 = no limit, default: 5000)\n'
    '  -o docx,csv,json,pdf,html  Opt-in output formats (any combination; .txt is always written)\n'
    '  -s my_report       Save/archive the report with a name\n'
    '  -sa my_report      Append results to a named file across searches\n'
    '  --output-dir PATH  Write all output files to a specific folder. Blocked if the folder is inside\n'
    '                     iCloud / OneDrive / Google Drive / Dropbox unless --allow-cloud-output is passed\n'
    '                     (or redirect_cloud_output=true is set in ~/.peekdocsrc).\n'
    '  --timestamp        Add timestamp to report filenames\n'
    '  --max-file-size N  Skip files larger than N MB (default 100, 0 = no limit)\n'
    '  --open FMT         Automatically open the report when search finishes:\n'
    '                       docx, txt, csv, json, pdf, html\n'
    '                       (csv/json/pdf/html are auto-generated if not already enabled)\n'
    '  --stdout           Output JSON results to stdout (for piping). No report files\n'
    '  --hash             Add SHA-256 of each matched file to JSON output (content fingerprint)\n'
    '  --dry-run          Report what would be searched (file count, size, by extension); no search\n'
    '  --no-log           Skip writing this run to ~/.peekdocs_runs.log (run log is on by default)\n'
    '  --runs [N]         Show the last N runs from the log (default 20). Add --json for raw JSONL\n'
    '  --diff OLD NEW     Compare two peekdocs JSON outputs. Buckets: new / removed / changed / modified.\n'
    '                     Exit codes DIFFER from search: 0=no change, 1=actionable change, 2=error.\n'
    '                     Watch for && chains (use ; for unconditional follow-up). Add --json for machine output.\n'
    '  --on-match CMD     Run CMD when search finds matches (batch searches only, NOT --watch). 30s timeout.\n'
    '                     Env vars: PEEKDOCS_MATCH_COUNT, PEEKDOCS_FILE_COUNT, PEEKDOCS_ELAPSED_SECONDS,\n'
    '                     PEEKDOCS_ARGV, PEEKDOCS_CWD, PEEKDOCS_REPORT_TXT/DOCX/JSON/CSV/PDF/HTML.\n'
    '  --allow-cloud-output  One-off override: write reports even when output_dir is inside a cloud-\n'
    '                     synced folder (iCloud / OneDrive / Google Drive / Dropbox). Without this,\n'
    '                     peekdocs aborts to prevent accidental uploads. Sticky alternative: set\n'
    '                     redirect_cloud_output=true in ~/.peekdocsrc to always redirect to\n'
    '                     ~/peekdocs_reports instead.\n'
    '                       written. Suppresses all banners and progress.\n'
    '\n'
    '── Index (optional, for faster repeated searches) ──────────────\n'
    '  Note: peekdocs builds an index on first search in each folder. The first\n'
    '    search may take longer (seconds to minutes); subsequent searches are\n'
    '    much faster. Use --no-index to skip indexing entirely.\n'
    '  --index            Build/rebuild the search index (includes all subfolders)\n'
    '  --index-refresh    Incrementally update the index\n'
    '  --index-status     Show index file count, size, last updated\n'
    '  --index-clear      Delete the search index\n'
    '  --no-index         Skip the index for this search (direct scan)\n'
    '\n'
    '── Settings & Info ──────────────────────────────────────────────\n'
    '  --suite NAME       Run a search suite (group of saved searches) by name.\n'
    '                     TXT report always written. Add `-o docx` to also write\n'
    '                     a DOCX report (suite CLI -o supports docx only; for\n'
    '                     HTML / CSV / JSON / PDF use the GUI suite popup).\n'
    '  --list-suites      List every known suite and the folder it lives in\n'
    '  --list-suites --rescan   Re-discover suites by scanning ~/Documents and ~/Desktop\n'
    '  --regex-collection NAME  Run a saved regex collection by name\n'
    '                     TXT report always written. Add -o docx,html,csv,json,pdf\n'
    '                     to opt in to additional formats (any combination).\n'
    '  --regex-collection --list  List all saved regex collections\n'
    '  --watch            Long-running mode: watch a folder, run a regex collection\n'
    '                     on each file create/modify, emit one NDJSON line per match\n'
    '                     to stdout. Pair with --regex-collection NAME. Add -r for\n'
    '                     recursive. Ctrl-C to stop. See "Folder watcher" below.\n'
    '  --config KEY=VAL   Save a default setting (e.g., --config recursive=true)\n'
    '  --config           Show all saved settings\n'
    '  --config --reset   Delete all saved settings and return to factory defaults\n'
    '\n'
    '  Config keys (boolean — true/false):\n'
    '    recursive, match_all, regex, fuzzy, wildcard, whole_word, ocr, inverse,\n'
    '    index_search, output_docx, output_csv, output_json, output_pdf, output_html, timestamp, quiet\n'
    '  Config keys (integer):\n'
    '    cores, context_before, context_after, proximity, max_matches, max_file_size_mb\n'
    '  Config keys (string):\n'
    '    file_types, search_terms, folder, exclude, specific_files, save_name,\n'
    '    append_name, output_dir, range, text_size, preview_size, appearance_mode\n'
    '  --check            Verify Python, dependencies, Tesseract, and disk space\n'
    '  --list-files       List all peekdocs-created files in the current directory\n'
    '  --clear            Delete peekdocs_*_results* files in the current directory\n'
    '  --clear-all        Delete all peekdocs output files (results, saved reports, error log, index)\n'
    '                       Saved searches (.peekdocs_collection.json), settings (~/.peekdocsrc),\n'
    '                       and bookmarks are never deleted — remove manually if needed.\n'
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
    'Exit codes: 0 = matches found, 1 = no matches, 2 = error.\n'
    '\n'
    'Usage: cd /path/to/your/documents && peekdocs [OPTIONS] TERM [TERM ...]\n'
    '       Navigate to the folder you want to search, then run peekdocs.\n'
    '\n'
    '── Search Modes (examples — flags can be combined freely) ────────\n'
    '  peekdocs term1 term2           OR search (any term matches)\n'
    '  peekdocs -a term1 term2        AND search (all terms required in same line)\n'
    '  peekdocs -e "(A AND B) OR C"   Boolean expression with AND, OR, NOT, parens\n'
    '  peekdocs -x "\\bREF-\\d{4,}\\b"   Regex pattern matching\n'
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
    '  peekdocs --suite "My Suite"      Run a saved search suite by name (auto-locates folder)\n'
    '  peekdocs --suite ~/Documents/MyDocs/"Example 1"  Run a suite by full path (explicit folder)\n'
    '  peekdocs --list-suites           List every known suite and its folder\n'
    '  peekdocs -r -a -t pdf budget revenue  Combine: recursive, AND, PDF only\n'
    '\n'
    '  Cannot combine: -x (regex), -z (fuzzy), -w (wildcard) — pick one.\n'
    '  Cannot combine: -e (expression) with -a (AND), -n (exclude), or -p (proximity).\n'
    '\n'
    '── Regex ────────────────────────────────────────────────────────\n'
    '  peekdocs --regex-collection Examples    Run the seeded universal-pattern\n'
    '                                            collection (email, URL, IPv4/IPv6,\n'
    '                                            ISO date/time, UUID, semver, hex\n'
    '                                            color, MD link, TODO/FIXME, JIRA\n'
    '                                            ticket, ISBN-13, DOI, USD amount,\n'
    '                                            env var). Seeded on first GUI\n'
    '                                            open of Regex Search; modify or\n'
    '                                            delete freely once seeded.\n'
    '\n'
    '  Regex collection output: TXT report always written (every match grouped by\n'
    '  pattern). DOCX / HTML / CSV / JSON / PDF are opt-in via -o; combine any:\n'
    '    peekdocs --regex-collection Examples                        TXT only\n'
    '    peekdocs --regex-collection Examples -o docx                TXT + DOCX\n'
    '    peekdocs --regex-collection Examples -o docx,html,csv       TXT + 3 more\n'
    '  DOCX and PDF are skipped above 25,000 total matches (in-memory build).\n'
    '\n'
    '  For more patterns, the syntax cheatsheet, or AI-generated regex:\n'
    '    regex101.com           — interactive tester + community pattern library\n'
    '    ihateregex.io          — common patterns with explanations\n'
    '    developer.mozilla.org  — regex syntax reference / cheatsheet\n'
    '\n'
    '── Folder watcher (long-running, NDJSON to stdout) ──────────────────\n'
    '  peekdocs --watch -d ~/folder --regex-collection NAME      Watch + stream matches\n'
    '  peekdocs --watch -d ~/folder --regex-collection NAME -r   Recursive into subfolders\n'
    '\n'
    '  Emits one JSON record per match to stdout while files are created or modified;\n'
    '  status / warnings go to stderr so the stdout stream stays a clean NDJSON pipe.\n'
    '  Ctrl-C stops cleanly (exit 0). Compose with anything that reads JSON Lines:\n'
    '    peekdocs --watch -d ~/Downloads --regex-collection Examples > matches.ndjson\n'
    '    peekdocs --watch -d ~/repo --regex-collection Examples | jq -c "{file,line}"\n'
    '  Refuses to run as root by default (pass --allow-root to override). Warns when\n'
    '  the watch target looks like a system path (pass --allow-system-paths to suppress).\n'
    '\n'
    '── Compositions (multi-flag workflows from the User Guide) ──────────\n'
    '  Live pattern sweep — folder watcher + regex collection, streams NDJSON to stdout:\n'
    '    peekdocs --watch --regex-collection NAME -d ~/folder -r | jq -c "{file,line,pattern_name}"\n'
    '\n'
    '  Provenance audit — baseline → later capture → diff, --hash for content-level change detection:\n'
    '    peekdocs --hash --stdout budget > baseline.json         # capture with SHA-256 fingerprints\n'
    '    peekdocs --hash --stdout budget > current.json          # later, same command → new snapshot\n'
    '    peekdocs --diff baseline.json current.json              # what changed? (see --diff above)\n'
    '\n'
    '  Scheduled pattern scan — cron / Task Scheduler + saved collection + timestamped output:\n'
    '    peekdocs --regex-collection NAME -r --timestamp --output-dir /var/log/peekdocs\n'
    '    (Pair with --on-match for notifications when patterns actually appear.)\n'
    '\n'
    '── Portable use — USB-carried standalone binary (no install on host) ────────\n'
    '  peekdocs --check                                # verify Python deps + Tesseract before deploy\n'
    '  peekdocs --output-dir /Volumes/USB/reports \\    # reports back to the USB, not the client drive\n'
    '      --no-index --timestamp budget               # --no-index = zero artifacts on client drive\n'
    '  peekdocs --hash --stdout budget \\               # provenance snapshot back to USB\n'
    '      > /Volumes/USB/reports/baseline.json\n'
    '  Every file peekdocs writes carries a peekdocs_ or .peekdocs prefix — cleanup is one\n'
    '  find command (Unix) or Get-ChildItem pipeline (Windows PowerShell) at the end of\n'
    '  the session. See the User Guide § Portable use for the full workflow.\n'
    '\n'
    '── Cleanup (current directory only — never subdirectories) ────────────────\n'
    '  peekdocs --list-files          List all peekdocs-created files\n'
    '  peekdocs --clear               Delete peekdocs_*_results* files\n'
    '  peekdocs --clear-all           Delete all peekdocs output files (results, saved reports,\n'
    '                                   accumulated reports, error log, and search index)\n'
    '\n'
    '  Neither command deletes .peekdocs_collection.json (saved searches and suites),\n'
    '  ~/.peekdocsrc (settings), or bookmarks. These are user work, not output — delete\n'
    '  manually if needed (rm .peekdocs_collection.json, etc.).\n'
    '\n'
    '  See Advanced Search Options in the GUI for the full list of search settings.'
)

# Short quick-reference shown when user types just `peekdocs` with no arguments.
BANNER_QUICK = (
    '\npeekdocs — privacy-first local document search. 100+ file types, keyword/fuzzy/OCR/regex. GUI: run peekdocs-gui\n'
    '\n'
    'Usage: cd /path/to/your/documents && peekdocs [OPTIONS] TERM [TERM ...]\n'
    '       Navigate to the folder you want to search, then run peekdocs.\n'
    '       By default, only the current folder is searched. Use -r to include subfolders.\n'
    '\n'
    '── Search Modes (examples — flags can be combined freely) ────────\n'
    '  peekdocs term1 term2           OR search (any term matches)\n'
    '  peekdocs -a term1 term2        AND search (all terms required in same line)\n'
    '  peekdocs -e "(A AND B) OR C"   Boolean expression with AND, OR, NOT, parens\n'
    '  peekdocs -x "\\bREF-\\d{4,}\\b"   Regex pattern matching\n'
    '  peekdocs -w "budg*"            Wildcard (* = any chars, ? = one char)\n'
    '  peekdocs -z budgt              Fuzzy matching (typo-tolerant)\n'
    '  peekdocs -W bob                Whole-word only (not "bobcat")\n'
    '  peekdocs -p 5 budget revenue   Word proximity (terms within 5 words of each other)\n'
    '  peekdocs -P 3 budget acme      Line proximity (terms within 3 lines of each other)\n'
    '  peekdocs --inverse budget      Find files that do NOT contain "budget"\n'
    '  peekdocs -n draft budget       Find "budget" but exclude lines containing "draft"\n'
    '  peekdocs -f report.pdf budget  Search only report.pdf for "budget"\n'
    '  peekdocs -s quarterly budget   Save a named copy of the report\n'
    '  peekdocs -sa archive budget    Append results to accumulated report\n'
    '  peekdocs --open docx budget    Search and auto-open the highlighted Word report\n'
    '  peekdocs --open html budget    Search, generate HTML, and open in browser\n'
    '  peekdocs -sa archive --open docx budget  Append and open accumulated report\n'
    '\n'
    '── Common Options ───────────────────────────────────────────────\n'
    '  peekdocs -r budget               Search all subfolders recursively\n'
    '  peekdocs -t pdf,docx budget      Search only PDF and Word files\n'
    '  peekdocs -A 5 -B 5 budget        Show 5 lines before and after each match\n'
    '  peekdocs -R amount:1000..5000 "" Filter by dollar range\n'
    '  peekdocs -O budget               Enable OCR for scanned PDFs and images\n'
    '  peekdocs -o docx,csv,json,pdf,html budget  Opt-in output formats (any combination; .txt is always written)\n'
    '  peekdocs -m 10000 budget         Max matches in reports (0 = no limit, default: 5000)\n'
    '  peekdocs --max-file-size 500     Skip files larger than 500 MB (default 100, 0 = no limit)\n'
    '  peekdocs --index                 Build search index for faster repeated searches\n'
    '  peekdocs --suite "My Suite"      Run a saved search suite by name (auto-locates folder)\n'
    '  peekdocs --suite ~/Documents/MyDocs/"Example 1"  Run a suite by full path (explicit folder)\n'
    '  peekdocs --list-suites           List every known suite and its folder\n'
    '  peekdocs --regex-collection "name"  Run a saved regex collection by name\n'
    '  peekdocs --regex-collection --list  List all saved regex collections\n'
    '  peekdocs --config max_matches=5000  Save a default setting permanently\n'
    '  peekdocs --stdout -r budget      Output JSON to stdout for piping (no report files)\n'
    '  peekdocs -r -a -t pdf budget revenue  Combine: recursive, AND, PDF only\n'
    '\n'
    '  Cannot combine: -x (regex), -z (fuzzy), -w (wildcard) — pick one.\n'
    '  Cannot combine: -e (expression) with -a (AND), -n (exclude), or -p (proximity).\n'
    '\n'
    '── Regex ────────────────────────────────────────────────────────\n'
    '  peekdocs --regex-collection Examples    Run the seeded universal-pattern\n'
    '                                            collection (email, URL, IPv4/IPv6,\n'
    '                                            ISO date/time, UUID, semver, hex\n'
    '                                            color, MD link, TODO/FIXME, JIRA\n'
    '                                            ticket, ISBN-13, DOI, USD amount,\n'
    '                                            env var). Seeded on first GUI\n'
    '                                            open of Regex Search; modify or\n'
    '                                            delete freely once seeded.\n'
    '\n'
    '  Regex collection output: TXT report always written (every match grouped by\n'
    '  pattern). DOCX / HTML / CSV / JSON / PDF are opt-in via -o; combine any:\n'
    '    peekdocs --regex-collection Examples                        TXT only\n'
    '    peekdocs --regex-collection Examples -o docx                TXT + DOCX\n'
    '    peekdocs --regex-collection Examples -o docx,html,csv       TXT + 3 more\n'
    '  DOCX and PDF are skipped above 25,000 total matches (in-memory build).\n'
    '\n'
    '  For more patterns, the syntax cheatsheet, or AI-generated regex:\n'
    '    regex101.com           — interactive tester + community pattern library\n'
    '    ihateregex.io          — common patterns with explanations\n'
    '    developer.mozilla.org  — regex syntax reference / cheatsheet\n'
    '\n'
    '── Folder watcher (long-running, NDJSON to stdout) ──────────────────\n'
    '  peekdocs --watch -d ~/folder --regex-collection NAME      Watch + stream matches\n'
    '  peekdocs --watch -d ~/folder --regex-collection NAME -r   Recursive into subfolders\n'
    '\n'
    '  Emits one JSON record per match to stdout while files are created or modified;\n'
    '  status / warnings go to stderr so the stdout stream stays a clean NDJSON pipe.\n'
    '  Ctrl-C stops cleanly (exit 0). Compose with anything that reads JSON Lines:\n'
    '    peekdocs --watch -d ~/Downloads --regex-collection Examples > matches.ndjson\n'
    '    peekdocs --watch -d ~/repo --regex-collection Examples | jq -c "{file,line}"\n'
    '  Refuses to run as root by default (pass --allow-root to override). Warns when\n'
    '  the watch target looks like a system path (pass --allow-system-paths to suppress).\n'
    '\n'
    '── Compositions (multi-flag workflows from the User Guide) ──────────\n'
    '  Live pattern sweep — folder watcher + regex collection, streams NDJSON to stdout:\n'
    '    peekdocs --watch --regex-collection NAME -d ~/folder -r | jq -c "{file,line,pattern_name}"\n'
    '\n'
    '  Provenance audit — baseline → later capture → diff, --hash for content-level change detection:\n'
    '    peekdocs --hash --stdout budget > baseline.json         # capture with SHA-256 fingerprints\n'
    '    peekdocs --hash --stdout budget > current.json          # later, same command → new snapshot\n'
    '    peekdocs --diff baseline.json current.json              # what changed? (see --diff above)\n'
    '\n'
    '  Scheduled pattern scan — cron / Task Scheduler + saved collection + timestamped output:\n'
    '    peekdocs --regex-collection NAME -r --timestamp --output-dir /var/log/peekdocs\n'
    '    (Pair with --on-match for notifications when patterns actually appear.)\n'
    '\n'
    '── Portable use — USB-carried standalone binary (no install on host) ────────\n'
    '  peekdocs --check                                # verify Python deps + Tesseract before deploy\n'
    '  peekdocs --output-dir /Volumes/USB/reports \\    # reports back to the USB, not the client drive\n'
    '      --no-index --timestamp budget               # --no-index = zero artifacts on client drive\n'
    '  peekdocs --hash --stdout budget \\               # provenance snapshot back to USB\n'
    '      > /Volumes/USB/reports/baseline.json\n'
    '  Every file peekdocs writes carries a peekdocs_ or .peekdocs prefix — cleanup is one\n'
    '  find command (Unix) or Get-ChildItem pipeline (Windows PowerShell) at the end of\n'
    '  the session. See the User Guide § Portable use for the full workflow.\n'
    '\n'
    '── Cleanup (current directory only — never subdirectories) ────────────────\n'
    '  peekdocs --list-files          List all peekdocs-created files\n'
    '  peekdocs --clear               Delete peekdocs_*_results* files\n'
    '  peekdocs --clear-all           Delete all peekdocs output files\n'
    '                                   (Saved searches, settings, and bookmarks preserved — see -h.)\n'
    '\n'
    'Exit codes: 0 = matches found, 1 = no matches, 2 = error.\n'
    '\n'
    'Type peekdocs -h for full help (all flags, file types, examples).\n'
)

CONFIG_BOOL_KEYS = {"recursive", "quiet", "match_all", "regex", "ocr", "fuzzy", "wildcard", "whole_word", "index_search", "output_docx", "output_csv", "output_json", "output_pdf", "output_html", "inverse", "timestamp", "hover_text", "delete_reports_on_close", "clear_history_on_close", "restrict_permissions", "run_log", "suite_html", "suite_csv", "suite_json", "suite_pdf", "redirect_cloud_output"}
CONFIG_INT_KEYS = {"cores", "context_before", "context_after", "proximity", "max_matches", "max_file_size_mb"}
CONFIG_STR_KEYS = {"file_types", "search_terms", "folder", "exclude", "specific_files", "save_name", "append_name", "output_dir", "range", "refresh_interval", "text_size", "preview_size", "appearance_mode", "assistant_history", "run_log_path", "on_match"}
CONFIG_ALL_KEYS = CONFIG_BOOL_KEYS | CONFIG_INT_KEYS | CONFIG_STR_KEYS


def _config_path() -> str:
    """Return the path to ~/.peekdocsrc."""
    return os.path.join(os.path.expanduser("~"), ".peekdocsrc")


def _load_config() -> dict[str, Any]:
    """Load defaults from ~/.peekdocsrc if it exists."""
    path = _config_path()
    if not os.path.exists(path):
        return {}
    config: dict[str, Any] = {}
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
            elif key.startswith("regex_search_"):
                # Regex Search popup settings — dynamic keys
                if value.lower() in ("true", "false"):
                    config[key] = value.lower() == "true"
                else:
                    config[key] = value
    return config


def _save_config(settings: dict[str, Any]) -> None:
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
    # Restrict to owner read-write only
    try:
        import stat
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass  # Windows may not support Unix permissions


# Re-export from scanner so tests can monkeypatch via peekdocs.cli
from peekdocs.scanner import _process_file, _ocr_image, discover_files, _extract_lines, _search_file_lines, RESULT_FILE_PREFIXES  # noqa: E402
from peekdocs.parser import parse_flags  # noqa: E402
from peekdocs.paths import find_tesseract  # noqa: E402
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


def _warn_unsupported_flags(
    args_tail: list[str],
    command_name: str,
    supported: set[str] | frozenset[str],
    value_taking: tuple[str, ...] | set[str] | frozenset[str] = (),
) -> None:
    """Warn to stderr about flags ``command_name`` does not honor.

    ``args_tail`` is what's left after the command's own already-consumed
    flags have been stripped — typically ``args[2:]`` with `-o VAL` and
    `--timestamp` already removed. ``supported`` is the set of flag
    strings the handler reads; ``value_taking`` lists supported flags
    that swallow a following value (so the value isn't misclassified as
    an unsupported flag).

    Silent in the well-behaved case. One stderr line per surplus flag.
    """
    surplus = []
    i = 0
    while i < len(args_tail):
        tok = args_tail[i]
        if tok in value_taking:
            i += 2
            continue
        if tok.startswith("-") and tok not in supported:
            surplus.append(tok)
        i += 1
    if surplus:
        print(
            f"Warning: {command_name} ignored these flags: {' '.join(surplus)}",
            file=sys.stderr,
        )
        print(
            f"         {command_name} reads only: {', '.join(sorted(supported))}",
            file=sys.stderr,
        )


def _get_pkg_version(package: str) -> str:
    """Return the installed version of a package, or '?' if unavailable."""
    try:
        return pkg_version(package)
    except Exception:
        return "?"


def _cli_cloud_guard_or_exit(
    output_dir: str,
    config: dict[str, Any],
    allow_cloud: bool,
    quiet: bool = False,
) -> str | None:
    """CLI-side cloud-output guard.

    Runs the central policy check from _helpers.cloud_output_guard and
    resolves it to a CLI-appropriate action:

      SAFE       — return output_dir unchanged.
      REDIRECTED — user has redirect_cloud_output set; print a note
                   (unless --quiet) and return the safe alternative.
      ALLOWED    — user passed --allow-cloud-output; print a warning
                   to stderr and return output_dir unchanged.
      PROMPT     — cloud detected, no policy — print an error to
                   stderr and return None. Caller should treat None
                   as "abort with exit code 2".
    """
    from peekdocs.gui._helpers import (
        cloud_output_guard,
        CLOUD_GUARD_SAFE, CLOUD_GUARD_REDIRECTED,
        CLOUD_GUARD_ALLOWED, CLOUD_GUARD_PROMPT,
    )
    redirect = bool(config.get("redirect_cloud_output", False))
    # cloud_output_guard is untyped upstream (mypy scope stops at this
    # file's boundary), so widen the destructured names explicitly.
    _guard_result = cloud_output_guard(
        output_dir, redirect_to_safe=redirect, allow_cloud=allow_cloud,
    )
    final_dir: str = _guard_result[0]
    outcome: str = _guard_result[1]
    service: str = _guard_result[2]
    if outcome == CLOUD_GUARD_SAFE:
        return final_dir
    if outcome == CLOUD_GUARD_REDIRECTED:
        if not quiet:
            print(
                f"Note: output directory is inside {service}; "
                f"redirecting reports to {final_dir} "
                f"(unset 'redirect_cloud_output' in ~/.peekdocsrc to disable).",
                file=sys.stderr,
            )
        return final_dir
    if outcome == CLOUD_GUARD_ALLOWED:
        print(
            f"Warning: --allow-cloud-output — writing reports to "
            f"{service}-synced folder {final_dir}. Reports will be "
            f"uploaded by {service}.",
            file=sys.stderr,
        )
        return final_dir
    # PROMPT
    print(
        f"Error: output directory is inside {service}:\n"
        f"  {output_dir}\n"
        f"Reports written there would be uploaded to {service}. "
        f"To proceed, either:\n"
        f"  • pass --allow-cloud-output to write anyway (one-off), or\n"
        f"  • set redirect_cloud_output=true in ~/.peekdocsrc\n"
        f"    (peekdocs --config redirect_cloud_output=true) to always\n"
        f"    redirect cloud-synced outputs to ~/peekdocs_reports.",
        file=sys.stderr,
    )
    return None


def _check_dependencies() -> list[tuple[str, str, str, str]]:
    """Check that all required modules can be imported.

    Returns list of (module_display, package, status, version) tuples.
    """
    results: list[tuple[str, str, str, str]] = []
    for module_name, package, description in _REQUIRED_MODULES:
        try:
            __import__(module_name)
            ver = _get_pkg_version(package)
            results.append((description, package, "ok", ver))
        except ImportError as e:
            results.append((description, package, "MISSING", str(e)))
    return results


def _check_optional_dependencies() -> list[tuple[str, str, str, str]]:
    """Check optional modules. Returns list of (description, package, status, version) tuples."""
    results: list[tuple[str, str, str, str]] = []
    for module_name, package, description in _OPTIONAL_MODULES:
        try:
            __import__(module_name)
            ver = _get_pkg_version(package)
            results.append((description, package, "ok", ver))
        except ImportError:
            results.append((description, package, "not installed", ""))
    return results


def _dep_versions_str() -> str:
    """Return a formatted string of all dependency versions for crash reports."""
    import sqlite3
    lines: list[str] = []
    for desc, pkg, status, ver in _check_dependencies():
        lines.append(f"  {pkg}: {ver}" if status == "ok" else f"  {pkg}: MISSING")
    for desc, pkg, status, ver in _check_optional_dependencies():
        if status == "ok":
            lines.append(f"  {pkg}: {ver}")
    lines.append(f"  sqlite3: {sqlite3.sqlite_version}")
    return "\n".join(lines)


def run_system_check() -> dict[str, Any]:
    """Gather installation health data for the --check CLI command and the GUI System Check.

    Returns a dict with structured results suitable for either text or UI display.
    """
    import sqlite3
    v = sys.version_info[:2]
    if v < TESTED_PYTHON_MIN:
        py_status = "below_min"
    elif v > TESTED_PYTHON_MAX:
        py_status = "above_max"
    else:
        py_status = "ok"

    required = _check_dependencies()
    optional = _check_optional_dependencies()
    all_required_ok = all(status == "ok" for _, _, status, _ in required)

    cwd = os.getcwd()
    free = shutil.disk_usage(cwd).free

    return {
        "peekdocs_version": VERSION,
        "python_version_tuple": v,
        "python_version_full": sys.version,
        "python_status": py_status,
        "tested_python_min": TESTED_PYTHON_MIN,
        "tested_python_max": TESTED_PYTHON_MAX,
        "os_system": platform.system(),
        "os_release": platform.release(),
        "required_deps": required,
        "optional_deps": optional,
        "tesseract_installed": find_tesseract() is not None,
        "sqlite_version": sqlite3.sqlite_version,
        "disk_free_bytes": free,
        "disk_free_human": fmt_size(free),
        "disk_low": free < 10_000_000,
        "cwd": cwd,
        "all_ok": all_required_ok,
    }


def _check_python_version() -> str | None:
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


def _diagnose(exc: BaseException) -> str:
    """Return a plain-English diagnosis based on the exception type and message."""
    name = type(exc).__name__
    msg = str(exc).lower()

    if isinstance(exc, ImportError):
        module = getattr(exc, "name", "") or ""
        if module:
            return (f"The Python module '{module}' could not be loaded. "
                    "This is usually caused by a missing or incompatible dependency. "
                    "Try: pipx upgrade peekdocs  (or see https://github.com/exbuf/peekdocs#installation)")
        return ("A required module could not be imported. "
                "A dependency may be missing or incompatible with your Python version. "
                "Try reinstalling: pipx upgrade peekdocs  (or see https://github.com/exbuf/peekdocs#installation)")

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


def _dry_run_report(
    cwd: str,
    recursive: bool,
    use_ocr: bool,
    file_types: list[str] | str | None,
    file_names: list[str] | str | None,
    max_file_size_mb: int | None,
    emit_json: bool,
) -> int:
    """Print/emit a scope report of what a real search would touch.

    Walks discovery only — no content read, no pattern matching, no reports,
    no index. Returns 0 if files would be searched, 1 if zero, 2 if discovery
    errors out.
    """
    # Discovery itself is the slow step on huge trees (e.g. recursive
    # walk of $HOME). discover_files() runs glob.glob() per supported
    # extension across the whole tree before returning, so it can sit
    # silently for minutes. Print a hint to stderr so the user knows
    # something is happening. Emitted only when not in JSON output mode.
    if not emit_json:
        import sys as _sys_scan
        print(f"Scanning files (this may take a while on large folders)...", file=_sys_scan.stderr, flush=True)
    discovered = discover_files(
        cwd, recursive, use_ocr,
        file_types=file_types,
        file_names=file_names,
    )
    # discover_files returns (exit_code, message) on error
    if isinstance(discovered, tuple):
        print(f"Error: {discovered[1]}")
        return int(discovered[0])

    # Apply max-file-size filter the way the real search does
    max_bytes = max_file_size_mb * 1024 * 1024 if max_file_size_mb and max_file_size_mb > 0 else 0
    files_kept: list[str] = []
    skipped_too_large = 0
    total_bytes = 0
    by_ext: dict[str, dict[str, int]] = {}
    for fp in discovered:
        try:
            size = os.path.getsize(fp)
        except OSError:
            continue
        if max_bytes and size > max_bytes:
            skipped_too_large += 1
            continue
        files_kept.append(fp)
        total_bytes += size
        ext = os.path.splitext(fp)[1].lower() or "(no ext)"
        if ext not in by_ext:
            by_ext[ext] = {"count": 0, "bytes": 0}
        by_ext[ext]["count"] += 1
        by_ext[ext]["bytes"] += size

    ext_rows: list[dict[str, Any]] = sorted(
        ({"ext": ext, "count": v["count"], "bytes": v["bytes"]} for ext, v in by_ext.items()),
        key=lambda r: (-int(r["count"]), r["ext"]),
    )

    if emit_json:
        payload = {
            "generator": f"peekdocs v{VERSION}",
            "dry_run": True,
            "directory": cwd,
            "recursive": bool(recursive),
            "use_ocr": bool(use_ocr),
            "file_count": len(files_kept),
            "total_bytes": total_bytes,
            "skipped_oversize": skipped_too_large,
            "max_file_size_mb": max_file_size_mb if max_file_size_mb else None,
            "by_extension": ext_rows,
        }
        sys.stdout.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        return 0 if files_kept else 1

    print()
    print(f"Dry run — would search {len(files_kept):,} file(s) ({fmt_size(total_bytes)}) in {cwd}")
    if recursive:
        print("  (recursive: subfolders included)")
    if skipped_too_large:
        print(f"  ({skipped_too_large} file(s) skipped — exceed --max-file-size {max_file_size_mb} MB)")
    if ext_rows:
        print()
        print("By extension:")
        ext_w = max(len(r["ext"]) for r in ext_rows)
        for row in ext_rows[:30]:
            print(f"  {row['ext'].ljust(ext_w)}   {row['count']:>6}   {fmt_size(row['bytes']):>10}")
        if len(ext_rows) > 30:
            print(f"  ... and {len(ext_rows) - 30} more extension(s)")
    print()
    print("No content read. No reports written. No index touched.")
    print("Remove --dry-run to run the actual search.")
    print()
    return 0 if files_kept else 1


def main(argv: list[str] | None = None) -> int:
    # Force UTF-8 output to prevent UnicodeEncodeError when printing
    # Unicode characters (progress bars, CJK filenames, etc.) on a
    # console or pipe whose default encoding is narrower than UTF-8
    # (Windows cp1252 being the common case).
    #
    # Reconfigure unconditionally — the original code only ran this
    # when sys.stdout.isatty(), which skipped every subprocess /
    # captured-pipe invocation (smoke tests, user pipes, cron jobs
    # logging to file) and let them crash on non-cp1252 content. The
    # GUI subprocess invocation in peekdocs/gui/_helpers.py already
    # sets PYTHONIOENCODING=utf-8 so a redundant reconfigure here is
    # an idempotent no-op for that path.
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

    # Snapshot the original argv (after --no-log / --on-match are filtered)
    # for the run log. _main_inner mutates its args list while parsing flags,
    # so we capture what the user actually typed before any of that happens.
    from peekdocs import run_log as _rl
    _rl.reset_stats()
    incoming = list(sys.argv[1:] if argv is None else argv)

    no_log = "--no-log" in incoming
    on_match_cmd, on_match_explicit = _extract_on_match(incoming)
    # If --on-match wasn't on the command line, fall back to the persistent
    # default from ~/.peekdocsrc. An explicit empty string (--on-match "")
    # disables the hook for this run even if config says otherwise.
    if not on_match_explicit:
        on_match_cmd = _rl._config_value("on_match") or ""

    # Filter --no-log and --on-match (+value) out of args before _main_inner
    # sees them, both in the caller's list (if passed) and in sys.argv.
    cleaned = [a for a in incoming if a != "--no-log"]
    cleaned = _strip_on_match(cleaned)
    if argv is not None and isinstance(argv, list):
        argv[:] = cleaned
    else:
        sys.argv = [sys.argv[0]] + cleaned
    incoming_for_log = cleaned

    cwd_at_start = os.getcwd()
    start_time = time.time()

    try:
        exit_code = _main_inner(argv)
    except KeyboardInterrupt:
        print("\nSearch cancelled.\n")
        exit_code = 2
    except Exception as exc:
        exit_code = _handle_unexpected_exception(exc, argv)

    elapsed = time.time() - start_time
    stats = _rl.get_stats()
    report_paths = stats.pop("report_paths", {})

    # Fire the --on-match hook on a successful match-finding run.
    on_match_fired = False
    if (on_match_cmd
            and exit_code == 0
            and _rl.is_search_invocation(incoming_for_log)
            and stats.get("match_count", 0) > 0):
        on_match_fired = _rl.fire_on_match(
            command=on_match_cmd,
            argv=["peekdocs"] + incoming_for_log,
            cwd=cwd_at_start,
            match_count=stats.get("match_count", 0),
            file_count=stats.get("file_count", 0),
            error_count=stats.get("error_count", 0),
            elapsed_seconds=elapsed,
            report_paths=report_paths,
        )

    if (not no_log
            and _rl.is_search_invocation(incoming_for_log)
            and _rl.is_enabled()):
        extra = {}
        if on_match_cmd:
            extra["on_match_fired"] = on_match_fired
        _rl.record_run(
            argv=["peekdocs"] + incoming_for_log,
            cwd=cwd_at_start,
            exit_code=exit_code,
            elapsed_seconds=elapsed,
            on_match_fired=on_match_fired if on_match_cmd else None,
            **stats,
        )
    return exit_code


def _extract_on_match(args: list[str]) -> tuple[str, bool]:
    """Return (command, explicit_flag_present) without mutating *args*.

    `peekdocs --on-match "/path/to/script"` → ("/path/to/script", True)
    `peekdocs --on-match ""`               → ("", True)  # disable for this run
    `peekdocs ...` (no flag)               → ("", False)
    """
    if "--on-match" in args:
        idx = args.index("--on-match")
        if idx + 1 < len(args):
            return (args[idx + 1], True)
        return ("", True)  # treat trailing --on-match as "disable"
    return ("", False)


def _strip_on_match(args: list[str]) -> list[str]:
    """Return a copy of *args* with `--on-match` and its value removed."""
    out: list[str] = []
    i = 0
    while i < len(args):
        if args[i] == "--on-match":
            i += 2  # skip flag and its value
            continue
        out.append(args[i])
        i += 1
    return out


def _handle_unexpected_exception(exc: BaseException, argv: list[str] | None) -> int:
    """Crash-report path, extracted so main() can wrap with run logging."""
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


def _main_inner(argv: list[str] | None = None) -> int:
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
        print(f"\nOr reinstall peekdocs: pipx upgrade peekdocs  (or see https://github.com/exbuf/peekdocs#installation)\n")
        return 2

    original_args = list(args)

    config: dict[str, Any] = {}  # CLI uses only explicit flags; config is for GUI only

    stdout_json = "--stdout" in args
    if stdout_json:
        args.remove("--stdout")

    # Cloud-output guard: explicit --allow-cloud-output overrides the
    # cloud-sync-folder detection at every report-write path (Standard
    # / Suite / Regex Search). Without it and without the sticky
    # `redirect_cloud_output` config, writing to a cloud-synced
    # output_dir errors out — the peekdocs no-cloud-confidentiality
    # claim (README auditor bullet, USER_GUIDE) is a write-time
    # guarantee, not a search-time one.
    allow_cloud_output = "--allow-cloud-output" in args
    if allow_cloud_output:
        args.remove("--allow-cloud-output")

    compute_hashes = "--hash" in args
    if compute_hashes:
        args.remove("--hash")

    dry_run = "--dry-run" in args
    if dry_run:
        args.remove("--dry-run")

    # --runs --json and --diff ... --json must emit clean JSON with no banner
    # above. Same rationale as --stdout.
    runs_json = (args and args[0] == "--runs" and "--json" in args[1:])
    diff_json = (args and args[0] == "--diff" and "--json" in args[1:])

    minimal = stdout_json or runs_json or diff_json or "-qq" in args
    if "-qq" in args:
        args.remove("-qq")
    quiet = minimal or "-q" in args
    if "-q" in args:
        args.remove("-q")

    cpu_count = os.cpu_count() or 1
    is_help = args and args[0] in ("-h", "-help", "--help")

    if args and args[0] in ("-v", "-version", "--version"):
        print(f"peekdocs {VERSION}\n")
        return 0

    if is_help:
        # Full reference: all flags, file types, regex patterns
        print(f'\npeekdocs v{VERSION}')
        print(f'Your system has {cpu_count} CPU cores (default for -c: {max(1, cpu_count // 2)})')
        print('Readme documentation: https://github.com/exbuf/peekdocs/blob/main/README.md')
        print(BANNER_TOP)
        print(BANNER_BOTTOM)
        print()
        print('Type peekdocs for a quick command reference.')
        return 0

    if not args:
        print(f'\npeekdocs v{VERSION}')
        print(f'Your system has {cpu_count} CPU cores (default for -c: {max(1, cpu_count // 2)})')
        print('Readme documentation: https://github.com/exbuf/peekdocs/blob/main/README.md')
        print(BANNER_QUICK)
        return 0

    # The watcher mode emits NDJSON to stdout — banner and "no index"
    # notes would pollute that stream and break downstream consumers
    # (jq, log shippers). Suppress all preamble unconditionally when
    # --watch is present; status / warnings still go to stderr from
    # peekdocs/watcher.py.
    _is_watch_mode = "--watch" in args
    if not quiet and not _is_watch_mode:
        # Normal search: show short banner before search runs
        print(f'\npeekdocs v{VERSION}')
        print(f'Your system has {cpu_count} CPU cores (default for -c: {max(1, cpu_count // 2)})')
        # Conditional first-run index notice: only when the search folder
        # has no .peekdocs.db yet, on commands that will actually search.
        _non_search_commands = {
            "--check", "--list-files", "--clear", "--clear-all",
            "--runs", "--diff", "--index", "--index-status",
            "--index-refresh", "--index-clear", "--config",
        }
        _is_search_command = not (args and args[0] in _non_search_commands)
        if _is_search_command and "--no-index" not in args:
            _search_folder = os.getcwd()
            for _i, _arg in enumerate(args):
                if _arg in ("-d", "--directory") and _i + 1 < len(args):
                    if os.path.isdir(args[_i + 1]):
                        _search_folder = args[_i + 1]
                    break
            if not os.path.exists(os.path.join(_search_folder, ".peekdocs.db")):
                print('Note: no search index for this folder yet — the first search builds')
                print('  one (may take longer); subsequent searches are much faster.')
                print('  Use --no-index to skip indexing entirely.')
        print('-------------------------------------------------------------------------')

    if args and args[0] == "--check":
        info = run_system_check()
        print(f"peekdocs {info['peekdocs_version']}")
        print(f"Python {info['python_version_full']}")
        print(f"OS: {info['os_system']} {info['os_release']}")
        print()

        v = info['python_version_tuple']
        py_min = info['tested_python_min']
        py_max = info['tested_python_max']
        if info['python_status'] == "below_min":
            print(f"Python version:  {v[0]}.{v[1]} (BELOW minimum {py_min[0]}.{py_min[1]}) — upgrade Python to {py_min[0]}.{py_min[1]} or later")
        elif info['python_status'] == "above_max":
            print(f"Python version:  {v[0]}.{v[1]} (above maximum tested {py_max[0]}.{py_max[1]}) — should work, but not yet verified")
        else:
            print(f"Python version:  {v[0]}.{v[1]} (ok)")
        print()

        print("Required dependencies:")
        for desc, pkg, status, ver in info['required_deps']:
            if status == "ok":
                print(f"  {desc} ({pkg}): ok (v{ver})")
            else:
                print(f"  {desc} ({pkg}): MISSING — install with: pip install {pkg}")
        print()

        print("Optional dependencies:")
        for desc, pkg, status, ver in info['optional_deps']:
            if status == "ok":
                print(f"  {desc} ({pkg}): ok (v{ver})")
            else:
                print(f"  {desc} ({pkg}): not installed — install with: pip install {pkg}")
        print()

        if info['tesseract_installed']:
            print("Tesseract OCR:   installed (OCR available with -O flag)")
        else:
            print("Tesseract OCR:   not installed (optional — needed only for -O flag)")

        print(f"SQLite version:  {info['sqlite_version']}")
        print()

        print(f"Disk space:      {info['disk_free_human']} free")
        if info['disk_low']:
            print("  Warning: Low disk space. Reports may fail to write.")
        print()

        if not info['all_ok']:
            print("Fix missing dependencies with: pipx upgrade peekdocs  (or see https://github.com/exbuf/peekdocs#installation)")
            print()
        else:
            print("All checks passed.")
            print()

        return 0 if info['all_ok'] else 2

    if args and args[0] == "--list-files":
        cwd = os.getcwd()
        found = []
        for f in sorted(os.listdir(cwd)):
            if (f.startswith(RESULT_FILE_PREFIXES) or
                f.startswith("peekdocs_report_") or
                f.startswith("peekdocs_accumulated_") or
                f in ("peekdocs_errors.log", ".peekdocs.db", ".peekdocs.db-wal",
                       ".peekdocs.db-shm", ".peekdocs_collection.json")):
                size = os.path.getsize(os.path.join(cwd, f))
                if size >= 1_000_000:
                    size_str = f"{size / 1_000_000:.2f} MB"
                elif size >= 1_000:
                    size_str = f"{size / 1_000:.2f} KB"
                else:
                    size_str = f"{size} bytes"
                found.append((f, size_str))
        if found:
            print(f"\npeekdocs files in {cwd}:\n")
            for f, size_str in found:
                print(f"  {f}  ({size_str})")
            print(f"\n{len(found)} file(s). Use --clear to delete results, --clear-all to delete everything.")
        else:
            print(f"\nNo peekdocs files found in {cwd}.")
        print()
        return 0

    if args and args[0] in ("--clear", "--clear-all"):
        cwd = os.getcwd()
        clear_all = args[0] == "--clear-all"
        deleted = []

        # Always delete results files
        for f in os.listdir(cwd):
            if f.startswith(RESULT_FILE_PREFIXES):
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
        else:
            print("\nPreserved (not deleted): saved searches (.peekdocs_collection.json),")
            print("settings (~/.peekdocsrc), and bookmarks. Remove manually if needed.")
            print()
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

    if args and args[0] in ("-s", "-save", "--save"):
        if len(args) < 2:
            print("Error: No filename provided. Usage: peekdocs -s name_of_your_file\n")
            return 2
        name = "_".join(args[1:]).replace(" ", "_")
        cwd = os.getcwd()
        save_dir = _load_config().get("output_dir", cwd)
        src_docx = os.path.join(save_dir, "peekdocs_standard_results.docx")
        src_txt = os.path.join(save_dir, "peekdocs_standard_results.txt")
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
        if config_args and config_args[0] == "--reset":
            rc_path = os.path.expanduser("~/.peekdocsrc")
            if os.path.exists(rc_path):
                os.remove(rc_path)
                print("Saved defaults deleted (~/.peekdocsrc). All settings reset to factory defaults.\n")
            else:
                print("No saved defaults found — already at factory defaults.\n")
            return 0
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

    # ── --list-suites [--rescan]: show all suites and where they live ──
    # ── --diff OLD.json NEW.json [--json]: compare two JSON outputs ──
    if args and args[0] == "--diff":
        if len(args) < 3:
            print("Error: --diff requires two JSON file paths.", file=sys.stderr)
            print("Usage: peekdocs --diff peekdocs_snapshot_old.json peekdocs_snapshot_new.json [--json]\n", file=sys.stderr)
            return 2
        old_path = args[1]
        new_path = args[2]
        emit_json = "--json" in args[3:]

        # Friendly hint when the input is obviously a source document
        # (.odt, .docx, .pdf, etc.) rather than a peekdocs JSON snapshot.
        # --diff compares two scan results, not two documents.
        _doc_exts = {".odt", ".ods", ".odp", ".doc", ".docx", ".xls", ".xlsx",
                     ".ppt", ".pptx", ".pdf", ".rtf", ".pages", ".numbers",
                     ".key", ".txt", ".md", ".html", ".htm"}

        def _diff_input_hint(path):
            ext = os.path.splitext(path)[1].lower()
            if ext in _doc_exts:
                print(
                    f"\nHint: '{os.path.basename(path)}' looks like a document, not a peekdocs JSON snapshot.\n"
                    "      --diff compares two scan results, not two source documents.\n"
                    "      Produce a snapshot first, e.g.:\n"
                    "          peekdocs <terms> -r --stdout > peekdocs_snapshot_yesterday.json\n"
                    "          peekdocs <terms> -r --stdout > peekdocs_snapshot_today.json\n"
                    "          peekdocs --diff peekdocs_snapshot_yesterday.json peekdocs_snapshot_today.json\n"
                    "      To compare two documents directly, use a document comparison tool\n"
                    "      (LibreOffice: Edit → Track Changes → Compare Document).",
                    file=sys.stderr,
                )
            else:
                print(
                    "\nHint: --diff expects JSON files produced by peekdocs --stdout or -o json.",
                    file=sys.stderr,
                )

        from peekdocs.diff import load_json, compute_diff, format_human, is_actionable
        old_data, err = load_json(old_path)
        if err:
            print(f"Error reading old file: {err}", file=sys.stderr)
            _diff_input_hint(old_path)
            return 2
        new_data, err = load_json(new_path)
        if err:
            print(f"Error reading new file: {err}", file=sys.stderr)
            _diff_input_hint(new_path)
            return 2

        diff = compute_diff(old_data, new_data)
        if emit_json:
            sys.stdout.write(json.dumps(diff, indent=2, ensure_ascii=False) + "\n")
        else:
            sys.stdout.write(format_human(diff, old_path, new_path))
        # Exit 1 if anything actionable changed (new files, more matches,
        # content modified). Exit 0 if only removals or all unchanged.
        return 1 if is_actionable(diff) else 0

    # ── --runs [N] [--json]: show recent run-log entries ──
    if args and args[0] == "--runs":
        from peekdocs.run_log import read_recent, log_path
        emit_json = "--json" in args[1:]
        limit = 20
        for tok in args[1:]:
            if tok == "--json":
                continue
            try:
                limit = max(0, int(tok))
                break
            except ValueError:
                print(f"Error: --runs argument must be a positive integer. Got: {tok}\n")
                return 2
        entries = read_recent(limit=limit if limit > 0 else 0)
        if emit_json:
            for e in entries:
                sys.stdout.write(json.dumps(e, ensure_ascii=False) + "\n")
            return 0
        if not entries:
            print(f"No run log entries found. Log file: {log_path()}")
            print("(The log is written automatically after every search; use --no-log to skip a single run.)")
            return 0
        print(f"Run log: {log_path()}")
        print()
        print(f"{'Time':<19}  {'Exit':>4}  {'Matches':>8}  {'Files':>6}  {'Errors':>6}  {'Elapsed':>8}  Command")
        print(f"{'-'*19}  {'-'*4}  {'-'*8}  {'-'*6}  {'-'*6}  {'-'*8}  {'-'*40}")
        for e in entries:
            ts = (e.get("timestamp") or "")[:19]
            ec = e.get("exit_code", "")
            mc = e.get("match_count", 0)
            fc = e.get("file_count", 0)
            er = e.get("error_count", 0)
            el = e.get("elapsed_seconds", 0)
            cmd = " ".join(e.get("argv", []))
            if len(cmd) > 80:
                cmd = cmd[:77] + "..."
            print(f"{ts:<19}  {str(ec):>4}  {mc:>8}  {fc:>6}  {er:>6}  {el:>8.2f}  {cmd}")
        print()
        print(f"{len(entries)} run(s). --runs N for more, --runs --json for raw JSON Lines.")
        return 0

    if args and args[0] == "--list-suites":
        from peekdocs.suite_index import list_suites_global, rescan
        if "--rescan" in args[1:]:
            rescan()
        entries = list_suites_global()
        if not entries:
            print("No suites found.")
            print()
            print("Create one in the GUI (Tools → Search Suites), or run a search")
            print("first so peekdocs learns which folders to look in.")
            return 0
        name_w = max(len(e["name"]) for e in entries)
        name_w = max(name_w, len("Suite"))
        print(f"{'Suite'.ljust(name_w)}  Searches  Folder")
        print(f"{'-' * name_w}  --------  ------")
        for e in entries:
            print(f"{e['name'].ljust(name_w)}  {str(e['search_count']).rjust(8)}  {e['folder']}")
        print()
        print(f"{len(entries)} suite(s).  Run with:  peekdocs --suite \"<name>\"")
        return 0

    # ── --watch: long-running folder-watcher mode ──
    # Accepts --watch anywhere in args (not necessarily args[0]) so it
    # composes naturally with the existing --regex-collection / -d / -r
    # flags. Headline usage:
    #     peekdocs --watch -d <folder> --regex-collection NAME [-r]
    # NDJSON streams to stdout, status / warnings to stderr, exits 0 on
    # clean Ctrl-C. See peekdocs/watcher.py for design notes.
    if "--watch" in args:
        if dry_run:
            print("Error: --dry-run is not supported with --watch — the watcher")
            print("is a long-running mode, not a one-shot scope-preview command.\n")
            return 2
        # Consume --watch and any --watch-mode-only flags before falling
        # through to pattern source discovery.
        args = [a for a in args if a != "--watch"]
        _watch_allow_root = False
        if "--allow-root" in args:
            _watch_allow_root = True
            args = [a for a in args if a != "--allow-root"]
        _watch_allow_system_paths = False
        if "--allow-system-paths" in args:
            _watch_allow_system_paths = True
            args = [a for a in args if a != "--allow-system-paths"]
        # Folder from -d / --directory (default cwd)
        _watch_folder = os.getcwd()
        for _flag in ("-d", "--directory"):
            if _flag in args:
                _i = args.index(_flag)
                if _i + 1 < len(args):
                    _watch_folder = args[_i + 1]
                    del args[_i:_i + 2]
                else:
                    print(f"Error: {_flag} requires a folder path.\n")
                    return 2
        _watch_recursive = "-r" in args
        if "-r" in args:
            args = [a for a in args if a != "-r"]
        # Pattern source: --regex-collection NAME is the only supported
        # source in v1. Single -x "regex" and standard-search modes are
        # deferred — every realistic watcher workflow names its patterns,
        # and a saved collection gives the NDJSON output meaningful
        # pattern_name and collection fields out of the box.
        if "--regex-collection" not in args:
            print("Error: --watch requires --regex-collection NAME.\n"
                  "Usage:\n"
                  "  peekdocs --watch -d <folder> --regex-collection NAME [-r]\n")
            return 2
        _i = args.index("--regex-collection")
        if _i + 1 >= len(args):
            print("Error: --regex-collection requires a collection name.\n")
            return 2
        _watch_collection_name = args[_i + 1]
        _watch_rc_path = os.path.join(
            os.path.expanduser("~"), ".peekdocs_regex_collections.json"
        )
        if not os.path.exists(_watch_rc_path):
            print("No saved regex collections found. Create one in the GUI "
                  "(Regex Search → Save Collection As).\n")
            return 2
        try:
            with open(_watch_rc_path, "r", encoding="utf-8") as _f:
                _watch_rc_data = json.loads(_f.read())
        except Exception as exc:
            print(f"Error reading collections: {exc}\n")
            return 2
        if _watch_collection_name not in _watch_rc_data:
            _available = sorted(_watch_rc_data.keys())
            print(f"Collection '{_watch_collection_name}' not found.")
            if _available:
                print(f"Available collections: {', '.join(_available)}")
            return 2
        from peekdocs.watcher import WatcherConfig, run_watch
        _watch_cfg = WatcherConfig(
            folder=_watch_folder,
            patterns=_watch_rc_data[_watch_collection_name],
            collection_name=_watch_collection_name,
            recursive=_watch_recursive,
            allow_root=_watch_allow_root,
            allow_system_paths=_watch_allow_system_paths,
        )
        return int(run_watch(_watch_cfg))

    # ── --suite NAME: run a search suite ──
    if args and args[0] == "--suite":
        if dry_run:
            print("Error: --dry-run is not supported with --suite in this release.")
            print("Use --dry-run on a standard search to preview scope, or run --suite without --dry-run.\n")
            return 2
        if len(args) < 2:
            print("Error: --suite requires a suite name. Usage: peekdocs --suite \"My Suite\"\n")
            return 2
        suite_name = args[1]
        suite_ts_suffix = ""
        if "--timestamp" in args[2:]:
            args.remove("--timestamp")
            suite_ts_suffix = "_" + datetime.now().strftime("%Y%m%d_%H%M%S")

        # -o format opt-in (1.2.6 policy parity). TXT is always written.
        # DOCX joins when '-o docx' is passed. Other formats (HTML / CSV
        # / JSON / PDF) live as inline code in the GUI suite path and
        # aren't exposed via the CLI suite handler — the GUI is the
        # surface to reach for those formats on suites for now.
        _suite_output_formats = []
        if "-o" in args[2:]:
            _so_idx = args.index("-o", 2)
            if _so_idx + 1 >= len(args):
                print("Error: -o needs a format. CLI suite supports: docx.")
                return 2
            _suite_output_formats = [
                fmt.strip().lower() for fmt in args[_so_idx + 1].split(",")
                if fmt.strip()
            ]
            _suite_valid = {"docx"}
            for _fmt in _suite_output_formats:
                if _fmt not in _suite_valid:
                    print(
                        f"Error: CLI suite -o supports 'docx' only; "
                        f"got '{_fmt}'. For other formats (HTML / CSV / "
                        f"JSON / PDF) run the suite from the GUI Search "
                        f"Suites popup, which has checkboxes for each."
                    )
                    return 2
            # Strip -o and its argument from args so downstream parsing
            # doesn't see them.
            del args[_so_idx:_so_idx + 2]
        # Surplus-flag warning. After --timestamp and -o removal,
        # args[2:] should be empty for well-formed invocations. Anything
        # left is a flag the user passed that the suite handler doesn't
        # read (e.g. -t, -A, -B, -m) — saved searches inside the suite
        # carry their own params, and surplus CLI flags are silently
        # dropped without this warning.
        _warn_unsupported_flags(
            args[2:],
            command_name="--suite",
            supported={"--timestamp", "-o"},
            value_taking={"-o"},
        )
        cwd = os.getcwd()
        from peekdocs.collection import get_suite, get_search_params, load_collection

        # Accept a path-prefixed form like "/path/to/folder/Suite Name" — useful
        # when the same suite name exists in several folders, or when the user
        # copy-pastes from `peekdocs --list-suites` output.
        if (os.sep in suite_name or "/" in suite_name) and not get_suite(cwd, suite_name):
            head, tail = os.path.split(suite_name)
            if head and tail and os.path.isdir(head):
                if get_suite(head, tail) is not None:
                    cwd = os.path.abspath(head)
                    suite_name = tail

        suite_searches = get_suite(cwd, suite_name)
        if suite_searches is None:
            from peekdocs.suite_index import find_suite
            matches = find_suite(suite_name)
            if len(matches) == 1:
                cwd = matches[0]
                print(f"Suite '{suite_name}' found in {cwd}")
                suite_searches = get_suite(cwd, suite_name)
            elif len(matches) > 1:
                print(f"Suite '{suite_name}' exists in more than one folder:")
                for f in matches:
                    print(f"  {f}")
                print()
                print("Pick one by passing the full path, e.g.:")
                print(f'  peekdocs --suite {matches[0]}/"{suite_name}"')
                return 2
            else:
                available = list(load_collection(os.getcwd()).get("suites", {}).keys())
                print(f"Suite '{suite_name}' not found.")
                if available:
                    print(f"Available suites in this folder: {', '.join(available)}")
                print()
                print("List every known suite and its folder:")
                print("  peekdocs --list-suites")
                print()
                print("Or create one in the GUI (Tools → Search Suites).")
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

            # Convert saved-search params to api.search() kwargs.
            # Three modes to distinguish:
            #   - Expression mode (params["expression"] == True):
            #     search_text IS the boolean expression string; goes
            #     into api_search's `expression=` kwarg, and
            #     `search_terms` must be empty (the parser handles the
            #     whole string).
            #   - Regex / wildcard: single-token pattern; shlex would
            #     eat backslashes (r"print\(" -> "print(" with an
            #     unbalanced paren) so we pass search_text through raw.
            #   - Plain text: shlex-split so quoted phrases work.
            # Historic bug (repro'd from Quarterly Content Audit demo):
            # `expr = params.get("expression") if params.get(...)` set
            # expr to True instead of the search_text, and api_search's
            # tokenize() then raised AttributeError trying to strip() a
            # boolean.
            terms_str = params.get("search_text", "")
            if params.get("expression"):
                search_terms = []
                expr = terms_str or None
            elif params.get("regex") or params.get("wildcard"):
                search_terms = [terms_str] if terms_str else []
                expr = None
            else:
                import shlex as _shlex
                try:
                    search_terms = _shlex.split(terms_str) if terms_str else []
                except ValueError:
                    search_terms = terms_str.split() if terms_str else []
                expr = None
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

        # Cloud-output guard: block or redirect writes if the suite's
        # output folder is inside a cloud-synced directory.
        _guarded_cwd = _cli_cloud_guard_or_exit(cwd, config, allow_cloud_output, quiet=quiet)
        if _guarded_cwd is None:
            return 2
        cwd = _guarded_cwd

        txt_path = os.path.join(cwd, f"peekdocs_suite_results{suite_ts_suffix}.txt")
        docx_path = None
        write_suite_txt_report(txt_path, suite_name, sections)
        if "docx" in _suite_output_formats:
            docx_path = os.path.join(cwd, f"peekdocs_suite_results{suite_ts_suffix}.docx")
            write_suite_docx_report(docx_path, txt_path, sections)

        total_matches = sum(len(s["matches"]) for s in sections)
        total_files = sum(len(s.get("all_files", [])) for s in sections)
        print(f"\nSuite '{suite_name}': {len(sections)} search(es), {total_matches} total match(es)")
        print(f"Reports: {txt_path}")
        if docx_path:
            print(f"         {docx_path}")
        from peekdocs.run_log import set_stats as _set_stats_suite, set_report_paths as _set_paths_suite
        _set_stats_suite(match_count=total_matches, file_count=total_files)
        if docx_path:
            _set_paths_suite(txt=txt_path, docx=docx_path)
        else:
            _set_paths_suite(txt=txt_path)
        return 0

    # ── --regex-collection NAME: run a saved regex collection ──
    if args and args[0] == "--regex-collection":
        if dry_run:
            print("Error: --dry-run is not supported with --regex-collection in this release.")
            print("Use --dry-run on a standard search to preview scope.\n")
            return 2
        if len(args) < 2:
            print("Error: --regex-collection requires a collection name.\n"
                  "Usage: peekdocs --regex-collection \"code patterns\"\n"
                  "       peekdocs --regex-collection --list\n")
            return 2
        if args[1] == "--list":
            _rc_path = os.path.join(os.path.expanduser("~"), ".peekdocs_regex_collections.json")
            if not os.path.exists(_rc_path):
                print("No saved regex collections found.")
                return 0
            try:
                with open(_rc_path, "r", encoding="utf-8") as _rc_f:
                    _rc_data = json.loads(_rc_f.read())
                if not _rc_data:
                    print("No saved regex collections found.")
                    return 0
                print("Saved regex collections:")
                for _rc_name in sorted(_rc_data.keys()):
                    _rc_patterns = _rc_data[_rc_name]
                    _rc_enabled = sum(1 for p in _rc_patterns if p.get("enabled"))
                    print(f"  {_rc_name} ({_rc_enabled} enabled pattern(s))")
            except Exception as e:
                print(f"Error reading collections: {e}")
                return 2
            return 0

        collection_name = args[1]
        _rc_path = os.path.join(os.path.expanduser("~"), ".peekdocs_regex_collections.json")
        if not os.path.exists(_rc_path):
            print("No saved regex collections found. Create one in the GUI (Regex Search → Save Collection As).")
            return 2
        try:
            with open(_rc_path, "r", encoding="utf-8") as _rc_f:
                _rc_data = json.loads(_rc_f.read())
        except Exception as e:
            print(f"Error reading collections: {e}")
            return 2

        if collection_name not in _rc_data:
            available = sorted(_rc_data.keys())
            print(f"Collection '{collection_name}' not found.")
            if available:
                print(f"Available collections: {', '.join(available)}")
            return 2

        patterns = _rc_data[collection_name]
        active = [(p["name"], p["regex"]) for p in patterns if p.get("enabled") and p.get("regex", "").strip()]
        if not active:
            print(f"Collection '{collection_name}' has no enabled patterns with regex.")
            return 2

        # Parse remaining flags: -r, -d, --stdout, --timestamp, -o
        # Note: --stdout was already removed from args and stored in stdout_json
        _rc_recursive = "-r" in args[2:]
        _rc_stdout = stdout_json or "--stdout" in args[2:]
        _rc_ts_suffix = ""
        if "--timestamp" in args[2:]:
            args.remove("--timestamp")
            _rc_ts_suffix = "_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        _rc_dir = os.getcwd()
        if "-d" in args[2:]:
            _d_idx = args.index("-d", 2)
            if _d_idx + 1 < len(args):
                _rc_dir = args[_d_idx + 1]
        if not os.path.isdir(_rc_dir):
            print(f"Error: directory '{_rc_dir}' not found.")
            return 2

        # Cloud-output guard for --regex-collection. Runs before any
        # writes so a redirect swaps in the safe dir cleanly.
        _guarded_rc_dir = _cli_cloud_guard_or_exit(_rc_dir, config, allow_cloud_output, quiet=quiet)
        if _guarded_rc_dir is None:
            return 2
        _rc_dir = _guarded_rc_dir

        # -o output formats: opt-in like Standard Search since 1.2.6.
        # TXT is always written; DOCX / HTML / CSV / JSON / PDF are opt-in.
        # Mirrors the GUI Regex Search popup's 'Also write:' checkboxes
        # and the Standard Search -o flag from parser.py:249.
        _rc_output_formats = []
        if "-o" in args[2:]:
            _o_idx = args.index("-o", 2)
            if _o_idx + 1 >= len(args):
                print("Error: -o needs a comma-separated format list (docx, csv, json, pdf, html).")
                return 2
            _valid_formats = {"docx", "csv", "json", "pdf", "html"}
            _rc_output_formats = [
                fmt.strip().lower() for fmt in args[_o_idx + 1].split(",")
                if fmt.strip()
            ]
            for _fmt in _rc_output_formats:
                if _fmt not in _valid_formats:
                    print(
                        f"Error: invalid output format '{_fmt}'. "
                        f"Supported: docx, csv, json, pdf, html."
                    )
                    return 2

        # Surplus-flag warning. --regex-collection reads only
        # -r / -d / -o / --timestamp / --stdout; anything else (-t, -A,
        # -B, -p, -P, -m, --max-file-size, -O, -n, --inverse, -e, -c)
        # is silently ignored. --stdout / --timestamp were stripped
        # earlier, so they're listed in supported but won't appear in
        # args[2:] either way.
        _warn_unsupported_flags(
            args[2:],
            command_name="--regex-collection",
            supported={"-r", "-d", "-o", "--timestamp", "--stdout"},
            value_taking={"-d", "-o"},
        )

        from peekdocs.api import search as _rc_search
        import re as _rc_re

        if not quiet:
            print(f"Running regex collection '{collection_name}' ({len(active)} pattern(s)) in {_rc_dir}")

        start_time = time.time()
        all_results = []
        all_matches = []

        for i, (name, regex) in enumerate(active, 1):
            # Validate regex
            try:
                _rc_re.compile(regex)
            except _rc_re.error as exc:
                print(f"  Warning: pattern '{name}' has invalid regex ({exc}) — skipping.")
                continue

            if not quiet:
                print(f"  [{i}/{len(active)}] {name}")

            result = _rc_search(
                [regex],
                directory=_rc_dir,
                recursive=_rc_recursive,
                use_regex=True,
                use_index=False,
            )
            match_tuples = [(m.file_dir, m.filename, m.line_num, m.text) for m in result.matches]
            all_results.append({
                "name": name,
                "regex": regex,
                "match_count": len(result.matches),
                "file_count": len({m.filename for m in result.matches}),
                # Per-pattern matches retained so the .txt report can
                # render them in per-pattern sections (pattern_sections
                # kwarg to write_txt_report).
                "matches": match_tuples,
            })
            all_matches.extend(match_tuples)

            if not quiet:
                file_count = len({m.filename for m in result.matches})
                print(f"           {len(result.matches)} match(es) in {file_count} file(s)")

        elapsed = time.time() - start_time
        total_matches = sum(r["match_count"] for r in all_results)

        if _rc_stdout:
            # JSON output to stdout
            from peekdocs.reporter import _strip_highlights, _sha256_of_file
            json_data = {
                "generator": f"peekdocs v{VERSION}",
                "collection": collection_name,
                "directory": _rc_dir,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "elapsed_seconds": round(elapsed, 2),
                "total_matches": total_matches,
                "patterns": all_results,
                "matches": [
                    {"filename": fn, "folder": fd, "line_number": ln, "matched_text": _strip_highlights(tx)}
                    for fd, fn, ln, tx in all_matches
                ],
            }
            if compute_hashes:
                # Deduplicate by (folder, filename) so each matched file is hashed once.
                seen: dict[tuple[str, str], dict[str, Any]] = {}
                for fd, fn, _ln, _tx in all_matches:
                    dedup_key = (fd, fn)
                    if dedup_key not in seen:
                        seen[dedup_key] = {"filename": fn, "folder": fd, "sha256": _sha256_of_file(os.path.join(fd, fn))}
                json_data["matches_per_file"] = list(seen.values())
            sys.stdout.write(json.dumps(json_data, indent=2, ensure_ascii=False) + "\n")
        else:
            # Write reports. TXT always; DOCX / HTML / CSV / JSON / PDF
            # opt-in via -o (1.2.6 policy parity with Standard Search).
            output_path = None
            docx_path = None
            html_path = None
            csv_path = None
            json_path = None
            pdf_path = None
            if all_matches:
                # write_txt_report, write_docx_report, insert_file_sizes already imported at module level
                output_path = os.path.join(_rc_dir, f"peekdocs_regex_results{_rc_ts_suffix}.txt")
                search_terms = [regex for _name, regex in active]
                # Show the -o invocation in the report header when it was
                # passed so the saved report self-documents.
                command_str = f"peekdocs --regex-collection \"{collection_name}\""
                if _rc_output_formats:
                    command_str += f" -o {','.join(_rc_output_formats)}"
                if _rc_recursive:
                    command_str += " -r"
                _cpu_total = os.cpu_count() or 1
                write_txt_report(
                    output_path, all_matches, [], search_terms, command_str,
                    "ANY", False, [], False, False, True, False,
                    elapsed, max(1, _cpu_total // 2), _cpu_total,
                    recursive=_rc_recursive, use_index=False,
                    bulleted_terms=True,
                    pattern_sections=all_results,
                )
                result_doc = None
                if "docx" in _rc_output_formats:
                    docx_path = os.path.join(_rc_dir, f"peekdocs_regex_results{_rc_ts_suffix}.docx")
                    result_doc = write_docx_report(
                        docx_path, output_path,
                        search_terms=search_terms,
                        use_regex=True,
                    )
                    insert_file_sizes(output_path, docx_path, result_doc)
                if "html" in _rc_output_formats:
                    html_path = os.path.join(_rc_dir, f"peekdocs_regex_results{_rc_ts_suffix}.html")
                    try:
                        write_html_report(
                            html_path, all_matches,
                            search_terms=search_terms, use_regex=True,
                        )
                    except Exception:
                        html_path = None
                if "csv" in _rc_output_formats:
                    csv_path = os.path.join(_rc_dir, f"peekdocs_regex_results{_rc_ts_suffix}.csv")
                    try:
                        write_csv_report(csv_path, all_matches)
                    except Exception:
                        csv_path = None
                if "json" in _rc_output_formats:
                    json_path = os.path.join(_rc_dir, f"peekdocs_regex_results{_rc_ts_suffix}.json")
                    try:
                        write_json_report(
                            json_path, all_matches, search_terms,
                            "ANY", 0, elapsed, directory=_rc_dir,
                        )
                    except Exception:
                        json_path = None
                if "pdf" in _rc_output_formats:
                    pdf_path = os.path.join(_rc_dir, f"peekdocs_regex_results{_rc_ts_suffix}.pdf")
                    try:
                        write_pdf_report(
                            pdf_path, all_matches,
                            search_terms=search_terms, use_regex=True,
                        )
                    except Exception:
                        pdf_path = None

            if not quiet:
                print(f"\nCollection '{collection_name}': {len(active)} pattern(s), {total_matches} total match(es) ({elapsed:.1f}s)")
                if all_matches:
                    print(f"Reports: {output_path}")
                    for _p in (docx_path, html_path, csv_path, json_path, pdf_path):
                        if _p:
                            print(f"         {_p}")

        from peekdocs.run_log import set_stats as _set_stats_rc, set_report_paths as _set_paths_rc
        _set_stats_rc(
            match_count=total_matches,
            file_count=len({(fd, fn) for fd, fn, _ln, _tx in all_matches}),
        )
        # output_path is only bound when reports were written (non-stdout
        # branch AND all_matches non-empty). Other format paths are bound
        # only when the corresponding -o format was requested AND the
        # write succeeded — pass each conditionally so the run log
        # accurately reflects what's on disk.
        if not _rc_stdout and all_matches:
            _rc_path_args = {"txt": output_path}
            if docx_path:
                _rc_path_args["docx"] = docx_path
            if html_path:
                _rc_path_args["html"] = html_path
            if csv_path:
                _rc_path_args["csv"] = csv_path
            if json_path:
                _rc_path_args["json"] = json_path
            if pdf_path:
                _rc_path_args["pdf"] = pdf_path
            _set_paths_rc(**_rc_path_args)
        return 0 if total_matches > 0 else 1

    no_index = "--no-index" in args
    if no_index:
        args.remove("--no-index")

    # DOCX is opt-in via `-o docx` (peekdocs >= 1.2.6). For Standard
    # Search, the CLI only writes peekdocs_standard_results.txt
    # automatically; DOCX joins the output formats list when explicitly
    # requested. Regex collections honor -o as of 1.2.25 (-o docx,csv,
    # json,pdf,html, any combination). Search Suites honor -o as of
    # 1.2.26 — CLI suite path supports -o docx only; the other formats
    # live as inline code in the GUI suite popup's picker for now.
    #
    # --no-docx is kept as a tolerated no-op for one release so any
    # scripts that pass it don't break — the new default is already
    # DOCX-off, so the flag is just redundant. Remove in a later release.
    if "--no-docx" in args:
        args.remove("--no-docx")

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
        return int(parsed[0])

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
    if not stdout_json:
        print('-------------------------------------------------------------------------')
        print(command_str)
    start_time = time.time()
    cwd = os.getcwd()
    if output_dir is None:
        output_dir = cwd
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Cloud-output guard for Standard Search. Runs before any writes so
    # a redirect swaps in the safe dir cleanly. --dry-run bypasses since
    # nothing gets written.
    if not dry_run:
        output_dir = _cli_cloud_guard_or_exit(output_dir, config, allow_cloud_output, quiet=quiet)
        if output_dir is None:
            return 2

    # --dry-run: report what would be searched and exit. No content extraction,
    # no pattern matching, no report files, no index hit. Honors the scope
    # filters (-r, -t, -f, -O, --max-file-size). Search terms are accepted
    # for syntactic consistency but ignored — they don't affect scope.
    if dry_run:
        return _dry_run_report(
            cwd=cwd,
            recursive=recursive,
            use_ocr=use_ocr,
            file_types=file_types,
            file_names=file_names,
            max_file_size_mb=parsed.get("max_file_size_mb", 100),
            emit_json=stdout_json,
        )

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
    if not stdout_json and not minimal:
        if _will_use_index:
            print(f"Searching ({mode}, indexed) on [{HIGHLIGHT}{display_label}{RESET}] ...")
        else:
            print(f"Searching ({mode}) on [{HIGHLIGHT}{display_label}{RESET}] ...")
        # Cancel hint — Ctrl+C is the universal keyboard interrupt
        # across macOS Terminal/iTerm, Windows cmd/PowerShell/Windows
        # Terminal, and any Linux terminal emulator. Suppressed in
        # stdout-JSON and minimal modes since both go to scripts/pipes
        # that don't need user-facing affordances.
        print("(Press Ctrl+C to cancel)")
        if exclude_terms:
            print(f"Excluding [{' '.join(exclude_terms)}]")

    # PHASE marker for OCR runs. Fires unconditionally when OCR is on,
    # before the search engine starts. The GUI elapsed-timer reads the
    # marker and shows 'Running OCR (first run on a folder takes
    # longer; later searches are much faster)' so users know why a
    # long wait is happening instead of staring at 'Searching...' for
    # 30 seconds with no explanation. If OCR results are already
    # cached in the index, this marker fires briefly and gets
    # superseded by the writing-txt marker — harmless.
    if use_ocr:
        print("PHASE: ocr-running", file=sys.stderr, flush=True)

    # Set up CLI progress bar / spinner
    bar_width = 40
    # Use ASCII fallbacks if the terminal can't handle Unicode (e.g. Windows cp1252)
    _can_unicode = True
    try:
        "█░⠋".encode(sys.stdout.encoding or "utf-8")
    except (UnicodeEncodeError, LookupError):
        _can_unicode = False

    spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏" if _can_unicode else "|/-\\"
    _bar_fill = "█" if _can_unicode else "#"
    _bar_empty = "░" if _can_unicode else "-"
    try:
        term_width = os.get_terminal_size().columns
    except OSError:
        term_width = 80

    spinner_lock = threading.Lock()
    spinner_stop = threading.Event()
    spinner_state: dict[str, Any] = {"done": 0, "total": 0, "filename": ""}

    def _render_progress(done, total_count, filename, spinner=""):
        if total_count == 0:
            return
        pct = done / total_count
        filled = int(bar_width * pct)
        bar = _bar_fill * filled + _bar_empty * (bar_width - filled)
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
    if not stdout_json and not minimal:
        spinner_t.start()
        # The existing spinner only animates while api.search() is
        # processing files — but api.search() first calls
        # discover_files() (in scanner.py), which on huge trees like
        # $HOME can take minutes by itself. Print a one-line hint to
        # stderr so the user sees something during enumeration before
        # the search-phase progress bar takes over.
        print("Scanning files (this may take a while on large folders)...", file=sys.stderr, flush=True)

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
            progress=None if (stdout_json or minimal) else _cli_progress,
            expression=expression,
            range_filters=range_specs_raw or None,
            max_file_size_mb=parsed.get("max_file_size_mb", 100),
        )
    except KeyboardInterrupt:
        spinner_stop.set()
        if spinner_t.is_alive():
            spinner_t.join()
        sys.stdout.write("\n")
        print("\nSearch cancelled.\n")
        return 2
    except (ValueError, FileNotFoundError) as e:
        spinner_stop.set()
        if spinner_t.is_alive():
            spinner_t.join()
        print(f"\nError: {e}")
        return 2

    spinner_stop.set()
    if spinner_t.is_alive():
        spinner_t.join()

    if not stdout_json and not minimal and spinner_state["total"] > 0:
        _render_progress(spinner_state["total"], spinner_state["total"], "done")
        sys.stdout.write("\n")
        sys.stdout.flush()

    matches = search_result.matches
    all_files = search_result.files_searched
    skipped_files = search_result.skipped_files
    search_elapsed = search_result.elapsed
    use_index = search_result.used_index

    # Surface the search-engine-only elapsed value to the GUI right
    # after the engine returns, before report writing starts. The
    # subsequent `search_elapsed = time.time() - start_time` overwrite
    # (next non-comment line) inflates the value to include everything
    # up to that point; the printed 'Elapsed time:' at the end of the
    # function is the TOTAL subprocess time including reports. Neither
    # of those matches what the user thinks of as 'how long did the
    # search take' — `search_result.elapsed` does. Stderr-only so JSON
    # consumers stay clean.
    print(f"PHASE: search-done elapsed={search_result.elapsed:.2f}",
          file=sys.stderr, flush=True)

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
    max_matches = parsed.get("max_matches", 5000)
    total_match_count = len(matches)
    total_file_count = len({os.path.join(fd, fn) for fd, fn, _ln, _tx in matches})
    capped = False
    if max_matches > 0 and total_match_count > max_matches:
        capped = True
        matches = matches[:max_matches]

    # --stdout: output JSON to stdout and exit (no report files written)
    if stdout_json:
        from peekdocs.reporter import _strip_highlights, _sha256_of_file
        elapsed = time.time() - start_time
        if inverse_files is not None:
            inverse_entries: list[dict[str, Any]] = [
                {"filename": os.path.basename(fp), "folder": os.path.dirname(fp)}
                for fp in inverse_files
            ]
            if compute_hashes:
                for entry, fp in zip(inverse_entries, inverse_files):
                    entry["sha256"] = _sha256_of_file(fp)
            json_data = {
                "generator": f"peekdocs v{VERSION}",
                "directory": cwd,
                "search_terms": search_terms,
                "mode": report_mode,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "files_searched": len(all_files),
                "files_without_matches": len(inverse_files),
                "elapsed_seconds": round(elapsed, 2),
                "inverse_files": inverse_entries,
            }
        else:
            file_counts: dict[tuple[str, str], int] = {}
            for file_dir, filename, _ln, _tx in matches:
                counts_key = (file_dir, filename)
                if counts_key not in file_counts:
                    file_counts[counts_key] = 0
                file_counts[counts_key] += 1
            per_file_entries: list[dict[str, Any]] = [
                {"filename": fn, "folder": fd, "matches": count}
                for (fd, fn), count in file_counts.items()
            ]
            if compute_hashes:
                for entry in per_file_entries:
                    entry["sha256"] = _sha256_of_file(
                        os.path.join(entry["folder"], entry["filename"])
                    )
            json_data = {
                "generator": f"peekdocs v{VERSION}",
                "directory": cwd,
                "search_terms": search_terms,
                "mode": report_mode,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "files_searched": len(all_files),
                "matches_found": total_match_count,
                "elapsed_seconds": round(elapsed, 2),
                "matches_per_file": per_file_entries,
                "matches": [
                    {
                        "filename": filename,
                        "folder": file_dir,
                        "line_number": line_num,
                        "matched_text": _strip_highlights(text),
                    }
                    for file_dir, filename, line_num, text in matches
                ],
            }
        sys.stdout.write(json.dumps(json_data, indent=2, ensure_ascii=False) + "\n")
        from peekdocs.run_log import set_stats as _set_stats_stdout
        _set_stats_stdout(
            match_count=(len(inverse_files) if inverse_files else len(matches)),
            file_count=len(all_files),
        )
        return 0 if (matches or inverse_files) else 1

    # Check disk space before writing reports
    free_space = shutil.disk_usage(output_dir).free
    if free_space < 10_000_000:
        print(f"\nWarning: Low disk space ({fmt_size(free_space)} free). Cannot write reports.")
        print("Free up disk space and try again.\n")
        return 2

    # Generate reports
    output_path = os.path.join(output_dir, f"peekdocs_standard_results{ts_suffix}.txt")
    docx_output_path: str | None = os.path.join(output_dir, f"peekdocs_standard_results{ts_suffix}.docx")

    idx_meta = index_status(cwd) if use_index else None

    # Set restrictive file permissions if enabled in config
    import peekdocs.reporter as _reporter_mod
    _reporter_mod.restrict_permissions = _load_config().get("restrict_permissions", False)

    # PHASE marker — the GUI streams stderr line-by-line and parses
    # these so the status line transitions from 'Searching...' to
    # 'Writing TXT report...' etc. without resorting to elapsed-time
    # heuristics. Format is stable: 'PHASE: <kebab-case-token>'.
    print("PHASE: writing-txt", file=sys.stderr, flush=True)
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

    write_docx = "docx" in output_formats
    if not write_docx:
        result_doc = None
        docx_output_path = None
        txt_size, docx_size = insert_file_sizes(output_path, None, None)
    else:
        print("PHASE: writing-docx", file=sys.stderr, flush=True)
        assert docx_output_path is not None  # set unconditionally at line 2563
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
        print("PHASE: writing-csv", file=sys.stderr, flush=True)
        csv_output_path = os.path.join(output_dir, f"peekdocs_standard_results{ts_suffix}.csv")
        write_csv_report(csv_output_path, matches, inverse_files=inverse_files)

    if "json" in output_formats:
        print("PHASE: writing-json", file=sys.stderr, flush=True)
        json_output_path = os.path.join(output_dir, f"peekdocs_standard_results{ts_suffix}.json")
        write_json_report(
            json_output_path, matches, search_terms, report_mode,
            len(all_files), search_elapsed,
            inverse_files=inverse_files,
            directory=cwd,
            compute_hashes=compute_hashes,
        )

    if "pdf" in output_formats:
        print("PHASE: writing-pdf", file=sys.stderr, flush=True)
        pdf_output_path = os.path.join(output_dir, f"peekdocs_standard_results{ts_suffix}.pdf")
        try:
            write_pdf_report(
                pdf_output_path, matches, search_terms=search_terms,
                report_mode=report_mode, inverse_files=inverse_files,
                use_regex=use_regex, use_wildcard=use_wildcard,
                use_whole_word=use_whole_word, use_fuzzy=use_fuzzy,
                expression=expression,
            )
        except Exception as pdf_err:
            print(f"Warning: PDF report could not be generated ({pdf_err})")
            pdf_output_path = None

    html_output_path = None
    if "html" in output_formats:
        print("PHASE: writing-html", file=sys.stderr, flush=True)
        html_output_path = os.path.join(output_dir, f"peekdocs_standard_results{ts_suffix}.html")
        try:
            write_html_report(
                html_output_path, matches, search_terms=search_terms,
                report_mode=report_mode, inverse_files=inverse_files,
                use_regex=use_regex, use_wildcard=use_wildcard,
                use_whole_word=use_whole_word, use_fuzzy=use_fuzzy,
                expression=expression,
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
        assert inverse_files is not None  # inverse=True path always populates this
        print(f"Found {HIGHLIGHT}{len(inverse_files)}{RESET} file(s) WITHOUT matches. Files searched: {len(all_files)} ({size_str}).")
    elif capped:
        print(f"Found {HIGHLIGHT}{total_match_count}{RESET} match(es) in {total_file_count} file(s). Files searched: {len(all_files)} ({size_str}). Reports capped at {max_matches:,}.")
    else:
        print(f"Found {HIGHLIGHT}{len(matches)}{RESET} match(es) in {matched_file_count} file(s). Files searched: {len(all_files)} ({size_str}).")
    print(f"Elapsed time: {elapsed:.2f} seconds, Cores used: {cores} of {cpu_count}")
    if search_result.index_bypass_reason:
        print(f"Note: index bypassed — {search_result.index_bypass_reason}.")
    if search_result.index_stale_notice:
        print(f"Note: {search_result.index_stale_notice}.")
    if len(all_files) == 0 and not minimal:
        print()
        print("  Tip: No files were found to search.")
        if file_types:
            print(f"  Requested types: {', '.join(file_types)}")
        if not recursive:
            print("  Use -r to include subfolders.")
        print("  Check that you're in the right folder.")
    if not minimal:
        if inverse:
            assert inverse_files is not None  # inverse=True path always populates this
            for f in inverse_files:
                print(f"  {os.path.basename(f)}")
        else:
            # Per-file match counts (reusing the outer `file_counts` name;
            # re-init here since we hit this path even when the earlier
            # branch didn't run).
            file_counts = {}
            for fd, fn, _ln, _tx in matches:
                fc_key = (fd, fn)
                if fc_key not in file_counts:
                    file_counts[fc_key] = 0
                file_counts[fc_key] += 1
            for (_fd, fn), count in sorted(file_counts.items(), key=lambda x: x[0][1].lower()):
                print(f"  {fn}: {count}")
        print(f"Results ==> {output_dir}")
        if docx_output_path:
            print(f"  {os.path.basename(output_path)} ({fmt_size(txt_size)}), {os.path.basename(docx_output_path)} ({fmt_size(docx_size)})")
        else:
            print(f"  {os.path.basename(output_path)} ({fmt_size(txt_size)})")
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
    from peekdocs.run_log import set_stats, set_report_paths
    set_report_paths(
        txt=output_path,
        docx=docx_output_path,
        csv=csv_output_path,
        json=json_output_path,
        pdf=pdf_output_path,
        html=html_output_path,
    )
    if inverse:
        set_stats(
            match_count=len(inverse_files) if inverse_files else 0,
            file_count=len(all_files),
            error_count=len(skipped_files) if skipped_files else 0,
        )
        return 0 if inverse_files else 1
    set_stats(
        match_count=total_match_count,
        file_count=len(all_files),
        error_count=len(skipped_files) if skipped_files else 0,
    )
    return 0 if matches else 1


if __name__ == "__main__":
    # PyInstaller + multiprocessing: must be called before any code that
    # creates worker processes. Harmless on a normal pip install (becomes
    # a no-op when sys.frozen is False); essential in a bundled exe so
    # multiprocessing workers don't re-execute the CLI's main code path.
    import multiprocessing
    multiprocessing.freeze_support()
    sys.exit(main())
