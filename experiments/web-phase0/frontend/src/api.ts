// Typed client for the peekdocs web backend.
// Mirrors the Pydantic models in backend/server.py.

const BACKEND = "http://127.0.0.1:8000";

/* ─── Search ─────────────────────────────────────────────────── */

export interface SearchRequest {
  terms: string[];
  directory: string;

  recursive?: boolean;
  use_whole_word?: boolean;
  use_index?: boolean;
  match_all?: boolean;

  use_fuzzy?: boolean;
  use_wildcard?: boolean;
  use_regex?: boolean;
  use_ocr?: boolean;
  expression?: string | null;

  exclude_terms?: string[] | null;
  file_types?: string[] | null;
  file_names?: string[] | null;

  context_before?: number;
  context_after?: number;
  proximity?: number;
  line_proximity?: number;

  cores?: number | null;
  max_file_size_mb?: number;
  range_filters?: string | null;

  write_reports?: boolean;
  output_txt?: boolean;
  output_docx?: boolean;
  output_csv?: boolean;
  output_json?: boolean;
  output_pdf?: boolean;
  output_html?: boolean;
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
  output_files: Record<string, string>; // format -> absolute path
  report_errors?: string[];
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status}: ${detail}`);
  }
  return (await res.json()) as T;
}

export async function runSearch(req: SearchRequest): Promise<SearchResponse> {
  const res = await fetch(`${BACKEND}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  return json<SearchResponse>(res);
}

/* ─── Folder / file picker ───────────────────────────────────── */

export async function pickFolder(): Promise<string> {
  const res = await fetch(`${BACKEND}/pick-folder`, { method: "POST" });
  const d = await json<{ path: string }>(res);
  return d.path;
}

export async function pickFile(): Promise<string> {
  const res = await fetch(`${BACKEND}/pick-file`, { method: "POST" });
  const d = await json<{ path: string }>(res);
  return d.path;
}

/* ─── Recent searches / saved searches ──────────────────────── */

export async function getHistory(): Promise<string[]> {
  const res = await fetch(`${BACKEND}/history`);
  const d = await json<{ history: string[] }>(res);
  return d.history;
}

export async function listSavedSearches(directory: string): Promise<string[]> {
  const res = await fetch(
    `${BACKEND}/saved-searches?directory=${encodeURIComponent(directory)}`
  );
  const d = await json<{ names: string[] }>(res);
  return d.names;
}

export async function loadSavedSearch(
  name: string,
  directory: string
): Promise<Partial<SearchRequest>> {
  const res = await fetch(
    `${BACKEND}/saved-searches/${encodeURIComponent(name)}?directory=${encodeURIComponent(directory)}`
  );
  const d = await json<{ name: string; params: Partial<SearchRequest> }>(res);
  return d.params;
}

export async function saveSavedSearch(
  name: string,
  directory: string,
  params: Partial<SearchRequest>
): Promise<void> {
  await fetch(`${BACKEND}/saved-searches`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, directory, params }),
  }).then(json);
}

export async function deleteSavedSearch(
  name: string,
  directory: string
): Promise<void> {
  await fetch(
    `${BACKEND}/saved-searches/${encodeURIComponent(name)}?directory=${encodeURIComponent(directory)}`,
    { method: "DELETE" }
  ).then(json);
}

/* ─── Settings ────────────────────────────────────────────────── */

export async function getDefaults(): Promise<Record<string, unknown>> {
  const res = await fetch(`${BACKEND}/settings/defaults`);
  return json<Record<string, unknown>>(res);
}

export async function saveDefaults(
  settings: Record<string, unknown>
): Promise<void> {
  await fetch(`${BACKEND}/settings/defaults`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ settings }),
  }).then(json);
}

export async function clearFactoryDefaults(): Promise<void> {
  await fetch(`${BACKEND}/settings/defaults`, { method: "DELETE" }).then(json);
}

/* ─── Open report ─────────────────────────────────────────────── */

export function reportUrl(fmt: string): string {
  return `${BACKEND}/report/${encodeURIComponent(fmt)}`;
}

/* ─── About ──────────────────────────────────────────────────── */

export interface AboutInfo {
  name: string;
  version: string;
  description: string;
  license: string;
  repo: string;
  author: string;
  web_backend_version: string;
}

export async function getAbout(): Promise<AboutInfo> {
  const res = await fetch(`${BACKEND}/about`);
  return json<AboutInfo>(res);
}

/* ─── Suites / Regex collections / System check ──────────────── */

export interface SuitesInfo {
  suites: Record<string, string[]>;
}

export async function listSuites(directory: string): Promise<SuitesInfo> {
  const res = await fetch(
    `${BACKEND}/suites?directory=${encodeURIComponent(directory)}`
  );
  return json<SuitesInfo>(res);
}

export async function runSuite(
  name: string,
  directory: string
): Promise<unknown> {
  const res = await fetch(`${BACKEND}/suites/${encodeURIComponent(name)}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ directory }),
  });
  return json(res);
}

export async function listRegexCollections(): Promise<{ collections: string[] }> {
  const res = await fetch(`${BACKEND}/regex-collections`);
  return json<{ collections: string[] }>(res);
}

export async function runRegexCollection(
  name: string,
  directory: string
): Promise<unknown> {
  const res = await fetch(
    `${BACKEND}/regex-collections/${encodeURIComponent(name)}/run`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ directory }),
    }
  );
  return json(res);
}

export async function getSystemCheck(): Promise<Record<string, unknown>> {
  const res = await fetch(`${BACKEND}/system-check`);
  return json<Record<string, unknown>>(res);
}

/* ─── Tools menu analyses ─────────────────────────────────────── */

export interface FileInventory {
  total_files: number;
  total_bytes: number;
  by_extension: Array<{ ext: string; count: number; bytes: number }>;
}

export async function getFileInventory(directory: string): Promise<FileInventory> {
  const res = await fetch(
    `${BACKEND}/tools/file-inventory?directory=${encodeURIComponent(directory)}`
  );
  return json<FileInventory>(res);
}

export interface AgeDistribution {
  buckets: Record<string, number>;
  total_files: number;
}

export async function getAgeDistribution(
  directory: string
): Promise<AgeDistribution> {
  const res = await fetch(
    `${BACKEND}/tools/age-distribution?directory=${encodeURIComponent(directory)}`
  );
  return json<AgeDistribution>(res);
}

export interface DuplicatesResult {
  groups: Array<{ hash: string; size: number; paths: string[] }>;
  wasted_bytes: number;
}

export async function getDuplicates(directory: string): Promise<DuplicatesResult> {
  const res = await fetch(
    `${BACKEND}/tools/duplicates?directory=${encodeURIComponent(directory)}`
  );
  return json<DuplicatesResult>(res);
}

export async function getLargeFiles(
  directory: string,
  limit = 50
): Promise<{ files: Array<{ path: string; size: number }> }> {
  const res = await fetch(
    `${BACKEND}/tools/large-files?directory=${encodeURIComponent(directory)}&limit=${limit}`
  );
  return json<{ files: Array<{ path: string; size: number }> }>(res);
}

export async function getEmptyFiles(
  directory: string
): Promise<{ files: string[] }> {
  const res = await fetch(
    `${BACKEND}/tools/empty-files?directory=${encodeURIComponent(directory)}`
  );
  return json<{ files: string[] }>(res);
}

export async function getRecentChanges(
  directory: string,
  days = 7
): Promise<{ files: Array<{ path: string; mtime: number }>; days: number }> {
  const res = await fetch(
    `${BACKEND}/tools/recent-changes?directory=${encodeURIComponent(directory)}&days=${days}`
  );
  return json<{ files: Array<{ path: string; mtime: number }>; days: number }>(
    res
  );
}

export async function getProtectedFiles(
  directory: string
): Promise<{ files: string[] }> {
  const res = await fetch(
    `${BACKEND}/tools/protected-files?directory=${encodeURIComponent(directory)}`
  );
  return json<{ files: string[] }>(res);
}

export async function getUnsearchableFiles(
  directory: string
): Promise<{
  categories: Record<string, { count: number; files: string[] }>;
}> {
  const res = await fetch(
    `${BACKEND}/tools/unsearchable-files?directory=${encodeURIComponent(directory)}`
  );
  return json<{
    categories: Record<string, { count: number; files: string[] }>;
  }>(res);
}
