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
import SearchHistoryModal from "./components/SearchHistoryModal";
import BookmarksModal from "./components/BookmarksModal";
import AllFilesModal from "./components/AllFilesModal";
import ClearFilesModal from "./components/ClearFilesModal";
import IndexesModal from "./components/IndexesModal";
import ScheduleSearchModal from "./components/ScheduleSearchModal";
import DiffSnapshotsModal from "./components/DiffSnapshotsModal";
import RegexTesterModal from "./components/RegexTesterModal";
import WizardModal from "./components/WizardModal";
import { runSearch, type SearchRequest, type SearchResponse } from "./api";
import { setLanguage } from "./i18n";

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

type ModalKey =
  | null
  | "save"
  | "reload"
  | "about"
  | "suites"
  | "regex-collections"
  | "system-check"
  | "search-history"
  | "bookmarks"
  | "all-files"
  | "clear-files"
  | "clean-folder"
  | "indexes"
  | "schedule"
  | "diff"
  | "regex-tester"
  | "wizard";

export default function App() {
  const [params, setParamsState] = useState<SearchRequest>(INITIAL_PARAMS);
  const [tooltipsOn, setTooltipsOn] = useState(true);
  const [lang, setLangState] = useState("en");

  const [outputTxt, setOutputTxt] = useState(true);
  const [outputDocx, setOutputDocx] = useState(true);
  const [outputCsv, setOutputCsv] = useState(false);
  const [outputJson, setOutputJson] = useState(false);
  const [outputPdf, setOutputPdf] = useState(false);
  const [outputHtml, setOutputHtml] = useState(false);
  const [deleteOnClose, setDeleteOnClose] = useState(false);

  const [leftPercent, setLeftPercent] = useState(50);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SearchResponse | null>(null);

  const [openModal, setOpenModal] = useState<ModalKey>(null);
  const [activeTool, setActiveTool] = useState<ToolKind | null>(null);

  const setParams = useCallback((next: Partial<SearchRequest>) => {
    setParamsState((prev) => ({ ...prev, ...next }));
  }, []);

  const resetToFactory = useCallback(() => {
    setParamsState({ ...INITIAL_PARAMS, directory: params.directory });
    setOutputTxt(true);
    setOutputDocx(true);
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
        output_txt: outputTxt,
        output_docx: outputDocx,
        output_csv: outputCsv,
        output_json: outputJson,
        output_pdf: outputPdf,
        output_html: outputHtml,
      });
      setResult(r);
      if (r.report_errors && r.report_errors.length > 0) {
        setError(`Some report formats failed: ${r.report_errors.join("; ")}`);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  function onTool(tool: string) {
    if (tool === "system-check") {
      setOpenModal("system-check");
      return;
    }
    if (tool === "history") {
      setOpenModal("search-history");
      return;
    }
    if (tool === "bookmarks") {
      setOpenModal("bookmarks");
      return;
    }
    if (tool === "view-all") {
      if (!params.directory) {
        alert("View All needs a folder — set Step 1 first.");
        return;
      }
      setOpenModal("all-files");
      return;
    }
    if (tool === "clear-files") {
      if (!params.directory) {
        alert("Clear Files needs a folder — set Step 1 first.");
        return;
      }
      setOpenModal("clear-files");
      return;
    }
    if (tool === "clean-folder") {
      setOpenModal("clean-folder");
      return;
    }
    if (tool === "indexes") {
      if (!params.directory) {
        alert("Indexes needs a folder — set Step 1 first.");
        return;
      }
      setOpenModal("indexes");
      return;
    }
    if (tool === "schedule") {
      if (!params.directory) {
        alert("Schedule Search needs a folder — set Step 1 first.");
        return;
      }
      setOpenModal("schedule");
      return;
    }
    if (tool === "diff") {
      setOpenModal("diff");
      return;
    }
    if (tool === "regex-tester") {
      setOpenModal("regex-tester");
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
    alert(`${tool}\n\n(Not wired yet.)`);
  }

  function onLangChange(newLang: string) {
    setLangState(newLang);
    setLanguage(newLang);
  }

  return (
    <div className="app">
      <Header
        tooltipsOn={tooltipsOn}
        setTooltipsOn={setTooltipsOn}
        lang={lang}
        setLang={onLangChange}
      />

      <main className="split-layout">
        <div className="left-pane" style={{ width: `${leftPercent}%` }}>
          <SearchPanel
            params={params}
            setParams={setParams}
            loading={loading}
            onRun={onRun}
            result={result}
            tooltipsOn={tooltipsOn}
            outputTxt={outputTxt}
            setOutputTxt={setOutputTxt}
            outputDocx={outputDocx}
            setOutputDocx={setOutputDocx}
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
            openSaveSearchModal={() => setOpenModal("save")}
            openReloadModal={() => setOpenModal("reload")}
            openSuitesModal={() => setOpenModal("suites")}
            openRegexModal={() => setOpenModal("regex-collections")}
            openWizardModal={() => setOpenModal("wizard")}
            resetToFactory={resetToFactory}
          />
        </div>

        <Splitter leftPercent={leftPercent} onChange={setLeftPercent} />

        <div className="right-pane" style={{ width: `${100 - leftPercent}%` }}>
          <ResultsPanel
            loading={loading}
            error={error}
            result={result}
            highlight={{
              terms: params.terms,
              expression: params.expression ?? null,
              useRegex: params.use_regex ?? false,
              useWildcard: params.use_wildcard ?? false,
              useWholeWord: params.use_whole_word ?? false,
            }}
          />
        </div>
      </main>

      <Footer onAbout={() => setOpenModal("about")} onTool={onTool} tooltipsOn={tooltipsOn} />

      {openModal === "save" && (
        <SaveSearchModal params={params} onClose={() => setOpenModal(null)} />
      )}
      {openModal === "reload" && (
        <ReloadSearchModal
          directory={params.directory}
          onLoad={(patch) => setParams(patch)}
          onClose={() => setOpenModal(null)}
        />
      )}
      {openModal === "about" && <AboutModal onClose={() => setOpenModal(null)} />}
      {openModal === "suites" && (
        <SuitesModal directory={params.directory} onClose={() => setOpenModal(null)} />
      )}
      {openModal === "regex-collections" && (
        <RegexCollectionsModal
          directory={params.directory}
          onClose={() => setOpenModal(null)}
        />
      )}
      {openModal === "system-check" && (
        <SystemCheckModal onClose={() => setOpenModal(null)} />
      )}
      {openModal === "search-history" && (
        <SearchHistoryModal
          onPick={(terms) =>
            setParams({ terms: terms.split(/\s+/).filter(Boolean) })
          }
          onClose={() => setOpenModal(null)}
        />
      )}
      {openModal === "bookmarks" && (
        <BookmarksModal onClose={() => setOpenModal(null)} />
      )}
      {openModal === "all-files" && (
        <AllFilesModal directory={params.directory} onClose={() => setOpenModal(null)} />
      )}
      {openModal === "clear-files" && (
        <ClearFilesModal
          directory={params.directory}
          kind="clear"
          onClose={() => setOpenModal(null)}
        />
      )}
      {openModal === "clean-folder" && (
        <ClearFilesModal
          directory={params.directory}
          kind="clean"
          onClose={() => setOpenModal(null)}
        />
      )}
      {openModal === "indexes" && (
        <IndexesModal directory={params.directory} onClose={() => setOpenModal(null)} />
      )}
      {openModal === "schedule" && (
        <ScheduleSearchModal
          directory={params.directory}
          onClose={() => setOpenModal(null)}
        />
      )}
      {openModal === "diff" && <DiffSnapshotsModal onClose={() => setOpenModal(null)} />}
      {openModal === "regex-tester" && (
        <RegexTesterModal onClose={() => setOpenModal(null)} />
      )}
      {openModal === "wizard" && (
        <WizardModal
          onApply={(pattern) => {
            // Drop the combined regex into the search bar as a single term,
            // enable Regex mode.
            setParams({ terms: [pattern], use_regex: true });
          }}
          onClose={() => setOpenModal(null)}
        />
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
