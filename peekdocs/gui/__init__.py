"""Graphical interface for PeekDocs."""

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
