# peekdocs FAQ and Troubleshooting

Common questions and solutions for peekdocs issues. If you're stuck, start with **[Where to Start](#where-to-start)** below — it tells you what to run first. For general usage, see the [User Guide](USER_GUIDE.md) or [README](../README.md).

## Table of Contents

- [Where to Start](#where-to-start)
- [FAQ (Frequently Asked Questions)](#faq-frequently-asked-questions)
- [Troubleshooting](#troubleshooting)

## Where to Start

**First, run `peekdocs --check`** (CLI) **or open Tools → System Check in the GUI**. Both run the same diagnostic — they verify your Python version, dependencies, Tesseract availability, SQLite, and free disk space, and tell you exactly what's missing. Many "peekdocs isn't working" problems resolve at this step before you need to read any further.

**Then search this page.** Use **Ctrl-F** (Windows/Linux) or **Cmd-F** (macOS) to find a phrase from your error message. With ~90 entries on this page, in-page search is faster than scrolling.

### Jump to your problem area

Use Ctrl-F / Cmd-F to land on the relevant entry — exact entry titles to search for are shown in **bold**:

- **Install or upgrade issues** — search for **"peekdocs: command not found"**, **"ensurepip"**, **"setup.py not found"**, **"pip' is not recognized"**, **"Wrong Python or wrong pip"**, or **"ModuleNotFoundError"**.
- **GUI doesn't launch or doesn't behave correctly** — Linux / macOS Homebrew Python: **"No module named '_tkinter'"**. Linux only: **"Tools menu requires holding"**, **"Browse button requires double-click"**. Windows/macOS: **"DOCX report won't open"**, **"File picker"**.
- **Search returns nothing or fewer matches than expected** — **"isn't finding matches I know are there"**, **"Search misses files I recently added"**.
- **OCR not working** — **"OCR requires the pytesseract"**, **"OCR is enabled but"**.
- **Specific file format errors** — **"PST support requires"**, or scan for **`.rar`** / **`libpff`** entries.
- **PowerShell or shell-quoting issues (Windows)** — **"PowerShell rejects"**, **"Regex patterns behave differently in PowerShell"**.
- **Index issues** — **"Index database was corrupted"**, **"Search misses files I recently added"**.
- **Permission errors ("can't read this folder")** — **"Why can't peekdocs read files"**, **"Permission denied"**.

### Still stuck?

If `peekdocs --check` is clean and nothing on this page matches your symptom, open an issue at [github.com/exbuf/peekdocs/issues](https://github.com/exbuf/peekdocs/issues). Include:

1. The exact command you ran (or the GUI action you took).
2. The exact error message — copy-paste, don't paraphrase.
3. The output of `peekdocs --check`.
4. Your OS and how you installed peekdocs (standalone download, pipx, or source).

## FAQ (Frequently Asked Questions)

**Where are my search results saved and what information is printed on the search report?**
Results are saved to two files in the current directory: `peekdocs_standard_results.txt` and `peekdocs_standard_results.docx`. Each report includes the date and time, the command used, search terms, number of hits, search time, number of files searched, total file size, and a file type tally. Each match shows the document name, directory path, line number, and the matched text with search terms highlighted — `**bold**` markers in the `.txt` file and yellow highlighting in the `.docx` file. Note that these two result files are overwritten each time you run a new search. Use the `-s` flag to archive them or the `-sa` flag to accumulate results across searches. Archived files are saved as `peekdocs_report_my_report.txt` and accumulated files as `peekdocs_accumulated_my_report.txt` — the prefix is added automatically so they are never re-searched in future searches.

**What happens when a file can't be read?**
Some files may fail to read — for example, encrypted PDFs, corrupted documents, password-protected spreadsheets, files with unsupported encoding, or files that are open in another program (especially on Windows, where open files are locked). When this happens, a warning is printed to the screen and the error is logged to `peekdocs_errors.log` with a timestamp. If a file is locked, the warning will suggest closing the program that has it open and trying again. In the GUI, a **View Error Log** button appears after any search where errors were logged — click it to open the log directly. The error log is only created when a file error occurs — if all files are read successfully, no error log is created. The log appends across searches so you have a history of any issues. You can delete `peekdocs_errors.log` at any time — a new one will be created automatically the next time a file error occurs. The error log is automatically excluded from searches so it never appears in your results. If peekdocs itself crashes unexpectedly, a crash report with a diagnosis is also written to this file.

**How do I recall a previous command?**
Press the up arrow key in your terminal to scroll through previous commands. This is a built-in feature of all terminals (macOS, Windows, and Linux) — not specific to peekdocs. You can press up repeatedly to go further back, then press Enter to re-run the command.

**How do I cancel a search in progress?**
Press Ctrl+C. peekdocs will stop cleanly and print "Search cancelled." This works on macOS, Windows, and Linux.

**How do I check if peekdocs is installed correctly?**
Run `peekdocs --check`. This verifies your Python version, checks that all required dependencies are installed, reports whether Tesseract is available for OCR, and checks available disk space. If anything is missing, it tells you exactly how to fix it.

**How do I save my preferred settings?**
Use the `--config` flag. For example, `peekdocs --config recursive=true` saves that setting so it applies automatically every time. See [Saved Settings](USER_GUIDE.md#saved-settings-optional) in the User Guide for details.

**Why doesn't peekdocs install the scheduled task for me?**
By design. **Tools → Schedule Search** generates the right `peekdocs` CLI command for your choices and puts it on your clipboard; you paste it into `crontab -e` (Mac/Linux) or Task Scheduler (Windows). peekdocs deliberately does not write to your system scheduler. The short version: peekdocs runs as a normal user app and doesn't take the system-write permissions a scheduler-write would need; cross-platform scheduler-write code (cron syntax, launchd plists, Task Scheduler XML, COM bindings, permission dialogs) is a large maintenance surface for a solo project; and keeping peekdocs's role to "compose the command, you paste it" means no privilege escalation, no in-app task registry to keep in sync with the OS, the schedule is auditable with standard tools (`crontab -l`, Task Scheduler GUI), and the scheduled command survives peekdocs upgrades or uninstall. The trade-off you accept: an extra paste step, no in-app schedule list, and changes mean editing the OS scheduler directly. Full rationale: [Why Schedule Search generates a command instead of installing the task](USER_GUIDE.md#why-schedule-search-generates-a-command-instead-of-installing-the-task) in the User Guide.

**Can I search all subfolders?**
Yes — use the `-r` flag.<br>
Example: `peekdocs -r budget`

**Can I search only PDFs (etc)?**
Yes — use the `-t` flag.<br>
Example: `peekdocs -t pdf budget`

**Can I search a specific file?**
Yes — use the `-f` flag.<br>
Example: `peekdocs -f report.pdf budget`<br>
You can focus on one file or several, comma-separated: `peekdocs -f report.pdf,notes.txt budget`

**Can I find terms near each other?**
Yes — use the `-p` flag.<br>
Example: `peekdocs -p 5 budget revenue`<br>
The number 5 means the terms must appear within 5 words of each other.

**Can I save these results?**
Yes — use the `-s` flag.<br>
Example: `peekdocs -s my_report`<br>
The saved/archived file is never re-searched because of its `peekdocs_report_` prefix.

**Can I accumulate results from multiple searches?**
Yes — use the `-sa` flag.<br>
Example: `peekdocs -sa my_report budget revenue`<br>
Each new search you run with the same name is appended to the bottom of the file, so your results accumulate over time. The accumulated file is never re-searched because of its `peekdocs_accumulated_` prefix.

**Can I find approximate matches or handle typos?**
Yes — use the `-z` flag. This enables fuzzy matching, which finds words that are similar to your search terms even if they're not spelled exactly the same. For example, searching for "budget" with `-z` will also match "budgt", "buget", or "budjet". This is especially useful when searching OCR text (combine with `-O`), which often contains recognition errors.<br>
Example: `peekdocs -z budget`

**Can I use wildcards instead of regex?**
Yes — use the `-w` flag. Wildcards are simpler than regex: `*` matches any characters and `?` matches exactly one character. For example, `budg*` matches "budget", "budgets", and "budgeting", while `te?t` matches "test" and "text". Wildcards match whole words only, so `budg*` won't match the "budg" inside "debugging".<br>
Example: `peekdocs -w "budg*"`

**How do I search for exact word matches only?**
Use the `-W` flag. This enables whole-word matching using word boundaries, so only complete words are matched — `bob` matches "bob" but not "bobcat", "bobby", etc.<br>
Example: `peekdocs -W bob`

**Can I exclude certain terms from results?**
Yes — use the `-n` flag. This filters out any lines that contain the specified terms, even if they match your search. Use commas for multiple exclude terms. The exclude check follows the current search mode — in fuzzy mode, exclude terms are fuzzy-matched; in wildcard mode, they are wildcard-matched.<br>
Example: `peekdocs -n draft budget`<br>
Example with multiple excludes: `peekdocs -n draft,obsolete budget`

**Can I search scanned PDFs or images?**
Yes — use the `-O` flag. This uses OCR (Optical Character Recognition) to extract text from scanned PDF pages and image files (.jpg, .jpeg, .png, .tiff, .tif, .bmp). Tesseract must be installed on your system — see the [README](../README.md#prerequisites) for installation instructions. OCR is slower than regular text search, so it's opt-in.<br>
Example: `peekdocs -O budget`

**Can I use regex patterns?**
Yes — use the `-x` flag. [Common Regex Patterns](USER_GUIDE.md#common-regex-search-patterns)<br>
Example: `peekdocs -x "\d{3}-\d{3}-\d{4}"`

**Can I see lines before and after each match?**
Yes — use the `-B` and `-A` flags.<br>
Example: `peekdocs -B 3 -A 3 budget`<br>
This captures 3 lines before (-B) and 3 lines after (-A) each match. The numbers can be different, e.g., `-B 2 -A 5`.

**Can I require all terms to appear in the same paragraph?**
Yes — use the `-a` flag.<br>
Example: `peekdocs -a budget revenue expenses`

**Can I combine AND, OR, and NOT in a single query?**
Yes — use the `-e` flag for boolean expression search. This lets you write complex logic with AND, OR, NOT, and parentheses.<br>
Example: `peekdocs -e "(budget OR revenue) AND NOT draft"`<br>
Precedence: NOT binds tightest, then AND, then OR. Use parentheses to override. The `-e` flag cannot be combined with `-a`, `-n`, or `-p` — those features are built into the expression syntax. Range specs (`field:min..max`) can be embedded directly in expressions (e.g., `"budget AND amount:1000..5000"`). See [Boolean Expression Search](USER_GUIDE.md#boolean-expression-search) in the User Guide for details.

**How many CPU cores does peekdocs use?**
By default, peekdocs uses half of your available CPU cores to keep your machine responsive. Use the `-c` flag to control this.<br>
Example: `peekdocs -c 4 budget`<br>
For small numbers of files (fewer than 10), single-threaded mode is used automatically to avoid overhead.<br>
peekdocs displays your core count and default `-c` value in the banner every time it runs (also visible with `peekdocs -h`). You can also check manually:<br>
- **macOS:** Open Terminal and run `sysctl -n hw.ncpu`<br>
- **Windows:** Open Command Prompt and run `echo %NUMBER_OF_PROCESSORS%`<br>
- **Linux:** Open Terminal and run `nproc`

You can set `-c` to any value from 1 to your maximum core count. Using more cores speeds up searches but uses more memory and CPU, which can slow down other applications and drain laptop batteries faster. The default (half of available cores) balances speed with keeping your machine responsive. Use `-c 1` for minimal resource usage, or `-c` with your full core count (e.g., `-c 8` on an 8-core machine) for maximum speed at the cost of heavier system load.

**Can I use multiple flags at the same time?**
Yes — most flags can be mixed and matched. Flag order doesn't matter.<br>
Example: `peekdocs -r -a -t pdf budget revenue` searches recursively, with AND logic, only in PDF files. See the [Command Examples](USER_GUIDE.md#command-examples) table in the User Guide for many combinations.

**Do I have to use the terminal, or is there a GUI?**
Both. If you prefer a graphical interface, run `peekdocs-gui` for a point-and-click window with a search box, folder picker, and all the advanced options. If you're comfortable in the terminal, `peekdocs` gives you the same search power in a single command.

Never used a terminal before? It's simpler than it looks — type `peekdocs` followed by what you're looking for, press Enter, and you're done. No menus, no buttons, no settings buried three screens deep. The terminal also launches instantly, runs identically on Mac, Windows, and Linux, and keeps a history of your commands so you can press the up arrow to repeat or tweak a previous search.

**What operating systems does peekdocs run on?**
peekdocs runs on macOS, Windows, and Linux — anywhere Python 3.10 or higher is installed.

**Does it search inside ZIP or RAR files?**
Yes — peekdocs searches inside .zip, .7z, .rar, .tar, .gz, .bz2, and .tgz archives. Files inside the archive are extracted to memory and searched like any other file. ZIP archives that would expand to over 500 MB are skipped to protect against archive bombs.

**Does it work offline?**
Yes — peekdocs runs entirely on your local machine with no internet connection needed. Your documents never leave your computer — no cloud uploads, no third-party servers, no risk of data exposure. It also means no rate limits, no usage caps, no subscriptions, and no slowdowns from server traffic. It works the same whether you have fast internet, slow internet, or no internet at all.

**Will upgrading peekdocs delete my saved searches or settings?**
No. Your saved searches, settings, indexes, and reports are stored in your home directory and document folders — completely separate from the peekdocs code. Upgrading replaces only the application code. Nothing else is touched. This applies to all installation methods (pipx, git, ZIP download). See the [User Guide](USER_GUIDE.md#will-peekdocs-affect-my-existing-python-installation) for the complete list of what is preserved.

---

**What if I upgrade Python and peekdocs stops working?**
Upgrading Python can occasionally break installed packages. If peekdocs stops working after a Python upgrade, run `peekdocs --check` to see which dependencies need updating, then reinstall: `pip install --upgrade peekdocs` (or `pipx reinstall peekdocs` if you used pipx). Check `peekdocs_errors.log` for a crash report with a diagnosis — it usually points to the exact package that needs updating. peekdocs will also print a warning at startup if your Python version is outside the tested range. Most dependency updates are available within a few weeks of a new Python release.

**What is the search index and when should I use it?**
The search index is an optional SQLite database (`.peekdocs.db`) that stores extracted text from your documents. Build it with `peekdocs --index` in any folder where you search frequently. After that, every search in that folder uses the index automatically — skipping file parsing entirely — making repeated searches much faster. You don't need the index for one-off searches or small folders. See [Search Index](USER_GUIDE.md#search-index-optional) in the User Guide for details.

**Why is my first search slow but later searches are fast?**
peekdocs builds the optional search index the first time you search a folder. The index reads every file once and stores the extracted text in `.peekdocs.db` — this takes anywhere from a few seconds (small folders) to a few minutes (thousands of files, large PDFs, or scanned documents). Every search after that uses the index and runs in milliseconds. The index keeps itself current automatically; you don't need to rebuild it manually. If you'd rather not use the index, add `--no-index` to your CLI command or uncheck **Use Index** in the GUI — searches will then read files directly each time. For scheduled jobs that want absolutely silent output, including any messages during the index-build phase, use standard shell redirection: `peekdocs TODO -r -qq 2>/dev/null` — this works alongside any quiet flag and discards every stderr message peekdocs (or any other tool) might emit. See [Search Index (Optional)](USER_GUIDE.md#search-index-optional) in the User Guide for full details, or run `peekdocs --check` to see your current index size.

**How much disk space does the index use?**
The index is typically 10–20% the size of the original files. Text-heavy documents (PDFs, Word docs) produce smaller indexes relative to file size since the index stores only the extracted text. You can check the exact size with `peekdocs --index-status` and delete it anytime with `peekdocs --index-clear`.

**Does the index stay up to date?**
Yes — each search automatically detects new, changed, or deleted files and refreshes the index incrementally before searching. You only need to rebuild manually (`peekdocs --index`) if you want a full rebuild, such as after changing OCR or recursive settings.

**Does it modify my files?**
No — peekdocs only reads your files. It never changes, moves, or deletes them.

**Is peekdocs safe from SQL injection?**
Yes. All user input that reaches the SQLite search index is handled safely. FTS5 search terms are escaped and passed via parameterized queries (`?` placeholders) — never interpolated into SQL strings. File type and filename filters also use parameterized queries. The direct-scan and parse-cache code paths load data with static SQL and filter entirely in Python, so user input never touches SQL at all. Malformed FTS5 expressions are caught and handled gracefully with a fallback to the parse-cache path.

**Is the search case-sensitive?**
No — all searches are case-insensitive by default.

**Why are my reports capped at 1,000 matches?**
By default, peekdocs caps reports at 1,000 matches to prevent very large result sets from causing slow report generation (especially the `.docx` report). The total match count is always reported accurately in the summary — only the report files are capped. To change the cap, use `-m N` (e.g., `-m 5000`). To remove the cap entirely, use `-m 0`. You can also set it permanently with `--config max_matches=5000` or in the GUI's Advanced Search Options panel.

Every feature in peekdocs serves the core mission of finding content in documents:

- **Search flags** (`-a`, `-e`, `-x`, `-p`, `-O`, `-z`, `-w`, `-W`) — control *how* to match
- **Filter flags** (`-t`, `-f`, `-r`, `-n`) — control *where* to search
- **Context flags** (`-A`, `-B`) — control *what to show* around matches
- **Output flags** (`-s`, `-sa`, `-o`) — control *what to do* with results
- **Performance flags** (`-c`, `-m`, `--index`) — control *how fast* to search
- **Settings flag** (`--config`) — manage *saved settings*

## Troubleshooting

**Search misses files I recently added (when using the index)**

If you're using the search index and peekdocs doesn't find matches in files you recently added, moved, or modified, the index is stale — it doesn't know about the new files yet. Rebuild the index:

- **GUI:** Tools → Manage Indexes → Build Index (or use Index Refresh for an incremental update)
- **CLI:** `peekdocs --index` (full rebuild) or `peekdocs --index-refresh` (incremental)

Alternatively, uncheck the Index checkbox or use `--no-index` to bypass the index and search files directly. Direct search always reads the current files on disk.

**The DOCX report won't open when I click the DOCX button**

The `.docx` report opens in whatever application your computer has associated with `.docx` files. If nothing happens when you click the button:

- **No word processor installed:** You need a program that can open `.docx` files. Microsoft Word works, but it's not required. [LibreOffice](https://www.libreoffice.org/download/download-libreoffice/) (free, cross-platform) is recommended. After installing one, try clicking the DOCX button again. You can also enable HTML output in Advanced Search Options — every computer has a browser. peekdocs avoids opening reports in Google Docs, Apple Pages, or any cloud-based application that may upload your data.
- **Garbled text in LibreOffice:** Files created in Google Docs and downloaded as `.docx` may display corrupted or unreadable text in LibreOffice. This is a known compatibility issue between Google Docs and LibreOffice — the document's embedded font may not be installed on your machine. **Simplest fix:** don't try to read the garbled text in LibreOffice — open the original document in Google Docs instead, use Edit → Find & Replace to search for the sensitive text shown in peekdocs's View Text, and redact it there. Then re-download and re-scan to verify. **Other options:** (1) Select all text (Ctrl+A on Windows/Linux, Cmd+A on macOS), then **Format → Clear Direct Formatting** to strip the embedded font styles, then change the font to **Liberation Serif** or **Liberation Sans**. (2) Re-export from Google Docs as OpenDocument format (.odt) — LibreOffice's native format. (3) Download as PDF instead of .docx — PDFs embed their fonts and render correctly everywhere (but are harder to edit for redaction). Note: peekdocs extracts text using python-docx, not LibreOffice, so peekdocs's View Text may show the text correctly even when LibreOffice cannot display it.
- **No default app set for .docx files:** Your computer may not know which program to use. On Windows: right-click any `.docx` file → Open with → Choose another app → select your word processor → check "Always use this app." On macOS: right-click any `.docx` file → Get Info → Open with → select your word processor → click "Change All."
- **File is missing:** If you ran another search after the first one, the previous `peekdocs_standard_results.docx` was overwritten. Use "Save report as:" in Advanced Search Options to keep a permanent copy.
- **Don't want to install anything?** Enable HTML output in Advanced Search Options and click the **HTML** button instead. Your highlighted report opens instantly in your web browser — every computer has a browser, so no extra software is needed.
- **Still not working:** Navigate to your Search Folder using File Explorer (Windows), Finder (macOS), or your file manager (Linux) and double-click `peekdocs_standard_results.docx` directly. If that also fails, try the HTML or `.txt` report instead.

**Why doesn't the File picker show a preview on Windows?**

On macOS, clicking the **File** button opens a file picker with a preview panel on the right side — you can inspect a file's contents before selecting it. On Windows, the file picker does not include a preview panel. This is a difference between the operating systems, not a peekdocs issue. Both platforms use the native OS file dialog, and peekdocs has no control over its appearance or features.

---

**My search isn't finding matches I know are there**

If a search returns no results (or fewer than expected) for terms you know exist in your documents, check **Advanced Search Options** for leftover settings from a previous search that may be filtering out results. Common culprits:

- **File types** — if set to `pdf`, only PDFs are searched; your `.docx` files are skipped
- **Exclude terms** — terms listed here cause matching lines to be silently dropped
- **Specific files** — limits the search to a single file
- **Range filters** — restricts results to lines with values in the specified range
- **Inverse** checked — shows files *missing* your terms instead of files containing them
- **Regex** or **Expression** checked — changes how your search terms are interpreted

To clear everything at once, open **Advanced Search Options** and click **Reset All Fields** (the red button). This restores all fields to their defaults for the current session without affecting your saved settings in `~/.peekdocsrc`.

If **Use Index** is checked on the main screen, try unchecking it and searching directly. A stale index may not contain recently added or changed files. To keep the index current, open **Manage Indexes** and set **Auto-Refresh** to an appropriate interval:

- **5–15 min** — folders where files change frequently
- **30 min–1 hour** — folders that change occasionally
- **4–24 hours** — stable folders checked periodically
- **Off** — rebuild manually with **Build Index(es)** when needed

Auto-refresh runs in the background while the app is open and does not interrupt searches.

---

**Why can't peekdocs read files in my Documents folder (permission denied)?**

Your operating system may be blocking peekdocs (or your terminal) from accessing protected folders like Documents or Downloads. This is a security feature — not a peekdocs bug. The fix below is a one-time setup that permanently allows access on each platform. These changes are narrowly scoped — they only grant read access to your terminal or Python for the folders you specify. All other OS security features (antivirus, firewall, app sandboxing, etc.) continue to work normally.

- **macOS:** Open System Settings → Privacy & Security → Full Disk Access. Click the `+` button, navigate to your terminal app (Terminal.app, iTerm, etc.), and add it. You may need to unlock the settings with your password first. Once added, the permission is permanent — it survives reboots and app updates. However, a major macOS upgrade (e.g., Ventura → Sonoma) can reset privacy permissions, so you may need to re-add it after upgrading. If you prefer narrower access, use Privacy & Security → Files and Folders instead and grant your terminal access to just the Documents folder.
- **Windows:** Open Windows Security → Virus & threat protection → Ransomware protection → Controlled folder access. If Controlled folder access is on, click "Allow an app through Controlled folder access," then click "Add an allowed app" → "Browse all apps" and select your Python executable. To find its path, run `where python` in a terminal. Once added, the allowlist entry is permanent. If you don't use Controlled folder access (it's off by default), this step is unnecessary — check your folder permissions instead: right-click the folder → Properties → Security tab and make sure your user account has Read access. Alternatively, running your terminal as administrator bypasses most access restrictions, but this is a per-session workaround, not a permanent fix.
- **Linux:** Run `chmod -R u+r /path/to/folder` to grant yourself read access, or `chown -R $USER /path/to/folder` to take ownership. These changes are permanent. If the folder is on an NTFS or FAT external drive, set the permissions at mount time by adding `uid=$USER,gid=$(id -g),dmask=022,fmask=133` to the mount options in `/etc/fstab`, then remount. This ensures the drive is always accessible when plugged in.

---

**"No module named '_tkinter'" or "ModuleNotFoundError: No module named 'tkinter'" (Linux / macOS Homebrew Python)**

The CLI (`peekdocs`) works but the GUI (`peekdocs-gui`) fails to launch. This happens because the Tkinter C extension is not bundled with the base Python install — it must be added separately as a system or Homebrew package.

**Fix on Linux:**

```bash
sudo apt install python3-tk
```

On Fedora/RHEL: `sudo dnf install python3-tkinter`. On Arch: `sudo pacman -S tk`.

**Fix on macOS (Homebrew Python only):**

```bash
brew install python-tk@3.14   # match the version you installed via brew install python@<version>
```

If you installed Python from [python.org](https://www.python.org/downloads/) instead, Tkinter is already included — there's nothing extra to install.

After installing, `peekdocs-gui` will launch normally. This is a one-time setup. Note: these are system / Homebrew packages — they cannot be installed via `pip`.

---

**Tools menu requires holding the mouse button (Linux)**

On Linux, clicking the Tools menu once causes it to disappear immediately. You must press and hold the mouse button, then drag to the menu item you want.

This is a known limitation of how Linux window managers handle menu focus in tkinter/customtkinter applications. It affects all tkinter-based apps on Linux, not just peekdocs. The menu is fully functional — the interaction is just different from macOS and Windows, where a single click keeps the menu open.

---

**Browse button requires double-click to select a folder (Linux)**

On Linux, clicking a folder once in the Browse dialog may not immediately select it — the folder shown in the window lags behind. Double-click the folder to confirm your selection, or single-click and then click OK.

This is a known limitation of the tkinter file dialog on Linux. On macOS and Windows, a single click selects the folder correctly. The Browse button is fully functional — the interaction just requires an extra click on Linux.

---

**"ensurepip" error when creating a virtual environment (Linux)**

On Debian-based Linux distributions (Ubuntu, Linux Mint, Pop!_OS, Debian), the base `python3` package does not include the `venv` or `pip` modules. Running `python3 -m venv venv` fails with an error like:

```
The virtual environment was not created successfully because ensurepip is not available.
```

**Fix:** Install the missing packages:

```bash
sudo apt install python3-venv python3-pip
```

Then re-run `python3 -m venv venv` — it will work. This is a one-time setup. On Fedora/RHEL, use `sudo dnf install python3-pip` instead. On Arch, `venv` and `pip` are included in the base `python` package.

---

**"setup.py not found" or "No setup.py, setup.cfg, or pyproject.toml" (Linux)**

This happens when the version of pip inside your virtual environment is too old to support `pyproject.toml`-based builds (which peekdocs uses instead of the older `setup.py` format). Older Linux distributions sometimes ship pip versions from 2021–2022 that don't have this support.

**Fix:** Upgrade pip, setuptools, and wheel inside the virtual environment before installing peekdocs:

```bash
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -e .
```

This updates the build tools to the latest versions, which fully support `pyproject.toml`. This only needs to be done once per virtual environment. Make sure the `(venv)` prefix is showing in your terminal prompt — if it's not, reactivate with `source venv/bin/activate` first.

---

**"'pip' is not recognized" or "'python' is not recognized" (Windows)**

This means Python is installed but not on your system PATH. The most common cause is forgetting to check **"Add Python to PATH"** during the Python installer. The easiest fix:

1. Re-run the Python installer from [python.org/downloads](https://www.python.org/downloads/)
2. On the first screen, check the box at the bottom that says **"Add Python to PATH"** (or "Add python.exe to PATH")
3. Click "Install Now" (or "Modify" if it offers that option)
4. Close and reopen Command Prompt

After that, `pip`, `python`, and `peekdocs` will all work from any Command Prompt window.

**Quick workaround (without reinstalling):** Use `py -m pip` instead of `pip`:

```cmd
py -m pip install pipx
```

The `py` launcher is usually available even when `pip` isn't on PATH.

---

**"ModuleNotFoundError: No module named 'fitz'" (or any other module)**

A required dependency is missing. This can happen after a Python upgrade or if the install was interrupted.

```bash
pip install --upgrade peekdocs       # reinstalls peekdocs and all dependencies
peekdocs --check                      # verify everything is installed
```

If you used pipx: `pipx reinstall peekdocs`

---

**"Error: peekdocs requires Python 3.10 or later"**

peekdocs needs Python 3.10+. Check your version with `python3 --version`, then upgrade:

- macOS: `brew install python@3.12`
- Ubuntu: `sudo apt install python3.12`
- Windows: Download from [python.org/downloads](https://www.python.org/downloads/)

After upgrading, reinstall peekdocs with the new Python.

---

**"Fuzzy search requires the rapidfuzz Python package"**

The `-z` (fuzzy) flag needs the `rapidfuzz` package:

```bash
pip install rapidfuzz
```

Or reinstall peekdocs: `pip install --upgrade peekdocs`

---

**"OCR requires the pytesseract and Pillow packages" / "Tesseract OCR is not installed"**

The `-O` (OCR) flag needs three things:

1. **Tesseract binary** (the OCR engine):
   - macOS: `brew install tesseract`
   - Ubuntu: `sudo apt install tesseract-ocr`
   - Windows: [Download from GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

2. **Python packages**: `pip install pytesseract Pillow`

Run `peekdocs --check` to verify Tesseract is detected.

---

**OCR is enabled but peekdocs doesn't find text in my scanned PDF or image**

Several possible causes:

1. **OCR not enabled** — check the OCR checkbox in Advanced Search Options (GUI) or add the `-O` flag (CLI). Without it, peekdocs only reads the text layer — image-only files will have no matches.
2. **Stale index** — if you're using the search index, it may not include the file yet. Rebuild the index (Tools → Manage Indexes → Build Index) or uncheck the Index checkbox to search directly.
2. **Tesseract not installed** — run `peekdocs --check` to verify. See the entry above for installation instructions.
3. **Low scan quality** — scans below 200 DPI produce poor OCR results. 300 DPI is recommended. Re-scan the document at a higher resolution if possible.
4. **Skewed or rotated text** — Tesseract struggles with text that isn't level. Re-scan with the document flat and straight.
5. **Handwritten text** — Tesseract is designed for printed text. Handwriting recognition is unreliable.
6. **Non-Latin scripts** — Tesseract needs language packs for non-English text. Install them: macOS: `brew install tesseract-lang`, Linux: `sudo apt install tesseract-ocr-chi-sim` (for Simplified Chinese, etc.).
7. **The file isn't image-only** — some PDFs have a text layer that's nearly empty (a few whitespace characters). peekdocs may read the text layer instead of falling back to OCR. Try searching with `-O --no-index` from the CLI to confirm.

---

**"PST support requires the libpff-python package"**

Searching `.pst` files (Outlook mailbox archives) requires `libpff-python`, which is a C extension that must be compiled from source:

```bash
pip install libpff-python
```

This requires a C compiler on your system:
- **macOS:** Install Xcode Command Line Tools: `xcode-select --install`
- **Ubuntu/Debian:** `sudo apt install build-essential python3-dev`
- **Windows:** Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) with the "Desktop development with C++" workload

If you can't install a C compiler, peekdocs still searches all other email formats (`.eml`, `.msg`, `.mbox`) — only `.pst` is affected.

**Note for testing:** No Python library can create `.pst` files from scratch. The PST format is a proprietary Microsoft binary structure ([MS-PST specification](https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-pst/)). To obtain a test `.pst` file, export one from Microsoft Outlook (File → Open & Export → Import/Export → Export to a file → Outlook Data File).

---

**"Index database was corrupted and has been removed"**

peekdocs detected that the `.peekdocs.db` file was damaged and automatically deleted it. This can happen if a previous indexing operation was interrupted. Simply rebuild:

```bash
peekdocs --index
```

---

**"peekdocs stopped working after upgrading Python"**

Python upgrades can break installed packages. Fix it by reinstalling:

```bash
pip install --upgrade peekdocs       # if installed with pip
pipx reinstall peekdocs              # if installed with pipx
peekdocs --check                      # verify the fix
```

Check `peekdocs_errors.log` in the current directory for a crash report with a diagnosis of the specific issue.

---

**"Permission denied" or "file is locked"**

A file could not be read because it's open in another application (common on Windows) or you don't have read permissions. peekdocs will skip the file and continue searching. Check `peekdocs_errors.log` for the specific file.

---

**"An unexpected error occurred"**

1. Check `peekdocs_errors.log` in the current directory — it contains a diagnosis with the likely cause and a suggested fix
2. Run `peekdocs --check` to verify your Python version and all dependencies
3. If the problem persists, [report it on GitHub](https://github.com/exbuf/peekdocs/issues) and include the contents of `peekdocs_errors.log`

---

**"peekdocs: command not found" after installation**

pip (or pipx) installed the `peekdocs` console script to a directory not in your `$PATH`. This commonly happens when installing with `--user` or when the virtual environment is not activated.

- **If you installed with pipx** (Option B in the README), run `pipx ensurepath` once, then **close and reopen the terminal** — the new PATH only takes effect in new shells. This is the most common cause on a fresh Linux install where `~/.local/bin` isn't on PATH yet.
- Check where it was installed: `pip show -f peekdocs | grep peekdocs`
- On Linux: scripts go to `~/.local/bin` — `pipx ensurepath` adds it for you, or manually add `export PATH="$HOME/.local/bin:$PATH"` to `~/.bashrc`
- On macOS with Homebrew: scripts go to `/opt/homebrew/bin` (Apple Silicon) or `/usr/local/bin` (Intel) — add to `~/.zshrc`
- On Windows: scripts go to `%APPDATA%\Python\Scripts` — add this to your system PATH
- As a fallback, you can always run `python -m peekdocs` instead

---

**Wrong Python or wrong pip (multiple Python installations)**

After installing peekdocs, running it gives `ModuleNotFoundError` because pip installed into a different Python than the one running peekdocs. This is common when system Python, Homebrew, pyenv, conda, or WSL Python coexist.

- Always install with `python -m pip install git+https://github.com/exbuf/peekdocs.git` (not just `pip install`) to ensure pip matches your Python
- Verify: `python -m pip show peekdocs` and `python -m peekdocs --version`
- In virtual environments, ensure the venv is activated: `which python` should point to the venv's Python

---

**`ModuleNotFoundError: No module named 'peekdocs'` right after `pipx install` succeeded (Windows)**

`pipx list` shows `peekdocs.exe` and `peekdocs-gui.exe` as installed, but running `peekdocs` fails with `ModuleNotFoundError: No module named 'peekdocs'`. Checking inside the pipx venv shows the package directory is empty or missing:

```powershell
dir $env:USERPROFILE\.local\pipx\venvs\peekdocs\Lib\site-packages\peekdocs
# "Cannot find path … because it does not exist."
```

Cause: pipx on certain Windows configurations reports a successful install while the package files silently fail to land in the venv. Not a Defender issue (protection history is empty); the install itself drops files midway. Reinstalling via pipx — including `--force` — produces the same empty state. The failure mode is reproducible.

Workaround: bypass pipx entirely. `python -m pip install --user …` uses a different code path and works on the same machines where pipx fails:

```powershell
pipx uninstall peekdocs
python -m pip install --user git+https://github.com/exbuf/peekdocs.git
peekdocs --version
peekdocs-gui
```

Upgrade later with the same command plus `--upgrade`. The trade-off vs pipx: no isolated venv (peekdocs's dependencies live alongside any other `pip --user` packages on your Python), which is typically fine on a personal Windows install.

---

**Regex patterns behave differently in PowerShell vs CMD (Windows)**

Regex patterns with special characters (`$`, `(`, `)`, `|`, `{`, `}`) produce unexpected results or errors in PowerShell because PowerShell interprets these characters before they reach Python.

- In PowerShell, use **single quotes** for search terms: `peekdocs -x '\d{3}-\d{3}-\d{4}'`
- In CMD, double quotes work normally: `peekdocs -x "\d{3}-\d{3}-\d{4}"`
- PowerShell also interprets backticks as escape characters — avoid them in search terms

---

**Regex returns zero matches in the GUI Regex Search popup even though the pattern looks right**

Common mistake: pasting the regex with surrounding quotes. The Regex field on the popup wants the **raw pattern**, with no enclosing quotes. peekdocs passes whatever you type straight to Python's `re` engine — it does no shell-style parsing. If you wrap the pattern in quotes (single or double), peekdocs literally searches for the quote character as part of the pattern, which almost never matches anything.

```
Correct in the GUI Regex field:    \b\d+\.\d+\.\d+\b
Wrong (looks for literal quotes):  "\b\d+\.\d+\.\d+\b"
```

Quotes are only needed when you type a regex on a **CLI**, where the shell would otherwise interpret special characters like `$`, `(`, `)`, `|` before peekdocs sees them:

```bash
peekdocs -x '\b\d+\.\d+\.\d+\b'      # POSIX shells (single quotes — safest)
peekdocs -x "\b\d+\.\d+\.\d+\b"      # CMD on Windows (double quotes work)
peekdocs -x '\b\d+\.\d+\.\d+\b'      # PowerShell (single quotes; see also the
                                     # PowerShell-vs-CMD entry above)
```

The shell strips the surrounding quotes; peekdocs receives the raw pattern.

---

**PowerShell rejects `--flag` arguments: "A positional parameter cannot be found that accepts argument '--check'"**

PowerShell treats `--` as its own end-of-options marker, so an argument like `--check` confuses the parser before peekdocs ever sees it. The error message is misleading — peekdocs isn't a PowerShell cmdlet, it's an external program; PowerShell is just over-eager. Three ways past it:

- Use the **`--%` stop-parsing token**, which tells PowerShell to pass everything that follows literally:
  ```powershell
  .\peekdocs-cli-windows.exe --% --check
  peekdocs --% --diff old.json new.json
  ```
- **Quote the flag**:
  ```powershell
  .\peekdocs-cli-windows.exe '--check'
  ```
- **Use Command Prompt instead of PowerShell** — `cmd.exe` doesn't have this quirk. Search "cmd" in the Start menu, hit Enter, and `--flag` works normally.

This is a general PowerShell issue, not a peekdocs bug — it affects any external CLI that uses double-dash flags (git, docker, kubectl, etc.).

---

**The standalone CLI exe flashes a terminal and disappears when double-clicked**

Expected behaviour, not a bug. `peekdocs-cli-windows.exe` is a command-line tool, not a GUI app. Double-clicking it:

1. Windows opens a fresh terminal to host the process,
2. peekdocs runs with no arguments — which prints the cheat-sheet banner,
3. peekdocs exits (it has nothing else to do),
4. Windows closes the terminal because the process is done.

To **actually use** the CLI exe, launch it from a Command Prompt or PowerShell window you already have open, passing real arguments:

```powershell
cd $env:USERPROFILE\Downloads
.\peekdocs-cli-windows.exe --check
.\peekdocs-cli-windows.exe budget                          # search current dir
.\peekdocs-cli-windows.exe budget revenue -a -r            # AND mode, recursive
.\peekdocs-cli-windows.exe -d C:\Users\me\Documents bowling
```

If you want the friendlier name `peekdocs`, rename the file once:

```powershell
Rename-Item $env:USERPROFILE\Downloads\peekdocs-cli-windows.exe peekdocs.exe
```

For a setup where `peekdocs` works from any folder without the `.\` prefix, copy the exe into a directory that's already on your PATH (e.g., `C:\Users\<you>\AppData\Local\Microsoft\WindowsApps\`).

The standalone GUI exe (`peekdocs-gui-windows.exe`) is a different story — double-clicking it is the *correct* way to launch a GUI.

---

**.rar files can't be searched in the standalone exe — "could not read NAME.rar (cannot find working tool)"**

RAR archive support relies on an external `unrar` binary which the standalone bundle does not include. (The unrar source has licensing restrictions that make it impractical to redistribute.) On Windows, the simplest install is **WinRAR** from [win-rar.com](https://www.win-rar.com/), which puts a working `unrar.exe` on your PATH. Reopen your terminal after install and peekdocs will read .rar files automatically — no peekdocs configuration needed.

If WinRAR isn't an option:

- **Extract the .rar contents first** (any extraction tool — 7-Zip, PeaZip, the Windows 11 built-in archive support for newer .rar versions) into a regular folder, then point peekdocs at that folder.
- **Use a pip / pipx install of peekdocs instead** and `pip install rarfile` — same root issue (RAR needs a sidecar tool) but with more control over what's bundled.

The error message is non-fatal: peekdocs logs the file to `peekdocs_errors.log` and continues with the rest of the corpus.

---

**.pst files can't be searched in the standalone Windows exe**

`libpff-python` (the library peekdocs uses for Outlook PST archives) is a C extension with no working Windows wheel — it requires a compiler toolchain to build and almost never succeeds on a typical Windows install. The standalone bundle on Windows therefore doesn't include it. peekdocs reports "PST support requires the libpff-python package" and skips the file.

Workarounds, in rough order of effort:

- **Convert the .pst to .mbox first.** Thunderbird's built-in "ImportExportTools NG" extension does this, as does the open-source [readpst](https://github.com/pst-format/libpst) utility. Point peekdocs at the resulting .mbox files — those work out of the box.
- **Use macOS or Linux for the PST search.** `pip install libpff-python` succeeds there, and the pipx-installed peekdocs reads .pst directly.
- **If you have the original .msg messages**, scan those — peekdocs reads .msg via the `extract-msg` library, which IS bundled in the standalone exe.

See also the [pre-existing PST troubleshooting entry](#pst-support-requires-the-libpff-python-package) earlier in this file for the pip-install case.

---

**Windows antivirus blocks peekdocs or quarantines report files**

Windows Defender or third-party antivirus may flag peekdocs's rapid file scanning as suspicious, quarantine report files immediately after creation, or block the `.peekdocs.db` index file.

- Add the search folder and Python's installation path to your antivirus exclusion list
- In Windows Security → Virus & threat protection → Manage settings → Exclusions, add the folder being searched
- If report files disappear after generation, check your antivirus quarantine

---

**Some files are being skipped (check peekdocs_errors.log)**

peekdocs automatically skips files over 100 MB to prevent slow searches and memory issues. Very large files — huge PDFs, massive spreadsheets, database exports, large email archives — can take minutes to parse and may exhaust available memory, causing the app to freeze or crash. When a file is skipped, `peekdocs_errors.log` records the file name, its size, and the current limit so you know exactly what was missed.

To change the limit:
- **GUI:** Open **Advanced Search Options** and change **Max File Size (MB)**. Set to 0 for no limit
- **CLI:** `peekdocs --config max_file_size_mb=200` (or 0 for no limit)

ZIP archives that would expand to over 500 MB are also skipped to protect against archive bombs (tiny ZIP files designed to expand to enormous sizes).

If you set the limit to 0 and a file causes a memory error, peekdocs catches it and logs the file without crashing — but the search will be slower and may use significant memory.

---

**Windows path length limit (260 characters) causes files to be skipped**

Deeply nested directories with long filenames may exceed Windows' default 260-character path limit, causing files to be silently skipped during recursive search.

- Enable long paths: run as Administrator: `reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled /t REG_DWORD /d 1 /f` and restart
- Alternatively, move files to a shorter base path

---

**Windows console shows garbled non-ASCII characters**

Search results with accented letters, CJK characters, or symbols display as garbled text in the legacy Windows console (cmd.exe).

- Run `chcp 65001` before running peekdocs to switch the console to UTF-8
- Or use Windows Terminal (included with Windows 11) which handles UTF-8 natively
- Setting `PYTHONIOENCODING=utf-8` as an environment variable also helps

---

**macOS Gatekeeper blocks Tesseract**

OCR with `-O` fails with "tesseract cannot be opened because the developer cannot be verified."

- Prefer installing via Homebrew: `brew install tesseract`
- For manually installed Tesseract: run `xattr -d com.apple.quarantine $(which tesseract)` to remove the quarantine flag
- Or go to System Settings → Privacy & Security and click "Allow Anyway" after the first blocked attempt

---

**Apple Silicon (M1/M2/M3) pip install fails with compilation errors**

`pip install git+https://github.com/exbuf/peekdocs.git` fails with build errors for PyMuPDF, rapidfuzz, or other C-extension packages on Apple Silicon Macs.

- Ensure you are using a native arm64 Python: `python3 -c "import platform; print(platform.machine())"` should print `arm64`
- Install Xcode Command Line Tools: `xcode-select --install`
- Update pip first: `pip install --upgrade pip` (newer pip finds pre-built wheels more reliably)
- Force pre-built wheels: `pip install --only-binary :all: pymupdf rapidfuzz`

---

**Homebrew Python vs system Python confusion (macOS)**

peekdocs is installed but `peekdocs` says "command not found", or it runs with the wrong Python.

- macOS ships a system Python at `/usr/bin/python3` but Homebrew installs its own at `/opt/homebrew/bin/python3` (Apple Silicon) or `/usr/local/bin/python3` (Intel)
- Check which Python you are using: `which python3`
- Ensure Homebrew's bin is in your PATH: add `export PATH="/opt/homebrew/bin:$PATH"` to `~/.zshrc`
- Install explicitly: `python3 -m pip install git+https://github.com/exbuf/peekdocs.git`

---

**GUI fails on headless Linux (no display server)**

Running `peekdocs-gui` on a Linux server or SSH session produces `TclError: no display name and no $DISPLAY environment variable`.

- Use the CLI (`peekdocs`) instead of the GUI on headless systems
- For remote GUI access, use SSH with X forwarding: `ssh -X user@host`
- Or set up a virtual framebuffer: `sudo apt install xvfb && xvfb-run peekdocs-gui`

---

**Missing Tkinter on Linux or macOS Homebrew Python**

`peekdocs-gui` fails with `ModuleNotFoundError: No module named '_tkinter'` even though customtkinter is installed.

Tkinter's C binding is a system / Homebrew dependency not included with pip:

- Ubuntu/Debian: `sudo apt install python3-tk`
- Fedora: `sudo dnf install python3-tkinter`
- Arch: `sudo pacman -S tk`
- macOS (Homebrew Python): `brew install python-tk@3.14` (match the version of your Homebrew `python@<version>`)
- macOS (python.org installer): Tkinter is already included — nothing to do
- If using pyenv: install `tk-dev` first, then rebuild Python: `sudo apt install tk-dev && pyenv install 3.12`

---

**GUI display issues on Linux with Wayland**

The GUI has rendering artifacts, blank areas, or input problems on modern Linux desktops using Wayland (GNOME 41+, Fedora, Ubuntu 22.04+).

- Force X11 backend: `GDK_BACKEND=x11 peekdocs-gui`
- Or log in using an "Xorg" or "GNOME on Xorg" session instead of the default Wayland session

---

**GUI text is too small or too large, or buttons overlap (high-DPI / display scaling)**

On 4K monitors, Retina displays, or systems with non-default display scaling, GUI text and buttons may appear too small, too large, or overlap each other.

**Try this first:** Use the **Text Size** dropdown on the bottom-right toolbar of the GUI. Choose Small, Normal, Large, or Extra Large. Normal works well on most screens. This setting is saved automatically and restored on next launch.

If the Text Size dropdown doesn't fully resolve the issue:

- Windows: right-click the Python executable → Properties → Compatibility → Change high DPI settings → Override high DPI scaling behavior (Application)
- Linux: set `TK_SCALING=2.0` as an environment variable before launching
- macOS: generally handled automatically, but mixed-DPI multi-monitor setups may have issues

---

**Scanned PDFs return no results (without OCR flag)**

PDFs that are scanned images (no selectable text layer) return zero matches in a normal search.

- Use the `-O` flag to enable OCR: `peekdocs -O search_term`
- Tesseract must be installed (see the OCR troubleshooting entry above)
- OCR is slower than text extraction — consider building an index with OCR: `peekdocs --index -O`

---

**Encrypted or password-protected PDFs produce no results**

Password-protected PDFs are processed without error but yield no matches because the content cannot be extracted.

- Remove PDF encryption before searching: `qpdf --decrypt input.pdf output.pdf` (requires the password)
- peekdocs does not currently support supplying PDF passwords
- The file appears in the "files searched" count but produces no matches — check `peekdocs_errors.log` for details

---

**Non-ASCII filenames cause errors on Linux**

Files with accented letters, Chinese/Japanese/Korean characters, or other non-ASCII characters in their names are skipped or cause errors.

- This typically happens when the system locale is set to `C` or `POSIX` (common in Docker containers and minimal server installations)
- Fix: `export LANG=en_US.UTF-8` (install the locale first if needed: `sudo apt install locales && sudo locale-gen en_US.UTF-8`)

---

**Search is very slow on network drives (SMB/NFS)**

peekdocs is unusably slow when searching files on a mapped network drive.

- Copy files to a local directory before searching — network latency multiplied by thousands of file operations creates massive cumulative delay
- If copying is not feasible, build the index locally after copying, then search with `--index-search`
- Use `-c 1` to avoid multiplying network I/O across multiple processes
- Do not place the `.peekdocs.db` index file on a network drive — SQLite does not officially support network filesystems

---

**"Too many open files" error on macOS or Linux**

peekdocs crashes with `OSError: [Errno 24] Too many open files` during large searches.

- Increase the file descriptor limit: run `ulimit -n 4096` before searching
- Use `-c 1` to reduce concurrent file opens
- For a permanent fix on macOS, see Apple's documentation on raising the `maxfiles` limit
- On Linux, edit `/etc/security/limits.conf` to increase the `nofile` limit

---

**"database is locked" error during indexing**

Building or refreshing the index fails with `sqlite3.OperationalError: database is locked`.

- Close all other peekdocs instances (CLI and GUI)
- If no other instances are running, a previous crash may have left stale lock files — delete `.peekdocs.db-wal` and `.peekdocs.db-shm` from the directory (use `ls -a` to see them)
- Then rebuild: `peekdocs --index-clear && peekdocs --index`

---

**pip install fails with C compiler errors**

`pip install git+https://github.com/exbuf/peekdocs.git` fails with "Microsoft Visual C++ 14.0 or greater is required" (Windows) or `gcc: error` (Linux) during installation of native extensions.

- Windows: install [Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- Linux: `sudo apt install build-essential python3-dev` (Ubuntu/Debian) or `sudo dnf install gcc python3-devel` (Fedora)
- macOS: `xcode-select --install`
- Upgrade pip first: `pip install --upgrade pip` — newer pip is better at finding pre-built wheels that avoid compilation entirely

---

**openpyxl warnings flood the console when searching Excel files**

Searching directories with many `.xlsx` files produces repeated `UserWarning: Data Validation extension not supported` messages.

- Upgrade openpyxl: `pip install --upgrade openpyxl`
- If warnings persist, set `PYTHONWARNINGS=ignore` as an environment variable before running peekdocs
- These warnings do not affect search results — they are cosmetic only

---

**"peekdocs: command not found" after activating the virtual environment**

You activated the virtual environment but `peekdocs` still isn't recognized. This usually means the activation didn't take effect, or peekdocs wasn't installed in that environment.

- Verify the venv is active: your terminal prompt should show `(venv)` at the beginning. If it doesn't, activation didn't work
- Make sure you're in the right directory: `cd` to the peekdocs project folder first, then run `source venv/bin/activate` (Mac/Linux) or `venv\Scripts\activate` (Windows)
- On Windows, if `activate` is blocked by execution policy, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` first
- After activating, reinstall: `pip install -e .`
- Verify: `which peekdocs` (Mac/Linux) or `where peekdocs` (Windows) should show a path inside the venv folder

If you don't want to activate a virtual environment every time, consider switching to [pipx installation](../README.md#option-a-quick-install-with-pipx-recommended) — it makes `peekdocs` available globally with no activation step.

---

**Which pip should I use? (pip vs pip3 vs python -m pip)**

Running `pip install` installs into one Python, but `peekdocs` runs with a different Python — causing "ModuleNotFoundError" even though pip says it's installed.

- **Safest option:** Always use `python -m pip install` (or `python3 -m pip install`) instead of bare `pip`. This guarantees pip installs into the same Python that will run peekdocs
- **In a virtual environment:** Once the venv is activated, `pip` and `python` always point to the right place — bare `pip install` is fine
- **Check which pip you're using:** `pip --version` shows the Python path it installs into. Compare with `python3 --version` to make sure they match
- **Multiple Pythons installed?** macOS often has system Python, Homebrew Python, and pyenv Python. Use `which python3` and `which pip3` to see which ones are active. If they point to different installations, use `python3 -m pip` to stay consistent

---

**pip or pipx can't download packages (corporate firewall or proxy)**

Installation fails with connection timeouts, SSL certificate errors, or "Could not find a version that satisfies the requirement."

- **Behind a proxy:** Set the proxy for pip: `pip install --proxy http://proxy.company.com:8080 peekdocs`
- **SSL certificate issues:** If your company uses a custom SSL certificate, tell pip to trust it: `pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org peekdocs`
- **No internet access at all:** Use the [ZIP download](../README.md#option-c-manual-install-no-git-no-sign-up) method — download the ZIP on a machine with internet, transfer it to the target machine, and install from the local folder with `pip install -e .`
- **pipx behind a proxy:** pipx uses pip internally, so set the `HTTP_PROXY` and `HTTPS_PROXY` environment variables before running `pipx install`
