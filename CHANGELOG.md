# Changelog

All notable changes to peekdocs are documented here.

## [1.0.0] — 2026-05-22

First 1.0 release. Brings a major new feature (Regex Search), removes PII Scan to eliminate legal liability, adds Schedule Search, expands the Python API, and rewrites large portions of the README. Not yet published to PyPI.

### Added

- **Regex Search** — new purple GUI button next to Standard Search. Run up to 10 named regex patterns per collection, each executed separately with per-pattern results, View Files / View Text buttons, and a Cancel button (turns red mid-run). Create unlimited named collections via Save Collection As / Restore From Collection — keep separate profiles for different tasks (code patterns, log analysis, invoice extraction). Clear All erases all patterns; Restore All undoes the last clear. Help screen includes 50 common regex patterns to copy and paste, custom-pattern guidance (regex101, web search, AI), and Performance/Index notes. Always scans files directly (index bypassed) for fresh results
- **Regex Search screen-only mode** — "Do not save regex match contents to reports" checkbox displays results in a screen-only popup that is never written to disk, piped, or returned via API. Inherited from the removed PII Scan design for sensitive-data workflows
- **`--regex-collection NAME` CLI flag** — run a saved regex collection from the command line with per-pattern progress. Supports `-r`, `-d DIR`, `--stdout` for JSON output, and `--timestamp` for unique report filenames. `--regex-collection --list` lists all saved collections
- **`--timestamp` for `--suite` and `--regex-collection`** — both batch CLI paths now honor `--timestamp` and produce uniquely named reports (`peekdocs_suite_results_YYYYMMDD_HHMMSS.{txt,docx}` and `peekdocs_regex_results_YYYYMMDD_HHMMSS.{txt,docx}`). Required for IT automation that loops over multiple suites or collections without overwriting reports
- **Schedule Search dialog** (Tools menu) — generates a ready-to-paste cron (Mac/Linux) or schtasks (Windows) command for any saved search suite or regex collection. Step-by-step instructions, frequency picker (daily/weekly/monthly), time selector, optional `--timestamp` and `--stdout`, Copy to Clipboard button. No terminal experience required
- **Clean Folder** (Tools menu) — browse to any folder and selectively delete peekdocs-created files. Includes a review-before-delete confirmation dialog
- **`run_suite()` and `run_regex_collection()` Python API** — run a saved suite or regex collection programmatically and get a `SuiteResult` / `RegexCollectionResult` with per-search/per-pattern matches, files searched, elapsed time, and skipped entries. Added `list_suites(directory)` and `list_regex_collections()` for enumeration
- **Search Wizard screenshot** in README, with 21 pre-built search patterns documented
- **Multiple new README screenshots** — Search Suites, Advanced Search Options, heart search (main/HTML/docx), highlighted Word report, HTML report
- **`Who Is It For?` README restructure** — audience profiles (developers, researchers, technical writers, investigators, archivists, IT, consultants, business power users, engineers, AI/ML, data researchers, programmers, home users, email archives) with outcome-oriented value statements
- **`Why Not Just Use Grep?` README section** — credit to grep, side-by-side capability table covering 20+ features, honest summary on when each tool is appropriate
- **FAQ entries** — email export, post-search workflow, sharing reports, default folders, search comparison
- **README intro sentence** describing CLI, GUI, and Python API interfaces and the type-and-click workflow
- **CLI exit codes documented** in README, plus zero-match report behavior and non-recursive search hints
- **Tooltips** with section titles ("Main Search Bar:", "Search Folder Bar:", "Results Preview:") on Search Suites buttons, Delete Everything Now, Clear Preview, and many others
- **Tagline reworked** — "Easy to Use", "Free and Open-Source (MIT License)", "yellow-highlighted reports" added; project tagline now synchronized across README, pyproject.toml, CLI banner, GUI, and CLAUDE.md

### Removed

- **PII Scan** — entire feature deleted on 2026-05-21 (~1,000 lines across 15 files): GUI button, CLI flag (`--pii-scan`), sensitive pattern detection (`sensitive_patterns.py`), all tests (`test_pii_patterns.py`), and every PII-related reference in docs and UI. Eliminated to remove implicit legal/compliance promises. Regex Search replaces it for user-defined sensitive-data workflows
- **Compliance-adjacent language** purged from all documentation. Example names changed from "security audit" to neutral alternatives ("code patterns", "log analysis", "invoice extraction"). peekdocs is positioned as a general-purpose search tool, not a security or compliance tool
- **"Coming soon" features** (Scheduled scans, Search templates) removed from README — Schedule Search shipped and Search Wizard provides templates
- **"Most likely early adopters" subsection** removed from README — covered by the new audience profile table

### Changed

- **Search button renamed to Standard Search** — green main-screen button now reads "🔍 Standard Search" (was "🔍 Search"), widened to 220px. Disambiguates from the purple Regex Search button. All post-search reset paths updated so the label stays consistent after completion or cancel. Tooltips, Step 3 badge label, and disambiguation sections in README and help text updated
- **`Standard Search vs Regex Search` decision table** in main help screen — when to use each, with green/purple button labels and a feature-by-feature breakdown
- **`Regex Search vs Search Suites` section** in main help — clarifies that suites group saved searches (any mode), while regex collections group regex patterns only
- **Regex Search results popup** — per-pattern View Files buttons (replaces show-files checkboxes), per-pattern match counts, View Text with highlighted content
- **README "Why peekdocs?" tightening** — credit paragraph compressed, off-topic LibreOffice tangent removed from highlighted-reports bullet, three application-feature bullets merged, summary shortened
- **Cloud language softened** — "blocks" → "avoids" across all docs for cloud-based applications (Google Docs, Apple Pages)
- **PII/security definitive claims softened** in remaining mentions before full PII removal — "ensures" → "helps prevent", "finds" → "scans for patterns"
- **CLI help text reorganized** — `--regex-collection` and related flags grouped with `--suite` in Settings & Info section

### Fixed

- **`--stdout` with `--regex-collection`** — JSON output now correctly suppresses banner and progress output; works in pipelines
- **Regex Search hang on large match counts** — lazy widget creation for pattern rows, report match cap at 10000, background-thread report writing prevents GUI freeze
- **Cancel button** — skips report writing and results popup when cancelled mid-run; cleans up partial state
- **Config persistence** for dynamic `regex_search_*` keys (and former `pii_scan_*` keys) — settings now survive across sessions
- **Results Preview double-highlighting** with capturing-group regex patterns
- **Regex Search settings persistence** on Close — pattern names, regex text, and enabled state retained; inline flags stripped from combined regex before execution
- **Indexed whole-word search** — no longer matches inside underscored identifiers
- **PDF and HTML report highlighting** for regex, wildcard, whole-word, and Boolean expression modes
- **View Files button alignment** — fixed inner-frame width to match canvas; button now aligns to right edge with proper pack ordering
- **FAQ correction** — clarify that grep results inside the source tree (XML namespaces, URLs in help text) are not network calls
- **Three exaggerated claims softened** — removed "air-gapped" (peekdocs runs locally but doesn't enforce air-gap), "milliseconds" (replaced with real benchmarks), and inflated search-mode counts
- **Pre-publication hardening** — PyPI URL placeholders, path sanitization in error log, `.gitignore` for `SearchTheseDocuments`, PyPI keywords, JSON `directory` field, README example fix

## [0.3.41] — 2026-05-06

### Added

- **100+ file types** — added Jupyter notebooks, .env, Dockerfile, CSS, SCSS, Scala, Lua, GraphQL, Protobuf, Terraform, .properties, .gradle, .cmake, .conf, Apple Numbers/Keynote, Visio .vsdx, and 31 source code/engineering formats (up from 86)
- **Search Suites** — group saved searches and run them together with per-suite output format options (DOCX, TXT, HTML, CSV, JSON, PDF) and progress bar during execution
- **--pii-scan CLI flag** — terminal-based PII scanning, safe to pipe, never shows actual sensitive data; works on remote/SSH servers
- **--open flag** — auto-open reports after search; auto-enables the requested output format (docx, txt, pdf, json, html)
- **--list-files CLI command** — show all peekdocs-created files in the current directory
- **--config --reset CLI command** — restore factory default settings
- **--clear and --clear-all CLI commands** — delete peekdocs files from the current directory
- **Line proximity search (-P N flag)** — find terms within N lines of each other across all file types
- **-q and -qq flags** — quiet mode (suppress banner) and minimal output
- **HTML report for suites** — search suites now generate HTML reports alongside DOCX and TXT
- **Cloud folder protection** — blocks searches to cloud-synced folders (Google Drive, OneDrive, iCloud, Dropbox); auto-redirects report output to ~/peekdocs_reports
- **Safe file opening** — blocks cloud-uploading apps (Apple Pages, Google Docs) from opening .docx and PDF reports to prevent data leaks
- **Delete on Close checkbox** — auto-delete all reports, index, and tracked session folders when the app closes
- **Delete Everything Now button** — one-click cleanup of all peekdocs files including search index, terms, and folder fields
- **Clear Preview button** — instantly clear the results preview pane
- **Clear History on Close option** — auto-clear search history when the app closes
- **Clear Files popup** — per-file checkbox popup replacing multiple clear buttons
- **Recent Searches persistence** — recent searches now saved across sessions in ~/.peekdocsrc
- **Hover Text ON/OFF toggle** — on main screen bottom row to control tooltips
- **Step 1–4 badges** — blue step labels replace numbered text on the main screen
- **PII Scan on main screen** — moved from Tools menu to a prominent green/teal button next to Search
- **PII Scan independence** — PII scan uses its own folder, recursive setting, and file types, independent from main search
- **PII scan report improvements** — READ BEFORE ACTING disclaimer, Think Before You Print warning, page break before summary, category name in View Text window
- **Suites button on main screen** — moved from Tools menu for easier access
- **README button** — added to bottom row next to User Guide
- **View Report HTML button** — added to main screen report row
- **Network folder support** — documented and tested searching network/NFS/SMB shares
- **Performance section** — benchmarks for 1K/10K/50K/1M files with real-world data (105 Word docs in 4.4s, index: 0.24s)
- **Glossary of technical terms** — added to both README and User Guide
- **Data Architecture section** — for IT and security teams in README
- **PyInstaller build script** — standalone .exe/.app builds with GitHub Actions release workflow
- **Integration test suite** — added alongside existing unit tests

### Fixed

- **Linux PII scan hang** — fixed blocking issue on Linux
- **Linux tooltip flicker and sticking** — use delayed hide instead of pointer check
- **Linux SPDX license format** — fixed PEP 639 compatibility for setuptools
- **Linux Browse double-click behavior** — documented and added tooltip note
- **Windows popups behind main window** — fixed Excluded Files, Matched Files, and all other popups appearing behind the main window
- **Windows dark mode** — fixed white flash, invisible popups, stuck-offscreen popups, and CTkToplevel crash
- **Windows path-too-long error** in tar archive extraction
- **Windows Unicode progress bar** — fixed encoding issue
- **Four Windows file handling issues** — hardened for cross-platform edge cases
- **Named pipes, sockets, and virtual filesystems** — prevent hangs during file discovery
- **.env and Dockerfile discovery** — handle dotfiles and extensionless files correctly
- **--open with -sa** — now opens the accumulated report, not the regular one
- **--pii-scan flag order** — works with -r in any position
- **Duplicate version/CPU lines** in CLI banner output
- **AND mode** — corrected 'same paragraph' to 'same line' with nuance
- **Whole-word matching** for terms with punctuation
- **View Text highlighting** for quoted phrases
- **Duplicate Finder crash** — added missing @staticmethod to _format_file_size
- **File Inventory crash** — removed stray @staticmethod decorator
- **Suite runner crashes** — fixed _update_status missing method, subprocess hang, 0-file count parsing, inflated file counts, and match limit issues
- **Max matches confusion** — reverted blank-means-unlimited; explicit 0 means no limit, defaults shown as 1000/100
- **Confusing status** when max matches caps the report
- **PII scan false positives** — fixed credit card matches on URLs, SSN matches on DOIs/ISBNs, password matches in URL query parameters
- **macOS file opening** — fall back to TextEdit when default app fails; Linux fallback added too
- **Dark mode fixes** — themed all 35 popups, fixed TOC text color, menu separators, PII scan status text, Search Wizard plain tk widgets

### Changed

- **GUI layout overhaul** — Search and PII Scan buttons enlarged with #76BA1B green/teal colors; AND/OR toggle changed to checkbox blue; Advanced and Wizard as icon buttons on options row; preview moved directly under status line; Cancel mode for Search and PII Scan buttons
- **Rename Proximity to Word Proximity** — clarify that line proximity is CLI-only
- **Rename Run Search to Search** — shorter button label
- **Rename Reset Saved Defaults to Restore Factory Settings**
- **Rename App Files to View All peekdocs Files** in Tools menu
- **Rename DO_NOT_SEARCH_ prefix to peekdocs_ prefix** for easier file identification
- **PII Scan report removed as file** — results shown on screen only, no file written
- **PII credential detection expanded** — added passcode, pin, passphrase, signin, logon, signon, p/w, user_id, uid, login, username keywords with hyphen/underscore variants
- **Token detection narrowed** to api_token/auth_token/access_token only (reduces false positives)
- **PII Scan folder persistence** — remembers folder between invocations and across sessions
- **Auto-save** for text size, appearance, hover text, preview size, and CSV/JSON/PDF/HTML checkbox states
- **Moved PII Scan and Manage Indexes** from main screen to Tools menu, then PII Scan back to main screen
- **Renamed Manage Indexes to Indexes** — shows search folder in popup
- **CLI banner reorganized** — version at top, CPU cores and README URL prominent, search modes at bottom, common options section added
- **Report headers** — added peekdocs version, 'Saved as' filepath, removed boilerplate
- **Browse/+Folder/Single File enclosed in visible frame** with border
- **Oversized files now shown in Excluded Files list** with Max File Size / Max Matches interaction documented
- **Dependencies documented** in User Guide and README prerequisites

## [0.3.0] — 2026-04-16

### Added

- **Tools menu** — eight new folder analysis and user utilities: File Inventory, Duplicate Finder, Large Files, Empty Files, Recent Changes, Protected Files, Search History, and Bookmarks
- **Search Options group** on main screen with AND/OR toggle buttons, Recursive and Whole Word checkboxes, and help button
- App Size and Preview Size dropdowns on the Results Preview header, both persisted between sessions
- Status line now leads with files-searched count
- Recursive and Whole Word default to ON at startup
- **Multi-folder search** — search across multiple folders at once via +Folder button or semicolon-separated paths
- **HTML export** — new `-o html` output format with styled, highlighted results for sharing via email or browser
- **Search status shows active modes** — status line now displays AND/OR, Regex, Fuzzy, Wildcard, Whole Word, Inverse, and Index indicators while searching
- **Dark mode** — Appearance toggle in Tools menu: Dark, Light, or System (follows OS). Saved between sessions
- PII pattern test suite (74 tests validating sensitivity and specificity of all 8 categories)
- Index corruption now notifies the user with a warning dialog and logs to peekdocs_errors.log
- Config file (~/.peekdocsrc) now written with owner-read-write-only permissions

### Fixed

- Wildcard search now matches punctuation (e.g., `budg*` matches "budget!" and "budget.")
- Single-file selection no longer persists after changing the search folder

### Removed

- **Compliance feature removed — peekdocs is now a focused home-user document search tool.** The following features were removed to simplify the product, eliminate legal-exposure concerns, and match peekdocs's actual audience of individuals and small teams searching their own files:
  - Compliance Wizard and the 9 industry starter templates (SOX, HIPAA, Legal, Government, ISO, FERPA, Real Estate, Insurance, HR)
  - Search Suites (Manage Suites panel, suite builder, cascade mode, pass/fail criteria, suite execution)
  - Auto-run scheduling for suites
  - Email alerts (SMTP configuration, test email, alert sending)
  - Suite reports (`.txt`/`.docx`/`.json` consolidated suite reports, stage reports, source file manifest, report fingerprint)
  - Search Wizard pattern categories that were compliance-specific
  - `compliance_templates.py` and `email_alert.py` modules (deleted)
  - `docs/COMPLIANCE_GUIDE.md` (deleted)
- Saved searches are preserved. Collection files with a legacy `test_suites` key continue to load — the key is silently dropped.

### Changed

- PII Scan, Save Search, Load Search, Search Wizard, and all other core features are unchanged and fully supported.
- README and User Guide rewritten to focus on home-user workflows: search, PII Scan, saved searches, highlighted reports.
- Disclaimers simplified — peekdocs is now described straightforwardly as a local document search and pattern-matching tool.

## [0.2.0] — 2026-03-30

### Added
- **Sensitive Data Scan** — one-click scan for PII and sensitive data: SSNs, credit cards, tax IDs, emails, phone numbers, passwords, dates of birth, and large dollar amounts. Results categorized by severity (HIGH/MODERATE/INFO) with per-file details, line numbers, and a highlighted `.docx` report with yellow-highlighted matches. Click any category to see affected files
- **Email support** — search .eml (standard email), .msg (Outlook), and .pst (Outlook mailbox archive) files. Searches headers (From, To, Subject, Date) and message body
- **Archive support** — search inside .zip, .tar, .gz, .bz2, .tgz, .7z, and .rar archives transparently. Each match shows which file inside the archive it came from
- **Legacy Office formats** — search .doc (Word 97-2003), .xls (Excel 97-2003), and .ppt (PowerPoint 97-2003) files
- **Email alerts** — optional SMTP email notifications when scheduled suite runs detect failures. Configure via GUI (Configure Email Alerts in suite panel)
- **Consolidated suite .docx report** — formatted Word document with color-coded PASS/FAIL summary table, per-stage details, report fingerprint for tamper detection, and source file manifest listing every document in scope
- **View Suite Report button** — appears in suite panel after each run to open the .docx report directly
- **Results preview pane** — inline scrollable preview in the main GUI window showing matches with highlighted terms, filenames, and directory paths after each search
- **Matched files popup with line numbers** — clickable "View N matched file(s)" link on the status line opens a popup listing each file with match count and line numbers (e.g., "contract.docx (3 matches — lines 12, 47, 89)")
- **View Text (with line numbers)** — new button in the matched files popup that displays the file's extracted content with line numbers and highlighted matches, scrolled to the first match. Works for all 46 file types
- **Determinate progress bar** — shows actual file count progress (e.g., "47/200 files") for direct file scanning; indeterminate spinner for indexed searches
- **Text Size dropdown** — Small/Normal/Large/Extra Large scaling for all GUI text and widgets. Auto-saves to config. Located on bottom toolbar
- **Advanced Search Options popup** — moved from collapsible inline panel to a separate window, keeping the main window compact
- **First-run welcome dialog** — getting-started guide appears on first launch with 4-step quick start
- **Clear Error Log button** — on bottom toolbar next to View Error Log
- **Clear Auto-Run History button** — in suite panel next to Open Auto-Run History
- **46 supported file types** (up from 25) — documents, spreadsheets, emails (.eml, .msg, .pst, .mbox), archives, Apple Pages, calendars (.ics), contacts (.vcf), data/config files, and images (OCR)
- **Comprehensive -h help** — rewritten with description, usage syntax, file type list, and sections grouped by purpose (Search Modes, Filters, Output, Index, Settings)
- **Troubleshooting section** expanded to 31 entries covering Windows, macOS, and Linux
- **Compliance Wizard** — pick an industry starter template (9 available), review and customize checks, create a search suite with one click. Starter templates for Financial Services/SOX, Healthcare/HIPAA, Legal, Government, Manufacturing/ISO, Education/FERPA, Real Estate, Insurance, and HR
- **Run Suite button** — on the main screen next to Run Search; opens the Manage Suites panel. Green when suites exist, red when none
- **Suite report preview** — after a suite run, the txt report is displayed in the main preview pane
- **Import Template** — new button in Manage Suites to load saved searches and suites from an external .json file, merging into the existing collection without overwriting non-conflicting items
- **Export Suite** — new button in Manage Suites to save the selected suite and all its referenced saved searches to a `.json` file for sharing with colleagues, clients, or other machines
- **Max File Size field** — in Advanced Search Options; files over the limit (default 100 MB) are skipped to prevent memory issues. New `--max-file-size` CLI flag. Changing the value automatically rebuilds the index on the next indexed search so results stay consistent
- **Excluded Files view** — "View N excluded file(s)" button appears after each search, opens a popup listing every file that was NOT searched, grouped by reason (unsupported type, prior output files, oversized, hidden, etc.)
- **Compliance and auditing guide** with industry examples, step-by-step instructions, and 9 pre-built sample suites
- **Limits and Constraints documentation**
- **Files Created by peekdocs reference** — complete catalog of every file peekdocs generates
- **Index and subfolder documentation** — explains how indexes work across folder hierarchies and with search suites
- **Search Wizard** — guided search configuration with 21 patterns (SSN, phone, email, dates, dollar amounts, etc.). Pick a type, click Apply, and the search bar is configured automatically
- **Recent Searches dropdown** — button next to the search bar remembers your last 10 searches for quick recall
- **PDF highlighted reports** — optional `.pdf` output with yellow-highlighted matches, matching the `.docx` report style. Enable with the PDF checkbox or `-o pdf` on the CLI
- **App Files button** — bottom toolbar button listing all peekdocs-created files in the search folder with full paths, grouped by category
- **All Collections button** — bottom toolbar button that scans your home directory for all `.peekdocs_collection.json` files, showing saved searches and suites across every folder. Double-click a folder to switch to it
- **Fuzzy search highlighting** — fuzzy matches are now highlighted in the results preview and reports, not just exact matches

### Changed
- **"Save Settings" buttons renamed** — Search Bar button is now "Save Search" (saves to collection for suites); Advanced Search Options button is now "Save Defaults" (saves to ~/.peekdocsrc)
- **Advanced Search Options, Search Suites, Manage Indexes** consolidated onto one row
- **README restructured** — slim landing page with detailed docs in `docs/` directory
- **Marketing summary** updated to mention emails, archives, email alerts, and all three interfaces (terminal, GUI, API)
- **Introduction** lists Word docs before PDFs (primary audience is Windows users)
- **.peekdocs_collection.json excluded** from search results on all platforms (was already hidden on macOS/Linux but not Windows)
- **peekdocs_errors.log and .peekdocsrc** also excluded from search results

### Fixed
- Last run label disappeared when auto-run schedule set to Off
- Auto-run suite reports now include .docx format (was only TXT and JSON)
- Suite reports auto-generated on manual runs (previously only on scheduled runs)
- CTkToplevel widget variables reset during initialization (recursive checkbox not persisting)

## [0.1.0] — 2026-03-28

### Initial release
- Search 25 file types (PDF, DOCX, XLSX, PPTX, EPUB, ODT, ODS, ODP, RTF, HTML, CSV, JSON, XML, YAML, YML, TOML, MD, RST, TEX, INI, CFG, SQL, LOG, TSV, TXT)
- CLI with full flag set (-a, -A, -B, -c, -e, -f, -m, -n, -o, -O, -p, -r, -R, -s, -sa, -t, -v, -w, -W, -x, -z)
- GUI with customtkinter (peekdocs-gui)
- Boolean expression search with AND, OR, NOT, parentheses
- Range queries on dates, dollar amounts, percentages, ages, file metadata
- Fuzzy matching via rapidfuzz
- Wildcard and whole-word matching
- Proximity search
- OCR via Tesseract
- SQLite FTS5 search index with auto-refresh
- Search suites with pass/fail criteria and cascade mode
- Suite scheduling (auto-run) with persistent schedules
- Highlighted .docx and .txt reports
- CSV, JSON, and PDF export
- Save and append report archiving
- Library API (Python search() function)
- Cross-platform: Windows, macOS, Linux
