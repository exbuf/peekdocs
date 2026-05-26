"""Graphical interface for PeekDocs."""

# PyInstaller + multiprocessing workaround: must run BEFORE any other
# code, especially before importing modules that may themselves create
# multiprocessing workers. When a PyInstaller-bundled exe spawns a
# multiprocessing worker on Windows, the worker re-launches the same
# exe. Without freeze_support(), the worker re-runs main(), which on
# the GUI side means each worker opens another peekdocs window — one
# per CPU core, which the user reported as "multiple screens" when
# running a search without the index (index-bypass search uses a
# multiprocessing.Pool to parallelize across files). With
# freeze_support(), workers recognize they are a frozen child and
# behave as worker processes only.
import multiprocessing
multiprocessing.freeze_support()

from peekdocs.gui._helpers import (
    _build_command_from_values,
    _parse_summary_text,
    _parse_matched_files,
    _parse_inverse_files,
    _build_wizard_regex,
)

def _launch_gui():
    from peekdocs.gui._app import create_app
    create_app()

def main():
    _launch_gui()

if __name__ == "__main__":
    main()
