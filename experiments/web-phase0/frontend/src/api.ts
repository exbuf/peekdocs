// Typed client for the Phase 0 backend. Mirrors the Pydantic models
// in backend/server.py — keep these in sync.

const BACKEND = "http://127.0.0.1:8000";

export interface SearchRequest {
  terms: string[];
  directory: string;
  recursive?: boolean;
  use_whole_word?: boolean;
  use_index?: boolean;
  match_all?: boolean;
}

export interface Match {
  file_dir: string;
  filename: string;
  line_num: number;
  text: string;
}

export interface SearchResponse {
  matches: Match[];
  files_searched: number;
  skipped_files: number;
  elapsed_seconds: number;
  used_index: boolean;
}

export async function runSearch(req: SearchRequest): Promise<SearchResponse> {
  const res = await fetch(`${BACKEND}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status}: ${detail}`);
  }
  return (await res.json()) as SearchResponse;
}
