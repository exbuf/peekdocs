# Changelog

All notable changes to docsearch are documented here.

## [0.2.0] — 2026-03-30

### Added
- **Email support** — search .eml (standard email), .msg (Outlook), and .pst (Outlook mailbox archive) files. Searches headers (From, To, Subject, Date) and message body
- **Archive support** — search inside .zip, .tar, .gz, .bz2, .tgz, .7z, and .rar archives transparently. Each match shows which file inside the archive it came from
- **Legacy Office formats** — search .doc (Word 97-2003), .xls (Excel 97-2003), and .ppt (PowerPoint 97-2003) files
- **Email alerts** — optional SMTP email notifications when scheduled suite runs detect failures. Configure via GUI (Configure Email Alerts in suite panel)
- **Consolidated suite .docx report** — formatted Word document with color-coded PASS/FAIL summary table, per-stage details, report fingerprint for tamper detection, and source file manifest listing every document in scope
- **View Suite Report button** — appears in suite panel after each run to open the .docx report directly
- **Results preview pane** — inline scrollable preview in the main GUI window showing matches with highlighted terms, filenames, and directory paths after each search
- **Determinate progress bar** — shows actual file count progress (e.g., "47/200 files") for direct file scanning; indeterminate spinner for indexed searches
- **Text Size dropdown** — Small/Normal/Large/Extra Large scaling for all GUI text and widgets. Auto-saves to config. Located on bottom toolbar
- **Advanced Search Options popup** — moved from collapsible inline panel to a separate window, keeping the main window compact
- **First-run welcome dialog** — getting-started guide appears on first launch with 4-step quick start
- **Clear Error Log button** — on bottom toolbar next to View Error Log
- **Clear Auto-Run History button** — in suite panel next to Open Auto-Run History
- **42 supported file types** (up from 25) — documents, spreadsheets, emails, archives, data/config files, and images (OCR)
- **Comprehensive -h help** — rewritten with description, usage syntax, file type list, and sections grouped by purpose (Search Modes, Filters, Output, Index, Settings)
- **Troubleshooting section** expanded to 31 entries covering Windows, macOS, and Linux
- **Compliance Wizard** — pick an industry template (9 available), review and customize checks, create a complete compliance suite with one click. Templates for Financial Services/SOX, Healthcare/HIPAA, Legal, Government, Manufacturing/ISO, Education/FERPA, Real Estate, Insurance, and HR
- **Run Suite button** — on the main screen next to Run Search; opens the Manage Suites panel. Green when suites exist, red when none
- **Suite report preview** — after a suite run, the txt report is displayed in the main preview pane
- **Compliance and auditing guide** with industry examples, step-by-step instructions, and 9 pre-built sample suites
- **Limits and Constraints documentation**
- **Files Created by docsearch reference** — complete catalog of every file docsearch generates
- **Index and subfolder documentation** — explains how indexes work across folder hierarchies and with search suites

### Changed
- **"Save Settings" buttons renamed** — Search Bar button is now "Save Search" (saves to collection for suites); Advanced Search Options button is now "Save Defaults" (saves to ~/.docsearchrc)
- **Advanced Search Options, Search Suites, Manage Indexes** consolidated onto one row
- **README restructured** — slim landing page with detailed docs in `docs/` directory
- **Marketing summary** updated to mention emails, archives, email alerts, and all three interfaces (terminal, GUI, API)
- **Introduction** lists Word docs before PDFs (primary audience is Windows users)
- **.docsearch_collection.json excluded** from search results on all platforms (was already hidden on macOS/Linux but not Windows)
- **docsearch_errors.log and .docsearchrc** also excluded from search results

### Fixed
- Last run label disappeared when auto-run schedule set to Off
- Auto-run suite reports now include .docx format (was only TXT and JSON)
- Suite reports auto-generated on manual runs (previously only on scheduled runs)
- CTkToplevel widget variables reset during initialization (recursive checkbox not persisting)

## [0.1.0] — 2026-03-28

### Initial release
- Search 25 file types (PDF, DOCX, XLSX, PPTX, EPUB, ODT, ODS, ODP, RTF, HTML, CSV, JSON, XML, YAML, YML, TOML, MD, RST, TEX, INI, CFG, SQL, LOG, TSV, TXT)
- CLI with full flag set (-a, -A, -B, -c, -e, -f, -m, -n, -o, -O, -p, -r, -R, -s, -sa, -t, -v, -w, -W, -x, -z)
- GUI with customtkinter (docsearch-gui)
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
- CSV and JSON export
- Save and append report archiving
- Library API (Python search() function)
- Cross-platform: Windows, macOS, Linux
