"""Command-line interface for DocSearch."""

import csv
import glob
import os
import re
import sys
import textwrap
import time
from datetime import datetime

import pdfplumber
from docx import Document
from odf.opendocument import load as load_odt
from odf.text import P as OdtParagraph
from odf import teletype
from docx.enum.text import WD_COLOR_INDEX


BANNER = (
    'docsearch searches through .docx, .pdf, .csv, .odt, and .txt files for a string that is entered as a command line argument\n'
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

    print("Searching...")
    start_time = time.time()

    query = " ".join(args)
    cwd = os.getcwd()

    docx_files = sorted(
        f for f in glob.glob(os.path.join(cwd, "*.docx"))
        if os.path.basename(f) != "docsearch_results.docx"
    )
    pdf_files = sorted(glob.glob(os.path.join(cwd, "*.pdf")))
    csv_files = sorted(glob.glob(os.path.join(cwd, "*.csv")))
    odt_files = sorted(glob.glob(os.path.join(cwd, "*.odt")))
    txt_files = sorted(
        f for f in glob.glob(os.path.join(cwd, "*.txt"))
        if os.path.basename(f) != "docsearch_results.txt"
    )
    all_files = sorted(docx_files + pdf_files + csv_files + odt_files + txt_files)

    matches = []
    for filepath in all_files:
        filename = os.path.basename(filepath)
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".docx":
            doc = Document(filepath)
            for i, para in enumerate(doc.paragraphs, start=1):
                if query.lower() in para.text.lower():
                    matches.append((filename, i, para.text))

        elif ext == ".pdf":
            with pdfplumber.open(filepath) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    if not text:
                        continue
                    for line_num, line in enumerate(text.split("\n"), start=1):
                        if query.lower() in line.lower():
                            matches.append((filename, page_num, line))

        elif ext == ".csv":
            with open(filepath, newline="", encoding="utf-8", errors="replace") as csvfile:
                reader = csv.reader(csvfile)
                for row_num, row in enumerate(reader, start=1):
                    row_text = ", ".join(row)
                    if query.lower() in row_text.lower():
                        matches.append((filename, row_num, row_text))

        elif ext == ".odt":
            odt_doc = load_odt(filepath)
            for i, para in enumerate(odt_doc.getElementsByType(OdtParagraph), start=1):
                para_text = teletype.extractText(para)
                if query.lower() in para_text.lower():
                    matches.append((filename, i, para_text))

        elif ext == ".txt":
            with open(filepath, encoding="utf-8", errors="replace") as txtfile:
                for line_num, line in enumerate(txtfile, start=1):
                    line = line.rstrip("\n")
                    if query.lower() in line.lower():
                        matches.append((filename, line_num, line))

    search_elapsed = time.time() - start_time

    output_path = os.path.join(cwd, "docsearch_results.txt")
    if os.path.exists(output_path):
        os.remove(output_path)
    with open(output_path, "w") as f:
        f.write(f"\nReport Generated On ==> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Search Term(s) ==> {query}\n")
        f.write(f"Hits ==> {len(matches)}\n")
        f.write(f"Search Time ==> {search_elapsed:.2f} seconds\n\n")
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
            is_doc_line = line.startswith("Document:")
            parts = re.split(r"(\*\*.*?\*\*)", line)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    run = para.add_run(part[2:-2])
                    run.font.highlight_color = WD_COLOR_INDEX.YELLOW
                    if is_doc_line:
                        run.bold = True
                else:
                    run = para.add_run(part)
                    if is_doc_line:
                        run.bold = True
    result_doc.save(docx_output_path)

    elapsed = time.time() - start_time
    print()
    print(f"Files searched: {len(all_files)}")
    print(f"Found {len(matches)} match(es). Results written to docsearch_results.txt and docsearch_results.docx")
    print(f"Elapsed time: {elapsed:.2f} seconds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
