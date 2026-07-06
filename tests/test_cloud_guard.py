"""Tests for the cloud-output guard.

Guards every peekdocs report-write path (Standard / Suite / Regex
Search across CLI, GUI, and Python API) so writes to cloud-synced
directories are either redirected to ~/peekdocs_reports (sticky
config) or blocked (interactive CLI abort / GUI prompt).
"""

import os
import pytest
from unittest.mock import patch

from peekdocs.gui._helpers import (
    detect_cloud_service,
    cloud_output_guard,
    CLOUD_GUARD_SAFE, CLOUD_GUARD_REDIRECTED,
    CLOUD_GUARD_ALLOWED, CLOUD_GUARD_PROMPT,
    get_safe_output_dir,
)


@pytest.mark.parametrize("path, expected", [
    ("/Users/bob/Documents/work", None),
    ("/tmp", None),
    ("", None),
    ("/Users/bob/Library/Mobile Documents/com~apple~CloudDocs/x", "iCloud Drive"),
    ("/Users/bob/iCloud Drive/x", "iCloud Drive"),
    ("/Users/bob/Dropbox/x", "Dropbox"),
    ("/Users/bob/Dropbox (Company Name)/x", "Dropbox"),
    ("/Users/bob/Google Drive/My Drive/x", "Google Drive"),
    ("/Users/bob/GoogleDrive/x", "Google Drive"),
    ("/Users/bob/OneDrive/x", "OneDrive"),
    ("/Users/bob/OneDrive - Company/x", "OneDrive"),
])
def test_detect_cloud_service(path, expected):
    assert detect_cloud_service(path) == expected


def test_guard_safe_path(tmp_path):
    final_dir, outcome, service = cloud_output_guard(str(tmp_path))
    assert final_dir == str(tmp_path)
    assert outcome == CLOUD_GUARD_SAFE
    assert service is None


def test_guard_cloud_prompt():
    final_dir, outcome, service = cloud_output_guard("/Users/x/Dropbox/work")
    assert final_dir == "/Users/x/Dropbox/work"
    assert outcome == CLOUD_GUARD_PROMPT
    assert service == "Dropbox"


def test_guard_cloud_redirect_when_config_on():
    final_dir, outcome, service = cloud_output_guard(
        "/Users/x/iCloud Drive/work", redirect_to_safe=True,
    )
    assert final_dir == get_safe_output_dir()
    assert outcome == CLOUD_GUARD_REDIRECTED
    assert service == "iCloud Drive"


def test_guard_cloud_allowed_when_flag_on():
    final_dir, outcome, service = cloud_output_guard(
        "/Users/x/OneDrive - Foo/work", allow_cloud=True,
    )
    assert final_dir == "/Users/x/OneDrive - Foo/work"
    assert outcome == CLOUD_GUARD_ALLOWED
    assert service == "OneDrive"


def test_guard_redirect_takes_precedence_over_allow():
    """If both config and flag are set, config wins (redirect is safer)."""
    final_dir, outcome, service = cloud_output_guard(
        "/Users/x/Dropbox/work",
        redirect_to_safe=True,
        allow_cloud=True,
    )
    assert final_dir == get_safe_output_dir()
    assert outcome == CLOUD_GUARD_REDIRECTED


def test_cli_regex_collection_blocks_cloud_without_flag(tmp_path, monkeypatch, capsys):
    """--regex-collection into a cloud-synced -d aborts with exit 2 unless
    --allow-cloud-output is passed."""
    import json
    from peekdocs.cli import main

    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / "doc.txt").write_text("TODO: fix\n")
    rc_data = {"c": [{"name": "T", "regex": r"TODO", "enabled": True}]}
    (tmp_path / ".peekdocs_regex_collections.json").write_text(json.dumps(rc_data))

    # Patch detect_cloud_service to force cloud detection on tmp_path.
    with patch("peekdocs.gui._cloud_guard.detect_cloud_service", return_value="iCloud Drive"):
        rc = main(["--regex-collection", "c", "-d", str(tmp_path), "-r"])
    assert rc == 2
    captured = capsys.readouterr()
    assert "iCloud Drive" in captured.err
    assert "--allow-cloud-output" in captured.err


def test_cli_regex_collection_allowed_with_flag(tmp_path, monkeypatch, capsys):
    """--allow-cloud-output lets the write proceed with a warning."""
    import json
    from peekdocs.cli import main

    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / "doc.txt").write_text("TODO: fix\n")
    rc_data = {"c": [{"name": "T", "regex": r"TODO", "enabled": True}]}
    (tmp_path / ".peekdocs_regex_collections.json").write_text(json.dumps(rc_data))

    with patch("peekdocs.gui._cloud_guard.detect_cloud_service", return_value="Dropbox"):
        rc = main([
            "--regex-collection", "c", "-d", str(tmp_path), "-r",
            "--allow-cloud-output",
        ])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Dropbox" in captured.err  # warning printed
    assert "--allow-cloud-output" in captured.err
