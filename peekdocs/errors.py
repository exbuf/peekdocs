"""Public exception hierarchy for peekdocs.

Consumers of the peekdocs library API (:mod:`peekdocs.api`) can catch
these types to distinguish user-input errors from IO errors from
programming errors. All library-level exceptions descend from
:class:`PeekdocsError` for the "catch anything peekdocs might raise"
case. Individual subclasses also inherit from the closest stdlib
exception (``ValueError``, ``KeyError``) so existing consumer code
that catches those types keeps working — this hierarchy is a
non-breaking upgrade for anyone already handling errors from
:mod:`peekdocs.api`.

Example — the sharp path (catch only what peekdocs raises)::

    from peekdocs import api
    from peekdocs.errors import QueryError, NameNotFoundError

    try:
        result = api.search(["foo"], use_regex=True, use_fuzzy=True)
    except QueryError as e:
        print(f"Search input invalid: {e}")
    try:
        result = api.run_suite("nonexistent")
    except NameNotFoundError as e:
        print(f"Suite not found: {e}")

Example — the back-compat path (existing consumer code)::

    try:
        result = api.search(["foo"], use_regex=True, use_fuzzy=True)
    except ValueError as e:                       # still works
        print(f"Invalid: {e}")
    try:
        result = api.run_suite("nonexistent")
    except KeyError as e:                         # still works
        print(f"Missing: {e}")

Notes on scope: internal control-flow ``raise`` sites (e.g., the
message-less ``raise ValueError`` inside ``parser.py``'s try/except
blocks) are deliberately left as bare stdlib exceptions — they're
never seen by library consumers, so typing them adds cost without
value. File-IO failures (missing directory, permission denied) also
remain as ``FileNotFoundError`` / ``OSError`` since those already
communicate intent unambiguously.
"""
from __future__ import annotations


class PeekdocsError(Exception):
    """Root of the peekdocs exception hierarchy.

    Catch this to handle any exception raised by peekdocs's library
    surface without also catching unrelated built-in exceptions.
    Subclasses:

    * :class:`QueryError` — bad search input (flag combos, empty
      terms, malformed regex, invalid boolean expressions).
    * :class:`RangeError` — malformed ``-R`` range spec.
    * :class:`NameNotFoundError` — named suite / regex collection
      doesn't exist.
    """


class QueryError(PeekdocsError, ValueError):
    """Bad user-provided search input.

    Raised for invalid search-mode combinations (fuzzy + regex,
    wildcard + fuzzy, expression + match_all), empty term lists,
    invalid individual regex patterns, and boolean-expression syntax
    errors. Inherits from :class:`ValueError` so code that already
    catches ``ValueError`` from search-input validation keeps working.
    """


class RangeError(PeekdocsError, ValueError):
    """Malformed ``-R`` range specifier.

    Range specs have their own mini-grammar (``field:min..max``,
    ``amount:>=1000``, ``date:2024-01-01..2024-12-31``, etc.). This
    subclass distinguishes range-syntax errors from broader query
    errors so callers can point the user at the specific ``-R`` flag
    they got wrong. Inherits from :class:`ValueError` for back-compat
    with existing consumer code.
    """


class NameNotFoundError(PeekdocsError, KeyError):
    """A named suite or regex collection wasn't found.

    Raised by :func:`peekdocs.api.run_suite` and
    :func:`peekdocs.api.run_regex_collection` when the requested name
    doesn't exist in the collection folder (or the folder itself has
    no collections). Inherits from :class:`KeyError` for back-compat.
    """
