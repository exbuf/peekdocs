# Claude-DocSearch

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
  - [Supported File Types](#supported-file-types)
- [Benefits and Applications](#benefits-and-applications)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Steps](#steps)
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

If you've ever downloaded years of documents to your local machine and then realized you have no way to search through them — that's exactly why docsearch exists. It searches across 25 file types — including PDFs, Word docs, spreadsheets, presentations, and e-books — using plain text or regex patterns, with AND/OR logic, proximity search to find terms near each other, context lines before and after each match, and results highlighted and saved to both `.txt` and `.docx` files, all entirely offline.

I'm a 77-year-old retired electrical engineer, programmer, and software patent holder who recently discovered Claude Code and used it to build my new website. For years I'd been meaning to back up my Google Docs and Sheets to my local machine — hundreds of files accumulated over a decade — but I kept putting it off because I knew that once they were saved locally, I'd have no easy way to search through them. I also had plenty of other documents that were never in Google to begin with — old Word files, PDFs, text files scattered across folders.

Then it hit me: with Claude Code, I could build the search tool myself.

What began as a weekend project took on a life of its own. I kept thinking "what if it could also do this?" and before long, docsearch had grown into something far more capable than I originally imagined. It searches across PDFs, Word docs, spreadsheets, and text files. It supports regex patterns. It works entirely offline, keeping your data private.

I built docsearch for myself, but I'm sharing it because I suspect I'm not the only one drowning in years of documents. If that sounds familiar, I hope this tool helps you as much as it's helped me.

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

### Supported File Types

| File Type | Description |
|-----------|-------------|
| `.cfg` | Configuration file |
| `.csv` | Comma-separated values |
| `.docx` | Microsoft Word document |
| `.epub` | E-book (EPUB format) |
| `.html` | HTML web page |
| `.ini` | INI configuration file |
| `.json` | JSON data file |
| `.log` | Log file |
| `.md` | Markdown document |
| `.odp` | OpenDocument Presentation (LibreOffice Impress) |
| `.ods` | OpenDocument Spreadsheet (LibreOffice Calc) |
| `.odt` | OpenDocument Text (LibreOffice Writer) |
| `.pdf` | PDF document |
| `.pptx` | Microsoft PowerPoint presentation |
| `.rst` | reStructuredText document |
| `.rtf` | Rich Text Format document |
| `.sql` | SQL script |
| `.tex` | LaTeX document |
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
- **Search across formats** — find information across PDFs, Word docs, presentations, spreadsheets, e-books, RTF, Markdown, JSON, XML, YAML, TOML, LaTeX, reStructuredText, SQL, config files, log files, and text files in one place
- **Build a personal knowledge base** — writers, students, and researchers can search years of notes, clippings, and drafts instantly
- **Preserve family and personal records** — genealogy notes, old letters, scanned documents, decades of personal history made searchable
- **Support professional work** — lawyers, consultants, and others with years of case files or client notes can quickly find precedents or past work

Local search is also fast, with no rate limits, usage caps, or waiting on cloud services.

**Programming process:** DocSearch was developed using Claude Code. It's my second Claude Code app, the first being my personal website.

## Installation

### Prerequisites

- Python 3.10 or higher — check if it's already installed by running `python3 --version` (macOS/Linux) or `python --version` (Windows)
  - **macOS:** Install from [python.org](https://www.python.org/downloads/) or via Homebrew: `brew install python`
  - **Windows:** Install from [python.org](https://www.python.org/downloads/) — check "Add Python to PATH" during installation
  - **Linux:** Usually pre-installed. If not: `sudo apt install python3` (Ubuntu/Debian) or `sudo dnf install python3` (Fedora)

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

Then navigate to the directory containing your document files and run:

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

docsearch has ten flags that can be mixed and matched:

| Flag&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Purpose |
|------------|---------|
| `-a` | AND logic (all terms must appear in the same paragraph) |
| `-f` | Search specific files (comma-separated, e.g., `report.pdf,notes.txt`) |
| `-r` | Search subdirectories recursively |
| `-t` | Filter by file type (comma-separated, e.g., `pdf,docx`) |
| `-p N` | Proximity search — find terms within N words of each other |
| `-s` | The -s flag is not for searching. It is used to archive the docsearch_results.docx and docsearch_results.txt files to new files named DO_NOT_SEARCH_your_file_name.docx (and .txt). The archived files are placed in the same directory folder as the two docsearch_results files. It does not erase the two original docsearch_results files. But the docsearch_results.docx and docsearch_results.txt files ARE erased and loaded with new results the next time you do a search. The -s flag and process just lets you save the current results if you need them.<br><br>Example: The command `docsearch -s your_file_name` will copy the contents of the two docsearch_results files to the two new DO_NOT_SEARCH_your_file_name files. (Don't type 'DO_NOT_SEARCH' in the command line; it's automatically provided.) This is to prevent re-searching these two files unnecessarily; docsearch skips any files with DO_NOT_SEARCH in the file name. The your_file_name could be something descriptive, or it could be a list of actual search terms you used to generate the search results. |
| `-sa` | Search and auto-append — runs the search normally, then appends the results to DO_NOT_SEARCH_ACCUMULATED_your_file_name.txt (and .docx). Use this to accumulate results from multiple searches into one file. The DO_NOT_SEARCH_ACCUMULATED prefix is added automatically.<br><br>Example: `docsearch -sa my_report budget revenue` results in your search for the terms budget and revenue being saved in file DO_NOT_SEARCH_ACCUMULATED_my_report.docx (and .txt). |
| `-x` | Regex pattern search (case-insensitive) |
| `-A N` | Show N lines after each match |
| `-B N` | Show N lines before each match |

### No flags (default)
```bash
docsearch budget revenue
```
OR search across all 25 file types in the current directory.

### Single flags
```bash
docsearch -a budget revenue          # AND search
docsearch -f report.pdf budget       # search only report.pdf
docsearch -p 5 budget revenue        # terms within 5 words of each other
docsearch -r budget                  # recursive search
docsearch -s my_report               # save results to named file
docsearch -sa my_report budget       # search and append results to named file
docsearch -t pdf,md budget           # only search .pdf and .md files
docsearch -x "\d{3}-\d{4}"          # regex search
docsearch -A 5 budget                # show 5 lines after each match
docsearch -B 3 budget                # show 3 lines before each match
```

### Two-flag combinations
```bash
docsearch -a -t csv,xlsx budget revenue     # AND search, only in .csv and .xlsx
docsearch -f report.pdf,data.csv -a budget revenue  # specific files, AND search
docsearch -f report.pdf -r budget           # specific file, recursive
docsearch -f report.pdf -x "\d{3}-\d{4}"   # specific file, regex
docsearch -f report.pdf -B 3 -A 3 budget   # specific file, context lines
docsearch -p 5 -r budget revenue            # proximity, recursive
docsearch -p 5 -t pdf,docx budget revenue  # proximity, file type filter
docsearch -sa my_report -a budget revenue  # save-append with AND search
docsearch -sa my_report -r budget          # save-append, recursive
docsearch -sa my_report -t pdf budget      # save-append, file type filter
docsearch -r -a budget revenue              # recursive AND search
docsearch -r -t pdf,docx budget             # recursive, only .pdf and .docx
docsearch -x -a "\d{3}" "\$\d+\.\d{2}"     # regex AND search
docsearch -x -t txt,csv "\b2026-\d{2}\b"   # regex, only .txt and .csv
docsearch -B 3 -A 3 budget                 # 3 lines before and after each match
docsearch -A 5 -t docx budget              # 5 lines after, only .docx files
```

### Three or more flags
```bash
docsearch -r -a -t txt,md budget revenue expenses
```
Recursively searches subdirectories, only in `.txt` and `.md` files, for paragraphs containing ALL three terms.

```bash
docsearch -x -r -t txt,csv "\d{3}-\d{3}-\d{4}"
```
Regex search recursively, only in `.txt` and `.csv` files.

```bash
docsearch -f report.pdf -r -a budget revenue
```
Search only `report.pdf`, recursively, for paragraphs containing ALL terms.

```bash
docsearch -p 5 -r -t pdf budget revenue
```
Proximity search recursively, only in `.pdf` files, for terms within 5 words of each other.

```bash
docsearch -sa my_report -r -t pdf budget revenue
```
Search and append results recursively, only in `.pdf` files.

- Use `-f` flag to search specific files (e.g., `docsearch -f report.pdf,notes.txt budget`)
- Use `-p N` flag for proximity search (e.g., `docsearch -p 5 budget revenue`)
- Use `-r` flag to search all subdirectories recursively
- Use `-s` flag to save results to a named file (e.g., `docsearch -s my_report`)
- Use `-sa` flag to search and auto-append results to a named file (e.g., `docsearch -sa my_report budget revenue`)
- Use `-t` flag to search only specific file types (e.g., `docsearch -t pdf,docx budget`)
- Use `-x` flag for regex pattern searches (e.g., `docsearch -x "\d{3}-\d{3}-\d{4}"`)
- Use `-A N` flag to show N lines after each match (e.g., `docsearch -A 5 budget`)
- Use `-B N` flag to show N lines before each match (e.g., `docsearch -B 5 budget`)

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
| | **Save, Version, and Help** | |
| 40 | Save results to a named file | `docsearch -s name_of_your_file` |
| | **Save and Append Searches** | |
| 41 | Search and append results to a file | `docsearch -sa my_report budget` |
| 42 | Append with AND search | `docsearch -sa my_report -a budget revenue` |
| 43 | Append with recursive search | `docsearch -sa my_report -r budget` |
| 44 | Append with file type filter | `docsearch -sa my_report -t pdf budget` |
| | **Version and Help** | |
| 45 | Show version | `docsearch -v` |
| 46 | Show help | `docsearch -h` |
| 47 | Show help (no arguments) | `docsearch` |

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

The terminal also displays a summary:
```
Found 2 match(es). Results written to docsearch_results.txt and docsearch_results.docx
```

## FAQ (Frequently Asked Questions)

**Can I search all subfolders?**
Yes — use the `-r` flag.<br>
Example: `docsearch -r budget`

**Can I search only PDFs (etc)?**
Yes — use the `-t` flag.<br>
Example: `docsearch -t pdf budget`

**Can I search a specific file?**
Yes — use the `-f` flag.<br>
Example: `docsearch -f report.pdf budget`

**Can I find terms near each other?**
Yes — use the `-p` flag.<br>
Example: `docsearch -p 5 budget revenue`

**Can I save these results?**
Yes — use the `-s` flag.<br>
Example: `docsearch -s my_report`

**Can I accumulate results from multiple searches?**
Yes — use the `-sa` flag.<br>
Example: `docsearch -sa my_report budget revenue`

**Can I use regex patterns?**
Yes — use the `-x` flag. [Common Regex Patterns](#common-regex-search-patterns)<br>
Example: `docsearch -x "\d{3}-\d{3}-\d{4}"`

**Can I see lines before and after each match?**
Yes — use the `-B` and `-A` flags.<br>
Example: `docsearch -B 3 -A 3 budget`

**Can I require all terms to appear in the same paragraph?**
Yes — use the `-a` flag.<br>
Example: `docsearch -a budget revenue expenses`

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

- **Search flags** (`-a`, `-x`, `-p`) — control *how* to match
- **Filter flags** (`-t`, `-f`, `-r`) — control *where* to search
- **Context flags** (`-A`, `-B`) — control *what to show* around matches
- **Output flags** (`-s`, `-sa`) — control *what to do* with results

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
