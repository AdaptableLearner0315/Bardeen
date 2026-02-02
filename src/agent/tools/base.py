"""Base tool implementation with rate limiting and common functionality."""

import time
import logging
import threading
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from functools import wraps
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from ...shared.exceptions import (
    ToolExecutionError,
    ToolTimeoutError,
    ToolRateLimitError,
    ToolNotFoundError,
)
from ...shared.models import ToolCall, ToolStatus, ToolMode
from ...storage.cache import get_tool_cache

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_second: float = 1.0
    burst_limit: int = 1
    cooldown_seconds: float = 1.0

    def __post_init__(self):
        if self.requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")
        if self.burst_limit < 1:
            raise ValueError("burst_limit must be at least 1")


class RateLimiter:
    """
    Thread-safe rate limiter using token bucket algorithm.

    Features:
    - Configurable requests per second
    - Burst capacity for handling spikes
    - Thread-safe operations
    - Blocking and non-blocking modes
    """

    def __init__(
        self,
        requests_per_second: float = 1.0,
        burst_limit: int = 1,
        name: str = "default"
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Maximum sustained request rate
            burst_limit: Maximum burst capacity (tokens)
            name: Identifier for logging
        """
        self.requests_per_second = requests_per_second
        self.burst_limit = burst_limit
        self.name = name

        # Token bucket state
        self._tokens = float(burst_limit)
        self._last_update = time.monotonic()
        self._lock = threading.RLock()

        # Statistics
        self._total_requests = 0
        self._blocked_requests = 0
        self._total_wait_time = 0.0

    def acquire(self, timeout: Optional[float] = None, blocking: bool = True) -> bool:
        """
        Acquire a token from the rate limiter.

        Args:
            timeout: Maximum time to wait for a token (None = unlimited)
            blocking: If True, wait for token; if False, return immediately

        Returns:
            True if token acquired, False if would block and blocking=False

        Raises:
            ToolRateLimitError: If timeout exceeded while waiting
        """
        start_time = time.monotonic()
        deadline = start_time + timeout if timeout else None

        with self._lock:
            self._total_requests += 1

            while True:
                self._refill_tokens()

                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return True

                if not blocking:
                    self._blocked_requests += 1
                    return False

                # Calculate wait time
                tokens_needed = 1.0 - self._tokens
                wait_time = tokens_needed / self.requests_per_second

                # Check deadline
                if deadline is not None:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        self._blocked_requests += 1
                        raise ToolRateLimitError(
                            tool_name=self.name,
                            retry_after_seconds=wait_time
                        )
                    wait_time = min(wait_time, remaining)

                self._total_wait_time += wait_time

                # Release lock while sleeping
                self._lock.release()
                try:
                    time.sleep(wait_time)
                finally:
                    self._lock.acquire()

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_update
        self._last_update = now

        # Add tokens based on elapsed time
        self._tokens = min(
            self.burst_limit,
            self._tokens + elapsed * self.requests_per_second
        )

    def try_acquire(self) -> bool:
        """
        Try to acquire a token without blocking.

        Returns:
            True if token acquired, False otherwise
        """
        return self.acquire(blocking=False)

    def get_wait_time(self) -> float:
        """
        Get estimated wait time for next available token.

        Returns:
            Seconds until a token is available (0 if available now)
        """
        with self._lock:
            self._refill_tokens()
            if self._tokens >= 1.0:
                return 0.0
            tokens_needed = 1.0 - self._tokens
            return tokens_needed / self.requests_per_second

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        with self._lock:
            self._refill_tokens()
            return {
                "name": self.name,
                "requests_per_second": self.requests_per_second,
                "burst_limit": self.burst_limit,
                "available_tokens": self._tokens,
                "total_requests": self._total_requests,
                "blocked_requests": self._blocked_requests,
                "total_wait_time": self._total_wait_time,
                "block_rate": (
                    self._blocked_requests / self._total_requests
                    if self._total_requests > 0 else 0.0
                )
            }

    def reset(self) -> None:
        """Reset rate limiter to initial state."""
        with self._lock:
            self._tokens = float(self.burst_limit)
            self._last_update = time.monotonic()
            self._total_requests = 0
            self._blocked_requests = 0
            self._total_wait_time = 0.0

    @contextmanager
    def limited(self, timeout: Optional[float] = None):
        """
        Context manager for rate-limited operations.

        Usage:
            with rate_limiter.limited(timeout=5.0):
                # rate-limited operation
        """
        self.acquire(timeout=timeout)
        try:
            yield
        finally:
            pass  # Token already consumed


@dataclass
class ToolResult:
    """Standard result from a tool execution."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    execution_time: float = 0.0
    cached: bool = False
    tool_name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "success": self.success,
            "data": self.data,
            "execution_time": self.execution_time,
            "cached": self.cached,
            "tool_name": self.tool_name,
        }
        if self.error:
            result["error"] = self.error
        if self.error_code:
            result["error_code"] = self.error_code
        return result


class BaseTool(ABC):
    """
    Abstract base class for all tools.

    Provides common functionality:
    - Rate limiting
    - Timeout handling
    - Error handling with retries
    - Caching
    - Tracing support
    - Fallback chain support
    """

    # Class-level configuration
    TOOL_NAME: str = "base_tool"
    TOOL_DESCRIPTION: str = "Base tool description"
    TOOL_MODE: ToolMode = ToolMode.CORE
    DEFAULT_TIMEOUT: float = 10.0
    MAX_RETRIES: int = 2
    CACHE_TTL: Optional[float] = None  # None = use default, 0 = no caching

    # Rate limit defaults (can be overridden per tool)
    RATE_LIMIT_RPS: float = 1.0
    RATE_LIMIT_BURST: int = 1

    def __init__(
        self,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        rate_limiter: Optional[RateLimiter] = None,
        enable_caching: bool = True,
        cache_ttl: Optional[float] = None,
    ):
        """
        Initialize base tool.

        Args:
            timeout: Execution timeout in seconds
            max_retries: Maximum retry attempts on failure
            rate_limiter: Optional rate limiter instance
            enable_caching: Whether to cache results
            cache_ttl: Cache TTL in seconds (None = use default)
        """
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.max_retries = max_retries if max_retries is not None else self.MAX_RETRIES
        self.enable_caching = enable_caching
        self.cache_ttl = cache_ttl if cache_ttl is not None else self.CACHE_TTL

        # Set up rate limiter
        self._rate_limiter = rate_limiter or RateLimiter(
            requests_per_second=self.RATE_LIMIT_RPS,
            burst_limit=self.RATE_LIMIT_BURST,
            name=self.TOOL_NAME
        )

        # Execution statistics
        self._total_calls = 0
        self._successful_calls = 0
        self._failed_calls = 0
        self._cached_calls = 0
        self._total_execution_time = 0.0
        self._stats_lock = threading.Lock()

        # Fallback chain
        self._fallback_tool: Optional['BaseTool'] = None

        # Thread pool for timeout handling
        self._executor = ThreadPoolExecutor(max_workers=1)

    @abstractmethod
    def _execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool's core logic.

        Subclasses must implement this method.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            Dictionary with tool results
        """
        pass

    @abstractmethod
    def get_input_schema(self) -> Dict[str, Any]:
        """
        Get JSON schema for tool input parameters.

        Returns:
            JSON Schema dict describing expected inputs
        """
        pass

    def execute(
        self,
        tracer: Optional[Any] = None,
        use_cache: Optional[bool] = None,
        **kwargs
    ) -> ToolResult:
        """
        Execute the tool with full error handling and features.

        Args:
            tracer: Optional tracer for logging tool calls
            use_cache: Override cache setting for this call
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult with success/failure and data
        """
        start_time = time.time()
        use_cache = use_cache if use_cache is not None else self.enable_caching

        # Update statistics
        with self._stats_lock:
            self._total_calls += 1

        # Check cache first
        if use_cache and self.cache_ttl != 0:
            cached_result = self._get_from_cache(**kwargs)
            if cached_result is not None:
                with self._stats_lock:
                    self._cached_calls += 1
                    self._successful_calls += 1

                execution_time = time.time() - start_time

                # Trace if tracer provided
                if tracer:
                    self._trace_call(tracer, kwargs, cached_result, execution_time, cached=True)

                return ToolResult(
                    success=True,
                    data=cached_result,
                    execution_time=execution_time,
                    cached=True,
                    tool_name=self.TOOL_NAME
                )

        # Apply rate limiting
        try:
            self._rate_limiter.acquire(timeout=self.timeout)
        except ToolRateLimitError as e:
            execution_time = time.time() - start_time
            with self._stats_lock:
                self._failed_calls += 1

            if tracer:
                self._trace_call(tracer, kwargs, None, execution_time, error=str(e))

            # Try fallback if available
            if self._fallback_tool:
                logger.info(f"Rate limited on {self.TOOL_NAME}, trying fallback")
                return self._fallback_tool.execute(tracer=tracer, **kwargs)

            return ToolResult(
                success=False,
                error=str(e),
                error_code="RATE_LIMIT",
                execution_time=execution_time,
                tool_name=self.TOOL_NAME
            )

        # Execute with retries
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                result = self._execute_with_timeout(**kwargs)

                # Check for tool-level failure
                if isinstance(result, dict) and result.get("success") is False:
                    error_msg = result.get("error", "Unknown error")
                    if attempt < self.max_retries:
                        logger.warning(
                            f"{self.TOOL_NAME} attempt {attempt + 1} failed: {error_msg}"
                        )
                        time.sleep(0.5 * (attempt + 1))  # Backoff
                        continue
                    last_error = error_msg
                else:
                    # Success
                    execution_time = time.time() - start_time
                    with self._stats_lock:
                        self._successful_calls += 1
                        self._total_execution_time += execution_time

                    # Cache result
                    if use_cache and self.cache_ttl != 0:
                        self._store_in_cache(result, **kwargs)

                    # Trace
                    if tracer:
                        self._trace_call(tracer, kwargs, result, execution_time)

                    return ToolResult(
                        success=True,
                        data=result,
                        execution_time=execution_time,
                        tool_name=self.TOOL_NAME
                    )

            except ToolTimeoutError as e:
                last_error = str(e)
                if attempt < self.max_retries:
                    logger.warning(f"{self.TOOL_NAME} timeout, retrying...")
                    continue

            except Exception as e:
                last_error = str(e)
                logger.error(f"{self.TOOL_NAME} error: {e}")
                if attempt < self.max_retries:
                    time.sleep(0.5 * (attempt + 1))
                    continue

        # All retries exhausted
        execution_time = time.time() - start_time
        with self._stats_lock:
            self._failed_calls += 1
            self._total_execution_time += execution_time

        if tracer:
            self._trace_call(tracer, kwargs, None, execution_time, error=last_error)

        # Try fallback
        if self._fallback_tool:
            logger.info(f"{self.TOOL_NAME} failed, trying fallback: {self._fallback_tool.TOOL_NAME}")
            return self._fallback_tool.execute(tracer=tracer, **kwargs)

        return ToolResult(
            success=False,
            error=last_error or "Unknown error",
            error_code="EXECUTION_ERROR",
            execution_time=execution_time,
            tool_name=self.TOOL_NAME
        )

    def _execute_with_timeout(self, **kwargs) -> Dict[str, Any]:
        """Execute with timeout handling."""
        future = self._executor.submit(self._execute, **kwargs)
        try:
            return future.result(timeout=self.timeout)
        except FuturesTimeoutError:
            future.cancel()
            raise ToolTimeoutError(
                tool_name=self.TOOL_NAME,
                timeout_seconds=self.timeout
            )

    def _get_from_cache(self, **kwargs) -> Optional[Any]:
        """Get result from cache."""
        try:
            cache = get_tool_cache()
            return cache.get_tool_response(self.TOOL_NAME, **kwargs)
        except Exception as e:
            logger.debug(f"Cache lookup failed: {e}")
            return None

    def _store_in_cache(self, result: Any, **kwargs) -> None:
        """Store result in cache."""
        try:
            cache = get_tool_cache()
            cache.set_tool_response(
                self.TOOL_NAME,
                result,
                ttl=self.cache_ttl,
                **kwargs
            )
        except Exception as e:
            logger.debug(f"Cache store failed: {e}")

    def _trace_call(
        self,
        tracer: Any,
        params: Dict[str, Any],
        result: Any,
        execution_time: float,
        cached: bool = False,
        error: Optional[str] = None
    ) -> None:
        """Record tool call to tracer."""
        try:
            if hasattr(tracer, 'record_call'):
                tracer.record_call(
                    tool_name=self.TOOL_NAME,
                    params=params,
                    result=result,
                    execution_time=execution_time,
                    cached=cached,
                    error=error
                )
        except Exception as e:
            logger.debug(f"Tracing failed: {e}")

    def set_fallback(self, fallback_tool: 'BaseTool') -> None:
        """
        Set a fallback tool to use when this tool fails.

        Args:
            fallback_tool: Tool to use as fallback
        """
        self._fallback_tool = fallback_tool

    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Get tool definition for LLM tool calling.

        Returns:
            Dictionary compatible with Claude's tool format
        """
        return {
            "name": self.TOOL_NAME,
            "description": self.TOOL_DESCRIPTION,
            "input_schema": self.get_input_schema()
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get tool execution statistics."""
        with self._stats_lock:
            success_rate = (
                self._successful_calls / self._total_calls
                if self._total_calls > 0 else 0.0
            )
            avg_execution_time = (
                self._total_execution_time / self._total_calls
                if self._total_calls > 0 else 0.0
            )
            cache_hit_rate = (
                self._cached_calls / self._total_calls
                if self._total_calls > 0 else 0.0
            )

            return {
                "tool_name": self.TOOL_NAME,
                "total_calls": self._total_calls,
                "successful_calls": self._successful_calls,
                "failed_calls": self._failed_calls,
                "cached_calls": self._cached_calls,
                "success_rate": success_rate,
                "cache_hit_rate": cache_hit_rate,
                "average_execution_time": avg_execution_time,
                "total_execution_time": self._total_execution_time,
                "rate_limiter": self._rate_limiter.get_stats()
            }

    def reset_stats(self) -> None:
        """Reset execution statistics."""
        with self._stats_lock:
            self._total_calls = 0
            self._successful_calls = 0
            self._failed_calls = 0
            self._cached_calls = 0
            self._total_execution_time = 0.0
        self._rate_limiter.reset()

    def __call__(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool (convenience method).

        Returns dictionary for backward compatibility with existing tools.
        """
        result = self.execute(**kwargs)
        if result.success:
            return result.data if isinstance(result.data, dict) else {"result": result.data}
        else:
            return {
                "success": False,
                "error": result.error,
                "error_code": result.error_code
            }


def with_rate_limit(rate_limiter: RateLimiter):
    """
    Decorator to apply rate limiting to a function.

    Usage:
        @with_rate_limit(my_rate_limiter)
        def my_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            rate_limiter.acquire()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def with_timeout(timeout_seconds: float):
    """
    Decorator to apply timeout to a function.

    Usage:
        @with_timeout(10.0)
        def my_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    return future.result(timeout=timeout_seconds)
                except FuturesTimeoutError:
                    raise ToolTimeoutError(
                        tool_name=func.__name__,
                        timeout_seconds=timeout_seconds
                    )
        return wrapper
    return decorator


# Pre-configured rate limiters for common tool types
class RateLimiters:
    """Factory for common rate limiter configurations."""

    @staticmethod
    def unlimited() -> RateLimiter:
        """Rate limiter with no effective limit."""
        return RateLimiter(requests_per_second=1000.0, burst_limit=1000, name="unlimited")

    @staticmethod
    def standard() -> RateLimiter:
        """Standard rate limiter (1 req/sec)."""
        return RateLimiter(requests_per_second=1.0, burst_limit=1, name="standard")

    @staticmethod
    def high_frequency() -> RateLimiter:
        """High-frequency rate limiter (10 req/sec)."""
        return RateLimiter(requests_per_second=10.0, burst_limit=5, name="high_frequency")

    @staticmethod
    def github_api(authenticated: bool = False) -> RateLimiter:
        """GitHub API rate limiter."""
        if authenticated:
            # 5000 req/hr = ~1.38 req/sec
            return RateLimiter(requests_per_second=1.38, burst_limit=10, name="github_auth")
        else:
            # 60 req/hr = 0.0167 req/sec
            return RateLimiter(requests_per_second=0.0167, burst_limit=5, name="github_unauth")

    @staticmethod
    def sec_edgar() -> RateLimiter:
        """SEC EDGAR API rate limiter (10 req/sec max)."""
        return RateLimiter(requests_per_second=10.0, burst_limit=5, name="sec_edgar")

    @staticmethod
    def yahoo_finance() -> RateLimiter:
        """Yahoo Finance rate limiter (2 req/sec)."""
        return RateLimiter(requests_per_second=2.0, burst_limit=2, name="yahoo_finance")
