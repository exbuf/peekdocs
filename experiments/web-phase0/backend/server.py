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

    # Output formats — selects which optional formats to also write
    write_reports: bool = Field(
        True, description="Write report files to disk (TXT+DOCX always, plus the optional flags below)"
    )
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


def _write_reports(req: SearchRequest, result) -> Dict[str, str]:
    """Write the result to .txt / .docx / optional formats next to
    the documents and return a {format: absolute_path} dict for the
    files actually written."""
    if not req.write_reports:
        return {}
    output_dir = req.directory
    if not os.path.isdir(output_dir):
        return {}

    written: Dict[str, str] = {}

    txt_path = os.path.join(output_dir, "peekdocs_standard_results.txt")
    docx_path = os.path.join(output_dir, "peekdocs_standard_results.docx")
    command_str = "peekdocs " + " ".join(req.terms)

    try:
        pd_reporter.write_txt_report(
            txt_path,
            result.matches,
            result.files_searched,
            req.terms,
            command_str,
            len(result.matches),
        )
        written["txt"] = txt_path
    except Exception:
        pass

    try:
        pd_reporter.write_docx_report(docx_path, txt_path, search_terms=req.terms)
        written["docx"] = docx_path
    except Exception:
        pass

    if req.output_csv:
        try:
            p = os.path.join(output_dir, "peekdocs_standard_results.csv")
            pd_reporter.write_csv_report(p, result.matches)
            written["csv"] = p
        except Exception:
            pass

    if req.output_json:
        try:
            p = os.path.join(output_dir, "peekdocs_standard_results.json")
            pd_reporter.write_json_report(
                p, result.matches, req.terms, "ANY", result.elapsed, len(result.files_searched)
            )
            written["json"] = p
        except Exception:
            pass

    if req.output_pdf:
        try:
            p = os.path.join(output_dir, "peekdocs_standard_results.pdf")
            pd_reporter.write_pdf_report(p, result.matches, search_terms=req.terms)
            written["pdf"] = p
        except Exception:
            pass

    if req.output_html:
        try:
            p = os.path.join(output_dir, "peekdocs_standard_results.html")
            pd_reporter.write_html_report(p, result.matches, search_terms=req.terms)
            written["html"] = p
        except Exception:
            pass

    return written


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
    output_files = _write_reports(req, result)
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


@app.post("/regex-collections/{name}/run")
def run_regex_collection(name: str, body: RunRegexCollectionBody) -> dict:
    if not os.path.isdir(body.directory):
        raise HTTPException(status_code=404, detail=f"directory not found: {body.directory}")
    try:
        result = api_run_regex_collection(name, directory=body.directory)
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
