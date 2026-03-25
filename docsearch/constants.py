"""Shared constants for docsearch."""

import os

SUPPORTED_TYPES = {".docx", ".pdf", ".csv", ".odt", ".txt", ".html", ".xlsx", ".md", ".json", ".rtf", ".pptx", ".xml", ".log", ".yaml", ".yml", ".tsv", ".epub", ".ods", ".odp", ".toml", ".rst", ".tex", ".ini", ".cfg", ".sql"}

OCR_IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"}

FUZZY_THRESHOLD = 80


TESTED_PYTHON_MIN = (3, 10)
TESTED_PYTHON_MAX = (3, 13)


def _default_cores():
    """Return the default number of worker processes: half of available cores, minimum 1."""
    cpu = os.cpu_count()
    if cpu is None:
        return 1
    return max(1, cpu // 2)
