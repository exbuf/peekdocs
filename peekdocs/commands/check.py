"""``peekdocs --check`` — verify Python, dependencies, Tesseract, disk.

Prints a plain-text health report and returns exit 0 if everything the
install needs is present, exit 2 if any required dependency is missing.
Data collection lives in :func:`peekdocs.cli.run_system_check` (also
used by the GUI System Check dialog); this module only renders that
dict as terminal output.
"""
from __future__ import annotations


def handle_check() -> int:
    """Render ``peekdocs --check`` output and return an exit code.

    Returns ``0`` when all required dependencies are present, ``2``
    otherwise. Optional dependencies missing (rapidfuzz, pytesseract,
    Pillow, customtkinter) don't fail the check — they're informational.
    """
    from peekdocs.cli import run_system_check

    info = run_system_check()
    print(f"peekdocs {info['peekdocs_version']}")
    print(f"Python {info['python_version_full']}")
    print(f"OS: {info['os_system']} {info['os_release']}")
    print()

    v = info['python_version_tuple']
    py_min = info['tested_python_min']
    py_max = info['tested_python_max']
    if info['python_status'] == "below_min":
        print(f"Python version:  {v[0]}.{v[1]} (BELOW minimum {py_min[0]}.{py_min[1]}) — upgrade Python to {py_min[0]}.{py_min[1]} or later")
    elif info['python_status'] == "above_max":
        print(f"Python version:  {v[0]}.{v[1]} (above maximum tested {py_max[0]}.{py_max[1]}) — should work, but not yet verified")
    else:
        print(f"Python version:  {v[0]}.{v[1]} (ok)")
    print()

    print("Required dependencies:")
    for desc, pkg, status, ver in info['required_deps']:
        if status == "ok":
            print(f"  {desc} ({pkg}): ok (v{ver})")
        else:
            print(f"  {desc} ({pkg}): MISSING — install with: pip install {pkg}")
    print()

    print("Optional dependencies:")
    for desc, pkg, status, ver in info['optional_deps']:
        if status == "ok":
            print(f"  {desc} ({pkg}): ok (v{ver})")
        else:
            print(f"  {desc} ({pkg}): not installed — install with: pip install {pkg}")
    print()

    if info['tesseract_installed']:
        print("Tesseract OCR:   installed (OCR available with -O flag)")
    else:
        print("Tesseract OCR:   not installed (optional — needed only for -O flag)")

    print(f"SQLite version:  {info['sqlite_version']}")
    print()

    print(f"Disk space:      {info['disk_free_human']} free")
    if info['disk_low']:
        print("  Warning: Low disk space. Reports may fail to write.")
    print()

    if not info['all_ok']:
        print("Fix missing dependencies with: pipx upgrade peekdocs  (or see https://github.com/exbuf/peekdocs#installation)")
        print()
    else:
        print("All checks passed.")
        print()

    return 0 if info['all_ok'] else 2
