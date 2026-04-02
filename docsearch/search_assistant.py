"""Natural language search assistant for docsearch.

Translates plain English queries into docsearch search parameters.
No external API needed — runs entirely offline using rule-based parsing.
"""

import re


def parse_natural_query(query):
    """Parse a natural language search query into docsearch parameters.

    Returns a dict with:
        search_text: str — the search terms or pattern
        recursive: bool
        regex: bool
        fuzzy: bool
        wildcard: bool
        inverse: bool
        whole_word: bool
        expression: bool
        file_types: str — comma-separated
        exclude: str — comma-separated
        proximity: str — number or empty
        range_filters: str
        context_before: str
        context_after: str
        explanation: str — human-readable description of what was configured
        unsupported: str — anything we couldn't handle (empty if all good)
    """
    q = query.strip()
    q_lower = q.lower()

    params = {
        "search_text": "",
        "recursive": False,
        "regex": False,
        "fuzzy": False,
        "wildcard": False,
        "inverse": False,
        "whole_word": False,
        "expression": False,
        "file_types": "",
        "exclude": "",
        "proximity": "",
        "range_filters": "",
        "context_before": "",
        "context_after": "",
        "explanation": "",
        "unsupported": "",
    }

    explanation_parts = []
    unsupported_parts = []
    has_amount_range = False
    _need_dollar_highlight = False

    # Helper to convert "10k" → "10000", "1.5m" → "1500000"
    def _expand_number(s):
        s = s.replace(",", "")
        m = re.match(r"([\d.]+)\s*([km])?", s.lower())
        if not m:
            return s
        num = float(m.group(1))
        suffix = m.group(2)
        if suffix == "k":
            num *= 1000
        elif suffix == "m":
            num *= 1000000
        return str(int(num))

    # ── Detect known regex patterns ──────────────────────────
    pattern_map = {
        r"ssn|social security number": (r"\d{3}-\d{2}-\d{4}", "SSN pattern (XXX-XX-XXXX)"),
        r"phone number|telephone": (r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", "US phone number pattern"),
        r"email address|e-mail": (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,}", "email address pattern"),
        r"ip address": (r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", "IP address pattern"),
        r"zip code|postal code": (r"\b\d{5}(-\d{4})?\b", "US ZIP code pattern"),
        r"date|dates": (r"\d{2}/\d{2}/\d{4}", "date pattern (MM/DD/YYYY)"),
        r"dollar amount|money|currency|\$": (r"\$[\d,]+\.?\d*", "dollar amount pattern"),
        r"credit card": (r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}", "credit card number pattern"),
        r"url|web address|website": (r"https?://\S+", "URL pattern"),
    }

    detected_pattern = None
    for trigger, (pattern, desc) in pattern_map.items():
        if re.search(trigger, q_lower):
            detected_pattern = (pattern, desc)
            break

    # ── Detect file type filters ──────────────────────────────
    file_type_map = {
        r"\bpdfs?\b": "pdf",
        r"\bword doc|word document|\.docx?\b": "docx,doc",
        r"\bexcel|spreadsheet|\.xlsx?\b": "xlsx,xls",
        r"\bpowerpoint|presentation|\.pptx?\b": "pptx,ppt",
        r"\bemails?\b|\.eml\b|\.msg\b": "eml,msg",
        r"\btext file|\.txt\b": "txt",
        r"\bhtml\b|web page": "html",
        r"\bcsv\b": "csv",
        r"\bjson\b": "json",
        r"\bxml\b": "xml",
        r"\barchive|\.zip\b|\.7z\b": "zip,7z,rar",
    }

    detected_types = []
    for trigger, types in file_type_map.items():
        if re.search(trigger, q_lower):
            detected_types.append(types)

    if detected_types:
        params["file_types"] = ",".join(detected_types)
        explanation_parts.append(f"File types: {params['file_types']}")

    # ── Detect recursive ──────────────────────────────────────
    if re.search(r"subfolder|sub-folder|all folder|recursive|nested|include subfolder|and subfolder", q_lower):
        params["recursive"] = True
        explanation_parts.append("Recursive: searching all subfolders")

    # ── Detect inverse (missing/without) ──────────────────────
    if re.search(r"missing|without|don't contain|doesn't contain|do not contain|not contain|lacking|absent|files that lack", q_lower):
        params["inverse"] = True
        explanation_parts.append("Inverse: finding files that do NOT contain the terms")

    # ── Spreadsheet-style queries ────────────────────────────
    # "show me all X over/under $Y"
    ss_match = re.search(r"(?:show me|find|list)\s+(?:all\s+)?(\w+)\s+(?:over|above|greater than|more than)\s+\$?([\d,.]+[km]?)", q_lower)
    if ss_match and not has_amount_range:
        params["search_text"] = ss_match.group(1)
        lo = _expand_number(ss_match.group(2))
        params["range_filters"] = f"amount:{lo}.."
        explanation_parts.insert(0, f"Search term: {ss_match.group(1)}")
        explanation_parts.append(f"Range: amounts over ${lo}")
        has_amount_range = True
        _need_dollar_highlight = False
    if not ss_match:
        ss_match = re.search(r"(?:show me|find|list)\s+(?:all\s+)?(\w+)\s+(?:under|below|less than)\s+\$?([\d,.]+[km]?)", q_lower)
        if ss_match and not has_amount_range:
            params["search_text"] = ss_match.group(1)
            hi = _expand_number(ss_match.group(2))
            params["range_filters"] = f"amount:..{hi}"
            explanation_parts.insert(0, f"Search term: {ss_match.group(1)}")
            explanation_parts.append(f"Range: amounts under ${hi}")
            has_amount_range = True
            _need_dollar_highlight = False

    # "find X where status is Y" / "find rows where Y"
    status_match = re.search(r"(?:where|with)\s+(?:status|state)\s+(?:is|=|equals?)\s+(\w+)", q_lower)
    if status_match:
        status_val = status_match.group(1)
        if not params["search_text"]:
            params["search_text"] = status_val
        else:
            params["search_text"] += " " + status_val
            params["expression"] = True
            params["search_text"] = f"{params['search_text'].split()[0]} AND {status_val}"
        explanation_parts.insert(0, f"Searching for status: {status_val}")

    # "find X and Y" / "show me X that are Y"
    and_match = re.search(r"(?:that are|that is|which are)\s+(\w+)\s+and\s+(\w+)", q_lower)
    if and_match:
        term1 = and_match.group(1)
        term2 = and_match.group(2)
        params["search_text"] = f"{term1} AND {term2}"
        params["expression"] = True
        explanation_parts.insert(0, f"Boolean: {term1} AND {term2}")

    # "find X with dollar amounts" / "find X and dollar amounts"
    with_amounts = re.search(r"(\w+)\s+(?:with|and)\s+(?:dollar\s+)?amounts?", q_lower)
    if with_amounts and not has_amount_range and not params["search_text"]:
        term = with_amounts.group(1)
        params["search_text"] = f"{term}|\\$[\\d,.]+"
        params["regex"] = True
        explanation_parts.insert(0, f"Search term: {term} (also highlighting dollar amounts)")

    # "show me everything from March" / "from Q2"
    from_match = re.search(r"(?:everything|all|data|rows?)\s+from\s+(january|february|march|april|may|june|july|august|september|october|november|december|q[1-4]|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)", q_lower)
    if from_match:
        period = from_match.group(1)
        if not params["search_text"]:
            params["search_text"] = period
            explanation_parts.insert(0, f"Search term: {period}")

    # ── Detect fuzzy ──────────────────────────────────────────
    if re.search(r"fuzzy|misspell|typo|approximate|similar to|close to|OCR error", q_lower):
        params["fuzzy"] = True
        explanation_parts.append("Fuzzy: matching approximate/misspelled terms")

    # ── Detect whole word ─────────────────────────────────────
    if re.search(r"whole word|exact word|word boundar|only the word\b|just the word\b", q_lower):
        params["whole_word"] = True
        explanation_parts.append("Whole word: matching complete words only")

    # ── Detect proximity ──────────────────────────────────────
    prox_match = re.search(r"within (\d+) words?|near each other|close together|(\d+) words? (?:of|apart|near)", q_lower)
    if prox_match:
        n = prox_match.group(1) or prox_match.group(2) or "5"
        params["proximity"] = n
        explanation_parts.append(f"Proximity: terms within {n} words of each other")

    # ── Detect range queries ──────────────────────────────────
    # Dollar amounts
    range_match = re.search(r"(?:between|from)\s*\$?([\d,.]+[km]?)\s*(?:and|to|through|-)\s*\$?([\d,.]+[km]?)", q_lower)
    if not range_match:
        # Also try without "between/from" if the query mentions dollars/amounts
        if re.search(r"dollar|amount|\$", q_lower):
            range_match = re.search(r"\$?([\d,.]+[km]?)\s*(?:and|to|through|-)\s*\$?([\d,.]+[km]?)", q_lower)
    if range_match:
        lo = _expand_number(range_match.group(1))
        hi = _expand_number(range_match.group(2))
        params["range_filters"] = f"amount:{lo}..{hi}"
        explanation_parts.append(f"Range: dollar amounts ${lo} to ${hi}")
        has_amount_range = True
    else:
        # "over $X" / "more than $X"
        range_match = re.search(r"(?:over|more than|above|exceeding|greater than)\s*\$?([\d,.]+[km]?)", q_lower)
        if range_match:
            lo = _expand_number(range_match.group(1))
            params["range_filters"] = f"amount:{lo}.."
            explanation_parts.append(f"Range: amounts over ${lo}")
            has_amount_range = True
        else:
            # "under $X" / "less than $X"
            range_match = re.search(r"(?:under|less than|below)\s*\$?([\d,.]+[km]?)", q_lower)
            if range_match:
                hi = _expand_number(range_match.group(1))
                params["range_filters"] = f"amount:..{hi}"
                explanation_parts.append(f"Range: amounts under ${hi}")
                has_amount_range = True
            else:
                # "under a dollar" / "less than a dollar"
                if re.search(r"(?:under|less than|below)\s+a\s+dollar", q_lower):
                    params["range_filters"] = "amount:..1"
                    explanation_parts.append("Range: amounts under $1")
                    has_amount_range = True

    # If we have an amount range, suppress the dollar regex pattern
    if has_amount_range:
        detected_pattern = None
        # Flag to add dollar highlighting if no other search terms are found
        _need_dollar_highlight = True
    else:
        _need_dollar_highlight = False

    # Date ranges
    date_range = re.search(r"dates?\s+(?:between|from)\s+(\d{4}-\d{2}(?:-\d{2})?)\s+(?:and|to)\s+(\d{4}-\d{2}(?:-\d{2})?)", q_lower)
    if date_range:
        r = f"date:{date_range.group(1)}..{date_range.group(2)}"
        if params["range_filters"]:
            params["range_filters"] += f", {r}"
        else:
            params["range_filters"] = r
        explanation_parts.append(f"Range: dates {date_range.group(1)} to {date_range.group(2)}")

    # ── Detect context lines ──────────────────────────────────
    ctx_match = re.search(r"(\d+)\s+lines?\s+(?:of\s+)?context|context\s+(?:of\s+)?(\d+)\s+lines?|show\s+(\d+)\s+lines?\s+(?:before|around)", q_lower)
    if ctx_match:
        n = ctx_match.group(1) or ctx_match.group(2) or ctx_match.group(3) or "3"
        params["context_before"] = n
        params["context_after"] = n
        explanation_parts.append(f"Context: {n} lines before and after each match")

    # ── Detect exclude terms ──────────────────────────────────
    excl_match = re.search(r"(?:but not|not|except|exclude|excluding|ignore)\s+[\"']?(\w+(?:\s*,\s*\w+)*)[\"']?$", q_lower)
    if excl_match and not params["inverse"]:  # Don't confuse with inverse "without"
        params["exclude"] = excl_match.group(1).strip()
        explanation_parts.append(f"Exclude: skipping lines containing '{params['exclude']}'")

    # ── Detect Boolean expressions ────────────────────────────
    if re.search(r"\bAND\b.*\bOR\b|\bOR\b.*\bAND\b|\bNOT\b.*\bAND\b|\bAND\b.*\bNOT\b", q):
        # Contains explicit Boolean operators
        # Extract the expression part
        bool_match = re.search(r"[\"'](.+?)[\"']|for\s+(.+?)(?:\s+in\s+|\s+across\s+|$)", q)
        if bool_match:
            expr = bool_match.group(1) or bool_match.group(2)
            params["search_text"] = expr.strip()
            params["expression"] = True
            explanation_parts.insert(0, f"Boolean expression: {params['search_text']}")

    # ── Build search text ─────────────────────────────────────
    if not params["search_text"]:
        if detected_pattern:
            params["search_text"] = detected_pattern[0]
            params["regex"] = True
            if not params["fuzzy"]:  # Can't combine
                explanation_parts.insert(0, f"Regex: {detected_pattern[1]}")
        else:
            # Extract the actual search terms from the query
            # Remove structural words and keep the content words
            cleaned = q_lower
            # Remove phrases we've already parsed
            remove_patterns = [
                # Range expressions first (before "to" is stripped as a stop word)
                r"\bbetween\s+\$?[\d,.]+[km]?\s*(?:and|to|through|-)\s*\$?[\d,.]+[km]?",
                r"\bfrom\s+\$?[\d,.]+[km]?\s*(?:and|to|through|-)\s*\$?[\d,.]+[km]?",
                r"\$?[\d,.]+[km]?\s*(?:-|to|through)\s*\$?[\d,.]+[km]?",
                r"\bover \$?[\d,.]+[km]?|\bunder \$?[\d,.]+[km]?|\babove \$?[\d,.]+[km]?|\bbelow \$?[\d,.]+[km]?",
                r"\bmore than \$?[\d,.]+[km]?|\bless than \$?[\d,.]+[km]?|\bexceeding \$?[\d,.]+[km]?|\bgreater than \$?[\d,.]+[km]?",
                r"\bunder a dollar\b|\bless than a dollar\b|\bbelow a dollar\b",
                r"\bunder\b|\bover\b|\babove\b|\bbelow\b|\bbetween\b",
                # Structural words
                r"\bfind\b|\bsearch\b|\blook for\b|\bshow me\b|\bshow\b|\blocate\b|\bget\b|\blist\b",
                r"\ball\b|\bevery\b|\bany\b|\beach\b|\bme\b|\bmy\b|\bfor\b|\bwith\b|\ban?\b|\bthe\b|\bto\b|\bof\b|\bis\b|\bare\b|\bwas\b|\bwere\b|\brows?\b|\bcolumns?\b|\bwhere\b|\bstatus\b|\bequals?\b",
                r"\bfiles?\b|\bdocuments?\b|\brecords?\b|\bin\b|\bfrom\b|\bacross\b|\btheir\b|\bthem\b|\bthose\b|\bthese\b|\bthat\b|\bwhich\b",
                r"\bthat\s+(contain|have|include|mention|reference)",
                r"\bcontain(s|ing)?\b|\bhave\b|\bhas\b|\binclude(s|ing)?\b|\bmention(s|ing)?\b",
                r"\bsubfolders?\b|\bsub-folders?\b|\brecursive\b|\bnested\b",
                r"\bmissing\b|\bwithout\b|\bdon't contain\b|\bdoesn't contain\b|\blacking\b",
                r"\bfuzzy\b|\bmisspell(ed)?\b|\bapproximate\b|\bsimilar\b",
                r"\bwhole word\b|\bexact word\b|\bword boundar",
                r"\bwithin \d+ words?\b|\bnear each other\b|\bclose together\b",
                r"\bbut not\b|\bexcept\b|\bexclude\b|\bexcluding\b|\bignore\b|\bnot\b",
                r"\bin pdfs?\b|\bin word\b|\bin excel\b|\bin emails?\b|\bin spreadsheets?\b|\bin presentations?\b",
                r"\bonly pdfs?\b|\bonly word\b|\bonly excel\b|\bonly emails?\b",
                r"\b\d+ lines? (?:of )?context\b|\bshow \d+ lines?\b|\blines? before\b|\blines? after\b|\blines? around\b",
                r"\bplease\b|\bcan you\b|\bcould you\b|\bi want\b|\bi need\b|\bi'd like\b|\bi would like\b",
                r"\bdollar amounts?\b|\bamounts?\b|\bphone numbers?\b|\bemail addresses?\b",
                r"\bword docs?\b|\bword documents?\b",
            ]
            for pat in remove_patterns:
                cleaned = re.sub(pat, " ", cleaned)
            # Remove exclude terms from search text
            if params["exclude"]:
                for excl_term in params["exclude"].split(","):
                    cleaned = re.sub(r"\b" + re.escape(excl_term.strip()) + r"\b", " ", cleaned)
            # Clean up
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            # Remove leading/trailing punctuation
            cleaned = re.sub(r"^[^\w]+|[^\w]+$", "", cleaned)

            if cleaned and len(cleaned) > 1:
                # Check if multiple terms should use AND
                terms = cleaned.split()
                if len(terms) > 1 and not params["expression"]:
                    params["search_text"] = cleaned
                    explanation_parts.insert(0, f"Search terms: {cleaned} (OR mode — any term matches)")
                elif terms:
                    params["search_text"] = cleaned
                    explanation_parts.insert(0, f"Search term: {cleaned}")

    # If we have a dollar range but no search terms, add dollar highlighting
    if _need_dollar_highlight and not params["search_text"]:
        params["search_text"] = r"\$[\d,.]+"
        params["regex"] = True
        explanation_parts.append("Highlighting dollar amounts in results")

    # ── Check for unsupported requests ────────────────────────
    unsupported_triggers = {
        r"replace|change|modify|edit|update|rename": "docsearch is read-only — it searches but cannot modify files",
        r"delete|remove (files|rows|blank)": "docsearch never deletes or modifies files — it only searches them",
        r"upload|send to cloud|send|share|email (this|the) report": "docsearch runs entirely offline — it cannot upload or send files",
        r"translate|convert|transform|combine|split|merge": "docsearch searches for content but cannot transform data",
        r"compare|diff|difference between": "docsearch searches within files but cannot compare files to each other",
        r"\bsort\b|order by|\brank\b|top \d+|lowest|highest": "docsearch finds matches but cannot sort or rank results. Try a range filter instead (e.g., 'find amounts over 50k')",
        r"\btotal\b|sum of|what's the sum|\baverage\b|\bmean\b|what's the average": "docsearch finds text matches but cannot calculate totals, sums, or averages. Use Excel or Google Sheets for calculations",
        r"\bcount how many\b|how many (rows|orders|items)": "docsearch shows match counts but cannot count specific values in columns. The results summary shows how many matches were found",
        r"\bmin and max\b|minimum|maximum": "docsearch cannot compute min/max values. Use a range filter to find values in a range (e.g., 'find salary amounts 50k - 200k')",
        r"add a column|create a column|new column|calculate.*column": "docsearch searches files but cannot add columns or create formulas. Use Excel or Google Sheets",
        r"percentage change|percent change|year over year": "docsearch cannot calculate percentage changes. Use Excel or Google Sheets",
        r"highlight.*red|make.*bold|format.*currency|freeze.*row|hide column": "docsearch cannot format spreadsheets. Use Excel or Google Sheets for formatting",
        r"(bar|pie|line) chart|plot|graph|visualization": "docsearch cannot create charts. Use Excel or Google Sheets for visualization",
        r"break ?down.*by|group by|totals by (month|region|category|department)": "docsearch cannot group or aggregate data. Use Excel pivot tables for breakdowns",
        r"how many days between|days since|last \d+ days|year.to.date": "docsearch cannot do date arithmetic. Use a date range filter instead (e.g., 'find dates 2026-01 to 2026-03')",
        r"trim|extra spaces|fix.*format|wrong format": "docsearch searches but cannot clean or reformat data",
        r"save.*pdf|export.*sheet|copy.*tab|new sheet": "docsearch saves results to .docx and .txt reports. Use -o csv for spreadsheet-compatible output",
        r"duplicate|find duplicates": "docsearch cannot detect duplicates. Use Excel's Remove Duplicates or conditional formatting",
    }

    for trigger, msg in unsupported_triggers.items():
        if re.search(trigger, q_lower):
            unsupported_parts.append(msg)

    # Conflicting modes
    if params["fuzzy"] and params["regex"]:
        params["fuzzy"] = False
        explanation_parts.append("Note: Fuzzy and Regex can't be combined — using Regex")
    if params["fuzzy"] and params["wildcard"]:
        params["fuzzy"] = False
        explanation_parts.append("Note: Fuzzy and Wildcard can't be combined — using Wildcard")

    # ── Build final explanation ────────────────────────────────
    if not params["search_text"] and not params["range_filters"] and not unsupported_parts:
        params["unsupported"] = "I couldn't figure out what to search for. Try something like:\n" \
                                "• 'find SSNs in all PDFs'\n" \
                                "• 'search for budget in subfolders'\n" \
                                "• 'find files missing an authorized signature'\n" \
                                "• 'find dollar amounts between 1000 and 5000'"
    else:
        params["explanation"] = "\n".join(explanation_parts) if explanation_parts else "Simple keyword search"
        if unsupported_parts:
            params["unsupported"] = "\n".join(unsupported_parts)

    return params
