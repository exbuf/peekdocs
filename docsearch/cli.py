"""Command-line interface for DocSearch."""

import csv
import glob
from html.parser import HTMLParser
import logging
import os
import re
import sys
import textwrap
import time
from datetime import datetime

logging.getLogger("pdfminer").setLevel(logging.ERROR)

import pdfplumber
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from odf.opendocument import load as load_odt
from odf.text import P as OdtParagraph
from odf import teletype
from docx.enum.text import WD_COLOR_INDEX
from openpyxl import load_workbook
from importlib.metadata import version as pkg_version


VERSION = pkg_version("claude-docsearch")

BANNER = (
    '\nEnter your search terms. Example: docsearch term1 term2 term3\n'
    'Option flags: -a for AND searches, -h for help, -v for version.'
)


def main(argv=None):
    if argv is None:
        args = sys.argv[1:]
    else:
        args = list(argv)

    print(BANNER)
    print()

    if args and args[0] in ("-v", "--version"):
        print(f"docsearch {VERSION}\n")
        return 0

    if not args or args[0] in ("help", "-h", "--help"):
        if args and args[0] in ("help", "-h", "--help"):
            print("docsearch -h...lists all available commands\n")
        return 0

    match_all = "-a" in args or "--all" in args
    search_terms = [a for a in args if a not in ("-a", "--all")]

    if not search_terms:
        print("No search terms provided.\n")
        return 1

    print("Searching...")
    start_time = time.time()
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
    html_files = sorted(glob.glob(os.path.join(cwd, "*.html")))
    xlsx_files = sorted(glob.glob(os.path.join(cwd, "*.xlsx")))
    all_files = sorted(docx_files + pdf_files + csv_files + odt_files + txt_files + html_files + xlsx_files)

    def text_matches(text):
        """Return True if search terms are found in text (ANY or ALL based on mode)."""
        text_lower = text.lower()
        check = all if match_all else any
        return check(term.lower() in text_lower for term in search_terms)

    matches = []
    for filepath in all_files:
        filename = os.path.basename(filepath)
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".docx":
            doc = Document(filepath)
            for i, para in enumerate(doc.paragraphs, start=1):
                if text_matches(para.text):
                    matches.append((filename, i, para.text))

        elif ext == ".pdf":
            with pdfplumber.open(filepath) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    if not text:
                        continue
                    for line_num, line in enumerate(text.split("\n"), start=1):
                        if text_matches(line):
                            matches.append((filename, page_num, line))

        elif ext == ".csv":
            with open(filepath, newline="", encoding="utf-8", errors="replace") as csvfile:
                reader = csv.reader(csvfile)
                for row_num, row in enumerate(reader, start=1):
                    row_text = ", ".join(row)
                    if text_matches(row_text):
                        matches.append((filename, row_num, row_text))

        elif ext == ".odt":
            odt_doc = load_odt(filepath)
            for i, para in enumerate(odt_doc.getElementsByType(OdtParagraph), start=1):
                para_text = teletype.extractText(para)
                if text_matches(para_text):
                    matches.append((filename, i, para_text))

        elif ext == ".txt":
            with open(filepath, encoding="utf-8", errors="replace") as txtfile:
                for line_num, line in enumerate(txtfile, start=1):
                    line = line.rstrip("\n")
                    if text_matches(line):
                        matches.append((filename, line_num, line))

        elif ext == ".html":
            class _HTMLTextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text_parts = []
                def handle_data(self, data):
                    self.text_parts.append(data)
            with open(filepath, encoding="utf-8", errors="replace") as htmlfile:
                parser = _HTMLTextExtractor()
                parser.feed(htmlfile.read())
            lines = "".join(parser.text_parts).split("\n")
            for line_num, line in enumerate(lines, start=1):
                line = line.strip()
                if line and text_matches(line):
                    matches.append((filename, line_num, line))

        elif ext == ".xlsx":
            wb = load_workbook(filepath, read_only=True, data_only=True)
            for sheet in wb.worksheets:
                for row_num, row in enumerate(sheet.iter_rows(values_only=True), start=1):
                    row_text = ", ".join(str(cell) for cell in row if cell is not None)
                    if row_text and text_matches(row_text):
                        matches.append((filename, row_num, row_text))
            wb.close()

    search_elapsed = time.time() - start_time

    output_path = os.path.join(cwd, "docsearch_results.txt")
    if os.path.exists(output_path):
        os.remove(output_path)
    with open(output_path, "w") as f:
        f.write("Program name: docsearch\n")
        f.write("Source: https://github.com/exbuf\n")
        f.write("Overview: Searches all supported file types in current directory for search terms.\n")
        f.write("Supported file types: .docx, .pdf, .csv, .odt, .txt, .html, .xlsx\n")
        f.write(f"\nReport Generated On ==> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        mode = "ALL" if match_all else "ANY"
        f.write(f"Search Term(s) ==> {', '.join(search_terms)} (match: {mode})\n")
        f.write(f"Hits ==> {len(matches)}\n")
        f.write(f"Search Time ==> {search_elapsed:.2f} seconds\n\n")
        for filename, line_num, text in matches:
            highlighted = text
            for term in search_terms:
                highlighted = re.sub(re.escape(term), lambda m: f"**{m.group()}**", highlighted, flags=re.IGNORECASE)
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

            # Make URL a clickable hyperlink
            if line.startswith("Source: "):
                prefix, url = line.split(" ", 1)
                para.add_run(prefix + " ")
                r_id = result_doc.part.relate_to(
                    url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True
                )
                hyperlink = OxmlElement("w:hyperlink")
                hyperlink.set(qn("r:id"), r_id)
                run_elem = OxmlElement("w:r")
                rPr = OxmlElement("w:rPr")
                color = OxmlElement("w:color")
                color.set(qn("w:val"), "0000FF")
                rPr.append(color)
                u = OxmlElement("w:u")
                u.set(qn("w:val"), "single")
                rPr.append(u)
                run_elem.append(rPr)
                text_elem = OxmlElement("w:t")
                text_elem.text = url
                run_elem.append(text_elem)
                hyperlink.append(run_elem)
                para._p.append(hyperlink)
                continue

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
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
