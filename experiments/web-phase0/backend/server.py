"""peekdocs web — backend.

Wraps the existing peekdocs Python API in a localhost-only FastAPI
server that the React frontend consumes. CORS restricted to the Vite
dev server origin only. 127.0.0.1 bind only — no external network
surface.

Run with:
    cd experiments/web-phase0/backend
    source ../../../venv/bin/activate
    python server.py
"""
from __future__ import annotations

import os
import json
import subprocess
import sys
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from peekdocs import (
    search as peekdocs_search,
    list_suites as api_list_suites,
    run_suite as api_run_suite,
    list_regex_collections as api_list_regex_collections,
    run_regex_collection as api_run_regex_collection,
)
from peekdocs import collection as pd_collection
from peekdocs.cli import _load_config, _save_config, _config_path
from peekdocs import reporter as pd_reporter

app = FastAPI(title="peekdocs-web", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


# ─── Module-level state ─────────────────────────────────────────────
# The last search's output files, indexed by format ("docx", "txt",
# "csv", "json", "pdf", "html"). The Open-report buttons in the GUI
# use these paths.
last_outputs: Dict[str, str] = {}


# ─── Pydantic models ────────────────────────────────────────────────


class SearchRequest(BaseModel):
    terms: List[str] = Field(..., description="Search terms (1 or more)")
    directory: str = Field(..., description="Absolute folder path to search")

    # Step 2 options row (now lives in Advanced)
    recursive: bool = False
    use_whole_word: bool = False
    use_index: bool = False
    match_all: bool = False

    # Advanced — search modes
    use_fuzzy: bool = False
    use_wildcard: bool = False
    use_regex: bool = False
    use_ocr: bool = False
    expression: Optional[str] = None

    # Advanced — filters
    exclude_terms: Optional[List[str]] = None
    file_types: Optional[List[str]] = None
    file_names: Optional[List[str]] = None

    # Advanced — context & proximity
    context_before: int = 0
    context_after: int = 0
    proximity: int = 0
    line_proximity: int = 0

    # Advanced — limits
    cores: Optional[int] = None
    max_file_size_mb: int = 100
    range_filters: Optional[str] = None

    # Output formats — selects which formats to write to disk. All
    # default ON in the web GUI (the user can opt out per format).
    write_reports: bool = Field(
        True, description="Master toggle for writing any report files to disk"
    )
    output_txt: bool = True
    output_docx: bool = True
    output_csv: bool = False
    output_json: bool = False
    output_pdf: bool = False
    output_html: bool = False


class MatchOut(BaseModel):
    file_dir: str
    filename: str
    line_num: int
    text: str


class SearchResponse(BaseModel):
    matches: List[MatchOut]
    files_searched: int
    skipped_files: int
    elapsed_seconds: float
    used_index: bool
    output_files: Dict[str, str]  # format -> absolute file path
    report_errors: List[str] = []  # per-format failures, if any


class SaveSearchRequest(BaseModel):
    directory: str
    name: str
    params: Dict[str, Any]


class SettingsBody(BaseModel):
    settings: Dict[str, Any]


# ─── Root ───────────────────────────────────────────────────────────


@app.get("/")
def root() -> dict:
    return {
        "name": "peekdocs-web",
        "version": "0.1.0",
        "endpoints": [
            "GET  /",
            "POST /search",
            "GET  /report/{fmt}",
            "POST /pick-folder",
            "GET  /history",
            "GET  /saved-searches?directory=…",
            "POST /saved-searches",
            "GET  /saved-searches/{name}?directory=…",
            "DELETE /saved-searches/{name}?directory=…",
            "GET  /settings/defaults",
            "POST /settings/defaults",
            "DELETE /settings/defaults",
            "GET  /suites?directory=…",
            "POST /suites/{name}/run",
            "GET  /regex-collections",
            "POST /regex-collections/{name}/run",
            "GET  /system-check",
            "GET  /tools/file-inventory?directory=…",
            "GET  /tools/age-distribution?directory=…",
            "GET  /tools/duplicates?directory=…",
            "GET  /tools/large-files?directory=…",
            "GET  /tools/empty-files?directory=…",
            "GET  /tools/recent-changes?directory=…",
            "GET  /tools/protected-files?directory=…",
            "GET  /tools/unsearchable-files?directory=…",
        ],
    }


# ─── Search ─────────────────────────────────────────────────────────


def _write_reports(
    req: SearchRequest, result
) -> tuple[Dict[str, str], List[str]]:
    """Write the requested formats next to the searched documents.

    Returns a tuple of (output_files_dict, errors_list). Output files
    is {format: absolute_path}; errors is a list of human-readable
    failure messages so the frontend can surface them rather than
    silently dropping a button.
    """
    written: Dict[str, str] = {}
    errors: List[str] = []

    if not req.write_reports:
        return written, errors

    output_dir = req.directory.split(";", 1)[0]  # first folder if multi
    if not os.path.isdir(output_dir):
        errors.append(f"output_dir not a directory: {output_dir}")
        return written, errors

    command_str = "peekdocs " + " ".join(req.terms)
    cpu_count = os.cpu_count() or 1
    report_mode = "ALL" if req.match_all else "ANY"

    txt_path = os.path.join(output_dir, "peekdocs_standard_results.txt")
    docx_path = os.path.join(output_dir, "peekdocs_standard_results.docx")

    # TXT — required for DOCX even if not explicitly requested, since
    # write_docx_report reads from the TXT file.
    need_txt = req.output_txt or req.output_docx
    if need_txt:
        try:
            pd_reporter.write_txt_report(
                txt_path,
                result.matches,
                result.files_searched,
                req.terms,
                command_str,
                report_mode,
                req.use_ocr,
                req.exclude_terms or [],
                bool(req.context_before or req.context_after),
                req.use_fuzzy,
                req.use_regex,
                req.use_wildcard,
                result.elapsed,
                req.cores or cpu_count,
                cpu_count,
                recursive=req.recursive,
                file_types=req.file_types,
                proximity=req.proximity,
                context_before=req.context_before,
                context_after=req.context_after,
                specific_files=req.file_names,
                use_index=bool(req.use_index),
                output_csv=req.output_csv,
                output_json=req.output_json,
                expression=req.expression,
                use_whole_word=req.use_whole_word,
                total_matches=len(result.matches),
            )
            if req.output_txt:
                written["txt"] = txt_path
        except Exception as e:
            errors.append(f"TXT: {type(e).__name__}: {e}")

    if req.output_docx:
        try:
            pd_reporter.write_docx_report(
                docx_path,
                txt_path,
                search_terms=req.terms,
                use_regex=req.use_regex,
                use_wildcard=req.use_wildcard,
                use_whole_word=req.use_whole_word,
                use_fuzzy=req.use_fuzzy,
                expression=req.expression,
            )
            written["docx"] = docx_path
        except Exception as e:
            errors.append(f"DOCX: {type(e).__name__}: {e}")

    # If TXT was only needed for DOCX, clean it up unless explicitly
    # requested.
    if need_txt and not req.output_txt and os.path.exists(txt_path):
        # Leave it — peekdocs's convention is to keep TXT next to DOCX,
        # so we leave it on disk but don't include it in output_files.
        # User can still download via the /report/txt endpoint if they
        # want it.
        pass

    if req.output_csv:
        try:
            p = os.path.join(output_dir, "peekdocs_standard_results.csv")
            pd_reporter.write_csv_report(p, result.matches)
            written["csv"] = p
        except Exception as e:
            errors.append(f"CSV: {type(e).__name__}: {e}")

    if req.output_json:
        try:
            p = os.path.join(output_dir, "peekdocs_standard_results.json")
            pd_reporter.write_json_report(
                p,
                result.matches,
                req.terms,
                report_mode,
                result.elapsed,
                len(result.files_searched),
            )
            written["json"] = p
        except Exception as e:
            errors.append(f"JSON: {type(e).__name__}: {e}")

    if req.output_pdf:
        try:
            p = os.path.join(output_dir, "peekdocs_standard_results.pdf")
            pd_reporter.write_pdf_report(
                p, result.matches, search_terms=req.terms
            )
            written["pdf"] = p
        except Exception as e:
            errors.append(f"PDF: {type(e).__name__}: {e}")

    if req.output_html:
        try:
            p = os.path.join(output_dir, "peekdocs_standard_results.html")
            pd_reporter.write_html_report(
                p, result.matches, search_terms=req.terms
            )
            written["html"] = p
        except Exception as e:
            errors.append(f"HTML: {type(e).__name__}: {e}")

    return written, errors


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest) -> SearchResponse:
    global last_outputs

    if not req.terms and not req.expression:
        raise HTTPException(
            status_code=400,
            detail="Either 'terms' or 'expression' must be provided",
        )
    if not req.directory:
        raise HTTPException(status_code=400, detail="directory must not be empty")

    try:
        result = peekdocs_search(
            req.terms,
            directory=req.directory,
            match_all=req.match_all,
            recursive=req.recursive,
            use_regex=req.use_regex,
            use_fuzzy=req.use_fuzzy,
            use_wildcard=req.use_wildcard,
            use_whole_word=req.use_whole_word,
            use_ocr=req.use_ocr,
            exclude_terms=req.exclude_terms,
            file_types=req.file_types,
            file_names=req.file_names,
            context_before=req.context_before,
            context_after=req.context_after,
            proximity=req.proximity,
            line_proximity=req.line_proximity,
            cores=req.cores,
            use_index=req.use_index,
            expression=req.expression,
            range_filters=req.range_filters,
            max_file_size_mb=req.max_file_size_mb,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Append to history.
    try:
        _append_history(" ".join(req.terms) if req.terms else (req.expression or ""))
    except Exception:
        pass

    # Write reports if requested.
    output_files, report_errors = _write_reports(req, result)
    last_outputs = output_files  # remember for /report/{fmt}

    return SearchResponse(
        matches=[
            MatchOut(
                file_dir=m.file_dir,
                filename=m.filename,
                line_num=m.line_num,
                text=m.text,
            )
            for m in result.matches
        ],
        files_searched=len(result.files_searched),
        skipped_files=len(result.skipped_files),
        elapsed_seconds=result.elapsed,
        used_index=result.used_index,
        output_files=output_files,
        report_errors=report_errors,
    )


# ─── Report files ───────────────────────────────────────────────────


@app.get("/report/{fmt}")
def get_report(fmt: str):
    path = last_outputs.get(fmt)
    if not path or not os.path.exists(path):
        raise HTTPException(
            status_code=404,
            detail=f"No {fmt.upper()} report available — run a search first with {fmt.upper()} selected",
        )
    media_types = {
        "txt": "text/plain",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "csv": "text/csv",
        "json": "application/json",
        "pdf": "application/pdf",
        "html": "text/html",
    }
    return FileResponse(
        path,
        media_type=media_types.get(fmt, "application/octet-stream"),
        filename=os.path.basename(path),
    )


# ─── Folder picker ──────────────────────────────────────────────────


@app.post("/pick-folder")
def pick_folder() -> dict:
    """Open a native folder picker via a subprocess running tkinter
    (avoids running Tk in the FastAPI event loop)."""
    code = (
        "import tkinter as tk\n"
        "from tkinter import filedialog\n"
        "root = tk.Tk()\n"
        "root.withdraw()\n"
        "root.attributes('-topmost', True)\n"
        "path = filedialog.askdirectory(title='Choose folder to search')\n"
        "print(path)\n"
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return {"path": result.stdout.strip()}
    except subprocess.TimeoutExpired:
        return {"path": ""}


@app.post("/pick-file")
def pick_file() -> dict:
    code = (
        "import tkinter as tk\n"
        "from tkinter import filedialog\n"
        "root = tk.Tk()\n"
        "root.withdraw()\n"
        "root.attributes('-topmost', True)\n"
        "path = filedialog.askopenfilename(title='Choose a single file to search')\n"
        "print(path)\n"
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return {"path": result.stdout.strip()}
    except subprocess.TimeoutExpired:
        return {"path": ""}


# ─── Recent search history ──────────────────────────────────────────


def _history_path() -> str:
    return os.path.join(os.path.expanduser("~"), ".peekdocs_history.json")


def _append_history(search_text: str) -> None:
    if not search_text:
        return
    path = _history_path()
    history: List[Dict[str, Any]] = []
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
    # Drop duplicates (most recent wins).
    history = [h for h in history if h.get("search_terms") != search_text]
    history.insert(0, {"search_terms": search_text})
    history = history[:100]
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception:
        pass


@app.get("/history")
def get_history() -> dict:
    path = _history_path()
    if not os.path.exists(path):
        return {"history": []}
    try:
        with open(path, encoding="utf-8") as f:
            history = json.load(f)
    except Exception:
        return {"history": []}
    return {
        "history": [
            entry.get("search_terms", "")
            for entry in history
            if entry.get("search_terms")
        ]
    }


# ─── Saved searches (per-folder) ────────────────────────────────────


@app.get("/saved-searches")
def list_saved_searches(directory: str = Query(...)) -> dict:
    if not os.path.isdir(directory):
        raise HTTPException(status_code=404, detail=f"directory not found: {directory}")
    data = pd_collection.load_collection(directory)
    return {"names": list((data.get("searches") or {}).keys())}


@app.get("/saved-searches/{name}")
def get_saved_search(name: str, directory: str = Query(...)) -> dict:
    if not os.path.isdir(directory):
        raise HTTPException(status_code=404, detail=f"directory not found: {directory}")
    params = pd_collection.get_search_params(directory, name)
    if params is None:
        raise HTTPException(status_code=404, detail=f"saved search not found: {name}")
    return {"name": name, "params": params}


@app.post("/saved-searches")
def save_search(req: SaveSearchRequest) -> dict:
    if not os.path.isdir(req.directory):
        raise HTTPException(status_code=404, detail=f"directory not found: {req.directory}")
    pd_collection.add_saved_search(req.directory, req.name, req.params)
    return {"ok": True, "name": req.name}


@app.delete("/saved-searches/{name}")
def delete_saved_search(name: str, directory: str = Query(...)) -> dict:
    if not os.path.isdir(directory):
        raise HTTPException(status_code=404, detail=f"directory not found: {directory}")
    pd_collection.remove_saved_search(directory, name)
    return {"ok": True, "name": name}


# ─── Settings (~/.peekdocsrc) ───────────────────────────────────────


@app.get("/settings/defaults")
def get_defaults() -> dict:
    return _load_config()


@app.post("/settings/defaults")
def post_defaults(body: SettingsBody) -> dict:
    _save_config(body.settings)
    return {"ok": True, "path": _config_path()}


@app.delete("/settings/defaults")
def delete_defaults() -> dict:
    """Restore factory settings by removing ~/.peekdocsrc."""
    path = _config_path()
    if os.path.exists(path):
        os.remove(path)
    return {"ok": True}


# ─── Suites ─────────────────────────────────────────────────────────


@app.get("/suites")
def get_suites(directory: str = Query(...)) -> dict:
    if not os.path.isdir(directory):
        raise HTTPException(status_code=404, detail=f"directory not found: {directory}")
    suites = api_list_suites(directory)
    return {"suites": suites}


class RunSuiteBody(BaseModel):
    directory: str


@app.post("/suites/{name}/run")
def run_suite(name: str, body: RunSuiteBody) -> dict:
    if not os.path.isdir(body.directory):
        raise HTTPException(status_code=404, detail=f"directory not found: {body.directory}")
    try:
        result = api_run_suite(name, directory=body.directory)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"suite not found: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "suite": result.suite,
        "total_matches": result.total_matches,
        "elapsed": result.elapsed,
        "search_results": [
            {
                "search_name": sr.search_name,
                "search_terms": sr.search_terms,
                "match_count": len(sr.matches),
                "files_count": len(sr.files_searched),
                "elapsed": sr.elapsed,
                "matches": [
                    {
                        "file_dir": m.file_dir,
                        "filename": m.filename,
                        "line_num": m.line_num,
                        "text": m.text,
                    }
                    for m in sr.matches[:200]
                ],
            }
            for sr in result.search_results
        ],
        "skipped_searches": result.skipped_searches,
    }


# ─── Regex collections ──────────────────────────────────────────────


@app.get("/regex-collections")
def get_regex_collections() -> dict:
    return {"collections": api_list_regex_collections()}


class RunRegexCollectionBody(BaseModel):
    directory: str


@app.get("/regex-collections/{name}/patterns")
def get_regex_collection_patterns(name: str) -> dict:
    """Return the patterns of a saved regex collection so the frontend
    can render checkboxes for the user to enable/disable."""
    rc_path = os.path.join(os.path.expanduser("~"), ".peekdocs_regex_collections.json")
    if not os.path.exists(rc_path):
        raise HTTPException(status_code=404, detail="no regex collections file yet")
    with open(rc_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if name not in data:
        raise HTTPException(status_code=404, detail=f"collection not found: {name}")
    coll = data[name]
    patterns = coll if isinstance(coll, list) else coll.get("patterns", [])
    return {
        "name": name,
        "patterns": [
            {
                "name": p.get("name", ""),
                "regex": p.get("regex", ""),
                "enabled": bool(p.get("enabled", False)),
            }
            for p in patterns
        ],
    }


class UpdatePatternsBody(BaseModel):
    patterns: List[Dict[str, Any]]


@app.put("/regex-collections/{name}/patterns")
def update_regex_collection_patterns(name: str, body: UpdatePatternsBody) -> dict:
    rc_path = os.path.join(os.path.expanduser("~"), ".peekdocs_regex_collections.json")
    if not os.path.exists(rc_path):
        raise HTTPException(status_code=404, detail="no regex collections file yet")
    with open(rc_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if name not in data:
        raise HTTPException(status_code=404, detail=f"collection not found: {name}")
    if isinstance(data[name], list):
        data[name] = body.patterns
    else:
        data[name]["patterns"] = body.patterns
    with open(rc_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return {"ok": True}


@app.post("/regex-collections/{name}/run")
def run_regex_collection(name: str, body: RunRegexCollectionBody) -> dict:
    if not os.path.isdir(body.directory):
        raise HTTPException(status_code=404, detail=f"directory not found: {body.directory}")
    try:
        result = api_run_regex_collection(name, directory=body.directory)
    except ValueError as e:
        # e.g. "Collection 'X' has no enabled patterns" — client problem,
        # surface as 400 so the frontend can show the right message.
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"collection not found: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "collection": result.collection,
        "total_matches": result.total_matches,
        "elapsed": result.elapsed,
        "pattern_results": [
            {
                "name": pr.name,
                "pattern": pr.pattern,
                "match_count": len(pr.matches),
                "files_count": len(pr.files_searched),
                "matches": [
                    {
                        "file_dir": m.file_dir,
                        "filename": m.filename,
                        "line_num": m.line_num,
                        "text": m.text,
                    }
                    for m in pr.matches[:200]
                ],
            }
            for pr in result.pattern_results
        ],
    }


# ─── System check (--check) ─────────────────────────────────────────


@app.get("/system-check")
def system_check() -> dict:
    """Run the equivalent of `peekdocs --check` and return as JSON."""
    import platform
    import sqlite3
    import shutil as _shutil
    import importlib.metadata as _meta
    from peekdocs import __version__ as pd_version

    def _pkg(name):
        try:
            return _meta.version(name)
        except Exception:
            return None

    free_b = _shutil.disk_usage(os.path.expanduser("~")).free
    free_gb = round(free_b / (1024 ** 3), 1)

    tesseract = _shutil.which("tesseract")
    tesseract_version = None
    if tesseract:
        try:
            result = subprocess.run(
                [tesseract, "--version"], capture_output=True, text=True, timeout=5
            )
            first = (result.stdout or result.stderr).splitlines()
            if first:
                tesseract_version = first[0]
        except Exception:
            tesseract_version = "unknown"

    return {
        "peekdocs_version": pd_version,
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "free_disk_gb": free_gb,
        "sqlite_version": sqlite3.sqlite_version,
        "tesseract_available": tesseract is not None,
        "tesseract_version": tesseract_version,
        "dependencies": {
            name: _pkg(name)
            for name in [
                "python-docx",
                "PyMuPDF",
                "odfpy",
                "openpyxl",
                "striprtf",
                "python-pptx",
                "EbookLib",
                "Pillow",
                "pytesseract",
                "rapidfuzz",
                "customtkinter",
                "olefile",
                "xlrd",
                "extract-msg",
                "py7zr",
                "rarfile",
                "fpdf2",
                "watchdog",
                "fastapi",
                "uvicorn",
            ]
        },
    }


# ─── Tools — read-only analysis features ────────────────────────────


def _walk_files(directory: str, recursive: bool = True) -> List[str]:
    """Walk files under directory and return absolute paths (skip
    peekdocs's own files and hidden files)."""
    out: List[str] = []
    for root, dirs, files in os.walk(directory):
        # Skip hidden dirs.
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in files:
            if fn.startswith("."):
                continue
            if (
                fn.startswith("peekdocs_")
                or fn == "peekdocs_errors.log"
            ):
                continue
            out.append(os.path.join(root, fn))
        if not recursive:
            break
    return out


@app.get("/tools/file-inventory")
def file_inventory(directory: str = Query(...)) -> dict:
    if not os.path.isdir(directory):
        raise HTTPException(status_code=404, detail=f"directory not found: {directory}")
    files = _walk_files(directory)
    total_bytes = 0
    by_ext: Dict[str, Dict[str, Any]] = {}
    for p in files:
        try:
            sz = os.path.getsize(p)
        except OSError:
            continue
        total_bytes += sz
        ext = os.path.splitext(p)[1].lower() or "<none>"
        entry = by_ext.setdefault(ext, {"count": 0, "bytes": 0})
        entry["count"] += 1
        entry["bytes"] += sz
    return {
        "total_files": len(files),
        "total_bytes": total_bytes,
        "by_extension": [
            {"ext": k, "count": v["count"], "bytes": v["bytes"]}
            for k, v in sorted(by_ext.items(), key=lambda kv: -kv[1]["bytes"])
        ],
    }


@app.get("/tools/age-distribution")
def age_distribution(directory: str = Query(...)) -> dict:
    """Bucket files by modification age."""
    import time

    if not os.path.isdir(directory):
        raise HTTPException(status_code=404, detail=f"directory not found: {directory}")
    files = _walk_files(directory)
    now = time.time()
    buckets = {"0-6m": 0, "6-12m": 0, "1-2y": 0, "2-5y": 0, "5-10y": 0, "10y+": 0}
    for p in files:
        try:
            mtime = os.path.getmtime(p)
        except OSError:
            continue
        age_days = (now - mtime) / 86400
        if age_days < 183:
            buckets["0-6m"] += 1
        elif age_days < 365:
            buckets["6-12m"] += 1
        elif age_days < 365 * 2:
            buckets["1-2y"] += 1
        elif age_days < 365 * 5:
            buckets["2-5y"] += 1
        elif age_days < 365 * 10:
            buckets["5-10y"] += 1
        else:
            buckets["10y+"] += 1
    return {"buckets": buckets, "total_files": len(files)}


@app.get("/tools/duplicates")
def duplicates(directory: str = Query(...)) -> dict:
    """Find duplicate files by SHA-256."""
    import hashlib

    if not os.path.isdir(directory):
        raise HTTPException(status_code=404, detail=f"directory not found: {directory}")
    files = _walk_files(directory)
    # Group by size first to skip the obvious non-duplicates.
    by_size: Dict[int, List[str]] = {}
    for p in files:
        try:
            sz = os.path.getsize(p)
        except OSError:
            continue
        by_size.setdefault(sz, []).append(p)
    groups: List[Dict[str, Any]] = []
    for sz, paths in by_size.items():
        if len(paths) < 2:
            continue
        by_hash: Dict[str, List[str]] = {}
        for p in paths:
            try:
                h = hashlib.sha256()
                with open(p, "rb") as f:
                    for chunk in iter(lambda: f.read(65536), b""):
                        h.update(chunk)
                by_hash.setdefault(h.hexdigest(), []).append(p)
            except OSError:
                continue
        for h, ps in by_hash.items():
            if len(ps) > 1:
                groups.append({"hash": h[:16], "size": sz, "paths": ps})
    return {
        "groups": groups,
        "wasted_bytes": sum(g["size"] * (len(g["paths"]) - 1) for g in groups),
    }


@app.get("/tools/large-files")
def large_files(directory: str = Query(...), limit: int = 50) -> dict:
    if not os.path.isdir(directory):
        raise HTTPException(status_code=404, detail=f"directory not found: {directory}")
    files = _walk_files(directory)
    sized: List[Dict[str, Any]] = []
    for p in files:
        try:
            sz = os.path.getsize(p)
            sized.append({"path": p, "size": sz})
        except OSError:
            continue
    sized.sort(key=lambda x: -x["size"])
    return {"files": sized[:limit]}


@app.get("/tools/empty-files")
def empty_files(directory: str = Query(...)) -> dict:
    if not os.path.isdir(directory):
        raise HTTPException(status_code=404, detail=f"directory not found: {directory}")
    out = []
    for p in _walk_files(directory):
        try:
            if os.path.getsize(p) == 0:
                out.append(p)
        except OSError:
            continue
    return {"files": out}


@app.get("/tools/recent-changes")
def recent_changes(directory: str = Query(...), days: int = 7) -> dict:
    import time

    if not os.path.isdir(directory):
        raise HTTPException(status_code=404, detail=f"directory not found: {directory}")
    cutoff = time.time() - days * 86400
    out: List[Dict[str, Any]] = []
    for p in _walk_files(directory):
        try:
            mtime = os.path.getmtime(p)
            if mtime >= cutoff:
                out.append({"path": p, "mtime": mtime})
        except OSError:
            continue
    out.sort(key=lambda x: -x["mtime"])
    return {"files": out, "days": days}


@app.get("/tools/protected-files")
def protected_files(directory: str = Query(...)) -> dict:
    """Detect password-protected files (PDF, Office docs, ZIP/7z/RAR).
    Heuristic: try to open a small bit and look for encryption markers."""
    if not os.path.isdir(directory):
        raise HTTPException(status_code=404, detail=f"directory not found: {directory}")
    out: List[str] = []
    for p in _walk_files(directory):
        ext = os.path.splitext(p)[1].lower()
        try:
            if ext == ".pdf":
                try:
                    import fitz
                    doc = fitz.open(p)
                    if doc.needs_pass:
                        out.append(p)
                    doc.close()
                except Exception:
                    pass
            elif ext in (".docx", ".xlsx", ".pptx"):
                # Office files are ZIP; check for encryption header.
                try:
                    with open(p, "rb") as f:
                        head = f.read(8)
                    if head.startswith(b"\xd0\xcf\x11\xe0"):
                        out.append(p)  # CFB header (encrypted Office)
                except Exception:
                    pass
            elif ext in (".zip", ".7z", ".rar"):
                # Lightweight check: just look at the file extension; the
                # full peekdocs scanner has the real logic.
                pass
        except Exception:
            continue
    return {"files": out}


@app.get("/tools/unsearchable-files")
def unsearchable_files(directory: str = Query(...)) -> dict:
    """Files peekdocs can't search: unsupported types, oversized, etc."""
    from peekdocs.constants import SUPPORTED_TYPES

    if not os.path.isdir(directory):
        raise HTTPException(status_code=404, detail=f"directory not found: {directory}")
    supported = {e.lower() for e in SUPPORTED_TYPES}
    categories = {
        "unsupported_type": [],
        "oversized": [],
        "empty": [],
    }
    max_size_b = 100 * 1024 * 1024  # 100 MB default
    for p in _walk_files(directory):
        try:
            sz = os.path.getsize(p)
        except OSError:
            continue
        ext = os.path.splitext(p)[1].lower()
        if sz == 0:
            categories["empty"].append(p)
            continue
        if sz > max_size_b:
            categories["oversized"].append(p)
            continue
        if ext and ext not in supported:
            categories["unsupported_type"].append(p)
    return {
        "categories": {
            k: {"count": len(v), "files": v[:50]} for k, v in categories.items()
        }
    }


# ─── Bookmarks ──────────────────────────────────────────────────────


def _bookmarks_path() -> str:
    return os.path.join(os.path.expanduser("~"), ".peekdocs_bookmarks.json")


@app.get("/bookmarks")
def list_bookmarks() -> dict:
    path = _bookmarks_path()
    if not os.path.exists(path):
        return {"bookmarks": []}
    try:
        with open(path, encoding="utf-8") as f:
            return {"bookmarks": json.load(f)}
    except Exception:
        return {"bookmarks": []}


# ─── About ──────────────────────────────────────────────────────────


# ─── Indexes ────────────────────────────────────────────────────────


@app.get("/indexes/info")
def index_info(directory: str = Query(...)) -> dict:
    from peekdocs import indexer as pd_idx

    if not os.path.isdir(directory):
        raise HTTPException(status_code=404, detail=f"directory not found: {directory}")
    db_path = pd_idx._db_path(directory)
    exists = pd_idx.index_exists(directory)
    size = os.path.getsize(db_path) if exists else 0
    return {"exists": exists, "path": db_path, "size_bytes": size}


class BuildIndexBody(BaseModel):
    directory: str
    recursive: bool = True
    use_ocr: bool = False


@app.post("/indexes/build")
def build_index(body: BuildIndexBody) -> dict:
    from peekdocs import indexer as pd_idx

    if not os.path.isdir(body.directory):
        raise HTTPException(status_code=404, detail=f"directory not found: {body.directory}")
    try:
        pd_idx.build_index(
            body.directory,
            recursive=body.recursive,
            use_ocr=body.use_ocr,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"ok": True}


@app.delete("/indexes")
def delete_index(directory: str = Query(...)) -> dict:
    from peekdocs import indexer as pd_idx

    if not os.path.isdir(directory):
        raise HTTPException(status_code=404, detail=f"directory not found: {directory}")
    pd_idx.clear_index(directory)
    return {"ok": True}


# ─── Diff snapshots ─────────────────────────────────────────────────


class DiffBody(BaseModel):
    old_path: str
    new_path: str


@app.post("/diff-snapshots")
def diff_snapshots(body: DiffBody) -> dict:
    """Compare two peekdocs JSON snapshots and return what's new,
    removed, changed, unchanged."""
    if not os.path.exists(body.old_path):
        raise HTTPException(status_code=404, detail=f"old_path missing: {body.old_path}")
    if not os.path.exists(body.new_path):
        raise HTTPException(status_code=404, detail=f"new_path missing: {body.new_path}")
    try:
        with open(body.old_path) as f:
            old = json.load(f)
        with open(body.new_path) as f:
            new = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"failed to parse JSON: {e}")

    def by_file(snapshot):
        out: Dict[str, int] = {}
        for m in snapshot.get("matches", []):
            fn = m.get("filename") or os.path.basename(m.get("file", ""))
            out[fn] = out.get(fn, 0) + 1
        return out

    old_files = by_file(old)
    new_files = by_file(new)

    new_set = set(new_files) - set(old_files)
    removed_set = set(old_files) - set(new_files)
    changed = []
    unchanged = []
    for f in set(old_files) & set(new_files):
        if old_files[f] != new_files[f]:
            changed.append({"filename": f, "old": old_files[f], "new": new_files[f]})
        else:
            unchanged.append({"filename": f, "count": old_files[f]})

    return {
        "new": [{"filename": f, "count": new_files[f]} for f in sorted(new_set)],
        "removed": [{"filename": f, "count": old_files[f]} for f in sorted(removed_set)],
        "changed": changed,
        "unchanged_summary": {"count": len(unchanged), "total_matches": sum(u["count"] for u in unchanged)},
    }


# ─── Schedule search command generator ──────────────────────────────


class ScheduleBody(BaseModel):
    kind: str  # "suite" or "regex-collection"
    name: str
    directory: str
    frequency: str  # "daily", "weekly", "monthly"
    os_target: str  # "unix" or "windows"


@app.post("/schedule-search/generate")
def schedule_search(body: ScheduleBody) -> dict:
    """Generate a ready-to-paste cron / Task Scheduler command."""
    if body.kind == "suite":
        flag = f"--suite {body.name!r}"
    elif body.kind == "regex-collection":
        flag = f"--regex-collection {body.name!r}"
    else:
        raise HTTPException(status_code=400, detail="kind must be 'suite' or 'regex-collection'")

    cmd_core = f"cd {body.directory!r} && peekdocs {flag} --timestamp"

    if body.os_target == "unix":
        schedule_lines = {
            "daily": "0 2 * * *",       # 2 AM daily
            "weekly": "0 2 * * 1",      # 2 AM Mondays
            "monthly": "0 2 1 * *",     # 2 AM first of month
        }
        cron_line = schedule_lines.get(body.frequency, "0 2 * * *")
        return {
            "command": f"{cron_line} {cmd_core}",
            "instructions": [
                "Open your crontab:    crontab -e",
                "Paste the line above at the bottom of the file.",
                "Save and exit. Verify with:    crontab -l",
            ],
        }

    # windows — Task Scheduler
    sched_args = {
        "daily": "/SC DAILY /ST 02:00",
        "weekly": "/SC WEEKLY /D MON /ST 02:00",
        "monthly": "/SC MONTHLY /D 1 /ST 02:00",
    }.get(body.frequency, "/SC DAILY /ST 02:00")
    task_name = f"peekdocs_{body.name.replace(' ', '_')}"
    cmd = (
        f'schtasks /CREATE /TN "{task_name}" '
        f"/TR \"powershell -Command \\\"{cmd_core}\\\"\" "
        f"{sched_args} /F"
    )
    return {
        "command": cmd,
        "instructions": [
            "Open PowerShell as Administrator.",
            "Paste the line above and press Enter.",
            "List your tasks with:    schtasks /QUERY /TN \"" + task_name + "\"",
        ],
    }


# ─── Wizard patterns ────────────────────────────────────────────────


@app.get("/wizard-patterns")
def wizard_patterns() -> dict:
    """Return WIZARD_PATTERNS for the Regex Wizard frontend modal."""
    from peekdocs.wizard_patterns import WIZARD_PATTERNS, WIZARD_CATEGORY_ORDER

    return {
        "categories": [
            {
                "name": cat,
                "patterns": [
                    {"name": p[0], "pattern": p[1]} for p in WIZARD_PATTERNS[cat]
                ],
            }
            for cat in WIZARD_CATEGORY_ORDER
        ],
    }


# ─── Regex tester ───────────────────────────────────────────────────


class RegexTestBody(BaseModel):
    pattern: str
    text: str
    case_sensitive: bool = False


@app.post("/regex-test")
def regex_test(body: RegexTestBody) -> dict:
    """Test a regex against a sample text. Returns positions and
    matched strings so the frontend can highlight."""
    import re

    flags = 0 if body.case_sensitive else re.IGNORECASE
    try:
        pat = re.compile(body.pattern, flags)
    except re.error as e:
        return {"error": str(e), "matches": []}
    matches = [
        {"start": m.start(), "end": m.end(), "text": m.group(0)}
        for m in pat.finditer(body.text)
    ]
    return {"matches": matches, "count": len(matches)}


# ─── peekdocs files (Clear Files / Clean Folder / View All) ─────────


@app.get("/peekdocs-files")
def peekdocs_files(directory: str = Query(...)) -> dict:
    """List every peekdocs-created file in the directory (and below)."""
    if not os.path.isdir(directory):
        raise HTTPException(status_code=404, detail=f"directory not found: {directory}")
    PREFIXES = ("peekdocs_", ".peekdocs")
    out: List[Dict[str, Any]] = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith(".") or d == ".peekdocs"]
        for fn in files:
            if any(fn.startswith(pref) for pref in PREFIXES):
                p = os.path.join(root, fn)
                try:
                    out.append({"path": p, "size": os.path.getsize(p)})
                except OSError:
                    pass
    out.sort(key=lambda x: x["path"])
    return {"files": out, "total_bytes": sum(f["size"] for f in out)}


class ClearFilesBody(BaseModel):
    directory: str
    include_index: bool = False
    include_saved_searches: bool = False  # .peekdocs_collection.json
    include_reports: bool = False  # peekdocs_report_*


@app.post("/peekdocs-files/clear")
def clear_files(body: ClearFilesBody) -> dict:
    """Delete peekdocs-generated files in a folder. Returns counts."""
    if not os.path.isdir(body.directory):
        raise HTTPException(status_code=404, detail=f"directory not found: {body.directory}")
    deleted: List[str] = []
    failed: List[str] = []

    def _maybe_rm(path: str):
        try:
            os.remove(path)
            deleted.append(path)
        except Exception as e:
            failed.append(f"{path}: {e}")

    for root, _, files in os.walk(body.directory):
        for fn in files:
            full = os.path.join(root, fn)
            # Standard / suite / regex result files
            if fn.startswith(
                ("peekdocs_standard_results.", "peekdocs_suite_results.", "peekdocs_regex_results.")
            ):
                _maybe_rm(full)
            elif fn == "peekdocs_errors.log":
                _maybe_rm(full)
            elif body.include_reports and fn.startswith(
                ("peekdocs_report_", "peekdocs_accumulated_")
            ):
                _maybe_rm(full)
            elif body.include_index and (
                fn == ".peekdocs.db" or fn.startswith(".peekdocs.db-")
            ):
                _maybe_rm(full)
            elif body.include_saved_searches and fn == ".peekdocs_collection.json":
                _maybe_rm(full)
    return {"deleted": deleted, "failed": failed, "count": len(deleted)}


# ─── i18n ───────────────────────────────────────────────────────────


@app.get("/i18n/{lang}")
def get_i18n(lang: str) -> dict:
    """Return the i18n strings for the requested language."""
    from peekdocs.i18n import _STRINGS, LANGUAGES

    if lang not in LANGUAGES:
        raise HTTPException(status_code=404, detail=f"unknown language: {lang}")
    return {"lang": lang, "strings": _STRINGS.get(lang, {})}


@app.get("/i18n")
def list_i18n() -> dict:
    from peekdocs.i18n import LANGUAGES

    return {"languages": LANGUAGES}


# ─── About (existing) ───────────────────────────────────────────────


@app.get("/about")
def about() -> dict:
    from peekdocs import __version__ as pd_version

    return {
        "name": "peekdocs",
        "version": pd_version,
        "description": (
            "Privacy-first local document search and analysis platform "
            "for Windows, macOS, and Linux."
        ),
        "license": "MIT",
        "repo": "https://github.com/exbuf/peekdocs",
        "author": "Robert D. Schoening",
        "web_backend_version": "0.1.0",
    }


# ─── Entrypoint ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    print()
    print("=" * 64)
    print(" peekdocs web backend")
    print("   API:       http://127.0.0.1:8000")
    print("   Docs:      http://127.0.0.1:8000/docs")
    print("   CORS:      http://localhost:5173 only")
    print("   Localhost: bound to 127.0.0.1 — no external network access")
    print("=" * 64)
    print()
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
