# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in peekdocs, please report it privately rather than opening a public issue.

**Email:** bobschoening@gmail.com

Please include:
- A description of the vulnerability
- Steps to reproduce it
- The version of peekdocs you're using (`peekdocs -v`)
- Your operating system and Python version

I will acknowledge your report within 48 hours and work with you to understand and address the issue.

## Security Design

peekdocs is designed with privacy and security as core principles:

- **No network calls** — peekdocs never connects to the internet. No telemetry, no analytics, no phone-home.
- **Read-only** — peekdocs never modifies, moves, or deletes your files.
- **PII Scan results are screen-only** — never written to disk, never piped, never returned via API.
- **Cloud-blocking** — reports are blocked from opening in cloud-based apps (Google Docs, Apple Pages). If your search folder is cloud-synced, reports are automatically redirected to a safe local folder.
- **No elevated privileges** — peekdocs runs with your normal user permissions and cannot access files you don't already have access to.

See [For IT and Security Teams](README.md#for-it-and-security-teams) in the README for the complete data architecture, known limitations, and threat model.

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest release | Yes |
| Older versions | Best-effort — upgrade recommended |
