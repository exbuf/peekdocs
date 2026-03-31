"""Debug script to test why the GUI shows 'Invalid input' on Windows."""
import os
from docsearch.gui import _build_command_from_values

folder = "c:/Users/bobsc/Documents"
search = "tired"

print(f"Folder: {folder}")
print(f"Folder exists: {os.path.isdir(folder)}")
print(f"Search text: {search}")
print()

cmd = _build_command_from_values(
    search_text=search,
    folder=folder,
    and_mode=False,
    recursive=False,
    fuzzy=False,
    wildcard=False,
    ocr=False,
    regex=False,
    exclude="",
    file_types="",
    proximity="",
    context_before="",
    context_after="",
)

print(f"Command result: {cmd}")
if cmd is None:
    print("ERROR: cmd is None - this is what causes 'Invalid input'")
elif cmd == "FLAGS_IN_SEARCH":
    print("ERROR: flags detected in search text")
else:
    print("OK - command built successfully")
