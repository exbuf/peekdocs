"""peekdocs web — backend.

Wraps the existing peekdocs.search() Python API in a localhost-only
FastAPI endpoint that the React frontend consumes. CORS restricted to
the Vite dev server origin (http://localhost:5173). 127.0.0.1 bind
only — no external network surface.

Run with:
    cd experiments/web-phase0/backend
    source ../../../venv/bin/activate
    python server.py
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from peekdocs import search as peekdocs_search

app = FastAPI(title="peekdocs-web", version="0.0.2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    # Step 1: folder + Step 2: terms
    terms: List[str] = Field(..., description="Search terms (1 or more)")
    directory: str = Field(..., description="Absolute folder path to search")

    # Step 2 options row
    recursive: bool = False
    use_whole_word: bool = False
    use_index: bool = False
    match_all: bool = Field(False, description="True = AND mode, False = OR mode")

    # Advanced — search modes
    use_fuzzy: bool = False
    use_wildcard: bool = False
    use_regex: bool = False
    use_ocr: bool = False
    expression: Optional[str] = Field(
        None, description="Boolean expression e.g. '(a OR b) AND NOT c'"
    )

    # Advanced — filters
    exclude_terms: Optional[List[str]] = None
    file_types: Optional[List[str]] = None
    file_names: Optional[List[str]] = Field(
        None, description="Specific filenames (e.g. ['*.docx', 'budget*.pdf'])"
    )

    # Advanced — context & proximity
    context_before: int = 0
    context_after: int = 0
    proximity: int = 0
    line_proximity: int = 0

    # Advanced — limits
    cores: Optional[int] = None
    max_file_size_mb: int = 100
    range_filters: Optional[str] = Field(
        None, description="Range filter string e.g. 'amount:1000..5000'"
    )


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


@app.get("/")
def root() -> dict:
    return {
        "name": "peekdocs-web",
        "docs": "/docs",
        "endpoints": ["/search"],
    }


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest) -> SearchResponse:
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
    )


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
