# peekdocs for IT and Security Teams — Deep Dive

This document expands on the [For IT and Security Teams](../README.md#for-it-and-security-teams) section of the README. The README answers the headline questions an IT evaluator asks; this document goes one level deeper: exactly where peekdocs stores data, exactly what's outside the application's control, and what mitigations are available.

## Q&A summary

For the at-a-glance Q&A table (Does it send data anywhere? Does it modify files? etc.), see [For IT and Security Teams](../README.md#for-it-and-security-teams) in the README.

### Data architecture

peekdocs stores data in three locations. No data is stored anywhere else — no registry, no hidden folders, no cloud.

**Per-folder files** (in each search folder, or redirected to `~/peekdocs_reports` for cloud-synced folders):

| File | Contains | Sensitive? | Cleanup |
|------|----------|-----------|---------|
| `peekdocs_standard_results.*` (.txt, .docx, .csv, .json, .pdf, .html) | Standard search results with matched text | Yes — contains text from your documents | Delete on Close, Wipe Session, Clear Files |
| `peekdocs_regex_results.*` (.txt, .docx) | Regex search results | Yes | Same as above |
| `peekdocs_suite_results.*` | Combined suite search results | Yes | Same as above |
| `peekdocs_report_*` | Named saved reports | Yes | Clear Files only (user must explicitly choose) |
| `peekdocs_accumulated_*` | Appended multi-search reports | Yes | Clear Files only |
| `.peekdocs.db` (.db, .db-wal, .db-shm) | Search index — extracted text of every indexed file | **Yes — full document text** | Delete on Close, Wipe Session, Clear Files |
| `.peekdocs_collection.json` | Saved search names and settings | No — contains settings, not document content | Clear Files only |
| `peekdocs_errors.log` | File paths that couldn't be read | Low — paths only, no content | Clear Files |

**Home directory** (`~`):

| File | Contains | Sensitive? | Cleanup |
|------|----------|-----------|---------|
| `~/.peekdocsrc` | Settings, recent searches, last search terms and folder | Moderate — reveals what was searched and where | Clear History on Close clears search terms, folder, and recent searches |
| `~/.peekdocs_history.json` | Timestamped log of past searches | Moderate — reveals search activity | Clear History on Close, Wipe Session |
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
- **Forced process termination.** Delete on Close and Clear History on Close run during normal app shutdown. If the process is force-killed (kill -9, Task Manager End Process, or a system crash), cleanup does not run and report files, search history, and indexes remain on disk. Use Wipe Session before closing if immediate cleanup is critical.
- **Custom regex patterns.** User-supplied regex patterns (in the search bar, Regex Search, or the Search Wizard) have no execution timeout. A pathological pattern (e.g., catastrophic backtracking) could cause the search to hang indefinitely. peekdocs validates regex syntax but does not limit pattern complexity.
- **Cloud folder detection is path-based.** peekdocs detects cloud-synced folders by looking for keywords like "OneDrive," "Dropbox," "Google Drive," and "iCloud" in the folder path. A folder with a cloud keyword in its name (e.g., `MyDropboxAnalysis`) would be falsely detected as cloud-synced and reports would be redirected to `~/peekdocs_reports`. Rename the folder to avoid the false trigger.
- **Safe output folder fallback.** If `~/peekdocs_reports` is itself inside a cloud-synced directory (e.g., the entire home directory is synced to OneDrive), peekdocs falls back to the system temp directory (`/tmp` on Unix/macOS, `%TEMP%` on Windows). This is automatic and requires no user action.
- **Backup software.** Report files written to disk may be picked up by backup software (Time Machine, Windows Backup, Backblaze, Carbonite, etc.) and uploaded to cloud storage. peekdocs avoids cloud-synced *folders* but cannot detect or prevent background backup services that copy files after they are written. Use **Delete on Close** or **Wipe Session** to remove report files before backups run.

### Support model and response expectations

peekdocs is a solo open-source project offered without warranty under the MIT License. The list below sets honest expectations for what users can rely on from the maintainer. IT teams evaluating peekdocs for use in their environment should weigh these against their internal risk-acceptance framework before deployment.

- **No service-level agreement.** Issues are triaged on no fixed cadence. Security-class reports are prioritized; feature requests and behavior-change complaints receive a response when time permits, which may be days or weeks. There is no guarantee of fix for any specific report.
- **No commercial support tier.** The maintainer does not provide paid support, custom builds, NDA-bound consulting, or compliance-attestation artifacts (SOC 2 reports, HIPAA business associate agreements, ISO 27001 certifications, signed SBOMs, etc.). Organizations whose vendor-management process requires those artifacts should evaluate whether peekdocs fits within their internal risk-acceptance framework rather than expect them to be produced on request.
- **Security disclosure.** Suspected security issues should be reported by opening a private security advisory at the project's GitHub repository (`Security` tab → `Advisories` → `Report a vulnerability`). Acknowledgement and fixes come when the maintainer has time; there is no commitment to respond within the 90-day window security researchers commonly use for coordinated disclosure. Reporters who want to publish details publicly — at any point, before or after a maintainer response — are free to do so; the maintainer does not request embargo and does not consider unilateral disclosure a breach of any norm.
- **Vendor-risk questionnaires.** Not completed. The information IT teams typically need — license, data architecture, network behavior, dependency list, change history — is in `LICENSE`, this document, the [README](../README.md), `THIRD_PARTY_NOTICES.md`, and `CHANGELOG.md`. Evaluators are encouraged to read the code directly; peekdocs is small enough to audit in a single sitting.
- **Behavior changes between releases.** Documented in `CHANGELOG.md` under `[Unreleased]` while in flight and under the release version once cut. Users who require stability across upgrades should pin to a specific version (`pip install peekdocs==X.Y.Z`) rather than rely on minor or patch releases preserving every default.
- **No commitment to merge contributions.** Pull requests are welcome and reviewed when time permits. Acceptance is at the maintainer's discretion; rejection or an extended review period is not a failure of the contribution and not a comment on its quality.
