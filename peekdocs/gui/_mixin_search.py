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
            self.process.terminate()
            self.search_button.configure(text="Search", fg_color="#76BA1B", hover_color="#5E9516", text_color="white")
            return
        # Cancel multi-folder search if running
        if hasattr(self, '_multi_folder_cancelled') and self._multi_folder_cancelled is False:
            self._multi_folder_cancelled = True
            self.status_label.configure(text="Cancelling multi-folder search...", text_color=("blue", "#66BBFF"))
            self.search_button.configure(text="Search", fg_color="#76BA1B", hover_color="#5E9516", text_color="white")
            return

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

        # Warn if search terms look like PII — they'll appear in report files
        import re as _re_pii
        _pii_patterns = [
            (r'\b\d{3}-\d{2}-\d{4}\b', "a Social Security number"),
            (r'\b(?:4\d{3}|5[1-5]\d{2}|3[47]\d{2}|6(?:011|5\d{2}))[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{1,4}\b', "a credit card number"),
            (r'\b\d{2}-\d{7}\b', "a Tax ID / EIN"),
        ]
        for pattern, desc in _pii_patterns:
            if _re_pii.search(pattern, search_text):
                from tkinter import messagebox
                proceed = messagebox.askyesno(
                    "Sensitive Search Term",
                    f"Your search term looks like it may contain {desc}.\n\n"
                    f"This term will appear in the report files "
                    f"(peekdocs_results.txt, .docx, etc.) written to disk. "
                    f"Consider using the PII Scan instead, which shows "
                    f"results on screen only and never writes a file.\n\n"
                    f"Continue with the search?",
                )
                if not proceed:
                    return
                break  # Only warn once

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

        # Record in recent searches (max 10, no duplicates, persisted)
        if search_text and search_text not in self._recent_searches:
            self._recent_searches.insert(0, search_text)
            self._recent_searches = self._recent_searches[:10]
        elif search_text in self._recent_searches:
            self._recent_searches.remove(search_text)
            self._recent_searches.insert(0, search_text)
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
        # Remove stale output files for formats not requested (skip when timestamps are on)
        if not self._last_ts_suffix:
            if self.output_csv_var.get() != "on":
                stale = os.path.join(self.results_dir, "peekdocs_results.csv")
                if os.path.exists(stale):
                    os.remove(stale)
            if self.output_json_var.get() != "on":
                stale = os.path.join(self.results_dir, "peekdocs_results.json")
                if os.path.exists(stale):
                    os.remove(stale)
            if self.output_pdf_var.get() != "on":
                stale = os.path.join(self.results_dir, "peekdocs_results.pdf")
                if os.path.exists(stale):
                    os.remove(stale)
            if self.output_html_var.get() != "on":
                stale = os.path.join(self.results_dir, "peekdocs_results.html")
                if os.path.exists(stale):
                    os.remove(stale)
        self.search_button.configure(text="Cancel", fg_color="red", hover_color="darkred")
        self.search_entry.configure(state="disabled")
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

        # If Use Index is on and the index was built with a different max file
        # size, warn the user that the index will be rebuilt during this search
        _will_rebuild = False
        if self.index_search_var.get() == "on":
            try:
                from peekdocs.indexer import index_status as _istatus
                status = _istatus(folder)
                if status:
                    stored = status.get("max_file_size_mb")
                    try:
                        current_mfs = int(self.max_file_size_entry.get().strip() or "100")
                    except ValueError:
                        current_mfs = 100
                    if stored is None:
                        # Old index from before this feature — will rebuild
                        _will_rebuild = True
                    else:
                        try:
                            if int(stored) != current_mfs:
                                _will_rebuild = True
                        except (ValueError, TypeError):
                            _will_rebuild = True
            except Exception:
                pass

        if _will_rebuild:
            self.status_label.configure(
                text=f"Rebuilding index with new Max File Size, then searching ({_term_label})...",
                text_color=("blue", "#66BBFF"),
            )
        else:
            self.status_label.configure(text=f"Searching ({_term_label})...", text_color=("blue", "#66BBFF"))
        self.search_start_time = time.time()
        self._start_elapsed_timer()

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
        self.search_button.configure(text="Cancel", fg_color="red", hover_color="darkred")
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
                output_csv=False,  # Don't write per-folder extras
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
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                proc = subprocess.Popen(
                    cmd, cwd=folder,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, encoding="utf-8", errors="replace", env=env,
                )
                stdout, stderr = proc.communicate()
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
                results_txt = os.path.join(folder, "peekdocs_results.txt")
                if os.path.exists(results_txt):
                    if is_inverse:
                        folder_matches = _parse_inverse_files(folder, "peekdocs_results.txt")
                    else:
                        folder_matches = _parse_matched_files(folder, "peekdocs_results.txt")
                    all_matched_files.extend(folder_matches)
            except Exception as e:
                failed_folders.append((folder, str(e)))
                combined_stdout.append(f"── {folder} — ERROR: {e} ──")

        elapsed = time.time() - start_time

        # Read all per-folder results BEFORE writing the combined file
        # (output_dir may be folders[0], so writing first would overwrite it)
        folder_contents = []
        for folder in folders:
            txt = os.path.join(folder, "peekdocs_results.txt")
            if os.path.exists(txt):
                try:
                    with open(txt, "r", encoding="utf-8", errors="replace") as src:
                        folder_contents.append((folder, src.read()))
                except Exception:
                    pass

        # Write combined results.txt to output_dir
        try:
            combined_txt_path = os.path.join(output_dir, "peekdocs_results.txt")
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
        self.search_button.configure(text="Search", fg_color="#76BA1B", hover_color="#5E9516", text_color="white")
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

        # Status line
        status = (f"{total_files} file(s) searched across {folder_count} folder(s) "
                  f"— Found {total_matches} match(es) in {elapsed:.1f}s")
        if fail_count:
            status += f"  ({fail_count} folder(s) failed — see preview)"
        self.status_label.configure(text=status, text_color=("blue", "#66BBFF"))

        # Populate matched files popup
        self._inverse_results = self.inverse_var.get() == "on"
        self.matched_files = all_matched_files
        self._show_action_buttons(inverse=self._inverse_results)

        # Show matched files link
        if self.matched_files:
            if self._inverse_results:
                link_text = f"{len(self.matched_files)} File(s) Without Matches"
                self._matched_files_link.configure(text=link_text, fg_color="#CC3333", hover_color="#AA2222")
            else:
                link_text = f"{len(self.matched_files)} Matched File(s)"
                self._matched_files_link.configure(text=link_text, fg_color="#FF6B35", hover_color="#E55A2B")
            self._matched_files_link.pack(side="left", padx=(5, 0))

        self._show_preview(combined_stdout)



    def _start_elapsed_timer(self):
        """Start the repeating timer that updates the elapsed-time display."""
        self._update_elapsed()



    def _update_elapsed(self):
        """Update the status label with the current elapsed search time."""
        if self.process is None and self.search_start_time is None:
            return
        if self.search_start_time is not None:
            elapsed = time.time() - self.search_start_time
            dots = "." * (int(elapsed) % 4)
            # Preserve a "Rebuilding index..." prefix if set, append elapsed time
            current = self.status_label.cget("text") or ""
            if current.startswith("Rebuilding index"):
                import re as _re
                new_text = _re.sub(r"\s*\(\d+s\)\s*$", "", current)
                new_text = f"{new_text} ({elapsed:.0f}s)"
                self.status_label.configure(text=new_text, text_color=("blue", "#66BBFF"))
            else:
                self.status_label.configure(
                    text=f"Searching{dots.ljust(3)}  ({elapsed:.0f}s elapsed)",
                    text_color=("blue", "#66BBFF"),
                )
        self.elapsed_timer_id = self.after(1000, self._update_elapsed)



    def _run_search(self, cmd, folder):
        """Run the peekdocs subprocess in a background thread and post results."""
        import re as _re
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
            self.process = subprocess.Popen(
                cmd,
                cwd=folder,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
            )
            stdout, stderr = self.process.communicate()
            returncode = self.process.returncode
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

        self.search_button.configure(text="Search", fg_color="#76BA1B", hover_color="#5E9516", text_color="white")
        self.search_entry.configure(state="normal")

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
            self._excluded_files_btn.configure(text=f"{_excl_count} Excluded Files")
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
            self.status_label.configure(
                text=status_text,
                text_color=("blue", "#66BBFF"),
            )
            # Post-search save (-s) if user filled in "Save as" field
            save_name = self.save_name_entry.get().strip()
            if save_name:
                save_cmd = [sys.executable, "-m", "peekdocs", "-s", save_name]
                try:
                    result = subprocess.run(save_cmd, cwd=self.results_dir, capture_output=True, text=True, encoding="utf-8", errors="replace")
                    if result.returncode != 0:
                        self._show_error(f"Save failed: {result.stdout.strip() or 'unknown error'}")
                        return
                except Exception as e:
                    self._show_error(f"Save failed: {e}")
                    return
            # Populate file list for the popup button
            ts = getattr(self, '_last_ts_suffix', '')
            results_fn = f"peekdocs_results_{ts}.txt" if ts else "peekdocs_results.txt"
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
                    link_text = f"{len(self.matched_files)} File(s) Without Matches"
                    self._matched_files_link.configure(text=link_text, fg_color="#CC3333", hover_color="#AA2222")
                else:
                    link_text = f"{len(self.matched_files)} Matched File(s)"
                    self._matched_files_link.configure(text=link_text, fg_color="#FF6B35", hover_color="#E55A2B")
                self._matched_files_link.pack(side="left", padx=(5, 0))
        elif returncode == 1:
            no_match_text = summary or "Search complete. No matches found."
            specific = self.specific_files_entry.get().strip()
            if specific:
                no_match_text += f"  [{specific}]"
            if _skip_count:
                no_match_text += f"  ({_skip_count} file(s) skipped — see Error Log)"
            self.status_label.configure(
                text=no_match_text,
                text_color=("blue", "#66BBFF"),
            )
            self._matched_files_link.configure(
                text="0 Matched File(s)",
                fg_color="#CC3333", hover_color="#AA2222",
            )
            self._matched_files_link.pack(side="left", padx=(5, 0))
            self._show_action_buttons()
        elif returncode == 2:
            # Check if results were produced despite the error (e.g., .docx generation failed)
            ts = getattr(self, '_last_ts_suffix', '')
            results_fn = f"peekdocs_results_{ts}.txt" if ts else "peekdocs_results.txt"
            results_path = os.path.join(self.results_dir or folder, results_fn)
            if os.path.exists(results_path):
                # Search succeeded but something else failed (likely report generation)
                self.status_label.configure(
                    text=summary or "Search complete (with warnings — check error log).",
                    text_color=("blue", "#66BBFF"),
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



    def _show_preview(self, stdout):
        """Populate the results preview pane from search output."""
        import re as _re
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")

        # If inverse search, show the list of files missing the term
        if self._inverse_results and self.matched_files:
            self.preview_text.tag_configure("inverse_header",
                font=("TkDefaultFont", 12, "bold"), foreground="#FF6B35")
            self.preview_text.tag_configure("inverse_file",
                font=("TkDefaultFont", 11))
            self.preview_text.insert("end",
                f"Files WITHOUT your search term ({len(self.matched_files)} file(s)) \u2014 Inverse box checked:\n\n",
                "inverse_header")
            for item in self.matched_files:
                filepath, filename = item[0], item[1]
                dirname = os.path.dirname(filepath)
                self.preview_text.insert("end", f"  {filename}\n", "inverse_file")
                self.preview_text.insert("end", f"  ({dirname})\n\n", "inverse_file")
            self.preview_text.configure(state="disabled")
            self.preview_text.see("1.0")
            self.preview_frame.grid(
                row=7, column=0, columnspan=3, padx=5, pady=(5, 0), sticky="nsew"
            )
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
                parts = highlight_pattern.split(line)
                matches = highlight_pattern.findall(line)
                for i, part in enumerate(parts):
                    if part:
                        self.preview_text.insert("end", part)
                    if i < len(matches):
                        self.preview_text.insert("end", matches[i], "match")
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
            results_path = os.path.join(self.results_dir, f"peekdocs_results{suffix}.txt")

        lines_added = 0
        max_preview_lines = 500  # Cap to keep the GUI responsive

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
                    if lines_added >= max_preview_lines:
                        self.preview_text.insert("end", f"\n... (showing first {max_preview_lines} lines — open the report for full results)\n")
                        break
                    if line.startswith("Document:"):
                        in_match_text = False
                        self.preview_text.insert("end", "\n")
                        self.preview_text.insert("end", line + "\n", "filename")
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

        self.preview_text.configure(state="disabled")
        self.preview_text.see("1.0")

        # Update count label
        match_count = len(self.matched_files)
        if self._inverse_results:
            self._preview_count_label.configure(
                text=f"{match_count} file(s) without matches")
        else:
            total_matches = sum(item[2] for item in self.matched_files)
            self._preview_count_label.configure(text=f"{total_matches} match(es) in {match_count} file(s)")

        # Show the preview frame
        self.preview_frame.grid(
            row=7, column=0, columnspan=3, padx=5, pady=(5, 0), sticky="nsew"
        )



    def _hide_preview(self):
        """Hide the results preview pane."""
        self.preview_frame.grid_remove()

    def _clear_preview(self):
        """Clear all text from the Results Preview pane."""
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.configure(state="disabled")
        self._preview_count_label.configure(text="")
        self.status_label.configure(
            text="Results Preview cleared.",
            text_color=("blue", "#66BBFF"),
        )

    def _delete_everything_now(self):
        """Immediately delete all result files, clear preview, and clear search history."""
        from tkinter import messagebox
        if not messagebox.askyesno(
            "Delete Everything Now",
            "This will immediately:\n\n"
            "\u2022 Delete all search result files (peekdocs_results.*, peekdocs_suite_results.*)\n"
            "\u2022 Delete the search index (.peekdocs.db) — contains extracted text of indexed files\n"
            "\u2022 Clear the Results Preview\n"
            "\u2022 Clear your search history and recent searches\n"
            "\u2022 Clear the search terms and folder fields\n\n"
            "Saved reports (peekdocs_report_*), accumulated reports, saved searches, "
            "and settings are not affected.\n\n"
            "Continue?",
        ):
            return

        deleted = 0
        # Collect all folders that may contain peekdocs files:
        # every folder searched this session, plus current state and safe dir.
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

        # Delete result files and search indexes from all folders
        for folder in folders_to_clean:
            if not os.path.isdir(folder):
                continue
            for fname in os.listdir(folder):
                if (fname.startswith("peekdocs_results") or
                        fname.startswith("peekdocs_suite_results")):
                    try:
                        os.remove(os.path.join(folder, fname))
                        deleted += 1
                    except OSError:
                        pass
            for idx_file in (".peekdocs.db", ".peekdocs.db-wal", ".peekdocs.db-shm"):
                idx_path = os.path.join(folder, idx_file)
                try:
                    if os.path.exists(idx_path):
                        os.remove(idx_path)
                        deleted += 1
                except OSError:
                    pass

        # Clear preview
        self._clear_preview()

        # Clear search history file
        history_path = os.path.join(os.path.expanduser("~"), ".peekdocs_history.json")
        try:
            if os.path.exists(history_path):
                os.remove(history_path)
        except OSError:
            pass

        # Clear recent searches and search terms from config
        try:
            from peekdocs.cli import _load_config, _save_config
            cfg = _load_config()
            cfg["recent_searches"] = []
            cfg["search_terms"] = ""
            _save_config(cfg)
            self._recent_searches = []
        except Exception:
            pass

        # Clear search terms and folder fields
        self.search_entry.delete(0, "end")
        self.folder_entry.delete(0, "end")

        # Also clear folder from saved config
        try:
            cfg = _load_config()
            cfg["folder"] = ""
            _save_config(cfg)
        except Exception:
            pass

        # Clear action buttons
        self._clear_action_buttons()

        self.status_label.configure(
            text=f"Deleted {deleted} file(s), cleared preview and search history.",
            text_color="green",
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

        # Check which report formats exist
        report_formats = {}
        if self.results_dir:
            suffix = f"_{self._last_ts_suffix}" if getattr(self, '_last_ts_suffix', '') else ""
            for fmt in ("txt", "docx", "csv", "json", "pdf", "html"):
                path = os.path.join(self.results_dir, f"peekdocs_results{suffix}.{fmt}")
                report_formats[fmt] = os.path.exists(path)

        has_any_report = any(report_formats.values())

        if not has_any_report:
            return

        # Pack report format buttons
        for fmt, btn in [
            ("docx", self.report_btn_docx),
            ("txt", self.report_btn_txt),
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
        self.report_delete_cb.pack(side="left", padx=(10, 0))
        self._delete_everything_btn.pack(side="left", padx=(10, 0))
        self.report_frame.grid(
            row=8, column=0, columnspan=3, padx=(10, 5), pady=(5, 5), sticky="w"
        )



    def _clear_action_buttons(self):
        """Hide all action buttons."""
        self.matched_files_button.grid_remove()
        self.report_frame.grid_remove()
        self.report_btn_txt.pack_forget()
        self.report_btn_docx.pack_forget()
        self.report_btn_csv.pack_forget()
        self.report_btn_json.pack_forget()
        self.report_btn_pdf.pack_forget()
        self.report_btn_html.pack_forget()
        self.report_delete_cb.pack_forget()
        self._delete_everything_btn.pack_forget()



    def _show_simple_popup(self, title, heading, message):
        """Show a simple informational popup with a consistent look and Close button."""
        import tkinter as tk
        popup, _dark = self._themed_toplevel()
        popup.title(title)
        popup.resizable(False, False)
        popup.geometry("520x280")
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - 520) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 280) // 2
        popup.geometry(f"+{x}+{y}")
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
        """Open the peekdocs error log file in the default text editor."""
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
        from peekdocs.gui._helpers import safe_open_file
        safe_open_file(error_log_path)



    def _clear_results_files(self):
        """Delete all peekdocs_results* files from the search folder."""
        folder = self.results_dir or self.folder_entry.get().strip()
        if not folder or not os.path.isdir(folder):
            self._show_error("Please select a folder first.")
            return
        # Find all peekdocs_results* files
        results_files = [
            f for f in os.listdir(folder)
            if f.startswith("peekdocs_results") and not f.startswith("peekdocs_results_dir")
        ]
        if not results_files:
            self.status_label.configure(text="No results files to clear.")
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
            self.status_label.configure(text=f"Deleted {deleted} results file(s).")
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
            self.status_label.configure(text="No error log to clear.")
            return
        from tkinter import messagebox
        if messagebox.askyesno("Clear Error Log",
                               f"Delete {os.path.basename(error_log_path)}?\n\nThis cannot be undone."):
            try:
                os.remove(error_log_path)
                self.status_label.configure(text="Error log cleared.")
            except OSError as e:
                self._show_error(f"Could not delete error log: {e}")



    def _clear_files(self):
        """Show a popup with checkboxes for every peekdocs-created file so the user can choose which to delete."""
        import tkinter as tk

        folder = self.folder_entry.get().strip()
        if not folder or not os.path.isdir(folder):
            self._show_error("Please select a folder first.")
            return

        # Categorize all peekdocs-created files
        # Each category: (label, description, files_list)
        categories = [
            ("Search results",
             "Overwritten after each search. Safe to delete.",
             []),
            ("Suite results",
             "Overwritten after each suite run. Safe to delete.",
             []),
            ("Saved reports (from 'Save report as:')",
             "Named copies you saved. Only delete if you no longer need them.",
             []),
            ("Accumulated reports (from 'Append to:')",
             "Results appended across multiple searches. Only delete if you no longer need them.",
             []),
            ("Error log",
             "Log of files that couldn't be read. Safe to delete.",
             []),
            ("Search index",
             "Built for faster searches. Can be rebuilt any time with Manage Indexes.",
             []),
        ]

        for root, dirs, files in os.walk(folder):
            for fname in files:
                filepath = os.path.join(root, fname)
                if fname.startswith("peekdocs_suite_results"):
                    categories[1][2].append(filepath)
                elif fname.startswith("peekdocs_results"):
                    categories[0][2].append(filepath)
                elif fname.startswith("peekdocs_accumulated_"):
                    categories[3][2].append(filepath)
                elif fname.startswith("peekdocs_report_"):
                    categories[2][2].append(filepath)
                elif fname == "peekdocs_errors.log":
                    categories[4][2].append(filepath)
                elif fname in (".peekdocs.db", ".peekdocs.db-wal", ".peekdocs.db-shm"):
                    categories[5][2].append(filepath)

        all_files = []
        for _, _, cat_files in categories:
            all_files.extend(cat_files)

        if not all_files:
            self.status_label.configure(text="No peekdocs files found to clear.")
            return

        win, _dark = self._themed_toplevel()
        win.title("Clear Files")
        win.resizable(True, True)
        win.geometry("700x500")
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - 700) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 500) // 2
        win.geometry(f"+{x}+{y}")

        _sf = self._scaled_font

        tk.Label(
            win, text="Clear peekdocs Files", font=_sf(14, "bold"),
        ).pack(anchor="w", padx=12, pady=(10, 2))
        tk.Label(
            win, text="Check the files you want to delete. Your original documents, saved searches, "
                      "and settings are never shown here and cannot be deleted.",
            font=_sf(10), fg="gray", wraplength=660, justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 8))

        # Scrollable frame for checkboxes
        list_frame = tk.Frame(win)
        list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 5))

        canvas = tk.Canvas(list_frame, highlightthickness=0)
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        check_vars = []  # list of (BooleanVar, filepath)

        for cat_name, cat_desc, cat_files in categories:
            if not cat_files:
                continue
            tk.Label(inner, text=cat_name, font=_sf(11, "bold")).pack(anchor="w", pady=(8, 0))
            tk.Label(inner, text=cat_desc, font=_sf(9), fg="gray").pack(anchor="w", padx=(4, 0), pady=(0, 2))
            for filepath in sorted(cat_files):
                var = tk.BooleanVar(value=False)
                rel = os.path.relpath(filepath, folder)
                try:
                    size = os.path.getsize(filepath)
                    size_str = f" ({size:,} bytes)" if size < 1_000_000 else f" ({size / 1_000_000:.1f} MB)"
                except OSError:
                    size_str = ""
                cb = tk.Checkbutton(
                    inner, variable=var,
                    text=f"{rel}{size_str}",
                    font=_sf(10), anchor="w",
                )
                cb.pack(anchor="w", padx=(16, 0))
                check_vars.append((var, filepath))

        # Select All / Deselect All / Delete / Close
        btn_frame = tk.Frame(win)
        btn_frame.pack(fill="x", padx=12, pady=(5, 10))

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
            from tkinter import messagebox
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
            self.status_label.configure(text=f"Deleted {deleted} file(s).")
            self._hide_preview()
            self._clear_action_buttons()

        ctk.CTkButton(btn_frame, text="Select All", width=80, font=ctk.CTkFont(size=12), command=_select_all).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="Deselect All", width=90, font=ctk.CTkFont(size=12), command=_deselect_all).pack(side="left", padx=2)
        ctk.CTkButton(
            btn_frame, text="Delete Selected", width=120,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#CC3333", hover_color="#AA2222",
            command=_delete_selected,
        ).pack(side="left", padx=(20, 2))
        ctk.CTkButton(
            win, text="Close", width=80,
            fg_color="transparent", text_color=("gray30", "gray70"),
            hover_color=("gray90", "gray25"),
            font=ctk.CTkFont(size=12), command=win.destroy,
        ).pack(pady=(0, 10))

        self._apply_dark_theme(win)

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
                # Search result files
                if fname.startswith("peekdocs_results"):
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
        suffix = f"_{self._last_ts_suffix}" if getattr(self, '_last_ts_suffix', '') else ""
        path = os.path.join(self.results_dir, f"peekdocs_results{suffix}.{fmt}")
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
                if fname.startswith("peekdocs_results") or fname.startswith(("peekdocs_report_", "peekdocs_accumulated_")):
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
        self.cores_entry.insert(0, str(self._default_cores))
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


