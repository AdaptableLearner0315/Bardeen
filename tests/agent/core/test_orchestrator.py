"""Tests for agent orchestrator module."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

from src.shared.config import ResearchMode
from src.agent.tools.base import ToolResult
from src.agent.core.orchestrator import (
    ToolCallRecord,
    AgentResponse,
    AgentOrchestrator,
    create_agent,
)


class TestToolCallRecord:
    """Tests for ToolCallRecord dataclass."""

    def test_creation(self):
        """Test basic creation."""
        record = ToolCallRecord(
            tool_name="calculator",
            input_params={"expression": "2+2"},
            result={"result": 4},
            success=True,
            execution_time=0.05
        )
        assert record.tool_name == "calculator"
        assert record.input_params == {"expression": "2+2"}
        assert record.result == {"result": 4}
        assert record.success is True
        assert record.execution_time == 0.05
        assert record.timestamp > 0

    def test_with_reasoning(self):
        """Test with reasoning field."""
        record = ToolCallRecord(
            tool_name="web_search",
            input_params={"query": "python"},
            result={"results": []},
            success=True,
            execution_time=0.5,
            reasoning="User asked about Python"
        )
        assert record.reasoning == "User asked about Python"

    def test_failed_tool_call(self):
        """Test failed tool call record."""
        record = ToolCallRecord(
            tool_name="wikipedia",
            input_params={"query": "nonexistent"},
            result={"error": "Not found"},
            success=False,
            execution_time=0.1
        )
        assert record.success is False


class TestAgentResponse:
    """Tests for AgentResponse dataclass."""

    def test_creation(self):
        """Test basic creation."""
        response = AgentResponse(answer="The answer is 42.")
        assert response.answer == "The answer is 42."
        assert response.tool_calls == []
        assert response.mode == ResearchMode.NORMAL
        assert response.success is True
        assert response.error is None

    def test_with_tool_calls(self):
        """Test with tool calls."""
        tool_record = ToolCallRecord(
            tool_name="calculator",
            input_params={},
            result={},
            success=True,
            execution_time=0.1
        )
        response = AgentResponse(
            answer="Result",
            tool_calls=[tool_record]
        )
        assert len(response.tool_calls) == 1

    def test_tool_count_property(self):
        """Test tool_count property."""
        records = [
            ToolCallRecord(tool_name=f"tool_{i}", input_params={}, result={}, success=True, execution_time=0.1)
            for i in range(3)
        ]
        response = AgentResponse(answer="Answer", tool_calls=records)
        assert response.tool_count == 3

    def test_successful_tool_calls_property(self):
        """Test successful_tool_calls property."""
        records = [
            ToolCallRecord(tool_name="tool_1", input_params={}, result={}, success=True, execution_time=0.1),
            ToolCallRecord(tool_name="tool_2", input_params={}, result={}, success=False, execution_time=0.1),
            ToolCallRecord(tool_name="tool_3", input_params={}, result={}, success=True, execution_time=0.1),
        ]
        response = AgentResponse(answer="Answer", tool_calls=records)
        assert response.successful_tool_calls == 2

    def test_to_dict(self):
        """Test to_dict method."""
        tool_record = ToolCallRecord(
            tool_name="calculator",
            input_params={"expression": "2+2"},
            result={"result": 4},
            success=True,
            execution_time=0.05
        )
        response = AgentResponse(
            answer="The answer is 4.",
            tool_calls=[tool_record],
            mode=ResearchMode.DEEP,
            total_time=1.5,
            token_usage={"input": 100, "output": 50}
        )

        result = response.to_dict()

        assert result["answer"] == "The answer is 4."
        assert result["mode"] == "deep"
        assert result["total_time"] == 1.5
        assert result["success"] is True
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["tool_name"] == "calculator"

    def test_error_response(self):
        """Test error response."""
        response = AgentResponse(
            answer="Error occurred",
            success=False,
            error="API Error"
        )
        assert response.success is False
        assert response.error == "API Error"


class TestAgentOrchestrator:
    """Tests for AgentOrchestrator class."""

    def test_initialization_defaults(self):
        """Test default initialization."""
        mock_registry = Mock()
        orchestrator = AgentOrchestrator(tool_registry=mock_registry)

        assert orchestrator.current_mode == ResearchMode.NORMAL
        assert orchestrator.max_tool_calls == 10
        assert orchestrator._total_requests == 0

    def test_initialization_custom(self):
        """Test custom initialization."""
        mock_registry = Mock()
        mock_memory = Mock()
        mock_llm = Mock()

        orchestrator = AgentOrchestrator(
            llm_client=mock_llm,
            tool_registry=mock_registry,
            memory_manager=mock_memory,
            default_mode=ResearchMode.DEEP,
            max_tool_calls=20
        )

        assert orchestrator.current_mode == ResearchMode.DEEP
        assert orchestrator.max_tool_calls == 20
        assert orchestrator.llm_client == mock_llm

    def test_set_mode(self):
        """Test setting research mode."""
        mock_registry = Mock()
        mock_memory = Mock()
        orchestrator = AgentOrchestrator(
            tool_registry=mock_registry,
            memory_manager=mock_memory
        )

        orchestrator.set_mode(ResearchMode.DEEP)

        assert orchestrator.current_mode == ResearchMode.DEEP
        mock_memory.set_mode.assert_called_with("deep")

    def test_get_available_tools(self):
        """Test getting available tools."""
        mock_registry = Mock()
        mock_registry.get_tool_names.return_value = ["calculator", "wikipedia"]

        orchestrator = AgentOrchestrator(tool_registry=mock_registry)
        tools = orchestrator.get_available_tools()

        assert tools == ["calculator", "wikipedia"]
        mock_registry.get_tool_names.assert_called_once()

    def test_get_available_tools_with_mode(self):
        """Test getting available tools for specific mode."""
        mock_registry = Mock()
        mock_registry.get_tool_names.return_value = ["calculator", "wikipedia", "yahoo_finance"]

        orchestrator = AgentOrchestrator(tool_registry=mock_registry)
        orchestrator.get_available_tools(mode=ResearchMode.DEEP)

        mock_registry.get_tool_names.assert_called_with(mode=ResearchMode.DEEP)

    def test_reset_conversation(self):
        """Test resetting conversation."""
        mock_registry = Mock()
        mock_memory = Mock()

        orchestrator = AgentOrchestrator(
            tool_registry=mock_registry,
            memory_manager=mock_memory
        )
        orchestrator.reset_conversation()

        mock_memory.clear_short_term.assert_called_once()

    def test_new_session(self):
        """Test starting new session."""
        mock_registry = Mock()
        mock_memory = Mock()
        mock_memory.new_session.return_value = "new_session_id"

        orchestrator = AgentOrchestrator(
            tool_registry=mock_registry,
            memory_manager=mock_memory
        )
        result = orchestrator.new_session()

        assert result == "new_session_id"
        mock_memory.new_session.assert_called_once()

    def test_get_stats(self):
        """Test getting statistics."""
        mock_registry = Mock()
        mock_registry.get_stats.return_value = {"tools": 5}
        mock_memory = Mock()
        mock_memory.get_stats.return_value = {"messages": 10}

        orchestrator = AgentOrchestrator(
            tool_registry=mock_registry,
            memory_manager=mock_memory
        )

        stats = orchestrator.get_stats()

        assert "total_requests" in stats
        assert "total_tool_calls" in stats
        assert "current_mode" in stats
        assert stats["memory"]["messages"] == 10
        assert stats["registry"]["tools"] == 5

    def test_reset_stats(self):
        """Test resetting statistics."""
        mock_registry = Mock()
        mock_llm = Mock()

        orchestrator = AgentOrchestrator(
            llm_client=mock_llm,
            tool_registry=mock_registry
        )
        orchestrator._total_requests = 10
        orchestrator._total_tool_calls = 50
        orchestrator._total_time = 100.0

        orchestrator.reset_stats()

        assert orchestrator._total_requests == 0
        assert orchestrator._total_tool_calls == 0
        assert orchestrator._total_time == 0.0
        mock_llm.reset_stats.assert_called_once()


class TestAgentOrchestratorAsk:
    """Tests for AgentOrchestrator.ask method."""

    def test_ask_basic(self):
        """Test basic ask functionality."""
        mock_registry = Mock()
        mock_registry.get_tool_definitions.return_value = []
        mock_memory = Mock()
        mock_memory.get_context_messages.return_value = []
        mock_llm = Mock()
        mock_llm.chat_with_tools.return_value = ("The answer is 42.", [])
        mock_llm.get_stats.return_value = {}

        orchestrator = AgentOrchestrator(
            llm_client=mock_llm,
            tool_registry=mock_registry,
            memory_manager=mock_memory
        )

        response = orchestrator.ask("What is the meaning of life?")

        assert response.answer == "The answer is 42."
        assert response.success is True
        mock_memory.add_user_message.assert_called_once()
        mock_memory.add_assistant_message.assert_called_once()

    def test_ask_with_mode_override(self):
        """Test ask with mode override."""
        mock_registry = Mock()
        mock_registry.get_tool_definitions.return_value = []
        mock_memory = Mock()
        mock_memory.get_context_messages.return_value = []
        mock_llm = Mock()
        mock_llm.chat_with_tools.return_value = ("Answer", [])
        mock_llm.get_stats.return_value = {}

        orchestrator = AgentOrchestrator(
            llm_client=mock_llm,
            tool_registry=mock_registry,
            memory_manager=mock_memory,
            default_mode=ResearchMode.NORMAL
        )

        response = orchestrator.ask("Question", mode=ResearchMode.DEEP)

        assert response.mode == ResearchMode.DEEP
        mock_memory.set_mode.assert_called_with("deep")

    def test_ask_with_reset_conversation(self):
        """Test ask with conversation reset."""
        mock_registry = Mock()
        mock_registry.get_tool_definitions.return_value = []
        mock_memory = Mock()
        mock_memory.get_context_messages.return_value = []
        mock_llm = Mock()
        mock_llm.chat_with_tools.return_value = ("Answer", [])
        mock_llm.get_stats.return_value = {}

        orchestrator = AgentOrchestrator(
            llm_client=mock_llm,
            tool_registry=mock_registry,
            memory_manager=mock_memory
        )

        orchestrator.ask("Question", reset_conversation=True)

        mock_memory.clear_short_term.assert_called_once()

    def test_ask_error_handling(self):
        """Test ask error handling."""
        mock_registry = Mock()
        mock_registry.get_tool_definitions.return_value = []
        mock_memory = Mock()
        mock_memory.get_context_messages.return_value = []
        mock_llm = Mock()
        mock_llm.chat_with_tools.side_effect = Exception("API Error")

        orchestrator = AgentOrchestrator(
            llm_client=mock_llm,
            tool_registry=mock_registry,
            memory_manager=mock_memory
        )

        response = orchestrator.ask("Question")

        assert response.success is False
        assert "error" in response.answer.lower()
        assert response.error == "API Error"

    def test_ask_lazy_llm_initialization(self):
        """Test lazy LLM client initialization."""
        mock_registry = Mock()
        mock_registry.get_tool_definitions.return_value = []
        mock_memory = Mock()
        mock_memory.get_context_messages.return_value = []

        orchestrator = AgentOrchestrator(
            tool_registry=mock_registry,
            memory_manager=mock_memory
        )

        # LLM client should be None initially
        assert orchestrator.llm_client is None

        # Mock the LLMClient class
        with patch("src.agent.core.orchestrator.LLMClient") as mock_llm_class:
            mock_llm = Mock()
            mock_llm.chat_with_tools.return_value = ("Answer", [])
            mock_llm.get_stats.return_value = {}
            mock_llm_class.return_value = mock_llm

            response = orchestrator.ask("Question")

            assert response.success is True
            mock_llm_class.assert_called_once()


class TestAgentOrchestratorToolExecution:
    """Tests for tool execution within ask method."""

    def test_tool_execution_recorded(self):
        """Test that tool executions are recorded."""
        mock_registry = Mock()
        mock_registry.get_tool_definitions.return_value = [
            {"name": "calculator", "description": "Calculate"}
        ]
        mock_registry.execute_tool.return_value = ToolResult(
            success=True,
            data={"result": 4, "expression": "2+2"}
        )
        mock_memory = Mock()
        mock_memory.get_context_messages.return_value = []
        mock_llm = Mock()

        # Capture the tool_executor that gets passed
        captured_executor = None

        def capture_executor(*args, **kwargs):
            nonlocal captured_executor
            captured_executor = kwargs.get("tool_executor")
            return ("The result is 4.", [])

        mock_llm.chat_with_tools.side_effect = capture_executor
        mock_llm.get_stats.return_value = {}

        orchestrator = AgentOrchestrator(
            llm_client=mock_llm,
            tool_registry=mock_registry,
            memory_manager=mock_memory
        )

        response = orchestrator.ask("What is 2+2?")

        # Verify executor was passed
        assert captured_executor is not None

    def test_tool_execution_success(self):
        """Test successful tool execution."""
        mock_registry = Mock()
        mock_registry.get_tool_definitions.return_value = [
            {"name": "calculator", "description": "Calculate"}
        ]
        mock_registry.execute_tool.return_value = ToolResult(
            success=True,
            data={"result": 4, "expression": "2+2"}
        )
        mock_memory = Mock()
        mock_memory.get_context_messages.return_value = []
        mock_llm = Mock()

        tool_records = []

        def mock_chat_with_tools(user_message, conversation_history, tools, tool_executor, system, max_tool_calls):
            # Simulate tool call
            if tool_executor:
                tool_executor("calculator", {"expression": "2+2"})
            return ("The result is 4.", [{"name": "calculator"}])

        mock_llm.chat_with_tools.side_effect = mock_chat_with_tools
        mock_llm.get_stats.return_value = {}

        orchestrator = AgentOrchestrator(
            llm_client=mock_llm,
            tool_registry=mock_registry,
            memory_manager=mock_memory
        )

        response = orchestrator.ask("What is 2+2?")

        # Verify tool was executed
        mock_registry.execute_tool.assert_called_once()

    def test_tool_execution_failure(self):
        """Test tool execution failure is handled."""
        mock_registry = Mock()
        mock_registry.get_tool_definitions.return_value = [
            {"name": "web_search", "description": "Search"}
        ]
        mock_registry.execute_tool.return_value = ToolResult(
            success=False,
            error="Network error"
        )
        mock_memory = Mock()
        mock_memory.get_context_messages.return_value = []
        mock_llm = Mock()

        def mock_chat_with_tools(user_message, conversation_history, tools, tool_executor, system, max_tool_calls):
            if tool_executor:
                result = tool_executor("web_search", {"query": "test"})
            return ("Search failed.", [])

        mock_llm.chat_with_tools.side_effect = mock_chat_with_tools
        mock_llm.get_stats.return_value = {}

        orchestrator = AgentOrchestrator(
            llm_client=mock_llm,
            tool_registry=mock_registry,
            memory_manager=mock_memory
        )

        response = orchestrator.ask("Search for something")

        # Should still return a response
        assert response.success is True


class TestAgentOrchestratorSystemPrompt:
    """Tests for system prompt building."""

    def test_build_system_prompt(self):
        """Test system prompt is built correctly."""
        mock_registry = Mock()
        mock_registry.get_tool_definitions.return_value = [
            {"name": "calculator", "description": "Perform calculations"},
            {"name": "wikipedia", "description": "Search Wikipedia"}
        ]

        orchestrator = AgentOrchestrator(tool_registry=mock_registry)
        prompt = orchestrator._build_system_prompt(ResearchMode.NORMAL)

        assert "calculator" in prompt
        assert "wikipedia" in prompt
        assert "NORMAL" in prompt

    def test_build_system_prompt_no_tools(self):
        """Test system prompt with no tools."""
        mock_registry = Mock()
        mock_registry.get_tool_definitions.return_value = []

        orchestrator = AgentOrchestrator(tool_registry=mock_registry)
        prompt = orchestrator._build_system_prompt(ResearchMode.NORMAL)

        assert "No tools available" in prompt

    def test_mode_description_in_prompt(self):
        """Test mode description is included in prompt."""
        mock_registry = Mock()
        mock_registry.get_tool_definitions.return_value = []

        orchestrator = AgentOrchestrator(tool_registry=mock_registry)

        normal_prompt = orchestrator._build_system_prompt(ResearchMode.NORMAL)
        assert "Normal mode" in normal_prompt or "core tools" in normal_prompt

        deep_prompt = orchestrator._build_system_prompt(ResearchMode.DEEP)
        assert "Deep mode" in deep_prompt or "comprehensive" in deep_prompt


class TestAgentOrchestratorFormatToolResult:
    """Tests for tool result formatting."""

    def test_format_error_result(self):
        """Test formatting error result."""
        mock_registry = Mock()
        orchestrator = AgentOrchestrator(tool_registry=mock_registry)

        result = ToolResult(success=False, error="Tool failed")
        formatted = orchestrator._format_tool_result(result)

        assert "Error" in formatted
        assert "Tool failed" in formatted

    def test_format_search_results(self):
        """Test formatting search results."""
        mock_registry = Mock()
        orchestrator = AgentOrchestrator(tool_registry=mock_registry)

        result = ToolResult(success=True, data={
            "answer": "Quick answer",
            "results": [
                {"title": "Result 1", "content": "Content 1", "url": "http://example.com/1"},
                {"title": "Result 2", "content": "Content 2", "url": "http://example.com/2"}
            ]
        })
        formatted = orchestrator._format_tool_result(result)

        assert "Quick answer" in formatted
        assert "Result 1" in formatted
        assert "Result 2" in formatted

    def test_format_empty_search_results(self):
        """Test formatting empty search results."""
        mock_registry = Mock()
        orchestrator = AgentOrchestrator(tool_registry=mock_registry)

        result = ToolResult(success=True, data={"results": []})
        formatted = orchestrator._format_tool_result(result)

        assert "No results" in formatted

    def test_format_wikipedia_result(self):
        """Test formatting Wikipedia-style result."""
        mock_registry = Mock()
        orchestrator = AgentOrchestrator(tool_registry=mock_registry)

        result = ToolResult(success=True, data={
            "title": "Python",
            "summary": "Python is a programming language...",
            "url": "https://wikipedia.org/wiki/Python"
        })
        formatted = orchestrator._format_tool_result(result)

        assert "Python" in formatted
        assert "programming language" in formatted

    def test_format_calculator_result(self):
        """Test formatting calculator result."""
        mock_registry = Mock()
        orchestrator = AgentOrchestrator(tool_registry=mock_registry)

        result = ToolResult(success=True, data={
            "expression": "2 + 2",
            "result": 4
        })
        formatted = orchestrator._format_tool_result(result)

        assert "2 + 2" in formatted
        assert "4" in formatted

    def test_format_financial_result(self):
        """Test formatting financial data result."""
        mock_registry = Mock()
        orchestrator = AgentOrchestrator(tool_registry=mock_registry)

        result = ToolResult(success=True, data={
            "company_name": "Apple Inc.",
            "stock_price": 150.00,
            "market_cap": "2.5T",
            "financials": {
                "revenue": "100B",
                "profit": "25B"
            }
        })
        formatted = orchestrator._format_tool_result(result)

        assert "Apple Inc." in formatted
        assert "150" in formatted or "stock" in formatted.lower()

    def test_format_generic_result(self):
        """Test formatting generic result."""
        mock_registry = Mock()
        orchestrator = AgentOrchestrator(tool_registry=mock_registry)

        result = ToolResult(success=True, data={"custom": "data"})
        formatted = orchestrator._format_tool_result(result)

        assert "custom" in formatted or "data" in formatted

    def test_format_non_dict_data(self):
        """Test formatting non-dict data."""
        mock_registry = Mock()
        orchestrator = AgentOrchestrator(tool_registry=mock_registry)

        result = ToolResult(success=True, data="Simple string result")
        formatted = orchestrator._format_tool_result(result)

        assert "Simple string result" in formatted


class TestCreateAgent:
    """Tests for create_agent factory function."""

    @patch("src.agent.core.orchestrator.LLMClient")
    def test_create_agent_default(self, mock_llm_class):
        """Test creating agent with defaults."""
        mock_llm_class.is_available.return_value = True

        agent = create_agent()

        assert isinstance(agent, AgentOrchestrator)
        assert agent.current_mode == ResearchMode.NORMAL

    @patch("src.agent.core.orchestrator.LLMClient")
    def test_create_agent_with_mode(self, mock_llm_class):
        """Test creating agent with specific mode."""
        mock_llm_class.is_available.return_value = True

        agent = create_agent(mode=ResearchMode.DEEP)

        assert agent.current_mode == ResearchMode.DEEP

    @patch("src.agent.core.orchestrator.LLMClient")
    def test_create_agent_with_api_key(self, mock_llm_class):
        """Test creating agent with API key."""
        mock_llm_class.is_available.return_value = True

        agent = create_agent(api_key="test_key")

        mock_llm_class.assert_called_with(api_key="test_key")

    @patch("src.agent.core.orchestrator.LLMClient")
    def test_create_agent_llm_unavailable(self, mock_llm_class):
        """Test creating agent when LLM is unavailable."""
        mock_llm_class.is_available.return_value = False

        agent = create_agent()

        # Should still create agent, just without LLM client
        assert isinstance(agent, AgentOrchestrator)

    @patch("src.agent.core.orchestrator.LLMClient")
    def test_create_agent_llm_init_failure(self, mock_llm_class):
        """Test creating agent when LLM initialization fails."""
        mock_llm_class.is_available.return_value = True
        mock_llm_class.side_effect = Exception("Init failed")

        agent = create_agent()

        # Should still create agent without crashing
        assert isinstance(agent, AgentOrchestrator)
        assert agent.llm_client is None
