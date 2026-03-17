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
    assert "See README.md here for details: https://github.com/exbuf/Claude-DocSearch/blob/main/README.md" in captured.out


def test_help(capsys):
    result = main(["-h"])
    captured = capsys.readouterr()
    assert result == 0
    assert "See README.md here for details: https://github.com/exbuf/Claude-DocSearch/blob/main/README.md" in captured.out
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
