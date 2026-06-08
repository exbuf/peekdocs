# Third-Party Notices

peekdocs's own source code is licensed under the [MIT License](LICENSE).
peekdocs depends on a number of third-party Python libraries, each
distributed under its own license. This file lists every direct
dependency declared in `pyproject.toml` along with its license and a
link to the upstream project, so that downstream developers, license-
compliance teams, and license-scan tools can audit the dependency
chain without re-discovering this information manually.

This file documents licenses as reported by the upstream packages
themselves. It is not legal advice. For derivative-work questions,
consult your own counsel. For commercial license inquiries (PyMuPDF,
where applicable), contact the upstream vendor directly.

## License summary

| Category | Libraries |
|---|---|
| **Permissive (MIT / BSD / Apache 2.0 / ISC / CC0 / MIT-CMU)** | python-docx, openpyxl, striprtf, python-pptx, Pillow, pytesseract, RapidFuzz, customtkinter, olefile, xlrd, rarfile |
| **Choice-of-license (multi-licensed, choose any)** | odfpy (Apache 2.0 OR GPL OR LGPL — Apache path is the permissive choice) |
| **Weak copyleft (LGPL)** | py7zr, fpdf2 |
| **Weak copyleft (LGPL, optional)** | libpff-python |
| **Strong copyleft (GPL)** | extract-msg |
| **Strong copyleft (AGPL v3 OR commercial)** | PyMuPDF, EbookLib |

## Per-library details

### Permissive licenses (no copyleft obligations on derivatives)

| Library | Version constraint | License | Upstream |
|---|---|---|---|
| **python-docx** | `>=1.0,<2.0` | MIT | https://github.com/python-openxml/python-docx |
| **openpyxl** | `>=3.1,<4.0` | MIT | https://openpyxl.readthedocs.io |
| **striprtf** | `>=0.0.20,<1.0` | BSD-3-Clause | https://github.com/joshy/striprtf |
| **python-pptx** | `>=1.0,<2.0` | MIT | https://github.com/scanny/python-pptx |
| **Pillow** | `>=10.0,<13.0` | MIT-CMU | https://python-pillow.github.io |
| **pytesseract** | `>=0.3,<1.0` | Apache 2.0 | https://github.com/madmaze/pytesseract |
| **RapidFuzz** | `>=3.0,<4.0` | MIT | https://github.com/rapidfuzz/RapidFuzz |
| **customtkinter** | `>=5.2,<6.0` | CC0 1.0 Universal | https://customtkinter.tomschimansky.com |
| **olefile** | `>=0.46,<1.0` | BSD | https://www.decalage.info/python/olefileio |
| **xlrd** | `>=2.0,<3.0` | BSD | http://www.python-excel.org/ |
| **rarfile** | `>=4.0,<5.0` | ISC | https://github.com/markokr/rarfile |

These libraries place no copyleft obligations on peekdocs or on any
work that depends on peekdocs. Each carries its own MIT- / BSD- /
Apache-style requirements (typically attribution in distributed
binaries) which downstream redistributors should respect, but no
share-alike or source-disclosure obligations.

### Multi-licensed — choose-your-license

| Library | Version constraint | License options | Upstream |
|---|---|---|---|
| **odfpy** | `>=1.4,<2.0` | Apache 2.0 OR GPL OR LGPL | https://github.com/eea/odfpy |

odfpy is distributed under a choice of three licenses. Downstream
consumers can pick whichever fits their needs. The Apache 2.0 branch
is the permissive choice and is recommended for downstream developers
who want to avoid copyleft obligations. Selecting the Apache 2.0
branch makes odfpy's licensing equivalent to the other permissive
libraries above.

### Weak copyleft — LGPL

| Library | Version constraint | License | Upstream |
|---|---|---|---|
| **py7zr** | `>=1.0,<2.0` | LGPL-2.1-or-later | https://py7zr.readthedocs.io/ |
| **fpdf2** | `>=2.7,<3.0` | LGPL-3.0-only | https://py-pdf.github.io/fpdf2/ |
| **libpff-python** *(optional, declared under `[project.optional-dependencies] pst`)* | unpinned | LGPL-3.0-or-later | https://github.com/libyal/libpff |

The LGPL is "weak" copyleft: it requires that LGPL-licensed code
remain available under the LGPL and that users be able to replace it
with their own version, but it generally permits proprietary code to
*use* the LGPL library through standard linking (which dynamic Python
imports qualify as in mainstream interpretation). Downstream
developers redistributing peekdocs in a proprietary product should:

- preserve the LGPL libraries' copyright notices and licenses,
- not modify the LGPL libraries' source without also distributing
  those modifications under the LGPL, and
- allow end users to substitute their own build of the LGPL library
  (which the standard `pip install` mechanism naturally supports).

These obligations are typically discharged simply by leaving the
LGPL libraries unmodified and shipping them as separately-installable
dependencies — which is how peekdocs uses them.

### Strong copyleft — GPL

| Library | Version constraint | License | Upstream |
|---|---|---|---|
| **extract-msg** | `>=0.40,<1.0` | GPL | https://github.com/TeamMsgExtractor/msg-extractor |

The GPL is "strong" copyleft: any derivative work, when distributed,
must also be GPL-licensed. The "derivative work" question for Python
imports is legally unsettled but the strict reading is that any code
that imports a GPL library is part of a GPL combined work upon
distribution. Downstream developers integrating peekdocs into work
that uses email-archive (`.msg`) reading should consider this. (If
your downstream work never invokes the `.msg`-reading code paths,
the practical exposure is smaller, but the dependency declaration
still carries the obligation.)

### Strong copyleft, network-trigger — AGPL v3 OR commercial

| Library | Version constraint | License | Upstream |
|---|---|---|---|
| **PyMuPDF** | `>=1.20,<2.0` | AGPL v3 OR commercial (Artifex) | https://github.com/pymupdf/PyMuPDF |
| **EbookLib** | `>=0.18,<1.0` | AGPL v3 | https://github.com/aerkalov/ebooklib |

PyMuPDF and EbookLib are the most license-significant dependencies in
peekdocs's tree. **PyMuPDF** (the PDF reader) is dual-licensed: AGPL
v3 for open-source use, or a commercial license from
[Artifex Software](https://artifex.com/licensing/) for proprietary
use. **EbookLib** (the EPUB reader) is AGPL v3 only, with no
documented commercial-license path from the maintainers.

The AGPL extends the GPL's strong copyleft with a network clause:
even running an AGPL-derived service over a network triggers source-
disclosure obligations to network users. peekdocs is a local desktop
tool with no network surface, so the network clause typically does
not apply — but the strong copyleft on distribution still does.

Downstream developers integrating peekdocs into a closed-source
product or a permissively-licensed derivative work have three
practical options:

1. **Accept that the combined work falls under AGPL terms** —
   distribute your derivative under AGPL v3 (or a compatible
   copyleft license), open-source the work.
2. **Acquire a commercial PyMuPDF license** from Artifex (for the
   PDF-reader piece) and **avoid the `.epub` reading code path
   entirely** (since EbookLib has no documented commercial-license
   alternative).
3. **Vendor or replace these libraries** with permissively-licensed
   alternatives if your use case allows.

Internal-only use within an organization (without distribution
to third parties) is generally not "conveyance" under AGPL/GPL
interpretation and does not trigger source-disclosure obligations.

## How license metadata was gathered

The license strings in this file were pulled from the live installed
packages via `pip show <package>` on a working virtual environment,
cross-checked against the upstream repositories and PyPI metadata
where the local `License` field was empty (odfpy, where the
authoritative source is the Trove classifiers, not the free-text
`License` field).

To regenerate or audit this file from a fresh install:

```bash
pip install -e .
pip install libpff-python  # the optional pst dependency
pip show python-docx PyMuPDF odfpy openpyxl striprtf python-pptx \
         EbookLib Pillow pytesseract rapidfuzz customtkinter \
         olefile xlrd extract-msg py7zr rarfile fpdf2 libpff-python \
  | grep -E "^Name|^Version|^License"
```

This list reflects direct dependencies only. Each direct dependency
brings its own transitive dependency tree with its own license
considerations. License-scan tools (FOSSA, Snyk Licenses, Black Duck,
GitHub's dependency graph) can produce a complete transitive
license report for any project that declares peekdocs as a
dependency.
