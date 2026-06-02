<h1 align="center">👀 peekdocs</h1>

<p align="center">
  <a href="https://github.com/exbuf/peekdocs/actions/workflows/test.yml"><img src="https://github.com/exbuf/peekdocs/actions/workflows/test.yml/badge.svg" alt="Tests"></a>&nbsp;&nbsp;
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python 3.10+"></a>&nbsp;&nbsp;
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT"></a>
</p>

peekdocs is a local document search and analysis workbench for Windows, macOS, and Linux, available as a point-and-click GUI, a command-line CLI, and a Python API. Search across 100+ file types—including PDFs, Office documents, email archives, ZIP/7z files, source code, and scanned documents via OCR—using keyword, Boolean, fuzzy, wildcard, proximity, range, and advanced regex searches. Generate yellow-highlighted reports, automate recurring searches, perform batch analysis, and save reusable search profiles. Free and open-source under the MIT License.

Built for people who prefer local, transparent, deterministic tools.

**Typical workflow:** Search 50,000 mixed-format documents → inspect matches in the Results Preview → generate a highlighted DOCX report → save the search → add it to a Search Suite → schedule it weekly.

*All steps are GUI-accessible from the main screen, the **Search Suites** popup (opened by the green button next to Run Standard Search), and **Tools → Schedule Search** — the last one generates a cron / Task Scheduler command for you to paste rather than installing the schedule for you.*

## Feature Highlights

A workbench for document collections: search them, characterize them through built-in analysis tools (duplicates, inventories, age distribution, change tracking), produce highlighted reports you can save or share, and drive it all through whichever interface fits — GUI, CLI, or Python API.

- **100+ file types in one query** — Word, PDF, Excel, email, source code, archives, and more — searched simultaneously
- **Reports for humans, output for machines** — .docx, .html, and .pdf reports with matches highlighted in yellow alongside their surrounding paragraphs or lines; .csv, .json, and .txt output for downstream tooling
- **Read-only and transparent** — peekdocs runs locally and never modifies, moves, or deletes your files. The Tools menu lists every file peekdocs has written (results, reports, indexes, saved searches) and lets you delete them in one click.
- **OCR** — search scanned PDFs and images. Tesseract (free, open-source) must be installed separately — but once it is, peekdocs handles the rest. *Accuracy depends on source quality: clean printed pages work well; handwriting, low-resolution scans, and complex layouts may extract poorly.*
- **Flexible search modes** — Boolean, fuzzy, wildcard, regex, proximity, inverse, whole-word, range, AND/OR, and more
- **Search Wizard** — 20 pre-built search-type forms (keywords, Boolean, fuzzy, proximity, dollar range, date range, phone, email, and more) plus a regex pattern builder with 35 named patterns across 6 categories — no syntax to memorize
- **Regex Search** — run up to 10 named regex patterns per collection, with unlimited saved collections. Switch between collections for different tasks (e.g., "code patterns", "log analysis", "invoice extraction") — or run any collection from Python via `run_regex_collection()`
- **Search Suites** — group saved searches and run them all with one click — or from Python via `run_suite()`
- **Repeatable workflows** — Saved Searches, Search Suites, Regex Collections, Schedule Search, Search History, and Diff Snapshots compose into a workflow system: define a search by name; group related searches into a suite; reuse pattern sets via Regex Collections; schedule a suite to run on a cadence; audit every run via Search History; compare today's run against last week's via Diff Snapshots.
- **File analysis built in** — Collection Summary, Duplicate Finder, Empty Files, File Age Distribution, File Inventory, Large Files, Protected Files, Recent Changes, and Unsearchable Files. Plus Bookmarks and Search History for recurring workflows.
- **Three interfaces, one engine** — same search engine and same behavior across the GUI, CLI, and Python API. Search Suites, Regex Collections, saved searches, and report formats are byte-identical regardless of which surface you use. Run a search by hand from the GUI today; schedule the identical command via cron / Task Scheduler tonight; integrate the same logic into a Python script tomorrow.
- **Scriptable, deterministic, integrable** — Python API, JSON / NDJSON output, meaningful exit codes, Diff Snapshots, Schedule Search, and a stable CLI surface for cron jobs, CI pipelines, log shippers, and shell pipelines. Same inputs produce byte-identical outputs every time — the same search produces the same results today, tomorrow, and a year from now.
- **Cross-platform** — same features on macOS, Windows, and Linux

&nbsp;

> **Local-only by design.** No network calls, no telemetry, no cloud, no account. peekdocs runs entirely on your machine with your normal user permissions — no admin or root required, and it works fine on air-gapped systems with no internet connection.

&nbsp;

> **Why local?** Most people have at least some documents they would rather not hand to a third party — drafts, work-in-progress, personal correspondence, financial paperwork. peekdocs is local-only because that's the only way the answer to "where does this go?" stays "nowhere — it stayed on my machine." The tradeoff is real: peekdocs doesn't summarize, doesn't answer questions about your documents, doesn't infer meaning. Those are jobs cloud AI tools do well; peekdocs is for finding exact text in a lot of files, repeatably, on your own machine.

&nbsp;

> **Transparency over magic.** If a file wasn't searched, peekdocs tells you why. If OCR couldn't extract text, you'll know. If a report was created, you'll know where it is. peekdocs favors observable behavior over hidden processing.

&nbsp;

<p align="center"><b>Free &nbsp;&nbsp;·&nbsp;&nbsp; Open-Source (MIT License) &nbsp;&nbsp;·&nbsp;&nbsp; No Cloud &nbsp;&nbsp;·&nbsp;&nbsp; Private &nbsp;&nbsp;·&nbsp;&nbsp; Easy to Use</b></p>
<p align="center"><b>Windows &nbsp;&nbsp;·&nbsp;&nbsp; macOS &nbsp;&nbsp;·&nbsp;&nbsp; Linux &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp; GUI &nbsp;&nbsp;·&nbsp;&nbsp; CLI &nbsp;&nbsp;·&nbsp;&nbsp; Python API</b></p>

&nbsp;

**Two ways to install:**
1. Developers with Python: `pipx install --force git+https://github.com/exbuf/peekdocs.git` (below)
   - **Windows tip:** if this fails with an SSL / SNI / certificate error in **Command Prompt**, try the same command in **PowerShell** instead — the two terminals can route through different Python installs. See [docs/INSTALLATION.md → Windows cmd.exe SSL / SNI / certificate errors](docs/INSTALLATION.md#windows-cmd-ssl) for the diagnosis and fix.
2. Everyone else: [download the standalone app](#option-a-standalone-download-recommended-for-most-users) — no Python needed, just download and run

A single install gets you everything — the GUI, the CLI, and the Python API. Run the commands below in a terminal (macOS / Linux) or Command Prompt / PowerShell (Windows):

```bash
# Install or upgrade (requires Python 3.10+)
pipx install --force git+https://github.com/exbuf/peekdocs.git    # recommended (isolated)
# — or —
pip install --upgrade git+https://github.com/exbuf/peekdocs.git   # if you prefer pip

# The same command works for first install AND for upgrade — re-run it
# whenever you want the latest commit. The --force / --upgrade flag is
# important: without it, pipx silently skips re-install if peekdocs is
# already present and pip leaves the existing version in place.

# GUI prerequisite (only if you'll use peekdocs-gui):
# macOS Homebrew Python: brew install python-tk@3.14   # match your python@<version>
# Linux:                 sudo apt install python3-tk
# Windows / python.org Mac installer: already included — nothing to do

# Uninstall (your settings in ~/.peekdocsrc and folder indexes are preserved)
pipx uninstall peekdocs
# — or —
pip uninstall peekdocs

# Search from the terminal
peekdocs "budget" ~/Documents
# Found 47 match(es) in 12 file(s). Files searched: 238 (142.50 MB).
#   2024_tax_return_summary.pdf: 8
#   quarterly_report_Q1.docx: 6
#   vendor_contract_2024.pdf: 5  ...

# Search with the GUI
peekdocs-gui

# Search from Python API
from peekdocs import search
results = search(["budget"], directory="~/Documents")
for match in results.matches:
    print(f"{match.filename}:{match.line_num} {match.text}")
```

## Contents

- [Feature Highlights](#feature-highlights)
- [CLI at a Glance](#cli-at-a-glance)
- [Screenshots](#screenshots)
- [Who Is It For?](#who-is-it-for)
- [Features](#features)
- [Supported File Types](#supported-file-types)
- [Installation](#installation)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Why peekdocs?](#why-peekdocs)
- [What peekdocs Is Not](#what-peekdocs-is-not)
- [Performance](#performance)
- [Platform Notes](#platform-notes)
- [Preparing Documents](#preparing-your-documents-for-searching)
- [Questions and troubleshooting](#questions-and-troubleshooting)
- [Glossary](#glossary)
- [For IT and Security Teams](#for-it-and-security-teams)
- [Testing](#testing)
- [Contributing](#contributing)
- [Author](#author)
- [Disclaimer](#disclaimer)
- [License](#license)

## CLI at a Glance

```bash
# Recursive search for "budget"
peekdocs -r budget

# Regex pattern, piped through jq for the match count
peekdocs --stdout -x "\d{3}-\d{4}" | jq '.matches_found'

# Run a saved Search Suite by name
peekdocs --suite "Code hygiene"
```

`peekdocs -h` shows every flag, file type, and regex pattern. The [User Guide](docs/USER_GUIDE.md) covers the CLI in full.

## Screenshots

*The examples below lean toward source-code use cases — searching for `TODO`, regex patterns for URLs / UUIDs / version strings, and so on. That bias is deliberate: developers and Python users are the most likely first adopters since they're the ones browsing GitHub and PyPI for a tool like this. peekdocs works equally well on personal documents, research archives, legal filings, scanned receipts, and anything else made of text — the screenshots just happen to showcase the audience most likely to be reading them.*

#### 1. Same search, three interfaces — plus the report

One `TODO` search shown across the three interfaces peekdocs ships (GUI, CLI, Python API), followed by the highlighted Word report a standard search auto-produces alongside the on-screen results.

**(a) GUI — main page searching for `TODO` across a source tree.** Index-backed search returned 69 matches in 54 files (out of 449 files / 806 MB scanned) in 0.59 seconds. Every match is highlighted in yellow with surrounding context.

![Main page searching for TODO](docs/images/screenshot-main-page-TODO.png)

> **Tip — can't find a file you expected?** The Results Preview is a scrollable window into the matched set, ordered alphabetically by file path. Broad searches (OR mode with a short common word like `dr` or `id`) can return hundreds of files, so the specific one you were looking for may be lower in the list. Click the **Matched File(s)** link on the status line for the complete list, or open the `.docx` / `.html` report for every match across every file. The simplest narrowing is **quoted phrase search** — type `"Dr. Bowling"` in the search bar for an exact-phrase match instead of OR'ing each word. See [the FAQ](docs/TROUBLESHOOTING.md) for AND / proximity / expression variants.

**(b) CLI — same search from the terminal.** Same folder, same Whole Word + indexed mode, same 69 matches in 54 files. Quiet output (`-qq`) keeps the screenshot to the headline numbers; stderr redirected so optional-format warnings don't clutter the frame. The 0.40-second elapsed time is the *second* run — the first search took about 44 seconds while peekdocs built the index for this folder. Every subsequent search uses the warm index and runs in milliseconds (see [First-run timing](#first-run-timing-and-the-banner-notice) for details).

![CLI searching for TODO](docs/images/screenshot-CLI-TODO.png)

**(c) Python API — same search from a script or notebook.** The same engine is exposed as a library: `from peekdocs import search` returns a typed `SearchResult` of `SearchMatch` dataclasses (`file_dir`, `filename`, `line_num`, `text`) — no parsing strings out of CLI output. Drop it into a Jupyter notebook, a script, or any Python program. Same index, same `0.3`-second result.

![peekdocs Python API in a Jupyter notebook](docs/images/screenshot-python-api.png)

**(d) Word report — the shareable artifact.** Every search automatically produces `peekdocs_standard_results.docx` alongside the .txt — yellow-highlighted matches, file paths as section headings, line numbers, surrounding context preserved. Hand it to a colleague who's never heard of peekdocs and they immediately understand what's in it. Opens in Microsoft Word, [LibreOffice](https://www.libreoffice.org/download/download-libreoffice/) (free), Apple Pages, or any word processor — the screenshot below is LibreOffice. Optional CSV, JSON, PDF, and HTML outputs are also available (checkboxes under Advanced Search Options).

![TODO results opened in LibreOffice](docs/images/screenshot-TODO-LibreOffice.png)

#### 2. Advanced Search Options — every option in one GUI panel

The CLI flags this README mentions — `--regex`, `--fuzzy`, `--whole-word`, `--ocr`, `--exclude`, `-t` (file types), `--range`, `--max-file-size`, `--output-dir`, `--timestamp`, CSV/JSON/PDF/HTML output, and so on — every one of them has a checkbox or field in the **Advanced Search Options** panel under the main search bar. Click the panel header on the main page to expand it. As the note at the top says: *"All searches are based on this screen and the Search Terms on the main screen. Your selections take effect immediately on the next search."* **Save As Defaults** persists the current configuration to `~/.peekdocsrc` for the next session; **Restore Factory Settings** clears it. Hover any control for a tooltip describing what it does.

![Advanced Search Options panel](docs/images/screenshot-advanced-screen.png)

#### 3. Regex Search — full workflow

A four-shot tour through the Regex Search popup using a saved collection of 10 common code patterns (URL, IPv4 address, Local port, ISO date, UPPER_CASE constant, Python decorator, Email, Semver version, UUID, Markdown link).

**(a) Setup.** All 10 patterns enabled, recursive search across the same 452-file folder.

![Regex Search setup](docs/images/screenshot-regex-search.png)

**(b) Results.** 1,402,532 matches across 452 files in 20.7 seconds, broken down per pattern. Each row has a **View Files** button to drill into that pattern's hits.

![Regex Search results](docs/images/screenshot-regex-search-results.png)

**(c) Drilling in.** Clicking **View Files** on the "Local port" row (above) narrows from millions of matches down to the one file containing `localhost:<port>` — a `Dockerfile`, with 2 matches on lines 19 and 25.

![Files containing Local port matches](docs/images/screenshot-regex-localport.png)

**(d) Context view.** Clicking **View Text (with line numbers)** opens the file with matches highlighted in yellow — here, `localhost:5432` and `localhost:8080` show up as hardcoded values that should probably come from environment variables. Reviewable in context, no leaving the GUI.

![Dockerfile text view with highlighted matches](docs/images/screenshot-regex-textview-dockerfile.png)

#### 4. Search Suites — recurring multi-search workflows

Where Regex Collections run many *patterns* at once, Search Suites run many *complete saved Standard Searches* at once — each with its own settings (AND/OR, Whole Word, Recursive, etc.). Demo: a "Code hygiene" suite that runs five common pre-commit checks in one click.

**(a) Setup.** Five saved searches (`TODO`, `FIXME`, `HACK` with Whole Word on; `print(` and `console.log(` with Whole Word off — same kit, different option per search). Run order is top-to-bottom; the Up/Down buttons reorder. HTML output added to the always-on TXT and DOCX defaults.

![Search Suites setup](docs/images/screenshot-searchsuite-setup.png)

**(b) Results on the main page.** 237 total matches across 177 files in 7.1 seconds. The Section summary at the top of the combined report lists every search's match count up front — no scrolling through 69 TODO matches to discover there were 7 `console.log` hits at the bottom.

![Suite results in the main-page preview](docs/images/screenshot-searchsuite-result-mainpage.png)

**(c) HTML report opened in the browser.** Same Section summary at the top, but each entry is a clickable anchor link that jumps to that section. Yellow match highlighting throughout. The report is a single self-contained file on disk — nothing uploaded, nothing requires the GUI to view.

![Suite HTML report](docs/images/screenshot-searchsuite-result-html.png)

**What this demo proves**, in three shots:

- Same source tree, **five distinct questions** answered in one click.
- **Per-search settings** — three searches with Whole Word on, two with it off. A regex collection couldn't express that mix as cleanly.
- **Combined report** with sections per saved search, plus the Section summary up front so the smallest result count is as visible as the largest.
- **Real workflow** — every developer recognizes this as their actual pre-commit / pre-PR sanity check, not a contrived demo.

#### 5. Diff Snapshots — what changed between two scans

For users who want to know not just *what's in my documents* but *what changed since last time*: the **Diff Snapshots** tool compares two peekdocs JSON snapshots and reports what's NEW, CHANGED, UNCHANGED, or REMOVED. Useful for periodic source-tree scans, weekly compliance reviews, and any "is the situation better or worse than last week?" question.

**(a) Finding it.** Tools menu in the lower-right corner of the main page. Lists every available power-user feature in plain English; **Diff Snapshots** is between **Bookmarks** and **Indexes**.

![Tools menu](docs/images/screenshot-tools-menu.png)

<p align="center"><b>Tools</b></p>

**(b) Comparing two snapshots.** Picked two snapshots of a `TODO` search captured before and after a small code change: one new file gained a TODO, one existing file went from 1 to 2 TODOs. The result pane shows the three distinct categories in color (green NEW, orange CHANGED, muted UNCHANGED summary) plus a red status line at the top — *"Actionable changes: 1 new, 1 changed, 0 modified."*

![Diff Snapshots popup with results](docs/images/screenshot-diff-snapshots.png)

Both snapshot JSON files used in this demo are checked into `docs/images/` (`peekdocs-snapshot-todo-before.json` and `peekdocs-snapshot-todo-after.json`) so a reader can download them and try the diff themselves. Snapshots were generated with:

```bash
peekdocs TODO -W -r --hash --stdout > peekdocs-snapshot-todo-before.json
# ... time passes, files change ...
peekdocs TODO -W -r --hash --stdout > peekdocs-snapshot-todo-after.json
peekdocs --diff peekdocs-snapshot-todo-before.json peekdocs-snapshot-todo-after.json
```

The same diff is also available as a CLI command — see [Automation and IT Use → Diff between runs](docs/USER_GUIDE.md#diff-between-runs) in the User Guide for the scheduled-scan use case.

#### 6. Schedule Search — generate a ready-to-paste cron / Task Scheduler command

For recurring scans (nightly source-tree audits, weekly code-hygiene runs, monthly project reviews), **Tools → Schedule Search** generates the scheduler command for you. Pick a Search Suite or Regex Collection, choose a folder, set the frequency (daily, weekly, monthly), and the dialog writes a complete `cd … && peekdocs …` one-liner with the right flags already in place — including `--timestamp` so each run's report is preserved instead of overwritten. Copy to Clipboard, then paste into `crontab -e` (Mac/Linux) or Task Scheduler (Windows). Step-by-step instructions for both Mac/Linux and Windows are shown right below the command box, with your current OS's steps listed first.

![Schedule Search dialog generating a cron command](docs/images/screenshot-schedule-search.png)

#### 7. `peekdocs --check` — operational health probe

For IT staff, scheduled jobs, and anyone wrapping peekdocs in automation: `peekdocs --check` verifies the installation in one shot. Reports the peekdocs version, Python version, OS, every required and optional dependency with its installed version, Tesseract (the OCR engine), SQLite version, and free disk space. Exit code 0 = everything healthy, exit code 2 = something missing. Run it once after install and at the start of any deployment script — and at the top of any scheduled command from the dialog above to fail fast on a broken environment.

![peekdocs --check output](docs/images/screenshot-check-output.png)

Most users never leave the search bar. Power users can go deeper with regex, Boolean logic, range queries, fuzzy matching, wildcards, proximity search, a command-line interface, and a Python API.

Searches text in any language (Unicode-based; see [Multilingual notes](docs/USER_GUIDE.md#multilingual-support) for caveats). Runs on Windows, macOS, and Linux. No fees, no subscriptions, no cloud. Everything stays on your computer. Nothing is uploaded anywhere. Your files are not altered or deleted. Free and open-source.

**[See peekdocs in action →](https://robertdschoening.com/peekdocs)**

## Who Is It For?

**You have files. You need to find something in them.**

peekdocs is built to do exactly that across many kinds of files at once — Word, PDF, Excel, email, scanned documents, archives, and 100+ more — entirely on your own computer.

**A few examples of what people could do with it:**

- **Home user** — Find a tax document from any of the last seven years across mixed folders.
- **Office worker** — Find all invoices over $10,000 from 2024.
- **IT consultant** — Search 50,000 client documents for a set of terms.
- **Sysadmin** — Search 20 GB of log files for a request ID across mixed archives.
- **Developer** — Run a regex collection against a source tree and generate JSON.
- **Engineer** — Search 200 datasheets for a part number across PDFs and scanned drawings.
- **Researcher** — Search 3,000 PDFs and export highlighted results.
- **Small business owner** — Find vendor contracts expiring in the next 90 days.

The sections below describe who finds it most useful and why.

### Home users and individuals

peekdocs works just as well on personal documents as it does on professional ones. Most people accumulate years of digital files — scanned forms, insurance documents, school papers, family correspondence, statements, warranties, e-books, downloaded receipts — spread across folders, drives, and cloud backups. peekdocs searches all of it locally with whatever words come to mind: a vendor name, a policy number, a year, a phrase from an old letter. Nothing is uploaded; nothing is sent anywhere; the search runs on your computer and the results stay there.

No command-line experience required. The GUI handles everything with a folder picker, a search box, and a Run button — no terminal, no flags, no syntax to learn.

### Core technical users

Developers, sysadmins, engineers, and technical writers — people who work with the tool from a terminal, automate it, or integrate it into pipelines.

| Who | Why they care | What they do with it |
|-----|--------------|---------------------|
| **Developers and technical power users** | Integrate document search into scripts and CI pipelines with CLI, JSON output, Python API, and regex collections | Search source trees for patterns, analyze logs, scan repos for TODO/FIXME, build automation scripts, generate machine-readable reports |
| **Engineers** | Search across datasheets, specs, and engineering files, with highlighted reports for design reviews | Search SPICE netlists, Verilog/VHDL, DXF, MATLAB files alongside PDFs, test reports, maintenance records, and standards references |
| **Technical writers and documentation teams** | Catch inconsistencies across large documentation sets using fuzzy matching, regex workflows, and recursive analysis | Find inconsistent terminology, review documentation trees, audit references across manuals, search exported HTML/Markdown/DOCX collections |

### System administrators and IT staff at small-to-mid-sized organizations

peekdocs is useful for solo IT professionals and small teams who need to search large document collections quickly across mixed Mac, Windows, and Linux environments. Common scenarios include independent IT consultants visiting multiple client sites, [MSP technicians](docs/GLOSSARY.md), financial or accounting offices, school districts or municipal offices, and technical staff managing document-heavy environments.

The common thread: one person owns the problem end-to-end, needs fast local document discovery with exportable reports, and prefers a privacy-first tool that runs entirely offline. Users can build their own search patterns (including regex) for whatever content matters to them.

See [Automation and IT Use](docs/USER_GUIDE.md#automation-and-it-use) in the User Guide. It opens with a [worked example](docs/USER_GUIDE.md#a-worked-example-nightly-source-tree-watch) — a full nightly cron script using `--stdout`, `--hash`, `--diff`, and an alert step — so you can see how the pieces compose before reading the reference material on exit codes, JSON schemas, the `--on-match` hook, headless deployment, and where reports and run logs land on disk.

### Professional and research audiences

Researchers, analysts, consultants, and business users — people who use peekdocs for literature review, due diligence, fact-checking, or finding information across years of mixed-format files.

| Who | Why they care | What they do with it |
|-----|--------------|---------------------|
| **Researchers and academics** | Search large research collections accurately, including scanned PDFs and historical documents, with highlighted exportable reports | Literature review across hundreds of PDFs, find themes across research collections, search scanned historical documents, extract references and citations |
| **Investigators, journalists, and analysts** | Sift through large document archives with precision using Boolean logic, proximity search, regex workflows, and OCR | Review large archives, investigate document collections, contract review, timeline reconstruction, email archive analysis |
| **Archivists and digital historians** | Search digitized and scanned collections locally without uploading to cloud services, with full OCR and Boolean support | Search digitized archives, historical newspapers, scanned records, museum and university collections, long-term document preservation |
| **Consultants and independent analysts** | Analyze client documents locally with no cloud exposure, then generate shareable highlighted reports | One-off document analysis, client archive review, research and report generation, technical due diligence |
| **Business and office power users** | Search years of mixed-format files without learning any syntax — just type keywords and click Run | Find contracts, search invoices, review budgets, search years of Word/PDF files, find information across correspondence |

*The audiences and scenarios above describe possible uses of peekdocs. peekdocs is provided "as is" under the [MIT License](LICENSE), without warranty of any kind, express or implied.*

### What makes peekdocs distinctive

The combination of **local + privacy-first + grep-like power + OCR + regex workflows + reporting + automation** across heterogeneous document collections is unusual. peekdocs delivers all of them in a single install.

<details>
<summary><b>Detailed use cases by role (click to expand)</b></summary>

- **Programmers** — VS Code is an excellent editor, but peekdocs searches the files it doesn't natively search: legacy specs and requirements in Word/PDF, email archives from past projects, vendor documentation and SDK guides in PDF, archived releases inside .zip/.7z files, scanned whiteboard photos (OCR), old project logs and meeting notes. A developer who needs to find "what did the client say about the authentication requirement in 2019" can't do that in VS Code if the answer is in a .docx email attachment inside a .zip archive. peekdocs can. One pipx command and you're running in seconds — CLI, GUI, or Python API (see [Option B](#option-b-quick-install-with-pipx-for-python-users)). **Search across entire codebases** — find every file that references a function, variable, endpoint, or error message across all source code files in all folders at once. Use Lines Before/After to see the full function or block surrounding each match, not just the matching line. Supported source code formats: .py, .c, .cpp, .h, .hpp, .html, .java, .js, .ts, .go, .rs, .rb, .sh, .bat, .ps1, .r, .swift, .kt, .cs, .vb, .f90, .f, .asm, .s, .pl, .tcl, .makefile
- **More for programmers** — find every TODO, FIXME, and HACK across all your projects at once, not just the one open in your IDE. Pre-upgrade audit: search all repos for a deprecated API or library before upgrading. Search log files for error patterns or request IDs across gigs of `.log` files. Search config files (`.yaml`, `.toml`, `.json`, `.ini`, `.properties`, `.conf`) and build files (`.gradle`, `.cmake`) to find where a setting, port, or environment variable is referenced. Multi-repo search: point peekdocs at a parent folder containing all your repos and search everything at once.
- **AI/ML engineers** — search training logs for specific metrics, hyperparameters, or error messages across experiment runs. Find every reference to a model name, checkpoint path, or dataset version across scripts, configs, and documentation. peekdocs reads Jupyter notebooks (`.ipynb`), JSONL training data (`.jsonl`), Scala Spark pipelines (`.scala`), and all common config formats. Search across READMEs, docstrings, and markdown files for outdated model names or deprecated API versions.
- **Data researchers** — search hundreds of CSV and Excel files for a specific value, account number, or outlier. Cross-reference interview transcripts, survey responses, and field notes for the same keyword to triangulate findings. Literature review: search 500 downloaded PDFs for a method name, author, or statistical technique. Find which analysis scripts reference a specific dataset, parameter, or threshold.
- **Engineers** — search hundreds of datasheets, design reviews, test reports, and failure analyses for a specific component value, part number, or tolerance. Find which documents reference a standard (MIL-STD-810, IEC 61508, ISO 9001). Search old design reviews and trade studies to find why a decision was made years ago. Locate error codes and symptoms across equipment manuals and maintenance logs. OCR reads scanned engineering drawings and handwritten notes. The highlighted Word report can be attached to a design review or emailed directly. Supported engineering formats: .m (MATLAB), .v .vhd .vhdl .sv (Verilog/VHDL/SystemVerilog), .cir .sp .spice (SPICE netlists), .dxf (AutoCAD interchange), .vsdx (Visio diagrams), .cmake (CMake build files)
- **Documentation teams and tech writers** — search for outdated references, inconsistent terminology, deprecated product names, or specific version numbers across an entire documentation set. Verify consistency across Word docs, PDFs, HTML exports, and Markdown files in a single search.
- **Researchers** — search across hundreds of downloaded journal articles (PDF), interview transcripts, survey responses, field notes, and datasets for a specific term, author, citation, or data point. OCR reads scanned source materials and historical documents. The highlighted Word report doubles as an annotated bibliography.
- **Small businesses** — find information across contracts, invoices, reports, and correspondence. Save searches by name and reload them later. Search across vendor contracts for specific terms, pricing, or expiration dates.
- **Home users** — tax returns, insurance policies, receipts, warranties, estate documents, email archives. Once installed, type your keyword(s), click Run Search, done. No configuration, no manual.
- **Email archives** — search exported email files (.eml, .msg, .pst, .mbox) for old correspondence, attachments, and contacts. peekdocs reads each format natively.

</details>

**What makes peekdocs different:**

- **[100+ file types at once](#supported-file-types)** — Word, PDF, Excel, PowerPoint, email (.eml, .msg, .pst), archives (.zip, .7z, .rar), source code, engineering files, e-books, calendars, contacts, and more. All searched simultaneously in a single pass. **Note:** `.pst` requires `libpff-python` (no Windows wheel) and `.rar` requires the `unrar` tool — both covered in [Prerequisites](#prerequisites).
- **Highlighted Results**
  Matches are highlighted in two ways:
  - **1) Results Preview (in-app):**
    - See matches instantly inside peekdocs
    - Right-click to copy text
    - Double-click a filename to open the file
  - **2) Word Report (.docx):**
    - Standalone document with all matches highlighted in yellow
    - Organized by file with surrounding context, search metadata, and match counts
    - Easy to save, print, email, or share
  - Both views show the same matches: Preview = quick scanning, Report = saving and sharing
  - **How matches are displayed:**
    - Word documents and PDFs: full paragraph is shown (based on text extraction)
    - Plain text files: individual lines are shown
    - Use Context Lines (Advanced Search Options) to include extra lines before/after matches
    - The yellow highlighting makes a real difference when reviewing large result sets — your eyes go straight to the matches instead of reading every line
  - **Other output options:**
    - A plain-text (.txt) report is generated automatically
    - Optional formats: CSV, JSON, PDF, HTML
  - **No Microsoft Word?**
    - Enable HTML output in Advanced Search Options
    - Click the HTML button to open the highlighted report in your browser
    - The file is stored locally — nothing is uploaded or shared
  - **Compatibility and privacy:**
    - The `.docx` report opens in Microsoft Word or [LibreOffice](https://www.libreoffice.org/download/download-libreoffice/) (free)
    - peekdocs avoids opening reports in Google Docs, Apple Pages, or other cloud-based apps that may upload your data
- **Regex Search** — run up to 10 custom regex patterns per collection from a dedicated popup (GUI only), each executed separately with per-pattern results and status updates. Each pattern has a name and regex field, with settings saved across sessions. Create unlimited named collections (Save Collection As / Restore From Collection) to maintain separate profiles for different tasks — "code patterns", "log analysis", "invoice extraction", and as many others as you need. Clear All erases all patterns; Restore All undoes the last clear. Results show per-pattern match counts with View Files buttons to see affected files and View Text to review highlighted matches. Cancel button stops the search between patterns. Check "Do not save regex match contents to reports" to prevent sensitive information from being saved to files — results are displayed in a screen-only popup only. Always scans files directly (index is bypassed) to ensure current results. The ? help includes 50 common regex patterns you can copy and paste. Note: you can also run a single regex search via Standard Search (check "Regex" in Advanced Search Options) — Standard Search supports all 11 search modes (AND, Boolean, fuzzy, wildcard, proximity, etc.) that the Regex Search popup does not.
- **11 search modes** — plain keywords, quoted phrases (`"annual report"` as a single unit), AND/OR, Boolean expressions (`(budget OR revenue) AND NOT draft`), regex, wildcards, fuzzy matching (typo-tolerant), whole-word, word proximity (terms within N words on the same line), line proximity (terms within N lines of each other), inverse search (find files that DON'T contain a term), and range queries (filter by dollar amounts, dates, percentages, ages, file sizes).
- **Three interfaces** — point-and-click GUI (`peekdocs-gui`), terminal CLI (`peekdocs`), and Python API (`from peekdocs import search`). All search modes work from all three interfaces except the Search Wizard, which is GUI-only. Use the GUI for daily work, the CLI for scripting, the API for integration.
- **Scanned documents** — OCR reads text from scanned PDFs and images (.jpg, .png, .tiff, .bmp). Tesseract (free, open-source) must be installed separately — but once it is, peekdocs handles the rest. *OCR accuracy depends on source quality: clean printed pages and modern scanner output extract well; handwriting, low-resolution scans, faxed pages, and documents with complex multi-column layouts may extract poorly or partially.*
- **Search inside archives** — searches inside .zip, .7z, and .rar files without extracting them first. Find a document buried in a compressed backup without unzipping anything.
- **Multi-folder search** — search across multiple top-level folders at once using the +Folder button, with optional recursive searching into subfolders. Results are combined from all folders. With recursive mode, you can even search your entire computer from a single search — point it at your root folder and peekdocs will search every supported file on the drive (system files that can't be read are logged and skipped).
- **Search Wizard** — configures complex searches for you with 20 pre-built search types (keywords, Boolean, fuzzy, proximity, dollar ranges, dates, phone numbers, and more) plus a separate regex pattern builder offering 35 named patterns across 6 tabs (one general, five profession-themed: Business/Finance, Legal, Engineering/Technical, Real Estate, HR/Admin). No regex or technical knowledge needed.
- **Save and reload searches** — save a configured search by name and reload it later with one click. Each folder has its own collection of saved searches.
- **Search Suites** — group multiple saved searches into a named suite and run them all at once with a single click. Each search runs independently with its own settings, and results are organized by search in a single combined highlighted report. Choose your output formats (TXT and DOCX are always generated; HTML, CSV, JSON, and PDF are optional — select them in the Search Suites popup). Create suites for recurring tasks like pre-publication checks, quarterly audits, onboarding reviews, or any workflow that involves the same set of searches. Suites are stored per folder, but the CLI finds them by name from anywhere: `peekdocs --suite "My Suite"` auto-locates the folder it was saved in, and `peekdocs --list-suites` shows every suite and where it lives. Available from the GUI (Tools → Search Suites) and CLI.
- **Search index** — optional SQLite FTS5 index for faster repeated searches. Build once, search in sub-second time. Auto-refresh keeps the index current when files change.
- **Built-in file analysis tools** — the Tools menu includes Collection Summary (one-page overview combining file count, total size, oldest/newest, top file types, searchability breakdown, age distribution, largest files, and recent activity counts — fast, single-pass), File Inventory (summary by type/size/date), File Age Distribution (histogram of files by modification age — useful for archives, document collections, and personal files), Duplicate Finder (identical files by content hash), Large Files, Empty Files, Recent Changes, Protected Files (password-encrypted detection), Unsearchable Files (categorizes everything peekdocs cannot search — unsupported types, oversized files relative to the Max File Size you set in Advanced Search Options, hidden / OS metadata, peekdocs-created — with counts per category), Search History (automatic log of past searches), Bookmarks (pin files for quick access), and App Files (lists every file peekdocs has created in the folder — results, reports, indexes, saved searches — so you always know what's yours and what's peekdocs').
- **Offline and private** — your documents never leave your computer.
  - peekdocs never uploads, transmits, alters, moves, or deletes your files
  - No cloud, no accounts, no subscriptions, no internet connection required
  - **Safe report handling:**
    - Reports (.docx, .pdf, .csv, .json) are opened only in trusted local applications
    - peekdocs launches installed programs directly (e.g., Microsoft Word, LibreOffice, Adobe Reader), bypassing the operating system's default file handler
    - Cloud-based apps (e.g., Google Docs, Apple Pages) are never used
  - **Protection against cloud syncing:**
    - If your output folder is inside a cloud-synced directory (OneDrive, Google Drive, iCloud Drive, Dropbox), peekdocs automatically redirects reports to a local folder (`~/peekdocs_reports`)
    - This allows you to search cloud-synced documents without uploading report files
  - **Automatic cleanup:**
    - Enable **Delete on Close** to remove all result files when the app closes
- **Report security** — peekdocs takes steps to reduce the risk of your search results being exposed. Reports are opened in safe local applications rather than cloud-based viewers like Google Docs or Apple Pages. If your search folder is inside OneDrive, Google Drive, iCloud Drive, or Dropbox, peekdocs automatically redirects report output to a safe local folder (`~/peekdocs_reports`) — your documents are still searched, but no report files are written to the cloud-synced location. The status line tells you where reports were saved and why. **Delete on Close** automatically removes result files when you close the app. **Clear History on Close** clears your search history and recent searches (useful if a search term you'd rather not leave on disk has been typed). **Clear Preview** wipes the Results Preview pane on demand. **Wipe Session** (Tools → Clear Files → Wipe Session tab) immediately deletes result files, clears the preview, and wipes search history in one click — useful if you don't close the app regularly. If your search term matches certain numeric ID patterns, peekdocs warns you before proceeding because that term will appear in report files. See [For IT and Security Teams](#for-it-and-security-teams) for details.
- **Network folders** — search documents on a shared network drive just like a local folder. Map or mount the network share (e.g., `Z:\` on Windows, `/Volumes/` on macOS) and point peekdocs at it. Tip: build a search index on your first search — subsequent searches query the local index instead of re-reading files over the network, which is much faster.
- **Cross-platform** — Windows, macOS, and Linux. Tested on all three.
- **Performance** — 1,000 mixed-format documents (PDFs, Word, Excel, email) searched in ~1 second. 105 real Word docs (1.9 GB) in 4 seconds (0.24 seconds with index). See [Performance](#performance) for detailed benchmarks.
- **Help everywhere** — every screen has a **?** button that opens a detailed help page explaining all the features on that screen. Every data field, button, and checkbox has a hover tooltip that explains what it does. No need to open the manual — the answers are right where you need them. Toggle tooltips on/off with the **Tooltips: ON/OFF** button on the bottom row of the main screen. Saved automatically.
- **Adjustable text size** — five sizes from Small to Huge, accessible from the Tools menu. All text, labels, and buttons scale together. Helpful for users with low vision or high-DPI displays. Saved automatically.
- **Dark mode** — switch between Dark, Light, or System (follows your OS setting) from the Tools menu. Saved automatically. Note: on Windows, popup windows may briefly flash white before the dark theme is applied — this is a normal Windows/tkinter limitation, not a bug. If the flashing is distracting, switch to Appearance: Light in the Tools menu.

## Features

peekdocs has **three search modes**, each writing its own self-described report family next to your documents so they never collide:

| Mode | How to run | Reports |
|------|-----------|---------|
| **Standard Search** | Blue **Run Standard Search** button on the main screen, or `peekdocs <terms>` | `peekdocs_standard_results.{txt,docx,csv,json,pdf,html}` |
| **Regex Search** | Orange **Regex Search** button on the main screen (opens the regex popup; its own Run Regex Search button executes the collection), or `peekdocs --regex-collection NAME` | `peekdocs_regex_results.{txt,docx}` |
| **Suite** (group of saved searches) | Green **Search Suites** button on the main screen (opens the suite popup; its own Run Search Suite button executes the selected suite), or `peekdocs --suite NAME` | `peekdocs_suite_results.{txt,docx,html,csv,json}` |

> *The "mode" is the workflow, not the flag set. A one-off `peekdocs -x "pattern"` (or `-z`, `-w`, `-W`) is a Standard Search with a regex/fuzzy/wildcard flag and writes `peekdocs_standard_results.*`. Only the dedicated Regex Search workflow — the GUI popup or `--regex-collection` — produces `peekdocs_regex_results.*`.*

All three share the same engine, flags, and 100+ file-type support. The matching `peekdocs_<mode>_results.*` naming means a Regex run never overwrites a Standard run (and vice versa), and `peekdocs --clear` / **Clear Files** can find them by prefix. Within a mode, each run overwrites the previous report — add `--timestamp` (CLI) or check **Timestamp** in Advanced Search Options (GUI) to append `_YYYYMMDD_HHMMSS` so every run is preserved. The **Schedule Search** dialog enables timestamping by default for cron / Task Scheduler use.

#### Search & discovery

- **100+ file types** — Word, PDF, Excel, PowerPoint, emails (.eml, .msg, .pst, .mbox), archives (.zip, .7z, .rar), source code (Python, C/C++, Java, Go, Rust, and more), engineering files (MATLAB, Verilog, VHDL, SPICE, DXF, Visio), Apple Pages/Numbers/Keynote, calendars (.ics), contacts (.vcf), e-books, HTML, and more. **Note:** `.pst` requires `libpff-python` (no Windows wheel) and `.rar` requires the `unrar` tool — see [Prerequisites](#prerequisites)
- **Search modes** — plain keywords, AND/OR, Boolean expressions, regex, wildcards, fuzzy matching, whole-word, word proximity, line proximity
- **Range queries** — filter by dollar amounts, dates, percentages, ages, file sizes
- **OCR** — search scanned PDFs and images (requires Tesseract)
- **Multi-folder search** — search across multiple folders at once, with optional recursive searching into subfolders. Click **+Folder** to add folders, or type semicolon-separated paths. Results are combined from all folders
- **Inverse search** — find files that are *missing* required content
- **Search Wizard** — guided search builder with 20 pre-built search types (phone, email, dollar range, date range, Boolean, fuzzy, and more) plus a regex pattern builder with 35 named patterns across 6 categories — no flags or regex knowledge needed
- **Save Search / Load Search** — save a configured search by name and reload it later with one click
- **Recent searches** — dropdown next to the search bar remembers your last 10 searches
- **Search index** — optional SQLite FTS5 index for faster repeated searches
- **Works in any language** — Unicode-based text handling; searches documents in any language with exact character-sequence matching (no stemming or word segmentation). GUI and documentation are English-only. The PDF report uses a Latin-1 font, so non-Latin text shows as `?` in `.pdf` only — use `.docx`, `.html`, `.txt`, `.json`, or `.csv` for non-Latin content.

#### Reporting

- **Highlighted reports** — results saved to `.docx` and `.pdf` with yellow-highlighted matches, `.txt` with full context, and optional CSV and JSON output
- **Results preview** — see matches inline in the GUI with highlighted terms. **View Text** on any matched file shows the file's full extracted text with every match highlighted, without opening external software. Double-click any file to open in its native application; click **DOCX**, **HTML**, or **PDF** to open the highlighted multi-file report
- **HTML export** — no Word or LibreOffice? Enable HTML output and the highlighted report opens in any browser. The file is stored locally — nothing is uploaded, and it's easy to share by email

#### Analysis

- **Collection Summary** — one-page consolidated overview of the search folder: total file count and size, oldest/newest file, top file types, age histogram, top 10 largest files, recent-activity counts, unsearchable breakdown, and empty-file count — all in a single fast pass
- **File Inventory** — instant summary of every file in a folder: total count, size breakdown by type, oldest and newest files
- **Duplicate Finder** — finds identical files by content (not just name), shows how much space is wasted by extra copies
- **Large Files** — shows the 50 biggest files so you can reclaim disk space
- **Empty Files** — finds zero-byte files: failed downloads, placeholders, junk
- **File Age Distribution** — histogram of how recently files were modified, in six buckets from 0–6 months out to 10+ years. Useful for archives, document collections, and personal files — surfaces stale folders at a glance and shows what fraction of a collection is recent activity vs. long-untouched material
- **Recent Changes** — which files were modified in the last 7, 30, or 90 days
- **Protected Files** — detects password-protected PDFs, Word/Excel/PowerPoint, ZIP/7z/RAR archives that peekdocs can't search
- **Unsearchable Files** — categorizes every file peekdocs cannot search (unsupported types, oversized, empty, hidden / OS metadata, peekdocs-created) with counts and per-category file lists. Answers "what fraction of this folder is even searchable?" before you run a search
- **Bookmarks** — pin files from search results for quick access later

#### Automation & integration

- **Search Suites** — group saved searches into a named suite and run them all at once (Tools → Search Suites)
- **Repeatable workflows** — Saved Searches, Search Suites, Regex Collections, Schedule Search, Search History, and Diff Snapshots compose into a workflow system: define a search by name; group related searches into a suite; reuse pattern sets via Regex Collections; schedule a suite to run on a cadence; audit every run via Search History; compare today's run against last week's via Diff Snapshots.
- **Search History** — automatic diary of every search you run: date, terms, match count, file count, elapsed time
- **Diff Snapshots** — compare two saved scans to see what files are new, changed, removed, or unchanged between them
- **Schedule Search** — generates a ready-to-paste cron (Mac/Linux) or Task Scheduler (Windows) command to run any saved search suite or regex collection on a schedule. Step-by-step instructions are included — no terminal experience required
- **Indexes** — build, refresh, or delete the optional search index that makes repeated searches dramatically faster
- **Three interfaces** — terminal CLI, point-and-click GUI (`peekdocs-gui`), Python API
- **Cross-platform** — Windows, macOS, Linux

#### Privacy & transparency

- **Offline and private** — your documents never leave your computer. peekdocs never uploads, transmits, alters, moves, or deletes your files. No cloud, no accounts, no subscriptions. Everything runs locally and stays local
- **Read-only** — peekdocs never modifies, moves, or deletes your files. It does create its own output files (reports, indexes, settings) and can delete those when you ask (e.g., Clear Results, Delete Index)
- **Delete on Close** — one checkbox automatically deletes every result file and the search index across the session when you close peekdocs. Saved reports, saved searches, settings, and bookmarks are preserved
- **Safe defaults** — files over 100 MB are skipped automatically to prevent slow searches and memory issues; archives that would expand past 500 MB are skipped to prevent archive bombs. Adjust **Max File Size** in Advanced Search Options or set it to 0 for no limit
- **Excluded Files view** — after each search, see exactly which files were skipped and why (unsupported type, oversized, hidden, etc.) — no guessing what was missed
- **Error Log** — opens `peekdocs_errors.log` to see any files that couldn't be read and why (corrupt, locked, password-protected, etc.)
- **Clear Files** — selectively delete peekdocs's output files (reports, error log, saved searches, index) from the current folder
- **Clean Folder** — same idea for any other folder, in case peekdocs files were generated elsewhere

### Supported File Types

| Category | Formats |
|----------|---------|
| **Documents** | .doc .docx .epub .html .key .md .odp .odt .pages .pdf .ppt .pptx .rst .rtf .tex |
| **Spreadsheets** | .csv .numbers .ods .tsv .xls .xlsx |
| **Email** | .eml .mbox .msg .pst (`.pst` requires `libpff-python` — no Windows wheel; see [Troubleshooting](docs/TROUBLESHOOTING.md)) |
| **Archives** | .7z .bz2 .gz .rar .tar .tgz .zip (`.rar` requires the `unrar` tool — see [Prerequisites](#prerequisites)) |
| **Calendar/Contacts** | .ics .vcf |
| **Source Code** | .asm .bat .c .cmake .cpp .cs .css .f .f90 .go .gradle .h .hpp .java .js .kt .lua .pl .ps1 .py .r .rb .rs .s .scala .scss .sh .swift .tcl .ts .vb |
| **Engineering** | .cir .dxf .m .sp .spice .sv .v .vhd .vhdl .vsdx |
| **Data/Config** | .cfg .conf .dockerfile .env .graphql .gql .ini .json .jsonl .log .makefile .ndjson .properties .proto .sql .tf .toml .txt .xml .yaml .yml |
| **Notebooks** | .ipynb (Jupyter) |
| **Images (OCR)** | .bmp .jpg .jpeg .png .tif .tiff (requires `-O` flag) |

**Note:** Apple Numbers (.numbers) and Keynote (.key) files created with recent versions of iWork use a protobuf-based internal format. peekdocs extracts whatever readable text exists inside these files, which may be partial. Older iWork files extract fully. Apple Pages (.pages) is fully supported.

## Installation

[Prerequisites](#prerequisites) · [Option A: Standalone Download](#option-a-standalone-download-recommended-for-most-users) · [Option B: pipx (for Python users)](#option-b-quick-install-with-pipx-for-python-users) · [Upgrading](#upgrading)

### Prerequisites

*Using Option A (standalone download)? Skip this section — no prerequisites needed.*

| Requirement | Why | How |
|---|---|---|
| **Python 3.10+** | Required for Option B and source install | macOS: `brew install python` (or [python.org](https://www.python.org/downloads/)). Windows: [python.org](https://www.python.org/downloads/), check "Add Python to PATH". Linux: `sudo apt install python3-venv python3-pip python3-tk`. Per-platform deep dives in [docs/INSTALLATION.md](docs/INSTALLATION.md) |
| **Tkinter** | GUI only (CLI works without it) | Windows: included. macOS Homebrew: `brew install python-tk@<version>`. Linux: covered by `python3-tk` above |
| **pipx** | Recommended over `pip` for Option B | `pip install pipx` (Windows) · `brew install pipx` (macOS) · `sudo apt install pipx` (Linux). Then `pipx ensurepath` and reopen your terminal |
| **Tesseract** (optional) | OCR for scanned PDFs and images | `brew install tesseract` · Windows [installer](https://github.com/UB-Mannheim/tesseract/wiki) · `sudo apt install tesseract-ocr` |
| **UnRAR** (optional) | Search inside `.rar` archives | `brew install unrar` · WinRAR · `sudo apt install unrar` |
| **libpff-python** (optional) | Search inside Outlook `.pst` archives (no Windows wheel) | macOS/Linux: `pip install libpff-python`. Windows: convert `.pst` to `.mbox` — see [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |

**Everything else installs automatically.** `pipx install` (or `pip install`) downloads the 17 Python libraries peekdocs needs (PDF reader, Word/Excel/PowerPoint parsers, email reader, and more) — about 50 packages, ~244 MB total. See [Dependencies](docs/USER_GUIDE.md#dependencies) for the full list and what each one does.

### Option A: Standalone Download (recommended for most users)

The simplest way to get peekdocs. No Python, no terminal commands, no installation — just download and run.

**Direct downloads** (always the latest release):

| Platform | Download | After download |
|---|---|---|
| Windows | [**peekdocs-gui-windows.exe**](https://github.com/exbuf/peekdocs/releases/latest/download/peekdocs-gui-windows.exe) | Double-click to run |
| macOS | [**peekdocs-gui-macos.zip**](https://github.com/exbuf/peekdocs/releases/latest/download/peekdocs-gui-macos.zip) | Unzip, open `peekdocs-gui.app` |
| Linux | [**peekdocs-gui-linux**](https://github.com/exbuf/peekdocs/releases/latest/download/peekdocs-gui-linux) | In the download folder (typically `~/Downloads`): `cd ~/Downloads && chmod +x peekdocs-gui-linux && ./peekdocs-gui-linux` |

Or browse the [**Releases page**](https://github.com/exbuf/peekdocs/releases/latest) for older versions, the full asset list (GUI + CLI for each platform), or release notes. *On the GitHub repo page, "Releases" is in the right sidebar under "About" — it's easy to miss if you're not looking for it.*

**First-launch security warnings (one-time, per platform).** Free, open-source software that hasn't paid for an OS-vendor code-signing certificate triggers a warning on first launch. This is normal and does not mean the software is unsafe.

- **Windows (SmartScreen):** Click **More info** → **Run anyway**.
- **macOS (Gatekeeper):** Recent macOS (Sequoia / Sonoma) shows a warning dialog with only **Done** and **Move to Trash** — no **Open** button. Click **Done**, then go **System Settings → Privacy & Security**, scroll down to *"peekdocs-gui.app was blocked..."*, and click **Open Anyway**. Re-launch the app and click **Open** in the final confirm dialog. From then on a regular double-click on *that copy* works. **Each new download (including upgrades) re-triggers the warning** — the trust is per downloaded file, not per app — so plan on running through this once each release. The one-line terminal alternative `xattr -dr com.apple.quarantine ~/Downloads/peekdocs-gui.app` is the fastest path if you upgrade often. Full walkthrough: [docs/INSTALLATION.md → macOS first-launch Gatekeeper](docs/INSTALLATION.md#macos-gatekeeper). *Note: Safari auto-unzips downloaded `.zip` files, so you'll see `peekdocs-gui.app` directly in Downloads rather than the `peekdocs-gui-macos.zip` you clicked — no extra unzip step.*
- **Linux:** Open a terminal in the folder where the file landed (typically `~/Downloads`), then `chmod +x peekdocs-gui-linux && ./peekdocs-gui-linux`. The `./` prefix is required because the current directory is not on `$PATH` by default — `./` tells the shell "run the file in *this* folder." If you moved the file elsewhere, `cd` there first or run it by absolute path (`/path/to/peekdocs-gui-linux`).

**CLI standalones** for terminal use — direct downloads: [peekdocs-cli-windows.exe](https://github.com/exbuf/peekdocs/releases/latest/download/peekdocs-cli-windows.exe), [peekdocs-cli-macos.zip](https://github.com/exbuf/peekdocs/releases/latest/download/peekdocs-cli-macos.zip), [peekdocs-cli-linux](https://github.com/exbuf/peekdocs/releases/latest/download/peekdocs-cli-linux). Run them from an already-open terminal — Windows-specific quirks (PowerShell `--%` token, `.rar`/`.pst` limitations) are in [docs/INSTALLATION.md#cli-on-windows-footnotes](docs/INSTALLATION.md#cli-on-windows-footnotes).

**Upgrading.** Download the new version and replace the old file. Your settings and saved searches live in your home directory — nothing is lost.

**No dependency breakage.** The standalone bundles Python, all libraries, and peekdocs into a single file frozen at versions that were tested together. Unlike `pip install`, there are no external dependencies to upgrade, conflict, or break.

**Safe for your computer.** No installation option (standalone, pipx, or source) modifies your existing Python, installs system services, writes to the registry, or interferes with any other program.

---

*If you used Option A, you're done — skip ahead to [Quick Start](#quick-start). The section below is for users who want the CLI / Python API alongside the GUI.*

### Option B: Quick Install with pipx (for Python users)

If you already have Python set up — or you want the CLI and Python API alongside the GUI — one command installs everything. Works the same on every OS.

```bash
pipx install --force git+https://github.com/exbuf/peekdocs.git
```

`--force` overwrites any existing peekdocs install cleanly. The same command is your future upgrade — re-run it whenever you want the latest commit.

After install, `peekdocs` and `peekdocs-gui` work from any terminal, any folder, every time — even after restarting your computer. pipx manages the underlying virtual environment for you. To uninstall completely: `pipx uninstall peekdocs`. See the [User Guide](docs/USER_GUIDE.md#will-peekdocs-affect-my-existing-python-installation) for what is and isn't preserved across upgrades.

**Niche cases** (macOS python3.13 selection, no-git ZIP install, Windows pipx fallback, source install for contributors) are documented in [docs/INSTALLATION.md](docs/INSTALLATION.md).

### Upgrading

Your saved searches, settings, indexes, and reports are stored outside the peekdocs installation — in your home directory and your document folders. Upgrading replaces only the code. These files are **never overwritten** by an upgrade:

- `~/.peekdocsrc` — your saved settings and preferences
- `~/.peekdocs_history.json` — your search history
- `~/.peekdocs_bookmarks.json` — your bookmarks
- `.peekdocs_collection.json` (in each search folder) — your saved searches and search suites
- `.peekdocs.db` (in each search folder) — your search index
- `peekdocs_report_*`, `peekdocs_accumulated_*` files — your saved reports

How to upgrade depends on which install method you used:

- **Standalone (Option A):** download the new file from the [Releases page](https://github.com/exbuf/peekdocs/releases/latest) and replace the old one.
- **pipx (Option B):** `pipx install --force git+https://github.com/exbuf/peekdocs.git` — same command as the original install.
- **Source install:** `cd peekdocs && git pull && pip install -e .` (see [CONTRIBUTING.md](CONTRIBUTING.md#development-setup)).
- **Niche paths** (no-git ZIP, Windows pip fallback): see [docs/INSTALLATION.md](docs/INSTALLATION.md).


## Quick Start

**Want a quick demo first?** Clone this repo and try peekdocs on the bundled samples: `cd samples/engineering_test && peekdocs TODO -r` returns hits across 35 source-code and engineering file types. No setup beyond installing peekdocs.

### Terminal

If you used Option A (standalone download) or Option B (pipx), peekdocs is always ready — just open any terminal. If you used the source install for contributors, navigate to the cloned repo folder and activate the virtual environment first:

```bash
cd /path/to/peekdocs                 # the folder containing pyproject.toml
source venv/bin/activate             # macOS/Linux (you'll see (venv) in your prompt)
venv\Scripts\activate                # Windows
```

**Tip:** Type `peekdocs` with no arguments to see a handy cheat sheet of all search modes, common options, and cleanup commands — right above your command prompt. Type `peekdocs -h` for the full reference with all flags, file types, and regex patterns.

Then navigate to your documents and search:

```bash
cd /path/to/your/documents
peekdocs budget                      # search for "budget"
peekdocs budget revenue              # OR search (any term)
peekdocs -a budget revenue           # AND search (both terms)
peekdocs -r budget                   # include subfolders
peekdocs -t pdf,docx budget          # only PDFs and Word docs
peekdocs -x "\d{3}-\d{2}-\d{4}"     # regex (9-digit ID with dashes)
peekdocs -e "(budget OR revenue) AND NOT draft"   # Boolean expression
peekdocs -R amount:1000..5000 budget # range query
peekdocs -R date:2024-01-01..2024-12-31 invoice  # date range (also accepts 01/01/2024 format)
peekdocs -P 3 budget acme            # line proximity (terms within 3 lines)
peekdocs --open docx budget          # search and auto-open the .docx report
peekdocs --open html budget          # auto-generate HTML and open in your browser
peekdocs --open csv budget           # auto-generate CSV and open in Excel/LibreOffice
peekdocs --open pdf budget           # auto-generate PDF and open in a PDF viewer
peekdocs --open json budget          # auto-generate JSON and open in a text editor
peekdocs -sa archive --open docx budget  # append to accumulated report and open it
peekdocs -sa archive --open html budget  # append and open accumulated report in browser
peekdocs --clear                    # delete peekdocs_*_results* files in current directory
peekdocs --clear-all                # delete all peekdocs output files (results, saved reports, index)
```

**No matches?** First search not turning anything up is common. Try `-r` to include subfolders, `-z` for typo-tolerance, drop `-W` if you had whole-word on (it excludes partial matches like "logger" when searching "log"), or check whether your search terms actually appear in those files by opening one manually. Run `peekdocs --list-files` to confirm peekdocs sees the files you expect.

If you used the manual install, you'll see `(venv)` before each command in your terminal — that's normal and means the virtual environment is active.

Results are saved to `peekdocs_standard_results.txt` and `peekdocs_standard_results.docx` (highlighted) in the current directory — the same folder your terminal is in when you run the search. If you enabled additional formats (CSV, JSON, PDF, HTML), those are saved too. **All result files are overwritten each time you run a new search.** To keep previous results, use `-s my_report` to save a named copy (saved as `peekdocs_report_my_report.txt/.docx` so peekdocs never searches its own reports), or `--timestamp` to add a date/time stamp to each filename so nothing is ever overwritten. When clicked, the .docx report opens automatically in whatever word processor you have — Microsoft Word or [LibreOffice](https://www.libreoffice.org/download/download-libreoffice/) (free) are recommended. peekdocs avoids opening reports in Google Docs, Apple Pages, or any cloud-based application that may upload your data. The .txt report works on any computer with no extra software.

To clean up output files: `peekdocs --clear` (deletes results files) or `peekdocs --clear-all` (deletes results, saved reports, error log, and index). Neither touches your saved searches or settings.

Run `peekdocs -h` for the full flag reference with examples. The complete flag list with detailed descriptions is in the [User Guide](docs/USER_GUIDE.md#flag-use-summary). All flags can be combined freely except: regex (`-x`), fuzzy (`-z`), and wildcard (`-w`) are mutually exclusive (pick one); and expression mode (`-e`) cannot be combined with AND (`-a`), exclude (`-n`), or proximity (`-p`) since those are built into the expression syntax.

### GUI

```bash
peekdocs-gui
```

See [Screenshots](#screenshots) for what peekdocs looks like in action — both GUI and CLI.

On first launch, the GUI opens with a **Getting Started** tab that walks you through your first search. Close it when you're ready to dive in, or skip it and follow these four steps:

1. Click **Browse** to select a folder (or **File** to search a single file)
2. Type your search terms
3. Click **Run Search**
4. View results in the preview pane or click **DOCX** to open the highlighted report

Most users won't need anything beyond the search bar — type your keywords and click Run Search. For more advanced searches, you have two choices: configure **Advanced Search Options** yourself (regex, fuzzy, Boolean, range queries, and all other settings), or let the **Search Wizard** do it for you — pick a search type from 20 pre-built forms, fill in your values, and click Apply. (The wizard also has a separate regex pattern builder with 35 named patterns across 6 categories.) The wizard configures Advanced Search Options automatically. Both are in the **Tools** menu, along with **Search Suites** (run a group of saved searches together).

**If buttons overlap or text looks too large**, use the **Text Size** dropdown on the bottom-right toolbar to adjust (Normal is recommended).

### Python API

```python
from peekdocs import search

if __name__ == "__main__":
    result = search(["budget", "revenue"], directory="/path/to/docs")

    print(f"Found {len(result.matches)} matches in {len(result.files_searched)} files")
    for match in result.matches:
        print(f"  {match.filename}:{match.line_num}: {match.text}")
```

The `if __name__ == "__main__":` guard is **required** — peekdocs uses `multiprocessing` internally, and on macOS and Windows child processes re-import the calling script. Without the guard, the script will crash with `RuntimeError` on those platforms. See the [API Reference](docs/API.md) for all parameters and options.

---

**Stuck?** Run `peekdocs --check` first — or, if you're using the GUI, open **Tools → System Check** for the same diagnostic in a window. Either way verifies Python, dependencies, Tesseract, SQLite, and free disk space and tells you what's missing. If the check looks clean but you're still hitting issues, see [FAQ & Troubleshooting](docs/TROUBLESHOOTING.md) for common questions and fixes across Windows, macOS, and Linux.

## Documentation

| Document | Description |
|----------|-------------|
| [User Guide](docs/USER_GUIDE.md) | Complete reference — GUI, CLI flags, search modes, indexing, file reference |
| [Installation](docs/INSTALLATION.md) | Per-platform Python prerequisites, optional tools (Tesseract, UnRAR, libpff-python), CLI-on-Windows footnotes, and less-common install paths |
| [API Reference](docs/API.md) | Python library API — `search()` function, parameters, return values |
| [Glossary](docs/GLOSSARY.md) | ~70 peekdocs terms: FTS5, regex modes, deterministic, exit codes, Tesseract, jq, SIEM, MSP, and more |
| [FAQ & Troubleshooting](docs/TROUBLESHOOTING.md) | Common questions and solutions for Windows, macOS, and Linux |
| [Security](docs/SECURITY.md) | Deep dive for IT and Security teams — data architecture, per-file sensitivity notes, and limitations outside the application's control |
| [Changelog](CHANGELOG.md) | Version history and release notes |
| [Contributing](CONTRIBUTING.md) | How to report bugs, suggest features, and submit code |

## Why peekdocs?

Every search tool — `grep`, OS file search, cloud AI assistants, enterprise search software — matches text at its core. The differences are in what each one can read, how it presents results, what stays private, and what you can do with the output.

If all you need is to find a word in a plain text file, many search tools work well. If you want to *see inside your own files* — across 100+ file formats, with context, in a report you can share, without uploading anything — that's what peekdocs was built for.

### Why Is peekdocs a Search and *Analysis* Tool?

peekdocs is a search tool because it helps you find information across PDFs, Office documents, email archives, source code, scanned documents, and 100+ other file types. It is also an *analysis* tool because it helps you characterize document collections, not just search them. Features such as Duplicate Finder, File Inventory, Large Files, Recent Changes, Protected Files, Diff Snapshots, Bookmarks, and Search History reveal patterns, changes, and characteristics within your files. peekdocs does not interpret results, assign risk scores, or make decisions for you; instead, it gathers and organizes information so you can analyze it yourself. In that sense, peekdocs goes beyond answering "Where is this?" and also helps answer "What do I have?", "What changed?", "What is duplicated?", and "What is taking up the most space?"

**Compared with built-in OS search (Windows Search, macOS Spotlight, Linux file managers).** OS search is convenient for everyday file discovery. peekdocs is purpose-built for document-search workflows across mixed-format collections — including `.pst`, `.msg`, `.7z`, `.rar`, `.odt`, `.eml`, `.mbox`, Jupyter notebooks, and scanned PDFs. Results show *where* each match occurs (filename, line number, surrounding context), and you can run them in Boolean, fuzzy, regex, proximity, or range mode, save them by name, group them into suites, and produce highlighted `.docx`, `.pdf`, and `.html` reports you can save or share. The index is yours to build and refresh on demand, and the same searches work across the GUI, CLI, and Python API.

**Compared with cloud AI document tools.** Cloud AI tools excel at summarization, question answering, semantic search, and extracting meaning from large document collections — often the right reach for those tasks. peekdocs serves a different purpose: it runs entirely on your computer. For keyword, pattern, date, amount, regex, fuzzy, and proximity searches across mixed-format folders, peekdocs delivers deterministic and repeatable results while keeping your documents local.

**Compared with `grep`.** For plain-text search in a terminal, `grep` is excellent — use it. peekdocs is built for mixed-format document collections (PDF, Word, Excel, PowerPoint, email, OCR-able scans), with highlighted reports, saved searches, search suites, regex collections, indexing, a GUI, and a Python API. Both can live in your toolkit; they're designed for different jobs.

| Capability | grep | peekdocs |
|---|---|---|
| Plain text files (.txt, .log, .csv) | Yes | Yes |
| PDF text extraction | Requires external conversion (`pdftotext`) | Built in |
| Word documents (.docx) | Requires external conversion | Built in |
| Excel spreadsheets (.xlsx) | Requires external conversion | Built in |
| PowerPoint presentations (.pptx) | Requires external conversion | Built in |
| Email files and archives (.eml, .msg, .mbox, .pst) | Requires external conversion | Built in |
| OCR (scanned PDFs and images) | Requires external OCR pipeline | Built in (`-O`) |
| EPUB, RTF, ODT, ODS, ODP, archives | Format-specific tools required | Built in |
| Source code (48 languages) | Yes | Yes |
| Highlighted .docx / .pdf / .html reports | No | Yes |
| CSV and JSON export | Requires scripting | Built in (`-o csv,json`) |
| Boolean expressions | Requires shell composition | Yes (`-e "A AND (B OR C)"`) |
| Proximity search | Requires custom scripting | Yes (`-p 5`) |
| Fuzzy / typo-tolerant matching | Requires specialized tools | Yes (`-z`) |
| Range queries (amounts, dates) | Requires custom scripting | Yes (`-R amount:1000..5000`) |
| Saved searches and suites | No | Yes |
| Regex collections (batch pattern sets) | Requires scripting | Built in (`--regex-collection`) |
| Search index with on-demand refresh | Requires separate indexing tool | Built in (`--index`) |
| Consistent behavior across Windows, macOS, and Linux | Varies (GNU vs BSD grep) | Same flags on all three platforms |
| GUI | No | Yes |
| Python API | No | Yes |

## What peekdocs Is Not

> **In one line:** peekdocs is a search utility — not a judgment engine, not a compliance certifier, not a forensic platform, not a threat-assessment tool.

peekdocs is a general-purpose local text-search application. To set honest expectations, here are the things it is **not**, alongside the kind of tool you would reach for instead:

- **Not a security or threat-detection product.** peekdocs matches the text patterns you give it. It does not score risk, classify findings, recognize malware, or judge whether a match is good or bad — that's your call. For threat detection, reach for a dedicated security product.
- **Not a substitute for human review.** peekdocs surfaces matches; it does not decide which matches matter. Treat its output as a starting point for code review, document review, or whatever judgment task brought you here.
- **Not a forensic or evidence-collection system.** The optional SHA-256 with `--hash` is a content fingerprint for snapshot comparison, not notarized, tamper-evident, or court-admissible evidence handling. For chain-of-custody workflows, reach for a dedicated forensic suite.
- **Not an AI or summarization tool.** peekdocs does not infer, summarize, paraphrase, answer questions, or reason about what your documents say. It finds matches; that's it. For summarization or question-answering, use an LLM-based system — along with the cloud, privacy, and cost tradeoffs that typically come with it.
- **Not a file manager or backup tool.** peekdocs reads your files; it never moves, modifies, renames, syncs, archives, or version-controls them. It writes its own report files (all prefixed `peekdocs_`) and nothing else.
- **Not networked.** peekdocs operates only on files mounted as local paths. It does not crawl websites, hit APIs, read SharePoint or Confluence over a network, or talk to a remote search index. A mapped network drive that appears as a regular folder works; everything else does not.
- **Not a search-index server or enterprise document platform.** peekdocs runs as a single-user CLI / GUI / library on one machine. It does not host a shared indexable corpus for many users, manage permissions or roles, version content, or expose an HTTP API for other systems to query. For multi-user document management, reach for Elasticsearch / OpenSearch / Solr (search servers) or SharePoint / M-Files / Documentum / Box (enterprise document platforms).
- **Not a high-assurance or safety-critical tool.** peekdocs is offered under the MIT License "as is" without warranty. It is not designed for environments where an incorrect or missed match could cause significant harm. Users remain solely responsible for how they use and interpret its output.

For what peekdocs *is*, see [Feature Highlights](#feature-highlights) and the [User Guide](docs/USER_GUIDE.md).

## Performance

**Test machine:** MacBook Pro, Apple M-series, 24 GB RAM, SSD, Python 3.13. peekdocs used 7 of 14 cores (its default is half; adjustable in Advanced Search Options). Your results will vary depending on CPU, RAM, disk type (SSD vs hard drive), and whether files are local or on a network drive.

### Mixed-format test (realistic documents)

The file mix represents a typical home or small business folder:

| File type | % of files | Examples |
|-----------|--:|-----|
| PDF | 35% | Bank statements, receipts, tax forms, manuals |
| Word (.docx) | 25% | Letters, resumes, reports, contracts |
| Plain text (.txt, .csv, .log) | 15% | Notes, data exports, logs |
| Excel (.xlsx) | 10% | Budgets, lists, financial records |
| Email (.eml) | 8% | Exported correspondence |
| PowerPoint (.pptx) | 5% | Presentations |
| Other (.html, .rtf) | 2% | Saved web pages, legacy docs |

**Results (files stored locally on SSD).** Each test folder contained the mix of file types shown above. Individual file sizes varied (PDFs 50–500 KB, Word docs 20–200 KB, text files 1–50 KB, etc.). "Total size" is the entire folder.

| Files | Total folder size | Search time |
|------:|-----------:|------------:|
| **1,000** | 13 MB | **~1 second** (no index) |
| **10,000** | 133 MB | **~5 seconds** (no index) |
| **50,000** | 663 MB | **~22 seconds** (no index) |
| **105 real Word docs** | 1,878 MB | **~4 seconds** without index, **0.24 seconds** with index |

10× more files doesn't mean 10× longer — peekdocs processes files in parallel across multiple CPU cores.

### Plain-text stress test

We also tested with small .txt files (~113 bytes each) to see how peekdocs handles extreme file counts:

| Files | Search time |
|------:|------------:|
| 10,000 | 1.4 seconds |
| 50,000 | 4.1 seconds |
| **1,000,000** | **90 seconds** |

**What does testing 1,000,000 files prove?** These were tiny text files (~113 bytes each), not real documents — nobody has a million small .txt files. The test confirms that peekdocs doesn't crash, doesn't run out of memory, and produces correct results at extreme scale. It's a stress test of the software's stability, not a realistic performance benchmark. The mixed-format results above are what real-world performance looks like.

### Should you build an index?

For most users, direct search is fast enough — just click Run Search. An index helps when you have large files or search the same folder repeatedly:

| Situation | Index helps? | Why |
|-----------|:-----------:|-----|
| Large files (PDFs, Word, Excel) | **Yes** | Skips expensive parsing — about 18× faster on the 105-Word-doc test in the Performance section |
| Same folder searched repeatedly | **Yes** | Pre-pays parsing cost once |
| Files on a network drive | **Yes** | Reads local index instead of files over the network |
| Small files, small folder | **No** | Direct search is already fast enough |
| One-time search you won't repeat | **No** | Build time won't be recouped |

To try it: click Build Index in Manage Indexes (Tools menu) or run `peekdocs --index`.

### First-run timing and the banner notice

The first time peekdocs searches a folder, it builds the search index by reading every file once. This can take from a few seconds (small folders) to a few minutes (thousands of files, large PDFs, or scanned documents). Every search after that uses the index and runs in milliseconds.

To make this expectation clear up front, peekdocs prints a short notice in the CLI banner when the search folder has no index yet:

```
Note: no search index for this folder yet — the first search builds
  one (may take longer); subsequent searches are much faster.
  Use --no-index to skip indexing entirely.
```

The notice is shown only when it's relevant — peekdocs respects every existing CLI contract:

| Scenario | Notice shown? |
|---|:---:|
| Cold folder (no `.peekdocs.db`) — interactive search | ✓ shown |
| Warm folder (index exists) | — not shown |
| `--no-index` flag passed | — not shown |
| Non-search command (`--check`, `--runs`, `--diff`, `--list-files`, `--clear*`, `--index*`, `--config`) | — not shown |
| Quiet mode (`-q` or `-qq`) — banner suppressed entirely | — not shown |
| `--stdout` JSON output mode — JSON pipeline stays clean | — not shown |
| `--runs --json` / `--diff --json` — machine-parsed output stays clean | — not shown |

Folder detection is `-d`/`--directory`-aware, so running `peekdocs -d /some/other/folder TODO` checks that folder, not the current directory.

If you'd rather avoid indexing entirely, add `--no-index` to your CLI command or uncheck **Use Index** in the GUI. Searches will then read files directly each time — fine for one-off searches, slower for repeated searches in the same folder. See the [Why is my first search slow but later searches are fast?](docs/TROUBLESHOOTING.md) FAQ entry for additional notes including the `2>/dev/null` idiom for absolutely silent automation.

**Cold-cache first search even with the index already built.** Once the index exists, a fresh terminal session's first search is still slower than the next — typically a few seconds vs. half a second — and there's no rebuild involved. That's the OS filesystem cache being cold for the `.peekdocs.db` file (often hundreds of MB), Python interpreter startup paid by each fresh invocation, and the `refresh_index` `os.stat()` pass hitting disk on its first walk. After the first search in a session, peekdocs is sub-second. The same FAQ entry above covers this in more detail along with a way to pre-warm the cache via a scheduled job.

**Network folders:** If your files are on a network drive, searches will be slower because every file must be read over the network. Building an index is strongly recommended — the first build is slow, but all subsequent searches query the local index instead.

**Why Python?** Python was chosen because it has mature, well-established libraries for every file format peekdocs supports — PyMuPDF for PDFs, python-docx for Word, openpyxl for Excel, python-pptx for PowerPoint, and dozens more. In C++ or Rust, equivalent libraries either don't exist or would require years of integration work. Python also runs on Windows, macOS, and Linux without recompilation, installs with a single `pip` command (no compiling from source), and produces readable open-source code that anyone can inspect or extend. The Python API means any Python programmer can call peekdocs directly from their own scripts. As for speed: the performance-critical work — PDF decoding, ZIP decompression, regex matching — is handled by C-backed libraries under the hood. Python orchestrates; C does the heavy lifting. Multiprocessing (separate OS processes, not threads) means Python's GIL (Global Interpreter Lock — a concurrency limitation) is not a factor.

## Platform Notes

**Tested on:** macOS (development machine), Windows 10/11, and Linux Mint 22.3 (Cinnamon) in a VirtualBox VM on Windows. The CLI and GUI work on all three platforms.

- **High-DPI displays (4K monitors)** — if buttons overlap or text looks too large, use the **Text Size** dropdown on the bottom-right toolbar to adjust. Normal is recommended for most screens
- **Antivirus software (Windows)** — some antivirus programs flag Python scripts as suspicious. If peekdocs is blocked, add your Python installation or the peekdocs folder to your antivirus allow list
- **Files locked by other programs (Windows)** — Windows locks files that are open in another program. If peekdocs reports "permission denied" on a file, close the program that has it open and search again. Errors are logged to `peekdocs_errors.log`
- **Corporate firewalls** — if `pip` or `pipx` can't download packages, use the [Standalone Download](#option-a-standalone-download-recommended-for-most-users) (no Python, no network needed beyond the initial download) or the ZIP-based pipx install (described under Option B's "No git?" subsection)
- **macOS file picker vs Windows** — on macOS, the file picker includes a preview panel; on Windows, it does not — this is an OS difference, not peekdocs
- **Linux GUI requires python3-tk** — the CLI works without it, but `peekdocs-gui` needs tkinter. Install with `sudo apt install python3-tk` (see [Prerequisites](#prerequisites))

### File Handling

peekdocs handles a wide range of real-world file issues automatically on all platforms:

| Issue | Windows | macOS | Linux | What happens |
|-------|:-------:|:-----:|:-----:|-------------|
| Word/Excel lock files (`~$`) | Yes | Yes | Rare | Silently skipped |
| System files (Thumbs.db, .DS_Store) | Yes | Yes | — | Silently skipped |
| Temp files (`~`) | Yes | Yes | Yes | Silently skipped |
| Symlinks | Rare | Yes | Yes | Silently skipped |
| Password-protected archives | Yes | Yes | Yes | Reported with clear message |
| Cloud-only placeholders (OneDrive, iCloud) | Yes | Yes | Rare | Reported: "download the file first" |
| Path length limit (260 chars) | Yes | — | — | Files in archives silently skipped |
| Raw .gz files (not tar) | Yes | Yes | Yes | Decompressed and searched |
| SSL .key files | Yes | Yes | Yes | Detected as non-Keynote, skipped |
| BOM in text files | Common | Rare | Rare | Stripped automatically |
| macOS resource forks (`._`) | — | Yes | — | Silently skipped |
| Named pipes / sockets | — | Possible | Yes | Detected via stat(), skipped |
| Virtual filesystems (/proc, /sys) | — | — | Yes | Excluded from recursive search |
| Corrupted files | Yes | Yes | Yes | Logged to error log, search continues |

See [File-handling details by platform](docs/USER_GUIDE.md#file-handling-details-by-platform) in the User Guide for the reasoning behind each row and platform-specific behavior. For installation and runtime gotchas, see [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## Preparing Your Documents for Searching

Most digital files (PDFs from banks, Word docs, emails, spreadsheets) are already searchable — just point peekdocs at the folder and search. No preparation needed.

**For paper documents** (tax returns, receipts, old letters), you'll need to scan them first:

1. **Scan at 300 DPI** — this is the sweet spot for text recognition. Lower resolutions produce poor OCR results. Most scanners default to 300 DPI.
2. **Save as searchable PDF** — modern scanners with built-in OCR (like the Fujitsu ScanSnap) automatically embed a text layer in the PDF. peekdocs reads these directly — no OCR flag needed.
3. **If your scanner doesn't have OCR** — save as PDF, JPG, or PNG. peekdocs can still search these using its OCR feature (enable the OCR checkbox in the GUI or use the `-O` flag in the CLI). Requires [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) to be installed.
4. **Organize by topic, not by date** — folders like `Tax Returns`, `Insurance`, `Receipts` make it easier to target searches. But peekdocs also works fine with one big folder and recursive search.
5. **Phone camera works too** — take a photo of a document and save it as JPG or PNG. peekdocs can OCR it. For best results, photograph in good lighting with the document flat and square in the frame.

**Consider going paperless.** Scanned PDFs are widely accepted for tax and financial records — the IRS has accepted digital records since 1997, and banks, brokerages, and the IRS itself deliver documents as PDFs. Scan your paper receipts and tax returns, then organize them into folders. Once digitized, peekdocs can search years of documents in seconds — no more digging through shoeboxes. (Consult your tax advisor for your specific situation.)

**Tip:** Before selling or donating a computer, search your entire documents folder for sensitive data — passwords, account numbers, and personal information you may have forgotten about.

## Questions and troubleshooting

Common questions, installation gotchas, and platform-specific issues are collected in **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** — ~90 entries covering search behavior, indexes, OCR, scheduling, email archives, network drives, uninstall steps, PDF report caveats, and more.

Quick diagnostic: run `peekdocs --check` (CLI) or open **Tools → System Check** (GUI). Both report your Python version, dependency status, Tesseract availability, SQLite version, and free disk space — most install-time issues resolve there.

Found a bug or have a feature idea? [Open an issue on GitHub](https://github.com/exbuf/peekdocs/issues).

## Glossary

The full glossary of peekdocs terms (FTS5, regex modes, deterministic, exit codes, Tesseract, jq, SIEM, MSP technician, and ~70 more — including a list of common Python networking libraries peekdocs deliberately does *not* use) lives in **[docs/GLOSSARY.md](docs/GLOSSARY.md)**.

## For IT and Security Teams

If you're evaluating peekdocs for your organization, here are the answers to the questions your security team will ask:

| Question | Answer |
|----------|--------|
| **Does it send data anywhere?** | No. peekdocs has no network calls, no telemetry, no tracking, no analytics, no phone-home. It never connects to the internet. All processing happens locally on the user's machine. |
| **Does it store what it finds?** | Yes — results are written to disk as `.txt` and `.docx` reports (plus optional CSV, JSON, PDF, HTML). These files contain matched text from your documents. Use **Delete on Close** to automatically remove them when you close the app, or **Wipe Session** (Tools → Clear Files) to remove them immediately. Reports are blocked from opening in cloud apps. If your search folder is cloud-synced, peekdocs automatically redirects reports to a safe local folder (`~/peekdocs_reports`) so no report files are uploaded. |
| **What about the search index?** | The optional search index (`.peekdocs.db`) is a SQLite database that contains the extracted text of every indexed file — this means it holds a searchable copy of your document content, including any sensitive data in those documents. Treat the index file with the same care as the documents themselves. The index is never required (uncheck "Index" to search files directly), and **Wipe Session** (Tools → Clear Files) deletes the index along with all result files, preview content, and search history. If you index a folder containing sensitive documents, consider deleting the index when you're done. |
| **Can it access files the user can't?** | No. peekdocs runs with the user's own file permissions. It cannot read files the user doesn't already have access to. It does not elevate privileges or bypass OS security. |
| **What kind of tool is it?** | A general-purpose local text search application. It reads documents you point it at, reports what it found, and writes nothing else. See [Disclaimer](#disclaimer). |
| **What does it install?** | Python packages only — no system services, no drivers, no registry entries, no background processes. It runs when launched and stops when closed. |
| **Can it modify or delete user files?** | No. peekdocs only reads user files. It creates its own report and index files (all prefixed with "peekdocs" for easy identification) but never modifies, moves, or deletes any user documents. |
| **Is the source code available?** | Yes. Fully open-source under the MIT License. Available for audit at [github.com/exbuf/peekdocs](https://github.com/exbuf/peekdocs). |
| **How is it installed?** | Via `pipx` from the public GitHub source (`pipx install --force git+https://github.com/exbuf/peekdocs.git`) — fully auditable, no unsigned executables required. (PyPI upload is planned.) |

*For the deep dive — every file peekdocs writes (path, contents, sensitivity rating, cleanup), plus a documented list of risks that are outside the application's control (process arguments, swap space, force-kill, backup software, etc.) — see **[docs/SECURITY.md](docs/SECURITY.md)**.*

## Testing

**Unit tests** — 627 pytest tests that verify correctness: exact match counts, error messages, edge cases, argument validation, regex patterns, expression parsing, range queries, and more.

```bash
pytest tests/ -v
```

**Integration test** — end-to-end runs of every search mode and flag combination. Verifies that flag combinations run without crashing, all output formats are generated, file type coverage across 100+ sample files is reported, and match counts are confirmed stable. Results are saved to `peekdocs_global_test_results.txt`. The bash script is run on macOS and Linux, the PowerShell script on Windows, before each release. See the script headers for details.

```bash
cd samples/test-files
bash peekdocs_global_test_unix.sh "test file for peekdocs"    # macOS / Linux
# Windows: powershell -ExecutionPolicy Bypass -File peekdocs_global_test_windows.ps1 "test file for peekdocs"
```

## Contributing

Ideas, bug reports, and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

If peekdocs saves you time, star the repo and share feedback — it helps others discover the tool.

## Author

Built by [Robert D. Schoening](https://robertdschoening.com) — electrical engineer, U.S. software patent holder, and independent developer. Developed with assistance from [Claude Code](https://claude.ai/code) by Anthropic. All architecture, review, testing, and maintenance performed by the author.

**Why I built it.** I built peekdocs to solve a problem I had myself: searching large collections of mixed-format documents locally, privately, and efficiently. It also became an opportunity to learn AI-assisted software development and explore what a single developer can build with today's tools. After relying on it in my own workflow, I decided to share it as free and open-source software under the MIT License.


## Disclaimer

peekdocs is provided as a general-purpose local text-search tool under the [MIT License](LICENSE), offered "as is" without warranty of any kind.

Regex Search performs pattern matching against text. Results depend entirely on the patterns the user supplies, and may include false positives or miss content that does not match those patterns. Review results in context before making decisions.

The tool is not designed or intended for high-assurance or safety-critical use cases. Users remain solely responsible for how they use and interpret its output.

## License

Copyright (c) 2026 Robert D. Schoening. This project is licensed under the [MIT License](LICENSE).
