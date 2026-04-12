# docsearch

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](docs/USER_GUIDE.md)

> Search Word docs, PDFs, spreadsheets, emails, archives, and more — 46 file types, all at once, all offline. No uploads, no cloud, no subscriptions. Everything stays on your computer. Free, open-source. Windows/Mac/Linux.
>
> **Do you know what's hiding in your documents?** One click scans your files for Social Security numbers, credit cards, tax IDs, passwords, and other sensitive data — with a highlighted report showing exactly where. Search years of personal documents, Google Docs backups, tax records, contracts, and correspondence using plain keywords, regex, Boolean logic, fuzzy matching, wildcards, or range queries. Results come with every match highlighted in yellow.
>
> Terminal, GUI, or Python API. For home users and anyone who wants to see what's in their own files.

**[See docsearch in action →](https://robertdschoening.com/docsearch)**

## Who Is It For?

- **Home users** — search years of personal documents, Google Docs backups, tax records, family files. Type a keyword, click Run Search, done. No setup, no configuration. Click **PII Scan** to check your personal files for Social Security numbers, credit cards, tax IDs, and other sensitive data hiding in your documents — one click, no setup
- **Small businesses** — find information across contracts, invoices, reports, and correspondence. Use AND mode, file type filters, exclude terms, and range queries to narrow results. Save searches by name and reload them later
- **Legal / HR / Finance** — search contracts, employee files, and financial documents privately and offline, with highlighted Word reports you can save and share
- **Research** — search across papers, notes, and datasets in any format

## Features

- **PII Scan** — one-click scan for sensitive data: SSNs, credit cards, tax IDs, emails, phone numbers, passwords, dates of birth, and user-configurable dollar-amount ranges. Results are categorized by severity (high/moderate/info) with per-file details and a highlighted `.docx` report
- **Offline and private** — your documents never leave your computer. No cloud, no uploads, no subscriptions
- **46 file types** — Word, PDF, Excel, PowerPoint, emails (.eml, .msg, .pst, .mbox), archives (.zip, .7z, .rar), Apple Pages, calendars (.ics), contacts (.vcf), e-books, HTML, and 30+ more
- **Highlighted reports** — results saved to `.docx` and `.pdf` with yellow-highlighted matches, `.txt` with full context, and optional CSV and JSON output
- **Results preview** — see matches inline in the GUI with highlighted terms; right-click to copy, double-click a filename to open it. Matched files popup shows line numbers and includes a "View Text" option that displays the file's extracted content with line numbers and highlighted matches
- **Recent searches** — dropdown next to the search bar remembers your last 10 searches
- **Save Search / Load Search** — save a configured search by name and reload it later with one click
- **Search Wizard** — guided search builder with 20+ pre-built patterns (SSN, phone, email, dollar range, and more) — no flags or regex knowledge needed
- **Inverse search** — find files that are *missing* required content
- **Search modes** — plain keywords, AND/OR, Boolean expressions, regex, wildcards, fuzzy matching, whole-word, proximity
- **Range queries** — filter by dollar amounts, dates, percentages, ages, file sizes
- **OCR** — search scanned PDFs and images (requires Tesseract)
- **Three interfaces** — terminal CLI, point-and-click GUI (`docsearch-gui`), Python API
- **Cross-platform** — Windows, macOS, Linux
- **Search index** — optional SQLite FTS5 index for faster repeated searches
- **Read-only** — docsearch never modifies, moves, or deletes your files. It does create its own output files (reports, indexes, settings) and can delete those when you ask (e.g., Clear Results, Delete Index)
- **Safe defaults** — files over 100 MB are automatically skipped to prevent slow searches and memory issues. Very large files (huge PDFs, massive spreadsheets, database exports) can take minutes to parse and may exhaust available memory. Skipped files are logged to `docsearch_errors.log` so you know what was missed. To change the limit, set **Max File Size (MB)** in Advanced Search Options — or set it to 0 for no limit. Changing the limit automatically rebuilds the index on the next search. ZIP archives that would expand to over 500 MB are also skipped to prevent archive bombs
- **Excluded Files view** — after each search, click the **View N excluded file(s)** button to see exactly which files were skipped and why (unsupported type, prior output, oversized, hidden, etc.) — no more guessing why a `find` count differs from docsearch's file count

### Supported File Types

| Category | Formats |
|----------|---------|
| **Documents** | .doc .docx .epub .html .md .odt .pages .pdf .ppt .pptx .rst .rtf .tex |
| **Spreadsheets** | .csv .ods .tsv .xls .xlsx |
| **Email** | .eml .mbox .msg .pst |
| **Archives** | .7z .bz2 .gz .rar .tar .tgz .zip |
| **Calendar/Contacts** | .ics .vcf |
| **Data/Config** | .cfg .ini .json .log .sql .toml .txt .xml .yaml .yml |
| **Images (OCR)** | .bmp .jpg .jpeg .png .tif .tiff (requires `-O` flag) |

## Installation

### Prerequisites

- **Python 3.10+** — check if it's already installed: `python3 --version` (macOS/Linux) or `python --version` (Windows). If not installed, download from [python.org/downloads](https://www.python.org/downloads/)
- **Tkinter** (optional, for GUI) — included on Windows/macOS; Linux: `sudo apt install python3-tk`
- **Tesseract** (optional, for OCR) — macOS: `brew install tesseract` | Windows: [download](https://github.com/UB-Mannheim/tesseract/wiki) | Linux: `sudo apt install tesseract-ocr`

### Option A: Quick Install with pipx (recommended)

First, check if pipx is installed by typing `pipx --version`. If it says "not recognized" or "command not found," install it:

```bash
pip install pipx          # Windows: if pip isn't recognized, use: python -m pip install pipx
pipx ensurepath           # adds pipx to your PATH
```

**Close and reopen your terminal** after running `ensurepath` (it only takes effect in a new window). Then install docsearch:

```bash
pipx install git+https://github.com/exbuf/docsearch.git
```

**Getting a git error?** If you see "do you have git installed," use this instead (downloads as a ZIP — no git required):

```bash
pipx install https://github.com/exbuf/docsearch/archive/refs/heads/main.zip
```

After installation, `docsearch` and `docsearch-gui` work from any terminal, any folder, every time — no activation step needed. This is the easiest way to install.

**Fully isolated.** pipx installs docsearch in its own private environment, completely separate from your system Python and all other programs. It will not install, upgrade, downgrade, or conflict with anything else on your computer. The only change to your system is two new commands (`docsearch` and `docsearch-gui`). To uninstall completely: `pipx uninstall docsearch`. See the [User Guide](docs/USER_GUIDE.md#will-docsearch-affect-my-existing-python-installation) for details.

### Option B: Manual Install (with git)

```bash
git clone https://github.com/exbuf/docsearch.git
cd docsearch
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -e .
```

**Important:** With a manual install, you must activate the virtual environment (`source venv/bin/activate`) every time you open a new terminal. If you see "command not found" when typing `docsearch`, this is why. See the [User Guide](docs/USER_GUIDE.md#which-installation-method-did-you-use) for details and how to switch to pipx.

### Option C: Manual Install (no git, no sign-up)

No git? No problem. Download docsearch as a ZIP file directly from your browser:

1. Go to [github.com/exbuf/docsearch](https://github.com/exbuf/docsearch)
2. Click the green **Code** button
3. Click **Download ZIP**
4. Extract the ZIP file, copy the extracted `docsearch-main` folder and paste it to where you want it
5. Open a terminal and navigate to the extracted folder:

   **Windows:**
   ```cmd
   cd C:\Users\YourName\Downloads\docsearch-main
   python -m venv venv
   venv\Scripts\activate
   pip install -e .
   ```

   **macOS/Linux:**
   ```bash
   cd ~/Downloads/docsearch-main
   python3 -m venv venv
   source venv/bin/activate
   pip install -e .
   ```

**Important:** Same as Option B — you must activate the virtual environment each time you open a new terminal. See the [User Guide](docs/USER_GUIDE.md#which-installation-method-did-you-use) for details.

### Upgrading

Your saved searches, settings, indexes, and reports are stored outside the docsearch installation — in your home directory and your document folders. Upgrading replaces only the code. Nothing else is touched.

- **pipx:** `pipx upgrade docsearch`
- **git:** `cd docsearch && git pull && pip install -e .`
- **ZIP:** download the new ZIP, replace the folder, run `pip install -e .`

See the [User Guide](docs/USER_GUIDE.md#will-docsearch-affect-my-existing-python-installation) for full details on what is and isn't preserved.

## Quick Start

### Terminal

```bash
cd /path/to/your/documents
docsearch budget                      # search for "budget"
docsearch budget revenue              # OR search (any term)
docsearch -a budget revenue           # AND search (both terms)
docsearch -r budget                   # include subfolders
docsearch -t pdf,docx budget          # only PDFs and Word docs
docsearch -x "\d{3}-\d{2}-\d{4}"     # regex (SSN pattern)
docsearch -e "(budget OR revenue) AND NOT draft"   # Boolean expression
docsearch -R amount:1000..5000 budget # range query
```

Results are saved to `docsearch_results.txt` and `docsearch_results.docx` (highlighted). The .docx report opens with whatever word processor you have — Microsoft Word, [LibreOffice](https://www.libreoffice.org/download/download-libreoffice/) (free), Google Docs, or Apple Pages. The .txt report works on any computer with no extra software.

Run `docsearch -h` for the full flag reference with examples.

### GUI

```bash
docsearch-gui
```

1. Click **Browse** to select a folder (or **File** to search a single file)
2. Type your search terms
3. Click **Run Search**
4. View results in the preview pane or click **DOCX** to open the highlighted report

Open **Advanced Search Options** for regex, fuzzy, Boolean, range queries, and all other settings. Use the **Search Wizard** for guided search configuration with 20+ pre-built patterns. Click **PII Scan** to find sensitive data with one click.

**If buttons overlap or text looks too large**, use the **Text Size** dropdown on the bottom-right toolbar to adjust (Normal is recommended).

### Python API

```python
from docsearch import search

result = search(["budget", "revenue"], directory="/path/to/docs")

print(f"Found {len(result.matches)} matches in {len(result.files_searched)} files")
for match in result.matches:
    print(f"  {match.filename}:{match.line_num}: {match.text}")
```

See the [API Reference](docs/API.md) for all parameters and options.

## Documentation

| Document | Description |
|----------|-------------|
| [User Guide](docs/USER_GUIDE.md) | Complete reference — GUI, CLI flags, search modes, indexing, file reference |
| [API Reference](docs/API.md) | Python library API — `search()` function, parameters, return values |
| [FAQ & Troubleshooting](docs/TROUBLESHOOTING.md) | Common questions and solutions for Windows, macOS, and Linux |
| [Changelog](CHANGELOG.md) | Version history and release notes |
| [Contributing](CONTRIBUTING.md) | How to report bugs, suggest features, and submit code |

## Why docsearch?

Most document search tools find text inside files. docsearch does that and more — it also helps you **see what's hiding in your own documents**, privately and offline. No other free tool gives you:

- A one-click PII Scan that finds Social Security numbers, credit cards, passwords, and other sensitive data in your own files, running entirely on your machine with nothing uploaded anywhere
- Highlighted Word reports with every match shown in yellow
- Save Search and Load Search so you can reuse a configured search with one click
- The Search Wizard with 20+ pre-built search patterns for non-technical users
- Range queries that filter by dollar amount, date range, or percentage
- A built-in view that shows exactly which files were skipped and why, so nothing falls through the cracks

If all you need is to find a word in a document, any search tool works. If you want to *see inside your own files* — what's there, what's sensitive, and what you might have forgotten about — that's what docsearch was built for.

## Platform Notes

- **High-DPI displays (4K monitors)** — if buttons overlap or text looks too large, use the **Text Size** dropdown on the bottom-right toolbar to adjust. Normal is recommended for most screens
- **Antivirus software (Windows)** — some antivirus programs flag Python scripts as suspicious. If docsearch is blocked, add your Python installation or the docsearch folder to your antivirus allow list
- **Files locked by other programs (Windows)** — Windows locks files that are open in another program. If docsearch reports "permission denied" on a file, close the program that has it open and search again. Errors are logged to `docsearch_errors.log`
- **Corporate firewalls** — if `pip` or `pipx` can't download packages, use the [ZIP download](#option-c-manual-install-no-git-no-sign-up) installation method instead
- **macOS file picker vs Windows** — on macOS, the file picker includes a preview panel; on Windows, it does not — this is an OS difference, not docsearch

For more, see the [FAQ & Troubleshooting](docs/TROUBLESHOOTING.md).

## Author

Built by [Robert D. Schoening](https://robertdschoening.com) — retired electrical engineer, former IBM engineer, US software patent holder, and solo developer.

## Disclaimer

docsearch is provided as-is under the [MIT License](LICENSE), without warranty of any kind. It is a search and reporting tool and does not provide legal, regulatory, or compliance advice. The PII Scan feature uses regex pattern matching and may produce false positives or miss data that does not match its built-in patterns — always review results in context before making decisions. Users are solely responsible for how they use the tool and interpret its results.

## License

This project is licensed under the [MIT License](LICENSE).
