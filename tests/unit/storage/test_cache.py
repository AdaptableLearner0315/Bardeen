"""Unit tests for storage/cache.py."""

import pytest
import time
import threading
from unittest.mock import MagicMock

from src.storage.cache import (
    TTLCache,
    ToolResponseCache,
    CacheEntry,
    get_cache,
    get_tool_cache,
    reset_caches,
)
from src.shared.config import reset_config


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up caches after each test."""
    reset_caches()
    reset_config()
    yield
    reset_caches()
    reset_config()


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_create_entry(self):
        """Test creating a cache entry."""
        entry = CacheEntry(value="test", created_at=time.time(), ttl_seconds=60)
        assert entry.value == "test"
        assert entry.access_count == 0
        assert entry.is_expired is False

    def test_entry_expiration(self):
        """Test entry expiration."""
        entry = CacheEntry(value="test", created_at=time.time() - 100, ttl_seconds=60)
        assert entry.is_expired is True

    def test_entry_not_expired(self):
        """Test entry not expired."""
        entry = CacheEntry(value="test", created_at=time.time(), ttl_seconds=60)
        assert entry.is_expired is False

    def test_entry_age(self):
        """Test entry age calculation."""
        created = time.time() - 30
        entry = CacheEntry(value="test", created_at=created, ttl_seconds=60)
        assert entry.age_seconds >= 30
        assert entry.age_seconds < 31


class TestTTLCache:
    """Tests for TTLCache class."""

    def test_create_cache_default_config(self):
        """Test creating cache with default config."""
        cache = TTLCache()
        assert cache.max_size > 0
        assert cache.default_ttl > 0

    def test_create_cache_custom_config(self):
        """Test creating cache with custom config."""
        cache = TTLCache(default_ttl=30, max_size=100)
        assert cache.default_ttl == 30
        assert cache.max_size == 100

    def test_set_and_get(self):
        """Test basic set and get."""
        cache = TTLCache()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_missing_key(self):
        """Test getting missing key."""
        cache = TTLCache()
        assert cache.get("missing") is None
        assert cache.get("missing", default="default") == "default"

    def test_get_expired_key(self):
        """Test getting expired key."""
        cache = TTLCache(default_ttl=0.05)  # 50ms TTL
        cache.set("key1", "value1")
        time.sleep(0.1)  # Wait for expiration
        assert cache.get("key1") is None

    def test_delete(self):
        """Test deleting a key."""
        cache = TTLCache()
        cache.set("key1", "value1")
        assert cache.delete("key1") is True
        assert cache.get("key1") is None

    def test_delete_missing(self):
        """Test deleting missing key."""
        cache = TTLCache()
        assert cache.delete("missing") is False

    def test_exists(self):
        """Test exists check."""
        cache = TTLCache()
        cache.set("key1", "value1")
        assert cache.exists("key1") is True
        assert cache.exists("missing") is False

    def test_exists_expired(self):
        """Test exists returns False for expired."""
        cache = TTLCache(default_ttl=0.05)
        cache.set("key1", "value1")
        time.sleep(0.1)
        assert cache.exists("key1") is False

    def test_clear(self):
        """Test clearing cache."""
        cache = TTLCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        count = cache.clear()
        assert count == 2
        assert len(cache) == 0

    def test_cleanup_expired(self):
        """Test cleaning up expired entries."""
        cache = TTLCache(default_ttl=0.05)
        cache.set("key1", "value1")
        cache.set("key2", "value2", ttl=60)  # Long TTL
        time.sleep(0.1)
        removed = cache.cleanup_expired()
        assert removed == 1
        assert cache.exists("key2") is True

    def test_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = TTLCache(max_size=3)
        cache.set("key1", "value1")
        time.sleep(0.01)
        cache.set("key2", "value2")
        time.sleep(0.01)
        cache.set("key3", "value3")
        time.sleep(0.01)

        # Access key1 to make it recently used
        cache.get("key1")
        time.sleep(0.01)

        # Add new key, should evict key2 (least recently used)
        cache.set("key4", "value4")

        assert cache.exists("key1") is True
        assert cache.exists("key2") is False
        assert cache.exists("key3") is True
        assert cache.exists("key4") is True

    def test_set_negative(self):
        """Test negative caching."""
        cache = TTLCache(negative_ttl=0.1)
        cache.set_negative("not_found")
        assert cache.get("not_found") is None  # Value is None, but key exists
        assert "not_found" in cache

    def test_custom_ttl_per_key(self):
        """Test custom TTL per key."""
        cache = TTLCache(default_ttl=60)
        cache.set("short", "value", ttl=0.05)
        cache.set("long", "value", ttl=60)

        time.sleep(0.1)

        assert cache.get("short") is None
        assert cache.get("long") == "value"

    def test_get_or_set(self):
        """Test get_or_set method."""
        cache = TTLCache()
        factory_calls = [0]

        def factory():
            factory_calls[0] += 1
            return "computed_value"

        # First call should compute
        result1 = cache.get_or_set("key", factory)
        assert result1 == "computed_value"
        assert factory_calls[0] == 1

        # Second call should use cache
        result2 = cache.get_or_set("key", factory)
        assert result2 == "computed_value"
        assert factory_calls[0] == 1  # Factory not called again

    def test_get_or_set_factory_error(self):
        """Test get_or_set with factory error."""
        cache = TTLCache()

        def failing_factory():
            raise ValueError("Factory failed")

        with pytest.raises(ValueError):
            cache.get_or_set("key", failing_factory)

    def test_len(self):
        """Test len() operator."""
        cache = TTLCache()
        assert len(cache) == 0
        cache.set("key1", "value1")
        assert len(cache) == 1
        cache.set("key2", "value2")
        assert len(cache) == 2

    def test_contains(self):
        """Test 'in' operator."""
        cache = TTLCache()
        cache.set("key1", "value1")
        assert "key1" in cache
        assert "missing" not in cache

    def test_stats(self):
        """Test statistics tracking."""
        cache = TTLCache(max_size=100)
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key1")  # Hit
        cache.get("missing")  # Miss

        stats = cache.get_stats()
        assert stats["size"] == 1
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 2 / 3


class TestTTLCacheThreadSafety:
    """Thread safety tests for TTLCache."""

    def test_concurrent_reads(self):
        """Test concurrent reads."""
        cache = TTLCache()
        cache.set("key", "value")

        errors = []
        results = []
        lock = threading.Lock()

        def reader():
            try:
                for _ in range(100):
                    value = cache.get("key")
                    with lock:
                        results.append(value)
            except Exception as e:
                with lock:
                    errors.append(str(e))

        threads = [threading.Thread(target=reader) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert all(v == "value" for v in results)

    def test_concurrent_writes(self):
        """Test concurrent writes."""
        cache = TTLCache(max_size=1000)
        errors = []
        lock = threading.Lock()

        def writer(thread_id):
            try:
                for i in range(100):
                    cache.set(f"key-{thread_id}-{i}", f"value-{i}")
            except Exception as e:
                with lock:
                    errors.append(str(e))

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_concurrent_mixed_operations(self):
        """Test concurrent mixed operations."""
        cache = TTLCache(max_size=100)
        errors = []
        lock = threading.Lock()

        def mixed_ops(thread_id):
            try:
                for i in range(50):
                    key = f"key-{thread_id}-{i % 10}"
                    cache.set(key, f"value-{i}")
                    cache.get(key)
                    cache.exists(key)
                    if i % 5 == 0:
                        cache.delete(key)
            except Exception as e:
                with lock:
                    errors.append(str(e))

        threads = [threading.Thread(target=mixed_ops, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestToolResponseCache:
    """Tests for ToolResponseCache class."""

    def test_make_key(self):
        """Test key generation."""
        cache = ToolResponseCache()
        key1 = cache.make_key("web_search", query="test")
        key2 = cache.make_key("web_search", query="test")
        key3 = cache.make_key("web_search", query="different")

        assert key1 == key2
        assert key1 != key3
        assert key1.startswith("tool:web_search:")

    def test_set_and_get_tool_response(self):
        """Test setting and getting tool responses."""
        cache = ToolResponseCache()
        response = {"results": ["item1", "item2"]}

        cache.set_tool_response("web_search", response, query="test")
        result = cache.get_tool_response("web_search", query="test")

        assert result == response

    def test_get_tool_response_missing(self):
        """Test getting missing tool response."""
        cache = ToolResponseCache()
        result = cache.get_tool_response("web_search", default="not_found", query="test")
        assert result == "not_found"

    def test_invalidate_tool(self):
        """Test invalidating all responses for a tool."""
        cache = ToolResponseCache()

        cache.set_tool_response("web_search", "result1", query="test1")
        cache.set_tool_response("web_search", "result2", query="test2")
        cache.set_tool_response("wikipedia", "result3", topic="Python")

        removed = cache.invalidate_tool("web_search")

        assert removed == 2
        assert cache.get_tool_response("web_search", query="test1") is None
        assert cache.get_tool_response("web_search", query="test2") is None
        assert cache.get_tool_response("wikipedia", topic="Python") == "result3"


class TestCacheSingletons:
    """Tests for cache singleton functions."""

    def test_get_cache_singleton(self):
        """Test get_cache returns singleton."""
        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2

    def test_get_tool_cache_singleton(self):
        """Test get_tool_cache returns singleton."""
        cache1 = get_tool_cache()
        cache2 = get_tool_cache()
        assert cache1 is cache2

    def test_reset_caches(self):
        """Test reset_caches clears both caches."""
        cache = get_cache()
        cache.set("key", "value")

        tool_cache = get_tool_cache()
        tool_cache.set_tool_response("tool", "response", query="test")

        reset_caches()

        new_cache = get_cache()
        new_tool_cache = get_tool_cache()

        assert new_cache is not cache
        assert new_tool_cache is not tool_cache


class TestCacheEdgeCases:
    """Edge case tests for cache."""

    def test_none_value(self):
        """Test storing None value."""
        cache = TTLCache()
        cache.set("key", None)
        # None is a valid value, but get returns default for missing
        # Need to use exists to check
        assert cache.exists("key") is True

    def test_empty_string_value(self):
        """Test storing empty string."""
        cache = TTLCache()
        cache.set("key", "")
        assert cache.get("key") == ""

    def test_complex_value(self):
        """Test storing complex nested values."""
        cache = TTLCache()
        value = {
            "list": [1, 2, 3],
            "nested": {"a": {"b": "c"}},
            "tuple": (1, 2, 3),
        }
        cache.set("key", value)
        assert cache.get("key") == value

    def test_large_value(self):
        """Test storing large value."""
        cache = TTLCache()
        value = "x" * 1000000  # 1MB
        cache.set("key", value)
        assert cache.get("key") == value

    def test_special_characters_in_key(self):
        """Test keys with special characters."""
        cache = TTLCache()
        keys = ["key:with:colons", "key/with/slashes", "key with spaces", "key\nwith\nnewlines"]
        for key in keys:
            cache.set(key, "value")
            assert cache.get(key) == "value"

    def test_zero_ttl(self):
        """Test zero TTL (immediate expiration)."""
        cache = TTLCache()
        cache.set("key", "value", ttl=0)
        # Should expire immediately
        time.sleep(0.01)
        assert cache.get("key") is None

    def test_very_long_ttl(self):
        """Test very long TTL."""
        cache = TTLCache()
        cache.set("key", "value", ttl=86400 * 365)  # 1 year
        assert cache.get("key") == "value"

    def test_update_existing_key(self):
        """Test updating an existing key."""
        cache = TTLCache()
        cache.set("key", "value1")
        cache.set("key", "value2")
        assert cache.get("key") == "value2"

    def test_max_size_one(self):
        """Test cache with max_size of 1."""
        cache = TTLCache(max_size=1)
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        assert len(cache) == 1
        assert cache.get("key2") == "value2"
        assert cache.get("key1") is None  # Evicted
