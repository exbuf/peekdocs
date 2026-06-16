import { useEffect, useState } from "react";

interface HeaderProps {
  tooltipsOn: boolean;
  setTooltipsOn: (v: boolean) => void;
  lang: string;
  setLang: (v: string) => void;
}

export default function Header({ tooltipsOn, setTooltipsOn, lang, setLang }: HeaderProps) {
  const [languages, setLanguages] = useState<Record<string, string>>({
    en: "English",
  });

  useEffect(() => {
    fetch("http://127.0.0.1:8000/i18n")
      .then((r) => r.json())
      .then((d: { languages: Record<string, string> }) => setLanguages(d.languages))
      .catch(() => {});
  }, []);

  return (
    <header className="app-header">
      <div className="brand">
        <span className="brand-icon">👀</span>
        <span className="brand-name">peekdocs</span>
      </div>
      <div className="header-controls">
        <label className="lang-picker">
          🌍
          <select
            value={lang}
            onChange={(e) => setLang(e.target.value)}
            title={tooltipsOn ? "Choose UI language" : undefined}
          >
            {Object.entries(languages).map(([code, name]) => (
              <option key={code} value={code}>
                {name}
              </option>
            ))}
          </select>
        </label>
        <button
          className={`tooltips-toggle ${tooltipsOn ? "on" : "off"}`}
          onClick={() => setTooltipsOn(!tooltipsOn)}
          title={tooltipsOn ? "Toggle tooltips off" : undefined}
        >
          Tooltips: {tooltipsOn ? "ON" : "OFF"}
        </button>
      </div>
    </header>
  );
}
