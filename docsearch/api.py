"""Public library API for docsearch — call search() programmatically."""

import multiprocessing
import os
import re
import signal
import time
from dataclasses import dataclass

from docsearch.constants import _default_cores
from docsearch.indexer import index_exists, refresh_index, search_with_index
from docsearch.scanner import _process_file, _ocr_image, discover_files


@dataclass
class SearchMatch:
    """A single search match."""

    file_dir: str
    filename: str
    line_num: int
    text: str

    def __iter__(self):
        """Allow tuple unpacking: fd, fn, ln, tx = match."""
        return iter((self.file_dir, self.filename, self.line_num, self.text))

    def __len__(self):
        return 4

    def __getitem__(self, index):
        return (self.file_dir, self.filename, self.line_num, self.text)[index]


@dataclass
class SearchResult:
    """Complete result of a search operation."""

    matches: list          # List[SearchMatch]
    files_searched: list   # List[str] — absolute paths
    skipped_files: list    # List[Tuple[str, str]] — (filename, error_msg)
    elapsed: float         # seconds
    used_index: bool       # whether the indexed path was used


def search(
    search_terms,
    *,
    directory=None,
    match_all=False,
    recursive=False,
    use_regex=False,
    use_fuzzy=False,
    use_wildcard=False,
    use_whole_word=False,
    use_ocr=False,
    exclude_terms=None,
    file_types=None,
    file_names=None,
    context_before=0,
    context_after=0,
    proximity=0,
    cores=None,
    use_index=None,
    progress=None,
    expression=None,
    range_filters=None,
):
    """Search documents and return structured results.

    Parameters
    ----------
    search_terms : list[str]
        Terms to search for.
    directory : str, optional
        Directory to search in. Defaults to current working directory.
    match_all : bool
        If True, require ALL terms to match (AND mode). Default is OR mode.
    recursive : bool
        Search subdirectories.
    use_regex : bool
        Treat search terms as regex patterns.
    use_fuzzy : bool
        Use fuzzy/approximate matching.
    use_wildcard : bool
        Treat search terms as wildcard patterns (* and ?).
    use_ocr : bool
        Enable OCR for scanned PDFs and images.
    exclude_terms : list[str], optional
        Exclude lines matching these terms.
    file_types : list[str], optional
        Limit to these file extensions (e.g. [".pdf", ".docx"]).
    file_names : list[str], optional
        Search only these specific filenames.
    context_before : int
        Number of lines to include before each match.
    context_after : int
        Number of lines to include after each match.
    proximity : int
        If > 0, require all terms within this many words of each other.
    cores : int, optional
        Number of CPU cores. None = auto-detect.
    use_index : bool, optional
        True = use index, False = direct scan, None = auto-detect.
    progress : callable, optional
        Callback ``progress(done, total, filename)`` called as files are processed.
    expression : str, optional
        Boolean expression string (e.g. "(bob AND amy) OR fred"). Mutually exclusive
        with match_all, exclude_terms, and proximity.
    range_filters : list[str], optional
        Range filter specs (e.g. ["amount:1000..5000", "date:2024-01-01..2024-12-31"]).
        Content ranges filter matched lines; metadata ranges filter files.

    Returns
    -------
    SearchResult
        Structured results with matches, files_searched, skipped_files, elapsed, used_index.

    Raises
    ------
    ValueError
        For invalid parameter combinations (e.g. regex + fuzzy).
    """
    # ── Parse range filters ────────────────────────────────────
    from docsearch.range_query import parse_range, split_ranges
    parsed_ranges = []
    if range_filters:
        for spec_str in range_filters:
            parsed_ranges.append(parse_range(spec_str))
    content_ranges, metadata_ranges, filename_ranges = split_ranges(parsed_ranges)

    # ── Validate parameters ─────────────────────────────────────
    if expression is not None:
        if match_all:
            raise ValueError("Cannot combine expression with match_all. Use AND/OR in the expression.")
        if exclude_terms:
            raise ValueError("Cannot combine expression with exclude_terms. Use NOT in the expression.")
        if proximity > 0:
            raise ValueError("Cannot combine expression with proximity search.")
        from docsearch.expr_parser import parse_expression, extract_terms
        expression_ast = parse_expression(expression)
        if not search_terms:
            search_terms = extract_terms(expression_ast)
        if use_regex:
            for term in extract_terms(expression_ast):
                try:
                    re.compile(term)
                except re.error as e:
                    raise ValueError(f"Invalid regex pattern '{term}' in expression: {e}")
    else:
        expression_ast = None
        if not search_terms and not range_filters:
            raise ValueError("No search terms provided.")
    if use_fuzzy and use_regex:
        raise ValueError("Cannot combine fuzzy and regex search modes.")
    if use_wildcard and use_regex:
        raise ValueError("Cannot combine wildcard and regex search modes.")
    if use_wildcard and use_fuzzy:
        raise ValueError("Cannot combine wildcard and fuzzy search modes.")
    if expression is None and use_regex:
        for term in search_terms:
            try:
                re.compile(term)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern '{term}': {e}")
    if proximity > 0 and len(search_terms) < 2:
        raise ValueError("Proximity search requires at least 2 search terms.")

    # ── Resolve defaults ────────────────────────────────────────
    if directory is None:
        directory = os.getcwd()
    if exclude_terms is None:
        exclude_terms = []
    if cores is None:
        cores = _default_cores()

    use_proximity = proximity > 0
    if use_proximity:
        match_all = True
    use_context = context_before > 0 or context_after > 0

    # Convert file_types list to set if provided
    ft_set = set(file_types) if file_types else None

    start_time = time.time()

    # ── Build search config dict (used by scanner/indexer) ──────
    search_config = {
        "search_terms": search_terms,
        "use_regex": use_regex,
        "match_all": match_all,
        "use_proximity": use_proximity,
        "proximity": proximity,
        "use_context": use_context,
        "context_before": context_before,
        "context_after": context_after,
        "use_ocr": use_ocr,
        "use_fuzzy": use_fuzzy,
        "exclude_terms": exclude_terms,
        "use_wildcard": use_wildcard,
        "use_whole_word": use_whole_word,
        "expression_ast": expression_ast,
        "_ocr_image_func": _ocr_image,
        "content_ranges": content_ranges,
        "metadata_ranges": metadata_ranges,
        "filename_ranges": filename_ranges,
    }

    # ── Determine search path ───────────────────────────────────
    matches = []
    skipped_files = []
    all_files = []
    indexed = False

    if use_index is None:
        use_index = index_exists(directory)
    elif use_index:
        use_index = index_exists(directory)

    if use_index:
        indexed = True
        try:
            refresh_index(directory, recursive=True, use_ocr=use_ocr)
        except Exception:
            pass  # Search with existing index if refresh fails (e.g. DB locked)
        idx_matches, idx_skipped, all_files = search_with_index(
            directory, search_config, ft_set, file_names,
        )
        matches = [SearchMatch(*m) for m in idx_matches]
        skipped_files = list(idx_skipped)

        # If index was corrupt and deleted, fall back to direct scan
        if not index_exists(directory):
            indexed = False
            matches = []
            skipped_files = []

    if not indexed:
        result = discover_files(directory, recursive, use_ocr, ft_set, file_names)
        if isinstance(result, tuple):
            raise FileNotFoundError(result[1])
        all_files = result
        total = len(all_files)

        if total < 10 or cores == 1:
            for i, filepath in enumerate(all_files):
                filename = os.path.relpath(filepath, directory)
                if progress:
                    progress(i, total, filename)
                file_matches, file_skipped = _process_file((filepath, search_config))
                matches.extend(SearchMatch(*m) for m in file_matches)
                skipped_files.extend(file_skipped)
        else:
            pool = multiprocessing.Pool(
                processes=cores,
                initializer=signal.signal,
                initargs=(signal.SIGINT, signal.SIG_IGN),
            )
            try:
                result_iter = pool.imap(
                    _process_file, [(f, search_config) for f in all_files]
                )
                for i in range(total):
                    filename = os.path.relpath(all_files[i], directory)
                    if progress:
                        progress(i, total, filename)
                    file_matches, file_skipped = next(result_iter)
                    matches.extend(SearchMatch(*m) for m in file_matches)
                    skipped_files.extend(file_skipped)
            finally:
                pool.terminate()
                pool.join()

        if progress and total > 0:
            progress(total, total, "done")

    elapsed = time.time() - start_time

    return SearchResult(
        matches=matches,
        files_searched=all_files,
        skipped_files=skipped_files,
        elapsed=elapsed,
        used_index=indexed,
    )
