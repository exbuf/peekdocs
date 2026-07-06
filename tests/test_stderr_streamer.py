"""Tests for the frozen-path stderr streaming fix.

Motivated by a 1.2.79 user report: installing the GUI ``.exe`` from the
website vs. the pipx install produced identical search results, but the
``.exe``'s status line skipped the report-writing progression that the
pipx install showed. Root cause: the PyInstaller-frozen path in
``peekdocs.gui._cli_runner._run_peekdocs_cli`` redirected stderr into a
plain ``io.StringIO()`` that was only readable after ``_cli_main``
returned, so the GUI never saw PHASE markers as they were printed.

Fix: :class:`_StderrLineStreamer` — a ``StringIO`` subclass that also
forwards completed lines to the caller's ``on_stderr_line`` callback,
matching what the subprocess path's background reader thread does.
"""
from __future__ import annotations

from peekdocs.gui._cli_runner import _StderrLineStreamer


def test_streamer_forwards_complete_lines():
    """Every completed line (newline-terminated) reaches the callback."""
    received = []
    s = _StderrLineStreamer(received.append)
    s.write("first\n")
    s.write("second\n")
    s.write("third\n")
    assert received == ["first", "second", "third"]


def test_streamer_buffers_partial_lines():
    """A write without a terminating newline is held back until the
    line completes — otherwise the callback would see a fragment and
    then the rest of the line as separate events."""
    received = []
    s = _StderrLineStreamer(received.append)
    s.write("PHASE: writing-")
    assert received == []
    s.write("docx\n")
    assert received == ["PHASE: writing-docx"]


def test_streamer_splits_multi_line_writes():
    """A single write() containing multiple lines emits each as a
    separate event."""
    received = []
    s = _StderrLineStreamer(received.append)
    s.write("line1\nline2\nline3\n")
    assert received == ["line1", "line2", "line3"]


def test_streamer_handles_windows_line_endings():
    """CRLF ('\\r\\n') from Windows-encoded output emits clean lines
    without the trailing CR."""
    received = []
    s = _StderrLineStreamer(received.append)
    s.write("phase1\r\nphase2\r\n")
    assert received == ["phase1", "phase2"]


def test_streamer_getvalue_returns_full_content():
    """The base ``io.StringIO`` semantics still hold — ``getvalue()`` at
    the end returns everything ever written, including partial lines
    that were never emitted as events. The subprocess path's
    ``stderr_buf.append(raw_line)`` behavior has the same "keep the
    whole transcript" contract."""
    received = []
    s = _StderrLineStreamer(received.append)
    s.write("emitted\n")
    s.write("partial-tail-no-newline")
    assert received == ["emitted"]
    assert s.getvalue() == "emitted\npartial-tail-no-newline"


def test_streamer_swallows_callback_exceptions():
    """A callback that raises must not break the stream — the search
    would otherwise die mid-flight because a status-line updater
    threw."""
    def bad(_line):
        raise RuntimeError("callback bug")

    s = _StderrLineStreamer(bad)
    # Should not raise
    s.write("line-that-triggers-bad-callback\n")
    # Still records to underlying buffer
    assert "line-that-triggers-bad-callback" in s.getvalue()


def test_streamer_empty_writes():
    """Empty write and empty pending state must not spuriously emit
    empty events."""
    received = []
    s = _StderrLineStreamer(received.append)
    s.write("")
    s.write("\n")  # a bare newline is a line — the empty one
    assert received == [""]
