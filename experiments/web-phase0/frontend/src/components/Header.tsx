import { useState } from "react";

const LANGUAGES = [
  { code: "en", name: "English" },
  { code: "es", name: "Español" },
  { code: "fr", name: "Français" },
  { code: "de", name: "Deutsch" },
  { code: "ja", name: "日本語" },
  { code: "zh-CN", name: "简体中文" },
  { code: "pt-BR", name: "Português brasileiro" },
];

interface HeaderProps {
  tooltipsOn: boolean;
  setTooltipsOn: (v: boolean) => void;
}

export default function Header({ tooltipsOn, setTooltipsOn }: HeaderProps) {
  const [lang, setLang] = useState("en");

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
            title="Language (visual stub — translation not yet wired)"
          >
            {LANGUAGES.map((l) => (
              <option key={l.code} value={l.code}>
                {l.name}
              </option>
            ))}
          </select>
        </label>
        <button
          className={`tooltips-toggle ${tooltipsOn ? "on" : "off"}`}
          onClick={() => setTooltipsOn(!tooltipsOn)}
          title="Toggle tooltips on / off"
        >
          Tooltips: {tooltipsOn ? "ON" : "OFF"}
        </button>
      </div>
    </header>
  );
}
