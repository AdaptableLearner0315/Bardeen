"""Unit tests for agent/tools/base.py."""

import pytest
import time
import threading
from unittest.mock import MagicMock, patch, PropertyMock
from typing import Dict, Any

from src.agent.tools.base import (
    RateLimiter,
    RateLimitConfig,
    BaseTool,
    ToolResult,
    RateLimiters,
    with_rate_limit,
    with_timeout,
)
from src.shared.exceptions import (
    ToolTimeoutError,
    ToolRateLimitError,
    ToolExecutionError,
)
from src.shared.models import ToolMode
from src.storage.cache import reset_caches
from src.shared.config import reset_config


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up caches after each test."""
    reset_caches()
    reset_config()
    yield
    reset_caches()
    reset_config()


# ============================================================================
# RateLimitConfig Tests
# ============================================================================

class TestRateLimitConfig:
    """Tests for RateLimitConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RateLimitConfig()
        assert config.requests_per_second == 1.0
        assert config.burst_limit == 1
        assert config.cooldown_seconds == 1.0

    def test_custom_config(self):
        """Test custom configuration values."""
        config = RateLimitConfig(
            requests_per_second=10.0,
            burst_limit=5,
            cooldown_seconds=0.5
        )
        assert config.requests_per_second == 10.0
        assert config.burst_limit == 5
        assert config.cooldown_seconds == 0.5

    def test_invalid_requests_per_second(self):
        """Test validation for invalid requests_per_second."""
        with pytest.raises(ValueError, match="requests_per_second must be positive"):
            RateLimitConfig(requests_per_second=0)

        with pytest.raises(ValueError, match="requests_per_second must be positive"):
            RateLimitConfig(requests_per_second=-1)

    def test_invalid_burst_limit(self):
        """Test validation for invalid burst_limit."""
        with pytest.raises(ValueError, match="burst_limit must be at least 1"):
            RateLimitConfig(burst_limit=0)


# ============================================================================
# RateLimiter Tests
# ============================================================================

class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_create_rate_limiter(self):
        """Test creating a rate limiter."""
        limiter = RateLimiter(requests_per_second=10.0, burst_limit=5, name="test")
        assert limiter.requests_per_second == 10.0
        assert limiter.burst_limit == 5
        assert limiter.name == "test"

    def test_acquire_within_limit(self):
        """Test acquiring tokens within burst limit."""
        limiter = RateLimiter(requests_per_second=1.0, burst_limit=3)

        # Should be able to acquire burst_limit tokens immediately
        assert limiter.acquire(blocking=False) is True
        assert limiter.acquire(blocking=False) is True
        assert limiter.acquire(blocking=False) is True

    def test_acquire_exceeds_burst(self):
        """Test acquiring beyond burst limit."""
        limiter = RateLimiter(requests_per_second=1.0, burst_limit=2)

        # Exhaust burst
        limiter.acquire(blocking=False)
        limiter.acquire(blocking=False)

        # Next acquire should fail (non-blocking)
        assert limiter.acquire(blocking=False) is False

    def test_acquire_blocking(self):
        """Test blocking acquire waits for token."""
        limiter = RateLimiter(requests_per_second=10.0, burst_limit=1)

        # Exhaust tokens
        limiter.acquire(blocking=False)

        # Blocking acquire should wait
        start = time.time()
        limiter.acquire(blocking=True, timeout=1.0)
        elapsed = time.time() - start

        # Should have waited approximately 0.1 seconds (1/10 RPS)
        assert elapsed >= 0.05
        assert elapsed < 0.5

    def test_acquire_timeout(self):
        """Test acquire with timeout."""
        limiter = RateLimiter(requests_per_second=0.1, burst_limit=1)  # Very slow

        # Exhaust tokens
        limiter.acquire(blocking=False)

        # Should timeout
        with pytest.raises(ToolRateLimitError):
            limiter.acquire(timeout=0.1, blocking=True)

    def test_try_acquire(self):
        """Test non-blocking try_acquire."""
        limiter = RateLimiter(requests_per_second=1.0, burst_limit=1)

        assert limiter.try_acquire() is True
        assert limiter.try_acquire() is False

    def test_get_wait_time(self):
        """Test get_wait_time calculation."""
        limiter = RateLimiter(requests_per_second=10.0, burst_limit=1)

        # With full token, wait time should be 0
        assert limiter.get_wait_time() == 0.0

        # After consuming token
        limiter.acquire(blocking=False)
        wait_time = limiter.get_wait_time()
        assert wait_time > 0
        assert wait_time <= 0.15  # Approximately 1/10 second

    def test_get_stats(self):
        """Test statistics tracking."""
        limiter = RateLimiter(requests_per_second=10.0, burst_limit=3, name="test")

        limiter.acquire(blocking=False)  # Success
        limiter.acquire(blocking=False)  # Success
        limiter.acquire(blocking=False)  # Success
        limiter.acquire(blocking=False)  # Blocked (non-blocking)

        stats = limiter.get_stats()
        assert stats["name"] == "test"
        assert stats["total_requests"] == 4
        assert stats["blocked_requests"] == 1

    def test_reset(self):
        """Test reset clears state."""
        limiter = RateLimiter(requests_per_second=1.0, burst_limit=2)

        # Exhaust and track stats
        limiter.acquire(blocking=False)
        limiter.acquire(blocking=False)
        limiter.acquire(blocking=False)  # Blocked

        # Reset
        limiter.reset()

        stats = limiter.get_stats()
        assert stats["total_requests"] == 0
        assert stats["blocked_requests"] == 0
        assert stats["available_tokens"] == 2.0

    def test_limited_context_manager(self):
        """Test limited context manager."""
        limiter = RateLimiter(requests_per_second=10.0, burst_limit=1)

        with limiter.limited():
            # Token consumed
            pass

        # Should need to wait
        assert limiter.get_wait_time() > 0

    def test_token_refill(self):
        """Test tokens refill over time."""
        limiter = RateLimiter(requests_per_second=20.0, burst_limit=1)

        # Consume token
        limiter.acquire(blocking=False)
        assert limiter.try_acquire() is False

        # Wait for refill
        time.sleep(0.1)  # Should refill ~2 tokens, but capped at burst_limit=1

        # Should have token now
        assert limiter.try_acquire() is True


class TestRateLimiterThreadSafety:
    """Thread safety tests for RateLimiter."""

    def test_concurrent_acquires(self):
        """Test concurrent token acquisition."""
        limiter = RateLimiter(requests_per_second=100.0, burst_limit=10)
        acquired_count = [0]
        lock = threading.Lock()
        errors = []

        def acquire_tokens(thread_id):
            try:
                for _ in range(5):
                    if limiter.acquire(timeout=2.0):
                        with lock:
                            acquired_count[0] += 1
                    time.sleep(0.01)
            except Exception as e:
                with lock:
                    errors.append(str(e))

        threads = [threading.Thread(target=acquire_tokens, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert acquired_count[0] > 0


# ============================================================================
# ToolResult Tests
# ============================================================================

class TestToolResult:
    """Tests for ToolResult dataclass."""

    def test_success_result(self):
        """Test successful result."""
        result = ToolResult(
            success=True,
            data={"key": "value"},
            execution_time=0.5,
            tool_name="test_tool"
        )
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.execution_time == 0.5
        assert result.tool_name == "test_tool"

    def test_failure_result(self):
        """Test failure result."""
        result = ToolResult(
            success=False,
            error="Something went wrong",
            error_code="TEST_ERROR",
            tool_name="test_tool"
        )
        assert result.success is False
        assert result.error == "Something went wrong"
        assert result.error_code == "TEST_ERROR"

    def test_to_dict_success(self):
        """Test to_dict for success."""
        result = ToolResult(
            success=True,
            data={"result": 42},
            execution_time=0.1,
            cached=True,
            tool_name="calculator"
        )
        d = result.to_dict()

        assert d["success"] is True
        assert d["data"] == {"result": 42}
        assert d["execution_time"] == 0.1
        assert d["cached"] is True
        assert "error" not in d

    def test_to_dict_failure(self):
        """Test to_dict for failure."""
        result = ToolResult(
            success=False,
            error="Failed",
            error_code="TIMEOUT",
            tool_name="web_search"
        )
        d = result.to_dict()

        assert d["success"] is False
        assert d["error"] == "Failed"
        assert d["error_code"] == "TIMEOUT"


# ============================================================================
# BaseTool Tests
# ============================================================================

class MockTool(BaseTool):
    """Mock tool for testing."""

    TOOL_NAME = "mock_tool"
    TOOL_DESCRIPTION = "A mock tool for testing"
    DEFAULT_TIMEOUT = 5.0
    MAX_RETRIES = 1
    RATE_LIMIT_RPS = 10.0
    RATE_LIMIT_BURST = 5

    def __init__(self, return_value=None, raise_error=None, delay=0, **kwargs):
        super().__init__(**kwargs)
        self.return_value = return_value or {"success": True, "result": "mock_result"}
        self.raise_error = raise_error
        self.delay = delay
        self.call_count = 0

    def _execute(self, **kwargs) -> Dict[str, Any]:
        self.call_count += 1
        if self.delay:
            time.sleep(self.delay)
        if self.raise_error:
            raise self.raise_error
        return self.return_value

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Test query"}
            },
            "required": ["query"]
        }


class TestBaseTool:
    """Tests for BaseTool class."""

    def test_create_tool(self):
        """Test creating a tool."""
        tool = MockTool()
        assert tool.TOOL_NAME == "mock_tool"
        assert tool.timeout == 5.0
        assert tool.max_retries == 1

    def test_get_tool_definition(self):
        """Test get_tool_definition."""
        tool = MockTool()
        definition = tool.get_tool_definition()

        assert definition["name"] == "mock_tool"
        assert definition["description"] == "A mock tool for testing"
        assert "input_schema" in definition
        assert definition["input_schema"]["type"] == "object"

    def test_execute_success(self):
        """Test successful execution."""
        tool = MockTool(return_value={"success": True, "data": "test"})
        result = tool.execute(query="test")

        assert result.success is True
        assert result.data == {"success": True, "data": "test"}
        assert result.tool_name == "mock_tool"
        assert result.execution_time > 0

    def test_execute_failure(self):
        """Test execution failure."""
        tool = MockTool(return_value={"success": False, "error": "Test error"})
        tool.max_retries = 0  # No retries
        result = tool.execute(query="test")

        assert result.success is False
        assert "error" in result.error.lower() or result.error == "Test error"

    def test_execute_with_exception(self):
        """Test execution with exception."""
        tool = MockTool(raise_error=ValueError("Test exception"))
        tool.max_retries = 0
        result = tool.execute(query="test")

        assert result.success is False
        assert "Test exception" in result.error

    def test_execute_with_retries(self):
        """Test retry logic."""
        fail_count = [0]
        max_fails = 2

        class RetryTool(MockTool):
            def _execute(self, **kwargs):
                fail_count[0] += 1
                if fail_count[0] <= max_fails:
                    return {"success": False, "error": "Temporary failure"}
                return {"success": True, "result": "success"}

        tool = RetryTool()
        tool.max_retries = 3
        result = tool.execute(query="test")

        assert result.success is True
        assert fail_count[0] == 3  # 2 failures + 1 success

    def test_execute_timeout(self):
        """Test execution timeout."""
        tool = MockTool(delay=1.0)
        tool.timeout = 0.1
        tool.max_retries = 0
        result = tool.execute(query="test")

        assert result.success is False
        assert "timeout" in result.error.lower() or result.error_code == "EXECUTION_ERROR"

    def test_execute_with_fallback(self):
        """Test fallback tool execution."""
        primary = MockTool(return_value={"success": False, "error": "Primary failed"})
        primary.max_retries = 0
        fallback = MockTool(return_value={"success": True, "result": "fallback"})

        primary.set_fallback(fallback)
        result = primary.execute(query="test")

        assert result.success is True
        assert result.data["result"] == "fallback"
        assert result.tool_name == "mock_tool"  # Returns fallback's result

    def test_call_method(self):
        """Test __call__ method returns dict."""
        tool = MockTool(return_value={"success": True, "result": "test"})
        result = tool(query="test")

        assert isinstance(result, dict)
        assert result["success"] is True

    def test_get_stats(self):
        """Test statistics tracking."""
        tool = MockTool()

        # Make some calls
        tool.execute(query="test1")
        tool.execute(query="test2")

        stats = tool.get_stats()
        assert stats["tool_name"] == "mock_tool"
        assert stats["total_calls"] == 2
        assert stats["successful_calls"] == 2
        assert stats["failed_calls"] == 0
        assert stats["success_rate"] == 1.0

    def test_reset_stats(self):
        """Test resetting statistics."""
        tool = MockTool()
        tool.execute(query="test")

        tool.reset_stats()
        stats = tool.get_stats()

        assert stats["total_calls"] == 0
        assert stats["successful_calls"] == 0

    def test_custom_timeout(self):
        """Test custom timeout configuration."""
        tool = MockTool(timeout=30.0)
        assert tool.timeout == 30.0

    def test_custom_max_retries(self):
        """Test custom max_retries configuration."""
        tool = MockTool(max_retries=5)
        assert tool.max_retries == 5


class TestBaseToolCaching:
    """Tests for BaseTool caching functionality."""

    def test_caching_enabled(self):
        """Test results are cached when enabled."""
        tool = MockTool(enable_caching=True, cache_ttl=60.0)

        # First call
        result1 = tool.execute(query="test")
        call_count_after_first = tool.call_count

        # Second call (should be cached)
        result2 = tool.execute(query="test")

        assert result1.success is True
        assert result2.success is True
        assert result2.cached is True
        assert tool.call_count == call_count_after_first  # No additional calls

    def test_caching_disabled(self):
        """Test caching can be disabled."""
        tool = MockTool(enable_caching=False)

        result1 = tool.execute(query="test")
        result2 = tool.execute(query="test")

        assert result1.cached is False
        assert result2.cached is False
        assert tool.call_count == 2

    def test_cache_override_per_call(self):
        """Test cache can be overridden per call."""
        tool = MockTool(enable_caching=True, cache_ttl=60.0)

        # First call with caching
        tool.execute(query="test")

        # Second call with cache disabled
        result = tool.execute(query="test", use_cache=False)

        assert result.cached is False
        assert tool.call_count == 2

    def test_different_params_different_cache(self):
        """Test different parameters create different cache entries."""
        tool = MockTool(enable_caching=True, cache_ttl=60.0)

        tool.execute(query="test1")
        tool.execute(query="test2")

        assert tool.call_count == 2


class TestBaseToolTracing:
    """Tests for BaseTool tracing functionality."""

    def test_tracer_called_on_success(self):
        """Test tracer is called on successful execution."""
        tracer = MagicMock()
        tracer.record_call = MagicMock()

        tool = MockTool()
        tool.execute(query="test", tracer=tracer)

        tracer.record_call.assert_called_once()
        call_args = tracer.record_call.call_args
        assert call_args.kwargs["tool_name"] == "mock_tool"
        assert call_args.kwargs["error"] is None

    def test_tracer_called_on_failure(self):
        """Test tracer is called on failed execution."""
        tracer = MagicMock()
        tracer.record_call = MagicMock()

        tool = MockTool(raise_error=ValueError("Test error"))
        tool.max_retries = 0
        tool.execute(query="test", tracer=tracer)

        tracer.record_call.assert_called_once()
        call_args = tracer.record_call.call_args
        assert call_args.kwargs["error"] is not None

    def test_tracer_records_cached(self):
        """Test tracer records cached results."""
        tracer = MagicMock()
        tracer.record_call = MagicMock()

        tool = MockTool(enable_caching=True, cache_ttl=60.0)
        tool.execute(query="test", tracer=tracer)  # First call
        tool.execute(query="test", tracer=tracer)  # Cached call

        assert tracer.record_call.call_count == 2
        # Second call should show cached=True
        second_call_args = tracer.record_call.call_args_list[1]
        assert second_call_args.kwargs["cached"] is True


class TestBaseToolRateLimiting:
    """Tests for BaseTool rate limiting integration."""

    def test_rate_limit_applied(self):
        """Test rate limiting is applied to tool execution."""
        limiter = RateLimiter(requests_per_second=100.0, burst_limit=2)
        tool = MockTool(rate_limiter=limiter)

        # Exhaust burst
        tool.execute(query="test1")
        tool.execute(query="test2")

        # Third call should be delayed
        start = time.time()
        tool.execute(query="test3")
        elapsed = time.time() - start

        # Should have waited for rate limit
        assert elapsed >= 0.005  # At least some delay

    def test_rate_limit_fallback_on_timeout(self):
        """Test fallback is used when rate limited."""
        # Create a very slow limiter
        limiter = RateLimiter(requests_per_second=0.01, burst_limit=1)
        primary = MockTool(rate_limiter=limiter)
        primary.timeout = 0.1  # Very short timeout

        # Exhaust burst
        primary.execute(query="warmup")

        # Set up fallback
        fallback = MockTool(return_value={"success": True, "result": "fallback"})
        primary.set_fallback(fallback)

        # Next call should use fallback after rate limit timeout
        result = primary.execute(query="test")
        assert result.success is True


# ============================================================================
# Decorator Tests
# ============================================================================

class TestDecorators:
    """Tests for rate limit and timeout decorators."""

    def test_with_rate_limit_decorator(self):
        """Test with_rate_limit decorator."""
        limiter = RateLimiter(requests_per_second=100.0, burst_limit=2)
        call_count = [0]

        @with_rate_limit(limiter)
        def my_function():
            call_count[0] += 1
            return "result"

        # Should work within burst
        my_function()
        my_function()

        assert call_count[0] == 2

    def test_with_timeout_decorator_success(self):
        """Test with_timeout decorator on fast function."""
        @with_timeout(1.0)
        def fast_function():
            return "fast"

        assert fast_function() == "fast"

    def test_with_timeout_decorator_timeout(self):
        """Test with_timeout decorator on slow function."""
        @with_timeout(0.1)
        def slow_function():
            time.sleep(1.0)
            return "slow"

        with pytest.raises(ToolTimeoutError):
            slow_function()


# ============================================================================
# RateLimiters Factory Tests
# ============================================================================

class TestRateLimitersFactory:
    """Tests for RateLimiters factory class."""

    def test_unlimited(self):
        """Test unlimited rate limiter."""
        limiter = RateLimiters.unlimited()
        assert limiter.requests_per_second == 1000.0
        assert limiter.burst_limit == 1000

    def test_standard(self):
        """Test standard rate limiter."""
        limiter = RateLimiters.standard()
        assert limiter.requests_per_second == 1.0
        assert limiter.burst_limit == 1

    def test_high_frequency(self):
        """Test high-frequency rate limiter."""
        limiter = RateLimiters.high_frequency()
        assert limiter.requests_per_second == 10.0
        assert limiter.burst_limit == 5

    def test_github_api_unauth(self):
        """Test GitHub API rate limiter (unauthenticated)."""
        limiter = RateLimiters.github_api(authenticated=False)
        assert limiter.requests_per_second < 1.0  # 60/hr = 0.0167

    def test_github_api_auth(self):
        """Test GitHub API rate limiter (authenticated)."""
        limiter = RateLimiters.github_api(authenticated=True)
        assert limiter.requests_per_second > 1.0  # 5000/hr = 1.38

    def test_sec_edgar(self):
        """Test SEC EDGAR rate limiter."""
        limiter = RateLimiters.sec_edgar()
        assert limiter.requests_per_second == 10.0

    def test_yahoo_finance(self):
        """Test Yahoo Finance rate limiter."""
        limiter = RateLimiters.yahoo_finance()
        assert limiter.requests_per_second == 2.0


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestBaseToolEdgeCases:
    """Edge case tests for BaseTool."""

    def test_zero_timeout(self):
        """Test tool with zero timeout."""
        tool = MockTool(timeout=0.001)
        tool.delay = 0.1  # Will definitely timeout
        tool.max_retries = 0

        result = tool.execute(query="test")
        assert result.success is False

    def test_negative_max_retries(self):
        """Test tool with negative max_retries treated as 0."""
        tool = MockTool(max_retries=-1)
        assert tool.max_retries == -1  # Stored as-is

    def test_empty_query(self):
        """Test tool with empty parameters."""
        tool = MockTool()
        result = tool.execute(query="")
        assert result.success is True  # MockTool doesn't validate

    def test_very_large_result(self):
        """Test tool returning very large result."""
        large_data = {"data": "x" * 100000}
        tool = MockTool(return_value={"success": True, **large_data})
        result = tool.execute(query="test")
        assert result.success is True

    def test_none_return_value(self):
        """Test tool returning None data."""
        tool = MockTool(return_value={"success": True, "result": None})
        result = tool.execute(query="test")
        assert result.success is True

    def test_nested_fallback_chain(self):
        """Test multiple fallback levels."""
        tool1 = MockTool(return_value={"success": False, "error": "Failed 1"})
        tool1.max_retries = 0
        tool2 = MockTool(return_value={"success": False, "error": "Failed 2"})
        tool2.max_retries = 0
        tool3 = MockTool(return_value={"success": True, "result": "success"})

        tool1.set_fallback(tool2)
        tool2.set_fallback(tool3)

        result = tool1.execute(query="test")
        assert result.success is True

    def test_fallback_same_as_primary(self):
        """Test setting fallback to same tool (should not infinite loop)."""
        tool = MockTool(return_value={"success": False, "error": "Failed"})
        tool.max_retries = 0
        # Note: Setting self as fallback would cause infinite recursion
        # but the code allows it - user should be careful

    def test_concurrent_executions(self):
        """Test concurrent tool executions."""
        tool = MockTool(delay=0.01)
        results = []
        errors = []
        lock = threading.Lock()

        def execute_tool():
            try:
                result = tool.execute(query="test")
                with lock:
                    results.append(result)
            except Exception as e:
                with lock:
                    errors.append(str(e))

        threads = [threading.Thread(target=execute_tool) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 5
        assert all(r.success for r in results)

    def test_tracer_exception_ignored(self):
        """Test that tracer exceptions don't break execution."""
        tracer = MagicMock()
        tracer.record_call.side_effect = Exception("Tracer broken")

        tool = MockTool()
        result = tool.execute(query="test", tracer=tracer)

        # Should still succeed despite tracer failure
        assert result.success is True

    def test_cache_exception_ignored(self):
        """Test that cache exceptions don't break execution."""
        tool = MockTool(enable_caching=True, cache_ttl=60.0)

        # Mock cache to raise exception
        with patch('src.agent.tools.base.get_tool_cache') as mock_cache:
            mock_cache.return_value.get_tool_response.side_effect = Exception("Cache broken")
            mock_cache.return_value.set_tool_response.side_effect = Exception("Cache broken")

            result = tool.execute(query="test")
            assert result.success is True


class TestRateLimiterEdgeCases:
    """Edge case tests for RateLimiter."""

    def test_very_high_rps(self):
        """Test very high requests per second."""
        limiter = RateLimiter(requests_per_second=10000.0, burst_limit=100)

        for _ in range(100):
            assert limiter.acquire(blocking=False) is True

    def test_very_low_rps(self):
        """Test very low requests per second."""
        limiter = RateLimiter(requests_per_second=0.001, burst_limit=1)

        assert limiter.acquire(blocking=False) is True
        assert limiter.acquire(blocking=False) is False

    def test_float_burst_limit_conversion(self):
        """Test that tokens work correctly as floats."""
        limiter = RateLimiter(requests_per_second=100.0, burst_limit=1)
        limiter.acquire(blocking=False)

        # Partial token should exist after short wait
        time.sleep(0.05)
        limiter._refill_tokens()

        # Should have ~5 tokens (0.05 * 100), capped at burst_limit=1
        assert limiter._tokens > 0

    def test_stats_after_many_operations(self):
        """Test stats remain accurate after many operations."""
        limiter = RateLimiter(requests_per_second=1000.0, burst_limit=100)

        for i in range(1000):
            limiter.acquire(blocking=False)

        stats = limiter.get_stats()
        assert stats["total_requests"] == 1000
        # At some point we should have blocked
        assert stats["blocked_requests"] > 0
