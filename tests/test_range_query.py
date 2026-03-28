"""Tests for the range_query module."""

import datetime
import os
import tempfile

import pytest

from docsearch.range_query import (
    RangeSpec,
    parse_range,
    split_ranges,
    line_matches_content_ranges,
    file_matches_metadata_ranges,
    file_matches_filename_ranges,
    _extract_dates,
    _extract_amounts,
    _extract_numbers,
    _extract_percents,
    _extract_ages,
    _extract_times,
    _parse_filesize,
)


# ── Parsing ──────────────────────────────────────────────────────

class TestParseRange:
    def test_basic(self):
        r = parse_range("amount:1000..5000")
        assert r.field == "amount"
        assert r.min_val == "1000"
        assert r.max_val == "5000"

    def test_open_min(self):
        r = parse_range("number:..100")
        assert r.field == "number"
        assert r.min_val == ""
        assert r.max_val == "100"

    def test_open_max(self):
        r = parse_range("number:100..")
        assert r.field == "number"
        assert r.min_val == "100"
        assert r.max_val == ""

    def test_date_range(self):
        r = parse_range("date:2024-01-01..2024-12-31")
        assert r.field == "date"
        assert r.min_val == "2024-01-01"
        assert r.max_val == "2024-12-31"

    def test_filesize(self):
        r = parse_range("filesize:1M..10M")
        assert r.field == "filesize"

    def test_invalid_field(self):
        with pytest.raises(ValueError, match="Unknown range field"):
            parse_range("unknown:1..2")

    def test_missing_colon(self):
        with pytest.raises(ValueError, match="missing ':'"):
            parse_range("amount1000..5000")

    def test_missing_dots(self):
        with pytest.raises(ValueError, match="missing '..'"):
            parse_range("amount:1000-5000")

    def test_empty_both(self):
        with pytest.raises(ValueError, match="at least a min or max"):
            parse_range("amount:..")

    def test_whitespace_tolerance(self):
        r = parse_range("  amount : 100 .. 500 ")
        assert r.field == "amount"
        assert r.min_val == "100"
        assert r.max_val == "500"


class TestSplitRanges:
    def test_split(self):
        ranges = [
            RangeSpec("date", "2024-01-01", "2024-12-31", target="content"),
            RangeSpec("filesize", "1M", "10M", target="metadata"),
            RangeSpec("amount", "100", "500", target="content"),
            RangeSpec("filedate", "2024-01-01", "", target="metadata"),
        ]
        content, metadata, filename = split_ranges(ranges)
        assert len(content) == 2
        assert len(metadata) == 2
        assert len(filename) == 0
        assert {r.field for r in content} == {"date", "amount"}
        assert {r.field for r in metadata} == {"filesize", "filedate"}

    def test_split_with_filename(self):
        ranges = [
            RangeSpec("date", "2024-01-01", "2024-12-31", target="filename"),
            RangeSpec("amount", "100", "500", target="content"),
            RangeSpec("filesize", "1M", "10M", target="metadata"),
        ]
        content, metadata, filename = split_ranges(ranges)
        assert len(content) == 1
        assert len(metadata) == 1
        assert len(filename) == 1
        assert filename[0].field == "date"


# ── Extractors ───────────────────────────────────────────────────

class TestExtractDates:
    def test_iso(self):
        dates = _extract_dates("Meeting on 2024-03-15 confirmed")
        assert datetime.date(2024, 3, 15) in dates

    def test_us_format(self):
        dates = _extract_dates("Due date: 03/15/2024")
        assert datetime.date(2024, 3, 15) in dates

    def test_natural(self):
        dates = _extract_dates("Submitted on January 15, 2024")
        assert datetime.date(2024, 1, 15) in dates

    def test_natural_short(self):
        dates = _extract_dates("Report from Jan 5, 2024")
        assert datetime.date(2024, 1, 5) in dates

    def test_no_dates(self):
        assert _extract_dates("no dates here") == []

    def test_multiple(self):
        dates = _extract_dates("From 2024-01-01 to 2024-12-31")
        assert len(dates) == 2


class TestExtractAmounts:
    def test_dollar_sign(self):
        amounts = _extract_amounts("Total: $1,234.56")
        assert 1234.56 in amounts

    def test_usd_prefix(self):
        amounts = _extract_amounts("Cost is USD 500")
        assert 500.0 in amounts

    def test_dollars_suffix(self):
        amounts = _extract_amounts("Paid 2500 dollars")
        assert 2500.0 in amounts

    def test_no_amounts(self):
        assert _extract_amounts("no money here") == []


class TestExtractNumbers:
    def test_integer(self):
        numbers = _extract_numbers("There are 42 items")
        assert 42.0 in numbers

    def test_float(self):
        numbers = _extract_numbers("Value is 3.14")
        assert 3.14 in numbers

    def test_comma_separated(self):
        numbers = _extract_numbers("Population: 1,234,567")
        assert 1234567.0 in numbers

    def test_no_numbers(self):
        assert _extract_numbers("no numbers here") == []


class TestExtractPercents:
    def test_percent_sign(self):
        percents = _extract_percents("Growth was 45%")
        assert 45.0 in percents

    def test_percent_word(self):
        percents = _extract_percents("Achieved 92 percent")
        assert 92.0 in percents

    def test_decimal_percent(self):
        percents = _extract_percents("Rate: 3.5%")
        assert 3.5 in percents


class TestExtractAges:
    def test_age_prefix(self):
        ages = _extract_ages("age 25")
        assert 25 in ages

    def test_aged_prefix(self):
        ages = _extract_ages("aged 30")
        assert 30 in ages

    def test_years_old(self):
        ages = _extract_ages("She is 42 years old")
        assert 42 in ages

    def test_no_ages(self):
        assert _extract_ages("no age info") == []


class TestExtractTimes:
    def test_24h(self):
        times = _extract_times("Meeting at 14:30")
        assert datetime.time(14, 30) in times

    def test_12h_pm(self):
        times = _extract_times("Lunch at 2:30 PM")
        assert datetime.time(14, 30) in times

    def test_12h_am(self):
        times = _extract_times("Wake up at 6:00 AM")
        assert datetime.time(6, 0) in times

    def test_with_seconds(self):
        times = _extract_times("Timestamp: 14:30:45")
        assert datetime.time(14, 30, 45) in times


class TestParseFilesize:
    def test_kilobytes(self):
        assert _parse_filesize("1K") == 1024

    def test_megabytes(self):
        assert _parse_filesize("5M") == 5 * 1024 * 1024

    def test_gigabytes(self):
        assert _parse_filesize("2G") == 2 * 1024 * 1024 * 1024

    def test_plain_bytes(self):
        assert _parse_filesize("1024") == 1024

    def test_fractional(self):
        assert _parse_filesize("1.5M") == int(1.5 * 1024 * 1024)


# ── Content range matching ───────────────────────────────────────

class TestLineMatchesContentRanges:
    def test_amount_in_range(self):
        ranges = [RangeSpec("amount", "1000", "5000")]
        assert line_matches_content_ranges("Total: $2,500.00 for services", ranges)

    def test_amount_out_of_range(self):
        ranges = [RangeSpec("amount", "1000", "5000")]
        assert not line_matches_content_ranges("Total: $500.00 for services", ranges)

    def test_date_in_range(self):
        ranges = [RangeSpec("date", "2024-01-01", "2024-12-31")]
        assert line_matches_content_ranges("Meeting on 2024-06-15", ranges)

    def test_date_out_of_range(self):
        ranges = [RangeSpec("date", "2024-01-01", "2024-12-31")]
        assert not line_matches_content_ranges("Meeting on 2023-06-15", ranges)

    def test_open_ended_min(self):
        ranges = [RangeSpec("number", "100", "")]
        assert line_matches_content_ranges("There are 500 items", ranges)
        assert not line_matches_content_ranges("There are 50 items", ranges)

    def test_open_ended_max(self):
        ranges = [RangeSpec("number", "", "100")]
        assert line_matches_content_ranges("There are 50 items", ranges)
        assert not line_matches_content_ranges("There are 500 items", ranges)

    def test_multiple_ranges_and(self):
        ranges = [
            RangeSpec("amount", "1000", "5000"),
            RangeSpec("date", "2024-01-01", "2024-12-31"),
        ]
        assert line_matches_content_ranges("Invoice $2,500 on 2024-06-15", ranges)
        assert not line_matches_content_ranges("Invoice $2,500 on 2023-06-15", ranges)
        assert not line_matches_content_ranges("Invoice $500 on 2024-06-15", ranges)

    def test_no_extractable_values(self):
        ranges = [RangeSpec("amount", "1000", "5000")]
        assert not line_matches_content_ranges("No amounts here", ranges)

    def test_percent_range(self):
        ranges = [RangeSpec("percent", "10", "50")]
        assert line_matches_content_ranges("Growth rate: 25%", ranges)
        assert not line_matches_content_ranges("Growth rate: 75%", ranges)

    def test_age_range(self):
        ranges = [RangeSpec("age", "18", "65")]
        assert line_matches_content_ranges("Patient aged 30", ranges)
        assert not line_matches_content_ranges("Patient aged 10", ranges)

    def test_time_range(self):
        ranges = [RangeSpec("time", "09:00", "17:00")]
        assert line_matches_content_ranges("Meeting at 14:30", ranges)
        assert not line_matches_content_ranges("Meeting at 20:00", ranges)


# ── Metadata range matching ──────────────────────────────────────

class TestFileMatchesMetadataRanges:
    def test_filesize_in_range(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"x" * 5000)
            path = f.name
        try:
            ranges = [RangeSpec("filesize", "1K", "10K")]
            assert file_matches_metadata_ranges(path, ranges)
        finally:
            os.unlink(path)

    def test_filesize_out_of_range(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"x" * 100)
            path = f.name
        try:
            ranges = [RangeSpec("filesize", "1K", "10K")]
            assert not file_matches_metadata_ranges(path, ranges)
        finally:
            os.unlink(path)

    def test_filedate_in_range(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            path = f.name
        try:
            today = datetime.date.today()
            ranges = [RangeSpec("filedate", str(today), str(today))]
            assert file_matches_metadata_ranges(path, ranges)
        finally:
            os.unlink(path)

    def test_nonexistent_file(self):
        ranges = [RangeSpec("filesize", "1K", "10K")]
        assert not file_matches_metadata_ranges("/nonexistent/file.txt", ranges)


# ── Prefix parsing (fn:/fc:) ────────────────────────────────────

class TestPrefixParsing:
    def test_fn_date(self):
        r = parse_range("fn:date:2024-01-01..2024-12-31")
        assert r.field == "date"
        assert r.target == "filename"
        assert r.min_val == "2024-01-01"
        assert r.max_val == "2024-12-31"

    def test_fn_amount(self):
        r = parse_range("fn:amount:1000..5000")
        assert r.field == "amount"
        assert r.target == "filename"

    def test_fn_number(self):
        r = parse_range("fn:number:1..100")
        assert r.field == "number"
        assert r.target == "filename"

    def test_fn_percent(self):
        r = parse_range("fn:percent:10..90")
        assert r.field == "percent"
        assert r.target == "filename"

    def test_fn_age(self):
        r = parse_range("fn:age:18..65")
        assert r.field == "age"
        assert r.target == "filename"

    def test_fn_time(self):
        r = parse_range("fn:time:09:00..17:00")
        assert r.field == "time"
        assert r.target == "filename"

    def test_fc_amount(self):
        r = parse_range("fc:amount:1000..5000")
        assert r.field == "amount"
        assert r.target == "content"

    def test_no_prefix_default_content(self):
        r = parse_range("amount:1000..5000")
        assert r.field == "amount"
        assert r.target == "content"

    def test_metadata_auto_target(self):
        r = parse_range("filesize:1M..10M")
        assert r.field == "filesize"
        assert r.target == "metadata"

    def test_fn_filesize_raises(self):
        with pytest.raises(ValueError, match="Cannot use 'fn:' prefix"):
            parse_range("fn:filesize:1M..10M")

    def test_fc_filesize_raises(self):
        with pytest.raises(ValueError, match="Cannot use 'fc:' prefix"):
            parse_range("fc:filesize:1M..10M")

    def test_fn_filedate_raises(self):
        with pytest.raises(ValueError, match="Cannot use 'fn:' prefix"):
            parse_range("fn:filedate:2024-01-01..2024-12-31")

    def test_case_insensitive_FN(self):
        r = parse_range("FN:date:2024-01-01..2024-12-31")
        assert r.target == "filename"

    def test_case_insensitive_Fn(self):
        r = parse_range("Fn:date:2024-01-01..2024-12-31")
        assert r.target == "filename"

    def test_case_insensitive_FC(self):
        r = parse_range("FC:amount:1000..5000")
        assert r.target == "content"


# ── Filename range matching ─────────────────────────────────────

class TestFileMatchesFilenameRanges:
    def test_date_in_filename_match(self):
        ranges = [RangeSpec("date", "2024-01-01", "2024-12-31", target="filename")]
        assert file_matches_filename_ranges("report-2024-06-15.pdf", ranges)

    def test_date_in_filename_no_match(self):
        ranges = [RangeSpec("date", "2024-01-01", "2024-12-31", target="filename")]
        assert not file_matches_filename_ranges("report-2023-06-15.pdf", ranges)

    def test_no_date_in_filename(self):
        ranges = [RangeSpec("date", "2024-01-01", "2024-12-31", target="filename")]
        assert not file_matches_filename_ranges("report.pdf", ranges)

    def test_amount_in_filename(self):
        ranges = [RangeSpec("amount", "1000", "5000", target="filename")]
        assert file_matches_filename_ranges("invoice-$2500.pdf", ranges)

    def test_amount_in_filename_no_match(self):
        ranges = [RangeSpec("amount", "1000", "5000", target="filename")]
        assert not file_matches_filename_ranges("invoice-$500.pdf", ranges)

    def test_number_in_filename(self):
        ranges = [RangeSpec("number", "100", "200", target="filename")]
        assert file_matches_filename_ranges(" 150 ", ranges)

    def test_multiple_filename_ranges_and(self):
        ranges = [
            RangeSpec("date", "2024-01-01", "2024-12-31", target="filename"),
            RangeSpec("number", "1", "10", target="filename"),
        ]
        assert file_matches_filename_ranges("report- 5 -2024-06-15.pdf", ranges)
        assert not file_matches_filename_ranges("report-2024-06-15.pdf", ranges)
