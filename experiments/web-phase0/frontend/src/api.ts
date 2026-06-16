// Typed client for the peekdocs web backend.
// Mirrors the Pydantic models in backend/server.py.

const BACKEND = "http://127.0.0.1:8000";

export interface SearchRequest {
  terms: string[];
  directory: string;

  // Step 2 options row
  recursive?: boolean;
  use_whole_word?: boolean;
  use_index?: boolean;
  match_all?: boolean;

  // Advanced — search modes
  use_fuzzy?: boolean;
  use_wildcard?: boolean;
  use_regex?: boolean;
  use_ocr?: boolean;
  expression?: string | null;

  // Advanced — filters
  exclude_terms?: string[] | null;
  file_types?: string[] | null;
  file_names?: string[] | null;

  // Advanced — context & proximity
  context_before?: number;
  context_after?: number;
  proximity?: number;
  line_proximity?: number;

  // Advanced — limits
  cores?: number | null;
  max_file_size_mb?: number;
  range_filters?: string | null;
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
