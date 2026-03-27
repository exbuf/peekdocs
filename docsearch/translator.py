"""Translate docsearch CLI commands into plain English, including regex and wildcard patterns."""

import re
import shlex
try:
    import re._parser as sre_parse
except ImportError:
    import sre_parse

# Max recursion depth for regex token tree
_MAX_DEPTH = 10

# Character descriptions for common punctuation
_CHAR_NAMES = {
    ord("-"): "a dash",
    ord("."): "a dot",
    ord("@"): "an @ sign",
    ord("_"): "an underscore",
    ord(" "): "a space",
    ord(","): "a comma",
    ord(";"): "a semicolon",
    ord(":"): "a colon",
    ord("/"): "a slash",
    ord("\\"): "a backslash",
    ord("("): "an open parenthesis",
    ord(")"): "a close parenthesis",
    ord("$"): "a dollar sign",
    ord("#"): "a hash sign",
    ord("%"): "a percent sign",
    ord("+"): "a plus sign",
    ord("="): "an equals sign",
    ord("!"): "an exclamation mark",
    ord("?"): "a question mark",
    ord("&"): "an ampersand",
    ord("*"): "an asterisk",
    ord("'"): "an apostrophe",
    ord('"'): "a quote",
    ord("^"): "a caret",
    ord("~"): "a tilde",
    ord("|"): "a pipe",
    ord("<"): "a less-than sign",
    ord(">"): "a greater-than sign",
    ord("["): "an open bracket",
    ord("]"): "a close bracket",
    ord("{"): "an open brace",
    ord("}"): "a close brace",
}

# Category constants — these are the values that appear inside (CATEGORY, value) tokens
_CATEGORY_DIGIT = sre_parse.CATEGORY_DIGIT
_CATEGORY_NOT_DIGIT = sre_parse.CATEGORY_NOT_DIGIT
_CATEGORY_SPACE = sre_parse.CATEGORY_SPACE
_CATEGORY_NOT_SPACE = sre_parse.CATEGORY_NOT_SPACE
_CATEGORY_WORD = sre_parse.CATEGORY_WORD
_CATEGORY_NOT_WORD = sre_parse.CATEGORY_NOT_WORD


def _describe_char(code):
    """Describe a single character code in English."""
    if code in _CHAR_NAMES:
        return _CHAR_NAMES[code]
    c = chr(code)
    if c.isalnum():
        return f'"{c}"'
    return f'"{c}"'


def _describe_category(category_value):
    """Describe an sre_parse category in English."""
    if category_value == _CATEGORY_DIGIT:
        return "a digit"
    if category_value == _CATEGORY_NOT_DIGIT:
        return "a non-digit"
    if category_value == _CATEGORY_SPACE:
        return "a whitespace character"
    if category_value == _CATEGORY_NOT_SPACE:
        return "a non-whitespace character"
    if category_value == _CATEGORY_WORD:
        return "a word character"
    if category_value == _CATEGORY_NOT_WORD:
        return "a non-word character"
    return "a character"


def _describe_in(items):
    """Describe a character class [...] from sre_parse IN items."""
    negate = False
    parts = []
    for item_type, item_value in items:
        if item_type == sre_parse.NEGATE:
            negate = True
        elif item_type == sre_parse.LITERAL:
            parts.append(_describe_char(item_value))
        elif item_type == sre_parse.RANGE:
            lo, hi = item_value
            lo_c, hi_c = chr(lo), chr(hi)
            if lo_c == "0" and hi_c == "9":
                parts.append("a digit")
            elif lo_c == "a" and hi_c == "z":
                parts.append("a lowercase letter")
            elif lo_c == "A" and hi_c == "Z":
                parts.append("an uppercase letter")
            else:
                parts.append(f'"{lo_c}" to "{hi_c}"')
        elif item_type == sre_parse.CATEGORY:
            parts.append(_describe_category(item_value))
    desc = ", ".join(parts) if parts else "a character"
    if negate:
        return f"any character except {desc}"
    if len(parts) == 1:
        return parts[0]
    return f"[{desc}]"


def _describe_quantity(lo, hi, inner_desc):
    """Describe a repeated element with quantity."""
    maxrepeat = sre_parse.MAXREPEAT
    if lo == 0 and hi == maxrepeat:
        return f"zero or more of {inner_desc}"
    if lo == 1 and hi == maxrepeat:
        return f"one or more of {inner_desc}"
    if lo == 0 and hi == 1:
        return f"optional {inner_desc}"
    if lo == hi:
        return f"{lo} of {inner_desc}"
    if hi == maxrepeat:
        return f"{lo} or more of {inner_desc}"
    return f"{lo} to {hi} of {inner_desc}"


def _merge_literals(parts):
    """Merge consecutive quoted single-character descriptions into words.

    E.g. ['"c"', '"a"', '"t"'] → ['"cat"']
    """
    merged = []
    run = []
    for p in parts:
        # Check if this is a single quoted character like '"x"'
        if len(p) == 3 and p.startswith('"') and p.endswith('"'):
            run.append(p[1])
        else:
            if run:
                merged.append(f'"{"".join(run)}"')
                run = []
            merged.append(p)
    if run:
        merged.append(f'"{"".join(run)}"')
    return merged


def _describe_tokens(tokens, depth=0):
    """Recursively describe a list of sre_parse tokens in English."""
    if depth > _MAX_DEPTH:
        return ["(complex pattern)"]
    parts = []
    for token_type, token_value in tokens:
        if token_type == sre_parse.LITERAL:
            parts.append(_describe_char(token_value))
        elif token_type == sre_parse.NOT_LITERAL:
            parts.append(f"any character except {_describe_char(token_value)}")
        elif token_type == sre_parse.ANY:
            parts.append("any character")
        elif token_type == sre_parse.AT:
            if token_value == sre_parse.AT_BEGINNING:
                parts.append("start of line")
            elif token_value == sre_parse.AT_END:
                parts.append("end of line")
            elif token_value == sre_parse.AT_BOUNDARY:
                parts.append("word boundary")
            elif token_value == sre_parse.AT_NON_BOUNDARY:
                parts.append("non-word-boundary")
            elif token_value == sre_parse.AT_BEGINNING_STRING:
                parts.append("start of string")
            elif token_value == sre_parse.AT_END_STRING:
                parts.append("end of string")
            else:
                parts.append("anchor")
        elif token_type == sre_parse.IN:
            parts.append(_describe_in(token_value))
        elif token_type == sre_parse.BRANCH:
            # token_value is (None, [branch1_tokens, branch2_tokens, ...])
            _, branches = token_value
            branch_descs = []
            for branch in branches:
                desc_parts = _describe_tokens(branch, depth + 1)
                branch_descs.append(", ".join(desc_parts) if desc_parts else "(empty)")
            if len(branch_descs) == 2:
                parts.append(f"either {branch_descs[0]} or {branch_descs[1]}")
            else:
                last = branch_descs[-1]
                rest = ", ".join(branch_descs[:-1])
                parts.append(f"either {rest}, or {last}")
        elif token_type == sre_parse.SUBPATTERN:
            # token_value is (group_id, add_flags, del_flags, tokens)
            group_id, _add, _del, sub_tokens = token_value
            sub_parts = _describe_tokens(sub_tokens, depth + 1)
            sub_desc = ", ".join(sub_parts) if sub_parts else "(empty group)"
            parts.append(sub_desc)
        elif token_type in (sre_parse.MAX_REPEAT, sre_parse.MIN_REPEAT):
            lo, hi, sub_tokens = token_value
            sub_parts = _describe_tokens(sub_tokens, depth + 1)
            inner = ", ".join(sub_parts) if sub_parts else "something"
            parts.append(_describe_quantity(lo, hi, inner))
        elif token_type == sre_parse.CATEGORY:
            parts.append(_describe_category(token_value))
        elif token_type == sre_parse.GROUPREF:
            parts.append(f"(same as group {token_value})")
        else:
            parts.append("(pattern element)")
    return _merge_literals(parts)


# ── Known regex pattern recognition ──────────────────────────────
# Each entry: (compiled_regex_matching_the_pattern_itself, human_label, example)
# We match against the NORMALIZED pattern string to identify common shapes.

# _DIGIT matches: \d, [0-9], [0123456789]
_D = r'(?:\\d|\[0-9\]|\[0123456789\])'
# _SEP matches common separators: /, -, ., \s, and character classes like [\s.-]
_SEP_OPT = r'(?:\[[^\]]*\]\??|\\s\??|[/.\-])'
_SEP = r'(?:\[[^\]]*\]|\\s|[/.\-])'

_KNOWN_PATTERNS = [
    # Dates: MM/DD/YYYY, DD/MM/YYYY, M/D/YY variants
    (re.compile(
        r'^' + _D + r'\{1,2\}' + _SEP + _D + r'\{1,2\}' + _SEP + _D + r'\{2,4\}$'
        r'|^' + _D + r'\{2\}' + _SEP + _D + r'\{2\}' + _SEP + _D + r'\{2,4\}$'
        r'|^' + _D + r'\{4\}' + _SEP + _D + r'\{1,2\}' + _SEP + _D + r'\{1,2\}$'
        r'|^' + _D + r'\{4\}-' + _D + r'\{2\}-' + _D + r'\{2\}$'
    ), "a date", "MM/DD/YYYY or YYYY-MM-DD"),

    # US phone: 555-123-4567
    (re.compile(
        r'^' + _D + r'\{3\}' + _SEP + _D + r'\{3\}' + _SEP + _D + r'\{4\}$'
    ), "a US phone number", "555-123-4567"),

    # Phone with area code parens: (555) 123-4567
    # Matches: \(\d{3}\)\s?\d{3}-\d{4}  and  \(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}
    (re.compile(
        r'^\\\(\??' + _D + r'\{3\}\\\)\??' + _SEP_OPT + _D + r'\{3\}' + _SEP_OPT + _D + r'\{4\}$'
    ), "a phone number with area code", "(555) 123-4567"),

    # Email
    (re.compile(
        r'\[A-Za-z0-9[^]]*\]\+@\[A-Za-z0-9[^]]*\]'
        r'|\\w\+@\\w\+'
    ), "an email address", "user@example.com"),

    # Dollar amount: $45.99
    (re.compile(
        r'^\\\$' + _D + r'|^\\\$\[\\?d'
    ), "a dollar amount", "$45.99"),

    # SSN: 123-45-6789
    (re.compile(
        r'^' + _D + r'\{3\}' + _SEP + _D + r'\{2\}' + _SEP + _D + r'\{4\}$'
    ), "a Social Security Number (SSN)", "123-45-6789"),

    # IP address: 192.168.1.1
    (re.compile(
        _D + r'\{1,3\}\\?\.' + _D + r'\{1,3\}\\?\.' + _D + r'\{1,3\}\\?\.' + _D + r'\{1,3\}'
    ), "an IP address", "192.168.1.1"),

    # URL: https://example.com
    (re.compile(
        r'^https?\??://\\S\+'
        r'|^https?\??://\.'
    ), "a URL", "https://example.com"),

    # ZIP code: 12345 or 12345-6789
    (re.compile(
        _D + r'\{5\}.*' + _D + r'\{4\}'
    ), "a US ZIP code", "12345 or 12345-6789"),

    # Percentage: 92%
    (re.compile(
        _D + r'.*%'
    ), "a percentage", "92%"),

    # Fiscal quarter: Q1 2026
    (re.compile(
        r'^Q\[1-4\]'
    ), "a fiscal quarter", "Q1 2026"),
]


def _normalize_pattern(pattern):
    """Normalize a regex pattern string for matching against known patterns.

    Removes unnecessary escaping and anchors so that variations like
    \\d{1,2}\\/\\d{1,2}\\/\\d{2,4} and \\d{1,2}/\\d{1,2}/\\d{2,4}
    are treated the same.
    """
    # Remove unnecessary escape of characters that don't need escaping in regex
    result = pattern
    for ch in '/-:;,!@#~':
        result = result.replace('\\' + ch, ch)
    # Strip ^ and $ anchors
    if result.startswith('^'):
        result = result[1:]
    if result.endswith('$') and not result.endswith('\\$'):
        result = result[:-1]
    return result


def _identify_pattern(pattern):
    """Try to identify a well-known regex pattern and return a human label.

    Uses two strategies:
    1. Token-structure matching via sre_parse (immune to string formatting)
    2. Normalized string matching as fallback

    Returns (label, example) if recognized, or (None, None) if not.
    """
    # Strategy 1: parse tokens and check structure
    result = _identify_by_structure(pattern)
    if result[0]:
        return result

    # Strategy 2: normalized string matching
    normalized = _normalize_pattern(pattern)
    for compiled, label, example in _KNOWN_PATTERNS:
        if compiled.search(normalized):
            return label, example
    return None, None


def _is_digit_token(tokens):
    """Check if tokens represent a digit class (\\d, [0-9], etc.)."""
    if len(tokens) == 1:
        t_type, t_val = tokens[0]
        if t_type == sre_parse.IN:
            # Check if it's a digit category or 0-9 range
            for item_type, item_val in t_val:
                if item_type == sre_parse.CATEGORY and item_val == _CATEGORY_DIGIT:
                    return True
                if item_type == sre_parse.RANGE and item_val == (ord('0'), ord('9')):
                    return True
    return False


def _is_literal_char(tokens, char):
    """Check if tokens are a single literal character."""
    return len(tokens) == 1 and tokens[0][0] == sre_parse.LITERAL and tokens[0][1] == ord(char)


def _is_separator_token(token):
    """Check if a token is a separator (literal /, -, ., or \\s, or a character class)."""
    t_type, t_val = token
    if t_type == sre_parse.LITERAL:
        return chr(t_val) in '/-.'
    if t_type == sre_parse.IN:
        return True  # character class used as separator
    if t_type == sre_parse.CATEGORY:
        return t_val == _CATEGORY_SPACE
    return False


def _extract_digit_runs(tokens):
    """Extract a simplified structure from tokens: list of (type, lo, hi) tuples.

    Returns items like ('D', 1, 2) for digit repeat, ('S',) for separator,
    ('L', char) for literal, ('?', inner) for optional group, etc.
    Returns None if structure is too complex.
    """
    items = []
    # Strip anchors
    filtered = [(t, v) for t, v in tokens
                if t != sre_parse.AT]
    for t_type, t_val in filtered:
        if t_type in (sre_parse.MAX_REPEAT, sre_parse.MIN_REPEAT):
            lo, hi, sub = t_val
            if _is_digit_token(sub):
                items.append(('D', lo, hi))
            elif len(sub) == 1 and _is_separator_token(sub[0]):
                items.append(('S',))
            elif len(sub) == 1 and sub[0][0] == sre_parse.LITERAL:
                items.append(('L', chr(sub[0][1])))
            elif len(sub) == 1 and sub[0][0] == sre_parse.SUBPATTERN:
                items.append(('G',))  # group
            else:
                items.append(('?',))
        elif t_type == sre_parse.IN:
            if any(it == sre_parse.CATEGORY and iv == _CATEGORY_DIGIT
                   for it, iv in t_val):
                items.append(('D', 1, 1))
            elif any(it == sre_parse.RANGE and iv == (ord('0'), ord('9'))
                     for it, iv in t_val):
                items.append(('D', 1, 1))
            else:
                items.append(('S',))  # character class as separator
        elif t_type == sre_parse.LITERAL:
            c = chr(t_val)
            if c in '/-._':
                items.append(('S',))
            else:
                items.append(('L', c))
        elif t_type == sre_parse.CATEGORY:
            if t_val == _CATEGORY_DIGIT:
                items.append(('D', 1, 1))
            else:
                items.append(('?',))
        elif t_type == sre_parse.SUBPATTERN:
            _, _, _, sub = t_val
            items.append(('G',))
        else:
            items.append(('?',))
    return items


def _identify_by_structure(pattern):
    """Identify a pattern by parsing its token structure with sre_parse.

    This is immune to string formatting differences like escaped slashes,
    [0-9] vs \\d, anchors, etc.
    """
    try:
        tokens = list(sre_parse.parse(pattern))
    except Exception:
        return None, None

    # Unwrap if entire pattern is a single group: (\d{1,2}/\d{1,2}/\d{2,4})
    while (len(tokens) == 1 and tokens[0][0] == sre_parse.SUBPATTERN):
        _, _, _, sub = tokens[0][1]
        tokens = list(sub)

    items = _extract_digit_runs(tokens)
    if items is None:
        return None, None

    # Strip non-essential items for matching
    core = [i for i in items if i[0] != '?']

    # Date: D{1,2} SEP D{1,2} SEP D{2,4} or D{4} SEP D{1,2} SEP D{1,2}
    if len(core) == 5:
        if (core[0][0] == 'D' and core[1][0] == 'S' and core[2][0] == 'D'
                and core[3][0] == 'S' and core[4][0] == 'D'):
            d1, d2, d3 = core[0], core[2], core[4]
            # MM/DD/YYYY: small-sep-small-sep-large
            if d1[2] <= 2 and d2[2] <= 2 and d3[2] >= 2:
                return "a date", "MM/DD/YYYY or YYYY-MM-DD"
            # YYYY-MM-DD: large-sep-small-sep-small
            if d1[1] >= 4 and d2[2] <= 2 and d3[2] <= 2:
                return "a date", "MM/DD/YYYY or YYYY-MM-DD"

    # US phone: D{3} SEP D{3} SEP D{4}
    if len(core) == 5:
        if (core[0][0] == 'D' and core[1][0] == 'S' and core[2][0] == 'D'
                and core[3][0] == 'S' and core[4][0] == 'D'):
            d1, d2, d3 = core[0], core[2], core[4]
            if d1[1:] == (3, 3) and d2[1:] == (3, 3) and d3[1:] == (4, 4):
                return "a US phone number", "555-123-4567"

    # SSN: D{3} SEP D{2} SEP D{4}
    if len(core) == 5:
        if (core[0][0] == 'D' and core[1][0] == 'S' and core[2][0] == 'D'
                and core[3][0] == 'S' and core[4][0] == 'D'):
            d1, d2, d3 = core[0], core[2], core[4]
            if d1[1:] == (3, 3) and d2[1:] == (2, 2) and d3[1:] == (4, 4):
                return "a Social Security Number (SSN)", "123-45-6789"

    # IP address: D{1,3} . D{1,3} . D{1,3} . D{1,3}
    if len(core) == 7:
        if all(core[i][0] == 'D' for i in (0, 2, 4, 6)):
            if all(core[i][0] == 'S' for i in (1, 3, 5)):
                if all(core[i][1:] == (1, 3) for i in (0, 2, 4, 6)):
                    return "an IP address", "192.168.1.1"

    # Phone with area code: various forms with parens + D{3} + D{3} + D{4}
    # Check for 3-3-4 digit pattern with extras (parens, optional chars)
    digit_groups = [i for i in items if i[0] == 'D']
    if len(digit_groups) == 3:
        d1, d2, d3 = digit_groups
        if d1[1:] == (3, 3) and d2[1:] == (3, 3) and d3[1:] == (4, 4):
            # Has literal parens in the pattern → phone with area code
            has_paren = any(i[0] == 'L' and i[1] in '()' for i in items)
            if has_paren:
                return "a phone number with area code", "(555) 123-4567"

    return None, None


def _translate_regex(pattern):
    """Translate a regex pattern into plain English.

    Returns a human-readable description of what the regex matches.
    If the pattern matches a well-known shape (date, phone, email, etc.),
    returns just the label and example — no character-level breakdown.
    Only falls back to token-level description for unrecognized patterns.

    For patterns with top-level alternation (A|B|C), each branch is
    identified separately.
    """
    # Check for top-level alternation — split on | and identify each branch
    branches = _split_top_level(pattern)
    if len(branches) > 1:
        branch_descs = []
        for branch_str in branches:
            # Strip outer parens from grouped branches like (\d{3})
            stripped = branch_str.strip()
            if stripped.startswith("(") and stripped.endswith(")"):
                stripped = stripped[1:-1]
            label, example = _identify_pattern(stripped)
            if label:
                branch_descs.append(f"{label} (e.g. {example})")
            else:
                branch_descs.append(_translate_regex_tokens(stripped))
        if len(branch_descs) == 2:
            return f"either {branch_descs[0]} or {branch_descs[1]}"
        last = branch_descs[-1]
        rest = ", ".join(branch_descs[:-1])
        return f"either {rest}, or {last}"

    # Not alternation — try to identify the whole pattern
    label, example = _identify_pattern(pattern)
    if label:
        return f"{label} (e.g. {example})"

    # Unrecognized — describe token by token
    return _translate_regex_tokens(pattern)


def _translate_regex_tokens(pattern):
    """Describe a regex pattern token by token (fallback for unrecognized patterns)."""
    try:
        parsed = list(sre_parse.parse(pattern))
        parts = _describe_tokens(parsed)
        if not parts:
            return f'pattern "{pattern}"'
        return ", ".join(parts)
    except Exception:
        return f'pattern "{pattern}"'


def _split_top_level(pattern):
    """Split a regex pattern on top-level | characters (not inside [] or ())."""
    parts = []
    current = []
    depth_paren = 0
    depth_bracket = 0
    escaped = False
    for ch in pattern:
        if escaped:
            current.append(ch)
            escaped = False
            continue
        if ch == "\\":
            current.append(ch)
            escaped = True
            continue
        if ch == "[" and depth_bracket == 0:
            depth_bracket += 1
        elif ch == "]" and depth_bracket > 0:
            depth_bracket -= 1
        elif depth_bracket == 0:
            if ch == "(":
                depth_paren += 1
            elif ch == ")":
                depth_paren -= 1
            elif ch == "|" and depth_paren == 0:
                parts.append("".join(current))
                current = []
                continue
        current.append(ch)
    parts.append("".join(current))
    return parts


def _translate_wildcard(pattern):
    """Translate a wildcard pattern (using * and ?) into plain English."""
    if not pattern:
        return '""'
    parts = []
    current_literal = []
    for ch in pattern:
        if ch == "*":
            if current_literal:
                parts.append(f'"{"".join(current_literal)}"')
                current_literal = []
            parts.append("any characters")
        elif ch == "?":
            if current_literal:
                parts.append(f'"{"".join(current_literal)}"')
                current_literal = []
            parts.append("any single character")
        else:
            current_literal.append(ch)
    if current_literal:
        parts.append(f'"{"".join(current_literal)}"')
    return " followed by ".join(parts)


# Flags that take no argument
_SIMPLE_FLAGS = {
    "-a": "AND mode",
    "-r": "recursive (searching all subdirectories)",
    "-z": "fuzzy matching (approximate, typo-tolerant)",
    "-x": "regex mode",
    "-w": "wildcard mode",
    "-W": "whole-word matching",
    "-O": "OCR enabled (scanned PDFs and images)",
    "-I": "using the search index",
    "-i": "inverse search (files WITHOUT matches)",
    "-q": "quiet mode",
}

# Flags that consume the next argument
_ARG_FLAGS = {
    "-n": "excluding",
    "-t": "file types",
    "-f": "specific files",
    "-p": "proximity (within {0} words of each other)",
    "-A": "showing {0} lines after each match",
    "-B": "showing {0} lines before each match",
    "-c": "using {0} CPU cores",
    "-o": "output formats",
    "-s": "saving results as",
    "-sa": "appending results to",
}


def translate_search(search_terms, report_mode="ANY", use_regex=False,
                     use_wildcard=False, use_fuzzy=False, use_ocr=False,
                     use_index=False, use_whole_word=False, inverse=False,
                     recursive=False,
                     exclude_terms=None, file_types=None, specific_files=None,
                     proximity=None, context_before=0, context_after=0,
                     cores=None, expression=None):
    """Translate search parameters into plain English.

    Takes the actual parsed search values (not a command string), so
    backslashes and special characters in regex terms are preserved exactly
    as the search engine sees them.

    Returns:
        A plain-English description of what the search does.
    """
    if not search_terms:
        return "No search terms"

    parts = []

    # Opening: Search scope
    if recursive:
        parts.append("Search all subdirectories")
    else:
        parts.append("Search current directory")

    if expression is not None:
        parts.append(f"for boolean expression: {expression}")
    else:
        # Determine AND/ALL vs ANY/OR
        is_and = "ALL" in report_mode or "AND" in report_mode

        # Describe search terms
        term_descs = []
        for term in search_terms:
            if use_regex:
                term_descs.append(_translate_regex(term))
            elif use_wildcard:
                term_descs.append(_translate_wildcard(term))
            else:
                term_descs.append(f'"{term}"')

        if len(term_descs) == 1:
            parts.append(f"for {term_descs[0]}")
        else:
            mode_word = "ALL" if is_and else "ANY"
            joiner = " AND " if is_and else " OR "
            parts.append(f"for {mode_word} of: {joiner.join(term_descs)}")

    # Additional modifiers
    modifiers = []
    if use_regex:
        modifiers.append("using regex")
    if use_wildcard:
        modifiers.append("using wildcard patterns")
    if use_whole_word:
        modifiers.append("matching whole words only")
    if use_fuzzy:
        modifiers.append("fuzzy matching (typo-tolerant)")
    if use_ocr:
        modifiers.append("OCR enabled")
    if use_index:
        modifiers.append("using search index")
    if inverse:
        modifiers.append("inverse (files WITHOUT matches)")
    if exclude_terms:
        modifiers.append(f'excluding "{" ".join(exclude_terms)}"')
    if file_types:
        modifiers.append(f"limited to file types: {file_types}")
    if specific_files:
        modifiers.append(f"in specific files: {specific_files}")
    if proximity:
        modifiers.append(f"terms within {proximity} words of each other")
    if context_before:
        modifiers.append(f"showing {context_before} lines before each match")
    if context_after:
        modifiers.append(f"showing {context_after} lines after each match")
    if cores:
        modifiers.append(f"using {cores} CPU cores")

    result = ", ".join(parts)
    if modifiers:
        result += " (" + ", ".join(modifiers) + ")"

    return result


def translate_command(command_str):
    """Translate a full docsearch CLI command string into plain English.

    NOTE: This parses the command string with shlex, which may lose
    backslashes. Prefer translate_search() with actual parsed values
    when available.
    """
    if not command_str or not command_str.strip():
        return "No command to translate"

    try:
        tokens = shlex.split(command_str)
    except ValueError:
        return f"Could not parse command: {command_str}"

    # Strip leading "docsearch" if present
    if tokens and tokens[0].lower() in ("docsearch", "./docsearch"):
        tokens = tokens[1:]

    if not tokens:
        return "Run docsearch with no search terms"

    # Parse flags and search terms
    flags = {}
    search_terms = []
    is_regex = False
    is_wildcard = False
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in _SIMPLE_FLAGS:
            flags[tok] = True
            if tok == "-x":
                is_regex = True
            elif tok == "-w":
                is_wildcard = True
        elif tok in _ARG_FLAGS and i + 1 < len(tokens):
            flags[tok] = tokens[i + 1]
            i += 1
        elif tok == "--no-index":
            flags[tok] = True
        elif tok.startswith("-") and len(tok) == 2 and tok not in _SIMPLE_FLAGS and tok not in _ARG_FLAGS:
            flags[tok] = True
        else:
            search_terms.append(tok)
        i += 1

    return translate_search(
        search_terms,
        report_mode="ALL" if "-a" in flags else "ANY",
        use_regex=is_regex,
        use_wildcard=is_wildcard,
        use_fuzzy="-z" in flags,
        use_ocr="-O" in flags,
        use_index="-I" in flags,
        use_whole_word="-W" in flags,
        inverse="-i" in flags,
        recursive="-r" in flags,
        exclude_terms=[flags["-n"]] if "-n" in flags else None,
        file_types=flags.get("-t"),
        specific_files=flags.get("-f"),
        proximity=flags.get("-p"),
        context_before=int(flags["-B"]) if "-B" in flags else 0,
        context_after=int(flags["-A"]) if "-A" in flags else 0,
        cores=flags.get("-c"),
    )
