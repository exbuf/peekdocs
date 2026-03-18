# Claude-DocSearch

If you've ever downloaded years of documents to your local machine and then realized you have no way to search through them — that's exactly why docsearch exists.

I'm a 77-year-old retired electrical engineer who recently discovered Claude Code and used it to build my new website. For years I'd been meaning to back up my Google Docs and Sheets to my local machine — hundreds of files accumulated over a decade — but I kept putting it off because I knew that once they were saved locally, I'd have no easy way to search through them. I also had plenty of other documents that were never in Google to begin with — old Word files, PDFs, text files scattered across folders.

Then it hit me: I could build the search tool myself.

What began as a weekend project took on a life of its own. I kept thinking "what if it could also do this?" and before long, docsearch had grown into something far more capable than I originally imagined. It searches across PDFs, Word docs, spreadsheets, and text files. It supports regex patterns. It works entirely offline, keeping your data private.

I built docsearch for myself, but I'm sharing it because I suspect I'm not the only one drowning in years of documents. If that sounds familiar, I hope this tool helps you as much as it's helped me.

**Overview:** A Python CLI tool that searches through `.docx`, `.pdf`, `.csv`, `.odt`, `.txt`, `.html`, `.xlsx`, `.md`, `.json`, `.rtf`, `.pptx`, `.xml`, `.log`, `.yaml`, `.yml`, `.tsv`, `.epub`, `.ods`, `.odp`, `.toml`, `.rst`, `.tex`, `.ini`, `.cfg`, and `.sql` files in the current directory for one or more search terms. Results are written to `docsearch_results.txt` and `docsearch_results.docx`.

- Results show the full text surrounding each match, so you can understand the context without opening the original document.
- Supports **AND** and **OR** search logic with any number of search terms.
  - **OR**: Show paragraph if it contains term1 OR term2 OR term3, etc.
  - **AND**: Show paragraph if it contains term1 AND term2 AND term3, etc.
- A simple search example can be found in the `docsearch_results.docx` and `docsearch_results.txt` files on GitHub.
  (NOTE: You can view docsearch_results.txt by clicking on it now, but GitHub can't render .docx, .odt, and .xlsx files directly in the browser. So to view the yellow highlighted .docx file and the others, you'll have to download and open them on your local machine. Here's how: .docx opens with Word, Pages, LibreOffice, or Google Docs. Open .odt files with LibreOffice, Google Docs, Word, or Apple Pages. .xlsx files open with Excel, Google Sheets, LibreOffice Calc, or Apple Numbers.)

## Features

- Searches all `.cfg`, `.csv`, `.docx`, `.epub`, `.html`, `.ini`, `.json`, `.log`, `.md`, `.odp`, `.ods`, `.odt`, `.pdf`, `.pptx`, `.rst`, `.rtf`, `.sql`, `.tex`, `.toml`, `.tsv`, `.txt`, `.xlsx`, `.xml`, `.yaml`, and `.yml` files in the directory/subdirectories. Or, with the -t flag, you can restrict your search to specific file types while ignoring the rest.
- Use `-r` flag to search all subdirectories recursively
- Use `-t` flag to search only specific file types (e.g., `docsearch -t pdf,docx budget`)
- Use `-A N` flag to show N lines after each match (e.g., `docsearch -A 5 budget`)
- Use `-B N` flag to show N lines before each match (e.g., `docsearch -B 5 budget`)
- Use `-x` flag for regex pattern searches (e.g., `docsearch -x "\d{3}-\d{3}-\d{4}"`)
- Case-insensitive matching
- Supports multiple search terms with OR logic (finds any match) by default
- Example: `docsearch term1 term2 term3` // any term must appear in the paragraph
- For AND logic (where all search terms must appear in the same paragraph) use the `-a` flag
- Example: `docsearch -a term1 term2 term3`   // all terms must appear in the paragraph
- Use quotes for multi-word phrases (e.g., `"annual report"`)
- Don't separate search terms with commas unless they're part of the search term itself
- Highlights matched terms with `**` markers in `.txt` output and yellow highlighting in `.docx` output, with search terms highlighted in green in the `.docx` header
- Results include document name, file directory path, line number, and matched text
- Timestamped output file
- Generates both `docsearch_results.txt` and `docsearch_results.docx`
- Gracefully handles corrupt or unreadable files — skips them with a warning instead of crashing
- Special characters (`<`, `>`, `[`, `]`, `*`, `?`, `$`, `|`, etc.) must be enclosed in quotes to prevent shell interpretation. Example: `docsearch "<" "[test]" "$amount"`
- Save search results with `-s` flag — copies results to named files prefixed with `DO_NOT_SEARCH_` so they won't be included in future searches
- Files with `DO_NOT_SEARCH` in the name are automatically skipped during searches

### Supported File Types

| File Type | Description |
|-----------|-------------|
| `.cfg` | Configuration file |
| `.csv` | Comma-separated values |
| `.docx` | Microsoft Word document |
| `.epub` | E-book (EPUB format) |
| `.html` | HTML web page |
| `.ini` | INI configuration file |
| `.json` | JSON data file |
| `.log` | Log file |
| `.md` | Markdown document |
| `.odp` | OpenDocument Presentation (LibreOffice Impress) |
| `.ods` | OpenDocument Spreadsheet (LibreOffice Calc) |
| `.odt` | OpenDocument Text (LibreOffice Writer) |
| `.pdf` | PDF document |
| `.pptx` | Microsoft PowerPoint presentation |
| `.rst` | reStructuredText document |
| `.rtf` | Rich Text Format document |
| `.sql` | SQL script |
| `.tex` | LaTeX document |
| `.toml` | TOML configuration file |
| `.tsv` | Tab-separated values |
| `.txt` | Plain text file |
| `.xlsx` | Microsoft Excel spreadsheet |
| `.xml` | XML data file |
| `.yaml` | YAML configuration file |
| `.yml` | YAML configuration file |

**Motivation:** Over the years I've accumulated more than a hundred files in Google Docs and Sheets — daily journal entries, newspaper and magazine articles, research papers,, family medical histories, jogging logs, and more. Searching through them one by one became impractical. I also wanted local copies as a backup in case access to Google is ever interrupted. docsearch lets me search all of these files at once with a single query.
But the usefulness extends beyond my own situation. docsearch can help anyone who wants to:

- **Keep sensitive documents private** — medical records, financial info, and legal documents stay on your machine, searchable without uploading to cloud AI services
- **Work offline** — search your files without an internet connection, useful for travel or unreliable connectivity
- **Search across formats** — find information across PDFs, Word docs, presentations, spreadsheets, e-books, RTF, Markdown, JSON, XML, YAML, TOML, LaTeX, reStructuredText, SQL, config files, log files, and text files in one place
- **Build a personal knowledge base** — writers, students, and researchers can search years of notes, clippings, and drafts instantly
- **Preserve family and personal records** — genealogy notes, old letters, scanned documents, decades of personal history made searchable
- **Support professional work** — lawyers, consultants, and others with years of case files or client notes can quickly find precedents or past work

Local search is also fast, with no rate limits, usage caps, or waiting on cloud services.

**Programming process:** DocSearch was developed using Claude Code. It's my second Claude Code app, the first being my personal website.

## Installation

### Prerequisites

- Python 3.10 or higher — check if it's already installed by running `python3 --version` (macOS/Linux) or `python --version` (Windows)
  - **macOS:** Install from [python.org](https://www.python.org/downloads/) or via Homebrew: `brew install python`
  - **Windows:** Install from [python.org](https://www.python.org/downloads/) — check "Add Python to PATH" during installation
  - **Linux:** Usually pre-installed. If not: `sudo apt install python3` (Ubuntu/Debian) or `sudo dnf install python3` (Fedora)

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/exbuf/Claude-DocSearch.git
   cd Claude-DocSearch
   ```

2. Create and activate a virtual environment:

   **macOS/Linux (Terminal):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   **Windows (Command Prompt):**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

   **Windows (PowerShell):**
   ```powershell
   python -m venv venv
   venv\Scripts\Activate.ps1
   ```

3. Install the package:
   ```bash
   pip install -e .
   ```

## Usage

First, activate the virtual environment:

**macOS/Linux (Terminal):**
```bash
cd /path/to/Claude-DocSearch
source venv/bin/activate
```

**Windows (Command Prompt):**
```cmd
cd \path\to\Claude-DocSearch
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
cd \path\to\Claude-DocSearch
venv\Scripts\Activate.ps1
```

Then navigate to the directory containing your document files and run:

### Search for a single word
```bash
docsearch budget
```

### Search for multiple terms (OR logic)
```bash
docsearch budget revenue expenses
```
Finds paragraphs containing "budget" OR "revenue" OR "expenses".

### Search for a multi-word phrase
```bash
docsearch "annual report"
```

### Combine phrases and single terms
```bash
docsearch "computer analysis" energy generation
```
Finds paragraphs containing "computer analysis" OR "energy" OR "generation".

### Require ALL terms (AND logic)
```bash
docsearch -a budget revenue expenses
```
Finds only paragraphs containing "budget" AND "revenue" AND "expenses". (Requires -a flag)

### Filter by file type
```bash
docsearch -t pdf,docx budget
```
Searches only `.pdf` and `.docx` files. Comma-separated, no spaces. Supported types: docx, pdf, csv, odt, txt, html, xlsx, md, json, rtf, pptx, xml, log, yaml, yml, tsv, epub, ods, odp, toml, rst, tex, ini, cfg, sql.

### Search subdirectories
```bash
docsearch -r budget
```
Searches all supported files in the current directory and all subdirectories.

The `-r` flag can be combined with other flags:
```bash
docsearch -r -a budget revenue expenses
```
Recursively searches subdirectories for paragraphs containing ALL three terms.

The `-t` flag can also be combined with other flags:
```bash
docsearch -t pdf,docx budget revenue
```
Searches only `.pdf` and `.docx` files for "budget" OR "revenue".

```bash
docsearch -a -t csv,xlsx budget revenue
```
Searches only `.csv` and `.xlsx` files for paragraphs containing "budget" AND "revenue".

```bash
docsearch -r -t pdf,docx budget
```
Recursively searches subdirectories but only in `.pdf` and `.docx` files.

```bash
docsearch -r -a -t txt budget revenue expenses
```
Recursively searches subdirectories, only in `.txt` files, for paragraphs containing ALL three terms.

### Regex search

**What are Regex searches?**
Regex (short for "regular expression") lets you search for patterns rather than exact text. Instead of searching for a specific phone number, you can search for any phone number. Instead of one date, you can find all dates in any format.

Think of it as a wildcard search on steroids. For example, `\d{3}-\d{3}-\d{4}` finds any phone number like 555-123-4567, while `\$\d+` finds any dollar amount.

Regex is powerful but can look intimidating at first. See the table below for common patterns you can copy and use.

#### Common Regex Search Patterns

| Pattern | Matches | Example |
|---------|---------|---------|
| `\d{3}-\d{3}-\d{4}` | US phone numbers | 555-123-4567 |
| `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,}` | Email addresses | jane@example.com |
| `\d{4}-\d{2}-\d{2}` | Dates (YYYY-MM-DD) | 2026-03-17 |
| `\$\d+(\.\d{2})?` | Dollar amounts | $45.99 |
| `\d{3}-\d{2}-\d{4}` | SSN format | 123-45-6789 |
| `\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}` | IP addresses | 192.168.1.1 |
| `https?://\S+` | URLs | https://example.com |
| `\b[A-Z]{2,}\b` | Acronyms (all caps) | NASA, FBI |
| `\b\d{5}(-\d{4})?\b` | US ZIP codes | 12345 or 12345-6789 |
| `\(\d{3}\)\s?\d{3}-\d{4}` | Phone numbers with area code parens | (555) 123-4567 |
| `\b[A-Z][a-z]+\s[A-Z][a-z]+\b` | Proper names (two capitalized words) | John Smith |
| `\b\d+%` | Percentages | 92% |
| `Q[1-4]\s?\d{4}` | Fiscal quarters | Q1 2026 |

**Examples:**

```bash
docsearch -x "\d{3}-\d{3}-\d{4}"
```
Searches using a regex pattern — in this case, US phone numbers like 555-123-4567.

```bash
docsearch -x "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,}"
```
Finds email addresses. Regex search is case-insensitive by default.

The `-x` flag can be combined with other flags:
```bash
docsearch -x -a "\d{3}" "\$\d+\.\d{2}"
```
Finds lines containing both a 3-digit number AND a dollar amount (regex AND logic).

```bash
docsearch -x -r -t txt,csv "\b2026-\d{2}-\d{2}\b"
```
Recursively searches only `.txt` and `.csv` files for dates in 2026.

### Context lines

Show surrounding lines for each match, similar to `grep -B` and `grep -A`. Useful when you want to see the full context around a match (e.g., an author's name appears on one line but the article text is on surrounding lines).

**Note:** These flags use uppercase letters. Don't confuse `-A` (lines after) with lowercase `-a` (AND logic).

```bash
docsearch -A 5 "John Smith"
```
Shows each matching line plus the 5 lines after it.

```bash
docsearch -B 3 budget
```
Shows 3 lines before each match.

```bash
docsearch -B 2 -A 2 budget
```
Shows 2 lines before and 2 lines after each match. When context regions overlap (e.g., two matches close together), they are merged into a single block with no duplicate lines.

The `-A` and `-B` flags can be combined with other flags:
```bash
docsearch -B 3 -A 3 -a budget revenue
```
AND search with 3 lines of context before and after.

```bash
docsearch -B 5 -A 5 -r -t docx "John Smith"
```
Recursively search only `.docx` files with 5 lines of context before and after.

### Save search results
```bash
docsearch -s name_of_your_file  // Saves results to DO_NOT_SEARCH_name_of_your_file.docx (and .txt)
```
Your file name could describe the contents or simply list the search terms used.

### Show version
```bash
docsearch -v
```

### Show help
```bash
docsearch -h
```

### Show help (method 2)
```bash
docsearch
```

## Flag Use Summary

docsearch has seven flags that can be mixed and matched:

| Flag | Purpose |
|------|---------|
| `-a` | AND logic (all terms must appear in the same paragraph) |
| `-r` | Search subdirectories recursively |
| `-t` | Filter by file type (comma-separated, e.g., `pdf,docx`) |
| `-s` | Save results to a named file |
| `-x` | Regex pattern search (case-insensitive) |
| `-A N` | Show N lines after each match |
| `-B N` | Show N lines before each match |

### No flags (default)
```bash
docsearch budget revenue
```
OR search across all 25 file types in the current directory.

### Single flags
```bash
docsearch -a budget revenue          # AND search
docsearch -r budget                  # recursive search
docsearch -t pdf,md budget           # only search .pdf and .md files
docsearch -x "\d{3}-\d{4}"          # regex search
docsearch -A 5 budget                # show 5 lines after each match
docsearch -B 3 budget                # show 3 lines before each match
```

### Two-flag combinations
```bash
docsearch -a -t csv,xlsx budget revenue     # AND search, only in .csv and .xlsx
docsearch -r -a budget revenue              # recursive AND search
docsearch -r -t pdf,docx budget             # recursive, only .pdf and .docx
docsearch -x -a "\d{3}" "\$\d+\.\d{2}"     # regex AND search
docsearch -x -t txt,csv "\b2026-\d{2}\b"   # regex, only .txt and .csv
docsearch -B 3 -A 3 budget                 # 3 lines before and after each match
docsearch -A 5 -t docx budget              # 5 lines after, only .docx files
```

### Three or more flags
```bash
docsearch -r -a -t txt,md budget revenue expenses
```
Recursively searches subdirectories, only in `.txt` and `.md` files, for paragraphs containing ALL three terms.

```bash
docsearch -x -r -t txt,csv "\d{3}-\d{3}-\d{4}"
```
Regex search recursively, only in `.txt` and `.csv` files.

### Notes
- Flag order doesn't matter — `-a -r -t` works the same as `-r -t -a`
- `-t` always needs its type list immediately after it (e.g., `-t pdf,docx`)
- `-x` treats search terms as regex patterns instead of literal strings
- `-s` is used separately after a search to save results: `docsearch -s my_report`
- `-A` and `-B` are uppercase — don't confuse `-A` (lines after) with `-a` (AND logic)
- `-A` and `-B` always need their count immediately after them (e.g., `-A 5`, `-B 3`)

## Output

Search results are written to two files in the current directory:

- **`docsearch_results.txt`** — Plain text with `**` markers around matched terms
- **`docsearch_results.docx`** — Word document with search terms highlighted in green in the header and matched terms highlighted in yellow throughout

Text file format:
```

2026-03-07 14:30:45
Search Term(s) ==> budget, revenue

Document: report.docx, Line: 12, Match:
(/Users/bob/GoogleDocs)
"The **budget** for this quarter exceeded expectations"

Document: summary.docx, Line: 3, Match:
(/Users/bob/GoogleDocs)
"Revised **budget** proposal attached"
```

The terminal also displays a summary:
```
Found 2 match(es). Results written to docsearch_results.txt and docsearch_results.docx
```

## Running Tests

```bash
source venv/bin/activate
pytest tests/ -v
```

## Project Structure

```
Claude-DocSearch/
├── docsearch/
│   └── cli.py          # Main CLI entry point
├── tests/
│   └── test_cli.py     # Test suite
├── pyproject.toml       # Project metadata and dependencies
├── requirements.txt     # Pip requirements
└── README.md
```

## License

This project is licensed under the [MIT License](LICENSE).
