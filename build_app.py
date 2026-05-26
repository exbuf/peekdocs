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
        # Copy peekdocs's installed package metadata into the bundle
        # so importlib.metadata.version("peekdocs") works at runtime
        # (used for the GUI title bar and for diagnostic --check output).
        "--copy-metadata", "peekdocs",
        "--noconfirm",                         # overwrite without asking
    ]

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
        "--copy-metadata", "peekdocs",         # so pkg_version() works in the bundle
        "--noconfirm",                         # overwrite without asking
    ]

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
