"""Tests for docsearch command and regex translation."""

import pytest
from docsearch.translator import (
    translate_command, _translate_regex, _translate_wildcard, _identify_pattern,
)


# ── Regex translation tests ──────────────────────────────────

class TestTranslateRegex:
    def test_phone_number(self):
        result = _translate_regex(r"\d{3}-\d{3}-\d{4}")
        assert "phone number" in result
        assert "555-123-4567" in result

    def test_simple_digits(self):
        result = _translate_regex(r"\d+")
        assert "one or more" in result
        assert "digit" in result

    def test_email_pattern(self):
        result = _translate_regex(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,}")
        assert "email" in result.lower()

    def test_alternation(self):
        result = _translate_regex(r"cat|dog")
        assert "either" in result
        assert "cat" in result
        assert "dog" in result

    def test_dollar_amount(self):
        result = _translate_regex(r"\$\d+\.?\d*")
        assert "dollar amount" in result

    def test_any_dot(self):
        result = _translate_regex(r".+")
        assert "one or more" in result
        assert "any character" in result

    def test_word_boundary(self):
        result = _translate_regex(r"\b\w+\b")
        assert "word boundary" in result
        assert "word character" in result

    def test_optional(self):
        result = _translate_regex(r"colou?r")
        assert "optional" in result

    def test_character_class_negated(self):
        result = _translate_regex(r"[^0-9]")
        assert "except" in result

    def test_start_end_anchors(self):
        result = _translate_regex(r"^hello$")
        assert "start" in result
        assert "end" in result

    def test_invalid_regex_graceful(self):
        result = _translate_regex(r"[invalid")
        assert "pattern" in result

    def test_empty(self):
        result = _translate_regex("")
        # Should handle gracefully
        assert isinstance(result, str)

    def test_literal_only(self):
        result = _translate_regex("abc")
        assert '"abc"' in result

    def test_quantifier_exact(self):
        result = _translate_regex(r"\d{5}")
        assert "5" in result
        assert "digit" in result

    def test_quantifier_range(self):
        result = _translate_regex(r"\d{2,4}")
        assert "2" in result
        assert "4" in result
        assert "digit" in result

    def test_non_whitespace(self):
        result = _translate_regex(r"\S+")
        assert "non-whitespace" in result

    def test_group(self):
        result = _translate_regex(r"(\d{3})-(\d{4})")
        assert "digit" in result
        assert "dash" in result

    def test_zero_or_more(self):
        result = _translate_regex(r"\d*")
        assert "zero or more" in result
        assert "digit" in result


# ── Pattern recognition tests ────────────────────────────────

class TestPatternRecognition:
    def test_date_slash(self):
        label, _ = _identify_pattern(r"\d{1,2}/\d{1,2}/\d{2,4}")
        assert label == "a date"

    def test_date_iso(self):
        label, _ = _identify_pattern(r"\d{4}-\d{2}-\d{2}")
        assert label == "a date"

    def test_us_phone(self):
        label, _ = _identify_pattern(r"\d{3}-\d{3}-\d{4}")
        assert label == "a US phone number"

    def test_ssn(self):
        label, _ = _identify_pattern(r"\d{3}-\d{2}-\d{4}")
        assert label == "a Social Security Number (SSN)"

    def test_email(self):
        label, _ = _identify_pattern(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,}")
        assert label == "an email address"

    def test_url(self):
        label, _ = _identify_pattern(r"https?://\S+")
        assert label == "a URL"

    def test_ip_address(self):
        label, _ = _identify_pattern(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
        assert label == "an IP address"

    def test_phone_with_parens(self):
        label, _ = _identify_pattern(r"\(\d{3}\)\s?\d{3}-\d{4}")
        assert label == "a phone number with area code"

    def test_zip_code(self):
        label, _ = _identify_pattern(r"\b\d{5}(-\d{4})?\b")
        assert label == "a US ZIP code"

    def test_percentage(self):
        label, _ = _identify_pattern(r"\b\d+%")
        assert label == "a percentage"

    def test_fiscal_quarter(self):
        label, _ = _identify_pattern(r"Q[1-4]\s?\d{4}")
        assert label == "a fiscal quarter"

    def test_unknown_pattern(self):
        label, _ = _identify_pattern(r"\b[A-Z]{2,}\b")
        assert label is None

    def test_date_escaped_slashes(self):
        """Date with escaped slashes (e.g. from user typing \\/) should still be recognized."""
        label, _ = _identify_pattern(r"\d{1,2}\/\d{1,2}\/\d{2,4}")
        assert label == "a date"

    def test_date_digit_ranges(self):
        """Date using [0-9] instead of \\d should still be recognized."""
        label, _ = _identify_pattern(r"[0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4}")
        assert label == "a date"

    def test_date_with_anchors(self):
        """Date with ^ and $ anchors should still be recognized."""
        label, _ = _identify_pattern(r"^\d{1,2}/\d{1,2}/\d{2,4}$")
        assert label == "a date"

    def test_wizard_phone_pattern(self):
        """Phone pattern from Regex Wizard should be recognized."""
        label, _ = _identify_pattern(r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")
        assert label == "a phone number with area code"

    def test_date_in_translation(self):
        result = _translate_regex(r"\d{1,2}/\d{1,2}/\d{2,4}")
        assert "a date" in result
        assert "digit" not in result  # no character breakdown for known patterns

    def test_date_escaped_in_translation(self):
        """Escaped slashes should still produce clean date translation."""
        result = _translate_regex(r"\d{1,2}\/\d{1,2}\/\d{2,4}")
        assert "a date" in result
        assert "digit" not in result

    def test_phone_in_translation(self):
        result = _translate_regex(r"\d{3}-\d{3}-\d{4}")
        assert "phone number" in result
        assert "digit" not in result  # no character breakdown for known patterns

    def test_wizard_phone_in_translation(self):
        """Wizard phone pattern should produce clean phone translation."""
        result = _translate_regex(r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")
        assert "phone" in result
        assert "digit" not in result


# ── Wildcard translation tests ────────────────────────────────

class TestTranslateWildcard:
    def test_star(self):
        result = _translate_wildcard("budg*")
        assert "budg" in result
        assert "any characters" in result

    def test_question(self):
        result = _translate_wildcard("t?st")
        assert "any single character" in result

    def test_no_wildcards(self):
        result = _translate_wildcard("budget")
        assert '"budget"' in result

    def test_star_at_start(self):
        result = _translate_wildcard("*.pdf")
        assert "any characters" in result
        assert ".pdf" in result

    def test_multiple_wildcards(self):
        result = _translate_wildcard("a*b?c")
        assert "any characters" in result
        assert "any single character" in result

    def test_empty(self):
        result = _translate_wildcard("")
        assert isinstance(result, str)


# ── Full command translation tests ────────────────────────────

class TestTranslateCommand:
    def test_simple(self):
        result = translate_command("docsearch budget")
        assert "budget" in result
        assert "Search" in result

    def test_and_recursive(self):
        result = translate_command("docsearch -a -r budget revenue")
        assert "ALL" in result
        assert "subdirectories" in result
        assert "budget" in result
        assert "revenue" in result

    def test_or_mode(self):
        result = translate_command("docsearch budget revenue")
        assert "ANY" in result
        assert "budget" in result
        assert "revenue" in result

    def test_regex_flag(self):
        result = translate_command(r'docsearch -x "\d+"')
        assert "regex" in result
        assert "digit" in result

    def test_with_exclude(self):
        result = translate_command("docsearch -n draft budget")
        assert "exclud" in result
        assert "draft" in result

    def test_with_proximity(self):
        result = translate_command("docsearch -p 5 term1 term2")
        assert "5" in result
        assert "word" in result

    def test_with_file_types(self):
        result = translate_command("docsearch -t pdf,docx budget")
        assert "pdf" in result
        assert "docx" in result

    def test_with_ocr(self):
        result = translate_command("docsearch -O budget")
        assert "OCR" in result

    def test_with_fuzzy(self):
        result = translate_command("docsearch -z budgt")
        assert "fuzzy" in result

    def test_with_wildcard(self):
        result = translate_command('docsearch -w "budg*"')
        assert "wildcard" in result
        assert "budg" in result

    def test_with_context(self):
        result = translate_command("docsearch -A 5 -B 3 budget")
        assert "5" in result and "after" in result
        assert "3" in result and "before" in result

    def test_with_cores(self):
        result = translate_command("docsearch -c 4 budget")
        assert "4" in result and "core" in result

    def test_specific_files(self):
        result = translate_command("docsearch -f report.pdf budget")
        assert "report.pdf" in result

    def test_inverse(self):
        result = translate_command("docsearch -i budget")
        assert "inverse" in result or "WITHOUT" in result

    def test_empty_command(self):
        result = translate_command("")
        assert isinstance(result, str)

    def test_no_terms(self):
        result = translate_command("docsearch")
        assert isinstance(result, str)

    def test_single_term_no_any_all(self):
        """Single term should not mention ANY/ALL."""
        result = translate_command("docsearch budget")
        assert "ANY" not in result
        assert "ALL" not in result

    def test_quoted_regex_with_spaces(self):
        result = translate_command('docsearch -x "\\d{3} \\d{4}"')
        assert "digit" in result

    def test_complex_regex(self):
        """Complex alternation regex identifies each branch."""
        result = _translate_regex(
            r"(\d{1,2}/\d{1,2}/\d{2,4})|(\$[\d,]+\.?\d*)|([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})"
        )
        assert "either" in result
        assert "date" in result
        assert "dollar" in result
        assert "email" in result
