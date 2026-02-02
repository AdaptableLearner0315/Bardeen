"""Tests for tool result caching."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import time

# Import will work after module is updated
try:
    from src.agent.tool_registry import ToolCache, get_tool_cache, reset_tool_cache
except ImportError:
    ToolCache = None
    get_tool_cache = None
    reset_tool_cache = None


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up cache between tests."""
    if reset_tool_cache:
        reset_tool_cache()
    yield
    if reset_tool_cache:
        reset_tool_cache()


class TestToolCache:
    """Tests for ToolCache class."""

    @pytest.fixture
    def cache(self):
        """Create a fresh cache instance."""
        if ToolCache is None:
            pytest.skip("ToolCache not available")
        return ToolCache()

    def test_cache_initialization(self, cache):
        """Test cache initializes empty."""
        assert len(cache._cache) == 0
        assert len(cache._access_order) == 0

    def test_cache_set_and_get(self, cache):
        """Test basic set and get operations."""
        params = {"query": "France"}
        result = {"title": "France", "summary": "A country..."}

        cache.set("wikipedia", params, result)
        cached = cache.get("wikipedia", params)

        assert cached == result

    def test_cache_hit(self, cache):
        """Cached result returned for same params."""
        params = {"query": "France"}
        result = {"data": "test"}

        cache.set("wikipedia", params, result)

        # Second get should return cached
        cached = cache.get("wikipedia", params)
        assert cached == result

    def test_cache_miss_different_params(self, cache):
        """Different params returns None."""
        params1 = {"query": "France"}
        params2 = {"query": "Germany"}
        result = {"data": "test"}

        cache.set("wikipedia", params1, result)

        cached = cache.get("wikipedia", params2)
        assert cached is None

    def test_cache_miss_different_tool(self, cache):
        """Different tool name returns None."""
        params = {"query": "France"}
        result = {"data": "test"}

        cache.set("wikipedia", params, result)

        cached = cache.get("web_search", params)
        assert cached is None

    def test_cache_expiration(self, cache):
        """Expired cache returns None."""
        params = {"query": "test"}
        result = {"data": "test"}

        # Manually set with old timestamp
        params_hash = cache._hash_params(params)
        key = f"web_search:{params_hash}"
        old_time = datetime.now() - timedelta(minutes=10)  # web_search TTL is 5 min
        cache._cache[key] = (result, old_time)
        cache._access_order.append(key)

        cached = cache.get("web_search", params)
        assert cached is None
        assert key not in cache._cache

    def test_ttl_wikipedia(self, cache):
        """Wikipedia has 30 minute TTL."""
        assert cache.TTL.get("wikipedia") == timedelta(minutes=30)

    def test_ttl_calculator(self, cache):
        """Calculator has 1 hour TTL."""
        assert cache.TTL.get("calculator") == timedelta(hours=1)

    def test_ttl_web_search(self, cache):
        """Web search has 5 minute TTL."""
        assert cache.TTL.get("web_search") == timedelta(minutes=5)

    def test_max_size_eviction(self, cache):
        """Cache evicts old entries when full."""
        # Set max size to small value for testing
        cache.MAX_SIZE = 3

        for i in range(5):
            params = {"query": f"query_{i}"}
            cache.set("wikipedia", params, {"result": i})

        # Should only have 3 entries
        assert len(cache._cache) <= 3

        # Most recent should still be there
        latest = cache.get("wikipedia", {"query": "query_4"})
        assert latest is not None

    def test_lru_access_order(self, cache):
        """Cache updates access order on get."""
        params1 = {"query": "first"}
        params2 = {"query": "second"}

        cache.set("wikipedia", params1, {"data": 1})
        cache.set("wikipedia", params2, {"data": 2})

        # Access first again
        cache.get("wikipedia", params1)

        # First should be at end of access order
        hash1 = cache._hash_params(params1)
        key1 = f"wikipedia:{hash1}"
        assert cache._access_order[-1] == key1

    def test_hash_params_consistency(self, cache):
        """Same params always produce same hash."""
        params = {"a": 1, "b": "test", "c": [1, 2, 3]}

        hash1 = cache._hash_params(params)
        hash2 = cache._hash_params(params)

        assert hash1 == hash2

    def test_hash_params_order_independent(self, cache):
        """Param order doesn't affect hash."""
        params1 = {"a": 1, "b": 2}
        params2 = {"b": 2, "a": 1}

        hash1 = cache._hash_params(params1)
        hash2 = cache._hash_params(params2)

        assert hash1 == hash2

    def test_unhashable_params_returns_none(self, cache):
        """Unhashable params return None for hash."""
        # This would fail JSON serialization
        class CustomObj:
            pass

        params = {"obj": CustomObj()}
        hash_result = cache._hash_params(params)
        assert hash_result is None

    def test_clear(self, cache):
        """Clear removes all entries."""
        cache.set("wikipedia", {"q": "1"}, {"data": 1})
        cache.set("wikipedia", {"q": "2"}, {"data": 2})

        cache.clear()

        assert len(cache._cache) == 0
        assert len(cache._access_order) == 0

    def test_stats(self, cache):
        """Stats returns cache information."""
        cache.set("wikipedia", {"q": "1"}, {"data": 1})
        cache.set("wikipedia", {"q": "2"}, {"data": 2})

        stats = cache.stats()

        assert stats["size"] == 2
        assert stats["max_size"] == cache.MAX_SIZE
        assert len(stats["keys"]) == 2


class TestToolCacheSingleton:
    """Tests for global cache singleton."""

    def test_get_tool_cache_returns_singleton(self):
        """get_tool_cache returns same instance."""
        if get_tool_cache is None:
            pytest.skip("get_tool_cache not available")

        cache1 = get_tool_cache()
        cache2 = get_tool_cache()

        assert cache1 is cache2

    def test_reset_tool_cache_creates_new_instance(self):
        """reset_tool_cache creates new instance."""
        if get_tool_cache is None or reset_tool_cache is None:
            pytest.skip("Functions not available")

        cache1 = get_tool_cache()
        reset_tool_cache()
        cache2 = get_tool_cache()

        assert cache1 is not cache2
