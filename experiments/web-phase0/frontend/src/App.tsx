import { useCallback, useState } from "react";
import Header from "./components/Header";
import Footer from "./components/Footer";
import SearchPanel from "./components/SearchPanel";
import ResultsPanel from "./components/ResultsPanel";
import Splitter from "./components/Splitter";
import SaveSearchModal from "./components/SaveSearchModal";
import ReloadSearchModal from "./components/ReloadSearchModal";
import AboutModal from "./components/AboutModal";
import SuitesModal from "./components/SuitesModal";
import RegexCollectionsModal from "./components/RegexCollectionsModal";
import SystemCheckModal from "./components/SystemCheckModal";
import ToolsModal, { type ToolKind } from "./components/ToolsModal";
import { runSearch, type SearchRequest, type SearchResponse } from "./api";

const INITIAL_PARAMS: SearchRequest = {
  terms: [],
  directory: "",
  recursive: true,
  use_whole_word: false,
  use_index: false,
  match_all: false,
  write_reports: true,
};

const ANALYSIS_TOOLS: Record<string, ToolKind> = {
  "file-inventory": "file-inventory",
  "age-distribution": "age-distribution",
  duplicates: "duplicates",
  "large-files": "large-files",
  "empty-files": "empty-files",
  "recent-changes": "recent-changes",
  "protected-files": "protected-files",
  "unsearchable-files": "unsearchable-files",
};

export default function App() {
  const [params, setParamsState] = useState<SearchRequest>(INITIAL_PARAMS);
  const [tooltipsOn, setTooltipsOn] = useState(true);

  const [outputCsv, setOutputCsv] = useState(false);
  const [outputJson, setOutputJson] = useState(false);
  const [outputPdf, setOutputPdf] = useState(false);
  const [outputHtml, setOutputHtml] = useState(false);
  const [deleteOnClose, setDeleteOnClose] = useState(false);

  const [leftPercent, setLeftPercent] = useState(50);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SearchResponse | null>(null);

  const [showSave, setShowSave] = useState(false);
  const [showReload, setShowReload] = useState(false);
  const [showAbout, setShowAbout] = useState(false);
  const [showSuites, setShowSuites] = useState(false);
  const [showRegex, setShowRegex] = useState(false);
  const [showSystemCheck, setShowSystemCheck] = useState(false);
  const [activeTool, setActiveTool] = useState<ToolKind | null>(null);

  const setParams = useCallback((next: Partial<SearchRequest>) => {
    setParamsState((prev) => ({ ...prev, ...next }));
  }, []);

  const resetToFactory = useCallback(() => {
    setParamsState({ ...INITIAL_PARAMS, directory: params.directory });
    setOutputCsv(false);
    setOutputJson(false);
    setOutputPdf(false);
    setOutputHtml(false);
    setDeleteOnClose(false);
  }, [params.directory]);

  async function onRun() {
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const r = await runSearch({
        ...params,
        output_csv: outputCsv,
        output_json: outputJson,
        output_pdf: outputPdf,
        output_html: outputHtml,
      });
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  function onTool(tool: string) {
    if (tool === "system-check") {
      setShowSystemCheck(true);
      return;
    }
    if (tool in ANALYSIS_TOOLS) {
      if (!params.directory) {
        alert(`${tool} needs a folder — set Step 1 first.`);
        return;
      }
      setActiveTool(ANALYSIS_TOOLS[tool]);
      return;
    }
    alert(
      `${tool}\n\nThis tool needs a dedicated backend endpoint — coming in the next round (Tier 3).`
    );
  }

  return (
    <div className="app">
      <Header tooltipsOn={tooltipsOn} setTooltipsOn={setTooltipsOn} />

      <main className="split-layout">
        <div className="left-pane" style={{ width: `${leftPercent}%` }}>
          <SearchPanel
            params={params}
            setParams={setParams}
            loading={loading}
            onRun={onRun}
            result={result}
            outputCsv={outputCsv}
            setOutputCsv={setOutputCsv}
            outputJson={outputJson}
            setOutputJson={setOutputJson}
            outputPdf={outputPdf}
            setOutputPdf={setOutputPdf}
            outputHtml={outputHtml}
            setOutputHtml={setOutputHtml}
            deleteOnClose={deleteOnClose}
            setDeleteOnClose={setDeleteOnClose}
            openSaveSearchModal={() => setShowSave(true)}
            openReloadModal={() => setShowReload(true)}
            openSuitesModal={() => setShowSuites(true)}
            openRegexModal={() => setShowRegex(true)}
            openWizardModal={() =>
              alert("Search Wizard — coming in Tier 3.")
            }
            resetToFactory={resetToFactory}
          />
        </div>

        <Splitter leftPercent={leftPercent} onChange={setLeftPercent} />

        <div className="right-pane" style={{ width: `${100 - leftPercent}%` }}>
          <ResultsPanel loading={loading} error={error} result={result} />
        </div>
      </main>

      <Footer onAbout={() => setShowAbout(true)} onTool={onTool} />

      {showSave && (
        <SaveSearchModal
          params={params}
          onClose={() => setShowSave(false)}
        />
      )}
      {showReload && (
        <ReloadSearchModal
          directory={params.directory}
          onLoad={(patch) => setParams(patch)}
          onClose={() => setShowReload(false)}
        />
      )}
      {showAbout && <AboutModal onClose={() => setShowAbout(false)} />}
      {showSuites && (
        <SuitesModal
          directory={params.directory}
          onClose={() => setShowSuites(false)}
        />
      )}
      {showRegex && (
        <RegexCollectionsModal
          directory={params.directory}
          onClose={() => setShowRegex(false)}
        />
      )}
      {showSystemCheck && (
        <SystemCheckModal onClose={() => setShowSystemCheck(false)} />
      )}
      {activeTool && (
        <ToolsModal
          kind={activeTool}
          directory={params.directory}
          onClose={() => setActiveTool(null)}
        />
      )}
    </div>
  );
}
