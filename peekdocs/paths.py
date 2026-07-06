"""Package-wide resource path resolution.

Consolidates the ``sys._MEIPASS`` check that several call sites need for
locating files bundled with peekdocs — the LICENSE viewer in the About
dialog, the customtkinter asset lookup, and anything else that reads
files packaged into the PyInstaller bundle via ``--add-data`` in
``build_app.py``.

Prior to this module, each consumer reinvented the check:

    if hasattr(sys, "_MEIPASS"):
        candidates.append(os.path.join(sys._MEIPASS, "LICENSE"))
    _here = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.normpath(os.path.join(_here, "..", "..", "LICENSE")))

Which is small but easy to get subtly wrong (wrong number of ``..``
parents, forgotten source-checkout fallback, forgotten ``normpath``).
The ``resource_path`` helper below is a single source of truth.
"""
from __future__ import annotations

import functools
import os
import platform
import shutil
import sys


def resource_path(relative_path: str) -> str:
    """Return the absolute path to a resource that ships with peekdocs.

    Handles two install modes:

    * **PyInstaller standalone binary** — searches ``sys._MEIPASS`` and
      a small set of well-known candidate locations relative to it.
      ``build_app.py`` copies LICENSE, NOTICE, THIRD_PARTY_NOTICES.md,
      and customtkinter assets into the bundle via ``--add-data``, but
      *where* PyInstaller physically places them depends on the build
      mode:

      - ``--onefile`` (Windows / Linux CLI + GUI): everything extracts
        to ``sys._MEIPASS``, so ``_MEIPASS/relative_path`` is correct.
      - ``--onedir`` non-``.app`` (Linux CLI, direct-dir builds):
        same — bundle root == ``sys._MEIPASS``.
      - ``--onedir --windowed`` macOS ``.app`` bundle: ``sys._MEIPASS``
        points at ``Contents/Frameworks/`` (runtime + libraries),
        while ``--add-data`` payloads land in
        ``Contents/Resources/``. Traditional
        ``os.path.join(_MEIPASS, relative_path)`` misses the file
        entirely; the fallback candidate
        ``os.path.join(_MEIPASS, "..", "Resources", relative_path)``
        finds it. This is the 1.2.80 bug that made
        "About → View License" report "LICENSE file not found" on
        macOS.

    * **Source checkout / editable install** — uses the repository root,
      which is one directory above this file (``peekdocs/paths.py`` →
      ``peekdocs/`` → repo root). This is the ``pip install -e .``
      case and the plain ``python -m peekdocs`` from a git clone.

    **Does NOT handle** the regular pip / pipx install case. In that
    case the peekdocs package sits inside site-packages/, and LICENSE
    ships alongside it in a sibling ``peekdocs-<version>.dist-info/``
    directory (per PEP 639's ``license-files`` mechanism). The path
    returned here would point at ``site-packages/LICENSE``, which
    doesn't exist. Callers that need to support pip / pipx installs
    should check ``os.path.exists`` on the return value and fall back
    to ``importlib.metadata.distribution("peekdocs")._path`` to locate
    the dist-info directory. This helper deliberately doesn't perform
    that lookup itself because it's only needed for a subset of
    resources (LICENSE, NOTICE) and adds import cost per call site.

    Parameters
    ----------
    relative_path :
        Path relative to the resource root. Use forward slashes for
        cross-platform paths; :func:`os.path.join` handles the rest.

    Returns
    -------
    str
        Absolute path. When PyInstaller-bundled, the returned path is
        the first candidate that exists on disk. If none exist, the
        traditional ``_MEIPASS/relative_path`` is returned so the
        caller's "not found" fallback logic still works cleanly.
    """
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller places data files at different locations depending
        # on --onefile vs --onedir vs macOS .app bundle. Try each in the
        # order most likely to succeed and return the first hit.
        candidates = [
            # Traditional --onefile / --onedir bundle root (Windows /
            # Linux, and macOS non-.app builds).
            os.path.join(sys._MEIPASS, relative_path),
            # macOS .app bundle: --add-data lands in
            # Contents/Resources/, while _MEIPASS is Contents/Frameworks/.
            # os.path.normpath collapses the "..".
            os.path.normpath(
                os.path.join(sys._MEIPASS, "..", "Resources", relative_path)
            ),
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
        # No candidate exists on disk. Return the traditional path so
        # the caller's os.path.exists() check hits False and its
        # "resource missing" fallback runs.
        return candidates[0]

    # Source checkout: this file is peekdocs/paths.py, so the repo root
    # is one parent directory up.
    _here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(_here, "..", relative_path))


# Well-known Tesseract install locations by OS. Consulted only when
# ``shutil.which("tesseract")`` returns None — which is common when
# peekdocs runs from a macOS ``.app`` bundle launched via Finder / Dock
# / Spotlight, because macOS gives GUI-launched processes a stripped
# PATH (``/usr/bin:/bin:/usr/sbin:/sbin``) that omits Homebrew's
# ``/opt/homebrew/bin`` and MacPorts' ``/opt/local/bin``. Same category
# of problem on Windows for third-party installs outside the default
# PATH. On Linux, GUIs launched via ``.desktop`` files typically get
# the user's PATH from the login shell, so the fallback is mostly
# defensive there.
_TESSERACT_FALLBACK_PATHS = {
    "Darwin": (
        "/opt/homebrew/bin/tesseract",   # Apple Silicon Homebrew
        "/usr/local/bin/tesseract",      # Intel Homebrew
        "/opt/local/bin/tesseract",      # MacPorts
    ),
    "Windows": (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ),
    "Linux": (
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
    ),
}


def read_bundled_text(name: str) -> str | None:
    """Return the text of a bundled resource, or ``None`` if unavailable.

    Universal helper that finds LICENSE, NOTICE, and
    THIRD_PARTY_NOTICES.md across every peekdocs install method:

    1. **Frozen** (PyInstaller ``.exe`` / ``.app``) — reads via
       :func:`resource_path`, which searches ``_MEIPASS`` and the
       macOS ``.app`` bundle's ``Contents/Resources/`` fallback.
    2. **Source checkout / editable install** — same
       :func:`resource_path` path resolves to the repo root.
    3. **pip / pipx install** — falls back to
       ``importlib.metadata.distribution("peekdocs").read_text(...)``
       which finds files in the ``.dist-info/`` directory. Tries
       PEP 639's ``licenses/<name>`` location first (setuptools ≥ 77
       with ``license-files`` in pyproject.toml) then the legacy
       ``<name>`` directly in ``.dist-info/`` for older wheels.

    Returns the file contents on success, or ``None`` when the
    resource isn't findable anywhere. Callers should render their own
    "resource missing" fallback (typically a GitHub URL pointing at
    the source-of-truth file on ``main``).

    This helper exists because ``resource_path`` deliberately does
    **not** chase into ``.dist-info/`` (see its docstring's "does not
    handle" section). Consolidating the fallback here keeps the
    knowledge in one place — the About viewer's LICENSE lookup, and
    any future NOTICE / third-party-notices viewer, all use the same
    universal find path.
    """
    # Try resource_path first — covers PyInstaller frozen builds and
    # source checkouts.
    path = resource_path(name)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        pass

    # Fall back to importlib.metadata for pip / pipx installs.
    # Lazy-import to avoid the metadata module cost on the frozen path.
    try:
        from importlib.metadata import distribution
        dist = distribution("peekdocs")
        # PEP 639 layout (setuptools ≥ 77): licenses/<name>
        text = dist.read_text(f"licenses/{name}")
        if text is not None:
            return text
        # Legacy layout: <name> directly in .dist-info/
        text = dist.read_text(name)
        if text is not None:
            return text
    except Exception:
        # Package metadata unavailable (very rare — most likely a
        # broken install). Fall through to returning None.
        pass

    return None


def format_bytes(n: int) -> str:
    """Format a byte count as a human-readable SI-decimal (1000-based) size.

    Tiers: ``bytes`` (< 1 KB), ``KB``, ``MB``, ``GB``. Two decimal places
    above the base tier. Single source of truth for peekdocs's user-facing
    byte formatting — before this helper, three separate implementations
    lived in ``reporter.py``, ``cli.py``, and ``gui/_mixin_file_analysis.py``
    and drifted (the GUI used IEC-binary 1024-based sizes, the others used
    SI-decimal; the reporter didn't have a GB tier at all). A user could
    see "2.10 MB" in a report and "2.00 MiB" in the GUI dupe finder for
    the same file. Consolidated here for consistency.

    SI decimal is the peekdocs convention because report output (the
    externally visible surface) has always used it. GUI file-analysis
    dialogs switched from IEC binary to match; the numeric difference is
    tiny (< 5% for MB, < 8% for GB) and consistency across surfaces
    wins over strict binary accuracy.

    Parameters
    ----------
    n :
        Non-negative byte count. Passing a negative value is not
        expected in normal usage; the returned string will contain the
        sign but the tier logic still works.

    Returns
    -------
    str
        Human-readable size string. Examples: ``"342 bytes"``,
        ``"12.34 KB"``, ``"1.20 MB"``, ``"3.50 GB"``.
    """
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f} GB"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f} MB"
    if n >= 1_000:
        return f"{n / 1_000:.2f} KB"
    return f"{n} bytes"


@functools.lru_cache(maxsize=1)
def find_tesseract() -> str | None:
    """Return the absolute path to the ``tesseract`` executable, or None.

    Search order:

    1. ``shutil.which("tesseract")`` — the fast path when the current
       process's PATH is correctly configured.
    2. Well-known install locations for the current OS — the fallback
       for macOS GUI launches (which get a stripped PATH from Finder /
       Dock / Spotlight and miss Homebrew's ``/opt/homebrew/bin``) and
       for Windows installs outside the default PATH.

    Result is cached for the process lifetime. If the user installs
    Tesseract after this function returns None once, they need to
    restart peekdocs to pick it up — same behavior the previous
    ``shutil.which`` call had, and consistent with the "restart peekdocs
    so the new PATH is picked up" advice in the OCR-toggle modal.

    Returns
    -------
    str or None
        Absolute path to the ``tesseract`` executable if found, else
        ``None``. Callers should pass the returned path to
        ``pytesseract.pytesseract.tesseract_cmd`` before calling
        ``pytesseract.image_to_string`` — that's necessary because
        pytesseract itself relies on the process PATH by default, so
        it hits the same GUI-launch trap that motivated this helper.
    """
    on_path = shutil.which("tesseract")
    if on_path:
        return on_path

    fallbacks = _TESSERACT_FALLBACK_PATHS.get(platform.system(), ())
    for candidate in fallbacks:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    return None
