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
  - [Steps](#steps)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Regex Search](#regex-search)
    - [Common Regex Search Patterns](#common-regex-search-patterns)
- [Flag Use Summary](#flag-use-summary)
  - [Command Examples](#command-examples)
  - [Notes](#notes)
- [Output](#output)
- [FAQ (Frequently Asked Questions)](#faq-frequently-asked-questions)
- [Running Tests](#running-tests)
- [Project Structure](#project-structure)
- [License](#license)

## Introduction

docsearch is a fast, offline search tool that scans 25+ file types — including PDFs, Word documents, spreadsheets, presentations, and e-books — all at once, without uploading anything to the cloud. Search using plain keywords, or go deeper with AND/OR logic to require all terms or match any of them. Use proximity search to find words that appear near each other, regular expressions for precise pattern matching (like phone numbers, dates, or email addresses), and context lines to see surrounding text for every hit. With the `-O` flag, docsearch can even read scanned PDFs and image files using OCR (Optical Character Recognition). Results are highlighted in the terminal and saved to `.txt` and `.docx` files for easy review and sharing. Whether you're a home user digging through years of personal documents or a professional searching legal files, research papers, or business records, docsearch handles it in seconds — no internet connection required.

I built it because I had hundreds of documents backed up from Google Docs and scattered across folders, with no way to search through them. If that sounds familiar, I hope this tool helps you as much as it's helped me.

## Features

- Searches all files in the active directory/subdirectories. Or, with the -t flag, you can focus your search on specific file types and ignore the rest. See table for supported file types.
- Rich set of flags for controlling docsearch behavior. See Flag summary table below.
- Case-insensitive matching
- Supports multiple search terms with OR logic (finds any match) by default
- Example: `docsearch term1 term2 term3` // any term must appear in the paragraph
- For AND logic (where all search terms must appear in the same paragraph) use the `-a` flag
- Example: `docsearch -a term1 term2 term3`   // all terms must appear in the paragraph
- Proximity search with `-p` flag finds terms within N words of each other
- Example: `docsearch -p 5 budget revenue`   // terms must appear within 5 words
- Use quotes for multi-word phrases (e.g., `"annual report"`)
- Don't separate search terms with commas unless they're part of the search term itself
- Highlights matched terms with `**` markers in `.txt` output and yellow highlighting in `.docx` output, with search terms highlighted in green in the `.docx` header
- Results include document name, file directory path, line number, and matched text
- Timestamped output file
- Generates both `docsearch_results.txt` and `docsearch_results.docx`
- Gracefully handles corrupt or unreadable files — skips them with a warning instead of crashing
- Special characters (`<`, `>`, `[`, `]`, `*`, `?`, `$`, `|`, etc.) must be enclosed in quotes to prevent shell interpretation. Example: `docsearch "<" "[test]" "$amount"`
- Save search results with `-s` flag — copies results to named files prefixed with `DO_NOT_SEARCH_` so they won't be included in future searches
- Auto-append search results with `-sa` flag — runs the search and automatically appends results to a named `DO_NOT_SEARCH_ACCUMULATED_` file, allowing you to accumulate results from multiple searches
- Files with `DO_NOT_SEARCH` in the name are automatically skipped during searches
- Multiprocessing with `-c N` flag — uses multiple CPU cores to search files in parallel, speeding up large searches. Defaults to half of available cores to keep your machine responsive
- OCR support with `-O` flag — extracts text from scanned PDFs and image files (.jpg, .jpeg, .png, .tiff, .tif, .bmp) using Optical Character Recognition. Requires Tesseract (see [Installation](#installation))

### Supported File Types

All file types can exist in the same folder — no need to separate them into different folders. docsearch searches all supported types together in a single pass.

| File Type | Description |
|-----------|-------------|
| `.bmp` | Bitmap image (requires `-O` flag) |
| `.cfg` | Configuration file |
| `.csv` | Comma-separated values |
| `.docx` | Microsoft Word document |
| `.epub` | E-book (EPUB format) |
| `.html` | HTML web page |
| `.ini` | INI configuration file |
| `.jpg` / `.jpeg` | JPEG image (requires `-O` flag) |
| `.json` | JSON data file |
| `.log` | Log file |
| `.md` | Markdown document |
| `.odp` | OpenDocument Presentation (LibreOffice Impress) |
| `.ods` | OpenDocument Spreadsheet (LibreOffice Calc) |
| `.odt` | OpenDocument Text (LibreOffice Writer) |
| `.pdf` | PDF document (scanned PDFs require `-O` flag) |
| `.png` | PNG image (requires `-O` flag) |
| `.pptx` | Microsoft PowerPoint presentation |
| `.rst` | reStructuredText document |
| `.rtf` | Rich Text Format document |
| `.sql` | SQL script |
| `.tex` | LaTeX document |
| `.tiff` / `.tif` | TIFF image (requires `-O` flag) |
| `.toml` | TOML configuration file |
| `.tsv` | Tab-separated values |
| `.txt` | Plain text file |
| `.xlsx` | Microsoft Excel spreadsheet |
| `.xml` | XML data file |
| `.yaml` | YAML configuration file |
| `.yml` | YAML configuration file |

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
- No internet connection required — docsearch runs entirely offline
- No database required — the only optional extra software is Tesseract, needed only for OCR (the `-O` flag)
- To view the `.docx` report, you need a word processor such as Microsoft Word, LibreOffice Writer (free), Google Docs (free), or Apple Pages (free, Mac only). The report file (`docsearch_results.docx`) is saved in the same folder where you ran docsearch. To open it, navigate to that folder in your file manager — Finder on Mac, File Explorer on Windows, or Files on Linux — and double-click the file. It will automatically open in your default word processor. The `.txt` report can be opened on any computer with no additional software

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
| `ocr` | true/false | `-O` | false (no OCR) |
| `file_types` | comma-separated | `-t` | all supported types |

If no settings are saved or if a value is invalid, docsearch uses its built-in defaults. Session-specific flags like `-p`, `-f`, `-s`, and `-sa` are not configurable.

**Advanced:** Your settings are stored in a text file called `.docsearchrc` in your user folder. You can also edit this file directly if you prefer — each line is a `key = value` pair, and lines starting with `#` are comments.

## Installation

### Prerequisites

- Python 3.10 or higher — check if it's already installed by running `python3 --version` (macOS/Linux) or `python --version` (Windows)
  - **macOS:** Install from [python.org](https://www.python.org/downloads/) or via Homebrew: `brew install python`
  - **Windows:** Install from [python.org](https://www.python.org/downloads/) — check "Add Python to PATH" during installation
  - **Linux:** Usually pre-installed. If not: `sudo apt install python3` (Ubuntu/Debian) or `sudo dnf install python3` (Fedora)
- **Tesseract OCR** (optional — only needed for the `-O` flag, which enables searching scanned PDFs and images)
  - **macOS:** `brew install tesseract`
  - **Windows:** Download installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
  - **Linux:** `sudo apt install tesseract-ocr` (Ubuntu/Debian) or `sudo dnf install tesseract` (Fedora)

### Steps

1. Clone the repository (requires [git](https://git-scm.com/downloads)):
   ```bash
   git clone https://github.com/exbuf/Claude-DocSearch.git
   cd Claude-DocSearch
   ```
   **Don't have git?** Click the green **Code** button on the [GitHub page](https://github.com/exbuf/Claude-DocSearch), select **Download ZIP**, extract it, and open the extracted folder in your terminal.

2. Create and activate a virtual environment:

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

3. Install the package:
   ```bash
   pip install -e .
   ```

## Quick Start

Open your terminal, navigate to the folder containing your documents, and search:

```bash
cd /path/to/your/documents
docsearch budget
```

That's it. docsearch scans every supported file in the folder and saves the results to `docsearch_results.txt` and `docsearch_results.docx`.

A few more examples to try:

```bash
docsearch budget revenue              # find files containing "budget" OR "revenue"
docsearch -a budget revenue           # find files containing both terms
docsearch -r budget                   # search subdirectories too
docsearch -t pdf,docx budget          # search only PDFs and Word docs
```

See the [Command Examples](#command-examples) table for 62 more combinations.

## Usage

First, activate the virtual environment:

**macOS/Linux (Terminal):**
```bash
cd /path/to/Claude-DocSearch
source venv/bin/activate
```

**Windows (Command Prompt):**
```cmd
cd \path\to\Claude-DocSearch
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
cd \path\to\Claude-DocSearch
venv\Scripts\Activate.ps1
```

Then navigate to the directory containing your document files and run docsearch with your search terms. See the [Command Examples](#command-examples) table for usage.

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

docsearch has fourteen flags that can be mixed and matched:

| Flag&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Purpose |
|------------|---------|
| `-a` (all) | AND logic — all terms must appear in the same paragraph |
| `-c N` (cores) | Number of CPU cores for parallel search (default: half of available cores). See [FAQ](#faq-frequently-asked-questions) for tradeoffs |
| `-f` (files) | Search specific files (comma-separated, e.g., `report.pdf,notes.txt`) |
| `-O` (OCR) | Enable OCR for scanned PDFs and image files (requires [Tesseract](#prerequisites)) |
| `-p N` (proximity) | Proximity search — find terms within N words of each other |
| `-q` (quiet) | Quiet mode — suppress the banner |
| `-r` (recursive) | Search subdirectories recursively |
| `-s` (save) | Archive results — copies docsearch_results files to DO_NOT_SEARCH_your_file_name.docx (and .txt). The DO_NOT_SEARCH prefix is added automatically so archived files are never re-searched. Does not erase the original results files, but they are overwritten on the next search. Example: `docsearch -s my_report` |
| `-sa` (save-append) | Search and auto-append — runs the search normally, then appends the results to DO_NOT_SEARCH_ACCUMULATED_your_file_name.txt (and .docx). Use this to accumulate results from multiple searches into one file. The DO_NOT_SEARCH_ACCUMULATED prefix is added automatically.<br><br>Example: `docsearch -sa my_report budget revenue` results in your search for the terms budget and revenue being saved in file DO_NOT_SEARCH_ACCUMULATED_my_report.docx (and .txt). |
| `-t` (types) | Filter by file type (comma-separated, e.g., `pdf,docx`) |
| `-x` (regex) | Regex pattern search (case-insensitive) |
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
| | **Saved Settings** | |
| 56 | View saved settings | `docsearch --config` |
| 57 | Save a setting | `docsearch --config recursive=true` |
| 58 | Save multiple settings | `docsearch --config recursive=true cores=4` |
| 59 | Remove a saved setting | `docsearch --config recursive=` |
| | **Version and Help** | |
| 60 | Show version | `docsearch -v` |
| 61 | Show help | `docsearch -h` |
| 62 | Show help (no arguments) | `docsearch` |

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

**Why is docsearch a terminal application? Why doesn't it have a GUI?**
docsearch was designed as a command-line tool for speed, simplicity, and portability. Terminal apps launch instantly, run on any operating system without modification, and are easy to script or automate. A GUI would add complexity and platform-specific dependencies without improving the core search functionality.

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

**What happens if a file is corrupt or unreadable?**
docsearch skips it with a warning and continues searching the remaining files.

Every feature in docsearch serves the core mission of finding content in documents:

- **Search flags** (`-a`, `-x`, `-p`, `-O`) — control *how* to match
- **Filter flags** (`-t`, `-f`, `-r`) — control *where* to search
- **Context flags** (`-A`, `-B`) — control *what to show* around matches
- **Output flags** (`-s`, `-sa`) — control *what to do* with results
- **Performance flags** (`-c`) — control *how fast* to search
- **Settings flag** (`--config`) — manage *saved settings*

## Running Tests

```bash
source venv/bin/activate
pytest tests/ -v
```

## Project Structure

```
Claude-DocSearch/
├── docsearch/
│   └── cli.py          # Main CLI entry point
├── tests/
│   └── test_cli.py     # Test suite
├── pyproject.toml       # Project metadata and dependencies
├── requirements.txt     # Pip requirements
└── README.md
```

## License

This project is licensed under the [MIT License](LICENSE).
