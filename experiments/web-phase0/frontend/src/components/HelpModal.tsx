import Modal from "./Modal";
import { useI18n } from "../i18n";

interface Props {
  onClose: () => void;
}

/**
 * Getting Started — mirrors the tkinter Help "?" popup with the same
 * four-step intro plus a short paragraph on each Run mode.
 */
export default function HelpModal({ onClose }: Props) {
  const { t } = useI18n();

  return (
    <Modal title={t("help_modal_title", "Getting Started with peekdocs")} onClose={onClose} width={600}>
      <p className="muted small">
        {t(
          "help_intro",
          "peekdocs searches across 100+ file types — Word, PDF, Excel, email, source code, archives, and more — locally on your machine. Nothing is uploaded anywhere."
        )}
      </p>

      <div className="help-step">
        <span className="help-step-num">1</span>
        <div className="help-step-body">
          <h4>{t("step_1_label", "Step 1")} — {t("help_step_1_title", "Choose a folder")}</h4>
          <p>
            {t(
              "help_step_1_body",
              "Click Browse to pick a folder, +Folder to add more (semicolon-separated), or Single File to search just one file."
            )}
          </p>
        </div>
      </div>

      <div className="help-step">
        <span className="help-step-num">2</span>
        <div className="help-step-body">
          <h4>{t("step_2_label", "Step 2")} — {t("help_step_2_title", "Type search terms")}</h4>
          <p>
            {t(
              "help_step_2_body",
              "Type one or more terms separated by spaces. Use ↑/↓ to walk through recent searches. Save the current configuration by name to reload later."
            )}
          </p>
        </div>
      </div>

      <div className="help-step">
        <span className="help-step-num">3</span>
        <div className="help-step-body">
          <h4>{t("step_3_label", "Step 3")} — {t("help_step_3_title", "Configure with Advanced Search Options")}</h4>
          <p>
            {t(
              "help_step_3_body",
              "AND/OR mode, Whole Word, Use Index, Fuzzy, Wildcard, Regex, OCR — all live in the Advanced panel below. Pick which output formats to write (TXT and DOCX by default, plus CSV/JSON/PDF/HTML)."
            )}
          </p>
        </div>
      </div>

      <div className="help-step">
        <span className="help-step-num">4</span>
        <div className="help-step-body">
          <h4>{t("step_4_label", "Step 4")} — {t("help_step_4_title", "Run a search")}</h4>
          <p>
            {t(
              "help_step_4_body",
              "Three modes: Run Standard Search (the blue button) for the current configuration, Search Suites (green) for groups of saved searches, Regex Search (orange) for collections of regex patterns. After running, the report buttons below light up green for the formats that were written — click to open."
            )}
          </p>
        </div>
      </div>

      <p className="muted small" style={{ marginTop: 16 }}>
        {t(
          "help_extras",
          "The Tools menu in the footer has analysis tools (File Inventory, Duplicate Finder, Age Distribution), workflow tools (Diff Snapshots, Schedule Search, Indexes, Regex Tester), and maintenance (Clear Files, View All peekdocs Files, System Check)."
        )}
      </p>

      <div className="modal-buttons">
        <button onClick={onClose}>{t("close_button_label", "Close")}</button>
      </div>
    </Modal>
  );
}
