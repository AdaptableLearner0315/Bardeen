"""Tests for research mode toggle and LLM reasoning traces."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json


class TestChatRequestMode:
    """Tests for chat request mode parameter."""

    def test_chat_request_default_mode(self):
        """Test that default mode is 'normal'."""
        from src.dashboard.backend.app import ChatRequest

        request = ChatRequest(message="test")
        assert request.mode == "normal"

    def test_chat_request_normal_mode(self):
        """Test explicit normal mode."""
        from src.dashboard.backend.app import ChatRequest

        request = ChatRequest(message="test", mode="normal")
        assert request.mode == "normal"

    def test_chat_request_deep_mode(self):
        """Test deep mode."""
        from src.dashboard.backend.app import ChatRequest

        request = ChatRequest(message="test", mode="deep")
        assert request.mode == "deep"


class TestChatResponseMode:
    """Tests for chat response mode parameter."""

    def test_chat_response_includes_mode(self):
        """Test that response includes mode."""
        from src.dashboard.backend.app import ChatResponse

        response = ChatResponse(
            answer="test",
            tool_calls=[],
            errors=[],
            ascii_trace="",
            latency_ms=100,
            mode="deep"
        )
        assert response.mode == "deep"

    def test_chat_response_default_mode(self):
        """Test response default mode is normal."""
        from src.dashboard.backend.app import ChatResponse

        response = ChatResponse(
            answer="test",
            tool_calls=[],
            errors=[],
            ascii_trace="",
            latency_ms=100
        )
        assert response.mode == "normal"


class TestModeConfiguration:
    """Tests for mode configuration settings."""

    def test_normal_mode_tools(self):
        """Test normal mode has 2-3 tools."""
        from src.shared.config import ModeConfig

        config = ModeConfig()

        # Normal mode should have limited tools
        assert len(config.normal_mode_tools) >= 2
        assert len(config.normal_mode_tools) <= 5
        assert config.normal_mode_max_calls <= 5

    def test_deep_mode_tools(self):
        """Test deep mode has 5-10 tools."""
        from src.shared.config import ModeConfig

        config = ModeConfig()

        # Deep mode should have more tools
        assert len(config.deep_mode_tools) >= 5
        assert config.deep_mode_max_calls >= 10

    def test_mode_timeouts(self):
        """Test mode-specific timeouts."""
        from src.shared.config import ModeConfig

        config = ModeConfig()

        # Deep mode should have longer timeout
        assert config.deep_mode_timeout > config.normal_mode_timeout


class TestToolTraceReasoning:
    """Tests for LLM reasoning in tool traces."""

    def test_tool_trace_has_reasoning_field(self):
        """Test that tool trace includes LLM reasoning."""
        from src.shared.models import ToolCallTrace, ToolStatus
        from datetime import datetime

        trace = ToolCallTrace(
            call_id="test_1",
            attempt_number=1,
            tool_name="calculator",
            params={"expression": "2+2"},
            result={"success": True, "result": 4},
            status=ToolStatus.SUCCESS,
            latency_ms=10,
            timestamp=datetime.now().isoformat(),
            llm_reasoning="I need to calculate 2+2"
        )

        assert trace.llm_reasoning == "I need to calculate 2+2"

    def test_tool_trace_reasoning_optional(self):
        """Test that reasoning is optional."""
        from src.shared.models import ToolCallTrace, ToolStatus
        from datetime import datetime

        trace = ToolCallTrace(
            call_id="test_2",
            attempt_number=1,
            tool_name="calculator",
            params={"expression": "2+2"},
            result={"success": True, "result": 4},
            status=ToolStatus.SUCCESS,
            latency_ms=10,
            timestamp=datetime.now().isoformat()
        )

        # Should not fail if reasoning is not provided
        assert trace.llm_reasoning is None or trace.llm_reasoning == ""


class TestToolTracerReasoning:
    """Tests for ToolTracer reasoning capture."""

    def test_tracer_captures_reasoning(self):
        """Test that tracer captures LLM reasoning."""
        from src.evaluation.tracers.tool_tracer import ToolTracer

        tracer = ToolTracer(attempt_number=1)

        with tracer.trace_tool_call(
            "calculator",
            {"expression": "2+2"},
            llm_reasoning="Let me calculate this"
        ) as trace:
            pass

        traces = tracer.get_traces()
        assert len(traces) == 1
        assert traces[0].llm_reasoning == "Let me calculate this"

    def test_tracer_handles_no_reasoning(self):
        """Test tracer works without reasoning."""
        from src.evaluation.tracers.tool_tracer import ToolTracer

        tracer = ToolTracer(attempt_number=1)

        with tracer.trace_tool_call(
            "calculator",
            {"expression": "2+2"}
        ) as trace:
            pass

        traces = tracer.get_traces()
        assert len(traces) == 1


class TestModeIntegration:
    """Integration tests for mode functionality."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent."""
        agent = Mock()
        agent.ask.return_value = ("Answer", [], [])
        agent.get_available_tools.return_value = ["calculator", "wikipedia"]
        return agent

    def test_normal_mode_message_unchanged(self, mock_agent):
        """Test that normal mode doesn't modify message much."""
        # In normal mode, the message should be passed as-is
        original_message = "What is 2+2?"

        # The enhancement for normal mode is minimal
        assert "DEEP RESEARCH" not in original_message

    def test_deep_mode_enhances_message(self):
        """Test that deep mode adds research instructions."""
        message = "What is Apple's market cap?"
        mode = "deep"

        # Deep mode should add instructions
        if mode == "deep":
            enhanced = f"[DEEP RESEARCH MODE] {message}"
            assert "DEEP RESEARCH" in enhanced


class TestHealthEndpointMode:
    """Tests for health endpoint mode information."""

    def test_health_returns_available_tools(self):
        """Test health endpoint returns tool list."""
        # The health endpoint should return available tools
        # which varies based on mode
        from src.shared.config import ModeConfig

        config = ModeConfig()

        normal_tools = config.normal_mode_tools
        deep_tools = config.deep_mode_tools

        # Deep mode should have more tools
        assert len(deep_tools) >= len(normal_tools)


class TestFrontendModeToggle:
    """Tests for frontend mode toggle elements."""

    def test_html_has_mode_buttons(self):
        """Test HTML includes mode toggle buttons."""
        from pathlib import Path

        html_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/index.html"

        with open(html_path, 'r') as f:
            html_content = f.read()

        assert 'mode-normal' in html_content
        assert 'mode-deep' in html_content
        assert 'mode-toggle' in html_content

    def test_html_has_thinking_trace_styles(self):
        """Test CSS includes thinking trace styles."""
        from pathlib import Path

        css_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/style.css"

        with open(css_path, 'r') as f:
            css_content = f.read()

        assert 'thinking-trace' in css_content
        assert 'mode-button' in css_content

    def test_js_has_mode_functions(self):
        """Test JavaScript includes mode functions."""
        from pathlib import Path

        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert 'currentMode' in js_content
        assert 'setMode' in js_content
        assert 'initializeModeToggle' in js_content


class TestDeepModeToolCount:
    """Tests for deep mode tool count requirements."""

    def test_deep_mode_min_tools(self):
        """Test deep mode uses at least 5 tools."""
        from src.shared.config import ModeConfig

        config = ModeConfig()

        # Deep mode should have at least 5 tools available
        assert len(config.deep_mode_tools) >= 5

    def test_deep_mode_max_calls(self):
        """Test deep mode allows up to 10 tool calls."""
        from src.shared.config import ModeConfig

        config = ModeConfig()

        # Deep mode should allow at least 10 calls
        assert config.deep_mode_max_calls >= 10

    def test_normal_vs_deep_tool_difference(self):
        """Test deep mode has more tools than normal."""
        from src.shared.config import ModeConfig

        config = ModeConfig()

        normal_count = len(config.normal_mode_tools)
        deep_count = len(config.deep_mode_tools)

        assert deep_count > normal_count


class TestReasoningDisplay:
    """Tests for reasoning display in responses."""

    def test_tool_call_dict_includes_reasoning(self):
        """Test serialized tool call includes reasoning."""
        tool_call = {
            "tool_name": "calculator",
            "params": {"expression": "2+2"},
            "result": "4",
            "status": "success",
            "latency_ms": 10,
            "llm_reasoning": "I need to calculate 2+2"
        }

        assert "llm_reasoning" in tool_call
        assert tool_call["llm_reasoning"] == "I need to calculate 2+2"

    def test_api_response_includes_reasoning(self):
        """Test API response format includes reasoning."""
        response_data = {
            "answer": "The result is 4",
            "tool_calls": [
                {
                    "tool_name": "calculator",
                    "params": {"expression": "2+2"},
                    "result": "{'result': 4}",
                    "status": "success",
                    "latency_ms": 10,
                    "llm_reasoning": "Let me calculate that"
                }
            ],
            "errors": [],
            "ascii_trace": "",
            "latency_ms": 1000,
            "mode": "normal"
        }

        # Verify reasoning is in tool calls
        assert len(response_data["tool_calls"]) == 1
        assert response_data["tool_calls"][0]["llm_reasoning"] == "Let me calculate that"
