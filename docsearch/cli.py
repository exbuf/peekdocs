"""Command-line interface for DocSearch."""

import glob
import os
import re
import sys
import textwrap
from datetime import datetime

from docx import Document
from docx.enum.text import WD_COLOR_INDEX


BANNER = (
    'docsearch searches through .docx files for a string that is entered as a command line argument\n'
    'Type "docsearch help" to see a list of available commands.'
)


def main(argv=None):
    if argv is None:
        args = sys.argv[1:]
    else:
        args = list(argv)

    print(BANNER)
    print()

    if not args or args[0] == "help":
        if args and args[0] == "help":
            print("docsearch help...lists all available commands\n")
        return 0

    query = " ".join(args)
    cwd = os.getcwd()
    docx_files = sorted(
        f for f in glob.glob(os.path.join(cwd, "*.docx"))
        if os.path.basename(f) != "docsearch_results.docx"
    )

    matches = []
    for filepath in docx_files:
        filename = os.path.basename(filepath)
        doc = Document(filepath)
        for i, para in enumerate(doc.paragraphs, start=1):
            if query.lower() in para.text.lower():
                matches.append((filename, i, para.text))

    output_path = os.path.join(cwd, "docsearch_results.txt")
    if os.path.exists(output_path):
        os.remove(output_path)
    with open(output_path, "w") as f:
        f.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Search Term(s) ==> {query}\n\n")
        for filename, line_num, text in matches:
            highlighted = re.sub(re.escape(query), lambda m: f"**{m.group()}**", text, flags=re.IGNORECASE)
            wrapped = textwrap.fill(highlighted, width=80)
            f.write(f'Document: {filename}, Paragraph: {line_num}, Line: {line_num}, Match:\n"{wrapped}"\n\n')

    # Create docsearch_results.docx with yellow-highlighted matches
    docx_output_path = os.path.join(cwd, "docsearch_results.docx")
    if os.path.exists(docx_output_path):
        os.remove(docx_output_path)
    result_doc = Document()
    with open(output_path, "r") as f:
        for line in f:
            line = line.rstrip("\n")
            para = result_doc.add_paragraph()
            parts = re.split(r"(\*\*.*?\*\*)", line)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    run = para.add_run(part[2:-2])
                    run.font.highlight_color = WD_COLOR_INDEX.YELLOW
                else:
                    para.add_run(part)
    result_doc.save(docx_output_path)

    print()
    print(f"Found {len(matches)} match(es). Results written to docsearch_results.txt and docsearch_results.docx")
    return 0


if __name__ == "__main__":
    sys.exit(main())
