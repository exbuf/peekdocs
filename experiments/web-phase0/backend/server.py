"""Phase 0 experiment — minimal FastAPI wrapper around peekdocs.search().

This is a throwaway architecture validation. It exposes ONE endpoint
(/search) over localhost-only HTTP, accepts a JSON request, calls the
existing peekdocs Python API, and returns a JSON response.

The goal is to answer one question: does the round-trip feel fast and
clean? If yes, the architecture is viable for the full project. If no,
the experiment dies here without polluting the production codebase.

Run with:
    cd experiments/web-phase0/backend
    python server.py

Then open http://127.0.0.1:8000/docs to see FastAPI's auto-generated
OpenAPI documentation, or start the frontend (../frontend) and point
your browser at http://localhost:5173.
"""
from __future__ import annotations

from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from peekdocs import search as peekdocs_search

app = FastAPI(title="peekdocs-web-phase0", version="0.0.1")

# CORS is restricted to the Vite dev server origin only. Production
# would tighten this further (session token, etc.) — Phase 0 is just
# proving the round-trip works.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    terms: List[str] = Field(..., description="Search terms (1 or more)")
    directory: str = Field(..., description="Absolute folder path to search")
    recursive: bool = False
    use_whole_word: bool = False
    use_index: bool = False
    match_all: bool = Field(False, description="True = AND mode, False = OR mode")


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
        "name": "peekdocs-web-phase0",
        "docs": "/docs",
        "endpoints": ["/search"],
    }


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest) -> SearchResponse:
    if not req.terms:
        raise HTTPException(status_code=400, detail="terms must not be empty")
    if not req.directory:
        raise HTTPException(status_code=400, detail="directory must not be empty")
    try:
        result = peekdocs_search(
            req.terms,
            directory=req.directory,
            recursive=req.recursive,
            use_whole_word=req.use_whole_word,
            use_index=req.use_index,
            match_all=req.match_all,
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
    print(" peekdocs Phase 0 backend")
    print("   API:       http://127.0.0.1:8000")
    print("   Docs:      http://127.0.0.1:8000/docs")
    print("   CORS:      http://localhost:5173 (Vite dev server only)")
    print("   Localhost: bound to 127.0.0.1 — no external network access")
    print("=" * 64)
    print()
    # host="127.0.0.1" — NOT 0.0.0.0. Localhost only.
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
