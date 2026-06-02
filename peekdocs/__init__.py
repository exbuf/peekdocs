"""peekdocs - A CLI tool for searching and retrieving content from documents."""

# Resolve __version__ from installed package metadata when available
# (covers normal pip / pipx installs). Falls back to the hardcoded
# value below in environments where the metadata isn't accessible —
# notably PyInstaller-bundled standalone exes, where the .dist-info
# directory isn't copied into the bundle by default. Keep this
# fallback in sync with pyproject.toml's version field on every bump.
try:
    from importlib.metadata import version as _pkg_version
    __version__ = _pkg_version("peekdocs")
except Exception:
    __version__ = "1.0.5"

from peekdocs.api import (
    SearchMatch, SearchResult, search,
    SuiteSearchResult, SuiteResult,
    list_suites, run_suite,
    PatternResult, CollectionResult,
    list_regex_collections, run_regex_collection,
)
