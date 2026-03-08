"""Command-line interface for DocSearch."""

import glob
import os
import re
import sys
import textwrap
from datetime import datetime

from docx import Document


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
    docx_files = sorted(glob.glob(os.path.join(cwd, "*.docx")))

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
        f.write("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n")
        f.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Search Term(s) ==> {query}\n\n")
        for filename, line_num, text in matches:
            highlighted = re.sub(re.escape(query), lambda m: f"**{m.group()}**", text, flags=re.IGNORECASE)
            wrapped = textwrap.fill(highlighted, width=80)
            f.write(f'Document: {filename}, Paragraph: {line_num}, Line: {line_num}, Match:\n"{wrapped}"\n\n')

    print()
    print(f"Found {len(matches)} match(es). Results written to docsearch_results.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
