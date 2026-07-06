"""Tests for peekdocs.errors — the public exception hierarchy.

Two concerns:

1. The new subclasses are catchable both by their peekdocs name and by
   their stdlib base (``ValueError`` / ``KeyError``). This is the
   back-compat guarantee that lets existing consumer code keep working.
2. The actual raise sites in api.py / range_query.py / expr_parser.py
   raise the new types instead of raw stdlib exceptions — so a library
   consumer who upgrades and switches to ``except QueryError`` still
   catches everything they were catching with ``except ValueError``.
"""
from __future__ import annotations

import pytest

from peekdocs.errors import (
    NameNotFoundError,
    PeekdocsError,
    QueryError,
    RangeError,
)


# ─── Hierarchy shape ───────────────────────────────────────────


def test_all_subclasses_descend_from_peekdocs_error():
    """Catching PeekdocsError catches every specific subclass — the
    'catch anything peekdocs might raise' contract."""
    assert issubclass(QueryError, PeekdocsError)
    assert issubclass(RangeError, PeekdocsError)
    assert issubclass(NameNotFoundError, PeekdocsError)


def test_query_error_is_also_a_value_error():
    """Back-compat: consumers catching ValueError from api.search()
    keep working after we swapped raw raises to QueryError."""
    assert issubclass(QueryError, ValueError)


def test_range_error_is_also_a_value_error():
    """Back-compat for consumers catching ValueError from range parsing."""
    assert issubclass(RangeError, ValueError)


def test_name_not_found_error_is_also_a_key_error():
    """Back-compat: run_suite() and run_regex_collection() used to
    raise KeyError; NameNotFoundError must still be catchable that way."""
    assert issubclass(NameNotFoundError, KeyError)


# ─── Actual raise sites raise the new types ────────────────────


def test_api_search_raises_query_error_on_conflicting_modes():
    """Sanity check: peekdocs.api.search() actually raises QueryError,
    not raw ValueError, for invalid mode combinations."""
    from peekdocs.api import search

    with pytest.raises(QueryError):
        search(["foo"], use_fuzzy=True, use_regex=True)


def test_api_search_still_catchable_as_value_error():
    """The same raise site is still catchable by consumers using the
    old pattern (except ValueError)."""
    from peekdocs.api import search

    with pytest.raises(ValueError):  # QueryError inherits ValueError
        search(["foo"], use_wildcard=True, use_regex=True)


def test_api_search_raises_query_error_on_invalid_regex():
    """A malformed regex pattern under -x raises QueryError with a
    descriptive message."""
    from peekdocs.api import search

    with pytest.raises(QueryError, match="Invalid regex pattern"):
        search(["*unclosed[bracket"], use_regex=True)


def test_range_query_raises_range_error_on_missing_colon():
    """range_query.parse_range() raises RangeError (not raw ValueError)
    when a range spec lacks the required 'field:' prefix."""
    from peekdocs.range_query import parse_range

    with pytest.raises(RangeError):
        parse_range("just-a-value")


def test_range_error_still_catchable_as_value_error():
    """Same raise site, old catch pattern."""
    from peekdocs.range_query import parse_range

    with pytest.raises(ValueError):  # RangeError inherits ValueError
        parse_range("just-a-value")


def test_expr_parser_raises_query_error_on_empty():
    """Boolean-expression parser raises QueryError for empty input."""
    from peekdocs.expr_parser import parse_expression

    with pytest.raises(QueryError, match="Empty"):
        parse_expression("")


def test_expr_parser_raises_query_error_on_unterminated_quote():
    """Boolean-expression parser raises QueryError with position info."""
    from peekdocs.expr_parser import parse_expression

    with pytest.raises(QueryError, match="Unterminated"):
        parse_expression('foo AND "bar')
