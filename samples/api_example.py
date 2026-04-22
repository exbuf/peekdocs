"""Example: Using the peekdocs Python API to search documents programmatically."""

from peekdocs import search


def main():
    # Basic search — find "budget" in the current directory
    result = search(["budget"], directory=".")

    print(f"Files searched: {len(result.files_searched)}")
    print(f"Matches found: {len(result.matches)}")
    print(f"Elapsed: {result.elapsed:.2f}s")
    print()

    # Print each match
    for match in result.matches[:10]:  # first 10 matches
        print(f"  {match.filename}, line {match.line_num}: {match.text[:80]}")

    print()

    # Advanced search — AND mode, recursive, only PDFs and Word docs
    result = search(
        ["invoice", "payment"],
        directory=".",
        match_all=True,         # AND mode — both terms must appear on the same line
        recursive=True,         # search subfolders
        file_types="pdf,docx",  # only PDFs and Word docs
    )

    print(f"AND search: {len(result.matches)} match(es) in {len(result.files_searched)} file(s)")

    # Regex search — find SSN patterns
    result = search(
        [r"\d{3}-\d{2}-\d{4}"],  # SSN pattern
        directory=".",
        use_regex=True,
        recursive=True,
    )

    print(f"SSN pattern: {len(result.matches)} match(es) found")

    # Access match details
    for match in result.matches:
        print(f"  File: {match.filename}")
        print(f"  Line: {match.line_num}")
        print(f"  Text: {match.text}")
        print()


# Required for multiprocessing on macOS and Windows
if __name__ == "__main__":
    main()
