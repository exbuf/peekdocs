# peekdocs — Phase 0 web experiment

A throwaway architecture validation for a possible React + Vite + Chart.js browser UI alongside the existing tkinter GUI. **Not production code.** Lives in `experiments/` deliberately so it can be deleted in seconds if the architecture doesn't feel right.

## What this validates

Exactly one question: **does the round-trip feel fast and clean?**

- Python backend wraps the existing `peekdocs.search()` in a localhost-only FastAPI endpoint.
- React frontend calls that endpoint, renders results in a list, and shows a Chart.js bar chart of matches-per-file.
- No production code is touched. No dependencies are added to `pyproject.toml`.

If the answer is **yes** → the architecture is viable for the full project (see Phase 1 in the strategy plan).
If the answer is **no** → delete `experiments/web-phase0/` and the production codebase is unaffected.

## Prerequisites

- **Python**: peekdocs venv (already exists at `../../venv`).
- **Node.js**: not installed yet. `brew install node` (installs both node and npm).

## One-time setup

```bash
# From the repo root
cd experiments/web-phase0

# Backend: install FastAPI + uvicorn into the existing peekdocs venv
source ../../venv/bin/activate
pip install -r backend/requirements.txt

# Frontend: install React + Vite + Chart.js
cd frontend
npm install
```

The `npm install` will fetch ~200 MB of node_modules into `frontend/node_modules/`. That's normal for the Vite/React ecosystem; the `.gitignore` excludes it.

## Running the experiment

Two terminals, one for each side:

### Terminal 1 — backend

```bash
cd experiments/web-phase0/backend
source ../../../venv/bin/activate
python server.py
```

You should see:

```
================================================================
 peekdocs Phase 0 backend
   API:       http://127.0.0.1:8000
   Docs:      http://127.0.0.1:8000/docs
   CORS:      http://localhost:5173 (Vite dev server only)
   Localhost: bound to 127.0.0.1 — no external network access
================================================================
```

The `/docs` URL gives you FastAPI's auto-generated OpenAPI explorer — useful for poking at the API directly without the React app.

### Terminal 2 — frontend

```bash
cd experiments/web-phase0/frontend
npm run dev
```

You should see:

```
  VITE v5.x ready in NNN ms
  ➜  Local:   http://127.0.0.1:5173/
```

Open that URL in any browser. The UI has:

- A folder input (absolute path)
- A search-terms input (space-separated)
- Four option toggles (recursive, whole word, use index, AND mode)
- A blue Run button
- After running: a summary line, a Chart.js bar chart of top-10 files by match count, and the matched lines

## What's deliberately missing in Phase 0

This is one endpoint, one screen. The full project would have:

- Suite management, Regex Search, Wizard
- WebSocket streaming for long searches
- Settings persistence
- All Tools-menu features
- Session-token auth on the API (Phase 0 relies on CORS + localhost binding only)
- i18n
- Bundled production build (Vite `build` + FastAPI static-file serving)

None of those are needed to answer the round-trip question.

## How to delete this experiment cleanly

```bash
rm -rf experiments/web-phase0/
# Backend dependencies installed into venv (fastapi, uvicorn) can stay
# or be removed:
source venv/bin/activate
pip uninstall fastapi uvicorn
```

The main `pyproject.toml` was never modified, so no `--force` is needed on any production install path.

## What to look at while running

Things worth paying attention to during the experiment:

1. **Does the first search round-trip feel snappy?** First impression matters.
2. **Does the chart render legibly on real data?** This is the strongest value-prop angle.
3. **Does the API shape feel awkward?** Pydantic + the existing `search()` kwargs map cleanly here; this is a leading indicator of how the full Phase 1 backend would feel.
4. **Does serving the React app over HTTP vs. opening the tkinter window feel different in any practical way?** The browser UX has real differences (URL sharing, browser zoom, dev tools) that might matter for the value calculation.

Once you've answered those, the Phase 0 experiment has done its job — proceed, defer, or delete.
