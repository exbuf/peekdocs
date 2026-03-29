# docsearch

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
  - [Command Translation](#command-translation)
- [Search Index (Optional)](#search-index-optional)
- [Inverse Search](#inverse-search)
- [Boolean Expression Search](#boolean-expression-search)
- [Range Queries](#range-queries)
- [Combining Modes](#combining-modes)
- [Breaking Down Complex Searches](#breaking-down-complex-searches)
- [Using docsearch for Compliance and Auditing](#using-docsearch-for-compliance-and-auditing)
  - [Why audits exist](#why-audits-exist)
  - [Who performs audits](#who-performs-audits)
  - [Industry examples](#industry-examples)
  - [How docsearch fits](#how-docsearch-fits)
  - [Sample compliance suites by industry](#sample-compliance-suites-by-industry)
- [Search Suites](#search-suites)
- [FAQ (Frequently Asked Questions)](#faq-frequently-asked-questions)
- [Troubleshooting](#troubleshooting)
- [Library API](#library-api)
- [Running Tests](#running-tests)
- [Project Structure](#project-structure)
- [License](#license)

## Introduction

docsearch is a fast, offline search tool that scans 29 file types — including PDFs, Word documents, spreadsheets, presentations, and e-books — all at once, without uploading anything to the cloud. Results are saved to an easy-to-read `.docx` report with every match highlighted in yellow and shown with full paragraph context, so you can understand each result without opening the original file. Search using plain keywords, or go deeper with AND/OR logic to require all terms or match any of them. Use proximity search to find words that appear near each other, wildcards for simple pattern matching (`budg*` finds "budget", "budgets", "budgeting"), regular expressions for precise pattern matching (like phone numbers, dates, or email addresses), fuzzy matching for typo-tolerant searches and imperfect OCR text, exclude terms to filter out unwanted matches (`-n draft` skips lines containing "draft"), range queries to filter by dates, dollar amounts, percentages, ages, or file metadata (`-R amount:1000..5000`), and context lines to see surrounding text for every hit. With the `-O` flag, docsearch can even read scanned PDFs and image files using OCR (Optical Character Recognition). Results are also highlighted in the terminal and saved to a plain `.txt` file. Prefer not to use the terminal? docsearch includes a point-and-click GUI — just run `docsearch-gui`. Whether you're a home user digging through years of personal documents or a professional searching legal files, research papers, or business records, docsearch handles it in seconds — no internet connection required.

I had hundreds of documents backed up from Google Docs and scattered across folders, along with other documents and files, with no convenient way to search through them. If that sounds familiar, I hope this tool helps you as much as it's helped me.

**docsearch is read-only. It does not modify, move, or delete any of your files.** The only files it creates are its own report files (`docsearch_results.txt`, `docsearch_results.docx`, and optionally `.csv` and `.json`) in the current directory (or a directory you specify with `--output-dir`), plus an optional `.docsearch.db` index file if you use `--index`, and an optional `.docsearch_collection.json` file if you save searches to a collection for search suites.

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
- Per-file match counts — see at a glance how many matches each file contributed
- Generates timestamped `docsearch_results.txt` and `docsearch_results.docx` reports with a plain-English **translation** of each command — regex patterns like `\d{3}-\d{3}-\d{4}` are automatically described as "a US phone number", dates, emails, dollar amounts, and more
- Gracefully handles corrupt or unreadable files — skips them with a warning instead of crashing
- Special characters (`<`, `>`, `[`, `]`, `*`, `?`, `$`, `|`, etc.) must be enclosed in quotes to prevent shell interpretation. Example: `docsearch "<" "[test]" "$amount"`
- Save or accumulate results with `-s` and `-sa` flags — saved files are automatically prefixed with `DO_NOT_SEARCH` so they're never re-searched
- Multiprocessing with `-c N` flag — uses multiple CPU cores to search files in parallel, speeding up large searches. Defaults to half of available cores to keep your machine responsive
- OCR support with `-O` flag — extracts text from scanned PDFs and image files (.jpg, .jpeg, .png, .tiff, .tif, .bmp) using Optical Character Recognition. Requires Tesseract (see [Installation](#installation))
- Fuzzy matching with `-z` flag — finds approximate matches for typos, misspellings, and OCR recognition errors (e.g., "budgt" matches "budget")
- Wildcard search with `-w` flag — simple pattern matching where `*` matches any characters and `?` matches one character (e.g., `budg*` matches "budget", "budgets", "budgeting")
- Exclude terms with `-n` flag — filter out lines containing unwanted terms (e.g., `-n draft budget` finds "budget" but skips lines containing "draft")
- Boolean expression search with `-e` flag — combine AND, OR, NOT, parentheses, and range specs for complex queries: `docsearch -e "(budget AND amount:1000..5000) OR revenue"`. Works with regex, fuzzy, and wildcard modes
- Range queries with `-R` flag — filter by dates, dollar amounts, numbers, percentages, ages, times, file sizes, or file dates. Multiple ranges combine with AND logic. Supports open-ended ranges, range-only searches, and embedding in boolean expressions
- Inverse search with `--inverse` flag — lists files that do NOT contain the search terms, instead of files that do. Useful for compliance checks ("which contracts are missing an indemnification clause?") and auditing ("which documents lack a required disclaimer?")
- Optional search index (`--index`) — build a SQLite FTS5 index for faster repeated searches. Once built, the index is used automatically and refreshed incrementally
- Search suites — save individual searches to a named collection, build search suites from saved searches, run them one-by-one with pass/fail tracking, and generate compliance/audit reports
- Optional GUI (`docsearch-gui`) — a point-and-click interface with search box, folder picker, and all advanced options, for users who prefer not to use the terminal
- Library API — call `search()` from your own Python code to integrate docsearch into automated workflows, pipelines, and custom applications

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
- No external database required — the optional search index uses SQLite (built into Python) and the only optional extra software is Tesseract, needed only for OCR (the `-O` flag)
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
| `proximity` | number | `-p N` | 0 (disabled) |
| `max_matches` | number | `-m N` | 1000 (cap report matches) |
| `output_csv` | true/false | `-o csv` | false (no CSV output) |
| `output_json` | true/false | `-o json` | false (no JSON output) |
| `exclude` | comma-separated | `-n` | empty (no exclusions) |
| `specific_files` | comma-separated | `-f` | empty (search all files) |
| `save_name` | text | `-s` | empty (no custom save) |
| `append_name` | text | `-sa` | empty (no append) |
| `inverse` | true/false | `--inverse` | false (normal search) |
| `whole_word` | true/false | `-W` | false (partial matches allowed) |
| `timestamp` | true/false | `--timestamp` | true in GUI (add timestamp to report filenames) |
| `suite_timestamp` | true/false | — | true in GUI (add timestamp to suite/stage report filenames) |
| `output_dir` | path | `--output-dir` | empty (write to search folder) |
| `range` | spec list | `-R` | empty (no range filtering) |
| `index_search` | true/false | — | false (direct file search) |
| `search_terms` | text | — | empty (none) |
| `folder` | path | — | empty (current directory) |

If no settings are saved or if a value is invalid, docsearch uses its built-in defaults. The `search_terms`, `folder`, and `index_search` settings are GUI-only — they pre-fill the GUI fields when it opens but have no effect on CLI searches.

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
   pipx install git+https://github.com/exbuf/docsearch.git
   ```

That's it. `docsearch` and `docsearch-gui` are now available from any terminal — no activation step, no virtual environment to manage.

### Option B: Manual Install

If you prefer to manage things yourself, or if pipx is not available:

1. Clone the repository (requires [git](https://git-scm.com/downloads)):
   ```bash
   git clone https://github.com/exbuf/docsearch.git
   cd docsearch
   ```
   **Don't have git?** Click the green **Code** button on the [GitHub page](https://github.com/exbuf/docsearch), select **Download ZIP**, extract it, and open the extracted folder in your terminal.

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

   After running the activate command, you'll notice `(venv)` appear at the beginning of your command line. This is normal — it just means docsearch is ready to use. If you close your terminal and open it later, you won't see `(venv)` anymore. Just navigate back to the docsearch folder and run the activate command again (step 2 above) before using docsearch.

3. Install docsearch (make sure you're still in the docsearch folder):
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

See the [Command Examples](#command-examples) table for over 150 more combinations and examples.

## GUI Mode

If you prefer pointing and clicking over typing commands, docsearch has a graphical interface. It works exactly like the terminal version — same search, same results, same reports — but with a familiar window instead of a command line.

**How to open it:**

You still need to open a terminal once to launch the GUI. If you used the manual install (Option B), activate the workspace first (see [Option B step 2](#option-b-manual-install)). Then type:

```bash
docsearch-gui
```

A window will appear. From here, everything is point-and-click — no more terminal commands needed. The GUI can do everything the terminal can do; you don't give up any features by using it.

The GUI window is organized into these regions, from top to bottom:

| Region | Description |
|--------|-------------|
| **Search Bar** | Search entry field, **Inverse** checkbox, **Run Search** button, **Wizard** button, **Save Settings** button (saves the current search to the folder's collection for reuse in search suites), and **Load Settings ▼** button (opens a popup to load or delete saved searches) |
| **Folder Bar** | Folder path entry and **Browse** button |
| **Advanced Options** | Collapsible panel with all search options (click to expand) |
| **Search Suites** | Collapsible toggle — opens a standalone window to manage search suites, select one or more suites, run them with pass/fail tracking, schedule auto-runs, view last-run timestamps, and generate compliance/audit reports |
| **Index Options** | Collapsible toggle — **Auto-Refresh Index** interval selector, **Build Index(es)**, **Delete Index(es)**, **Index Status**, and **About Index** |
| **Results** | After a search: **Matched Files** button (click to view matching files and open them), **View Report:** label with **DOCX**, **CSV**, **JSON**, and **TXT** buttons to open reports in each format, and **View Error Log** if any files could not be read |
| **Toolbar** | **Open Readme.md**, **View Error Log**, and **About** buttons |

**Your first GUI search:**

1. Type what you're looking for in the **Search Bar**
2. Click **Browse** in the **Folder Bar** to pick the folder containing your documents (your home folder is selected by default)
3. Click **Run Search** (or press Enter)
4. When the search finishes, a result summary appears. Click **DOCX** next to **View Report:** to view your results in a `.docx` file with matches highlighted in yellow. You can also click **TXT**, **CSV**, or **JSON** to open the report in other formats. If any files could not be read, a **View Error Log** button also appears — click it to open `docsearch_errors.log` and see which files had problems and why

**Advanced Options:**

Click "Advanced Options" to expand a panel with additional settings — AND mode, recursive search, fuzzy matching, wildcards, OCR, regex, whole-word matching, expression mode, inverse search, exclude terms, file type filtering, proximity, context lines, CPU cores, max matches, range filters, specific files, save as, append to, output directory, additional output formats (CSV, JSON), and timestamp filenames. Every terminal flag is available in the GUI. You don't need any of them for a basic search. Hover over any option to see a description of what it does. At the bottom of the panel are four buttons: **Inspect .docsearchrc** shows the current saved settings (read-only). **Save Settings** saves your current search terms, folder, and all options as defaults — the next time you open the GUI, everything will be pre-filled. **Restore Settings** reloads saved defaults from `~/.docsearchrc` into the GUI. **Reset** clears all fields and restores the GUI to its default state.

**Index Options:**

Click "Index Options" below Search Suites to expand index controls. Use the **Auto-Refresh Index** dropdown to keep the index updated automatically. Click **Build Index(es)** to create the index (all subfolders are included automatically). Use **Delete Index(es)** to remove the index, **Index Status** to view index info, or **About Index** to learn how indexes work. The **Search Using Index(es)** checkbox is inside Advanced Options — check it to use the index for your next search, or uncheck it to search files directly.

Do not type flags (like `-a` or `-r`) into the **Search Bar** — it is only for search terms. Each checkbox and input field in **Advanced Options** handles the corresponding flag behind the scenes.

**Search Wizard:**

Click the **Wizard** button in the Search Bar to open the Search Wizard — a point-and-click regex builder. Instead of writing regex by hand, choose a profession-specific category and check the patterns you want:

| Category | Example patterns |
|----------|-----------------|
| **Common / General** | Dates, dollar amounts, phone numbers, email addresses, SSNs |
| **Business / Finance** | Invoice numbers, purchase orders, tax IDs, account numbers |
| **Legal** | Case numbers, statute references, Bates numbers, court dockets |
| **Medical / Healthcare** | ICD-10 codes, CPT codes, NPI numbers, patient IDs |
| **Engineering / Technical** | Part numbers, serial numbers, measurements, tolerances |
| **Real Estate** | Parcel/APN numbers, square footage, lot/block, MLS numbers |
| **HR / Admin** | SSNs, employee IDs, phone numbers, email addresses |
| **Compliance / Audit** | SSNs, tax IDs, employee IDs, dollar amounts, dates, classification markings, policy numbers, retention codes |

Use the **Match mode** radio buttons to choose **OR** (match any selected pattern) or **AND** (all selected patterns must appear). You can also type a custom regex in the **Custom regex** field. A live preview shows the combined regex before you apply it.

When you click **Apply**, the wizard inserts the regex into the Search Bar and automatically enables the Regex checkbox. If the Search Bar already has text, you can choose to replace or append. The wizard remembers your selections between uses.

**Mixing wizard patterns with typed terms:**

You can combine wizard-generated patterns with terms you type manually. This is powerful because the wizard's OR logic is embedded *inside* the regex pattern using `|`, while the AND mode checkbox controls how *separate* search terms relate to each other. They operate at different levels and don't conflict.

For example, to find paragraphs that contain a phone number or email address *and* the word "invoice":

1. Open the Wizard, select **Common / General**, check **Phone Number** and **Email Address** (with OR mode), click **Apply**
2. The Search Bar now contains one regex term: `(\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})|([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})`
3. After the regex, type a space and then `invoice` — the Search Bar now has two terms
4. Check the **AND mode** checkbox in Advanced Options

The search finds paragraphs where *both* conditions are true: at least one phone number or email appears, *and* the word "invoice" appears. The OR stays inside the wizard's regex, and the AND applies between the two separate search terms.

You can also build up the Search Bar in multiple passes — use the wizard once, append, type some words, open the wizard again with a different category, and append again. Each append adds to what's already there.

**Note:** The wizard enables regex mode. If you manually type additional terms containing special characters (`.` `+` `(` `)` `[` `]` etc.), escape them with `\` — for example, `cost\+fees`. Plain words like `budget` need no escaping.

**Compliance and audit examples:**

The wizard combined with typed search terms is especially useful for compliance, auditing, and risk management. Below are practical examples across industries. In each case, use the wizard to select the pattern(s), type any additional keyword(s), and check AND mode so both must appear together.

| Use case | Wizard patterns | Typed terms | Mode | What it finds |
|----------|----------------|-------------|------|---------------|
| **PII exposure scan** | SSN, Phone Number, Email Address (Common) | *(none — just the patterns)* | OR | Sensitive personal data in any document. Search shared drives and public folders — any match is a potential data privacy violation (GDPR, CCPA) |
| **HIPAA — PHI detection** | ICD-10 Code, Patient ID (Medical) | a patient name | AND | Protected health information appearing alongside patient identifiers — flags potential HIPAA exposure |
| **Invoice completeness** | Invoice Number, Dollar Amount, Date (Business) | *(none)* | AND | Invoices containing all three required fields. Documents that *don't* match may be missing required information |
| **Missing purchase orders** | Dollar Amount (Business) | invoice | AND, then search *without* PO Number | Find invoices with dollar amounts but no purchase order — flags spending without proper authorization |
| **Contract clause verification** | Dollar Amount, Date (Common) | indemnif | AND | Contracts containing financial terms and indemnification language — verifies required clauses are present |
| **Contract expiration review** | Date (Common) | termination renewal expir | AND | Contracts mentioning termination, renewal, or expiration alongside dates — identifies agreements approaching key deadlines |
| **Export control** | Part Number, Serial Number (Engineering) | controlled restricted ITAR | AND | Technical documents referencing part or serial numbers alongside export-control language |
| **HR records audit** | SSN, Employee ID (HR) | *(none — just the patterns)* | OR | SSNs or employee IDs in any folder. Matches on a shared or public drive indicate a policy violation |
| **Salary disclosure check** | Dollar Amount (Common) | salary compensation bonus | AND | Documents containing dollar amounts alongside pay-related terms — flags potential unauthorized salary disclosures |
| **Tax document review** | Tax ID / EIN, Dollar Amount (Business) | deduction credit | AND | Tax filings referencing specific EINs alongside deduction or credit language — useful for tax audit preparation |
| **Real estate due diligence** | Parcel / APN, Dollar Amount (Real Estate) | lien encumbrance easement | AND | Property documents referencing parcel numbers alongside potential title issues |
| **Insurance claims audit** | Dollar Amount, Date (Common) | claim denied approved | AND | Claims documents with dollar amounts, dates, and disposition keywords — identifies patterns in claim processing |
| **Regulatory filing check** | Case Number, Statute Reference (Legal) | violation penalty fine | AND | Legal filings referencing case numbers and statutes alongside enforcement language |
| **Vendor compliance** | Invoice Number, Dollar Amount (Business) | late overdue past.due | AND | Vendor invoices mentioning late or overdue status — identifies vendors with payment issues |
| **Document retention audit** | Date (Common) | destroy shred retain archive | AND | Documents containing dates alongside retention-related terms — helps enforce retention schedules |
| **Intellectual property scan** | Part Number, Drawing Number (Engineering) | confidential proprietary | AND | Engineering documents referencing specific parts alongside IP markings — verifies proper classification |
| **Background check compliance** | SSN, Date (Common) | consent authorization | AND | Background check documents containing SSNs and dates alongside consent language — verifies proper authorization was obtained |
| **Medical billing audit** | CPT Code, Dollar Amount (Medical) | *(none)* | AND | Medical billing records containing both procedure codes and dollar amounts — useful for detecting billing anomalies |

**Tip:** For any of these searches, enable **Recursive** to scan all subfolders, and use **File types** to limit the search to specific formats (e.g., `pdf,docx`). After the search completes, click **DOCX** next to **View Report:** to review all matches with context highlighted in yellow, or click **CSV** for further analysis in a spreadsheet.

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

docsearch has twenty-nine flags that can be mixed and matched:

| Flag&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Purpose |
|------------|---------|
| `-a` (all) | AND logic — all terms must appear in the same paragraph |
| `-c N` (cores) | Number of CPU cores for parallel search (default: half of available cores). See [FAQ](#faq-frequently-asked-questions) for tradeoffs |
| `-e` (expression) | Boolean expression search — use AND, OR, NOT, parentheses, and range specs for complex queries. See [Boolean Expression Search](#boolean-expression-search) |
| `-f` (files) | Search specific files (comma-separated, e.g., `report.pdf,notes.txt`) |
| `-m N` (max-matches) | Maximum matches included in reports (default: 1,000). Use `0` for no limit |
| `-n` (not) | Exclude lines matching specified terms (comma-separated, e.g., `-n draft,obsolete`) |
| `-o` (output) | Additional output formats — `csv`, `json`, or both (`csv,json`). The `.txt` and `.docx` reports are always created; `-o` adds extra formats |
| `-O` (OCR) | Enable OCR for scanned PDFs and image files (requires [Tesseract](#prerequisites)) |
| `-p N` (proximity) | Proximity search — find terms within N words of each other |
| `-q` (quiet) | Quiet mode — suppress the banner |
| `-R SPEC` / `--range` | Range filter — filter by value ranges in content or file metadata. Repeatable. See [Range Queries](#range-queries) |
| `-r` (recursive) | Search subdirectories recursively |
| `-s` (save) | Archive results — copies docsearch_results files to DO_NOT_SEARCH_your_file_name.docx (and .txt). The DO_NOT_SEARCH prefix is added automatically so archived files are never re-searched. Does not erase the original results files, but they are overwritten on the next search. Example: `docsearch -s my_report` |
| `-sa` (save-append) | Search and auto-append — runs the search normally, then appends the results to DO_NOT_SEARCH_ACCUMULATED_your_file_name.txt (and .docx). Use this to accumulate results from multiple searches into one file. The DO_NOT_SEARCH_ACCUMULATED prefix is added automatically.<br><br>Example: `docsearch -sa my_report budget revenue` results in your search for the terms budget and revenue being saved in file DO_NOT_SEARCH_ACCUMULATED_my_report.docx (and .txt). |
| `-t` (types) | Filter by file type (comma-separated, e.g., `pdf,docx`) |
| `--timestamp` (timestamp) | Add a timestamp suffix to report filenames (e.g., `docsearch_results_20260327_143022.txt`). Each search produces uniquely named files so previous results are preserved |
| `-w` (wildcard) | Wildcard pattern search — `*` matches any characters, `?` matches one character |
| `-W` (whole-word) | Whole-word matching — matches complete words only (`bob` matches "bob" but not "bobcat") |
| `-x` (regex) | Regex pattern search (case-insensitive) |
| `-z` (fuzzy) | Fuzzy matching — find approximate matches (e.g., typos like "budgt" matching "budget") |
| `--check` (check) | Verify installation — checks Python version, dependencies, Tesseract, and disk space |
| `--config` (config) | View, set, or remove saved settings. See [Saved Settings](#saved-settings-optional) |
| `--index` (index) | Build or rebuild the search index for faster repeated searches. See [Search Index](#search-index-optional) |
| `--index-clear` (index-clear) | Delete the search index |
| `--index-refresh` (index-refresh) | Incrementally update the index — add new files, re-index changed files, remove deleted files |
| `--index-status` (index-status) | Show index info — file count, line count, database size, creation date, and settings |
| `--inverse` (inverse) | Inverse search — list files that do NOT contain the search terms. See [Inverse Search](#inverse-search) |
| `--output-dir PATH` (output-dir) | Write all output files (reports, error log, CSV, JSON) to the specified directory instead of the search folder |
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
- `-e` always needs its expression immediately after it, enclosed in quotes (e.g., `-e "(bob AND amy) OR fred"`)
- `-e` and `-a` cannot be used together — use AND/OR inside the expression instead
- `-e` and `-n` cannot be used together — use NOT inside the expression instead
- `-e` and `-p` cannot be used together
- `-e` works with `-x` (regex), `-z` (fuzzy), `-w` (wildcard), `-r` (recursive), `-t` (file types), `-A`/`-B` (context), `-c` (cores), and all other flags except `-a`, `-n`, and `-p`
- `-e` supports `AND`, `OR`, `NOT` (case-insensitive) and parentheses for grouping
- `-e` standard precedence: NOT binds tightest, then AND, then OR — use parentheses to override
- `-e` to search for the literal word "AND", "OR", or "NOT", enclose it in quotes inside the expression: `"AND"`
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
- `-W` uses word boundary matching (regex `\b`). `bob` matches "bob" but not "bobcat", "bobby", etc. Works with all other flags including `-a`, `-e`, `-x`, `-w`, `-z`
- `-n` always needs its exclude terms immediately after it (e.g., `-n draft` or `-n draft,obsolete`)
- `-n` follows the current search mode — in fuzzy mode, exclude terms are fuzzy-matched; in wildcard mode, exclude terms are wildcard-matched
- `-n` works with all flags and all search modes except `-e` (use NOT inside the expression instead)
- `-o` always needs its format list immediately after it (e.g., `-o csv` or `-o csv,json`)
- `-o` supported formats are `csv` and `json`
- `-o` does not replace the default `.txt` and `.docx` reports — it adds additional output files
- `-o csv` creates `docsearch_results.csv` with columns: filename, folder, line_number, matched_text
- `-o json` creates `docsearch_results.json` with metadata and a matches array
- `-o csv,json` creates both files
- `-m` always needs its count immediately after it (e.g., `-m 5000`)
- `-m 0` disables the match cap entirely — all matches are included in reports
- `-m` defaults to 1,000 when not specified. This prevents very large result sets from causing slow report generation
- `-m` can be set permanently via `--config max_matches=5000` or in the GUI's Advanced Options panel
- `--timestamp` adds a `_YYYYMMDD_HHMMSS` suffix to report filenames so each search produces unique files (e.g., `docsearch_results_20260327_143022.txt`)
- `--timestamp` is on by default in the GUI (via the Timestamp checkbox). Uncheck it to revert to the standard `docsearch_results` filename
- `--timestamp` and `-s` are independent — `-s` looks for `docsearch_results.txt` by name, so it only works when `--timestamp` is not used
- `--output-dir` writes all output files to the specified directory instead of the search folder. The search still runs in the current directory — only the output destination changes
- `--output-dir` creates the directory if it doesn't exist
- `--output-dir` works with all other flags including `--timestamp`, `-s`, `-sa`, `-o`, and search suites
- `--inverse` flips the search — instead of showing files WITH matches, it shows files WITHOUT matches
- `--inverse` works with all search modes (OR, AND, regex, fuzzy, wildcard) and all other flags
- `--inverse` reports and exports list the files that are missing the search terms
- `--inverse` exit code: 0 if files without matches were found, 1 if all files matched
- `--inverse` is especially useful for compliance — "which documents are missing required content?"
- `-R` (or `--range`) always needs its range spec immediately after it (e.g., `-R amount:1000..5000` or `--range amount:1000..5000`)
- `-R` syntax: `field:min..max` — use `field:min..` for open-ended minimum, `field:..max` for open-ended maximum. Both bounds are inclusive
- `-R` content fields: `date`, `amount`, `number`, `percent`, `age`, `time` — these extract values from document text and filter lines
- `-R` metadata fields: `filesize`, `filedate` — these filter entire files by their properties before text scanning
- `-R` is repeatable — multiple `-R` flags combine with AND logic (all must match)
- `-R` can be used alone (range-only search) or combined with text search terms
- `-R filesize` accepts size suffixes: `K` (kilobytes), `M` (megabytes), `G` (gigabytes), `T` (terabytes). Example: `-R filesize:1M..10M`
- `-R` works with all other flags including `-a`, `-e`, `-x`, `-z`, `-w`, `-r`, `-t`, and `-O`
- `-R` range specs can also be embedded directly inside `-e` expressions (e.g., `-e "budget AND amount:1000..5000"`). Metadata fields only work with `-R`, not inside expressions

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
| | **Whole-Word Searches** | |
| 70 | Whole-word single term | `docsearch -W bob` |
| 71 | Whole-word with AND logic | `docsearch -W -a bob amy` |
| 72 | Whole-word with expression | `docsearch -W -e "bob AND amy"` |
| | **Exclude Searches** | |
| 73 | Exclude lines containing a term | `docsearch -n draft budget` |
| 74 | Exclude multiple terms | `docsearch -n draft,obsolete budget` |
| 75 | Exclude with AND logic | `docsearch -n draft -a budget revenue` |
| 76 | Exclude with recursive search | `docsearch -n draft -r budget` |
| 77 | Exclude with file type filter | `docsearch -n draft -t pdf,docx budget` |
| 78 | Exclude with wildcard search | `docsearch -w -n "dra*" "budg*"` |
| | **Additional Output Formats** | |
| 79 | Output results as CSV | `docsearch -o csv budget` |
| 80 | Output results as JSON | `docsearch -o json budget` |
| 81 | Output both CSV and JSON | `docsearch -o csv,json budget` |
| 82 | CSV with recursive search | `docsearch -o csv -r budget` |
| | **Match Cap** | |
| 83 | Set max matches to 5000 | `docsearch -m 5000 budget` |
| 84 | Disable match cap (no limit) | `docsearch -m 0 budget` |
| 85 | Match cap with AND and recursive | `docsearch -m 500 -a -r budget revenue` |
| | **Saved Settings** | |
| 86 | View saved settings | `docsearch --config` |
| 87 | Save a setting | `docsearch --config recursive=true` |
| 88 | Save multiple settings | `docsearch --config recursive=true cores=4` |
| 89 | Remove a saved setting | `docsearch --config recursive=` |
| | **Search Index** | |
| 90 | Build index (includes all subfolders) | `docsearch --index` |
| 91 | Build index with OCR | `docsearch --index -O` |
| 92 | Show index info | `docsearch --index-status` |
| 93 | Delete the index | `docsearch --index-clear` |
| 93a | Incrementally refresh the index | `docsearch --index-refresh` |
| | **Inverse Search** | |
| 94 | Find files missing a term | `docsearch --inverse "indemnification"` |
| 95 | Files missing any of several terms | `docsearch --inverse disclaimer warranty` |
| 96 | Files missing ALL required terms | `docsearch --inverse -a confidential signature date` |
| 97 | Inverse with regex pattern | `docsearch --inverse -x "\d{3}-\d{2}-\d{4}"` |
| 98 | Inverse with file type filter | `docsearch --inverse -t pdf,docx "effective date"` |
| 99 | Inverse recursive search | `docsearch --inverse -r "retention policy"` |
| 100 | Inverse with CSV output | `docsearch --inverse -o csv "indemnification"` |
| 101 | Inverse with JSON output | `docsearch --inverse -o json "compliance"` |
| | **Boolean Expression Search** | |
| 102 | AND expression | `docsearch -e "budget AND revenue"` |
| 103 | OR expression | `docsearch -e "budget OR revenue"` |
| 104 | AND NOT expression | `docsearch -e "budget AND NOT draft"` |
| 105 | Grouped OR within AND | `docsearch -e "(budget OR revenue) AND (cost OR profit)"` |
| 106 | Grouped AND with OR | `docsearch -e "(bob AND amy) OR (fred AND wilma)"` |
| 107 | Complex with NOT | `docsearch -e "(merger OR acquisition) AND NOT draft"` |
| 108 | Multi-word terms in expression | `docsearch -e '"annual report" AND (2023 OR 2024)'` |
| 109 | Expression with wildcard | `docsearch -e -w "budg* AND rev*"` |
| 110 | Expression with regex | `docsearch -e -x "\\d{3}-\\d{4} AND budget"` |
| 111 | Expression with fuzzy | `docsearch -e -z "budgt AND revnue"` |
| 112 | Expression with context | `docsearch -e -B 2 -A 2 "merger AND NOT confidential"` |
| 113 | Expression recursive | `docsearch -e -r "(budget OR revenue) AND (cost OR profit)"` |
| | **Output Directory** | |
| 114 | Write results to a specific folder | `docsearch --output-dir ~/reports budget` |
| 115 | Output dir with recursive search | `docsearch --output-dir /tmp/results -r budget` |
| | **Range Queries** | |
| 116 | Filter by dollar amount range | `docsearch -R amount:1000..5000 budget` |
| 117 | Filter by date range | `docsearch -R date:2024-01-01..2024-12-31 report` |
| 118 | Range-only search (no text terms) | `docsearch -R amount:1000..5000` |
| 119 | Filter by file size | `docsearch -R filesize:1M..10M report` |
| 120 | Multiple ranges (AND) | `docsearch -R amount:1000..5000 -R date:2024-01-01..2024-12-31 invoice` |
| 121 | Open-ended range (minimum only) | `docsearch -R amount:10000.. contract` |
| 122 | Percent range | `docsearch -R percent:10..50 growth` |
| 123 | Age range | `docsearch -R age:18..65 patient` |
| 124 | Time range | `docsearch -R time:09:00..17:00 meeting` |
| 125 | Range with recursive search | `docsearch -R amount:1000..5000 -r budget` |
| 126 | Open-ended range (maximum only) | `docsearch -R amount:..5000 invoice` |
| 127 | Filter by file modification date | `docsearch -R filedate:2024-01-01..2024-06-30 report` |
| 128 | Number range (any standalone number) | `docsearch -R number:100..999 report` |
| 129 | Range with file type filter | `docsearch -R amount:1000.. -t .pdf,.docx invoice` |
| 130 | Range with context lines | `docsearch -R amount:5000..10000 -B 2 -A 2 payment` |
| 131 | Range with AND mode text search | `docsearch -R date:2024-01-01..2024-12-31 -a budget revenue` |
| 132 | Range with exclude terms | `docsearch -R amount:1000..5000 -n draft invoice` |
| 133 | Large file search | `docsearch -R filesize:10M.. -r report` |
| 134 | Small recent files | `docsearch -R filesize:..100K -R filedate:2025-01-01.. memo` |
| | **Filename Ranges** | |
| 134a | Filter by date in filename | `docsearch -R fn:date:2024-01-01..2024-12-31 budget` |
| 134b | Filename + content range | `docsearch -R fn:date:2024-01-01..2024-12-31 -R amount:1000..5000 invoice` |
| 134c | Filename range in expression | `docsearch -e "budget AND fn:date:2024-01-01..2024-12-31"` |
| | **Range Queries in Expressions** | |
| 135 | Text AND amount range | `docsearch -e "budget AND amount:1000..5000"` |
| 136 | Text AND date range | `docsearch -e "report AND date:2024-01-01..2024-12-31"` |
| 137 | OR with range on one branch | `docsearch -e "(budget AND amount:1000..5000) OR revenue"` |
| 138 | NOT with range (exclude high amounts) | `docsearch -e "invoice AND NOT amount:10000.."` |
| 139 | Multiple ranges in expression | `docsearch -e "invoice AND amount:500..5000 AND date:2024-01-01..2024-12-31"` |
| 140 | Range-only expression | `docsearch -e "amount:1000..5000"` |
| 141 | OR between two ranges | `docsearch -e "amount:1000..5000 OR percent:10..50"` |
| 142 | Text with percent range | `docsearch -e "growth AND percent:20..100"` |
| 143 | Text with age range | `docsearch -e "patient AND age:18..65"` |
| 144 | Text with time range | `docsearch -e "meeting AND time:09:00..17:00"` |
| 145 | Complex: text + range + NOT | `docsearch -e "(contract AND amount:5000..50000) AND NOT draft"` |
| 146 | Complex: two branches with ranges | `docsearch -e "(budget AND amount:1000..5000) OR (invoice AND date:2024-01-01..2024-12-31)"` |
| 147 | Expression + -R metadata filter | `docsearch -e "budget AND amount:1000..5000" -R filesize:..1M` |
| 148 | Expression with wildcard + range | `docsearch -e -w "budg* AND amount:1000..5000"` |
| 149 | Expression with regex + range | `docsearch -e -x "INV-\\d+ AND amount:1000..5000"` |
| | **Installation Check** | |
| 150 | Check installation health | `docsearch --check` |
| | **Version and Help** | |
| 151 | Show version | `docsearch -v` |
| 152 | Show help | `docsearch -h` |
| 153 | Show help (no arguments) | `docsearch` |

## Output

Search results are always written to two files in the current directory:

- **`docsearch_results.txt`** — Plain text with `**` markers around matched terms
- **`docsearch_results.docx`** — Word document with search terms highlighted in green in the header and matched terms highlighted in yellow throughout

With the `-o` flag, additional output files are created:

- **`docsearch_results.csv`** (`-o csv`) — Spreadsheet-ready format with columns: filename, folder, line_number, matched_text. Open in Excel, Google Sheets, or any spreadsheet application to sort, filter, and analyze results.
- **`docsearch_results.json`** (`-o json`) — Machine-readable format with search metadata, per-file match counts, and a matches array. Useful for integrating docsearch into automated workflows, dashboards, or other tools.

### Command Translation

Every report includes a **Translation** line that explains the search command in plain English. Regex patterns are automatically recognized and described by their meaning — not their individual characters:

| Regex Pattern | Translation |
|---|---|
| `\d{1,2}/\d{1,2}/\d{2,4}` | a date (e.g. MM/DD/YYYY or YYYY-MM-DD) |
| `\d{3}-\d{3}-\d{4}` | a US phone number (e.g. 555-123-4567) |
| `\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}` | a phone number with area code (e.g. (555) 123-4567) |
| `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,}` | an email address (e.g. user@example.com) |
| `\$\d+\.?\d*` | a dollar amount (e.g. $45.99) |
| `\d{3}-\d{2}-\d{4}` | a Social Security Number (SSN) (e.g. 123-45-6789) |
| `\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}` | an IP address (e.g. 192.168.1.1) |
| `https?://\S+` | a URL (e.g. https://example.com) |
| `\d{5}(-\d{4})?` | a US ZIP code (e.g. 12345 or 12345-6789) |
| `\d+%` | a percentage (e.g. 92%) |
| `Q[1-4]\s?\d{4}` | a fiscal quarter (e.g. Q1 2026) |

Example report header:
```
Command ==> docsearch -a -x "\d{1,2}/\d{1,2}/\d{2,4}" budget
Translation ==> Search current directory, for ALL of: a date (e.g. MM/DD/YYYY or YYYY-MM-DD) AND "budget" (using regex)
```

Regex patterns combined with `|` (alternation) are also recognized per-branch. Unrecognized patterns fall back to a character-level description.

Text file format:
```

2026-03-07 14:30:45
Search Term(s) ==> budget, revenue

Document: report.docx (2 matches), Line: 12, Match:
(/Users/bob/GoogleDocs)
"The **budget** for this quarter exceeded expectations"

Document: summary.docx (1 match), Line: 3, Match:
(/Users/bob/GoogleDocs)
"Revised **budget** proposal attached"
```

If any files could not be read during a search, errors are logged to **`docsearch_errors.log`** in the current directory. Each entry includes a timestamp, the filename, and the reason it failed:
```
2026-03-22 14:05:12  Could not read report.pdf (encrypted PDF)
2026-03-22 14:05:12  Could not read data.xlsx (file is corrupted)
```

The error log is only created when a file error occurs — if all files are read successfully, no error log is created. The error log appends across searches so you can track issues over time. You can safely delete `docsearch_errors.log` at any time — a new one will be created automatically the next time a file error occurs.

If docsearch itself crashes unexpectedly, a crash report is also written to `docsearch_errors.log` with a diagnosis to help identify the cause:
```
============================================================
2026-03-25 14:30:12  CRASH REPORT
docsearch 0.1.0
Python 3.13.2 (main, Feb 4 2025, 14:51:09)
OS: Darwin 24.6.0
Command: docsearch budget

Diagnosis: The Python module 'fitz' could not be loaded. This is usually
caused by a missing or incompatible dependency. Try: pip install --upgrade docsearch
============================================================
Traceback (most recent call last):
  ...
```

If you experience a crash, check `docsearch_errors.log` in the folder where you ran the search. The diagnosis line suggests a likely cause and fix. Common causes include a missing or incompatible Python package (fix: `pip install --upgrade docsearch`), a corrupted file that couldn't be handled, or a Python version incompatibility. If the problem persists, the crash report contains everything needed to investigate — you can include it when reporting an issue.

The terminal also displays a summary with per-file match counts:
```
Files searched: 12 (4.50 MB) — Found 3 match(es).
Elapsed time: 0.45 seconds, Cores used: 4 of 8
  report.docx: 2
  summary.docx: 1
Results ==> /Users/bob/GoogleDocs
```

## Search Index (Optional)

By default, docsearch opens and parses every file on each search. For large folders with many documents, you can build an optional search index to make repeated searches much faster. The index stores extracted text in a SQLite FTS5 database so subsequent searches skip file I/O and parsing entirely.

**Building the index:**

```bash
cd /path/to/your/documents
docsearch --index              # index files in current folder and all subfolders
docsearch --index -O           # same, with OCR for scanned PDFs and images
```

**Using the index:**

Once built, the index is used automatically — just search as usual:

```bash
docsearch budget               # uses the index automatically (faster)
docsearch -z budgt             # fuzzy search — also uses the index
docsearch -x "\d{3}-\d{4}"    # regex search — also uses the index
```

The index stays up to date automatically. Each search checks for new, changed, or deleted files and refreshes the index incrementally before searching. You do not need to rebuild the index manually unless you want a full rebuild.

**Managing the index:**

```bash
docsearch --index-status       # show file count, size, creation date
docsearch --index-refresh      # incrementally update (add new, re-index changed, remove deleted)
docsearch --index-clear        # delete the index
```

**Scheduled refresh:** Use `--index-refresh` with cron or launchd to keep the index up to date automatically:

```bash
# cron: refresh every 15 minutes
*/15 * * * * cd /path/to/documents && docsearch --index-refresh

# macOS launchd: create a plist with ProgramArguments pointing to docsearch --index-refresh
```

**How it works:** The index extracts and stores text from every supported file in a `.docsearch.db` file in the search directory. For simple keyword searches (OR/AND), the index uses FTS5 full-text search for speed. For advanced modes (regex, fuzzy, wildcard, proximity, context lines), the index reads stored text from the database instead of re-parsing files — this guarantees identical results to non-indexed search while still skipping file I/O.

**In the GUI:** Click **▶ Index Options** (below Search Suites on the main page) to expand index controls. The panel has an **Auto-Refresh Index** dropdown (Off / 5 min / 15 min / 30 min / 1 hour) on the left, then **Build Index(es)**, **Delete Index(es)**, **Index Status**, and **About Index** buttons. The **Search Using Index(es)** checkbox is inside Advanced Options to toggle between indexed and direct search. Building an index always includes all subfolders. The auto-refresh keeps the index up to date automatically while the app is open — it runs incremental refreshes in the background without interrupting searches. The index last-updated timestamp is shown below the Build Index(es) button. The selected interval is saved to `~/.docsearchrc` and restored on next launch.

**Concurrency safety:** The index is safe to use while auto-refresh is running, while multiple searches are happening, or while external tools (cron jobs, other terminals) access the same folder. Protections include:

- **WAL mode with 10-second busy timeout** — SQLite's Write-Ahead Logging allows concurrent reads during writes. If two writers collide (e.g., auto-refresh and a CLI search both trying to refresh), the second waits up to 10 seconds for the lock instead of failing.
- **Graceful lock handling** — If a search cannot refresh the index (because another process holds the write lock), it searches with the existing index data. Results may be seconds stale but never corrupted or incomplete.
- **Locked-vs-corrupt distinction** — A locked database is never mistaken for a corrupt one. Only actual corruption (malformed schema, unreadable pages) triggers index deletion and rebuild.
- **GUI scheduling guards** — Auto-refresh is paused while a search, index build, or suite run is active and resumed when it finishes. Starting a search while a refresh is in progress is blocked until the refresh completes.
- **Atomic transactions** — All index writes (adds, updates, deletes) happen within a single SQLite transaction. If the process crashes mid-refresh, uncommitted changes are rolled back automatically — the index reverts to its previous consistent state.
- **Connection cleanup** — All database connections are wrapped in `try/finally` blocks so connections are always closed, even if an error occurs.

## Inverse Search

Normal docsearch shows files that **contain** your search terms. Inverse search (`--inverse`) flips this — it shows files that **do not contain** the search terms. This answers the question: "Which documents are missing required content?"

**Use cases:**

| Scenario | Command |
|----------|---------|
| Contracts missing an indemnification clause | `docsearch --inverse -t pdf,docx "indemnification"` |
| Policies missing a confidentiality notice | `docsearch --inverse -r "CONFIDENTIAL"` |
| Documents without a required signature date | `docsearch --inverse -x "\d{1,2}/\d{1,2}/\d{2,4}"` |
| Files missing SSNs (data hygiene check) | `docsearch --inverse -x "\d{3}-\d{2}-\d{4}"` |
| HR documents without employee IDs | `docsearch --inverse -t pdf,docx -x "[Ee]mp\.?\s*#?\s*\d{4,}"` |

**How it works:**

1. docsearch searches all files normally and identifies which files have matches
2. It then computes the **difference** — files that were searched but had no matches
3. The console output, TXT/DOCX reports, and optional CSV/JSON exports all list the files without matches instead of match details

**Output:**

- Console: `Found 8 file(s) WITHOUT matches (out of 20 searched).` followed by a list of filenames
- TXT/DOCX report: includes a "Files WITHOUT matches" section listing each file and its directory
- CSV (`-o csv`): two columns — `filename` and `folder`
- JSON (`-o json`): includes `files_without_matches` count and `inverse_files` array

**In the GUI:** Check the **Inverse** checkbox in the Search Bar (next to the Wizard button) before clicking **Run Search**. The results summary will show how many files are missing the search terms.

**Exit codes:** In inverse mode, exit code 0 means files without matches were found (success — missing content detected). Exit code 1 means all files contained the search terms (nothing to report).

## Boolean Expression Search

The `-e` flag enables boolean expression search, allowing you to combine AND, OR, NOT, and parentheses for complex queries that can't be expressed with the `-a` and `-n` flags alone.

### Why use `-e` instead of `-a` and `-n`?

The `-a` flag applies one global AND/OR mode to all terms, and `-n` applies one global exclusion list. This means you can't express queries like:

- "Find lines mentioning **either** (budget AND revenue) **or** (cost AND profit)" — mixing AND and OR in the same query
- "Find lines with budget but not draft, **or** lines with revenue but not obsolete" — different exclusions per group

With `-e`, you can express any combination:

```bash
# Either topic A or topic B, where each topic requires multiple terms
docsearch -e "(budget AND revenue) OR (cost AND profit)"

# Synonyms within an AND query
docsearch -e "(budget OR revenue) AND (cost OR profit)"

# Different NOT conditions per group
docsearch -e "(budget AND NOT draft) OR (revenue AND NOT obsolete)"

# Complex nested logic
docsearch -e "((merger OR acquisition) AND NOT confidential) OR (ipo AND SEC)"
```

### Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `AND` | Both sides must match | `budget AND revenue` |
| `OR` | Either side must match | `budget OR revenue` |
| `NOT` | Must not match | `budget AND NOT draft` |
| `()` | Group expressions | `(a OR b) AND (c OR d)` |

Operators are case-insensitive (`and`, `And`, `AND` all work).

**Precedence:** NOT binds tightest, then AND, then OR. Use parentheses to override: `a OR b AND c` means `a OR (b AND c)`, while `(a OR b) AND c` requires both.

### Combining with other modes

Expression search works with regex (`-x`), fuzzy (`-z`), and wildcard (`-w`) — these control **how** each term is matched, while the expression controls the **logic**:

```bash
# Wildcard terms in an expression
docsearch -e -w "budg* AND rev*"

# Regex terms in an expression
docsearch -e -x "\\d{3}-\\d{4} AND budget"

# Fuzzy terms in an expression (typo-tolerant)
docsearch -e -z "budgt AND revnue"

# With context lines
docsearch -e -B 2 -A 2 "(merger OR acquisition) AND NOT draft"
```

### Multi-word terms

Use quotes inside the expression for multi-word terms:

```bash
docsearch -e '"annual report" AND (2023 OR 2024)'
```

### Range filters in expressions

Range specs (`field:min..max`) can be embedded directly inside boolean expressions, combining value-based filtering with text matching in a single query:

```bash
# Lines mentioning "budget" that contain amounts between $1,000 and $5,000
docsearch -e "budget AND amount:1000..5000"

# OR logic: budget with amounts in range, or any line with "revenue"
docsearch -e "(budget AND amount:1000..5000) OR revenue"

# NOT logic: "invoice" lines without amounts over $10,000
docsearch -e "invoice AND NOT amount:10000.."

# Multiple ranges: invoice with amount and date constraints
docsearch -e "invoice AND amount:500..5000 AND date:2024-01-01..2024-12-31"

# Range-only expression (no text terms)
docsearch -e "amount:1000..5000"

# Combine -e with -R for metadata filtering on top of expression logic
docsearch -e "budget OR revenue" -R filesize:..1M
```

All content fields (date, amount, number, percent, age, time) work inside expressions. Metadata fields (filesize, filedate) only work with the `-R` flag, not inside expressions. See [Range Queries](#range-queries) for comprehensive examples of all range types in both `-R` and `-e` modes.

### Limitations

- `-e` cannot be combined with `-a` (AND mode), `-n` (exclude), or `-p` (proximity) — these features are built into the expression syntax
- To search for the literal word "AND", "OR", or "NOT", enclose it in double quotes inside the expression: `docsearch -e '"AND" OR budget'`
- Metadata range fields (`filesize`, `filedate`) cannot be used inside expressions — use `-R` for file-level filtering

## Range Queries

Range queries filter results by numeric values, dates, times, ages, percentages, and file metadata. Use the `-R` (or `--range`) flag with the syntax `field:min..max`. Both bounds are **inclusive** — `amount:1000..5000` matches $1,000, $5,000, and everything in between.

**Target prefixes** — by default, content fields extract values from document text. Use `fn:` to extract values from the **filename** instead:

| Prefix | Target | Example | Meaning |
|--------|--------|---------|---------|
| *(none)* | Content (line text) | `-R date:2024-01-01..2024-12-31` | Match dates found in document text |
| `fn:` | Filename | `-R fn:date:2024-01-01..2024-12-31` | Match dates found in the filename |
| `fc:` | Content (explicit) | `-R fc:amount:1000..5000` | Same as no prefix — explicitly targets content |

The `fn:` prefix works with all 6 content fields (date, amount, number, percent, age, time). Metadata fields (filesize, filedate) cannot use `fn:` or `fc:` prefixes. Prefixes are case-insensitive (`fn:`, `FN:`, `Fn:` all work).

**Content fields** extract values from document text and filter matching lines:

| Field | Matches | Recognized formats in document text | Example |
|-------|---------|-------------------------------------|---------|
| `date` | Dates in text | ISO: `2024-01-15` · US: `01/15/2024`, `01-15-2024` · Natural: `January 15, 2024`, `Jan 15 2024`, `Jan 15, 2024` (all 12 month names and standard abbreviations) | `-R date:2024-01-01..2024-12-31` |
| `amount` | Currency amounts | `$1,234.56`, `$ 1234`, `USD 1234`, `EUR 500`, `GBP 100`, `1,234 dollars`, `500 USD`, `200 EUR`, `150 GBP` | `-R amount:1000..5000` |
| `number` | Any standalone number | `42`, `1,234`, `3.14`, `1,000,000` (must be surrounded by whitespace — numbers inside words are ignored) | `-R number:100..999` |
| `percent` | Percentage values | `45%`, `45.5%`, `1,000%`, `45 percent` (case-insensitive) | `-R percent:10..50` |
| `age` | Age mentions | `age 25`, `aged 25`, `25 years old`, `25 year old`, `25-year-old`, `25-years-old` (case-insensitive) | `-R age:18..65` |
| `time` | Time values | 24-hour: `14:30`, `14:30:00` · 12-hour: `2:30 PM`, `9:00 AM`, `2:30:00 PM` (AM/PM converted to 24-hour: 12 PM = 12:00, 1 PM = 13:00, 12 AM = 0:00) | `-R time:09:00..17:00` |

**Metadata fields** filter entire files by their properties (before text scanning):

| Field | Matches | Accepted bound formats | Example |
|-------|---------|----------------------|---------|
| `filesize` | File size in bytes | Plain bytes (`1048576`), suffixes: `K` (1,024), `M` (1,048,576), `G` (1,073,741,824), `T` (case-insensitive) | `-R filesize:1M..10M` |
| `filedate` | File modification date | ISO: `2024-01-15` · US: `01/15/2024`, `01-15-2024` | `-R filedate:2024-01-01..2024-06-30` |

**Bound string formats** — the min and max values in your range spec accept flexible formatting:

| Field | Accepted bound formats | Example specs |
|-------|----------------------|---------------|
| `date`, `filedate` | `YYYY-MM-DD`, `MM/DD/YYYY`, `MM-DD-YYYY` | `date:2024-01-01..2024-12-31`, `date:01/01/2024..12/31/2024` |
| `amount`, `number`, `percent`, `age` | Plain numbers, with `$`, `,`, or `%` (stripped automatically) | `amount:$1,000..$5,000`, `percent:10%..50%`, `amount:1000..5000` |
| `time` | `HH:MM`, `HH:MM:SS`, `HH:MM AM/PM`, `HH:MM:SS AM/PM` | `time:09:00..17:00`, `time:9:00 AM..5:00 PM`, `time:09:00:00..17:00:00` |
| `filesize` | Plain bytes or with `K`/`M`/`G`/`T` suffix | `filesize:1M..10M`, `filesize:1048576..10485760` |

### Using the `-R` flag

**Basic range filtering** — combine `-R` with text search terms:

```bash
# Find "budget" in lines that mention amounts between $1,000 and $5,000
docsearch -R amount:1000..5000 budget

# Find "report" in lines dated within 2024
docsearch -R date:2024-01-01..2024-12-31 report

# Find "meeting" in lines with times between 9 AM and 5 PM
docsearch -R time:09:00..17:00 meeting

# Find "growth" in lines with percentages between 10% and 50%
docsearch -R percent:10..50 growth

# Find "patient" in lines mentioning ages 18 to 65
docsearch -R age:18..65 patient

# Find lines with any standalone number between 100 and 999
docsearch -R number:100..999 report
```

**Open-ended ranges** — omit min or max for unbounded filtering:

```bash
# Amounts of $10,000 or more
docsearch -R amount:10000.. contract

# Amounts up to $500
docsearch -R amount:..500 expense

# Files larger than 10 MB
docsearch -R filesize:10M.. report

# Files smaller than 100 KB
docsearch -R filesize:..100K memo

# Dates from 2024 onward
docsearch -R date:2024-01-01.. report

# Dates before July 2024
docsearch -R date:..2024-06-30 invoice

# After-hours times only
docsearch -R time:17:00.. log

# Percentages above 90%
docsearch -R percent:90.. performance
```

**Multiple ranges** combine with AND logic — all must match:

```bash
# Invoices with amounts $1,000-$5,000 AND dated within 2024
docsearch -R amount:1000..5000 -R date:2024-01-01..2024-12-31 invoice

# Payments over $500 in lines mentioning ages 18-65
docsearch -R amount:500.. -R age:18..65 payment

# Small, recent files only
docsearch -R filesize:..100K -R filedate:2025-01-01.. memo

# Large files modified in 2024
docsearch -R filesize:10M.. -R filedate:2024-01-01..2024-12-31 report
```

**Filename ranges** — use `fn:` to filter files by values extracted from their filenames:

```bash
# Only search files with 2024 dates in the filename (e.g., report-2024-06-15.pdf)
docsearch -R fn:date:2024-01-01..2024-12-31 budget

# Combine filename range with content range
docsearch -R fn:date:2024-01-01..2024-12-31 -R amount:1000..5000 invoice

# Filename range in an expression
docsearch -e "budget AND fn:date:2024-01-01..2024-12-31"
```

**Range-only search** — use `-R` without text terms to find all lines containing values in range:

```bash
# Find all lines with dollar amounts between $1,000 and $5,000
docsearch -R amount:1000..5000

# Find all lines with dates in Q1 2024
docsearch -R date:2024-01-01..2024-03-31

# Find all lines with percentages over 50%
docsearch -R percent:50..
```

**Combining with other flags:**

```bash
# Range with recursive search
docsearch -R amount:1000..5000 -r budget

# Range with file type filter
docsearch -R amount:1000.. -t .pdf,.docx invoice

# Range with context lines
docsearch -R amount:5000..10000 -B 2 -A 2 payment

# Range with AND mode text search
docsearch -R date:2024-01-01..2024-12-31 -a budget revenue

# Range with exclude terms
docsearch -R amount:1000..5000 -n draft invoice

# Range with whole-word matching
docsearch -R amount:1000..5000 -W budget

# Range with max matches limit
docsearch -R amount:1000..5000 -m 50 invoice
```

### Range specs in boolean expressions

Range specs can also be embedded directly inside `-e` expressions using the same `field:min..max` syntax. This lets you combine value-based filtering with boolean logic in a single query:

```bash
# Lines mentioning "budget" that contain amounts between $1,000 and $5,000
docsearch -e "budget AND amount:1000..5000"

# Lines mentioning "report" with dates in 2024
docsearch -e "report AND date:2024-01-01..2024-12-31"

# Lines with "growth" and a percentage above 20%
docsearch -e "growth AND percent:20..100"

# Lines with "patient" and an age between 18 and 65
docsearch -e "patient AND age:18..65"

# Lines with "meeting" and a time between 9 AM and 5 PM
docsearch -e "meeting AND time:09:00..17:00"
```

**OR logic** — match one condition or the other:

```bash
# Lines with budget amounts in range, OR any line with "revenue"
docsearch -e "(budget AND amount:1000..5000) OR revenue"

# Match either high amounts OR high percentages
docsearch -e "amount:10000.. OR percent:50.."

# Different criteria per branch
docsearch -e "(budget AND amount:1000..5000) OR (invoice AND date:2024-01-01..2024-12-31)"
```

**NOT logic** — exclude lines matching a range:

```bash
# "invoice" lines that do NOT have amounts over $10,000
docsearch -e "invoice AND NOT amount:10000.."

# "contract" lines excluding dates before 2024
docsearch -e "contract AND NOT date:..2023-12-31"

# Complex: require text + range, exclude another range
docsearch -e "(contract AND amount:5000..50000) AND NOT date:..2023-12-31"
```

**Multiple ranges in one expression:**

```bash
# Invoice lines with amounts $500-$5,000 AND dated in 2024
docsearch -e "invoice AND amount:500..5000 AND date:2024-01-01..2024-12-31"

# Payment lines with both amount and time constraints
docsearch -e "payment AND amount:100..1000 AND time:09:00..17:00"
```

**Range-only expressions** (no text terms):

```bash
# All lines with amounts in range
docsearch -e "amount:1000..5000"

# Lines with amounts in range OR percentages in range
docsearch -e "amount:1000..5000 OR percent:10..50"
```

**Combining with other modes:**

```bash
# Wildcard terms with a range
docsearch -e -w "budg* AND amount:1000..5000"

# Regex terms with a range
docsearch -e -x "INV-\\d+ AND amount:1000..5000"

# Fuzzy terms with a range
docsearch -e -z "budgt AND amount:1000..5000"

# Expression + -R flag for metadata filtering
docsearch -e "budget AND amount:1000..5000" -R filesize:..1M

# Expression + -R flag for file date filtering
docsearch -e "budget OR revenue" -R filedate:2024-01-01..2024-12-31
```

**Real-world scenarios:**

```bash
# Compliance: find contracts with payments over $50,000 signed in 2024
docsearch -e "contract AND amount:50000.. AND date:2024-01-01..2024-12-31"

# HR: find employee records for people aged 55-65
docsearch -e "(employee OR staff) AND age:55..65"

# Finance: find Q4 invoices between $1,000 and $10,000
docsearch -e "invoice AND amount:1000..10000 AND date:2024-10-01..2024-12-31"

# Audit: find high-growth reports (over 25%) excluding drafts
docsearch -e "growth AND percent:25.. AND NOT draft"

# Legal: find settlements over $100,000 or judgments over $500,000
docsearch -e "(settlement AND amount:100000..) OR (judgment AND amount:500000..)"

# Healthcare: after-hours patient records for ages 18-30
docsearch -e "patient AND age:18..30 AND time:17:00.."

# Small recent PDFs with budget amounts over $5,000
docsearch -e "budget AND amount:5000.." -R filesize:..1M -R filedate:2025-01-01.. -t .pdf

# Find budget mentions only in files from 2024 (by filename date)
docsearch -R fn:date:2024-01-01..2024-12-31 budget

# Invoices from 2024 (filename) with amounts $1,000-$10,000 (content)
docsearch -R fn:date:2024-01-01..2024-12-31 -R amount:1000..10000 invoice

# Expression: budget lines in 2024-dated files
docsearch -e "budget AND fn:date:2024-01-01..2024-12-31"
```

### Notes on range queries

- **Inclusive bounds** — both min and max are inclusive. `amount:1000..5000` matches $1,000, $5,000, and everything in between
- **Content fields** (date, amount, number, percent, age, time) extract values from document text and filter at the line level
- **Filename ranges** (`fn:` prefix) extract values from the filename string and filter entire files — files whose names don't contain matching values are skipped entirely. All 6 content fields work with `fn:`
- **Metadata fields** (filesize, filedate) filter entire files by their properties before text scanning — files that don't match metadata ranges are skipped entirely
- **Multiple values in one line** — if a line contains multiple values of the same type (e.g., two dates or three dollar amounts), the line matches if **any one** of those values falls within the range. All ranges must still be satisfied (AND logic across different ranges)
- Metadata fields (`filesize`, `filedate`) can only be used with the `-R` flag, not inside `-e` expressions. Use `-R` alongside `-e` for metadata filtering
- When using `-R` alongside `-e`, the `-R` filters apply as an additional AND layer on top of the expression result
- Multiple `-R` flags combine with AND logic — all ranges must be satisfied
- **Bound string flexibility** — amounts accept `$` and `,` (e.g., `amount:$1,000..$5,000`), percents accept `%` (e.g., `percent:10%..50%`), dates accept ISO (`YYYY-MM-DD`) and US (`MM/DD/YYYY`, `MM-DD-YYYY`) formats, times accept `HH:MM`, `HH:MM:SS`, and `HH:MM AM/PM` formats
- **Long form** — `--range` is the long form of `-R` (e.g., `--range amount:1000..5000`)
- **Reports** — when range filters are active, they appear in the report header as modifiers (e.g., "range filter amount: 1000 .. 5000"). For range-only searches (no text terms), the report describes the search as "with range filters only"
- **Index search** — ranges work with the search index. Indexed results are post-filtered by content and metadata ranges
- **Search suites** — range filters are fully preserved in saved searches and restored when suites run. Enter ranges in the GUI's Range field before clicking Save Settings
- **Settings persistence** — the Range field value is saved to `~/.docsearchrc` when you click Save Settings in the GUI, and restored when the GUI opens or when you click Restore Settings

In the GUI, enter range filters in the **Range** field in Advanced Options, comma-separated for multiple ranges (e.g., `amount:1000..5000, date:2024-01-01..2024-12-31`).

## Combining Modes

You can mix multiple modes together for more powerful searches.

**Regex + AND + Recursive** — Find files containing both an SSN and a dollar amount anywhere in nested subfolders:

```bash
docsearch -x -a -r "\d{3}-\d{2}-\d{4}" "\$[\d,]+\.\d{2}"
```

In the GUI:

```
      Terms:  \d{3}-\d{2}-\d{4}  \$[\d,]+\.\d{2}
Checkboxes:  Regex, AND mode, Recursive
```

**Wildcard + File Types** — Find any mention of "report" variations in PDFs only:

```bash
docsearch -w -t pdf "report*"
```

In the GUI:

```
      Terms:  report*
Checkboxes:  Wildcard       File Types: .pdf
```

**Expression + Range + Context** — Find lines mentioning budget or revenue (but not draft) with amounts over 10,000, showing surrounding lines:

```bash
docsearch -e "(budget OR revenue) AND NOT draft" -R amount:10000..999999 -B 2 -A 2
```

In the GUI:

```
Expression:  (budget OR revenue) AND NOT draft
Range:       amount:10000..999999
Context:     Before=2, After=2
```

**Whole Word + AND + Proximity** — Find "breach" and "contract" as whole words within 5 words of each other (avoids matching "breached" or "contractor"):

```bash
docsearch -W -p 5 "breach" "contract"
```

In the GUI:

```
      Terms:  breach contract
Checkboxes:  Whole Word, AND mode     Proximity: 5
```

**Fuzzy + Recursive + File Types** — Find misspelled names across all Word docs in subfolders:

```bash
docsearch -z -r -t docx "accommodation" "occurrence"
```

In the GUI:

```
      Terms:  accommodation  occurrence
Checkboxes:  Fuzzy, Recursive   File Types: .docx
```

**Inverse + Regex** — Find files that do NOT contain a required signature line:

```bash
docsearch --inverse -x "Authorized\s+Signature"
```

In the GUI:

```
      Terms:  Authorized\s+Signature
Checkboxes:  Regex, Inverse
```

## Breaking Down Complex Searches

When a single search becomes too complex, break it into several focused searches and combine them in a suite.

**Why this helps:**

- Each search is simpler to configure and understand
- You see which specific check passed or failed
- Different criteria per search (>= 1, == 0, <= N)
- Easy to update one check without affecting others
- Reusable across multiple suites

**Example: Contract compliance audit** — Instead of one giant search, create these saved searches:

```
1. "has_signature"     — Regex: Authorized\s+Signature  (>= 1)
2. "has_date"          — Regex: \d{2}/\d{2}/\d{4}      (>= 1)
3. "no_draft_stamp"    — Terms: DRAFT                   (== 0)
4. "amount_in_range"   — Range: amount:1000..50000      (>= 1)
5. "no_pii"            — Regex: \d{3}-\d{2}-\d{4}      (== 0)
```

Group them into a "contract_review" suite. Run with one click and get a report showing exactly which checks passed or failed.

**Example: Cascade pipeline** — Use cascade mode to progressively narrow results:

```
Stage 1: Find all PDFs mentioning "contract"
Stage 2: Of those, find ones with "termination"
Stage 3: Of those, find ones with dollar amounts
```

Each stage searches only the files that matched the previous stage, producing a focused final result set.

## Using docsearch for Compliance and Auditing

### Why audits exist

An audit is a systematic review of documents, records, or processes to verify that they meet a set of requirements — legal, regulatory, contractual, or internal. Organizations perform audits because the consequences of non-compliance can be severe: fines, lawsuits, lost licenses, data breaches, or failed certifications. Audits answer a simple question: *are we doing what we said we would do, and can we prove it?*

Most audits are not triggered by suspicion of wrongdoing. They are routine, scheduled activities — the organizational equivalent of a regular checkup. The goal is to catch problems early, before they become expensive.

### Who performs audits

- **Internal auditors** — employees (or a dedicated department) who review their own organization's processes. They report to management or an audit committee and focus on risk, controls, and operational efficiency. Many organizations have a Chief Audit Executive or an internal audit team.
- **External auditors** — independent firms (e.g., accounting firms, consulting firms, or government inspectors) hired to provide an objective assessment. Financial statement audits, SOX compliance audits, and regulatory inspections are typically performed by external auditors.
- **Compliance officers** — staff responsible for ensuring the organization follows applicable laws and regulations. They often design the compliance program and monitor adherence on an ongoing basis.
- **IT and security teams** — review systems, access controls, and data handling practices. They perform audits related to data privacy (GDPR, HIPAA), cybersecurity frameworks (SOC 2, ISO 27001), and internal security policies.
- **Contract managers and legal teams** — review agreements to verify that required clauses are present, terms are current, and obligations are being met.
- **Quality assurance teams** — verify that processes and outputs meet defined standards (ISO 9001, FDA regulations, industry-specific requirements).

In smaller organizations, audits are often performed by a single person wearing multiple hats — a controller who also handles compliance, or an office manager responsible for records management.

### Industry examples

| Industry | What gets audited | Why | Typical requirements |
|----------|------------------|-----|---------------------|
| **Financial services** | Loan documents, account records, transaction logs | Banking regulations (SOX, Dodd-Frank, BSA/AML) require documented controls and regular review | Every loan file must contain signed disclosures; no account should have unauthorized transactions above reporting thresholds |
| **Healthcare** | Patient records, billing documents, policy manuals | HIPAA requires protection of patient data; CMS requires accurate billing documentation | No patient SSN or medical record number in unsecured documents; every billing record must reference a valid diagnosis code |
| **Legal** | Contracts, court filings, discovery documents | Bar associations, courts, and clients require accurate document handling and retention | Every contract must contain an indemnification clause and an effective date; no privileged documents in production sets |
| **Government** | Policy documents, procurement records, correspondence | Freedom of Information laws, records retention schedules, and inspector general reviews | Every procurement file must contain a signed authorization; no classified markings in unclassified folders |
| **Manufacturing** | Quality records, inspection reports, certifications | ISO 9001, FDA, and industry standards require documented quality processes | Every batch record must reference an approved specification; no expired certifications in the active file |
| **Education** | Student records, accreditation documents, grant files | FERPA protects student data; accreditation bodies require documented compliance | No student SSN in publicly accessible files; every grant file must contain a signed agreement |
| **Real estate** | Lease agreements, inspection reports, closing documents | State licensing boards and lenders require complete documentation | Every closing file must contain a signed disclosure; all lease amounts must fall within approved ranges |
| **Insurance** | Policy documents, claims files, underwriting records | State insurance regulators require documented underwriting and claims processes | Every policy must contain required state-mandated language; no lapsed policies in the active portfolio |
| **Human resources** | Employee files, benefit documents, I-9 forms | Employment law (EEOC, FLSA, ACA) and immigration law (USCIS) require documented compliance | Every employee file must contain a signed offer letter and I-9; no SSNs in shared drive folders |

In each of these industries, the core task is the same: search a set of documents, verify that specific content is present (or absent), and produce a report proving the results. This is exactly what docsearch does.

### How docsearch fits

docsearch can serve as a lightweight compliance and auditing tool. Instead of manually opening documents one at a time to verify that required language is present, prohibited content is absent, or values fall within acceptable ranges, you can automate those checks and produce evidence-grade reports — all offline, without uploading anything to the cloud.

**What compliance and audit teams typically need to verify:**

- Every contract contains a required clause (e.g., indemnification, signature, effective date)
- No document contains prohibited content (e.g., "DRAFT" watermarks, outdated policy references)
- Sensitive data like Social Security numbers or account numbers does not appear where it shouldn't
- Dollar amounts, dates, or percentages fall within acceptable ranges
- A consistent set of checks runs on a regular schedule with documented results

docsearch handles all of these with features already built in. Here's how to set it up, step by step.

**Step 1: Identify your checks.** Write down what you need to verify. For example, a quarterly contract review might include:

| Check | What to look for | Expected result |
|-------|-----------------|-----------------|
| Signature present | "Authorized Signature" in every file | Every file has it |
| Date present | A date pattern (MM/DD/YYYY) in every file | Every file has it |
| No DRAFT stamps | The word "DRAFT" in any file | No file has it |
| Amounts in range | Dollar amounts between $1,000 and $50,000 | At least one match |
| No SSNs | SSN pattern (XXX-XX-XXXX) in any file | No file has it |

**Step 2: Create saved searches in the GUI.** Open the GUI with `docsearch-gui`, point it at the folder containing your documents, and configure each check as a separate search:

- **"has_signature"** — Enter `Authorized\s+Signature` in the search box, check **Regex** and **Inverse**. Inverse mode lists files that do *not* contain the term — if the result is zero files, every document has it.
- **"has_date"** — Enter `\d{2}/\d{2}/\d{4}` in the search box, check **Regex** and **Inverse**. Same logic: zero files missing a date means all files have one.
- **"no_draft"** — Enter `DRAFT` in the search box. A normal (non-inverse) search that should return zero matches.
- **"amount_in_range"** — Enter `amount:1000..50000` in the Range field. Should return at least one match.
- **"no_ssn"** — Enter `\d{3}-\d{2}-\d{4}` in the search box, check **Regex**. Should return zero matches.

After configuring each search, click **Save Settings** in the Search Bar and give it a name. The search and all its settings are saved to the folder's collection file.

**Step 3: Build a suite.** Click **Search Suites** to open the suites panel. Click **Build a New Suite**, name it (e.g., "quarterly_contract_review"), and add your saved searches in order. For each search, set the **pass criteria**:

| Search | Criteria | Meaning |
|--------|----------|---------|
| has_signature (inverse) | `== 0` | Pass if zero files are missing a signature |
| has_date (inverse) | `== 0` | Pass if zero files are missing a date |
| no_draft | `== 0` | Pass if zero files contain "DRAFT" |
| amount_in_range | `>= 1` | Pass if at least one amount is in range |
| no_ssn | `== 0` | Pass if zero SSNs are found |

Click **Create**.

**Step 4: Run the suite.** Select your suite and click **Run Selected Suite**. docsearch runs each check in order and evaluates pass/fail against your criteria. When it finishes, three report files are generated automatically:

- **`.docx`** — A formatted Word document with a color-coded summary table (green PASS / red FAIL), per-stage details, a report fingerprint for tamper detection, and a source file manifest listing every document that was in scope. This is the report you hand to a reviewer or attach to an audit workpaper.
- **`.txt`** — A plain text version of the same report.
- **`.json`** — A machine-readable version for integration with other tools or scripts.

Click **View Suite Report** to open the `.docx` report directly.

**Step 5: Schedule recurring runs (optional).** If this is a check you need to run regularly, use the **Auto-Run every** dropdown in the suites panel to schedule it (e.g., every 24 hours). docsearch will run the suite automatically at the set interval, generate timestamped reports, and log each run to `DO_NOT_SEARCH_autorun_log.txt`. You don't need to keep the suites window open — auto-runs execute in the background.

**Step 6: Review failures.** When a check fails, the suite report tells you exactly which check failed and how many matches (or missing files) were found. Click the individual stage report (listed in the suite report) to see the specific matches — each one shows the filename, line number, and matched text with yellow highlighting. Fix the issue in the source document and re-run the suite to confirm.

**Why docsearch works well for this:**

- **Offline and read-only** — Your documents never leave your computer. docsearch does not modify, move, or delete any files. This matters for sensitive documents like financial records, legal contracts, medical files, and personnel records.
- **Portable reports** — The `.docx` report is a standard Word document that anyone can open. No special software, no login, no subscription required to review the results.
- **Repeatable** — The same suite with the same criteria produces consistent results. Save the suite once, run it whenever you need to.
- **Auditable** — Each report includes a timestamp, the docsearch version, a report fingerprint (proving the reports haven't been tampered with), and a source file manifest (listing every document that was in scope).
- **Free** — No per-seat licenses, no annual subscriptions, no per-GB processing fees. Commercial compliance tools that offer similar functionality cost $249 to $150,000+ per year.

### Sample compliance suites by industry

docsearch includes a set of 90 sample documents across 9 industries, each with pre-built compliance suites ready to run. These serve as both a demonstration of docsearch's compliance capabilities and a starting point you can adapt for your own use. The sample documents are located in subfolders under a `googledocs/` folder, with each industry in its own subfolder. Each subfolder contains 10 realistic documents — a mix of compliant and non-compliant files — along with a `.docsearch_collection.json` file containing 8 saved searches and 1 compliance suite.

**How to run any industry suite:**

1. Open `docsearch-gui`
2. In the **Search Folder** field, browse to the industry subfolder (e.g., `googledocs/financial_services`)
3. Click **Search Suites** (below Advanced Options) to open the suites panel
4. Select the suite from the **Suites** list
5. Click **Run Selected Suite**
6. Watch the results — each check shows PASS (green) or FAIL (red) in real time
7. When the suite finishes, click **View Suite Report** to open the `.docx` report

Each suite is designed so that some checks will fail — this is intentional. The non-compliant documents demonstrate what failures look like in practice and how the stage reports pinpoint the exact files and lines that caused the failure.

---

#### Financial Services Compliance

**Folder:** `googledocs/financial_services` (10 documents — loan applications, disclosures, audit reports, wire transfer logs, SAR filings)

| # | Search Name | Search Configuration | Criteria | What it checks |
|---|-------------|---------------------|----------|---------------|
| 1 | has_signature | Terms: `Authorized Signature` — Inverse: ON | `== 0` | Every file has an authorized signature |
| 2 | no_ssn | Regex: `\d{3}-\d{2}-\d{4}` | `== 0` | No Social Security numbers in any document |
| 3 | no_draft | Terms: `DRAFT` | `== 0` | No draft documents in the folder |
| 4 | has_date | Regex: `\d{2}/\d{2}/\d{4}` — Inverse: ON | `== 0` | Every file contains a date |
| 5 | sox_reference | Terms: `SOX` | `>= 1` | At least one document references SOX compliance |
| 6 | bsa_aml_reference | Expression: `BSA OR AML` | `>= 1` | Anti-money laundering documentation exists |
| 7 | large_transactions | Terms: `transaction` — Range: `amount:10000..50000` | `>= 1` | Transactions in reportable range are documented |
| 8 | account_numbers | Regex: `ACCT-\d+` | `>= 1` | Account numbers are traceable |

**Expected failures:** `no_ssn` (2 files contain SSNs), `no_draft` (1 DRAFT memo), `has_signature` (1 file missing signature)

---

#### Healthcare Compliance

**Folder:** `googledocs/healthcare` (10 documents — patient intake forms, HIPAA notices, billing summaries, clinical trial consent, discharge summaries)

| # | Search Name | Search Configuration | Criteria | What it checks |
|---|-------------|---------------------|----------|---------------|
| 1 | has_signature | Terms: `Authorized Signature` — Inverse: ON | `== 0` | Every file has an authorized signature |
| 2 | no_ssn | Regex: `\d{3}-\d{2}-\d{4}` | `== 0` | No SSNs exposed in documents (HIPAA) |
| 3 | no_draft | Terms: `DRAFT` | `== 0` | No unapproved drafts in the folder |
| 4 | hipaa_reference | Terms: `HIPAA` | `>= 1` | HIPAA compliance is documented |
| 5 | diagnosis_codes | Regex: `[A-Z]\d{2}\.\d` | `>= 1` | ICD-10 diagnosis codes are present in clinical docs |
| 6 | billing_amounts | Terms: `billing` — Range: `amount:100..50000` | `>= 1` | Billing amounts are documented |
| 7 | mrn_in_transfer | Expression: `MRN AND transfer` | `>= 1` | Medical record numbers accompany transfer requests |
| 8 | patient_consent | Terms: `consent` | `>= 1` | Consent documentation exists |

**Expected failures:** `no_ssn` (1 file contains a patient SSN), `no_draft` (1 DRAFT training document), `has_signature` (1 file missing signature)

---

#### Legal Document Review

**Folder:** `googledocs/legal` (10 documents — service agreements, settlements, NDAs, employment contracts, court filings, lease agreements)

| # | Search Name | Search Configuration | Criteria | What it checks |
|---|-------------|---------------------|----------|---------------|
| 1 | has_signature | Terms: `Authorized Signature` — Inverse: ON | `== 0` | Every file has an authorized signature |
| 2 | has_indemnification | Terms: `indemnif` — Inverse: ON | `== 0` | Every agreement has an indemnification clause |
| 3 | has_effective_date | Terms: `Effective Date` — Inverse: ON | `== 0` | Every agreement has an effective date |
| 4 | no_draft | Terms: `DRAFT` | `== 0` | No draft documents in the active folder |
| 5 | no_privileged | Terms: `PRIVILEGED` | `== 0` | No privileged documents in a production set |
| 6 | settlement_amounts | Terms: `settlement` — Range: `amount:1000..1000000` | `>= 1` | Settlement amounts are documented |
| 7 | case_numbers | Regex: `\d{4}-CV-\d+` | `>= 1` | Case numbers are present and traceable |
| 8 | nda_exists | Expression: `non-disclosure OR nondisclosure OR NDA` | `>= 1` | Non-disclosure agreements are on file |

**Expected failures:** `has_indemnification` (1 employment contract missing the clause), `has_effective_date` (1 vendor agreement missing the date), `no_draft` (1 DRAFT amendment), `no_privileged` (1 privileged litigation hold)

---

#### Government Records Compliance

**Folder:** `googledocs/government` (10 documents — procurement authorizations, budget allocations, FOIA responses, inspector general reports, grant agreements)

| # | Search Name | Search Configuration | Criteria | What it checks |
|---|-------------|---------------------|----------|---------------|
| 1 | has_signature | Terms: `Authorized Signature` — Inverse: ON | `== 0` | Every file has an authorized signature |
| 2 | no_draft | Terms: `DRAFT` | `== 0` | No draft documents in the official folder |
| 3 | no_classified | Expression: `CONFIDENTIAL OR CLASSIFIED OR SECRET` | `== 0` | No classified markings in an unclassified folder |
| 4 | has_date | Regex: `\d{2}/\d{2}/\d{4}` — Inverse: ON | `== 0` | Every document contains a date |
| 5 | procurement_authorized | Expression: `procurement AND authorized` | `>= 1` | Procurement actions have authorization |
| 6 | budget_amounts | Terms: `budget` — Range: `amount:10000..50000000` | `>= 1` | Budget allocations are documented |
| 7 | purchase_orders | Regex: `PO-\d{4}` | `>= 1` | Purchase orders are traceable |
| 8 | foia_compliance | Terms: `FOIA` | `>= 1` | FOIA documentation exists |

**Expected failures:** `has_signature` (1 procurement missing signature), `no_draft` (1 DRAFT policy memo), `no_classified` (1 file with CONFIDENTIAL marking)

---

#### Manufacturing Quality Compliance

**Folder:** `googledocs/manufacturing` (10 documents — batch records, inspection reports, calibration certificates, nonconformance reports, ISO management reviews)

| # | Search Name | Search Configuration | Criteria | What it checks |
|---|-------------|---------------------|----------|---------------|
| 1 | has_signature | Terms: `Authorized Signature` — Inverse: ON | `== 0` | Every file has a quality sign-off |
| 2 | no_draft | Terms: `DRAFT` | `== 0` | No unapproved drafts in the production folder |
| 3 | no_expired_certs | Terms: `expired` | `== 0` | No expired certifications in active files |
| 4 | iso_reference | Terms: `ISO 9001` | `>= 1` | ISO 9001 compliance is documented |
| 5 | lot_numbers | Regex: `LOT-\d{4}-\d+` | `>= 1` | Lot/batch numbers are traceable |
| 6 | part_numbers | Regex: `[A-Z]{3}-\d{4}` | `>= 1` | Part numbers are documented |
| 7 | nonconformance_closed | Expression: `nonconformance AND corrective` | `>= 1` | Nonconformances have corrective actions |
| 8 | calibration_current | Terms: `calibration` | `>= 1` | Calibration records exist |

**Expected failures:** `has_signature` (1 batch record missing QC signature), `no_draft` (1 DRAFT engineering change order), `no_expired_certs` (1 expired ISO certification)

---

#### Education FERPA Compliance

**Folder:** `googledocs/education` (10 documents — grant agreements, financial aid reports, FERPA policies, accreditation studies, class rosters, scholarship letters)

| # | Search Name | Search Configuration | Criteria | What it checks |
|---|-------------|---------------------|----------|---------------|
| 1 | has_signature | Terms: `Authorized Signature` — Inverse: ON | `== 0` | Every file has an authorized signature |
| 2 | no_ssn | Regex: `\d{3}-\d{2}-\d{4}` | `== 0` | No student SSNs exposed (FERPA violation) |
| 3 | no_draft | Terms: `DRAFT` | `== 0` | No draft documents in the official folder |
| 4 | ferpa_reference | Terms: `FERPA` | `>= 1` | FERPA compliance is documented |
| 5 | grant_amounts | Terms: `grant` — Range: `amount:1000..10000000` | `>= 1` | Grant amounts are documented |
| 6 | accreditation_docs | Terms: `accreditation` | `>= 1` | Accreditation documentation exists |
| 7 | student_ids | Terms: `Student ID` | `>= 1` | Student IDs (not SSNs) are used for identification |
| 8 | financial_aid | Expression: `financial aid OR scholarship` | `>= 1` | Financial aid records exist |

**Expected failures:** `no_ssn` (1 class roster contains student SSNs), `no_draft` (1 DRAFT curriculum proposal), `has_signature` (1 grant agreement missing signature)

---

#### Real Estate Closing Compliance

**Folder:** `googledocs/real_estate` (10 documents — closing disclosures, lease agreements, inspection reports, title searches, appraisals, purchase agreements)

| # | Search Name | Search Configuration | Criteria | What it checks |
|---|-------------|---------------------|----------|---------------|
| 1 | has_signature | Terms: `Authorized Signature` — Inverse: ON | `== 0` | Every file has a signature |
| 2 | no_draft | Terms: `DRAFT` | `== 0` | No draft documents in the closing folder |
| 3 | has_date | Regex: `\d{2}/\d{2}/\d{4}` — Inverse: ON | `== 0` | Every document contains a date |
| 4 | disclosure_present | Terms: `disclosure` | `>= 1` | Required disclosures are on file |
| 5 | property_values | Terms: `property` — Range: `amount:100000..1000000` | `>= 1` | Property values are documented |
| 6 | square_footage | Regex: `\d[\d,]+ sq ft` | `>= 1` | Square footage is documented |
| 7 | title_search | Terms: `title` | `>= 1` | Title search documentation exists |
| 8 | inspection_report | Terms: `inspection` | `>= 1` | Property inspection is on file |

**Expected failures:** `has_signature` (1 closing disclosure missing buyer signature), `no_draft` (1 DRAFT HOA disclosure)

---

#### Insurance Compliance Audit

**Folder:** `googledocs/insurance` (10 documents — homeowners/auto policies, claim reports, underwriting reviews, renewal notices, agent agreements)

| # | Search Name | Search Configuration | Criteria | What it checks |
|---|-------------|---------------------|----------|---------------|
| 1 | has_signature | Terms: `Authorized Signature` — Inverse: ON | `== 0` | Every file has an authorized signature |
| 2 | no_draft | Terms: `DRAFT` | `== 0` | No draft documents in the active folder |
| 3 | no_lapsed_policies | Expression: `lapsed OR expired` | `== 0` | No lapsed policies in the active folder |
| 4 | state_mandated_language | Terms: `state-mandated` | `>= 1` | Required state-mandated language is present |
| 5 | premium_amounts | Terms: `premium` — Range: `amount:100..10000` | `>= 1` | Premium amounts are documented |
| 6 | policy_numbers | Regex: `POL-\d{4}-\d+` | `>= 1` | Policy numbers are traceable |
| 7 | claim_numbers | Regex: `CLM-\d{4}-\d+` | `>= 1` | Claims have reference numbers |
| 8 | underwriting_review | Terms: `underwriting` | `>= 1` | Underwriting documentation exists |

**Expected failures:** `has_signature` (1 claim report missing signature), `no_draft` (1 DRAFT agent agreement), `no_lapsed_policies` (1 lapsed auto policy still in active folder)

---

#### HR Compliance Review

**Folder:** `googledocs/human_resources` (10 documents — offer letters, I-9 logs, benefits summaries, performance reviews, termination checklists, payroll memos)

| # | Search Name | Search Configuration | Criteria | What it checks |
|---|-------------|---------------------|----------|---------------|
| 1 | has_signature | Terms: `Authorized Signature` — Inverse: ON | `== 0` | Every file has an authorized signature |
| 2 | no_ssn | Regex: `\d{3}-\d{2}-\d{4}` | `== 0` | No SSNs on shared drives |
| 3 | no_draft | Terms: `DRAFT` | `== 0` | No draft documents in the official folder |
| 4 | offer_letters | Terms: `offer` | `>= 1` | Offer letter documentation exists |
| 5 | i9_verification | Terms: `I-9` | `>= 1` | I-9 employment verification records exist |
| 6 | salary_amounts | Terms: `salary` — Range: `amount:50000..200000` | `>= 1` | Salary/compensation is documented |
| 7 | eeoc_compliance | Expression: `EEOC OR EEO-1` | `>= 1` | Equal employment documentation exists |
| 8 | flsa_reference | Terms: `FLSA` | `>= 1` | Fair Labor Standards Act compliance is documented |

**Expected failures:** `no_ssn` (1 employee list with SSNs on shared drive), `no_draft` (1 DRAFT handbook update), `has_signature` (1 offer letter missing signature)

---

**Summary of expected results across all 9 suites:**

Every suite is designed to produce a mix of passes and failures. The failures demonstrate how docsearch identifies specific compliance gaps:

| Suite | Total checks | Expected PASS | Expected FAIL | Key failures |
|-------|-------------|---------------|---------------|-------------|
| Financial Services Compliance | 8 | 5 | 3 | SSNs in loan files, DRAFT memo, unsigned application |
| Healthcare Compliance | 8 | 5 | 3 | Patient SSN exposed, DRAFT training doc, unsigned intake |
| Legal Document Review | 8 | 4 | 4 | Missing indemnification, missing date, DRAFT, privileged doc |
| Government Records Compliance | 8 | 5 | 3 | Unsigned procurement, DRAFT memo, classified marking |
| Manufacturing Quality Compliance | 8 | 5 | 3 | Unsigned batch record, DRAFT ECO, expired certification |
| Education FERPA Compliance | 8 | 5 | 3 | Student SSNs in roster, DRAFT proposal, unsigned grant |
| Real Estate Closing Compliance | 8 | 6 | 2 | Missing buyer signature, DRAFT HOA disclosure |
| Insurance Compliance Audit | 8 | 5 | 3 | Unsigned claim, DRAFT agreement, lapsed policy |
| HR Compliance Review | 8 | 5 | 3 | SSNs on shared drive, DRAFT handbook, unsigned offer |

When a check fails, open the stage report (listed in the suite report) to see exactly which files and lines caused the failure. This is the workflow an auditor would follow: run the suite, review the summary, drill into failures, fix the underlying issues, and re-run to confirm.

## Search Suites

Search suites let you save individual searches, group them into named suites, and run them as a batch with pass/fail tracking. This turns docsearch into an audit automation tool — run the same compliance checks repeatedly and get a report showing which checks passed and which failed.

**How it works:**

1. **Save a search:** Configure a search in the GUI (terms, flags, options), then click the **Save Settings** button in the Search Bar. Give it a unique name (e.g., "missing_disclaimer"). The search and all its settings are saved to `.docsearch_collection.json` in the search folder.

2. **Build a suite:** Click **▶ Search Suites** (below Advanced Options) to open the suites window. Click **Build a New Suite**, give it a name (e.g., "quarterly_compliance"), and use the dual-panel selector to choose and order your searches. The left panel shows available saved searches; use the **→** button (or double-click) to add them to the right panel, which represents execution order. Use the **▲ Up** and **▼ Down** buttons to reorder. Click **Create**.

3. **Run the suite:** Select one or more suites from the **Suites** list and click **Run Selected Suite**. Each search runs sequentially against the folder — its settings are loaded into the main GUI as it runs so you can see what's happening. Results appear in real-time with color-coded PASS/FAIL indicators. When multiple suites are selected, their searches are combined (deduplicated) and run together.

4. **Reports:** Suite report files are automatically generated with timestamps in three formats: `.docx`, `.txt`, and `.json` (e.g., `DO_NOT_SEARCH_docsearch_suite_{name}_{timestamp}.docx`). The `.docx` report is a formatted Word document with a color-coded summary table (green PASS / red FAIL), per-stage details with search criteria, a report fingerprint for audit traceability, and the docsearch version used. Each report includes each test's name, search terms, result, and an overall PASSED/FAILED verdict. After a suite run completes, a **View Suite Report** button appears in the suite panel — click it to open the `.docx` report directly.

**Report fingerprint and source file manifest:** Each `.docx` suite report includes two audit traceability features:

1. **Report fingerprint** (e.g., `Report fingerprint: 3a8f1c09b72e4d5a`). This is a **hash** — a one-way mathematical function that converts data into a fixed-length string of characters. Think of it like a wax seal on an envelope: if anyone changes the contents, the seal breaks. Specifically, docsearch takes the names and sizes of all stage report files generated during the suite run, feeds them through the SHA-256 hash algorithm, and truncates the result to 16 characters. The same set of stage reports will always produce the same fingerprint. If a report file is modified, replaced, or deleted after the suite run, re-running the hash would produce a different fingerprint — proving the reports have changed. This gives auditors a simple way to verify that the reports they are reviewing are the same ones that were originally generated. The fingerprint does not contain any of your document content — it is a one-way computation that cannot be reversed to recover the original data.

2. **Source file manifest** — a table at the end of the `.docx` report listing every document that was present in the search folder when the suite ran. Each row shows the file number, filename, size, and last-modified date, followed by a total file count and size. This answers the auditor's question "which documents were examined?" in a way that is human-readable and reviewable. An auditor can look at the manifest and confirm "yes, these are the right 247 documents" or notice "wait, the Q4 folder is missing." Unlike a hash of the source files — which would break any time a file was legitimately added or modified after the suite ran, and which would require re-running docsearch to verify — the manifest is a plain list that anyone can review without special tools. The report fingerprint proves the reports are intact; the manifest proves which documents were in scope.

**Pass Criteria:** By default, a search passes if it finds at least 1 match (`>= 1`). You can set custom pass criteria per-search when creating or editing a suite. Select a search in the right panel of the suite editor and use the **Pass criteria** dropdown and threshold field. Three operators are available:

| Operator | Meaning | Example use case |
|----------|---------|-----------------|
| `>= N` | Pass if matches >= N | "Find at least 5 contracts" (`>= 5`) |
| `<= N` | Pass if matches <= N | "No more than 3 violations allowed" (`<= 3`) |
| `== N` | Pass if matches == N | "No PII should be found" (`== 0`) |

The criteria is displayed next to each search in the suite contents list (e.g., `find_contracts (>= 1)`) and in the run results (e.g., `[PASS] find_contracts — 12 match(es) (need >= 1)`). Criteria are stored per-search within each suite in the collection file, so different suites can apply different criteria to the same saved search. Suites created before this feature default to `>= 1`.

**Pass/fail logic (with default `>= 1` criteria):**

| Condition | Result |
|-----------|--------|
| Match count satisfies the pass criteria | PASS |
| Match count does not satisfy the pass criteria | FAIL |
| Search configuration error | FAIL (always, regardless of criteria) |

With the default criteria (`>= 1`), a search passes if it finds at least one match and fails if it finds none. Custom criteria change this — for example, `== 0` makes a search pass only when there are no matches, and `<= 3` passes when there are 3 or fewer matches.

**Compliance audit patterns:** By combining search modes with pass criteria, you can build document-level compliance checks that flag exactly which files pass or fail:

| Check | How to build it | Criteria | What the report shows |
|-------|----------------|----------|----------------------|
| **Every file must contain a term** | Search for "disclaimer" with **Inverse** on | `== 0` | Passes if all files have it. If it fails, the stage report lists every file *missing* the term |
| **No file should contain a term** | Search for "DRAFT" normally | `== 0` | Passes if no file contains it. If it fails, the stage report lists every file that still has it |
| **Required clause with complex wording** | Expression: `(signature AND date) AND NOT draft`, **Inverse** on | `== 0` | Flags files missing the required combination |
| **Limit violations** | Search for "TBD" or "TODO" normally | `<= 3` | Passes if 3 or fewer matches remain across all files |
| **Sensitive data detection** | Search for SSN/PII patterns with **Regex** on | `== 0` | Flags every file containing sensitive data |

The key technique is **inverse search + `== 0`**: inverse mode lists files that do *not* contain the search terms, and `== 0` means "pass only if no files are missing it." The stage report then serves as a non-compliance report — it lists the exact files that need attention.

**Managing the collection:**

- **Load Settings ▼:** Click the **Load Settings ▼** button in the Search Bar to open a popup listing all saved searches for the current folder. The highlight follows your cursor — click to lock your selection, then click **Select** to load it into the GUI, or **Delete** to remove it from the collection. If a deleted search is referenced by any suites, it's automatically removed from those suites too.
- **Edit Suite:** Modify which searches are included in an existing suite and change their execution order using the same dual-panel selector with Up/Down reordering.
- **Delete Suite:** Remove a suite (or multiple selected suites) without affecting the saved searches it references.

**Boolean expression searches in suites:** Saved searches fully support expression mode. Toggle the **Expression** checkbox, enter your boolean expression (e.g., `(budget OR revenue) AND NOT draft`), and click **Save Settings** — the expression flag and query are preserved. When the suite runs that search, it uses the same boolean logic. This makes it easy to build compliance suites with complex conditions like "must contain (signature AND date) but NOT draft".

**Range queries in suites:** Saved searches fully preserve range filters. Enter your range specs in the **Range** field (e.g., `amount:1000..5000, date:2024-01-01..2024-12-31`), configure your text search terms (or leave empty for range-only), and click **Save Settings**. When the suite runs that search, the same range filters are applied. Range filters also work with expressions in suites — for example, save a search with expression `budget AND amount:1000..5000` and it will be restored exactly when the suite runs.

**Per-stage reports:** When a suite runs — in both normal and cascade mode — each search's results are automatically preserved as separate timestamped files named `DO_NOT_SEARCH_SUITE_{suite}_stage{NN}_{search}_{timestamp}.txt` (and `.docx`, `.csv`, `.json` if those formats were generated). Without this, each search would overwrite the previous one's `docsearch_results` files, leaving only the last search's report. The `DO_NOT_SEARCH_` prefix ensures these files are never re-searched in future searches. Previous run's stage files are cleaned up automatically before each new run, so you always see fresh results.

**Search execution order:** The order of searches in a suite determines the order they run. When creating or editing a suite, use the **▲ Up** and **▼ Down** buttons in the right panel to set the desired execution order. This is especially important for cascade mode, where each stage's output feeds into the next.

**Cascade mode:** When creating or editing a suite, check the **Cascade mode** checkbox to enable progressive file narrowing. In cascade mode, each stage's matched files become the file filter (`-f`) for the next stage — creating a pipeline that progressively narrows results.

*Example use case:* A three-stage cascade suite for contract review:
1. Stage 1 searches all documents for "contract" or "agreement" → finds 200 files
2. Stage 2 searches only those 200 files for "liability" or "indemnification" → narrows to 45 files
3. Stage 3 searches only those 45 files for specific clause language → finds 12 files with the exact provisions

If a cascade stage finds no matches, the chain breaks — that stage is marked FAIL and subsequent stages run unrestricted (no file filter) so they can still produce results independently. Cascade mode only applies when running a single suite; when multiple suites are selected and combined, cascade is ignored because the deduped searches have no meaningful order.

The suite results display shows cascade narrowing information:
```
  [PASS] liability_clauses — 23 match(es) in 45 file(s) (narrowed from 200)
```

**Clean Up Suite Files:** Click this button (next to Delete Suite) to delete all generated suite and stage report files (`DO_NOT_SEARCH_SUITE_*` and `DO_NOT_SEARCH_docsearch_suite_*`) from the search folder and the suite output directory. A confirmation dialog lists the files before deletion. User-saved reports from `-s` and `-sa` are never affected.

**Suite Scheduling (Auto-Run):** Each suite can be scheduled to run automatically at a set interval. Select a suite, then use the **Auto-Run every:** dropdown to choose an interval: Off, 30 min, 1 hour, 4 hours, 12 hours, or 24 hours. The **Auto-Run Suite:** label shows which suite is scheduled — this is independent of the listbox selection, so you can select and run a different suite manually without affecting the auto-run schedule. The schedule is stored per-suite in the collection file, so different suites can have different schedules. Safety guards prevent conflicts — a scheduled run is skipped (and retried at the next interval) if a search, index build, index refresh, or another suite run is already in progress. The **Last run** label shows the suite name and timestamp of its most recent run (manual or scheduled). The **Next Auto-Run** label shows a countdown timer (e.g., "4h 22m", "15m", "<1m") that updates every minute.

Scheduled runs persist across app restarts — when the app opens, it reads the last run time from the collection file, calculates when the next run is due, and resumes the schedule automatically. If a run is overdue (e.g., the app was closed during the interval), it runs shortly after launch. The Suites window does not need to be open for auto-runs to execute. When you reopen the Suites window, the scheduled suite is automatically re-selected and highlighted in the list.

When a scheduled run completes, two things happen automatically:

1. **Suite reports are generated** — `DO_NOT_SEARCH_docsearch_suite_{name}_{timestamp}.docx`, `.txt`, and `.json` are created with full results (always timestamped to avoid overwriting previous runs). The `.docx` report includes a color-coded summary table and per-stage details.
2. **An auto-run log entry is appended** — `DO_NOT_SEARCH_autorun_log.txt` records each run with a summary and per-search pass/fail details:
   ```
   [2026-03-28 14:30:00] Suite: quarterly_compliance — 4/5 passed — FAILED
     [PASS] find_contracts — 12 match(es) (need >= 1)
     [FAIL] no_pii — 2 match(es) (need == 0)
   ```

Both files are written to the suite's **Output Dir** if set, otherwise to the search folder. The `DO_NOT_SEARCH` prefix ensures they are never re-searched. Click **Open Auto-Run History** in the suite panel to open the log file directly. If the log file is deleted, it is automatically recreated on the next auto-run.

**Output Directory:** The suite panel has its own **Output Dir** field with a Browse button. When set, all suite-generated files (stage reports, suite reports, auto-run logs) are written there instead of the search folder. This setting is automatically saved to `~/.docsearchrc` when you close the Suites window and restored on next launch.

**Storage:** Each folder has its own collection file (`.docsearch_collection.json`). When you switch folders, the Search Suites window automatically refreshes to show that folder's collection. Suite schedules and last-run timestamps are stored per-suite in this file.

## FAQ (Frequently Asked Questions)

**Where are my search results saved and what information is printed on the search report?**
Results are saved to two files in the current directory: `docsearch_results.txt` and `docsearch_results.docx`. Each report includes the date and time, the command used, search terms, number of hits, search time, number of files searched, total file size, and a file type tally. Each match shows the document name, directory path, line number, and the matched text with search terms highlighted — `**bold**` markers in the `.txt` file and yellow highlighting in the `.docx` file. Note that these two result files are overwritten each time you run a new search. Use the `-s` flag to archive them or the `-sa` flag to accumulate results across searches. Archived and accumulated files include your chosen name and are automatically prefixed with `DO_NOT_SEARCH` (e.g., `DO_NOT_SEARCH_my_report.txt`) so they are never re-searched in future searches.

**What happens when a file can't be read?**
Some files may fail to read — for example, encrypted PDFs, corrupted documents, password-protected spreadsheets, files with unsupported encoding, or files that are open in another program (especially on Windows, where open files are locked). When this happens, a warning is printed to the screen and the error is logged to `docsearch_errors.log` with a timestamp. If a file is locked, the warning will suggest closing the program that has it open and trying again. In the GUI, a **View Error Log** button appears after any search where errors were logged — click it to open the log directly. The error log is only created when a file error occurs — if all files are read successfully, no error log is created. The log appends across searches so you have a history of any issues. You can delete `docsearch_errors.log` at any time — a new one will be created automatically the next time a file error occurs. The error log is automatically excluded from searches so it never appears in your results. If docsearch itself crashes unexpectedly, a crash report with a diagnosis is also written to this file — see the [Output](#output) section for details.

**How do I recall a previous command?**
Press the up arrow key in your terminal to scroll through previous commands. This is a built-in feature of all terminals (macOS, Windows, and Linux) — not specific to docsearch. You can press up repeatedly to go further back, then press Enter to re-run the command.

**How do I cancel a search in progress?**
Press Ctrl+C. docsearch will stop cleanly and print "Search cancelled." This works on macOS, Windows, and Linux.

**How do I check if docsearch is installed correctly?**
Run `docsearch --check`. This verifies your Python version, checks that all required dependencies are installed, reports whether Tesseract is available for OCR, and checks available disk space. If anything is missing, it tells you exactly how to fix it.

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

**How do I search for exact word matches only?**
Use the `-W` flag. This enables whole-word matching using word boundaries, so only complete words are matched — `bob` matches "bob" but not "bobcat", "bobby", etc.<br>
Example: `docsearch -W bob`

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

**Can I combine AND, OR, and NOT in a single query?**
Yes — use the `-e` flag for boolean expression search. This lets you write complex logic with AND, OR, NOT, and parentheses.<br>
Example: `docsearch -e "(budget OR revenue) AND NOT draft"`<br>
Precedence: NOT binds tightest, then AND, then OR. Use parentheses to override. The `-e` flag cannot be combined with `-a`, `-n`, or `-p` — those features are built into the expression syntax. Range specs (`field:min..max`) can be embedded directly in expressions (e.g., `"budget AND amount:1000..5000"`). See [Boolean Expression Search](#boolean-expression-search) for details.

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

**What if I upgrade Python and docsearch stops working?**
Upgrading Python can occasionally break installed packages. If docsearch stops working after a Python upgrade, run `docsearch --check` to see which dependencies need updating, then reinstall: `pip install --upgrade docsearch` (or `pipx reinstall docsearch` if you used pipx). Check `docsearch_errors.log` for a crash report with a diagnosis — it usually points to the exact package that needs updating. docsearch will also print a warning at startup if your Python version is outside the tested range. Most dependency updates are available within a few weeks of a new Python release.

**What is the search index and when should I use it?**
The search index is an optional SQLite database (`.docsearch.db`) that stores extracted text from your documents. Build it with `docsearch --index` in any folder where you search frequently. After that, every search in that folder uses the index automatically — skipping file parsing entirely — making repeated searches much faster. You don't need the index for one-off searches or small folders. See [Search Index](#search-index-optional) for details.

**How much disk space does the index use?**
The index is typically 10–20% the size of the original files. Text-heavy documents (PDFs, Word docs) produce smaller indexes relative to file size since the index stores only the extracted text. You can check the exact size with `docsearch --index-status` and delete it anytime with `docsearch --index-clear`.

**Does the index stay up to date?**
Yes — each search automatically detects new, changed, or deleted files and refreshes the index incrementally before searching. You only need to rebuild manually (`docsearch --index`) if you want a full rebuild, such as after changing OCR or recursive settings.

**Does it modify my files?**
No — docsearch only reads your files. It never changes, moves, or deletes them.

**Is docsearch safe from SQL injection?**
Yes. All user input that reaches the SQLite search index is handled safely. FTS5 search terms are escaped and passed via parameterized queries (`?` placeholders) — never interpolated into SQL strings. File type and filename filters also use parameterized queries. The direct-scan and parse-cache code paths load data with static SQL and filter entirely in Python, so user input never touches SQL at all. Malformed FTS5 expressions are caught and handled gracefully with a fallback to the parse-cache path.

**Is the search case-sensitive?**
No — all searches are case-insensitive by default.

**Why are my reports capped at 1,000 matches?**
By default, docsearch caps reports at 1,000 matches to prevent very large result sets from causing slow report generation (especially the `.docx` report). The total match count is always reported accurately in the summary — only the report files are capped. To change the cap, use `-m N` (e.g., `-m 5000`). To remove the cap entirely, use `-m 0`. You can also set it permanently with `--config max_matches=5000` or in the GUI's Advanced Options panel.

Every feature in docsearch serves the core mission of finding content in documents:

- **Search flags** (`-a`, `-e`, `-x`, `-p`, `-O`, `-z`, `-w`, `-W`) — control *how* to match
- **Filter flags** (`-t`, `-f`, `-r`, `-n`) — control *where* to search
- **Context flags** (`-A`, `-B`) — control *what to show* around matches
- **Output flags** (`-s`, `-sa`, `-o`) — control *what to do* with results
- **Performance flags** (`-c`, `-m`, `--index`) — control *how fast* to search
- **Settings flag** (`--config`) — manage *saved settings*

## Troubleshooting

**Why can't docsearch read files in my Documents folder (permission denied)?**

Your operating system may be blocking docsearch (or your terminal) from accessing protected folders like Documents or Downloads. This is a security feature — not a docsearch bug. The fix below is a one-time setup that permanently allows access on each platform. These changes are narrowly scoped — they only grant read access to your terminal or Python for the folders you specify. All other OS security features (antivirus, firewall, app sandboxing, etc.) continue to work normally.

- **macOS:** Open System Settings → Privacy & Security → Full Disk Access. Click the `+` button, navigate to your terminal app (Terminal.app, iTerm, etc.), and add it. You may need to unlock the settings with your password first. Once added, the permission is permanent — it survives reboots and app updates. However, a major macOS upgrade (e.g., Ventura → Sonoma) can reset privacy permissions, so you may need to re-add it after upgrading. If you prefer narrower access, use Privacy & Security → Files and Folders instead and grant your terminal access to just the Documents folder.
- **Windows:** Open Windows Security → Virus & threat protection → Ransomware protection → Controlled folder access. If Controlled folder access is on, click "Allow an app through Controlled folder access," then click "Add an allowed app" → "Browse all apps" and select your Python executable. To find its path, run `where python` in a terminal. Once added, the allowlist entry is permanent. If you don't use Controlled folder access (it's off by default), this step is unnecessary — check your folder permissions instead: right-click the folder → Properties → Security tab and make sure your user account has Read access. Alternatively, running your terminal as administrator bypasses most access restrictions, but this is a per-session workaround, not a permanent fix.
- **Linux:** Run `chmod -R u+r /path/to/folder` to grant yourself read access, or `chown -R $USER /path/to/folder` to take ownership. These changes are permanent. If the folder is on an NTFS or FAT external drive, set the permissions at mount time by adding `uid=$USER,gid=$(id -g),dmask=022,fmask=133` to the mount options in `/etc/fstab`, then remount. This ensures the drive is always accessible when plugged in.

---

**"ModuleNotFoundError: No module named 'fitz'" (or any other module)**

A required dependency is missing. This can happen after a Python upgrade or if the install was interrupted.

```bash
pip install --upgrade docsearch       # reinstalls docsearch and all dependencies
docsearch --check                      # verify everything is installed
```

If you used pipx: `pipx reinstall docsearch`

---

**"Error: docsearch requires Python 3.10 or later"**

docsearch needs Python 3.10+. Check your version with `python3 --version`, then upgrade:

- macOS: `brew install python@3.12`
- Ubuntu: `sudo apt install python3.12`
- Windows: Download from [python.org/downloads](https://www.python.org/downloads/)

After upgrading, reinstall docsearch with the new Python.

---

**"Fuzzy search requires the rapidfuzz Python package"**

The `-z` (fuzzy) flag needs the `rapidfuzz` package:

```bash
pip install rapidfuzz
```

Or reinstall docsearch: `pip install --upgrade docsearch`

---

**"OCR requires the pytesseract and Pillow packages" / "Tesseract OCR is not installed"**

The `-O` (OCR) flag needs three things:

1. **Tesseract binary** (the OCR engine):
   - macOS: `brew install tesseract`
   - Ubuntu: `sudo apt install tesseract-ocr`
   - Windows: [Download from GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

2. **Python packages**: `pip install pytesseract Pillow`

---

**"Index database was corrupted and has been removed"**

docsearch detected that the `.docsearch.db` file was damaged and automatically deleted it. This can happen if a previous indexing operation was interrupted. Simply rebuild:

```bash
docsearch --index
```

---

**"docsearch stopped working after upgrading Python"**

Python upgrades can break installed packages. Fix it by reinstalling:

```bash
pip install --upgrade docsearch       # if installed with pip
pipx reinstall docsearch              # if installed with pipx
docsearch --check                      # verify the fix
```

Check `docsearch_errors.log` in the current directory for a crash report with a diagnosis of the specific issue.

---

**"Permission denied" or "file is locked"**

A file could not be read because it's open in another application (common on Windows) or you don't have read permissions. docsearch will skip the file and continue searching. Check `docsearch_errors.log` for the specific file.

---

**"An unexpected error occurred"**

1. Check `docsearch_errors.log` in the current directory — it contains a diagnosis with the likely cause and a suggested fix
2. Run `docsearch --check` to verify your Python version and all dependencies
3. If the problem persists, [report it on GitHub](https://github.com/exbuf/docsearch/issues) and include the contents of `docsearch_errors.log`

## Library API

docsearch can be called directly from Python code, making it easy to integrate into automated workflows, compliance pipelines, or custom applications.

### Basic Usage

```python
from docsearch import search

result = search(["budget", "revenue"], directory="/path/to/docs")

print(f"Found {len(result.matches)} matches in {len(result.files_searched)} files")
for match in result.matches:
    print(f"  {match.filename}:{match.line_num}: {match.text}")
```

### With Options

```python
from docsearch import search

# Wildcard search in specific file types, with subdirectories
result = search(
    ["budg*"],
    directory="/path/to/docs",
    use_wildcard=True,
    recursive=True,
    file_types=[".pdf", ".docx"],
)

# Regex search with AND mode
result = search(
    [r"\d{3}-\d{3}-\d{4}", "invoice"],
    directory="/path/to/docs",
    use_regex=True,
    match_all=True,
)

# Boolean expression search
result = search(
    [],
    directory="/path/to/docs",
    expression="(budget OR revenue) AND (cost OR profit)",
)

# Expression with wildcard mode
result = search(
    [],
    directory="/path/to/docs",
    expression="budg* AND rev*",
    use_wildcard=True,
)

# Range query — filter by value ranges
result = search(
    ["invoice"],
    directory="/path/to/docs",
    range_filters=["amount:1000..5000", "date:2024-01-01..2024-12-31"],
)

# Range-only search (no text terms)
result = search(
    [],
    directory="/path/to/docs",
    range_filters=["amount:1000..5000"],
)

# Range specs inside boolean expressions
result = search(
    [],
    directory="/path/to/docs",
    expression="budget AND amount:1000..5000",
)

# Filename range — filter files by date in filename
result = search(
    ["budget"],
    directory="/path/to/docs",
    range_filters=["fn:date:2024-01-01..2024-12-31"],
)

# Progress tracking
def on_progress(done, total, filename):
    print(f"  [{done}/{total}] {filename}")

result = search(["error"], directory="/var/log", progress=on_progress)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `search_terms` | `list[str]` | *(required)* | Terms to search for (pass `[]` when using `expression` or `range_filters`) |
| `directory` | `str` | Current directory | Directory to search in |
| `match_all` | `bool` | `False` | Require ALL terms (AND mode) |
| `expression` | `str` | `None` | Boolean expression with AND, OR, NOT, parentheses, and range specs (e.g. `"(budget OR revenue) AND NOT draft"`, `"budget AND amount:1000..5000"`) |
| `recursive` | `bool` | `False` | Search subdirectories |
| `use_regex` | `bool` | `False` | Treat terms as regex patterns |
| `use_fuzzy` | `bool` | `False` | Approximate matching |
| `use_wildcard` | `bool` | `False` | Wildcard patterns (`*` and `?`) |
| `use_whole_word` | `bool` | `False` | Whole-word matching — matches complete words only |
| `use_ocr` | `bool` | `False` | OCR for scanned PDFs and images |
| `exclude_terms` | `list[str]` | `None` | Exclude lines matching these terms |
| `file_types` | `list[str]` | `None` | Limit to these extensions (e.g. `[".pdf", ".docx"]`) |
| `file_names` | `list[str]` | `None` | Search only these specific files |
| `context_before` | `int` | `0` | Lines to include before each match |
| `context_after` | `int` | `0` | Lines to include after each match |
| `proximity` | `int` | `0` | Require terms within N words of each other |
| `cores` | `int` | Auto | CPU cores for parallel processing |
| `use_index` | `bool` | Auto | Use search index if available |
| `progress` | `callable` | `None` | Callback `progress(done, total, filename)` |
| `range_filters` | `list[str]` | `None` | Range filter specs (e.g. `["amount:1000..5000", "date:2024-01-01..2024-12-31"]`). Use `fn:` prefix for filename ranges (e.g. `["fn:date:2024-01-01..2024-12-31"]`) |

### Return Value

`search()` returns a `SearchResult` with these fields:

| Field | Type | Description |
|-------|------|-------------|
| `matches` | `list[SearchMatch]` | List of matches found |
| `files_searched` | `list[str]` | Absolute paths of all files examined |
| `skipped_files` | `list[tuple]` | Files that couldn't be read: `(filename, error_msg)` |
| `elapsed` | `float` | Search time in seconds |
| `used_index` | `bool` | Whether the indexed search path was used |

Each `SearchMatch` has fields: `file_dir`, `filename`, `line_num`, `text`.

### Error Handling

`search()` raises `ValueError` for invalid parameter combinations (e.g. combining regex + fuzzy) and `FileNotFoundError` if specified files are not found.

```python
from docsearch import search

try:
    result = search([r"[invalid"], use_regex=True)
except ValueError as e:
    print(f"Invalid search: {e}")
```

## Running Tests

Running tests requires the cloned repository (see [Option B](#option-b-manual-install)). From the project folder:

```bash
source venv/bin/activate
pytest tests/ -v
```

## Project Structure

```
docsearch/
├── docsearch/
│   ├── __init__.py      # Package init, re-exports library API
│   ├── __main__.py      # Enables python -m docsearch
│   ├── api.py           # Public library API (search(), SearchMatch, SearchResult)
│   ├── cli.py           # CLI entry point (calls api.search internally)
│   ├── collection.py    # Saved search collections and search suites
│   ├── constants.py     # Shared constants and defaults
│   ├── expr_parser.py   # Boolean expression parser (AND/OR/NOT)
│   ├── gui.py           # Optional GUI (docsearch-gui)
│   ├── indexer.py       # Optional SQLite FTS5 search index
│   ├── parser.py        # Command-line flag parsing
│   ├── reporter.py      # Report generation (txt, docx, csv, json)
│   ├── scanner.py       # File processing and discovery
│   ├── translator.py    # Plain-English translation of commands and regex
│   └── wizard_patterns.py # Regex Wizard pattern presets
├── tests/
│   ├── test_api.py        # Library API test suite
│   ├── test_cli.py        # CLI test suite
│   ├── test_expr_parser.py # Boolean expression parser tests
│   ├── test_collection.py # Collection and search suite tests
│   ├── test_gui.py        # GUI test suite
│   ├── test_translator.py # Translator test suite
│   └── test_wizard.py     # Wizard patterns test suite
├── pyproject.toml       # Project metadata and dependencies
├── requirements.txt     # Pip requirements
└── README.md
```

## License

This project is licensed under the [MIT License](LICENSE).
