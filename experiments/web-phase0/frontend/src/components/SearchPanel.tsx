import type { SearchRequest } from "../api";
import AdvancedOptions from "./AdvancedOptions";

interface SearchPanelProps {
  params: SearchRequest;
  setParams: (next: Partial<SearchRequest>) => void;
  loading: boolean;
  onRun: () => void;

  // Output-format checkboxes — passed through to AdvancedOptions
  // (they live in the Output Formats section there now).
  outputCsv: boolean;
  setOutputCsv: (v: boolean) => void;
  outputJson: boolean;
  setOutputJson: (v: boolean) => void;
  outputPdf: boolean;
  setOutputPdf: (v: boolean) => void;
  outputHtml: boolean;
  setOutputHtml: (v: boolean) => void;
  deleteOnClose: boolean;
  setDeleteOnClose: (v: boolean) => void;
}

const stub = (msg: string) => () =>
  alert(`${msg}\n\n(Stub — Phase 1 wires this up.)`);

export default function SearchPanel(p: SearchPanelProps) {
  return (
    <div className="left-pane-body">
      {/* Step 1 — folder */}
      <section className="step-row">
        <span className="step-label">Step 1</span>
        <div className="step-body">
          <div className="folder-buttons">
            <button onClick={stub("Browse folder")}>Browse</button>
            <button onClick={stub("Add another folder (multi-folder search)")}>+Folder</button>
            <button onClick={stub("Pick a single file to search")}>Single File</button>
          </div>
          <input
            type="text"
            placeholder="/absolute/path/to/folder"
            value={p.params.directory}
            onChange={(e) => p.setParams({ directory: e.target.value })}
          />
        </div>
      </section>

      {/* Step 2 — search terms only (options moved to Advanced) */}
      <section className="step-row">
        <span className="step-label">Step 2</span>
        <div className="step-body">
          <div className="search-input-row">
            <input
              type="text"
              placeholder="Enter search terms…"
              value={p.params.terms.join(" ")}
              onChange={(e) =>
                p.setParams({
                  terms: e.target.value.split(/\s+/).filter(Boolean),
                })
              }
            />
            <button onClick={stub("Previous recent search (↑)")}>↑</button>
            <button onClick={stub("Next recent search (↓)")}>↓</button>
            <button className="clear-btn" onClick={() => p.setParams({ terms: [] })}>
              Clear
            </button>
          </div>
          <div className="step2-buttons">
            <button onClick={stub("Save current search by name")}>Save</button>
            <button onClick={stub("Reload a saved search")}>Reload</button>
            <button onClick={stub("Open Search Wizard")}>Wizard</button>
          </div>
        </div>
      </section>

      {/* Step 3 — pointer to Advanced */}
      <section className="step-row">
        <span className="step-label">Step 3</span>
        <div className="step-body">
          <p className="step3-note">
            Use <strong>Advanced Search Options</strong> below to configure search parameters
          </p>
        </div>
      </section>

      {/* Step 4 — Run buttons, then report indicators below them */}
      <section className="step-row">
        <span className="step-label step-4">Step 4</span>
        <div className="step-body">
          <div className="run-buttons">
            <button
              className="run-standard"
              disabled={p.loading || !p.params.directory || p.params.terms.length === 0}
              onClick={p.onRun}
            >
              {p.loading ? "Searching…" : "🔍 Run Standard Search"}
            </button>
            <button
              className="run-suites"
              onClick={stub("Open Search Suites popup")}
            >
              Search Suites
            </button>
            <button
              className="run-regex"
              onClick={stub("Open Regex Search popup")}
            >
              Regex Search
            </button>
          </div>
          <div className="report-indicators">
            <span className="muted small">Open report:</span>
            <button className="fmt-btn" onClick={stub("Open DOCX report")}>DOCX</button>
            <button className="fmt-btn" onClick={stub("Open TXT report")}>TXT</button>
            <button className="fmt-btn" onClick={stub("Open CSV report")}>CSV</button>
            <button className="fmt-btn" onClick={stub("Open JSON report")}>JSON</button>
            <button className="fmt-btn" onClick={stub("Open PDF report")}>PDF</button>
            <button className="fmt-btn" onClick={stub("Open HTML report")}>HTML</button>
          </div>
        </div>
      </section>

      {/* Advanced — now holds AND/OR, Recursive, Whole Word, Use Index,
          CSV/JSON/PDF/HTML output checkboxes, and Delete on Close */}
      <AdvancedOptions
        params={p.params}
        setParams={p.setParams}
        outputCsv={p.outputCsv}
        setOutputCsv={p.setOutputCsv}
        outputJson={p.outputJson}
        setOutputJson={p.setOutputJson}
        outputPdf={p.outputPdf}
        setOutputPdf={p.setOutputPdf}
        outputHtml={p.outputHtml}
        setOutputHtml={p.setOutputHtml}
        deleteOnClose={p.deleteOnClose}
        setDeleteOnClose={p.setDeleteOnClose}
      />
    </div>
  );
}
