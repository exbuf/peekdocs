"""Re-export shim for the GUI's helper functions.

The former 850-LOC ``_helpers.py`` grab-bag was split in v1.2.79 into
three focused modules:

  :mod:`peekdocs.gui._cli_runner`
      Subprocess plumbing (``_run_peekdocs_cli``), CLI-command
      construction (``_build_command_from_values``), and result-file
      parsing (``_parse_summary_text``, ``_parse_matched_files``,
      ``_parse_inverse_files``).

  :mod:`peekdocs.gui._cloud_guard`
      Cloud-synced folder detection (``check_cloud_folder``,
      ``detect_cloud_service``, ``get_safe_output_dir``) and the
      report-write policy guard (``cloud_output_guard``,
      ``gui_cloud_guard``, ``CLOUD_GUARD_*`` outcome sentinels).

  :mod:`peekdocs.gui._dialogs`
      Themed input dialog (``themed_ask_string``) + OS file-open
      shim (``safe_open_file``).

Existing imports through ``peekdocs.gui._helpers`` continue to work
via the re-exports below — that's how the ~30 call sites across
``cli.py`` and the GUI mixins keep working without touching every
one of them. New code should import from the specific submodule
above.

The tiny ``_build_wizard_regex`` helper (7 lines, used only by
:mod:`peekdocs.gui._mixin_wizard`) lives here for now; it doesn't
fit any of the split themes and doesn't merit its own file.
"""
from __future__ import annotations

# Subprocess + command construction + result parsing.
from peekdocs.gui._cli_runner import (
    _run_peekdocs_cli,
    _build_command_from_values,
    _parse_summary_text,
    _parse_matched_files,
    _parse_inverse_files,
)

# Cloud-folder detection + policy guard.
from peekdocs.gui._cloud_guard import (
    check_cloud_folder,
    detect_cloud_service,
    get_safe_output_dir,
    cloud_output_guard,
    gui_cloud_guard,
    CLOUD_GUARD_SAFE,
    CLOUD_GUARD_REDIRECTED,
    CLOUD_GUARD_ALLOWED,
    CLOUD_GUARD_PROMPT,
    CLOUD_GUARD_BLOCKED,
)

# Themed dialogs + OS file open.
from peekdocs.gui._dialogs import (
    themed_ask_string,
    safe_open_file,
)


def _build_wizard_regex(selected_patterns):
    """Combine selected (label, regex) tuples into a single regex.

    Returns a regex string joining patterns with '|' (OR).
    """
    if not selected_patterns:
        return ""
    return "|".join(f"({regex})" for _, regex in selected_patterns)
