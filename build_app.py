"""Build standalone peekdocs executables with PyInstaller.

Usage:
    python build_app.py          # build both GUI and CLI
    python build_app.py gui      # build GUI only
    python build_app.py cli      # build CLI only

Output goes to the dist/ folder:
    macOS:   dist/peekdocs-gui.app, dist/peekdocs (CLI binary)
    Windows: dist/peekdocs-gui.exe, dist/peekdocs.exe
"""

import subprocess
import sys
import os

# Common hidden imports that PyInstaller misses
HIDDEN_IMPORTS = [
    "customtkinter",
    "PIL",
    "PIL._tkinter_finder",
    "fitz",             # PyMuPDF
    "docx",
    "openpyxl",
    "odf",
    "striprtf",
    "pptx",
    "ebooklib",
    "pytesseract",
    "rapidfuzz",
    "olefile",
    "xlrd",
    "extract_msg",
    "py7zr",
    "rarfile",
    "fpdf",
    "sqlite3",
]

# Package metadata to copy into the bundle. PyInstaller does NOT ship
# .dist-info directories by default, which means importlib.metadata.version()
# fails inside the bundle and `peekdocs --check` reports every dep version as
# "?". Listing each package here tells PyInstaller to copy that package's
# .dist-info into the bundle so version lookups work at runtime.
#
# Keep in sync with peekdocs/cli.py:_REQUIRED_MODULES and _OPTIONAL_MODULES —
# every "package" string (the second element of each tuple) listed there
# must also appear here, or its version will show as "?" in the standalone
# `peekdocs --check` output.
COPY_METADATA = [
    "peekdocs",
    # Required deps (peekdocs/cli.py:_REQUIRED_MODULES)
    "pymupdf",
    "python-docx",
    "openpyxl",
    "python-pptx",
    "ebooklib",
    "striprtf",
    "odfpy",
    # Optional deps (peekdocs/cli.py:_OPTIONAL_MODULES)
    "rapidfuzz",
    "pytesseract",
    "Pillow",
    "customtkinter",
]


def find_package_path(package_name):
    """Find the installed location of a package."""
    import importlib
    mod = importlib.import_module(package_name)
    return os.path.dirname(mod.__file__)


def build_gui():
    """Build the GUI executable."""
    ctk_path = find_package_path("customtkinter")

    # macOS .app bundles require --onedir (--onefile is deprecated for
    # windowed apps and will become an error in PyInstaller v7).
    # Windows uses --onefile for a single .exe.
    is_mac = sys.platform == "darwin"
    # On Windows, the path separator for --add-data is ; instead of :
    sep = ";" if sys.platform == "win32" else ":"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "peekdocs-gui",
        "--windowed",                          # no console window (GUI app)
        "--onedir" if is_mac else "--onefile",  # .app bundle or single .exe
        "--add-data", f"{ctk_path}{sep}customtkinter",  # customtkinter assets
        "--noconfirm",                         # overwrite without asking
    ]

    # Copy installed package metadata into the bundle so
    # importlib.metadata.version() works at runtime — needed for
    # the GUI title bar (peekdocs's own version) and for the
    # dependency version numbers reported by Tools → System Check.
    # See COPY_METADATA comment at the top of this file.
    for pkg in COPY_METADATA:
        cmd.extend(["--copy-metadata", pkg])

    for imp in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", imp])

    # Entry point
    cmd.append("peekdocs/gui/__init__.py")

    print("Building GUI...")
    print(f"  Command: {' '.join(cmd[:6])}...")
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__) or ".")
    if result.returncode == 0:
        print("  GUI build complete — check dist/ folder")
    else:
        print("  GUI build FAILED")
        sys.exit(1)


def build_cli():
    """Build the CLI executable."""
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "peekdocs",
        "--console",                           # console app
        "--onefile",                           # single executable
        "--noconfirm",                         # overwrite without asking
    ]

    # Copy installed package metadata into the bundle so
    # importlib.metadata.version() works at runtime — used by
    # `peekdocs --version` (peekdocs itself) AND by `peekdocs --check`
    # for every dependency version number. Without this, every dep
    # line in --check output reads "ok (v?)" because the bundle
    # lacks .dist-info directories. See COPY_METADATA comment at the
    # top of this file.
    for pkg in COPY_METADATA:
        # customtkinter isn't a runtime dep of the CLI, but keeping
        # it in COPY_METADATA means GUI/CLI share one source of truth.
        # The CLI skips it because the GUI hidden-import filter does
        # the same below; keeping --copy-metadata for it is harmless.
        cmd.extend(["--copy-metadata", pkg])

    for imp in HIDDEN_IMPORTS:
        if imp not in ("customtkinter", "PIL._tkinter_finder"):
            cmd.extend(["--hidden-import", imp])

    # Entry point
    cmd.append("peekdocs/cli.py")

    print("Building CLI...")
    print(f"  Command: {' '.join(cmd[:6])}...")
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__) or ".")
    if result.returncode == 0:
        print("  CLI build complete — check dist/ folder")
    else:
        print("  CLI build FAILED")
        sys.exit(1)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "both"

    if target in ("gui", "both"):
        build_gui()
    if target in ("cli", "both"):
        build_cli()

    if target == "both":
        print("\nDone! Both executables are in the dist/ folder.")
