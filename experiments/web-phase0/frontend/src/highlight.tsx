import type { ReactNode } from "react";

/**
 * Build a regex that matches any of the supplied search terms inside
 * a result line, mirroring peekdocs's search semantics:
 *   - case-insensitive
 *   - regex mode  → use the terms as patterns directly
 *   - wildcard    → translate * → .* and ? → .
 *   - whole word  → wrap each in \b…\b
 *   - otherwise   → escape regex special chars, literal substring match
 *
 * For Boolean expressions like "(budget OR revenue) AND NOT draft" we
 * extract every alphanumeric word and exclude the NOT-prefixed ones —
 * good enough for highlighting at the result-rendering layer.
 */
function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function wildcardToRegex(s: string): string {
  // Escape everything, then un-escape the wildcards.
  return escapeRegex(s).replace(/\\\*/g, ".*").replace(/\\\?/g, ".");
}

function extractExpressionTerms(expr: string): string[] {
  // Collect every non-keyword word and drop the ones that follow NOT.
  const tokens = expr.split(/\s+/);
  const out: string[] = [];
  for (let i = 0; i < tokens.length; i++) {
    const tok = tokens[i].replace(/[()]/g, "");
    if (!tok) continue;
    const upper = tok.toUpperCase();
    if (upper === "AND" || upper === "OR" || upper === "NOT") continue;
    if (i > 0 && tokens[i - 1].toUpperCase() === "NOT") continue;
    out.push(tok);
  }
  return out;
}

function buildHighlightRegex(
  terms: string[],
  expression: string | null | undefined,
  useRegex: boolean,
  useWildcard: boolean,
  useWholeWord: boolean
): RegExp | null {
  let sources = terms.filter(Boolean);
  if (expression && expression.trim()) {
    sources = extractExpressionTerms(expression);
  }
  if (sources.length === 0) return null;

  const patterns = sources
    .map((t) => {
      let p: string;
      if (useRegex) p = t;
      else if (useWildcard) p = wildcardToRegex(t);
      else p = escapeRegex(t);
      if (useWholeWord) p = `\\b(?:${p})\\b`;
      return p;
    })
    .filter(Boolean);

  if (patterns.length === 0) return null;
  try {
    return new RegExp(`(${patterns.join("|")})`, "gi");
  } catch {
    // If the user typed an invalid regex, don't blow up — just don't
    // highlight anything.
    return null;
  }
}

export interface HighlightContext {
  terms: string[];
  expression: string | null | undefined;
  useRegex: boolean;
  useWildcard: boolean;
  useWholeWord: boolean;
}

export function highlightLine(line: string, ctx: HighlightContext): ReactNode {
  const re = buildHighlightRegex(
    ctx.terms,
    ctx.expression,
    ctx.useRegex,
    ctx.useWildcard,
    ctx.useWholeWord
  );
  if (!re) return line;

  const parts: ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  while ((match = re.exec(line)) !== null) {
    if (match.index > lastIndex) {
      parts.push(line.substring(lastIndex, match.index));
    }
    parts.push(
      <mark key={`m-${match.index}`} className="hl">
        {match[0]}
      </mark>
    );
    lastIndex = match.index + match[0].length;
    // Guard against zero-width matches (e.g. user typed an empty regex).
    if (match[0].length === 0) re.lastIndex++;
  }
  if (lastIndex < line.length) parts.push(line.substring(lastIndex));
  return parts;
}
