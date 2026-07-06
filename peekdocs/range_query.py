"""Range query parsing, value extraction, and evaluation.

Supports content ranges (date, amount, number, percent, age, time) that filter
matched lines by extracting values from text, and metadata ranges (filesize,
filedate) that filter entire files by their properties.
"""

import dataclasses
import datetime
import os
import re

from peekdocs.errors import RangeError


CONTENT_FIELDS = {"date", "amount", "number", "percent", "age", "time"}
METADATA_FIELDS = {"filesize", "filedate"}
ALL_FIELDS = CONTENT_FIELDS | METADATA_FIELDS


@dataclasses.dataclass
class RangeSpec:
    """A parsed range filter specification."""
    field: str        # one of ALL_FIELDS
    min_val: str      # raw string or "" for open-ended
    max_val: str      # raw string or "" for open-ended
    target: str = "content"  # "content", "filename", or "metadata"


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_range(spec_str):
    """Parse ``"field:min..max"`` into a *RangeSpec*.

    Supports ``fn:`` and ``fc:`` target prefixes:
    - ``fn:date:2024-01-01..2024-12-31`` → target="filename"
    - ``fc:amount:1000..5000`` → target="content"
    - ``amount:1000..5000`` → target="content" (default)

    Raises *ValueError* for invalid syntax or unknown field names.
    """
    if ":" not in spec_str:
        raise RangeError(f"Invalid range spec (missing ':'): {spec_str}")

    # Check for fn:/fc: target prefix
    target = "content"
    working = spec_str.strip()
    first_colon = working.index(":")
    prefix = working[:first_colon].strip().lower()
    if prefix in ("fn", "fc"):
        target = "filename" if prefix == "fn" else "content"
        working = working[first_colon + 1:]
        if ":" not in working:
            raise RangeError(f"Invalid range spec (missing ':'): {spec_str}")

    field, _, rest = working.partition(":")
    field = field.strip().lower()
    if field not in ALL_FIELDS:
        raise RangeError(
            f"Unknown range field '{field}'. "
            f"Valid fields: {', '.join(sorted(ALL_FIELDS))}"
        )
    # Metadata fields auto-assign target; fn:/fc: prefixes are invalid for them
    if field in METADATA_FIELDS:
        if prefix in ("fn", "fc"):
            raise RangeError(
                f"Cannot use '{prefix}:' prefix with metadata field '{field}'. "
                f"Metadata fields (filesize, filedate) don't need a target prefix."
            )
        target = "metadata"
    elif prefix == "fn":
        target = "filename"

    if ".." not in rest:
        raise RangeError(f"Invalid range spec (missing '..'): {spec_str}")
    min_val, _, max_val = rest.partition("..")
    min_val = min_val.strip()
    max_val = max_val.strip()
    if not min_val and not max_val:
        raise RangeError(f"Range must have at least a min or max value: {spec_str}")
    return RangeSpec(field=field, min_val=min_val, max_val=max_val, target=target)


def split_ranges(ranges):
    """Split a list of *RangeSpec* into ``(content, metadata, filename)``."""
    content = [r for r in ranges if r.target == "content"]
    metadata = [r for r in ranges if r.target == "metadata"]
    filename = [r for r in ranges if r.target == "filename"]
    return content, metadata, filename


# ---------------------------------------------------------------------------
# Value extractors — pull comparable values out of text
# ---------------------------------------------------------------------------

# Month name mapping for natural-language dates
_MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

# ISO: 2024-01-15
_RE_DATE_ISO = re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")
# US: 01/15/2024 or 01-15-2024
_RE_DATE_US = re.compile(r"\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})\b")
# Natural: January 15, 2024 or Jan 15 2024
_RE_DATE_NATURAL = re.compile(
    r"\b(" + "|".join(_MONTH_NAMES) + r")\s+(\d{1,2}),?\s+(\d{4})\b",
    re.IGNORECASE,
)


def _extract_dates(text):
    """Extract date values from *text*. Returns list of ``datetime.date``."""
    results = []
    for m in _RE_DATE_ISO.finditer(text):
        try:
            results.append(datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
        except ValueError:
            pass
    for m in _RE_DATE_US.finditer(text):
        try:
            results.append(datetime.date(int(m.group(3)), int(m.group(1)), int(m.group(2))))
        except ValueError:
            pass
    for m in _RE_DATE_NATURAL.finditer(text):
        month_num = _MONTH_NAMES.get(m.group(1).lower())
        if month_num:
            try:
                results.append(datetime.date(int(m.group(3)), month_num, int(m.group(2))))
            except ValueError:
                pass
    return results


# Currency: $1,234.56 or USD 1234 or 1,234 dollars
_RE_AMOUNT = re.compile(
    r"(?:\$\s?|USD\s?|EUR\s?|GBP\s?)"
    r"([\d,]+(?:\.\d+)?)"
    r"|"
    r"([\d,]+(?:\.\d+)?)\s*(?:dollars?|USD|EUR|GBP)",
    re.IGNORECASE,
)


def _extract_amounts(text):
    """Extract currency amounts from *text*. Returns list of ``float``."""
    results = []
    for m in _RE_AMOUNT.finditer(text):
        raw = m.group(1) or m.group(2)
        if raw:
            try:
                results.append(float(raw.replace(",", "")))
            except ValueError:
                pass
    return results


# Standalone numbers (int or float, with optional commas)
_RE_NUMBER = re.compile(r"(?<!\S)([\d,]+(?:\.\d+)?)(?!\S)")


def _extract_numbers(text):
    """Extract standalone numeric values from *text*. Returns list of ``float``."""
    results = []
    for m in _RE_NUMBER.finditer(text):
        raw = m.group(1).replace(",", "")
        try:
            results.append(float(raw))
        except ValueError:
            pass
    return results


# Percentages: 45%, 45 percent, 45.5%
_RE_PERCENT = re.compile(r"([\d,]+(?:\.\d+)?)\s*(?:%|percent)", re.IGNORECASE)


def _extract_percents(text):
    """Extract percentage values from *text*. Returns list of ``float``."""
    results = []
    for m in _RE_PERCENT.finditer(text):
        raw = m.group(1).replace(",", "")
        try:
            results.append(float(raw))
        except ValueError:
            pass
    return results


# Ages: age 25, 25 years old, aged 25, 25-year-old
_RE_AGE = re.compile(
    r"\bage[d]?\s+(\d+)"
    r"|(\d+)\s*[-\s]?years?\s*[-\s]?old"
    r"|(\d+)\s*[-\s]year[-\s]old",
    re.IGNORECASE,
)


def _extract_ages(text):
    """Extract age mentions from *text*. Returns list of ``int``."""
    results = []
    for m in _RE_AGE.finditer(text):
        raw = m.group(1) or m.group(2) or m.group(3)
        if raw:
            try:
                results.append(int(raw))
            except ValueError:
                pass
    return results


# Times: 14:30, 2:30 PM, 14:30:00
_RE_TIME = re.compile(
    r"\b(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM|am|pm)?\b"
)


def _extract_times(text):
    """Extract time values from *text*. Returns list of ``datetime.time``."""
    results = []
    for m in _RE_TIME.finditer(text):
        hour = int(m.group(1))
        minute = int(m.group(2))
        second = int(m.group(3)) if m.group(3) else 0
        ampm = m.group(4)
        if ampm:
            ampm = ampm.upper()
            if ampm == "PM" and hour != 12:
                hour += 12
            elif ampm == "AM" and hour == 12:
                hour = 0
        if 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59:
            results.append(datetime.time(hour, minute, second))
    return results


_EXTRACTORS = {
    "date": _extract_dates,
    "amount": _extract_amounts,
    "number": _extract_numbers,
    "percent": _extract_percents,
    "age": _extract_ages,
    "time": _extract_times,
}


# ---------------------------------------------------------------------------
# Value parsers — convert min/max bound strings to comparable values
# ---------------------------------------------------------------------------

def _parse_date(s):
    """Parse a date bound string into ``datetime.date``."""
    # Try ISO first
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    raise RangeError(f"Cannot parse date: {s}")


def _parse_number(s):
    """Parse a numeric bound string into ``float``."""
    cleaned = s.replace("$", "").replace(",", "").replace("%", "").strip()
    return float(cleaned)


def _parse_time(s):
    """Parse a time bound string into ``datetime.time``."""
    for fmt in ("%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M:%S %p"):
        try:
            return datetime.datetime.strptime(s.strip(), fmt).time()
        except ValueError:
            pass
    raise RangeError(f"Cannot parse time: {s}")


_SIZE_SUFFIXES = {"K": 1024, "M": 1024 ** 2, "G": 1024 ** 3, "T": 1024 ** 4}


def _parse_filesize(s):
    """Parse a filesize string like ``"1M"`` or ``"500K"`` into bytes (int)."""
    s = s.strip().upper()
    if not s:
        raise RangeError("Empty filesize")
    if s[-1] in _SIZE_SUFFIXES:
        return int(float(s[:-1]) * _SIZE_SUFFIXES[s[-1]])
    return int(float(s))


def _get_parser(field):
    """Return the appropriate bound parser for *field*."""
    if field in ("date", "filedate"):
        return _parse_date
    if field == "time":
        return _parse_time
    if field == "filesize":
        return _parse_filesize
    # amount, number, percent, age
    return _parse_number


def _parse_bound(field, val_str):
    """Parse a bound value string for *field*, or return None if empty."""
    if not val_str:
        return None
    return _get_parser(field)(val_str)


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def _in_range(value, min_bound, max_bound):
    """Check whether *value* falls within [min_bound, max_bound]."""
    if min_bound is not None and value < min_bound:
        return False
    if max_bound is not None and value > max_bound:
        return False
    return True


def line_matches_content_ranges(text, content_ranges):
    """Return True if *text* satisfies ALL content range filters.

    For each range, at least one extracted value must fall within the range.
    All ranges must be satisfied (AND logic).
    """
    for rspec in content_ranges:
        extractor = _EXTRACTORS.get(rspec.field)
        if not extractor:
            continue
        try:
            min_bound = _parse_bound(rspec.field, rspec.min_val)
            max_bound = _parse_bound(rspec.field, rspec.max_val)
        except (ValueError, TypeError):
            # Invalid range bounds (e.g., invalid date like June 31) —
            # reject all lines rather than silently matching everything
            return False
        values = extractor(text)
        if not values:
            return False
        if not any(_in_range(v, min_bound, max_bound) for v in values):
            return False
    return True


def file_matches_filename_ranges(filename, filename_ranges):
    """Return True if *filename* satisfies ALL filename range filters.

    Uses the same content extractors on the filename string.
    All ranges must be satisfied (AND logic).
    """
    for rspec in filename_ranges:
        extractor = _EXTRACTORS.get(rspec.field)
        if not extractor:
            continue
        try:
            min_bound = _parse_bound(rspec.field, rspec.min_val)
            max_bound = _parse_bound(rspec.field, rspec.max_val)
        except (ValueError, TypeError):
            continue
        values = extractor(filename)
        if not values:
            return False
        if not any(_in_range(v, min_bound, max_bound) for v in values):
            return False
    return True


def evaluate_single_range(text, spec_str, filename=None):
    """Evaluate a single range spec against *text*.

    For use inside boolean expression evaluation.  Metadata fields
    (filesize, filedate) always return False since they don't apply to
    line text content.  Filename ranges (``fn:`` prefix) are evaluated
    against *filename* if provided.
    """
    rspec = parse_range(spec_str)
    if rspec.field in METADATA_FIELDS:
        return False
    if rspec.target == "filename":
        if filename is None:
            return False
        return file_matches_filename_ranges(filename, [rspec])
    return line_matches_content_ranges(text, [rspec])


def file_matches_metadata_ranges(filepath, metadata_ranges):
    """Return True if the file at *filepath* satisfies ALL metadata range filters."""
    for rspec in metadata_ranges:
        try:
            min_bound = _parse_bound(rspec.field, rspec.min_val)
            max_bound = _parse_bound(rspec.field, rspec.max_val)
        except (ValueError, TypeError):
            continue

        if rspec.field == "filesize":
            try:
                size = os.path.getsize(filepath)
            except OSError:
                return False
            if not _in_range(size, min_bound, max_bound):
                return False

        elif rspec.field == "filedate":
            try:
                mtime = os.path.getmtime(filepath)
            except OSError:
                return False
            file_date = datetime.date.fromtimestamp(mtime)
            if not _in_range(file_date, min_bound, max_bound):
                return False

    return True
