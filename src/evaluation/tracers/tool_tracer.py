"""Tool execution tracer for capturing detailed tool call information."""

import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

from ...shared.models import ToolCallTrace, ToolStatus


class ToolTracer:
    """Captures and stores traces of all tool executions."""

    def __init__(self, attempt_number: int):
        self.attempt_number = attempt_number
        self.traces: List[ToolCallTrace] = []
        self._current_trace: Optional[ToolCallTrace] = None
        self._start_time: Optional[float] = None

    @contextmanager
    def trace_tool_call(
        self,
        tool_name: str,
        params: Dict[str, Any],
        llm_reasoning: Optional[str] = None
    ):
        """
        Context manager for tracing a tool call.

        Usage:
            with tracer.trace_tool_call("web_search", {"query": "..."}) as trace:
                result = execute_tool(...)
                trace.set_result(result)
        """
        call_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # Initialize trace
        trace = ToolCallTrace(
            call_id=call_id,
            attempt_number=self.attempt_number,
            tool_name=tool_name,
            params=params,
            result=None,
            error=None,
            status=ToolStatus.SUCCESS,
            latency_ms=0.0,
            timestamp=datetime.now().isoformat(),
            llm_reasoning=llm_reasoning,
            recovery_action=None
        )

        self._current_trace = trace

        try:
            yield trace
            # If no explicit status was set, mark as success
            if trace.status == ToolStatus.SUCCESS and trace.result is not None:
                trace.status = ToolStatus.SUCCESS
        except TimeoutError as e:
            trace.status = ToolStatus.TIMEOUT
            trace.error = str(e)
        except ValueError as e:
            trace.status = ToolStatus.INVALID_PARAMS
            trace.error = str(e)
        except Exception as e:
            trace.status = ToolStatus.ERROR
            trace.error = str(e)
        finally:
            # Calculate latency
            end_time = time.time()
            trace.latency_ms = (end_time - start_time) * 1000

            # Store trace
            self.traces.append(trace)
            self._current_trace = None

    def get_traces(self) -> List[ToolCallTrace]:
        """Get all captured traces."""
        return self.traces

    def get_tool_distribution(self) -> Dict[str, int]:
        """Get distribution of tool calls."""
        distribution = {}
        for trace in self.traces:
            distribution[trace.tool_name] = distribution.get(trace.tool_name, 0) + 1
        return distribution

    def get_error_rate(self) -> float:
        """Calculate overall error rate."""
        if not self.traces:
            return 0.0
        error_count = sum(
            1 for t in self.traces
            if t.status in [ToolStatus.ERROR, ToolStatus.TIMEOUT, ToolStatus.INVALID_PARAMS]
        )
        return error_count / len(self.traces)

    def get_error_rate_by_tool(self) -> Dict[str, float]:
        """Calculate error rate for each tool."""
        tool_calls = {}
        tool_errors = {}

        for trace in self.traces:
            tool_calls[trace.tool_name] = tool_calls.get(trace.tool_name, 0) + 1
            if trace.status in [ToolStatus.ERROR, ToolStatus.TIMEOUT, ToolStatus.INVALID_PARAMS]:
                tool_errors[trace.tool_name] = tool_errors.get(trace.tool_name, 0) + 1

        error_rates = {}
        for tool, calls in tool_calls.items():
            errors = tool_errors.get(tool, 0)
            error_rates[tool] = errors / calls if calls > 0 else 0.0

        return error_rates

    def get_avg_latency(self) -> float:
        """Calculate average latency across all tool calls."""
        if not self.traces:
            return 0.0
        return sum(t.latency_ms for t in self.traces) / len(self.traces)

    def get_total_latency(self) -> float:
        """Calculate total latency of all tool calls."""
        return sum(t.latency_ms for t in self.traces)


class TraceHelper:
    """Helper methods for working with traces."""

    @staticmethod
    def set_result(trace: ToolCallTrace, result: Any):
        """Set successful result on a trace."""
        trace.result = result
        trace.status = ToolStatus.SUCCESS

    @staticmethod
    def set_error(
        trace: ToolCallTrace,
        error: str,
        status: ToolStatus = ToolStatus.ERROR,
        recovery_action: Optional[str] = None
    ):
        """Set error on a trace."""
        trace.error = error
        trace.status = status
        trace.recovery_action = recovery_action

    @staticmethod
    def set_fallback(trace: ToolCallTrace, fallback_tool: str):
        """Mark trace as a fallback call."""
        trace.status = ToolStatus.FALLBACK
        trace.recovery_action = f"fallback_to_{fallback_tool}"
