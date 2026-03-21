"""Tests for the CLI module."""

import os
import re

from docx import Document
from docx.enum.text import WD_COLOR_INDEX
from fpdf import FPDF

from docsearch.cli import BANNER, SUPPORTED_TYPES, VERSION, main


def test_no_args(capsys):
    result = main([])
    captured = capsys.readouterr()
    assert result == 0
    assert BANNER in captured.out
    assert "More details here: https://github.com/exbuf/Claude-DocSearch/blob/main/README.md" in captured.out


def test_help(capsys):
    result = main(["-h"])
    captured = capsys.readouterr()
    assert result == 0
    assert "More details here: https://github.com/exbuf/Claude-DocSearch/blob/main/README.md" in captured.out
    assert BANNER in captured.out


def test_search_finds_matches(tmp_path, monkeypatch, capsys):
    doc = Document()
    doc.add_paragraph("Hello world")
    doc.add_paragraph("This is a test")
    doc.add_paragraph("Hello again")
    doc.save(str(tmp_path / "sample.docx"))

    monkeypatch.chdir(tmp_path)
    result = main(["hello"])
    captured = capsys.readouterr()

    assert result == 0
    assert "2 match(es)" in captured.out

    results_file = tmp_path / "docsearch_results.txt"
    assert results_file.exists()
    content = results_file.read_text()
    assert "Search Term(s) ==> hello (match: ANY)" in content
    assert f'Document: sample.docx, Line: 1, Match:\n({tmp_path})\n"**Hello** world"\n\n' in content
    assert f'Document: sample.docx, Line: 3, Match:\n({tmp_path})\n"**Hello** again"\n\n' in content

    # Check docsearch_results.docx was created with yellow highlighting
    docx_results = tmp_path / "docsearch_results.docx"
    assert docx_results.exists()
    result_doc = Document(str(docx_results))
    highlighted_runs = [
        run for para in result_doc.paragraphs for run in para.runs
        if run.font.highlight_color == WD_COLOR_INDEX.YELLOW
    ]
    assert len(highlighted_runs) == 2
    assert highlighted_runs[0].text == "Hello"
    assert highlighted_runs[1].text == "Hello"


def test_search_no_matches(tmp_path, monkeypatch, capsys):
    doc = Document()
    doc.add_paragraph("Nothing here")
    doc.save(str(tmp_path / "empty.docx"))

    monkeypatch.chdir(tmp_path)
    result = main(["zzzzz"])
    captured = capsys.readouterr()

    assert result == 0
    assert "0 match(es)" in captured.out

    results_file = tmp_path / "docsearch_results.txt"
    assert results_file.exists()
    content = results_file.read_text()
    assert "Search Term(s) ==> zzzzz (match: ANY)" in content


def test_search_case_insensitive(tmp_path, monkeypatch, capsys):
    doc = Document()
    doc.add_paragraph("Python is great")
    doc.save(str(tmp_path / "test.docx"))

    monkeypatch.chdir(tmp_path)
    main(["PYTHON"])

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert f'Document: test.docx, Line: 1, Match:\n({tmp_path})\n"**Python** is great"' in content


def test_search_multi_word_phrase(tmp_path, monkeypatch, capsys):
    """Quoted multi-word phrase is a single search term."""
    doc = Document()
    doc.add_paragraph("Hello world")
    doc.add_paragraph("Hello again")
    doc.save(str(tmp_path / "sample.docx"))

    monkeypatch.chdir(tmp_path)
    result = main(["Hello world"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "**Hello world**" in content


def test_search_multiple_terms(tmp_path, monkeypatch, capsys):
    """Multiple args are separate search terms (OR logic)."""
    doc = Document()
    doc.add_paragraph("Hello world")
    doc.add_paragraph("Nothing here")
    doc.add_paragraph("Goodbye world")
    doc.save(str(tmp_path / "sample.docx"))

    monkeypatch.chdir(tmp_path)
    result = main(["Hello", "Goodbye"])
    captured = capsys.readouterr()

    assert result == 0
    assert "2 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "Search Term(s) ==> Hello, Goodbye (match: ANY)" in content
    assert "**Hello**" in content
    assert "**Goodbye**" in content


def test_search_all_terms(tmp_path, monkeypatch, capsys):
    """With -a flag, only match paragraphs containing ALL terms."""
    doc = Document()
    doc.add_paragraph("Hello world")
    doc.add_paragraph("Hello Goodbye")
    doc.add_paragraph("Goodbye world")
    doc.save(str(tmp_path / "sample.docx"))

    monkeypatch.chdir(tmp_path)
    result = main(["-a", "Hello", "Goodbye"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "Search Term(s) ==> Hello, Goodbye (match: ALL)" in content
    assert "**Hello** **Goodbye**" in content


def test_search_pdf(tmp_path, monkeypatch, capsys):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(text="Budget report for Q1")
    pdf.ln()
    pdf.cell(text="No match here")
    pdf.ln()
    pdf.cell(text="Revised budget plan")
    pdf.output(str(tmp_path / "report.pdf"))

    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "2 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "report.pdf" in content
    assert "**budget**" in content or "**Budget**" in content


def test_search_csv(tmp_path, monkeypatch, capsys):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("Name,Amount\nAlice,500\nBob,budget review\nCharlie,300\n")

    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "data.csv" in content
    assert "**budget**" in content


def test_search_odt(tmp_path, monkeypatch, capsys):
    from odf.opendocument import OpenDocumentText
    from odf.text import P as OdtP

    odt_doc = OpenDocumentText()
    p1 = OdtP(text="Hello from ODT")
    odt_doc.text.addElement(p1)
    p2 = OdtP(text="Nothing here")
    odt_doc.text.addElement(p2)
    odt_doc.save(str(tmp_path / "test.odt"))

    monkeypatch.chdir(tmp_path)
    result = main(["hello"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "test.odt" in content
    assert "**Hello**" in content


def test_search_txt(tmp_path, monkeypatch, capsys):
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("First line\nBudget overview\nThird line\n")

    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "notes.txt" in content
    assert "**Budget**" in content


def test_search_html(tmp_path, monkeypatch, capsys):
    html_file = tmp_path / "page.html"
    html_file.write_text("<html><body><p>Budget report</p><p>No match</p></body></html>")

    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "page.html" in content
    assert "**Budget**" in content


def test_search_xlsx(tmp_path, monkeypatch, capsys):
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(["Name", "Amount"])
    ws.append(["Alice", "500"])
    ws.append(["Bob", "budget review"])
    wb.save(str(tmp_path / "data.xlsx"))

    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "data.xlsx" in content
    assert "**budget**" in content


def test_version_flag(capsys):
    result = main(["-v"])
    captured = capsys.readouterr()
    assert result == 0
    assert f"docsearch {VERSION}" in captured.out


def test_version_flag_long(capsys):
    result = main(["-version"])
    captured = capsys.readouterr()
    assert result == 0
    assert f"docsearch {VERSION}" in captured.out


def test_banner_always_printed(capsys):
    main(["anything"])
    captured = capsys.readouterr()
    assert BANNER in captured.out


def test_search_recursive(tmp_path, monkeypatch, capsys):
    """With -r flag, files in subdirectories are found and shown with relative paths."""
    subdir = tmp_path / "sub" / "deep"
    subdir.mkdir(parents=True)
    txt_file = subdir / "nested.txt"
    txt_file.write_text("Budget overview in nested file\nNo match here\n")

    monkeypatch.chdir(tmp_path)
    result = main(["-r", "budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert str(tmp_path / "sub" / "deep") in content
    assert "nested.txt" in content
    assert "**Budget**" in content


def test_search_no_recursive_skips_subdirs(tmp_path, monkeypatch, capsys):
    """Without -r flag, files in subdirectories are NOT searched."""
    subdir = tmp_path / "sub"
    subdir.mkdir()
    txt_file = subdir / "nested.txt"
    txt_file.write_text("Budget overview in nested file\n")

    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "0 match(es)" in captured.out


def test_search_with_type_filter(tmp_path, monkeypatch, capsys):
    """With -t flag, only specified file types are searched."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Budget overview\n")
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("Name,Amount\nBob,budget review\n")

    monkeypatch.chdir(tmp_path)
    result = main(["-t", "txt", "budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out
    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "notes.txt" in content
    assert "data.csv" not in content


def test_search_with_multiple_type_filters(tmp_path, monkeypatch, capsys):
    """With -t flag and comma-separated types, multiple types are searched."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Budget overview\n")
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("Name,Amount\nBob,budget review\n")
    html_file = tmp_path / "page.html"
    html_file.write_text("<html><body><p>Budget report</p></body></html>")

    monkeypatch.chdir(tmp_path)
    result = main(["-t", "txt,csv", "budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "2 match(es)" in captured.out
    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "notes.txt" in content
    assert "data.csv" in content
    assert "page.html" not in content


def test_search_invalid_type_filter(tmp_path, monkeypatch, capsys):
    """With -t flag and unsupported type, an error is returned."""
    monkeypatch.chdir(tmp_path)
    result = main(["-t", "xyz", "budget"])
    captured = capsys.readouterr()

    assert result == 1
    assert "Unsupported file type: xyz" in captured.out


def test_search_md(tmp_path, monkeypatch, capsys):
    md_file = tmp_path / "notes.md"
    md_file.write_text("# Heading\nBudget overview for Q1\nNo match here\n")

    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "notes.md" in content
    assert "**Budget**" in content


def test_search_regex(tmp_path, monkeypatch, capsys):
    """With -x flag, search terms are treated as regex patterns."""
    txt_file = tmp_path / "contacts.txt"
    txt_file.write_text("Call 555-123-4567\nNo phone here\nReach out at 555-987-6543\n")

    monkeypatch.chdir(tmp_path)
    result = main(["-x", r"\d{3}-\d{3}-\d{4}"])
    captured = capsys.readouterr()

    assert result == 0
    assert "2 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "contacts.txt" in content
    assert "**555-123-4567**" in content
    assert "**555-987-6543**" in content


def test_search_regex_with_and(tmp_path, monkeypatch, capsys):
    """Combine -x and -a for regex AND logic."""
    txt_file = tmp_path / "data.txt"
    txt_file.write_text("Order 123 costs $45.99\nOrder 456 no price\nJust $99.99 here\n")

    monkeypatch.chdir(tmp_path)
    result = main(["-x", "-a", r"\d{3}", r"\$\d+\.\d{2}"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "REGEX+AND" in content


def test_search_invalid_regex(tmp_path, monkeypatch, capsys):
    """With -x flag and invalid regex, return error."""
    monkeypatch.chdir(tmp_path)
    result = main(["-x", "[invalid"])
    captured = capsys.readouterr()

    assert result == 1
    assert "Invalid regex pattern" in captured.out


def test_search_json(tmp_path, monkeypatch, capsys):
    json_file = tmp_path / "data.json"
    json_file.write_text('{\n  "title": "Budget report",\n  "amount": 500\n}\n')

    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "data.json" in content
    assert "**Budget**" in content


def test_search_context_after(tmp_path, monkeypatch, capsys):
    """With -A flag, lines after each match are included."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("\n".join(f"Line {i}" for i in range(1, 11)) + "\n")

    monkeypatch.chdir(tmp_path)
    result = main(["-A", "2", "Line 3"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "**Line 3**" in content
    assert "Line 4" in content
    assert "Line 5" in content
    assert "Line 6" not in content


def test_search_context_before(tmp_path, monkeypatch, capsys):
    """With -B flag, lines before each match are included."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("\n".join(f"Line {i}" for i in range(1, 11)) + "\n")

    monkeypatch.chdir(tmp_path)
    result = main(["-B", "2", "Line 3"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "Line 1" in content
    assert "Line 2" in content
    assert "**Line 3**" in content
    assert "Line 4" not in content


def test_search_context_both(tmp_path, monkeypatch, capsys):
    """With -B and -A flags combined, lines before and after are included."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("\n".join(f"Line {i}" for i in range(1, 11)) + "\n")

    monkeypatch.chdir(tmp_path)
    result = main(["-B", "1", "-A", "1", "Line 3"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "Line 1" not in content
    assert "Line 2" in content
    assert "**Line 3**" in content
    assert "Line 4" in content
    assert "Line 5" not in content


def test_search_context_merge(tmp_path, monkeypatch, capsys):
    """When context regions overlap, they merge without duplicate lines."""
    txt_file = tmp_path / "notes.txt"
    lines = ["alpha", "beta", "MATCH_ONE", "gamma", "MATCH_TWO", "delta", "epsilon"]
    txt_file.write_text("\n".join(lines) + "\n")

    monkeypatch.chdir(tmp_path)
    result = main(["-B", "1", "-A", "1", "MATCH"])
    captured = capsys.readouterr()

    assert result == 0
    # Overlapping context should merge into one group
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "beta" in content
    assert "**MATCH**_ONE" in content
    assert "gamma" in content
    assert "**MATCH**_TWO" in content
    assert "delta" in content
    # gamma should appear exactly once (no duplicates from overlap)
    match_text = content.split('"')[1]  # get the quoted match text
    assert match_text.count("gamma") == 1


def test_search_ods(tmp_path, monkeypatch, capsys):
    from odf.opendocument import OpenDocumentSpreadsheet
    from odf.table import Table, TableRow, TableCell
    from odf.text import P as OdtP

    ods_doc = OpenDocumentSpreadsheet()
    table = Table(name="Sheet1")
    row1 = TableRow()
    cell1 = TableCell()
    cell1.addElement(OdtP(text="Budget report"))
    row1.addElement(cell1)
    table.addElement(row1)
    row2 = TableRow()
    cell2 = TableCell()
    cell2.addElement(OdtP(text="No match"))
    row2.addElement(cell2)
    table.addElement(row2)
    ods_doc.spreadsheet.addElement(table)
    ods_doc.save(str(tmp_path / "data.ods"))

    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "data.ods" in content
    assert "**Budget**" in content


def test_search_odp(tmp_path, monkeypatch, capsys):
    from odf.opendocument import OpenDocumentPresentation
    from odf.text import P as OdtP
    from odf.draw import Page, Frame, TextBox

    odp_doc = OpenDocumentPresentation()
    page = Page(masterpagename="Default")
    frame = Frame()
    textbox = TextBox()
    textbox.addElement(OdtP(text="Budget presentation"))
    frame.addElement(textbox)
    page.addElement(frame)
    odp_doc.presentation.addElement(page)
    odp_doc.save(str(tmp_path / "slides.odp"))

    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "slides.odp" in content
    assert "**Budget**" in content


def test_search_toml(tmp_path, monkeypatch, capsys):
    toml_file = tmp_path / "config.toml"
    toml_file.write_text('[project]\nname = "budget-tracker"\nversion = "1.0"\n')

    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "config.toml" in content
    assert "**budget**" in content


def test_search_rst(tmp_path, monkeypatch, capsys):
    rst_file = tmp_path / "docs.rst"
    rst_file.write_text("Title\n=====\n\nBudget overview for Q1\n\nNo match here\n")

    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "docs.rst" in content
    assert "**Budget**" in content


def test_search_tex(tmp_path, monkeypatch, capsys):
    tex_file = tmp_path / "paper.tex"
    tex_file.write_text("\\documentclass{article}\n\\begin{document}\nBudget analysis results\n\\end{document}\n")

    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "paper.tex" in content
    assert "**Budget**" in content


def test_search_ini(tmp_path, monkeypatch, capsys):
    ini_file = tmp_path / "settings.ini"
    ini_file.write_text("[general]\nproject = budget_app\nversion = 1.0\n")

    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "settings.ini" in content
    assert "**budget**" in content


def test_search_cfg(tmp_path, monkeypatch, capsys):
    cfg_file = tmp_path / "app.cfg"
    cfg_file.write_text("[settings]\nbudget_limit = 5000\nactive = true\n")

    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "app.cfg" in content
    assert "**budget**" in content


def test_search_sql(tmp_path, monkeypatch, capsys):
    sql_file = tmp_path / "queries.sql"
    sql_file.write_text("SELECT * FROM expenses;\nSELECT * FROM budget WHERE year = 2026;\nDROP TABLE temp;\n")

    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "queries.sql" in content
    assert "**budget**" in content


def test_search_tsv(tmp_path, monkeypatch, capsys):
    tsv_file = tmp_path / "data.tsv"
    tsv_file.write_text("Name\tAmount\nAlice\t500\nBob\tbudget review\nCharlie\t300\n")

    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "data.tsv" in content
    assert "**budget**" in content


def test_search_epub(tmp_path, monkeypatch, capsys):
    from ebooklib import epub as epub_mod
    book = epub_mod.EpubBook()
    book.set_identifier("test123")
    book.set_title("Test Book")
    book.set_language("en")
    ch = epub_mod.EpubHtml(title="Chapter 1", file_name="ch1.xhtml", lang="en")
    ch.content = b"<html><body><p>Budget report for Q1</p><p>No match here</p></body></html>"
    book.add_item(ch)
    book.spine = ["nav", ch]
    book.add_item(epub_mod.EpubNcx())
    book.add_item(epub_mod.EpubNav())
    epub_mod.write_epub(str(tmp_path / "book.epub"), book)

    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "book.epub" in content
    assert "**Budget**" in content


def test_search_yaml(tmp_path, monkeypatch, capsys):
    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text("title: Budget report\namount: 500\ndescription: No match here\n")

    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "config.yaml" in content
    assert "**Budget**" in content


def test_search_yml(tmp_path, monkeypatch, capsys):
    yml_file = tmp_path / "settings.yml"
    yml_file.write_text("name: test\nbudget_limit: 1000\nstatus: active\n")

    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "settings.yml" in content
    assert "**budget**" in content


def test_search_xml(tmp_path, monkeypatch, capsys):
    xml_file = tmp_path / "config.xml"
    xml_file.write_text('<?xml version="1.0"?>\n<root>\n  <title>Budget report</title>\n  <value>No match</value>\n</root>\n')

    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "config.xml" in content
    assert "**Budget**" in content


def test_search_log(tmp_path, monkeypatch, capsys):
    log_file = tmp_path / "app.log"
    log_file.write_text("2026-03-18 INFO Starting up\n2026-03-18 ERROR Budget exceeded limit\n2026-03-18 INFO Shutting down\n")

    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "app.log" in content
    assert "**Budget**" in content


def test_search_pptx(tmp_path, monkeypatch, capsys):
    from pptx import Presentation as PptxPresentation
    from pptx.util import Inches
    prs = PptxPresentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank layout
    txBox = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(5), Inches(1))
    txBox.text_frame.text = "Budget report for Q1"
    txBox2 = slide.shapes.add_textbox(Inches(1), Inches(3), Inches(5), Inches(1))
    txBox2.text_frame.text = "No match here"
    prs.save(str(tmp_path / "report.pptx"))

    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "report.pptx" in content
    assert "**Budget**" in content


def test_search_rtf(tmp_path, monkeypatch, capsys):
    rtf_file = tmp_path / "report.rtf"
    rtf_content = r'{\rtf1\ansi{\fonttbl\f0 Times New Roman;}\f0 Budget report for Q1\par No match here\par}'
    rtf_file.write_text(rtf_content)

    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "report.rtf" in content
    assert "**Budget**" in content


def test_search_context_invalid(tmp_path, monkeypatch, capsys):
    """With -A and invalid count, an error is returned."""
    monkeypatch.chdir(tmp_path)
    result = main(["-A", "abc", "budget"])
    captured = capsys.readouterr()

    assert result == 1
    assert "Invalid count for -A" in captured.out


def test_search_with_file_filter(tmp_path, monkeypatch, capsys):
    """With -f flag, only specified files are searched."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Budget overview\n")
    txt_file2 = tmp_path / "other.txt"
    txt_file2.write_text("Budget details\n")

    monkeypatch.chdir(tmp_path)
    result = main(["-f", "notes.txt", "budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out
    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "notes.txt" in content
    assert "other.txt" not in content


def test_search_with_multiple_file_filters(tmp_path, monkeypatch, capsys):
    """With -f flag and comma-separated files, multiple files are searched."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Budget overview\n")
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("Name,Amount\nBob,budget review\n")
    html_file = tmp_path / "page.html"
    html_file.write_text("<html><body><p>Budget report</p></body></html>")

    monkeypatch.chdir(tmp_path)
    result = main(["-f", "notes.txt,data.csv", "budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "2 match(es)" in captured.out
    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "notes.txt" in content
    assert "data.csv" in content
    assert "page.html" not in content


def test_search_file_filter_not_found(tmp_path, monkeypatch, capsys):
    """With -f flag and nonexistent file, an error is returned."""
    monkeypatch.chdir(tmp_path)
    result = main(["-f", "missing.txt", "budget"])
    captured = capsys.readouterr()

    assert result == 1
    assert "File not found: missing.txt" in captured.out


def test_search_file_filter_with_and(tmp_path, monkeypatch, capsys):
    """With -f and -a flags, AND logic applies to specified files."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Budget and revenue overview\n")
    txt_file2 = tmp_path / "other.txt"
    txt_file2.write_text("Budget and revenue details\n")

    monkeypatch.chdir(tmp_path)
    result = main(["-f", "notes.txt", "-a", "budget", "revenue"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out
    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "notes.txt" in content
    assert "other.txt" not in content


def test_search_file_filter_with_regex(tmp_path, monkeypatch, capsys):
    """With -f and -x flags, regex search applies to specified files."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Call 555-123-4567 for details\n")
    txt_file2 = tmp_path / "other.txt"
    txt_file2.write_text("Call 555-987-6543 for info\n")

    monkeypatch.chdir(tmp_path)
    result = main(["-f", "notes.txt", "-x", r"\d{3}-\d{3}-\d{4}"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out
    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "notes.txt" in content
    assert "other.txt" not in content


def test_search_file_filter_with_context(tmp_path, monkeypatch, capsys):
    """With -f, -A, and -B flags, context lines apply to specified files."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Line one\nBudget overview\nLine three\n")
    txt_file2 = tmp_path / "other.txt"
    txt_file2.write_text("Budget details\n")

    monkeypatch.chdir(tmp_path)
    result = main(["-f", "notes.txt", "-B", "1", "-A", "1", "budget"])
    captured = capsys.readouterr()

    assert result == 0
    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "notes.txt" in content
    assert "other.txt" not in content
    assert "Line one" in content
    assert "Line three" in content


def test_search_file_filter_recursive(tmp_path, monkeypatch, capsys):
    """With -f and -r flags, specific file is found in subdirectories."""
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    txt_file = subdir / "notes.txt"
    txt_file.write_text("Budget overview\n")
    txt_file2 = tmp_path / "other.txt"
    txt_file2.write_text("Budget details\n")

    monkeypatch.chdir(tmp_path)
    result = main(["-f", "notes.txt", "-r", "budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out
    content = (tmp_path / "docsearch_results.txt").read_text()
    assert "notes.txt" in content
    assert "other.txt" not in content


def test_search_proximity(tmp_path, monkeypatch, capsys):
    """With -p flag, terms within N words of each other match."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("The budget for revenue growth was approved\n")

    monkeypatch.chdir(tmp_path)
    result = main(["-p", "3", "budget", "revenue"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out


def test_search_proximity_no_match(tmp_path, monkeypatch, capsys):
    """With -p flag, terms too far apart don't match."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("The budget was set and later the team discussed revenue\n")

    monkeypatch.chdir(tmp_path)
    result = main(["-p", "2", "budget", "revenue"])
    captured = capsys.readouterr()

    assert result == 0
    assert "0 match(es)" in captured.out


def test_search_proximity_requires_two_terms(tmp_path, monkeypatch, capsys):
    """With -p flag and only one term, an error is returned."""
    monkeypatch.chdir(tmp_path)
    result = main(["-p", "5", "budget"])
    captured = capsys.readouterr()

    assert result == 1
    assert "requires at least 2 search terms" in captured.out


def test_search_proximity_invalid(tmp_path, monkeypatch, capsys):
    """With -p flag and invalid count, an error is returned."""
    monkeypatch.chdir(tmp_path)
    result = main(["-p", "abc", "budget", "revenue"])
    captured = capsys.readouterr()

    assert result == 1
    assert "Invalid count for -p" in captured.out


def test_search_save_append(tmp_path, monkeypatch, capsys):
    """With -sa flag, search runs normally and results are appended to DO_NOT_SEARCH file."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Budget overview for Q1\n")

    monkeypatch.chdir(tmp_path)
    result = main(["-sa", "my_report", "budget"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out
    assert "Results appended to DO_NOT_SEARCH_ACCUMULATED_my_report.txt and DO_NOT_SEARCH_ACCUMULATED_my_report.docx" in captured.out

    assert (tmp_path / "docsearch_results.txt").exists()
    assert (tmp_path / "docsearch_results.docx").exists()
    assert (tmp_path / "DO_NOT_SEARCH_ACCUMULATED_my_report.txt").exists()
    assert (tmp_path / "DO_NOT_SEARCH_ACCUMULATED_my_report.docx").exists()

    content = (tmp_path / "DO_NOT_SEARCH_ACCUMULATED_my_report.txt").read_text()
    assert "budget" in content.lower()


def test_search_save_append_accumulates(tmp_path, monkeypatch, capsys):
    """With -sa flag used twice, results accumulate in the DO_NOT_SEARCH file."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Budget overview for Q1\nRevenue report for Q2\n")

    monkeypatch.chdir(tmp_path)
    main(["-sa", "combined", "budget"])
    main(["-sa", "combined", "revenue"])

    append_txt = tmp_path / "DO_NOT_SEARCH_ACCUMULATED_combined.txt"
    content = append_txt.read_text()
    assert "budget" in content.lower()
    assert "revenue" in content.lower()


def test_search_save_append_no_filename(capsys):
    """With -sa flag and no filename, an error is returned."""
    result = main(["-sa"])
    captured = capsys.readouterr()

    assert result == 1
    assert "No filename provided" in captured.out


def test_search_save_append_no_terms(tmp_path, monkeypatch, capsys):
    """With -sa flag and filename but no search terms, an error is returned."""
    monkeypatch.chdir(tmp_path)
    result = main(["-sa", "my_report"])
    captured = capsys.readouterr()

    assert result == 1
    assert "No search terms provided" in captured.out


def test_search_with_cores_flag(tmp_path, monkeypatch, capsys):
    """With -c flag, search uses specified number of cores."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Budget overview\n")
    monkeypatch.chdir(tmp_path)
    result = main(["-c", "2", "budget"])
    captured = capsys.readouterr()
    assert result == 0
    assert "1 match(es)" in captured.out


def test_search_with_single_core(tmp_path, monkeypatch, capsys):
    """With -c 1, search runs single-threaded."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Budget overview\n")
    monkeypatch.chdir(tmp_path)
    result = main(["-c", "1", "budget"])
    captured = capsys.readouterr()
    assert result == 0
    assert "1 match(es)" in captured.out


def test_search_cores_invalid(tmp_path, monkeypatch, capsys):
    """With -c and invalid count, an error is returned."""
    monkeypatch.chdir(tmp_path)
    result = main(["-c", "abc", "budget"])
    captured = capsys.readouterr()
    assert result == 1
    assert "Invalid count for -c" in captured.out


def test_search_cores_zero(tmp_path, monkeypatch, capsys):
    """With -c 0, an error is returned."""
    monkeypatch.chdir(tmp_path)
    result = main(["-c", "0", "budget"])
    captured = capsys.readouterr()
    assert result == 1
    assert "Invalid count for -c" in captured.out


def test_search_cores_no_count(capsys):
    """With -c and no count, an error is returned."""
    result = main(["-c"])
    captured = capsys.readouterr()
    assert result == 1
    assert "No count provided" in captured.out


def test_search_cores_negative(tmp_path, monkeypatch, capsys):
    """With -c and negative number, an error is returned."""
    monkeypatch.chdir(tmp_path)
    result = main(["-c", "-1", "budget"])
    captured = capsys.readouterr()
    assert result == 1
    assert "Invalid count for -c" in captured.out


def test_search_cores_with_other_flags(tmp_path, monkeypatch, capsys):
    """With -c combined with other flags, all work together."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Budget and revenue overview\n")
    monkeypatch.chdir(tmp_path)
    result = main(["-c", "2", "-a", "budget", "revenue"])
    captured = capsys.readouterr()
    assert result == 0
    assert "1 match(es)" in captured.out


def test_search_quiet_mode(tmp_path, monkeypatch, capsys):
    """With -q flag, banner is suppressed but results still print."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Budget overview\n")
    monkeypatch.chdir(tmp_path)
    result = main(["-q", "budget"])
    captured = capsys.readouterr()
    assert result == 0
    assert "1 match(es)" in captured.out
    assert "OR search" not in captured.out


def test_search_without_quiet_shows_banner(tmp_path, monkeypatch, capsys):
    """Without -q flag, banner is shown."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Budget overview\n")
    monkeypatch.chdir(tmp_path)
    result = main(["budget"])
    captured = capsys.readouterr()
    assert result == 0
    assert "OR search" in captured.out
