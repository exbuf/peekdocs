"""Project-wide pytest configuration.

The autouse ``isolate_home`` fixture below redirects every test's notion of
``~`` to a fresh per-test temporary directory. peekdocs reads and writes
several user-level files via ``os.path.expanduser("~")`` —
``~/.peekdocsrc``, ``~/.peekdocs_runs.log``, ``~/.peekdocs_suites_index.json``,
``~/.peekdocs_history.json``, ``~/.peekdocs_bookmarks.json``,
``~/.peekdocs_regex_collections.json``, ``~/peekdocs_reports`` — and without
isolation, tests either:

1. Read configuration / state left behind by the runner's real account
   (this is what made tests pass on the maintainer's machine but fail on
   a fresh Windows CI runner with no prior config), or
2. Pollute the runner's real home directory with files from a failing
   test, which is rude on CI and dangerous on a workstation.

Cross-platform note:

  * On Unix-like systems, ``os.path.expanduser`` reads ``$HOME``.
  * On Windows (recent CPython), ``ntpath.expanduser`` reads
    ``%USERPROFILE%`` first, then falls back to ``%HOMEDRIVE%`` +
    ``%HOMEPATH%``. It does NOT consult ``$HOME`` on Windows.

Setting only ``HOME`` therefore isolated macOS/Linux tests but silently
no-op'd on Windows, leading to the failing-Windows-CI symptom that
prompted this fixture. We redirect ``HOME``, ``USERPROFILE``, ``HOMEDRIVE``,
and ``HOMEPATH`` together so the isolation behaves the same on every
platform.
"""

import os
import pytest


@pytest.fixture(autouse=True)
def isolate_home(tmp_path, monkeypatch):
    """Redirect ~ to the per-test ``tmp_path`` on every supported platform.

    Tests can write to ``tmp_path / ".peekdocsrc"`` (or any other
    ``~/.peekdocs*`` file) and have peekdocs find it there, with no further
    setup. Pointing HOME at ``tmp_path`` directly (rather than a
    sub-directory) matches the convention the existing test suite already
    uses, so this fixture is a drop-in replacement for the per-file
    ``isolate_home`` fixtures that existed before.
    """
    home_str = str(tmp_path)

    # POSIX, and Windows when HOME happens to be set (e.g. Git Bash).
    monkeypatch.setenv("HOME", home_str)

    # Windows: ntpath.expanduser checks USERPROFILE first.
    monkeypatch.setenv("USERPROFILE", home_str)

    # Windows fallback (HOMEDRIVE + HOMEPATH, used only if USERPROFILE
    # is unset). Set both anyway so the test never falls through to the
    # runner's real account regardless of which resolution path ntpath
    # takes.
    drive, tail = os.path.splitdrive(home_str)
    monkeypatch.setenv("HOMEDRIVE", drive)
    monkeypatch.setenv("HOMEPATH", tail or home_str)

    yield tmp_path
