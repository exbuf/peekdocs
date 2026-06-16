import { useState } from "react";
import type { SearchRequest } from "../api";

interface AdvancedOptionsProps {
  params: SearchRequest;
  setParams: (next: Partial<SearchRequest>) => void;

  // Output-format checkboxes (also Delete on Close) — moved here
  // from Step 3.
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

/**
 * Advanced Search Options — collapsible section, default expanded.
 * Now the home for everything that used to live next to the step
 * labels: AND/OR mode, Recursive, Whole Word, Use Index, and the
 * CSV/JSON/PDF/HTML output toggles plus Delete on Close.
 */
export default function AdvancedOptions(p: AdvancedOptionsProps) {
  const [expanded, setExpanded] = useState(true);

  return (
    <section className="adv-options">
      <button
        className={`adv-header ${expanded ? "open" : ""}`}
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
      >
        <span className="chevron">{expanded ? "▾" : "▸"}</span>
        Advanced Search Options
      </button>

      {expanded && (
        <div className="adv-body">
          {/* Search modes — now includes AND, Recursive, Use Index,
              alongside the existing fuzzy/wildcard/regex/etc. */}
          <div className="adv-group">
            <div className="adv-group-label">Search modes</div>
            <div className="adv-checkrow">
              <label>
                <input
                  type="checkbox"
                  checked={p.params.match_all ?? false}
                  onChange={(e) =>
                    p.setParams({ match_all: e.target.checked })
                  }
                />
                AND mode <span className="muted small">(default OR)</span>
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={p.params.recursive ?? false}
                  onChange={(e) =>
                    p.setParams({ recursive: e.target.checked })
                  }
                />
                Recursive
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={p.params.use_whole_word ?? false}
                  onChange={(e) =>
                    p.setParams({ use_whole_word: e.target.checked })
                  }
                />
                Whole Word
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={p.params.use_index ?? false}
                  onChange={(e) =>
                    p.setParams({ use_index: e.target.checked })
                  }
                />
                Use Index
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={p.params.use_fuzzy ?? false}
                  onChange={(e) =>
                    p.setParams({ use_fuzzy: e.target.checked })
                  }
                />
                Fuzzy
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={p.params.use_wildcard ?? false}
                  onChange={(e) =>
                    p.setParams({ use_wildcard: e.target.checked })
                  }
                />
                Wildcard
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={p.params.use_regex ?? false}
                  onChange={(e) =>
                    p.setParams({ use_regex: e.target.checked })
                  }
                />
                Regex
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={p.params.use_ocr ?? false}
                  onChange={(e) =>
                    p.setParams({ use_ocr: e.target.checked })
                  }
                />
                OCR
              </label>
            </div>
          </div>

          <div className="adv-group">
            <div className="adv-group-label">Boolean expression (overrides terms)</div>
            <input
              type="text"
              placeholder="(budget OR revenue) AND NOT draft"
              value={p.params.expression ?? ""}
              onChange={(e) =>
                p.setParams({ expression: e.target.value || null })
              }
            />
          </div>

          {/* Context & proximity — moved out of the filters grid so
              the four numeric tweaks live with their conceptual home
              (the search expression). */}
          <div className="adv-grid adv-grid-cols-4">
            <label>
              Word proximity
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
            <label>
              Line proximity
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
            <label>
              Lines before
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
            <label>
              Lines after
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
            <label>
              Exclude
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
            <label>
              File types
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
            <label>
              Specific files
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
            <label>
              Range filter
              <input
                type="text"
                placeholder="amount:1000..5000"
                value={p.params.range_filters ?? ""}
                onChange={(e) =>
                  p.setParams({ range_filters: e.target.value || null })
                }
              />
            </label>
            <label>
              Cores
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
            <label>
              Max file size (MB)
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

          {/* Output formats — moved here from Step 3. TXT and DOCX are
              always generated; these are the optional formats. */}
          <div className="adv-group">
            <div className="adv-group-label">
              Output formats <span className="muted small">(TXT and DOCX always generated)</span>
            </div>
            <div className="adv-checkrow">
              <label>
                <input
                  type="checkbox"
                  checked={p.outputCsv}
                  onChange={(e) => p.setOutputCsv(e.target.checked)}
                />
                CSV
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={p.outputJson}
                  onChange={(e) => p.setOutputJson(e.target.checked)}
                />
                JSON
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={p.outputPdf}
                  onChange={(e) => p.setOutputPdf(e.target.checked)}
                />
                PDF
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={p.outputHtml}
                  onChange={(e) => p.setOutputHtml(e.target.checked)}
                />
                HTML
              </label>
              <label className="delete-on-close-adv">
                <input
                  type="checkbox"
                  checked={p.deleteOnClose}
                  onChange={(e) => p.setDeleteOnClose(e.target.checked)}
                />
                Delete on Close
              </label>
            </div>
            <p className="muted small">
              peekdocs never modifies or deletes your own documents — Delete on Close removes only files peekdocs created (results, the search index, etc.) when you close the app.
            </p>
          </div>

          {/* Output-targeting fields — still visual only in Phase 0;
              the web backend returns JSON rather than writing files. */}
          <div className="adv-group output-stub">
            <div className="adv-group-label">
              Output settings <span className="muted">(visual only — backend returns JSON, doesn't write files yet)</span>
            </div>
            <div className="adv-grid">
              <label>
                Save report as
                <input type="text" placeholder="my_report" disabled />
              </label>
              <label>
                Append to
                <input type="text" placeholder="archive" disabled />
              </label>
              <label>
                Output dir
                <input type="text" placeholder="~/peekdocs_reports" disabled />
              </label>
            </div>
            <div className="adv-checkrow">
              <label><input type="checkbox" disabled /> Timestamp filename</label>
              <label><input type="checkbox" disabled /> Clear history on close</label>
              <label><input type="checkbox" disabled /> Restrict file permissions</label>
              <label><input type="checkbox" disabled /> Notify when search complete</label>
            </div>
          </div>

          <div className="adv-buttons">
            <button onClick={() => alert("Save Defaults (stub)")}>
              Save as Defaults
            </button>
            <button onClick={() => alert("Restore Saved Defaults (stub)")}>
              Restore Saved Defaults
            </button>
            <button onClick={() => alert("Restore Factory (stub)")}>
              Restore Factory Settings
            </button>
            <button onClick={() => alert("Reset All Fields (stub)")}>
              Reset All Fields
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
