# Contributing translations to peekdocs

Thanks for your interest in helping with peekdocs's internationalization. This document covers the experimental partial-i18n surface that ships with v1.1.4 — what's there, what's missing, how to fix an existing translation, and how to add a new language.

If you're looking for general contribution guidance (bug reports, code PRs, development setup), see [CONTRIBUTING.md](CONTRIBUTING.md). This document is i18n-specific.

## Current state

peekdocs ships with five languages: **English, Español, Français, Deutsch, 日本語** — about 102 translation keys × 5 languages = 510 entries. The translations cover the main page workflow surface (Search row, options row, three Run buttons, Status / Results Preview / Clear Preview, bottom-row navigation, Delete on Close, App Size / Language labels) plus the Advanced Search Options panel labels.

**Translation-quality disclosure.** The initial translations to date were authored by an AI assistant (Claude) — non-native for Spanish, French, German, and Japanese. Grammar parses; idiom may not. **Native-speaker corrections are exactly what this document is asking for.**

The current scope is a deliberate first cut, not a complete localization. The full inventory of what is and isn't translated lives in [`peekdocs/i18n.py`](peekdocs/i18n.py)'s module docstring — that file is the canonical source for "what's already translatable" at any given moment.

## What contributions we welcome (priority order)

1. **Corrections to existing translations.** A native speaker spotting awkward phrasing, wrong register, missing typographic conventions, or just-plain-incorrect translations is the highest-value contribution. Even one-character fixes (curly quotes, full-width punctuation, space-before-colon in French) are welcome.
2. **Filling in deferred surfaces in an already-supported language.** The next batches of strings to translate are the Advanced Search Options panel tooltips, the Tools-menu popups, and the help popups. Each of those is mechanical — find the English string, add the translation row.
3. **Adding a new language.** Welcomed, but please open an issue first to discuss — translations are a long-term maintenance commitment, and we want to be honest about whether the language has enough community demand to justify carrying it forward across future releases.

## Priority for now: corrections > new languages

If you're a native speaker of one of the five languages already shipped, the highest-leverage thing you can do is review the current translations in [`peekdocs/i18n.py`](peekdocs/i18n.py) and open a PR fixing whatever sounds awkward, wrong-register, or just unidiomatic. A translation review pass by a single native speaker per language is what would let peekdocs honestly mark the non-English UI as "native-reviewed" rather than "AI-authored."

## How to submit a translation correction

1. Fork peekdocs on GitHub and create a branch (`git checkout -b i18n-ja-tooltips-pass`).
2. Open [`peekdocs/i18n.py`](peekdocs/i18n.py). Find the language sub-dict (the `"ja": { ... }` block, for example) and edit the strings.
3. Verify your changes load: `python -c "from peekdocs.i18n import t, set_language; set_language('ja'); print(t('readme_button_label'))"`.
4. Launch the GUI and switch to the language you changed: `peekdocs-gui`, then pick the language from the picker in the preview-header row. Confirm the labels read naturally.
5. Open a PR. **In the PR description, please disclose your native-language background** — "native Japanese speaker, ~15 years software localization experience" or "fluent Spanish (L2), translated this professionally for 5 years" or whatever fits. We use the disclosure to weigh corrections; we won't reject a PR for "L2 with strong fluency" status, but we do want it visible to future readers of the PR.
6. Keep PRs focused — one language at a time, ideally one logical batch (e.g., "Japanese button labels," not "all Japanese translations + a code refactor").

## How to add a new language

If you want to add a sixth language:

1. **Open an issue first** describing the language and your willingness to maintain corrections across future releases. We want to be honest about the carrying cost — every new translatable string in future releases needs to be translated in every supported language, and unmaintained translations drift faster than English source strings change.
2. Add the language to the `LANGUAGES` dict at the top of `peekdocs/i18n.py` (ISO 639-1 code as key, native-language name as value).
3. Add a sub-dict to `_STRINGS` with translations for every key the English row carries. Missing keys fall back through the active-language → English → key-itself chain, so a partial sub-dict won't crash anything — but the picker UI doesn't currently distinguish "fully translated" from "partial fallback to English." Aim for completeness or clearly mark in the PR which strings need follow-up.
4. Launch the GUI and verify the picker shows the new language and switching to it doesn't leak English strings into the translated surface.
5. Open a PR with the same native-language disclosure as above.

## Style notes by language

These are conventions the existing translations try to follow — feel free to correct any that fell short.

- **Spanish.** Use formal register (`Examinar`, `Guardar`) over informal. Inverted question marks at the start of questions (`¿…?`). Native-language name in the picker is `Español` (capitalized).
- **French.** Use the typographic non-breaking space before `?`, `!`, `:`, `;` (`Statut :`, `Mot entier`, `Tooltips : OUI`). The straight ASCII space works at the source-code level; the rendered glyph is what matters. Native-language name is `Français`.
- **German.** Use compound nouns where natural (`Suchordner`, `Dateiinventar`). Capitalize nouns. `ß` vs `ss` follows the 1996 reform (use `ß` after long vowels and diphthongs: `schließen`, `Schließen`). Native-language name is `Deutsch`.
- **Japanese.** Use 全角 (full-width) punctuation where appropriate (`？`, `：` — but the experiment currently uses half-width `:` after English-style labels, e.g. `ステータス:`; either is defensible). Mix kanji + hiragana + katakana naturally — katakana for foreign loanwords (ステップ, スイート), kanji for content words, hiragana for grammar particles. Native-language name is `日本語`. The `README` button currently translates to `お読みください` ("please read") as a localization choice; many real Japanese OSS projects just keep `README` — feel free to argue either way in a PR.

## Width caveats

GUI labels live in fixed-width buttons in many places. German is typically ~30% wider than English, Japanese CJK glyphs are wider per character, and French is often 20% longer. If your translation overflows a button or wraps in an ugly place, you have two options:

1. **Use a shorter natural alternative** — abbreviations or alternate phrasings that fit. Reasonable for narrow buttons (the OR / AND button widths are particularly tight).
2. **Open a separate PR widening the button** with a note about which language(s) needed the space. We'd rather widen the button than ship truncated UI.

## What's NOT yet in scope (deferred surface)

The following are intentionally untranslated in the current experiment. PRs that just translate them in `i18n.py` won't actually surface anything because the call sites haven't been routed through `t()` yet:

- Status line dynamic text (`Searching ({terms})...`, etc.) — needs a format-arg template machinery that doesn't exist yet
- Advanced Search Options panel **tooltips**
- Help popups (Getting Started content, Search Wizard, Regex Wizard, Regex Tester, Recent Searches, Advanced help)
- Tools-menu popups (Bookmarks, Diff Snapshots, Indexes, Schedule Search, Search History, Clear Files)
- Search Suites popup, Regex Search popup, Search Wizard popup, Diff Snapshots popup
- Confirmation dialogs and error popups
- CLI banner / `--check` / `--version` / `--help` output
- Notifier body text, watcher status messages, report file content

If you want to expand the translatable surface, the work is:

1. Find the English string in the appropriate file.
2. Add an i18n key + translations for every language.
3. Refactor the creation site to use `t(key)`, stashing a widget reference on `self` so it can be re-rendered.
4. Extend `_set_language` in `peekdocs/gui/_mixin_build.py` to call `.configure(text=t(...))` on the new widget.
5. For tooltips, refactor the creation site to stash the `Tooltip` reference on `self` and rewrite `self._foo_tooltip.text = t(...)` in `_set_language`.

That's about 2-3 lines of code per translatable string, plus the translation entries. **Open an issue first if you want to take on a big batch** — a casual contributor and the maintainer should agree on scope before you put in hours of work.

## Architecture in 30 seconds

```python
# peekdocs/i18n.py
LANGUAGES = {"en": "English", "es": "Español", "fr": "Français", "de": "Deutsch", "ja": "日本語"}
_current = "en"
_STRINGS = {"en": {key: english_text, ...}, "es": {key: spanish_text, ...}, ...}

def set_language(code): ...  # updates module-level _current
def t(key): ...              # returns _STRINGS[_current].get(key, _STRINGS["en"].get(key, key))
```

That's the whole pattern — no gettext, no .po / .mo files, no external deps. Adding a key adds a row; adding a language adds a column. The trade-off is that the translations live in Python source rather than a translator-friendly format like .po; translator-friendly tooling is on the table if a translation community ever forms.

## License

By contributing translations, you agree that your contributions will be licensed under the [MIT License](LICENSE) along with the rest of peekdocs.

## Questions?

Open an issue, or hop into an existing i18n discussion on the [issues page](https://github.com/exbuf/peekdocs/issues?q=label%3Ai18n).
