"""Shared constants for docsearch."""

import os

SUPPORTED_TYPES = {".docx", ".doc", ".pdf", ".csv", ".odt", ".txt", ".html", ".xlsx", ".xls", ".md", ".json", ".rtf", ".pptx", ".ppt", ".xml", ".log", ".yaml", ".yml", ".tsv", ".epub", ".ods", ".odp", ".toml", ".rst", ".tex", ".ini", ".cfg", ".sql", ".eml", ".msg", ".pst", ".zip", ".tar", ".gz", ".bz2", ".tgz", ".7z", ".rar", ".mbox", ".ics", ".vcf", ".pages"}

OCR_IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"}

FUZZY_THRESHOLD = 80

INDEX_FILENAME = ".docsearch.db"

TESTED_PYTHON_MIN = (3, 10)
TESTED_PYTHON_MAX = (3, 13)


def _default_cores():
    """Return the default number of worker processes: half of available cores, minimum 1."""
    cpu = os.cpu_count()
    if cpu is None:
        return 1
    return max(1, cpu // 2)
