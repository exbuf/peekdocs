# Security Policy

peekdocs is provided "as is" under the [MIT License](LICENSE) without warranty of any kind. This document describes how to report suspected security vulnerabilities and what response you can reasonably expect.

For the architectural reference — every file peekdocs writes, where, with what sensitivity, and what's outside the application's control — see [docs/SECURITY.md](docs/SECURITY.md). This file is only about reporting issues.

## Reporting a vulnerability

**Preferred channel: GitHub's private vulnerability reporting.** Use the *Report a vulnerability* button on the repository's **Security** tab (https://github.com/exbuf/peekdocs/security/advisories/new). This creates a private advisory that only the maintainer sees, with built-in coordinated-disclosure tooling.

**Please do not** open a public issue, post in Discussions, or send tweets about a suspected vulnerability before it has been addressed — coordinated disclosure protects users in the window before a fix ships.

A useful report includes:

- peekdocs version (`peekdocs --version` or the Releases page tag)
- OS and Python version
- Steps to reproduce the issue, or a minimal proof of concept
- Impact assessment in your own words — what an attacker could do, and what they would need (local user, specific file in the search path, network access, etc.)
- Whether the issue is already publicly known (CVE, blog post, other report)

## Supported versions

Only the **latest release** receives security fixes. Older releases are frozen at the version that shipped. If you need a fix backported, the practical answer is to upgrade.

| Version | Supported |
|---------|-----------|
| Latest release on `main` | ✅ |
| Any prior release | ❌ |

There is no long-term-support branch and no commitment to one.

## In scope

Security-relevant issues the maintainer wants to know about:

- Vulnerabilities in peekdocs's own source code (path traversal, command injection, unsafe deserialization, etc.) that an attacker could exploit by feeding peekdocs a crafted document, archive, or search query.
- Vulnerabilities in the CLI surface that could be triggered by an attacker who controls flag values or environment variables a user passes in.
- Issues that cause peekdocs to read, write, or expose files the user did not intend (peekdocs is read-only by design with respect to user documents; a vulnerability that breaks that contract is in scope).
- Issues that cause peekdocs to make network calls (peekdocs is local-only by design; a vulnerability that triggers any outbound network activity is in scope).
- Privilege-escalation issues — peekdocs is supposed to run with the invoking user's permissions and nothing more.

## Out of scope

These are documented limitations, not security vulnerabilities:

- **Process arguments visible to other users on shared systems** — `peekdocs "sensitive-term"` puts the search term on the process command line, which other users on the same machine may see via `ps`. Use the Search Wizard's screen-only mode or read the term from a file rather than the CLI when this matters.
- **Operating-system level concerns** — swap space, hibernation files, backup software snapshotting the search folder, full-disk encryption being absent, force-kill leaving temporary files behind. These are properties of the host environment, not peekdocs.
- **Cloud-synced search folders** — peekdocs redirects reports to `~/peekdocs_reports` when it detects a cloud-synced output folder, but the source documents themselves remain wherever the user pointed peekdocs.
- **Third-party dependency vulnerabilities** — report these to the upstream project. peekdocs's dependency tree includes PyMuPDF, EbookLib, extract-msg, py7zr, fpdf2, customtkinter, and roughly a dozen others (full list in [`pyproject.toml`](pyproject.toml) and [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)). A CVE in PyMuPDF, for example, is upstream's to coordinate; peekdocs will pull the fix in via a dependency bump once it's available.
- **User-controlled regex patterns that are slow** — regex catastrophic backtracking is a documented property of the regex engine. peekdocs does not pre-compile or sandbox user-supplied patterns.
- **OCR accuracy** — OCR output is what Tesseract returns. Inaccurate OCR is not a vulnerability.

## What you can expect

The maintainer is one person, working on peekdocs without compensation. There is no on-call rotation, no SLA, and no commitment to any specific response time. In practice:

- A private advisory will usually get an acknowledgment within **about a week**, often much sooner.
- Triage and a proposed fix or mitigation typically follow within **two to four weeks** depending on complexity, the maintainer's availability, and whether the fix lives in peekdocs or upstream.
- Critical issues (remote code execution, credential disclosure, the read-only contract being broken) are prioritized over everything else; less-critical issues may take longer.
- If a report sits without acknowledgment for **more than 30 days**, treat that as silence rather than rejection. You may re-ping the advisory once. After that, you are free to disclose publicly using whatever coordinated-disclosure norms you prefer.

## Coordinated disclosure

A fix-then-disclose model is preferred:

1. Reporter and maintainer coordinate privately on the advisory.
2. A fix lands on `main`, ships in a new release, and the release notes describe the issue at a level appropriate for users to evaluate their exposure.
3. The advisory is published on GitHub Security Advisories with credit to the reporter (or anonymous, if preferred).

Reporters who would rather publish on a public timeline are welcome to — peekdocs is MIT-licensed and you owe nothing. A heads-up before publication is appreciated but not required.

## What this policy does not do

This policy describes how the maintainer intends to handle reports in good faith. It does **not** create any legal obligation, warranty, indemnity, or guaranteed response. The [MIT License](LICENSE) governs the legal relationship between peekdocs and its users; this document does not modify it.
