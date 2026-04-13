"""Tests for the Search Wizard patterns and regex builder."""

import re
import pytest
from peekdocs.wizard_patterns import WIZARD_PATTERNS, WIZARD_CATEGORY_ORDER
from peekdocs.gui import _build_wizard_regex


# ── Pattern data structure tests ─────────────────────────────

def test_category_order_matches_patterns():
    """WIZARD_CATEGORY_ORDER lists exactly the keys in WIZARD_PATTERNS."""
    assert set(WIZARD_CATEGORY_ORDER) == set(WIZARD_PATTERNS.keys())
    assert len(WIZARD_CATEGORY_ORDER) == len(WIZARD_PATTERNS)


def test_all_entries_are_label_regex_tuples():
    """Every entry in every category is a (str, str) tuple."""
    for category, patterns in WIZARD_PATTERNS.items():
        assert len(patterns) > 0, f"Category '{category}' is empty"
        for entry in patterns:
            assert isinstance(entry, tuple), f"Entry {entry} in '{category}' is not a tuple"
            assert len(entry) == 2, f"Entry {entry} in '{category}' does not have 2 elements"
            label, regex = entry
            assert isinstance(label, str) and label, f"Bad label in '{category}': {label}"
            assert isinstance(regex, str) and regex, f"Bad regex in '{category}': {regex}"


def test_all_patterns_compile():
    """Every regex pattern compiles without error."""
    for category, patterns in WIZARD_PATTERNS.items():
        for label, regex in patterns:
            try:
                re.compile(regex)
            except re.error as e:
                pytest.fail(f"Regex for '{label}' in '{category}' failed to compile: {e}")


def test_eight_categories():
    """There should be exactly 8 categories."""
    assert len(WIZARD_CATEGORY_ORDER) == 8


# ── _build_wizard_regex tests ───────────────────────────────

def test_build_wizard_regex_empty():
    assert _build_wizard_regex([]) == ""


def test_build_wizard_regex_single():
    result = _build_wizard_regex([("Date", r"\d{1,2}/\d{1,2}/\d{2,4}")])
    assert result == r"(\d{1,2}/\d{1,2}/\d{2,4})"


def test_build_wizard_regex_multiple():
    patterns = [
        ("Date", r"\d{1,2}/\d{1,2}/\d{2,4}"),
        ("Dollar", r"\$[\d,]+\.?\d*"),
    ]
    result = _build_wizard_regex(patterns)
    assert result == r"(\d{1,2}/\d{1,2}/\d{2,4})|(\$[\d,]+\.?\d*)"


def test_build_wizard_regex_compiles():
    """The combined regex should compile and match expected strings."""
    patterns = [
        ("Date", r"\d{1,2}/\d{1,2}/\d{2,4}"),
        ("Dollar", r"\$[\d,]+\.?\d*"),
    ]
    combined = _build_wizard_regex(patterns)
    compiled = re.compile(combined)
    assert compiled.search("Invoice date: 12/25/2024")
    assert compiled.search("Total: $1,234.56")
    assert not compiled.search("no patterns here")


# ── Representative pattern match tests ──────────────────────

@pytest.mark.parametrize("category,label,test_string", [
    ("Common / General", "Date (MM/DD/YYYY)", "Filed on 03/15/2024"),
    ("Common / General", "Date (YYYY-MM-DD)", "Date: 2024-03-15"),
    ("Common / General", "Dollar Amount", "Total: $1,234.56"),
    ("Common / General", "Percentage", "Growth of 15.5%"),
    ("Common / General", "Phone Number", "Call (555) 123-4567"),
    ("Common / General", "Email Address", "contact@example.com"),
    ("Common / General", "6-digit Number", "ID: 123456"),
    ("Common / General", "SSN (XXX-XX-XXXX)", "SSN: 123-45-6789"),
    ("Business / Finance", "Invoice Number", "INV-12345"),
    ("Business / Finance", "Purchase Order", "PO 98765"),
    ("Business / Finance", "Tax ID / EIN", "EIN: 12-3456789"),
    ("Legal", "Case Number", "Case 23-CV-12345"),
    ("Legal", "Bates Number", "ABC123456"),
    ("Medical / Healthcare", "ICD-10 Code", "Diagnosis: J18.9"),
    ("Medical / Healthcare", "NPI Number", "NPI: 1234567890"),
    ("Engineering / Technical", "Part Number", "ABC-12345"),
    ("Engineering / Technical", "Measurement", "Diameter: 25.4 mm"),
    ("Engineering / Technical", "Serial Number", "S/N: ABC-1234"),
    ("Real Estate", "Square Footage", "2,500 sq ft"),
    ("Real Estate", "Lot/Block", "Lot 15"),
    ("HR / Admin", "Employee ID", "Emp #12345"),
    ("Compliance / Audit", "Policy / Document Number", "See POL-2024 for details"),
    ("Compliance / Audit", "Classification Marking", "This document is CONFIDENTIAL"),
    ("Compliance / Audit", "Effective / Expiration Date", "Effective: 01/15/2025"),
    ("Compliance / Audit", "Retention Code", "Assigned RET-001"),
    ("Compliance / Audit", "Account Number", "Acct #98765"),
])
def test_pattern_matches_expected(category, label, test_string):
    """Verify representative patterns match their expected strings."""
    patterns = dict(WIZARD_PATTERNS[category])
    regex = patterns[label]
    assert re.search(regex, test_string), f"'{regex}' did not match '{test_string}'"
