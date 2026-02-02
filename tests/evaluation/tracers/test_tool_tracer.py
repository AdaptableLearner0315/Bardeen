"""Tests for tool tracer module."""

import pytest
import time
from unittest.mock import Mock

from src.evaluation.tracers.tool_tracer import ToolTracer, TraceHelper
from src.shared.models import ToolCallTrace, ToolStatus


class TestToolTracer:
    """Tests for ToolTracer class."""

    def test_initialization(self):
        """Test basic initialization."""
        tracer = ToolTracer(attempt_number=1)
        assert tracer.attempt_number == 1
        assert tracer.traces == []

    def test_trace_tool_call_success(self):
        """Test tracing a successful tool call."""
        tracer = ToolTracer(attempt_number=1)

        with tracer.trace_tool_call("calculator", {"expression": "2+2"}) as trace:
            trace.result = {"answer": 4}

        assert len(tracer.traces) == 1
        assert tracer.traces[0].tool_name == "calculator"
        assert tracer.traces[0].params == {"expression": "2+2"}
        assert tracer.traces[0].result == {"answer": 4}
        assert tracer.traces[0].status == ToolStatus.SUCCESS
        assert tracer.traces[0].latency_ms > 0

    def test_trace_tool_call_with_reasoning(self):
        """Test tracing with LLM reasoning."""
        tracer = ToolTracer(attempt_number=1)

        with tracer.trace_tool_call(
            "web_search",
            {"query": "python"},
            llm_reasoning="User asked about Python programming"
        ) as trace:
            trace.result = {"results": []}

        assert tracer.traces[0].llm_reasoning == "User asked about Python programming"

    def test_trace_tool_call_timeout_error(self):
        """Test tracing a timeout error."""
        tracer = ToolTracer(attempt_number=1)

        with tracer.trace_tool_call("web_search", {"query": "test"}) as trace:
            raise TimeoutError("Request timed out")

        assert tracer.traces[0].status == ToolStatus.TIMEOUT
        assert "timed out" in tracer.traces[0].error

    def test_trace_tool_call_value_error(self):
        """Test tracing an invalid params error."""
        tracer = ToolTracer(attempt_number=1)

        with tracer.trace_tool_call("calculator", {"expression": "invalid"}) as trace:
            raise ValueError("Invalid expression")

        assert tracer.traces[0].status == ToolStatus.INVALID_PARAMS
        assert "Invalid" in tracer.traces[0].error

    def test_trace_tool_call_generic_error(self):
        """Test tracing a generic error."""
        tracer = ToolTracer(attempt_number=1)

        with tracer.trace_tool_call("wikipedia", {"query": "test"}) as trace:
            raise RuntimeError("Network error")

        assert tracer.traces[0].status == ToolStatus.ERROR
        assert "Network error" in tracer.traces[0].error

    def test_trace_multiple_calls(self):
        """Test tracing multiple tool calls."""
        tracer = ToolTracer(attempt_number=1)

        with tracer.trace_tool_call("web_search", {"query": "q1"}) as trace:
            trace.result = {"results": ["r1"]}

        with tracer.trace_tool_call("wikipedia", {"query": "q2"}) as trace:
            trace.result = {"summary": "s2"}

        with tracer.trace_tool_call("calculator", {"expression": "2+2"}) as trace:
            trace.result = {"result": 4}

        assert len(tracer.traces) == 3
        assert tracer.traces[0].tool_name == "web_search"
        assert tracer.traces[1].tool_name == "wikipedia"
        assert tracer.traces[2].tool_name == "calculator"

    def test_trace_latency_measurement(self):
        """Test that latency is measured correctly."""
        tracer = ToolTracer(attempt_number=1)

        with tracer.trace_tool_call("slow_tool", {}) as trace:
            time.sleep(0.05)  # 50ms
            trace.result = "done"

        # Should be at least 50ms
        assert tracer.traces[0].latency_ms >= 50

    def test_get_traces(self):
        """Test getting all traces."""
        tracer = ToolTracer(attempt_number=1)

        with tracer.trace_tool_call("tool1", {}) as trace:
            trace.result = "r1"
        with tracer.trace_tool_call("tool2", {}) as trace:
            trace.result = "r2"

        traces = tracer.get_traces()
        assert len(traces) == 2
        assert traces is tracer.traces  # Same object

    def test_get_tool_distribution(self):
        """Test getting tool call distribution."""
        tracer = ToolTracer(attempt_number=1)

        for _ in range(3):
            with tracer.trace_tool_call("web_search", {}) as trace:
                trace.result = {}
        for _ in range(2):
            with tracer.trace_tool_call("calculator", {}) as trace:
                trace.result = {}
        with tracer.trace_tool_call("wikipedia", {}) as trace:
            trace.result = {}

        distribution = tracer.get_tool_distribution()
        assert distribution["web_search"] == 3
        assert distribution["calculator"] == 2
        assert distribution["wikipedia"] == 1

    def test_get_error_rate_no_errors(self):
        """Test error rate when no errors."""
        tracer = ToolTracer(attempt_number=1)

        for _ in range(5):
            with tracer.trace_tool_call("tool", {}) as trace:
                trace.result = {}

        assert tracer.get_error_rate() == 0.0

    def test_get_error_rate_some_errors(self):
        """Test error rate with some errors."""
        tracer = ToolTracer(attempt_number=1)

        # 3 successful
        for _ in range(3):
            with tracer.trace_tool_call("tool", {}) as trace:
                trace.result = {}

        # 2 errors
        for _ in range(2):
            with tracer.trace_tool_call("tool", {}) as trace:
                raise RuntimeError("Error")

        assert tracer.get_error_rate() == 0.4  # 2/5

    def test_get_error_rate_empty(self):
        """Test error rate when no traces."""
        tracer = ToolTracer(attempt_number=1)
        assert tracer.get_error_rate() == 0.0

    def test_get_error_rate_by_tool(self):
        """Test error rate calculation by tool."""
        tracer = ToolTracer(attempt_number=1)

        # web_search: 2 success, 1 error
        for _ in range(2):
            with tracer.trace_tool_call("web_search", {}) as trace:
                trace.result = {}
        with tracer.trace_tool_call("web_search", {}) as trace:
            raise RuntimeError("Error")

        # calculator: all success
        for _ in range(3):
            with tracer.trace_tool_call("calculator", {}) as trace:
                trace.result = {}

        error_rates = tracer.get_error_rate_by_tool()
        assert error_rates["web_search"] == pytest.approx(1/3)
        assert error_rates["calculator"] == 0.0

    def test_get_avg_latency(self):
        """Test average latency calculation."""
        tracer = ToolTracer(attempt_number=1)

        # Create traces with known latencies by setting latency directly
        with tracer.trace_tool_call("tool", {}) as trace:
            trace.result = {}
        tracer.traces[0].latency_ms = 100

        with tracer.trace_tool_call("tool", {}) as trace:
            trace.result = {}
        tracer.traces[1].latency_ms = 200

        with tracer.trace_tool_call("tool", {}) as trace:
            trace.result = {}
        tracer.traces[2].latency_ms = 300

        assert tracer.get_avg_latency() == 200

    def test_get_avg_latency_empty(self):
        """Test average latency when no traces."""
        tracer = ToolTracer(attempt_number=1)
        assert tracer.get_avg_latency() == 0.0

    def test_get_total_latency(self):
        """Test total latency calculation."""
        tracer = ToolTracer(attempt_number=1)

        with tracer.trace_tool_call("tool", {}) as trace:
            trace.result = {}
        tracer.traces[0].latency_ms = 100

        with tracer.trace_tool_call("tool", {}) as trace:
            trace.result = {}
        tracer.traces[1].latency_ms = 200

        assert tracer.get_total_latency() == 300

    def test_trace_generates_unique_ids(self):
        """Test that each trace gets a unique ID."""
        tracer = ToolTracer(attempt_number=1)

        for _ in range(10):
            with tracer.trace_tool_call("tool", {}) as trace:
                trace.result = {}

        ids = [t.call_id for t in tracer.traces]
        assert len(set(ids)) == 10  # All unique

    def test_trace_includes_timestamp(self):
        """Test that traces include timestamp."""
        tracer = ToolTracer(attempt_number=1)

        with tracer.trace_tool_call("tool", {}) as trace:
            trace.result = {}

        assert tracer.traces[0].timestamp is not None
        assert len(tracer.traces[0].timestamp) > 0


class TestTraceHelper:
    """Tests for TraceHelper class."""

    def test_set_result(self):
        """Test setting result on trace."""
        trace = ToolCallTrace(
            call_id="test",
            attempt_number=1,
            tool_name="tool",
            params={},
            result=None,
            error=None,
            status=ToolStatus.SUCCESS,
            latency_ms=0.0,
            timestamp="",
            llm_reasoning=None,
            recovery_action=None
        )

        TraceHelper.set_result(trace, {"answer": 42})

        assert trace.result == {"answer": 42}
        assert trace.status == ToolStatus.SUCCESS

    def test_set_error(self):
        """Test setting error on trace."""
        trace = ToolCallTrace(
            call_id="test",
            attempt_number=1,
            tool_name="tool",
            params={},
            result=None,
            error=None,
            status=ToolStatus.SUCCESS,
            latency_ms=0.0,
            timestamp="",
            llm_reasoning=None,
            recovery_action=None
        )

        TraceHelper.set_error(trace, "Connection failed", ToolStatus.ERROR)

        assert trace.error == "Connection failed"
        assert trace.status == ToolStatus.ERROR

    def test_set_error_with_recovery(self):
        """Test setting error with recovery action."""
        trace = ToolCallTrace(
            call_id="test",
            attempt_number=1,
            tool_name="tool",
            params={},
            result=None,
            error=None,
            status=ToolStatus.SUCCESS,
            latency_ms=0.0,
            timestamp="",
            llm_reasoning=None,
            recovery_action=None
        )

        TraceHelper.set_error(
            trace,
            "API error",
            ToolStatus.ERROR,
            recovery_action="retry_with_backoff"
        )

        assert trace.recovery_action == "retry_with_backoff"

    def test_set_fallback(self):
        """Test setting fallback status."""
        trace = ToolCallTrace(
            call_id="test",
            attempt_number=1,
            tool_name="web_search",
            params={},
            result=None,
            error=None,
            status=ToolStatus.SUCCESS,
            latency_ms=0.0,
            timestamp="",
            llm_reasoning=None,
            recovery_action=None
        )

        TraceHelper.set_fallback(trace, "wikipedia")

        assert trace.status == ToolStatus.FALLBACK
        assert trace.recovery_action == "fallback_to_wikipedia"


class TestToolTracerAttemptNumbers:
    """Tests for attempt number handling."""

    def test_different_attempt_numbers(self):
        """Test tracers with different attempt numbers."""
        tracer1 = ToolTracer(attempt_number=1)
        tracer2 = ToolTracer(attempt_number=2)

        with tracer1.trace_tool_call("tool", {}) as trace:
            trace.result = {}
        with tracer2.trace_tool_call("tool", {}) as trace:
            trace.result = {}

        assert tracer1.traces[0].attempt_number == 1
        assert tracer2.traces[0].attempt_number == 2

    def test_attempt_number_in_traces(self):
        """Test that attempt number is included in all traces."""
        tracer = ToolTracer(attempt_number=5)

        for _ in range(3):
            with tracer.trace_tool_call("tool", {}) as trace:
                trace.result = {}

        for t in tracer.traces:
            assert t.attempt_number == 5
