"""In-memory TTL cache implementation."""

import time
import threading
import logging
from typing import Optional, Any, Dict, TypeVar, Generic, Callable
from dataclasses import dataclass, field

from ..shared.config import get_config
from ..shared.exceptions import CacheError
from ..shared.utils import generate_cache_key

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """A single cache entry with value and metadata."""
    value: T
    created_at: float
    ttl_seconds: float
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)

    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        # TTL of 0 or negative means immediate expiration
        if self.ttl_seconds <= 0:
            return True
        return time.time() > (self.created_at + self.ttl_seconds)

    @property
    def age_seconds(self) -> float:
        """Get age of entry in seconds."""
        return time.time() - self.created_at


class TTLCache:
    """
    Thread-safe in-memory cache with TTL expiration and LRU eviction.

    Features:
    - Configurable TTL per entry
    - Maximum size with LRU eviction
    - Thread-safe operations
    - Negative caching (cache "not found" results)
    - Statistics tracking
    """

    def __init__(
        self,
        default_ttl: Optional[float] = None,
        max_size: Optional[int] = None,
        negative_ttl: float = 300.0  # 5 minutes for "not found" results
    ):
        """
        Initialize cache.

        Args:
            default_ttl: Default TTL in seconds (uses config if None)
            max_size: Maximum number of entries (uses config if None)
            negative_ttl: TTL for negative cache entries
        """
        config = get_config()
        self.default_ttl = default_ttl or config.storage.cache_ttl_seconds
        self.max_size = max_size or config.storage.cache_max_size
        self.negative_ttl = negative_ttl

        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()

        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Value to return if not found or expired

        Returns:
            Cached value or default
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._misses += 1
                return default

            if entry.is_expired:
                del self._cache[key]
                self._misses += 1
                logger.debug(f"Cache entry expired: {key}")
                return default

            # Update access tracking
            entry.access_count += 1
            entry.last_accessed = time.time()
            self._hits += 1

            return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None
    ) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (uses default if None)
        """
        with self._lock:
            # Evict if at max size
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()

            self._cache[key] = CacheEntry(
                value=value,
                created_at=time.time(),
                ttl_seconds=ttl if ttl is not None else self.default_ttl
            )

    def set_negative(self, key: str) -> None:
        """
        Set a negative cache entry (for "not found" results).

        Args:
            key: Cache key
        """
        self.set(key, None, ttl=self.negative_ttl)

    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.

        Args:
            key: Cache key

        Returns:
            True if entry was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def exists(self, key: str) -> bool:
        """
        Check if key exists and is not expired.

        Args:
            key: Cache key

        Returns:
            True if key exists and is valid
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            if entry.is_expired:
                del self._cache[key]
                return False
            return True

    def clear(self) -> int:
        """
        Clear all entries from cache.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache cleared: {count} entries removed")
            return count

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired
            ]
            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

            return len(expired_keys)

    def _evict_lru(self) -> None:
        """Evict the least recently used entry."""
        if not self._cache:
            return

        # Find LRU entry
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed
        )
        del self._cache[lru_key]
        self._evictions += 1
        logger.debug(f"Evicted LRU cache entry: {lru_key}")

    def get_or_set(
        self,
        key: str,
        factory: Callable[[], T],
        ttl: Optional[float] = None
    ) -> T:
        """
        Get value from cache, or compute and cache it.

        Args:
            key: Cache key
            factory: Function to compute value if not cached
            ttl: TTL in seconds

        Returns:
            Cached or computed value
        """
        # Check cache first
        value = self.get(key)
        if value is not None:
            return value

        # Compute value
        try:
            value = factory()
            self.set(key, value, ttl)
            return value
        except Exception as e:
            logger.error(f"Cache factory failed for key {key}: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "evictions": self._evictions,
                "default_ttl": self.default_ttl
            }

    def __len__(self) -> int:
        """Return number of entries in cache."""
        return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """Check if key is in cache."""
        return self.exists(key)


class ToolResponseCache(TTLCache):
    """
    Specialized cache for tool responses.

    Generates cache keys from tool name and parameters.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def make_key(self, tool_name: str, **params) -> str:
        """
        Generate cache key for a tool call.

        Args:
            tool_name: Name of the tool
            **params: Tool parameters

        Returns:
            Cache key string
        """
        return f"tool:{tool_name}:{generate_cache_key(**params)}"

    def get_tool_response(
        self,
        tool_name: str,
        default: Any = None,
        **params
    ) -> Any:
        """
        Get cached tool response.

        Args:
            tool_name: Name of the tool
            default: Default value if not cached
            **params: Tool parameters

        Returns:
            Cached response or default
        """
        key = self.make_key(tool_name, **params)
        return self.get(key, default)

    def set_tool_response(
        self,
        tool_name: str,
        response: Any,
        ttl: Optional[float] = None,
        **params
    ) -> None:
        """
        Cache a tool response.

        Args:
            tool_name: Name of the tool
            response: Response to cache
            ttl: TTL in seconds
            **params: Tool parameters
        """
        key = self.make_key(tool_name, **params)
        self.set(key, response, ttl)

    def invalidate_tool(self, tool_name: str) -> int:
        """
        Invalidate all cached responses for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Number of entries invalidated
        """
        prefix = f"tool:{tool_name}:"
        with self._lock:
            keys_to_delete = [
                key for key in self._cache.keys()
                if key.startswith(prefix)
            ]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)


# Singleton instances
_cache: Optional[TTLCache] = None
_tool_cache: Optional[ToolResponseCache] = None


def get_cache() -> TTLCache:
    """Get singleton cache instance."""
    global _cache
    if _cache is None:
        _cache = TTLCache()
    return _cache


def get_tool_cache() -> ToolResponseCache:
    """Get singleton tool response cache instance."""
    global _tool_cache
    if _tool_cache is None:
        _tool_cache = ToolResponseCache()
    return _tool_cache


def reset_caches() -> None:
    """Reset all cache singletons (for testing)."""
    global _cache, _tool_cache
    if _cache:
        _cache.clear()
    if _tool_cache:
        _tool_cache.clear()
    _cache = None
    _tool_cache = None
