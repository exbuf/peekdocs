# docsearch

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

> Search Word docs, PDFs, spreadsheets, emails, archives, and 33 other file types — all at once, all offline. Use plain keywords, regex, Boolean logic, fuzzy matching, or range queries to find exactly what you need. Build compliance suites that run the same checks on a schedule, produce pass/fail audit reports, and send email alerts when failures are detected. From a home user searching personal files to an auditor reviewing 500 contracts, it just works. Terminal, GUI, or Python API. Free, open-source. Windows/Mac/Linux.

<!-- Add screenshots here when available:
![docsearch GUI](screenshots/main-window.png)
-->

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

```bash
pipx install git+https://github.com/exbuf/docsearch.git
```

After installation, `docsearch` and `docsearch-gui` work from any terminal, any folder, every time — no activation step needed. This is the easiest way to install. docsearch is installed in its own private workspace — it will not affect your existing Python installation or any other programs. See the [User Guide](docs/USER_GUIDE.md#will-docsearch-affect-my-existing-python-installation) for details.

### Option B: Manual Install

```bash
git clone https://github.com/exbuf/docsearch.git
cd docsearch
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -e .
```

**Important:** With a manual install, you must activate the virtual environment (`source venv/bin/activate`) every time you open a new terminal. If you see "command not found" when typing `docsearch`, this is why. See the [User Guide](docs/USER_GUIDE.md#which-installation-method-did-you-use) for details and how to switch to pipx.

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

Results are saved to `docsearch_results.txt` and `docsearch_results.docx` (highlighted).

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

## How It Compares

docsearch is free and matches or exceeds commercial tools costing $79–$150,000+/year:

| Feature | docsearch | dtSearch ($249) | Copernic ($29-96/yr) | Relativity ($80K+/yr) |
|---------|-----------|----------------|---------------------|----------------------|
| File types | 42 | Hundreds | 170+ | Hundreds |
| CLI + GUI + API | All three | GUI only | GUI only | Web only |
| Cross-platform | Win/Mac/Linux | Windows | Windows | Web |
| Highlighted .docx reports | Yes | No | No | Custom |
| Search suites with pass/fail | Yes | No | No | No |
| Range queries (dates, $, %) | Yes | Numeric only | No | Yes |
| Email alerts | Yes | No | No | Yes |
| Price | Free | $249 | $29-96/yr | $80K+/yr |

## Author

Built by [Robert D. Schoening](https://robertdschoening.com) — retired electrical engineer, former IBM engineer, US software patent holder, and solo developer.

## License

This project is licensed under the [MIT License](LICENSE).
