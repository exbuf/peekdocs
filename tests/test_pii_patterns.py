"""Tests for PII scan patterns — validates that each regex in sensitive_patterns.py
catches known-good examples and does not match known false positives."""

import re
import pytest
from peekdocs.sensitive_patterns import SENSITIVE_PATTERNS


def _find_pattern(category_name):
    """Return the compiled regex for a given category name."""
    for cat, pattern, severity, desc in SENSITIVE_PATTERNS:
        if cat == category_name:
            return re.compile(pattern)
    raise ValueError(f"Pattern not found: {category_name}")


# ── Social Security Numbers ──────────────────────────────────────


class TestSSN:
    pat = _find_pattern("Social Security Numbers")

    @pytest.mark.parametrize("text", [
        "123-45-6789",
        "SSN: 123-45-6789",
        "My SSN is 999-88-7777.",
        "ssn=078-05-1120 on file",
    ])
    def test_matches(self, text):
        assert self.pat.search(text)

    @pytest.mark.parametrize("text", [
        "123-45-67890",       # too many digits
        "12-345-6789",        # wrong grouping
        "1234-5-6789",        # wrong grouping
        "123456789",          # no dashes
        "phone 123-45-6789012",  # trailing digits
        "9123-45-6789",       # leading digit
        "DOI: 10.1007/978-981-15-1792-1_20",  # DOI with embedded XXX-XX-XXXX
        "ISBN 978-0-13-468599-1",  # ISBN with hyphenated digits
        "part-number-123-45-6789-rev2",  # embedded in hyphenated string
    ])
    def test_no_match(self, text):
        assert not self.pat.search(text)


# ── Credit Card Numbers ──────────────────────────────────────────


class TestCreditCard:
    pat = _find_pattern("Credit Card Numbers")

    @pytest.mark.parametrize("text", [
        "4111-1111-1111-1111",        # Visa test card
        "4111 1111 1111 1111",        # Visa with spaces
        "4111111111111111",           # Visa no separators
        "5500-0000-0000-0004",        # Mastercard test
        "3782-8224-6310-005",         # Amex test (4-4-4-3 grouping)
        "6011-0000-0000-0004",        # Discover test
        "Card: 4111-1111-1111-1111",  # with prefix text
    ])
    def test_matches(self, text):
        assert self.pat.search(text)

    @pytest.mark.parametrize("text", [
        "1234-5678-9012-3456",  # doesn't start with valid prefix
        "4111-1111-1111",       # too short
        "not a card number",
        "https://www.cnn.com/world/live-news/omicron-variant-coronavirus-news-12-23-21/h_f9aab70b4357549960098d6079771f9c",  # URL with digits
        "file_4357549960098d60.txt",  # filename with digits
        "/path/to/4111111111111111/resource",  # digits inside URL path
        "token=abc4111111111111111def",  # digits inside alphanumeric string
    ])
    def test_no_match(self, text):
        assert not self.pat.search(text)


# ── Tax ID / EIN ─────────────────────────────────────────────────


class TestTaxID:
    pat = _find_pattern("Tax ID / EIN")

    @pytest.mark.parametrize("text", [
        "12-3456789",
        "EIN: 98-7654321",
        "Tax ID 12-3456789 on form",
    ])
    def test_matches(self, text):
        assert self.pat.search(text)

    @pytest.mark.parametrize("text", [
        "123-456789",       # wrong grouping (SSN-like)
        "12-34567890",      # too many digits
        "12-345678",        # too few digits
        "1234567890",       # no dash
    ])
    def test_no_match(self, text):
        assert not self.pat.search(text)


# ── Email Addresses ──────────────────────────────────────────────


class TestEmail:
    pat = _find_pattern("Email Addresses")

    @pytest.mark.parametrize("text", [
        "user@example.com",
        "first.last@company.org",
        "test+tag@sub.domain.co.uk",
        "Contact: admin@example.com for info",
    ])
    def test_matches(self, text):
        assert self.pat.search(text)

    @pytest.mark.parametrize("text", [
        "@example.com",         # no local part
        "user@",                # no domain
        "user@.com",            # domain starts with dot
        "plaintext",            # no @ at all
    ])
    def test_no_match(self, text):
        assert not self.pat.search(text)


# ── Phone Numbers ────────────────────────────────────────────────


class TestPhoneNumbers:
    pat = _find_pattern("Phone Numbers")

    @pytest.mark.parametrize("text", [
        "(555) 123-4567",
        "555-123-4567",
        "555.123.4567",
        "Call 555-123-4567 today",
        "(800) 555-1212",
    ])
    def test_matches(self, text):
        assert self.pat.search(text)

    @pytest.mark.parametrize("text", [
        "555-1234",             # only 7 digits
        "12345678901234",       # too many digits
        "not a phone number",
    ])
    def test_no_match(self, text):
        assert not self.pat.search(text)


# ── Passwords / Secrets ──────────────────────────────────────────


class TestPasswords:
    pat = _find_pattern("Passwords / Secrets")

    @pytest.mark.parametrize("text", [
        "password: secret123",
        "PASSWORD=hunter2",
        "pwd: myp@ss!",
        "api_key: sk-abc123def456",
        "API-KEY=abcdef",
        "api_token: eyJhbGciOi",
        "auth-token=abc123xyz",
        "access_token: sk-123456",
        "secret = very_secret_value",
    ])
    def test_matches(self, text):
        assert self.pat.search(text)

    @pytest.mark.parametrize("text", [
        "enter your password",       # no assignment
        "forgot my password again",  # no assignment
        "the secret garden",         # no assignment
        "api key documentation",     # no assignment operator
        "?token=eyJ0eXAiOiJKV1QiLCJhbGciOi",  # URL query parameter
        "&token=abc123&other=value",  # URL query parameter with &
        "https://example.com/path?token=xyz",  # full URL with token param
        "token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",  # bare JWT token assignment
        "cookie_token=abc123",  # prefixed token (not api/auth/access)
    ])
    def test_no_match(self, text):
        assert not self.pat.search(text)


# ── Dates of Birth ───────────────────────────────────────────────


class TestDOB:
    pat = _find_pattern("Dates of Birth")

    @pytest.mark.parametrize("text", [
        "DOB: 01/15/1990",
        "dob=12-25-1985",
        "Date of Birth: 3/4/92",
        "born: 07-22-1955",
        "Born 11/30/2001",
    ])
    def test_matches(self, text):
        assert self.pat.search(text)

    @pytest.mark.parametrize("text", [
        "01/15/1990",           # date without DOB context
        "the date was 01/15",   # no DOB keyword
        "birthday party",       # no date
    ])
    def test_no_match(self, text):
        assert not self.pat.search(text)


# ── Dollar Amounts ───────────────────────────────────────────────


class TestDollarAmounts:
    pat = _find_pattern("Dollar Amounts")

    @pytest.mark.parametrize("text", [
        "$100",
        "$1,000.00",
        "$10,000,000.00",
        "$0.99",
        "Price: $250.00",
        "Total $1,234,567.89 due",
    ])
    def test_matches(self, text):
        assert self.pat.search(text)

    @pytest.mark.parametrize("text", [
        "100 dollars",      # no $ sign
        "€500",             # wrong currency
        "£200.00",          # wrong currency
    ])
    def test_no_match(self, text):
        assert not self.pat.search(text)


# ── Pattern metadata ─────────────────────────────────────────────


def test_all_patterns_compile():
    """Every pattern in SENSITIVE_PATTERNS should compile without error."""
    for cat, pattern, severity, desc in SENSITIVE_PATTERNS:
        re.compile(pattern)


def test_all_severities_valid():
    """Every severity should be one of the expected values."""
    valid = {"high", "moderate", "info"}
    for cat, pattern, severity, desc in SENSITIVE_PATTERNS:
        assert severity in valid, f"{cat} has invalid severity: {severity}"


def test_no_duplicate_categories():
    """No two patterns should share the same category name."""
    cats = [cat for cat, _, _, _ in SENSITIVE_PATTERNS]
    assert len(cats) == len(set(cats)), f"Duplicate categories: {cats}"
