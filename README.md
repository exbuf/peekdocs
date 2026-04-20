# peekdocs

**Free · Open-Source · No Cloud · Searches 77 file types all at once · Tested on 1,000,000 files**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](docs/USER_GUIDE.md)

> peekdocs document search app searches your Word docs, PDFs, spreadsheets, emails — 77 file types, all searched at once, all offline. Yellow-highlighted results, sensitive-data (PII) scanning, text-from-images (OCR) for scanned documents, and search modes from simple keywords to advanced patterns (regex).
>
> Runs entirely on your computer — your files are never uploaded, altered, or deleted. (peekdocs creates its own local report and index files, which you can delete at any time.) Free. No fees, no subscriptions.
>
> Point-and-click GUI • Terminal CLI • Python API
>
> **For home users, small businesses, professionals, and developers.**

**Contents:** [Who Is It For?](#who-is-it-for) · [Features](#features) · [Supported File Types](#supported-file-types) · [Installation](#installation) · [Quick Start](#quick-start) · [Documentation](#documentation) · [Why peekdocs?](#why-peekdocs) · [Why Not Just Use AI?](#why-not-just-use-ai) · [Why Not Just Use Grep?](#why-not-just-use-grep) · [Performance](#performance) · [Platform Notes](#platform-notes) · [Author](#author) · [License](#license)

**What makes peekdocs different:**

- **Highlighted results** — matches are highlighted two ways. The **Results Preview** pane shows matches instantly inside the app for quick scanning — right-click to copy, double-click a filename to open it. The `.docx` **Word report** is a standalone document with every match highlighted in yellow, organized by file with surrounding context, search metadata, and match counts — a polished report you can save, print, email, or share with anyone. Both show the same matches; the preview is for quick review, the report is for keeping or sharing. (A `.txt` plain-text report is also generated automatically, and CSV, JSON, and PDF output are available optionally.) Don't have Microsoft Word? The `.docx` report opens in any word processor — [LibreOffice](https://www.libreoffice.org/download/download-libreoffice/) (free), Google Docs, Apple Pages, or others.
- **One-click PII Scan** (Personally Identifiable Information) — worried about sensitive data inadvertently left in your files? One click finds Social Security numbers, credit cards, passwords, and more — before someone else does. One button, no setup.
- **Search Wizard** — configures more complex searches for you. No regex (regular expressions — a pattern language for matching text) or technical knowledge needed.
- **Scanned documents** — OCR reads text from scanned PDFs and images that other tools can't search.
- **77 file types at once** — Word, PDF, Excel, PowerPoint, email (.eml, .msg, .pst), archives (.zip, .7z, .rar), source code, engineering files, e-books, calendars, contacts, and more. All searched simultaneously.
- **Hover tips everywhere** — not sure what a button or field does? Hover your mouse over it and a helpful tooltip explains what it does and how to use it. No need to open the manual. Toggle on/off from the Tools menu. Saved automatically.
- **Adjustable text size** — five sizes from Small to Huge, accessible from the Tools menu. All text, labels, and buttons scale together. Helpful for users with low vision or high-DPI displays. Saved automatically.
- **Dark mode** — switch between Dark, Light, or System (follows your OS setting) from the Tools menu. Saved automatically.

**How it works:**

1. Point it at a folder on your computer
2. Type what you're looking for
3. Click Run Search
4. View results in the Results Preview window, or optionally open the highlighted `.docx` report

That's it. No server, no configuration, no account. Typical searches complete in 1–5 seconds for personal document collections. An optional search index makes repeated searches even faster.

### See it in action

*Click any image to enlarge, or visit [robertdschoening.com/peekdocs](https://robertdschoening.com/peekdocs) for full-size screenshots and a video walkthrough.*

**Getting Started tab — friendly introduction for first-time users:**

![Getting Started tab](docs/images/getting-started-tab.png)

**Search for "password" — results highlighted instantly:**

![Main screen with search results](docs/images/main--screen-password.png)

**PII Scan — one click finds sensitive data hiding in your files:**

![PII Scan category selection](docs/images/PII_Scan.png)

![PII Scan results with severity badges](docs/images/PII_scan_results.png)

**Highlighted Word report — every match in yellow, with context:**

![Highlighted .docx report open in Word](docs/images/main-screen-report.png)

**Simple for everyone, powerful when you need it.** Most users never leave the search bar and PII Scan button. Power users can go deeper with regex, Boolean logic, range queries, fuzzy matching, wildcards, proximity search, a command-line interface, and a Python API.

Works in any language. Runs on Windows, macOS, and Linux. No fees, no subscriptions, no cloud. Everything stays on your computer. Nothing is uploaded anywhere. Your files are never altered or deleted. Free and open-source.

**[See peekdocs in action →](https://robertdschoening.com/peekdocs)**

## Who Is It For?

- **Home users** — type your keyword(s), click Run Search, done. No setup, no configuration, no manual. Designed to be easy to use for non-technical people. Click **PII Scan** to check your files for Social Security numbers, credit cards, and other sensitive data — one click, no setup
- **Small businesses** — find information across contracts, invoices, reports, and correspondence. Save searches by name and reload them later. Search across vendor contracts for specific terms, pricing, or expiration dates. Locate transactions and policy references before an audit. (peekdocs is a search tool, not compliance or auditing software — it helps you find what's in your files, not certify regulatory status)
- **Power users** — regex, Boolean expressions, range queries, fuzzy matching, wildcards, proximity search, OCR, a terminal CLI, and a Python API. All search modes work from both the GUI and the command line. The PII Scan and Search Wizard are GUI-only features
- **Programmers** — search the files VS Code can't: legacy specs and requirements in Word/PDF, email archives from past projects, vendor documentation and SDK guides in PDF, archived releases inside .zip/.7z files, scanned whiteboard photos (OCR), old project logs and meeting notes, and API keys accidentally saved in documents (PII Scan). A developer who needs to find "what did the client say about the authentication requirement in 2019" can't do that in VS Code if the answer is in a .docx email attachment inside a .zip archive. peekdocs can. Tip: use Lines Before/After in Advanced Search Options to capture surrounding code context — not just the matching line, but the function or block it belongs to. Supported source code formats: .py, .c, .cpp, .h, .hpp, .java, .js, .ts, .go, .rs, .rb, .sh, .bat, .ps1, .r, .swift, .kt, .cs, .vb, .f90, .f, .asm, .s, .pl, .tcl, .makefile
- **Engineers** — search hundreds of datasheets, design reviews, test reports, and failure analyses for a specific component value, part number, or tolerance. Find which documents reference a standard (MIL-STD-810, IEC 61508, ISO 9001). Search old design reviews and trade studies to find why a decision was made years ago. Locate error codes and symptoms across equipment manuals and maintenance logs. Find calibration records, inspection reports, and certification dates. Search change orders and ECNs for a specific part number. Find every document that references a vendor, supplier, or material. Search old test data reports for baseline measurements. OCR reads scanned engineering drawings and handwritten notes. Engineers accumulate PDFs like nobody else — datasheets, standards, specs, reports, manuals — and most are in formats that grep (a popular command-line text search tool, limited to plain text files) and VS Code can't read. The highlighted Word report can be attached to a design review or emailed directly. Supported engineering formats: .m (MATLAB), .v .vhd .vhdl .sv (Verilog/VHDL/SystemVerilog), .cir .sp .spice (SPICE netlists), .dxf (AutoCAD interchange)
- **Students and writers** — search across course notes, research papers, interview transcripts, and assignments in any format
- **Teachers** — search years of lesson plans for a specific topic or standard. Find old tests, quizzes, and worksheets that covered a particular concept — across Word docs, PDFs, and scanned handouts (OCR). Search parent correspondence for a specific student or issue. Find what you wrote on report cards last year. PII Scan is critical for IEP documents and student accommodation records, which contain highly sensitive data
- **Librarians** — search donated document collections and digital archives without opening files one by one. Find specific titles, authors, or ISBNs across acquisition lists, catalog records, and spreadsheets. Search grant applications, board meeting minutes, and policy documents across years. PII Scan on patron records before archiving or sharing
- **Researchers** — search across hundreds of downloaded journal articles (PDF), interview transcripts, survey responses, field notes, and datasets for a specific term, author, citation, or data point. Find a methodology reference buried in last year's literature review. Search grant proposals and progress reports for specific aims or deliverables. OCR reads scanned source materials and historical documents. The highlighted Word report serves as an annotated bibliography or evidence trail
- **Tax season** — search years of tax returns, W-2s, 1099s, and receipts for a specific deduction, amount, or account number. Find what you need in seconds instead of opening files one by one
- **Medical records** — find old lab results, prescriptions, doctor names, and diagnoses across years of PDFs from patient portals
- **Estate and family documents** — handling a relative's files? Search for wills, insurance policies, account numbers, passwords, and important records across an entire folder of unfamiliar documents
- **Home renovation and vehicles** — find contractor invoices, permits, appliance model numbers, warranty dates, VIN numbers, and maintenance records buried in old documents
- **Warranties and receipts** — "when did I buy the dishwasher?" Search years of email receipts and scanned warranties to find purchase dates, model numbers, and return policies
- **Genealogy** — search scanned family documents, old letters (OCR), immigration records, and historical PDFs for names, dates, and places
- **Selling or donating a computer** — run the PII Scan before handing off a device to make sure no Social Security numbers, credit cards, or passwords are left behind
- **Customer disputes** — find the original email, invoice, or agreement with a specific customer across years of correspondence
- **Employee onboarding** — new hires searching policy manuals, benefit documents, and training materials for specific topics
- **Email archives** — search exported email files (.eml, .msg, .pst, .mbox) for old correspondence, attachments, and contacts. Most search tools can't read email formats — peekdocs can

## Features

- **PII Scan** — **Do you know what's hiding in your documents?** One click finds Social Security numbers, credit cards, passwords (including pw, p/w, login, username, user ID, UID), tax IDs, emails, phone numbers, dates of birth, and user-configurable dollar-amount ranges — with a highlighted report showing exactly where. Results are categorized by severity (high/moderate/info) with per-file details. **Custom patterns:** advanced users can add their own regex (e.g., UK NINO, Canadian SIN, German Steuer-ID, company account IDs) to extend the scan beyond the built-in categories
- **Offline and private** — your documents never leave your computer. peekdocs never uploads, transmits, alters, moves, or deletes your files. No cloud, no accounts, no subscriptions. Everything runs locally and stays local
- **77 file types** — Word, PDF, Excel, PowerPoint, emails (.eml, .msg, .pst, .mbox), archives (.zip, .7z, .rar), source code (Python, C/C++, Java, Go, Rust, and more), engineering files (MATLAB, Verilog, VHDL, SPICE, DXF), Apple Pages, calendars (.ics), contacts (.vcf), e-books, HTML, and more
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
- **Multi-folder search** — search across multiple folders at once. Click **+Folder** to add folders, or type semicolon-separated paths. Results are combined from all folders
- **HTML export** — in addition to TXT, DOCX, CSV, JSON, and PDF, results can be exported as a styled HTML page with highlighted matches — easy to share via email or open in any browser
- **Three interfaces** — terminal CLI, point-and-click GUI (`peekdocs-gui`), Python API
- **Cross-platform** — Windows, macOS, Linux
- **Search index** — optional SQLite FTS5 index for faster repeated searches
- **Read-only** — peekdocs never modifies, moves, or deletes your files. It does create its own output files (reports, indexes, settings) and can delete those when you ask (e.g., Clear Results, Delete Index)
- **Safe defaults** — files over 100 MB are automatically skipped to prevent slow searches and memory issues. Very large files (huge PDFs, massive spreadsheets, database exports) can take minutes to parse and may exhaust available memory. Skipped files are logged to `peekdocs_errors.log` so you know what was missed. To change the limit, set **Max File Size (MB)** in Advanced Search Options — or set it to 0 for no limit. Changing the limit automatically rebuilds the index on the next search. ZIP archives that would expand to over 500 MB are also skipped to prevent archive bombs
- **Excluded Files view** — after each search, click the **View N excluded file(s)** button to see exactly which files were skipped and why (unsupported type, prior output, oversized, hidden, etc.) — no more guessing why a `find` count differs from peekdocs's file count
- **Tools menu** — built-in utilities beyond search:
  - **File Inventory** — instant summary of every file in a folder: total count, size breakdown by type, oldest and newest files
  - **Duplicate Finder** — finds identical files by content (not just name), shows how much space is wasted by extra copies
  - **Large Files** — shows the 50 biggest files so you can reclaim disk space
  - **Empty Files** — finds zero-byte files: failed downloads, placeholders, junk
  - **Recent Changes** — which files were modified in the last 7, 30, or 90 days
  - **Protected Files** — detects password-protected PDFs, Word/Excel/PowerPoint, ZIP/7z/RAR archives that peekdocs can't search
  - **Search History** — automatic diary of every search you run: date, terms, match count, file count, elapsed time
  - **Bookmarks** — pin files from search results for quick access later

### Supported File Types

| Category | Formats |
|----------|---------|
| **Documents** | .doc .docx .epub .html .md .odt .pages .pdf .ppt .pptx .rst .rtf .tex |
| **Spreadsheets** | .csv .ods .tsv .xls .xlsx |
| **Email** | .eml .mbox .msg .pst |
| **Archives** | .7z .bz2 .gz .rar .tar .tgz .zip |
| **Calendar/Contacts** | .ics .vcf |
| **Source Code** | .asm .bat .c .cpp .cs .f .f90 .go .h .hpp .java .js .kt .pl .ps1 .py .r .rb .rs .s .sh .swift .tcl .ts .vb |
| **Engineering** | .cir .dxf .m .sp .spice .sv .v .vhd .vhdl |
| **Data/Config** | .cfg .ini .json .log .makefile .sql .toml .txt .xml .yaml .yml |
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

peekdocs reads 77 file formats that most tools can't touch — Word, PDF, Excel, email archives, .7z, .rar, scanned images. It produces a highlighted Word report with every match in context — not a list of filenames in a terminal, but a real document you can save, print, or hand to someone. It finds sensitive data with one click. And it does all of this in a GUI that a non-technical person can use without reading a manual.

If all you need is to find a word in a document, any search tool works. If you want to *see inside your own files* — what's there, what's sensitive, and what you might have forgotten about — that's what peekdocs was built for.

## Why Not Just Use AI?

AI document tools (ChatGPT, Copilot, NotebookLM) require uploading your files to a cloud server. A corporation sees your tax returns, medical records, and passwords. Your data may be used for training. A breach exposes everything you uploaded. And you pay $20+/month for the privilege.

For finding specific content in your documents — keywords, patterns, SSNs, credit cards, phone numbers, account numbers — peekdocs does what AI does, without uploading anything. Your files stay on your computer. No account, no internet connection, no subscription, no third party.

There's also a practical problem: AI tools have upload limits and format restrictions. You can't upload 500 tax PDFs, 2,000 emails, and 10 years of contracts to ChatGPT — and even if you could, most AI tools can't read .msg, .pst, .7z, .rar, .odt, .xls, .doc, or scanned images. By the time you've uploaded your first few files to an AI tool, peekdocs would already be done searching hundreds. It reads 77 file types at once, on your machine, with no file count or size limit.

What AI adds beyond search — summarization, question answering, semantic understanding — requires giving up your privacy. Most people searching for "where's my insurance policy number" or "do any of my files contain passwords" don't need that. They need to find something. peekdocs finds it.

## Why Not Just Use Grep?

grep is a powerful command-line text search tool — if you know how to use it. But grep only reads plain text files. It can't open Word docs, PDFs, Excel spreadsheets, PowerPoint, email archives, or compressed files. It can't OCR a scanned document. It outputs matching lines to a terminal — no highlighted reports, no file-by-file organization, no GUI.

peekdocs reads 22 binary file types that grep can't open at all — Word, PDF, Excel, PowerPoint, email archives, e-books, compressed files, and more — plus 6 image types via OCR. For the 55 plain-text types that grep can read, peekdocs adds highlighted Word reports, a point-and-click GUI, PII scanning, proximity search, range queries, fuzzy matching, multi-folder search, and a search index — none of which grep offers.

If you're comfortable in a terminal and only search plain text files, grep is fine. If you have Word docs, PDFs, emails, spreadsheets, or archives — or if you want results you can hand to someone who doesn't use a terminal — peekdocs is what grep would be if grep could read your actual documents.

## Performance

peekdocs was tested on 1,000,000 files to verify it handles large document collections without crashing, slowing to a crawl, or running out of memory.

**Test setup:**
- **Machine:** MacBook Pro, Apple M-series, 14 cores (peekdocs used 7 — its default is half the available cores to leave CPU available for other programs), macOS 24.6
- **Files:** 10,000 / 50,000 / 1,000,000 plain-text files (.txt), each containing one line of realistic text (~113 bytes per file)
- **Search term:** a single keyword present in every file (worst case — maximum matches)
- **Python:** 3.13, peekdocs running via `pip install -e .` in a virtual environment

**Benchmark results — warm cache.\*** Plain-text files on MacBook Pro, Apple M-series, 14 cores (7 used), SSD.

| Files | Direct search | With index | Index build | Index size |
|------:|--------------:|-----------:|------------:|-----------:|
| 10,000 | 1.4 seconds | — | — | — |
| 50,000 | 4.1 seconds* | 9.1 seconds | 5.3 seconds | 17 MB |
| 1,000,000 | 90 seconds* | 240 seconds | 110 seconds | 311 MB |

*\* Warm cache — files already in OS memory from recent access. Cold-cache times are significantly longer (see below).*

**Cold cache vs warm cache — why the same search can take 4 seconds or 4 minutes:**

Your operating system keeps recently accessed files in RAM so they don't have to be read from disk again. A "warm cache" search runs after the files have already been read once — the OS serves them from memory, which is fast. A "cold cache" search happens when the files haven't been accessed recently and must be read from disk. In our 50,000-file test, cold cache took 87.5 seconds vs 9.1 seconds warm — a 10× difference. This is why the first search after rebooting or switching folders feels slower than the second one.

**Our recommendation: just build an index.** Click Build Index in Manage Indexes (or run `peekdocs --index` from the terminal) and every search after that is fast — cold cache or warm, first search or fiftieth. The index reads all your files once, extracts the text, and stores it in a single compact database. Future searches query the database instead of re-opening every file. If your files change, peekdocs can keep the index current automatically — set Auto-Refresh in Manage Indexes to an interval (5 minutes to 24 hours) and peekdocs detects new, changed, and deleted files and updates the index in the background. You never have to think about it again.

**Surprise findings at 1,000,000 files:**

- **peekdocs handled it without crashing, running out of memory, or producing errors.** One million files, one million matches, correct results.
- **The index was actually slower** (240 seconds) than direct search (90 seconds warm cache). At this scale, the SQLite FTS5 engine has to process a million result rows, which is more expensive than just reading a million small text files from cache. The index wins when files are large, binary (PDF/DOCX), or not in cache — not when everything is small and already in memory.
- **File discovery became the bottleneck.** At 1 million files, enumerating the directory (listing all filenames) takes over 200 seconds before any searching even starts. This is an operating system limitation, not peekdocs.
- **Bottom line:** peekdocs has no built-in file count limit, but the practical sweet spot is under 100,000 files. Beyond that, searches still work but take minutes. Most home users and small businesses have well under 10,000 documents.

**When to use an index — and when not to:**

| Situation | Index helps? | Why |
|-----------|:-----------:|-----|
| Folder with 100+ files you search repeatedly | **Yes** | Build once, fast searches forever |
| Folder with PDFs, Word, Excel (binary formats) | **Yes** | Skips expensive file parsing on every search |
| First search after reboot or folder switch (cold cache) | **Yes** | Single database file loads faster than thousands of individual files |
| Small folder (under 100 files) | **No** | Direct search is already fast enough |
| Folder with only plain text files already in memory | **No** | Index adds overhead without benefit |
| One-time search of a folder you won't revisit | **No** | Index build takes time you won't recoup |
| Folder where files change frequently | **Maybe** | Use Auto-Refresh to keep the index current, but frequent rebuilds have a cost |

The index is optional. peekdocs works without one. Build it from Manage Indexes in the GUI or `peekdocs --index` from the terminal.

**Realistic estimate — typical home or small business folder:**

A real document folder is a mix of PDFs, Word docs, spreadsheets, emails, and other formats. Each type takes a different amount of time to parse:

| File type | Typical parse time per file | Why |
|-----------|---------------------------|-----|
| Plain text (.txt, .csv, .log, source code) | 1–5 ms | Just reading bytes — no decoding needed |
| Email (.eml) | 5–10 ms | Parse headers and body text |
| Word (.docx) | 20–50 ms | Unzip container, parse XML |
| Excel (.xlsx) | 30–100 ms | Unzip, parse multiple sheet XMLs |
| PowerPoint (.pptx) | 30–80 ms | Unzip, parse slide XMLs |
| PDF | 50–200 ms | Decode page streams, font tables, layout |
| Scanned image (OCR) | 1–3 seconds | Full optical character recognition |

**Estimated search times for mixed-format collections:**

| Files | Without index | With index | Who has this many |
|------:|--------------:|-----------:|-------------------|
| 1,000 | 15–30 seconds | 2–5 seconds | Home user, small business |
| 10,000 | 2–5 minutes | 10–20 seconds | Active business, shared drive |
| 50,000 | 10–25 minutes | 30–60 seconds | Department archive, legacy file server |

These are estimates for mixed binary formats (PDF, DOCX, XLSX), not benchmarks. Your hardware matters — more CPU cores means more files processed in parallel, more RAM keeps file data cached between searches, and an SSD is significantly faster than a spinning hard drive for cold-cache searches. An older machine with 2 cores and a hard drive will be noticeably slower than a modern machine with 8+ cores and an SSD. You can adjust how many CPU cores peekdocs uses in Advanced Search Options — increase for faster searches, or decrease to leave more CPU available for other programs. If OCR is enabled for scanned images, add 1–3 seconds per image on the first search (the index stores OCR results so subsequent searches don't repeat it). The search itself (matching text against your terms) is nearly instantaneous; the time is spent opening and parsing files.

**Why Python?** peekdocs is written in Python, but the performance-critical work — PDF decoding, ZIP decompression, regex matching — is handled by C-backed libraries (PyMuPDF, openpyxl, Python's `re` module). Python orchestrates the search; C does the heavy lifting. File processing uses multiprocessing (separate OS processes, not threads), so Python's GIL is not a factor. The result: 1 million files searched without crashing, without running out of memory, and with reasonable times (90 seconds warm cache) — on an interpreted language that skeptics might dismiss as "too slow."

**Limitations of these tests:** The benchmark used small, single-line text files on a fast SSD. Real-world performance depends on file sizes, formats (PDFs are slower to parse than .txt), disk speed, available RAM, and how many files actually match. A folder of 1,000 large PDFs will take longer than 50,000 tiny text files, because PDF parsing dominates the time. The tests confirm that peekdocs handles high file counts — up to 1 million — without architectural limits, but your actual search times will vary based on your documents and hardware.

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
