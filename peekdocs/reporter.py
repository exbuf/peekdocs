"""Report generation for peekdocs (TXT, DOCX, CSV, JSON, PDF, append, PII)."""

import csv
import json
import os
import re
import shutil
import textwrap
from copy import deepcopy
from datetime import datetime

from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.enum.text import WD_COLOR_INDEX
from docx.shared import Pt, RGBColor, Inches

from peekdocs.scanner import _wildcard_to_regex
from peekdocs.translator import translate_search


def fmt_size(b):
    """Format byte count as human-readable string."""
    if b >= 1_000_000:
        return f"{b / 1_000_000:.2f} MB"
    elif b >= 1_000:
        return f"{b / 1_000:.2f} KB"
    return f"{b} bytes"


def _strip_highlights(text):
    """Remove ** highlight markers from text."""
    return re.sub(r"\*\*(.+?)\*\*", r"\1", text)


def write_txt_report(output_path, matches, all_files, search_terms, command_str,
                     report_mode, use_ocr, exclude_terms, use_context,
                     use_fuzzy, use_regex, use_wildcard,
                     search_elapsed, cores, cpu_count,
                     inverse_files=None, recursive=False,
                     file_types=None, proximity=None,
                     context_before=0, context_after=0,
                     specific_files=None, use_index=False,
                     inverse=False, output_csv=False, output_json=False,
                     expression=None, use_whole_word=False,
                     total_matches=None, max_matches=None,
                     range_specs=None, index_meta=None):
    """Write peekdocs_results.txt report file.

    Returns (total_bytes, size_str) for use in console summary.
    """
    if os.path.exists(output_path):
        os.remove(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("Header:\n\n")
        f.write("Program name: peekdocs\n")
        f.write("Program Source: https://github.com/exbuf\n")
        f.write("Overview: Searches all supported file types in current directory for search terms.\n")
        f.write("Supported file types:\n")
        f.write(".7z, .bz2, .cfg, .csv, .doc, .docx, .eml, .epub, .gz, .html, .ini, .json, .log, .md, .msg,\n")
        f.write(".ods, .odp, .odt, .pdf, .ppt, .pptx, .pst, .rar, .rst, .rtf, .sql, .tar, .tex, .tgz, .toml,\n")
        f.write(".tsv, .txt, .xls, .xlsx, .xml, .yaml, .yml, .zip\n")
        if use_ocr:
            f.write("OCR image types: .bmp, .jpg, .jpeg, .png, .tif, .tiff\n")
        f.write(f"\nReport Generated On ==> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Command ==> {command_str}\n")
        translation = translate_search(
            search_terms, report_mode=report_mode,
            use_regex=use_regex, use_wildcard=use_wildcard,
            use_fuzzy=use_fuzzy, use_ocr=use_ocr, use_index=use_index,
            use_whole_word=use_whole_word,
            inverse=inverse, recursive=recursive,
            exclude_terms=exclude_terms,
            file_types=file_types, specific_files=specific_files,
            proximity=proximity,
            context_before=context_before, context_after=context_after,
            expression=expression,
            range_specs=range_specs,
        )
        f.write(f"Translation ==> {translation}\n")
        if expression:
            f.write(f"Search Expression ==> {expression} (mode: {report_mode})\n")
        else:
            f.write(f"Search Term(s) ==> {' '.join(search_terms)} (match: {report_mode})\n")
        if exclude_terms:
            f.write(f"Exclude Term(s) ==> {' '.join(exclude_terms)}\n")
        if total_matches is not None and total_matches > len(matches):
            f.write(f"Hits ==> {len(matches)} (of {total_matches:,} total — report capped at {max_matches:,}; use -m to change)\n")
        else:
            f.write(f"Hits ==> {len(matches)}\n")

        # ── Search Settings ──
        on_off = lambda v: "ON" if v else "OFF"
        f.write(f"\nSearch Settings:\n")
        f.write(f"  AND mode: {on_off(report_mode == 'ALL')}  |  Recursive: {on_off(recursive)}  |  Inverse: {on_off(inverse)}  |  Expression: {on_off(expression is not None)}\n")
        f.write(f"  Fuzzy: {on_off(use_fuzzy)}  |  Wildcard: {on_off(use_wildcard)}  |  Regex: {on_off(use_regex)}  |  Whole Word: {on_off(use_whole_word)}  |  OCR: {on_off(use_ocr)}\n")
        f.write(f"  Index: {on_off(use_index)}\n")
        if use_index and index_meta:
            f.write(f"  Index last updated: {index_meta.get('last_updated', index_meta.get('created_at', '?'))}"
                    f"  ({index_meta.get('file_count', '?')} files, {index_meta.get('line_count', '?')} lines)\n")
        if file_types:
            f.write(f"  File types: {file_types}\n")
        if specific_files:
            f.write(f"  Specific files: {specific_files}\n")
        if proximity:
            f.write(f"  Proximity: {proximity} words\n")
        if use_context:
            f.write(f"  Context: {context_before} line(s) before, {context_after} line(s) after\n")
        outputs = ["TXT", "DOCX"]
        if output_csv:
            outputs.append("CSV")
        if output_json:
            outputs.append("JSON")
        f.write(f"  Output formats: {', '.join(outputs)}\n\n")
        # Per-file match counts (used later for per-match headers)
        file_counts = {}
        for fd, fn, _ln, _tx in matches:
            key = (fd, fn)
            if key not in file_counts:
                file_counts[key] = 0
            file_counts[key] += 1
        f.write(f"Search Time ==> {search_elapsed:.2f} seconds, Cores used ==> {cores} of {cpu_count}\n")
        total_bytes = sum(os.path.getsize(f_path) for f_path in all_files)
        if total_bytes >= 1_000_000:
            size_str = f"{total_bytes / 1_000_000:.2f} MB"
        elif total_bytes >= 1_000:
            size_str = f"{total_bytes / 1_000:.2f} KB"
        else:
            size_str = f"{total_bytes} bytes"
        f.write(f"Files searched ==> {len(all_files)} ({size_str})\n")
        ext_counts = {}
        for fp in all_files:
            ext = os.path.splitext(fp)[1].lower()
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
        if ext_counts:
            tally = ", ".join(f"{ext}: {count}" for ext, count in ext_counts.items())
            f.write(f"File Types Searched ==> {tally}\n")
        f.write("\n")
        f.write("Results:\n\n")
        if inverse_files is not None:
            f.write(f"Files WITHOUT matches: {len(inverse_files)} (out of {len(all_files)} searched)\n\n")
            for fp in inverse_files:
                f.write(f"  {os.path.basename(fp)}\n")
                f.write(f"  ({os.path.dirname(fp)})\n\n")
            # Inverse reports only list files missing the term — no match lines
            return (total_bytes, size_str)
        prev_file = None
        for file_dir, filename, line_num, text in matches:
            current_file = os.path.join(file_dir, filename)
            if use_context and prev_file == current_file:
                f.write("---\n\n")
            prev_file = current_file
            if use_context:
                lines = text.split("\n")
                wrapped_lines = [textwrap.fill(line, width=80) if line else line for line in lines]
                wrapped = "\n".join(wrapped_lines)
            else:
                wrapped = textwrap.fill(text, width=80)
            fc = file_counts.get((file_dir, filename), 1)
            f.write(f'Document: {filename} ({fc} match{"es" if fc != 1 else ""}), Line: {line_num}, Match:\n({file_dir})\n"{wrapped}"\n\n')

    return (total_bytes, size_str)


def write_docx_report(docx_path, txt_path, search_terms=None,
                      use_regex=False, use_wildcard=False,
                      use_whole_word=False, use_fuzzy=False,
                      expression=None):
    """Create peekdocs_results.docx from the .txt report with yellow highlighting.

    Highlights matched terms directly using the search parameters rather than
    parsing markers from the text. Returns the Document object for further
    modification.
    """
    if os.path.exists(docx_path):
        os.remove(docx_path)

    # Build highlight patterns from search terms
    highlight_patterns = []
    if not use_fuzzy:
        if expression:
            from peekdocs.expr_parser import parse_expression, extract_positive_terms
            highlight_terms = extract_positive_terms(parse_expression(expression))
        elif search_terms:
            highlight_terms = search_terms
        else:
            highlight_terms = []
        for term in highlight_terms:
            if use_wildcard:
                highlight_patterns.append(_wildcard_to_regex(term))
            elif use_regex:
                highlight_patterns.append(term)
            elif use_whole_word:
                highlight_patterns.append(r'\b' + re.escape(term) + r'\b')
            else:
                highlight_patterns.append(re.escape(term))

    # Combine into one pattern for efficient matching
    combined_pattern = None
    if highlight_patterns:
        try:
            combined_pattern = re.compile("|".join(highlight_patterns), re.IGNORECASE)
        except re.error:
            combined_pattern = None

    def _add_highlighted_line(para, line, bold=False):
        """Add a line to a paragraph with yellow highlighting on matched terms."""
        if combined_pattern:
            parts = combined_pattern.split(line)
            matches = combined_pattern.findall(line)
            for i, part in enumerate(parts):
                if part:
                    run = para.add_run(part)
                    if bold:
                        run.bold = True
                if i < len(matches):
                    run = para.add_run(matches[i])
                    run.font.highlight_color = WD_COLOR_INDEX.YELLOW
                    if bold:
                        run.bold = True
        else:
            run = para.add_run(line)
            if bold:
                run.bold = True

    result_doc = Document()
    in_results = False
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            para = result_doc.add_paragraph()

            # Make URL a clickable hyperlink
            if line.startswith("Program Source: "):
                prefix = "Program Source: "
                url = line[len(prefix):]
                para.add_run(prefix)
                r_id = result_doc.part.relate_to(
                    url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True
                )
                hyperlink = OxmlElement("w:hyperlink")
                hyperlink.set(qn("r:id"), r_id)
                run_elem = OxmlElement("w:r")
                rPr = OxmlElement("w:rPr")
                color = OxmlElement("w:color")
                color.set(qn("w:val"), "0000FF")
                rPr.append(color)
                u = OxmlElement("w:u")
                u.set(qn("w:val"), "single")
                rPr.append(u)
                run_elem.append(rPr)
                text_elem = OxmlElement("w:t")
                text_elem.text = url
                run_elem.append(text_elem)
                hyperlink.append(run_elem)
                para._p.append(hyperlink)
                continue

            if line.startswith("Search Term(s) ==> "):
                prefix = "Search Term(s) ==> "
                rest = line[len(prefix):]
                match = re.match(r"(.+?)( \(match: [A-Z+]+\))$", rest)
                if match:
                    terms_str, mode_str = match.group(1), match.group(2)
                    para.add_run(prefix)
                    run = para.add_run(terms_str)
                    run.font.highlight_color = WD_COLOR_INDEX.BRIGHT_GREEN
                    para.add_run(mode_str)
                else:
                    para.add_run(line)
                continue

            if line in ("Header:", "Results:"):
                run = para.add_run(line)
                run.bold = True
                in_results = (line == "Results:")
                continue

            is_doc_line = line.startswith("Document:")
            if in_results and not is_doc_line and not line.startswith("(") and not line.startswith("Files WITHOUT"):
                # Match line in results section — apply highlighting
                _add_highlighted_line(para, line)
            elif is_doc_line:
                _add_highlighted_line(para, line, bold=True)
            else:
                para.add_run(line)

    result_doc.save(docx_path)
    return result_doc


def write_pii_scan_report(docx_path, scan_results, folder, elapsed, files_searched):
    """Generate a .docx report from PII scan results with yellow-highlighted matches.

    Each category gets a section with a severity header and per-file match details.
    Matched text is highlighted in yellow.
    """
    from peekdocs.sensitive_patterns import SEVERITY_COLORS, SEVERITY_ORDER

    if os.path.exists(docx_path):
        os.remove(docx_path)

    doc = Document()

    # Title
    title = doc.add_heading("Sensitive Data Scan Report", level=1)

    # Summary
    total = sum(r["match_count"] for r in scan_results)
    high = sum(r["match_count"] for r in scan_results if r["severity"] == "high")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    doc.add_paragraph(f"Folder: {folder}")
    doc.add_paragraph(f"Date: {now}")
    doc.add_paragraph(f"Files scanned: {files_searched}")
    doc.add_paragraph(f"Scan time: {elapsed:.1f}s")
    doc.add_paragraph(f"Total findings: {total}  ({high} high severity)")

    if total == 0:
        para = doc.add_paragraph()
        run = para.add_run("No sensitive data found.")
        run.font.color.rgb = RGBColor(0, 128, 0)
        run.bold = True
        # Fall through to the disclaimer + MIT License section so the
        # scope of the scan is documented even on a clean report.
        _write_pii_disclaimer_and_license(doc)
        doc.save(docx_path)
        return doc

    # Summary table
    doc.add_heading("Summary", level=2)
    hint = doc.add_paragraph()
    hint_run = hint.add_run(
        "Click a category name below to jump to its detail section. "
        "(On Windows, hold Ctrl and click.)"
    )
    hint_run.font.size = Pt(9)
    hint_run.italic = True
    hint_run.font.color.rgb = RGBColor(0x88, 0x88, 0x88)
    table = doc.add_table(rows=1, cols=4)
    table.style = "Light Grid Accent 1"
    hdr = table.rows[0].cells
    hdr[0].text = "Severity"
    hdr[1].text = "Category"
    hdr[2].text = "Matches"
    hdr[3].text = "Files"

    severity_rank = {s: i for i, s in enumerate(SEVERITY_ORDER)}
    # Separate built-in and custom results so custom patterns always
    # appear at the bottom of both the summary table and the details
    # section, where the user expects to find them.
    builtin_results = [r for r in scan_results if not r.get("is_custom")]
    custom_results = [r for r in scan_results if r.get("is_custom")]
    builtin_sorted = sorted(
        builtin_results,
        key=lambda r: (severity_rank.get(r["severity"], 99), -r["match_count"]),
    )
    custom_sorted = sorted(
        custom_results,
        key=lambda r: (severity_rank.get(r["severity"], 99), -r["match_count"]),
    )
    sorted_results = builtin_sorted + custom_sorted

    # Build bookmark names so the summary table can hyperlink to each
    # detail section.  Only categories with findings get a bookmark.
    _bookmark_names = {}  # result index → bookmark name
    _bookmark_id = [100]  # mutable counter for unique bookmark IDs

    def _add_bookmark(paragraph, name):
        """Insert a Word bookmark into *paragraph*."""
        bm_id = str(_bookmark_id[0])
        _bookmark_id[0] += 1
        bs = OxmlElement("w:bookmarkStart")
        bs.set(qn("w:id"), bm_id)
        bs.set(qn("w:name"), name)
        be = OxmlElement("w:bookmarkEnd")
        be.set(qn("w:id"), bm_id)
        paragraph._p.insert(0, bs)
        paragraph._p.append(be)

    def _add_internal_hyperlink(paragraph, anchor, text):
        """Append a clickable internal hyperlink (blue, underlined) to *paragraph*."""
        hyperlink = OxmlElement("w:hyperlink")
        hyperlink.set(qn("w:anchor"), anchor)
        run_elem = OxmlElement("w:r")
        rPr = OxmlElement("w:rPr")
        color = OxmlElement("w:color")
        color.set(qn("w:val"), "0563C1")
        rPr.append(color)
        underline = OxmlElement("w:u")
        underline.set(qn("w:val"), "single")
        rPr.append(underline)
        run_elem.append(rPr)
        t = OxmlElement("w:t")
        t.text = text
        t.set(qn("xml:space"), "preserve")
        run_elem.append(t)
        hyperlink.append(run_elem)
        paragraph._p.append(hyperlink)

    for idx, result in enumerate(sorted_results):
        bm_name = f"_pii_cat_{idx}"
        if result["match_count"] > 0:
            _bookmark_names[idx] = bm_name

        row = table.add_row().cells
        sev = SEVERITY_COLORS.get(result["severity"], SEVERITY_COLORS["info"])
        row[0].text = sev["label"]

        # Category cell — hyperlink to the detail section if findings exist
        cat_label = result["category"]
        if result.get("is_custom"):
            cat_label += "  (custom)"
        if idx in _bookmark_names:
            # Clear the default empty paragraph text and add a hyperlink
            cat_cell = row[1]
            cat_cell.text = ""
            _add_internal_hyperlink(cat_cell.paragraphs[0], bm_name, cat_label)
        else:
            row[1].text = cat_label

        row[2].text = str(result["match_count"])
        row[3].text = str(result["file_count"])

        # Color the severity cell
        if result["severity"] == "high" and result["match_count"] > 0:
            for paragraph in row[0].paragraphs:
                for run in paragraph.runs:
                    run.font.color.rgb = RGBColor(204, 0, 0)
                    run.bold = True

    # Prominent top-of-report disclaimer so readers see it before acting on
    # any findings. The full multi-point disclaimer is repeated at the end.
    doc.add_paragraph("")
    notice_heading = doc.add_paragraph()
    notice_run = notice_heading.add_run("IMPORTANT \u2014 READ BEFORE ACTING ON THIS REPORT")
    notice_run.bold = True
    notice_run.font.size = Pt(12)
    notice_run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)

    notice_body = doc.add_paragraph()
    notice_body_run = notice_body.add_run(
        "This report is a pattern-matching discovery aid, not a security product "
        "or a compliance certification. It can produce false positives (things "
        "that look like sensitive data but aren't) and false negatives (real "
        "sensitive data that doesn't match the built-in patterns). A clean or "
        "near-clean report does NOT prove that a file is free of sensitive data. "
        "Always review findings in context before taking action, and do not rely "
        "on this report alone for any security, privacy, or compliance decision. "
        "See the full disclaimer at the end of this report."
    )
    notice_body_run.font.size = Pt(10)
    notice_body_run.italic = True
    doc.add_paragraph("")

    # Detail sections per category with matches
    doc.add_heading("Details", level=2)

    # Map severity → RGB color for the category headings
    _heading_colors = {
        "high": RGBColor(0xCC, 0x00, 0x00),      # red
        "moderate": RGBColor(0xCC, 0x66, 0x00),  # amber
        "info": RGBColor(0x1F, 0x6A, 0xA5),      # blue
    }

    for idx, result in enumerate(sorted_results):
        if result["match_count"] == 0:
            continue

        sev = SEVERITY_COLORS.get(result["severity"], SEVERITY_COLORS["info"])

        # Visual separator above each category — blank line for breathing room
        doc.add_paragraph("")

        # Prominent category heading: level 2, large colored bold text
        # with a bracketed severity label prefix. Custom user-supplied
        # patterns also get a "(custom)" marker so readers can distinguish
        # them from peekdocs's built-in categories.
        cat_heading = doc.add_heading(level=2)
        heading_color = _heading_colors.get(result["severity"], _heading_colors["info"])
        heading_text = f"[{sev['label']}]  {result['category']}"
        if result.get("is_custom"):
            heading_text += "  (custom)"
        run = cat_heading.add_run(heading_text)
        run.bold = True
        run.font.size = Pt(18)
        run.font.color.rgb = heading_color

        # Insert a bookmark so the summary table hyperlink jumps here
        bm_name = _bookmark_names.get(idx)
        if bm_name:
            _add_bookmark(cat_heading, bm_name)

        # For custom patterns, add a prominent warning line immediately below
        # the heading so the reader cannot miss that this category came from
        # a user-supplied regex that peekdocs did not validate.
        if result.get("is_custom"):
            custom_notice = doc.add_paragraph()
            custom_notice_run = custom_notice.add_run(
                "USER-SUPPLIED CUSTOM PATTERN \u2014 not validated by peekdocs. "
                "Review findings carefully. See the Disclaimer section at the "
                "end of this report."
            )
            custom_notice_run.bold = True
            custom_notice_run.italic = True
            custom_notice_run.font.size = Pt(10)
            custom_notice_run.font.color.rgb = RGBColor(0x99, 0x66, 0x00)

        # Summary line under the heading (description + counts)
        summary_para = doc.add_paragraph()
        summary_run = summary_para.add_run(
            f"{result['description']} — {result['match_count']} match(es) in {result['file_count']} file(s)"
        )
        summary_run.font.size = Pt(11)
        summary_run.italic = True

        # Build highlight pattern from this category's regex
        regex = result.get("regex", "")
        combined_pattern = None
        if regex:
            try:
                combined_pattern = re.compile(regex, re.IGNORECASE)
            except re.error:
                pass

        for fname, info in sorted(result["files"].items()):
            line_nums = sorted(set(info["lines"]))[:20]
            lines_str = ", ".join(str(ln) for ln in line_nums)
            if len(info["lines"]) > 20:
                lines_str += "..."

            para = doc.add_paragraph()
            run = para.add_run(f"{fname}")
            run.bold = True
            para.add_run(f"  ({info['count']} match(es) — lines {lines_str})")

            # Add matched text with highlighting
            for match_text in info.get("match_texts", [])[:50]:
                para = doc.add_paragraph()
                if combined_pattern:
                    parts = combined_pattern.split(match_text)
                    matches = combined_pattern.findall(match_text)
                    for i, part in enumerate(parts):
                        if part:
                            para.add_run(part)
                        if i < len(matches):
                            run = para.add_run(matches[i])
                            run.font.highlight_color = WD_COLOR_INDEX.YELLOW
                else:
                    para.add_run(match_text)

    _write_pii_disclaimer_and_license(doc)

    doc.save(docx_path)
    return doc


def _write_pii_disclaimer_and_license(doc):
    """Append the full PII Scan disclaimer and MIT License text to *doc*.

    Used by write_pii_scan_report for both the no-findings and the
    has-findings code paths so the legal language always travels with
    the report, regardless of outcome.
    """
    _GRAY = RGBColor(0x55, 0x55, 0x55)

    doc.add_paragraph("")
    disc_heading = doc.add_paragraph()
    disc_heading_run = disc_heading.add_run("Disclaimer")
    disc_heading_run.bold = True
    disc_heading_run.font.size = Pt(12)
    disc_heading_run.font.color.rgb = _GRAY

    intro = doc.add_paragraph()
    intro_run = intro.add_run(
        "This report was generated by peekdocs's PII Scan feature. "
        "The PII Scan is a pattern-matching discovery aid, not a security "
        "product. Please read the following before relying on it."
    )
    intro_run.font.size = Pt(9)
    intro_run.font.color.rgb = _GRAY

    def _add_disclaimer_point(title, body):
        """Add one bullet with a bold lead-in and body text."""
        para = doc.add_paragraph(style=None)
        lead = para.add_run(f"\u2022 {title} ")
        lead.bold = True
        lead.font.size = Pt(9)
        lead.font.color.rgb = _GRAY
        body_run = para.add_run(body)
        body_run.font.size = Pt(9)
        body_run.font.color.rgb = _GRAY

    _add_disclaimer_point(
        "False positives happen.",
        "A 9-digit account number can look like an SSN. A tracking number can "
        "match the credit card pattern. The word 'password' can appear in a "
        "help document that contains no actual passwords. Always review "
        "findings in context before taking action."
    )
    _add_disclaimer_point(
        "False negatives happen.",
        "The PII Scan cannot find PII that does not match its built-in regex "
        "patterns. An SSN written as '123 45 6789' (spaces instead of dashes) "
        "may not be detected. A credit card number without separators may be "
        "missed. A foreign tax ID in a format peekdocs does not know will "
        "not be flagged. A clean report does NOT prove that a file is free of "
        "sensitive data \u2014 it proves only that peekdocs's specific patterns "
        "did not match anything in the file's extracted text."
    )
    _add_disclaimer_point(
        "Some file formats may not be fully extracted.",
        "peekdocs searches 46 file types, but extraction quality varies. A "
        "scanned PDF without OCR enabled will not surface any text. An image "
        "file is ignored unless OCR is on. Complex binary formats may yield "
        "partial text. Files that peekdocs could not read will not produce "
        "findings even if they contain PII."
    )
    _add_disclaimer_point(
        "Not a breach prevention tool.",
        "The PII Scan finds and reports only. It does not block, encrypt, "
        "move, delete, or otherwise secure any data. Any action taken based "
        "on this report is the reader's decision and responsibility."
    )
    _add_disclaimer_point(
        "Not compliance software.",
        "A clean scan does not certify HIPAA, GDPR, PCI-DSS, SOX, or any "
        "other regulatory compliance. The PII Scan can be one input to a "
        "review process, but it is not a substitute for professional "
        "compliance expertise or a formal audit."
    )
    _add_disclaimer_point(
        "Custom user-supplied patterns are your responsibility.",
        "If a finding in this report comes from the Custom Pattern you "
        "entered in the PII Scan configuration, peekdocs did not validate "
        "that your pattern correctly identifies the data you intended to "
        "find. A custom pattern may produce many false positives (if it is "
        "too broad) or miss the data you care about (if it is too narrow "
        "or written incorrectly). peekdocs never modifies, moves, or "
        "deletes the files it searches, so a bad pattern cannot harm your "
        "documents \u2014 but the interpretation of the results is yours."
    )
    _add_disclaimer_point(
        "Provided as-is under the MIT License.",
        "peekdocs comes with no warranty of any kind, express or implied. "
        "Users are solely responsible for how they interpret and act on "
        "these results. The full MIT License text is reproduced below."
    )

    summary = doc.add_paragraph()
    summary_run = summary.add_run(
        "In short: the PII Scan is a helpful set of eyes on your own files. "
        "It is not a guarantee, a certification, or a security system. Use "
        "the results as a starting point for your own review, not as a final "
        "answer."
    )
    summary_run.font.size = Pt(9)
    summary_run.italic = True
    summary_run.font.color.rgb = _GRAY

    # ── Full MIT License text ──
    doc.add_paragraph("")
    license_heading = doc.add_paragraph()
    license_heading_run = license_heading.add_run("MIT License")
    license_heading_run.bold = True
    license_heading_run.font.size = Pt(11)
    license_heading_run.font.color.rgb = _GRAY

    _MIT_LICENSE_PARAGRAPHS = [
        "Copyright (c) 2026 Robert D. Schoening",
        "Permission is hereby granted, free of charge, to any person obtaining "
        "a copy of this software and associated documentation files (the "
        "\"Software\"), to deal in the Software without restriction, including "
        "without limitation the rights to use, copy, modify, merge, publish, "
        "distribute, sublicense, and/or sell copies of the Software, and to "
        "permit persons to whom the Software is furnished to do so, subject to "
        "the following conditions:",
        "The above copyright notice and this permission notice shall be "
        "included in all copies or substantial portions of the Software.",
        "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, "
        "EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF "
        "MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. "
        "IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY "
        "CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, "
        "TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE "
        "SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.",
    ]
    for para_text in _MIT_LICENSE_PARAGRAPHS:
        lic_para = doc.add_paragraph()
        lic_run = lic_para.add_run(para_text)
        lic_run.font.size = Pt(8)
        lic_run.font.color.rgb = _GRAY


def insert_file_sizes(txt_path, docx_path, result_doc):
    """Insert report file sizes into both txt and docx reports.

    Returns (txt_size, docx_size) in bytes.
    """
    txt_size = os.path.getsize(txt_path)
    docx_size = os.path.getsize(docx_path)
    txt_name = os.path.basename(txt_path)
    docx_name = os.path.basename(docx_path)
    sizes_line = f"Report File Sizes ==> {txt_name} ({fmt_size(txt_size)}), {docx_name} ({fmt_size(docx_size)})"

    # Update txt report
    with open(txt_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = content.replace(
        "\nCommand ==>",
        f"\n{sizes_line}\nCommand ==>",
        1,
    )
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Update docx report — insert sizes paragraph after timestamp
    for i, para in enumerate(result_doc.paragraphs):
        if para.text.startswith("Report Generated On ==>"):
            new_para = OxmlElement("w:p")
            run_elem = OxmlElement("w:r")
            text_elem = OxmlElement("w:t")
            text_elem.text = sizes_line
            run_elem.append(text_elem)
            new_para.append(run_elem)
            para._p.addnext(new_para)
            break
    result_doc.save(docx_path)

    return (txt_size, docx_size)


def write_csv_report(output_path, matches, inverse_files=None):
    """Write peekdocs_results.csv."""
    if os.path.exists(output_path):
        os.remove(output_path)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if inverse_files is not None:
            writer.writerow(["filename", "folder"])
            for fp in inverse_files:
                writer.writerow([os.path.basename(fp), os.path.dirname(fp)])
        else:
            writer.writerow(["filename", "folder", "line_number", "matched_text"])
            for file_dir, filename, line_num, text in matches:
                writer.writerow([filename, file_dir, line_num, _strip_highlights(text)])


def write_json_report(output_path, matches, search_terms, report_mode,
                      files_count, search_elapsed, inverse_files=None):
    """Write peekdocs_results.json."""
    if os.path.exists(output_path):
        os.remove(output_path)

    if inverse_files is not None:
        json_data = {
            "search_terms": search_terms,
            "mode": report_mode,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "files_searched": files_count,
            "files_without_matches": len(inverse_files),
            "elapsed_seconds": round(search_elapsed, 2),
            "inverse_files": [
                {
                    "filename": os.path.basename(fp),
                    "folder": os.path.dirname(fp),
                }
                for fp in inverse_files
            ],
        }
    else:
        # Per-file match counts (ordered by first appearance)
        file_counts = {}
        for file_dir, filename, _ln, _tx in matches:
            key = (file_dir, filename)
            if key not in file_counts:
                file_counts[key] = 0
            file_counts[key] += 1
        matches_per_file = [
            {"filename": fn, "folder": fd, "matches": count}
            for (fd, fn), count in file_counts.items()
        ]

        json_data = {
            "search_terms": search_terms,
            "mode": report_mode,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "files_searched": files_count,
            "matches_found": len(matches),
            "matches_per_file": matches_per_file,
            "elapsed_seconds": round(search_elapsed, 2),
            "matches": [
                {
                    "filename": filename,
                    "folder": file_dir,
                    "line_number": line_num,
                    "matched_text": _strip_highlights(text),
                }
                for file_dir, filename, line_num, text in matches
            ],
        }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)


def _pdf_safe(text):
    """Replace Unicode characters that Helvetica can't render."""
    replacements = {
        '\u2018': "'", '\u2019': "'",   # smart single quotes
        '\u201c': '"', '\u201d': '"',   # smart double quotes
        '\u2013': '-', '\u2014': '--',  # en dash, em dash
        '\u2026': '...', '\u00a0': ' ', # ellipsis, nbsp
        '\u2022': '*', '\u2023': '>',   # bullets
        '\ufb01': 'fi', '\ufb02': 'fl', # ligatures
        '\u00b0': 'deg',               # degree sign
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Remove any remaining non-latin1 characters
    return text.encode('latin-1', errors='replace').decode('latin-1')


def _pdf_insert_highlighted(pdf, text, search_terms):
    """Insert text with search terms highlighted in orange background."""
    import re as _re
    if not search_terms:
        pdf.multi_cell(0, 5, text)
        return
    # Build pattern from search terms
    patterns = []
    for term in search_terms:
        patterns.append(_re.escape(term))
    try:
        pattern = _re.compile("|".join(patterns), _re.IGNORECASE)
    except _re.error:
        pdf.multi_cell(0, 5, text)
        return
    parts = pattern.split(text)
    found = pattern.findall(text)
    if not found:
        pdf.multi_cell(0, 5, text)
        return
    # Use cell for inline highlighting (multi_cell doesn't support mixed colors)
    x_start = pdf.get_x()
    page_width = pdf.w - pdf.r_margin - x_start
    for i, part in enumerate(parts):
        if part:
            pdf.set_text_color(0, 0, 0)
            pdf.write(5, part)
        if i < len(found):
            # Yellow background highlight
            pdf.set_fill_color(255, 255, 0)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(pdf.get_string_width(found[i]) + 1, 5, found[i], fill=True)
            pdf.set_fill_color(255, 255, 255)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)


def write_pdf_report(output_path, matches, search_terms=None,
                     report_mode="ANY", inverse_files=None):
    """Write peekdocs_results.pdf with highlighted matches."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "peekdocs Search Results", ln=True)
    pdf.ln(3)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, _pdf_safe(f"Search terms: {' '.join(search_terms or [])}"), ln=True)
    pdf.cell(0, 6, f"Mode: {report_mode}", ln=True)
    pdf.cell(0, 6, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.ln(5)

    if inverse_files is not None:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, f"Files WITHOUT matches: {len(inverse_files)}", ln=True)
        pdf.ln(3)
        pdf.set_font("Helvetica", "", 10)
        for fp in inverse_files:
            filename = os.path.basename(fp)
            dirname = os.path.dirname(fp)
            pdf.cell(0, 5, _pdf_safe(f"  {filename}"), ln=True)
            pdf.set_text_color(128, 128, 128)
            pdf.cell(0, 5, _pdf_safe(f"  ({dirname})"), ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(2)
    else:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, f"Matches found: {len(matches)}", ln=True)
        pdf.ln(3)

        prev_file = None
        for file_dir, filename, line_num, text in matches:
            current_file = os.path.join(file_dir, filename)
            if current_file != prev_file:
                pdf.ln(3)
                pdf.set_font("Helvetica", "B", 10)
                fc = sum(1 for fd, fn, _ln, _tx in matches
                         if os.path.join(fd, fn) == current_file)
                pdf.set_text_color(26, 115, 232)
                pdf.cell(0, 6, _pdf_safe(f"Document: {filename} ({fc} match{'es' if fc != 1 else ''})"), ln=True)
                pdf.set_text_color(128, 128, 128)
                pdf.set_font("Helvetica", "", 9)
                pdf.cell(0, 5, _pdf_safe(f"({file_dir})"), ln=True)
                pdf.set_text_color(0, 0, 0)
                prev_file = current_file

            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(128, 128, 128)
            pdf.cell(15, 5, f"Line {line_num}:")
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 10)
            clean_text = _pdf_safe(_strip_highlights(text))
            if len(clean_text) > 200:
                clean_text = clean_text[:197] + "..."
            _pdf_insert_highlighted(pdf, clean_text, [_pdf_safe(t) for t in (search_terms or [])])
            pdf.ln(1)

    pdf.output(output_path)


def append_results(append_name, output_dir, txt_path, docx_path):
    """Append current results to accumulated DO_NOT_SEARCH files."""
    append_txt_path = os.path.join(output_dir, f"DO_NOT_SEARCH_ACCUMULATED_{append_name}.txt")
    append_docx_path = os.path.join(output_dir, f"DO_NOT_SEARCH_ACCUMULATED_{append_name}.docx")
    with open(txt_path, "r", encoding="utf-8") as src:
        results_content = src.read()
    with open(append_txt_path, "a", encoding="utf-8") as dst:
        dst.write(results_content)
    if os.path.exists(append_docx_path):
        existing_doc = Document(append_docx_path)
        new_doc = Document(docx_path)
        body = existing_doc.element.body
        sect_pr = body.find(qn('w:sectPr'))
        for para in new_doc.paragraphs:
            new_elem = deepcopy(para._p)
            if sect_pr is not None:
                sect_pr.addprevious(new_elem)
            else:
                body.append(new_elem)
        existing_doc.save(append_docx_path)
    else:
        shutil.copy2(docx_path, append_docx_path)


# ── Suite Reports ──────────────────────────────────────────────
