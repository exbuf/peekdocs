"""Tests for the CLI module."""

import os
import re

from docx import Document

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
    assert content.startswith("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n")
    assert "Search Term(s) ==> hello\n" in content
    assert 'Document: sample.docx, Line: 1, Match: "**Hello** world"\n\n' in content
    assert 'Document: sample.docx, Line: 3, Match: "**Hello** again"\n\n' in content


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
    assert content.startswith("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n")
    assert "Search Term(s) ==> zzzzz\n" in content


def test_search_case_insensitive(tmp_path, monkeypatch, capsys):
    doc = Document()
    doc.add_paragraph("Python is great")
    doc.save(str(tmp_path / "test.docx"))

    monkeypatch.chdir(tmp_path)
    main(["PYTHON"])

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert 'Document: test.docx, Line: 1, Match: "**Python** is great"' in content


def test_search_multi_word_query(tmp_path, monkeypatch, capsys):
    doc = Document()
    doc.add_paragraph("Hello world")
    doc.add_paragraph("Hello again")
    doc.save(str(tmp_path / "sample.docx"))

    monkeypatch.chdir(tmp_path)
    result = main(["Hello", "world"])
    captured = capsys.readouterr()

    assert result == 0
    assert "1 match(es)" in captured.out

    content = (tmp_path / "docsearch_results.txt").read_text()
    assert 'Document: sample.docx, Line: 1, Match: "**Hello world**"' in content


def test_banner_always_printed(capsys):
    main(["anything"])
    captured = capsys.readouterr()
    assert BANNER in captured.out
