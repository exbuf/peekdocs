"""Tests for the MCP setup helper core (peekdocs.mcp_setup)."""

import json
import sys

import pytest

from peekdocs import mcp_setup as s


# ── resolve_self_command ───────────────────────────────────────────

class TestResolveSelfCommand:
    def test_targets_mcp_even_when_run_from_gui(self, tmp_path, monkeypatch):
        """Generated from peekdocs-gui, the command must still be peekdocs-mcp
        (its sibling in the same bin dir), not the gui executable."""
        bindir = tmp_path / "bin"
        bindir.mkdir()
        (bindir / "peekdocs-gui").write_text("")   # the running entry point
        mcp = bindir / "peekdocs-mcp"
        mcp.write_text("")
        monkeypatch.setattr(sys, "argv", [str(bindir / "peekdocs-gui")])
        assert s.resolve_self_command() == str(mcp.resolve())

    def test_find_mcp_server_returns_path_when_present(self, tmp_path, monkeypatch):
        bindir = tmp_path / "bin"
        bindir.mkdir()
        (bindir / "peekdocs-gui").write_text("")
        mcp = bindir / "peekdocs-mcp"
        mcp.write_text("")
        monkeypatch.setattr(sys, "argv", [str(bindir / "peekdocs-gui")])
        assert s.find_mcp_server() == str(mcp.resolve())

    def test_find_mcp_server_none_when_absent(self, tmp_path, monkeypatch):
        # No sibling peekdocs-mcp and nothing on PATH → None (drives the GUI's
        # "install the [mcp] extra" banner). resolve_self_command still degrades
        # to the bare name for a still-well-shaped config.
        bindir = tmp_path / "bin"
        bindir.mkdir()
        (bindir / "peekdocs-gui").write_text("")
        monkeypatch.setattr(sys, "argv", [str(bindir / "peekdocs-gui")])
        monkeypatch.setattr(s.shutil, "which", lambda name: None)
        assert s.find_mcp_server() is None
        assert s.resolve_self_command() == "peekdocs-mcp"

    def test_install_command_targets_mcp_extra(self):
        assert "peekdocs[mcp]" in s.INSTALL_COMMAND
        assert s.INSTALL_COMMAND.startswith("pipx install")


# ── render_config / render_json ────────────────────────────────────

class TestRender:
    def test_roots_in_order(self):
        setup = s.McpSetup(roots=["/a", "/b", "/c"])
        cfg = s.render_config(setup)
        args = cfg["mcpServers"]["peekdocs"]["args"]
        # roots appear in order, each preceded by --root
        assert args[:6] == ["--root", "/a", "--root", "/b", "--root", "/c"]

    def test_default_flags_absent(self):
        setup = s.McpSetup(roots=["/a"])
        args = s.render_config(setup)["mcpServers"]["peekdocs"]["args"]
        assert "--ocr" not in args
        assert "--recursive" not in args
        assert "--allow-index" not in args

    def test_max_results_defaults_low_for_local_models(self):
        # The helper suggests a small cap by default so a local model's context
        # window doesn't overflow on a broad search.
        setup = s.McpSetup(roots=["/a"])
        args = s.render_config(setup)["mcpServers"]["peekdocs"]["args"]
        assert setup.max_results == s.SUGGESTED_MAX_RESULTS == 25
        assert args[args.index("--max-results") + 1] == "25"

    def test_max_results_omitted_when_equal_to_server_default(self):
        # Asking for exactly the server's own default is redundant → flag omitted.
        setup = s.McpSetup(roots=["/a"], max_results=s.SERVER_DEFAULT_MAX_RESULTS)
        args = s.render_config(setup)["mcpServers"]["peekdocs"]["args"]
        assert "--max-results" not in args

    def test_flags_present_when_set(self):
        setup = s.McpSetup(
            roots=["/a"], recursive=True, ocr=True, allow_index=True, max_results=50
        )
        args = s.render_config(setup)["mcpServers"]["peekdocs"]["args"]
        assert "--recursive" in args
        assert "--ocr" in args
        assert "--allow-index" in args
        assert args[args.index("--max-results") + 1] == "50"

    def test_command_present(self):
        setup = s.McpSetup(roots=["/a"])
        cfg = s.render_config(setup)
        assert cfg["mcpServers"]["peekdocs"]["command"]

    def test_render_json_valid(self):
        setup = s.McpSetup(roots=["/tmp/x"], ocr=True)
        parsed = json.loads(s.render_json(setup))
        assert "--ocr" in parsed["mcpServers"]["peekdocs"]["args"]

    def test_server_name_respected(self):
        setup = s.McpSetup(roots=["/a"], server_name="custom")
        cfg = s.render_config(setup)
        assert "custom" in cfg["mcpServers"]


# ── write_config ───────────────────────────────────────────────────

class TestWriteConfig:
    def test_merges_and_preserves_other_servers(self, tmp_path):
        path = tmp_path / "mcp.json"
        path.write_text(json.dumps({"mcpServers": {"other": {"command": "x"}}}))
        setup = s.McpSetup(roots=["/a"])
        s.write_config(setup, path, backup=True)
        data = json.loads(path.read_text())
        assert "other" in data["mcpServers"]
        assert "peekdocs" in data["mcpServers"]
        # backup created
        assert path.with_suffix(".json.bak").exists()

    def test_malformed_json_raises_and_preserves(self, tmp_path):
        path = tmp_path / "mcp.json"
        path.write_text("{ this is not valid json ")
        setup = s.McpSetup(roots=["/a"])
        with pytest.raises(s.SetupError):
            s.write_config(setup, path)
        # original untouched
        assert path.read_text() == "{ this is not valid json "

    def test_creates_new_file_with_parent(self, tmp_path):
        path = tmp_path / "nested" / "dir" / "mcp.json"
        setup = s.McpSetup(roots=["/a"])
        s.write_config(setup, path, create_parent=True)
        assert path.exists()
        data = json.loads(path.read_text())
        assert "peekdocs" in data["mcpServers"]

    def test_no_backup_when_disabled(self, tmp_path):
        path = tmp_path / "mcp.json"
        path.write_text(json.dumps({"mcpServers": {}}))
        setup = s.McpSetup(roots=["/a"])
        s.write_config(setup, path, backup=False)
        assert not path.with_suffix(".json.bak").exists()


# ── path helpers ───────────────────────────────────────────────────

class TestPaths:
    def test_lmstudio_paths(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        # Path.home() reads HOME on POSIX
        assert s.lmstudio_dir() == tmp_path / ".lmstudio"
        assert s.lmstudio_config_path() == tmp_path / ".lmstudio" / "mcp.json"
        assert s.lmstudio_installed() is False
        (tmp_path / ".lmstudio").mkdir()
        assert s.lmstudio_installed() is True
