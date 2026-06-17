import { useEffect, useMemo, useState } from "react";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import type { SearchResponse } from "../api";
import { highlightLine, type HighlightContext } from "../highlight";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

interface ResultsPanelProps {
  loading: boolean;
  error: string | null;
  result: SearchResponse | null;
  highlight: HighlightContext;
}

const CAP_OPTIONS = [100, 500, 1000, 5000, 0] as const; // 0 = no cap
const CAP_KEY = "peekdocs.previewCap";

function loadCap(): number {
  try {
    const raw = localStorage.getItem(CAP_KEY);
    if (raw === null) return 500;
    const n = parseInt(raw, 10);
    return CAP_OPTIONS.includes(n as 100 | 500 | 1000 | 5000 | 0) ? n : 500;
  } catch {
    return 500;
  }
}

export default function ResultsPanel({
  loading,
  error,
  result,
  highlight,
}: ResultsPanelProps) {
  const [view, setView] = useState<"matches" | "files" | "excluded" | "chart">(
    "matches"
  );
  const [previewCap, setPreviewCap] = useState<number>(() => loadCap());

  useEffect(() => {
    try {
      localStorage.setItem(CAP_KEY, String(previewCap));
    } catch {
      // ignore
    }
  }, [previewCap]);

  const matchedFiles = useMemo(() => {
    if (!result) return [];
    const counts = new Map<string, number>();
    for (const m of result.matches) {
      counts.set(m.filename, (counts.get(m.filename) ?? 0) + 1);
    }
    return [...counts.entries()].sort((a, b) => b[1] - a[1]);
  }, [result]);

  const chartData = useMemo(() => {
    if (!matchedFiles.length) return null;
    const top = matchedFiles.slice(0, 10);
    return {
      labels: top.map(([fn]) => fn),
      datasets: [
        {
          label: "Matches",
          data: top.map(([, n]) => n),
          backgroundColor: "rgba(33, 150, 243, 0.7)",
          borderColor: "rgba(33, 150, 243, 1)",
          borderWidth: 1,
        },
      ],
    };
  }, [matchedFiles]);

  if (loading) {
    return (
      <div className="results-panel">
        <div className="status-row loading">Searching…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="results-panel">
        <div className="status-row error">Error: {error}</div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="results-panel">
        <div className="placeholder">
          <h3>Results Preview</h3>
          <p>Run a search to see matches here.</p>
          <p className="muted small">
            Configure folder and terms on the left, then click Run Standard
            Search. Matches and a Chart.js breakdown render in this pane.
          </p>
        </div>
      </div>
    );
  }

  const effectiveCap =
    previewCap === 0 ? result.matches.length : previewCap;
  const isCapped =
    previewCap !== 0 && result.matches.length > previewCap;

  return (
    <div className="results-panel">
      <div className="status-row">
        <strong>{result.matches.length}</strong> match
        {result.matches.length === 1 ? "" : "es"} in{" "}
        <strong>{matchedFiles.length}</strong> file
        {matchedFiles.length === 1 ? "" : "s"} · searched{" "}
        <strong>{result.files_searched}</strong> · {" "}
        <strong>{result.elapsed_seconds.toFixed(2)}s</strong>
        {result.used_index && <span className="badge">indexed</span>}
        {result.skipped_files > 0 && (
          <span className="muted small"> · {result.skipped_files} skipped</span>
        )}
      </div>

      <div className="preview-cap-row">
        <span className="muted small">
          {isCapped ? (
            <>
              Preview shows the first <strong>{previewCap.toLocaleString()}</strong> of{" "}
              <strong>{result.matches.length.toLocaleString()}</strong> matches.
              The cap keeps the browser responsive on big result sets — the full
              data is always in the DOCX / TXT / CSV / JSON / HTML reports next
              to your documents. To render more in-browser, raise the cap →
            </>
          ) : (
            <>
              All <strong>{result.matches.length.toLocaleString()}</strong> matches
              rendered. The cap (used when results exceed it) keeps the browser
              responsive on very large result sets. Adjust →
            </>
          )}
        </span>
        <select
          className="preview-cap-select"
          value={previewCap}
          onChange={(e) => setPreviewCap(parseInt(e.target.value, 10))}
          aria-label="Preview cap"
        >
          <option value={100}>100</option>
          <option value={500}>500</option>
          <option value={1000}>1,000</option>
          <option value={5000}>5,000</option>
          <option value={0}>No cap</option>
        </select>
      </div>

      <div className="results-tabs">
        <button
          className={view === "matches" ? "tab on" : "tab"}
          onClick={() => setView("matches")}
        >
          Matches
        </button>
        <button
          className={view === "files" ? "tab on" : "tab"}
          onClick={() => setView("files")}
        >
          Matched Files ({matchedFiles.length})
        </button>
        <button
          className={view === "chart" ? "tab on" : "tab"}
          onClick={() => setView("chart")}
        >
          Chart
        </button>
        <button
          className={view === "excluded" ? "tab on" : "tab"}
          onClick={() => setView("excluded")}
        >
          Excluded ({result.skipped_files})
        </button>
      </div>

      <div className="results-body">
        {view === "matches" && (
          <ul className="match-list">
            {result.matches.slice(0, effectiveCap).map((m, i) => (
              <li key={i}>
                <span className="match-loc">
                  {m.filename}:{m.line_num}
                </span>
                <span className="match-text">
                  {highlightLine(m.text, highlight)}
                </span>
              </li>
            ))}
            {isCapped && (
              <li className="muted small">
                … {(result.matches.length - effectiveCap).toLocaleString()} more
                hidden by the preview cap. The full set is in the report files.
              </li>
            )}
          </ul>
        )}

        {view === "files" && (
          <ul className="file-list">
            {matchedFiles.map(([fn, n]) => (
              <li key={fn}>
                <span className="match-loc">{fn}</span>
                <span className="muted small"> · {n} match{n === 1 ? "" : "es"}</span>
              </li>
            ))}
          </ul>
        )}

        {view === "chart" && chartData && (
          <div className="chart-wrap">
            <Bar
              data={chartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  title: { display: true, text: "Top 10 files by match count" },
                  legend: { display: false },
                },
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
              }}
            />
          </div>
        )}

        {view === "excluded" && (
          <div className="placeholder">
            <p className="muted small">
              Excluded-files detail isn't exposed by the backend yet — the
              count shows here (<strong>{result.skipped_files}</strong>) but
              the per-file list will come in Phase 1.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
