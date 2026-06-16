import { useMemo, useState } from "react";
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
import { runSearch, type Match, type SearchResponse } from "./api";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function App() {
  const [directory, setDirectory] = useState("");
  const [terms, setTerms] = useState("");
  const [recursive, setRecursive] = useState(true);
  const [wholeWord, setWholeWord] = useState(false);
  const [useIndex, setUseIndex] = useState(false);
  const [matchAll, setMatchAll] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SearchResponse | null>(null);

  async function onRun() {
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const r = await runSearch({
        terms: terms.split(/\s+/).filter(Boolean),
        directory,
        recursive,
        use_whole_word: wholeWord,
        use_index: useIndex,
        match_all: matchAll,
      });
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  // Top-10 files by match count for the Chart.js bar chart.
  const chartData = useMemo(() => {
    if (!result) return null;
    const byFile = new Map<string, number>();
    for (const m of result.matches) {
      byFile.set(m.filename, (byFile.get(m.filename) ?? 0) + 1);
    }
    const top = [...byFile.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);
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
  }, [result]);

  return (
    <div className="container">
      <header>
        <h1>👀 peekdocs</h1>
        <p className="sub">Phase 0 web experiment — round-trip + Chart.js</p>
      </header>

      <section className="search-form">
        <label>
          Folder
          <input
            type="text"
            placeholder="/absolute/path/to/folder"
            value={directory}
            onChange={(e) => setDirectory(e.target.value)}
          />
        </label>

        <label>
          Search terms
          <input
            type="text"
            placeholder="budget revenue"
            value={terms}
            onChange={(e) => setTerms(e.target.value)}
          />
        </label>

        <div className="options">
          <label>
            <input
              type="checkbox"
              checked={recursive}
              onChange={(e) => setRecursive(e.target.checked)}
            />
            Recursive
          </label>
          <label>
            <input
              type="checkbox"
              checked={wholeWord}
              onChange={(e) => setWholeWord(e.target.checked)}
            />
            Whole word
          </label>
          <label>
            <input
              type="checkbox"
              checked={useIndex}
              onChange={(e) => setUseIndex(e.target.checked)}
            />
            Use index
          </label>
          <label>
            <input
              type="checkbox"
              checked={matchAll}
              onChange={(e) => setMatchAll(e.target.checked)}
            />
            AND mode
          </label>
        </div>

        <button
          className="run-button"
          disabled={loading || !directory || !terms}
          onClick={onRun}
        >
          {loading ? "Searching…" : "Run Standard Search"}
        </button>
      </section>

      {error && <div className="error">Error: {error}</div>}

      {result && (
        <section className="results">
          <div className="summary">
            <strong>{result.matches.length}</strong> matches in{" "}
            <strong>
              {new Set(result.matches.map((m) => m.filename)).size}
            </strong>{" "}
            file(s) — searched <strong>{result.files_searched}</strong>{" "}
            file(s),{" "}
            <strong>{result.elapsed_seconds.toFixed(2)}s</strong>
            {result.used_index && (
              <span className="badge">indexed</span>
            )}
            {result.skipped_files > 0 && (
              <span className="muted">
                · {result.skipped_files} skipped
              </span>
            )}
          </div>

          {chartData && chartData.labels.length > 0 && (
            <div className="chart">
              <Bar
                data={chartData}
                options={{
                  responsive: true,
                  plugins: {
                    title: { display: true, text: "Matches per file (top 10)" },
                    legend: { display: false },
                  },
                  scales: {
                    y: { beginAtZero: true, ticks: { precision: 0 } },
                  },
                }}
              />
            </div>
          )}

          <ul className="matches">
            {result.matches.slice(0, 200).map((m: Match, i: number) => (
              <li key={i}>
                <span className="match-loc">
                  {m.filename}:{m.line_num}
                </span>
                <span className="match-text">{m.text}</span>
              </li>
            ))}
            {result.matches.length > 200 && (
              <li className="muted">
                … {result.matches.length - 200} more matches (preview capped at
                200)
              </li>
            )}
          </ul>
        </section>
      )}

      <footer>
        <p className="muted">
          Backend: <code>http://127.0.0.1:8000</code> · Frontend:{" "}
          <code>http://127.0.0.1:5173</code> · Local-only, no external network.
        </p>
      </footer>
    </div>
  );
}
