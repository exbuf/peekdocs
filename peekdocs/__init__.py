"""peekdocs - A CLI tool for searching and retrieving content from documents."""

__version__ = "1.0.0"

from peekdocs.api import (
    SearchMatch, SearchResult, search,
    SuiteSearchResult, SuiteResult,
    list_suites, run_suite,
    PatternResult, CollectionResult,
    list_regex_collections, run_regex_collection,
)
