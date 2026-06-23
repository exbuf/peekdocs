"""PeekDocs GUI — SearchMixin."""

import os
import platform
import re
import subprocess
import sys
import threading
import time
from datetime import datetime

import customtkinter as ctk

from peekdocs.gui._tooltip import Tooltip
from peekdocs.scanner import RESULT_FILE_PREFIXES
from peekdocs.gui._helpers import (
    _build_command_from_values,
    _parse_summary_text,
    _parse_matched_files,
    _parse_inverse_files,
    _build_wizard_regex,
)
from tkinter import filedialog, messagebox

class SearchMixin:
    def start_search(self):
        """Validate inputs, build the CLI command, and launch a search thread."""
        if self.process is not None:
            # Mark this run as user-cancelled BEFORE sending the signal
            # so the completion handler can short-circuit the returncode
            # dispatch. SIGTERM exits with returncode = -15 on Unix but
            # = 1 on Windows (`TerminateProcess` uses exit code 1 by
            # convention) — and 1 happens to be peekdocs's "no matches"
            # code, so without the flag a Windows cancel would land in
            # the "Search complete. No matches found." branch.
            self._search_cancelled = True
            self.process.terminate()
            self.search_button.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("run_standard_search_label"), fg_color="#2196F3", hover_color="#1976D2", text_color="white")
            return
        # Cancel multi-folder search if running
        if hasattr(self, '_multi_folder_cancelled') and self._multi_folder_cancelled is False:
            self._multi_folder_cancelled = True
            self.status_label.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("status_cancelling_multi_folder"), text_color=("blue", "#66BBFF"))
            self.search_button.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("run_standard_search_label"), fg_color="#2196F3", hover_color="#1976D2", text_color="white")
            return

        # Reset report-button context to Standard Search; a prior Suite run
        # may have left this pointed at "peekdocs_suite_results".
        self._report_file_prefix = "peekdocs_standard_results"

        # Wait for any in-progress index build or auto-refresh to finish
        if hasattr(self, '_index_process') and self._index_process is not None:
            self._show_error("Index build in progress — please wait for it to finish, or cancel it in Manage Indexes.")
            return
        if self._refresh_running:
            self._show_error("Index refresh in progress — please wait a moment.")
            return

        # Pause scheduled auto-refresh while search runs
        if self._refresh_timer_id is not None:
            self.after_cancel(self._refresh_timer_id)
            self._refresh_timer_id = None

        raw_folder = self.folder_entry.get().strip()
        # Multi-folder support: semicolon-separated paths
        if ";" in raw_folder:
            folders = [os.path.normpath(f.strip()) for f in raw_folder.split(";") if f.strip()]
            invalid = [f for f in folders if not os.path.isdir(f)]
            if invalid:
                self._show_error(f"Invalid folder(s): {', '.join(invalid)}")
                return
            if len(folders) > 1:
                self._multi_folder_search(folders)
                return
            folder = folders[0]
        else:
            folder = os.path.normpath(raw_folder)
        if not folder or not os.path.isdir(folder):
            self._show_error("Please select a valid folder.")
            return

        search_text = self.search_entry.get().strip()
        range_text = self.range_entry.get().strip()
        if not search_text and not range_text:
            self._show_error("Please enter search terms or a range filter.")
            return

        # Auto-save search terms, folder, and max file size for next launch
        # (max_file_size_mb must be saved here so the CLI subprocess picks it up)
        try:
            from peekdocs.cli import _load_config, _save_config
            cfg = _load_config()
            cfg["search_terms"] = search_text
            cfg["folder"] = folder
            try:
                mfs = int(self.max_file_size_entry.get().strip() or "100")
                cfg["max_file_size_mb"] = mfs
            except ValueError:
                pass
            _save_config(cfg)
        except Exception:
            pass

        # Record in recent searches (max 10, no duplicate terms, persisted).
        # Each entry is a full config dict (terms + folder + all advanced
        # search options) so selecting one from the popup restores the
        # whole configuration. Legacy plain-string entries from older
        # builds still work — see _recent_entry_terms.
        if search_text:
            snap = self._snapshot_search_config()
            self._recent_searches = [
                e for e in self._recent_searches
                if self._recent_entry_terms(e) != search_text
            ]
            self._recent_searches.insert(0, snap)
            self._recent_searches = self._recent_searches[:10]
        self._save_ui_preference("recent_searches", self._recent_searches)

        if self.index_search_var.get() == "on":
            index_path = os.path.join(folder, ".peekdocs.db")
            if not os.path.exists(index_path):
                self._show_error(
                    "No search index found in this folder. "
                    "First use Browse to navigate to the folder where your files are, "
                    "then click Build Index(es) to create one."
                )
                return

        if self.timestamp_var.get() == "on":
            self._last_ts_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        else:
            self._last_ts_suffix = ""

        cmd = _build_command_from_values(
            search_text=search_text,
            folder=folder,
            and_mode=self.and_mode_var.get() == "on",
            recursive=self.recursive_var.get() == "on",
            fuzzy=self.fuzzy_var.get() == "on",
            wildcard=self.wildcard_var.get() == "on",
            ocr=self.ocr_var.get() == "on",
            regex=self.regex_var.get() == "on",
            exclude=self.exclude_entry.get(),
            file_types=self.file_types_entry.get(),
            proximity=self.proximity_entry.get(),
            context_before=self.context_before_entry.get(),
            context_after=self.context_after_entry.get(),
            cores=self.cores_entry.get(),
            specific_files=self.specific_files_entry.get(),
            append_name=self.append_name_entry.get(),
            output_docx=self.output_docx_var.get() == "on",
            output_csv=self.output_csv_var.get() == "on",
            output_json=self.output_json_var.get() == "on",
            output_pdf=self.output_pdf_var.get() == "on",
            output_html=self.output_html_var.get() == "on",
            index_search=self.index_search_var.get() == "on",
            inverse=self.inverse_var.get() == "on",
            expression=self.expression_var.get() == "on",
            whole_word=self.whole_word_var.get() == "on",
            max_matches=self.max_matches_entry.get(),
            max_file_size_mb=self.max_file_size_entry.get(),
            timestamp_suffix=self._last_ts_suffix,
            output_dir=self.output_dir_entry.get(),
            range_filters=self.range_entry.get(),
        )
        if cmd == "FLAGS_IN_SEARCH":
            self._show_error("Flags go in Advanced Search Options, not the search box.")
            return
        if cmd is None:
            # Debug: show what values were passed
            dbg = f"folder='{folder}' search='{search_text}' isdir={os.path.isdir(folder)}"
            self._show_error(f"Invalid input. Debug: {dbg}")
            return

        od = self.output_dir_entry.get().strip()
        self.results_dir = od if od else folder
        # Auto-redirect to a safe local folder if output dir is cloud-synced.
        from peekdocs.gui._helpers import check_cloud_folder, get_safe_output_dir
        self._cloud_redirected = False
        cloud_warning = check_cloud_folder(self.results_dir)
        if cloud_warning:
            safe_dir = get_safe_output_dir()
            self.results_dir = safe_dir
            self.output_dir_entry.delete(0, "end")
            self.output_dir_entry.insert(0, safe_dir)
            self._save_ui_preference("output_dir", safe_dir)
            self._cloud_redirected = True
        # Track all folders used this session for Delete on Close
        self._searched_folders.add(self.results_dir)
        self._searched_folders.add(folder)
        # Remove stale output files at search start so a search that errors
        # before writing fresh ones can't leave the previous good run's
        # results in place — which would let `_search_finished`'s
        # returncode == 2 recovery path parse last time's `.txt`/`.docx`
        # and display it as if it were this run's, causing the "Inverse
        # persists" and "no files without your search term" reports.
        # Skip when timestamping is on so each historical report is
        # preserved.
        if not self._last_ts_suffix:
            for fmt in ("txt", "docx"):
                stale = os.path.join(self.results_dir, f"peekdocs_standard_results.{fmt}")
                if os.path.exists(stale):
                    try:
                        os.remove(stale)
                    except OSError:
                        pass
            if self.output_csv_var.get() != "on":
                stale = os.path.join(self.results_dir, "peekdocs_standard_results.csv")
                if os.path.exists(stale):
                    os.remove(stale)
            if self.output_json_var.get() != "on":
                stale = os.path.join(self.results_dir, "peekdocs_standard_results.json")
                if os.path.exists(stale):
                    os.remove(stale)
            if self.output_pdf_var.get() != "on":
                stale = os.path.join(self.results_dir, "peekdocs_standard_results.pdf")
                if os.path.exists(stale):
                    os.remove(stale)
            if self.output_html_var.get() != "on":
                stale = os.path.join(self.results_dir, "peekdocs_standard_results.html")
                if os.path.exists(stale):
                    os.remove(stale)
        self.search_button.configure(text="Cancel", fg_color="#D32F2F", hover_color="#B71C1C")
        self.search_entry.configure(state="disabled")
        # Reset stateful fields that influence later rendering — if we don't,
        # a returncode == 1 branch (which never updated these before the
        # corresponding fix in _search_finished) could carry stale inverse
        # state and stale matched_files from a previous search.
        self._inverse_results = self.inverse_var.get() == "on"
        self.matched_files = []
        # Forget any combined regex left over from a previous Suite run —
        # otherwise the Matched Files popup for this Standard search would
        # pick the suite regex over the main search bar, highlighting the
        # wrong terms in opened files.
        self._suite_highlight_re = None
        self._clear_action_buttons()
        self._hide_files_list()
        self._hide_preview()
        self._matched_files_link.pack_forget()
        self._excluded_files_btn.pack_forget()
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        self.progress_bar.grid(
            row=5, column=0, columnspan=3, padx=10, pady=(2, 2), sticky="ew"
        )
        # Count search terms for status display
        import shlex as _shlex
        try:
            _term_count = len(_shlex.split(search_text))
        except ValueError:
            _term_count = len(search_text.split())
        _term_label = f"{_term_count} term{'s' if _term_count != 1 else ''}"
        # Build mode indicators for status display
        _modes = []
        if self.and_mode_var.get() == "on":
            _modes.append("AND")
        if hasattr(self, "expression_var") and self.expression_var.get() == "on":
            _modes.append("Expression")
        elif hasattr(self, "regex_var") and self.regex_var.get() == "on":
            _modes.append("Regex")
        elif hasattr(self, "fuzzy_var") and self.fuzzy_var.get() == "on":
            _modes.append("Fuzzy")
        elif hasattr(self, "wildcard_var") and self.wildcard_var.get() == "on":
            _modes.append("Wildcard")
        if self.whole_word_var.get() == "on":
            _modes.append("Whole Word")
        if hasattr(self, "inverse_var") and self.inverse_var.get() == "on":
            _modes.append("Inverse")
        if self.index_search_var.get() == "on":
            _modes.append("Index")
        _mode_str = f", {'+'.join(_modes)}" if _modes else ""
        _term_label += _mode_str

        # Pre-search status. Earlier code here probed the index meta for a
        # max_file_size_mb mismatch and showed "Rebuilding index with new
        # Max File Size, then searching..." — but since api.py was changed
        # to surface index_stale_notice instead of attempting a rebuild
        # (commit 6101c07), that pre-search message was a lie: nothing
        # rebuilds, and the mismatch usually has nothing to do with the
        # current session's settings (it's typically a long-standing
        # config-vs-meta delta the user never touched). The post-search
        # status line picks up the actual stale-notice condensed by
        # _parse_summary_text in _helpers.py, so the user still gets a
        # one-line notice in the right place without the false "Rebuilding"
        # claim.
        self.status_label.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("status_searching_format").format(terms=_term_label), text_color=("blue", "#66BBFF"))
        # Wipe last run's headline from the right pane while we start the new one.
        if hasattr(self, "_results_summary_label"):
            try:
                self._results_summary_label.configure(text="")
            except Exception:
                pass
        self.search_start_time = time.time()
        # Captured separately because search_start_time gets nulled at
        # finish; _show_action_buttons needs a stable cutoff to decide
        # whether a report file on disk was written by this run vs a
        # prior session.
        self._last_search_start_time = self.search_start_time
        # Reset the phase tracker — CLI subprocess will emit
        # 'PHASE: writing-txt' / 'writing-docx' / 'writing-csv' /
        # 'writing-json' / 'writing-pdf' / 'writing-html' markers on
        # stderr; _on_subprocess_stderr_line updates this string and
        # _update_elapsed reads it for the live status line.
        self._search_phase = "searching"
        self._start_elapsed_timer()

        # Reset the cancel flag for the new run — a prior cancelled run
        # would otherwise short-circuit the completion handler.
        self._search_cancelled = False

        self.search_thread = threading.Thread(
            target=self._run_search, args=(cmd, folder), daemon=True
        )
        self.search_thread.start()



    def _multi_folder_search(self, folders):
        """Run search across multiple folders sequentially and combine results."""
        search_text = self.search_entry.get().strip()
        range_text = self.range_entry.get().strip()
        if not search_text and not range_text:
            self._show_error("Please enter search terms or a range filter.")
            return

        self.status_label.configure(
            text=f"Searching {len(folders)} folder(s)...", text_color=("blue", "#66BBFF"))
        self.progress_bar.grid(
            row=5, column=0, columnspan=3, padx=10, pady=(2, 2), sticky="ew")
        self.progress_bar.start()
        self.search_button.configure(text="Cancel", fg_color="#D32F2F", hover_color="#B71C1C")
        self.search_entry.configure(state="disabled")

        self._multi_folder_cancelled = False
        # Track all folders for Delete on Close cleanup
        for f in folders:
            self._searched_folders.add(f)
        import threading
        t = threading.Thread(
            target=self._multi_folder_thread,
            args=(folders, search_text), daemon=True)
        self.search_thread = t  # Allow cancel via search button
        t.start()



    def _multi_folder_thread(self, folders, search_text):
        """Worker thread: search each folder and combine output."""
        import re as _re_mf
        import time
        combined_stdout = []
        all_matched_files = []  # (filepath, filename, count, line_nums)
        total_matches = 0
        total_files = 0
        failed_folders = []
        start_time = time.time()
        output_dir = self.output_dir_entry.get().strip() or folders[0]

        for i, folder in enumerate(folders):
            if self._multi_folder_cancelled:
                combined_stdout.append(f"\n── Search cancelled after {i} of {len(folders)} folder(s) ──")
                break

            self.after(0, lambda i=i, f=folder: self.status_label.configure(
                text=f"Searching folder {i+1}/{len(folders)}: {os.path.basename(f)}...",
                text_color=("blue", "#66BBFF")))

            cmd = _build_command_from_values(
                search_text=search_text,
                folder=folder,
                and_mode=self.and_mode_var.get() == "on",
                recursive=self.recursive_var.get() == "on",
                fuzzy=self.fuzzy_var.get() == "on",
                wildcard=self.wildcard_var.get() == "on",
                ocr=self.ocr_var.get() == "on",
                regex=self.regex_var.get() == "on",
                exclude=self.exclude_entry.get(),
                file_types=self.file_types_entry.get(),
                proximity=self.proximity_entry.get(),
                context_before=self.context_before_entry.get(),
                context_after=self.context_after_entry.get(),
                cores=self.cores_entry.get(),
                specific_files=self.specific_files_entry.get(),
                output_docx=False,  # Skip per-folder extras
                output_csv=False,
                output_json=False,
                output_pdf=False,
                output_html=False,
                index_search=self.index_search_var.get() == "on",
                inverse=self.inverse_var.get() == "on",
                expression=self.expression_var.get() == "on",
                whole_word=self.whole_word_var.get() == "on",
                max_matches=self.max_matches_entry.get(),
                max_file_size_mb=self.max_file_size_entry.get(),
                range_filters=self.range_entry.get(),
            )
            if cmd is None or cmd == "FLAGS_IN_SEARCH":
                continue

            try:
                from peekdocs.gui._helpers import _run_peekdocs_cli
                stdout, stderr, _returncode = _run_peekdocs_cli(cmd, folder)
                if stdout:
                    combined_stdout.append(f"── {folder} ──")
                    combined_stdout.append(stdout)
                    _clean = _re_mf.sub(r"\033\[[0-9;]*m", "", stdout)
                    m = _re_mf.search(r"Found\s+(\d+)\s+match", _clean)
                    if m:
                        total_matches += int(m.group(1))
                    f = _re_mf.search(r"Files searched:\s*(\d+)", _clean)
                    if f:
                        total_files += int(f.group(1))

                # Collect matched files from this folder's results
                is_inverse = self.inverse_var.get() == "on"
                results_txt = os.path.join(folder, "peekdocs_standard_results.txt")
                if os.path.exists(results_txt):
                    if is_inverse:
                        folder_matches = _parse_inverse_files(folder, "peekdocs_standard_results.txt")
                    else:
                        folder_matches = _parse_matched_files(folder, "peekdocs_standard_results.txt")
                    all_matched_files.extend(folder_matches)
            except Exception as e:
                failed_folders.append((folder, str(e)))
                combined_stdout.append(f"── {folder} — ERROR: {e} ──")

        elapsed = time.time() - start_time

        # Read all per-folder results BEFORE writing the combined file
        # (output_dir may be folders[0], so writing first would overwrite it)
        folder_contents = []
        for folder in folders:
            txt = os.path.join(folder, "peekdocs_standard_results.txt")
            if os.path.exists(txt):
                try:
                    with open(txt, "r", encoding="utf-8", errors="replace") as src:
                        folder_contents.append((folder, src.read()))
                except Exception:
                    pass

        # Write combined results.txt to output_dir
        try:
            combined_txt_path = os.path.join(output_dir, "peekdocs_standard_results.txt")
            with open(combined_txt_path, "w", encoding="utf-8") as out:
                out.write(f"Multi-folder search: {len(folders)} folder(s)\n")
                out.write(f"Search terms: {search_text}\n")
                out.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                out.write(f"Total matches: {total_matches}, Files searched: {total_files}\n\n")
                for folder, content in folder_contents:
                    out.write(f"\n{'=' * 60}\n")
                    out.write(f"Folder: {folder}\n")
                    out.write(f"{'=' * 60}\n\n")
                    out.write(content)
                    out.write("\n")
        except Exception:
            pass

        # Build synthetic summary for _parse_summary_text
        combined = "\n".join(combined_stdout)
        summary = (f"Files searched: {total_files}\n"
                   f"Found {total_matches} match(es).\n"
                   f"Elapsed time: {elapsed:.2f} seconds\n")
        combined = combined + "\n" + summary

        self.after(0, self._multi_folder_finished, combined, total_matches,
                   total_files, elapsed, len(folders), len(failed_folders),
                   all_matched_files, output_dir)

    def _multi_folder_finished(self, combined_stdout, total_matches, total_files,
                               elapsed, folder_count, fail_count,
                               all_matched_files, output_dir):
        """Handle multi-folder search completion."""
        try:
            self.progress_bar.stop()
        except Exception:
            pass
        self.progress_bar.grid_remove()
        self.search_button.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("run_standard_search_label"), fg_color="#2196F3", hover_color="#1976D2", text_color="white")
        self.search_entry.configure(state="normal")
        self.process = None
        self._multi_folder_cancelled = None  # Reset for next search

        # Log to search history
        try:
            search_text = self.search_entry.get().strip()
            if search_text:
                self._log_search_history(search_text, total_matches, total_files, f"{elapsed:.2f}")
        except Exception:
            pass

        # Set results directory for report opening
        self.results_dir = output_dir

        # Results summary — goes to the right-pane headline; the left
        # status_label just reports completion.
        status = (f"{total_files} file(s) searched across {folder_count} folder(s) "
                  f"— Found {total_matches} match(es) in {elapsed:.1f}s")
        if fail_count:
            status += f"  ({fail_count} folder(s) failed — see preview)"
        self._report_search_result(status)

        # Populate matched files popup
        self._inverse_results = self.inverse_var.get() == "on"
        self.matched_files = all_matched_files
        self._show_action_buttons(inverse=self._inverse_results)

        # Show matched files link
        if self.matched_files:
            if self._inverse_results:
                link_text = __import__("peekdocs.i18n", fromlist=["t"]).t("files_without_matches_format").format(n=len(self.matched_files))
                self._matched_files_link.configure(text=link_text, fg_color="#CC3333", hover_color="#AA2222")
            else:
                link_text = __import__("peekdocs.i18n", fromlist=["t"]).t("matched_files_format").format(n=len(self.matched_files))
                self._matched_files_link.configure(text=link_text, fg_color="#FF6B35", hover_color="#E55A2B")
            self._matched_files_link.pack(side="left", padx=(5, 0))

        self._show_preview(combined_stdout)



    def _start_elapsed_timer(self):
        """Start the repeating timer that updates the elapsed-time display."""
        self._update_elapsed()



    # Maps CLI-emitted 'PHASE: <token>' markers to user-facing status
    # verbs. Tokens come from peekdocs/cli.py before each report-write
    # call. Anything not in the map falls back to 'Searching'.
    _PHASE_LABELS = {
        "searching":    "Searching",
        "writing-txt":  "Writing TXT report",
        "writing-docx": "Writing DOCX report",
        "writing-csv":  "Writing CSV report",
        "writing-json": "Writing JSON report",
        "writing-pdf":  "Writing PDF report",
        "writing-html": "Writing HTML report",
    }

    def _on_subprocess_stderr_line(self, line: str):
        """Handle one line of subprocess stderr — pluck PHASE markers.

        Called from a background thread by _run_peekdocs_cli's stderr
        reader. Updates self._search_phase (atomic string assignment;
        the elapsed-timer reads it from the main thread) and also
        schedules an immediate _update_elapsed via self.after(0, ...)
        so fast phases (CSV at tens of milliseconds, JSON / PDF / HTML
        at fractions of a second) are visible in the status line.
        Without the immediate refresh, the 1-second elapsed-timer tick
        would miss any phase that completed within the same second.
        Other stderr content (the 'Scanning files...' hint, warnings,
        errors) is captured by the helper into stderr for the existing
        post-search handling — we don't intercept it.
        """
        if not line.startswith("PHASE: "):
            return
        token = line[len("PHASE: "):].strip()
        if token in self._PHASE_LABELS:
            self._search_phase = token
            try:
                self.after(0, self._render_phase_status)
            except Exception:
                pass

    def _render_phase_status(self):
        """Compute + render the phase + elapsed status line.

        Pure rendering — no timer scheduling. Called by _update_elapsed
        on the recurring tick AND by _on_subprocess_stderr_line via
        self.after(0, ...) the moment a PHASE marker arrives, so fast
        phases that complete inside one timer interval still flash
        their label.
        """
        if self.search_start_time is None:
            return
        elapsed = time.time() - self.search_start_time
        dots = "." * (int(elapsed) % 4)
        phase = getattr(self, "_search_phase", "searching")
        verb = self._PHASE_LABELS.get(phase, "Searching")
        self.status_label.configure(
            text=f"{verb}{dots.ljust(3)}  ({elapsed:.0f}s elapsed)",
            text_color=("blue", "#66BBFF"),
        )

    def _update_elapsed(self):
        """Recurring tick — render the status and reschedule.

        Phase comes from CLI 'PHASE: <token>' markers parsed by
        _on_subprocess_stderr_line. Reports running long (DOCX with
        tens of thousands of matches can take a minute) show
        'Writing DOCX report... (Ns elapsed)' instead of stale
        'Searching...'.
        """
        if self.process is None and self.search_start_time is None:
            return
        self._render_phase_status()
        self.elapsed_timer_id = self.after(1000, self._update_elapsed)



    def _run_search(self, cmd, folder):
        """Run the peekdocs CLI in a background thread and post results.

        Uses subprocess in normal pip / pipx installs and in-process
        execution in PyInstaller-bundled standalone exes. See
        peekdocs.gui._helpers._run_peekdocs_cli for the why.
        """
        import re as _re
        from peekdocs.gui._helpers import _run_peekdocs_cli
        try:
            # Hand the live Popen object to self.process so the Cancel
            # branch in start_search() can terminate the running search.
            # In-process (PyInstaller) mode never invokes the callback —
            # there's no subprocess to expose — so self.process stays
            # None there and Cancel is a no-op for the duration. That's
            # called out in _run_peekdocs_cli's docstring.
            self.process = None
            def _capture_process(proc):
                self.process = proc
            stdout, stderr, returncode = _run_peekdocs_cli(
                cmd, folder,
                on_process_started=_capture_process,
                on_stderr_line=self._on_subprocess_stderr_line,
            )
            # Include stderr in output if stdout is empty
            if not stdout.strip() and stderr.strip():
                stdout = stderr
        except Exception as e:
            stdout = str(e)
            returncode = -1
        finally:
            self.process = None

        self.after(0, self._search_finished, stdout, returncode, stderr)



    def _search_finished(self, stdout, returncode, stderr=""):
        """Handle search completion by updating status, reports, and preview."""
        try:
            self.progress_bar.stop()
        except Exception:
            pass
        self.progress_bar.grid_remove()
        self.search_start_time = None
        if self.elapsed_timer_id:
            self.after_cancel(self.elapsed_timer_id)
            self.elapsed_timer_id = None

        self.search_button.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("run_standard_search_label"), fg_color="#2196F3", hover_color="#1976D2", text_color="white")
        self.search_entry.configure(state="normal")

        # User-cancelled run: short-circuit the returncode dispatch.
        # SIGTERM returncode is platform-dependent (-15 on Unix, 1 on
        # Windows) and the Windows code collides with peekdocs's "no
        # matches" exit code — without this check, a Windows cancel
        # would silently show "Search complete. No matches found." or
        # an error popup with the half-written CLI banner stdout.
        if getattr(self, "_search_cancelled", False):
            self._search_cancelled = False
            self.status_label.configure(
                text="Search was cancelled.", text_color=("blue", "#66BBFF"),
            )
            self._reschedule_refresh()
            return

        if returncode == -1:
            self._show_error("Search process failed to start.")
            return

        summary = _parse_summary_text(stdout)

        # Log to search history
        try:
            import re as _re_hist
            _clean = _re_hist.sub(r"\033\[[0-9;]*m", "", stdout or "")
            _h_matches = _re_hist.search(r"Found\s+(\d+)\s+match", _clean)
            _h_files = _re_hist.search(r"Files searched:\s*(\d+)", _clean)
            _h_elapsed = _re_hist.search(r"Elapsed time:\s*([\d.]+)", _clean)
            _h_search = self.search_entry.get().strip()
            if _h_search:
                self._log_search_history(
                    _h_search,
                    int(_h_matches.group(1)) if _h_matches else 0,
                    int(_h_files.group(1)) if _h_files else 0,
                    _h_elapsed.group(1) if _h_elapsed else "",
                )
        except Exception:
            pass

        # Check if any files were skipped (appears in subprocess output)
        import re as _re_fin
        _skip_match = _re_fin.search(r"Errors logged to peekdocs_errors\.log \((\d+) error", stdout or "")
        _skip_count = int(_skip_match.group(1)) if _skip_match else 0

        # Compute excluded files list (unsupported types, peekdocs outputs, etc.)
        folder = self.folder_entry.get().strip()
        recursive = self.recursive_var.get() == "on"
        try:
            self._excluded_files = self._compute_excluded_files(folder, recursive=recursive)
        except Exception:
            self._excluded_files = []
        _excl_count = len(self._excluded_files)
        if _excl_count > 0:
            self._excluded_files_btn.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("excluded_files_format").format(n=_excl_count))
            self._excluded_files_btn.pack(side="left", padx=(5, 0))
        else:
            self._excluded_files_btn.pack_forget()

        # Notify user if the search index was corrupt and rebuilt
        if stderr and "corrupted" in stderr.lower():
            from tkinter import messagebox
            messagebox.showwarning(
                "Index Corrupted",
                "The search index was corrupted and has been removed. "
                "This search ran without the index.\n\n"
                "To rebuild, go to Manage Indexes and click Build Index.",
                parent=self,
            )

        if returncode == 0:
            status_text = summary or "Search complete. Matches found."
            specific = self.specific_files_entry.get().strip()
            if specific:
                status_text += f"  [{specific}]"
            if _skip_count:
                status_text += f"  ({_skip_count} file(s) skipped — see Error Log)"
            if getattr(self, "_cloud_redirected", False):
                status_text += f"  Reports saved to {self.results_dir} (cloud folder detected)"
            self._report_search_result(status_text)
            # Post-search save (-s) if user filled in "Save as" field.
            # Uses the same subprocess-or-in-process helper as the main
            # search so the standalone bundled exe doesn't spawn a
            # duplicate GUI window during the save step.
            save_name = self.save_name_entry.get().strip()
            if save_name:
                save_cmd = [sys.executable, "-m", "peekdocs", "-s", save_name]
                try:
                    from peekdocs.gui._helpers import _run_peekdocs_cli
                    save_stdout, save_stderr, save_rc = _run_peekdocs_cli(save_cmd, self.results_dir)
                    if save_rc != 0:
                        self._show_error(f"Save failed: {save_stdout.strip() or save_stderr.strip() or 'unknown error'}")
                        return
                except Exception as e:
                    self._show_error(f"Save failed: {e}")
                    return
            # Populate file list for the popup button
            ts = getattr(self, '_last_ts_suffix', '')
            results_fn = f"peekdocs_standard_results_{ts}.txt" if ts else "peekdocs_standard_results.txt"
            self._inverse_results = self.inverse_var.get() == "on"
            if self._inverse_results:
                self.matched_files = _parse_inverse_files(self.results_dir, results_fn)
            else:
                self.matched_files = _parse_matched_files(self.results_dir, results_fn)
            self._show_action_buttons(inverse=self._inverse_results)
            self._show_preview(stdout)
            # Show matched files link on status line
            if self.matched_files:
                if self._inverse_results:
                    link_text = __import__("peekdocs.i18n", fromlist=["t"]).t("files_without_matches_format").format(n=len(self.matched_files))
                    self._matched_files_link.configure(text=link_text, fg_color="#CC3333", hover_color="#AA2222")
                else:
                    link_text = __import__("peekdocs.i18n", fromlist=["t"]).t("matched_files_format").format(n=len(self.matched_files))
                    self._matched_files_link.configure(text=link_text, fg_color="#FF6B35", hover_color="#E55A2B")
                self._matched_files_link.pack(side="left", padx=(5, 0))
        elif returncode == 1:
            # Refresh state from the current checkbox AND clear matched_files
            # so stale values from a previous search can't leak into this
            # branch's status, link, or any later code that reads them.
            self._inverse_results = self.inverse_var.get() == "on"
            self.matched_files = []

            no_match_text = summary or "Search complete. No matches found."
            specific = self.specific_files_entry.get().strip()
            if specific:
                no_match_text += f"  [{specific}]"
            if _skip_count:
                no_match_text += f"  ({_skip_count} file(s) skipped — see Error Log)"
            self._report_search_result(no_match_text, status_text="No matches found.")
            # Link color differs by inverse state: red is reserved for the
            # "files without matches" inverse style, orange is the normal
            # "matched files" style. Using red for non-inverse zero-match
            # runs made it look like Inverse was still on.
            if self._inverse_results:
                link_text = __import__("peekdocs.i18n", fromlist=["t"]).t("files_without_matches_format").format(n=0)
                link_fg, link_hover = "#CC3333", "#AA2222"
            else:
                link_text = __import__("peekdocs.i18n", fromlist=["t"]).t("matched_files_format").format(n=0)
                link_fg, link_hover = "#FF6B35", "#E55A2B"
            self._matched_files_link.configure(
                text=link_text, fg_color=link_fg, hover_color=link_hover,
            )
            self._matched_files_link.pack(side="left", padx=(5, 0))
            self._show_action_buttons(inverse=self._inverse_results)
        elif returncode == 2:
            # Check if results were produced despite the error (e.g., .docx generation failed)
            ts = getattr(self, '_last_ts_suffix', '')
            results_fn = f"peekdocs_standard_results_{ts}.txt" if ts else "peekdocs_standard_results.txt"
            results_path = os.path.join(self.results_dir or folder, results_fn)
            if os.path.exists(results_path):
                # Search succeeded but something else failed (likely report generation)
                self._report_search_result(
                    summary or "Search complete (with warnings — check error log).",
                    status_text="Search complete (with warnings).",
                )
                self._inverse_results = self.inverse_var.get() == "on"
                if self._inverse_results:
                    self.matched_files = _parse_inverse_files(self.results_dir or folder, results_fn)
                else:
                    self.matched_files = _parse_matched_files(self.results_dir or folder, results_fn)
                self._show_action_buttons(inverse=self._inverse_results)
                self._show_preview(stdout)
            else:
                error_msg = stdout.strip() if stdout.strip() else "Search failed (exit code 2). No output captured."
                self._show_error(error_msg)
                self._show_action_buttons()
        else:
            self.status_label.configure(
                text="Search was cancelled.", text_color=("blue", "#66BBFF"),
            )

        # Resume auto-refresh schedule if active
        self._reschedule_refresh()

        # Suggest indexing for large folders without an index
        if returncode in (0, 1) and self.index_search_var.get() != "on":
            _files_match = _re_fin.search(r"Files searched:\s*(\d+)", stdout or "")
            if _files_match:
                _file_count = int(_files_match.group(1))
                if _file_count >= 100:
                    from peekdocs.indexer import index_exists
                    if not index_exists(folder):
                        current = self.status_label.cget("text")
                        self.status_label.configure(
                            text=current + "  |  Tip: Build an index for faster searches — click Manage Indexes",
                        )

        # Desktop notification (opt-in, focus-suppressed). Reads the
        # final status text so the notification body matches exactly
        # what the user would see if they switched back to the GUI.
        self._fire_completion_notification(
            "peekdocs — Standard Search complete",
            self.status_label.cget("text") or "Search complete.",
        )



    def _fire_completion_notification(self, title, body):
        """Fire a desktop notification when a search finishes.

        No-op when ``Notify on Search Complete`` is unchecked, or when
        the peekdocs window is the foreground OS-level app (the user
        can already see the result; no need to interrupt). Failures
        are swallowed — desktop notifications are nice-to-have polish,
        not load-bearing functionality.

        Focus detection uses `self._gui_has_focus`, a flag maintained
        by `<FocusIn>` / `<FocusOut>` root-toplevel handlers in
        `_app.py`. The original implementation tried Tk's
        `focus_displayof()` and failed on macOS: that API is
        per-application, not per-OS-foreground, so it kept reporting
        our toplevel as focused even after the user clicked away to
        another app. The event-driven flag tracks the actual OS-level
        transition."""
        try:
            if getattr(self, "notify_on_complete_var", None) is None:
                return
            if self.notify_on_complete_var.get() != "on":
                return
            # Default True so a notification doesn't fire when we
            # genuinely don't know (e.g. very early startup before the
            # first FocusOut has been observed). Once macOS hands us
            # FocusOut, the flag goes False and stays False until the
            # user comes back.
            if getattr(self, "_gui_has_focus", True):
                return
            from peekdocs.notifier import desktop_notify
            desktop_notify(title, body)
        except Exception:
            pass

    def _show_preview(self, stdout):
        """Populate the results preview pane from search output."""
        import re as _re
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")

        # If inverse search, always show inverse-style output \u2014 never fall
        # through to highlighted-match rendering even when matched_files is
        # empty. Previously the condition was `if self._inverse_results and
        # self.matched_files:` which meant an inverse run with zero
        # results-file entries (whatever the cause \u2014 CLI didn't write the
        # "Files WITHOUT matches:" header, parse failure, etc.) would fall
        # through to the normal block below and show yellow-highlighted
        # matches parsed from stdout \u2014 exactly the inconsistent state users
        # have reported. Render inverse-style output unconditionally when
        # _inverse_results is set.
        if self._inverse_results:
            self.preview_text.tag_configure("inverse_header",
                font=("TkDefaultFont", 12, "bold"), foreground="#FF6B35")
            self.preview_text.tag_configure("inverse_file",
                font=("TkDefaultFont", 11))
            if self.matched_files:
                self.preview_text.insert("end",
                    f"Files WITHOUT your search term ({len(self.matched_files)} file(s)) \u2014 Inverse box checked:\n\n",
                    "inverse_header")
                for item in self.matched_files:
                    filepath, filename = item[0], item[1]
                    dirname = os.path.dirname(filepath)
                    self.preview_text.insert("end", f"  {filename}\n", "inverse_file")
                    self.preview_text.insert("end", f"  ({dirname})\n\n", "inverse_file")
            else:
                self.preview_text.insert("end",
                    "No files without your search term \u2014 every file in the search "
                    "contains a match. (Inverse box is checked; uncheck it to see "
                    "the matches.)\n",
                    "inverse_header")
            self.preview_text.configure(state="disabled")
            self.preview_text.see("1.0")
            self.preview_frame.pack(fill="both", expand=True, padx=0, pady=0)
            return

        # Build highlight pattern from current search settings
        highlight_pattern = None
        search_text = self.search_entry.get().strip()
        use_regex = self.regex_var.get() == "on"
        use_wildcard = self.wildcard_var.get() == "on"
        use_whole_word = self.whole_word_var.get() == "on"
        use_fuzzy = self.fuzzy_var.get() == "on"
        is_expression = self.expression_var.get() == "on"

        if search_text and use_fuzzy:
            # For fuzzy, build patterns that match approximate words
            from rapidfuzz import fuzz
            import shlex as _shlex_fz
            try:
                _fuzzy_terms = _shlex_fz.split(search_text)
            except ValueError:
                _fuzzy_terms = search_text.split()
            _fuzzy_highlight = True
        else:
            _fuzzy_highlight = False

        if search_text and not use_fuzzy:
            patterns = []
            if is_expression:
                from peekdocs.expr_parser import parse_expression, extract_positive_terms
                terms = extract_positive_terms(parse_expression(search_text))
            elif use_regex:
                # Regex mode: use the raw search text as-is (shlex strips backslashes)
                terms = [search_text]
            else:
                # Use shlex.split to respect quoted phrases (e.g., "insecure core")
                import shlex as _shlex_hl
                try:
                    terms = _shlex_hl.split(search_text)
                except ValueError:
                    terms = search_text.split()
            for term in terms:
                if use_wildcard:
                    from peekdocs.scanner import _wildcard_to_regex
                    patterns.append(_wildcard_to_regex(term))
                elif use_regex:
                    patterns.append(term)
                elif use_whole_word:
                    _pfx = r'\b' if _re.match(r'\w', term) else ''
                    _sfx = r'\b' if _re.search(r'\w$', term) else ''
                    patterns.append(_pfx + _re.escape(term) + _sfx)
                else:
                    patterns.append(_re.escape(term))
            if patterns:
                try:
                    highlight_pattern = _re.compile("|".join(patterns), _re.IGNORECASE)
                except _re.error:
                    highlight_pattern = None

        def _insert_highlighted(line):
            """Insert a line with yellow highlighting on matched terms."""
            if highlight_pattern:
                last_end = 0
                for m in highlight_pattern.finditer(line):
                    if m.start() > last_end:
                        self.preview_text.insert("end", line[last_end:m.start()])
                    self.preview_text.insert("end", m.group(), "match")
                    last_end = m.end()
                if last_end < len(line):
                    self.preview_text.insert("end", line[last_end:])
            elif _fuzzy_highlight:
                # Highlight words that fuzzy-match the search terms
                import re as _re_fz
                from peekdocs.constants import FUZZY_THRESHOLD
                words = _re_fz.split(r'(\s+)', line)
                for word in words:
                    if word.strip() and any(
                        fuzz.ratio(term.lower(), word.lower()) >= FUZZY_THRESHOLD
                        for term in _fuzzy_terms
                    ):
                        self.preview_text.insert("end", word, "match")
                    else:
                        self.preview_text.insert("end", word)
            else:
                self.preview_text.insert("end", line)
            self.preview_text.insert("end", "\n")

        # Parse the results file for cleaner output
        results_path = None
        if self.results_dir:
            suffix = f"_{self._last_ts_suffix}" if getattr(self, '_last_ts_suffix', '') else ""
            results_path = os.path.join(self.results_dir, f"peekdocs_standard_results{suffix}.txt")

        # Preview cap — browser-GUI convention. Reads the user-chosen
        # value from the dropdown in the preview header. "No cap" means
        # render everything; a numeric value caps on MATCHES (not lines).
        _cap_raw = getattr(self, "_preview_cap_var", None)
        _cap_str = _cap_raw.get() if _cap_raw is not None else "500"
        try:
            preview_cap_matches = int(_cap_str)
        except ValueError:
            preview_cap_matches = 0  # "No cap"
        lines_added = 0
        matches_rendered = 0

        if results_path and os.path.exists(results_path):
            in_results = False
            in_match_text = False
            with open(results_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if line == "Results:":
                        in_results = True
                        continue
                    if not in_results:
                        continue
                    if preview_cap_matches and matches_rendered >= preview_cap_matches:
                        break
                    if line.startswith("Document:"):
                        in_match_text = False
                        self.preview_text.insert("end", "\n")
                        # Strip the leading "Document: " prefix from the
                        # rendered line. The prefix stays in the on-disk
                        # .txt report (PDF, Matched Files popup, heatmap
                        # all parse it) — only the preview pane drops it
                        # since the user knows everything here is a file.
                        display = line[len("Document: "):] if line.startswith("Document: ") else line
                        self.preview_text.insert("end", display + "\n", "filename")
                    elif line.startswith("(") and not in_match_text:
                        self.preview_text.insert("end", line + "\n", "line_num")
                    elif line.startswith("Files WITHOUT matches:"):
                        self.preview_text.insert("end", line + "\n", "filename")
                    elif line.startswith('"') or in_match_text:
                        # Match text block — may span multiple wrapped lines
                        in_match_text = True
                        # Strip leading/trailing quotes
                        display = line
                        if display.startswith('"'):
                            display = display[1:]
                            # The opening quote marks the start of a new match.
                            matches_rendered += 1
                        if display.endswith('"'):
                            display = display[:-1]
                            in_match_text = False
                        _insert_highlighted(display)
                    elif line == "---":
                        self.preview_text.insert("end", "---\n")
                    elif line.strip() == "":
                        if not in_match_text:
                            continue  # Skip blank lines between matches
                    else:
                        _insert_highlighted(line)
                    lines_added += 1

        if lines_added == 0:
            self.preview_text.insert("end", "(No results to preview)")

        # Remember the results file so cap changes can re-render in place.
        self._last_preview_results_path = results_path

        self.preview_text.configure(state="disabled")
        self.preview_text.see("1.0")

        # Counts moved to the right-pane headline; no inline count label
        # to update. Cap-status text still drives the line above the
        # text widget.
        match_count = len(self.matched_files)
        if self._inverse_results:
            self._preview_cap_status.configure(text="")
        else:
            total_matches = sum(item[2] for item in self.matched_files)
            self._update_preview_cap_status(matches_rendered, total_matches, preview_cap_matches)

        # Show the preview frame (lives in the right pane of the split)
        self.preview_frame.pack(fill="both", expand=True, padx=0, pady=0)



    def _hide_preview(self):
        """Hide the results preview pane and clear its text.

        Previously this only grid-removed the frame, which left whatever was
        last rendered (e.g., yellow-highlighted matches from a prior search)
        in the Text widget. Branches that re-showed the frame without first
        calling _show_preview (notably the `returncode == 1` "no matches"
        path) then displayed stale match content alongside a "no matches"
        status — the inconsistent state users have reported. Clearing the
        text here guarantees the preview is empty whenever it's been hidden.
        """
        self.preview_frame.pack_forget()
        try:
            self.preview_text.configure(state="normal")
            self.preview_text.delete("1.0", "end")
            self.preview_text.configure(state="disabled")
        except Exception:
            pass

    def _update_preview_cap_status(self, matches_rendered, total_matches, cap):
        """Render the browser-GUI-style status line above the preview
        text — "All N matches rendered…" or "Preview shows the first
        M of N matches…" depending on whether the cap kicked in."""
        # (Internal note: snapshot/apply helpers for Recent Searches
        #  are defined just below this method — see _snapshot_search_config.)
        if not hasattr(self, "_preview_cap_status"):
            return
        capped = bool(cap) and matches_rendered >= cap and total_matches > matches_rendered
        if capped:
            text = (
                f"Preview shows the first {matches_rendered:,} of {total_matches:,} matches. "
                "The cap keeps the GUI responsive on big result sets — the full data is always "
                "in the DOCX / TXT / CSV / JSON / HTML reports next to your documents. "
                "To render more, raise the cap →"
            )
        else:
            text = (
                f"All {total_matches:,} matches rendered below. The cap (used when results exceed it) "
                "keeps the GUI responsive on very large result sets. Adjust using Preview cap →"
            )
        self._preview_cap_status.configure(text=text)

    # ── Recent-search config snapshot / restore helpers ──────────────
    # Field map: (attribute name on self, key inside the recent-search
    # dict). _ENTRY_FIELDS are CTkEntry widgets (use .get()/.delete()/
    # .insert()); _VAR_FIELDS are StringVars (use .get()/.set()).
    _RECENT_ENTRY_FIELDS = (
        ("search_entry",          "terms"),
        ("folder_entry",          "folder"),
        ("exclude_entry",         "exclude"),
        ("file_types_entry",      "file_types"),
        ("proximity_entry",       "proximity"),
        ("context_before_entry",  "context_before"),
        ("context_after_entry",   "context_after"),
        ("cores_entry",           "cores"),
        ("max_matches_entry",     "max_matches"),
        ("max_file_size_entry",   "max_file_size"),
        ("range_entry",           "range"),
        ("specific_files_entry",  "specific_files"),
        ("output_dir_entry",      "output_dir"),
    )
    _RECENT_VAR_FIELDS = (
        ("and_mode_var",            "and_mode"),
        ("recursive_var",           "recursive"),
        ("whole_word_var",          "whole_word"),
        ("index_search_var",        "index_search"),
        ("fuzzy_var",               "fuzzy"),
        ("wildcard_var",            "wildcard"),
        ("ocr_var",                 "ocr"),
        ("regex_var",               "regex"),
        ("expression_var",          "expression"),
        ("inverse_var",             "inverse"),
        ("output_docx_var",         "output_docx"),
        ("output_csv_var",          "output_csv"),
        ("output_json_var",         "output_json"),
        ("output_pdf_var",          "output_pdf"),
        ("output_html_var",         "output_html"),
        ("timestamp_var",           "timestamp"),
        ("delete_reports_var",      "delete_reports"),
        ("clear_history_var",       "clear_history"),
        ("restrict_permissions_var","restrict_permissions"),
        ("notify_on_complete_var",  "notify_on_complete"),
    )

    @staticmethod
    def _recent_entry_terms(entry):
        """Return the search-terms string for a Recent Searches entry.
        Accepts both the new dict format and the legacy plain-string
        format that may still be sitting in older ~/.peekdocsrc files."""
        if isinstance(entry, str):
            return entry
        if isinstance(entry, dict):
            return entry.get("terms", "")
        return ""

    def _snapshot_search_config(self):
        """Capture the full search configuration (search bar + folder +
        every Advanced Search Options field) as a dict, for storage in
        Recent Searches."""
        snap = {}
        for attr, key in self._RECENT_ENTRY_FIELDS:
            w = getattr(self, attr, None)
            if w is not None:
                try:
                    snap[key] = w.get()
                except Exception:
                    pass
        for attr, key in self._RECENT_VAR_FIELDS:
            v = getattr(self, attr, None)
            if v is not None:
                try:
                    snap[key] = v.get()
                except Exception:
                    pass
        return snap

    def _apply_search_config(self, cfg):
        """Restore a search configuration from a dict produced by
        _snapshot_search_config (or from a legacy plain-string entry,
        in which case only the search terms are filled). Missing keys
        leave the existing widget value in place."""
        if isinstance(cfg, str):
            cfg = {"terms": cfg}
        if not isinstance(cfg, dict):
            return
        for attr, key in self._RECENT_ENTRY_FIELDS:
            if key in cfg:
                w = getattr(self, attr, None)
                if w is not None:
                    try:
                        w.delete(0, "end")
                        if cfg[key]:
                            w.insert(0, cfg[key])
                    except Exception:
                        pass
        for attr, key in self._RECENT_VAR_FIELDS:
            if key in cfg:
                v = getattr(self, attr, None)
                if v is not None:
                    try:
                        v.set(cfg[key])
                    except Exception:
                        pass

    def _on_preview_cap_changed(self, value):
        """Persist the cap selection and re-render the current preview
        in place (browser-GUI behaviour)."""
        self._save_ui_preference("preview_cap", value)
        path = getattr(self, "_last_preview_results_path", None)
        if path and os.path.exists(path):
            self._show_preview("")

    def _report_search_result(self, results_text, status_text="Search complete."):
        """Route the search-result summary to the right pane's headline
        label and set a short status string on the left status_label.
        Used by every search-completion path so the right pane carries
        the numbers and the left pane keeps narrating progress."""
        if hasattr(self, "_results_summary_label"):
            try:
                self._results_summary_label.configure(text=results_text)
            except Exception:
                pass
        try:
            self.status_label.configure(text=status_text, text_color=("blue", "#66BBFF"))
        except Exception:
            pass

    def _open_chart_window(self, title, plot_fn, *, geometry="760x500",
                           figsize=(7.4, 4.6), parent=None, scrollable=False):
        """Generic chart popup: themed Toplevel + matplotlib canvas +
        Close button, with figure-cleanup on close. Shared by every
        chart entry point in the GUI.

        plot_fn receives a matplotlib Axes and draws on it. Returns
        the Toplevel (or None if matplotlib failed to import).

        matplotlib is imported lazily so the ~300 ms first-import cost
        is paid only when a user actually clicks a chart button."""
        try:
            import matplotlib
            matplotlib.use("TkAgg")
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        except Exception as e:
            self._show_error(
                f"matplotlib not available — install it with `pip install matplotlib`.\n\n{e}"
            )
            return None

        chart_win, _dark = self._themed_toplevel(parent or self)
        chart_win.title(title)
        chart_win.geometry(geometry)
        chart_win.resizable(True, True)
        try:
            chart_win.transient(parent or self)
        except Exception:
            pass

        fig, ax = plt.subplots(figsize=figsize, dpi=100)
        try:
            plot_fn(ax)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._show_error(f"Chart render failed: {e}")
            plt.close(fig)
            chart_win.destroy()
            return None
        fig.tight_layout()

        if scrollable:
            # Vertical-scroll wrapper. Used by charts whose Y-axis label
            # count can be large (e.g. matches-by-file-type with 40+
            # extensions) — without this the bars get crushed together
            # and the labels overlap. We fix the rendered figure height
            # to figsize[1] inches × 100 dpi and scroll within a smaller
            # window.
            import tkinter as _tk_scroll
            outer = _tk_scroll.Frame(chart_win)
            outer.pack(fill="both", expand=True, padx=8, pady=8)
            scroll_canvas = _tk_scroll.Canvas(outer, highlightthickness=0)
            v_scroll = _tk_scroll.Scrollbar(outer, orient="vertical",
                                            command=scroll_canvas.yview)
            scroll_canvas.configure(yscrollcommand=v_scroll.set)
            v_scroll.pack(side="right", fill="y")
            scroll_canvas.pack(side="left", fill="both", expand=True)

            inner = _tk_scroll.Frame(scroll_canvas)
            inner_id = scroll_canvas.create_window((0, 0), window=inner, anchor="nw")

            canvas = FigureCanvasTkAgg(fig, master=inner)
            canvas.draw()
            chart_widget = canvas.get_tk_widget()
            chart_widget.configure(
                width=int(figsize[0] * 100), height=int(figsize[1] * 100),
            )
            chart_widget.pack(fill="both", expand=True)

            def _on_inner_configure(_event):
                scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))
            inner.bind("<Configure>", _on_inner_configure)

            def _on_canvas_configure(event):
                scroll_canvas.itemconfigure(inner_id, width=event.width)
            scroll_canvas.bind("<Configure>", _on_canvas_configure)

            # Mouse-wheel scroll (binds platform-aware deltas)
            def _on_mousewheel(event):
                delta = -1 if event.delta > 0 else 1
                scroll_canvas.yview_scroll(delta, "units")
            scroll_canvas.bind_all("<MouseWheel>", _on_mousewheel)
            # Unbind global mousewheel on window destroy so other windows
            # aren't affected.
            chart_win.bind("<Destroy>",
                           lambda _e: scroll_canvas.unbind_all("<MouseWheel>"))
        else:
            canvas = FigureCanvasTkAgg(fig, master=chart_win)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

        import customtkinter as _ctk_chart
        close_btn = _ctk_chart.CTkButton(
            chart_win, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=lambda: (plt.close(fig), chart_win.destroy()),
            font=_ctk_chart.CTkFont(size=12),
        )
        close_btn.pack(side="bottom", pady=(0, 8))

        def _on_close():
            try:
                plt.close(fig)
            except Exception:
                pass
            chart_win.destroy()
        chart_win.protocol("WM_DELETE_WINDOW", _on_close)
        return chart_win

    def _show_match_chart(self):
        """Top 10 files by match count from the most recent search."""
        matched = list(getattr(self, "matched_files", []) or [])
        if not matched:
            self._show_error(
                "No chart data yet. Run a search first — the chart shows the "
                "top 10 files by match count from the most recent search."
            )
            return
        try:
            ranked = sorted(matched, key=lambda r: r[2], reverse=True)[:10]
            labels = [r[1] for r in ranked]
            counts = [r[2] for r in ranked]
        except (IndexError, TypeError):
            self._show_error("Match data missing the count column — can't render a chart.")
            return

        # Search-terms prefix for the chart title — same pattern as
        # the Chart-File Type Count and Matched Files popup. Quoted,
        # comma-separated, capped at ~80 chars.
        try:
            import shlex as _shlex_mc
            _terms_raw = self.search_entry.get().strip() if hasattr(self, "search_entry") else ""
            try:
                _terms_tokens = _shlex_mc.split(_terms_raw)
            except ValueError:
                _terms_tokens = _terms_raw.split()
            _terms_display = ", ".join(f"'{t}'" for t in _terms_tokens)
            if len(_terms_display) > 80:
                _terms_display = _terms_display[:77] + "..."
        except Exception:
            _terms_display = ""

        def _plot(ax):
            y_pos = list(range(len(labels)))
            ax.barh(y_pos, counts, color="#2196F3", edgecolor="#1976D2")
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels, fontsize=9)
            ax.invert_yaxis()
            ax.set_xlabel("Matches", fontsize=10)
            base_title = "Top 10 files by match count"
            title = f"{_terms_display} — {base_title}" if _terms_display else base_title
            ax.set_title(title, fontsize=12, weight="bold")
            ax.grid(axis="x", linestyle="--", alpha=0.4)
            for i, v in enumerate(counts):
                ax.text(v, i, f" {v:,}", va="center", fontsize=9, color="#333333")

        self._open_chart_window("Top files by match count", _plot)

    def _show_filetype_chart(self):
        """Match count grouped by file extension, alphabetical.

        Companion to _show_match_chart. Reads the same self.matched_files
        list (each entry is (filepath, filename, count, lines)), groups
        by lowercased extension, sums the per-file counts, and renders a
        horizontal bar chart with types alphabetically on the Y axis.
        Files with no extension are grouped under '(no extension)'.
        """
        import os as _os_ft
        matched = list(getattr(self, "matched_files", []) or [])
        if not matched:
            self._show_error(
                "No chart data yet. Run a search first — the chart shows "
                "match counts grouped by file type for the most recent search."
            )
            return
        type_counts = {}
        try:
            for _fp, fname, count, _lines in matched:
                ext = _os_ft.path.splitext(fname)[1].lower()
                if not ext:
                    ext = "(no extension)"
                type_counts[ext] = type_counts.get(ext, 0) + count
        except (IndexError, TypeError, ValueError):
            self._show_error("Match data missing the count column — can't render a chart.")
            return
        if not type_counts:
            self._show_error("No matches to chart.")
            return

        labels = sorted(type_counts.keys(), key=lambda e: (e == "(no extension)", e))
        counts = [type_counts[e] for e in labels]
        total_matches = sum(counts)
        total_types = len(labels)

        # Also compute the count of distinct file types that were
        # SEARCHED — regardless of whether any file of that type matched.
        # Re-walk via discover_files; fast because the OS file cache is
        # warm from the search itself. Fails gracefully if the folder is
        # unavailable.
        searched_types_count = None
        try:
            folder = self.folder_entry.get().strip()
            if folder and _os_ft.path.isdir(folder):
                from peekdocs.scanner import discover_files as _discover
                use_ocr = self.ocr_var.get() == "on" if hasattr(self, "ocr_var") else False
                recursive = self.recursive_var.get() == "on" if hasattr(self, "recursive_var") else True
                file_types_raw = self.file_types_entry.get().strip() if hasattr(self, "file_types_entry") else ""
                file_types = [t.strip() for t in file_types_raw.split(",") if t.strip()] or None
                discovered = _discover(folder, recursive, use_ocr, file_types=file_types)
                if isinstance(discovered, list):
                    searched_exts = set()
                    for fp in discovered:
                        ext = _os_ft.path.splitext(fp)[1].lower() or "(no extension)"
                        searched_exts.add(ext)
                    searched_types_count = len(searched_exts)
        except Exception:
            searched_types_count = None

        # Search-terms prefix for the chart title. Quoted, comma-
        # separated. Trimmed to ~80 chars to keep the title from
        # spilling across the whole figure when the user searched for
        # a long expression. Empty / Expression mode falls back to
        # plain 'Matches by file type'.
        try:
            import shlex as _shlex_ft
            _terms_raw = self.search_entry.get().strip() if hasattr(self, "search_entry") else ""
            try:
                _terms_tokens = _shlex_ft.split(_terms_raw)
            except ValueError:
                _terms_tokens = _terms_raw.split()
            _terms_display = ", ".join(f"'{t}'" for t in _terms_tokens)
            if len(_terms_display) > 80:
                _terms_display = _terms_display[:77] + "..."
        except Exception:
            _terms_display = ""

        def _plot(ax):
            y_pos = list(range(len(labels)))
            ax.barh(y_pos, counts, color="#76BA1B", edgecolor="#5A8E15")
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels, fontsize=9)
            ax.invert_yaxis()
            ax.set_xlabel("Matches", fontsize=10)
            line1 = (
                f"{_terms_display} — Matches by file type"
                if _terms_display
                else "Matches by file type"
            )
            line2 = (
                f"{total_matches:,} total matches across {total_types} "
                f"matched file type{'s' if total_types != 1 else ''}"
            )
            if searched_types_count is not None:
                line2 += f" ({searched_types_count} file type{'s' if searched_types_count != 1 else ''} searched, 100+ supported)"
            ax.set_title(f"{line1}\n{line2}", fontsize=12, weight="bold")
            ax.grid(axis="x", linestyle="--", alpha=0.4)
            for i, v in enumerate(counts):
                ax.text(v, i, f" {v:,}", va="center", fontsize=9, color="#333333")

        # Wider geometry so the long composite title fits, and a figure
        # height that grows with the number of matched types so the
        # horizontal bars don't get crushed together. ~0.35 inches per
        # type with a 4.8" floor (covers the 1-12 type case at the
        # previous default height). The window opens at 520px tall and
        # scrolls vertically whenever the figure is taller than that.
        _ft_fig_h = max(4.8, 0.35 * total_types)
        self._open_chart_window(
            "Matches by file type", _plot,
            geometry="1100x520",
            figsize=(10.6, _ft_fig_h),
            scrollable=True,
        )

    # Extension → human-named category mapping for _show_category_chart.
    # Kept at module-load scope for cheap lookup and so the order below
    # is the chart's Y-axis order (most-recognized categories first;
    # 'Other' last so unknown extensions always sink to the bottom).
    _CATEGORY_MAP = {
        "Office": {".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
                   ".odt", ".ods", ".odp", ".rtf",
                   ".pages", ".numbers", ".key"},
        "PDF": {".pdf"},
        "Email": {".eml", ".msg", ".pst", ".mbox"},
        "E-books": {".epub"},
        "Images / OCR": {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"},
        "Archives": {".zip", ".tar", ".gz", ".bz2", ".tgz", ".7z", ".rar"},
        "Code": {".py", ".c", ".cpp", ".h", ".hpp", ".java", ".js", ".ts",
                 ".go", ".rs", ".rb", ".sh", ".bat", ".ps1", ".r", ".m",
                 ".v", ".vhd", ".vhdl", ".sv", ".cir", ".sp", ".spice",
                 ".tcl", ".pl", ".swift", ".kt", ".cs", ".vb", ".f90", ".f",
                 ".asm", ".s", ".lua", ".scala"},
        "Notebooks": {".ipynb"},
        "Data / Config": {".csv", ".tsv", ".json", ".jsonl", ".ndjson",
                          ".xml", ".yaml", ".yml", ".toml", ".ini", ".cfg",
                          ".conf", ".sql", ".properties", ".env", ".tf",
                          ".proto", ".graphql", ".gql", ".gradle", ".cmake",
                          ".makefile", ".dockerfile"},
        "Markup / Docs": {".md", ".rst", ".tex", ".html", ".css", ".scss"},
        "Calendar / Contacts": {".ics", ".vcf"},
        "Plain text": {".txt", ".log"},
        "CAD / Engineering": {".dxf", ".vsdx"},
    }

    def _show_category_chart(self):
        """Match counts grouped by human-readable category.

        Rolls the per-extension counts from self.matched_files up into
        named buckets (Office, PDF, Email, Images / OCR, Archives,
        Code, Data / Config, etc.). Useful when the per-extension
        chart has 20+ bars and the viewer wants the at-a-glance
        breakdown by what kind of content peekdocs found in.
        """
        import os as _os_cat
        matched = list(getattr(self, "matched_files", []) or [])
        if not matched:
            self._show_error(
                "No chart data yet. Run a search first — the chart shows "
                "match counts grouped by file-type category for the "
                "most recent search."
            )
            return

        # Build extension → category lookup (inverted from _CATEGORY_MAP).
        ext_to_cat = {}
        for cat_name, exts in self._CATEGORY_MAP.items():
            for ext in exts:
                ext_to_cat[ext] = cat_name

        category_counts = {}
        try:
            for _fp, fname, count, _lines in matched:
                ext = _os_cat.path.splitext(fname)[1].lower()
                cat = ext_to_cat.get(ext, "Other")
                category_counts[cat] = category_counts.get(cat, 0) + count
        except (IndexError, TypeError, ValueError):
            self._show_error("Match data missing the count column — can't render a chart.")
            return
        if not category_counts:
            self._show_error("No matches to chart.")
            return

        # Sort by match count descending — categories with the most
        # matches read first; 'Other' falls wherever its count lands
        # (typically near the bottom since it captures the long tail).
        ranked = sorted(category_counts.items(), key=lambda kv: kv[1], reverse=True)
        labels = [k for k, _ in ranked]
        counts = [v for _, v in ranked]
        total_matches = sum(counts)
        total_categories = len(labels)

        # Search-terms prefix — same pattern as the other chart titles.
        try:
            import shlex as _shlex_cat
            _terms_raw = self.search_entry.get().strip() if hasattr(self, "search_entry") else ""
            try:
                _terms_tokens = _shlex_cat.split(_terms_raw)
            except ValueError:
                _terms_tokens = _terms_raw.split()
            _terms_display = ", ".join(f"'{t}'" for t in _terms_tokens)
            if len(_terms_display) > 80:
                _terms_display = _terms_display[:77] + "..."
        except Exception:
            _terms_display = ""

        def _plot(ax):
            y_pos = list(range(len(labels)))
            # Distinctive purple/violet so this chart is visually
            # different from the green Chart-File Type Count and the
            # blue Top-files chart.
            ax.barh(y_pos, counts, color="#7E57C2", edgecolor="#5E35B1")
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels, fontsize=10)
            ax.invert_yaxis()
            ax.set_xlabel("Matches", fontsize=10)
            line1 = (
                f"{_terms_display} — Matches by file-type category"
                if _terms_display
                else "Matches by file-type category"
            )
            line2 = (
                f"{total_matches:,} total matches across {total_categories} "
                f"categor{'ies' if total_categories != 1 else 'y'} "
                f"({len(self._CATEGORY_MAP) + 1} categories tracked)"
            )
            ax.set_title(f"{line1}\n{line2}", fontsize=12, weight="bold")
            ax.grid(axis="x", linestyle="--", alpha=0.4)
            for i, v in enumerate(counts):
                ax.text(v, i, f" {v:,}", va="center", fontsize=10, color="#333333")

        # Categories are bounded (~13) so the default chart height is
        # plenty; no vertical scroll needed.
        self._open_chart_window(
            "Matches by file-type category", _plot,
            geometry="1000x520",
            figsize=(9.6, 4.8),
        )

    def _clear_preview(self):
        """Clear the Results Preview pane and the matched/excluded files buttons.

        Leaving the buttons visible after clearing the preview is misleading
        — the preview pane goes empty but the buttons still advertise
        "N Matched File(s)" / "N Excluded File(s)" against no on-screen
        evidence. Mirror the reset pattern used at search start
        (lines 215–220) so the main screen returns to a clean state.
        """
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.configure(state="disabled")
        if hasattr(self, "_preview_cap_status"):
            self._preview_cap_status.configure(text="")
        # _preview_count_label removed — counts now live in headline.
        if hasattr(self, "_results_summary_label"):
            self._results_summary_label.configure(text="")
        self._matched_files_link.pack_forget()
        self._excluded_files_btn.pack_forget()
        self._hide_files_list()
        # Drop any saved Suite-run highlight regex too — clearing the
        # preview means there's no result on screen this regex still
        # applies to.
        self._suite_highlight_re = None
        self.status_label.configure(
            text=__import__("peekdocs.i18n", fromlist=["t"]).t("preview_cleared_status"),
            text_color=("blue", "#66BBFF"),
        )

    def _update_search_progress(self, done, total):
        """Update the determinate progress bar during search."""
        pct = done / total if total > 0 else 0
        self.progress_bar.set(pct)
        if self.search_start_time is not None:
            elapsed = time.time() - self.search_start_time
            pct_display = int(pct * 100)
            self.status_label.configure(
                text=f"Searching... {done}/{total} files  ({pct_display}%)  ({elapsed:.0f}s)",
                text_color=("blue", "#66BBFF"),
            )



    def _show_action_buttons(self, inverse=False):
        """Show Matched Files and View Report buttons."""
        self._clear_action_buttons()

        has_matched = bool(self.matched_files)

        # Check which report formats exist. _report_file_prefix lets the same
        # report-button row serve both Standard Search and Suite runs without
        # duplicate widgets — defaults to "peekdocs_standard_results" and is
        # reassigned by _suite_finished() to point at "peekdocs_suite_results"
        # so the same DOCX/TXT/etc. buttons open suite reports after a Run
        # Suite completes.
        prefix = getattr(self, "_report_file_prefix", "peekdocs_standard_results")
        report_formats = {}
        # Mtime cutoff: only treat a format as "green" if its file mtime
        # is at or after the current search's start time. Prevents a
        # leftover peekdocs_standard_results.pdf from a prior session
        # showing as green after a run that didn't even ask for PDF
        # output. _last_search_start_time survives the search_start_time
        # = None reset at search-finish so it's still readable here. The
        # 2-second buffer accommodates filesystem timestamp coarseness
        # on Windows and network shares. If no start time has been
        # recorded yet (very first action-button render before any
        # search has run), fall back to the exists-only check.
        _cutoff = getattr(self, "_last_search_start_time", None)
        if self.results_dir:
            suffix = f"_{self._last_ts_suffix}" if getattr(self, '_last_ts_suffix', '') else ""
            for fmt in ("txt", "docx", "csv", "json", "pdf", "html"):
                path = os.path.join(self.results_dir, f"{prefix}{suffix}.{fmt}")
                if not os.path.exists(path):
                    report_formats[fmt] = False
                elif _cutoff is None:
                    report_formats[fmt] = True
                else:
                    try:
                        report_formats[fmt] = os.path.getmtime(path) >= _cutoff - 2
                    except OSError:
                        report_formats[fmt] = False

        has_any_report = any(report_formats.values())

        if not has_any_report:
            return

        # Pack report format buttons. TXT first because it's always
        # written and feeds the GUI's preview pane; DOCX next; then the
        # optional formats in the same order as the Advanced checkboxes.
        for fmt, btn in [
            ("txt", self.report_btn_txt),
            ("docx", self.report_btn_docx),
            ("csv", self.report_btn_csv),
            ("json", self.report_btn_json),
            ("pdf", self.report_btn_pdf),
            ("html", self.report_btn_html),
        ]:
            btn.pack(side="left", padx=(0, 2))
            btn.configure(state="normal")
            if report_formats.get(fmt):
                btn.configure(
                    fg_color="green",
                    hover_color="darkgreen",
                    text_color="white",
                )
            else:
                btn.configure(
                    fg_color="#CC3333",
                    hover_color="#AA2222",
                    text_color="white",
                )
        # Delete on Close checkbox removed from this row.
        # report_frame is gridded at startup by _app.py and is never
        # hidden during a search any more — no re-grid needed here.



    def _clear_action_buttons(self):
        """Hide all action buttons."""
        self.matched_files_button.grid_remove()
        # report_frame is the Step 3 label row ("Use Advanced Search
        # Options below…") — keep it visible during searches so the
        # rows below it (Step 4, status, report buttons, Advanced) do
        # not collapse upward when the search starts.
        self.report_btn_txt.pack_forget()
        self.report_btn_docx.pack_forget()
        self.report_btn_csv.pack_forget()
        self.report_btn_json.pack_forget()
        self.report_btn_pdf.pack_forget()
        self.report_btn_html.pack_forget()



    def _show_simple_popup(self, title, heading, message):
        """Show a simple informational popup with a consistent look and Close button."""
        import tkinter as tk
        popup, _dark = self._themed_toplevel()

        popup.withdraw()  # hidden during widget setup; centered + shown at end
        popup.title(title)
        popup.resizable(False, False)
        self._center_popup_on_main(popup, 520, 280)
        try:
            popup.transient(self)
        except Exception:
            pass

        # Close button anchored to the bottom row
        ctk.CTkButton(
            popup, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=popup.destroy,
            font=ctk.CTkFont(size=12),
        ).pack(side="bottom", pady=(5, 15))

        tk.Label(
            popup, text=heading,
            font=("TkDefaultFont", 14, "bold"),
        ).pack(pady=(18, 8))

        tk.Label(
            popup, text=message,
            font=("TkDefaultFont", 12),
            wraplength=470, justify="left",
        ).pack(padx=20, pady=(0, 10), fill="both", expand=True)
        self._apply_dark_theme(popup)



    def open_error_log(self):
        """Open the peekdocs error log file in an in-app viewer.

        Replaces an earlier safe_open_file() call that handed the log off
        to TextEdit (or the system default text editor). TextEdit has no
        peekdocs Close button at the bottom and opens its own subsequent
        windows (e.g. Reveal in Finder) on whichever monitor the OS
        chooses — both behaviors users found confusing. The in-app viewer
        gives a centered Close button and stays on the main window's
        monitor.
        """
        # Check results dir first (output dir if set), then search folder
        candidates = []
        if self.results_dir:
            candidates.append(self.results_dir)
        folder = self.folder_entry.get().strip()
        if folder and folder not in candidates:
            candidates.append(folder)
        if not candidates:
            self._show_error("Please select a folder first.")
            return
        error_log_path = None
        for d in candidates:
            p = os.path.join(d, "peekdocs_errors.log")
            if os.path.exists(p):
                error_log_path = p
                break
        if not error_log_path:
            self._show_simple_popup(
                title="Error Log",
                heading="No Error Log Found",
                message=(
                    "No error log was found.\n\n"
                    "This is good news — the log file is only created when a file error "
                    "occurs during a search (e.g., a file couldn't be read). If you haven't "
                    "had any errors, no log exists."
                ),
            )
            self.status_label.configure(
                text="No error log found — no file errors have occurred.",
                text_color="green",
            )
            return
        self._show_error_log_viewer(error_log_path)

    def _show_error_log_viewer(self, log_path):
        """Show the error log content in an in-app popup with a Close button."""
        import tkinter as tk
        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError as exc:
            self._show_error(f"Could not read {log_path}: {exc}")
            return

        popup, _dark = self._themed_toplevel()
        popup.withdraw()  # hidden during widget setup; centered + shown at end
        popup.title("Error Log")
        popup.resizable(True, True)

        # Path label so users can find the file on disk if they want.
        tk.Label(
            popup, text=log_path,
            font=("TkDefaultFont", 10), fg="gray",
        ).pack(anchor="w", padx=12, pady=(10, 4))

        # Log text — scrollable, read-only, monospace.
        text_frame = tk.Frame(popup)
        text_frame.pack(fill="both", expand=True, padx=12, pady=(0, 4))
        vbar = tk.Scrollbar(text_frame, orient="vertical")
        vbar.pack(side="right", fill="y")
        txt = tk.Text(
            text_frame, wrap="word",
            font=("Courier", 11),
            yscrollcommand=vbar.set,
            borderwidth=0, highlightthickness=0,
        )
        vbar.config(command=txt.yview)
        txt.pack(side="left", fill="both", expand=True)
        txt.insert("1.0", content or "(error log is empty)")
        txt.configure(state="disabled")

        # Clear Log row — left-anchored, sits one row above Close.
        # The file might be deleted by _clear_error_log(); if so, close the
        # viewer since the content it's showing is now stale.
        def _clear_and_close():
            self._clear_error_log()
            if not os.path.exists(log_path):
                popup.destroy()

        clear_row = tk.Frame(popup)
        clear_row.pack(fill="x", padx=12, pady=(5, 0))
        ctk.CTkButton(
            clear_row, text="Clear Log", width=100,
            fg_color="#CC3333", hover_color="#AA2222",
            text_color="white",
            command=_clear_and_close,
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left")

        # Close — centered, on its own row at the bottom.
        close_row = tk.Frame(popup)
        close_row.pack(pady=(5, 12))
        ctk.CTkButton(
            close_row, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            command=popup.destroy, font=ctk.CTkFont(size=12),
        ).pack()

        self._apply_dark_theme(popup)
        self._center_popup_on_main(popup, 760, 500)



    def _clear_results_files(self):
        """Delete all peekdocs_*_results* files from the search folder."""
        folder = self.results_dir or self.folder_entry.get().strip()
        if not folder or not os.path.isdir(folder):
            self._show_error("Please select a folder first.")
            return
        # Find all standard/regex/suite result files
        results_files = [
            f for f in os.listdir(folder)
            if f.startswith(RESULT_FILE_PREFIXES)
        ]
        if not results_files:
            self.status_label.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("status_no_results_to_clear"))
            return
        from tkinter import messagebox
        msg = f"Delete {len(results_files)} results file(s)?\n\n"
        if len(results_files) <= 10:
            msg += "\n".join(results_files)
        else:
            msg += "\n".join(results_files[:10]) + f"\n... and {len(results_files) - 10} more"
        msg += "\n\nThis cannot be undone."
        if messagebox.askyesno("Clear Search Results", msg):
            deleted = 0
            for fname in results_files:
                try:
                    os.remove(os.path.join(folder, fname))
                    deleted += 1
                except OSError:
                    pass
            self.status_label.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("status_deleted_results_format").format(n=deleted))
            self._hide_preview()
            self._clear_action_buttons()



    def _clear_error_log(self):
        """Delete the peekdocs error log file after confirmation."""
        folder = self.results_dir or self.folder_entry.get().strip()
        if not folder or not os.path.isdir(folder):
            self._show_error("Please select a folder first.")
            return
        error_log_path = os.path.join(folder, "peekdocs_errors.log")
        if not os.path.exists(error_log_path):
            self.status_label.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("status_no_error_log_to_clear"))
            return
        from tkinter import messagebox
        if messagebox.askyesno("Clear Error Log",
                               f"Delete {os.path.basename(error_log_path)}?\n\nThis cannot be undone."):
            try:
                os.remove(error_log_path)
                self.status_label.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("status_error_log_cleared"))
            except OSError as e:
                self._show_error(f"Could not delete error log: {e}")



    def _clean_folder(self):
        """Browse to any folder and delete peekdocs-generated files in it.

        Two-stage confirmation: auto-generated files (results / index /
        error log) first, then user-saved reports (peekdocs_report_* /
        peekdocs_accumulated_*) as a separate opt-in. Both dialogs warn
        that any file the user manually named with a peekdocs_ prefix
        gets caught by the pattern match. Deletion failures are
        reported explicitly rather than silently swallowed.
        """
        import tkinter as tk
        from tkinter import filedialog, messagebox

        folder = filedialog.askdirectory(title="Select folder to clean")
        if not folder or not os.path.isdir(folder):
            return

        # Split into two categories: auto-generated vs user-saved
        auto_files = []
        user_saved_files = []
        for fname in os.listdir(folder):
            if (fname.startswith(RESULT_FILE_PREFIXES) or
                    fname == "peekdocs_errors.log" or
                    fname in (".peekdocs.db", ".peekdocs.db-wal", ".peekdocs.db-shm")):
                auto_files.append(fname)
            elif (fname.startswith("peekdocs_report_") or
                  fname.startswith("peekdocs_accumulated_")):
                user_saved_files.append(fname)

        if not auto_files and not user_saved_files:
            messagebox.showinfo("Clean Folder", f"No peekdocs files found in:\n{folder}")
            return

        deleted = []
        failed = []  # list of (fname, reason)

        def _delete_each(files):
            for fname in files:
                try:
                    os.remove(os.path.join(folder, fname))
                    deleted.append(fname)
                except OSError as exc:
                    failed.append((fname, str(exc)))

        # Stage 1 \u2014 auto-generated files (results, index, error log).
        if auto_files:
            file_list = "\n".join(f"  \u2022 {f}" for f in sorted(auto_files))
            if messagebox.askyesno(
                "Clean Folder \u2014 Auto-Generated Files",
                f"Delete {len(auto_files)} auto-generated peekdocs file(s) from:\n{folder}\n\n"
                f"{file_list}\n\n"
                "Saved searches (.peekdocs_collection.json), settings (~/.peekdocsrc), "
                "and bookmarks (~/.peekdocs_bookmarks.json) are not affected.\n\n"
                "IMPORTANT: this deletes any file in this folder whose name starts "
                "with 'peekdocs_standard_results', 'peekdocs_regex_results', or "
                "'peekdocs_suite_results', plus the search index (.peekdocs.db*) "
                "and error log. If you have manually named other files with these "
                "prefixes, they will be deleted too.\n\n"
                "This cannot be undone.\n\n"
                "Continue?",
            ):
                _delete_each(auto_files)

        # Stage 2 \u2014 user-saved reports (opt-in, default No).
        if user_saved_files:
            file_list = "\n".join(f"  \u2022 {f}" for f in sorted(user_saved_files))
            if messagebox.askyesno(
                "Clean Folder \u2014 Saved Reports",
                f"The following files in:\n{folder}\n\n"
                f"look like saved reports you named yourself "
                f"(peekdocs_report_* / peekdocs_accumulated_*) \u2014 these may be "
                f"intentional and are NOT removed by Clear Files unless you "
                f"explicitly check them.\n\n"
                f"{file_list}\n\n"
                "IMPORTANT: if you have manually named other files with the prefix "
                "'peekdocs_report_' or 'peekdocs_accumulated_', they will be deleted too.\n\n"
                "This cannot be undone.\n\n"
                f"Delete these {len(user_saved_files)} file(s) too?",
                default=messagebox.NO,
            ):
                _delete_each(user_saved_files)

        # Report results.
        if not deleted and not failed:
            self.status_label.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("status_no_files_deleted"))
            return

        if failed:
            preview = "\n".join(f"  \u2022 {f}: {r}" for f, r in failed[:5])
            if len(failed) > 5:
                preview += f"\n  ... and {len(failed) - 5} more"
            messagebox.showwarning(
                "Clean Folder \u2014 Some Deletions Failed",
                f"Deleted {len(deleted)} file(s).\n"
                f"Could not delete {len(failed)} file(s):\n\n{preview}\n\n"
                "Common causes: file is locked by another program, "
                "insufficient permissions, or the file was already removed.",
            )
            self.status_label.configure(
                text=f"Cleaned {len(deleted)} file(s); {len(failed)} failed.",
                text_color="orange",
            )
        else:
            self.status_label.configure(
                text=f"Cleaned {len(deleted)} file(s) from {os.path.basename(folder)}.",
                text_color="green",
            )

    def _clear_files(self):
        """Tabbed popup: Wipe Session (bulk session wipe) and Choose Files
        (per-file picker in the current Search Folder).

        Wipe Session replaces the standalone Delete Now button that used
        to live in the main page report row. Centralizing both bulk and
        granular cleanup paths in one Tools-menu popup keeps the
        delete-files mental model in one place.
        """
        import tkinter as tk
        from tkinter import messagebox

        # ── Wipe Session scope ──
        # Every folder peekdocs has touched this session, plus the safe
        # output dir and saved-config folders. Matches the scope the old
        # Delete Now button used.
        folders_to_clean = set(getattr(self, "_searched_folders", set()))
        search_folder = self.folder_entry.get().strip() if hasattr(self, "folder_entry") else ""
        if search_folder and os.path.isdir(search_folder):
            folders_to_clean.add(search_folder)
        results_dir = getattr(self, "results_dir", None)
        if results_dir and os.path.isdir(results_dir):
            folders_to_clean.add(results_dir)
        safe_dir = os.path.join(os.path.expanduser("~"), "peekdocs_reports")
        if os.path.isdir(safe_dir):
            folders_to_clean.add(safe_dir)
        try:
            from peekdocs.cli import _load_config
            _cfg = _load_config()
            _cfg_folder = _cfg.get("folder", "")
            if _cfg_folder and os.path.isdir(_cfg_folder):
                folders_to_clean.add(_cfg_folder)
            _rs_folder = _cfg.get("regex_search_folder", "")
            if _rs_folder and os.path.isdir(_rs_folder):
                folders_to_clean.add(_rs_folder)
        except Exception:
            pass

        folders_with_files = []
        for folder in folders_to_clean:
            if not os.path.isdir(folder):
                continue
            try:
                for fname in os.listdir(folder):
                    if (fname.startswith(RESULT_FILE_PREFIXES)
                            or fname in (".peekdocs.db", ".peekdocs.db-wal", ".peekdocs.db-shm")):
                        folders_with_files.append(folder)
                        break
            except OSError:
                pass

        # ── Choose Files scope (current Search Folder only) ──
        categories = [
            ("Standard search results",
             "Overwritten after each Standard Search. Safe to delete.", []),
            ("Regex search results",
             "Overwritten after each Regex Search. Safe to delete.", []),
            ("Suite results",
             "Overwritten after each suite run. Safe to delete.", []),
            ("Saved reports (from 'Save report as:')",
             "Named copies you saved. Only delete if you no longer need them.", []),
            ("Accumulated reports (from 'Append to:')",
             "Results appended across multiple searches. Only delete if you no longer need them.", []),
            ("Error log",
             "Log of files that couldn't be read. Safe to delete.", []),
            ("Search index",
             "Built for faster searches. Can be rebuilt any time with Manage Indexes.", []),
        ]
        if search_folder and os.path.isdir(search_folder):
            for root, dirs, files in os.walk(search_folder):
                for fname in files:
                    filepath = os.path.join(root, fname)
                    if fname.startswith("peekdocs_standard_results"):
                        categories[0][2].append(filepath)
                    elif fname.startswith("peekdocs_regex_results"):
                        categories[1][2].append(filepath)
                    elif fname.startswith("peekdocs_suite_results"):
                        categories[2][2].append(filepath)
                    elif fname.startswith("peekdocs_report_"):
                        categories[3][2].append(filepath)
                    elif fname.startswith("peekdocs_accumulated_"):
                        categories[4][2].append(filepath)
                    elif fname == "peekdocs_errors.log":
                        categories[5][2].append(filepath)
                    elif fname in (".peekdocs.db", ".peekdocs.db-wal", ".peekdocs.db-shm"):
                        categories[6][2].append(filepath)

        all_choose_files = []
        for _, _, cat_files in categories:
            all_choose_files.extend(cat_files)

        if not folders_with_files and not all_choose_files:
            self.status_label.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("status_no_peekdocs_files_to_clear"))
            return

        # ── Popup ──
        win, _dark = self._themed_toplevel()
        win.withdraw()
        win.title("Clear Files")
        win.resizable(True, True)
        self._center_popup_on_main(win, 720, 580)

        _sf = self._scaled_font

        tabview = ctk.CTkTabview(win)
        tabview.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        # ── Tab 1: Wipe Session ──
        tab_wipe = tabview.add("Wipe Session")

        if folders_with_files:
            tk.Label(tab_wipe, text="Wipe everything peekdocs created this session",
                     font=_sf(13, "bold")).pack(anchor="w", padx=10, pady=(8, 4))

            tk.Label(tab_wipe, text=f"Affected folders ({len(folders_with_files)}):",
                     font=_sf(11, "bold")).pack(anchor="w", padx=10, pady=(6, 2))
            for f in sorted(folders_with_files):
                tk.Label(tab_wipe, text=f"  • {f}", font=_sf(10),
                         justify="left", wraplength=640, anchor="w").pack(anchor="w", padx=(20, 10))

            tk.Label(tab_wipe, text="What gets deleted:",
                     font=_sf(11, "bold")).pack(anchor="w", padx=10, pady=(10, 2))
            for line in (
                "Standard / Regex / Suite search result files",
                "Search index (.peekdocs.db, -wal, -shm)",
                "Search history (~/.peekdocs_history.json)",
                "Recent searches",
                "Search terms + Folder field (cleared on screen)",
            ):
                tk.Label(tab_wipe, text=f"  • {line}", font=_sf(10)).pack(anchor="w", padx=(20, 10))

            tk.Label(tab_wipe, text="What's preserved:",
                     font=_sf(11, "bold")).pack(anchor="w", padx=10, pady=(10, 2))
            for line in (
                "Saved reports (peekdocs_report_*)",
                "Accumulated reports (peekdocs_accumulated_*)",
                "Saved searches, settings, bookmarks",
            ):
                tk.Label(tab_wipe, text=f"  • {line}", font=_sf(10)).pack(anchor="w", padx=(20, 10))

            def _do_wipe():
                if not messagebox.askyesno(
                    "Wipe Session",
                    f"Wipe peekdocs files across {len(folders_with_files)} folder(s) "
                    f"plus your search history and recent searches?\n\nThis cannot be undone.",
                    parent=win,
                ):
                    return

                deleted, failed = [], []
                for folder in folders_to_clean:
                    if not os.path.isdir(folder):
                        continue
                    try:
                        for fname in os.listdir(folder):
                            if fname.startswith(RESULT_FILE_PREFIXES):
                                p = os.path.join(folder, fname)
                                try:
                                    os.remove(p)
                                    deleted.append(p)
                                except OSError as exc:
                                    failed.append((p, str(exc)))
                    except OSError as exc:
                        failed.append((folder, str(exc)))
                    for idx_file in (".peekdocs.db", ".peekdocs.db-wal", ".peekdocs.db-shm"):
                        idx_path = os.path.join(folder, idx_file)
                        if os.path.exists(idx_path):
                            try:
                                os.remove(idx_path)
                                deleted.append(idx_path)
                            except OSError as exc:
                                failed.append((idx_path, str(exc)))

                self._clear_preview()

                history_path = os.path.join(os.path.expanduser("~"), ".peekdocs_history.json")
                try:
                    if os.path.exists(history_path):
                        os.remove(history_path)
                except OSError:
                    pass

                try:
                    from peekdocs.cli import _load_config, _save_config
                    cfg = _load_config()
                    cfg["recent_searches"] = []
                    cfg["search_terms"] = ""
                    cfg["folder"] = ""
                    _save_config(cfg)
                    self._recent_searches = []
                except Exception:
                    pass

                self.index_search_var.set("off")
                self.search_entry.delete(0, "end")
                self.folder_entry.delete(0, "end")
                self._clear_action_buttons()

                win.destroy()

                if failed:
                    preview = "\n".join(f"  • {p}: {r}" for p, r in failed[:5])
                    if len(failed) > 5:
                        preview += f"\n  ... and {len(failed) - 5} more"
                    messagebox.showwarning(
                        "Wipe Session — Some Deletions Failed",
                        f"Deleted {len(deleted)} file(s); cleared preview, history, and recent searches.\n"
                        f"Could not delete {len(failed)} file(s):\n\n{preview}\n\n"
                        "Common causes: file is locked by another program, "
                        "insufficient permissions, or the file was already removed.",
                    )
                    self.status_label.configure(
                        text=f"Wiped {len(deleted)} file(s); {len(failed)} failed.",
                        text_color="orange",
                    )
                else:
                    self.status_label.configure(
                        text=f"Wiped {len(deleted)} file(s) across {len(folders_with_files)} folder(s); cleared preview, history, and recent searches.",
                        text_color="green",
                    )

            ctk.CTkButton(
                tab_wipe, text="Wipe Session", width=140,
                fg_color="#CC3333", hover_color="#AA2222", text_color="white",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=_do_wipe,
            ).pack(pady=(16, 10))
        else:
            tk.Label(
                tab_wipe,
                text="No peekdocs files found across any session folder.\nNothing to wipe.",
                font=_sf(11), justify="center",
            ).pack(expand=True, pady=40)

        # ── Tab 2: Choose Files ──
        tab_choose = tabview.add("Choose Files")

        if all_choose_files and search_folder:
            tk.Label(
                tab_choose, text=f"Search folder: {search_folder}",
                font=_sf(11, "bold"), wraplength=640, justify="left", anchor="w",
            ).pack(anchor="w", padx=10, pady=(8, 2))
            tk.Label(
                tab_choose,
                text="Check the files you want to delete. Your original documents, saved searches, "
                     "settings, and bookmarks are never shown here and cannot be deleted.",
                font=_sf(10), fg="gray", wraplength=640, justify="left",
            ).pack(anchor="w", padx=10, pady=(0, 6))

            list_frame = tk.Frame(tab_choose)
            list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

            canvas = tk.Canvas(list_frame, highlightthickness=0)
            scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
            inner = tk.Frame(canvas)
            inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=inner, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)

            check_vars = []
            for cat_name, cat_desc, cat_files in categories:
                if not cat_files:
                    continue
                tk.Label(inner, text=cat_name, font=_sf(11, "bold")).pack(anchor="w", pady=(8, 0))
                tk.Label(inner, text=cat_desc, font=_sf(9), fg="gray").pack(anchor="w", padx=(4, 0), pady=(0, 2))
                for filepath in sorted(cat_files):
                    var = tk.BooleanVar(value=False)
                    rel = os.path.relpath(filepath, search_folder)
                    try:
                        size = os.path.getsize(filepath)
                        size_str = f" ({size:,} bytes)" if size < 1_000_000 else f" ({size / 1_000_000:.1f} MB)"
                    except OSError:
                        size_str = ""
                    tk.Checkbutton(
                        inner, variable=var,
                        text=f"{rel}{size_str}",
                        font=_sf(10), anchor="w",
                    ).pack(anchor="w", padx=(16, 0))
                    check_vars.append((var, filepath))

            def _select_all():
                for var, _ in check_vars:
                    var.set(True)

            def _deselect_all():
                for var, _ in check_vars:
                    var.set(False)

            def _delete_selected():
                selected = [(var, path) for var, path in check_vars if var.get()]
                if not selected:
                    self._show_error("No files selected.")
                    return
                if not messagebox.askyesno(
                    "Confirm Delete",
                    f"Permanently delete {len(selected)} file(s)?\n\nThis cannot be undone.",
                    parent=win,
                ):
                    return
                deleted = 0
                for var, path in selected:
                    try:
                        os.remove(path)
                        deleted += 1
                    except OSError:
                        pass
                win.destroy()
                self.status_label.configure(text=__import__("peekdocs.i18n", fromlist=["t"]).t("status_deleted_files_format").format(n=deleted))
                self._hide_preview()
                self._clear_action_buttons()

            btn_frame = tk.Frame(tab_choose)
            btn_frame.pack(fill="x", padx=10, pady=(5, 8))
            ctk.CTkButton(btn_frame, text="Select All", width=80, font=ctk.CTkFont(size=12), command=_select_all).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="Deselect All", width=90, font=ctk.CTkFont(size=12), command=_deselect_all).pack(side="left", padx=2)
            ctk.CTkButton(
                btn_frame, text="Delete Selected", width=120,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#CC3333", hover_color="#AA2222",
                command=_delete_selected,
            ).pack(side="left", padx=(20, 2))
        else:
            if not search_folder:
                msg = "Set a Search Folder on the main page to use Choose Files."
            else:
                msg = f"No peekdocs files found in:\n{search_folder}"
            tk.Label(tab_choose, text=msg, font=_sf(11), justify="center").pack(expand=True, pady=40)

        # ── Close button at popup level ──
        ctk.CTkButton(
            win, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            font=ctk.CTkFont(size=12), command=win.destroy,
        ).pack(pady=(0, 10))

        # Default to Wipe Session if it has content; otherwise Choose Files
        tabview.set("Wipe Session" if folders_with_files else "Choose Files")

        self._apply_dark_theme(win)
        win.deiconify()

    def _clean_up_practice_files(self):
        """Delete all peekdocs-generated artifacts from the search folder
        (and all subfolders), preserving saved searches and settings.

        For users who have been experimenting with the app and want to
        start fresh before serious work.
        """
        folder = self.folder_entry.get().strip()
        if not folder or not os.path.isdir(folder):
            self._show_error("Please select a folder first.")
            return

        # Files to delete — anything peekdocs created during searches
        # Preserved: .peekdocs_collection.json (saved searches)
        #           .peekdocsrc (in home dir, not search folder anyway)
        to_delete = []  # list of (path, reason)

        for root, dirs, files in os.walk(folder):
            for fname in files:
                filepath = os.path.join(root, fname)
                # Search result files (standard / regex / suite)
                if fname.startswith(RESULT_FILE_PREFIXES):
                    to_delete.append((filepath, "search results"))
                # Saved reports (peekdocs_report_*, peekdocs_accumulated_*) are preserved — use Clear Saved Reports
                # Error log
                elif fname == "peekdocs_errors.log":
                    to_delete.append((filepath, "error log"))
                # Index database
                elif fname in (".peekdocs.db", ".peekdocs.db-wal", ".peekdocs.db-shm"):
                    to_delete.append((filepath, "index database"))

        if not to_delete:
            self.status_label.configure(
                text="Nothing to clean up — no practice files found.",
                text_color=("blue", "#66BBFF"),
            )
            return

        from tkinter import messagebox
        # Build confirmation message
        from collections import Counter
        reasons = Counter(r for _, r in to_delete)
        reason_lines = "\n".join(f"  \u2022 {count} {reason}" for reason, count in sorted(reasons.items()))
        msg = (
            f"Delete {len(to_delete)} practice file(s) from\n"
            f"{folder}\n\n"
            f"{reason_lines}\n\n"
            f"PRESERVED:\n"
            f"  \u2022 Your saved searches (.peekdocs_collection.json)\n"
            f"  \u2022 Your saved reports (peekdocs_report_*, peekdocs_accumulated_*)\n"
            f"  \u2022 Your settings (~/.peekdocsrc)\n"
            f"  \u2022 Your original documents\n\n"
            f"This cannot be undone."
        )
        if not messagebox.askyesno("Clean Up Practice Files", msg):
            return

        deleted = 0
        failed = 0
        for path, _ in to_delete:
            try:
                os.remove(path)
                deleted += 1
            except OSError:
                failed += 1

        # Refresh index button color since we may have deleted the index
        self._update_index_button_color()
        self._hide_preview()
        self._clear_action_buttons()

        if failed:
            self.status_label.configure(
                text=f"Cleaned up {deleted} file(s). {failed} could not be deleted.",
                text_color=("blue", "#66BBFF"),
            )
        else:
            self.status_label.configure(
                text=f"Cleaned up {deleted} practice file(s). Saved searches preserved.",
                text_color=("blue", "#66BBFF"),
            )



    def _open_report_format(self, fmt):
        """Open the report file for the given format (txt, docx, csv, json)."""
        from peekdocs.gui._helpers import safe_open_file
        prefix = getattr(self, "_report_file_prefix", "peekdocs_standard_results")
        suffix = f"_{self._last_ts_suffix}" if getattr(self, '_last_ts_suffix', '') else ""
        path = os.path.join(self.results_dir, f"{prefix}{suffix}.{fmt}")
        if not os.path.exists(path):
            self._show_error(f"Report file not found: {os.path.basename(path)}")
            return
        warning = safe_open_file(path)
        if warning:
            self._show_error(warning)



    def _compute_excluded_files(self, folder, recursive=True):
        """Walk the search folder and return a list of (filepath, reason) tuples
        for files that peekdocs did NOT include in its search pool.

        Files that were discovered but skipped at process time (e.g., oversized)
        are reported in the error log, not here — that avoids double-counting.
        """
        from peekdocs.constants import SUPPORTED_TYPES, OCR_IMAGE_TYPES
        from peekdocs.scanner import discover_files as _discover
        excluded = []
        use_ocr = self.ocr_var.get() == "on"
        supported = SUPPORTED_TYPES | (OCR_IMAGE_TYPES if use_ocr else set())

        # Get the set of files peekdocs would include in its search pool
        try:
            disc = _discover(folder, recursive=recursive, use_ocr=use_ocr)
            if isinstance(disc, tuple):
                searched_set = set()
            else:
                searched_set = {os.path.normcase(os.path.normpath(p)) for p in disc}
        except Exception:
            searched_set = set()

        # Check for oversized files — these are discovered but skipped at
        # process time, so move them from searched_set to excluded.
        try:
            max_mb = int(self.max_file_size_entry.get().strip() or "100")
        except (ValueError, AttributeError):
            max_mb = 100
        if max_mb > 0:
            oversized = set()
            for fp in searched_set:
                try:
                    size_mb = os.path.getsize(fp) / (1024 * 1024)
                    if size_mb > max_mb:
                        excluded.append((fp, f"file is {size_mb:.0f} MB, exceeds {max_mb} MB limit"))
                        oversized.add(fp)
                except OSError:
                    pass
            searched_set -= oversized

        _PEEKDOCS_INTERNAL = {
            ".peekdocs.db", ".peekdocs.db-wal", ".peekdocs.db-shm",
            ".peekdocs_collection.json", ".peekdocsrc",
            "peekdocs_errors.log",
        }

        walker = os.walk(folder) if recursive else [(folder, [], os.listdir(folder))]
        for root, dirs, files in walker:
            for fname in files:
                filepath = os.path.join(root, fname)
                # Skip files that discover_files already includes
                if os.path.normcase(os.path.normpath(filepath)) in searched_set:
                    continue
                ext = os.path.splitext(fname)[1].lower()

                # Hidden file
                if fname.startswith("."):
                    if fname in _PEEKDOCS_INTERNAL:
                        excluded.append((filepath, "peekdocs internal file (hidden)"))
                    else:
                        excluded.append((filepath, "hidden file (starts with .)"))
                    continue

                # peekdocs output files
                if fname.startswith(RESULT_FILE_PREFIXES) or fname.startswith(("peekdocs_report_", "peekdocs_accumulated_")):
                    excluded.append((filepath, "peekdocs output file (prior search results)"))
                    continue
                if fname in _PEEKDOCS_INTERNAL:
                    excluded.append((filepath, "peekdocs internal file"))
                    continue

                # Unsupported file type
                if ext not in supported:
                    if ext in OCR_IMAGE_TYPES and not use_ocr:
                        excluded.append((filepath, f"image file ({ext}) — enable OCR to search"))
                    else:
                        excluded.append((filepath, f"unsupported file type ({ext or 'no extension'})"))
                    continue

                # Supported type but not in searched set — unknown reason
                excluded.append((filepath, "not included in search (unknown reason)"))
            if not recursive:
                break
        return excluded

    # ── File Inventory ────────────────────────────────────────



    def _show_error(self, message):
        """Display an error message in the status label and a modal dialog."""
        self.status_label.configure(
            text=message, text_color="red"
        )
        self.bell()
        messagebox.showerror("Error", message)



    def reset_form(self):
        """Reset all fields to their defaults."""
        self.search_entry.delete(0, "end")
        self.and_mode_var.set("off")
        if hasattr(self, "_sync_and_or_colors"):
            self._sync_and_or_colors()
        self.recursive_var.set("off")
        self.fuzzy_var.set("off")
        self.wildcard_var.set("off")
        self.ocr_var.set("off")
        self.regex_var.set("off")
        self.exclude_entry.delete(0, "end")
        self.file_types_entry.delete(0, "end")
        self.proximity_entry.delete(0, "end")
        self.context_before_entry.delete(0, "end")
        self.context_after_entry.delete(0, "end")
        self.cores_entry.delete(0, "end")
        self.max_matches_entry.delete(0, "end")
        self.max_matches_entry.insert(0, "1000")
        self.max_file_size_entry.delete(0, "end")
        self.max_file_size_entry.insert(0, "100")
        self.specific_files_entry.delete(0, "end")
        self.save_name_entry.delete(0, "end")
        self.append_name_entry.delete(0, "end")
        self.output_csv_var.set("off")
        self.output_json_var.set("off")
        self.output_pdf_var.set("off")
        self.output_html_var.set("off")
        self.index_search_var.set("off")
        self.inverse_var.set("off")
        self.expression_var.set("off")
        self.whole_word_var.set("off")
        self.timestamp_var.set("off")
        self.output_dir_entry.delete(0, "end")
        self.range_entry.delete(0, "end")
        self.refresh_interval_var.set("Off")
        self._on_refresh_interval_changed("Off")
        self.search_entry.configure(placeholder_text="Enter search terms...")
        self.status_label.configure(
            text="", text_color=("gray30", "gray70")
        )
        self._clear_action_buttons()
        self._hide_files_list()



    def _log_search_history(self, search_text, match_count, file_count, elapsed):
        """Append a search entry to the history file."""
        from datetime import datetime
        folder = self.folder_entry.get().strip()
        history_path = os.path.join(os.path.expanduser("~"), ".peekdocs_history.json")
        try:
            import json
            history = []
            if os.path.exists(history_path):
                with open(history_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
            entry = {
                "timestamp": datetime.now().isoformat(),
                "search_text": search_text,
                "folder": folder,
                "matches": match_count,
                "files": file_count,
                "elapsed": elapsed,
            }
            history.append(entry)
            # Keep last 200 entries
            history = history[-200:]
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
        except Exception:
            pass



    def _open_selected_file(self):
        """Open the selected file from the matched files list in the default app."""
        from peekdocs.gui._helpers import safe_open_file
        selection = self.files_listbox.curselection()
        if not selection:
            return
        filepath = self.matched_files[selection[0]][0]
        if not os.path.exists(filepath):
            self._show_error(f"File not found: {filepath}")
            return
        warning = safe_open_file(filepath)
        if warning:
            self._show_error(warning)



    def _hide_files_list(self):
        """Clear the matched files list."""
        self.matched_files = []
        self._excluded_files = []


