"""Shared core for the peekdocs MCP setup helper.

Generates (and optionally writes) the LM Studio ``mcp.json`` config that
points an MCP host at the ``peekdocs-mcp`` server. This module is the single
source of truth behind all three entry points — the ``peekdocs-mcp`` CLI
flags, the interactive folder picker, and the GUI Tools-menu dialog.

It is deliberately small and dependency-free (stdlib only). The folder
picker uses ``tkinter`` lazily and degrades to ``None`` when no display is
available, so callers can fall back to a required ``--root``.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path


class SetupError(Exception):
    """Raised when a config file can't be read/merged (e.g. malformed JSON)."""


@dataclass
class McpSetup:
    """The knobs that shape a generated ``peekdocs-mcp`` invocation."""

    roots: list[str] = field(default_factory=list)  # absolute paths
    max_results: int = 200
    recursive: bool = False
    ocr: bool = False
    allow_index: bool = False
    server_name: str = "peekdocs"


def resolve_self_command() -> str:
    """Return an absolute path to the ``peekdocs-mcp`` executable to launch.

    Resolves ``peekdocs-mcp`` *specifically* — not whichever peekdocs entry
    point happens to be running — so the generated config is correct even when
    produced from the GUI (``peekdocs-gui``) or via ``python -m``. Looks in the
    running executable's own bin directory first (the console scripts are
    installed side by side), then on PATH, then falls back to the bare name.
    """
    names = ("peekdocs-mcp", "peekdocs-mcp.exe")
    here = Path(sys.argv[0]).resolve().parent
    for name in names:
        cand = here / name
        if cand.exists():
            return str(cand)
    for name in names:
        found = shutil.which(name)
        if found:
            return str(Path(found).resolve())
    return "peekdocs-mcp"


def build_args(s: McpSetup) -> list[str]:
    """Build the ``args`` list for the MCP server command from ``s``."""
    args: list[str] = []
    for r in s.roots:
        args += ["--root", r]
    if s.recursive:
        args.append("--recursive")
    if s.ocr:
        args.append("--ocr")
    if s.allow_index:
        args.append("--allow-index")
    if s.max_results != 200:
        args += ["--max-results", str(s.max_results)]
    return args


def render_config(s: McpSetup) -> dict:
    """Return the full ``mcpServers`` config dict for ``s``."""
    return {
        "mcpServers": {
            s.server_name: {"command": resolve_self_command(), "args": build_args(s)}
        }
    }


def render_json(s: McpSetup) -> str:
    """Return the pretty-printed JSON for :func:`render_config`."""
    return json.dumps(render_config(s), indent=2)


def lmstudio_dir() -> Path:
    """Return the default LM Studio config directory (``~/.lmstudio``)."""
    return Path.home() / ".lmstudio"


def lmstudio_config_path() -> Path:
    """Return the default LM Studio ``mcp.json`` path."""
    return lmstudio_dir() / "mcp.json"


def lmstudio_installed() -> bool:
    """Return True if the default LM Studio config directory exists."""
    return lmstudio_dir().is_dir()


def write_config(
    s: McpSetup, path: Path, *, backup: bool = True, create_parent: bool = False
) -> Path:
    """Merge ONLY the ``server_name`` key into ``path``'s ``mcpServers``.

    Preserves any other servers already configured in the file. Backs the
    file up to ``<name>.json.bak`` before overwriting (when ``backup`` and the
    file already exists). Raises :class:`SetupError` if the file exists but is
    not valid JSON — without clobbering it.
    """
    if create_parent:
        path.parent.mkdir(parents=True, exist_ok=True)
    data: dict = {"mcpServers": {}}
    if path.exists() and path.read_text().strip():
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            raise SetupError(
                f"{path} isn't valid JSON — fix or remove it first ({e})."
            )
        if backup:
            shutil.copy2(path, path.with_suffix(".json.bak"))
    if not isinstance(data, dict):
        data = {}
    servers = data.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        servers = {}
        data["mcpServers"] = servers
    servers[s.server_name] = render_config(s)["mcpServers"][s.server_name]
    path.write_text(json.dumps(data, indent=2) + "\n")
    return path


def pick_folder(title: str = "Folder the assistant may search") -> str | None:
    """Native folder picker via stdlib tkinter.

    Returns the chosen folder's real path, or ``None`` when the user cancels
    or no display / Tk is available (so callers can fall back to ``--root``).
    """
    try:
        import tkinter as tk
        from tkinter import filedialog

        existing = getattr(tk, "_default_root", None)
        root = existing or tk.Tk()
        if existing is None:
            root.withdraw()
        chosen = filedialog.askdirectory(title=title) or None
        if existing is None:
            root.destroy()
        return os.path.realpath(chosen) if chosen else None
    except Exception:
        return None
