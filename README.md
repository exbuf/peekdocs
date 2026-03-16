# Claude-DocSearch

**Overview:** A Python CLI tool that searches through `.docx`, `.pdf`, `.csv`, `.odt`, `.txt`, `.html`, and `.xlsx` files in the current directory for a given search term or terms. Results are written to `docsearch_results.txt` and `docsearch_results.docx`.

- Results show the full text surrounding each match, so you can understand the context without opening the original document.
- Supports **AND** and **OR** search logic with any number of search terms.
  - **OR**: Show paragraph if it contains term1 OR term2 OR term3, etc.
  - **AND**: Show paragraph if it contains term1 AND term2 AND term3, etc.
- A simple search example can be found in the `docsearch_results.docx` and `docsearch_results.txt` files on GitHub.
  (NOTE: You can view docsearch_results.txt by clicking on it now, but GitHub can't render .docx, .odt, and .xlsx files directly in the browser. So to view the yellow highlighted .docx file and the others, you'll have to download and open them on your local machine. Here's how: .docx opens with Word, Pages, LibreOffice, or Google Docs. Open .odt files with LibreOffice, Google Docs, Word, or Apple Pages. .xlsx files open with Excel, Google Sheets, LibreOffice Calc, or Apple Numbers.)

**Motivation:** Over the years I've accumulated more than a hundred files in Google Docs and Sheets — daily journal entries, newspaper articles I've saved, family medical histories, jogging logs, and more. Searching through them one by one became impractical. I also wanted local copies as a backup in case access to Google is ever interrupted. docsearch lets me search all of these files at once with a single query.
But the usefulness extends beyond my own situation. docsearch can help anyone who wants to:

- Keep sensitive documents private — medical records, financial info, and legal documents stay on your machine, searchable without uploading to cloud AI services
- Work offline — search your files without an internet connection, useful for travel or unreliable connectivity
- Search across formats — find information across PDFs, Word docs, spreadsheets, and text files in one place
- Build a personal knowledge base — writers, students, and researchers can search years of notes, clippings, and drafts instantly
- Preserve family and personal records — genealogy notes, old letters, scanned documents, decades of personal history made searchable
- Support professional work — lawyers, consultants, and others with years of case files or client notes can quickly find precedents or past work

Local search is also fast, with no rate limits, usage caps, or waiting on cloud services.

**Programming process:** DocSearch was developed using Claude Code. It's my second Claude Code app, the first being my personal website.

## Features

- Searches all `.docx`, `.pdf`, `.csv`, `.odt`, `.txt`, `.html`, and `.xlsx` files in the current working directory
- Case-insensitive matching
- Supports multiple search terms with OR logic (finds any match) by default
- Example: `docsearch term1 term2 term3` // any term must appear in the paragraph
- For AND logic (where all search terms must appear in the same paragraph) use the `-a` flag
- Example: `docsearch -a term1 term2 term3`   // all terms must appear in the paragraph
- Use quotes for multi-word phrases (e.g., `"annual report"`)
- Don't separate search terms with commas unless they're part of the search term itself
- Highlights matched terms with `**` markers in `.txt` output and yellow highlighting in `.docx` output
- Results include document name, paragraph number, line number, and matched text
- Timestamped output file
- Generates both `docsearch_results.txt` and `docsearch_results.docx`
- Gracefully handles corrupt or unreadable files — skips them with a warning instead of crashing
- Special characters (`<`, `>`, `[`, `]`, `*`, `?`, `$`, `|`, etc.) must be enclosed in quotes to prevent shell interpretation. Example: `docsearch "<" "[test]" "$amount"`
- Save search results with `-s` flag — copies results to named files prefixed with `Do_Not_Search_` so they won't be included in future searches
- Files with `Do_Not_Search` in the name are automatically skipped during searches

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

### Save search results
```bash
docsearch -s name_of_your_file  // Saves results to Do_Not_Search_name_of_your_file.docx (and .txt)
```

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

## Output

Search results are written to two files in the current directory:

- **`docsearch_results.txt`** — Plain text with `**` markers around matched terms
- **`docsearch_results.docx`** — Word document with matched terms highlighted in yellow

Text file format:
```

2026-03-07 14:30:45
Search Term(s) ==> budget, revenue

Document: report.docx, Paragraph: 12, Line: 12, Match:
"The **budget** for this quarter exceeded expectations"

Document: summary.docx, Paragraph: 3, Line: 3, Match:
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
