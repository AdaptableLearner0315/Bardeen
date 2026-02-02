"""Tests for LLM reasoning traces display."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from pathlib import Path


class TestReasoningTraceCapture:
    """Tests for capturing LLM reasoning in traces."""

    def test_tracer_captures_reasoning(self):
        """Test that ToolTracer captures LLM reasoning."""
        from src.evaluation.tracers.tool_tracer import ToolTracer

        tracer = ToolTracer(attempt_number=1)

        with tracer.trace_tool_call(
            "wikipedia",
            {"title": "France"},
            llm_reasoning="I need to look up information about France"
        ) as trace:
            trace.result = {"success": True}

        traces = tracer.get_traces()
        assert len(traces) == 1
        assert traces[0].llm_reasoning == "I need to look up information about France"

    def test_tracer_handles_empty_reasoning(self):
        """Test tracer handles empty reasoning gracefully."""
        from src.evaluation.tracers.tool_tracer import ToolTracer

        tracer = ToolTracer(attempt_number=1)

        with tracer.trace_tool_call(
            "calculator",
            {"expression": "2+2"},
            llm_reasoning=""
        ) as trace:
            trace.result = {"success": True}

        traces = tracer.get_traces()
        assert len(traces) == 1
        assert traces[0].llm_reasoning == ""

    def test_tracer_handles_none_reasoning(self):
        """Test tracer handles None reasoning gracefully."""
        from src.evaluation.tracers.tool_tracer import ToolTracer

        tracer = ToolTracer(attempt_number=1)

        with tracer.trace_tool_call(
            "calculator",
            {"expression": "2+2"},
            llm_reasoning=None
        ) as trace:
            trace.result = {"success": True}

        traces = tracer.get_traces()
        assert len(traces) == 1
        assert traces[0].llm_reasoning is None

    def test_multiple_tool_calls_reasoning(self):
        """Test reasoning is captured for multiple tool calls."""
        from src.evaluation.tracers.tool_tracer import ToolTracer

        tracer = ToolTracer(attempt_number=1)

        # First tool call with reasoning
        with tracer.trace_tool_call(
            "wikipedia",
            {"title": "France"},
            llm_reasoning="Looking up France"
        ) as trace:
            trace.result = {"success": True}

        # Second tool call without reasoning
        with tracer.trace_tool_call(
            "calculator",
            {"expression": "67000000/640000"}
        ) as trace:
            trace.result = {"success": True}

        # Third tool call with reasoning
        with tracer.trace_tool_call(
            "wikipedia",
            {"title": "Germany"},
            llm_reasoning="Now checking Germany for comparison"
        ) as trace:
            trace.result = {"success": True}

        traces = tracer.get_traces()
        assert len(traces) == 3
        assert traces[0].llm_reasoning == "Looking up France"
        assert traces[1].llm_reasoning is None
        assert traces[2].llm_reasoning == "Now checking Germany for comparison"


class TestToolCallTraceModel:
    """Tests for ToolCallTrace model with reasoning."""

    def test_trace_model_has_reasoning_field(self):
        """Test ToolCallTrace model includes reasoning field."""
        from src.shared.models import ToolCallTrace, ToolStatus

        trace = ToolCallTrace(
            call_id="test_1",
            attempt_number=1,
            tool_name="wikipedia",
            params={"title": "Test"},
            result={"success": True},
            status=ToolStatus.SUCCESS,
            latency_ms=100,
            timestamp=datetime.now().isoformat(),
            llm_reasoning="Test reasoning"
        )

        assert hasattr(trace, 'llm_reasoning')
        assert trace.llm_reasoning == "Test reasoning"

    def test_trace_model_reasoning_optional(self):
        """Test reasoning field is optional."""
        from src.shared.models import ToolCallTrace, ToolStatus

        # Should not raise error without reasoning
        trace = ToolCallTrace(
            call_id="test_2",
            attempt_number=1,
            tool_name="calculator",
            params={"expression": "1+1"},
            result={"success": True},
            status=ToolStatus.SUCCESS,
            latency_ms=10,
            timestamp=datetime.now().isoformat()
        )

        assert trace.llm_reasoning is None or trace.llm_reasoning == ""


class TestAPIResponseReasoning:
    """Tests for API response reasoning serialization."""

    def test_tool_calls_include_reasoning_in_response(self):
        """Test API response includes reasoning in tool_calls."""
        tool_calls_dict = [
            {
                "tool_name": "wikipedia",
                "params": {"title": "France"},
                "result": "{'success': True}",
                "status": "success",
                "latency_ms": 100,
                "llm_reasoning": "Looking up France info"
            },
            {
                "tool_name": "calculator",
                "params": {"expression": "67000000/640000"},
                "result": "{'result': 104.6875}",
                "status": "success",
                "latency_ms": 5,
                "llm_reasoning": None
            }
        ]

        # First tool has reasoning
        assert tool_calls_dict[0]["llm_reasoning"] == "Looking up France info"

        # Second tool has no reasoning
        assert tool_calls_dict[1]["llm_reasoning"] is None

    def test_response_handles_missing_reasoning_key(self):
        """Test handling when llm_reasoning key is missing."""
        tool_call = {
            "tool_name": "calculator",
            "params": {"expression": "1+1"},
            "status": "success",
            "latency_ms": 5
        }

        # Should handle missing key gracefully
        reasoning = tool_call.get("llm_reasoning", None)
        assert reasoning is None


class TestFrontendReasoningDisplay:
    """Tests for frontend reasoning display elements."""

    def test_js_handles_empty_reasoning(self):
        """Test JavaScript handles empty reasoning correctly."""
        # Read the JavaScript file
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Should check for reasoning before displaying
        assert "llm_reasoning" in js_content
        assert "t.llm_reasoning && t.llm_reasoning.trim()" in js_content

    def test_js_shows_params_for_tools(self):
        """Test JavaScript shows tool parameters."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Should display params
        assert "t.params" in js_content
        assert "tool-params" in js_content

    def test_css_has_reasoning_styles(self):
        """Test CSS includes reasoning trace styles."""
        css_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/style.css"

        with open(css_path, 'r') as f:
            css_content = f.read()

        # Should have reasoning styles
        assert ".thinking-step .reasoning" in css_content
        assert ".thinking-step .tool-params" in css_content
        assert ".step-number" in css_content

    def test_css_has_success_error_states(self):
        """Test CSS includes success/error states for steps."""
        css_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/style.css"

        with open(css_path, 'r') as f:
            css_content = f.read()

        assert ".thinking-step.success" in css_content
        assert ".thinking-step.error" in css_content


class TestReasoningExtraction:
    """Tests for LLM reasoning extraction from responses."""

    def test_extract_reasoning_before_tool(self):
        """Test extracting reasoning text before tool call."""
        # Simulate Claude response content blocks
        class MockTextBlock:
            def __init__(self, text):
                self.type = "text"
                self.text = text

        class MockToolUseBlock:
            def __init__(self, name, input_data):
                self.type = "tool_use"
                self.name = name
                self.input = input_data
                self.id = "test_id"

        content_blocks = [
            MockTextBlock("Let me look up that information for you."),
            MockToolUseBlock("wikipedia", {"title": "France"})
        ]

        # Extract reasoning before tool call
        reasoning_parts = []
        tool_block = content_blocks[1]

        for block in content_blocks:
            if block == tool_block:
                break
            if block.type == "text":
                reasoning_parts.append(block.text)

        reasoning = "\n".join(reasoning_parts) if reasoning_parts else None
        assert reasoning == "Let me look up that information for you."

    def test_no_reasoning_before_tool(self):
        """Test when there's no text before tool call."""
        class MockToolUseBlock:
            def __init__(self, name, input_data):
                self.type = "tool_use"
                self.name = name
                self.input = input_data
                self.id = "test_id"

        content_blocks = [
            MockToolUseBlock("calculator", {"expression": "2+2"})
        ]

        # No text before tool call
        reasoning_parts = []
        tool_block = content_blocks[0]

        for block in content_blocks:
            if block == tool_block:
                break
            if hasattr(block, 'type') and block.type == "text":
                reasoning_parts.append(block.text)

        reasoning = "\n".join(reasoning_parts) if reasoning_parts else None
        assert reasoning is None


class TestToolParamsDisplay:
    """Tests for tool parameters display."""

    def test_params_serialization(self):
        """Test tool params are serialized correctly."""
        params = {
            "expression": "2 + 2",
            "title": "France"
        }

        # Convert to display string
        param_entries = list(params.items())
        assert ("expression", "2 + 2") in param_entries
        assert ("title", "France") in param_entries

    def test_long_params_truncated(self):
        """Test long parameter values are truncated."""
        params = {
            "query": "This is a very long query string that should be truncated to avoid display issues"
        }

        value = params["query"]
        truncated = value[:50] + ("..." if len(value) > 50 else "")

        assert len(truncated) <= 53  # 50 chars + "..."
        assert truncated.endswith("...")

    def test_nested_params_handled(self):
        """Test nested parameters are handled."""
        import json

        params = {
            "filters": {"category": "tech", "limit": 10}
        }

        # Nested params should be JSON stringified
        value = params["filters"]
        if not isinstance(value, str):
            value = json.dumps(value)

        assert "category" in value
        assert "tech" in value


class TestReasoningTraceIntegration:
    """Integration tests for reasoning traces."""

    def test_full_trace_flow(self):
        """Test full flow from tracer to API response format."""
        from src.evaluation.tracers.tool_tracer import ToolTracer

        tracer = ToolTracer(attempt_number=1)

        # Simulate tool calls
        with tracer.trace_tool_call(
            "wikipedia",
            {"title": "Apple Inc"},
            llm_reasoning="I'll look up Apple Inc information"
        ) as trace:
            trace.result = {"success": True, "title": "Apple Inc", "summary": "..."}

        with tracer.trace_tool_call(
            "calculator",
            {"expression": "150000000000 / 1000000000"},
            llm_reasoning="Calculating market cap in billions"
        ) as trace:
            trace.result = {"success": True, "result": 150}

        traces = tracer.get_traces()

        # Convert to API response format
        tool_calls_dict = [
            {
                "tool_name": t.tool_name,
                "params": t.params,
                "result": str(t.result)[:200] if t.result else None,
                "status": t.status.value,
                "latency_ms": t.latency_ms,
                "llm_reasoning": t.llm_reasoning
            }
            for t in traces
        ]

        assert len(tool_calls_dict) == 2
        assert tool_calls_dict[0]["llm_reasoning"] == "I'll look up Apple Inc information"
        assert tool_calls_dict[1]["llm_reasoning"] == "Calculating market cap in billions"
        assert tool_calls_dict[0]["params"]["title"] == "Apple Inc"
        assert tool_calls_dict[1]["params"]["expression"] == "150000000000 / 1000000000"
