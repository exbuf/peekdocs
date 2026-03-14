"""Tests for the CLI module."""

import os
import re

from docx import Document
from docx.enum.text import WD_COLOR_INDEX
from fpdf import FPDF

from docsearch.cli import BANNER, main


def test_no_args(capsys):
    result = main([])
    captured = capsys.readouterr()
    assert result == 0
    assert BANNER in captured.out


def test_help(capsys):
    result = main(["help"])
    captured = capsys.readouterr()
    assert result == 0
    assert "docsearch help...lists all available commands" in captured.out
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
    assert 'Document: sample.docx, Paragraph: 1, Line: 1, Match:\n"**Hello** world"\n\n' in content
    assert 'Document: sample.docx, Paragraph: 3, Line: 3, Match:\n"**Hello** again"\n\n' in content

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
    assert 'Document: test.docx, Paragraph: 1, Line: 1, Match:\n"**Python** is great"' in content


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


def test_banner_always_printed(capsys):
    main(["anything"])
    captured = capsys.readouterr()
    assert BANNER in captured.out
