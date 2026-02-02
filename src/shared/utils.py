"""Utility functions for the B2B Account Intelligence Agent."""

import re
import time
import hashlib
import unicodedata
from typing import Any, Dict, List, Optional, TypeVar, Callable
from datetime import datetime, timezone
from functools import wraps
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


# =============================================================================
# String Utilities
# =============================================================================

def normalize_text(text: str) -> str:
    """Normalize text for comparison.

    - Lowercase
    - Remove extra whitespace
    - Normalize unicode
    """
    if not text:
        return ""
    # Normalize unicode
    text = unicodedata.normalize("NFKC", text)
    # Lowercase
    text = text.lower()
    # Remove extra whitespace
    text = " ".join(text.split())
    return text.strip()


def normalize_answer(answer: str) -> str:
    """Normalize an answer for evaluation comparison.

    - Remove common prefixes like "The answer is"
    - Normalize numbers
    - Remove punctuation
    """
    if not answer:
        return ""

    # Common answer prefixes to remove
    prefixes = [
        r"^the answer is\s*",
        r"^answer:\s*",
        r"^based on.*?,\s*",
        r"^according to.*?,\s*",
    ]

    text = answer.lower().strip()
    for prefix in prefixes:
        text = re.sub(prefix, "", text, flags=re.IGNORECASE)

    # Normalize whitespace
    text = " ".join(text.split())

    return text.strip()


def extract_numbers(text: str) -> List[float]:
    """Extract all numbers from text."""
    # Match integers, decimals, and numbers with commas
    pattern = r'[\d,]+\.?\d*'
    matches = re.findall(pattern, text)

    numbers = []
    for match in matches:
        try:
            # Remove commas and convert
            num = float(match.replace(",", ""))
            numbers.append(num)
        except ValueError:
            continue

    return numbers


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to max length with suffix."""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def sanitize_for_filename(text: str) -> str:
    """Sanitize text for use in filenames."""
    # Remove or replace invalid characters
    text = re.sub(r'[<>:"/\\|?*]', '_', text)
    # Remove control characters
    text = "".join(c for c in text if unicodedata.category(c) != 'Cc')
    # Limit length
    return text[:200].strip()


# =============================================================================
# Numeric Utilities
# =============================================================================

def numbers_approximately_equal(
    a: float,
    b: float,
    tolerance_percent: float = 10.0
) -> bool:
    """Check if two numbers are approximately equal within tolerance."""
    if a == b:
        return True
    if a == 0 or b == 0:
        return abs(a - b) < (tolerance_percent / 100)

    diff_percent = abs(a - b) / max(abs(a), abs(b)) * 100
    return diff_percent <= tolerance_percent


def format_number(num: float, precision: int = 2) -> str:
    """Format number with thousand separators."""
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.{precision}f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.{precision}f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.{precision}f}K"
    else:
        return f"{num:.{precision}f}"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero."""
    if denominator == 0:
        return default
    return numerator / denominator


# =============================================================================
# Time Utilities
# =============================================================================

def utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format datetime as ISO string."""
    if dt is None:
        dt = utc_now()
    return dt.isoformat()


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO timestamp string."""
    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))


def measure_time(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to measure function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000  # ms
        logger.debug(f"{func.__name__} took {elapsed:.2f}ms")
        return result
    return wrapper


class Timer:
    """Context manager for timing code blocks."""

    def __init__(self, name: str = "operation"):
        self.name = name
        self.start_time: float = 0
        self.elapsed_ms: float = 0

    def __enter__(self) -> 'Timer':
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args) -> None:
        self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000
        logger.debug(f"{self.name} took {self.elapsed_ms:.2f}ms")


# =============================================================================
# Hash Utilities
# =============================================================================

def generate_hash(data: str, length: int = 8) -> str:
    """Generate a short hash from data."""
    return hashlib.sha256(data.encode()).hexdigest()[:length]


def generate_cache_key(*args, **kwargs) -> str:
    """Generate a cache key from arguments."""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    key_string = ":".join(key_parts)
    return generate_hash(key_string, 16)


# =============================================================================
# Collection Utilities
# =============================================================================

def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_dict(
    d: Dict[str, Any],
    parent_key: str = '',
    sep: str = '.'
) -> Dict[str, Any]:
    """Flatten a nested dictionary."""
    items: List[tuple] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def deep_get(d: Dict[str, Any], path: str, default: Any = None) -> Any:
    """Get a value from nested dict using dot notation path."""
    keys = path.split('.')
    value = d
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    return value


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge multiple dictionaries."""
    result: Dict[str, Any] = {}
    for d in dicts:
        for key, value in d.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_dicts(result[key], value)
            else:
                result[key] = value
    return result


# =============================================================================
# Retry Utilities
# =============================================================================

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """Decorator for retrying with exponential backoff."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception: Optional[Exception] = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = min(
                            base_delay * (exponential_base ** attempt),
                            max_delay
                        )
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                            f"retrying in {delay:.1f}s: {e}"
                        )
                        time.sleep(delay)

            raise last_exception  # type: ignore

        return wrapper
    return decorator


async def async_retry_with_backoff(
    func: Callable,
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    exceptions: tuple = (Exception,),
    **kwargs
) -> Any:
    """Async retry with exponential backoff."""
    import asyncio

    last_exception: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    f"Async call failed (attempt {attempt + 1}/{max_retries + 1}), "
                    f"retrying in {delay:.1f}s: {e}"
                )
                await asyncio.sleep(delay)

    raise last_exception  # type: ignore


# =============================================================================
# Validation Utilities
# =============================================================================

def is_valid_url(url: str) -> bool:
    """Check if string is a valid URL."""
    pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$',
        re.IGNORECASE
    )
    return bool(pattern.match(url))


def is_valid_email(email: str) -> bool:
    """Check if string is a valid email address."""
    pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return bool(pattern.match(email))


def is_valid_uuid(value: str) -> bool:
    """Check if string is a valid UUID."""
    pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(pattern.match(value))


# =============================================================================
# Fuzzy Matching
# =============================================================================

def fuzzy_match(
    text: str,
    target: str,
    tolerance: float = 0.1
) -> bool:
    """Check if text matches target with some tolerance.

    For numeric comparisons, uses percentage tolerance.
    For text, uses normalized comparison.
    """
    # Try numeric comparison first
    text_numbers = extract_numbers(text)
    target_numbers = extract_numbers(target)

    if text_numbers and target_numbers:
        # Compare the most prominent numbers
        return numbers_approximately_equal(
            text_numbers[0],
            target_numbers[0],
            tolerance * 100
        )

    # Text comparison
    normalized_text = normalize_answer(text)
    normalized_target = normalize_answer(target)

    # Exact match after normalization
    if normalized_text == normalized_target:
        return True

    # Check if target is contained in text
    if normalized_target in normalized_text:
        return True

    return False


def find_best_match(
    query: str,
    candidates: List[str],
    threshold: float = 0.6
) -> Optional[str]:
    """Find the best matching candidate for a query."""
    query_normalized = normalize_text(query)

    best_match: Optional[str] = None
    best_score = threshold

    for candidate in candidates:
        candidate_normalized = normalize_text(candidate)

        # Simple token overlap score
        query_tokens = set(query_normalized.split())
        candidate_tokens = set(candidate_normalized.split())

        if not query_tokens or not candidate_tokens:
            continue

        overlap = len(query_tokens & candidate_tokens)
        score = overlap / max(len(query_tokens), len(candidate_tokens))

        if score > best_score:
            best_score = score
            best_match = candidate

    return best_match
