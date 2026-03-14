# Claude-DocSearch

A Python CLI tool that searches through `.docx`, `.pdf`, `.csv`, `.odt`, `.txt`, and `.html` files in the current directory for a given search term and outputs the results to `docsearch_results.txt` and `docsearch_results.docx`. Results show the full text surrounding each match, so you can understand the context without opening the original document.

## Features

- Searches all `.docx`, `.pdf`, `.csv`, `.odt`, `.txt`, and `.html` files in the current working directory
- Case-insensitive matching
- Supports multiple search terms with OR logic (finds any match) by default
- Use `-a` flag for AND logic (all terms must appear in the same paragraph)
- Use quotes for multi-word phrases (e.g., `"annual report"`)
- Don't separate search terms with commas unless they're part of the search term itself
- Highlights matched terms with `**` markers in `.txt` output and yellow highlighting in `.docx` output
- Results include document name, paragraph number, line number, and matched text
- Timestamped output file
- Generates both `docsearch_results.txt` and `docsearch_results.docx`

## Installation

### Prerequisites

- Python 3.10 or higher

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/exbuf/Claude-DocSearch.git
   cd Claude-DocSearch
   ```

2. Create and activate a virtual environment:

   **macOS/Linux:**
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

**macOS/Linux:**
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
Finds only paragraphs containing "budget" AND "revenue" AND "expenses".

### Show help
```bash
docsearch help
```

### Show description
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

This project is provided as-is for personal use.
