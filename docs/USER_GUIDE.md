# docsearch User Guide

This is the complete reference guide for docsearch. For a quick overview, see the [README](../README.md).

## Table of Contents

- [Getting Started with the Terminal](#getting-started-with-the-terminal)
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
- [Saved Settings (Optional)](#saved-settings-optional)
- [Files Created by docsearch](#files-created-by-docsearch)
- [Limits and Constraints](#limits-and-constraints)
- [Your First Advanced Search — Step by Step](#your-first-advanced-search--step-by-step)
- [Search Suites](#search-suites)
- [Running Tests](#running-tests)
- [Project Structure](#project-structure)

## Getting Started with the Terminal

If you've never used a terminal before, this section walks you through everything from opening it to running your first search. If you're already comfortable with the command line, skip ahead to [GUI Mode](#gui-mode) or [Usage](#usage).

**Prefer not to use the terminal?** That's completely fine — run `docsearch-gui` for a point-and-click interface instead. See [GUI Mode](#gui-mode).

### What is a terminal?

A terminal (also called "command line," "command prompt," or "shell") is a text-based way to tell your computer what to do. Instead of clicking buttons, you type commands and press Enter. It looks intimidating at first, but you only need to learn a few commands to use docsearch.

### Step 1: Open your terminal

- **Windows:** Press the Windows key, type `cmd`, and click **Command Prompt**. Or type `powershell` and click **Windows PowerShell**. Either works.
- **macOS:** Open **Finder** → **Applications** → **Utilities** → **Terminal**. Or press Cmd+Space, type `terminal`, and press Enter.
- **Linux:** Press Ctrl+Alt+T, or find **Terminal** in your applications menu.

You'll see a window with a blinking cursor waiting for you to type something. This is your terminal.

### Step 2: Navigate to your documents folder

Your terminal starts in your home directory. You need to tell it where your documents are. Use the `cd` command (short for "change directory"):

**Windows:**
```cmd
cd C:\Users\YourName\Documents
```

**macOS:**
```bash
cd ~/Documents
```

**Linux:**
```bash
cd ~/Documents
```

Replace the path with wherever your actual documents are. If the folder name has spaces, wrap it in quotes:

```bash
cd "/Users/YourName/My Documents"
```

**Tip:** You can drag a folder from your file manager onto the terminal window — most terminals will paste the full path for you.

### Step 3: Run your first search

Type this and press Enter:

```bash
docsearch budget
```

docsearch will scan every supported file in the folder and show a summary:

```
Files searched: 47 (12.34 MB) — Found 23 match(es).
Elapsed time: 1.2 seconds, Cores used: 4 of 8
Results ==> /Users/YourName/Documents
  docsearch_results.txt (5.67 KB), docsearch_results.docx (42.31 KB)
```

That's it — you just searched 47 files in 1.2 seconds. Your results are saved in two files.

### Step 4: Open your results

The results are saved in the same folder where you ran the search. Open the Word report to see your matches highlighted in yellow:

**Windows:**
```cmd
start docsearch_results.docx
```

**macOS:**
```bash
open docsearch_results.docx
```

**Linux:**
```bash
xdg-open docsearch_results.docx
```

Or simply navigate to the folder in your file manager and double-click `docsearch_results.docx`.

### Step 5: Try a few more searches

Now that you know the basics, try these:

**Search for multiple words (finds files containing any of them):**
```bash
docsearch budget revenue expenses
```

**Search for files containing ALL of the words:**
```bash
docsearch -a budget revenue
```

**Search subfolders too:**
```bash
docsearch -r budget
```

**Search only PDFs and Word documents:**
```bash
docsearch -t pdf,docx budget
```

**Search for a pattern (like Social Security numbers):**
```bash
docsearch -x "\d{3}-\d{2}-\d{4}"
```

**Find files that are MISSING a required term:**
```bash
docsearch --inverse "Authorized Signature"
```

**Find dollar amounts in a range:**
```bash
docsearch -R amount:1000..5000 budget
```

### Step 6: Get help

To see all available options with examples:

```bash
docsearch -h
```

This shows every flag, organized by category (Search Modes, Filters, Output, Index, Settings), with examples for each one.

### Useful terminal tips

- **Up arrow** — press it to recall your previous command. Press it again to go further back. This is how you re-run or modify a previous search without retyping it.
- **Tab completion** — start typing a folder or file name and press Tab. The terminal fills in the rest. This saves typing and avoids typos.
- **Ctrl+C** — cancels a search in progress. docsearch stops cleanly.
- **History** — your terminal remembers every command you've typed. Use the up/down arrows to scroll through them.

### What's next?

- See the [Flag Use Summary](#flag-use-summary) for a complete table of all options
- See the [Command Examples](#command-examples) table for 150+ example commands
- Try the GUI for a visual interface: just type `docsearch-gui`
- Read [Your First Advanced Search](#your-first-advanced-search--step-by-step) for guided walkthroughs of regex, fuzzy, range queries, and more

---

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
| **Search Bar** | Search entry field, **Inverse** checkbox, **Run Search** button, **Wizard** button, **Save Search** button (saves the current search to the folder's collection for reuse in search suites), and **Load Settings ▼** button (opens a popup to load or delete saved searches) |
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

Click "Advanced Options" to expand a panel with additional settings — AND mode, recursive search, fuzzy matching, wildcards, OCR, regex, whole-word matching, expression mode, inverse search, exclude terms, file type filtering, proximity, context lines, CPU cores, max matches, range filters, specific files, save as, append to, output directory, additional output formats (CSV, JSON), and timestamp filenames. Every terminal flag is available in the GUI. You don't need any of them for a basic search. Hover over any option to see a description of what it does. At the bottom of the panel are four buttons: **Inspect .docsearchrc** shows the current saved settings (read-only). **Save Defaults** saves your current search terms, folder, and all options as defaults to `~/.docsearchrc` — the next time you open the GUI, everything will be pre-filled. **Restore Settings** reloads saved defaults from `~/.docsearchrc` into the GUI. **Reset** clears all fields and restores the GUI to its default state — but it only affects the current session. Your saved defaults in `~/.docsearchrc` are not changed unless you also click **Save Defaults** after resetting.

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

**Building the index from the terminal:**

```bash
cd /path/to/your/documents
docsearch --index              # index files in current folder and all subfolders
docsearch --index -O           # same, with OCR for scanned PDFs and images
```

**Building the index from the GUI:**

1. Open `docsearch-gui`
2. In the **Search Folder** field, browse to the folder you want to index
3. Click **Index Options** (below Search Suites on the main screen) to expand the index panel
4. Click **Build Index(es)** — this indexes all files in the folder **and all subfolders** automatically (recursive is always on for index builds)
5. Once built, check **Search Using Index(es)** in Advanced Options to use it

The index is stored as a single `.docsearch.db` file inside the folder you indexed. It contains the extracted text from every supported file in that folder and all its subfolders. This means if you build an index in your top-level documents folder, one index covers everything — you don't need to build separate indexes in each subfolder. Each folder can have its own index if you prefer, but a single top-level index is the simplest approach for most users. You can see the index status (file count, size, last updated) by clicking **Index Status** in the index panel.

**Using the index:**

Once built, the index is used automatically in the CLI — just search as usual. In the GUI, make sure **Search Using Index(es)** is checked in Advanced Options:

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

**Indexes and subfolders:** The index (`.docsearch.db`) is always stored in the folder you point docsearch at — the search folder. When you build an index with recursive mode, it indexes all files in all subfolders, but the index file itself lives in the top folder. If you also build indexes inside individual subfolders, each gets its own separate `.docsearch.db`. These indexes are completely independent — they do not interfere with each other. When you search from the top folder with `-r`, docsearch uses the top folder's index. When you search from a subfolder, it uses that subfolder's index (if one exists). The only downside of building indexes at both levels is disk space — the top-level index already contains everything the subfolder indexes contain. For small folders this is trivial; for very large document collections, choose one level or the other.

**Indexes and search suites:** The index setting is stored **per saved search**, not as a global setting. When you save a search with the **Search Using Index(es)** checkbox checked, that search will use the index when it runs as part of a suite. If the checkbox was not checked when the search was saved, the suite will search files directly — even if an index exists in the folder. The main screen's index checkbox does not affect suite runs. To enable indexing for an existing saved search, load it into the GUI, check **Search Using Index(es)**, and re-save it with the same name. If a saved search has indexing enabled but no index exists in the folder, docsearch falls back to direct file scanning automatically — the search still runs, just without the speed benefit of the index.

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
- **Search suites** — range filters are fully preserved in saved searches and restored when suites run. Enter ranges in the GUI's Range field before clicking **Save Search**
- **Settings persistence** — the Range field value is saved to `~/.docsearchrc` when you click **Save Defaults** in Advanced Options, and restored when the GUI opens or when you click Restore Settings

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

## Files Created by docsearch

docsearch creates several types of files during normal operation. Understanding what each file is, where it lives, and how to manage it helps you keep your folders clean and troubleshoot issues.

**Important:** docsearch never modifies, moves, or deletes your original documents. All files listed below are created by docsearch itself.

### Search reports

These are your search results. They are overwritten each time you run a new search (unless you use `-s` to save or `--timestamp` to add a timestamp).

| File | Purpose | Location |
|------|---------|----------|
| `docsearch_results.txt` | Plain text report with `**highlighted**` matches | Search folder (or `--output-dir`) |
| `docsearch_results.docx` | Word report with yellow-highlighted matches | Search folder (or `--output-dir`) |
| `docsearch_results.csv` | Spreadsheet format (optional, with `-o csv`) | Search folder (or `--output-dir`) |
| `docsearch_results.json` | Machine-readable format (optional, with `-o json`) | Search folder (or `--output-dir`) |

**Protected from searching:** Yes — these filenames are explicitly excluded so docsearch never searches its own reports.
**How to delete:** Delete them manually at any time. They are recreated on the next search.

### Saved and accumulated reports

Created when you use `-s` (save) or `-sa` (append) to archive results with a name you choose.

| File | Purpose | Location |
|------|---------|----------|
| `DO_NOT_SEARCH_{name}.txt` | Named archive of search results (text) | Search folder (or `--output-dir`) |
| `DO_NOT_SEARCH_{name}.docx` | Named archive of search results (Word) | Search folder (or `--output-dir`) |
| `DO_NOT_SEARCH_ACCUMULATED_{name}.txt` | Accumulated results from multiple searches (text) | Search folder (or `--output-dir`) |
| `DO_NOT_SEARCH_ACCUMULATED_{name}.docx` | Accumulated results from multiple searches (Word) | Search folder (or `--output-dir`) |

**Protected from searching:** Yes — the `DO_NOT_SEARCH_` prefix ensures these are never included in future searches.
**How to delete:** Delete them manually at any time. Use the **Clean Up Suite Files** button in the suites panel to bulk-delete suite-related files.

### Suite stage reports

Created automatically during suite runs. Each search in the suite gets its own timestamped report files.

| File | Purpose | Location |
|------|---------|----------|
| `DO_NOT_SEARCH_SUITE_{suite}_stage{NN}_{search}_{timestamp}.txt` | Individual stage text results | Suite output dir (or search folder) |
| `DO_NOT_SEARCH_SUITE_{suite}_stage{NN}_{search}_{timestamp}.docx` | Individual stage Word results | Suite output dir (or search folder) |
| `DO_NOT_SEARCH_SUITE_{suite}_stage{NN}_{search}_{timestamp}.csv` | Individual stage CSV results (if CSV output enabled) | Suite output dir (or search folder) |
| `DO_NOT_SEARCH_SUITE_{suite}_stage{NN}_{search}_{timestamp}.json` | Individual stage JSON results (if JSON output enabled) | Suite output dir (or search folder) |

**Protected from searching:** Yes — `DO_NOT_SEARCH_` prefix.
**How to delete:** Click **Clean Up Suite Files** in the suites panel, or delete manually. Previous run's stage files are automatically cleaned up before each new suite run.

### Suite summary reports

Created automatically when a suite run completes (manual or scheduled).

| File | Purpose | Location |
|------|---------|----------|
| `DO_NOT_SEARCH_docsearch_suite_{name}_{timestamp}.docx` | Formatted Word report with color-coded pass/fail table, stage details, fingerprint, and source file manifest | Suite output dir (or search folder) |
| `DO_NOT_SEARCH_docsearch_suite_{name}_{timestamp}.txt` | Plain text summary | Suite output dir (or search folder) |
| `DO_NOT_SEARCH_docsearch_suite_{name}_{timestamp}.json` | Machine-readable summary | Suite output dir (or search folder) |

**Protected from searching:** Yes — `DO_NOT_SEARCH_` prefix.
**How to delete:** Click **Clean Up Suite Files** in the suites panel, or delete manually. Each run creates new timestamped files, so old reports accumulate unless cleaned up.

### Auto-run log

A persistent, append-only history of all scheduled suite runs.

| File | Purpose | Location |
|------|---------|----------|
| `DO_NOT_SEARCH_autorun_log.txt` | Timestamped log of every auto-run with pass/fail summary | Suite output dir (or search folder) |

**Protected from searching:** Yes — `DO_NOT_SEARCH_` prefix.
**How to delete:** Click **Clear Auto-Run History** in the suites panel. The file is automatically recreated on the next scheduled run.

### Error log

An append-only log of file processing errors and crash reports.

| File | Purpose | Location |
|------|---------|----------|
| `docsearch_errors.log` | Records files that couldn't be read (permission denied, corrupted, locked) and crash diagnostics | Search folder (or `--output-dir`) |

**Protected from searching:** Yes — this filename is explicitly excluded.
**How to delete:** Click **Clear Error Log** on the bottom toolbar, or delete manually. The file is automatically recreated the next time a file error occurs. If docsearch runs cleanly with no errors, no error log is created.

### Search index

An optional SQLite database that stores extracted text for faster repeated searches.

| File | Purpose | Location |
|------|---------|----------|
| `.docsearch.db` | SQLite FTS5 full-text search index | Search folder |
| `.docsearch.db-wal` | Write-Ahead Log (temporary, for concurrent access) | Search folder |
| `.docsearch.db-shm` | Shared memory file (temporary, for concurrent access) | Search folder |

**Protected from searching:** Yes — excluded by filename.
**How to delete:** Use `docsearch --index-clear` or the **Delete Index(es)** button in the GUI. This removes all three files. The index can be rebuilt at any time with `docsearch --index`. The `-wal` and `-shm` files are created and removed automatically by SQLite — if they persist after a crash, they are safe to delete manually.
**How to recover:** If the index becomes corrupted, docsearch detects it automatically, deletes it, and falls back to direct file scanning. Rebuild with `docsearch --index`.

### Collection file

Stores your saved searches and suite definitions for each folder.

| File | Purpose | Location |
|------|---------|----------|
| `.docsearch_collection.json` | Saved searches, suite definitions, pass criteria, schedules | Each search folder |

**Protected from searching:** Yes — excluded by filename.
**Caution:** This file contains all your saved searches and suite definitions for the folder. **Do not delete it unless you intend to lose all your suites.** If you spent time building compliance suites with pass/fail criteria and scheduling, deleting this file erases all of that work. There is no undo — you would need to recreate every saved search and every suite from scratch in the GUI.
**How to back up:** Copy the file to a safe location. It's a standard JSON file that can be viewed in any text editor. Consider backing it up before major changes.

### Configuration file

Your saved default settings.

| File | Purpose | Location |
|------|---------|----------|
| `~/.docsearchrc` | Default values for all CLI flags and GUI settings, plus email alert configuration | Home directory (`~` = `/Users/you` on Mac, `C:\Users\you` on Windows, `/home/you` on Linux) |

**What does "rc" mean?** The "rc" in `.docsearchrc` stands for "run commands" — a naming convention from Unix in the 1960s. Files ending in `rc` (like `.bashrc`, `.vimrc`, `.docsearchrc`) contain startup configuration that's loaded when the program runs. It simply means "config file."

**Protected from searching:** Yes — located in your home directory, not in any search folder. Also excluded by filename if it happens to be in a search folder.
**How to delete:** Delete it to reset all settings to defaults. You can also click **Reset** in Advanced Options and then **Save Defaults** to overwrite it with defaults. Use **Inspect .docsearchrc** in Advanced Options to view its current contents.
**What happens if it's deleted?** docsearch runs normally using built-in defaults. Nothing breaks — you just lose your customized settings.
**How to recover:**
1. Open the GUI (`docsearch-gui`)
2. Open **Advanced Options** and configure your preferred settings (recursive, file types, cores, max matches, etc.)
3. Click **Save Defaults** — this recreates the file
4. If you had email alerts configured, click **Configure Email Alerts** in the Search Suites panel and re-enter your SMTP settings
5. Change the **Text Size** dropdown if you had a non-default size — it auto-saves immediately

The file is a plain text list of key-value pairs. You can also recreate it from the terminal: `docsearch --config recursive=true` saves a single setting, and each subsequent `--config` call adds to it.

### Summary

| Category | File count | Auto-excluded from searches | Can safely delete |
|----------|-----------|----------------------------|-------------------|
| Search reports | 2-4 per search | Yes | Yes — recreated on next search |
| Saved/accumulated reports | 2 per save | Yes | Yes — user's choice |
| Suite stage reports | 2-4 per stage per run | Yes | Yes — auto-cleaned before next run |
| Suite summary reports | 3 per run | Yes | Yes — use Clean Up Suite Files |
| Auto-run log | 1 per folder | Yes | Yes — use Clear Auto-Run History |
| Error log | 0-1 per folder | Yes | Yes — use Clear Error Log |
| Search index | 1-3 per folder | Yes | Yes — use Delete Index or --index-clear |
| Collection file | 1 per folder | Yes | **No** — contains your saved searches and suites. Back up before deleting |
| Config file | 1 (home dir) | N/A | With caution — loses saved settings and email config |

**Most of these files are safe to delete** — docsearch recreates reports, logs, and indexes automatically. The two exceptions are the **collection file** (`.docsearch_collection.json`), which contains your saved searches and suites, and the **config file** (`~/.docsearchrc`), which contains your settings and email configuration. Deleting either of these means recreating that work from scratch. Everything else can be deleted freely.

## Limits and Constraints

docsearch has very few hard limits. Most constraints are system-dependent (available memory, disk space, OS file descriptor limits) rather than imposed by docsearch itself.

**Configurable limits:**

| Limit | Default | Flag | Notes |
|-------|---------|------|-------|
| **Max matches in reports** | 1,000 | `-m N` | Caps the number of matches written to report files. The total match count is always reported accurately in the summary — only the report files are capped. Set `-m 0` for unlimited. Set permanently with `--config` (see below) |

**Setting permanent defaults with `--config`:** The `--config` flag saves a setting to a configuration file (`~/.docsearchrc`) so it applies automatically every time you run docsearch — you don't have to type the flag on every search. For example, if you always want a higher match cap:

```bash
docsearch --config max_matches=5000     # save the setting once
docsearch budget                         # all future searches use max_matches=5000
```

You can still override a saved setting on any individual search by passing the flag directly:

```bash
docsearch -m 0 budget                    # this search only: unlimited matches (overrides saved 5000)
```

To see all your saved settings: `docsearch --config`. To reset a setting to its default: `docsearch --config max_matches=`. The `--config` flag works for many settings — see the [Saved Settings](#saved-settings-optional) section for the full list.
| **CPU cores used** | Half of available | `-c N` | Balances search speed with keeping your machine responsive. Use `-c 1` for minimal resource usage or `-c` with your full core count for maximum speed |
| **Fuzzy match threshold** | 80 (out of 100) | — | Minimum similarity score for fuzzy matching (`-z`). Words scoring below 80% similarity are not considered matches. Not user-configurable |

**No limits on:**

| Item | Notes |
|------|-------|
| **File size** | docsearch processes whatever the underlying libraries (PyMuPDF, openpyxl, python-docx, etc.) can handle. There is no hardcoded maximum. Very large files (multi-GB PDFs, spreadsheets with millions of rows) may cause high memory usage — use `-c 1` to reduce memory consumption |
| **Number of files** | No maximum. The only constraint is the operating system's file descriptor limit, which defaults to 256 on macOS and 1024 on Linux. Increase with `ulimit -n 4096` if needed. See the Troubleshooting section for details |
| **PDF page count** | PDFs are processed page by page with no page count limit |
| **Excel rows and sheets** | No maximum. openpyxl processes worksheets in read-only mode for memory efficiency |
| **Number of search terms** | No maximum — you can provide as many terms as needed |
| **Index database size** | No maximum. The index grows proportionally to the amount of text in your documents (typically 10–20% of original file sizes) |
| **Number of saved searches or suites** | No maximum per folder |

**System-dependent constraints:**

| Constraint | What happens | How to fix |
|------------|-------------|------------|
| **Memory** | Very large files, or many files searched in parallel across multiple cores, can exhaust available RAM. docsearch catches `MemoryError` and suggests reducing cores or limiting file types | Use `-c 1` to search single-threaded, or `-t` to limit file types |
| **Open files limit** | Searching thousands of files may exceed the OS file descriptor limit, causing "Too many open files" errors | Run `ulimit -n 4096` before searching. See Troubleshooting |
| **Disk space** | docsearch checks available disk space before writing reports. If free space is below 10 MB, it warns and skips report generation | Free disk space, or use `--output-dir` to write reports to a different drive |
| **Path length (Windows)** | Windows has a default 260-character path limit. Deeply nested folders with long filenames may cause files to be silently skipped | Enable long paths in Windows. See Troubleshooting |
| **SQLite lock timeout** | If another process holds the index database lock, docsearch waits up to 10 seconds before falling back to direct file scanning | Close other docsearch instances, or delete stale lock files. See Troubleshooting |

## Your First Advanced Search — Step by Step

You know how to do a basic search — type a word, click Run Search, see results. This section walks you through the most useful advanced features one at a time. Each example is a complete walkthrough: what to type, what to check, and what you'll see.

All of these use the GUI. Open `docsearch-gui`, click **Browse** to select a folder with some documents, and follow along.

### Example 1: Find Social Security numbers with regex

**Goal:** Find any document containing a Social Security number (format: 123-45-6789).

1. Open **Advanced Options** and check the **Regex** checkbox
2. In the **Search Terms** field, type: `\d{3}-\d{2}-\d{4}`
   - This is a regex pattern: `\d` means "any digit" and `{3}` means "exactly 3 of them"
   - You don't need to memorize regex — click the **Wizard** button next to the search box for a list of pre-built patterns you can insert with one click
3. Click **Run Search**
4. Look at the results preview:
   - Each match shows the filename, line number, and the actual SSN found, highlighted in yellow
   - If no matches appear, your documents don't contain SSNs — that's good
5. Open **Advanced Options** and uncheck **Regex** when you're done

**Tip:** The Wizard button has patterns for phone numbers, email addresses, dates, dollar amounts, ZIP codes, and more. You don't need to know regex to use them.

### Example 2: Find misspelled words with fuzzy matching

**Goal:** Find documents containing "compliance" even if it's misspelled (common in scanned/OCR documents).

1. Open **Advanced Options** and check the **Fuzzy** checkbox
2. In the **Search Terms** field, type: `compliance`
3. Click **Run Search**
4. Look at the results preview:
   - You'll see matches for "compliance" (exact) but also "complience", "compliancce", "comp1iance" (OCR error), and other approximate matches
   - Fuzzy matching uses a similarity score — words that are at least 80% similar to your search term are considered matches
5. Uncheck **Fuzzy** when you're done

**When to use this:** Searching documents that were scanned (OCR introduces errors), documents written by non-native English speakers, or any collection where spelling is inconsistent.

### Example 3: Find dollar amounts in a specific range

**Goal:** Find documents mentioning dollar amounts between $10,000 and $50,000.

1. In the **Search Terms** field, type: `payment` (or any related keyword, or leave it empty for a range-only search)
2. Open **Advanced Options** and find the **Range** field
3. In the Range field, type: `amount:10000..50000`
   - This tells docsearch: "only show matches where a dollar amount between 10,000 and 50,000 appears on the same line"
4. Click **Run Search**
5. Look at the results preview:
   - Each match shows a line containing both your keyword and a dollar amount in the specified range
   - Dollar amounts outside the range (like $500 or $100,000) are filtered out

**Other range types you can try:**
- `date:2025-01-01..2025-12-31` — dates in 2025
- `percent:5..15` — percentages between 5% and 15%
- `age:18..65` — ages between 18 and 65
- `amount:10000..` — amounts of $10,000 or more (open-ended)

### Example 4: Find files missing required content with inverse search

**Goal:** Find which contracts are missing an "Authorized Signature" line.

1. In the **Search Terms** field, type: `Authorized Signature`
2. Open **Advanced Options** and check the **Inverse** checkbox
   - Normal search finds files WITH your terms. Inverse flips it — it finds files WITHOUT your terms
3. Click **Run Search**
4. Look at the results preview:
   - Instead of showing matches, it lists every file that does NOT contain "Authorized Signature"
   - These are the files that need attention
   - If the list is empty (0 matches), every file contains the required text
5. Uncheck **Inverse** when you're done

**Why this matters:** This is one of the most powerful features for compliance. Instead of searching for problems, you're verifying that requirements are met — and the report lists exactly which files fail.

### Example 5: Find words near each other with proximity search

**Goal:** Find documents where "breach" and "contract" appear within 5 words of each other (not just anywhere in the same file).

1. In the **Search Terms** field, type: `breach contract`
2. Open **Advanced Options** and find the **Proximity** field
3. In the Proximity field, type: `5`
   - This means both words must appear within 5 words of each other on the same line
   - AND mode is applied automatically when you use proximity
4. Click **Run Search**
5. Look at the results preview:
   - You'll only see matches where "breach" and "contract" are close together — like "breach of contract" or "contract breach notification"
   - Lines where both words appear far apart (like "The contract was signed in January. The breach occurred in March.") are excluded
6. Clear the Proximity field when you're done

### Example 6: Search only specific file types

**Goal:** Search only PDFs and Word documents, ignoring everything else.

1. In the **Search Terms** field, type your search term
2. Open **Advanced Options** and find the **File types** field
3. In the File types field, type: `pdf,docx`
   - No dots, no spaces — just the extensions separated by commas
   - Other file types in the folder are ignored
4. Click **Run Search**

**Common combinations:**
- `pdf,docx,doc` — all Word and PDF documents
- `xlsx,xls,csv` — all spreadsheet formats
- `eml,msg,pst` — all email formats
- `txt,md,log` — all plain text formats

### Example 7: Combine multiple features together

**Goal:** Find SSNs in PDF files across all subfolders, showing 2 lines of context before and after each match.

1. In the **Search Terms** field, type: `\d{3}-\d{2}-\d{4}`
2. Open **Advanced Options** and set:
   - Check **Regex**
   - Check **Recursive** (searches subfolders)
   - **File types:** `pdf`
   - **Lines Before:** `2`
   - **Lines After:** `2`
3. Click **Run Search**
4. The results show each SSN match with 2 lines above and below for context, from PDF files only, across all subfolders

**You can mix and match almost any combination of features.** The main restrictions:
- Regex and Fuzzy can't be used together
- Regex and Wildcard can't be used together
- Fuzzy and Wildcard can't be used together
- Expression mode replaces AND mode, Exclude, and Proximity (use AND/OR/NOT in the expression instead)

### What's next?

Now that you're comfortable with individual advanced searches, you can:
- **Save searches for reuse** — click **Save Search** to name and store any search you've configured
- **Build compliance suites** — group saved searches into suites with pass/fail criteria (see below)
- **Read the [Compliance Guide](COMPLIANCE_GUIDE.md)** for 9 industry-specific audit examples

---

## Search Suites

Search suites let you save individual searches, group them into named suites, and run them as a batch with pass/fail tracking. This turns docsearch into an audit automation tool — run the same compliance checks repeatedly and get a report showing which checks passed and which failed.

**Before you start:** Suites are built from saved searches. A saved search is just a regular search that you've given a name so you can reuse it. Before saving a search, always **run it first** to verify it finds what you expect. If a search doesn't produce the right results as a standalone search, it won't produce the right results inside a suite either. Think of it like writing a recipe — test each step before combining them.

**Want a real-world compliance example?** The [Compliance Guide](COMPLIANCE_GUIDE.md) walks through building a full contract review suite with 5 checks across 9 industries, including which search modes to use, what pass criteria to set, and what the results mean. If you're building suites for auditing or compliance, read that guide alongside this one.

### Your First Suite — Step by Step

This walkthrough creates a simple 2-check compliance suite that verifies every document has an authorized signature and no documents contain the word "DRAFT." Follow along with any folder containing a few test documents.

**1. Open the GUI and select a folder**

Run `docsearch-gui`. Click the **Browse** button next to the Search Folder field and navigate to the folder containing your documents.

**2. Create your first saved search: "has_signature"**

This search checks that every file contains "Authorized Signature."

- In the **Search Terms** field, type: `Authorized Signature`
- Open **Advanced Options** and check the **Inverse** checkbox (this flips the search — instead of finding files WITH the term, it finds files WITHOUT it)
- Click **Run Search** to test it first. Look at the results preview:
  - If some files are missing the signature, they'll be listed — that means the search is working correctly
  - If all files have it, you'll see "0 matches" — that's also correct, it means every file passed
  - If the results don't look right, adjust your search terms before saving
- Once you're satisfied the search finds what you want, click **Save Search** in the Search Bar
- When prompted for a name, type: `has_signature`
- Click OK

**3. Create your second saved search: "no_draft"**

This search checks that no file contains "DRAFT."

- Clear the search box and type: `DRAFT`
- Open **Advanced Options** and **uncheck** Inverse (you want to find files that DO contain DRAFT)
- Click **Run Search** to test it first. Look at the results preview:
  - If any files contain DRAFT, they'll appear — the search is working
  - If no files contain DRAFT, you'll see "0 matches" — also correct
  - This is the result you want to see inside the suite later
- Once you're satisfied, click **Save Search** in the Search Bar
- Name it: `no_draft`
- Click OK

**4. Build the suite**

- Click **Search Suites** (on the same row as Advanced Options) to open the suites window
- Click **Build a New Suite**
- Name it: `my_first_suite`
- In the left panel, you'll see your two saved searches: `has_signature` and `no_draft`
- Click `has_signature`, then click the **→** button to add it to the right panel
- Click `no_draft`, then click **→** to add it too
- Now set the pass criteria for each search:
  - Select `has_signature` in the right panel. Set the criteria dropdown to **==** and the number to **0** (meaning: pass if zero files are missing the signature)
  - Select `no_draft` in the right panel. Set the criteria dropdown to **==** and the number to **0** (meaning: pass if zero files contain DRAFT)
- Click **Create**

**5. Run the suite**

- Select `my_first_suite` in the Suites list
- Click **Run Selected Suite**
- Watch the status label — it shows each search running in sequence
- When finished, you'll see "Done in Xs — PASSED" or "Done in Xs — FAILED"
- Click **View Suite Report** to open the `.docx` report with color-coded pass/fail results

**6. Understand the results**

- If both checks show **PASS** (green): every file has a signature and no file contains DRAFT
- If `has_signature` shows **FAIL** (red): some files are missing "Authorized Signature" — open the stage report to see which ones
- If `no_draft` shows **FAIL** (red): some files contain "DRAFT" — open the stage report to see which ones

You now have a reusable compliance suite. Run it again anytime — same folder, same checks, one click. Add more searches to the suite as needed by clicking **Edit Suite**.

For a more detailed compliance walkthrough with 9 industry examples, see the [Compliance Guide](COMPLIANCE_GUIDE.md).

---

**How it works (reference):**

1. **Save a search:** Configure a search in the GUI (terms, flags, options), then click the **Save Search** button in the Search Bar. Give it a unique name (e.g., "missing_disclaimer"). The search and all its settings are saved to `.docsearch_collection.json` in the search folder.

2. **Build a suite:** Click **▶ Search Suites** (below Advanced Options) to open the suites window. Click **Build a New Suite**, give it a name (e.g., "quarterly_compliance"), and use the dual-panel selector to choose and order your searches. The left panel shows available saved searches; use the **→** button (or double-click) to add them to the right panel, which represents execution order. Use the **▲ Up** and **▼ Down** buttons to reorder. Click **Create**.

3. **Run the suite:** Select one or more suites from the **Suites** list and click **Run Selected Suite**. Each search runs sequentially against the folder — its settings are loaded into the main GUI as it runs so you can see what's happening. Results appear in real-time with color-coded PASS/FAIL indicators. When multiple suites are selected, their searches are combined (deduplicated) and run together.

4. **Reports:** Suite report files are automatically generated with timestamps in three formats: `.docx`, `.txt`, and `.json` (e.g., `DO_NOT_SEARCH_docsearch_suite_{name}_{timestamp}.docx`). The `.docx` report is a formatted Word document with a color-coded summary table (green PASS / red FAIL), per-stage details with search criteria, a report fingerprint for audit traceability, and the docsearch version used. Each report includes each test's name, search terms, result, and an overall PASSED/FAILED verdict. After a suite run completes, a **View Suite Report** button appears in the suite panel — click it to open the `.docx` report directly.

**How the collection file works:** When you save a search or build a suite, docsearch stores everything in a file called `.docsearch_collection.json` inside the search folder. Here is the full lifecycle of this file:

1. **Created automatically** — the first time you click **Save Search** in the Search Bar for a folder, docsearch creates `.docsearch_collection.json` in that folder. You don't create it manually.
2. **One per folder** — each folder has its own collection file. When you browse to a different folder in the GUI, docsearch loads that folder's collection. If no collection file exists yet, the suites panel is empty.
3. **Lives with your documents** — the collection file is stored inside the search folder alongside the documents it searches, not in a central location. This means if you copy or move a folder, the saved searches and suites travel with it.
4. **Contains saved searches + suites** — inside the file are two things: your saved searches (each with a name and all its settings — terms, flags, file types, range filters, etc.) and your suites (each with a name, an ordered list of searches, pass/fail criteria, cascade setting, and schedule). All of this is managed through the GUI — you never need to edit the file directly.
5. **Updated by the GUI** — every time you save a search, build/edit/delete a suite, change pass criteria, or set a schedule, the GUI writes the changes to this file immediately.
6. **Read on folder change** — when you browse to a folder or open the suites window, the GUI reads the collection file and populates the saved searches list and suites list from it.
7. **Do not delete it** — this file represents all the work you put into building searches and suites. Deleting it erases all of that with no undo. If you need to start fresh, delete individual searches or suites through the GUI instead.
8. **Back it up** — it's a standard JSON text file. Copy it to a safe location before making major changes. You can view its contents in any text editor.

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

**Boolean expression searches in suites:** Saved searches fully support expression mode. Toggle the **Expression** checkbox, enter your boolean expression (e.g., `(budget OR revenue) AND NOT draft`), and click **Save Search** — the expression flag and query are preserved. When the suite runs that search, it uses the same boolean logic. This makes it easy to build compliance suites with complex conditions like "must contain (signature AND date) but NOT draft".

**Range queries in suites:** Saved searches fully preserve range filters. Enter your range specs in the **Range** field (e.g., `amount:1000..5000, date:2024-01-01..2024-12-31`), configure your text search terms (or leave empty for range-only), and click **Save Search**. When the suite runs that search, the same range filters are applied. Range filters also work with expressions in suites — for example, save a search with expression `budget AND amount:1000..5000` and it will be restored exactly when the suite runs.

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

When a scheduled run completes, three things happen automatically:

1. **Suite reports are generated** — `DO_NOT_SEARCH_docsearch_suite_{name}_{timestamp}.docx`, `.txt`, and `.json` are created with full results (always timestamped to avoid overwriting previous runs). The `.docx` report includes a color-coded summary table and per-stage details.
2. **An auto-run log entry is appended** — `DO_NOT_SEARCH_autorun_log.txt` records each run with a summary and per-search pass/fail details:
   ```
   [2026-03-28 14:30:00] Suite: quarterly_compliance — 4/5 passed — FAILED
     [PASS] find_contracts — 12 match(es) (need >= 1)
     [FAIL] no_pii — 2 match(es) (need == 0)
   ```
3. **An email alert is sent** (if configured) — docsearch sends a notification email with the suite name, pass/fail summary, per-test details, and a reference to the .docx report file. By default, alerts are sent only when a suite has FAIL results — you can change this to "always" or "off."

Both report files are written to the suite's **Output Dir** if set, otherwise to the search folder. The `DO_NOT_SEARCH` prefix ensures they are never re-searched. Click **Open Auto-Run History** in the suite panel to open the log file directly. If the log file is deleted, it is automatically recreated on the next auto-run.

**Email Alerts (optional):** Click **Configure Email Alerts** in the suite panel to set up email notifications. To send email, docsearch needs to connect to an **SMTP server** — this is the outgoing mail server that your email provider operates for sending messages. Every email provider has one: Gmail's is `smtp.gmail.com`, Outlook's is `smtp.office365.com`, and corporate email systems have their own (ask your IT department). The **SMTP port** is the door number on that server — port `587` is the standard for secure email sending and works with Gmail, Outlook, and most providers. You don't need to understand the technical details; just enter the values from the table below and click **Send Test Email** to verify it works.

| Field | Description | Example |
|-------|-------------|---------|
| SMTP Server | Your email provider's outgoing mail server | `smtp.gmail.com` or `smtp.office365.com` |
| SMTP Port | The port number for the mail server (587 works for most providers) | `587` |
| Username | Your own email address — the account docsearch will send alerts from | `you@gmail.com` |
| Password | The app password for that email account (not your regular login password — see below) | — |
| From Address | The "From" line on the alert email (defaults to your username if left blank) | `you@gmail.com` |
| To Address | The email address that receives the alerts — your own address, your manager's, or a team distribution list | `compliance-team@company.com` |
| Send alerts | `failure` = only on FAIL results, `always` = every auto-run, `off` = disabled | `failure` |

**Password notes:** Most email providers no longer allow your regular password for SMTP. Instead, you need to generate an **app password** — a special one-time password specifically for applications like docsearch. For Gmail: go to myaccount.google.com → Security → 2-Step Verification → App passwords, and generate one for "Mail." For Outlook/Microsoft 365: go to account.microsoft.com → Security → App passwords. For corporate email: ask your IT department for SMTP credentials or an app password.

**Quick setup for common providers:**

| Provider | SMTP Server | Port | Notes |
|----------|-------------|------|-------|
| Gmail | `smtp.gmail.com` | `587` | Requires app password (2-Step Verification must be enabled) |
| Outlook / Microsoft 365 | `smtp.office365.com` | `587` | Requires app password |
| Yahoo Mail | `smtp.mail.yahoo.com` | `587` | Requires app password |
| Corporate / on-premises | Ask your IT department | Usually `587` or `25` | May not require authentication on internal networks |

Click **Send Test Email** to verify your settings before saving. Settings are stored in `~/.docsearchrc`. Email alerts are completely optional — if no SMTP server is configured, no emails are sent. docsearch never modifies your documents; email alerts are outbound notifications about search results only.

**Output Directory:** The suite panel has its own **Output Dir** field with a Browse button. When set, all suite-generated files (stage reports, suite reports, auto-run logs) are written there instead of the search folder. This setting is automatically saved to `~/.docsearchrc` when you close the Suites window and restored on next launch.

**Storage:** Each folder has its own collection file (`.docsearch_collection.json`). When you switch folders, the Search Suites window automatically refreshes to show that folder's collection. Suite schedules and last-run timestamps are stored per-suite in this file.

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
