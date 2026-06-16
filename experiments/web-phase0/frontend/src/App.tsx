import { useCallback, useState } from "react";
import Header from "./components/Header";
import Footer from "./components/Footer";
import SearchPanel from "./components/SearchPanel";
import ResultsPanel from "./components/ResultsPanel";
import Splitter from "./components/Splitter";
import { runSearch, type SearchRequest, type SearchResponse } from "./api";

const INITIAL_PARAMS: SearchRequest = {
  terms: [],
  directory: "",
  recursive: true,
  use_whole_word: false,
  use_index: false,
  match_all: false,
};

export default function App() {
  const [params, setParamsState] = useState<SearchRequest>(INITIAL_PARAMS);
  const [tooltipsOn, setTooltipsOn] = useState(true);

  // Step 3 output-format checkboxes — visual only for now since the
  // web backend doesn't write files. Lifted to App level so a future
  // Phase 1 can persist them like the other settings.
  const [outputCsv, setOutputCsv] = useState(false);
  const [outputJson, setOutputJson] = useState(false);
  const [outputPdf, setOutputPdf] = useState(false);
  const [outputHtml, setOutputHtml] = useState(false);
  const [deleteOnClose, setDeleteOnClose] = useState(false);

  const [leftPercent, setLeftPercent] = useState(50);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SearchResponse | null>(null);

  // Partial setter — merges into existing params.
  const setParams = useCallback((next: Partial<SearchRequest>) => {
    setParamsState((prev) => ({ ...prev, ...next }));
  }, []);

  async function onRun() {
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const r = await runSearch(params);
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
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
          />
        </div>

        <Splitter leftPercent={leftPercent} onChange={setLeftPercent} />

        <div className="right-pane" style={{ width: `${100 - leftPercent}%` }}>
          <ResultsPanel loading={loading} error={error} result={result} />
        </div>
      </main>

      <Footer />
    </div>
  );
}
