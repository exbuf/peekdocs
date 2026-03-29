"""SQLite FTS5 index for docsearch."""

import os
import re
import sqlite3
import time
from datetime import datetime
from importlib.metadata import version as pkg_version

from docsearch.constants import INDEX_FILENAME
from docsearch.scanner import _extract_lines, _ocr_image, _search_file_lines, discover_files


# ─── Database setup ───────────────────────────────────────


def _db_path(directory):
    """Return the path to the index database in the given directory."""
    return os.path.join(directory, INDEX_FILENAME)


def index_exists(directory):
    """Return True if an index database exists in directory."""
    return os.path.exists(_db_path(directory))


def _connect(directory):
    """Open a connection to the index database with WAL mode and foreign keys."""
    path = _db_path(directory)
    conn = sqlite3.connect(path, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _create_schema(conn):
    """Create the database schema if it doesn't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY,
            filepath TEXT UNIQUE NOT NULL,
            filename TEXT NOT NULL,
            file_dir TEXT NOT NULL,
            extension TEXT NOT NULL,
            size INTEGER NOT NULL,
            mtime REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS paragraphs (
            id INTEGER PRIMARY KEY,
            file_id INTEGER NOT NULL,
            line_num INTEGER NOT NULL,
            text TEXT NOT NULL,
            FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS paragraphs_fts USING fts5(
            text, content='paragraphs', content_rowid='id'
        );

        CREATE TRIGGER IF NOT EXISTS paragraphs_ai AFTER INSERT ON paragraphs BEGIN
            INSERT INTO paragraphs_fts(rowid, text) VALUES (new.id, new.text);
        END;

        CREATE TRIGGER IF NOT EXISTS paragraphs_ad AFTER DELETE ON paragraphs BEGIN
            INSERT INTO paragraphs_fts(paragraphs_fts, rowid, text)
                VALUES('delete', old.id, old.text);
        END;
    """)


def _validate_db(directory):
    """Check if the index database is valid. Returns True if ok, False if corrupt."""
    try:
        conn = _connect(directory)
        conn.execute("SELECT COUNT(*) FROM files")
        conn.execute("SELECT COUNT(*) FROM paragraphs")
        conn.close()
        return True
    except sqlite3.DatabaseError:
        return False
    except sqlite3.OperationalError as e:
        # "database is locked" is not corruption — treat as valid
        if "locked" in str(e).lower():
            return True
        return False


def _handle_corrupt_db(directory):
    """Delete a corrupt database and print a warning. Returns True if deleted."""
    import sys
    clear_index(directory)
    print("Warning: Index database was corrupted and has been removed.",
          file=sys.stderr)
    print("Rebuild with: docsearch --index", file=sys.stderr)
    return True


# ─── Index building ──────────────────────────────────────


def _index_single_file(conn, filepath, use_ocr, ocr_func):
    """Extract and index a single file into the database."""
    filename = os.path.basename(filepath)
    file_dir = os.path.dirname(filepath)
    ext = os.path.splitext(filename)[1].lower()

    try:
        all_lines = _extract_lines(filepath, use_ocr, ocr_func)
    except Exception:
        return 0

    if not all_lines:
        return 0

    try:
        stat = os.stat(filepath)
    except OSError:
        return 0

    cursor = conn.execute(
        "INSERT INTO files (filepath, filename, file_dir, extension, size, mtime) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (filepath, filename, file_dir, ext, stat.st_size, stat.st_mtime)
    )
    file_id = cursor.lastrowid

    lines_to_insert = [(file_id, ln, text) for ln, text in all_lines if text.strip()]
    conn.executemany(
        "INSERT INTO paragraphs (file_id, line_num, text) VALUES (?, ?, ?)",
        lines_to_insert,
    )

    return len(lines_to_insert)


def build_index(directory, recursive=False, use_ocr=False, progress_callback=None):
    """Build or rebuild the full FTS5 index for files in directory.

    Args:
        directory: Root directory to index.
        recursive: If True, index files in subdirectories.
        use_ocr: If True, use OCR for scanned PDFs and images.
        progress_callback: Optional callable(done, total, filename) for progress.

    Returns:
        dict with keys: file_count, line_count, elapsed, errors
    """
    start = time.time()

    # If existing DB is corrupt, delete and start fresh
    if index_exists(directory) and not _validate_db(directory):
        clear_index(directory)

    try:
        conn = _connect(directory)
        _create_schema(conn)
        # Clear existing data for full rebuild
        conn.execute("DELETE FROM paragraphs")
        conn.execute("DELETE FROM files")
    except (sqlite3.DatabaseError, sqlite3.OperationalError):
        # Database broken beyond repair — delete and retry once
        clear_index(directory)
        conn = _connect(directory)
        _create_schema(conn)

    # Discover files
    result = discover_files(directory, recursive, use_ocr)
    if isinstance(result, tuple):
        conn.close()
        return {"file_count": 0, "line_count": 0, "elapsed": 0, "errors": [result[1]]}

    all_files = result
    total = len(all_files)
    errors = []
    file_count = 0
    line_count = 0
    ocr_func = _ocr_image

    for i, filepath in enumerate(all_files):
        filename = os.path.basename(filepath)

        if progress_callback:
            progress_callback(i, total, filename)

        try:
            all_lines = _extract_lines(filepath, use_ocr, ocr_func)
        except Exception as e:
            errors.append((filename, str(e)))
            continue

        if not all_lines:
            continue

        try:
            stat = os.stat(filepath)
        except OSError:
            continue

        ext = os.path.splitext(filename)[1].lower()
        cursor = conn.execute(
            "INSERT INTO files (filepath, filename, file_dir, extension, size, mtime) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (filepath, filename, os.path.dirname(filepath), ext, stat.st_size, stat.st_mtime)
        )
        file_id = cursor.lastrowid

        lines_to_insert = [(file_id, ln, text) for ln, text in all_lines if text.strip()]
        conn.executemany(
            "INSERT INTO paragraphs (file_id, line_num, text) VALUES (?, ?, ?)",
            lines_to_insert,
        )

        file_count += 1
        line_count += len(lines_to_insert)

    # Update meta
    try:
        version = pkg_version("docsearch")
    except Exception:
        version = "unknown"

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta_values = {
        "created_at": now,
        "last_updated": now,
        "recursive": str(recursive),
        "use_ocr": str(use_ocr),
        "docsearch_version": version,
    }
    for key, value in meta_values.items():
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            (key, value)
        )

    conn.commit()
    conn.close()

    elapsed = time.time() - start
    return {
        "file_count": file_count,
        "line_count": line_count,
        "elapsed": elapsed,
        "errors": errors,
    }


# ─── Incremental updates ─────────────────────────────────


def refresh_index(directory, recursive, use_ocr):
    """Incrementally update the index: add new files, re-index changed files, remove deleted.

    Returns:
        dict with keys: added, updated, removed, elapsed
    """
    start = time.time()

    if not _validate_db(directory):
        _handle_corrupt_db(directory)
        return {"added": 0, "updated": 0, "removed": 0, "elapsed": 0}

    conn = _connect(directory)
    try:
        # Get current files on disk
        result = discover_files(directory, recursive, use_ocr)
        if isinstance(result, tuple):
            return {"added": 0, "updated": 0, "removed": 0, "elapsed": 0}

        current_files = set(result)

        # Get indexed files
        rows = conn.execute("SELECT id, filepath, mtime, size FROM files").fetchall()
        indexed = {row[1]: (row[0], row[2], row[3]) for row in rows}
        indexed_paths = set(indexed.keys())

        new_files = sorted(current_files - indexed_paths)
        deleted_paths = indexed_paths - current_files
        deleted_file_ids = [indexed[p][0] for p in deleted_paths]

        changed_files = []
        for filepath in current_files & indexed_paths:
            file_id, old_mtime, old_size = indexed[filepath]
            try:
                stat = os.stat(filepath)
                if stat.st_mtime != old_mtime or stat.st_size != old_size:
                    changed_files.append((filepath, file_id))
            except OSError:
                deleted_file_ids.append(file_id)

        ocr_func = _ocr_image

        # Remove deleted files (CASCADE deletes paragraphs, triggers update FTS)
        for file_id in deleted_file_ids:
            conn.execute("DELETE FROM files WHERE id = ?", (file_id,))

        # Re-index changed files (delete and re-add)
        for filepath, file_id in changed_files:
            conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
            _index_single_file(conn, filepath, use_ocr, ocr_func)

        # Index new files
        for filepath in new_files:
            _index_single_file(conn, filepath, use_ocr, ocr_func)

        # Update last_updated timestamp
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            ("last_updated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )

        conn.commit()
    finally:
        conn.close()

    elapsed = time.time() - start
    return {
        "added": len(new_files),
        "updated": len(changed_files),
        "removed": len(deleted_file_ids),
        "elapsed": elapsed,
    }


# ─── Index management ────────────────────────────────────


def clear_index(directory):
    """Delete the index database file. Returns True if deleted, False if not found."""
    path = _db_path(directory)
    if os.path.exists(path):
        os.remove(path)
        # Also remove WAL and SHM files if present
        for suffix in ("-wal", "-shm"):
            aux = path + suffix
            if os.path.exists(aux):
                os.remove(aux)
        return True
    return False


def index_status(directory):
    """Return index metadata as a dict, or None if no index exists."""
    if not index_exists(directory):
        return None

    if not _validate_db(directory):
        _handle_corrupt_db(directory)
        return None

    conn = _connect(directory)
    try:
        rows = conn.execute("SELECT key, value FROM meta").fetchall()
        meta = dict(rows)

        file_count = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        line_count = conn.execute("SELECT COUNT(*) FROM paragraphs").fetchone()[0]

        db_size = os.path.getsize(_db_path(directory))

        meta["file_count"] = file_count
        meta["line_count"] = line_count
        meta["db_size"] = db_size

        return meta
    finally:
        conn.close()


# ─── Search via index ─────────────────────────────────────


def _can_use_fts5_fast_path(config):
    """Determine if the search can be executed directly against FTS5.

    FTS5 fast path is used for simple keyword searches (OR/AND)
    without regex, fuzzy, wildcard, proximity, or context.
    All other modes use the parse-cache path for guaranteed identical results.
    """
    if config.get("use_regex", False):
        return False
    if config.get("use_fuzzy", False):
        return False
    if config.get("use_proximity", False):
        return False
    if config.get("use_context", False):
        return False
    if config.get("use_wildcard", False):
        return False
    if config.get("expression_ast") is not None:
        if not config.get("use_whole_word", False):
            return False  # expression without whole-word uses direct scan
    return True


def _build_fts5_query(search_terms, match_all):
    """Build an FTS5 MATCH query string.

    FTS5 is used as a candidate filter — results are post-filtered
    with Python substring matching for exact semantics.
    """
    if not search_terms:
        return None

    def fts5_escape(term):
        escaped = term.replace('"', '""')
        return f'"{escaped}"'

    parts = [fts5_escape(t) for t in search_terms]

    if match_all:
        return " AND ".join(parts)
    else:
        return " OR ".join(parts)


def search_with_index(directory, config, file_types=None, file_names=None):
    """Search using the FTS5 index.

    Args:
        directory: The working directory containing the index.
        config: search_config dict (same as used by _process_file).
        file_types: Optional set of extensions to filter.
        file_names: Optional list of specific filenames to search.

    Returns:
        (matches, skipped, all_indexed_files) where:
        - matches = list of (file_dir, filename, line_num, text) tuples
        - skipped = list of (filename, error_msg) tuples
        - all_indexed_files = list of filepaths in the index (for report)
    """
    if not _validate_db(directory):
        _handle_corrupt_db(directory)
        return [], [], []

    conn = _connect(directory)

    # Get list of indexed files (for report generation)
    file_filter_sql = ""
    file_filter_params = []
    if file_types:
        placeholders = ",".join("?" * len(file_types))
        file_filter_sql += f" AND extension IN ({placeholders})"
        file_filter_params.extend(file_types)
    if file_names:
        placeholders = ",".join("?" * len(file_names))
        file_filter_sql += f" AND LOWER(filename) IN ({placeholders})"
        file_filter_params.extend(n.lower() for n in file_names)

    all_indexed_files = [
        row[0] for row in conn.execute(
            f"SELECT filepath FROM files WHERE 1=1 {file_filter_sql} ORDER BY filepath",
            file_filter_params
        ).fetchall()
    ]

    use_fast_path = _can_use_fts5_fast_path(config)
    use_direct_scan = _can_use_direct_scan(config)

    if use_direct_scan:
        matches, skipped = _direct_scan_search(conn, config, file_filter_sql, file_filter_params)
    elif use_fast_path:
        matches, skipped = _fts5_fast_search(conn, config, file_filter_sql, file_filter_params)
    else:
        matches, skipped = _parse_cache_search(conn, config, file_filter_sql, file_filter_params)

    # Apply range filtering on index results
    content_ranges = config.get("content_ranges", [])
    metadata_ranges = config.get("metadata_ranges", [])
    if content_ranges:
        from docsearch.range_query import line_matches_content_ranges
        matches = [(fd, fn, ln, tx) for fd, fn, ln, tx in matches
                   if line_matches_content_ranges(tx, content_ranges)]
    if metadata_ranges:
        from docsearch.range_query import file_matches_metadata_ranges
        matches = [(fd, fn, ln, tx) for fd, fn, ln, tx in matches
                   if file_matches_metadata_ranges(os.path.join(fd, fn), metadata_ranges)]
    filename_ranges = config.get("filename_ranges", [])
    if filename_ranges:
        from docsearch.range_query import file_matches_filename_ranges
        matches = [(fd, fn, ln, tx) for fd, fn, ln, tx in matches
                   if file_matches_filename_ranges(fn, filename_ranges)]

    conn.close()
    return matches, skipped, all_indexed_files


def _can_use_direct_scan(config):
    """Determine if the search can use a direct paragraph scan.

    Direct scan reads all stored paragraphs and filters with Python substring
    matching.  This is used for AND mode and expression mode because FTS5's
    token-based matching can miss substring hits (e.g. "bob" inside "bobcat").
    Only applicable when no special matching modes are active.
    """
    if config.get("use_whole_word", False):
        return False  # FTS5 token matching is already whole-word — no need for direct scan
    if config.get("use_regex", False):
        return False
    if config.get("use_fuzzy", False):
        return False
    if config.get("use_wildcard", False):
        return False
    if config.get("use_proximity", False):
        return False
    if config.get("use_context", False):
        return False
    return True


def _direct_scan_search(conn, config, file_filter_sql, file_filter_params):
    """Scan all stored paragraphs with Python matching.

    Bypasses FTS5 entirely to avoid token-vs-substring mismatches.
    Used for AND mode and expression mode with plain literal terms.
    """
    sql = f"""
        SELECT f.file_dir, f.filename, p.line_num, p.text
        FROM paragraphs p
        JOIN files f ON p.file_id = f.id
        WHERE 1=1
        {file_filter_sql.replace('extension', 'f.extension').replace('filename)', 'f.filename)')}
        ORDER BY f.filepath, p.line_num
    """
    rows = conn.execute(sql, file_filter_params).fetchall()

    expression_ast = config.get("expression_ast")
    use_whole_word = config.get("use_whole_word", False)
    matches = []

    def _term_matches(term, text):
        if use_whole_word:
            return bool(re.search(r'\b' + re.escape(term) + r'\b', text, re.IGNORECASE))
        return term.lower() in text.lower()

    if expression_ast is not None:
        from docsearch.expr_parser import evaluate_expression

        for file_dir, filename, line_num, text in rows:
            if evaluate_expression(expression_ast, text, _term_matches, filename=filename):
                matches.append((file_dir, filename, line_num, text))
    else:
        search_terms = config["search_terms"]
        match_all = config.get("match_all", False)
        exclude_terms = config.get("exclude_terms", [])
        check = all if match_all else any
        for file_dir, filename, line_num, text in rows:
            if check(_term_matches(t, text) for t in search_terms):
                if exclude_terms and any(_term_matches(e, text) for e in exclude_terms):
                    continue
                matches.append((file_dir, filename, line_num, text))

    return matches, []


def _fts5_fast_search(conn, config, file_filter_sql, file_filter_params):
    """Execute search directly against FTS5 index.

    FTS5 returns candidates; Python post-filters for exact semantics.
    For expression mode with whole-word, uses FTS5 OR as pre-filter
    and evaluates the expression AST as post-filter.
    """
    search_terms = config["search_terms"]
    match_all = config["match_all"]
    exclude_terms = config.get("exclude_terms", [])
    expression_ast = config.get("expression_ast")

    # For expression mode, use OR pre-filter to get all candidate rows
    if expression_ast is not None:
        fts_query = _build_fts5_query(search_terms, match_all=False)
    else:
        fts_query = _build_fts5_query(search_terms, match_all)
    if not fts_query:
        return [], []

    # Query FTS5 for candidates, joined with files table
    sql = f"""
        SELECT f.file_dir, f.filename, p.line_num, p.text
        FROM paragraphs p
        JOIN paragraphs_fts fts ON p.id = fts.rowid
        JOIN files f ON p.file_id = f.id
        WHERE paragraphs_fts MATCH ?
        {file_filter_sql.replace('extension', 'f.extension').replace('filename)', 'f.filename)')}
        ORDER BY f.filepath, p.line_num
    """
    params = [fts_query] + file_filter_params

    try:
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        # FTS5 query syntax error — fall back to parse-cache path
        return _parse_cache_search(conn, config, file_filter_sql, file_filter_params)

    # Post-filter
    matches = []

    if expression_ast is not None:
        from docsearch.expr_parser import evaluate_expression
        use_whole_word = config.get("use_whole_word", False)

        def _term_matches(term, text):
            if use_whole_word:
                return bool(re.search(r'\b' + re.escape(term) + r'\b', text, re.IGNORECASE))
            return term.lower() in text.lower()

        for file_dir, filename, line_num, text in rows:
            if evaluate_expression(expression_ast, text, _term_matches, filename=filename):
                matches.append((file_dir, filename, line_num, text))
    else:
        check = all if match_all else any
        for file_dir, filename, line_num, text in rows:
            text_lower = text.lower()
            if check(t.lower() in text_lower for t in search_terms):
                if exclude_terms:
                    if any(e.lower() in text_lower for e in exclude_terms):
                        continue
                matches.append((file_dir, filename, line_num, text))

    return matches, []


def _parse_cache_search(conn, config, file_filter_sql, file_filter_params):
    """Read stored text from DB and apply Python matching logic.

    Used for regex, fuzzy, wildcards, proximity, and context modes.
    This guarantees identical results to the non-indexed code path.
    """
    # Get all indexed files matching filter
    sql = f"SELECT id, filepath, filename, file_dir FROM files WHERE 1=1 {file_filter_sql} ORDER BY filepath"
    file_rows = conn.execute(sql, file_filter_params).fetchall()

    all_matches = []
    all_skipped = []

    for file_id, filepath, filename, file_dir in file_rows:
        # Read stored lines from DB
        line_rows = conn.execute(
            "SELECT line_num, text FROM paragraphs WHERE file_id = ? ORDER BY id",
            (file_id,)
        ).fetchall()

        all_lines = [(ln, text) for ln, text in line_rows]

        if not all_lines:
            continue

        # Reuse the exact same matching logic
        file_matches, file_skipped = _search_file_lines(all_lines, file_dir, filename, config)
        all_matches.extend(file_matches)
        all_skipped.extend(file_skipped)

    return all_matches, all_skipped
