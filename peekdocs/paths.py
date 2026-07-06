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

    * **PyInstaller standalone binary** — uses ``sys._MEIPASS`` (the
      temporary extraction directory for ``--onefile`` bundles, or the
      bundle root for ``--onedir``). ``build_app.py`` copies LICENSE,
      NOTICE, THIRD_PARTY_NOTICES.md, and customtkinter assets into
      this location via ``--add-data``.
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
        Absolute path. The file may or may not actually exist — the
        caller is responsible for existence checks and fallback behavior.
        Callers that need to handle "resource missing" should use
        ``os.path.exists`` on the return value.
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)

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
