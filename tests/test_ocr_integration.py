"""Integration tests for the OCR pipeline — real Tesseract, real image,
real ``pytesseract`` shell-out.

Motivated by the 1.2.77 release bug: the mocked tests in
``tests/test_paths.py`` and ``tests/test_cli.py`` verify Tesseract
*detection* (does ``find_tesseract()`` return a path?) but nothing
exercised the actual OCR *execution* (does ``pytesseract.image_to_string``
succeed?). That gap masked a real bug where detection succeeded via
fallback path but the pytesseract call still shelled out to the wrong
place because ``pytesseract.pytesseract.tesseract_cmd`` wasn't pinned.

These tests cover the whole ``find_tesseract → cmd-pin →
image_to_string → SearchResult.matches`` contract with a real image and
a real Tesseract binary. They're skipped when Tesseract isn't installed
locally, and CI runs them on Ubuntu with ``apt install tesseract-ocr``
(see ``.github/workflows/test.yml``).
"""
from __future__ import annotations

import pytest

from peekdocs.paths import find_tesseract


# Skip the whole module when Tesseract isn't available. The individual
# tests would fail in a way that's technically correct but noisy on
# developer machines that haven't installed Tesseract yet; a module-level
# skip is cleaner and matches the pattern in test_headless.py.
pytestmark = pytest.mark.skipif(
    find_tesseract() is None,
    reason="Tesseract not installed — needed for OCR integration tests",
)


@pytest.fixture(autouse=True)
def _clear_tesseract_cache():
    """Reset find_tesseract's lru_cache before each test in this module.

    Other tests in the suite (notably tests/test_cli.py's OCR paths)
    monkeypatch shutil.which to return fake Tesseract paths like
    /usr/local/bin/tesseract. When that runs before this file, the
    lru_cache captures the fake path — and after the monkeypatch tears
    down, find_tesseract keeps returning the stale cached value. The
    scanner then pins pytesseract.pytesseract.tesseract_cmd to a
    nonexistent binary and real OCR fails.

    Cache-clear here restores the real behavior so this test's own
    shutil.which lookup wins.
    """
    find_tesseract.cache_clear()
    yield
    find_tesseract.cache_clear()


def _make_test_image(path: str, text: str) -> None:
    """Render *text* into a PNG at *path* large enough for Tesseract to read.

    Uses PIL's default bitmap font upscaled onto a large canvas. Real OCR
    accuracy varies with font size, contrast, and rendering — we err on
    the side of "obviously readable" so the test isn't flaky on Tesseract
    version drift.
    """
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (800, 200), color="white")
    draw = ImageDraw.Draw(img)
    # Pillow 10+ accepts a size arg on load_default; older versions
    # ignore it and return the tiny built-in bitmap. On CI (Ubuntu +
    # modern Pillow) the size arg is honored; on older dev installs
    # Tesseract can still read the tiny default if the phrase is
    # distinctive enough.
    try:
        font = ImageFont.load_default(size=60)
    except TypeError:
        font = ImageFont.load_default()
    draw.text((40, 60), text, fill="black", font=font)
    img.save(path)


def test_ocr_finds_text_in_generated_png(tmp_path):
    """End-to-end: create a PNG with known text, run search() with OCR
    enabled, assert the text is found.

    Exercises the whole pipeline that the 1.2.77 bug slipped through:

      1. ``find_tesseract()`` returns a valid path.
      2. ``_ocr_image()`` sets ``pytesseract.pytesseract.tesseract_cmd``
         from that path.
      3. ``pytesseract.image_to_string()`` actually shells out and reads
         text.
      4. The extracted text lands in ``SearchResult.matches`` where the
         caller can find it.
    """
    img_path = tmp_path / "sample.png"
    _make_test_image(str(img_path), "PEEKDOCS OCR TEST")

    from peekdocs.api import search

    result = search(
        search_terms=["PEEKDOCS"],
        directory=str(tmp_path),
        use_ocr=True,
    )

    assert len(result.matches) > 0, (
        f"OCR search returned no matches. files_searched="
        f"{result.files_searched}, skipped_files={result.skipped_files}"
    )
    # Tesseract sometimes returns slightly different casing or spacing;
    # accept any match whose text contains our search term (case-insensitive).
    found_terms = [m.text for m in result.matches]
    assert any("PEEKDOCS" in t.upper() for t in found_terms), (
        f"OCR ran but PEEKDOCS not in extracted text. Got: {found_terms}"
    )


def test_ocr_does_not_scan_image_without_ocr_flag(tmp_path):
    """Sanity check: without ``use_ocr=True``, image files are excluded
    from the search entirely — no OCR attempted, no matches from image
    content. This guards against a future change accidentally routing
    images through OCR by default (which would blow up scan time on any
    folder with photos).
    """
    img_path = tmp_path / "sample.png"
    _make_test_image(str(img_path), "PEEKDOCS OCR TEST")

    from peekdocs.api import search

    result = search(
        search_terms=["PEEKDOCS"],
        directory=str(tmp_path),
        use_ocr=False,
    )

    # Image files aren't in SUPPORTED_TYPES — discover_files skips them
    # when use_ocr=False. So we should see zero files searched.
    assert len(result.files_searched) == 0
    assert len(result.matches) == 0
