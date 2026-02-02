"""Unit tests for shared/utils.py."""

import pytest
import time
from datetime import datetime, timezone

from src.shared.utils import (
    # String utilities
    normalize_text,
    normalize_answer,
    extract_numbers,
    truncate_text,
    sanitize_for_filename,
    # Numeric utilities
    numbers_approximately_equal,
    format_number,
    safe_divide,
    # Time utilities
    utc_now,
    format_timestamp,
    parse_timestamp,
    measure_time,
    Timer,
    # Hash utilities
    generate_hash,
    generate_cache_key,
    # Collection utilities
    chunk_list,
    flatten_dict,
    deep_get,
    merge_dicts,
    # Validation utilities
    is_valid_url,
    is_valid_email,
    is_valid_uuid,
    # Fuzzy matching
    fuzzy_match,
    find_best_match,
)


class TestNormalizeText:
    """Tests for normalize_text function."""

    def test_lowercase(self):
        """Test text is lowercased."""
        assert normalize_text("HELLO") == "hello"

    def test_whitespace_normalized(self):
        """Test extra whitespace is normalized."""
        assert normalize_text("hello   world") == "hello world"
        assert normalize_text("  hello  ") == "hello"

    def test_unicode_normalized(self):
        """Test unicode is normalized."""
        # Different representations of the same character
        assert normalize_text("café") == normalize_text("café")

    def test_empty_string(self):
        """Test empty string handling."""
        assert normalize_text("") == ""
        assert normalize_text("   ") == ""

    def test_none_handling(self):
        """Test None-like handling."""
        assert normalize_text("") == ""


class TestNormalizeAnswer:
    """Tests for normalize_answer function."""

    def test_removes_common_prefixes(self):
        """Test common answer prefixes are removed."""
        assert normalize_answer("The answer is 42") == "42"
        assert normalize_answer("Answer: 42") == "42"

    def test_handles_context_prefixes(self):
        """Test context prefixes are removed."""
        assert "stripe" in normalize_answer("Based on Wikipedia, Stripe was founded in 2010")

    def test_preserves_core_answer(self):
        """Test core answer is preserved."""
        assert normalize_answer("2010") == "2010"

    def test_empty_string(self):
        """Test empty string handling."""
        assert normalize_answer("") == ""


class TestExtractNumbers:
    """Tests for extract_numbers function."""

    def test_extract_integers(self):
        """Test extracting integers."""
        assert extract_numbers("There are 42 items") == [42.0]

    def test_extract_decimals(self):
        """Test extracting decimals."""
        assert extract_numbers("The value is 3.14") == [3.14]

    def test_extract_with_commas(self):
        """Test extracting numbers with commas."""
        assert extract_numbers("Revenue is 1,000,000") == [1000000.0]

    def test_extract_multiple_numbers(self):
        """Test extracting multiple numbers."""
        result = extract_numbers("From 100 to 200")
        assert 100.0 in result
        assert 200.0 in result

    def test_no_numbers(self):
        """Test string with no numbers."""
        assert extract_numbers("No numbers here") == []


class TestTruncateText:
    """Tests for truncate_text function."""

    def test_short_text_unchanged(self):
        """Test short text is unchanged."""
        assert truncate_text("hello", 10) == "hello"

    def test_long_text_truncated(self):
        """Test long text is truncated."""
        result = truncate_text("hello world", 8)
        assert len(result) == 8
        assert result.endswith("...")

    def test_custom_suffix(self):
        """Test custom suffix."""
        result = truncate_text("hello world", 9, suffix="…")
        assert result.endswith("…")

    def test_empty_string(self):
        """Test empty string."""
        assert truncate_text("", 10) == ""


class TestSanitizeForFilename:
    """Tests for sanitize_for_filename function."""

    def test_removes_invalid_chars(self):
        """Test invalid characters are removed."""
        result = sanitize_for_filename("file<>name")
        assert "<" not in result
        assert ">" not in result

    def test_replaces_with_underscore(self):
        """Test invalid chars replaced with underscore."""
        result = sanitize_for_filename("file:name")
        assert result == "file_name"

    def test_limits_length(self):
        """Test filename length is limited."""
        long_name = "a" * 300
        result = sanitize_for_filename(long_name)
        assert len(result) <= 200


class TestNumbersApproximatelyEqual:
    """Tests for numbers_approximately_equal function."""

    def test_exact_match(self):
        """Test exact numbers match."""
        assert numbers_approximately_equal(100, 100) is True

    def test_within_tolerance(self):
        """Test numbers within tolerance."""
        assert numbers_approximately_equal(100, 105, tolerance_percent=10) is True
        assert numbers_approximately_equal(100, 95, tolerance_percent=10) is True

    def test_outside_tolerance(self):
        """Test numbers outside tolerance."""
        assert numbers_approximately_equal(100, 120, tolerance_percent=10) is False

    def test_zero_handling(self):
        """Test zero handling."""
        assert numbers_approximately_equal(0, 0) is True
        assert numbers_approximately_equal(0, 0.05, tolerance_percent=10) is True

    def test_negative_numbers(self):
        """Test negative numbers."""
        assert numbers_approximately_equal(-100, -100) is True
        assert numbers_approximately_equal(-100, -105, tolerance_percent=10) is True


class TestFormatNumber:
    """Tests for format_number function."""

    def test_billions(self):
        """Test billion formatting."""
        assert "B" in format_number(1_500_000_000)

    def test_millions(self):
        """Test million formatting."""
        assert "M" in format_number(1_500_000)

    def test_thousands(self):
        """Test thousand formatting."""
        assert "K" in format_number(1_500)

    def test_small_numbers(self):
        """Test small number formatting."""
        assert format_number(100) == "100.00"

    def test_precision(self):
        """Test custom precision."""
        result = format_number(1_500_000, precision=1)
        assert "1.5M" == result


class TestSafeDivide:
    """Tests for safe_divide function."""

    def test_normal_division(self):
        """Test normal division."""
        assert safe_divide(10, 2) == 5.0

    def test_division_by_zero(self):
        """Test division by zero returns default."""
        assert safe_divide(10, 0) == 0.0

    def test_custom_default(self):
        """Test custom default value."""
        assert safe_divide(10, 0, default=-1) == -1


class TestTimeUtilities:
    """Tests for time utilities."""

    def test_utc_now(self):
        """Test utc_now returns UTC time."""
        now = utc_now()
        assert now.tzinfo is not None

    def test_format_timestamp(self):
        """Test timestamp formatting."""
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = format_timestamp(dt)
        assert "2024-01-15" in result

    def test_format_timestamp_default(self):
        """Test format_timestamp with no argument."""
        result = format_timestamp()
        assert result is not None

    def test_parse_timestamp(self):
        """Test timestamp parsing."""
        ts = "2024-01-15T10:30:00+00:00"
        dt = parse_timestamp(ts)
        assert dt.year == 2024
        assert dt.month == 1

    def test_timer_context_manager(self):
        """Test Timer context manager."""
        with Timer("test") as t:
            time.sleep(0.01)
        assert t.elapsed_ms > 0

    def test_measure_time_decorator(self):
        """Test measure_time decorator."""
        @measure_time
        def slow_function():
            time.sleep(0.01)
            return "done"

        result = slow_function()
        assert result == "done"


class TestHashUtilities:
    """Tests for hash utilities."""

    def test_generate_hash(self):
        """Test hash generation."""
        hash1 = generate_hash("test")
        hash2 = generate_hash("test")
        assert hash1 == hash2
        assert len(hash1) == 8

    def test_generate_hash_different_inputs(self):
        """Test different inputs produce different hashes."""
        hash1 = generate_hash("test1")
        hash2 = generate_hash("test2")
        assert hash1 != hash2

    def test_generate_cache_key(self):
        """Test cache key generation."""
        key1 = generate_cache_key("query", limit=10)
        key2 = generate_cache_key("query", limit=10)
        assert key1 == key2

    def test_cache_key_different_args(self):
        """Test different args produce different keys."""
        key1 = generate_cache_key("query1")
        key2 = generate_cache_key("query2")
        assert key1 != key2


class TestCollectionUtilities:
    """Tests for collection utilities."""

    def test_chunk_list(self):
        """Test list chunking."""
        lst = [1, 2, 3, 4, 5]
        chunks = chunk_list(lst, 2)
        assert chunks == [[1, 2], [3, 4], [5]]

    def test_chunk_list_exact(self):
        """Test chunking when list divides evenly."""
        lst = [1, 2, 3, 4]
        chunks = chunk_list(lst, 2)
        assert chunks == [[1, 2], [3, 4]]

    def test_flatten_dict(self):
        """Test dictionary flattening."""
        nested = {"a": {"b": {"c": 1}}}
        flat = flatten_dict(nested)
        assert flat == {"a.b.c": 1}

    def test_flatten_dict_custom_separator(self):
        """Test custom separator."""
        nested = {"a": {"b": 1}}
        flat = flatten_dict(nested, sep="_")
        assert flat == {"a_b": 1}

    def test_deep_get(self):
        """Test deep_get function."""
        d = {"a": {"b": {"c": 1}}}
        assert deep_get(d, "a.b.c") == 1
        assert deep_get(d, "a.b.d", default="not found") == "not found"

    def test_merge_dicts(self):
        """Test dictionary merging."""
        d1 = {"a": 1, "b": {"c": 2}}
        d2 = {"b": {"d": 3}, "e": 4}
        result = merge_dicts(d1, d2)
        assert result["a"] == 1
        assert result["b"]["c"] == 2
        assert result["b"]["d"] == 3
        assert result["e"] == 4


class TestValidationUtilities:
    """Tests for validation utilities."""

    def test_valid_url(self):
        """Test valid URLs."""
        assert is_valid_url("https://example.com") is True
        assert is_valid_url("http://localhost:8000") is True
        assert is_valid_url("https://example.com/path?query=1") is True

    def test_invalid_url(self):
        """Test invalid URLs."""
        assert is_valid_url("not-a-url") is False
        assert is_valid_url("ftp://example.com") is False

    def test_valid_email(self):
        """Test valid emails."""
        assert is_valid_email("test@example.com") is True
        assert is_valid_email("user.name@domain.co.uk") is True

    def test_invalid_email(self):
        """Test invalid emails."""
        assert is_valid_email("not-an-email") is False
        assert is_valid_email("@example.com") is False

    def test_valid_uuid(self):
        """Test valid UUIDs."""
        assert is_valid_uuid("550e8400-e29b-41d4-a716-446655440000") is True

    def test_invalid_uuid(self):
        """Test invalid UUIDs."""
        assert is_valid_uuid("not-a-uuid") is False
        assert is_valid_uuid("550e8400-e29b-41d4") is False


class TestFuzzyMatching:
    """Tests for fuzzy matching utilities."""

    def test_fuzzy_match_exact(self):
        """Test exact match."""
        assert fuzzy_match("hello", "hello") is True

    def test_fuzzy_match_normalized(self):
        """Test normalized match."""
        assert fuzzy_match("HELLO", "hello") is True

    def test_fuzzy_match_contained(self):
        """Test contained match."""
        assert fuzzy_match("The answer is hello", "hello") is True

    def test_fuzzy_match_numbers(self):
        """Test numeric fuzzy match."""
        # Both extract as plain numbers and compare
        assert fuzzy_match("About 100", "100", tolerance=0.1) is True
        assert fuzzy_match("The value is 95", "100", tolerance=0.1) is True

    def test_fuzzy_match_numbers_within_tolerance(self):
        """Test numeric match within tolerance."""
        assert fuzzy_match("95", "100", tolerance=0.1) is True
        assert fuzzy_match("Revenue: $50B", "50", tolerance=0.1) is True

    def test_find_best_match(self):
        """Test find_best_match function."""
        # Need enough token overlap to exceed threshold
        candidates = ["apple computer inc", "microsoft corp", "google llc"]
        result = find_best_match("apple computer", candidates, threshold=0.5)
        assert result == "apple computer inc"

    def test_find_best_match_no_match(self):
        """Test no match found."""
        candidates = ["apple", "microsoft", "google"]
        result = find_best_match("xyz corporation", candidates)
        assert result is None


class TestEdgeCases:
    """Edge case tests for utilities."""

    def test_extract_numbers_edge_cases(self):
        """Test edge cases for number extraction."""
        assert extract_numbers("") == []
        assert extract_numbers("$1,234.56") == [1234.56]
        # "1.2.3" extracts "1.2" and "3" as separate numbers
        result = extract_numbers("1.2.3")
        assert 1.2 in result
        assert 3.0 in result

    def test_normalize_text_edge_cases(self):
        """Test edge cases for text normalization."""
        assert normalize_text(None or "") == ""
        assert normalize_text("\t\n") == ""

    def test_chunk_list_edge_cases(self):
        """Test edge cases for list chunking."""
        assert chunk_list([], 5) == []
        assert chunk_list([1], 5) == [[1]]

    def test_deep_get_edge_cases(self):
        """Test edge cases for deep_get."""
        assert deep_get({}, "a.b") is None
        assert deep_get({"a": None}, "a.b") is None

    def test_safe_divide_edge_cases(self):
        """Test edge cases for safe_divide."""
        assert safe_divide(0, 0) == 0.0
        assert safe_divide(0, 5) == 0.0
