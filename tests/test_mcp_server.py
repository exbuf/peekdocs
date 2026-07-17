"""Tests for the read-only MCP server adapter.

The tool logic and guardrails import without the optional ``mcp`` package,
so those tests always run. The server-construction test is skipped when
``mcp`` is not installed.
"""

import os

import pytest

from peekdocs import mcp_server as m


@pytest.fixture(autouse=True)
def _reset_config():
    """Restore server config after each test (it is module-global state)."""
    saved_roots = list(m._CONFIG.roots)
    saved_max = m._CONFIG.max_results
    m._CONFIG.roots = []
    m._CONFIG.max_results = 200
    yield
    m._CONFIG.roots = saved_roots
    m._CONFIG.max_results = saved_max


def _seed(root):
    (root / "a.txt").write_text("the quick brown fox\njumps over\n")
    (root / "b.txt").write_text("another fox appears\n")


# ── Path guard ─────────────────────────────────────────────────────

class TestPathGuard:
    def test_unrestricted_returns_realpath(self, tmp_path):
        assert m._resolve_within_roots(str(tmp_path)) == os.path.realpath(str(tmp_path))

    def test_inside_root_allowed(self, tmp_path):
        m._CONFIG.roots = [os.path.realpath(str(tmp_path))]
        sub = tmp_path / "sub"
        sub.mkdir()
        assert m._resolve_within_roots(str(sub)) == os.path.realpath(str(sub))

    def test_outside_root_blocked(self, tmp_path):
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        other = tmp_path / "other"
        other.mkdir()
        m._CONFIG.roots = [os.path.realpath(str(allowed))]
        with pytest.raises(m.PathNotAllowedError):
            m._resolve_within_roots(str(other))

    def test_traversal_escape_blocked(self, tmp_path):
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        m._CONFIG.roots = [os.path.realpath(str(allowed))]
        with pytest.raises(m.PathNotAllowedError):
            m._resolve_within_roots(str(allowed / ".." / "secret.txt"))

    def test_resolve_dir_defaults_to_first_root(self, tmp_path):
        m._CONFIG.roots = [os.path.realpath(str(tmp_path))]
        assert m._resolve_dir(None) == os.path.realpath(str(tmp_path))


# ── Result cap ─────────────────────────────────────────────────────

class TestCap:
    def test_truncates_and_reports(self):
        m._CONFIG.max_results = 2
        rows, env = m._cap([1, 2, 3, 4, 5])
        assert rows == [1, 2]
        assert env == {"truncated": True, "total": 5, "returned": 2}

    def test_under_cap_untouched(self):
        m._CONFIG.max_results = 10
        rows, env = m._cap([1, 2])
        assert rows == [1, 2]
        assert env == {"truncated": False, "total": 2, "returned": 2}


# ── Tool logic ─────────────────────────────────────────────────────

class TestSearchDocuments:
    def test_finds_matches(self, tmp_path):
        _seed(tmp_path)
        out = m.search_documents(["fox"], directory=str(tmp_path), recursive=True)
        assert out["total"] == 2
        assert {os.path.basename(x["file"]) for x in out["matches"]} == {"a.txt", "b.txt"}
        assert out["files_searched"] >= 2

    def test_reports_searched_directory(self, tmp_path):
        _seed(tmp_path)
        out = m.search_documents(["fox"], directory=str(tmp_path), recursive=True)
        assert out["searched_directory"] == os.path.realpath(str(tmp_path))

    def test_read_only_no_index_written(self, tmp_path):
        _seed(tmp_path)
        m.search_documents(["fox"], directory=str(tmp_path), recursive=True)
        assert not (tmp_path / ".peekdocs.db").exists()

    def test_path_guard_enforced(self, tmp_path):
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        other = tmp_path / "other"
        other.mkdir()
        _seed(other)
        m._CONFIG.roots = [os.path.realpath(str(allowed))]
        with pytest.raises(m.PathNotAllowedError):
            m.search_documents(["fox"], directory=str(other))

    def test_truncation_envelope(self, tmp_path):
        _seed(tmp_path)
        m._CONFIG.max_results = 1
        out = m.search_documents(["fox"], directory=str(tmp_path), recursive=True)
        assert out["truncated"] is True
        assert out["total"] == 2
        assert len(out["matches"]) == 1


class TestOtherTools:
    def test_get_document_context(self, tmp_path):
        _seed(tmp_path)
        out = m.get_document_context("a.txt", ["fox"], directory=str(tmp_path))
        assert out["file"] == "a.txt"
        assert out["searched_directory"] == os.path.realpath(str(tmp_path))
        assert any("fox" in x["text"] for x in out["matches"])

    def test_inventory_folder_tool(self, tmp_path):
        _seed(tmp_path)
        out = m.inventory_folder(directory=str(tmp_path))
        assert out["total"] == 2
        assert out["searched_directory"] == os.path.realpath(str(tmp_path))
        assert all("size_human" in row for row in out["files"])
        # modified is a human-readable ISO-8601 string, not a raw epoch float
        for row in out["files"]:
            assert isinstance(row["modified"], str)
            assert row["modified"][:2] == "20"  # e.g. "2026-07-08T14:30:00"

    def test_list_supported_file_types_tool(self):
        out = m.list_supported_file_types()
        assert ".pdf" in out["extensions"]
        assert out["count"] == len(out["extensions"])


# ── Tier-2 tools: suites + regex collections ───────────────────────

class TestSuiteAndCollectionTools:
    def test_list_and_run_search_suite(self, tmp_path):
        from peekdocs.collection import add_saved_search, add_suite

        (tmp_path / "a.txt").write_text("budget line here\nother stuff\n")
        add_saved_search(
            str(tmp_path), "find budget",
            {"search_text": "budget", "recursive": True},
        )
        add_suite(str(tmp_path), "My Suite", ["find budget"])

        listing = m.list_search_suites(directory=str(tmp_path))
        assert "My Suite" in listing["suites"]

        out = m.run_search_suite("My Suite", directory=str(tmp_path))
        assert out["suite"] == "My Suite"
        assert out["total_matches"] >= 1
        assert out["searches"][0]["name"] == "find budget"
        assert out["searches"][0]["match_count"] >= 1
        assert any("budget" in x["text"] for x in out["matches"])

    def test_list_and_run_regex_collection(self, tmp_path):
        import json

        (tmp_path / "a.txt").write_text("call 555-1234 today\n")
        # ~/.peekdocs_regex_collections.json is redirected to tmp_path by the
        # autouse isolate_home fixture in conftest.py, so write it there.
        coll = {"Phones": [{"name": "US phone", "regex": r"\d{3}-\d{4}", "enabled": True}]}
        (tmp_path / ".peekdocs_regex_collections.json").write_text(json.dumps(coll))

        names = m.list_regex_collections()
        assert "Phones" in names["collections"]

        out = m.run_regex_collection("Phones", directory=str(tmp_path), recursive=True)
        assert out["collection"] == "Phones"
        assert out["total_matches"] >= 1
        assert out["patterns"][0]["name"] == "US phone"
        assert out["patterns"][0]["file_count"] >= 1
        assert any("555-1234" in x["text"] for x in out["matches"])

    def test_run_suite_path_guard(self, tmp_path):
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        other = tmp_path / "other"
        other.mkdir()
        m._CONFIG.roots = [os.path.realpath(str(allowed))]
        with pytest.raises(m.PathNotAllowedError):
            m.run_search_suite("Whatever", directory=str(other))


# ── main() argument handling ───────────────────────────────────────

class TestMain:
    def test_root_is_required(self):
        # No --root: argparse should error out (exit code 2) before the
        # server ever starts, so this never blocks on the stdio loop.
        with pytest.raises(SystemExit) as exc:
            m.main(["--max-results", "5"])
        assert exc.value.code == 2


# ── Server construction (requires the optional `mcp` package) ───────

class TestBuildServer:
    def test_registers_all_tools(self):
        pytest.importorskip("mcp.server.fastmcp")
        import asyncio

        server = m.build_server()
        tools = asyncio.run(server.list_tools())
        names = {t.name for t in tools}
        expected = {fn.__name__ for fn in m._TOOLS}
        assert expected <= names
