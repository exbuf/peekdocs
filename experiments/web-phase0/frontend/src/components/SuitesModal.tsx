import { useEffect, useState } from "react";
import Modal from "./Modal";
import { listSuites, runSuite } from "../api";

interface Props {
  directory: string;
  onClose: () => void;
}

interface SuiteRunResult {
  suite: string;
  total_matches: number;
  elapsed: number;
  search_results: Array<{
    search_name: string;
    search_terms: string[];
    match_count: number;
    files_count: number;
    elapsed: number;
  }>;
  skipped_searches: Array<[string, string]>;
}

export default function SuitesModal({ directory, onClose }: Props) {
  const [suites, setSuites] = useState<Record<string, string[]>>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState<string | null>(null);
  const [result, setResult] = useState<SuiteRunResult | null>(null);

  useEffect(() => {
    listSuites(directory)
      .then((d) => setSuites(d.suites))
      .catch((e) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, [directory]);

  async function onRunSuite(name: string) {
    setRunning(name);
    setError(null);
    setResult(null);
    try {
      const r = (await runSuite(name, directory)) as SuiteRunResult;
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(null);
    }
  }

  const names = Object.keys(suites);

  return (
    <Modal title="Search Suites" onClose={onClose} width={620}>
      <p className="muted small">
        Saved suites for: <code>{directory}</code>
      </p>

      {loading && <p>Loading…</p>}
      {error && <div className="modal-error">{error}</div>}

      {!loading && names.length === 0 && !error && (
        <p className="muted small">
          No suites saved for this folder. Suites are groups of saved searches
          that run together. Create them in the tkinter GUI's Search Suites
          popup (not yet wired here).
        </p>
      )}

      {names.length > 0 && !result && (
        <ul className="saved-search-list">
          {names.map((n) => (
            <li key={n}>
              <button className="link-btn" onClick={() => onRunSuite(n)}>
                {n}
              </button>
              <span className="muted small">
                {suites[n].length} search{suites[n].length === 1 ? "" : "es"}
              </span>
              {running === n && (
                <span className="muted small"> · running…</span>
              )}
            </li>
          ))}
        </ul>
      )}

      {result && (
        <div>
          <h4 style={{ marginTop: 16 }}>
            Suite "{result.suite}" — {result.total_matches} match
            {result.total_matches === 1 ? "" : "es"} ·{" "}
            {result.elapsed.toFixed(2)}s
          </h4>
          <ul className="saved-search-list">
            {result.search_results.map((sr) => (
              <li key={sr.search_name}>
                <span>
                  <strong>{sr.search_name}</strong>
                  <span className="muted small">
                    {" "}
                    · {sr.search_terms.join(" ")}
                  </span>
                </span>
                <span className="muted small">
                  {sr.match_count} match{sr.match_count === 1 ? "" : "es"} ·{" "}
                  {sr.files_count} file{sr.files_count === 1 ? "" : "s"} ·{" "}
                  {sr.elapsed.toFixed(2)}s
                </span>
              </li>
            ))}
          </ul>
          <button className="link-btn" onClick={() => setResult(null)}>
            ← back to suites
          </button>
        </div>
      )}

      <div className="modal-buttons">
        <button onClick={onClose}>Close</button>
      </div>
    </Modal>
  );
}
