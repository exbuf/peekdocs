import { useState, useRef, useEffect } from "react";
import { useI18n } from "../i18n";

const TOOLS_ITEMS = [
  { label: "File Inventory", section: "Analysis", tool: "file-inventory" },
  { label: "File Age Distribution", section: "Analysis", tool: "age-distribution" },
  { label: "Duplicate Finder", section: "Analysis", tool: "duplicates" },
  { label: "Large Files", section: "Analysis", tool: "large-files" },
  { label: "Empty Files", section: "Analysis", tool: "empty-files" },
  { label: "Recent Changes", section: "Analysis", tool: "recent-changes" },
  { label: "Protected Files", section: "Analysis", tool: "protected-files" },
  { label: "Unsearchable Files", section: "Analysis", tool: "unsearchable-files" },
  { label: "Search History", section: "Workflows", tool: "history" },
  { label: "Bookmarks", section: "Workflows", tool: "bookmarks" },
  { label: "Diff Snapshots", section: "Workflows", tool: "diff" },
  { label: "Schedule Search", section: "Workflows", tool: "schedule" },
  { label: "Indexes", section: "Workflows", tool: "indexes" },
  { label: "Regex Tester", section: "Workflows", tool: "regex-tester" },
  { label: "Clear Files", section: "Maintenance", tool: "clear-files" },
  { label: "Clean Folder", section: "Maintenance", tool: "clean-folder" },
  { label: "View All peekdocs Files", section: "Maintenance", tool: "view-all" },
  { label: "System Check (--check)", section: "Maintenance", tool: "system-check" },
];

export type ToolId = string;

interface FooterProps {
  onAbout: () => void;
  onTool: (toolId: ToolId) => void;
  tooltipsOn: boolean;
}

export default function Footer({ onAbout, onTool, tooltipsOn }: FooterProps) {
  const { t } = useI18n();
  const [toolsOpen, setToolsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const tip = (s: string): string | undefined => (tooltipsOn ? s : undefined);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setToolsOpen(false);
      }
    }
    if (toolsOpen) document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [toolsOpen]);

  const sections = Array.from(new Set(TOOLS_ITEMS.map((i) => i.section)));

  return (
    <footer className="app-footer">
      <a
        href="https://github.com/exbuf/peekdocs#readme"
        target="_blank"
        rel="noreferrer"
        title={tip(t("readme_button_tooltip", "Open the peekdocs README on GitHub"))}
      >
        {t("readme_button_label", "README")}
      </a>
      <a
        href="https://github.com/exbuf/peekdocs/blob/main/docs/USER_GUIDE.md"
        target="_blank"
        rel="noreferrer"
        title={tip(t("user_guide_button_tooltip", "Open the User Guide"))}
      >
        {t("user_guide_button_label", "User Guide")}
      </a>
      <button
        className="link-btn"
        onClick={onAbout}
        title={tip(t("about_button_tooltip", "About peekdocs — version, license"))}
      >
        {t("about_button_label", "About")}
      </button>
      <div className="tools-menu" ref={menuRef}>
        <button
          className={`link-btn tools-btn ${toolsOpen ? "open" : ""}`}
          onClick={() => setToolsOpen(!toolsOpen)}
          title={tip(t("tools_button_tooltip", "Tools menu — analysis, workflows, maintenance"))}
        >
          {t("tools_button_label", "Tools")} ▾
        </button>
        {toolsOpen && (
          <div className="tools-dropdown">
            {sections.map((sec) => (
              <div key={sec} className="tools-section">
                <div className="tools-section-label">{sec}</div>
                {TOOLS_ITEMS.filter((i) => i.section === sec).map((i) => (
                  <button
                    key={i.label}
                    className="tools-item"
                    onClick={() => {
                      setToolsOpen(false);
                      onTool(i.tool);
                    }}
                  >
                    {i.label}
                  </button>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>
    </footer>
  );
}
