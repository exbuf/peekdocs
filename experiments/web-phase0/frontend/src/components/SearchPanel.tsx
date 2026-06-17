import { useEffect, useState } from "react";
import type { SearchRequest, SearchResponse } from "../api";
import {
  pickFolder,
  pickFile,
  getHistory,
  reportUrl,
} from "../api";
import AdvancedOptions from "./AdvancedOptions";
import Tooltip from "./Tooltip";
import { useI18n } from "../i18n";

interface SearchPanelProps {
  params: SearchRequest;
  setParams: (next: Partial<SearchRequest>) => void;
  loading: boolean;
  onRun: () => void;
  result: SearchResponse | null;
  tooltipsOn: boolean;

  outputTxt: boolean;
  setOutputTxt: (v: boolean) => void;
  outputDocx: boolean;
  setOutputDocx: (v: boolean) => void;
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

  // Modal openers (lifted to App.tsx)
  openSaveSearchModal: () => void;
  openReloadModal: () => void;
  openSuitesModal: () => void;
  openRegexModal: () => void;
  openWizardModal: () => void;

  // Pass-through to AdvancedOptions
  resetToFactory: () => void;
}

const FORMATS = ["docx", "txt", "csv", "json", "pdf", "html"] as const;

export default function SearchPanel(p: SearchPanelProps) {
  const { t } = useI18n();
  const [history, setHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState<number | null>(null);
  const [stash, setStash] = useState<string>(""); // current input before cycling
  const tip = (s: string): string | undefined => (p.tooltipsOn ? s : undefined);

  // Load history once on mount.
  useEffect(() => {
    getHistory()
      .then(setHistory)
      .catch(() => {}); // silent — history is optional
  }, []);

  // Refresh history whenever a new result comes in (the backend
  // appended to it).
  useEffect(() => {
    if (p.result) {
      getHistory()
        .then(setHistory)
        .catch(() => {});
    }
  }, [p.result]);

  async function onBrowse() {
    try {
      const path = await pickFolder();
      if (path) p.setParams({ directory: path });
    } catch (e) {
      alert(`Folder picker failed: ${e}`);
    }
  }

  async function onAddFolder() {
    try {
      const path = await pickFolder();
      if (!path) return;
      const current = p.params.directory.trim();
      p.setParams({
        directory: current ? `${current};${path}` : path,
      });
    } catch (e) {
      alert(`Folder picker failed: ${e}`);
    }
  }

  async function onSingleFile() {
    try {
      const path = await pickFile();
      if (!path) return;
      // peekdocs supports file_names + directory — set both.
      const parent = path.substring(0, path.lastIndexOf("/")) || path;
      const basename = path.substring(path.lastIndexOf("/") + 1);
      p.setParams({
        directory: parent,
        file_names: [basename],
      });
    } catch (e) {
      alert(`File picker failed: ${e}`);
    }
  }

  function onArrowUp() {
    if (history.length === 0) return;
    const next = historyIndex === null ? 0 : Math.min(historyIndex + 1, history.length - 1);
    if (historyIndex === null) {
      setStash(p.params.terms.join(" "));
    }
    setHistoryIndex(next);
    p.setParams({ terms: (history[next] ?? "").split(/\s+/).filter(Boolean) });
  }

  function onArrowDown() {
    if (history.length === 0 || historyIndex === null) return;
    if (historyIndex === 0) {
      // Past the newest → restore stash
      setHistoryIndex(null);
      p.setParams({ terms: stash.split(/\s+/).filter(Boolean) });
      return;
    }
    const next = historyIndex - 1;
    setHistoryIndex(next);
    p.setParams({ terms: (history[next] ?? "").split(/\s+/).filter(Boolean) });
  }

  function onClear() {
    p.setParams({ terms: [] });
    setHistoryIndex(null);
    setStash("");
  }

  function onTermsChange(value: string) {
    setHistoryIndex(null); // typing breaks history-cycle mode
    p.setParams({ terms: value.split(/\s+/).filter(Boolean) });
  }

  function openReportFmt(fmt: string) {
    const path = p.result?.output_files[fmt];
    if (!path) {
      alert(
        `No ${fmt.toUpperCase()} report from the most recent search.\n\nRun a search first, with ${fmt.toUpperCase()} checked in Advanced Search Options → Output formats.`
      );
      return;
    }
    // Browser opens DOCX/PDF/CSV/JSON/TXT as downloads; HTML in a tab.
    const url = reportUrl(fmt);
    if (fmt === "html") {
      window.open(url, "_blank");
    } else {
      // Trigger a download (the FileResponse has filename set)
      const a = document.createElement("a");
      a.href = url;
      a.download = "";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  }

  return (
    <div className="left-pane-body">
      {/* Step 1 — folder */}
      <section className="step-row">
        <Tooltip text={t("step_1_tooltip", "Search folder — point peekdocs at the folder that holds your documents")} disabled={!p.tooltipsOn} placement="right">
          <span className="step-label">{t("step_1_label", "Step 1")}</span>
        </Tooltip>
        <div className="step-body">
          <div className="folder-buttons">
            <button onClick={onBrowse} title={tip("Open native folder picker")}>
              {t("browse_button_label", "Browse")}
            </button>
            <button onClick={onAddFolder} title={tip("Add another folder (multi-folder search)")}>
              {t("multi_folder_button_label", "+Folder")}
            </button>
            <button onClick={onSingleFile} title={tip("Pick a single file to search")}>
              {t("single_file_button_label", "Single File")}
            </button>
          </div>
          <input
            type="text"
            placeholder="/absolute/path/to/folder (or paths separated by ;)"
            value={p.params.directory}
            onChange={(e) => p.setParams({ directory: e.target.value })}
          />
        </div>
      </section>

      {/* Step 2 — search terms only */}
      <section className="step-row">
        <Tooltip text={t("step_2_tooltip", "Search terms — type what you're looking for")} disabled={!p.tooltipsOn} placement="right">
          <span className="step-label">{t("step_2_label", "Step 2")}</span>
        </Tooltip>
        <div className="step-body">
          <div className="search-input-row">
            <input
              type="text"
              placeholder="Enter search terms…"
              value={p.params.terms.join(" ")}
              onChange={(e) => onTermsChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "ArrowUp") {
                  e.preventDefault();
                  onArrowUp();
                } else if (e.key === "ArrowDown") {
                  e.preventDefault();
                  onArrowDown();
                } else if (e.key === "Enter") {
                  e.preventDefault();
                  if (p.params.directory && p.params.terms.length > 0) {
                    p.onRun();
                  }
                }
              }}
            />
            <button
              onClick={onArrowUp}
              disabled={history.length === 0}
              title="Previous recent search"
            >
              ↑
            </button>
            <button
              onClick={onArrowDown}
              disabled={history.length === 0 || historyIndex === null}
              title="Next recent search"
            >
              ↓
            </button>
            <button
              className="clear-btn"
              onClick={onClear}
              title={tip("Clear the search bar")}
            >
              {t("clear_button_label", "Clear")}
            </button>
          </div>
          <div className="step2-buttons">
            <button
              onClick={p.openSaveSearchModal}
              disabled={!p.params.directory}
              title={tip("Save current configuration as a named search")}
            >
              {t("save_label", "Save")}
            </button>
            <button
              onClick={p.openReloadModal}
              disabled={!p.params.directory}
              title={tip("Load a saved search")}
            >
              {t("reload_label", "Reload")}
            </button>
            <button onClick={p.openWizardModal} title={tip("Open the Regex Wizard")}>
              {t("wizard_label", "Wizard")}
            </button>
          </div>
          {history.length > 0 && (
            <div className="history-hint muted small">
              {historyIndex !== null
                ? `Recent ${historyIndex + 1} / ${history.length} (↓ to come back)`
                : `↑ for ${history.length} recent search${history.length === 1 ? "" : "es"}`}
            </div>
          )}
        </div>
      </section>

      {/* Step 3 — pointer to Advanced */}
      <section className="step-row">
        <Tooltip text={t("step_3_tooltip", "Output formats — choose which report files get written next to your documents")} disabled={!p.tooltipsOn} placement="right">
          <span className="step-label">{t("step_3_label", "Step 3")}</span>
        </Tooltip>
        <div className="step-body">
          <p className="step3-note">
            Use <strong>Advanced Search Options</strong> below to configure search parameters
          </p>
        </div>
      </section>

      {/* Step 4 — Run buttons + report indicators */}
      <section className="step-row">
        <Tooltip text={t("step_4_tooltip", "Run the search and view results")} disabled={!p.tooltipsOn} placement="right">
          <span className="step-label step-4">{t("step_4_label", "Step 4")}</span>
        </Tooltip>
        <div className="step-body">
          <div className="run-buttons">
            <Tooltip text={t("run_standard_search_tooltip", "Run a Standard Search with the current configuration")} disabled={!p.tooltipsOn}>
              <button
                className="run-standard"
                disabled={p.loading || !p.params.directory || p.params.terms.length === 0}
                onClick={p.onRun}
              >
                {p.loading ? "Searching…" : t("run_standard_search_label", "🔍 Run Standard Search")}
              </button>
            </Tooltip>
            <Tooltip text={t("search_suites_tooltip", "Open Search Suites — groups of saved searches")} disabled={!p.tooltipsOn}>
              <button
                className="run-suites"
                onClick={p.openSuitesModal}
                disabled={!p.params.directory}
              >
                {t("search_suites_label", "Search Suites")}
              </button>
            </Tooltip>
            <Tooltip text={t("regex_search_tooltip", "Open Regex Search collections")} disabled={!p.tooltipsOn}>
              <button
                className="run-regex"
                onClick={p.openRegexModal}
                disabled={!p.params.directory}
              >
                {t("regex_search_label", "Regex Search")}
              </button>
            </Tooltip>
          </div>
          <div className="report-indicators">
            <span className="muted small">Open report:</span>
            {FORMATS.map((fmt) => {
              const have = !!p.result?.output_files[fmt];
              return (
                <button
                  key={fmt}
                  className={`fmt-btn ${have ? "have" : ""}`}
                  onClick={() => openReportFmt(fmt)}
                  title={
                    have
                      ? `Open the ${fmt.toUpperCase()} report from the most recent search`
                      : `${fmt.toUpperCase()} not generated by the most recent search (enable in Advanced Options for CSV/JSON/PDF/HTML, or run a search at all for DOCX/TXT)`
                  }
                >
                  {fmt.toUpperCase()}
                </button>
              );
            })}
          </div>
        </div>
      </section>

      {/* Advanced */}
      <AdvancedOptions
        params={p.params}
        setParams={p.setParams}
        outputTxt={p.outputTxt}
        setOutputTxt={p.setOutputTxt}
        outputDocx={p.outputDocx}
        setOutputDocx={p.setOutputDocx}
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
        resetToFactory={p.resetToFactory}
        tooltipsOn={p.tooltipsOn}
      />
    </div>
  );
}
