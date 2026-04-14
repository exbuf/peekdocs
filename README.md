# peekdocs

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](docs/USER_GUIDE.md)

> peekdocs searches your Word docs, PDFs, spreadsheets, emails, and 46 file types in all — at once, all offline. Type a word, click a button, see your results. No manual needed.

**What makes it different:**

- **Highlighted results** — matches are highlighted two ways: instantly in the **Results Preview** pane inside the app as you search, and in a standalone `.docx` **Word report** with every match in yellow and surrounding context you can save, print, email, or share with anyone. (A `.txt` plain-text report is also generated automatically, and CSV, JSON, and PDF output are available optionally.) Not just a list of filenames — a readable report. Don't have Microsoft Word? The `.docx` report opens in any word processor — [LibreOffice](https://www.libreoffice.org/download/download-libreoffice/) (free), Google Docs, Apple Pages, or others.
- **One-click PII Scan** (Personally Identifiable Information) — worried about sensitive data inadvertently left in your files? One click finds Social Security numbers, credit cards, passwords, and more — before someone else does. One button, no setup.
- **Search Wizard** — configures more complex searches for you. No regex (regular expressions — a pattern language for matching text) or technical knowledge needed.
- **Scanned documents** — OCR reads text from scanned PDFs and images that other tools can't search.
- **46 file types at once** — Word, PDF, Excel, PowerPoint, email (.eml, .msg, .pst), archives (.zip, .7z, .rar), e-books, calendars, contacts, and 30+ more. All searched simultaneously.
- **Hover tips everywhere** — not sure what a button or field does? Hover your mouse over it and a helpful tooltip explains what it does and how to use it. No need to open the manual.
- **Adjustable text size** — five sizes from Small to Huge, accessible from the Tools menu. All text, labels, and buttons scale together. Helpful for users with low vision or high-DPI displays.

**How it works:**

1. Point it at a folder on your computer
2. Type what you're looking for
3. Click Run Search
4. View results in the Results Preview window, or optionally open the highlighted `.docx` report

That's it. No server, no configuration, no account.

**Simple for everyone, powerful when you need it.** Most users never leave the search bar and PII Scan button. Power users can go deeper with regex, Boolean logic, range queries, fuzzy matching, wildcards, proximity search, a command-line interface, and a Python API.

Works in any language. Runs on Windows, macOS, and Linux. No fees, no subscriptions, no cloud. Everything stays on your computer. Nothing is uploaded anywhere. Your files are never altered or deleted. Free and open-source.

**[See peekdocs in action →](https://robertdschoening.com/peekdocs)**

## Who Is It For?

- **Home users** — type your keyword(s), click Run Search, done. No setup, no configuration, no manual. Designed to be easy to use for non-technical people. Click **PII Scan** to check your files for Social Security numbers, credit cards, and other sensitive data — one click, no setup
- **Tax season** — search years of tax returns, W-2s, 1099s, and receipts for a specific deduction, amount, or account number. Find what you need in seconds instead of opening files one by one
- **Estate and family documents** — handling a relative's files? Search for wills, insurance policies, account numbers, passwords, and important records across an entire folder of unfamiliar documents
- **Selling or donating a computer** — run the PII Scan before handing off a device to make sure no Social Security numbers, credit cards, or passwords are left behind
- **Email archives** — search exported email files (.eml, .msg, .pst, .mbox) for old correspondence, attachments, and contacts. Most search tools can't read email formats — peekdocs can
- **Small businesses** — find information across contracts, invoices, reports, and correspondence. Save searches by name and reload them later. peekdocs is a search tool, not compliance or auditing software — it helps you find what's in your files, not certify regulatory status
- **Students and writers** — search across course notes, research papers, interview transcripts, and assignments in any format
- **Power users** — regex, Boolean expressions, range queries, fuzzy matching, wildcards, proximity search, OCR, a terminal CLI, and a Python API. All search modes work from both the GUI and the command line. The PII Scan and Search Wizard are GUI-only features

## Features

- **PII Scan** — **Do you know what's hiding in your documents?** One click finds Social Security numbers, credit cards, passwords, tax IDs, emails, phone numbers, dates of birth, and user-configurable dollar-amount ranges — with a highlighted report showing exactly where. Results are categorized by severity (high/moderate/info) with per-file details. **Custom patterns:** advanced users can add their own regex (e.g., UK NINO, Canadian SIN, German Steuer-ID, company account IDs) to extend the scan beyond the built-in categories
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
- **Works in any language** — peekdocs searches documents written in English, Spanish, French, German, Chinese, Japanese, Korean, Arabic, Hindi, Russian, Greek, and every other language. All text handling is Unicode-based. Type your search terms in any language and peekdocs finds them. **Note:** peekdocs performs exact text matching — it finds the character sequence you type, which works well for all languages including CJK (Chinese, Japanese, Korean). It does not perform language-specific processing such as word segmentation, stemming, or stop-word removal. Documentation and the GUI are in English only
- **Three interfaces** — terminal CLI, point-and-click GUI (`peekdocs-gui`), Python API
- **Cross-platform** — Windows, macOS, Linux
- **Search index** — optional SQLite FTS5 index for faster repeated searches
- **Read-only** — peekdocs never modifies, moves, or deletes your files. It does create its own output files (reports, indexes, settings) and can delete those when you ask (e.g., Clear Results, Delete Index)
- **Safe defaults** — files over 100 MB are automatically skipped to prevent slow searches and memory issues. Very large files (huge PDFs, massive spreadsheets, database exports) can take minutes to parse and may exhaust available memory. Skipped files are logged to `peekdocs_errors.log` so you know what was missed. To change the limit, set **Max File Size (MB)** in Advanced Search Options — or set it to 0 for no limit. Changing the limit automatically rebuilds the index on the next search. ZIP archives that would expand to over 500 MB are also skipped to prevent archive bombs
- **Excluded Files view** — after each search, click the **View N excluded file(s)** button to see exactly which files were skipped and why (unsupported type, prior output, oversized, hidden, etc.) — no more guessing why a `find` count differs from peekdocs's file count

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
  - **Windows users:** When installing Python, make sure to check **"Add Python to PATH"** at the bottom of the first installer screen. This ensures that `pip`, `python`, and `peekdocs` commands work from any Command Prompt window. If you've already installed Python without this option, the easiest fix is to re-run the Python installer and check the box.
  - **Linux users (Ubuntu, Debian, Linux Mint, Pop!_OS):** The base `python3` package does not include `venv`, `pip`, or `tkinter`. You must install them before creating a virtual environment. Run this single command to get everything peekdocs needs:
    ```bash
    sudo apt install python3-venv python3-pip python3-tk
    ```
    Without `python3-venv` and `python3-pip`, `python3 -m venv venv` will fail with an `ensurepip` error. Without `python3-tk`, the CLI works but the GUI (`peekdocs-gui`) will not launch. This is a one-time setup.
- **Tkinter** (required for GUI) — included on Windows and macOS. On Linux you must install it: `sudo apt install python3-tk` (already included in the Linux command above)
- **Tesseract** (optional, for OCR) — macOS: `brew install tesseract` | Windows: [download](https://github.com/UB-Mannheim/tesseract/wiki) | Linux: `sudo apt install tesseract-ocr`

### Option A: Quick Install with pipx (recommended)

First, check if pipx is installed by typing `pipx --version`. If it says "not recognized" or "command not found," install it:

```bash
pip install pipx          # Windows: if pip isn't recognized, use: python -m pip install pipx
pipx ensurepath           # adds pipx to your PATH
```

**Close and reopen your terminal** after running `ensurepath` (it only takes effect in a new window). Then install peekdocs:

```bash
pipx install git+https://github.com/exbuf/peekdocs.git
```

**Getting a git error?** If you see "do you have git installed," use this instead (downloads as a ZIP — no git required):

```bash
pipx install https://github.com/exbuf/peekdocs/archive/refs/heads/main.zip
```

After installation, `peekdocs` and `peekdocs-gui` work from any terminal, any folder, every time — no activation step needed. This is the easiest way to install.

**Fully isolated.** pipx installs peekdocs in its own private environment, completely separate from your system Python and all other programs. It will not install, upgrade, downgrade, or conflict with anything else on your computer. The only change to your system is two new commands (`peekdocs` and `peekdocs-gui`). To uninstall completely: `pipx uninstall peekdocs`. See the [User Guide](docs/USER_GUIDE.md#will-peekdocs-affect-my-existing-python-installation) for details.

### Option B: Manual Install (with git)

```bash
git clone https://github.com/exbuf/peekdocs.git
cd peekdocs
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install --upgrade pip setuptools wheel   # required on some Linux distros — see note below
pip install -e .
```

**Important:** With a manual install, you must activate the virtual environment (`source venv/bin/activate`) every time you open a new terminal. If you see "command not found" when typing `peekdocs`, this is why. See the [User Guide](docs/USER_GUIDE.md#which-installation-method-did-you-use) for details and how to switch to pipx.

**"setup.py not found" error on Linux?** Some Linux distributions ship older versions of pip and setuptools that don't support `pyproject.toml`-based builds (which peekdocs uses). The fix is `pip install --upgrade pip setuptools wheel` inside the virtual environment before running `pip install -e .` — this is already included in the commands above. Make sure the `(venv)` prefix is showing in your terminal prompt before running these commands.

### Option C: Manual Install (no git, no sign-up)

No git? No problem. Download peekdocs as a ZIP file directly from your browser:

1. Go to [github.com/exbuf/peekdocs](https://github.com/exbuf/peekdocs)
2. Click the green **Code** button
3. Click **Download ZIP**
4. Extract the ZIP file, copy the extracted `peekdocs-main` folder and paste it to where you want it
5. Open a terminal and navigate to the extracted folder:

   **Windows:**
   ```cmd
   cd C:\Users\YourName\Downloads\peekdocs-main
   python -m venv venv
   venv\Scripts\activate
   pip install -e .
   ```

   **macOS/Linux:**
   ```bash
   cd ~/Downloads/peekdocs-main
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip setuptools wheel
   pip install -e .
   ```

**Important:** Same as Option B — you must activate the virtual environment each time you open a new terminal. See the [User Guide](docs/USER_GUIDE.md#which-installation-method-did-you-use) for details.

### Upgrading

Your saved searches, settings, indexes, and reports are stored outside the peekdocs installation — in your home directory and your document folders. Upgrading replaces only the code. Nothing else is touched.

- **pipx:** `pipx upgrade peekdocs`
- **git:** `cd peekdocs && git pull && pip install -e .`
- **ZIP:** download the new ZIP, replace the folder, run `pip install -e .`

See the [User Guide](docs/USER_GUIDE.md#will-peekdocs-affect-my-existing-python-installation) for full details on what is and isn't preserved.

## Quick Start

### Terminal

```bash
cd /path/to/your/documents
peekdocs budget                      # search for "budget"
peekdocs budget revenue              # OR search (any term)
peekdocs -a budget revenue           # AND search (both terms)
peekdocs -r budget                   # include subfolders
peekdocs -t pdf,docx budget          # only PDFs and Word docs
peekdocs -x "\d{3}-\d{2}-\d{4}"     # regex (SSN pattern)
peekdocs -e "(budget OR revenue) AND NOT draft"   # Boolean expression
peekdocs -R amount:1000..5000 budget # range query
```

Results are saved to `peekdocs_results.txt` and `peekdocs_results.docx` (highlighted). The .docx report opens with whatever word processor you have — Microsoft Word, [LibreOffice](https://www.libreoffice.org/download/download-libreoffice/) (free), Google Docs, or Apple Pages. The .txt report works on any computer with no extra software.

Run `peekdocs -h` for the full flag reference with examples.

### GUI

```bash
peekdocs-gui
```

1. Click **Browse** to select a folder (or **File** to search a single file)
2. Type your search terms
3. Click **Run Search**
4. View results in the preview pane or click **DOCX** to open the highlighted report

Open **Advanced Search Options** for regex, fuzzy, Boolean, range queries, and all other settings. Use the **Search Wizard** for guided search configuration with 20+ pre-built patterns. Click **PII Scan** to find sensitive data with one click.

**If buttons overlap or text looks too large**, use the **Text Size** dropdown on the bottom-right toolbar to adjust (Normal is recommended).

### Python API

```python
from peekdocs import search

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

## Why peekdocs?

Every search tool — from Google to Spotlight to $2,500 enterprise software — does the same thing at its core: match a pattern against text. Any modern tool can search in any language, because they all use Unicode. The difference is never the matching. It's what happens around it: what files can it read, how does it present the results, how easy is it to use, and what can you do with the output.

peekdocs reads 46 file formats that most tools can't touch — Word, PDF, Excel, email archives, .7z, .rar, scanned images. It produces a highlighted Word report with every match in context — not a list of filenames in a terminal, but a real document you can save, print, or hand to someone. It finds sensitive data with one click. And it does all of this in a GUI that a non-technical person can use without reading a manual.

If all you need is to find a word in a document, any search tool works. If you want to *see inside your own files* — what's there, what's sensitive, and what you might have forgotten about — that's what peekdocs was built for.

## Platform Notes

**Tested on:** macOS (development machine), Windows 10/11, and Linux Mint 22.3 (Cinnamon) in a VirtualBox VM on Windows. The CLI and GUI work on all three platforms.

- **High-DPI displays (4K monitors)** — if buttons overlap or text looks too large, use the **Text Size** dropdown on the bottom-right toolbar to adjust. Normal is recommended for most screens
- **Antivirus software (Windows)** — some antivirus programs flag Python scripts as suspicious. If peekdocs is blocked, add your Python installation or the peekdocs folder to your antivirus allow list
- **Files locked by other programs (Windows)** — Windows locks files that are open in another program. If peekdocs reports "permission denied" on a file, close the program that has it open and search again. Errors are logged to `peekdocs_errors.log`
- **Corporate firewalls** — if `pip` or `pipx` can't download packages, use the [ZIP download](#option-c-manual-install-no-git-no-sign-up) installation method instead
- **macOS file picker vs Windows** — on macOS, the file picker includes a preview panel; on Windows, it does not — this is an OS difference, not peekdocs
- **Linux GUI requires python3-tk** — the CLI works without it, but `peekdocs-gui` needs tkinter. Install with `sudo apt install python3-tk` (see [Prerequisites](#prerequisites))

For more, see the [FAQ & Troubleshooting](docs/TROUBLESHOOTING.md).

## Author

Built by [Robert D. Schoening](https://robertdschoening.com) — retired electrical engineer, former IBM engineer, US software patent holder, and solo developer. peekdocs exists to make powerful document search accessible to everyone, for free — no paywalls, no feature limits, no catch. Developed with extensive use of [Claude Code](https://claude.ai/code) by Anthropic.

## Disclaimer

peekdocs is provided as-is under the [MIT License](LICENSE), without warranty of any kind. It is a search and reporting tool and does not provide legal, regulatory, or compliance advice. The PII Scan feature uses regex pattern matching and may produce false positives or miss data that does not match its built-in patterns — always review results in context before making decisions. Users are solely responsible for how they use the tool and interpret its results.

## License

Copyright (c) 2026 Robert D. Schoening. This project is licensed under the [MIT License](LICENSE).
