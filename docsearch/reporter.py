"""Report generation for docsearch (TXT, DOCX, CSV, JSON, append)."""

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

from docsearch.scanner import _wildcard_to_regex


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
                     search_elapsed, cores, cpu_count):
    """Write docsearch_results.txt report file.

    Returns (total_bytes, size_str) for use in console summary.
    """
    if os.path.exists(output_path):
        os.remove(output_path)
    with open(output_path, "w") as f:
        f.write("Program name: docsearch\n")
        f.write("Program Source: https://github.com/exbuf\n")
        f.write("Overview: Searches all supported file types in current directory for search terms.\n")
        f.write("Supported file types:\n")
        f.write(".cfg, .csv, .docx, .epub, .html, .ini, .json, .log, .md, .ods, .odp, .odt, .pdf, .pptx, .rst,\n")
        f.write(".rtf, .sql, .tex, .toml, .tsv, .txt, .xlsx, .xml, .yaml, .yml\n")
        if use_ocr:
            f.write("OCR image types: .bmp, .jpg, .jpeg, .png, .tif, .tiff\n")
        f.write(f"\nReport Generated On ==> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Command ==> {command_str}\n")
        f.write(f"Search Term(s) ==> {', '.join(search_terms)} (match: {report_mode})\n")
        if exclude_terms:
            f.write(f"Exclude Term(s) ==> {', '.join(exclude_terms)}\n")
        f.write(f"Hits ==> {len(matches)}\n")
        # Per-file match counts
        file_counts = {}
        for fd, fn, _ln, _tx in matches:
            key = (fd, fn)
            if key not in file_counts:
                file_counts[key] = 0
            file_counts[key] += 1
        for (_fd, fn), count in file_counts.items():
            f.write(f"  {fn}: {count}\n")
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
                if use_fuzzy:
                    wrapped = textwrap.fill(text, width=80)
                else:
                    highlighted = text
                    for term in search_terms:
                        if use_wildcard:
                            pattern = _wildcard_to_regex(term)
                        elif use_regex:
                            pattern = term
                        else:
                            pattern = re.escape(term)
                        highlighted = re.sub(pattern, lambda m: f"**{m.group()}**", highlighted, flags=re.IGNORECASE)
                    wrapped = textwrap.fill(highlighted, width=80)
            fc = file_counts.get((file_dir, filename), 1)
            f.write(f'Document: {filename} ({fc} match{"es" if fc != 1 else ""}), Line: {line_num}, Match:\n({file_dir})\n"{wrapped}"\n\n')

    return (total_bytes, size_str)


def write_docx_report(docx_path, txt_path):
    """Create docsearch_results.docx from the .txt report with yellow highlighting.

    Returns the Document object for further modification.
    """
    if os.path.exists(docx_path):
        os.remove(docx_path)
    result_doc = Document()
    with open(txt_path, "r") as f:
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
                # rest looks like "budget, revenue (match: ANY)"
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

            is_doc_line = line.startswith("Document:")
            parts = re.split(r"(\*\*.*?\*\*)", line)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    run = para.add_run(part[2:-2])
                    run.font.highlight_color = WD_COLOR_INDEX.YELLOW
                    if is_doc_line:
                        run.bold = True
                else:
                    run = para.add_run(part)
                    if is_doc_line:
                        run.bold = True
    result_doc.save(docx_path)
    return result_doc


def insert_file_sizes(txt_path, docx_path, result_doc):
    """Insert report file sizes into both txt and docx reports.

    Returns (txt_size, docx_size) in bytes.
    """
    txt_size = os.path.getsize(txt_path)
    docx_size = os.path.getsize(docx_path)
    sizes_line = f"Report File Sizes ==> docsearch_results.txt ({fmt_size(txt_size)}), docsearch_results.docx ({fmt_size(docx_size)})"

    # Update txt report
    with open(txt_path, "r") as f:
        content = f.read()
    content = content.replace(
        "\nCommand ==>",
        f"\n{sizes_line}\nCommand ==>",
        1,
    )
    with open(txt_path, "w") as f:
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


def write_csv_report(output_path, matches):
    """Write docsearch_results.csv."""
    if os.path.exists(output_path):
        os.remove(output_path)
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "folder", "line_number", "matched_text"])
        for file_dir, filename, line_num, text in matches:
            writer.writerow([filename, file_dir, line_num, _strip_highlights(text)])


def write_json_report(output_path, matches, search_terms, report_mode,
                      files_count, search_elapsed):
    """Write docsearch_results.json."""
    if os.path.exists(output_path):
        os.remove(output_path)
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
    with open(output_path, "w") as f:
        json.dump(json_data, f, indent=2)


def append_results(append_name, cwd, txt_path, docx_path):
    """Append current results to accumulated DO_NOT_SEARCH files."""
    append_txt_path = os.path.join(cwd, f"DO_NOT_SEARCH_ACCUMULATED_{append_name}.txt")
    append_docx_path = os.path.join(cwd, f"DO_NOT_SEARCH_ACCUMULATED_{append_name}.docx")
    with open(txt_path, "r") as src:
        results_content = src.read()
    with open(append_txt_path, "a") as dst:
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
