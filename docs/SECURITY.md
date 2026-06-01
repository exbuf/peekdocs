# peekdocs for IT and Security Teams — Deep Dive

This document expands on the [For IT and Security Teams](../README.md#for-it-and-security-teams) section of the README. The README answers the headline questions an IT evaluator asks; this document goes one level deeper: exactly where peekdocs stores data, exactly what's outside the application's control, and what mitigations are available.

## Q&A summary

For the at-a-glance Q&A table (Does it send data anywhere? Does it modify files? etc.), see [For IT and Security Teams](../README.md#for-it-and-security-teams) in the README.

### Data architecture

peekdocs stores data in three locations. No data is stored anywhere else — no registry, no hidden folders, no cloud.

**Per-folder files** (in each search folder, or redirected to `~/peekdocs_reports` for cloud-synced folders):

| File | Contains | Sensitive? | Cleanup |
|------|----------|-----------|---------|
| `peekdocs_standard_results.*` (.txt, .docx, .csv, .json, .pdf, .html) | Standard search results with matched text | Yes — contains text from your documents | Delete on Close, Delete Now, Clear Files |
| `peekdocs_regex_results.*` (.txt, .docx) | Regex search results | Yes | Same as above |
| `peekdocs_suite_results.*` | Combined suite search results | Yes | Same as above |
| `peekdocs_report_*` | Named saved reports | Yes | Clear Files only (user must explicitly choose) |
| `peekdocs_accumulated_*` | Appended multi-search reports | Yes | Clear Files only |
| `.peekdocs.db` (.db, .db-wal, .db-shm) | Search index — extracted text of every indexed file | **Yes — full document text** | Delete on Close, Delete Now, Clear Files |
| `.peekdocs_collection.json` | Saved search names and settings | No — contains settings, not document content | Clear Files only |
| `peekdocs_errors.log` | File paths that couldn't be read | Low — paths only, no content | Clear Files |

**Home directory** (`~`):

| File | Contains | Sensitive? | Cleanup |
|------|----------|-----------|---------|
| `~/.peekdocsrc` | Settings, recent searches, last search terms and folder | Moderate — reveals what was searched and where | Clear History on Close clears search terms, folder, and recent searches |
| `~/.peekdocs_history.json` | Timestamped log of past searches | Moderate — reveals search activity | Clear History on Close, Delete Now |
| `~/.peekdocs_bookmarks.json` | Pinned file paths | Low — paths only | Clear Files |

**In memory only** (never written to disk):

| Data | Contains | Cleanup |
|------|----------|---------|
| Results Preview | Matched text displayed on screen | Clear Preview button, or close the app |

All peekdocs-created files use the `peekdocs` prefix or `.peekdocs` prefix, making them easy to identify and audit. peekdocs never writes to system directories, the registry, or any location outside the search folder and home directory.

### Known limitations (what peekdocs cannot control)

peekdocs takes extensive steps to protect user data, but the following are outside the application's control. We document them here so IT teams can make informed decisions:

- **CLI process arguments.** When the GUI runs a search, it launches `peekdocs` as a subprocess with search terms in the command line. On Unix/macOS, other users on the same machine can see process arguments via `ps aux`. A search term you'd rather not expose is briefly visible in the process list while the search runs.
- **Report file permissions.** Check **Restrict File Permissions** in Advanced Search Options to set all report files to owner-only read/write (chmod 600) on Unix/macOS. This prevents other users on shared machines from reading your search results. Off by default — leave unchecked if colleagues need to access reports in a shared folder. No effect on Windows (NTFS permissions are managed differently).
- **Temp files from archives.** Searching inside `.zip`, `.7z`, and `.rar` files may extract content to temporary directories. If the process is killed mid-search, those temp files could persist. Under normal operation they are cleaned up automatically.
- **Process memory.** Sensitive data found during a search sits in Python process memory until garbage collected. The operating system may write process memory to swap/page files on disk. This is standard behavior for all desktop applications and is not practically exploitable on a single-user machine, but it means sensitive data could theoretically persist in swap space after the application closes.
- **Error log file paths.** The error log (`peekdocs_errors.log`) contains file paths of documents that could not be read. This reveals which folders and files were being searched, though not the content of those files.
- **Microsoft 365 desktop apps.** peekdocs launches the local Word desktop application (`WINWORD.EXE` / `Microsoft Word.app`) — never Word Online or any browser-based editor. However, if the user is signed into a Microsoft 365 account, the desktop Word app may show the file in their "Recent" list on office.com, prompt to upload to OneDrive, or auto-save if the file is in a OneDrive-synced folder. peekdocs cannot control the internal cloud features of local applications after launching them. If this is a concern, use LibreOffice (which has no cloud integration) or the HTML report (which opens in your browser directly from local disk).
- **Forced process termination.** Delete on Close and Clear History on Close run during normal app shutdown. If the process is force-killed (kill -9, Task Manager End Process, or a system crash), cleanup does not run and report files, search history, and indexes remain on disk. Use Delete Now before closing if immediate cleanup is critical.
- **Custom regex patterns.** User-supplied regex patterns (in the search bar, Regex Search, or the Search Wizard) have no execution timeout. A pathological pattern (e.g., catastrophic backtracking) could cause the search to hang indefinitely. peekdocs validates regex syntax but does not limit pattern complexity.
- **Cloud folder detection is path-based.** peekdocs detects cloud-synced folders by looking for keywords like "OneDrive," "Dropbox," "Google Drive," and "iCloud" in the folder path. A folder with a cloud keyword in its name (e.g., `MyDropboxAnalysis`) would be falsely detected as cloud-synced and reports would be redirected to `~/peekdocs_reports`. Rename the folder to avoid the false trigger.
- **Safe output folder fallback.** If `~/peekdocs_reports` is itself inside a cloud-synced directory (e.g., the entire home directory is synced to OneDrive), peekdocs falls back to the system temp directory (`/tmp` on Unix/macOS, `%TEMP%` on Windows). This is automatic and requires no user action.
- **Backup software.** Report files written to disk may be picked up by backup software (Time Machine, Windows Backup, Backblaze, Carbonite, etc.) and uploaded to cloud storage. peekdocs avoids cloud-synced *folders* but cannot detect or prevent background backup services that copy files after they are written. Use **Delete on Close** or **Delete Now** to remove report files before backups run.
