import { useState } from "react";
import type { SearchRequest } from "../api";
import { saveDefaults, getDefaults, clearFactoryDefaults } from "../api";
import { useI18n } from "../i18n";

interface AdvancedOptionsProps {
  params: SearchRequest;
  setParams: (next: Partial<SearchRequest>) => void;

  // Output-format checkboxes (also Delete on Close) — moved here
  // from Step 3. All six formats are now individually selectable.
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

  // Factory reset (used by Restore Factory Settings and Reset All Fields)
  resetToFactory: () => void;

  // Tooltip-toggle awareness
  tooltipsOn: boolean;
}

// Subset of fields that map cleanly to ~/.peekdocsrc keys.
function paramsToConfigDict(
  p: SearchRequest,
  outputTxt: boolean,
  outputDocx: boolean,
  outputCsv: boolean,
  outputJson: boolean,
  outputPdf: boolean,
  outputHtml: boolean
): Record<string, unknown> {
  return {
    match_all: p.match_all ?? false,
    recursive: p.recursive ?? false,
    use_whole_word: p.use_whole_word ?? false,
    use_index: p.use_index ?? false,
    use_fuzzy: p.use_fuzzy ?? false,
    use_wildcard: p.use_wildcard ?? false,
    use_regex: p.use_regex ?? false,
    use_ocr: p.use_ocr ?? false,
    context_before: p.context_before ?? 0,
    context_after: p.context_after ?? 0,
    proximity: p.proximity ?? 0,
    line_proximity: p.line_proximity ?? 0,
    cores: p.cores ?? "",
    max_file_size_mb: p.max_file_size_mb ?? 100,
    file_types: (p.file_types ?? []).join(","),
    exclude: (p.exclude_terms ?? []).join(" "),
    specific_files: (p.file_names ?? []).join(","),
    range: p.range_filters ?? "",
    output_txt: outputTxt,
    output_docx: outputDocx,
    output_csv: outputCsv,
    output_json: outputJson,
    output_pdf: outputPdf,
    output_html: outputHtml,
  };
}

function configDictToParamsPatch(
  cfg: Record<string, unknown>
): Partial<SearchRequest> {
  const patch: Partial<SearchRequest> = {};
  const set = <K extends keyof SearchRequest>(k: K, v: SearchRequest[K]) => {
    patch[k] = v;
  };
  if ("match_all" in cfg) set("match_all", !!cfg.match_all);
  if ("recursive" in cfg) set("recursive", !!cfg.recursive);
  if ("use_whole_word" in cfg) set("use_whole_word", !!cfg.use_whole_word);
  if ("use_index" in cfg) set("use_index", !!cfg.use_index);
  if ("use_fuzzy" in cfg) set("use_fuzzy", !!cfg.use_fuzzy);
  if ("use_wildcard" in cfg) set("use_wildcard", !!cfg.use_wildcard);
  if ("use_regex" in cfg) set("use_regex", !!cfg.use_regex);
  if ("use_ocr" in cfg) set("use_ocr", !!cfg.use_ocr);
  if ("context_before" in cfg)
    set("context_before", Number(cfg.context_before) || 0);
  if ("context_after" in cfg)
    set("context_after", Number(cfg.context_after) || 0);
  if ("proximity" in cfg) set("proximity", Number(cfg.proximity) || 0);
  if ("line_proximity" in cfg)
    set("line_proximity", Number(cfg.line_proximity) || 0);
  if ("max_file_size_mb" in cfg)
    set("max_file_size_mb", Number(cfg.max_file_size_mb) || 100);
  if ("cores" in cfg && cfg.cores !== "" && cfg.cores != null)
    set("cores", Number(cfg.cores));
  if (typeof cfg.file_types === "string" && cfg.file_types) {
    set(
      "file_types",
      cfg.file_types.split(",").map((s) => s.trim()).filter(Boolean)
    );
  }
  if (typeof cfg.exclude === "string" && cfg.exclude) {
    set(
      "exclude_terms",
      cfg.exclude.split(/\s+/).filter(Boolean)
    );
  }
  if (typeof cfg.specific_files === "string" && cfg.specific_files) {
    set(
      "file_names",
      cfg.specific_files.split(",").map((s) => s.trim()).filter(Boolean)
    );
  }
  if (typeof cfg.range === "string" && cfg.range) {
    set("range_filters", cfg.range);
  }
  return patch;
}

/**
 * Advanced Search Options — collapsible section, default expanded.
 * Now the home for everything that used to live next to the step
 * labels: AND/OR mode, Recursive, Whole Word, Use Index, and the
 * CSV/JSON/PDF/HTML output toggles plus Delete on Close.
 */
export default function AdvancedOptions(p: AdvancedOptionsProps) {
  const { t } = useI18n();
  const [expanded, setExpanded] = useState(true);
  const tip = (s: string): string | undefined => (p.tooltipsOn ? s : undefined);

  return (
    <section className="adv-options">
      <button
        className={`adv-header ${expanded ? "open" : ""}`}
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
        title={tip("Click to collapse / expand the Advanced Search Options panel")}
      >
        <span className="chevron">{expanded ? "▾" : "▸"}</span>
        {t("adv_window_title", "Advanced Search Options")}
      </button>

      {expanded && (
        <div className="adv-body">
          {/* Search modes — now includes AND, Recursive, Use Index,
              alongside the existing fuzzy/wildcard/regex/etc. */}
          <div className="adv-group">
            <div className="adv-group-label">{t("search_options_label", "Search modes")}</div>
            <div className="adv-checkrow">
              <label title={tip(t("and_tooltip", "AND mode — all terms must appear on the same line"))}>
                <input
                  type="checkbox"
                  checked={p.params.match_all ?? false}
                  onChange={(e) =>
                    p.setParams({ match_all: e.target.checked })
                  }
                />
                {t("adv_and_mode_label", "AND mode")} <span className="muted small">(default OR)</span>
              </label>
              <label title={tip(t("recursive_tooltip", "Include all subfolders when searching"))}>
                <input
                  type="checkbox"
                  checked={p.params.recursive ?? false}
                  onChange={(e) =>
                    p.setParams({ recursive: e.target.checked })
                  }
                />
                {t("recursive_label", "Recursive")}
              </label>
              <label title={tip(t("whole_word_tooltip", "Match only complete words"))}>
                <input
                  type="checkbox"
                  checked={p.params.use_whole_word ?? false}
                  onChange={(e) =>
                    p.setParams({ use_whole_word: e.target.checked })
                  }
                />
                {t("whole_word_label", "Whole Word")}
              </label>
              <label title={tip(t("use_index_tooltip", "Use the search index for faster repeated searches"))}>
                <input
                  type="checkbox"
                  checked={p.params.use_index ?? false}
                  onChange={(e) =>
                    p.setParams({ use_index: e.target.checked })
                  }
                />
                {t("use_index_label", "Use Index")}
              </label>
              <label title={tip("Typo-tolerant matching — catches misspellings")}>
                <input
                  type="checkbox"
                  checked={p.params.use_fuzzy ?? false}
                  onChange={(e) =>
                    p.setParams({ use_fuzzy: e.target.checked })
                  }
                />
                {t("adv_fuzzy_label", "Fuzzy")}
              </label>
              <label title={tip("Wildcard matching — * and ? supported")}>
                <input
                  type="checkbox"
                  checked={p.params.use_wildcard ?? false}
                  onChange={(e) =>
                    p.setParams({ use_wildcard: e.target.checked })
                  }
                />
                {t("adv_wildcard_label", "Wildcard")}
              </label>
              <label title={tip("Regular expression matching")}>
                <input
                  type="checkbox"
                  checked={p.params.use_regex ?? false}
                  onChange={(e) =>
                    p.setParams({ use_regex: e.target.checked })
                  }
                />
                {t("adv_regex_label", "Regex")}
              </label>
              <label title={tip("Optical Character Recognition — search scanned PDFs and images (requires Tesseract)")}>
                <input
                  type="checkbox"
                  checked={p.params.use_ocr ?? false}
                  onChange={(e) =>
                    p.setParams({ use_ocr: e.target.checked })
                  }
                />
                {t("adv_ocr_label", "OCR")}
              </label>
            </div>
          </div>

          <div className="adv-group">
            <div className="adv-group-label">
              {t("adv_expression_label", "Boolean expression")} <span className="muted small">({t("adv_expression_overrides_terms", "overrides terms")})</span>
            </div>
            <input
              type="text"
              placeholder="(budget OR revenue) AND NOT draft"
              value={p.params.expression ?? ""}
              onChange={(e) =>
                p.setParams({ expression: e.target.value || null })
              }
              title={tip("Boolean syntax with AND / OR / NOT and parentheses")}
            />
          </div>

          {/* Context & proximity — moved out of the filters grid so
              the four numeric tweaks live with their conceptual home
              (the search expression). */}
          <div className="adv-grid adv-grid-cols-4">
            <label title={tip("All terms must be within N words on the same line")}>
              {t("adv_word_proximity_label", "Word proximity")}
              <input
                type="number"
                min={0}
                max={50}
                value={p.params.proximity ?? 0}
                onChange={(e) =>
                  p.setParams({ proximity: parseInt(e.target.value) || 0 })
                }
              />
            </label>
            <label title={tip("All terms must be within N lines of each other")}>
              {t("adv_line_proximity_label", "Line proximity")}
              <input
                type="number"
                min={0}
                max={50}
                value={p.params.line_proximity ?? 0}
                onChange={(e) =>
                  p.setParams({ line_proximity: parseInt(e.target.value) || 0 })
                }
              />
            </label>
            <label title={tip("Include N lines of context before each match")}>
              {t("adv_lines_before_label", "Lines before")}
              <input
                type="number"
                min={0}
                max={20}
                value={p.params.context_before ?? 0}
                onChange={(e) =>
                  p.setParams({ context_before: parseInt(e.target.value) || 0 })
                }
              />
            </label>
            <label title={tip("Include N lines of context after each match")}>
              {t("adv_lines_after_label", "Lines after")}
              <input
                type="number"
                min={0}
                max={20}
                value={p.params.context_after ?? 0}
                onChange={(e) =>
                  p.setParams({ context_after: parseInt(e.target.value) || 0 })
                }
              />
            </label>
          </div>

          {/* Filters */}
          <div className="adv-grid">
            <label title={tip("Exclude lines containing any of these terms")}>
              {t("adv_exclude_label", "Exclude")}
              <input
                type="text"
                placeholder="draft archive"
                value={(p.params.exclude_terms ?? []).join(" ")}
                onChange={(e) =>
                  p.setParams({
                    exclude_terms:
                      e.target.value.split(/\s+/).filter(Boolean) || null,
                  })
                }
              />
            </label>
            <label title={tip("Restrict to these file extensions (comma-separated)")}>
              {t("adv_file_types_label", "File types")}
              <input
                type="text"
                placeholder="pdf,docx,txt"
                value={(p.params.file_types ?? []).join(",")}
                onChange={(e) =>
                  p.setParams({
                    file_types:
                      e.target.value.split(",").map((s) => s.trim()).filter(Boolean) ||
                      null,
                  })
                }
              />
            </label>
            <label title={tip("Filename patterns to include — comma-separated, supports * and ?")}>
              {t("adv_specific_files_label", "Specific files")}
              <input
                type="text"
                placeholder="budget*.pdf, *.docx"
                value={(p.params.file_names ?? []).join(", ")}
                onChange={(e) =>
                  p.setParams({
                    file_names:
                      e.target.value.split(",").map((s) => s.trim()).filter(Boolean) ||
                      null,
                  })
                }
              />
            </label>
            <label title={tip("Filter by dollar amounts, dates, percentages, ages, or file sizes")}>
              {t("adv_range_label", "Range filter")}
              <input
                type="text"
                placeholder="amount:1000..5000"
                value={p.params.range_filters ?? ""}
                onChange={(e) =>
                  p.setParams({ range_filters: e.target.value || null })
                }
              />
            </label>
            <label title={tip("Number of CPU cores to use (blank = auto, half of available)")}>
              {t("adv_cores_to_use_label", "Cores")}
              <input
                type="number"
                min={1}
                max={64}
                value={p.params.cores ?? ""}
                placeholder="auto"
                onChange={(e) =>
                  p.setParams({
                    cores: e.target.value ? parseInt(e.target.value) : null,
                  })
                }
              />
            </label>
            <label title={tip("Skip files larger than this (in MB)")}>
              {t("adv_max_file_size_label", "Max file size (MB)")}
              <input
                type="number"
                min={0}
                value={p.params.max_file_size_mb ?? 100}
                onChange={(e) =>
                  p.setParams({
                    max_file_size_mb: parseInt(e.target.value) || 100,
                  })
                }
              />
            </label>
          </div>

          {/* Output formats — all six are individually selectable. */}
          <div className="adv-group">
            <div className="adv-group-label">
              {t("adv_also_output_label", "Output formats")} <span className="muted small">({t("adv_output_each_file", "each format produces a file next to the searched documents")})</span>
            </div>
            <div className="adv-checkrow">
              <label title={tip("Plain-text report")}>
                <input
                  type="checkbox"
                  checked={p.outputTxt}
                  onChange={(e) => p.setOutputTxt(e.target.checked)}
                />
                TXT
              </label>
              <label title={tip("Word document with yellow-highlighted matches")}>
                <input
                  type="checkbox"
                  checked={p.outputDocx}
                  onChange={(e) => p.setOutputDocx(e.target.checked)}
                />
                DOCX
              </label>
              <label title={tip("Spreadsheet — one row per match")}>
                <input
                  type="checkbox"
                  checked={p.outputCsv}
                  onChange={(e) => p.setOutputCsv(e.target.checked)}
                />
                CSV
              </label>
              <label title={tip("Machine-readable JSON for automation")}>
                <input
                  type="checkbox"
                  checked={p.outputJson}
                  onChange={(e) => p.setOutputJson(e.target.checked)}
                />
                JSON
              </label>
              <label title={tip("PDF report — Latin-1 font, non-Latin shows as ?")}>
                <input
                  type="checkbox"
                  checked={p.outputPdf}
                  onChange={(e) => p.setOutputPdf(e.target.checked)}
                />
                PDF
              </label>
              <label title={tip("HTML report — opens in any browser")}>
                <input
                  type="checkbox"
                  checked={p.outputHtml}
                  onChange={(e) => p.setOutputHtml(e.target.checked)}
                />
                HTML
              </label>
              <label
                className="delete-on-close-adv"
                title={tip(t("delete_on_close_tooltip", "peekdocs never modifies or deletes your own documents — Delete on Close removes only files peekdocs created (results, the search index, etc.) when you close the app."))}
              >
                <input
                  type="checkbox"
                  checked={p.deleteOnClose}
                  onChange={(e) => p.setDeleteOnClose(e.target.checked)}
                />
                {t("delete_on_close_label", "Delete on Close")}
              </label>
            </div>
            <p className="muted small">
              {t("delete_on_close_explainer", "peekdocs never modifies or deletes your own documents — Delete on Close removes only files peekdocs created (results, the search index, etc.) when you close the app.")}
            </p>
          </div>

          {/* Output-targeting fields — still visual only in Phase 0;
              the web backend returns JSON rather than writing files. */}
          <div className="adv-group output-stub">
            <div className="adv-group-label">
              {t("adv_output_settings_label", "Output settings")} <span className="muted">({t("adv_output_settings_visual_only", "visual only — backend returns JSON, doesn't write files yet")})</span>
            </div>
            <div className="adv-grid">
              <label>
                {t("adv_save_report_as_label", "Save report as")}
                <input type="text" placeholder="my_report" disabled />
              </label>
              <label>
                {t("adv_append_report_to_label", "Append to")}
                <input type="text" placeholder="archive" disabled />
              </label>
              <label>
                {t("adv_output_dir_label", "Output dir")}
                <input type="text" placeholder="~/peekdocs_reports" disabled />
              </label>
            </div>
            <div className="adv-checkrow">
              <label><input type="checkbox" disabled /> {t("adv_timestamp_filename_label", "Timestamp filename")}</label>
              <label><input type="checkbox" disabled /> {t("adv_clear_history_label", "Clear history on close")}</label>
              <label><input type="checkbox" disabled /> {t("adv_restrict_perms_label", "Restrict file permissions")}</label>
              <label><input type="checkbox" disabled /> {t("adv_notify_complete_label", "Notify when search complete")}</label>
            </div>
          </div>

          <div className="adv-buttons">
            <button
              title={tip("Save the current configuration as defaults (~/.peekdocsrc)")}
              onClick={async () => {
                try {
                  await saveDefaults(
                    paramsToConfigDict(
                      p.params,
                      p.outputTxt,
                      p.outputDocx,
                      p.outputCsv,
                      p.outputJson,
                      p.outputPdf,
                      p.outputHtml
                    )
                  );
                  alert("Defaults saved to ~/.peekdocsrc");
                } catch (e) {
                  alert(`Save Defaults failed: ${e}`);
                }
              }}
            >
              {t("adv_save_defaults_label", "Save as Defaults")}
            </button>
            <button
              title={tip("Restore your saved defaults from ~/.peekdocsrc")}
              onClick={async () => {
                try {
                  const cfg = await getDefaults();
                  const patch = configDictToParamsPatch(cfg);
                  p.setParams(patch);
                  if ("output_txt" in cfg) p.setOutputTxt(!!cfg.output_txt);
                  if ("output_docx" in cfg) p.setOutputDocx(!!cfg.output_docx);
                  if ("output_csv" in cfg) p.setOutputCsv(!!cfg.output_csv);
                  if ("output_json" in cfg) p.setOutputJson(!!cfg.output_json);
                  if ("output_pdf" in cfg) p.setOutputPdf(!!cfg.output_pdf);
                  if ("output_html" in cfg) p.setOutputHtml(!!cfg.output_html);
                  alert("Restored from ~/.peekdocsrc");
                } catch (e) {
                  alert(`Restore Saved Defaults failed: ${e}`);
                }
              }}
            >
              {t("adv_restore_defaults_label", "Restore Saved Defaults")}
            </button>
            <button
              title={tip("Delete ~/.peekdocsrc and reset every field to factory defaults")}
              onClick={async () => {
                if (
                  !confirm(
                    "Restore Factory Settings will delete ~/.peekdocsrc and reset every field. Continue?"
                  )
                )
                  return;
                try {
                  await clearFactoryDefaults();
                  p.resetToFactory();
                  alert("Factory settings restored.");
                } catch (e) {
                  alert(`Restore Factory failed: ${e}`);
                }
              }}
            >
              {t("adv_restore_factory_label", "Restore Factory Settings")}
            </button>
            <button
              title={tip("Reset every field to factory defaults (does not touch ~/.peekdocsrc)")}
              onClick={() => p.resetToFactory()}
            >
              {t("adv_reset_all_label", "Reset All Fields")}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
