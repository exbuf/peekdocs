# Claude-DocSearch

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
  - [Supported File Types](#supported-file-types)
- [Benefits and Applications](#benefits-and-applications)
- [System Requirements](#system-requirements)
- [Saved Settings (Optional)](#saved-settings-optional)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Option A: Quick Install with pipx (recommended)](#option-a-quick-install-with-pipx-recommended)
  - [Option B: Manual Install](#option-b-manual-install)
- [Quick Start](#quick-start)
- [GUI Mode](#gui-mode)
- [Usage](#usage)
  - [Regex search](#regex-search)
    - [Common Regex Search Patterns](#common-regex-search-patterns)
- [Flag Use Summary](#flag-use-summary)
  - [Notes](#notes)
  - [Command Examples](#command-examples)
- [Output](#output)
- [FAQ (Frequently Asked Questions)](#faq-frequently-asked-questions)
- [Running Tests](#running-tests)
- [Project Structure](#project-structure)
- [License](#license)

## Introduction

docsearch is a fast, offline search tool that scans 29 file types — including PDFs, Word documents, spreadsheets, presentations, and e-books — all at once, without uploading anything to the cloud. Results are saved to an easy-to-read `.docx` report with every match highlighted in yellow and shown with full paragraph context, so you can understand each result without opening the original file. Search using plain keywords, or go deeper with AND/OR logic to require all terms or match any of them. Use proximity search to find words that appear near each other, wildcards for simple pattern matching (`budg*` finds "budget", "budgets", "budgeting"), regular expressions for precise pattern matching (like phone numbers, dates, or email addresses), fuzzy matching for typo-tolerant searches and imperfect OCR text, exclude terms to filter out unwanted matches (`-n draft` skips lines containing "draft"), and context lines to see surrounding text for every hit. With the `-O` flag, docsearch can even read scanned PDFs and image files using OCR (Optical Character Recognition). Results are also highlighted in the terminal and saved to a plain `.txt` file. Prefer not to use the terminal? docsearch includes a point-and-click GUI — just run `docsearch-gui`. Whether you're a home user digging through years of personal documents or a professional searching legal files, research papers, or business records, docsearch handles it in seconds — no internet connection required.

I had hundreds of documents backed up from Google Docs and scattered across folders, along with other documents and files, with no convenient way to search through them. If that sounds familiar, I hope this tool helps you as much as it's helped me.

## Features

- Searches all files in the current folder (and subfolders with `-r`). Use `-t` to focus on specific file types. See table for supported file types.
- Rich set of flags for controlling docsearch behavior. See Flag summary table below.
- Case-insensitive matching
- Multiple search terms use OR logic (finds any match) by default: `docsearch term1 term2 term3`
- For AND logic (all terms must appear in the same paragraph) use `-a`: `docsearch -a term1 term2 term3`
- Proximity search with `-p` finds terms within N words of each other: `docsearch -p 5 budget revenue`
- Use quotes for multi-word phrases (e.g., `"annual report"`)
- Don't separate search terms with commas unless they're part of the search term itself
- Each match includes document name, folder path, line number, and matched text
- Generates timestamped `docsearch_results.txt` and `docsearch_results.docx` reports
- Gracefully handles corrupt or unreadable files — skips them with a warning instead of crashing
- Special characters (`<`, `>`, `[`, `]`, `*`, `?`, `$`, `|`, etc.) must be enclosed in quotes to prevent shell interpretation. Example: `docsearch "<" "[test]" "$amount"`
- Save or accumulate results with `-s` and `-sa` flags — saved files are automatically prefixed with `DO_NOT_SEARCH` so they're never re-searched
- Multiprocessing with `-c N` flag — uses multiple CPU cores to search files in parallel, speeding up large searches. Defaults to half of available cores to keep your machine responsive
- OCR support with `-O` flag — extracts text from scanned PDFs and image files (.jpg, .jpeg, .png, .tiff, .tif, .bmp) using Optical Character Recognition. Requires Tesseract (see [Installation](#installation))
- Fuzzy matching with `-z` flag — finds approximate matches for typos, misspellings, and OCR recognition errors (e.g., "budgt" matches "budget")
- Wildcard search with `-w` flag — simple pattern matching where `*` matches any characters and `?` matches one character (e.g., `budg*` matches "budget", "budgets", "budgeting")
- Exclude terms with `-n` flag — filter out lines containing unwanted terms (e.g., `-n draft budget` finds "budget" but skips lines containing "draft")
- Optional GUI (`docsearch-gui`) — a point-and-click interface with search box, folder picker, and all advanced options, for users who prefer not to use the terminal

### Supported File Types

All file types can exist in the same folder — no need to separate them into different folders. docsearch searches all supported types together in a single pass.

| # | File Type | Description |
|---|-----------|-------------|
| 1 | `.bmp` | Bitmap image (requires `-O` flag) |
| 2 | `.cfg` | Configuration file |
| 3 | `.csv` | Comma-separated values |
| 4 | `.docx` | Microsoft Word document |
| 5 | `.epub` | E-book (EPUB format) |
| 6 | `.html` | HTML web page |
| 7 | `.ini` | INI configuration file |
| 8 | `.jpg` / `.jpeg` | JPEG image (requires `-O` flag) |
| 9 | `.json` | JSON data file |
| 10 | `.log` | Log file |
| 11 | `.md` | Markdown document |
| 12 | `.odp` | OpenDocument Presentation (LibreOffice Impress) |
| 13 | `.ods` | OpenDocument Spreadsheet (LibreOffice Calc) |
| 14 | `.odt` | OpenDocument Text (LibreOffice Writer) |
| 15 | `.pdf` | PDF document (scanned PDFs require `-O` flag) |
| 16 | `.png` | PNG image (requires `-O` flag) |
| 17 | `.pptx` | Microsoft PowerPoint presentation |
| 18 | `.rst` | reStructuredText document |
| 19 | `.rtf` | Rich Text Format document |
| 20 | `.sql` | SQL script |
| 21 | `.tex` | LaTeX document |
| 22 | `.tiff` / `.tif` | TIFF image (requires `-O` flag) |
| 23 | `.toml` | TOML configuration file |
| 24 | `.tsv` | Tab-separated values |
| 25 | `.txt` | Plain text file |
| 26 | `.xlsx` | Microsoft Excel spreadsheet |
| 27 | `.xml` | XML data file |
| 28 | `.yaml` | YAML configuration file |
| 29 | `.yml` | YAML configuration file |

## Benefits and Applications

- **Keep sensitive documents private** — medical records, financial info, and legal documents stay on your machine, searchable without uploading to cloud AI services
- **Work offline** — search your files without an internet connection, useful for travel or unreliable connectivity
- **Search across formats** — find information across PDFs, Word docs, presentations, spreadsheets, e-books, RTF, Markdown, JSON, XML, YAML, TOML, LaTeX, reStructuredText, SQL, config files, log files, text files, and scanned images in one place
- **Build a personal knowledge base** — writers, students, and researchers can search years of notes, clippings, and drafts instantly
- **Preserve family and personal records** — genealogy notes, old letters, scanned documents, decades of personal history made searchable
- **Support professional work** — lawyers, consultants, and others with years of case files or client notes can quickly find precedents or past work

Local search is also fast, with no rate limits, usage caps, or waiting on cloud services.

**Programming process:** DocSearch was developed using Claude Code. It's my second Claude Code app, the first being my personal website.

## System Requirements

### Minimum Requirements

- **Operating System:** Windows 10 or later, macOS 11 (Big Sur) or later, or Ubuntu 20.04 or later
- **Processor:** Dual-core 1.5 GHz or faster
- **Memory:** 2 GB RAM (4 GB recommended)
- **Storage:** 300 MB available disk space
- **Python:** Version 3.10 or higher
- **Display:** Terminal or command-line interface

### Recommended Requirements

- **Processor:** Quad-core 2.0 GHz or faster
- **Memory:** 8 GB RAM
- **Storage:** 500 MB available disk space
- **Python:** Version 3.10 or higher

### Additional Notes

- More CPU cores improve performance when searching large numbers of files
- Disk space requirements do not include user documents or search output files
- No database required — the only optional extra software is Tesseract, needed only for OCR (the `-O` flag)
- To view the `.docx` report, you need a word processor such as Microsoft Word, LibreOffice Writer (free), Google Docs (free), or Apple Pages (free, Mac only). See [Quick Start](#quick-start) for how to open it
- The `.txt` report can be opened on any computer with no additional software

## Saved Settings (Optional)

If you find yourself typing the same flags every time, you can save them as defaults so docsearch remembers them for you. This is entirely optional — docsearch works fine without it.

Use the `--config` flag to manage your saved settings:

```bash
docsearch --config recursive=true       # always search subdirectories
docsearch --config quiet=true cores=4   # save multiple settings at once
docsearch --config                      # view your saved settings
docsearch --config recursive=           # remove a saved setting
```

Once saved, your settings apply automatically every time you run docsearch. For example, after running `docsearch --config recursive=true quiet=true cores=4`, typing `docsearch budget` behaves like `docsearch -r -q -c 4 budget`. You can always override a saved setting for a single search by typing the flag explicitly — this does not change your saved settings.

**Available settings:**

| Setting | Type | Maps to flag | Default |
|---------|------|-------------|---------|
| `recursive` | true/false | `-r` | false (current directory only) |
| `quiet` | true/false | `-q` | false (show banner) |
| `match_all` | true/false | `-a` | false (OR logic) |
| `regex` | true/false | `-x` | false (plain text search) |
| `cores` | number | `-c N` | half of available CPU cores |
| `context_before` | number | `-B N` | 0 (no lines before match) |
| `context_after` | number | `-A N` | 0 (no lines after match) |
| `fuzzy` | true/false | `-z` | false (exact match) |
| `wildcard` | true/false | `-w` | false (plain text search) |
| `ocr` | true/false | `-O` | false (no OCR) |
| `file_types` | comma-separated | `-t` | all supported types |

If no settings are saved or if a value is invalid, docsearch uses its built-in defaults. Session-specific flags like `-p`, `-f`, `-n`, `-s`, and `-sa` are not configurable.

**Advanced:** Your settings are stored in a text file called `.docsearchrc` in your user folder. You can also edit this file directly if you prefer — each line is a `key = value` pair, and lines starting with `#` are comments.

## Installation

### Prerequisites

- Python 3.10 or higher — check if it's already installed by running `python3 --version` (macOS/Linux) or `python --version` (Windows)
  - **macOS:** Install from [python.org](https://www.python.org/downloads/) or via Homebrew: `brew install python`
  - **Windows:** Install from [python.org](https://www.python.org/downloads/) — check "Add Python to PATH" during installation
  - **Linux:** Usually pre-installed. If not: `sudo apt install python3` (Ubuntu/Debian) or `sudo dnf install python3` (Fedora)
- **Tkinter** (optional — only needed for the GUI. Included by default on Windows and macOS from python.org)
  - **macOS (Homebrew):** `brew install python-tk@3.13` (adjust version to match your Python)
  - **Linux:** `sudo apt install python3-tk` (Ubuntu/Debian) or `sudo dnf install python3-tkinter` (Fedora)
- **Tesseract OCR** (optional — only needed for the `-O` flag, which enables searching scanned PDFs and images)
  - **macOS:** `brew install tesseract`
  - **Windows:** Download installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
  - **Linux:** `sudo apt install tesseract-ocr` (Ubuntu/Debian) or `sudo dnf install tesseract` (Fedora)

### Option A: Quick Install with pipx (recommended)

[pipx](https://pipx.pypa.io/) installs docsearch in its own private workspace automatically — no manual setup needed.

1. Install pipx if you don't have it (check by running `pipx --version`):

   **macOS:** `brew install pipx && pipx ensurepath`<br>
   **Windows:** `pip install pipx && pipx ensurepath`<br>
   **Linux:** `sudo apt install pipx && pipx ensurepath` (Ubuntu/Debian) or `pip install pipx && pipx ensurepath`

   Close and reopen your terminal after running `ensurepath`.

2. Install docsearch:
   ```bash
   pipx install git+https://github.com/exbuf/Claude-DocSearch.git
   ```

That's it. `docsearch` and `docsearch-gui` are now available from any terminal — no activation step, no virtual environment to manage.

### Option B: Manual Install

If you prefer to manage things yourself, or if pipx is not available:

1. Clone the repository (requires [git](https://git-scm.com/downloads)):
   ```bash
   git clone https://github.com/exbuf/Claude-DocSearch.git
   cd Claude-DocSearch
   ```
   **Don't have git?** Click the green **Code** button on the [GitHub page](https://github.com/exbuf/Claude-DocSearch), select **Download ZIP**, extract it, and open the extracted folder in your terminal.

2. Set up a private workspace for docsearch (called a "virtual environment" — this keeps docsearch's files separate from the rest of your computer so nothing conflicts):

   **macOS/Linux (Terminal):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   **Windows (Command Prompt):**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

   **Windows (PowerShell):**
   ```powershell
   python -m venv venv
   venv\Scripts\Activate.ps1
   ```

   After running the activate command, you'll notice `(venv)` appear at the beginning of your command line. This is normal — it just means docsearch is ready to use. If you close your terminal and open it later, you won't see `(venv)` anymore. Just navigate back to the Claude-DocSearch folder and run the activate command again (step 2 above) before using docsearch.

3. Install docsearch (make sure you're still in the Claude-DocSearch folder):
   ```bash
   pip install -e .
   ```

## Quick Start

Open your terminal (if you used the manual install, activate the workspace first — see [Option B step 2](#option-b-manual-install)), navigate to the folder containing your documents, and search:

```bash
cd /path/to/your/documents
docsearch budget
```

That's it. docsearch scans every supported file in the folder and saves the results to `docsearch_results.txt` and `docsearch_results.docx`. The `.docx` report is especially easy to read — every match is highlighted in yellow so you can spot results at a glance. To open the report, double-click it in your file manager (it's saved in the folder where you ran docsearch, not inside any subfolder) or — once your search finishes — type one of these commands on the same command line:

```bash
open docsearch_results.docx        # macOS
start docsearch_results.docx       # Windows
xdg-open docsearch_results.docx    # Linux
```

A few more examples to try:

```bash
docsearch budget revenue              # find files containing "budget" OR "revenue"
docsearch -a budget revenue           # find files containing both terms
docsearch -r budget                   # search subdirectories too
docsearch -t pdf,docx budget          # search only PDFs and Word docs
```

See the [Command Examples](#command-examples) table for over 80 more combinations.

## GUI Mode

If you prefer pointing and clicking over typing commands, docsearch has a graphical interface. It works exactly like the terminal version — same search, same results, same reports — but with a familiar window instead of a command line.

**How to open it:**

You still need to open a terminal once to launch the GUI. If you used the manual install (Option B), activate the workspace first (see [Option B step 2](#option-b-manual-install)). Then type:

```bash
docsearch-gui
```

A window will appear. From here, everything is point-and-click — no more terminal commands needed.

**Your first GUI search:**

1. Type what you're looking for in the **Search** box
2. Click **Browse** to pick the folder containing your documents (your home folder is selected by default)
3. Click **Search** (or press Enter)
4. When the search finishes, click **Open Report** to view your results in a `.docx` file with matches highlighted in yellow

**Advanced Options:**

Click "Advanced Options" to expand a panel with additional settings — AND mode, recursive search, fuzzy matching, wildcards, OCR, regex, exclude terms, file type filtering, proximity, and context lines. These are the same options available as terminal flags. You don't need any of them for a basic search.

## Usage

If you installed with pipx (Option A), docsearch is always ready — just open any terminal. If you used the manual install (Option B), activate the workspace first each time you open a new terminal (see [Option B step 2](#option-b-manual-install)) — you'll see `(venv)` appear in your prompt. Then navigate to the folder containing your documents and run docsearch with your search terms. See the [Command Examples](#command-examples) table for usage.

### Regex search

**What are Regex searches?**
Regex (short for "regular expression") lets you search for patterns rather than exact text. Instead of searching for a specific phone number, you can search for any phone number. Instead of one date, you can find all dates in any format.

Think of it as a wildcard search on steroids. For example, `\d{3}-\d{3}-\d{4}` finds any phone number like 555-123-4567, while `\$\d+` finds any dollar amount.

Regex is powerful but can look intimidating at first. See the table below for common patterns you can copy and use.

#### Common Regex Search Patterns

Below is a list of common regex patterns you can copy and paste into your search. Remember to enclose in quotes.

| Pattern | Matches | Example |
|---------|---------|---------|
| `\d{3}-\d{3}-\d{4}` | US phone numbers | 555-123-4567 |
| `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,}` | Email addresses | jane@example.com |
| `\d{4}-\d{2}-\d{2}` | Dates (YYYY-MM-DD) | 2026-03-17 |
| `\$\d+(\.\d{2})?` | Dollar amounts | $45.99 |
| `\d{3}-\d{2}-\d{4}` | SSN format | 123-45-6789 |
| `\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}` | IP addresses | 192.168.1.1 |
| `https?://\S+` | URLs | https://example.com |
| `\b[A-Z]{2,}\b` | Acronyms (all caps) | NASA, FBI |
| `\b\d{5}(-\d{4})?\b` | US ZIP codes | 12345 or 12345-6789 |
| `\(\d{3}\)\s?\d{3}-\d{4}` | Phone numbers with area code parens | (555) 123-4567 |
| `\b[A-Z][a-z]+\s[A-Z][a-z]+\b` | Proper names (two capitalized words) | John Smith |
| `\b\d+%` | Percentages | 92% |
| `Q[1-4]\s?\d{4}` | Fiscal quarters | Q1 2026 |

## Flag Use Summary

docsearch has seventeen flags that can be mixed and matched:

| Flag&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Purpose |
|------------|---------|
| `-a` (all) | AND logic — all terms must appear in the same paragraph |
| `-c N` (cores) | Number of CPU cores for parallel search (default: half of available cores). See [FAQ](#faq-frequently-asked-questions) for tradeoffs |
| `-f` (files) | Search specific files (comma-separated, e.g., `report.pdf,notes.txt`) |
| `-n` (not) | Exclude lines matching specified terms (comma-separated, e.g., `-n draft,obsolete`) |
| `-O` (OCR) | Enable OCR for scanned PDFs and image files (requires [Tesseract](#prerequisites)) |
| `-p N` (proximity) | Proximity search — find terms within N words of each other |
| `-q` (quiet) | Quiet mode — suppress the banner |
| `-r` (recursive) | Search subdirectories recursively |
| `-s` (save) | Archive results — copies docsearch_results files to DO_NOT_SEARCH_your_file_name.docx (and .txt). The DO_NOT_SEARCH prefix is added automatically so archived files are never re-searched. Does not erase the original results files, but they are overwritten on the next search. Example: `docsearch -s my_report` |
| `-sa` (save-append) | Search and auto-append — runs the search normally, then appends the results to DO_NOT_SEARCH_ACCUMULATED_your_file_name.txt (and .docx). Use this to accumulate results from multiple searches into one file. The DO_NOT_SEARCH_ACCUMULATED prefix is added automatically.<br><br>Example: `docsearch -sa my_report budget revenue` results in your search for the terms budget and revenue being saved in file DO_NOT_SEARCH_ACCUMULATED_my_report.docx (and .txt). |
| `-t` (types) | Filter by file type (comma-separated, e.g., `pdf,docx`) |
| `-w` (wildcard) | Wildcard pattern search — `*` matches any characters, `?` matches one character |
| `-x` (regex) | Regex pattern search (case-insensitive) |
| `-z` (fuzzy) | Fuzzy matching — find approximate matches (e.g., typos like "budgt" matching "budget") |
| `--config` (config) | View, set, or remove saved settings. See [Saved Settings](#saved-settings-optional) |
| `-A N` (after) | Show N lines after each match |
| `-B N` (before) | Show N lines before each match |

### Notes
- Flag order doesn't matter — `-a -r -t` works the same as `-r -t -a`
- `-f` always needs its file list immediately after it (e.g., `-f report.pdf,notes.txt`)
- `-f` has no limit on the number of files — list as many as you need, comma-separated
- `-f` requires each file to have a supported extension and to exist in the search directory
- `-f` and `-t` cannot be used together
- `-p` always needs its word count immediately after it (e.g., `-p 5`)
- `-p` requires at least 2 search terms
- `-p` implies AND logic — all terms must appear within N words of each other
- `-t` always needs its type list immediately after it (e.g., `-t pdf,docx`)
- `-x` treats search terms as regex patterns instead of literal strings
- `-s` is used separately after a search to save results: `docsearch -s my_report`
- `-sa` always needs its filename immediately after it (e.g., `-sa my_report`)
- `-sa` appends to existing DO_NOT_SEARCH_ACCUMULATED files, allowing you to accumulate results from multiple searches
- `-A` and `-B` are uppercase — don't confuse `-A` (lines after) with `-a` (AND logic)
- `-A` and `-B` always need their count immediately after them (e.g., `-A 5`, `-B 3`)
- `-c` always needs its core count immediately after it (e.g., `-c 4`)
- `-c` defaults to half of available CPU cores when not specified
- For small numbers of files (fewer than 10), single-threaded mode is used automatically regardless of `-c`
- `-O` requires Tesseract to be installed on your system (see [Installation](#installation))
- `-O` enables OCR for PDF pages that have no extractable text and adds image file types (.jpg, .jpeg, .png, .tiff, .tif, .bmp) to the search
- `-O` makes searches slower — only use it when you need to search scanned or image-based documents
- `-z` enables fuzzy matching — words that are approximately similar (80% or better) to your search terms will match
- `-z` and `-x` cannot be used together (fuzzy and regex are incompatible modes)
- `-z` is especially useful with `-O` (OCR), since OCR text often contains recognition errors
- `-z` works with `-a` (AND), `-p` (proximity), `-t` (file type filter), `-r` (recursive), `-A`/`-B` (context), and all other flags except `-x`
- `-w` enables wildcard pattern matching — `*` matches zero or more characters, `?` matches exactly one character (e.g., `budg*` matches "budget", "budgets", "budgeting")
- `-w` and `-x` cannot be used together (wildcard and regex are incompatible modes)
- `-w` and `-z` cannot be used together (wildcard and fuzzy are incompatible modes)
- `-w` matches whole words only — `budg*` will not match the "budg" inside "debugging"
- `-n` always needs its exclude terms immediately after it (e.g., `-n draft` or `-n draft,obsolete`)
- `-n` follows the current search mode — in fuzzy mode, exclude terms are fuzzy-matched; in wildcard mode, exclude terms are wildcard-matched
- `-n` works with all flags and all search modes

### Command Examples

| # | Search Type | Command |
|---|-------------|---------|
| | **Basic Searches** | |
| 1 | Single word | `docsearch budget` |
| 2 | Multiple terms (OR logic) | `docsearch budget revenue expenses` |
| 3 | Multi-word phrase | `docsearch "annual report"` |
| 4 | Combine phrases and single terms | `docsearch "computer analysis" energy generation` |
| 5 | Require ALL terms (AND logic) | `docsearch -a budget revenue expenses` |
| | **Filter by File Name** | |
| 6 | Search a specific file | `docsearch -f report.pdf budget` |
| 7 | Search multiple specific files | `docsearch -f report.pdf,notes.txt budget` |
| 8 | Specific files with AND logic | `docsearch -f report.pdf,data.csv -a budget revenue` |
| 9 | Specific file recursive | `docsearch -f report.pdf -r budget` |
| 10 | Specific file with regex | `docsearch -f report.pdf -x "\d{3}-\d{3}-\d{4}"` |
| 11 | Specific file with context lines | `docsearch -f report.pdf -B 3 -A 3 budget` |
| 12 | Specific file, regex, AND | `docsearch -f report.pdf -x -a "\d{3}" "\$\d+"` |
| | **Filter by File Type** | |
| 13 | Search only specific file types | `docsearch -t pdf,docx budget` |
| 14 | File type filter with OR search | `docsearch -t pdf,docx budget revenue` |
| 15 | File type filter with AND search | `docsearch -a -t csv,xlsx budget revenue` |
| | **Proximity Searches** | |
| 16 | Terms within 5 words of each other | `docsearch -p 5 budget revenue` |
| 17 | Proximity with file type filter | `docsearch -p 5 -t pdf,docx budget revenue` |
| 18 | Proximity with recursive search | `docsearch -p 5 -r budget revenue` |
| 19 | Proximity with specific file | `docsearch -p 5 -f report.pdf budget revenue` |
| | **Recursive (Subdirectory) Searches** | |
| 20 | Search all subdirectories | `docsearch -r budget` |
| 21 | Recursive with AND logic | `docsearch -r -a budget revenue expenses` |
| 22 | Recursive with file type filter | `docsearch -r -t pdf,docx budget` |
| 23 | Recursive, AND, and file type filter | `docsearch -r -a -t txt budget revenue expenses` |
| | **Regex Pattern Searches** | |
| 24 | Search for phone numbers | `docsearch -x "\d{3}-\d{3}-\d{4}"` |
| 25 | Search for email addresses | `docsearch -x "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,}"` |
| 26 | Regex with AND logic | `docsearch -x -a "\d{3}" "\$\d+\.\d{2}"` |
| 27 | Regex with file type filter | `docsearch -x -t pdf,docx "\$\d+(\.\d{2})?"` |
| 28 | Regex recursive | `docsearch -x -r "\d{3}-\d{3}-\d{4}"` |
| 29 | Regex, recursive, file type filter | `docsearch -x -r -t txt,csv "\b2026-\d{2}-\d{2}\b"` |
| 30 | Regex, AND, recursive, file type filter | `docsearch -x -a -r -t pdf "\d{3}" "\$\d+"` |
| | **Context Lines (Before/After)** | |
| 31 | Show 5 lines after each match | `docsearch -A 5 "John Smith"` |
| 32 | Show 3 lines before each match | `docsearch -B 3 budget` |
| 33 | Show lines before and after | `docsearch -B 2 -A 2 budget` |
| 34 | Context lines with AND logic | `docsearch -B 3 -A 3 -a budget revenue` |
| 35 | Context with file type filter | `docsearch -A 5 -t docx,pdf budget` |
| 36 | Context with recursive search | `docsearch -B 3 -A 3 -r budget` |
| 37 | Context with regex | `docsearch -B 2 -A 2 -x "\d{3}-\d{3}-\d{4}"` |
| 38 | Context, recursive, file type filter | `docsearch -B 5 -A 5 -r -t docx "John Smith"` |
| 39 | Context, AND, recursive, file type filter | `docsearch -B 3 -A 3 -a -r -t txt budget revenue` |
| | **Parallel Processing** | |
| 40 | Use 4 cores for search | `docsearch -c 4 budget` |
| 41 | Parallel with recursive search | `docsearch -c 4 -r budget` |
| 42 | Parallel with file type filter | `docsearch -c 4 -t pdf,docx budget` |
| | **Save, Version, and Help** | |
| 43 | Save results to a named file | `docsearch -s name_of_your_file` |
| | **Save and Append Searches** | |
| 44 | Search and append results to a file | `docsearch -sa my_report budget` |
| 45 | Append with AND search | `docsearch -sa my_report -a budget revenue` |
| 46 | Append with recursive search | `docsearch -sa my_report -r budget` |
| 47 | Append with file type filter | `docsearch -sa my_report -t pdf budget` |
| | **Quiet Mode** | |
| 48 | Suppress banner | `docsearch -q budget` |
| 49 | Quiet with recursive search | `docsearch -q -r budget` |
| | **OCR Searches** | |
| 50 | Search scanned PDFs and images | `docsearch -O budget` |
| 51 | OCR with file type filter | `docsearch -O -t pdf budget` |
| 52 | Search only image files | `docsearch -O -t jpg,png budget` |
| 53 | OCR with recursive search | `docsearch -O -r budget` |
| 54 | OCR with AND logic | `docsearch -O -a budget revenue` |
| 55 | OCR with context lines | `docsearch -O -B 3 -A 3 budget` |
| | **Fuzzy Searches** | |
| 56 | Fuzzy single term | `docsearch -z budget` |
| 57 | Fuzzy with AND logic | `docsearch -z -a budget revenue` |
| 58 | Fuzzy with file type filter | `docsearch -z -t pdf,docx budget` |
| 59 | Fuzzy with recursive search | `docsearch -z -r budget` |
| 60 | Fuzzy with proximity | `docsearch -z -p 5 budget revenue` |
| 61 | Fuzzy with OCR | `docsearch -z -O budget` |
| 62 | Fuzzy with context lines | `docsearch -z -B 3 -A 3 budget` |
| 63 | Fuzzy, AND, recursive, file type | `docsearch -z -a -r -t pdf budget revenue` |
| | **Wildcard Searches** | |
| 64 | Wildcard single pattern | `docsearch -w "budg*"` |
| 65 | Wildcard question mark | `docsearch -w "te?t"` |
| 66 | Wildcard with AND logic | `docsearch -w -a "budg*" "rev*"` |
| 67 | Wildcard with file type filter | `docsearch -w -t pdf,docx "budg*"` |
| 68 | Wildcard with recursive search | `docsearch -w -r "budg*"` |
| 69 | Wildcard with context lines | `docsearch -w -B 3 -A 3 "budg*"` |
| | **Exclude Searches** | |
| 70 | Exclude lines containing a term | `docsearch -n draft budget` |
| 71 | Exclude multiple terms | `docsearch -n draft,obsolete budget` |
| 72 | Exclude with AND logic | `docsearch -n draft -a budget revenue` |
| 73 | Exclude with recursive search | `docsearch -n draft -r budget` |
| 74 | Exclude with file type filter | `docsearch -n draft -t pdf,docx budget` |
| 75 | Exclude with wildcard search | `docsearch -w -n "dra*" "budg*"` |
| | **Saved Settings** | |
| 76 | View saved settings | `docsearch --config` |
| 77 | Save a setting | `docsearch --config recursive=true` |
| 78 | Save multiple settings | `docsearch --config recursive=true cores=4` |
| 79 | Remove a saved setting | `docsearch --config recursive=` |
| | **Version and Help** | |
| 80 | Show version | `docsearch -v` |
| 81 | Show help | `docsearch -h` |
| 82 | Show help (no arguments) | `docsearch` |

## Output

Search results are written to two files in the current directory:

- **`docsearch_results.txt`** — Plain text with `**` markers around matched terms
- **`docsearch_results.docx`** — Word document with search terms highlighted in green in the header and matched terms highlighted in yellow throughout

Text file format:
```

2026-03-07 14:30:45
Search Term(s) ==> budget, revenue

Document: report.docx, Line: 12, Match:
(/Users/bob/GoogleDocs)
"The **budget** for this quarter exceeded expectations"

Document: summary.docx, Line: 3, Match:
(/Users/bob/GoogleDocs)
"Revised **budget** proposal attached"
```

If any files could not be read during a search, errors are logged to **`docsearch_errors.log`** in the current directory. Each entry includes a timestamp, the filename, and the reason it failed:
```
2026-03-22 14:05:12  Could not read report.pdf (encrypted PDF)
2026-03-22 14:05:12  Could not read data.xlsx (file is corrupted)
```

The error log is only created when a file error occurs — if all files are read successfully, no error log is created. The error log appends across searches so you can track issues over time. You can safely delete `docsearch_errors.log` at any time — a new one will be created automatically the next time a file error occurs.

The terminal also displays a summary:
```
Found 2 match(es). Results written to docsearch_results.txt and docsearch_results.docx
```

## FAQ (Frequently Asked Questions)

**Where are my search results saved and what information is printed on the search report?**
Results are saved to two files in the current directory: `docsearch_results.txt` and `docsearch_results.docx`. Each report includes the date and time, the command used, search terms, number of hits, search time, number of files searched, total file size, and a file type tally. Each match shows the document name, directory path, line number, and the matched text with search terms highlighted — `**bold**` markers in the `.txt` file and yellow highlighting in the `.docx` file. Note that these two result files are overwritten each time you run a new search. Use the `-s` flag to archive them or the `-sa` flag to accumulate results across searches. Archived and accumulated files include your chosen name and are automatically prefixed with `DO_NOT_SEARCH` (e.g., `DO_NOT_SEARCH_my_report.txt`) so they are never re-searched in future searches.

**What happens when a file can't be read?**
Some files may fail to read — for example, encrypted PDFs, corrupted documents, password-protected spreadsheets, or files with unsupported encoding. When this happens, a warning is printed to the screen and the error is logged to `docsearch_errors.log` with a timestamp. The error log is only created when a file error occurs — if all files are read successfully, no error log is created. The log appends across searches so you have a history of any issues. You can delete `docsearch_errors.log` at any time — a new one will be created automatically the next time a file error occurs. The error log is automatically excluded from searches so it never appears in your results.

**How do I recall a previous command?**
Press the up arrow key in your terminal to scroll through previous commands. This is a built-in feature of all terminals (macOS, Windows, and Linux) — not specific to docsearch. You can press up repeatedly to go further back, then press Enter to re-run the command.

**How do I cancel a search in progress?**
Press Ctrl+C. docsearch will stop cleanly and print "Search cancelled." This works on macOS, Windows, and Linux.

**How do I save my preferred settings?**
Use the `--config` flag. For example, `docsearch --config recursive=true` saves that setting so it applies automatically every time. See the [Saved Settings](#saved-settings-optional) section for details.

**Can I search all subfolders?**
Yes — use the `-r` flag.<br>
Example: `docsearch -r budget`

**Can I search only PDFs (etc)?**
Yes — use the `-t` flag.<br>
Example: `docsearch -t pdf budget`

**Can I search a specific file?**
Yes — use the `-f` flag.<br>
Example: `docsearch -f report.pdf budget`<br>
You can focus on one file or several, comma-separated: `docsearch -f report.pdf,notes.txt budget`

**Can I find terms near each other?**
Yes — use the `-p` flag.<br>
Example: `docsearch -p 5 budget revenue`<br>
The number 5 means the terms must appear within 5 words of each other.

**Can I save these results?**
Yes — use the `-s` flag.<br>
Example: `docsearch -s my_report`<br>
The saved/archived file is never re-searched because of its `DO_NOT_SEARCH` prefix.

**Can I accumulate results from multiple searches?**
Yes — use the `-sa` flag.<br>
Example: `docsearch -sa my_report budget revenue`<br>
Each new search you run with the same name is appended to the bottom of the file, so your results accumulate over time. The accumulated file is never re-searched because of its `DO_NOT_SEARCH` prefix.

**Can I find approximate matches or handle typos?**
Yes — use the `-z` flag. This enables fuzzy matching, which finds words that are similar to your search terms even if they're not spelled exactly the same. For example, searching for "budget" with `-z` will also match "budgt", "buget", or "budjet". This is especially useful when searching OCR text (combine with `-O`), which often contains recognition errors.<br>
Example: `docsearch -z budget`

**Can I use wildcards instead of regex?**
Yes — use the `-w` flag. Wildcards are simpler than regex: `*` matches any characters and `?` matches exactly one character. For example, `budg*` matches "budget", "budgets", and "budgeting", while `te?t` matches "test" and "text". Wildcards match whole words only, so `budg*` won't match the "budg" inside "debugging".<br>
Example: `docsearch -w "budg*"`

**Can I exclude certain terms from results?**
Yes — use the `-n` flag. This filters out any lines that contain the specified terms, even if they match your search. Use commas for multiple exclude terms. The exclude check follows the current search mode — in fuzzy mode, exclude terms are fuzzy-matched; in wildcard mode, they are wildcard-matched.<br>
Example: `docsearch -n draft budget`<br>
Example with multiple excludes: `docsearch -n draft,obsolete budget`

**Can I search scanned PDFs or images?**
Yes — use the `-O` flag. This uses OCR (Optical Character Recognition) to extract text from scanned PDF pages and image files (.jpg, .jpeg, .png, .tiff, .tif, .bmp). Tesseract must be installed on your system — see the [Installation](#installation) section for instructions. OCR is slower than regular text search, so it's opt-in.<br>
Example: `docsearch -O budget`

**Can I use regex patterns?**
Yes — use the `-x` flag. [Common Regex Patterns](#common-regex-search-patterns)<br>
Example: `docsearch -x "\d{3}-\d{3}-\d{4}"`

**Can I see lines before and after each match?**
Yes — use the `-B` and `-A` flags.<br>
Example: `docsearch -B 3 -A 3 budget`<br>
This captures 3 lines before (-B) and 3 lines after (-A) each match. The numbers can be different, e.g., `-B 2 -A 5`.

**Can I require all terms to appear in the same paragraph?**
Yes — use the `-a` flag.<br>
Example: `docsearch -a budget revenue expenses`

**How many CPU cores does docsearch use?**
By default, docsearch uses half of your available CPU cores to keep your machine responsive. Use the `-c` flag to control this.<br>
Example: `docsearch -c 4 budget`<br>
For small numbers of files (fewer than 10), single-threaded mode is used automatically to avoid overhead.<br>
docsearch displays your core count and default `-c` value in the banner every time it runs (also visible with `docsearch -h`). You can also check manually:<br>
- **macOS:** Open Terminal and run `sysctl -n hw.ncpu`<br>
- **Windows:** Open Command Prompt and run `echo %NUMBER_OF_PROCESSORS%`<br>
- **Linux:** Open Terminal and run `nproc`

You can set `-c` to any value from 1 to your maximum core count. Using more cores speeds up searches but uses more memory and CPU, which can slow down other applications and drain laptop batteries faster. The default (half of available cores) balances speed with keeping your machine responsive. Use `-c 1` for minimal resource usage, or `-c` with your full core count (e.g., `-c 8` on an 8-core machine) for maximum speed at the cost of heavier system load.

**Can I use multiple flags at the same time?**
Yes — most flags can be mixed and matched. Flag order doesn't matter.<br>
Example: `docsearch -r -a -t pdf budget revenue` searches recursively, with AND logic, only in PDF files. See the [Command Examples](#command-examples) table for many combinations.

**Do I have to use the terminal, or is there a GUI?**
Both. If you prefer a graphical interface, run `docsearch-gui` for a point-and-click window with a search box, folder picker, and all the advanced options. If you're comfortable in the terminal, `docsearch` gives you the same search power in a single command.

Never used a terminal before? It's simpler than it looks — type `docsearch` followed by what you're looking for, press Enter, and you're done. No menus, no buttons, no settings buried three screens deep. The terminal also launches instantly, runs identically on Mac, Windows, and Linux, and keeps a history of your commands so you can press the up arrow to repeat or tweak a previous search.

**What operating systems does docsearch run on?**
docsearch runs on macOS, Windows, and Linux — anywhere Python 3.10 or higher is installed.

**Does it search inside ZIP or RAR files?**
No — docsearch searches uncompressed files only.

**Does it work offline?**
Yes — docsearch runs entirely on your local machine with no internet connection needed. Your documents never leave your computer — no cloud uploads, no third-party servers, no risk of data exposure. This makes it ideal for sensitive files like medical records, financial documents, legal files, and personal correspondence. It also means no rate limits, no usage caps, no subscriptions, and no slowdowns from server traffic. It works the same whether you have fast internet, slow internet, or no internet at all.

**Does it modify my files?**
No — docsearch only reads your files. It never changes, moves, or deletes them.

**Is the search case-sensitive?**
No — all searches are case-insensitive by default.

Every feature in docsearch serves the core mission of finding content in documents:

- **Search flags** (`-a`, `-x`, `-p`, `-O`, `-z`, `-w`) — control *how* to match
- **Filter flags** (`-t`, `-f`, `-r`, `-n`) — control *where* to search
- **Context flags** (`-A`, `-B`) — control *what to show* around matches
- **Output flags** (`-s`, `-sa`) — control *what to do* with results
- **Performance flags** (`-c`) — control *how fast* to search
- **Settings flag** (`--config`) — manage *saved settings*

## Running Tests

Running tests requires the cloned repository (see [Option B](#option-b-manual-install)). From the project folder:

```bash
source venv/bin/activate
pytest tests/ -v
```

## Project Structure

```
Claude-DocSearch/
├── docsearch/
│   ├── __init__.py      # Package init
│   ├── __main__.py      # Enables python -m docsearch
│   ├── cli.py           # Main CLI entry point
│   └── gui.py           # Optional GUI (docsearch-gui)
├── tests/
│   ├── test_cli.py      # CLI test suite
│   └── test_gui.py      # GUI test suite
├── pyproject.toml       # Project metadata and dependencies
├── requirements.txt     # Pip requirements
└── README.md
```

## License

This project is licensed under the [MIT License](LICENSE).
