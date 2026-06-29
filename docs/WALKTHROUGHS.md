# peekdocs — Labeled Walkthroughs

Annotated screenshots that pair with descriptions of the moment captured — useful for slowing down what the demo videos in the [README's Screenshots section](../README.md#screenshots) show in motion, or for readers who'd rather scan stills than watch a clip.

#### 1. Same search, three interfaces — plus the report

One `TODO` search shown across the three interfaces peekdocs ships (GUI, CLI, Python API), followed by the highlighted Word report a standard search auto-produces alongside the on-screen results.

**(a) GUI — main page searching for `TODO` across a source tree.** Index-backed search returned 69 matches in 54 files (out of 442 files / 806 MB scanned) in 0.51 seconds. Every match is highlighted in yellow with surrounding context.

![Main page searching for TODO](images/screenshot-main-page-TODO.png)

> **Tip — can't find a file you expected?** The Results Preview is a scrollable window into the matched set, ordered alphabetically by file path. Broad searches (OR mode with a short common word like `dr` or `id`) can return hundreds of files, so the specific one you were looking for may be lower in the list. Click the **Matched File(s)** link on the status line for the complete list, or open the `.docx` / `.html` report for every match across every file. The simplest narrowing is **quoted phrase search** — type `"Dr. Bowling"` in the search bar for an exact-phrase match instead of OR'ing each word. See [the FAQ](TROUBLESHOOTING.md) for AND / proximity / expression variants.

**(b) CLI — same search from the terminal.** Same folder, same Whole Word + indexed mode, same 69 matches in 54 files. Quiet output (`-qq`) keeps the screenshot to the headline numbers; stderr redirected so optional-format warnings don't clutter the frame. The 0.50-second elapsed time is the *second* run — the first search took about 44 seconds while peekdocs built the index for this folder. Every subsequent search uses the warm index and runs in milliseconds (see [First-run timing](../README.md#first-run-timing-and-the-banner-notice) for details).

![CLI searching for TODO](images/screenshot-CLI-TODO.png)

**(c) Python API — same search from a script or notebook.** The same engine is exposed as a library: `from peekdocs import search` returns a typed `SearchResult` of `SearchMatch` dataclasses (`file_dir`, `filename`, `line_num`, `text`) — no parsing strings out of CLI output. Drop it into a Jupyter notebook, a script, or any Python program. Same index, same matches; the in-process call also runs faster than the CLI (~`0.3`-second vs. `0.50`) because there's no subprocess startup cost.

![peekdocs Python API in a Jupyter notebook](images/screenshot-python-api.png)

**(d) Word report — the shareable artifact.** Every Standard Search produces `peekdocs_standard_results.docx` by default alongside the always-written .txt (uncheck the **DOCX** checkbox in Advanced Search Options, or pass `--no-docx` on the CLI, to skip the Word report) — yellow-highlighted matches, file paths as section headings, line numbers, surrounding context preserved. Hand it to a colleague who's never heard of peekdocs and they immediately understand what's in it. Opens in whatever app you've set as your OS default for `.docx` files — the screenshot below is [LibreOffice](https://www.libreoffice.org/download/download-libreoffice/) (free). Optional CSV, JSON, PDF, and HTML outputs are also available (checkboxes under Advanced Search Options) — these apply to Standard Search only. Search Suites have their own format picker inside the Suites popup, and Regex Search always writes just TXT and DOCX.

![TODO results opened in LibreOffice](images/screenshot-TODO-LibreOffice.png)

#### 2. Advanced Search Options — every option in one GUI panel

The CLI flags the README mentions — `--regex`, `--fuzzy`, `--whole-word`, `--ocr`, `--exclude`, `-t` (file types), `--range`, `--max-file-size`, `--output-dir`, `--timestamp`, CSV/JSON/PDF/HTML output, and so on — every one of them has a checkbox or field in the **Advanced Search Options** panel under the main search bar. Click the panel header on the main page to expand it. As the note at the top says: *"All searches are based on this screen and the Search Terms on the main screen. Your selections take effect immediately on the next search."* **Save As Defaults** persists the current configuration to `~/.peekdocsrc` for the next session; **Restore Factory Settings** clears it. Hover any control for a tooltip describing what it does.

![Advanced Search Options panel](images/screenshot-advanced-screen.png)

#### 3. Regex Search — full workflow

A four-shot tour through the Regex Search popup using a saved collection of 10 common code patterns (URL, IPv4 address, Local port, ISO date, UPPER_CASE constant, Python decorator, Email, Semver version, UUID, Markdown link).

**(a) Setup.** All 10 patterns enabled, recursive search across the same 452-file folder.

![Regex Search setup](images/screenshot-regex-search.png)

**(b) Results.** 1,402,532 matches across 452 files in 20.7 seconds, broken down per pattern. Each row has a **View Files** button to drill into that pattern's hits.

![Regex Search results](images/screenshot-regex-search-results.png)

**(c) Drilling in.** Clicking **View Files** on the "Local port" row (above) narrows from millions of matches down to the one file containing `localhost:<port>` — a `Dockerfile`, with 2 matches on lines 19 and 25.

![Files containing Local port matches](images/screenshot-regex-localport.png)

**(d) Context view.** Clicking **View Text (with line numbers)** opens the file with matches highlighted in yellow — here, `localhost:5432` and `localhost:8080` show up as hardcoded values that should probably come from environment variables. Reviewable in context, no leaving the GUI.

![Dockerfile text view with highlighted matches](images/screenshot-regex-textview-dockerfile.png)

#### 4. Search Suites — recurring multi-search workflows

Where Regex Collections run many *patterns* at once, Search Suites run many *complete saved Standard Searches* at once — each with its own settings (AND/OR, Whole Word, Recursive, etc.). Demo: a "Code hygiene" suite that runs five common pre-commit checks in one click.

**(a) Setup.** Five saved searches (`TODO`, `FIXME`, `HACK` with Whole Word on; `print(` and `console.log(` with Whole Word off — same kit, different option per search). Run order is top-to-bottom; the Up/Down buttons reorder. HTML output added to the always-on TXT and DOCX defaults.

![Search Suites setup](images/screenshot-searchsuite-setup.png)

**(b) Results on the main page.** 237 total matches across 177 files in 7.1 seconds. The Section summary at the top of the combined report lists every search's match count up front — no scrolling through 69 TODO matches to discover there were 7 `console.log` hits at the bottom.

![Suite results in the main-page preview](images/screenshot-searchsuite-result-mainpage.png)

**(c) HTML report opened in the browser.** Same Section summary at the top, but each entry is a clickable anchor link that jumps to that section. Yellow match highlighting throughout. The report is a single self-contained file on disk — nothing uploaded, nothing requires the GUI to view.

![Suite HTML report](images/screenshot-searchsuite-result-html.png)

**What this demo proves**, in three shots:

- Same source tree, **five distinct questions** answered in one click.
- **Per-search settings** — three searches with Whole Word on, two with it off. A regex collection couldn't express that mix as cleanly.
- **Combined report** with sections per saved search, plus the Section summary up front so the smallest result count is as visible as the largest.
- **Real workflow** — every developer recognizes this as their actual pre-commit / pre-PR sanity check, not a contrived demo.

#### 5. Diff Snapshots — what changed between two scans

For users who want to know not just *what's in my documents* but *what changed since last time*: the **Diff Snapshots** tool compares two peekdocs JSON snapshots and reports what's NEW, CHANGED, UNCHANGED, or REMOVED. Useful for periodic source-tree scans and any "is the situation better or worse than last week?" question.

**(a) Finding it.** Tools menu in the lower-right corner of the main page. Lists every Tools-menu feature in plain English; **Diff Snapshots** is between **Bookmarks** and **Indexes**.

![Tools menu](images/screenshot-tools-menu.png)

<p align="center"><b>Tools</b></p>

**(b) Comparing two snapshots.** Picked two snapshots of a `TODO` search captured before and after a small code change: one new file gained a TODO, one existing file went from 1 to 2 TODOs. The result pane shows the three distinct categories in color (green NEW, orange CHANGED, muted UNCHANGED summary) plus a red status line at the top — *"Actionable changes: 1 new, 1 changed, 0 modified."*

![Diff Snapshots popup with results](images/screenshot-diff-snapshots.png)

Both snapshot JSON files used in this demo are checked into `docs/images/` (`peekdocs-snapshot-todo-before.json` and `peekdocs-snapshot-todo-after.json`) so a reader can download them and try the diff themselves. Snapshots were generated with:

```bash
peekdocs TODO -W -r --hash --stdout > peekdocs-snapshot-todo-before.json
# ... time passes, files change ...
peekdocs TODO -W -r --hash --stdout > peekdocs-snapshot-todo-after.json
peekdocs --diff peekdocs-snapshot-todo-before.json peekdocs-snapshot-todo-after.json
```

**To preserve snapshots across recurring runs** (so you can diff today's against last week's), either redirect each run to a unique filename — `> snapshot_$(date +%F).json` in a POSIX shell, or the equivalent date-stamped form in PowerShell — or add `--timestamp -o json` so peekdocs appends `_YYYYMMDD_HHMMSS` to its output filenames automatically. Without one of those, each run overwrites the previous JSON and there's nothing to diff against. The **Schedule Search** dialog enables `--timestamp` by default for exactly this reason.

The same diff is also available as a CLI command — see [Automation and IT Use → Diff between runs](USER_GUIDE.md#diff-between-runs) in the User Guide for the scheduled-scan use case.

#### 6. Schedule Search — generate a ready-to-paste cron / Task Scheduler command

For recurring scans (nightly source-tree sweeps, weekly code-hygiene runs, monthly project sweeps), **Tools → Schedule Search** generates the scheduler command for you. Pick a Search Suite or Regex Collection, choose a folder, set the frequency (daily, weekly, monthly), and the dialog writes a complete `cd … && peekdocs …` one-liner with the right flags already in place — including `--timestamp` so each run's report is preserved instead of overwritten. Copy to Clipboard, then paste into `crontab -e` (Mac/Linux) or Task Scheduler (Windows). Step-by-step instructions for both Mac/Linux and Windows are shown right below the command box, with your current OS's steps listed first.

![Schedule Search dialog generating a cron command](images/screenshot-schedule-search.png)

#### 7. `peekdocs --check` — operational health probe

For IT staff, scheduled jobs, and anyone wrapping peekdocs in automation: `peekdocs --check` verifies the installation in one shot. Reports the peekdocs version, Python version, OS, every required and optional dependency with its installed version, Tesseract (the OCR engine), SQLite version, and free disk space. Exit code 0 = everything healthy, exit code 2 = something missing. Run it once after install and at the start of any deployment script — and at the top of any scheduled command from the dialog above to fail fast on a broken environment.

![peekdocs --check output](images/screenshot-check-output.png)
