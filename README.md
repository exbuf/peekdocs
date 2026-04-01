# docsearch

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

> Search Word docs, PDFs, spreadsheets, emails, archives, and 33 other file types — all at once, all offline. Results are saved to a Word report with every match highlighted in yellow and shown with full paragraph context, so you can understand each result without opening the original file.
>
> **Built for compliance and auditing.** Create search suites that check every document for required language, flag prohibited content, detect PII like Social Security numbers, and verify that dollar amounts fall within policy ranges — then run those checks on a schedule with pass/fail reports and email alerts when failures are detected. No other free tool does this.
>
> Also a powerful everyday search tool — use plain keywords, regex, Boolean logic, fuzzy matching, wildcards, proximity search, or range queries. From a home user searching personal files to an auditor reviewing 500 contracts, it just works. Terminal, GUI, or Python API. Free, open-source. Windows/Mac/Linux.

**[See docsearch in action →](https://robertdschoening.com/docsearch)**

## Features

- **42 file types** — Word, PDF, Excel, PowerPoint, emails (.eml, .msg, .pst), archives (.zip, .7z, .rar), e-books, HTML, and 30+ more
- **Search modes** — plain keywords, AND/OR, Boolean expressions, regex, wildcards, fuzzy matching, whole-word, proximity
- **Range queries** — filter by dollar amounts, dates, percentages, ages, file sizes
- **OCR** — search scanned PDFs and images (requires Tesseract)
- **Highlighted reports** — results saved to `.docx` with yellow-highlighted matches and `.txt` with full context
- **Search suites** — save searches, group into suites, run with pass/fail criteria and scheduled auto-runs
- **Email alerts** — get notified when scheduled suites detect compliance failures
- **Results preview** — see matches inline in the GUI with highlighted terms
- **Search index** — optional SQLite FTS5 index for faster repeated searches
- **Inverse search** — find files that are *missing* required content
- **Cross-platform** — Windows, macOS, Linux
- **Three interfaces** — terminal CLI, point-and-click GUI (`docsearch-gui`), Python API
- **Offline and private** — your documents never leave your computer
- **Read-only** — docsearch never modifies, moves, or deletes your files

### Supported File Types

| Category | Formats |
|----------|---------|
| **Documents** | .doc .docx .pdf .odt .rtf .epub .pptx .ppt .html .md .rst .tex |
| **Spreadsheets** | .xlsx .xls .ods .csv .tsv |
| **Email** | .eml .msg .pst |
| **Archives** | .zip .tar .gz .bz2 .tgz .7z .rar |
| **Data/Config** | .json .xml .yaml .yml .toml .ini .cfg .sql .log .txt |
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

1. Click **Browse** to select a folder
2. Type your search terms
3. Click **Run Search**
4. View results in the preview pane or click **DOCX** to open the highlighted report

Open **Advanced Options** for regex, fuzzy, Boolean, range queries, and all other settings. Open **Search Suites** to build compliance checks with pass/fail tracking.

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
| [Compliance Guide](docs/COMPLIANCE_GUIDE.md) | Using docsearch for auditing — industry examples, sample suites, step-by-step setup |
| [API Reference](docs/API.md) | Python library API — `search()` function, parameters, return values |
| [FAQ & Troubleshooting](docs/TROUBLESHOOTING.md) | Common questions and solutions for Windows, macOS, and Linux |
| [Changelog](CHANGELOG.md) | Version history and release notes |
| [Contributing](CONTRIBUTING.md) | How to report bugs, suggest features, and submit code |

## Use Cases

- **Home users** — search years of personal documents, Google Docs backups, family records
- **Compliance & audit** — automated checks with pass/fail suites, scheduled runs, email alerts, .docx evidence reports
- **Legal** — search contracts for required clauses, find privileged documents, pre-litigation review
- **Healthcare** — HIPAA compliance checks, PII detection across patient records
- **Finance** — SOX audit documentation, transaction monitoring, range queries on dollar amounts
- **HR** — verify employee files have required documents, detect SSNs on shared drives
- **Research** — search across papers, notes, and datasets in any format

## What You Get at Each Price Point

| Feature | docsearch (free) | Paid competitors ($29-249/yr) |
|---------|-----------------|-------------------------------|
| File types | 42 | 170+ |
| CLI + GUI + API | All three | GUI only |
| Cross-platform | Win/Mac/Linux | Windows only |
| Highlighted .docx reports | Yes | No |
| Search suites with pass/fail | Yes | No |
| Range queries (dates, $, %) | Yes | Limited or none |
| Email alerts | Yes | No |
| OCR (scanned PDFs/images) | Yes | Varies |
| Email search (.eml/.msg/.pst) | Yes | Yes |
| Archive search (.zip/.7z/.rar) | Yes | No |
| Open source | Yes | No |

## Author

Built by [Robert D. Schoening](https://robertdschoening.com) — retired electrical engineer, former IBM engineer, US software patent holder, and solo developer.

## License

This project is licensed under the [MIT License](LICENSE).
