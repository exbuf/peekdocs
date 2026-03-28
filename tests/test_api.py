"""Tests for the public library API."""

import os

import pytest
from docx import Document

from docsearch.api import SearchMatch, SearchResult, search


@pytest.fixture(autouse=True)
def isolate_home(tmp_path, monkeypatch):
    """Prevent tests from reading the user's real ~/.docsearchrc."""
    monkeypatch.setenv("HOME", str(tmp_path))


def _make_docx(path, paragraphs):
    """Helper: create a .docx with the given paragraph strings."""
    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    doc.save(str(path))


# ── SearchMatch tuple compatibility ─────────────────────────────

class TestSearchMatch:
    def test_unpack(self):
        m = SearchMatch("/dir", "file.txt", 1, "hello")
        fd, fn, ln, tx = m
        assert fd == "/dir"
        assert fn == "file.txt"
        assert ln == 1
        assert tx == "hello"

    def test_indexing(self):
        m = SearchMatch("/dir", "file.txt", 1, "hello")
        assert m[0] == "/dir"
        assert m[1] == "file.txt"
        assert m[2] == 1
        assert m[3] == "hello"

    def test_len(self):
        m = SearchMatch("/dir", "file.txt", 1, "hello")
        assert len(m) == 4

    def test_iter_in_loop(self):
        matches = [SearchMatch("/a", "f1.txt", 1, "x"), SearchMatch("/b", "f2.txt", 2, "y")]
        for fd, fn, ln, tx in matches:
            assert isinstance(fd, str)
            assert isinstance(ln, int)


# ── search() function ───────────────────────────────────────────

class TestSearch:
    def test_basic(self, tmp_path, monkeypatch):
        _make_docx(tmp_path / "doc.docx", ["budget report", "other line", "budget summary"])
        monkeypatch.chdir(tmp_path)
        result = search(["budget"], directory=str(tmp_path))
        assert isinstance(result, SearchResult)
        assert len(result.matches) == 2
        assert result.elapsed > 0
        assert len(result.files_searched) == 1
        for m in result.matches:
            assert "budget" in m.text.lower()

    def test_no_matches(self, tmp_path, monkeypatch):
        _make_docx(tmp_path / "doc.docx", ["hello world"])
        monkeypatch.chdir(tmp_path)
        result = search(["zzzznotfound"], directory=str(tmp_path))
        assert len(result.matches) == 0
        assert len(result.files_searched) == 1

    def test_match_all(self, tmp_path, monkeypatch):
        _make_docx(tmp_path / "doc.docx", [
            "budget and revenue report",
            "budget only",
            "revenue only",
        ])
        monkeypatch.chdir(tmp_path)
        result = search(["budget", "revenue"], directory=str(tmp_path), match_all=True)
        assert len(result.matches) == 1
        assert "budget" in result.matches[0].text.lower()
        assert "revenue" in result.matches[0].text.lower()

    def test_regex(self, tmp_path, monkeypatch):
        _make_docx(tmp_path / "doc.docx", ["call 555-123-4567", "no phone here"])
        monkeypatch.chdir(tmp_path)
        result = search([r"\d{3}-\d{3}-\d{4}"], directory=str(tmp_path), use_regex=True)
        assert len(result.matches) == 1
        assert "555" in result.matches[0].text

    def test_wildcard(self, tmp_path, monkeypatch):
        _make_docx(tmp_path / "doc.docx", ["budget report", "budgetary concerns", "other"])
        monkeypatch.chdir(tmp_path)
        result = search(["budg*"], directory=str(tmp_path), use_wildcard=True)
        assert len(result.matches) == 2

    def test_cores_one(self, tmp_path, monkeypatch):
        _make_docx(tmp_path / "doc.docx", ["budget report"])
        monkeypatch.chdir(tmp_path)
        result = search(["budget"], directory=str(tmp_path), cores=1)
        assert len(result.matches) == 1

    def test_progress_callback(self, tmp_path, monkeypatch):
        _make_docx(tmp_path / "doc.docx", ["budget report"])
        monkeypatch.chdir(tmp_path)
        calls = []
        result = search(
            ["budget"], directory=str(tmp_path), cores=1,
            progress=lambda done, total, fn: calls.append((done, total, fn)),
        )
        assert len(calls) > 0
        # Last call should indicate completion
        assert calls[-1][0] == calls[-1][1]

    def test_default_directory(self, tmp_path, monkeypatch):
        _make_docx(tmp_path / "doc.docx", ["budget report"])
        monkeypatch.chdir(tmp_path)
        result = search(["budget"])
        assert len(result.matches) == 1

    def test_used_index_false(self, tmp_path, monkeypatch):
        _make_docx(tmp_path / "doc.docx", ["budget"])
        monkeypatch.chdir(tmp_path)
        result = search(["budget"], directory=str(tmp_path))
        assert result.used_index is False


# ── Expression search ─────────────────────────────────────────────

class TestExpressionSearch:
    def test_expression_and(self, tmp_path, monkeypatch):
        _make_docx(tmp_path / "doc.docx", [
            "budget and revenue report",
            "budget only",
            "revenue only",
        ])
        monkeypatch.chdir(tmp_path)
        result = search([], directory=str(tmp_path), expression="budget AND revenue")
        assert len(result.matches) == 1
        assert "budget" in result.matches[0].text.lower()
        assert "revenue" in result.matches[0].text.lower()

    def test_expression_or(self, tmp_path, monkeypatch):
        _make_docx(tmp_path / "doc.docx", [
            "budget report",
            "revenue report",
            "other line",
        ])
        monkeypatch.chdir(tmp_path)
        result = search([], directory=str(tmp_path), expression="budget OR revenue")
        assert len(result.matches) == 2

    def test_expression_not(self, tmp_path, monkeypatch):
        _make_docx(tmp_path / "doc.docx", [
            "budget draft",
            "budget final",
            "other line",
        ])
        monkeypatch.chdir(tmp_path)
        result = search([], directory=str(tmp_path), expression="budget AND NOT draft")
        assert len(result.matches) == 1
        assert "final" in result.matches[0].text.lower()

    def test_expression_grouped(self, tmp_path, monkeypatch):
        _make_docx(tmp_path / "doc.docx", [
            "budget and cost analysis",
            "revenue and profit analysis",
            "budget and profit analysis",
            "other line",
        ])
        monkeypatch.chdir(tmp_path)
        result = search([], directory=str(tmp_path),
                        expression="(budget OR revenue) AND (cost OR profit)")
        assert len(result.matches) == 3

    def test_expression_no_matches(self, tmp_path, monkeypatch):
        _make_docx(tmp_path / "doc.docx", ["hello world"])
        monkeypatch.chdir(tmp_path)
        result = search([], directory=str(tmp_path), expression="budget AND revenue")
        assert len(result.matches) == 0

    def test_expression_with_regex(self, tmp_path, monkeypatch):
        _make_docx(tmp_path / "doc.docx", [
            "call 555-123-4567 about budget",
            "call 555-123-4567 about revenue",
            "no phone here about budget",
        ])
        monkeypatch.chdir(tmp_path)
        result = search([], directory=str(tmp_path), use_regex=True,
                        expression=r"\d{3}-\d{3}-\d{4} AND budget")
        assert len(result.matches) == 1
        assert "555" in result.matches[0].text

    def test_expression_with_wildcard(self, tmp_path, monkeypatch):
        _make_docx(tmp_path / "doc.docx", [
            "budget and revenue report",
            "budgetary concerns",
            "revenue only",
        ])
        monkeypatch.chdir(tmp_path)
        result = search([], directory=str(tmp_path), use_wildcard=True,
                        expression="budg* AND rev*")
        assert len(result.matches) == 1
        assert "budget" in result.matches[0].text.lower()
        assert "revenue" in result.matches[0].text.lower()

    def test_expression_with_fuzzy(self, tmp_path, monkeypatch):
        _make_docx(tmp_path / "doc.docx", [
            "the budget report is ready",
            "other line",
        ])
        monkeypatch.chdir(tmp_path)
        result = search([], directory=str(tmp_path), use_fuzzy=True,
                        expression="budgt")
        assert len(result.matches) == 1

    def test_expression_quoted_term(self, tmp_path, monkeypatch):
        _make_docx(tmp_path / "doc.docx", [
            "the annual report is ready",
            "annual meeting scheduled",
            "other report line",
        ])
        monkeypatch.chdir(tmp_path)
        result = search([], directory=str(tmp_path),
                        expression='"annual report"')
        assert len(result.matches) == 1
        assert "annual report" in result.matches[0].text.lower()


# ── Validation errors ────────────────────────────────────────────

class TestSearchValidation:
    def test_no_terms(self):
        with pytest.raises(ValueError, match="No search terms"):
            search([])

    def test_regex_plus_fuzzy(self):
        with pytest.raises(ValueError, match="fuzzy and regex"):
            search(["test"], use_regex=True, use_fuzzy=True)

    def test_wildcard_plus_regex(self):
        with pytest.raises(ValueError, match="wildcard and regex"):
            search(["test"], use_wildcard=True, use_regex=True)

    def test_wildcard_plus_fuzzy(self):
        with pytest.raises(ValueError, match="wildcard and fuzzy"):
            search(["test"], use_wildcard=True, use_fuzzy=True)

    def test_invalid_regex(self):
        with pytest.raises(ValueError, match="Invalid regex"):
            search(["[invalid"], use_regex=True)

    def test_proximity_needs_two_terms(self):
        with pytest.raises(ValueError, match="Proximity"):
            search(["single"], proximity=5)

    def test_expression_with_match_all(self):
        with pytest.raises(ValueError, match="expression with match_all"):
            search([], expression="a AND b", match_all=True)

    def test_expression_with_exclude(self):
        with pytest.raises(ValueError, match="expression with exclude_terms"):
            search([], expression="a AND b", exclude_terms=["c"])

    def test_expression_with_proximity(self):
        with pytest.raises(ValueError, match="expression with proximity"):
            search(["a", "b"], expression="a AND b", proximity=5)

    def test_expression_invalid_regex(self):
        with pytest.raises(ValueError, match="Invalid regex"):
            search([], expression="[invalid AND budget", use_regex=True)
