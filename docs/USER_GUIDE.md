# peekdocs User Guide

This is the complete reference guide for peekdocs. For a quick overview, see the [README](../README.md).

## Table of Contents

- [Will peekdocs affect my existing Python installation?](#will-peekdocs-affect-my-existing-python-installation)
- [Security Best Practices](#security-best-practices)
- [Getting Started with the Terminal](#getting-started-with-the-terminal)
- [GUI Mode (Graphical User Interface)](#gui-mode-graphical-user-interface)
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
- [PII Scan](#pii-scan)
- [Boolean Expression Search](#boolean-expression-search)
- [Range Queries](#range-queries)
- [Combining Modes](#combining-modes)
- [Breaking Down Complex Searches](#breaking-down-complex-searches)
- [Saved Settings (Optional)](#saved-settings-optional)
- [Files Created by peekdocs](#files-created-by-peekdocs)
- [Limits and Constraints](#limits-and-constraints)
- [Multilingual Support](#multilingual-support)
- [Your First Advanced Search — Step by Step](#your-first-advanced-search--step-by-step)
- [Running Tests](#running-tests)
- [Project Structure](#project-structure)

## Will peekdocs affect my existing Python installation?

No. Both installation methods keep peekdocs completely isolated from your existing Python setup, your other Python programs, and your system.

**With pipx** (`pipx install peekdocs`): pipx creates a private workspace for peekdocs behind the scenes. Your system Python, any other Python programs, and any other virtual environments are completely untouched. peekdocs's dependencies (the libraries it needs, like PyMuPDF, openpyxl, etc.) are installed only inside that private workspace. You won't even see them if you run `pip list` from your normal Python. The only thing that changes system-wide is that two new commands (`peekdocs` and `peekdocs-gui`) are added to your PATH so you can type them in any terminal.

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
| Search reports | `peekdocs_results.*` (each search folder) | Yes |
| Saved reports and PII scan reports | `DO_NOT_SEARCH_*` (each search folder) | Yes |
| Error log | `peekdocs_errors.log` (each search folder) | Yes |

**How to upgrade:**

- **pipx:** `pipx upgrade peekdocs` — replaces the code, preserves all your data
- **Manual install:** download the new ZIP, replace the `peekdocs-main` folder, run `pip install -e .` — your data is untouched

No migration, no export/import, no reconfiguration. Everything just works with the new version.

**Backing up your work — only two files matter:** `~/.peekdocsrc` (your settings) and `.peekdocs_collection.json` (your saved searches, one per folder). Everything else peekdocs creates can be regenerated. Copy these to a safe location before major changes. See [Files Created by peekdocs](#files-created-by-peekdocs) for the complete list of all files and what each one does.

**How to see hidden files:** These files start with a dot, which makes them hidden by default.
- **macOS:** In Finder, press **Cmd+Shift+.** (period) to toggle hidden files
- **Windows:** In File Explorer, click the **View** tab and check **Show hidden items**
- **Linux:** In your file manager, press **Ctrl+H** or use `ls -a` in the terminal

**If you want to uninstall completely:**

- **pipx:** `pipx uninstall peekdocs` — removes the peekdocs code and its private workspace. Your settings (`~/.peekdocsrc`), saved searches, indexes, and reports in your document folders are not deleted — remove those manually if you want a clean slate.
- **Manual install:** delete the `peekdocs-main` folder you downloaded. Your settings and data in document folders remain.

---

## Security Best Practices

peekdocs runs entirely on your computer — your documents are never uploaded, transmitted, or shared. But because peekdocs works with sensitive documents (financial records, legal files, medical records, PII), here are some practices to keep your data safe:

- **Lock your screen when stepping away.** peekdocs stores search results in plain files on your computer. Anyone with access to your screen can see the results preview, and anyone with access to your folder can open the report files. Lock your screen with **Win+L** (Windows), **Ctrl+Cmd+Q** (macOS), or **Super+L** (Linux). This protects everything — not just peekdocs, but email, browser, and all open files.
- **Be careful with report files.** The `peekdocs_results.docx`, `.txt`, and `DO_NOT_SEARCH_pii_scan_report.docx` files contain matched text from your documents — including any sensitive content that matched your search. Don't leave them on shared drives or send them via unencrypted email. Use **Clear Results** on the bottom toolbar to delete them when you're done.
- **Don't store peekdocs results on shared drives.** If your search folder is on a shared network drive, the results files are written there too. Use `--output-dir` (or the Output Dir field in Advanced Search Options) to write results to a private local folder instead.
- **Review the error log.** `peekdocs_errors.log` may contain filenames that reveal what you were searching. Clear it with **Clear Error Log** when you're done.

---

## Getting Started with the Terminal

If you've never used a terminal before, this section walks you through everything from opening it to running your first search. If you're already comfortable with the command line, skip ahead to [GUI Mode](#gui-mode) or [Usage](#usage).

**Prefer not to use the terminal?** That's completely fine — run `peekdocs-gui` for a point-and-click interface instead. See [GUI Mode](#gui-mode).

### Which installation method did you use?

This matters for how you launch peekdocs:

- **If you installed with pipx** (`pipx install peekdocs`): you're all set. `peekdocs` and `peekdocs-gui` work from any terminal, any folder, every time. Just open a terminal and start searching. Skip to [Step 1: Open your terminal](#step-1-open-your-terminal).

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

  **Tired of activating every time?** Consider switching to pipx: `pip install pipx && pipx ensurepath && pipx install peekdocs`. After restarting your terminal, peekdocs works everywhere without activation.

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
  peekdocs_results.txt (5.67 KB), peekdocs_results.docx (42.31 KB)
```

That's it — you just searched 47 files in 1.2 seconds. Your results are saved in two files.

### Step 4: Open your results

The results are saved in the same folder where you ran the search. Open the Word report to see your matches highlighted in yellow:

**Windows:**
```cmd
start peekdocs_results.docx
```

**macOS:**
```bash
open peekdocs_results.docx
```

**Linux:**
```bash
xdg-open peekdocs_results.docx
```

Or simply navigate to the folder in your file manager and double-click `peekdocs_results.docx`.

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

**Search for a pattern (like Social Security numbers):**
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
| **Search Bar** | Search entry field with **▼** recent-searches dropdown (shows your last 10 searches), **Run Search** and **PII Scan** buttons, **Search Wizard** button, **Save Search** button (saves the current search to the folder's collection so you can reload it later), and **Load Search ▼** button (opens a popup to load or delete saved searches). During a search the status line shows the number of terms being searched (e.g., "Searching (3 terms)...") |
| **Folder Bar** | Folder path entry, **Browse** button (select a folder), and **Single File** button (select a single file to search — click the ✕ to clear the selection and revert to full folder search) |
| **Advanced Search Options** | Collapsible panel with all search options (click to expand) |
| **Manage Indexes** | Collapsible toggle — **Auto-Refresh Index** interval selector, **Build Index(es)**, **Delete Index(es)**, **Index Status**, and **?** help |
| **Results** | After a search: clickable **View N matched file(s)** button on the status line opens a popup listing each matching file with its match count and line numbers (e.g., "contract.docx (3 matches — lines 12, 47, 89)"). Double-click a file to open it in its default application, or click **View Text (with line numbers)** to see the extracted file content with line numbers and highlighted matches. A **View N excluded file(s)** button appears alongside, showing files that were NOT searched grouped by reason (unsupported type, prior output files, oversized, hidden, etc.) — useful when the file count differs from a manual `find` or `ls` count. **View Report:** label with **TXT**, **DOCX**, **CSV**, **JSON**, and **PDF** buttons to open reports in each format, and **View Error Log** if any files could not be read. In the Results Preview pane, right-click to copy the selected text (or the current line) to the clipboard, and double-click a filename to open it in your default application |
| **Toolbar** | **User Guide**, **App Files**, **All Collections** (global view of saved searches across all folders), **Error Log**, **Maintenance**, **Text Size**, **Disable Hover Text** (tooltips are on by default), and **About** buttons |

**Your first GUI search:**

1. Type what you're looking for in the **Search Bar**
2. Click **Browse** in the **Folder Bar** to pick the folder containing your documents (your home folder is selected by default), or click **File** to pick a single file
3. Click **Run Search** (or press Enter)

**macOS vs Windows file picker:** On macOS, clicking **File** opens a file picker with a preview panel on the right — you can inspect the file's contents before selecting it. On Windows, the file picker does not include a preview. This is a difference in the operating systems, not peekdocs.
4. When the search finishes, a result summary appears. Click **DOCX** next to **View Report:** to view your results in a `.docx` file with matches highlighted in yellow. You can also click **TXT**, **CSV**, **JSON**, or **PDF** to open the report in other formats. The PDF report also highlights matches in yellow. If any files could not be read, a **View Error Log** button also appears — click it to open `peekdocs_errors.log` and see which files had problems and why

**Don't have Microsoft Word?** The .docx report opens with whatever word processor is installed on your computer. If you have [LibreOffice](https://www.libreoffice.org/download/download-libreoffice/) (free) installed and it's set as your default for .docx files, Windows will open it automatically. You can also use [Google Docs](https://docs.google.com) (upload the file), Apple Pages (free, Mac only), or any other application that supports .docx files. The .txt report can be opened on any computer with no additional software.

**Sensitive Data Scan:**

Click the red **PII Scan** button to scan your documents for PII and sensitive data. A configuration popup appears with checkboxes for each category — all are enabled by default. Uncheck any categories you don't need, then click **Run Scan**. Use **Select All** / **Deselect All** for quick toggling. Your selections are saved to `~/.peekdocsrc` and remembered between sessions — the next time you open the popup, the same checkboxes will be checked. The scan checks for 8 categories of sensitive data:

| Category | Severity | What it finds |
|----------|----------|---------------|
| Social Security Numbers | HIGH | SSN patterns (XXX-XX-XXXX) |
| Credit Card Numbers | HIGH | Visa, Mastercard, Amex, Discover patterns |
| Tax ID / EIN | HIGH | Employer Identification Numbers (XX-XXXXXXX) |
| Email Addresses | MODERATE | Email address patterns |
| Phone Numbers | MODERATE | US phone number patterns |
| Passwords / Secrets | MODERATE | Lines containing password, secret, or API key assignments |
| Dates of Birth | MODERATE | Date-of-birth patterns near keywords like "DOB" or "born" |
| Dollar Amounts Over $10,000 | INFO | Dollar amounts $10,000 and above |

Results appear in a popup with color-coded severity badges (red for HIGH, yellow for MODERATE, blue for INFO). Categories with no findings show a green "Clean" label. Click **View Files** on any category to see which files are affected, with match counts and line numbers. Double-click a file to open it.

When findings are detected, a highlighted `.docx` report is automatically generated: `DO_NOT_SEARCH_pii_scan_report.docx`. The report is saved in the search folder by default, or in the **Output Dir** if set in Advanced Search Options. The report includes a summary table of all categories, then a detail section for each category with findings — every file is listed with its match count and line numbers, followed by the matched text with the sensitive data **highlighted in yellow**. Click **Open Report** in the results popup to view it. The report includes a disclaimer noting that pattern-based detection may produce false positives — review each finding to confirm it represents actual sensitive data.

The scan respects your current **Recursive** and **File Type** settings. It always scans files directly — the search index is not used because regex pattern matching requires scanning every line of text. The Use Index checkbox is temporarily unchecked during the scan and restored afterward.

Each popup (PII Scan and Search Wizard) has its own **Change Folder** button and operates independently — changing the folder inside a popup does not change the Search Folder on the main screen. The Search Wizard is the one exception: when you click **Apply**, the main screen folder is updated to match the wizard's folder, since the search runs from the main screen.

**Advanced Search Options:**

Click "Advanced Search Options" to expand a panel with additional settings — AND mode, recursive search, fuzzy matching, wildcards, OCR, regex, whole-word matching, expression mode, inverse search, exclude terms, file type filtering, proximity, context lines, CPU cores, max matches, range filters, specific files, save as, append to, output directory, additional output formats (CSV, JSON, PDF), and timestamp filenames. Every terminal flag is available in the GUI. You don't need any of them for a basic search. Hover over any option to see a description of what it does. At the bottom of the panel are four buttons: **Inspect .peekdocsrc** shows the current saved settings (read-only). **Save Defaults** saves your current search terms, folder, and all options as defaults to `~/.peekdocsrc` — the next time you open the GUI, everything will be pre-filled. **Restore Settings** reloads saved defaults from `~/.peekdocsrc` into the GUI. **Reset** clears all fields and restores the GUI to its default state — but it only affects the current session. Your saved defaults in `~/.peekdocsrc` are not changed unless you also click **Save Defaults** after resetting.

**Save Search vs Save Defaults — what's the difference?**

These two buttons do different things:

| Button | Location | What it saves | Where it's stored | Purpose |
|--------|----------|--------------|-------------------|---------|
| **Save Search** | Main screen | Current search terms + all settings, by name | `.peekdocs_collection.json` in the search folder | Reusable named search |
| **Save Defaults** | Advanced Search Options | Your preferred default settings | `~/.peekdocsrc` in your home directory | Starting configuration for every future session |

Your selections in Advanced Search Options take effect immediately on the next Run Search — you do not need to press Save Defaults first. Save Defaults is only for making your choices persist across sessions.

**Manage Indexes:**

Click "Manage Indexes" below Advanced Search Options to expand index controls. Use the **Auto-Refresh Index** dropdown to keep the index updated automatically. Click **Build Index(es)** to create the index (all subfolders are included automatically). Use **Delete Index(es)** to remove the index, **Index Status** to view index info, or **?** for help on how indexes work. The **Search Using Index(es)** checkbox is inside Advanced Search Options — check it to use the index for your next search, or uncheck it to search files directly.

Do not type flags (like `-a` or `-r`) into the **Search Bar** — it is only for search terms. Each checkbox and input field in **Advanced Search Options** handles the corresponding flag behind the scenes.

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
| `\d{3}-\d{2}-\d{4}` | SSN format | 123-45-6789 | a Social Security Number (SSN) |
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
| `-a` (all) | AND logic — all terms must appear in the same paragraph |
| `-c N` (cores) | Number of CPU cores for parallel search (default: half of available cores). For small numbers of files (fewer than 10), single-threaded mode is used automatically |
| `-e` (expression) | Boolean expression search — use AND, OR, NOT, parentheses, and range specs for complex queries. See [Boolean Expression Search](#boolean-expression-search) |
| `-f` (files) | Search specific files (comma-separated, e.g., `report.pdf,notes.txt`) |
| `-m N` (max-matches) | Maximum matches included in reports (default: 1,000). Use `0` for no limit |
| `-n` (not) | Exclude lines matching specified terms (comma-separated, e.g., `-n draft,obsolete`) |
| `-o` (output) | Additional output formats — `csv`, `json`, `pdf`, or any combination (`csv,json,pdf`). The `.txt` and `.docx` reports are always created; `-o` adds extra formats |
| `-O` (OCR) | Enable OCR for scanned PDFs and image files (requires [Tesseract](#prerequisites)) |
| `-p N` (proximity) | Proximity search — find terms within N words of each other |
| `-q` (quiet) | Quiet mode — suppress the banner |
| `-R SPEC` / `--range` | Range filter — filter by value ranges in content or file metadata. Repeatable. See [Range Queries](#range-queries) |
| `-r` (recursive) | Search subdirectories recursively |
| `-s` (save) | Archive results — copies peekdocs_results files to DO_NOT_SEARCH_your_file_name.docx (and .txt). The DO_NOT_SEARCH prefix is added automatically so archived files are never re-searched. Does not erase the original results files, but they are overwritten on the next search. Example: `peekdocs -s my_report` |
| `-sa` (save-append) | Search and auto-append — runs the search normally, then appends the results to DO_NOT_SEARCH_ACCUMULATED_your_file_name.txt (and .docx). Use this to accumulate results from multiple searches into one file. The DO_NOT_SEARCH_ACCUMULATED prefix is added automatically.<br><br>Example: `peekdocs -sa my_report budget revenue` results in your search for the terms budget and revenue being saved in file DO_NOT_SEARCH_ACCUMULATED_my_report.docx (and .txt). |
| `-t` (types) | Filter by file type (comma-separated, e.g., `pdf,docx`) |
| `--timestamp` (timestamp) | Add a timestamp suffix to report filenames (e.g., `peekdocs_results_20260327_143022.txt`). Each search produces uniquely named files so previous results are preserved |
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
- `-o` supported formats are `csv`, `json`, and `pdf`
- `-o` does not replace the default `.txt` and `.docx` reports — it adds additional output files
- `-o csv` creates `peekdocs_results.csv` with columns: filename, folder, line_number, matched_text
- `-o json` creates `peekdocs_results.json` with metadata and a matches array
- `-o csv,json` creates both files; `-o csv,json,pdf` creates all three
- `-m` always needs its count immediately after it (e.g., `-m 5000`)
- `-m 0` disables the match cap entirely — all matches are included in reports
- `-m` defaults to 1,000 when not specified. This prevents very large result sets from causing slow report generation
- `-m` can be set permanently via `--config max_matches=5000` or in the GUI's Advanced Search Options panel
- `--timestamp` adds a `_YYYYMMDD_HHMMSS` suffix to report filenames so each search produces unique files (e.g., `peekdocs_results_20260327_143022.txt`)
- `--timestamp` is off by default in the GUI. Check the Timestamp checkbox in Advanced Search Options to enable it — each search then produces uniquely named files instead of overwriting the previous results
- `--timestamp` and `-s` are independent — `-s` looks for `peekdocs_results.txt` by name, so it only works when `--timestamp` is not used
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
| | **Recursive (Subdirectory) Searches** | |
| 20 | Search all subdirectories | `peekdocs -r budget` |
| 21 | Recursive with AND logic | `peekdocs -r -a budget revenue expenses` |
| 22 | Recursive with file type filter | `peekdocs -r -t pdf,docx budget` |
| 23 | Recursive, AND, and file type filter | `peekdocs -r -a -t txt budget revenue expenses` |
| | **Regex Pattern Searches** | |
| 24 | Search for phone numbers | `peekdocs -x "\d{3}-\d{3}-\d{4}"` |
| 25 | Search for email addresses | `peekdocs -x "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,}"` |
| 26 | Regex with AND logic | `peekdocs -x -a "\d{3}" "\$\d+\.\d{2}"` |
| 27 | Regex with file type filter | `peekdocs -x -t pdf,docx "\$\d+(\.\d{2})?"` |
| 28 | Regex recursive | `peekdocs -x -r "\d{3}-\d{3}-\d{4}"` |
| 29 | Regex, recursive, file type filter | `peekdocs -x -r -t txt,csv "\b2026-\d{2}-\d{2}\b"` |
| 30 | Regex, AND, recursive, file type filter | `peekdocs -x -a -r -t pdf "\d{3}" "\$\d+"` |
| | **Context Lines (Before/After)** | |
| 31 | Show 5 lines after each match | `peekdocs -A 5 "John Smith"` |
| 32 | Show 3 lines before each match | `peekdocs -B 3 budget` |
| 33 | Show lines before and after | `peekdocs -B 2 -A 2 budget` |
| 34 | Context lines with AND logic | `peekdocs -B 3 -A 3 -a budget revenue` |
| 35 | Context with file type filter | `peekdocs -A 5 -t docx,pdf budget` |
| 36 | Context with recursive search | `peekdocs -B 3 -A 3 -r budget` |
| 37 | Context with regex | `peekdocs -B 2 -A 2 -x "\d{3}-\d{3}-\d{4}"` |
| 38 | Context, recursive, file type filter | `peekdocs -B 5 -A 5 -r -t docx "John Smith"` |
| 39 | Context, AND, recursive, file type filter | `peekdocs -B 3 -A 3 -a -r -t txt budget revenue` |
| | **Parallel Processing** | |
| 40 | Use 4 cores for search | `peekdocs -c 4 budget` |
| 41 | Parallel with recursive search | `peekdocs -c 4 -r budget` |
| 42 | Parallel with file type filter | `peekdocs -c 4 -t pdf,docx budget` |
| | **Save, Version, and Help** | |
| 43 | Save results to a named file | `peekdocs -s name_of_your_file` |
| | **Save and Append Searches** | |
| 44 | Search and append results to a file | `peekdocs -sa my_report budget` |
| 45 | Append with AND search | `peekdocs -sa my_report -a budget revenue` |
| 46 | Append with recursive search | `peekdocs -sa my_report -r budget` |
| 47 | Append with file type filter | `peekdocs -sa my_report -t pdf budget` |
| | **Quiet Mode** | |
| 48 | Suppress banner | `peekdocs -q budget` |
| 49 | Quiet with recursive search | `peekdocs -q -r budget` |
| | **OCR Searches** | |
| 50 | Search scanned PDFs and images | `peekdocs -O budget` |
| 51 | OCR with file type filter | `peekdocs -O -t pdf budget` |
| 52 | Search only image files | `peekdocs -O -t jpg,png budget` |
| 53 | OCR with recursive search | `peekdocs -O -r budget` |
| 54 | OCR with AND logic | `peekdocs -O -a budget revenue` |
| 55 | OCR with context lines | `peekdocs -O -B 3 -A 3 budget` |
| | **Fuzzy Searches** | |
| 56 | Fuzzy single term | `peekdocs -z budget` |
| 57 | Fuzzy with AND logic | `peekdocs -z -a budget revenue` |
| 58 | Fuzzy with file type filter | `peekdocs -z -t pdf,docx budget` |
| 59 | Fuzzy with recursive search | `peekdocs -z -r budget` |
| 60 | Fuzzy with proximity | `peekdocs -z -p 5 budget revenue` |
| 61 | Fuzzy with OCR | `peekdocs -z -O budget` |
| 62 | Fuzzy with context lines | `peekdocs -z -B 3 -A 3 budget` |
| 63 | Fuzzy, AND, recursive, file type | `peekdocs -z -a -r -t pdf budget revenue` |
| | **Wildcard Searches** | |
| 64 | Wildcard single pattern | `peekdocs -w "budg*"` |
| 65 | Wildcard question mark | `peekdocs -w "te?t"` |
| 66 | Wildcard with AND logic | `peekdocs -w -a "budg*" "rev*"` |
| 67 | Wildcard with file type filter | `peekdocs -w -t pdf,docx "budg*"` |
| 68 | Wildcard with recursive search | `peekdocs -w -r "budg*"` |
| 69 | Wildcard with context lines | `peekdocs -w -B 3 -A 3 "budg*"` |
| | **Whole-Word Searches** | |
| 70 | Whole-word single term | `peekdocs -W bob` |
| 71 | Whole-word with AND logic | `peekdocs -W -a bob amy` |
| 72 | Whole-word with expression | `peekdocs -W -e "bob AND amy"` |
| | **Exclude Searches** | |
| 73 | Exclude lines containing a term | `peekdocs -n draft budget` |
| 74 | Exclude multiple terms | `peekdocs -n draft,obsolete budget` |
| 75 | Exclude with AND logic | `peekdocs -n draft -a budget revenue` |
| 76 | Exclude with recursive search | `peekdocs -n draft -r budget` |
| 77 | Exclude with file type filter | `peekdocs -n draft -t pdf,docx budget` |
| 78 | Exclude with wildcard search | `peekdocs -w -n "dra*" "budg*"` |
| | **Additional Output Formats** | |
| 79 | Output results as CSV | `peekdocs -o csv budget` |
| 80 | Output results as JSON | `peekdocs -o json budget` |
| 81 | Output both CSV and JSON | `peekdocs -o csv,json budget` |
| 82 | CSV with recursive search | `peekdocs -o csv -r budget` |
| 82a | Output as PDF (highlighted) | `peekdocs -o pdf budget` |
| 82b | All extra formats at once | `peekdocs -o csv,json,pdf budget` |
| | **Match Cap** | |
| 83 | Set max matches to 5000 | `peekdocs -m 5000 budget` |
| 84 | Disable match cap (no limit) | `peekdocs -m 0 budget` |
| 85 | Match cap with AND and recursive | `peekdocs -m 500 -a -r budget revenue` |
| | **Saved Settings** | |
| 86 | View saved settings | `peekdocs --config` |
| 87 | Save a setting | `peekdocs --config recursive=true` |
| 88 | Save multiple settings | `peekdocs --config recursive=true cores=4` |
| 89 | Remove a saved setting | `peekdocs --config recursive=` |
| | **Search Index** | |
| 90 | Build index (includes all subfolders) | `peekdocs --index` |
| 91 | Build index with OCR | `peekdocs --index -O` |
| 92 | Show index info | `peekdocs --index-status` |
| 93 | Delete the index | `peekdocs --index-clear` |
| 93a | Incrementally refresh the index | `peekdocs --index-refresh` |
| 93b | Skip the index (direct scan) | `peekdocs --no-index budget` |
| | **Inverse Search** | |
| 94 | Find files missing a term | `peekdocs --inverse "indemnification"` |
| 95 | Files missing any of several terms | `peekdocs --inverse disclaimer warranty` |
| 96 | Files missing ALL required terms | `peekdocs --inverse -a confidential signature date` |
| 97 | Inverse with regex pattern | `peekdocs --inverse -x "\d{3}-\d{2}-\d{4}"` |
| 98 | Inverse with file type filter | `peekdocs --inverse -t pdf,docx "effective date"` |
| 99 | Inverse recursive search | `peekdocs --inverse -r "retention policy"` |
| 100 | Inverse with CSV output | `peekdocs --inverse -o csv "indemnification"` |
| 101 | Inverse with JSON output | `peekdocs --inverse -o json "authorization"` |
| | **Boolean Expression Search** | |
| 102 | AND expression | `peekdocs -e "budget AND revenue"` |
| 103 | OR expression | `peekdocs -e "budget OR revenue"` |
| 104 | AND NOT expression | `peekdocs -e "budget AND NOT draft"` |
| 105 | Grouped OR within AND | `peekdocs -e "(budget OR revenue) AND (cost OR profit)"` |
| 106 | Grouped AND with OR | `peekdocs -e "(bob AND amy) OR (fred AND wilma)"` |
| 107 | Complex with NOT | `peekdocs -e "(merger OR acquisition) AND NOT draft"` |
| 108 | Multi-word terms in expression | `peekdocs -e '"annual report" AND (2023 OR 2024)'` |
| 109 | Expression with wildcard | `peekdocs -e -w "budg* AND rev*"` |
| 110 | Expression with regex | `peekdocs -e -x "\\d{3}-\\d{4} AND budget"` |
| 111 | Expression with fuzzy | `peekdocs -e -z "budgt AND revnue"` |
| 112 | Expression with context | `peekdocs -e -B 2 -A 2 "merger AND NOT confidential"` |
| 113 | Expression recursive | `peekdocs -e -r "(budget OR revenue) AND (cost OR profit)"` |
| | **Output Directory** | |
| 114 | Write results to a specific folder | `peekdocs --output-dir ~/reports budget` |
| 115 | Output dir with recursive search | `peekdocs --output-dir /tmp/results -r budget` |
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
| 116 | Filter by dollar amount range | `peekdocs -R amount:1000..5000 budget` |
| 117 | Filter by date range | `peekdocs -R date:2024-01-01..2024-12-31 report` |
| 118 | Range-only search (no text terms) | `peekdocs -R amount:1000..5000` |
| 119 | Filter by file size | `peekdocs -R filesize:1M..10M report` |
| 120 | Multiple ranges (AND) | `peekdocs -R amount:1000..5000 -R date:2024-01-01..2024-12-31 invoice` |
| 121 | Open-ended range (minimum only) | `peekdocs -R amount:10000.. contract` |
| 122 | Percent range | `peekdocs -R percent:10..50 growth` |
| 123 | Age range | `peekdocs -R age:18..65 patient` |
| 124 | Time range | `peekdocs -R time:09:00..17:00 meeting` |
| 125 | Range with recursive search | `peekdocs -R amount:1000..5000 -r budget` |
| 126 | Open-ended range (maximum only) | `peekdocs -R amount:..5000 invoice` |
| 127 | Filter by file modification date | `peekdocs -R filedate:2024-01-01..2024-06-30 report` |
| 128 | Number range (any standalone number) | `peekdocs -R number:100..999 report` |
| 129 | Range with file type filter | `peekdocs -R amount:1000.. -t .pdf,.docx invoice` |
| 130 | Range with context lines | `peekdocs -R amount:5000..10000 -B 2 -A 2 payment` |
| 131 | Range with AND mode text search | `peekdocs -R date:2024-01-01..2024-12-31 -a budget revenue` |
| 132 | Range with exclude terms | `peekdocs -R amount:1000..5000 -n draft invoice` |
| 133 | Large file search | `peekdocs -R filesize:10M.. -r report` |
| 134 | Small recent files | `peekdocs -R filesize:..100K -R filedate:2025-01-01.. memo` |
| | **Filename Ranges** | |
| 134a | Filter by date in filename | `peekdocs -R fn:date:2024-01-01..2024-12-31 budget` |
| 134b | Filename + content range | `peekdocs -R fn:date:2024-01-01..2024-12-31 -R amount:1000..5000 invoice` |
| 134c | Filename range in expression | `peekdocs -e "budget AND fn:date:2024-01-01..2024-12-31"` |
| | **Range Queries in Expressions** | |
| 135 | Text AND amount range | `peekdocs -e "budget AND amount:1000..5000"` |
| 136 | Text AND date range | `peekdocs -e "report AND date:2024-01-01..2024-12-31"` |
| 137 | OR with range on one branch | `peekdocs -e "(budget AND amount:1000..5000) OR revenue"` |
| 138 | NOT with range (exclude high amounts) | `peekdocs -e "invoice AND NOT amount:10000.."` |
| 139 | Multiple ranges in expression | `peekdocs -e "invoice AND amount:500..5000 AND date:2024-01-01..2024-12-31"` |
| 140 | Range-only expression | `peekdocs -e "amount:1000..5000"` |
| 141 | OR between two ranges | `peekdocs -e "amount:1000..5000 OR percent:10..50"` |
| 142 | Text with percent range | `peekdocs -e "growth AND percent:20..100"` |
| 143 | Text with age range | `peekdocs -e "patient AND age:18..65"` |
| 144 | Text with time range | `peekdocs -e "meeting AND time:09:00..17:00"` |
| 145 | Complex: text + range + NOT | `peekdocs -e "(contract AND amount:5000..50000) AND NOT draft"` |
| 146 | Complex: two branches with ranges | `peekdocs -e "(budget AND amount:1000..5000) OR (invoice AND date:2024-01-01..2024-12-31)"` |
| 147 | Expression + -R metadata filter | `peekdocs -e "budget AND amount:1000..5000" -R filesize:..1M` |
| 148 | Expression with wildcard + range | `peekdocs -e -w "budg* AND amount:1000..5000"` |
| 149 | Expression with regex + range | `peekdocs -e -x "INV-\\d+ AND amount:1000..5000"` |
| | **Installation Check** | |
| 150 | Check installation health | `peekdocs --check` |
| | **Version and Help** | |
| 151 | Show version | `peekdocs -v` |
| 152 | Show help | `peekdocs -h` |
| 153 | Show help (no arguments) | `peekdocs` |

## Output

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

- **`peekdocs_results.txt`** — Plain text with `**` markers around matched terms
- **`peekdocs_results.docx`** — Word document with search terms highlighted in green in the header and matched terms highlighted in yellow throughout

With the `-o` flag, additional output files are created:

- **`peekdocs_results.csv`** (`-o csv`) — Spreadsheet-ready format with columns: filename, folder, line_number, matched_text. Open in Excel, Google Sheets, or any spreadsheet application to sort, filter, and analyze results.
- **`peekdocs_results.json`** (`-o json`) — Machine-readable format with search metadata, per-file match counts, and a matches array. Useful for integrating peekdocs into automated workflows, dashboards, or other tools.

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
(/Users/bob/GoogleDocs)
"The **budget** for this quarter exceeded expectations"

Document: summary.docx (1 match), Line: 3, Match:
(/Users/bob/GoogleDocs)
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
Results ==> /Users/bob/GoogleDocs
```

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

**Safe and reliable:** The index uses SQLite WAL mode with atomic transactions, busy timeouts, and graceful lock handling. Multiple searches, auto-refresh, and external tools can access the same index safely. If the process crashes mid-refresh, uncommitted changes are rolled back automatically.

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

## PII Scan

The **PII Scan** is peekdocs's one-click scan for sensitive data (PII) in your own files. Click the red **PII Scan** button on the main screen — peekdocs runs a battery of regex pattern searches for Social Security numbers, credit cards, tax IDs / EINs, email addresses, phone numbers, passwords, dates of birth, and dollar amounts, and produces a highlighted Word report showing exactly where each finding was detected.

The PII Scan is a **GUI feature only** — the CLI (`peekdocs`) runs individual searches but does not currently expose the PII Scan as a flag.

### What it does

- Runs the eight built-in PII regex patterns against every file in your selected search folder (respecting Recursive and File Type settings).
- Groups findings by category (SSN, credit card, tax ID, email, phone, password, DOB, dollar amounts).
- Categorizes each category by severity (HIGH for SSNs, credit cards, and tax IDs; MODERATE for emails, phones, passwords, and dates of birth; INFO for dollar amounts).
- Produces a consolidated `.docx` report with a summary table, a detail section per category, every affected file listed with match counts and line numbers, and the matched text highlighted in yellow.
- Everything runs locally on your machine. Nothing is uploaded, transmitted, or sent to any third party.

### How to use it

1. Open the GUI: `peekdocs-gui`.
2. Browse to the folder you want to scan (use **Change Folder** inside the PII Scan popup if you want to scan a different folder without changing the main screen).
3. Click the red **PII Scan** button in the main Search Bar.
4. A configuration popup appears. All eight categories are checked by default. Uncheck any you don't want, or use **Select All** / **Deselect All**.
5. For **Dollar Amounts**, set the **Min $** and **Max $** range. Defaults are $10,000 and $999,999,999. The scan uses a loose regex to match any dollar amount and then filters results to those within your range.
6. Click **Run Scan**. The status bar shows progress through each category.
7. When the scan finishes, a results popup appears with one row per category, showing severity and findings count. Categories with no findings show a green "Clean" label. Click **View Files** on any category with findings to see exactly which files are affected.
8. Inside the View Files popup, each row shows the filename, match count, and up to 20 line numbers. Double-click a row to open the original file in its default application, or select a row and click **View Text (with line numbers)** to see the extracted file content with line numbers and every match highlighted in orange.
9. Click **Open Report** in the main results popup to open the `.docx` report that was automatically generated: `DO_NOT_SEARCH_pii_scan_report.docx`, saved in your search folder (or the Output Dir if set in Advanced Search Options). Each category heading in the report is color-coded by severity (red for HIGH, amber for MODERATE, blue for INFO) so you can find what matters quickly.

### Categories

| Category | Severity | What it finds |
|----------|----------|---------------|
| Social Security Numbers | HIGH | SSN patterns (XXX-XX-XXXX) |
| Credit Card Numbers | HIGH | Visa, Mastercard, Amex, Discover patterns |
| Tax ID / EIN | HIGH | Employer Identification Numbers (XX-XXXXXXX) |
| Email Addresses | MODERATE | Email address patterns |
| Phone Numbers | MODERATE | US phone number patterns |
| Passwords / Secrets | MODERATE | Lines containing password, secret, or API key assignments |
| Dates of Birth | MODERATE | Date-of-birth patterns near keywords like "DOB" or "born" |
| Dollar Amounts | INFO | Dollar amounts in a user-specified range |

### When to use it

The PII Scan answers the question *"what sensitive data is hiding in my own files?"* Common uses:

- **Before sharing a file or folder** — run a scan to check what's about to go out the door.
- **Before selling, donating, or retiring a computer** — see what's still sitting on the disk.
- **Helping a relative with a device** — check an elderly parent's laptop or an estate's records before handing it off.
- **Periodic personal audit** — once or twice a year, see what's accumulated in your Documents folder over the years.
- **Small-business file hygiene** — scan a shared folder for data that shouldn't be there anymore.

The PII Scan runs entirely on the user's own files, on the user's own machine, so there's no custody relationship with anyone else's data — it's just you looking at what's already on your disk.

### Custom Pattern (Advanced)

The eight built-in categories cover common US PII. If you need something the built-ins don't match — an international ID number, a company-specific account format, an internal reference code, an API key shape — the **Advanced — Custom Pattern** section at the bottom of the PII Scan configuration popup lets you add your own regex to the scan.

**How to use it:**

1. Open **PII Scan** on the main screen.
2. Scroll to the bottom of the category selection popup. You'll see a horizontal separator and a section labeled **Advanced — Custom Pattern (optional)**.
3. Check the checkbox to include your custom pattern in the scan.
4. Fill in three fields:
   - **Name** — a short label for this pattern (e.g., `UK NINO` or `Client Account ID`). The name appears as a category in the results popup and report.
   - **Regex** — the pattern to search for.
   - **Severity** — `high`, `moderate`, or `info`. Used for the color badge in the results popup and the heading color in the report.
5. Click **Run Scan**. Your custom pattern runs alongside the built-in categories you have checked, and findings appear as a separate category in the results.

**Example patterns** for common international and use-case formats:

| Pattern | What it matches |
|---------|-----------------|
| `[A-Z]{2}\d{6}[A-Z]` | UK National Insurance Number (NINO) |
| `\d{3}[- ]?\d{3}[- ]?\d{3}` | Canadian Social Insurance Number (SIN) |
| `GB\d{9}` | UK VAT number |
| `\d{2}[ ]?\d{3}[ ]?\d{3}[ ]?\d{3}` | German Steuer-ID |
| `[A-Z]{5}\d{4}[A-Z]` | Indian PAN (Permanent Account Number) |
| `[A-Za-z0-9_]{20,}` | Long alphanumeric token (API keys, session tokens) |
| `AKIA[0-9A-Z]{16}` | AWS access key ID |

**Regex basics**, if you need a refresher:

```
\d              any digit 0–9
\d{3}           exactly 3 digits
\d{3,5}         3 to 5 digits
[A-Z]           any uppercase letter
\s              any whitespace character
.               any single character (escape as \. for a literal dot)
?               the previous item is optional
|               OR (e.g., cat|dog)
( )             grouping
```

**What can go wrong — and what can't.** Writing a custom regex is a power-user affordance, and it comes with the usual regex footguns: a broad pattern like `\d+` will match every digit sequence in every file and flood the report, and a pattern like `[0-9` (missing closing bracket) won't even compile. peekdocs catches syntax errors before starting the scan and shows a friendly error message. peekdocs also warns you if your pattern looks suspiciously broad (three characters or less, or one of the common too-broad patterns like `.`, `.*`, `\d+`) and asks you to confirm before running.

**But note what can't go wrong:** peekdocs never modifies, moves, or deletes the files it searches. A bad custom regex cannot corrupt your documents, change filenames, delete anything, or touch your data in any destructive way. The worst outcome of a poorly written pattern is a useless or overwhelming report, which you fix by editing the pattern and running the scan again.

**Persistence.** Your custom pattern is saved to `~/.peekdocsrc` and restored the next time you open the PII Scan. Uncheck the box to skip your custom pattern for a scan without losing it — it stays filled in, ready for the next run.

### Important disclaimers

The PII Scan is a **pattern-matching discovery aid**, not a security product. Please read these before you rely on it.

- **Pattern-based detection produces false positives.** A 9-digit account number can look like an SSN. A tracking number can match the credit card pattern. The word "password" can appear in a help document that contains no actual passwords. Always review findings in context before taking action — the report shows the matched text with surrounding context precisely so you can judge whether each finding is real.
- **Pattern-based detection also produces false negatives.** peekdocs cannot find PII that doesn't match its built-in regex patterns. An SSN written as `123 45 6789` (spaces instead of dashes) may not be detected. A credit card number written without any separator may be missed. A foreign tax ID in a format peekdocs doesn't know about will not be flagged. **A clean PII Scan report does not prove that a file is free of sensitive data.** It proves only that peekdocs's specific regex patterns did not match anything in the file's extracted text.
- **Some file formats may not be fully extracted.** peekdocs searches 46 file types, but extraction quality varies — a scanned PDF without OCR enabled will not surface any text at all, an image file will be ignored unless OCR is on, and complex binary formats may yield partial text. Files that peekdocs could not read or partially read will not produce findings even if they contain PII. Check the **View N excluded file(s)** button after each scan to see which files were skipped.
- **The PII Scan is not a breach prevention tool.** It does not block, encrypt, move, delete, or otherwise secure any data. It only finds and reports. If you decide based on the report that a file needs to be removed or redacted, that's your decision to make and your action to take — peekdocs does not modify your files.
- **The PII Scan is not compliance software.** A clean scan does not certify HIPAA, GDPR, PCI-DSS, SOX, or any other regulatory compliance. If your organization has compliance obligations, the PII Scan can be one input to your review process, but it is not a substitute for professional compliance expertise or a formal audit.
- **Custom user-supplied patterns are your responsibility.** When you enter your own regex in the Custom Pattern section, peekdocs does not validate that your pattern correctly identifies the data you intend to find. A pattern that is too broad will produce many false positives; a pattern that is too narrow will miss the data you are looking for. If you type your own regex, you own the outcome. peekdocs will catch regex syntax errors and warn you about obviously too-broad patterns, but it cannot judge whether your regex is *semantically* right for your data.
- **peekdocs is provided as-is under the [MIT License](../LICENSE).** There is no warranty of any kind, express or implied. Users are solely responsible for how they interpret and act on the results. See the LICENSE file for the full text.

In short: **the PII Scan is a helpful set of eyes on your own files. It is not a guarantee, a certification, or a security system.** Use the results as a starting point for your own review, not as a final answer.

### Privacy and the local-only model

The PII Scan is built around a simple principle: **your files never leave your computer**. The scan runs in the same Python process as the rest of peekdocs, reads your files directly from local disk, and writes the resulting `.docx` report back to local disk. Nothing is sent to a server, an API, a cloud service, or any third party.

This matters for two reasons. First, you can scan files containing real PII (your own tax returns, your own credit card statements, your own medical records) without worrying that the tool is creating a new exposure. Second, there is no network traffic for a firewall or ISP to observe, no API key to leak, no cloud bill to pay, and no vendor relationship to audit.

The one thing to be aware of is the output file itself. The generated report contains snippets of matched text, including the actual sensitive data that was detected, highlighted in yellow. That file lives on your local disk like any other document — if your disk is backed up to the cloud, or shared over a network, or readable by other users on a shared machine, the report is subject to whatever access policies apply to that location. See the [Security Best Practices](#security-best-practices) section for handling tips.

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
peekdocs -e "((merger OR acquisition) AND NOT confidential) OR (ipo AND SEC)"
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

**Basic range filtering** — combine `-R` with text search terms:

```bash
# Find "budget" in lines that mention amounts between $1,000 and $5,000
peekdocs -R amount:1000..5000 budget

# Find "report" in lines dated within 2024
peekdocs -R date:2024-01-01..2024-12-31 report

# Find "meeting" in lines with times between 9 AM and 5 PM
peekdocs -R time:09:00..17:00 meeting

# Find "growth" in lines with percentages between 10% and 50%
peekdocs -R percent:10..50 growth

# Find "patient" in lines mentioning ages 18 to 65
peekdocs -R age:18..65 patient

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

# Lines with "patient" and an age between 18 and 65
peekdocs -e "patient AND age:18..65"

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

# Healthcare: after-hours patient records for ages 18-30
peekdocs -e "patient AND age:18..30 AND time:17:00.."

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
- Metadata fields (`filesize`, `filedate`) can only be used with the `-R` flag, not inside `-e` expressions. Use `-R` alongside `-e` for metadata filtering
- When using `-R` alongside `-e`, the `-R` filters apply as an additional AND layer on top of the expression result
- Multiple `-R` flags combine with AND logic — all ranges must be satisfied
- **Bound string flexibility** — amounts accept `$` and `,` (e.g., `amount:$1,000..$5,000`), percents accept `%` (e.g., `percent:10%..50%`), dates accept ISO (`YYYY-MM-DD`) and US (`MM/DD/YYYY`, `MM-DD-YYYY`) formats, times accept `HH:MM`, `HH:MM:SS`, and `HH:MM AM/PM` formats
- **Long form** — `--range` is the long form of `-R` (e.g., `--range amount:1000..5000`)
- **Reports** — when range filters are active, they appear in the report header as modifiers (e.g., "range filter amount: 1000 .. 5000"). For range-only searches (no text terms), the report describes the search as "with range filters only"
- **Index search** — ranges work with the search index. Indexed results are post-filtered by content and metadata ranges
- **Saved searches** — range filters are fully preserved in saved searches and restored when you reload them. Enter ranges in the GUI's Range field before clicking **Save Search**
- **Settings persistence** — the Range field value is saved to `~/.peekdocsrc` when you click **Save Defaults** in Advanced Search Options, and restored when the GUI opens or when you click Restore Settings

In the GUI, enter range filters in the **Range** field in Advanced Search Options, comma-separated for multiple ranges (e.g., `amount:1000..5000, date:2024-01-01..2024-12-31`).

## Combining Modes

You can mix multiple modes together for more powerful searches.

**Regex + AND + Recursive** — Find files containing both an SSN and a dollar amount anywhere in nested subfolders:

```bash
peekdocs -x -a -r "\d{3}-\d{2}-\d{4}" "\$[\d,]+\.\d{2}"
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
peekdocs --config                      # view your saved settings
peekdocs --config recursive=           # remove a saved setting
```

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
| `index_search` | true/false | — | false (direct file search) |
| `search_terms` | text | — | empty (none) |
| `folder` | path | — | empty (current directory) |
| `pii_scan_categories` | list | — | all 8 categories enabled (SSNs, credit cards, tax IDs, emails, phones, passwords, DOB, dollar amounts) |

If no settings are saved or if a value is invalid, peekdocs uses its built-in defaults. The `search_terms`, `folder`, and `index_search` settings are GUI-only — they pre-fill the GUI fields when it opens but have no effect on CLI searches.

**Advanced:** Your settings are stored in a text file called `.peekdocsrc` in your user folder. You can also edit this file directly if you prefer — each line is a `key = value` pair, and lines starting with `#` are comments.

## Files Created by peekdocs

peekdocs creates several types of files during normal operation. Understanding what each file is, where it lives, and how to manage it helps you keep your folders clean and troubleshoot issues.

**Important:** peekdocs never modifies, moves, or deletes your original documents. All files listed below are created by peekdocs itself. peekdocs can delete its own files when you ask — for example, Clear Results removes report files and Delete Index removes the search index. These operations only affect files that peekdocs created, never your documents.

### Search reports

These are your search results. By default, they are overwritten each time you run a new search. If you enable the Timestamp checkbox in Advanced Search Options, each search creates uniquely named files (e.g., `peekdocs_results_20260331_103425.docx`) — useful for keeping a history, but these accumulate over time.

| File | Purpose | Location |
|------|---------|----------|
| `peekdocs_results.txt` | Plain text report | Search folder (or `--output-dir`) |
| `peekdocs_results.docx` | Word report with yellow-highlighted matches | Search folder (or `--output-dir`) |
| `peekdocs_results.csv` | Spreadsheet format (optional, with `-o csv`) | Search folder (or `--output-dir`) |
| `peekdocs_results.json` | Machine-readable format (optional, with `-o json`) | Search folder (or `--output-dir`) |

**Protected from searching:** Yes — all filenames starting with `peekdocs_results` are excluded so peekdocs never searches its own reports (including timestamped versions).
**How to delete:** Click **Clear Results** on the bottom toolbar to delete all `peekdocs_results*` files at once (a confirmation dialog lists the files before deletion). Or delete them manually. They are recreated on the next search.

### Saved and accumulated reports

Created when you use `-s` (save) or `-sa` (append) to archive results with a name you choose.

| File | Purpose | Location |
|------|---------|----------|
| `DO_NOT_SEARCH_{name}.txt` | Named archive of search results (text) | Search folder (or `--output-dir`) |
| `DO_NOT_SEARCH_{name}.docx` | Named archive of search results (Word) | Search folder (or `--output-dir`) |
| `DO_NOT_SEARCH_ACCUMULATED_{name}.txt` | Accumulated results from multiple searches (text) | Search folder (or `--output-dir`) |
| `DO_NOT_SEARCH_ACCUMULATED_{name}.docx` | Accumulated results from multiple searches (Word) | Search folder (or `--output-dir`) |

**Protected from searching:** Yes — the `DO_NOT_SEARCH_` prefix ensures these are never included in future searches.
**How to delete:** Delete them manually at any time, or use **Clear Results** on the main screen to remove peekdocs_results files.

### PII scan report

Created automatically when a Sensitive Data Scan detects findings.

| File | Purpose | Location |
|------|---------|----------|
| `DO_NOT_SEARCH_pii_scan_report.docx` | Highlighted Word report with summary table, per-category details, and yellow-highlighted matches | Output Dir if set in Advanced Search Options, otherwise search folder |

**Protected from searching:** Yes — `DO_NOT_SEARCH_` prefix.
**How to delete:** Delete manually, or use **Clean Up Practice Files** in the Maintenance menu. Overwritten on each new PII scan.

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
| Config file | 1 (home dir) | N/A | With caution — loses saved settings and email config |

**Most of these files are safe to delete** — peekdocs recreates reports, logs, and indexes automatically. The two exceptions are the **collection file** (`.peekdocs_collection.json`), which contains your saved searches, and the **config file** (`~/.peekdocsrc`), which contains your settings and email configuration. Deleting either of these means recreating that work from scratch. Everything else can be deleted freely.

## Limits and Constraints

**peekdocs itself has no upper limits.** It will search as many files as you have, of any size, with as many search terms as you need. There is no cap on file count, file size, PDF page count, spreadsheet rows, search terms, saved searches, or index size. The only constraints are your computer's available memory, disk space, and processing power.

**Optional safeguards (all configurable, all removable):**

The following defaults exist to prevent accidental slowdowns or memory issues on very large folders. They are **entirely optional** — set any of them to 0 or remove them if you prefer no limits. peekdocs will search everything your hardware can handle.

| Safeguard | Default | Flag | Why it exists | How to remove |
|-----------|---------|------|---------------|---------------|
| **Max matches in reports** | 1,000 | `-m N` | Writing 50,000 matches to a .docx file can take minutes and produce a very large report. The total match count is always accurate in the summary — only the report files are capped | Set `-m 0` for unlimited |
| **Max file size** | 100 MB | `--max-file-size N` | Very large files (multi-GB PDFs, massive spreadsheets) can take minutes to parse and may exhaust memory. Skipped files are logged to `peekdocs_errors.log` so you know what was missed | Set `--max-file-size 0` for no limit. In the GUI, set **Max File Size (MB)** to 0 in Advanced Search Options |
| **CPU cores** | Half of available | `-c N` | Using all cores speeds up searches but makes your computer unresponsive while searching | Set `-c` to your full core count for maximum speed |

These safeguards exist because a user once searching a folder with multi-GB database exports shouldn't have to wonder why the app froze — the defaults protect against that while being easy to override. If you know your files are manageable, remove the limits entirely.

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

## Multilingual Support

peekdocs searches documents written in any language — English, Chinese, Japanese, Korean, Arabic, Hindi, Russian, Greek, Spanish, German, French, Portuguese, Thai, Hebrew, and every other language that can be represented in Unicode. Type your search terms in any language and peekdocs finds the exact character sequence in your files.

This is not a special feature unique to peekdocs. All modern search tools are built on Unicode, the universal standard for representing text in every writing system. peekdocs uses Python's built-in Unicode string handling, which means it has the same multilingual capabilities — and the same limitations — as any other Unicode-based tool.

### What works

- **Exact text matching in any language.** If your document contains `预算报告` and you search for `预算`, peekdocs finds it. This works for every script: Latin, Chinese, Japanese, Korean, Arabic, Hebrew, Cyrillic, Devanagari, Thai, Greek, and all others.
- **Regex in any language.** You can write regex patterns that match characters in any script. For example, `[A-Z]{2}\d{6}[A-Z]` matches a UK National Insurance Number, and `[\u4e00-\u9fff]+` matches Chinese characters.
- **Mixed-language documents.** A single file can contain text in multiple languages. peekdocs searches all of it — the same search can find English keywords in one file and Chinese keywords in another.
- **All 46 file types.** Multilingual support applies to every format peekdocs reads — .docx, .pdf, .xlsx, .eml, .txt, and all the rest. If the file's text extraction produces Unicode (which it does for all modern file formats), peekdocs can search it.
- **PII Scan custom patterns.** The Custom Pattern feature in the PII Scan lets you add regex patterns for international ID formats (UK NINO, Canadian SIN, Indian PAN, German Steuer-ID, Brazilian CPF, and more).

### What doesn't work (limitations)

- **No word segmentation for CJK languages.** Chinese, Japanese, and Korean do not use spaces between words. peekdocs searches for exact character sequences, which works well for most searches, but features that depend on word boundaries (like whole-word matching with `-W`) may not behave as expected for CJK text.
- **No stemming or lemmatization.** peekdocs does not reduce words to their root form. In English, searching for "running" will not automatically find "run" or "ran." The same applies to all other languages. Fuzzy matching (`-z`) can help find some variations, but it is not a substitute for proper stemming.
- **No stop-word removal.** peekdocs does not filter out common words like "the," "and," or "of" (or their equivalents in other languages). Every term you type is searched for literally.
- **No language detection.** peekdocs does not detect which language a document is written in. It treats all text as a sequence of Unicode characters regardless of language.
- **No right-to-left layout in the GUI.** Arabic and Hebrew text is searchable and appears correctly in reports (Word handles bidirectional text natively), but the GUI's text widgets may not render right-to-left text perfectly on all platforms.
- **No transliteration or translation.** Searching for "budget" will not find the Chinese word for budget (预算). You must search for the exact characters that appear in the document.

### Documentation and GUI language

The peekdocs GUI, help screens, documentation, and reports are all in **English only**. There are no translations of the interface into other languages. This is a practical limitation of being a solo-developer project — maintaining translations across every update is not feasible. The GUI labels are short and largely self-explanatory (Browse, Run Search, Save, Reload, PII Scan), so most non-English speakers can navigate the interface without difficulty.

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

### Example 1: Find Social Security numbers with regex

**Goal:** Find any document containing a Social Security number (format: 123-45-6789).

1. Open **Advanced Search Options** and check the **Regex** checkbox
2. In the **Search Terms** field, type: `\d{3}-\d{2}-\d{4}`
   - This is a regex pattern: `\d` means "any digit" and `{3}` means "exactly 3 of them"
   - You don't need to memorize regex — click the **Wizard** button next to the search box for a list of pre-built patterns you can insert with one click
3. Click **Run Search**
4. Look at the results preview:
   - Each match shows the filename, line number, and the actual SSN found, highlighted in yellow
   - If no matches appear, your documents don't contain SSNs — that's good
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

**Goal:** Find SSNs in PDF files across all subfolders, showing 2 lines of context before and after each match.

1. In the **Search Terms** field, type: `\d{3}-\d{2}-\d{4}`
2. Open **Advanced Search Options** and set:
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

---

## Running Tests

Running tests requires the cloned repository (see [Option B](../README.md#option-b-manual-install-with-git) in the README). From the project folder:

```bash
source venv/bin/activate
pytest tests/ -v
```

## Project Structure

```
peekdocs/
├── peekdocs/
│   ├── __init__.py      # Package init, re-exports library API
│   ├── __main__.py      # Enables python -m peekdocs
│   ├── api.py           # Public library API (search(), SearchMatch, SearchResult)
│   ├── cli.py           # CLI entry point (calls api.search internally)
│   ├── collection.py    # Saved search collections
│   ├── constants.py     # Shared constants and defaults
│   ├── expr_parser.py   # Boolean expression parser (AND/OR/NOT)
│   ├── gui.py           # Optional GUI (peekdocs-gui)
│   ├── indexer.py       # Optional SQLite FTS5 search index
│   ├── parser.py        # Command-line flag parsing
│   ├── reporter.py      # Report generation (txt, docx, csv, json, pdf)
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
