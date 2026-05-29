# peekdocs User Guide

This is the complete reference guide for peekdocs — a privacy-first local document search and analysis tool for Windows, macOS, and Linux, available as a GUI, CLI, and Python API. For a quick overview, see the [README](../README.md). For installation, see [Installation](../README.md#installation).

## Table of Contents

- [Where to Start](#where-to-start)
- [Will peekdocs affect my existing Python installation?](#will-peekdocs-affect-my-existing-python-installation)
- [Security Best Practices](#security-best-practices)
- [Dependencies](#dependencies)
  - [What gets installed automatically](#what-gets-installed-automatically)
  - [What you must install yourself](#what-you-must-install-yourself)
- [Getting Started with the Terminal](#getting-started-with-the-terminal)
  - [Which installation method did you use?](#which-installation-method-did-you-use)
  - [What is a terminal?](#what-is-a-terminal)
  - [Step 1: Open your terminal](#step-1-open-your-terminal)
  - [Step 2: Navigate to your documents folder](#step-2-navigate-to-your-documents-folder)
  - [Step 3: Run your first search](#step-3-run-your-first-search)
  - [Step 4: Open your results](#step-4-open-your-results)
  - [Step 5: Try a few more searches](#step-5-try-a-few-more-searches)
  - [Step 6: Get help](#step-6-get-help)
  - [Useful terminal tips](#useful-terminal-tips)
  - [What's next?](#whats-next)
- [GUI Mode (Graphical User Interface)](#gui-mode-graphical-user-interface)
- [Why peekdocs Instead of grep?](#why-peekdocs-instead-of-grep)
- [Usage](#usage)
  - [Phrase search (quoted terms)](#phrase-search-quoted-terms)
  - [Regex search](#regex-search)
    - [Common Regex Search Patterns](#common-regex-search-patterns)
- [Flag Use Summary](#flag-use-summary)
  - [Notes](#notes)
  - [Regex Collection Use Cases](#regex-collection-use-cases)
  - [Search Suite Use Cases](#search-suite-use-cases)
  - [Command Examples](#command-examples)
- [Output](#output)
  - [Search Modes and Their Reports](#search-modes-and-their-reports)
  - [Results Preview vs. Reports](#results-preview-vs-reports)
  - [Report Files](#report-files)
  - [Command Translation](#command-translation)
- [Automation and IT Use](#automation-and-it-use)
  - [A worked example: nightly source-tree watch](#a-worked-example-nightly-source-tree-watch)
  - [Exit codes](#exit-codes)
  - [JSON output (--stdout) schema](#json-output---stdout-schema)
  - [Scheduled and unattended runs](#scheduled-and-unattended-runs)
  - [Where things live](#where-things-live)
  - [Per-run structured log](#per-run-structured-log)
  - [Notification hook](#notification-hook)
  - [Diff between runs](#diff-between-runs)
  - [Headless servers and containers](#headless-servers-and-containers)
  - [Service accounts and file permissions](#service-accounts-and-file-permissions)
  - [Sharing collections across machines](#sharing-collections-across-machines)
  - [Useful CLI references for IT](#useful-cli-references-for-it)
- [Search Index (Optional)](#search-index-optional)
- [Inverse Search](#inverse-search)
- [Boolean Expression Search](#boolean-expression-search)
  - [Why use `-e` instead of `-a` and `-n`?](#why-use--e-instead-of--a-and--n)
  - [Operators](#operators)
  - [Combining with other modes](#combining-with-other-modes)
  - [Multi-word terms](#multi-word-terms)
  - [Range filters in expressions](#range-filters-in-expressions)
  - [Limitations](#limitations)
- [Range Queries](#range-queries)
  - [Using the `-R` flag](#using-the--r-flag)
  - [Range specs in boolean expressions](#range-specs-in-boolean-expressions)
  - [Notes on range queries](#notes-on-range-queries)
- [Combining Modes](#combining-modes)
- [Breaking Down Complex Searches](#breaking-down-complex-searches)
- [Saved Settings (Optional)](#saved-settings-optional)
- [Files Created by peekdocs](#files-created-by-peekdocs)
  - [Search reports](#search-reports)
  - [Saved and accumulated reports](#saved-and-accumulated-reports)
  - [Error log](#error-log)
  - [Search index](#search-index)
  - [Collection file](#collection-file)
  - [Search history](#search-history)
  - [Bookmarks](#bookmarks)
  - [Configuration file](#configuration-file)
  - [Summary](#summary)
  - [Delete on Close](#delete-on-close)
  - [Privacy cleanup options](#privacy-cleanup-options)
  - [CLI cleanup scope (`--clear`, `--clear-all`)](#cli-cleanup-scope---clear---clear-all)
  - [Cloud-synced folders](#cloud-synced-folders)
  - [Numeric-pattern search term warning](#numeric-pattern-search-term-warning)
  - [Known limitations (what peekdocs cannot control)](#known-limitations-what-peekdocs-cannot-control)
- [Limits and Constraints](#limits-and-constraints)
- [Platform Notes](#platform-notes)
  - [Showing hidden files](#showing-hidden-files)
  - [Locking the screen](#locking-the-screen)
  - [Network folder paths](#network-folder-paths)
  - [Activating the virtual environment](#activating-the-virtual-environment)
  - [File picker differences](#file-picker-differences)
  - [Opening reports without Microsoft Word](#opening-reports-without-microsoft-word)
  - [Schedule Search command format](#schedule-search-command-format)
  - [Batch loops over collections and suites](#batch-loops-over-collections-and-suites)
- [Multilingual Support](#multilingual-support)
  - [What works](#what-works)
  - [What doesn't work (limitations)](#what-doesnt-work-limitations)
  - [Documentation and GUI language](#documentation-and-gui-language)
  - [Sample multilingual files](#sample-multilingual-files)
  - [The automated language test](#the-automated-language-test)
- [Your First Advanced Search — Step by Step](#your-first-advanced-search--step-by-step)
  - [Example 1: Find an invoice-ID pattern with regex](#example-1-find-an-invoice-id-pattern-with-regex)
  - [Example 2: Find misspelled words with fuzzy matching](#example-2-find-misspelled-words-with-fuzzy-matching)
  - [Example 3: Find dollar amounts in a specific range](#example-3-find-dollar-amounts-in-a-specific-range)
  - [Example 4: Find files missing required content with inverse search](#example-4-find-files-missing-required-content-with-inverse-search)
  - [Example 5: Find words near each other with proximity search](#example-5-find-words-near-each-other-with-proximity-search)
  - [Example 6: Search only specific file types](#example-6-search-only-specific-file-types)
  - [Example 7: Combine multiple features together](#example-7-combine-multiple-features-together)
  - [What's next?](#whats-next-1)
- [Python API Reference](#python-api-reference)
- [Running Tests](#running-tests)
- [Project Structure](#project-structure)
- [Glossary](#glossary)

## Where to Start

This is a long reference document. Skip directly to what you need:

- **First time using peekdocs from the terminal?** Start with [Getting Started with the Terminal](#getting-started-with-the-terminal).
- **First time using the GUI?** Start with [GUI Mode (Graphical User Interface)](#gui-mode-graphical-user-interface).
- **Want a hands-on walkthrough of advanced features?** See [Your First Advanced Search — Step by Step](#your-first-advanced-search--step-by-step).
- **Integrating from Python?** Read [Python API Reference](#python-api-reference) and the full [API Reference](API.md).
- **Setting up automation or scheduled scans?** Start with [Automation and IT Use](#automation-and-it-use), especially the [worked example](#a-worked-example-nightly-source-tree-watch).
- **Looking up a flag or term?** See [Flag Use Summary](#flag-use-summary) and the [Glossary](#glossary).
- **Hit an error?** First run `peekdocs --check` (CLI) or open **Tools → System Check** in the GUI — both run the same diagnostic. If that's clean and you're still stuck, see [FAQ & Troubleshooting](TROUBLESHOOTING.md) for common questions and fixes across Windows, macOS, and Linux.

## Will peekdocs affect my existing Python installation?

No. Both installation methods keep peekdocs completely isolated from your existing Python setup, your other Python programs, and your system.

**With pipx** (`pipx install git+https://github.com/exbuf/peekdocs.git`): pipx creates a private workspace for peekdocs behind the scenes. Your system Python, any other Python programs, and any other virtual environments are completely untouched. peekdocs's dependencies (the libraries it needs, like PyMuPDF, openpyxl, etc.) are installed only inside that private workspace. You won't even see them if you run `pip list` from your normal Python. The only thing that changes system-wide is that two new commands (`peekdocs` and `peekdocs-gui`) are added to your PATH so you can type them in any terminal.

**With manual install** (git clone + virtual environment): The `python -m venv venv` command creates a sandbox folder. Everything peekdocs installs goes into that `venv` folder. When you deactivate the virtual environment or close the terminal, it's as if peekdocs doesn't exist. Your system Python packages are unchanged. Nothing is modified outside the `venv` folder.

**What peekdocs will NOT do:**

- It will not upgrade or downgrade your existing Python packages
- It will not break other Python programs on your computer
- It will not modify your system Python installation
- It will not interfere with conda, pyenv, Anaconda, or other Python environments
- It will not install anything outside its private workspace (except the two command names on your PATH if you use pipx)

**Upgrading to a new version — your data is preserved:**

All your settings, saved searches, indexes, and reports are stored outside the peekdocs installation — either in your home directory or in the folders where your documents are. When you upgrade, none of this is touched:

| Your data | Where it lives | Preserved on upgrade? |
|-----------|---------------|----------------------|
| Settings | `~/.peekdocsrc` (home directory) | Yes |
| Saved searches | `.peekdocs_collection.json` (each search folder) | Yes |
| Search index | `.peekdocs.db` (each search folder) | Yes |
| Search reports | `peekdocs_standard_results.*`, `peekdocs_regex_results.*`, `peekdocs_suite_results.*` (each search folder) | Yes |
| Saved reports | `peekdocs_report_*`, `peekdocs_accumulated_*` (each search folder) | Yes |
| Error log | `peekdocs_errors.log` (each search folder) | Yes |

**How to upgrade:**

- **pipx:** `pipx upgrade peekdocs` — replaces the code, preserves all your data
- **Manual install:** download the new ZIP, replace the `peekdocs-main` folder, run `pip install -e .` — your data is untouched

No migration, no export/import, no reconfiguration. Everything just works with the new version.

**Backing up your work — only two files matter:** `~/.peekdocsrc` (your settings) and `.peekdocs_collection.json` (your saved searches, one per folder). You may also want to back up `~/.peekdocs_history.json` (search history) and `~/.peekdocs_bookmarks.json` (bookmarks). Everything else peekdocs creates can be regenerated. Copy these to a safe location before major changes. See [Files Created by peekdocs](#files-created-by-peekdocs) for the complete list of all files and what each one does.

**How to see hidden files:** These files start with a dot, which makes them hidden by default.
- **macOS:** In Finder, press **Cmd+Shift+.** (period) to toggle hidden files
- **Windows:** In File Explorer, click the **View** tab and check **Show hidden items**
- **Linux:** In your file manager, press **Ctrl+H** or use `ls -a` in the terminal

**If you want to uninstall completely:**

- **pipx:** `pipx uninstall peekdocs` — removes the peekdocs code and its private workspace. Your settings (`~/.peekdocsrc`), saved searches, indexes, and reports in your document folders are not deleted — remove those manually if you want a clean slate.
- **Manual install:** delete the `peekdocs-main` folder you downloaded. Your settings and data in document folders remain.

---

## Security Best Practices

peekdocs runs entirely on your computer. Your documents are never uploaded, transmitted, sent to a server, or shared with any third party. peekdocs never alters, moves, or deletes your files — it only reads them and writes its own report files (`peekdocs_standard_results.txt`, `peekdocs_standard_results.docx`, and optionally CSV, JSON, PDF, and HTML). All processing happens locally on your machine. No internet connection is required or used.

Because the documents you search and the reports peekdocs writes may contain text you would rather not share, here are some practices to keep your data safe:

- **Lock your screen when stepping away.** peekdocs stores search results in plain files on your computer. Anyone with access to your screen can see the results preview, and anyone with access to your folder can open the report files. Lock your screen with **Win+L** (Windows), **Ctrl+Cmd+Q** (macOS), or **Super+L** (Linux). This protects everything — not just peekdocs, but email, browser, and all open files.
- **Be careful with report files.** The `peekdocs_standard_results.docx` and `.txt` files contain matched text from your documents — including any sensitive content that matched your search. Don't leave them on shared drives or send them via unencrypted email. Use **Clear Results** on the bottom toolbar to delete them when you're done.
- **Network folders work.** peekdocs can search documents on a shared network drive — just map or mount it so it appears as a regular folder on your computer (e.g., `Z:\` on Windows, `/Volumes/ShareName` on macOS, or an NFS/SMB mount on Linux) and point peekdocs at it. Tip: build a search index on your first search — subsequent searches query the local index instead of re-reading files over the network, which is much faster.
- **Don't store peekdocs results on shared drives.** If your search folder is on a shared network drive, the results files are written there too. Use `--output-dir` (or the Output Dir field in Advanced Search Options) to write results to a private local folder instead.
- **Review the error log.** `peekdocs_errors.log` may contain filenames that reveal what you were searching. Clear it with **Clear Error Log** when you're done.
- **Think before you print.** The highlighted `.docx` search reports contain matched text from your documents — which could include sensitive data. Printing creates a physical copy of that data. If you must print, treat the printout as confidential and shred it when done. Consider whether viewing the results on screen is sufficient.

---

## Dependencies

When you install peekdocs (`pip install git+https://github.com/exbuf/peekdocs.git` or `pipx install git+https://github.com/exbuf/peekdocs.git`), pip automatically downloads and installs everything peekdocs needs to read all 100+ file types. You don't have to install these yourself — they come along for the ride.

### What gets installed automatically

peekdocs has 17 direct dependencies, which pull in about 50 packages total. Here's what they do:

| Category | Packages | What they do |
|----------|----------|-------------|
| **Document readers** | python-docx, python-pptx, openpyxl, xlrd, odfpy, striprtf, EbookLib | Read Word, PowerPoint, Excel, LibreOffice, RTF, and ePub files |
| **PDF** | PyMuPDF | Read PDF files (the largest dependency — about 56 MB) |
| **Email** | extract-msg, olefile | Read Outlook .msg files and older Microsoft formats (.doc, .xls) |
| **Archives** | py7zr, rarfile | Read .7z archives (rarfile also needs UnRAR — see below) |
| **Images/OCR** | Pillow, pytesseract | Process images and call Tesseract for OCR |
| **Search** | rapidfuzz | Fuzzy (typo-tolerant) matching |
| **Report output** | fpdf2 | Generate PDF reports |
| **GUI** | customtkinter | The graphical interface |

**Total installed size:** approximately 244 MB on disk. Most of that is PyMuPDF (PDF reader, 56 MB), cryptography libraries (needed by the email reader, ~37 MB), and Pillow (image processing, 15 MB). The peekdocs code itself is about 2 MB.

### What you must install yourself

Most of these are covered in the [Prerequisites](../README.md#prerequisites) section of the README. Here's the complete list:

| Dependency | Required? | What it's for | How to install |
|-----------|-----------|--------------|----------------|
| **Python 3.10+** | Yes | Runs peekdocs | [python.org/downloads](https://www.python.org/downloads/) or your package manager |
| **tkinter** | For GUI only | The GUI framework (`peekdocs-gui`) | Included with Python on Windows. macOS: `brew install python-tk@3.13`. Linux: `sudo apt install python3-tk` |
| **Tesseract** | Optional | OCR — reading text from scanned PDFs and images (`-O` flag) | macOS: `brew install tesseract`. Linux: `sudo apt install tesseract-ocr`. Windows: [download installer](https://github.com/UB-Mannheim/tesseract/wiki) |
| **UnRAR** | Optional | Searching inside .rar archives | macOS: `brew install unrar`. Linux: `sudo apt install unrar`. Windows: comes with [WinRAR](https://www.win-rar.com/) or install standalone unrar |

**If you don't install the optional ones:** peekdocs still works fine — it just can't do OCR or search inside .rar files. If you try to use OCR without Tesseract, peekdocs tells you it's missing and shows install instructions. If you try to search a .rar file without UnRAR, it logs an error and continues with the other files.

**The CLI (`peekdocs`) works without tkinter.** You only need tkinter for the graphical interface (`peekdocs-gui`). If you only use the terminal, you can skip it.

---

## Getting Started with the Terminal

If you've never used a terminal before, this section walks you through everything from opening it to running your first search. If you're already comfortable with the command line, skip ahead to [GUI Mode](#gui-mode) or [Usage](#usage).

**Prefer not to use the terminal?** That's completely fine — run `peekdocs-gui` for a point-and-click interface instead. See [GUI Mode](#gui-mode).

**Want to try peekdocs on a sample corpus first?** Clone the repo and `cd samples/engineering_test && peekdocs TODO -r` returns hits across 35 source-code and engineering file types — no setup beyond installing peekdocs. Once you've seen it work, point peekdocs at your own folders.

### Which installation method did you use?

This matters for how you launch peekdocs:

- **If you installed with pipx** (`pipx install git+https://github.com/exbuf/peekdocs.git`): you're all set. `peekdocs` and `peekdocs-gui` work from any terminal, any folder, every time. Just open a terminal and start searching. Skip to [Step 1: Open your terminal](#step-1-open-your-terminal).

- **If you installed manually** (git clone + virtual environment): you need to **activate the virtual environment** every time you open a new terminal before peekdocs will work. If you close your terminal and open a new one, typing `peekdocs` will say "command not found" — this doesn't mean it's broken, it means the virtual environment isn't active. To fix it:

  **macOS/Linux:**
  ```bash
  cd /path/to/peekdocs      # navigate to where you cloned peekdocs
  source venv/bin/activate    # activate the virtual environment
  ```

  **Windows (Command Prompt):**
  ```cmd
  cd C:\path\to\peekdocs
  venv\Scripts\activate
  ```

  **Windows (PowerShell):**
  ```powershell
  cd C:\path\to\peekdocs
  venv\Scripts\Activate.ps1
  ```

  You'll see `(venv)` appear at the beginning of your command line — that means peekdocs is ready. You need to do this activation step each time you open a new terminal window.

  **Tired of activating every time?** Consider switching to pipx: `pip install pipx && pipx ensurepath && pipx install --force git+https://github.com/exbuf/peekdocs.git`. After restarting your terminal, peekdocs works everywhere without activation.

### What is a terminal?

A terminal (also called "command line," "command prompt," or "shell") is a text-based way to tell your computer what to do. Instead of clicking buttons, you type commands and press Enter. It looks intimidating at first, but you only need to learn a few commands to use peekdocs.

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
peekdocs budget
```

peekdocs will scan every supported file in the folder and show a summary:

```
Files searched: 47 (12.34 MB) — Found 23 match(es).
Elapsed time: 1.2 seconds, Cores used: 4 of 8
Results ==> /Users/YourName/Documents
  peekdocs_standard_results.txt (5.67 KB), peekdocs_standard_results.docx (42.31 KB)
```

That's it — you just searched 47 files in 1.2 seconds. Your results are saved in two files.

### Step 4: Open your results

The results are saved in the same folder where you ran the search (`peekdocs_standard_results.txt` and `peekdocs_standard_results.docx`). Open the Word report to see your matches highlighted in yellow:

**Windows:**
```cmd
start peekdocs_standard_results.docx
```

**macOS:**
```bash
open peekdocs_standard_results.docx
```

**Linux:**
```bash
xdg-open peekdocs_standard_results.docx
```

Or simply navigate to the folder in your file manager and double-click `peekdocs_standard_results.docx`.

### Step 5: Try a few more searches

Now that you know the basics, try these:

**Search for multiple words (finds files containing any of them):**
```bash
peekdocs budget revenue expenses
```

**Search for files containing ALL of the words:**
```bash
peekdocs -a budget revenue
```

**Search subfolders too:**
```bash
peekdocs -r budget
```

**Search only PDFs and Word documents:**
```bash
peekdocs -t pdf,docx budget
```

**Search for a regex pattern (e.g., a 9-digit ID with dashes):**
```bash
peekdocs -x "\d{3}-\d{2}-\d{4}"
```

**Find files that are MISSING a required term:**
```bash
peekdocs --inverse "Authorized Signature"
```

**Find dollar amounts in a range:**
```bash
peekdocs -R amount:1000..5000 budget
```

### Step 6: Get help

To see all available options with examples:

```bash
peekdocs -h
```

This shows every flag, organized by category (Search Modes, Filters, Output, Index, Settings), with examples for each one.

### Useful terminal tips

- **Up arrow** — press it to recall your previous command. Press it again to go further back. This is how you re-run or modify a previous search without retyping it.
- **Tab completion** — start typing a folder or file name and press Tab. The terminal fills in the rest. This saves typing and avoids typos.
- **Ctrl+C** — cancels a search in progress. peekdocs stops cleanly.
- **History** — your terminal remembers every command you've typed. Use the up/down arrows to scroll through them.

### What's next?

- See the [Flag Use Summary](#flag-use-summary) for a complete table of all options
- See the [Command Examples](#command-examples) table for 150+ example commands
- Try the GUI for a visual interface: just type `peekdocs-gui`
- Read [Your First Advanced Search](#your-first-advanced-search--step-by-step) for guided walkthroughs of regex, fuzzy, range queries, and more

---

## GUI Mode (Graphical User Interface)

If you prefer pointing and clicking over typing commands, peekdocs has a graphical interface. It works exactly like the terminal version — same search, same results, same reports — but with a familiar window instead of a command line.

**How to open it:**

You still need to open a terminal once to launch the GUI. If you used the manual install (Option B), activate the virtual environment first (`source venv/bin/activate` on Mac/Linux or `venv\Scripts\activate` on Windows — see the [README](../README.md#option-b-manual-install-with-git) for details). Then type:

```bash
peekdocs-gui
```

A window will appear. From here, everything is point-and-click — no more terminal commands needed. The GUI can do everything the terminal can do; you don't give up any features by using it.

The GUI window is organized into these regions, from top to bottom:

| Region | Description |
|--------|-------------|
| **Search Bar** | Search entry field with **▼ Recent Searches** dropdown (shows your last 10 search terms — stored in memory only, not saved to disk, lost when you close the app; different from Search History in the Tools menu which persists across sessions), **🔍 Standard Search** button (the main green action button — runs a keyword/regex/Boolean search using whatever is set in Advanced Search Options), **Regex Search** button (purple — opens the multi-pattern regex popup), **Search Wizard** button, **Save Search** button (saves the current search to the folder's collection so you can reload it later), and **Load Search ▼** button (opens a popup to load or delete saved searches). During a search the status line shows the number of terms being searched (e.g., "Searching (3 terms)...") |
| **Folder Bar** | Folder path entry, **Browse** button (select a folder), **Single File** button (select a single file to search — click the ✕ to clear), and **+Folder** button (add another folder for multi-folder search — folders are separated by semicolons) |
| **Advanced Search Options** | Collapsible panel with all search options (click to expand) |
| **Manage Indexes** | Collapsible toggle — **Auto-Refresh Index** interval selector, **Build Index(es)**, **Delete Index(es)**, **Index Status**, and **?** help |
| **Results** | After a search: clickable **View N matched file(s)** button on the status line opens a popup listing each matching file with its match count and line numbers (e.g., "contract.docx (3 matches — lines 12, 47, 89)"). Double-click a file to open it in its default application, or click **View Text (with line numbers)** to see the extracted file content with line numbers and highlighted matches. A **View N excluded file(s)** button appears alongside, showing files that were NOT searched grouped by reason (unsupported type, prior output files, oversized, hidden, etc.) — useful when the file count differs from a manual `find` or `ls` count. **View Report:** label with **TXT**, **DOCX**, **CSV**, **JSON**, and **PDF** buttons to open reports in each format, and **View Error Log** if any files could not be read. In the Results Preview pane, right-click to copy the selected text (or the current line) to the clipboard, and double-click a filename to open it in your default application |
| **Toolbar** | **User Guide**, **View All peekdocs Files**, **All Collections** (global view of saved searches across all folders), **Error Log**, **Maintenance**, **Text Size**, **Tooltips: ON/OFF** (toggle tooltips on or off — saved automatically), and **About** buttons |

**Your first GUI search:**

1. Type what you're looking for in the **Search Bar**
2. Click **Browse** in the **Folder Bar** to pick the folder containing your documents (your home folder is selected by default), or click **File** to pick a single file
3. Click **Run Search** (or press Enter)

**macOS vs Windows file picker:** On macOS, clicking **File** opens a file picker with a preview panel on the right — you can inspect the file's contents before selecting it. On Windows, the file picker does not include a preview. This is a difference in the operating systems, not peekdocs.
4. When the search finishes, a result summary appears. Click **DOCX** next to **View Report:** to view your results in a `.docx` file with matches highlighted in yellow. You can also click **TXT**, **CSV**, **JSON**, or **PDF** to open the report in other formats. The PDF report also highlights matches in yellow. If any files could not be read, a **View Error Log** button also appears — click it to open `peekdocs_errors.log` and see which files had problems and why

**Don't have Microsoft Word?** The .docx report opens with whatever word processor is installed on your computer. If you have [LibreOffice](https://www.libreoffice.org/download/download-libreoffice/) (free) installed and it's set as your default for .docx files, Windows will open it automatically. The .txt report can be opened on any computer with no additional software. You can also enable HTML output in Advanced Search Options for a highlighted report that opens directly in your browser. peekdocs avoids opening reports in Google Docs, Apple Pages, or any cloud-based application that may upload your data.


The Search Wizard has its own **Change Folder** button and operates independently — changing the folder inside the wizard does not change the Search Folder on the main screen until you click **Apply**, at which point the main screen folder is updated to match the wizard's folder, since the search runs from the main screen.

**Advanced Search Options:**

Click "Advanced Search Options" to expand a panel with additional settings — AND mode, recursive search, fuzzy matching, wildcards, OCR, regex, whole-word matching, expression mode, inverse search, exclude terms, file type filtering, proximity, context lines, CPU cores, max matches, range filters, specific files, save as, append to, output directory, additional output formats (CSV, JSON, PDF, HTML), timestamp filenames, and Delete on Close. Every terminal flag is available in the GUI. You don't need any of them for a basic search. Hover over any option to see a description of what it does. At the bottom of the panel are four buttons: **Inspect .peekdocsrc** shows the current saved settings (read-only). **Save Defaults** saves your current search terms, folder, and all options as defaults to `~/.peekdocsrc` — the next time you open the GUI, everything will be pre-filled. **Restore Settings** reloads saved defaults from `~/.peekdocsrc` into the GUI. **Reset** clears all fields and restores the GUI to its default state — but it only affects the current session. Your saved defaults in `~/.peekdocsrc` are not changed unless you also click **Save Defaults** after resetting.

**Save Search vs Save Defaults — what's the difference?**

These two buttons do different things:

| Button | Location | What it saves | Where it's stored | Purpose |
|--------|----------|--------------|-------------------|---------|
| **Save Search** | Main screen | Current search terms + all settings, by name | `.peekdocs_collection.json` in the search folder | Reusable named search |
| **Save Defaults** | Advanced Search Options | Your preferred default settings | `~/.peekdocsrc` in your home directory | Starting configuration for every future session |

Your selections in Advanced Search Options take effect immediately on the next Run Search — you do not need to press Save Defaults first. Save Defaults is only for making your choices persist across sessions.

**Manage Indexes:**

Click "Manage Indexes" below Advanced Search Options to expand index controls. Use the **Auto-Refresh Index** dropdown to keep the index updated automatically. Click **Build Index(es)** to create the index (all subfolders are included automatically). Use **Delete Index(es)** to remove the index, **Index Status** to view index info, or **?** for help on how indexes work. The **Search Using Index(es)** checkbox is inside Advanced Search Options — check it to use the index for your next search, or uncheck it to search files directly. Note: because the index always includes all subfolders, checking Use Index will return subfolder results even if Recursive is unchecked. To search only the top folder, uncheck both Use Index and Recursive.

Do not type flags (like `-a` or `-r`) into the **Search Bar** — it is only for search terms. Each checkbox and input field in **Advanced Search Options** handles the corresponding flag behind the scenes.

**Search Wizard:**

Click the **Wizard** button in the Search Bar to open the Search Wizard — a point-and-click regex builder. Instead of writing regex by hand, choose a profession-specific category and check the patterns you want:

| Category | Example patterns |
|----------|-----------------|
| **Common / General** | Dates, dollar amounts, phone numbers, email addresses |
| **Business / Finance** | Invoice numbers, purchase orders, account numbers |
| **Legal** | Case numbers, statute references, Bates numbers, court dockets |
| **Engineering / Technical** | Part numbers, serial numbers, measurements, tolerances |
| **Real Estate** | Parcel/APN numbers, square footage, lot/block, MLS numbers |
| **HR / Admin** | Employee IDs, phone numbers, email addresses |

Use the **Match mode** radio buttons to choose **OR** (match any selected pattern) or **AND** (all selected patterns must appear). You can also type a custom regex in the **Custom regex** field. A live preview shows the combined regex before you apply it.

When you click **Apply**, the wizard inserts the regex into the Search Bar and automatically enables the Regex checkbox. If the Search Bar already has text, you can choose to replace or append. The wizard remembers your selections between uses.

**Mixing wizard patterns with typed terms:**

You can combine wizard-generated patterns with terms you type manually. This is powerful because the wizard's OR logic is embedded *inside* the regex pattern using `|`, while the AND mode checkbox controls how *separate* search terms relate to each other. They operate at different levels and don't conflict.

For example, to find paragraphs that contain a phone number or email address *and* the word "invoice":

1. Open the Wizard, select **Common / General**, check **Phone Number** and **Email Address** (with OR mode), click **Apply**
2. The Search Bar now contains one regex term: `(\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})|([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})`
3. After the regex, type a space and then `invoice` — the Search Bar now has two terms
4. Check the **AND mode** checkbox in Advanced Search Options

The search finds paragraphs where *both* conditions are true: at least one phone number or email appears, *and* the word "invoice" appears. The OR stays inside the wizard's regex, and the AND applies between the two separate search terms.

You can also build up the Search Bar in multiple passes — use the wizard once, append, type some words, open the wizard again with a different category, and append again. Each append adds to what's already there.

**Note:** The wizard enables regex mode. If you manually type additional terms containing special characters (`.` `+` `(` `)` `[` `]` etc.), escape them with `\` — for example, `cost\+fees`. Plain words like `budget` need no escaping.

The Search Wizard shows the current **Search Folder** at the top of the window with a **Change Folder** button. You can switch folders without closing the wizard. When you click **Apply**, the main screen's Search Folder is updated to match the wizard's folder (since the search runs from the main screen).

**Tools Menu:**

The **Tools** button (top-right of the Search tab) opens a menu of built-in utilities that go beyond search. All folder-based tools respect the current **Search Folder** and **Recursive** checkbox setting.

| Tool | What it does |
|------|-------------|
| **File Inventory** | Scans the folder and shows a summary: total file count, total size, breakdown by file type (extension, count, size), oldest and newest files with dates, and subfolder count. Click **Save Report** to export as a text file. |
| **Duplicate Finder** | Finds groups of identical files by comparing content (MD5 hash), not just filenames. Two files with different names but identical content are flagged. Shows how many extra copies exist and how much disk space they waste. Click **Save Report** to export. |
| **Large Files** | Lists the 50 largest files in the folder with their sizes. Useful for finding disk hogs — large files you may have forgotten about. |
| **Empty Files** | Finds zero-byte files. These are completely empty — often failed downloads, placeholders, or leftover junk that can be safely deleted. |
| **Recent Changes** | Shows files modified in the last 7, 30, and 90 days, grouped by time period. Each file is shown with its modification date and size. Useful for seeing what changed recently in a folder you haven't visited in a while. |
| **Protected Files** | Detects password-protected and encrypted files: PDFs, Word/Excel/PowerPoint (both modern and legacy formats), ODF documents, ZIP/7z/RAR archives. These files cannot be searched by peekdocs. The report tells you exactly which files are locked so you can decide whether to unprotect them. Click **Save Report** to export. |
| **Search History** | Every search you run is automatically logged with the date, search terms, number of matches, number of files searched, and elapsed time. Open Search History to review past searches — most recent first. Click **Clear History** to delete the log. History is stored in `~/.peekdocs_history.json` and persists across sessions. |
| **Bookmarks** | Pin files for quick access. After a search, right-click any file in the **Matched Files** popup and choose **Add Bookmark**. Open Bookmarks from the Tools menu to see all pinned files. Double-click to open a file; right-click to remove it. Bookmarks are stored in `~/.peekdocs_bookmarks.json` and persist across sessions. |
| **Search Suites** | Group multiple saved searches into a named suite and run them all at once. Create a suite, add saved searches to it, reorder them with Move Up / Move Down, select your output formats (TXT and DOCX are always generated; HTML, CSV, JSON, and PDF are optional checkboxes in the popup), and click **Run Suite**. Each search runs independently with its own settings (AND/OR, regex, recursive, etc.), and results are organized by search in a single combined highlighted report. Every suite report (TXT, DOCX, HTML) opens with a **Section summary** listing each saved search's name with its match count and file count, so a search that finds 50 matches is not buried under a previous section that found 5000 — and the HTML version turns each summary line into an anchor link that jumps to that section. The GUI Results Preview shows the same summary plus the first 20 matches per section with the standard yellow match-highlighting. Output format selection is independent from Advanced Search Options. Suites are stored in the folder's `.peekdocs_collection.json` file alongside saved searches. The suite popup always uses the Search Folder from the main page — if you change the folder while the popup is open, it closes automatically because suites and saved searches belong to a specific folder. Reopen it to see the new folder's suites. Use cases: pre-publication checklists, quarterly audits, onboarding reviews, or any recurring workflow. Also available from the CLI: `peekdocs --suite "My Suite"` auto-locates the folder a suite was saved in, and `peekdocs --list-suites` shows every suite peekdocs knows about. See [Suite Use Cases](#search-suite-use-cases). |
| **Manage Indexes** | Build, delete, and refresh search indexes for faster repeated searches. See [Search Index](#search-index) for details. |
| **Schedule Search** | Generates a ready-to-paste scheduling command so peekdocs runs automatically on a timer — no terminal experience required. Pick a saved search suite or regex collection, choose a folder, set the frequency (daily, weekly, or monthly) and time, and the dialog builds the correct command for your operating system: a crontab entry for Mac/Linux or a schtasks command for Windows. Step-by-step instructions walk you through pasting the command into your system's scheduler. Options include `--timestamp` (each run produces uniquely named reports instead of overwriting) and `--stdout` (also saves JSON output to a file). Click **Copy to Clipboard** to copy the generated command. Reports are saved automatically in the search folder each time the scheduled search runs. |
| **View All peekdocs Files** | Wondering what files peekdocs created in your folder? Lists every peekdocs-created file in the Search Folder and subfolders: standard-search reports (`peekdocs_standard_results.*`), regex-search reports (`peekdocs_regex_results.*`), suite reports (`peekdocs_suite_results.*`), saved reports (`peekdocs_report_*`), accumulated reports (`peekdocs_accumulated_*`), the search index (`.peekdocs.db`), saved searches (`.peekdocs_collection.json`), the error log (`peekdocs_errors.log`), and your settings (`~/.peekdocsrc`). Each file is shown with its size and last-modified date. Files only appear if they exist — if you haven't saved any searches yet, `.peekdocs_collection.json` won't be listed. To delete peekdocs files, use **Clear Files** in the Tools menu — it lets you choose exactly which files to remove. Your saved searches and settings are protected and never appear in Clear Files. |

The Tools menu also includes: **All Collections** (finds saved searches across folders), **Error Log**, **Appearance** (Dark, Light, or System — follows your OS setting), **Text Size**, and cleanup options (Clear Files, Clean Up Practice Files). **Tooltips** is toggled from the **Tooltips: ON/OFF** button on the bottom row of the main screen (not in the Tools menu). Your **Appearance**, **Text Size**, and **Tooltips** choices are all saved automatically when changed — no need to click Save Defaults. They persist between sessions in `~/.peekdocsrc`.


## Why peekdocs Instead of grep?

grep is an excellent tool for searching plain text files. However, most real-world document folders contain a mix of PDFs, Word documents, spreadsheets, emails, and other binary formats that grep cannot read. To search those with grep, you would need to install separate converters for each format, write a script to detect file types and pipe each through the right converter, and glue the results together — a fragile pipeline that can be hundreds of lines long.

peekdocs handles all of this in a single command. Here is what each tool can do:

| Capability | grep | peekdocs |
|---|---|---|
| Plain text files (.txt, .log, .csv) | Yes | Yes |
| PDF text extraction | Manual piping required | Built in |
| Word documents (.docx) | Manual piping required | Built in |
| Excel spreadsheets (.xlsx) | Manual piping required | Built in |
| PowerPoint, email, EPUB, RTF, ODT | Each needs a different converter | Built in |
| OCR (scanned PDFs and images) | Manual piping required | Built in (`-O` flag) |
| Highlighted .docx, .pdf, .html reports | No | Yes |
| CSV and JSON export | Manual scripting | Built in (`-o csv,json`) |
| Boolean expressions | No | Yes (`-e "A AND (B OR C)"`) |
| Proximity search (terms near each other) | No | Yes (`-p 5`) |
| Fuzzy matching (typo-tolerant) | No | Yes (`-z`) |
| Range queries (amounts, dates, file size) | No | Yes (`-R amount:1000..5000`) |
| Saved searches and search suites | No | Yes |
| Regex collections (batch patterns) | Manual scripting | Built in (`--regex-collection`) |
| Search index with auto-refresh | No | Built in (`--index`) |
| GUI | No | Yes |
| Cross-platform consistency | Varies (GNU vs BSD grep) | Identical on all platforms |

**When to use grep:** For quick plain-text searches in a terminal, grep is faster and simpler. Use it when all your files are plain text and you don't need reports.

**When to use peekdocs:** For searching across mixed-format documents (PDFs, Word, Excel, email archives), producing shareable highlighted reports, running saved pattern collections, or giving a non-terminal user a search tool with a GUI.

For a more detailed comparison, see [Why peekdocs?](../README.md#why-peekdocs) in the README.

## Usage

If you installed with pipx (Option A), peekdocs is always ready — just open any terminal. If you used the manual install (Option B), activate the virtual environment first each time you open a new terminal (`source venv/bin/activate` on Mac/Linux or `venv\Scripts\activate` on Windows — see the [README](../README.md#option-b-manual-install-with-git)) — you'll see `(venv)` appear in your prompt. Then navigate to the folder containing your documents and run peekdocs with your search terms. See the [Command Examples](#command-examples) table for usage.

### Phrase search (quoted terms)

By default, peekdocs treats each space-separated word as a separate search term. To search for a multi-word phrase as a single unit, enclose it in **double quotes**:

```bash
peekdocs '"annual report"'             # find the exact phrase "annual report"
peekdocs -a '"Q4 2025" budget'         # AND mode: find "Q4 2025" AND budget
```

This works in both the terminal and the GUI — in the GUI, type `"annual report"` directly into the Search Terms field. Phrase searches also work inside Boolean expressions: `peekdocs -e '"annual report" AND (2023 OR 2024)'`.

Without quotes, `annual report` becomes two terms (`annual` and `report`) joined by OR logic (or AND if `-a` is used), which is usually not what you want for a phrase. Use quotes when you need the words to appear adjacent to each other in the same order.

### Regex search

**What are Regex searches?**
Regex (short for "regular expression") lets you search for patterns rather than exact text. Instead of searching for a specific phone number, you can search for any phone number. Instead of one date, you can find all dates in any format.

Think of it as a wildcard search on steroids. For example, `\d{3}-\d{3}-\d{4}` finds any phone number like 555-123-4567, while `\$\d+` finds any dollar amount.

Regex is powerful but can look intimidating at first. See the table below for common patterns you can copy and use.

#### Common Regex Search Patterns

Below is a list of common regex patterns you can copy and paste into your search. Remember to enclose in quotes. The **Report translation** column shows how peekdocs describes each pattern in the plain-English report header (see [Command Translation](#command-translation) below).

| Pattern | Matches | Example | Report translation |
|---------|---------|---------|-------------------|
| `\d{3}-\d{3}-\d{4}` | US phone numbers | 555-123-4567 | a US phone number |
| `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,}` | Email addresses | jane@example.com | an email address |
| `\d{1,2}/\d{1,2}/\d{2,4}` | Dates (MM/DD/YYYY) | 03/17/2026 | a date |
| `\d{4}-\d{2}-\d{2}` | Dates (YYYY-MM-DD) | 2026-03-17 | — |
| `\$\d+(\.\d{2})?` | Dollar amounts | $45.99 | a dollar amount |
| `\d{3}-\d{2}-\d{4}` | 9-digit ID with dashes | 123-45-6789 | — |
| `\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}` | IP addresses | 192.168.1.1 | an IP address |
| `https?://\S+` | URLs | https://example.com | a URL |
| `\b[A-Z]{2,}\b` | Acronyms (all caps) | NASA, FBI | — |
| `\b\d{5}(-\d{4})?\b` | US ZIP codes | 12345 or 12345-6789 | a US ZIP code |
| `\(\d{3}\)\s?\d{3}-\d{4}` | Phone with area code parens | (555) 123-4567 | a phone number with area code |
| `\b[A-Z][a-z]+\s[A-Z][a-z]+\b` | Proper names (two capitalized words) | John Smith | — |
| `\b\d+%` | Percentages | 92% | a percentage |
| `Q[1-4]\s?\d{4}` | Fiscal quarters | Q1 2026 | a fiscal quarter |

## Flag Use Summary

peekdocs has twenty-nine flags that can be mixed and matched:

| Flag&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Purpose |
|------------|---------|
| `-a` (all) | AND logic — all terms must appear in the same line. (For PDF and Word documents, a "line" is typically a paragraph since each paragraph is extracted as one line. For plain text files, a line is a literal line. If your terms might span multiple lines, use `-p N` (proximity) to find terms within N words of each other, or `-B`/`-A` for surrounding context.) |
| `-c N` (cores) | Number of CPU cores for parallel search (default: half of available cores). For small numbers of files (fewer than 10), single-threaded mode is used automatically |
| `-e` (expression) | Boolean expression search — use AND, OR, NOT, parentheses, and range specs for complex queries. See [Boolean Expression Search](#boolean-expression-search) |
| `-f` (files) | Search specific files (comma-separated, e.g., `report.pdf,notes.txt`) |
| `-m N` (max-matches) | Maximum matches included in reports (default: 1,000). Use `0` for no limit |
| `--max-file-size N` | Skip files larger than N MB (default 100, 0 = no limit) |
| `-n` (not) | Exclude lines matching specified terms (comma-separated, e.g., `-n draft,obsolete`) |
| `-o` (output) | Additional output formats — `csv`, `json`, `pdf`, `html`, or any combination (`csv,json,pdf,html`). The `.txt` and `.docx` reports are always created; `-o` adds extra formats |
| `-O` (OCR) | Enable OCR for scanned PDFs and image files (requires [Tesseract](#prerequisites)) |
| `-p N` (word-proximity) | Word proximity — find terms within N words of each other (same line) |
| `-P N` (line-proximity) | Line proximity — a genuinely useful feature, especially for programmers searching code. Find terms within N lines of each other. Works on all file types, but what a "line" means varies by format: for plain text and source code, a line is a literal line; for Word (.docx), a line is a paragraph; for Excel, a line is a row; for PDF, a line is a text block (variable). Most reliable and intuitive for plain text and source code files. `-P` implies AND across lines — if combined with `-a`, the `-a` is automatically handled |
| `-q` (quiet) | Suppress the output banner (file list, warnings, and report paths still shown) |
| `-qq` (minimal) | Minimal output — show only the Found/Elapsed summary lines (no banner, no file list, no warnings, no report paths). Useful for scripting |
| `-R SPEC` / `--range` | Range filter — filter by value ranges in content or file metadata. Repeatable. See [Range Queries](#range-queries) |
| `-r` (recursive) | Search subdirectories recursively |
| `-s` (save) | Archive results — copies peekdocs_standard_results files to peekdocs_report_your_file_name.docx (and .txt). The peekdocs_report_ prefix is added automatically so archived files are never re-searched. Does not erase the original results files, but they are overwritten on the next search. Example: `peekdocs -s my_report` |
| `-sa` (save-append) | Search and auto-append — runs the search normally, then appends the results to peekdocs_accumulated_your_file_name.txt (and .docx). Use this to accumulate results from multiple searches into one file. The peekdocs_accumulated_ prefix is added automatically.<br><br>Example: `peekdocs -sa my_report budget revenue` results in your search for the terms budget and revenue being saved in file peekdocs_accumulated_my_report.docx (and .txt). |
| `-t` (types) | Filter by file type (comma-separated, e.g., `pdf,docx`) |
| `--timestamp` (timestamp) | Add a timestamp suffix to report filenames (e.g., `peekdocs_standard_results_20260327_143022.txt`). Each search produces uniquely named files so previous results are preserved |
| `--hash` (hash) | Compute SHA-256 of each matched file's raw bytes and add a `sha256` field to JSON output (`--stdout` and `-o json`). File-identity / integrity-verification use. Hashing happens once per matched file (not per match) so the overhead is bounded by match count, not files searched. See [Automation and IT Use → JSON output](#json-output---stdout-schema) |
| `--dry-run` (dry-run) | Show the scope of a search without running it. Walks file discovery (`-r`, `-t`, `-f`, `-O`, `--max-file-size` all respected) and prints the count, total size, and per-extension breakdown. No content is read, no reports are written, the index is not touched, and the run is not added to `~/.peekdocs_runs.log`. Search terms are accepted but ignored — they don't affect scope. Add `--stdout` for JSON output. Useful as a "what would this do?" preflight on network shares and large folders. **Standard search only in this release** — `--dry-run` with `--suite` or `--regex-collection` exits with an error rather than running silently. |
| `--no-log` (no-log) | Skip writing this single run to `~/.peekdocs_runs.log`. The run log is enabled by default and captures every search-mode invocation. Persistent opt-out: `--config run_log=false`. See [Automation and IT Use → Per-run structured log](#per-run-structured-log) |
| `--runs` (runs) | Show the last 20 runs from the log in a readable table. `--runs N` shows the last N. `--runs --json` re-emits the raw JSON Lines for piping. The `--runs` command itself is never logged. See [Per-run structured log](#per-run-structured-log) |
| `--diff OLD NEW` (diff) | Compare two peekdocs JSON outputs (from `--stdout` or `-o json`) and report what changed: NEW files matching, REMOVED files, CHANGED match counts, MODIFIED file content (when both were produced with `--hash`). Default output is human-readable; add `--json` for a structured payload. Exit codes are diff-flavored: 0 = no actionable change, 1 = new findings detected, 2 = error — so `peekdocs --diff peekdocs_snapshot_yesterday.json peekdocs_snapshot_today.json \|\| alert` works. Also available in the GUI: `Tools → Diff Snapshots`. See [Diff between runs](#diff-between-runs) |
| `--on-match CMD` (on-match) | Run an external command (notification hook) when a search finds matches. Fires only on exit 0; skipped for no-match runs, errors, `--dry-run`, and informational commands. The command is invoked without a shell — quoted arguments work, pipes/redirects do not (wrap them in a script). 30-second timeout. Hook receives `PEEKDOCS_MATCH_COUNT`, `PEEKDOCS_FILE_COUNT`, `PEEKDOCS_ERROR_COUNT`, `PEEKDOCS_ELAPSED_SECONDS`, `PEEKDOCS_ARGV`, `PEEKDOCS_CWD`, and `PEEKDOCS_REPORT_TXT` / `_DOCX` / `_JSON` / `_HTML` / `_CSV` / `_PDF` (whichever were written). Persistent default: `--config on_match=/path/to/script`. Override per-run with `--on-match ""` (empty string) to disable. See [Notification hook](#notification-hook) |
| `-w` (wildcard) | Wildcard pattern search — `*` matches any characters, `?` matches one character |
| `-W` (whole-word) | Whole-word matching — matches complete words only (`bob` matches "bob" but not "bobcat") |
| `-x` (regex) | Regex pattern search (case-insensitive) |
| `-z` (fuzzy) | Fuzzy matching — find approximate matches (e.g., typos like "budgt" matching "budget") |
| `--check` (check) | Verify installation — checks Python version, dependencies, Tesseract, and disk space |
| `--config` (config) | View, set, or remove saved settings. See [Saved Settings](#saved-settings-optional) |
| `--suite NAME` (suite) | Run a search suite — executes all saved searches in the named suite and produces a combined report (`peekdocs_suite_results.txt` and `.docx`). Auto-locates the folder from a global suite index, so you can run it from any directory. Create suites in the GUI (Tools → Search Suites). See [Suite Use Cases](#search-suite-use-cases) |
| `--list-suites` (list-suites) | List every known suite with its folder and search count. Add `--rescan` to re-discover suites by walking `~/Documents` and `~/Desktop` for `.peekdocs_collection.json` files (useful after moving folders or copying them in from another machine) |
| `--regex-collection NAME` | Run a saved regex collection by name — executes each enabled pattern separately with per-pattern results. Create collections in the GUI (Regex Search → Save Collection As). Add `-r` for recursive, `-d DIR` for a specific directory, `--stdout` for JSON output. Use `--regex-collection --list` to list all saved collections. See [Regex Collection Use Cases](#regex-collection-use-cases) below |
| `--index` (index) | Build or rebuild the search index for faster repeated searches. See [Search Index](#search-index-optional) |
| `--clear` (clear) | Delete `peekdocs_standard_results*`, `peekdocs_regex_results*`, and `peekdocs_suite_results*` files in the current directory |
| `--clear-all` (clear-all) | Delete all peekdocs output files — results, saved reports (`peekdocs_report_*`, `peekdocs_accumulated_*`), error log, and search index. Does not touch saved searches (`.peekdocs_collection.json`) or settings (`~/.peekdocsrc`) |
| `--index-clear` (index-clear) | Delete the search index |
| `--index-refresh` (index-refresh) | Incrementally update the index — add new files, re-index changed files, remove deleted files |
| `--index-status` (index-status) | Show index info — file count, line count, database size, creation date, and settings |
| `--inverse` (inverse) | Inverse search — list files that do NOT contain the search terms. See [Inverse Search](#inverse-search) |
| `--open FMT` (open) | Automatically open the report when the search finishes. Specify the format: `docx`, `txt`, `csv`, `json`, `pdf`, or `html`. For csv/json/pdf/html, the output format is auto-generated if not already enabled — no need to also specify `-o`. Opens in a safe local application (cloud apps are blocked) |
| `--output-dir PATH` (output-dir) | Write all output files (reports, error log, CSV, JSON, PDF) to the specified directory instead of the search folder |
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
- `-s` is used separately after a search to save results: `peekdocs -s my_report`
- `-sa` always needs its filename immediately after it (e.g., `-sa my_report`)
- `-sa` appends to existing peekdocs_accumulated files, allowing you to accumulate results from multiple searches
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
- `-O` requires Tesseract to be installed on your system (see the [README](../README.md#prerequisites) for installation instructions)
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
- `-o` supported formats are `csv`, `json`, `pdf`, and `html`
- `-o` does not replace the default `.txt` and `.docx` reports — it adds additional output files
- `-o csv` creates `peekdocs_standard_results.csv` with columns: filename, folder, line_number, matched_text
- `-o json` creates `peekdocs_standard_results.json` with metadata and a matches array
- `-o csv,json` creates both files; `-o csv,json,pdf,html` creates all four
- `-m` always needs its count immediately after it (e.g., `-m 5000`)
- `-m 0` disables the match cap entirely — all matches are included in reports
- `-m` defaults to 1,000 when not specified. This prevents very large result sets from causing slow report generation
- `-m` can be set permanently via `--config max_matches=5000` or in the GUI's Advanced Search Options panel
- `--timestamp` adds a `_YYYYMMDD_HHMMSS` suffix to report filenames so each search produces unique files (e.g., `peekdocs_standard_results_20260327_143022.txt`)
- `--timestamp` is off by default in the GUI. Check the Timestamp checkbox in Advanced Search Options to enable it — each search then produces uniquely named files instead of overwriting the previous results
- `--timestamp` and `-s` are independent — `-s` looks for `peekdocs_standard_results.txt` by name, so it only works when `--timestamp` is not used
- `--output-dir` writes all output files to the specified directory instead of the search folder. The search still runs in the current directory — only the output destination changes
- `--output-dir` creates the directory if it doesn't exist
- `--output-dir` works with all other flags including `--timestamp`, `-s`, `-sa`, and `-o`
- `--inverse` flips the search — instead of showing files WITH matches, it shows files WITHOUT matches
- `--inverse` works with all search modes (OR, AND, regex, fuzzy, wildcard) and all other flags
- `--inverse` reports and exports list the files that are missing the search terms
- `--inverse` exit code: 0 if files without matches were found, 1 if all files matched
- `--inverse` is useful when you want to find files that are missing something they should contain
- `-R` (or `--range`) always needs its range spec immediately after it (e.g., `-R amount:1000..5000` or `--range amount:1000..5000`)
- `-R` syntax: `field:min..max` — use `field:min..` for open-ended minimum, `field:..max` for open-ended maximum. Both bounds are inclusive
- `-R` content fields: `date`, `amount`, `number`, `percent`, `age`, `time` — these extract values from document text and filter lines
- `-R` metadata fields: `filesize`, `filedate` — these filter entire files by their properties before text scanning
- `-R` is repeatable — multiple `-R` flags combine with AND logic (all must match)
- `-R` can be used alone (range-only search) or combined with text search terms
- `-R filesize` accepts size suffixes: `K` (kilobytes), `M` (megabytes), `G` (gigabytes), `T` (terabytes). Example: `-R filesize:1M..10M`
- `-R` works with all other flags including `-a`, `-e`, `-x`, `-z`, `-w`, `-r`, `-t`, and `-O`
- `-R` range specs can also be embedded directly inside `-e` expressions (e.g., `-e "budget AND amount:1000..5000"`). Metadata fields only work with `-R`, not inside expressions

### Regex Collection Use Cases

The `--regex-collection` flag lets you run saved regex collections from the command line. Collections are created in the GUI (Regex Search → Save Collection As) and can contain up to 10 regex patterns each. Here are some practical scenarios:

**Code patterns** — Create a collection with patterns for TODO/FIXME comments (`(TODO|FIXME|HACK|XXX)\b`), deprecated function calls, and debug print statements. Run it against your source code to catch loose ends:

```
peekdocs --regex-collection "code patterns" -d ~/projects/myapp -r
```

**Documentation review** — Build a collection with patterns for broken links (`\[.*?\]\(.*?\)`), placeholder text (`(TBD|TODO|FIXME)`), and missing sections. Run it against your docs folder:

```
peekdocs --regex-collection "documentation review" -d ~/projects/myapp/docs -r --stdout
```

**Financial document check** — Create a collection with patterns for dollar amounts (`\$[\d,]+(\.\d{2})?`), account numbers (`\b\d{8,12}\b`), and date formats. Run it against a folder of invoices or reports:

```
peekdocs --regex-collection "financial" -d ~/Documents/invoices
```

**Scheduled log monitoring** — Set up a cron job (macOS/Linux) or Task Scheduler entry (Windows) to run a collection against log files on a regular schedule. Results are appended to a JSON file for later review:

```
# Every Monday at 8am — scan server logs for error patterns
0 8 * * 1 cd /var/log && peekdocs --regex-collection "error patterns" -r --stdout >> /tmp/weekly_errors.json
```

**Running several collections in one pass** — `--regex-collection` takes one collection at a time. To run several in sequence (e.g., for IT scans or daily sweeps), use a shell loop or the Python API. Add `--timestamp` so each run produces uniquely named reports (`peekdocs_regex_results_YYYYMMDD_HHMMSS.txt`/`.docx`) instead of overwriting the previous run.

*Shell loop (macOS/Linux):*

```
for c in "code patterns" "log analysis" "invoice extraction"; do
  peekdocs --regex-collection "$c" -d /path/to/folder -r --timestamp
done
```

*Shell loop (Windows PowerShell):*

```
foreach ($c in "code patterns","log analysis","invoice extraction") {
  peekdocs --regex-collection $c -d C:\path -r --timestamp
}
```

*Python API (single process, programmatic results):*

```python
from peekdocs.api import list_regex_collections, run_regex_collection

if __name__ == "__main__":
    for name in list_regex_collections():
        result = run_regex_collection(name, directory="/path", recursive=True)
        print(f"{name}: {result.total_matches} matches in {result.elapsed:.1f}s")
```

The `if __name__ == "__main__":` guard is **required** when scripting the peekdocs API on macOS or Windows — `multiprocessing` spawned children re-import the calling script. Without the guard, the script crashes with `RuntimeError`.

The Python API is the most reliable way to enumerate and run every saved collection in one pass — `list_regex_collections()` returns a clean list of names you can iterate over, and the API returns results in memory rather than writing report files. Pair any of these with cron (macOS/Linux) or Task Scheduler (Windows) for recurring runs. Note: Search Suites group *saved searches*, not regex collections — they don't replace this pattern.

**Zero-match runs write no report.** If a `--regex-collection` run finds no matches, no `peekdocs_standard_results.{txt,docx}` file is written for that run (with or without `--timestamp`). The CLI still prints the summary line and exits with status 1. This matters for batch loops where you want a permanent record of every run: use `--stdout > results.json` instead to always capture a file, or rely on the JSON exit-code (0 = matches, 1 = no matches) to detect empty runs. Search Suites are different — `--suite` always writes a report file even when every search returns zero matches.

**Listing and managing collections** — See all saved collections before running one:

```
peekdocs --regex-collection --list
```

### Search Suite Use Cases

The `--suite` flag runs a saved search suite from the command line. Suites live in `.peekdocs_collection.json` inside each search folder, but peekdocs keeps a small global index (`~/.peekdocs_suites_index.json`) so the CLI can find a suite by name from any working directory. Concretely:

- `peekdocs --suite "monthly review"` — runs in the current folder if a suite by that name exists there; otherwise consults the global index and auto-locates the right folder. Reports are written next to the documents, in the folder where the suite is saved.
- `peekdocs --suite ~/Documents/MyDocs/"Example 1"` — explicit form, useful for disambiguating when the same suite name exists in several folders, or when scripting against a known path. Only the part containing whitespace needs quotes; the folder path can be unquoted.
- If the same suite name exists in more than one folder (e.g., you cloned "monthly review" into several client directories) and you used the bare-name form, the CLI prints every match and asks you to re-run with the full path.
- `peekdocs --list-suites` shows every known suite, its folder, and the number of saved searches it contains. Use `--list-suites --rescan` to walk `~/Documents` and `~/Desktop` for `.peekdocs_collection.json` files — handy after moving folders or copying a project in from another machine.

The index is updated automatically every time you create, rename, or delete a suite in the GUI. On first CLI use, peekdocs seeds the index by scanning your search history and the same two directories. Add `--timestamp` to produce uniquely named reports (`peekdocs_suite_results_YYYYMMDD_HHMMSS.txt`/`.docx`) instead of overwriting `peekdocs_suite_results.txt`/`.docx` on each run.

**Why does this only apply to suites, not regex collections?** Suites group *saved searches*, which live per folder inside each folder's `.peekdocs_collection.json` — so a suite has to live in the same file as the searches it references, and the same name can legitimately exist in different folders pointing at different searches. Regex collections are self-contained patterns with no per-folder dependencies; they all live in a single global file (`~/.peekdocs_regex_collections.json`) under one shared namespace, so `peekdocs --regex-collection "name"` is always unambiguous and never needs a folder hint.

**Running several suites by name from anywhere** — Loop through suite names; no `cd` needed when each name is unique.

*Shell loop (macOS/Linux):*

```
for s in "monthly review" "quarterly review" "vendor audit"; do
  peekdocs --suite "$s" --timestamp
done
```

*Shell loop (Windows PowerShell):*

```
foreach ($s in "monthly review","quarterly review","vendor audit") {
  peekdocs --suite $s --timestamp
}
```

Each suite runs in the folder where it was saved, and reports land there.

**Running the same suite across several folders** — When the same suite name exists in multiple folders (`monthly review` in three different client directories), pass the full path so each iteration targets one folder unambiguously.

*Shell loop (macOS/Linux):*

```
for d in /clients/acme /clients/globex /clients/initech; do
  peekdocs --suite "$d/monthly review"
done
```

*Shell loop (Windows PowerShell):*

```
foreach ($d in "C:\clients\acme","C:\clients\globex","C:\clients\initech") {
  peekdocs --suite "$d\monthly review"
}
```

Reports stay in each folder (`acme/peekdocs_suite_results.txt`, etc.) with no overwriting since they're in different locations. Add `--timestamp` if you plan to re-run periodically and want history preserved.

**Python API (cleanest — programmatic results, no report files):**

```python
from peekdocs.api import list_suites, run_suite

if __name__ == "__main__":
    folder = "/path/to/folder"
    for name in list_suites(directory=folder):
        result = run_suite(name, directory=folder)
        print(f"{name}: {result.total_matches} matches across {len(result.search_results)} searches ({result.elapsed:.2f}s)")
```

The `if __name__ == "__main__":` guard is **required** on macOS and Windows — see the earlier note in [Regex Collection Use Cases](#regex-collection-use-cases) or the [API Reference](API.md).

`list_suites()` returns a dict of suite names to their member search lists. `run_suite()` returns a `SuiteResult` with `total_matches`, `search_results` (a list of per-search results), `elapsed`, and `skipped_searches`. The API returns results in memory without writing reports, so you can collect everything and build a custom combined report. Pair any of these with cron (macOS/Linux) or Task Scheduler (Windows) for recurring runs.

### Command Examples

| # | Search Type | Command |
|---|-------------|---------|
| | **Basic Searches** | |
| 1 | Single word | `peekdocs budget` |
| 2 | Multiple terms (OR logic) | `peekdocs budget revenue expenses` |
| 3 | Multi-word phrase | `peekdocs "annual report"` |
| 4 | Combine phrases and single terms | `peekdocs "computer analysis" energy generation` |
| 5 | Require ALL terms (AND logic) | `peekdocs -a budget revenue expenses` |
| | **Filter by File Name** | |
| 6 | Search a specific file | `peekdocs -f report.pdf budget` |
| 7 | Search multiple specific files | `peekdocs -f report.pdf,notes.txt budget` |
| 8 | Specific files with AND logic | `peekdocs -f report.pdf,data.csv -a budget revenue` |
| 9 | Specific file recursive | `peekdocs -f report.pdf -r budget` |
| 10 | Specific file with regex | `peekdocs -f report.pdf -x "\d{3}-\d{3}-\d{4}"` |
| 11 | Specific file with context lines | `peekdocs -f report.pdf -B 3 -A 3 budget` |
| 12 | Specific file, regex, AND | `peekdocs -f report.pdf -x -a "\d{3}" "\$\d+"` |
| | **Filter by File Type** | |
| 13 | Search only specific file types | `peekdocs -t pdf,docx budget` |
| 14 | File type filter with OR search | `peekdocs -t pdf,docx budget revenue` |
| 15 | File type filter with AND search | `peekdocs -a -t csv,xlsx budget revenue` |
| | **Proximity Searches** | |
| 16 | Terms within 5 words of each other | `peekdocs -p 5 budget revenue` |
| 17 | Proximity with file type filter | `peekdocs -p 5 -t pdf,docx budget revenue` |
| 18 | Proximity with recursive search | `peekdocs -p 5 -r budget revenue` |
| 19 | Proximity with specific file | `peekdocs -p 5 -f report.pdf budget revenue` |
| 20 | Line proximity (within 3 lines, implies AND) | `peekdocs -P 3 budget acme` |
| | **Recursive (Subdirectory) Searches** | |
| 21 | Search all subdirectories | `peekdocs -r budget` |
| 22 | Recursive with AND logic | `peekdocs -r -a budget revenue expenses` |
| 23 | Recursive with file type filter | `peekdocs -r -t pdf,docx budget` |
| 24 | Recursive, AND, and file type filter | `peekdocs -r -a -t txt budget revenue expenses` |
| | **Regex Pattern Searches** | |
| 25 | Search for phone numbers | `peekdocs -x "\d{3}-\d{3}-\d{4}"` |
| 26 | Search for email addresses | `peekdocs -x "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,}"` |
| 27 | Regex with AND logic | `peekdocs -x -a "\d{3}" "\$\d+\.\d{2}"` |
| 28 | Regex with file type filter | `peekdocs -x -t pdf,docx "\$\d+(\.\d{2})?"` |
| 29 | Regex recursive | `peekdocs -x -r "\d{3}-\d{3}-\d{4}"` |
| 30 | Regex, recursive, file type filter | `peekdocs -x -r -t txt,csv "\b2026-\d{2}-\d{2}\b"` |
| 31 | Regex, AND, recursive, file type filter | `peekdocs -x -a -r -t pdf "\d{3}" "\$\d+"` |
| | **Context Lines (Before/After)** | |
| 32 | Show 5 lines after each match | `peekdocs -A 5 "John Smith"` |
| 33 | Show 3 lines before each match | `peekdocs -B 3 budget` |
| 34 | Show lines before and after | `peekdocs -B 2 -A 2 budget` |
| 35 | Context lines with AND logic | `peekdocs -B 3 -A 3 -a budget revenue` |
| 36 | Context with file type filter | `peekdocs -A 5 -t docx,pdf budget` |
| 37 | Context with recursive search | `peekdocs -B 3 -A 3 -r budget` |
| 38 | Context with regex | `peekdocs -B 2 -A 2 -x "\d{3}-\d{3}-\d{4}"` |
| 39 | Context, recursive, file type filter | `peekdocs -B 5 -A 5 -r -t docx "John Smith"` |
| 40 | Context, AND, recursive, file type filter | `peekdocs -B 3 -A 3 -a -r -t txt budget revenue` |
| | **Parallel Processing** | |
| 41 | Use 4 cores for search | `peekdocs -c 4 budget` |
| 42 | Parallel with recursive search | `peekdocs -c 4 -r budget` |
| 43 | Parallel with file type filter | `peekdocs -c 4 -t pdf,docx budget` |
| | **Save, Version, and Help** | |
| 44 | Save results to a named file | `peekdocs -s name_of_your_file` |
| | **Save and Append Searches** | |
| 45 | Search and append results to a file | `peekdocs -sa my_report budget` |
| 46 | Append with AND search | `peekdocs -sa my_report -a budget revenue` |
| 47 | Append with recursive search | `peekdocs -sa my_report -r budget` |
| 48 | Append with file type filter | `peekdocs -sa my_report -t pdf budget` |
| | **Quiet Mode** | |
| 49 | Suppress banner | `peekdocs -q budget` |
| 48a | Minimal output (Found/Elapsed only) | `peekdocs -qq budget` |
| 50 | Quiet with recursive search | `peekdocs -q -r budget` |
| | **OCR Searches** | |
| 51 | Search scanned PDFs and images | `peekdocs -O budget` |
| 52 | OCR with file type filter | `peekdocs -O -t pdf budget` |
| 53 | Search only image files | `peekdocs -O -t jpg,png budget` |
| 54 | OCR with recursive search | `peekdocs -O -r budget` |
| 55 | OCR with AND logic | `peekdocs -O -a budget revenue` |
| 56 | OCR with context lines | `peekdocs -O -B 3 -A 3 budget` |
| | **Fuzzy Searches** | |
| 57 | Fuzzy single term | `peekdocs -z budget` |
| 58 | Fuzzy with AND logic | `peekdocs -z -a budget revenue` |
| 59 | Fuzzy with file type filter | `peekdocs -z -t pdf,docx budget` |
| 60 | Fuzzy with recursive search | `peekdocs -z -r budget` |
| 61 | Fuzzy with word proximity | `peekdocs -z -p 5 budget revenue` |
| 62 | Fuzzy with OCR | `peekdocs -z -O budget` |
| 63 | Fuzzy with context lines | `peekdocs -z -B 3 -A 3 budget` |
| 64 | Fuzzy, AND, recursive, file type | `peekdocs -z -a -r -t pdf budget revenue` |
| | **Wildcard Searches** | |
| 65 | Wildcard single pattern | `peekdocs -w "budg*"` |
| 66 | Wildcard question mark | `peekdocs -w "te?t"` |
| 67 | Wildcard with AND logic | `peekdocs -w -a "budg*" "rev*"` |
| 68 | Wildcard with file type filter | `peekdocs -w -t pdf,docx "budg*"` |
| 69 | Wildcard with recursive search | `peekdocs -w -r "budg*"` |
| 70 | Wildcard with context lines | `peekdocs -w -B 3 -A 3 "budg*"` |
| | **Whole-Word Searches** | |
| 71 | Whole-word single term | `peekdocs -W bob` |
| 72 | Whole-word with AND logic | `peekdocs -W -a bob amy` |
| 73 | Whole-word with expression | `peekdocs -W -e "bob AND amy"` |
| | **Exclude Searches** | |
| 74 | Exclude lines containing a term | `peekdocs -n draft budget` |
| 75 | Exclude multiple terms | `peekdocs -n draft,obsolete budget` |
| 76 | Exclude with AND logic | `peekdocs -n draft -a budget revenue` |
| 77 | Exclude with recursive search | `peekdocs -n draft -r budget` |
| 78 | Exclude with file type filter | `peekdocs -n draft -t pdf,docx budget` |
| 79 | Exclude with wildcard search | `peekdocs -w -n "dra*" "budg*"` |
| | **Additional Output Formats** | |
| 80 | Output results as CSV | `peekdocs -o csv budget` |
| 81 | Output results as JSON | `peekdocs -o json budget` |
| 82 | Output both CSV and JSON | `peekdocs -o csv,json budget` |
| 83 | CSV with recursive search | `peekdocs -o csv -r budget` |
| 82a | Output as PDF (highlighted) | `peekdocs -o pdf budget` |
| 82b | All extra formats at once | `peekdocs -o csv,json,pdf,html budget` |
| | **Match Cap** | |
| 84 | Set max matches to 5000 | `peekdocs -m 5000 budget` |
| 85 | Disable match cap (no limit) | `peekdocs -m 0 budget` |
| 86 | Match cap with AND and recursive | `peekdocs -m 500 -a -r budget revenue` |
| | **Saved Settings** | |
| 87 | View saved settings | `peekdocs --config` |
| 88 | Save a setting | `peekdocs --config recursive=true` |
| 89 | Save multiple settings | `peekdocs --config recursive=true cores=4` |
| 90 | Remove a saved setting | `peekdocs --config recursive=` |
| | **Search Index** | |
| 91 | Build index (includes all subfolders) | `peekdocs --index` |
| 92 | Build index with OCR | `peekdocs --index -O` |
| 93 | Show index info | `peekdocs --index-status` |
| 94 | Delete the index | `peekdocs --index-clear` |
| 93a | Incrementally refresh the index | `peekdocs --index-refresh` |
| 93b | Skip the index (direct scan) | `peekdocs --no-index budget` |
| 95 | Delete results files | `peekdocs --clear` |
| 96 | Delete all peekdocs output files | `peekdocs --clear-all` |
| 97 | Search and auto-open the .docx report | `peekdocs --open docx budget` |
| 98 | Search and auto-open HTML in browser | `peekdocs --open html budget` |
| 99 | Search and auto-open CSV in Excel/LibreOffice | `peekdocs --open csv budget` |
| 100 | Search and auto-open PDF in a PDF viewer | `peekdocs --open pdf budget` |
| 101 | Search and auto-open JSON in a text editor | `peekdocs --open json budget` |
| 101a | Append to accumulated report and open it | `peekdocs -sa archive --open docx budget` |
| 101b | Append and open accumulated report in browser | `peekdocs -sa archive --open html budget` |
| | **Cleanup** | |
| 101c | Delete results files in current directory | `peekdocs --clear` |
| 101d | Delete all peekdocs output files | `peekdocs --clear-all` |
| | **Inverse Search** | |
| 97 | Find files missing a term | `peekdocs --inverse "indemnification"` |
| 98 | Files missing any of several terms | `peekdocs --inverse disclaimer warranty` |
| 99 | Files missing ALL required terms | `peekdocs --inverse -a confidential signature date` |
| 100 | Inverse with regex pattern | `peekdocs --inverse -x "\d{3}-\d{2}-\d{4}"` |
| 101 | Inverse with file type filter | `peekdocs --inverse -t pdf,docx "effective date"` |
| 102 | Inverse recursive search | `peekdocs --inverse -r "retention policy"` |
| 103 | Inverse with CSV output | `peekdocs --inverse -o csv "indemnification"` |
| 104 | Inverse with JSON output | `peekdocs --inverse -o json "authorization"` |
| | **Boolean Expression Search** | |
| 105 | AND expression | `peekdocs -e "budget AND revenue"` |
| 106 | OR expression | `peekdocs -e "budget OR revenue"` |
| 107 | AND NOT expression | `peekdocs -e "budget AND NOT draft"` |
| 108 | Grouped OR within AND | `peekdocs -e "(budget OR revenue) AND (cost OR profit)"` |
| 109 | Grouped AND with OR | `peekdocs -e "(bob AND amy) OR (fred AND wilma)"` |
| 110 | Complex with NOT | `peekdocs -e "(merger OR acquisition) AND NOT draft"` |
| 111 | Multi-word terms in expression | `peekdocs -e '"annual report" AND (2023 OR 2024)'` |
| 112 | Expression with wildcard | `peekdocs -e -w "budg* AND rev*"` |
| 113 | Expression with regex | `peekdocs -e -x "\\d{3}-\\d{4} AND budget"` |
| 114 | Expression with fuzzy | `peekdocs -e -z "budgt AND revnue"` |
| 115 | Expression with context | `peekdocs -e -B 2 -A 2 "merger AND NOT confidential"` |
| 116 | Expression recursive | `peekdocs -e -r "(budget OR revenue) AND (cost OR profit)"` |
| | **Output Directory** | |
| 117 | Write results to a specific folder | `peekdocs --output-dir ~/reports budget` |
| 118 | Output dir with recursive search | `peekdocs --output-dir /tmp/results -r budget` |
| 115a | Timestamped filenames | `peekdocs --timestamp budget` |
| 115b | Timestamp with output directory | `peekdocs --timestamp --output-dir ~/reports -r budget` |
| 115c | Max file size limit (skip large files) | `peekdocs --max-file-size 50 budget` |
| 115d | No file size limit | `peekdocs --max-file-size 0 budget` |
| | **Real-World Workflow Combinations** | |
| 115e | Recursive + types + AND + context | `peekdocs -r -t pdf,docx -a -B 2 -A 2 budget revenue` |
| 115f | Regex + range + output dir | `peekdocs -x "\$[\d,]+" -R amount:5000..100000 --output-dir ~/reports` |
| 115g | Inverse + recursive + types | `peekdocs -r -t docx --inverse "confidentiality"` |
| 115h | Fuzzy + recursive + CSV output | `peekdocs -r -z accommodation -o csv` |
| 115i | AND + exclude + file types + timestamp | `peekdocs -a -n draft -t pdf,docx --timestamp budget revenue` |
| 115j | Regex + context + recursive + JSON | `peekdocs -x "\d{3}-\d{2}-\d{4}" -B 3 -A 3 -r -o json` |
| | **Range Queries** | |
| 119 | Filter by dollar amount range | `peekdocs -R amount:1000..5000 budget` |
| 120 | Filter by date range | `peekdocs -R date:2024-01-01..2024-12-31 report` |
| 121 | Range-only search (no text terms) | `peekdocs -R amount:1000..5000` |
| 122 | Filter by file size | `peekdocs -R filesize:1M..10M report` |
| 123 | Multiple ranges (AND) | `peekdocs -R amount:1000..5000 -R date:2024-01-01..2024-12-31 invoice` |
| 124 | Open-ended range (minimum only) | `peekdocs -R amount:10000.. contract` |
| 125 | Percent range | `peekdocs -R percent:10..50 growth` |
| 126 | Age range | `peekdocs -R age:18..65 visit` |
| 127 | Time range | `peekdocs -R time:09:00..17:00 meeting` |
| 128 | Range with recursive search | `peekdocs -R amount:1000..5000 -r budget` |
| 129 | Open-ended range (maximum only) | `peekdocs -R amount:..5000 invoice` |
| 130 | Filter by file modification date | `peekdocs -R filedate:2024-01-01..2024-06-30 report` |
| 131 | Number range (any standalone number) | `peekdocs -R number:100..999 report` |
| 132 | Range with file type filter | `peekdocs -R amount:1000.. -t .pdf,.docx invoice` |
| 133 | Range with context lines | `peekdocs -R amount:5000..10000 -B 2 -A 2 payment` |
| 134 | Range with AND mode text search | `peekdocs -R date:2024-01-01..2024-12-31 -a budget revenue` |
| 135 | Range with exclude terms | `peekdocs -R amount:1000..5000 -n draft invoice` |
| 136 | Large file search | `peekdocs -R filesize:10M.. -r report` |
| 137 | Small recent files | `peekdocs -R filesize:..100K -R filedate:2025-01-01.. memo` |
| | **Filename Ranges** | |
| 134a | Filter by date in filename | `peekdocs -R fn:date:2024-01-01..2024-12-31 budget` |
| 134b | Filename + content range | `peekdocs -R fn:date:2024-01-01..2024-12-31 -R amount:1000..5000 invoice` |
| 134c | Filename range in expression | `peekdocs -e "budget AND fn:date:2024-01-01..2024-12-31"` |
| | **Range Queries in Expressions** | |
| 138 | Text AND amount range | `peekdocs -e "budget AND amount:1000..5000"` |
| 139 | Text AND date range | `peekdocs -e "report AND date:2024-01-01..2024-12-31"` |
| 140 | OR with range on one branch | `peekdocs -e "(budget AND amount:1000..5000) OR revenue"` |
| 141 | NOT with range (exclude high amounts) | `peekdocs -e "invoice AND NOT amount:10000.."` |
| 142 | Multiple ranges in expression | `peekdocs -e "invoice AND amount:500..5000 AND date:2024-01-01..2024-12-31"` |
| 143 | Range-only expression | `peekdocs -e "amount:1000..5000"` |
| 144 | OR between two ranges | `peekdocs -e "amount:1000..5000 OR percent:10..50"` |
| 145 | Text with percent range | `peekdocs -e "growth AND percent:20..100"` |
| 146 | Text with age range | `peekdocs -e "visit AND age:18..65"` |
| 147 | Text with time range | `peekdocs -e "meeting AND time:09:00..17:00"` |
| 148 | Complex: text + range + NOT | `peekdocs -e "(contract AND amount:5000..50000) AND NOT draft"` |
| 149 | Complex: two branches with ranges | `peekdocs -e "(budget AND amount:1000..5000) OR (invoice AND date:2024-01-01..2024-12-31)"` |
| 150 | Expression + -R metadata filter | `peekdocs -e "budget AND amount:1000..5000" -R filesize:..1M` |
| 151 | Expression with wildcard + range | `peekdocs -e -w "budg* AND amount:1000..5000"` |
| 152 | Expression with regex + range | `peekdocs -e -x "INV-\\d+ AND amount:1000..5000"` |
| | **Regex Collections (CLI)** | |
| 153 | List saved regex collections | `peekdocs --regex-collection --list` |
| 154 | Run a saved regex collection | `peekdocs --regex-collection "Email Patterns"` |
| 155 | Run collection on a specific folder | `peekdocs --regex-collection "Email Patterns" -d ~/Documents` |
| 156 | Run collection recursively | `peekdocs --regex-collection "Email Patterns" -r` |
| 157 | Run collection with JSON to stdout | `peekdocs --regex-collection "Email Patterns" --stdout` |
| 158 | Run collection on folder, recursive, JSON | `peekdocs --regex-collection "IP Addresses" -d /var/log -r --stdout` |
| 159 | Pipe collection results to a file | `peekdocs --regex-collection "Dates" --stdout > results.json` |
| 160 | Run collection in a scheduled task | `peekdocs --regex-collection "Audit Patterns" -d ~/reports -r --stdout >> /tmp/audit.json` |
| | **Installation Check** | |
| 161 | Check installation health | `peekdocs --check` |
| | **Version and Help** | |
| 162 | Show version | `peekdocs -v` |
| 163 | Show help | `peekdocs -h` |
| 164 | Show help (no arguments) | `peekdocs` |

## Output

This section covers the report files peekdocs writes — what each search mode produces, what's in each format, and how to read what's on screen during a run.

<a id="search-modes-and-their-reports"></a>
### Search Modes and Their Reports

peekdocs has three distinct search modes. They share the same search engine, flags, and 100+ file-type support, but each writes its own report family so a run in one mode never overwrites a run in another:

| Mode | What it does | How to launch | Report files (in the search folder) |
|------|-------------|--------------|-------------------------------------|
| **Standard Search** | One search, configured by flags or GUI options (keyword, AND/OR, fuzzy, wildcard, OCR, etc.) | GUI **Run Standard Search** button, or `peekdocs <terms>` | `peekdocs_standard_results.txt`, `peekdocs_standard_results.docx`, plus optional `.csv` / `.json` / `.pdf` / `.html` with `-o` |
| **Regex Search** | A named collection of up to 10 regex patterns, each run separately with per-pattern results | GUI **Regex Search** button, or `peekdocs --regex-collection "Name"` | `peekdocs_regex_results.txt`, `peekdocs_regex_results.docx` |
| **Suite** | A named group of saved Standard searches, run together and combined into one highlighted report | GUI **Run Suite** (Tools → Search Suites, or **Suites** button), or `peekdocs --suite "Name"` | `peekdocs_suite_results.txt`, `peekdocs_suite_results.docx`, plus optional `.html` / `.csv` / `.json` |

> **What counts as which mode?** The "mode" is defined by the workflow, not by the flag set. A one-off `peekdocs -x "pattern"` (or `-z` for fuzzy, `-w` for wildcard, `-W` for whole-word) is a *Standard Search* with a search-mode flag — it writes `peekdocs_standard_results.*`. Only the dedicated **Regex Search** workflow (the GUI popup or `--regex-collection`) writes `peekdocs_regex_results.*`. This is deliberate: the CLI's `-x`, `-z`, `-w`, etc. are all just search modifiers on the same Standard pipeline, and giving each its own filename would be a slippery slope.

Within each family, the report files are overwritten on every run unless `--timestamp` is set (or the GUI's Timestamp checkbox is enabled), in which case `_YYYYMMDD_HHMMSS` is appended to every filename. `peekdocs --clear` and the GUI's **Clear Files** match all three families by prefix; saved/accumulated reports (`peekdocs_report_*`, `peekdocs_accumulated_*`) and the search index (`.peekdocs.db`) are separate file families and are not part of this overview.

### Results Preview vs. Reports

When a search completes, you see results in two places:

**Results Preview pane** (inside the app):
- Appears immediately after the search finishes — no need to open a separate file
- Shows matching lines with search terms highlighted in color
- Right-click any line to copy it to the clipboard
- Double-click a filename to open the original file in its default application
- Best for: quick scanning, checking if a search found what you expected, copying a specific match

**Report files** (on disk):
- A `.txt` and `.docx` report are generated automatically after every search
- The `.docx` report is a standalone Word document with every match highlighted in yellow, organized by file, with surrounding context, match counts, line numbers, and a full header showing what was searched, when, and with which settings
- The `.txt` report contains the same matches in plain text with `**` markers around matched terms
- Best for: saving a permanent record, printing, emailing to someone, reviewing later, sharing with a colleague who doesn't have peekdocs

**Both show the same matches.** Every result that appears in the Results Preview also appears in the reports, and vice versa (subject to the max-matches limit, which applies equally to both). The difference is presentation: the preview is for instant review inside the app; the reports are polished documents for keeping or sharing.

### Report Files

Search results are always written to two files in the current directory:

- **`peekdocs_standard_results.txt`** — Plain text with `**` markers around matched terms
- **`peekdocs_standard_results.docx`** — Word document with search terms highlighted in green in the header and matched terms highlighted in yellow throughout

With the `-o` flag, additional output files are created:

- **`peekdocs_standard_results.csv`** (`-o csv`) — Spreadsheet-ready format with columns: filename, folder, line_number, matched_text. Open in Excel, Google Sheets, or any spreadsheet application to sort, filter, and analyze results.
- **`peekdocs_standard_results.json`** (`-o json`) — Machine-readable format with search metadata, per-file match counts, and a matches array. Useful for integrating peekdocs into automated workflows, dashboards, or other tools.

### Command Translation

Every report includes a **Translation** line that explains the search command in plain English. Regex patterns are automatically recognized and described by their meaning — not their individual characters. See the **Report translation** column in the [Common Regex Search Patterns](#common-regex-search-patterns) table above for the full list of recognized patterns.

Example report header:
```
Command ==> peekdocs -a -x "\d{1,2}/\d{1,2}/\d{2,4}" budget
Translation ==> Search current directory, for ALL of: a date (e.g. MM/DD/YYYY or YYYY-MM-DD) AND "budget" (using regex)
```

Regex patterns combined with `|` (alternation) are also recognized per-branch. Unrecognized patterns fall back to a character-level description.

Text file format:
```

2026-03-07 14:30:45
Search Term(s) ==> budget, revenue

Document: report.docx (2 matches), Line: 12, Match:
(/Users/yourname/Documents)
"The **budget** for this quarter exceeded expectations"

Document: summary.docx (1 match), Line: 3, Match:
(/Users/yourname/Documents)
"Revised **budget** proposal attached"
```

If any files could not be read during a search, errors are logged to **`peekdocs_errors.log`** in the current directory. Each entry includes a timestamp, the filename, and the reason it failed:
```
2026-03-22 14:05:12  Could not read report.pdf (encrypted PDF)
2026-03-22 14:05:12  Could not read data.xlsx (file is corrupted)
```

The error log is only created when a file error occurs — if all files are read successfully, no error log is created. The error log appends across searches so you can track issues over time. You can safely delete `peekdocs_errors.log` at any time — a new one will be created automatically the next time a file error occurs.

If peekdocs itself crashes unexpectedly, a crash report is also written to `peekdocs_errors.log` with a diagnosis to help identify the cause:
```
============================================================
2026-03-25 14:30:12  CRASH REPORT
peekdocs 0.1.0
Python 3.13.2 (main, Feb 4 2025, 14:51:09)
OS: Darwin 24.6.0
Command: peekdocs budget

Diagnosis: The Python module 'fitz' could not be loaded. This is usually
caused by a missing or incompatible dependency. Try: pip install --upgrade peekdocs
============================================================
Traceback (most recent call last):
  ...
```

If you experience a crash, check `peekdocs_errors.log` in the folder where you ran the search. The diagnosis line suggests a likely cause and fix. Common causes include a missing or incompatible Python package (fix: `pip install --upgrade peekdocs`), a corrupted file that couldn't be handled, or a Python version incompatibility. If the problem persists, the crash report contains everything needed to investigate — you can include it when reporting an issue.

The terminal also displays a summary with per-file match counts:
```
Files searched: 12 (4.50 MB) — Found 3 match(es).
Elapsed time: 0.45 seconds, Cores used: 4 of 8
  report.docx: 2
  summary.docx: 1
Results ==> /Users/yourname/Documents
```

## Automation and IT Use

peekdocs is designed for interactive use, but every interactive flow has a matching CLI surface that you can drive from cron, Task Scheduler, a CI job, or a wrapper script. This section is the operational reference: exit codes, JSON output schemas, scheduling defaults, where things live on disk, and how to ship a reusable workflow to other machines.

### A worked example: nightly source-tree watch

Before the reference material, here is how the pieces compose into something an on-call engineer would actually run. The scenario: a source tree is shared by several developers and you want to know about new hardcoded credentials *the morning they appear* rather than days later when someone happens to notice.

**Setup (done once):**

Build a regex collection through the GUI (Tools → Regex Search → Save Collection As) covering the shapes you care about — `password\s*=\s*['"][^'"]+['"]`, `aws_secret_access_key`, `api_key\s*=`, and whatever else is specific to your stack. Save it as `secrets`.

Capture a baseline so the first nightly diff has something to compare against:

```bash
mkdir -p /var/log/peekdocs
peekdocs --regex-collection secrets -r --hash --stdout \
    > /var/log/peekdocs/peekdocs_snapshot_baseline.json
```

Drop the wrapper script at `/usr/local/bin/peekdocs-nightly.sh`:

```bash
#!/bin/bash
STAMP=$(date +%Y-%m-%d)
LOGDIR=/var/log/peekdocs
NEW="$LOGDIR/peekdocs_snapshot_$STAMP.json"

# Newest existing snapshot BEFORE we write today's = yesterday's run.
PREV=$(ls -t "$LOGDIR"/peekdocs_snapshot_*.json 2>/dev/null | head -1)

# Tonight's scan.
peekdocs --regex-collection secrets -r --hash --stdout > "$NEW"

# First run ever — nothing to diff against, exit clean.
[ -z "$PREV" ] && exit 0

# Diff exits 1 when there are actionable changes (NEW / CHANGED / MODIFIED).
# That's the signal to alert. Use `;` not `&&` because exit 1 is "found stuff",
# not "failure" — see the exit-code gotcha later in this section.
peekdocs --diff "$PREV" "$NEW" --json > "$LOGDIR/peekdocs_diff_$STAMP.json"
if [ $? -eq 1 ]; then
    mail -s "peekdocs: new findings in source tree" oncall@example.com \
        < "$LOGDIR/peekdocs_diff_$STAMP.json"
fi
```

Schedule it under cron:

```
0 3 * * * /usr/local/bin/peekdocs-nightly.sh
```

**What you get every morning:**

- A timestamped JSON snapshot on disk with a SHA-256 fingerprint of every matched file. If anyone later asks "did this file look the same last Tuesday?", `jq` answers in one command.
- A diff file showing exactly what changed since yesterday: NEW files matching, files that gained matches (CHANGED), and files whose content changed without affecting the match count (MODIFIED — only catchable because both sides carry `--hash`).
- An email only on days when something actionable shows up. Cron health checks stay green on quiet days; you do not get spammed with "everything still fine" notifications.
- A persistent history on disk for as far back as you keep the snapshot files. Trends over weeks or months are a one-liner with `jq` and your favorite plotter.

**The same loop covers other recurring questions** by swapping the regex collection:

| You want to track... | Patterns to put in the collection |
|----------------------|-----------------------------------|
| Deprecated API usage | `OldClass\.legacy_method`, `deprecated_function_name` |
| TODO / FIXME drift | `\bTODO\b`, `\bFIXME\b`, `XXX:` |
| Hardcoded paths and ports | `localhost:\d{4}`, `/etc/[a-z_]+\.conf` |
| Stale references to a renamed service | `old-service-name`, `OLD_SERVICE_URL` |
| Untracked migrations | `def migration\d+`, `class Migration\d+` |
| Files quietly edited under a steady match count | (any pattern, with `--hash` on both sides → MODIFIED bucket) |

Each is the same shape: regex collection + nightly diff + conditional alert. The MODIFIED bucket is the subtle one — same file, same match count, different SHA-256 — somebody touched a watched file in a way the search alone would not have noticed.

**Variations worth knowing:**

- If you would rather have peekdocs fire the alert directly instead of branching on `$?`, use `--on-match HOOK` to run an arbitrary command after a successful match-finding run. Env vars `PEEKDOCS_MATCH_COUNT`, `PEEKDOCS_REPORT_TXT`, etc. are populated for the hook.
- `peekdocs --runs --json` reads the per-run structured log (`~/.peekdocs_runs.log`) — useful when something fails at 3 a.m. and you want to know how long the run took, what its exit code was, and where its report landed without digging through email.
- `peekdocs --dry-run --regex-collection secrets -r` validates the scope (collection exists, folder exists, flags compose correctly) without scanning anything. Run it in your CI before scheduling the real job.

**What this is not:** a substitute for code review or for any decision-grade analysis. peekdocs is a general-purpose local text-search tool. It gives you the *signal* — "something new appeared since yesterday" — and you decide what to do about it. The exit codes are stable; the JSON shape is versioned (`generator` field); the rest is your wrapper script.

The remainder of this section is the reference material the example above depends on: exit-code semantics, the JSON schema for `--stdout`, where reports and logs live on disk, the contract for `--diff` and `--on-match`, the headless deployment guarantee, and the gotchas (notably the `&&` vs `;` exit-code flip) that catch out people the first time they wire a peekdocs CLI into a pipeline.

### Exit codes

Every CLI command returns one of three codes. Wrappers and schedulers should branch on these, not on parsing stdout.

| Code | Meaning |
|------|---------|
| `0` | The command completed and matches were found (or, for informational commands like `--check`, `--list-files`, `--list-suites`, the command succeeded). |
| `1` | The command completed but no matches were found. Common in scheduled scans where "no findings" is the expected good case. |
| `2` | The command failed. Validation error, suite or regex collection not found, `--check` reported a missing dependency, an unexpected exception, etc. |

Typical usage in a shell wrapper:

```bash
peekdocs --regex-collection "my-patterns" -r --timestamp --stdout > /var/log/peekdocs/$(date +%Y%m%d).json
rc=$?
case $rc in
  0) echo "Findings logged" | mail -s "peekdocs: findings" admin@example.com ;;
  1) ;;  # clean scan, no action
  2) echo "peekdocs failed (see peekdocs_errors.log)" | mail -s "peekdocs: FAIL" oncall@example.com ;;
esac
```

### JSON output (`--stdout`) schema

`--stdout` writes a JSON object to standard output and skips report-file generation. The exit code is still 0 (matches) / 1 (no matches), so a wrapper can use both signals. Two schemas exist — one for the standard pipeline, one for `--regex-collection` — because regex collections carry per-pattern results.

Every payload starts with a `generator` field that includes the peekdocs version, so downstream consumers can branch on it if the schema ever evolves.

**Standard search** (`peekdocs --stdout <terms>` and variants):

```json
{
  "generator": "peekdocs v1.0.0",
  "directory": "/abs/path/to/search/folder",
  "search_terms": ["budget", "revenue"],
  "mode": "ANY",
  "timestamp": "2026-05-23 09:08:31",
  "files_searched": 444,
  "matches_found": 3246,
  "elapsed_seconds": 2.27,
  "matches_per_file": [
    {"filename": "Q3.docx", "folder": "/abs/.../docs", "matches": 17}
  ],
  "matches": [
    {"filename": "Q3.docx", "folder": "/abs/.../docs", "line_number": 42, "matched_text": "revenue growth"}
  ]
}
```

**Inverse search** (`--inverse`) — `matches` / `matches_found` / `matches_per_file` are replaced by:

```json
{
  "files_without_matches": 38,
  "inverse_files": [
    {"filename": "missing-disclaimer.docx", "folder": "/abs/.../docs"}
  ]
}
```

**Regex collection** (`peekdocs --regex-collection NAME --stdout`):

```json
{
  "generator": "peekdocs v1.0.0",
  "collection": "my-patterns",
  "directory": "/abs/.../docs",
  "timestamp": "2026-05-23 09:08:31",
  "elapsed_seconds": 4.81,
  "total_matches": 47,
  "patterns": [
    {"name": "Invoice IDs", "regex": "\\bINV-\\d+\\b", "match_count": 3, "...": "..."}
  ],
  "matches": [
    {"filename": "ledger.pdf", "folder": "/abs/.../docs", "line_number": 19, "matched_text": "INV-12345"}
  ]
}
```

`mode` is `"ALL"` (AND) or `"ANY"` (OR). `matched_text` has the highlight markers stripped — pipe into your own indexer or SIEM without post-processing.

**Field naming note.** The JSON output (and CSV output) uses `line_number`. The Python API's `SearchMatch` dataclass uses `line_num` for the same field. Code that round-trips between the API and JSON/CSV must translate the name; reading `match.line_number` on a `SearchMatch` raises `AttributeError`.

**File hashes (`--hash`).** For file-identity and integrity-verification workflows, add `--hash` to any of the above. Each entry in `matches_per_file` / `inverse_files` then carries a `"sha256"` field with the hex digest of the file's *raw bytes* (not the extracted text). For `--regex-collection`, `--hash` adds a top-level `matches_per_file` array of unique matched files with their hashes. Hashing happens once per matched file (not per match) so a file with 100 matches is only read for hashing once. If a file can't be read for hashing — deleted between search and hash, permission revoked — the field is `null` and an entry is appended to `peekdocs_errors.log`; the search itself is not aborted. The field is omitted entirely when `--hash` is not set, so existing consumers see no schema change.

```json
{
  "matches_per_file": [
    {"filename": "ledger.pdf", "folder": "/abs/.../docs", "matches": 3,
     "sha256": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"}
  ]
}
```

The algorithm is SHA-256 in this release; the field is named `sha256` so additional algorithms (SHA-512, BLAKE3) can be added later without breaking consumers. `--hash` works with `--stdout`, with `-o json`, and with `--regex-collection --stdout`. It does not currently affect the `.txt` / `.docx` reports.

### Scheduled and unattended runs

Three pieces matter for unattended operation:

1. **Use `--timestamp`** on every scheduled run so each invocation produces uniquely named reports (`peekdocs_standard_results_YYYYMMDD_HHMMSS.txt`, `peekdocs_regex_results_YYYYMMDD_HHMMSS.txt`, `peekdocs_suite_results_YYYYMMDD_HHMMSS.txt`). Without it, every run overwrites the previous report and you lose the historical record that is usually the point of scheduling.

2. **Use the Schedule Search dialog** (Tools menu in the GUI) to generate the correct cron / `schtasks` command for your OS — it pre-checks `--timestamp` by default and pre-fills the search folder, search type (suite or regex collection), frequency, and time. Copy the generated command into your scheduler.

3. **Persist common defaults via `~/.peekdocsrc`.** `peekdocs --config timestamp=true` saves the timestamp flag as a default so every CLI run gets it without re-typing. Other useful keys: `recursive=true`, `cores=N`, `max_file_size_mb=N`. See [Saved Settings (Optional)](#saved-settings-optional) for the full key list.

For batch loops (run several collections or suites in one cron job) see [Regex Collection Use Cases](#regex-collection-use-cases) and [Search Suite Use Cases](#search-suite-use-cases).

### Where things live

| Path | Contents | Per-folder or global? |
|------|---------|----------------------|
| `<search-folder>/peekdocs_standard_results.*` | Standard search reports (overwritten each run unless `--timestamp`) | Per-folder |
| `<search-folder>/peekdocs_regex_results.*` | Regex Search / regex collection reports | Per-folder |
| `<search-folder>/peekdocs_suite_results.*` | Suite reports | Per-folder |
| `<search-folder>/peekdocs_errors.log` | Per-file read errors and uncaught exceptions from runs in this folder | Per-folder |
| `<search-folder>/peekdocs_report_*` | Reports archived with `-s` | Per-folder |
| `<search-folder>/peekdocs_accumulated_*` | Reports appended with `-sa` | Per-folder |
| `<search-folder>/.peekdocs.db` | Optional FTS5 search index | Per-folder |
| `<search-folder>/.peekdocs_collection.json` | Saved searches and suites for this folder | Per-folder |
| `~/.peekdocsrc` | Per-user CLI/GUI defaults | Per-user (one file) |
| `~/.peekdocs_history.json` | Search history | Per-user |
| `~/.peekdocs_runs.log` | Per-run structured log (JSON Lines, one line per CLI invocation) | Per-user, default path |
| `~/.peekdocs_bookmarks.json` | Bookmarked files | Per-user |
| `~/.peekdocs_regex_collections.json` | All regex collections (single namespace, all folders) | Per-user (one file) |
| `~/.peekdocs_suites_index.json` | Global suite name → folder index so `peekdocs --suite NAME` works from anywhere | Per-user |

`peekdocs --list-files` shows all peekdocs-created files in the current directory; the GUI's **View All peekdocs Files** does the same recursively.

### Per-run structured log

Every search-mode CLI invocation appends one JSON object to `~/.peekdocs_runs.log` (JSON Lines / NDJSON format — one self-contained JSON per line). This gives IT a tail-able, grep-able, SIEM-shippable record of every search peekdocs has run on this machine, without setting anything up first.

```json
{"timestamp":"2026-05-23T10:32:01","peekdocs_version":"1.0.0","argv":["peekdocs","--suite","Example 1"],"cwd":"/Users/bob/Documents/SearchTheseDocuments","exit_code":0,"match_count":3339,"file_count":444,"error_count":0,"elapsed_seconds":3.05}
```

**What's captured:**

| Field | Meaning |
|-------|---------|
| `timestamp` | Local time, ISO 8601 to the second |
| `peekdocs_version` | Version string of the running peekdocs |
| `argv` | The full command as an array (`["peekdocs", "--suite", "Example 1"]`) — preserves quoting cleanly so consumers can filter on flags without parsing shell syntax. **Note:** search terms are part of `argv` and therefore land in the log, same as the existing `~/.peekdocs_history.json`. Opt out with `--no-log` per-run or `--config run_log=false` permanently if that's a concern. |
| `cwd` | The working directory where the command ran |
| `exit_code` | 0 = matches found, 1 = no matches, 2 = error |
| `match_count` | Total matches across all files (or for inverse search, the count of files-without-matches) |
| `file_count` | Files actually searched |
| `error_count` | Files skipped due to read errors (mirrors the count in `peekdocs_errors.log`) |
| `elapsed_seconds` | Wall-clock duration, rounded to milliseconds |

**What's logged:** the three search modes — Standard Search, `--suite`, `--regex-collection`. Informational commands (`--help`, `--version`, `--check`, `--list-*`, `--clear*`, `--index*`, `--config`, `--runs` itself) are skipped, so the log captures search activity rather than every CLI invocation.

**Reading the log:**

```bash
peekdocs --runs           # last 20 in a readable table
peekdocs --runs 100       # last 100
peekdocs --runs --json    # re-emit raw JSONL for piping
tail -f ~/.peekdocs_runs.log | jq .          # live tail, filtered
grep '"exit_code":2' ~/.peekdocs_runs.log    # every failed run
jq 'select(.match_count > 100)' ~/.peekdocs_runs.log   # heavy-find runs
```

**Disabling:**

| What you want | How |
|---|---|
| Skip this one run | `peekdocs --no-log <args>` |
| Disable permanently (per user) | `peekdocs --config run_log=false` |
| Route to a different path | `peekdocs --config run_log_path=/var/log/peekdocs/runs.log` (path must be writable by the user) |
| Move into syslog / Splunk / Elastic | Run Filebeat or your shipper of choice against the log path — JSONL is universally supported. Or set `run_log_path` to a fifo / tmpfs that your pipeline reads. |

**No rotation today.** Each entry is ~400 bytes, so 10,000 runs is ~4 MB. If you hit a size where rotation matters, point `run_log_path` at a file managed by `logrotate` (Linux) or rotate it yourself from cron.

**Write failures don't break searches.** If the log file can't be written (disk full, permission denied, locked on Windows), peekdocs silently skips the log line for that run and continues — observability is best-effort by design, and the user's actual search must never fail because of a logging issue.

### Notification hook

For unattended runs (cron, Task Scheduler), the obvious next question is *"how do I find out when something matched?"* The `--on-match COMMAND` flag fires an external command of your choice whenever a search exits with code 0 (matches found). peekdocs doesn't know about email, Slack, Splunk, PagerDuty, or any specific notification system — it just runs your command and passes context via environment variables. You write the script that does the actual notifying, which keeps peekdocs's surface area small and your stack open.

**When the hook fires:** exit code 0 only (matches found). Skipped on exit 1 (no matches), exit 2 (error), `--dry-run`, and informational commands (`--list-suites`, `--runs`, etc.). The hook runs *after* the search completes and reports are written, so report files referenced by env vars are guaranteed to exist on disk.

**How the hook is invoked:** `subprocess.run(shlex.split(command))` — no shell. Quoted args work (`--on-match "python /opt/scripts/notify.py --priority high"`), but pipes and redirects need to be inside a wrapper script.

**Timeout:** 30 seconds. A hung hook does not block peekdocs forever; it is killed and a warning is logged to `peekdocs_errors.log`. The user's search exit code is preserved regardless of hook outcome — a broken notification script never penalizes a successful search.

**Environment variables passed to the hook:**

| Variable | Meaning |
|----------|---------|
| `PEEKDOCS_EXIT_CODE` | Always `0` (the hook only fires on matches) |
| `PEEKDOCS_MATCH_COUNT` | Total matches across all files |
| `PEEKDOCS_FILE_COUNT` | Files actually searched |
| `PEEKDOCS_ERROR_COUNT` | Files skipped due to read errors |
| `PEEKDOCS_ELAPSED_SECONDS` | Wall-clock duration, milliseconds |
| `PEEKDOCS_ARGV` | The original command, space-joined |
| `PEEKDOCS_CWD` | Working directory where the search ran |
| `PEEKDOCS_REPORT_TXT` | Absolute path to the .txt report (if written) |
| `PEEKDOCS_REPORT_DOCX` | Absolute path to the .docx report (if written) |
| `PEEKDOCS_REPORT_JSON` / `_HTML` / `_CSV` / `_PDF` | Set if those optional formats were written |

The hook's stdout/stderr are captured. If the hook exits non-zero, both streams (truncated to 500 chars each) and the exit code are written to `peekdocs_errors.log` so you can debug a broken hook after the fact.

**Worked example — email on match:**

```bash
# /usr/local/bin/notify.sh
#!/bin/bash
mail -s "peekdocs: $PEEKDOCS_MATCH_COUNT findings on $(hostname)" admin@example.com <<EOF
Command: $PEEKDOCS_ARGV
Folder:  $PEEKDOCS_CWD
Matches: $PEEKDOCS_MATCH_COUNT in $PEEKDOCS_FILE_COUNT file(s)
Errors:  $PEEKDOCS_ERROR_COUNT file(s) couldn't be read
Elapsed: ${PEEKDOCS_ELAPSED_SECONDS}s
Report:  $PEEKDOCS_REPORT_DOCX
EOF
```

```bash
peekdocs --regex-collection "my-patterns" -r --timestamp \
    --on-match /usr/local/bin/notify.sh
```

**Worked example — Slack webhook with the JSON report:**

```bash
# /usr/local/bin/notify-slack.sh
#!/bin/bash
[ -f "$PEEKDOCS_REPORT_JSON" ] || exit 0
jq --arg cwd "$PEEKDOCS_CWD" --arg n "$PEEKDOCS_MATCH_COUNT" \
   '{text: "\($n) findings in \($cwd)", attachments: [.matches[:5]]}' \
   "$PEEKDOCS_REPORT_JSON" \
| curl -s -X POST -H 'Content-Type: application/json' \
   -d @- "$SLACK_WEBHOOK_URL"
```

```bash
peekdocs --regex-collection "my-patterns" -r -o json \
    --on-match /usr/local/bin/notify-slack.sh
```

**Persistent default for every cron run:**

```bash
peekdocs --config on_match=/usr/local/bin/notify.sh
```

This saves the hook to `~/.peekdocsrc`. Every subsequent CLI search inherits it without retyping. Override for one run with `--on-match ""` (empty string) to disable, or `--on-match /other/script` to substitute a different hook.

**Observability:** every run that uses `--on-match` (whether by flag or persistent default) records `"on_match_fired": true|false` in its `~/.peekdocs_runs.log` entry. Grep across the log to verify your notifications are actually going out:

```bash
jq 'select(.on_match_fired == false and .match_count > 0) | .timestamp + " " + (.argv | join(" "))' ~/.peekdocs_runs.log
```

(Lists runs where matches were found but the hook reported failure — the IT-relevant "we should have been notified but weren't" query.)

### Diff between runs

#### Why compare snapshots? (and why JSON?)

If you do not come from an IT or security background, "diff two scan results" can sound abstract. Here is what it actually solves.

**The pattern is drift detection.** Picture a QA bench. You do not re-inspect every solder joint on every board — you compare today's reject rate against yesterday's and investigate only the delta. Schedule a peekdocs scan to run every night (via cron on Linux/macOS or Task Scheduler on Windows) and the same logic applies: the interesting question is rarely "how many matches?" but **"what's new since last time?"**

It is the difference between a multimeter and a strip-chart recorder. A standard search is the multimeter — "what's the value right now?" The `--diff` workflow is the strip chart — "show me when the reading drifted, and by how much."

**JSON is just structured plain text.** Think of it as a SPICE netlist or a BOM file with labeled columns. Each entry has a `"filename"`, a `"folder"`, a `"matches"` count, optionally a `"sha256"`. Open one in TextEdit or `less` — it is readable. It is the format `--diff` uses because:

1. *A program can parse it without ambiguity.* The cron job that produced the snapshot pipes it into the next stage (alerting, ticketing, a log aggregator) and that stage needs structure, not prose.
2. *Humans can still read and grep it.* JSON is not binary; if a script misbehaves, you can open the file and see exactly what was captured.

CSV could carry some of the same data, but JSON handles nested structure (files contain matches contain line numbers) more naturally and is the de facto modern choice for machine-to-machine handoff.

**Typical things IT staff look for** with snapshot-diffing:

- **Credential leaks.** Did anyone commit a hardcoded `password=`, AWS key, or API token to source control this week that wasn't there before? Diff yesterday's snapshot against today's; alert on **NEW** entries only.
- **Cleanup verification.** A contractor was told to remove every `TODO: fix before ship`. Did they actually do it? Snapshot before and after — the **REMOVED** count should equal the original TODO count.
- **Stale references.** A document folder still mentions an old product name, an old service URL, or a renamed team after a rebrand. Did a new occurrence slip in this quarter? **NEW** entries are the alert.
- **Unexpected file edits (with `--hash`).** A backup or archived document is not supposed to change between snapshots. If the SHA-256 differs but the match count is identical, the file was edited in a way the search alone would not have noticed — that lands in the **MODIFIED** bucket.
- **Trend analysis.** Plot the CHANGED counts week over week to see whether a problem (deprecated API usage, log error volume) is shrinking or growing.

If you use peekdocs interactively — running searches yourself, eyeballing the report — you will likely never need `--diff`. It exists for the unattended, scheduled, machine-monitored use case where the human is asleep when the scan runs and only wants to be paged on real change.

> **GUI surface:** `Tools → Diff Snapshots` opens the same workflow with two file pickers, a Compare button, and a color-coded results pane (green = NEW, red = REMOVED, orange = CHANGED, purple = MODIFIED). It calls the same code as the CLI, so output matches. Use the GUI for ad-hoc inspection; use the CLI for scheduled jobs that need exit codes for alerting.

#### Basic usage

```bash
# Snapshot 1 (run weekly via cron, name with a date for clarity)
peekdocs --regex-collection my-patterns -r --stdout --hash \
    > /var/log/peekdocs/peekdocs_snapshot_2026-W20.json

# Next week: snapshot 2
peekdocs --regex-collection my-patterns -r --stdout --hash \
    > /var/log/peekdocs/peekdocs_snapshot_2026-W21.json

# Diff
peekdocs --diff /var/log/peekdocs/peekdocs_snapshot_2026-W20.json \
              /var/log/peekdocs/peekdocs_snapshot_2026-W21.json
```

> **Naming convention.** peekdocs report files use the `peekdocs_*_results.*` prefix (e.g. `peekdocs_standard_results.docx`). Snapshot JSONs you redirect to disk are not auto-generated, but for consistency we recommend naming them `peekdocs_snapshot_<label>.json` and diff outputs `peekdocs_diff_<label>.json` so they sort and grep alongside the rest of your peekdocs files.

**Five buckets in the output:**

| Bucket | Meaning |
|--------|---------|
| **NEW** | Files matching in the new run that weren't matching before. The most actionable category — "we have new findings since last scan." |
| **REMOVED** | Files that were matching but no longer are. Usually means the file was deleted, cleaned up, or removed from scope. Not actionable by itself. |
| **CHANGED** | Same file, different match count. e.g. `contract-v2.pdf  3 → 7  (+4)` means four more occurrences appeared. |
| **MODIFIED** | Same file, **same** match count, but the SHA-256 differs — content changed in a way that didn't affect the search outcome. Only detected when both inputs were produced with `--hash`; otherwise this bucket is silently empty. Useful for "the file was edited but our scan didn't notice" investigations. |
| **UNCHANGED** | Files matching in both runs with same count and same content (when hashes are available). Summarized as a count, not enumerated. |

**Exit codes** are diff-flavored, the opposite of search exit codes:

| Code | Meaning |
|------|---------|
| `0` | No actionable change. Either nothing changed, or only files were removed. This is the "boring" success case a cron health check wants. |
| `1` | Actionable change detected: new files matching, more matches in existing files, or content modified. Wrap in `\|\| alert ...` to fire on this. |
| `2` | Error reading or parsing one of the inputs. |

> **Gotcha — `&&` vs `;` for interactive use.** The exit codes above are *opposite* of what most CLI tools return, which surprises people every time. Concretely:
>
> ```bash
> peekdocs --diff peekdocs_snapshot_old.json peekdocs_snapshot_new.json > diff.txt && open -a LibreOffice diff.txt
> ```
>
> Looks reasonable, but if the diff *did* find changes (the case you presumably care about), it returns exit code 1 and the shell's `&&` short-circuits — `open` never runs, even though `diff.txt` was written. Use `;` instead when you want unconditional follow-up:
>
> ```bash
> # Always open the diff, regardless of findings
> peekdocs --diff peekdocs_snapshot_old.json peekdocs_snapshot_new.json > diff.txt ; open -a LibreOffice diff.txt
> ```
>
> Or branch on the real failure case (exit 2 only):
>
> ```bash
> peekdocs --diff peekdocs_snapshot_old.json peekdocs_snapshot_new.json > diff.txt
> [ $? -ne 2 ] && open -a LibreOffice diff.txt
> ```
>
> The `&&`/`||` patterns make sense in cron wrappers, where exit 1 *means* "alert" — see the script at the end of this section. For interactive inspection, reach for `;`.

**JSON output for pipelines:**

```bash
peekdocs --diff peekdocs_snapshot_a.json peekdocs_snapshot_b.json --json | jq '.new | length'
peekdocs --diff peekdocs_snapshot_a.json peekdocs_snapshot_b.json --json | jq '.changed[] | select(.delta > 5)'
```

The JSON payload includes `new`, `removed`, `changed`, `modified`, `unchanged_count`, `old_file_count`, `new_file_count`, `old_match_total`, `new_match_total`. Each entry preserves `folder`, `filename`, match counts, and `sha256` values where available.

**Works with any peekdocs JSON shape:** standard search (`--stdout`), inverse search (`--inverse --stdout`), and regex collections (`--regex-collection --stdout`). If `matches_per_file` is absent (regex-collection without `--hash`), it's reconstructed from the flat `matches` array — you still get a usable diff, just without the MODIFIED bucket.

**Pair with `--on-match` and cron** for a complete IT loop: weekly run produces a snapshot, diff against last week's snapshot, fire a notification only when new findings appear:

```bash
# /usr/local/bin/weekly-scan.sh
WEEK=$(date +%Y-W%V)
LAST=$(ls /var/log/peekdocs/peekdocs_snapshot_*.json | tail -1)
peekdocs --regex-collection my-patterns -r --stdout --hash \
    > "/var/log/peekdocs/peekdocs_snapshot_$WEEK.json"
if ! peekdocs --diff "$LAST" "/var/log/peekdocs/peekdocs_snapshot_$WEEK.json" --json \
      > "/var/log/peekdocs/peekdocs_diff_$WEEK.json"; then
    mail -s "peekdocs: new findings this week" admin@example.com \
        < "/var/log/peekdocs/peekdocs_diff_$WEEK.json"
fi
```

### Headless servers and containers

The CLI is import-clean: it runs on a machine that has **no display, no `tkinter`, and no `customtkinter` installed**. That covers the usual deployment targets — Linux servers without an X session, slim container images, locked-down VMs, fleet scanners triggered from a configuration-management tool.

What this means in practice:

- `pip install git+https://github.com/exbuf/peekdocs.git --no-deps` followed by installing only the non-GUI dependencies works. The package imports cleanly; `customtkinter` is loaded lazily inside the GUI mixins, not at module load.
- `peekdocs --check` is the canonical health probe. On a headless box it reports `customtkinter: not installed — install with: pip install customtkinter` and **still returns exit 0** as long as required dependencies are present. That is the correct signal: "the CLI is fully usable; the optional GUI is not."
- `peekdocs-gui` (the GUI entry point) raises a clear `ImportError` on first invocation if Tk is missing. That is the only behaviour change: do not bind that command in your service unit.
- The core CLI commands — `--check`, `--help`, plain search, `--stdout` — have explicit automated test coverage that runs with Tk blocked. See `tests/test_headless.py` for the current set. Other subcommands (`--diff`, `--runs`, `--regex-collection`, `--suite`, `--list-suites`, `--list-files`) share the same import-time code path and should run headlessly as well, but they don't yet have dedicated headless tests.

A minimal headless install in a container:

```dockerfile
FROM python:3.13-slim
RUN pip install --no-cache-dir peekdocs
# customtkinter is intentionally not installed; the CLI does not need it
ENTRYPOINT ["peekdocs"]
```

If you ever see an `ImportError` involving `tkinter` or `customtkinter` from a CLI command, that is a bug — please file an issue with the exact command and traceback.

### Service accounts and file permissions

When peekdocs runs under a Windows service account or a Linux service user (typical for scheduled tasks), the account's read permissions limit what gets searched. peekdocs treats a permission denial the same as any other read failure:

- The file is **skipped**, not retried.
- An entry is appended to `peekdocs_errors.log` in the output directory with the filename and the underlying error message.
- The terminal/stdout summary line reports the total skip count: `Errors logged to peekdocs_errors.log (N error(s))`.
- The search continues with the remaining readable files. Exit code is still based on whether *any* matches were found.

If you want to surface this in your wrapper, parse `peekdocs_errors.log` after the run, or use the `(N error(s))` line from stdout. The error log is overwritten on each run (it's not append-only), so capture it before the next run if you need history.

### Sharing collections across machines

Regex collections live in one global file per user:

```
~/.peekdocs_regex_collections.json
```

To ship a curated set of patterns to a fleet, distribute this file via your configuration management tool (Ansible, Puppet, Chef, Intune, Jamf, plain `scp`). The GUI Regex Search popup's **Save Collection As** / **Restore From Collection** menu items export and import a single named collection as a portable JSON file — convenient for sharing one collection without overwriting a user's other patterns.

Saved searches and suites are per-folder (`<search-folder>/.peekdocs_collection.json`), so they travel with the data: copy the documents folder and the collection file goes with it.

There is no system-wide config file today; `~/.peekdocsrc` is per-user. If you need to enforce defaults across a fleet, push `~/.peekdocsrc` via your config-management tool.

### Useful CLI references for IT

- `peekdocs --check` — verifies Python version, dependencies, Tesseract, and disk space. Returns 0 if everything is fine, 2 if something is missing. Run this as the first step of a deployment validation.
- `peekdocs --list-suites` — every suite peekdocs knows about, with its folder and search count. Add `--rescan` to walk `~/Documents` and `~/Desktop` for any collection files the index doesn't know about yet.
- `peekdocs --regex-collection --list` — every regex collection by name with its pattern count.
- `peekdocs --index-status` — file count, line count, database size, and creation date for the search index in the current folder.
- `peekdocs --runs` — last 20 search runs from `~/.peekdocs_runs.log` in a readable table. Add a number for more (`--runs 100`), `--json` to re-emit raw JSONL for piping. See [Per-run structured log](#per-run-structured-log).
- `peekdocs --dry-run <terms>` — preflight: how many files, how big, broken down by extension. Honors `-r`, `-t`, `-f`, `--max-file-size`. No content read, no reports, no log entry. Add `--stdout` for JSON output. Use this before unleashing a recursive scan on a network share or unfamiliar folder.
- `peekdocs --on-match /path/to/notify.sh <args>` — fire a shell command when matches are found. Hook receives `PEEKDOCS_MATCH_COUNT`, `PEEKDOCS_REPORT_*`, and friends as env vars; you write the script that does the actual notifying (email, Slack, webhook, syslog). Set `--config on_match=...` for a persistent default that every cron run inherits. See [Notification hook](#notification-hook).
- `peekdocs --diff peekdocs_snapshot_old.json peekdocs_snapshot_new.json` — compare two JSON outputs and report what's new, removed, changed, or modified. Exit 1 if anything actionable changed, 0 otherwise — the natural shape for `|| alert "new findings"` wrappers. Add `--json` for machine-readable output. See [Diff between runs](#diff-between-runs).
- `peekdocs --clear` and `--clear-all` — non-recursive cleanup of result files; useful as a pre-step in test pipelines that want a clean folder.
- `peekdocs -h` — full flag reference. Add `peekdocs --suite "name" --timestamp` or `peekdocs --regex-collection "name" --timestamp --stdout` for the most common batch shapes.

---

*peekdocs is provided "as is" under the [MIT License](https://github.com/exbuf/peekdocs/blob/main/LICENSE), without warranty of any kind, express or implied. The flags and schemas described in this section are operational features of a general-purpose search tool.*

## Search Index (Optional)

Indexing is a one-time setup that makes all future searches on a folder faster. Click **Manage Indexes** → **Build Index(es)** and you're done — Use Index is enabled and Auto-Refresh is set to 1 hour automatically. From that point on, searches use the index behind the scenes and the index stays current on its own.

Under the hood, the index reads your files once, stores the extracted text in a small database, and searches that database instead of re-reading files each time. Results are identical — the index just skips the file-parsing step.

You don't need an index for small folders or one-off searches. If you search a large folder (100+ files) without an index, peekdocs suggests building one on the status line.

**Building an index:**

| Method | Command |
|--------|---------|
| **GUI** | Click **Manage Indexes** → **Build Index(es)**. Use Index is enabled and Auto-Refresh is set to 1 hour automatically |
| **Terminal** | `peekdocs --index` (add `-O` to include OCR for scanned PDFs) |

The index covers the folder and all subfolders. It's stored as `.peekdocs.db` in the search folder — one file, typically 10–20% the size of your documents.

**Staying current:** Auto-Refresh runs incremental updates in the background while the app is open (default: 1 hour after first build). In the terminal, use `peekdocs --index-refresh` manually or with cron. Each search also checks for changes automatically.

**Managing the index:**

| Action | GUI | Terminal |
|--------|-----|----------|
| Build | **Build Index(es)** | `peekdocs --index` |
| Check status | **Index Status** | `peekdocs --index-status` |
| Refresh | Auto-Refresh dropdown | `peekdocs --index-refresh` |
| Delete | **Delete Index(es)** | `peekdocs --index-clear` |
| Toggle on/off | **Use Index** checkbox | Automatic (use `--no-index` to skip) |

**When the index may be slower:** Folders with a few very large files (huge PDFs, massive spreadsheets) can be slower with an index than without one. Direct scanning stops reading a file after finding matches; the index searches all stored text. If indexed searches feel slow, uncheck **Use Index**.

**Use Index with saved searches:** The index setting is saved per search. When you save a search with Use Index checked, reloading it restores that setting. If no index exists when Use Index is on, peekdocs falls back to direct scanning automatically.

**Subfolders:** One index in your top folder covers everything underneath. You can build separate indexes in subfolders too — they're independent and don't interfere with each other.

**Concurrent access:** The index uses SQLite WAL mode with atomic transactions, busy timeouts, and graceful lock handling. Multiple searches, auto-refresh, and external tools can access the same index without blocking each other. If the process crashes mid-refresh, uncommitted changes are rolled back automatically.

## Inverse Search

Normal peekdocs shows files that **contain** your search terms. Inverse search (`--inverse`) flips this — it shows files that **do not contain** the search terms. This answers the question: "Which documents are missing required content?"

**Use cases:**

| Scenario | Command |
|----------|---------|
| Contracts missing an indemnification clause | `peekdocs --inverse -t pdf,docx "indemnification"` |
| Policies missing a confidentiality notice | `peekdocs --inverse -r "CONFIDENTIAL"` |
| Documents without a required signature date | `peekdocs --inverse -x "\d{1,2}/\d{1,2}/\d{2,4}"` |
| Files missing SSNs (data hygiene check) | `peekdocs --inverse -x "\d{3}-\d{2}-\d{4}"` |
| HR documents without employee IDs | `peekdocs --inverse -t pdf,docx -x "[Ee]mp\.?\s*#?\s*\d{4,}"` |

**How it works:**

1. peekdocs searches all files normally and identifies which files have matches
2. It then computes the **difference** — files that were searched but had no matches
3. The console output, TXT/DOCX reports, and optional CSV/JSON/PDF exports all list the files without matches instead of match details

**Output:**

- Console: `Found 8 file(s) WITHOUT matches (out of 20 searched).` followed by a list of filenames
- TXT/DOCX report: includes a "Files WITHOUT matches" section listing each file and its directory
- CSV (`-o csv`): two columns — `filename` and `folder`
- JSON (`-o json`): includes `files_without_matches` count and `inverse_files` array

**In the GUI:** Check the **Inverse** checkbox in the Search Bar (next to the Wizard button) before clicking **Run Search**. The results summary will show how many files are missing the search terms.

**Exit codes:** In inverse mode, exit code 0 means files without matches were found (success — missing content detected). Exit code 1 means all files contained the search terms (nothing to report).

## Boolean Expression Search

The `-e` flag enables boolean expression search, allowing you to combine AND, OR, NOT, and parentheses for complex queries that can't be expressed with the `-a` and `-n` flags alone. There is no limit on the number of terms or nesting depth — you can have as many conditions inside parentheses as you need (e.g., `(budget OR revenue OR limit OR expenses) AND approved`). AND, OR, and NOT must be UPPERCASE to distinguish them from search terms.

### Why use `-e` instead of `-a` and `-n`?

The `-a` flag applies one global AND/OR mode to all terms, and `-n` applies one global exclusion list. This means you can't express queries like:

- "Find lines mentioning **either** (budget AND revenue) **or** (cost AND profit)" — mixing AND and OR in the same query
- "Find lines with budget but not draft, **or** lines with revenue but not obsolete" — different exclusions per group

With `-e`, you can express any combination:

```bash
# Either topic A or topic B, where each topic requires multiple terms
peekdocs -e "(budget AND revenue) OR (cost AND profit)"

# Synonyms within an AND query
peekdocs -e "(budget OR revenue) AND (cost OR profit)"

# Different NOT conditions per group
peekdocs -e "(budget AND NOT draft) OR (revenue AND NOT obsolete)"

# Complex nested logic
peekdocs -e "((merger OR acquisition) AND NOT confidential) OR (ipo AND prospectus)"
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
peekdocs -e -w "budg* AND rev*"

# Regex terms in an expression
peekdocs -e -x "\\d{3}-\\d{4} AND budget"

# Fuzzy terms in an expression (typo-tolerant)
peekdocs -e -z "budgt AND revnue"

# With context lines
peekdocs -e -B 2 -A 2 "(merger OR acquisition) AND NOT draft"
```

### Multi-word terms

Use quotes inside the expression for multi-word terms:

```bash
peekdocs -e '"annual report" AND (2023 OR 2024)'
```

### Range filters in expressions

Range specs (`field:min..max`) can be embedded directly inside boolean expressions, combining value-based filtering with text matching in a single query:

```bash
# Lines mentioning "budget" that contain amounts between $1,000 and $5,000
peekdocs -e "budget AND amount:1000..5000"

# OR logic: budget with amounts in range, or any line with "revenue"
peekdocs -e "(budget AND amount:1000..5000) OR revenue"

# NOT logic: "invoice" lines without amounts over $10,000
peekdocs -e "invoice AND NOT amount:10000.."

# Multiple ranges: invoice with amount and date constraints
peekdocs -e "invoice AND amount:500..5000 AND date:2024-01-01..2024-12-31"

# Range-only expression (no text terms)
peekdocs -e "amount:1000..5000"

# Combine -e with -R for metadata filtering on top of expression logic
peekdocs -e "budget OR revenue" -R filesize:..1M
```

All content fields (date, amount, number, percent, age, time) work inside expressions. Metadata fields (filesize, filedate) only work with the `-R` flag, not inside expressions. See [Range Queries](#range-queries) for comprehensive examples of all range types in both `-R` and `-e` modes.

### Limitations

- `-e` cannot be combined with `-a` (AND mode), `-n` (exclude), or `-p` (proximity) — these features are built into the expression syntax
- To search for the literal word "AND", "OR", or "NOT", enclose it in double quotes inside the expression: `peekdocs -e '"AND" OR budget'`
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

**Basic range filtering** — use `-R` alone to find values in a range, or combine with search terms:

```bash
# Find all lines containing dates in June 2026 (no search term needed)
peekdocs -R date:06/01/2026..06/30/2026

# Find "budget" in lines that mention amounts between $1,000 and $5,000
peekdocs -R amount:1000..5000 budget

# Find "report" in lines dated within 2024
peekdocs -R date:2024-01-01..2024-12-31 report

# Find "invoice" in lines dated in June 2026 (US date format also accepted)
peekdocs -R date:2026-06-01..2026-06-30 invoice
peekdocs -R date:06/01/2026..06/30/2026 invoice   # same search, US format

# Find "invoice" OR "refund" in lines dated in June 2026
peekdocs -R date:06/01/2026..06/30/2026 invoice refund

# Find "invoice" AND "refund" on the same line, dated in June 2026
peekdocs -a -R date:06/01/2026..06/30/2026 invoice refund

# Find "meeting" in lines with times between 9 AM and 5 PM
peekdocs -R time:09:00..17:00 meeting

# Find "growth" in lines with percentages between 10% and 50%
peekdocs -R percent:10..50 growth

# Find "visit" in lines mentioning ages 18 to 65
peekdocs -R age:18..65 visit

# Find lines with any standalone number between 100 and 999
peekdocs -R number:100..999 report
```

**Open-ended ranges** — omit min or max for unbounded filtering:

```bash
# Amounts of $10,000 or more
peekdocs -R amount:10000.. contract

# Amounts up to $500
peekdocs -R amount:..500 expense

# Files larger than 10 MB
peekdocs -R filesize:10M.. report

# Files smaller than 100 KB
peekdocs -R filesize:..100K memo

# Dates from 2024 onward
peekdocs -R date:2024-01-01.. report

# Dates before July 2024
peekdocs -R date:..2024-06-30 invoice

# After-hours times only
peekdocs -R time:17:00.. log

# Percentages above 90%
peekdocs -R percent:90.. performance
```

**Multiple ranges** combine with AND logic — all must match:

```bash
# Invoices with amounts $1,000-$5,000 AND dated within 2024
peekdocs -R amount:1000..5000 -R date:2024-01-01..2024-12-31 invoice

# Payments over $500 in lines mentioning ages 18-65
peekdocs -R amount:500.. -R age:18..65 payment

# Small, recent files only
peekdocs -R filesize:..100K -R filedate:2025-01-01.. memo

# Large files modified in 2024
peekdocs -R filesize:10M.. -R filedate:2024-01-01..2024-12-31 report
```

**Filename ranges** — use `fn:` to filter files by values extracted from their filenames:

```bash
# Only search files with 2024 dates in the filename (e.g., report-2024-06-15.pdf)
peekdocs -R fn:date:2024-01-01..2024-12-31 budget

# Combine filename range with content range
peekdocs -R fn:date:2024-01-01..2024-12-31 -R amount:1000..5000 invoice

# Filename range in an expression
peekdocs -e "budget AND fn:date:2024-01-01..2024-12-31"
```

**Range-only search** — use `-R` without text terms to find all lines containing values in range:

```bash
# Find all lines with dollar amounts between $1,000 and $5,000
peekdocs -R amount:1000..5000

# Find all lines with dates in Q1 2024
peekdocs -R date:2024-01-01..2024-03-31

# Find all lines with percentages over 50%
peekdocs -R percent:50..
```

**Combining with other flags:**

```bash
# Range with recursive search
peekdocs -R amount:1000..5000 -r budget

# Range with file type filter
peekdocs -R amount:1000.. -t .pdf,.docx invoice

# Range with context lines
peekdocs -R amount:5000..10000 -B 2 -A 2 payment

# Range with AND mode text search
peekdocs -R date:2024-01-01..2024-12-31 -a budget revenue

# Range with exclude terms
peekdocs -R amount:1000..5000 -n draft invoice

# Range with whole-word matching
peekdocs -R amount:1000..5000 -W budget

# Range with max matches limit
peekdocs -R amount:1000..5000 -m 50 invoice
```

### Range specs in boolean expressions

Range specs can also be embedded directly inside `-e` expressions using the same `field:min..max` syntax. This lets you combine value-based filtering with boolean logic in a single query:

```bash
# Lines mentioning "budget" that contain amounts between $1,000 and $5,000
peekdocs -e "budget AND amount:1000..5000"

# Lines mentioning "report" with dates in 2024
peekdocs -e "report AND date:2024-01-01..2024-12-31"

# Lines with "growth" and a percentage above 20%
peekdocs -e "growth AND percent:20..100"

# Lines with "visit" and an age between 18 and 65
peekdocs -e "visit AND age:18..65"

# Lines with "meeting" and a time between 9 AM and 5 PM
peekdocs -e "meeting AND time:09:00..17:00"
```

**OR logic** — match one condition or the other:

```bash
# Lines with budget amounts in range, OR any line with "revenue"
peekdocs -e "(budget AND amount:1000..5000) OR revenue"

# Match either high amounts OR high percentages
peekdocs -e "amount:10000.. OR percent:50.."

# Different criteria per branch
peekdocs -e "(budget AND amount:1000..5000) OR (invoice AND date:2024-01-01..2024-12-31)"
```

**NOT logic** — exclude lines matching a range:

```bash
# "invoice" lines that do NOT have amounts over $10,000
peekdocs -e "invoice AND NOT amount:10000.."

# "contract" lines excluding dates before 2024
peekdocs -e "contract AND NOT date:..2023-12-31"

# Complex: require text + range, exclude another range
peekdocs -e "(contract AND amount:5000..50000) AND NOT date:..2023-12-31"
```

**Multiple ranges in one expression:**

```bash
# Invoice lines with amounts $500-$5,000 AND dated in 2024
peekdocs -e "invoice AND amount:500..5000 AND date:2024-01-01..2024-12-31"

# Payment lines with both amount and time constraints
peekdocs -e "payment AND amount:100..1000 AND time:09:00..17:00"
```

**Range-only expressions** (no text terms):

```bash
# All lines with amounts in range
peekdocs -e "amount:1000..5000"

# Lines with amounts in range OR percentages in range
peekdocs -e "amount:1000..5000 OR percent:10..50"
```

**Combining with other modes:**

```bash
# Wildcard terms with a range
peekdocs -e -w "budg* AND amount:1000..5000"

# Regex terms with a range
peekdocs -e -x "INV-\\d+ AND amount:1000..5000"

# Fuzzy terms with a range
peekdocs -e -z "budgt AND amount:1000..5000"

# Expression + -R flag for metadata filtering
peekdocs -e "budget AND amount:1000..5000" -R filesize:..1M

# Expression + -R flag for file date filtering
peekdocs -e "budget OR revenue" -R filedate:2024-01-01..2024-12-31
```

**Real-world scenarios:**

```bash
# Find contracts with payments over $50,000 signed in 2024
peekdocs -e "contract AND amount:50000.. AND date:2024-01-01..2024-12-31"

# HR: find employee records for people aged 55-65
peekdocs -e "(employee OR staff) AND age:55..65"

# Finance: find Q4 invoices between $1,000 and $10,000
peekdocs -e "invoice AND amount:1000..10000 AND date:2024-10-01..2024-12-31"

# Audit: find high-growth reports (over 25%) excluding drafts
peekdocs -e "growth AND percent:25.. AND NOT draft"

# Legal: find settlements over $100,000 or judgments over $500,000
peekdocs -e "(settlement AND amount:100000..) OR (judgment AND amount:500000..)"

# Visit records logged after 5pm for a given age range
peekdocs -e "visit AND age:18..30 AND time:17:00.."

# Small recent PDFs with budget amounts over $5,000
peekdocs -e "budget AND amount:5000.." -R filesize:..1M -R filedate:2025-01-01.. -t .pdf

# Find budget mentions only in files from 2024 (by filename date)
peekdocs -R fn:date:2024-01-01..2024-12-31 budget

# Invoices from 2024 (filename) with amounts $1,000-$10,000 (content)
peekdocs -R fn:date:2024-01-01..2024-12-31 -R amount:1000..10000 invoice

# Expression: budget lines in 2024-dated files
peekdocs -e "budget AND fn:date:2024-01-01..2024-12-31"
```

### Notes on range queries

- **Inclusive bounds** — both min and max are inclusive. `amount:1000..5000` matches $1,000, $5,000, and everything in between
- **Content fields** (date, amount, number, percent, age, time) extract values from document text and filter at the line level
- **Filename ranges** (`fn:` prefix) extract values from the filename string and filter entire files — files whose names don't contain matching values are skipped entirely. All 6 content fields work with `fn:`
- **Metadata fields** (filesize, filedate) filter entire files by their properties before text scanning — files that don't match metadata ranges are skipped entirely
- **Multiple values in one line** — if a line contains multiple values of the same type (e.g., two dates or three dollar amounts), the line matches if **any one** of those values falls within the range. All ranges must still be satisfied (AND logic across different ranges)
- **Metadata in expressions** — metadata fields (`filesize`, `filedate`) can only be used with the `-R` flag, not inside `-e` expressions. Use `-R` alongside `-e` for metadata filtering
- **`-R` + `-e` together** — when using `-R` alongside `-e`, the `-R` filters apply as an additional AND layer on top of the expression result
- **Multiple `-R` flags** — combine with AND logic; all ranges must be satisfied
- **Bound string flexibility** — amounts accept `$` and `,` (e.g., `amount:$1,000..$5,000`), percents accept `%` (e.g., `percent:10%..50%`), dates accept ISO (`YYYY-MM-DD`) and US (`MM/DD/YYYY`, `MM-DD-YYYY`) formats, times accept `HH:MM`, `HH:MM:SS`, and `HH:MM AM/PM` formats
- **Long form** — `--range` is the long form of `-R` (e.g., `--range amount:1000..5000`)
- **Reports** — when range filters are active, they appear in the report header as modifiers (e.g., "range filter amount: 1000 .. 5000"). For range-only searches (no text terms), the report describes the search as "with range filters only"
- **Index search** — ranges work with the search index. Indexed results are post-filtered by content and metadata ranges
- **Saved searches** — range filters are fully preserved in saved searches and restored when you reload them. Enter ranges in the GUI's Range field before clicking **Save Search**
- **Settings persistence** — the Range field value is saved to `~/.peekdocsrc` when you click **Save Defaults** in Advanced Search Options, and restored when the GUI opens or when you click Restore Settings

In the GUI, enter range filters in the **Range** field in Advanced Search Options, comma-separated for multiple ranges (e.g., `amount:1000..5000, date:2024-01-01..2024-12-31`).

## Combining Modes

You can mix multiple modes together for more powerful searches.

**Regex + AND + Recursive** — Find files containing both an invoice ID (`INV-12345`) and a dollar amount anywhere in nested subfolders:

```bash
peekdocs -x -a -r "\bINV-\d+\b" "\$[\d,]+\.\d{2}"
```

In the GUI:

```
      Terms:  \d{3}-\d{2}-\d{4}  \$[\d,]+\.\d{2}
Checkboxes:  Regex, AND mode, Recursive
```

**Wildcard + File Types** — Find any mention of "report" variations in PDFs only:

```bash
peekdocs -w -t pdf "report*"
```

In the GUI:

```
      Terms:  report*
Checkboxes:  Wildcard       File Types: .pdf
```

**Expression + Range + Context** — Find lines mentioning budget or revenue (but not draft) with amounts over 10,000, showing surrounding lines:

```bash
peekdocs -e "(budget OR revenue) AND NOT draft" -R amount:10000..999999 -B 2 -A 2
```

In the GUI:

```
Expression:  (budget OR revenue) AND NOT draft
Range:       amount:10000..999999
Context:     Before=2, After=2
```

**Whole Word + AND + Proximity** — Find "breach" and "contract" as whole words within 5 words of each other (avoids matching "breached" or "contractor"):

```bash
peekdocs -W -p 5 "breach" "contract"
```

In the GUI:

```
      Terms:  breach contract
Checkboxes:  Whole Word, AND mode     Proximity: 5
```

**Fuzzy + Recursive + File Types** — Find misspelled names across all Word docs in subfolders:

```bash
peekdocs -z -r -t docx "accommodation" "occurrence"
```

In the GUI:

```
      Terms:  accommodation  occurrence
Checkboxes:  Fuzzy, Recursive   File Types: .docx
```

**Inverse + Regex** — Find files that do NOT contain a required signature line:

```bash
peekdocs --inverse -x "Authorized\s+Signature"
```

In the GUI:

```
      Terms:  Authorized\s+Signature
Checkboxes:  Regex, Inverse
```

## Breaking Down Complex Searches

When a single search becomes too complex, break it into several focused searches and run them one at a time, or save each one with Save Search and reload them later.

**Why this helps:**

- Each search is simpler to configure and understand
- You see exactly which files matched which check
- Easy to update one check without affecting others
- Saved searches can be reloaded individually later

**Example: Breaking down a document review** — Instead of one giant search, save a series of focused searches:

```
1. "find_contracts"    — Terms: contract
2. "missing_date"      — Regex: \d{2}/\d{2}/\d{4}  + Inverse
3. "no_draft_stamp"    — Terms: DRAFT
4. "amounts_in_range"  — Range: amount:1000..50000
5. "has_ssn"           — Regex: \d{3}-\d{2}-\d{4}
```

Use Load Search to reload each one when you need it. The search bar and all Advanced Search Options settings are restored exactly as they were when you saved the search.

## Saved Settings (Optional)

If you find yourself typing the same flags every time, you can save them as defaults so peekdocs remembers them for you. This is entirely optional — peekdocs works fine without it.

Use the `--config` flag to manage your saved settings:

```bash
peekdocs --config recursive=true       # always search subdirectories
peekdocs --config quiet=true cores=4   # save multiple settings at once
peekdocs --config max_file_size_mb=0   # no file size limit (default is 100 MB)
peekdocs --config max_file_size_mb=500 # skip files larger than 500 MB
peekdocs --config                      # view your saved settings
peekdocs --config recursive=           # remove a saved setting
```

Note: `--config` saves settings permanently. To override for a single search without saving, use the flag directly: `peekdocs --max-file-size 0 budget`.

Once saved, your settings apply automatically every time you run peekdocs. For example, after running `peekdocs --config recursive=true quiet=true cores=4`, typing `peekdocs budget` behaves like `peekdocs -r -q -c 4 budget`. You can always override a saved setting for a single search by typing the flag explicitly — this does not change your saved settings.

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
| `timestamp` | true/false | `--timestamp` | false (overwrite previous results) |
| `output_dir` | path | `--output-dir` | empty (write to search folder) |
| `range` | spec list | `-R` | empty (no range filtering) |
| `max_file_size_mb` | number | `--max-file-size N` | 100 (skip files larger than 100 MB, 0 = no limit) |
| `output_pdf` | true/false | `-o pdf` | false (no PDF output) |
| `output_html` | true/false | `-o html` | false (no HTML output) |
| `index_search` | true/false | `-I` | false (direct file search) |
| `search_terms` | text | — | empty (none) |
| `folder` | path | — | empty (current directory) |
| `text_size` | text | — | Normal (GUI only) |
| `preview_size` | text | — | 11 (GUI only) |
| `appearance_mode` | text | — | System (GUI only) |

If no settings are saved or if a value is invalid, peekdocs uses its built-in defaults. The `search_terms`, `folder`, and `index_search` settings are GUI-only — they pre-fill the GUI fields when it opens but have no effect on CLI searches.

**Advanced:** Your settings are stored in a text file called `.peekdocsrc` in your user folder. You can also edit this file directly if you prefer — each line is a `key = value` pair, and lines starting with `#` are comments.

## Files Created by peekdocs

peekdocs creates several types of files during normal operation. Understanding what each file is, where it lives, and how to manage it helps you keep your folders clean and troubleshoot issues.

**How to identify peekdocs files:** Every file peekdocs creates has "peekdocs" in the filename — either starting with `peekdocs_` (reports, results, error log) or `.peekdocs` (index, saved searches, settings). If you see "peekdocs" in a filename, it's ours. If you don't, it's your document.

**Important:** peekdocs never modifies, moves, or deletes your original documents. All files listed below are created by peekdocs itself. peekdocs can delete its own files when you ask — use **Clear Files** in the Tools menu to choose which peekdocs files to remove. These operations only affect files that peekdocs created, never your documents.

### Search reports

These are your search results. **All result files — TXT, DOCX, CSV, JSON, PDF, and HTML — are overwritten each time you run a new search.** If you enable the Timestamp checkbox in Advanced Search Options, each search creates uniquely named files (e.g., `peekdocs_standard_results_20260331_103425.docx`) — useful for keeping a history, but files accumulate over time. **Delete on Close**, **Delete Now**, and **Clear Files** all clean up timestamped files — they match any file starting with `peekdocs_standard_results`, `peekdocs_regex_results`, or `peekdocs_suite_results`, regardless of the timestamp suffix.

| File | Purpose | Location |
|------|---------|----------|
| `peekdocs_standard_results.txt` | Plain text report | Search folder (or `--output-dir`) |
| `peekdocs_standard_results.docx` | Word report with yellow-highlighted matches | Search folder (or `--output-dir`) |
| `peekdocs_standard_results.csv` | Spreadsheet format (optional, with `-o csv`) | Search folder (or `--output-dir`) |
| `peekdocs_standard_results.json` | Machine-readable format (optional, with `-o json`) | Search folder (or `--output-dir`) |

**Protected from searching:** Yes — all filenames starting with `peekdocs_standard_results`, `peekdocs_regex_results`, or `peekdocs_suite_results` are excluded so peekdocs never searches its own reports (including timestamped versions).
**How to delete:** Click **Clear Results** on the bottom toolbar to delete all of these result files at once (a confirmation dialog lists the files before deletion). Or delete them manually. They are recreated on the next search. You can also check **Delete on Close** (on the main screen next to the report buttons, or in Advanced Search Options) to automatically delete all result files when you close peekdocs — see [Delete on Close](#delete-on-close) below.

### Saved and accumulated reports

Created when you use `-s` (save) or `-sa` (append) to archive results with a name you choose.

| File | Purpose | Location |
|------|---------|----------|
| `peekdocs_report_{name}.txt` | Named archive of search results (text) | Search folder (or `--output-dir`) |
| `peekdocs_report_{name}.docx` | Named archive of search results (Word) | Search folder (or `--output-dir`) |
| `peekdocs_accumulated_{name}.txt` | Accumulated results from multiple searches (text) | Search folder (or `--output-dir`) |
| `peekdocs_accumulated_{name}.docx` | Accumulated results from multiple searches (Word) | Search folder (or `--output-dir`) |

**Protected from searching:** Yes — the `peekdocs_report_` and `peekdocs_accumulated_` prefixes ensure these are never included in future searches.
**How to delete:** Delete them manually at any time, or use **Clear Results** on the main screen to remove the standard/regex/suite result files.

### Error log

An append-only log of file processing errors and crash reports.

| File | Purpose | Location |
|------|---------|----------|
| `peekdocs_errors.log` | Records files that couldn't be read (permission denied, corrupted, locked) and crash diagnostics | Search folder (or `--output-dir`) |

**Protected from searching:** Yes — this filename is explicitly excluded.
**How to delete:** Click **Clear Error Log** on the bottom toolbar, or delete manually. The file is automatically recreated the next time a file error occurs. If peekdocs runs cleanly with no errors, no error log is created.

### Search index

An optional SQLite database that stores extracted text for faster repeated searches.

| File | Purpose | Location |
|------|---------|----------|
| `.peekdocs.db` | SQLite FTS5 full-text search index | Search folder |
| `.peekdocs.db-wal` | Write-Ahead Log (temporary, for concurrent access) | Search folder |
| `.peekdocs.db-shm` | Shared memory file (temporary, for concurrent access) | Search folder |

**Protected from searching:** Yes — excluded by filename.
**How to delete:** Use `peekdocs --index-clear` or the **Delete Index(es)** button in the GUI. This removes all three files. The index can be rebuilt at any time with `peekdocs --index`. The `-wal` and `-shm` files are created and removed automatically by SQLite — if they persist after a crash, they are safe to delete manually.
**How to recover:** If the index becomes corrupted, peekdocs detects it automatically, deletes it, and falls back to direct file scanning. Rebuild with `peekdocs --index`.

### Collection file

Stores your saved searches for each folder.

| File | Purpose | Location |
|------|---------|----------|
| `.peekdocs_collection.json` | Saved searches | Each search folder |

**Protected from searching:** Yes — excluded by filename.
**Caution:** This file contains all your saved searches for the folder. **Do not delete it unless you intend to lose them.** There is no undo — you would need to recreate every saved search from scratch in the GUI.
**How to back up:** Copy the file to a safe location. It's a standard JSON file that can be viewed in any text editor. Consider backing it up before major changes.

### Search history

Automatic log of every search you run.

| File | Purpose | Location |
|------|---------|----------|
| `~/.peekdocs_history.json` | Records each search with date, terms, match count, file count, and elapsed time | Home directory |

**Protected from searching:** Yes — located in your home directory.
**How to delete:** Use **Clear History** in the Search History popup (Tools menu), or delete the file manually. Keeps the last 200 entries automatically.

### Bookmarks

Files you've pinned for quick access.

| File | Purpose | Location |
|------|---------|----------|
| `~/.peekdocs_bookmarks.json` | List of bookmarked file paths with notes and dates | Home directory |

**Protected from searching:** Yes — located in your home directory.
**How to delete:** Remove individual bookmarks from the Bookmarks popup (right-click → Remove Bookmark), or delete the file to clear all bookmarks.

### Configuration file

Your saved default settings.

| File | Purpose | Location |
|------|---------|----------|
| `~/.peekdocsrc` | Default values for all CLI flags and GUI settings | Home directory (`~` = `/Users/you` on Mac, `C:\Users\you` on Windows, `/home/you` on Linux) |

**What does "rc" mean?** The "rc" in `.peekdocsrc` stands for "run commands" — a naming convention from Unix in the 1960s. Files ending in `rc` (like `.bashrc`, `.vimrc`, `.peekdocsrc`) contain startup configuration that's loaded when the program runs. It simply means "config file."

**Protected from searching:** Yes — located in your home directory, not in any search folder. Also excluded by filename if it happens to be in a search folder.
**How to delete:** Delete it to reset all settings to defaults. You can also click **Reset** in Advanced Search Options and then **Save Defaults** to overwrite it with defaults. Use **Inspect .peekdocsrc** in Advanced Search Options to view its current contents.
**What happens if it's deleted?** peekdocs runs normally using built-in defaults. Nothing breaks — you just lose your customized settings.
**How to recover:**
1. Open the GUI (`peekdocs-gui`)
2. Open **Advanced Search Options** and configure your preferred settings (recursive, file types, cores, max matches, etc.)
3. Click **Save Defaults** — this recreates the file
5. Change the **Text Size** dropdown if you had a non-default size — it auto-saves immediately

The file is a plain text list of key-value pairs. You can also recreate it from the terminal: `peekdocs --config recursive=true` saves a single setting, and each subsequent `--config` call adds to it.

### Summary

| Category | File count | Auto-excluded from searches | Can safely delete |
|----------|-----------|----------------------------|-------------------|
| Search reports | 2-4 per search | Yes | Yes — recreated on next search |
| Saved/accumulated reports | 2 per save | Yes | Yes — user's choice |
| Auto-run log | 1 per folder | Yes | Yes — use Clear Auto-Run History |
| Error log | 0-1 per folder | Yes | Yes — use Clear Error Log |
| Search index | 1-3 per folder | Yes | Yes — use Delete Index or --index-clear |
| Collection file | 1 per folder | Yes | **No** — contains your saved searches. Back up before deleting |
| Config file | 1 (home dir) | N/A | With caution — loses saved settings |
| Search history | 1 (home dir) | N/A | Yes — only loses search log |
| Bookmarks | 1 (home dir) | N/A | Yes — only loses pinned files list |

**Most of these files are safe to delete** — peekdocs recreates reports, logs, and indexes automatically. The two exceptions are the **collection file** (`.peekdocs_collection.json`), which contains your saved searches, and the **config file** (`~/.peekdocsrc`), which contains your settings and email configuration. Deleting either of these means recreating that work from scratch. Everything else can be deleted freely.

### Delete on Close

Check the **Delete on Close** checkbox to automatically delete all search result files (`peekdocs_standard_results.*`, `peekdocs_regex_results.*`, `peekdocs_suite_results.*`) when you close peekdocs. The checkbox appears in two places — on the main screen next to the report buttons, and in Advanced Search Options — both stay in sync.

You can check or uncheck this at any time. It only matters at the moment you close the app. A typical workflow:

1. Run a search
2. Review your results in the Results Preview or by opening the reports
3. When you're done, check **Delete on Close**
4. Close peekdocs — result files are automatically deleted

If you change your mind, uncheck the box before closing and the files are kept.

**What gets deleted:** `peekdocs_standard_results.*`, `peekdocs_regex_results.*`, `peekdocs_suite_results.*`, and the search index (`.peekdocs.db`) in every folder searched during the session — not just the last one. If you searched three different folders, all three are cleaned.

**What is never deleted:** Saved reports (`peekdocs_report_*`), accumulated reports (`peekdocs_accumulated_*`), saved searches, settings, indexes, and error logs. These are files you explicitly chose to keep or that peekdocs needs to function.

The setting is saved to `~/.peekdocsrc` and persists between sessions — if you always want results cleaned up, check it once and it stays checked.

### Privacy cleanup options

peekdocs provides several ways to clean up after a search session:

| Feature | Where | What it does | When |
|---------|-------|-------------|------|
| **Delete on Close** | Checkbox on main screen or Advanced Search Options | Deletes `peekdocs_standard_results.*`, `peekdocs_regex_results.*`, `peekdocs_suite_results.*`, and the search index (`.peekdocs.db`) in every folder searched during the session | Automatically when you close peekdocs |
| **Clear History on Close** | Checkbox in Advanced Search Options | Clears search history (`~/.peekdocs_history.json`) and recent searches from `~/.peekdocsrc` | Automatically when you close peekdocs |
| **Clear Preview** | Button on Results Preview header | Wipes all visible match data from the Results Preview pane | Immediately on click |
| **Delete Now** | Main screen (report row) | Deletes result files and search indexes in every folder searched during the session, clears preview, wipes search history, and blanks search terms and folder — all at once | Immediately, after confirmation |
| **Clear Files** | Tools menu | You choose — checkboxes for each file | Immediately, after confirmation |
| **Manually** | Finder (macOS), File Explorer (Windows), or file manager (Linux) | Whatever you select | Anytime |

All methods except **Delete Now** leave the search index untouched. **Delete Now** includes the index because it contains extracted text from every indexed file — effectively a searchable copy of your document content, including any sensitive data. **Delete on Close** and **Delete Now** both clean all possible report locations: the search folder, any custom output directory, and `~/peekdocs_reports` (the safe redirect folder for cloud-synced searches). Saved reports (`peekdocs_report_*`), accumulated reports (`peekdocs_accumulated_*`), saved searches, and settings are never deleted by any of these methods. Only **Clear Files** gives you the option to delete those as well, and only if you explicitly check them.

### CLI cleanup scope (`--clear`, `--clear-all`)

The CLI also has two cleanup commands. Their scope differs slightly from the GUI's **Delete Now** button — by design. The CLI cares about on-disk files; the GUI also cares about live UI state (preview, history, fields). Here is the exact scope of each:

| What gets deleted | CLI `--clear` | CLI `--clear-all` | GUI **Delete Now** |
|---|:---:|:---:|:---:|
| Result files (`peekdocs_standard_results.*`, `peekdocs_regex_results.*`, `peekdocs_suite_results.*`) | ✓ | ✓ | ✓ |
| Search index (`.peekdocs.db`, `.peekdocs.db-wal`, `.peekdocs.db-shm`) | — | ✓ | ✓ |
| Error log (`peekdocs_errors.log`) | — | ✓ | — |
| Saved reports (`peekdocs_report_*`) | — | ✓ | — *(preserved)* |
| Accumulated reports (`peekdocs_accumulated_*`) | — | ✓ | — *(preserved)* |
| `.peekdocs_collection.json` (saved searches and suites) | — *(preserved)* | — *(preserved)* | — *(preserved)* |
| `~/.peekdocsrc` settings | — *(preserved)* | — *(preserved)* | — *(preserved)* |
| Bookmarks | — *(preserved)* | — *(preserved)* | — *(preserved)* |
| Search history | — | — | ✓ |
| Results Preview, search terms, folder fields (UI state) | n/a | n/a | ✓ |

**Why `.peekdocs_collection.json`, `~/.peekdocsrc`, and bookmarks are always preserved.** They represent *user work*, not search output. Building a useful search suite or curating a bookmark list takes time, and a single typo on the command line shouldn't wipe that out. None of the cleanup commands — CLI or GUI — will touch them.

**If you actually do want to delete `.peekdocs_collection.json`**, remove it by hand from the search folder:

```bash
rm .peekdocs_collection.json                    # macOS / Linux
```

```powershell
Remove-Item .peekdocs_collection.json           # Windows PowerShell
```

Or just delete the file from Finder / File Explorer / your file manager. The next time you open the folder in peekdocs, the saved-searches list will be empty and a fresh `.peekdocs_collection.json` will be created when you save your first search there.

### Cloud-synced folders

If your search folder is inside OneDrive, Google Drive, iCloud Drive, or Dropbox, peekdocs automatically redirects report output to a safe local folder (`~/peekdocs_reports`). Your documents are still searched in the original cloud-synced location — only the report output changes. This helps prevent report files from being written to a location that automatically uploads to the cloud.

The redirect happens silently — the search runs without interruption. The status line tells you where reports were saved and why. The output directory setting is saved to `~/.peekdocsrc` and persists between sessions.

**Delete on Close** and **Delete Now** both clean `~/peekdocs_reports` along with the search folder and any custom output directory — so reports saved there are not forgotten.

### Numeric-pattern search term warning

If you type a search term that matches certain numeric ID patterns (such as a 9-digit ID with dashes, a 13-to-19-digit run with optional dashes/spaces, or a 2-digit-dash-7-digit pattern), peekdocs warns you before running the search. The warning explains that your search term will appear in the report files written to disk. You can choose to continue or cancel.

### Known limitations (what peekdocs cannot control)

peekdocs takes a number of steps to protect user data (safe app opening, cloud folder detection, Delete on Close, Clear History on Close, Clear Preview, Delete Now, search-term pattern warnings). The following are outside the application's control:

- **CLI process arguments.** When the GUI runs a search, it launches `peekdocs` as a subprocess with search terms in the command line. On Unix/macOS, other users on the same machine can see process arguments via `ps aux`. If someone searches for a specific numeric ID or account number, that term is briefly visible in the process list while the search runs.
- **Report file permissions.** Check **Restrict File Permissions** in Advanced Search Options to set all report files to owner-only read/write (chmod 600) on Unix/macOS. This prevents other users on shared machines from reading your search results. Off by default — leave unchecked if colleagues need to access reports in a shared folder. No effect on Windows (NTFS permissions are managed differently).
- **Temp files from archives.** Searching inside `.zip`, `.7z`, and `.rar` files may extract content to temporary directories. If the process is killed mid-search, those temp files could persist. Under normal operation they are cleaned up automatically.
- **Process memory.** Sensitive data found during a search sits in Python process memory until garbage collected. The operating system may write process memory to swap/page files on disk. This is standard behavior for all desktop applications and is not practically exploitable on a single-user machine, but it means sensitive data could theoretically persist in swap space after the application closes.
- **Error log file paths.** The error log (`peekdocs_errors.log`) contains file paths of documents that could not be read. This reveals which folders and files were being searched, though not the content of those files.
- **Microsoft 365 desktop apps.** peekdocs launches the local Word desktop application (`WINWORD.EXE` / `Microsoft Word.app`) — never Word Online or any browser-based editor. However, if the user is signed into a Microsoft 365 account, the desktop Word app may show the file in their "Recent" list on office.com, prompt to upload to OneDrive, or auto-save if the file is in a OneDrive-synced folder. peekdocs cannot control the internal cloud features of local applications after launching them. If this is a concern, use LibreOffice (which has no cloud integration) or the HTML report (which opens in your browser directly from local disk).
- **Forced process termination.** Delete on Close and Clear History on Close run during normal app shutdown. If the process is force-killed (kill -9, Task Manager End Process, or a system crash), cleanup does not run and report files, search history, and indexes remain on disk. Use Delete Now before closing if immediate cleanup is critical.
- **Custom regex patterns.** User-supplied regex patterns (in the search bar, Regex Search, or the Search Wizard) have no execution timeout. A pathological pattern (e.g., catastrophic backtracking) could cause the search to hang indefinitely. peekdocs validates regex syntax but does not limit pattern complexity.
- **Cloud folder detection is path-based.** peekdocs detects cloud-synced folders by looking for keywords like "OneDrive," "Dropbox," "Google Drive," and "iCloud" in the folder path. A folder with a cloud keyword in its name (e.g., `MyDropboxAnalysis`) would be falsely detected as cloud-synced and reports would be redirected to `~/peekdocs_reports`. Rename the folder to avoid the false trigger.
- **Safe output folder fallback.** If `~/peekdocs_reports` is itself inside a cloud-synced directory (e.g., the entire home directory is synced to OneDrive), peekdocs falls back to the system temp directory (`/tmp` on Unix/macOS, `%TEMP%` on Windows). This is automatic and requires no user action.
- **Backup software.** Report files written to disk may be picked up by backup software (Time Machine, Windows Backup, Backblaze, Carbonite, etc.) and uploaded to cloud storage. peekdocs avoids cloud-synced *folders* but cannot detect or prevent background backup services that copy files after they are written. Use **Delete on Close** or **Delete Now** to remove report files before backups run.

## Limits and Constraints

**peekdocs imposes no hard limits in code.** There is no cap on file count, file size, PDF page count, spreadsheet rows, search terms, saved searches, or index size. Practical limits come from your hardware (memory, disk, CPU) and the operating system (file-descriptor limits, path-length limits).

**Optional safeguards (all configurable, all removable):**

The following defaults exist to prevent accidental slowdowns or memory issues on very large folders. They are **entirely optional** — set any of them to 0 or remove them if you prefer no limits. peekdocs will search everything your hardware can handle.

| Safeguard | Default | Flag | Why it exists | How to remove |
|-----------|---------|------|---------------|---------------|
| **Max matches in reports** | 1,000 | `-m N` | Writing 50,000 matches to a .docx file can take minutes and produce a very large report. The total match count is always accurate in the summary — only the report files are capped | Set `-m 0` for unlimited |
| **Max file size** | 100 MB | `--max-file-size N` | Very large files (multi-GB PDFs, massive spreadsheets) can take minutes to parse and may exhaust memory. Skipped files appear in the Excluded Files list after each search so you know what was missed | Set `--max-file-size 0` for no limit. In the GUI, set **Max File Size (MB)** to 0 in Advanced Search Options |
| **CPU cores** | Half of available | `-c N` | Using all cores speeds up searches but makes your computer unresponsive while searching | Set `-c` to your full core count for maximum speed |

These safeguards exist because a user once searching a folder with multi-GB database exports shouldn't have to wonder why the app froze — the defaults protect against that while being easy to override. If you know your files are manageable, remove the limits entirely.

**Why raising Max File Size can show fewer matched files:** This is counterintuitive but expected. When a very large file (e.g., a 110 MB log file) contains thousands of matches, those matches consume most of the Max Matches budget (default 1,000). Fewer slots remain for matches from other files, so the Matched Files count goes *down* even though you're searching *more* files. Lowering Max File Size to skip the large file frees up those match slots for other files, so you actually see more matched files. If you raise Max File Size and notice fewer matched files, raise Max Matches too (or set it to 0 for unlimited).

**Setting permanent defaults with `--config`:** The `--config` flag saves a setting to a configuration file (`~/.peekdocsrc`) so it applies automatically every time you run peekdocs — you don't have to type the flag on every search. For example, if you always want a higher match cap:

```bash
peekdocs --config max_matches=5000     # save the setting once
peekdocs budget                         # all future searches use max_matches=5000
```

You can still override a saved setting on any individual search by passing the flag directly:

```bash
peekdocs -m 0 budget                    # this search only: unlimited matches (overrides saved 5000)
```

To see all your saved settings: `peekdocs --config`. To reset a setting to its default: `peekdocs --config max_matches=`. The `--config` flag works for many settings — see the [Saved Settings](#saved-settings-optional) section for the full list.

**No limits on:**

| Item | Notes |
|------|-------|
| **File size** | peekdocs processes whatever the underlying libraries (PyMuPDF, openpyxl, python-docx, etc.) can handle. There is no hardcoded maximum. Very large files (multi-GB PDFs, spreadsheets with millions of rows) may cause high memory usage — use `-c 1` to reduce memory consumption |
| **Number of files** | No maximum. The only constraint is the operating system's file descriptor limit, which defaults to 256 on macOS and 1024 on Linux. Increase with `ulimit -n 4096` if needed. See [FAQ & Troubleshooting](TROUBLESHOOTING.md) for details |
| **PDF page count** | PDFs are processed page by page with no page count limit |
| **Excel rows and sheets** | No maximum. openpyxl processes worksheets in read-only mode for memory efficiency |
| **Number of search terms** | No maximum — you can provide as many terms as needed |
| **Index database size** | No maximum. The index grows proportionally to the amount of text in your documents (typically 10–20% of original file sizes) |
| **Number of saved searches** | No maximum per folder |

**System-dependent constraints:**

| Constraint | What happens | How to fix |
|------------|-------------|------------|
| **Memory** | Very large files, or many files searched in parallel across multiple cores, can exhaust available RAM. peekdocs catches `MemoryError` and suggests reducing cores or limiting file types | Use `-c 1` to search single-threaded, or `-t` to limit file types |
| **Open files limit** | Searching thousands of files may exceed the OS file descriptor limit, causing "Too many open files" errors | Run `ulimit -n 4096` before searching. See [FAQ & Troubleshooting](TROUBLESHOOTING.md) |
| **Disk space** | peekdocs checks available disk space before writing reports. If free space is below 10 MB, it warns and skips report generation | Free disk space, or use `--output-dir` to write reports to a different drive |
| **Path length (Windows)** | Windows has a default 260-character path limit. Deeply nested folders with long filenames may cause files to be silently skipped | Enable long paths in Windows. See [FAQ & Troubleshooting](TROUBLESHOOTING.md) |
| **SQLite lock timeout** | If another process holds the index database lock, peekdocs waits up to 10 seconds before falling back to direct file scanning | Close other peekdocs instances, or delete stale lock files. See [FAQ & Troubleshooting](TROUBLESHOOTING.md) |

## Platform Notes

peekdocs runs on Windows, macOS, and Linux with the same features in all three. A handful of day-to-day operations vary by operating system — this section collects them in one place. For install-related platform details, see [Dependencies](#dependencies) and [Getting Started with the Terminal](#getting-started-with-the-terminal). For lower-level file-handling differences (lock files, symlinks, virtual filesystems, etc.), see the **Platform Notes** section in the README.

### Showing hidden files

peekdocs uses dot-files (`.peekdocs_collection.json`, `~/.peekdocsrc`, etc.) that are hidden by default.

- **macOS:** In Finder, press **Cmd+Shift+.** (period) to toggle hidden files.
- **Windows:** In File Explorer, click the **View** tab and check **Show hidden items**.
- **Linux:** In your file manager, press **Ctrl+H**, or use `ls -a` in the terminal.

### Locking the screen

peekdocs stores results in plain files on disk, so lock the screen when stepping away.

- **Windows:** Win+L
- **macOS:** Ctrl+Cmd+Q
- **Linux:** Super+L

### Network folder paths

Map or mount the share so it appears as a regular folder, then point peekdocs at it. Build an index on the first search to avoid re-reading files over the network on every run.

- **Windows:** mapped drive (e.g., `Z:\`)
- **macOS:** `/Volumes/ShareName`
- **Linux:** NFS or SMB mount point

### Activating the virtual environment

Required only for the manual-install (Option B) workflow. pipx users (Option A) can skip this — peekdocs is always on `PATH`.

- **macOS/Linux:** `source venv/bin/activate`
- **Windows:** `venv\Scripts\activate`

You'll see `(venv)` appear in your prompt when activation succeeds.

### File picker differences

When you click **File** in the Folder Bar:

- **macOS:** The picker includes a preview panel on the right.
- **Windows:** The picker does not include a preview.

This is an OS-level difference, not a peekdocs choice.

### Opening reports without Microsoft Word

The `.docx` report opens with whatever word processor is installed on your computer. [LibreOffice](https://www.libreoffice.org/download/download-libreoffice/) (free) is recommended on all three platforms. The `.txt` report opens anywhere with no additional software. Enable HTML output in Advanced Search Options for a browser-based highlighted report. peekdocs avoids opening reports in Google Docs, Apple Pages, or any cloud-based app that may upload your data.

### Schedule Search command format

The Schedule Search dialog (Tools menu) generates the correct command format for your detected OS:

- **macOS/Linux:** crontab entry (paste into `crontab -e`)
- **Windows:** `schtasks` command (paste into Command Prompt or Task Scheduler)

### Batch loops over collections and suites

- **macOS/Linux:** bash `for ... do ... done` loops. See [Regex Collection Use Cases](#regex-collection-use-cases) and [Search Suite Use Cases](#search-suite-use-cases).
- **Windows:** PowerShell `foreach (...) { ... }` loops. Same sections include PowerShell variants.
- **Any OS:** the Python API works identically. Use `list_regex_collections()` / `list_suites()` to enumerate, then `run_regex_collection()` / `run_suite()` to execute.

## Multilingual Support

peekdocs searches documents written in any language — English, Chinese, Japanese, Korean, Arabic, Hindi, Russian, Greek, Spanish, German, French, Portuguese, Thai, Hebrew, and every other language that can be represented in Unicode. Type your search terms in any language and peekdocs finds the exact character sequence in your files.

This is not a special feature unique to peekdocs. All modern search tools are built on Unicode, the universal standard for representing text in every writing system. peekdocs uses Python's built-in Unicode string handling, which means it has the same multilingual capabilities — and the same limitations — as any other Unicode-based tool.

### What works

- **Exact text matching in any language.** If your document contains `预算报告` and you search for `预算`, peekdocs finds it. This works for every script: Latin, Chinese, Japanese, Korean, Arabic, Hebrew, Cyrillic, Devanagari, Thai, Greek, and all others.
- **Regex in any language.** You can write regex patterns that match characters in any script. For example, `[A-Z]{2}\d{6}[A-Z]` matches a UK National Insurance Number, and `[\u4e00-\u9fff]+` matches Chinese characters.
- **Mixed-language documents.** A single file can contain text in multiple languages. peekdocs searches all of it — the same search can find English keywords in one file and Chinese keywords in another.
- **All 100+ file types.** Multilingual support applies to every format peekdocs reads — .docx, .pdf, .xlsx, .eml, .txt, and all the rest. If the file's text extraction produces Unicode (which it does for all modern file formats), peekdocs can search it.
- **Regex Search custom patterns.** The Regex Search lets you add regex patterns for international ID formats (UK NINO, Canadian SIN, Indian PAN, German Steuer-ID, Brazilian CPF, and more).

### What doesn't work (limitations)

- **No word segmentation for CJK languages.** Chinese, Japanese, and Korean do not use spaces between words. peekdocs searches for exact character sequences, which works well for most searches, but features that depend on word boundaries (like whole-word matching with `-W`) may not behave as expected for CJK text.
- **No stemming or lemmatization.** peekdocs does not reduce words to their root form. In English, searching for "running" will not automatically find "run" or "ran." The same applies to all other languages. Fuzzy matching (`-z`) can help find some variations, but it is not a substitute for proper stemming.
- **No stop-word removal.** peekdocs does not filter out common words like "the," "and," or "of" (or their equivalents in other languages). Every term you type is searched for literally.
- **No language detection.** peekdocs does not detect which language a document is written in. It treats all text as a sequence of Unicode characters regardless of language.
- **No right-to-left layout in the GUI.** Arabic and Hebrew text is searchable and appears correctly in reports (Word handles bidirectional text natively), but the GUI's text widgets may not render right-to-left text perfectly on all platforms.
- **No transliteration or translation.** Searching for "budget" will not find the Chinese word for budget (预算). You must search for the exact characters that appear in the document.
- **PDF reports limited to Latin-1 characters.** The PDF output format uses a built-in font (Helvetica) that can only render Western European characters. Non-Latin scripts (Chinese, Japanese, Korean, Russian, Arabic, Greek, Hindi, Thai, etc.) will appear as `?` in PDF reports. This does not affect searching — all languages are found correctly. It only affects the PDF report. Use `.docx`, `.html`, or `.txt` output for non-Latin content.

### Documentation and GUI language

The peekdocs GUI, help screens, documentation, and reports are all in **English only**. There are no translations of the interface into other languages. This is a practical limitation of being a solo-developer project — maintaining translations across every update is not feasible. The GUI labels are short and largely self-explanatory (Browse, Run Search, Save, Reload), so most non-English speakers can navigate the interface without difficulty.

### Sample multilingual files

The `samples/multilingual/` folder in the repository contains test documents in Chinese, Greek, Spanish, Arabic, and a 14-language text file. You can point peekdocs at this folder to verify multilingual search on your system:

```bash
cd samples/multilingual
peekdocs 预算                    # Chinese: "budget"
peekdocs προϋπολογισμού         # Greek: "budget"
peekdocs الميزانية               # Arabic: "budget"
peekdocs factura                # Spanish: "invoice"
```

### The automated language test

To verify multilingual support across all 14 tested languages at once:

```bash
source venv/bin/activate
python tests/language_test.py
```

This creates temporary test files, runs peekdocs against each language, prints a summary table, and cleans up after itself.

## Your First Advanced Search — Step by Step

You know how to do a basic search — type a word, click Run Search, see results. This section walks you through the most useful advanced features one at a time. Each example is a complete walkthrough: what to type, what to check, and what you'll see.

All of these use the GUI. Open `peekdocs-gui`, click **Browse** to select a folder with some documents, and follow along.

### Example 1: Find an invoice-ID pattern with regex

**Goal:** Find any document containing an invoice ID (format: `INV-12345`).

1. Open **Advanced Search Options** and check the **Regex** checkbox
2. In the **Search Terms** field, type: `\bINV-\d+\b`
   - This is a regex pattern: `\b` means "word boundary", `INV-` matches that exact text, and `\d+` means "one or more digits"
   - You don't need to memorize regex — click the **Wizard** button next to the search box for a list of pre-built patterns you can insert with one click
3. Click **Run Search**
4. Look at the results preview:
   - Each match shows the filename, line number, and the actual invoice ID found, highlighted in yellow
   - If no matches appear, your documents don't contain text in that format
5. Open **Advanced Search Options** and uncheck **Regex** when you're done

**Tip:** The Wizard button has patterns for phone numbers, email addresses, dates, dollar amounts, ZIP codes, and more. You don't need to know regex to use them.

### Example 2: Find misspelled words with fuzzy matching

**Goal:** Find documents containing "accommodation" even if it's misspelled (common in scanned/OCR documents).

1. Open **Advanced Search Options** and check the **Fuzzy** checkbox
2. In the **Search Terms** field, type: `accommodation`
3. Click **Run Search**
4. Look at the results preview:
   - You'll see matches for "accommodation" (exact) but also "accomodation", "accomadation", "acco mmodation" (OCR errors), and other approximate matches
   - Fuzzy matching uses a similarity score — words that are at least 80% similar to your search term are considered matches
5. Uncheck **Fuzzy** when you're done

**When to use this:** Searching documents that were scanned (OCR introduces errors), documents written by non-native English speakers, or any collection where spelling is inconsistent.

### Example 3: Find dollar amounts in a specific range

**Goal:** Find documents mentioning dollar amounts between $10,000 and $50,000.

1. In the **Search Terms** field, type: `payment` (or any related keyword, or leave it empty for a range-only search)
2. Open **Advanced Search Options** and find the **Range** field
3. In the Range field, type: `amount:10000..50000`
   - This tells peekdocs: "only show matches where a dollar amount between 10,000 and 50,000 appears on the same line"
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
2. Open **Advanced Search Options** and check the **Inverse** checkbox
   - Normal search finds files WITH your terms. Inverse flips it — it finds files WITHOUT your terms
3. Click **Run Search**
4. Look at the results preview:
   - Instead of showing matches, it lists every file that does NOT contain "Authorized Signature"
   - These are the files that need attention
   - If the list is empty (0 matches), every file contains the required text
5. Uncheck **Inverse** when you're done

**Why this matters:** This is a useful pattern when you want to verify that every file contains something you expect. The report lists exactly which files are missing it.

### Example 5: Find words near each other with proximity search

**Goal:** Find documents where "breach" and "contract" appear within 5 words of each other (not just anywhere in the same file).

1. In the **Search Terms** field, type: `breach contract`
2. Open **Advanced Search Options** and find the **Proximity** field
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
2. Open **Advanced Search Options** and find the **File types** field
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

**Goal:** Find invoice IDs in PDF files across all subfolders, showing 2 lines of context before and after each match.

1. In the **Search Terms** field, type: `\bINV-\d+\b`
2. Open **Advanced Search Options** and set:
   - Check **Regex**
   - Check **Recursive** (searches subfolders)
   - **File types:** `pdf`
   - **Lines Before:** `2`
   - **Lines After:** `2`
3. Click **Run Search**
4. The results show each invoice-ID match with 2 lines above and below for context, from PDF files only, across all subfolders

**You can mix and match almost any combination of features.** The main restrictions:
- Regex and Fuzzy can't be used together
- Regex and Wildcard can't be used together
- Fuzzy and Wildcard can't be used together
- Expression mode replaces AND mode, Exclude, and Proximity (use AND/OR/NOT in the expression instead)

### What's next?

Now that you're comfortable with individual advanced searches, you can:
- **Save searches for reuse** — click **Save Search** to name and store any search you've configured

---

## Python API Reference

peekdocs includes a Python API that lets you call the search engine directly from your own scripts. Every search workflow available in the CLI and GUI is also available in the API:

| Function | What it does |
|---|---|
| `search()` | Run a single search with any combination of modes (regex, fuzzy, Boolean, etc.) |
| `run_suite(name)` | Run a saved search suite by name — executes each saved search with its original settings |
| `run_regex_collection(name)` | Run a saved regex collection by name — executes each enabled pattern separately |
| `list_suites(directory)` | List all saved search suites in a folder |
| `list_regex_collections()` | List all saved regex collections |

For full documentation, parameters, return types, and examples, see the [peekdocs Library API Reference](API.md).

A complete working example is available at [`samples/api_example.py`](../samples/api_example.py).

**Important:** All scripts that use the peekdocs API must include the `if __name__ == "__main__":` guard because peekdocs uses multiprocessing. Without it, macOS and Windows will crash with a `RuntimeError`. See the API Reference for details.

**Field naming note.** `SearchMatch.line_num` is the field on the Python dataclass. The JSON output (`--stdout`, `-o json`) and CSV output (`-o csv`) name the same field `line_number`. See the [JSON output schema](#json-output---stdout-schema) section for the full output field list.

## Running Tests

Running tests requires the cloned repository (see [Option B](../README.md#option-b-manual-install-with-git) in the README). From the project folder:

```bash
source venv/bin/activate
pytest tests/ -v
```

## Project Structure

The peekdocs codebase is organized as follows. The package itself lives in `peekdocs/`; tests, docs, and sample files live alongside it.

```
peekdocs/
├── peekdocs/
│   ├── __init__.py      # Package init, re-exports library API
│   ├── __main__.py      # Enables python -m peekdocs
│   ├── api.py           # Public library API (search(), run_suite(), run_regex_collection(), list functions)
│   ├── cli.py           # CLI entry point (calls api.search internally)
│   ├── collection.py    # Saved search collections
│   ├── constants.py     # Shared constants and defaults
│   ├── expr_parser.py   # Boolean expression parser (AND/OR/NOT)
│   ├── gui/             # Optional GUI package (peekdocs-gui)
│   │   ├── _app.py      #   Main app class
│   │   ├── _helpers.py   #   Free functions (no GUI dependency)
│   │   ├── _tooltip.py   #   Tooltip widget
│   │   ├── _mixin_build.py  #   UI construction
│   │   ├── _mixin_search.py #   Search execution
│   │   ├── _mixin_tools.py  #   Tools, regex search, wizard, help
│   │   └── _mixin_data.py   #   Settings, history, bookmarks, index
│   ├── indexer.py       # Optional SQLite FTS5 search index
│   ├── parser.py        # Command-line flag parsing
│   ├── reporter.py      # Report generation (txt, docx, csv, json, pdf, html)
│   ├── scanner.py       # File processing and discovery
│   ├── translator.py    # Plain-English translation of commands and regex
│   └── wizard_patterns.py # Regex Wizard pattern presets
├── tests/
│   ├── test_api.py        # Library API test suite
│   ├── test_cli.py        # CLI test suite
│   ├── test_expr_parser.py # Boolean expression parser tests
│   ├── test_collection.py # Saved search collection tests
│   ├── test_gui.py        # GUI test suite
│   ├── test_translator.py # Translator test suite
│   └── test_wizard.py     # Wizard patterns test suite
├── pyproject.toml       # Project metadata and dependencies
├── requirements.txt     # Pip requirements
└── README.md
```

## Glossary

| Term | What it means |
|------|--------------|
| **AND mode** | A search setting where all terms must appear on the same line to count as a match. Without AND mode, any single term matching counts |
| **API** | Application Programming Interface — a way for programs to use peekdocs from Python code. Example: `from peekdocs import search, run_suite, run_regex_collection` |
| **Boolean expression** | A search using AND, OR, and NOT to combine terms. Example: `(budget OR revenue) AND NOT draft` |
| **Catastrophic backtracking** | A regex performance trap where certain pattern shapes (typically nested quantifiers like `(a+)+` or `(.*)*` on the same input) make the engine try exponentially many ways to match, freezing on large inputs. peekdocs validates regex syntax but does not cap pattern complexity — a pathological pattern from the search bar can hang the run until killed. Common avoidance: use atomic groups, possessive quantifiers, or simpler patterns |
| **CI pipeline** | Continuous Integration pipeline — an automated workflow (GitHub Actions, GitLab CI, Jenkins, CircleCI, etc.) that runs tests or checks on every code change. peekdocs fits in via its CLI: `--stdout` JSON, exit codes (0 = matches, 1 = none), and `--regex-collection` for batch pattern scans. Example: a nightly job that scans every repo for TODO/FIXME comments or deprecated APIs |
| **CLI** | Command-Line Interface — the terminal version of peekdocs. You type commands like `peekdocs budget -r` instead of clicking buttons |
| **Collection** | The file (`.peekdocs_collection.json`) in each folder that stores your saved searches and search suites for that folder |
| **Command Prompt** | The Windows terminal application where you type commands. On macOS it's called Terminal |
| **Context lines** | Extra lines shown before and/or after each match to give you surrounding context — helpful for understanding what the match is part of |
| **cron** | A built-in Unix/Linux/macOS scheduler for running commands on a schedule. Windows equivalent: **Task Scheduler** (`schtasks`). peekdocs's CLI flags compose into cron / Task Scheduler jobs for unattended scans. See Tools → Schedule Search in the GUI for an OS-correct command generator |
| **Diff** | Comparison of two files or datasets — term from the Unix `diff` command. peekdocs's `--diff peekdocs_snapshot_old.json peekdocs_snapshot_new.json` reports what's new, removed, changed, or modified between two scan snapshots — the scheduled-scan "what's new since last week?" question. See [Diff between runs](#diff-between-runs) |
| **Direct search** | Searching by reading each file on the fly, without using a pre-built index. Slower for repeated searches but always up-to-date |
| **Expression mode** | A search mode that lets you type Boolean expressions like `(budget OR revenue) AND NOT draft` directly in the search bar |
| **Exit codes** | The number a command-line program returns when it finishes. Convention: **0** = success, non-zero = error. peekdocs uses **0** (matches found), **1** (no matches), **2** (error). The `--diff` command uses diff-style codes: 0 = no actionable change, 1 = new findings detected, 2 = error. See [Exit codes](#exit-codes) |
| **File descriptor** | The handle the operating system gives a program for each open file. Every OS limits how many a single process can hold open at once: macOS defaults to 256, Linux to 1024. Searching thousands of files in parallel can exceed this, producing "Too many open files" errors. Fix: `ulimit -n 4096` before running, or raise the limit system-wide |
| **Flag** | A command-line option that modifies how a search works. Example: `-r` for recursive, `-a` for AND mode. In the GUI, each flag has a corresponding checkbox |
| **FTS5** | Full-Text Search 5 — a fast search technology built into SQLite that peekdocs uses for its search index |
| **Fuzzy matching** | Finding approximate matches — catches typos like "budgt" when searching for "budget" |
| **grep** | A classic Unix command-line tool for searching text in files. Very fast for plain text, but can't read Word, PDF, Excel, or email files |
| **GUI** | Graphical User Interface — the point-and-click window version of peekdocs (launched with `peekdocs-gui`) |
| **Hash (SHA-256)** | A fixed-length fingerprint (64 hexadecimal characters) computed from a file's raw bytes — any change to the file produces a completely different hash. peekdocs's `--hash` flag adds a `sha256` field to JSON output (`--stdout` or `-o json`) so a reviewer can verify later that "this is the exact file I found" — file-identity and integrity verification. Same algorithm used by Git, Bitcoin, and most modern security tools |
| **Headless** | A computer with no display, keyboard, or mouse — typically a server, virtual machine, or container running unattended. peekdocs's CLI runs headlessly without the GUI dependency installed; `peekdocs --check` reports the GUI as missing and still exits 0 because the CLI is fully usable. See [Headless and server deployments](#headless-and-server-deployments) |
| **Homebrew** | A popular package manager for macOS. Used to install Python, pipx, and other tools. Website: [brew.sh](https://brew.sh) |
| **Index** | A pre-built database of your files' contents that makes repeated searches much faster. Like a book's index — instead of reading every page, you look up the word and go straight to the right page |
| **ImportError** | A Python exception raised when an `import` statement fails — usually because the named module isn't installed. peekdocs's CLI avoids this by lazy-loading the GUI dependency (`customtkinter`) inside the GUI mixins, so the CLI runs cleanly on machines where Tk isn't installed. The `peekdocs-gui` entry point raises a clear ImportError on first invocation if Tk is missing — by design, so a missing GUI dep fails early instead of silently |
| **Inverse search** | Finding files that do *not* contain a term — the opposite of a normal search |
| **jq** | Command-line JSON processor — grep/awk/sed for JSON. Useful for filtering peekdocs's `--stdout`, `-o json`, and `~/.peekdocs_runs.log` outputs. Install via `brew install jq` or your distro's package manager |
| **JSON Lines (JSONL / NDJSON)** | Streaming text format: one self-contained JSON object per line. Universal in log shipping (Filebeat, Splunk, Elastic) because malformed lines don't break later ones. peekdocs's `~/.peekdocs_runs.log` uses it; so does `--runs --json` |
| **MIT License** | A permissive open-source license that lets anyone use, copy, modify, and share the software for free, with no restrictions |
| **ModuleNotFoundError** | A specific Python `ImportError` raised when an `import` statement names a module that isn't installed in the active Python interpreter. peekdocs users hit this most often when (a) pip installed into a different Python than the one running `peekdocs`, (b) the virtual environment isn't activated, or (c) the package wasn't installed at all. Quick check: `python -m peekdocs --check` should show the same Python you `pip install`-ed into. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| **MSP technician** | Managed Service Provider technician — an IT professional employed by an outside firm that manages computers, networks, and software for client businesses on contract. One MSP typically serves dozens of small clients who do not have their own in-house IT staff |
| **multiprocessing** | Python's standard library for running work in parallel processes (not threads — to sidestep the GIL). peekdocs uses it to scan many files at once. Side effect: scripts that import the peekdocs API must wrap their main code in `if __name__ == "__main__":` because on macOS and Windows, child processes re-import the parent script — without the guard, this re-imports and re-spawns infinitely, crashing with `RuntimeError`. See the API Reference for details |
| **OCR** | Optical Character Recognition — technology that reads text from images and scanned PDFs. Requires Tesseract (optional) |
| **PATH** | A system setting that tells your computer where to find programs. If a command says "not recognized," the program probably isn't in your PATH |
| **pip** | Python's built-in package installer. Comes with Python automatically. Used to install Python programs and libraries |
| **Piping** | Connecting one command's output to another command's input with the `\|` character on macOS, Linux, and Windows terminals. Example: `peekdocs --stdout TODO \| jq '.matches_found'` runs the search, then pipes the JSON output into `jq`. peekdocs's `--stdout` and `--runs --json` flags exist specifically to compose into pipes |
| **pipx** | A tool that installs Python programs (like peekdocs) in isolated environments so they don't interfere with anything else on your computer |
| **Proximity search** | Finding terms that appear near each other — within N words on the same line (word proximity) or within N lines of each other (line proximity) |
| **pyenv, conda, WSL** | Three common sources of multiple-Python confusion on a single machine. **pyenv** (Mac/Linux) installs and switches between multiple Python versions per project. **conda** (cross-platform, from the Anaconda distribution) is a Python package and environment manager popular in data-science workflows. **WSL** (Windows Subsystem for Linux) is a Linux environment running inside Windows — Python installed in WSL is a different Python than Python installed in regular Windows. When `pip install peekdocs` succeeds but `peekdocs` then fails with `ModuleNotFoundError`, the cause is usually pip and the `peekdocs` shell command pointing at different Pythons across these systems |
| **PyPI** | Python Package Index (pronounced "pie-pee-eye") — the official repository where Python packages are published. Like an app store for Python programs |
| **pyproject.toml** | The modern Python packaging configuration file (introduced in PEP 518, 2016; standardized in PEP 621, 2020). Replaces the older `setup.py` script. peekdocs uses it to declare its dependencies, version, console scripts, and build backend. Older pip versions (pre-2022) may not understand it — if you see "No setup.py, setup.cfg, or pyproject.toml" during install, run `pip install --upgrade pip setuptools wheel` first |
| **Python** | The programming language peekdocs is written in. Users need Python 3.10 or newer installed (unless using the standalone download) |
| **Range query** | Filtering matches by numeric or date ranges. Example: `amount:1000..5000` finds lines where an amount falls between 1,000 and 5,000 |
| **Recursive** | Searching not just the selected folder but all subfolders inside it, and their subfolders, and so on |
| **Regex** | Regular Expression — a pattern language for matching text. Example: `\d{3}-\d{2}-\d{4}` matches a 9-digit ID with dashes, like 123-45-6789 |
| **Search suite** | A named group of saved searches that run together with one click. Create them in the GUI (Tools → Search Suites) or run from the CLI with `--suite` |
| **setuptools** | The traditional Python build backend that turns source code into installable packages. Most Python projects (peekdocs included) use it under the hood. Updated regularly; older versions may not understand modern `pyproject.toml` files. The `pip install --upgrade pip setuptools wheel` incantation in install troubleshooting refreshes both pip and the build backend in one go |
| **SIEM** | Security Information and Event Management — tools (Splunk, Elastic Security, Datadog, Microsoft Sentinel) that aggregate logs for searching and alerting. peekdocs feeds them via JSON Lines and `--stdout` JSON — no plugin needed |
| **SQLite** | A lightweight database engine built into Python. peekdocs uses it for the search index — no separate database software needed |
| **SSD** | Solid State Drive — a fast storage drive with no moving parts. Searches are faster on SSDs than on older spinning hard drives |
| **stdin / stdout / stderr** | The three "standard streams" every command-line program has. **stdin** is its input, **stdout** is its normal output, **stderr** is its errors and warnings — kept on separate channels so you can pipe one without the other. `peekdocs --stdout` writes a JSON document to stdout (the normal output channel), keeping it clean for piping into other tools; warnings go to stderr where they don't pollute the JSON. Quiet mode (`-qq`) suppresses most stderr noise |
| **Stemming, stop-words, word segmentation, lemmatization** | Four concepts from linguistic search engines that peekdocs deliberately does *not* perform. **Stemming** reduces words to a root form ("running" → "run"). **Lemmatization** does the same using a dictionary of word forms (more accurate but slower). **Stop-word removal** ignores common words like "the", "and", "of" during indexing. **Word segmentation** breaks languages without spaces (Chinese, Japanese) into individual words. peekdocs does exact character-sequence matching across all languages instead — simpler, more predictable, and works equally well for English prose, Chinese text, code identifiers, account numbers, and product SKUs |
| **Tesseract** | Free OCR software that reads text from images. Optional — only needed if you want to search scanned documents or photos of text |
| **Unicode** | The standard that lets computers handle text in every language — English, Chinese, Arabic, emoji, and everything else. peekdocs uses Unicode throughout |
| **venv** | Virtual environment — an isolated copy of Python where peekdocs and its libraries are installed without affecting the rest of your system. You'll see `(venv)` in your terminal prompt when one is active |
| **WAL mode** | Write-Ahead Logging — a SQLite mode where changes are written to a separate log file first, then merged into the main database. Allows multiple readers and one writer to access the database simultaneously without blocking each other. peekdocs uses WAL mode for the search index so concurrent searches, auto-refresh, and external tools can all read the same `.peekdocs.db` without lock contention |
| **Wheel** (Python wheel) | Pre-built, ready-to-install Python package format (`.whl` file). Most Python libraries ship as wheels so `pip install` doesn't need a C compiler — it just downloads the matching wheel for your OS and Python version. A few peekdocs optional dependencies (notably `libpff-python` for `.pst` archives) have no Windows wheel, which means Windows users either need a working compiler toolchain or have to use the `.mbox` workaround documented in TROUBLESHOOTING.md |
| **Whole-word matching** | Only matching complete words — searching for "cat" won't match "catalog" or "concatenate" |
| **Webhook** | A user-defined HTTP callback — your service POSTs JSON to a URL. Common in Slack, GitHub, alerting systems (PagerDuty, Opsgenie). peekdocs's `--on-match` hook can `curl` a webhook URL to fire chat / paging / ticketing notifications |
| **Wildcard** | A search pattern where `*` matches any characters and `?` matches one character. Example: `budg*` matches "budget," "budgeting," "budgetary" |
