import { useState, useRef, useEffect } from "react";

// Mirrors the tkinter Tools menu structure. Items are stubs for now —
// clicking shows a placeholder alert. Phase 1 wires them to backend
// endpoints.
const TOOLS_ITEMS = [
  { label: "Collection Summary", section: "Analysis" },
  { label: "File Inventory", section: "Analysis" },
  { label: "File Age Distribution", section: "Analysis" },
  { label: "Duplicate Finder", section: "Analysis" },
  { label: "Large Files", section: "Analysis" },
  { label: "Empty Files", section: "Analysis" },
  { label: "Recent Changes", section: "Analysis" },
  { label: "Protected Files", section: "Analysis" },
  { label: "Unsearchable Files", section: "Analysis" },
  { label: "Search History", section: "Workflows" },
  { label: "Bookmarks", section: "Workflows" },
  { label: "Diff Snapshots", section: "Workflows" },
  { label: "Schedule Search", section: "Workflows" },
  { label: "Indexes", section: "Workflows" },
  { label: "Regex Tester", section: "Workflows" },
  { label: "Clear Files", section: "Maintenance" },
  { label: "Clean Folder", section: "Maintenance" },
  { label: "View All peekdocs Files", section: "Maintenance" },
  { label: "System Check (--check)", section: "Maintenance" },
];

export default function Footer() {
  const [toolsOpen, setToolsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setToolsOpen(false);
      }
    }
    if (toolsOpen) document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [toolsOpen]);

  // Group items by section.
  const sections = Array.from(new Set(TOOLS_ITEMS.map((i) => i.section)));

  return (
    <footer className="app-footer">
      <a href="https://github.com/exbuf/peekdocs#readme" target="_blank" rel="noreferrer">
        README
      </a>
      <a href="https://github.com/exbuf/peekdocs/blob/main/docs/USER_GUIDE.md" target="_blank" rel="noreferrer">
        User Guide
      </a>
      <button className="link-btn" onClick={() => alert("About peekdocs (stub)")}>
        About
      </button>
      <div className="tools-menu" ref={menuRef}>
        <button
          className={`link-btn tools-btn ${toolsOpen ? "open" : ""}`}
          onClick={() => setToolsOpen(!toolsOpen)}
        >
          Tools ▾
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
                      alert(`Tools → ${i.label} (stub — Phase 1 wires this up)`);
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
