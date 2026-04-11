# docsearch

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](docs/USER_GUIDE.md)

> Search Word docs, PDFs, spreadsheets, emails, archives, and more — 46 file types, all at once, all offline. No uploads, no cloud, no subscriptions. Everything stays on your computer. Free, open-source. Windows/Mac/Linux.
>
> **For home users and small businesses:** **Do you know what's hiding in your documents?** One click scans your files for Social Security numbers, credit cards, tax IDs, passwords, and other sensitive data — with a highlighted report showing exactly where. Search years of personal documents, Google Docs backups, tax records, contracts, and correspondence using plain keywords, regex, Boolean logic, fuzzy matching, wildcards, or range queries. Results come with every match highlighted in yellow.
>
> **For compliance, audit, and legal teams:** **Can you prove you checked every document?** Build search suites that verify 500 contracts all contain a required clause, flag any file still marked DRAFT, detect SSNs that shouldn't be there, and confirm dollar amounts fall within expected ranges — then run those checks on a schedule with pass/fail reports, highlighted evidence, and email alerts on failure. Auditors get a Word report documenting exactly what was searched, what passed, what failed, and which files were in scope. Includes starter templates for 9 industries. docsearch is a search tool, not compliance software — the checks you build and the conclusions you draw are yours.
>
> Terminal, GUI, or Python API. From a home user scanning personal files for PII to an auditor reviewing 500 contracts, it just works.

**[See docsearch in action →](https://robertdschoening.com/docsearch)**

## Who Is It For?

docsearch scales from simple keyword searches to organized document review workflows — use as much or as little as you need:

- **Home users** — search years of personal documents, Google Docs backups, tax records, family files. Type a keyword, click Run Search, done. No setup, no configuration. Click **PII Scan** to check your personal files for Social Security numbers, credit cards, tax IDs, and other sensitive data hiding in your documents — one click, no setup
- **Small businesses** — find information across contracts, invoices, reports, and correspondence. Use AND mode, file type filters, exclude terms, and range queries to narrow results. Save searches for reuse
- **Compliance & audit workflows** — create search suites to help review documents for required language, flag prohibited content, detect PII (Personally Identifiable Information), and check that dollar amounts fall within expected ranges. Run suites on a schedule with pass/fail reports and email alerts. The Compliance Wizard provides starter templates for common industries — SOX (Sarbanes-Oxley), HIPAA (Health Insurance Portability and Accountability Act), Legal, Government, ISO (International Organization for Standardization), FERPA (Family Educational Rights and Privacy Act), Real Estate, Insurance, HR (Human Resources) — customize to fit your needs
- **Legal** — search contracts for required clauses, find privileged documents, pre-litigation review
- **Healthcare** — search patient records for PII, help organize HIPAA-related document reviews
- **Finance** — search financial documents for SOX-related terms, transaction monitoring, range queries on dollar amounts
- **HR (Human Resources)** — verify employee files have required documents, detect SSNs (Social Security Numbers) on shared drives
- **Research** — search across papers, notes, and datasets in any format

## Features

- **Sensitive Data Scan** — one-click scan for PII and sensitive data: SSNs, credit cards, tax IDs, emails, phone numbers, passwords, dates of birth, and large dollar amounts. Results are categorized by severity (high/moderate/info) with per-file details and a highlighted `.docx` report
- **Offline and private** — your documents never leave your computer. No cloud, no uploads, no subscriptions
- **46 file types** — Word, PDF, Excel, PowerPoint, emails (.eml, .msg, .pst, .mbox), archives (.zip, .7z, .rar), Apple Pages, calendars (.ics), contacts (.vcf), e-books, HTML, and 30+ more
- **Highlighted reports** — results saved to `.docx` and `.pdf` with yellow-highlighted matches, `.txt` with full context, and optional CSV and JSON output
- **Results preview** — see matches inline in the GUI with highlighted terms; right-click to copy, double-click a filename to open it. Matched files popup shows line numbers and includes a "View Text" option that displays the file's extracted content with line numbers and highlighted matches
- **Recent searches** — dropdown next to the search bar remembers your last 10 searches
- **Compliance Wizard** — pick an industry starter template, customize checks, create a search suite in one click
- **Search suites** — save searches, group into suites, run with pass/fail criteria and scheduled auto-runs. Import custom templates from `.json` files to add new suites
- **Email alerts** — get notified when scheduled suites detect failures
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

Your saved searches, suites, settings, indexes, and reports are stored outside the docsearch installation — in your home directory and your document folders. Upgrading replaces only the code. Nothing else is touched.

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

Open **Advanced Search Options** for regex, fuzzy, Boolean, range queries, and all other settings. Use the **Search Wizard** for guided search configuration, or the **Compliance Wizard** to create a search suite from 9 industry starter templates (Financial/SOX, Healthcare/HIPAA, Legal, Government, Manufacturing/ISO, Education/FERPA, Real Estate, Insurance, HR) — customize to fit your needs.

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
| [User Guide](docs/USER_GUIDE.md) | Complete reference — GUI, CLI flags, search modes, indexing, suites, file reference |
| [Compliance Guide](docs/COMPLIANCE_GUIDE.md) | Using docsearch for document review workflows — industry examples, sample suites, step-by-step setup |
| [API Reference](docs/API.md) | Python library API — `search()` function, parameters, return values |
| [FAQ & Troubleshooting](docs/TROUBLESHOOTING.md) | Common questions and solutions for Windows, macOS, and Linux |
| [Changelog](CHANGELOG.md) | Version history and release notes |
| [Contributing](CONTRIBUTING.md) | How to report bugs, suggest features, and submit code |

## Why docsearch?

Most document search tools find text inside files. docsearch does that too — but it also helps you **prove what's in your documents and what's missing**. No other free tool lets you:

- Save a search, reuse it tomorrow, and get the same results
- Group searches into suites that run as a batch with pass/fail verdicts
- Detect files that are **missing** required content (inverse search)
- Filter matches by dollar amount, date range, or percentage
- Generate a highlighted Word report documenting what was searched and found
- Schedule checks to run automatically with email alerts on failure
- Start with industry-specific search templates and customize to fit your needs (Compliance Wizard)

If all you need is to find a word in a document, any search tool works. If you need to **systematically verify** that 500 documents meet a set of requirements — and produce evidence that you checked — that's what docsearch was built for.

We call this **verifiable document audit** — the ability to define a set of checks, run them against a collection of documents, and generate a report that proves what was searched, what passed, what failed, and which files were in scope. Other tools search. docsearch searches *and proves it searched*.

docsearch is a search and workflow tool that helps you organize document reviews. It does not certify compliance or provide legal advice — the checks you build and the conclusions you draw are yours.

## What You Get at Each Price Point

| Feature | docsearch (free) | Paid competitors ($29-249/yr) |
|---------|-----------------|-------------------------------|
| File types | 46 | 170+ |
| CLI + GUI + API | All three | GUI only |
| Cross-platform | Win/Mac/Linux | Windows only |
| Highlighted .docx reports | Yes | No |
| Compliance Wizard (9 industries) | Yes | No |
| Search suites with pass/fail | Yes | No |
| Range queries (dates, $, %) | Yes | Limited or none |
| Email alerts | Yes | No |
| OCR (scanned PDFs/images) | Yes | Varies |
| Email search (.eml/.msg/.pst) | Yes | Yes |
| Archive search (.zip/.7z/.rar) | Yes | No |
| Open source | Yes | No |

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

docsearch is a search and reporting tool. It does not provide legal, regulatory, or compliance advice. Templates are document search configurations, not compliance certifications — pass/fail results indicate whether search criteria were met, not whether documents satisfy regulatory requirements. The built-in industry templates are examples of the kinds of checks that tend to come up in each industry; they do not necessarily cover everything needed to be compliant in any given industry, and they are not certified against any specific regulation. Users are solely responsible for determining whether search results meet their specific compliance obligations and for adding, removing, or editing checks to match what their organization actually needs to verify. This software is provided "as is" without warranty of any kind (see [MIT License](LICENSE)).

## License

This project is licensed under the [MIT License](LICENSE).
