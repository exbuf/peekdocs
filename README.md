# Claude-DocSearch

A Python CLI tool that searches through `.docx` files in the current directory for a given search term and outputs the results to `docsearch_results.txt`.

## Features

- Searches all `.docx` files in the current working directory
- Case-insensitive matching
- Supports multi-word search terms (with or without quotes)
- Highlights matched terms in the output with `**` markers
- Results include document name, line (paragraph) number, and matched text
- Timestamped output file

## Installation

### Prerequisites

- Python 3.10 or higher

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/Claude-DocSearch.git
   cd Claude-DocSearch
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the package:
   ```bash
   pip install -e .
   ```

## Usage

First, activate the virtual environment:
```bash
cd /path/to/Claude-DocSearch
source venv/bin/activate
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

Search results are written to `docsearch_results.txt` in the current directory. The file format is:

```
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

2026-03-07 14:30:45
Search Term(s) ==> budget

Document: report.docx, Line: 12, Match: "The **budget** for this quarter exceeded expectations"

Document: summary.docx, Line: 3, Match: "Revised **budget** proposal attached"
```

The terminal also displays a summary:
```
Found 2 match(es). Results written to docsearch_results.txt
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
