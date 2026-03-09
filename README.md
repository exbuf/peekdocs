# Claude-DocSearch

A Python CLI tool that searches through `.docx` files in the current directory for a given search term and outputs the results to `docsearch_results.txt`.

## Features

- Searches all `.docx` files in the current working directory
- Case-insensitive matching
- Supports multi-word search terms (with or without quotes)
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

Then navigate to the directory containing your `.docx` files and run:

### Search for a single word
```bash
docsearch budget
```

### Search for a multi-word phrase
```bash
docsearch "annual report"
```

Or without quotes:
```bash
docsearch annual report
```

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
Search Term(s) ==> budget

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
