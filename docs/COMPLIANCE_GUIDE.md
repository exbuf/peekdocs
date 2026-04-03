# docsearch Compliance and Auditing Guide

This guide explains how to use docsearch as a compliance and auditing tool. For general usage, see the [User Guide](USER_GUIDE.md) or [README](../README.md).

## Table of Contents

- [Why audits exist](#why-audits-exist)
- [Who performs audits](#who-performs-audits)
- [Industry examples](#industry-examples)
- [How docsearch fits](#how-docsearch-fits)
- [Sample compliance suites by industry](#sample-compliance-suites-by-industry)
  - [Financial Services Compliance](#financial-services-compliance)
  - [Healthcare Compliance](#healthcare-compliance)
  - [Legal Document Review](#legal-document-review)
  - [Government Records Compliance](#government-records-compliance)
  - [Manufacturing Quality Compliance](#manufacturing-quality-compliance)
  - [Education FERPA Compliance](#education-ferpa-compliance)
  - [Real Estate Closing Compliance](#real-estate-closing-compliance)
  - [Insurance Compliance Audit](#insurance-compliance-audit)
  - [HR Compliance Review](#hr-compliance-review)

## Why audits exist

An audit is a systematic review of documents, records, or processes to verify that they meet a set of requirements — legal, regulatory, contractual, or internal. Organizations perform audits because the consequences of non-compliance can be severe: fines, lawsuits, lost licenses, data breaches, or failed certifications. Audits answer a simple question: *are we doing what we said we would do, and can we prove it?*

Most audits are not triggered by suspicion of wrongdoing. They are routine, scheduled activities — the organizational equivalent of a regular checkup. The goal is to catch problems early, before they become expensive.

## Who performs audits

- **Internal auditors** — employees (or a dedicated department) who review their own organization's processes. They report to management or an audit committee and focus on risk, controls, and operational efficiency. Many organizations have a Chief Audit Executive or an internal audit team.
- **External auditors** — independent firms (e.g., accounting firms, consulting firms, or government inspectors) hired to provide an objective assessment. Financial statement audits, SOX compliance audits, and regulatory inspections are typically performed by external auditors.
- **Compliance officers** — staff responsible for ensuring the organization follows applicable laws and regulations. They often design the compliance program and monitor adherence on an ongoing basis.
- **IT and security teams** — review systems, access controls, and data handling practices. They perform audits related to data privacy (GDPR, HIPAA), cybersecurity frameworks (SOC 2, ISO 27001), and internal security policies.
- **Contract managers and legal teams** — review agreements to verify that required clauses are present, terms are current, and obligations are being met.
- **Quality assurance teams** — verify that processes and outputs meet defined standards (ISO 9001, FDA regulations, industry-specific requirements).

In smaller organizations, audits are often performed by a single person wearing multiple hats — a controller who also handles compliance, or an office manager responsible for records management.

## Industry examples

| Industry | What gets audited | Why | Typical requirements |
|----------|------------------|-----|---------------------|
| **Financial services** | Loan documents, account records, transaction logs | Banking regulations (SOX, Dodd-Frank, BSA/AML) require documented controls and regular review | Every loan file must contain signed disclosures; no account should have unauthorized transactions above reporting thresholds |
| **Healthcare** | Patient records, billing documents, policy manuals | HIPAA requires protection of patient data; CMS requires accurate billing documentation | No patient SSN or medical record number in unsecured documents; every billing record must reference a valid diagnosis code |
| **Legal** | Contracts, court filings, discovery documents | Bar associations, courts, and clients require accurate document handling and retention | Every contract must contain an indemnification clause and an effective date; no privileged documents in production sets |
| **Government** | Policy documents, procurement records, correspondence | Freedom of Information laws, records retention schedules, and inspector general reviews | Every procurement file must contain a signed authorization; no classified markings in unclassified folders |
| **Manufacturing** | Quality records, inspection reports, certifications | ISO 9001, FDA, and industry standards require documented quality processes | Every batch record must reference an approved specification; no expired certifications in the active file |
| **Education** | Student records, accreditation documents, grant files | FERPA protects student data; accreditation bodies require documented compliance | No student SSN in publicly accessible files; every grant file must contain a signed agreement |
| **Real estate** | Lease agreements, inspection reports, closing documents | State licensing boards and lenders require complete documentation | Every closing file must contain a signed disclosure; all lease amounts must fall within approved ranges |
| **Insurance** | Policy documents, claims files, underwriting records | State insurance regulators require documented underwriting and claims processes | Every policy must contain required state-mandated language; no lapsed policies in the active portfolio |
| **Human resources** | Employee files, benefit documents, I-9 forms | Employment law (EEOC, FLSA, ACA) and immigration law (USCIS) require documented compliance | Every employee file must contain a signed offer letter and I-9; no SSNs in shared drive folders |

In each of these industries, the core task is the same: search a set of documents, verify that specific content is present (or absent), and produce a report proving the results. This is exactly what docsearch does.

## How docsearch fits

docsearch can serve as a lightweight compliance and auditing tool. Instead of manually opening documents one at a time to verify that required language is present, prohibited content is absent, or values fall within acceptable ranges, you can automate those checks and produce evidence-grade reports — all offline, without uploading anything to the cloud.

**What compliance and audit teams typically need to verify:**

- Every contract contains a required clause (e.g., indemnification, signature, effective date)
- No document contains prohibited content (e.g., "DRAFT" watermarks, outdated policy references)
- Sensitive data like Social Security numbers or account numbers does not appear where it shouldn't
- Dollar amounts, dates, or percentages fall within acceptable ranges
- A consistent set of checks runs on a regular schedule with documented results

docsearch handles all of these with features already built in. Here's how to set it up, step by step.

**Step 1: Identify your checks.** Write down what you need to verify. For example, a quarterly contract review might include:

| Check | What to look for | Expected result |
|-------|-----------------|-----------------|
| Signature present | "Authorized Signature" in every file | Every file has it |
| Date present | A date pattern (MM/DD/YYYY) in every file | Every file has it |
| No DRAFT stamps | The word "DRAFT" in any file | No file has it |
| Amounts in range | Dollar amounts between $1,000 and $50,000 | At least one match |
| No SSNs | SSN pattern (XXX-XX-XXXX) in any file | No file has it |

**Step 2: Create saved searches in the GUI.** Open the GUI by running `docsearch-gui` in your terminal. "Point it at a folder" means clicking the **Browse** button next to the **Search Folder** field at the top of the window and navigating to the folder containing your documents. Once selected, all searches will run against that folder. Now configure each check as a separate search:

- **"has_signature"** — Enter `Authorized\s+Signature` in the search box, check **Regex** and **Inverse**. Inverse mode lists files that do *not* contain the term — if the result is zero files, every document has it.
- **"has_date"** — Enter `\d{2}/\d{2}/\d{4}` in the search box, check **Regex** and **Inverse**. Same logic: zero files missing a date means all files have one.
- **"no_draft"** — Enter `DRAFT` in the search box. A normal (non-inverse) search that should return zero matches.
- **"amount_in_range"** — Enter `amount:1000..50000` in the Range field. Should return at least one match.
- **"no_ssn"** — Enter `\d{3}-\d{2}-\d{4}` in the search box, check **Regex**. Should return zero matches.

After configuring each search, click **Save Search** in the Search Bar and give it a name. The search and all its settings are saved to the folder's collection file.

**Step 3: Build a suite.** Click **Manage Suites** to open the suites panel (or use the **Compliance Wizard** to skip this step entirely — it creates the searches and suite for you). Click **Build a New Suite**, name it (e.g., "quarterly_contract_review"), and add your saved searches in order. For each search, set the **pass criteria**:

| Search | Criteria | Meaning |
|--------|----------|---------|
| has_signature (inverse) | `== 0` | Pass if zero files are missing a signature |
| has_date (inverse) | `== 0` | Pass if zero files are missing a date |
| no_draft | `== 0` | Pass if zero files contain "DRAFT" |
| amount_in_range | `>= 1` | Pass if at least one amount is in range |
| no_ssn | `== 0` | Pass if zero SSNs are found |

Click **Create**.

**Step 4: Run the suite.** Select your suite and click **Run Selected Suite**. docsearch runs each check in order and evaluates pass/fail against your criteria. When it finishes, three report files are generated automatically:

- **`.docx`** — A formatted Word document with a color-coded summary table (green PASS / red FAIL), per-stage details, a report fingerprint for tamper detection, and a source file manifest listing every document that was in scope. This is the report you hand to a reviewer or attach to an audit workpaper.
- **`.txt`** — A plain text version of the same report.
- **`.json`** — A machine-readable version for integration with other tools or scripts.

Click **View Suite Report** to open the `.docx` report directly.

**Step 5: Schedule recurring runs (optional).** If this is a check you need to run regularly, use the **Auto-Run every** dropdown in the suites panel to schedule it (e.g., every 24 hours). docsearch will run the suite automatically at the set interval, generate timestamped reports, and log each run to `DO_NOT_SEARCH_autorun_log.txt`. You don't need to keep the suites window open — auto-runs execute in the background.

**Step 6: Review failures.** When a check fails, the suite report tells you exactly which check failed and how many matches (or missing files) were found. Click the individual stage report (listed in the suite report) to see the specific matches — each one shows the filename, line number, and matched text with yellow highlighting. Fix the issue in the source document and re-run the suite to confirm.

**Why docsearch works well for this:**

- **Offline and read-only** — Your documents never leave your computer. docsearch does not modify, move, or delete any files. This matters for sensitive documents like financial records, legal contracts, medical files, and personnel records.
- **Portable reports** — The `.docx` report is a standard Word document that anyone can open. No special software, no login, no subscription required to review the results.
- **Repeatable** — The same suite with the same criteria produces consistent results. Save the suite once, run it whenever you need to.
- **Auditable** — Each report includes a timestamp, the docsearch version, a report fingerprint (proving the reports haven't been tampered with), and a source file manifest (listing every document that was in scope).
- **Free** — No per-seat licenses, no annual subscriptions, no per-GB processing fees. Commercial compliance tools that offer similar functionality cost $249 to $150,000+ per year.

## Sample compliance suites by industry

docsearch includes a set of 90 sample documents across 9 industries, each with pre-built compliance suites ready to run. These serve as both a demonstration of docsearch's compliance capabilities and a starting point you can adapt for your own use. The sample documents are located in subfolders under a `googledocs/` folder, with each industry in its own subfolder. Each subfolder contains 10 realistic documents — a mix of compliant and non-compliant files — along with a `.docsearch_collection.json` file containing 8 saved searches and 1 compliance suite.

**Compliance Wizard — the fastest way to get started:**

The **Compliance Wizard** (on the main screen, next to the Search Wizard) creates a complete compliance suite for your industry in one click. Instead of manually building individual searches and assembling them into a suite:

1. Click **Compliance Wizard**
2. Choose your industry from the dropdown (e.g., Healthcare/HIPAA)
3. Review and customize the 8 pre-built checks if needed
4. Click **Create Suite**

The wizard creates all the saved searches and the suite automatically. The created suite appears in the **Manage Suites** panel alongside any suites you built manually — there is no difference in how they work. You can run it immediately, schedule it, or edit individual searches later.

Available templates: Financial Services (SOX/BSA/AML), Healthcare (HIPAA), Legal Document Review, Government Records, Manufacturing (ISO 9001), Education (FERPA), Real Estate Closing, Insurance Compliance, and HR Compliance.

**Where the suites are stored:** The saved searches and suites for each industry — whether created manually, by the Search Wizard, or by the Compliance Wizard — are stored in a `.docsearch_collection.json` file inside that industry's folder. This is docsearch's standard approach — the collection file lives alongside the documents it searches. This is best practice for several reasons: the suites travel with the documents (if you copy or move the folder, the suites come with it), each folder has suites tailored to its specific content, and there is no central configuration file to manage or accidentally break. When you point the GUI at a folder, it automatically loads that folder's collection. You can view, edit, or add to the suites from the GUI at any time.

**Why JSON?** The collection file uses JSON (JavaScript Object Notation), which is a standard format for storing structured data. JSON is the right choice here because it is human-readable (you can open it in any text editor and understand what's in it), universally supported (every programming language has built-in JSON support — Python's `json` module is part of the standard library with no extra dependencies), and naturally handles nested data (suites containing ordered search lists, each with its own parameters and pass criteria). JSON is also plain text, so it works on every operating system, diffs cleanly in version control, and has syntax highlighting in every code editor. Other formats have drawbacks for this use case: SQLite is overkill for a small config file, YAML adds an external dependency and has well-known gotchas (like silently converting `no` to `False` or `3.10` to `3.1`), TOML is awkward for deeply nested structures, and binary formats like Pickle are not human-readable and pose security risks. You never need to edit the JSON file directly — the GUI manages it for you — but if you want to inspect or modify it manually, it's straightforward to do so.

**How to run any industry suite:**

1. Open `docsearch-gui`
2. In the **Search Folder** field, browse to the industry subfolder (e.g., `googledocs/financial_services`)
3. Click **Manage Suites** (below Advanced Search Options) to open the suites panel — or click **Run Suite** on the main screen
4. Select the suite from the **Suites** list
5. Click **Run Selected Suite**
6. Watch the results — each check shows PASS (green) or FAIL (red) in real time
7. When the suite finishes, the suite report appears in the main preview pane. Click **View Suite Report** in the suites panel to open the `.docx` report

Each suite is designed so that some checks will fail — this is intentional. The non-compliant documents demonstrate what failures look like in practice and how the stage reports pinpoint the exact files and lines that caused the failure.

---

### Financial Services Compliance

**Folder:** `googledocs/financial_services` (10 documents — loan applications, disclosures, audit reports, wire transfer logs, SAR filings)

| # | Search Name | Search Configuration | Criteria | What it checks |
|---|-------------|---------------------|----------|---------------|
| 1 | has_signature | Terms: `Authorized Signature` — Inverse: ON | `== 0` | Every file has an authorized signature |
| 2 | no_ssn | Regex: `\d{3}-\d{2}-\d{4}` | `== 0` | No Social Security numbers in any document |
| 3 | no_draft | Terms: `DRAFT` | `== 0` | No draft documents in the folder |
| 4 | has_date | Regex: `\d{2}/\d{2}/\d{4}` — Inverse: ON | `== 0` | Every file contains a date |
| 5 | sox_reference | Terms: `SOX` | `>= 1` | At least one document references SOX compliance |
| 6 | bsa_aml_reference | Expression: `BSA OR AML` | `>= 1` | Anti-money laundering documentation exists |
| 7 | large_transactions | Terms: `transaction` — Range: `amount:10000..50000` | `>= 1` | Transactions in reportable range are documented |
| 8 | account_numbers | Regex: `ACCT-\d+` | `>= 1` | Account numbers are traceable |

**Expected failures:** `no_ssn` (2 files contain SSNs), `no_draft` (1 DRAFT memo), `has_signature` (1 file missing signature)

---

### Healthcare Compliance

**Folder:** `googledocs/healthcare` (10 documents — patient intake forms, HIPAA notices, billing summaries, clinical trial consent, discharge summaries)

| # | Search Name | Search Configuration | Criteria | What it checks |
|---|-------------|---------------------|----------|---------------|
| 1 | has_signature | Terms: `Authorized Signature` — Inverse: ON | `== 0` | Every file has an authorized signature |
| 2 | no_ssn | Regex: `\d{3}-\d{2}-\d{4}` | `== 0` | No SSNs exposed in documents (HIPAA) |
| 3 | no_draft | Terms: `DRAFT` | `== 0` | No unapproved drafts in the folder |
| 4 | hipaa_reference | Terms: `HIPAA` | `>= 1` | HIPAA compliance is documented |
| 5 | diagnosis_codes | Regex: `[A-Z]\d{2}\.\d` | `>= 1` | ICD-10 diagnosis codes are present in clinical docs |
| 6 | billing_amounts | Terms: `billing` — Range: `amount:100..50000` | `>= 1` | Billing amounts are documented |
| 7 | mrn_in_transfer | Expression: `MRN AND transfer` | `>= 1` | Medical record numbers accompany transfer requests |
| 8 | patient_consent | Terms: `consent` | `>= 1` | Consent documentation exists |

**Expected failures:** `no_ssn` (1 file contains a patient SSN), `no_draft` (1 DRAFT training document), `has_signature` (1 file missing signature)

---

### Legal Document Review

**Folder:** `googledocs/legal` (10 documents — service agreements, settlements, NDAs, employment contracts, court filings, lease agreements)

| # | Search Name | Search Configuration | Criteria | What it checks |
|---|-------------|---------------------|----------|---------------|
| 1 | has_signature | Terms: `Authorized Signature` — Inverse: ON | `== 0` | Every file has an authorized signature |
| 2 | has_indemnification | Terms: `indemnif` — Inverse: ON | `== 0` | Every agreement has an indemnification clause |
| 3 | has_effective_date | Terms: `Effective Date` — Inverse: ON | `== 0` | Every agreement has an effective date |
| 4 | no_draft | Terms: `DRAFT` | `== 0` | No draft documents in the active folder |
| 5 | no_privileged | Terms: `PRIVILEGED` | `== 0` | No privileged documents in a production set |
| 6 | settlement_amounts | Terms: `settlement` — Range: `amount:1000..1000000` | `>= 1` | Settlement amounts are documented |
| 7 | case_numbers | Regex: `\d{4}-CV-\d+` | `>= 1` | Case numbers are present and traceable |
| 8 | nda_exists | Expression: `non-disclosure OR nondisclosure OR NDA` | `>= 1` | Non-disclosure agreements are on file |

**Expected failures:** `has_indemnification` (1 employment contract missing the clause), `has_effective_date` (1 vendor agreement missing the date), `no_draft` (1 DRAFT amendment), `no_privileged` (1 privileged litigation hold)

---

### Government Records Compliance

**Folder:** `googledocs/government` (10 documents — procurement authorizations, budget allocations, FOIA responses, inspector general reports, grant agreements)

| # | Search Name | Search Configuration | Criteria | What it checks |
|---|-------------|---------------------|----------|---------------|
| 1 | has_signature | Terms: `Authorized Signature` — Inverse: ON | `== 0` | Every file has an authorized signature |
| 2 | no_draft | Terms: `DRAFT` | `== 0` | No draft documents in the official folder |
| 3 | no_classified | Expression: `CONFIDENTIAL OR CLASSIFIED OR SECRET` | `== 0` | No classified markings in an unclassified folder |
| 4 | has_date | Regex: `\d{2}/\d{2}/\d{4}` — Inverse: ON | `== 0` | Every document contains a date |
| 5 | procurement_authorized | Expression: `procurement AND authorized` | `>= 1` | Procurement actions have authorization |
| 6 | budget_amounts | Terms: `budget` — Range: `amount:10000..50000000` | `>= 1` | Budget allocations are documented |
| 7 | purchase_orders | Regex: `PO-\d{4}` | `>= 1` | Purchase orders are traceable |
| 8 | foia_compliance | Terms: `FOIA` | `>= 1` | FOIA documentation exists |

**Expected failures:** `has_signature` (1 procurement missing signature), `no_draft` (1 DRAFT policy memo), `no_classified` (1 file with CONFIDENTIAL marking)

---

### Manufacturing Quality Compliance

**Folder:** `googledocs/manufacturing` (10 documents — batch records, inspection reports, calibration certificates, nonconformance reports, ISO management reviews)

| # | Search Name | Search Configuration | Criteria | What it checks |
|---|-------------|---------------------|----------|---------------|
| 1 | has_signature | Terms: `Authorized Signature` — Inverse: ON | `== 0` | Every file has a quality sign-off |
| 2 | no_draft | Terms: `DRAFT` | `== 0` | No unapproved drafts in the production folder |
| 3 | no_expired_certs | Terms: `expired` | `== 0` | No expired certifications in active files |
| 4 | iso_reference | Terms: `ISO 9001` | `>= 1` | ISO 9001 compliance is documented |
| 5 | lot_numbers | Regex: `LOT-\d{4}-\d+` | `>= 1` | Lot/batch numbers are traceable |
| 6 | part_numbers | Regex: `[A-Z]{3}-\d{4}` | `>= 1` | Part numbers are documented |
| 7 | nonconformance_closed | Expression: `nonconformance AND corrective` | `>= 1` | Nonconformances have corrective actions |
| 8 | calibration_current | Terms: `calibration` | `>= 1` | Calibration records exist |

**Expected failures:** `has_signature` (1 batch record missing QC signature), `no_draft` (1 DRAFT engineering change order), `no_expired_certs` (1 expired ISO certification)

---

### Education FERPA Compliance

**Folder:** `googledocs/education` (10 documents — grant agreements, financial aid reports, FERPA policies, accreditation studies, class rosters, scholarship letters)

| # | Search Name | Search Configuration | Criteria | What it checks |
|---|-------------|---------------------|----------|---------------|
| 1 | has_signature | Terms: `Authorized Signature` — Inverse: ON | `== 0` | Every file has an authorized signature |
| 2 | no_ssn | Regex: `\d{3}-\d{2}-\d{4}` | `== 0` | No student SSNs exposed (FERPA violation) |
| 3 | no_draft | Terms: `DRAFT` | `== 0` | No draft documents in the official folder |
| 4 | ferpa_reference | Terms: `FERPA` | `>= 1` | FERPA compliance is documented |
| 5 | grant_amounts | Terms: `grant` — Range: `amount:1000..10000000` | `>= 1` | Grant amounts are documented |
| 6 | accreditation_docs | Terms: `accreditation` | `>= 1` | Accreditation documentation exists |
| 7 | student_ids | Terms: `Student ID` | `>= 1` | Student IDs (not SSNs) are used for identification |
| 8 | financial_aid | Expression: `financial aid OR scholarship` | `>= 1` | Financial aid records exist |

**Expected failures:** `no_ssn` (1 class roster contains student SSNs), `no_draft` (1 DRAFT curriculum proposal), `has_signature` (1 grant agreement missing signature)

---

### Real Estate Closing Compliance

**Folder:** `googledocs/real_estate` (10 documents — closing disclosures, lease agreements, inspection reports, title searches, appraisals, purchase agreements)

| # | Search Name | Search Configuration | Criteria | What it checks |
|---|-------------|---------------------|----------|---------------|
| 1 | has_signature | Terms: `Authorized Signature` — Inverse: ON | `== 0` | Every file has a signature |
| 2 | no_draft | Terms: `DRAFT` | `== 0` | No draft documents in the closing folder |
| 3 | has_date | Regex: `\d{2}/\d{2}/\d{4}` — Inverse: ON | `== 0` | Every document contains a date |
| 4 | disclosure_present | Terms: `disclosure` | `>= 1` | Required disclosures are on file |
| 5 | property_values | Terms: `property` — Range: `amount:100000..1000000` | `>= 1` | Property values are documented |
| 6 | square_footage | Regex: `\d[\d,]+ sq ft` | `>= 1` | Square footage is documented |
| 7 | title_search | Terms: `title` | `>= 1` | Title search documentation exists |
| 8 | inspection_report | Terms: `inspection` | `>= 1` | Property inspection is on file |

**Expected failures:** `has_signature` (1 closing disclosure missing buyer signature), `no_draft` (1 DRAFT HOA disclosure)

---

### Insurance Compliance Audit

**Folder:** `googledocs/insurance` (10 documents — homeowners/auto policies, claim reports, underwriting reviews, renewal notices, agent agreements)

| # | Search Name | Search Configuration | Criteria | What it checks |
|---|-------------|---------------------|----------|---------------|
| 1 | has_signature | Terms: `Authorized Signature` — Inverse: ON | `== 0` | Every file has an authorized signature |
| 2 | no_draft | Terms: `DRAFT` | `== 0` | No draft documents in the active folder |
| 3 | no_lapsed_policies | Expression: `lapsed OR expired` | `== 0` | No lapsed policies in the active folder |
| 4 | state_mandated_language | Terms: `state-mandated` | `>= 1` | Required state-mandated language is present |
| 5 | premium_amounts | Terms: `premium` — Range: `amount:100..10000` | `>= 1` | Premium amounts are documented |
| 6 | policy_numbers | Regex: `POL-\d{4}-\d+` | `>= 1` | Policy numbers are traceable |
| 7 | claim_numbers | Regex: `CLM-\d{4}-\d+` | `>= 1` | Claims have reference numbers |
| 8 | underwriting_review | Terms: `underwriting` | `>= 1` | Underwriting documentation exists |

**Expected failures:** `has_signature` (1 claim report missing signature), `no_draft` (1 DRAFT agent agreement), `no_lapsed_policies` (1 lapsed auto policy still in active folder)

---

### HR Compliance Review

**Folder:** `googledocs/human_resources` (10 documents — offer letters, I-9 logs, benefits summaries, performance reviews, termination checklists, payroll memos)

| # | Search Name | Search Configuration | Criteria | What it checks |
|---|-------------|---------------------|----------|---------------|
| 1 | has_signature | Terms: `Authorized Signature` — Inverse: ON | `== 0` | Every file has an authorized signature |
| 2 | no_ssn | Regex: `\d{3}-\d{2}-\d{4}` | `== 0` | No SSNs on shared drives |
| 3 | no_draft | Terms: `DRAFT` | `== 0` | No draft documents in the official folder |
| 4 | offer_letters | Terms: `offer` | `>= 1` | Offer letter documentation exists |
| 5 | i9_verification | Terms: `I-9` | `>= 1` | I-9 employment verification records exist |
| 6 | salary_amounts | Terms: `salary` — Range: `amount:50000..200000` | `>= 1` | Salary/compensation is documented |
| 7 | eeoc_compliance | Expression: `EEOC OR EEO-1` | `>= 1` | Equal employment documentation exists |
| 8 | flsa_reference | Terms: `FLSA` | `>= 1` | Fair Labor Standards Act compliance is documented |

**Expected failures:** `no_ssn` (1 employee list with SSNs on shared drive), `no_draft` (1 DRAFT handbook update), `has_signature` (1 offer letter missing signature)

---

**Summary of expected results across all 9 suites:**

Every suite is designed to produce a mix of passes and failures. The failures demonstrate how docsearch identifies specific compliance gaps:

| Suite | Total checks | Expected PASS | Expected FAIL | Key failures |
|-------|-------------|---------------|---------------|-------------|
| Financial Services Compliance | 8 | 5 | 3 | SSNs in loan files, DRAFT memo, unsigned application |
| Healthcare Compliance | 8 | 5 | 3 | Patient SSN exposed, DRAFT training doc, unsigned intake |
| Legal Document Review | 8 | 4 | 4 | Missing indemnification, missing date, DRAFT, privileged doc |
| Government Records Compliance | 8 | 5 | 3 | Unsigned procurement, DRAFT memo, classified marking |
| Manufacturing Quality Compliance | 8 | 5 | 3 | Unsigned batch record, DRAFT ECO, expired certification |
| Education FERPA Compliance | 8 | 5 | 3 | Student SSNs in roster, DRAFT proposal, unsigned grant |
| Real Estate Closing Compliance | 8 | 6 | 2 | Missing buyer signature, DRAFT HOA disclosure |
| Insurance Compliance Audit | 8 | 5 | 3 | Unsigned claim, DRAFT agreement, lapsed policy |
| HR Compliance Review | 8 | 5 | 3 | SSNs on shared drive, DRAFT handbook, unsigned offer |

When a check fails, open the stage report (listed in the suite report) to see exactly which files and lines caused the failure. This is the workflow an auditor would follow: run the suite, review the summary, drill into failures, fix the underlying issues, and re-run to confirm.
