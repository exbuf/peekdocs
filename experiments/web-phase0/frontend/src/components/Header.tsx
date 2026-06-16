import { useEffect, useState } from "react";
import { useI18n } from "../i18n";

interface HeaderProps {
  tooltipsOn: boolean;
  setTooltipsOn: (v: boolean) => void;
  lang: string;
  setLang: (v: string) => void;
}

export default function Header({ tooltipsOn, setTooltipsOn, lang, setLang }: HeaderProps) {
  const { t } = useI18n();
  const tip = (s: string): string | undefined => (tooltipsOn ? s : undefined);
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
        <label
          className="lang-picker"
          title={tip(t("language_picker_label", "Choose UI language"))}
        >
          🌍
          <select
            value={lang}
            onChange={(e) => setLang(e.target.value)}
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
          title={tip(t("tooltips_button_tooltip", "Enable/disable hover tooltips"))}
        >
          {tooltipsOn
            ? t("tooltips_on_label", "Tooltips: ON")
            : t("tooltips_off_label", "Tooltips: OFF")}
        </button>
      </div>
    </header>
  );
}
