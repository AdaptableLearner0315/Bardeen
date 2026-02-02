"""
Unit tests for BaseSpecialist

Tests:
- AgentResponse dataclass
- AgentStatus enum
- Tool filtering
- Confidence calculation
- Response formatting
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.multi_agent.specialists.base_specialist import (
    BaseSpecialist,
    AgentResponse,
    AgentStatus,
)
from src.multi_agent.guardrails.tool_access import AgentType


class TestAgentStatus:
    """Tests for AgentStatus enum."""

    def test_all_statuses_exist(self):
        """All expected statuses should exist."""
        assert AgentStatus.SUCCESS.value == "success"
        assert AgentStatus.PARTIAL.value == "partial"
        assert AgentStatus.FAILED.value == "failed"
        assert AgentStatus.TIMEOUT.value == "timeout"


class TestAgentResponse:
    """Tests for AgentResponse dataclass."""

    def test_response_creation_minimal(self):
        """AgentResponse should be created with minimal fields."""
        response = AgentResponse(
            agent_type=AgentType.COMPANY_RESEARCH,
            query="test query",
            answer="test answer",
            status=AgentStatus.SUCCESS,
        )
        assert response.agent_type == AgentType.COMPANY_RESEARCH
        assert response.query == "test query"
        assert response.answer == "test answer"
        assert response.status == AgentStatus.SUCCESS
        assert response.confidence == 1.0  # Default
        assert response.tool_calls == []  # Default
        assert response.sources == []  # Default

    def test_response_creation_full(self):
        """AgentResponse should accept all fields."""
        response = AgentResponse(
            agent_type=AgentType.FINANCIAL_ANALYST,
            query="What is Apple's market cap?",
            answer="$3 trillion",
            status=AgentStatus.SUCCESS,
            confidence=0.95,
            tool_calls=[{"tool": "web_search", "input": {"query": "Apple market cap"}}],
            sources=["https://example.com"],
            latency_ms=1234.5,
            error_message=None,
            metadata={"extra": "data"},
        )
        assert response.confidence == 0.95
        assert len(response.tool_calls) == 1
        assert len(response.sources) == 1
        assert response.latency_ms == 1234.5

    def test_response_to_dict(self):
        """to_dict should serialize all fields."""
        response = AgentResponse(
            agent_type=AgentType.COMPANY_RESEARCH,
            query="test",
            answer="answer",
            status=AgentStatus.SUCCESS,
            confidence=0.8,
        )
        d = response.to_dict()

        assert d["agent_type"] == "company_research"
        assert d["query"] == "test"
        assert d["answer"] == "answer"
        assert d["status"] == "success"
        assert d["confidence"] == 0.8

    def test_response_with_error(self):
        """Error responses should include error message."""
        response = AgentResponse(
            agent_type=AgentType.GENERAL_FALLBACK,
            query="test",
            answer="Failed to process",
            status=AgentStatus.FAILED,
            confidence=0.0,
            error_message="Connection timeout",
        )
        assert response.status == AgentStatus.FAILED
        assert response.error_message == "Connection timeout"


class TestBaseSpecialistHelpers:
    """Tests for BaseSpecialist helper methods."""

    def _create_mock_specialist(self, agent_type: AgentType):
        """Create a concrete mock specialist for testing."""
        # Create a mock tool registry
        mock_registry = Mock()
        mock_registry.get_tool_definitions.return_value = [
            {"name": "web_search", "description": "Search the web"},
            {"name": "calculator", "description": "Do math"},
            {"name": "wikipedia", "description": "Search Wikipedia"},
            {"name": "gmail", "description": "Email operations"},
        ]

        # Create concrete subclass for testing
        class TestSpecialist(BaseSpecialist):
            @property
            def system_prompt(self):
                return "Test prompt"

            @property
            def agent_name(self):
                return "Test Agent"

        with patch('anthropic.Anthropic'):
            return TestSpecialist(
                agent_type=agent_type,
                tool_registry=mock_registry,
            )

    def test_get_filtered_tool_definitions_company(self):
        """Company Research should only get web_search and wikipedia."""
        specialist = self._create_mock_specialist(AgentType.COMPANY_RESEARCH)
        tools = specialist.get_filtered_tool_definitions()

        tool_names = [t["name"] for t in tools]
        assert "web_search" in tool_names
        assert "wikipedia" in tool_names
        assert "calculator" not in tool_names
        assert "gmail" not in tool_names

    def test_get_filtered_tool_definitions_financial(self):
        """Financial Analyst should get web_search and calculator."""
        specialist = self._create_mock_specialist(AgentType.FINANCIAL_ANALYST)
        tools = specialist.get_filtered_tool_definitions()

        tool_names = [t["name"] for t in tools]
        assert "web_search" in tool_names
        assert "calculator" in tool_names
        assert "wikipedia" not in tool_names
        assert "gmail" not in tool_names

    def test_get_filtered_tool_definitions_action(self):
        """Action Executor should get gmail and calculator."""
        specialist = self._create_mock_specialist(AgentType.ACTION_EXECUTOR)
        tools = specialist.get_filtered_tool_definitions()

        tool_names = [t["name"] for t in tools]
        assert "gmail" in tool_names
        assert "calculator" in tool_names
        assert "web_search" not in tool_names

    def test_calculate_confidence_no_tools(self):
        """No tool calls should return 1.0 confidence."""
        specialist = self._create_mock_specialist(AgentType.COMPANY_RESEARCH)
        confidence = specialist._calculate_confidence([])
        assert confidence == 1.0

    def test_calculate_confidence_all_success(self):
        """All successful tool calls should return 1.0."""
        specialist = self._create_mock_specialist(AgentType.COMPANY_RESEARCH)
        tool_calls = [
            {"result": {"success": True}, "allowed": True},
            {"result": {"success": True}, "allowed": True},
        ]
        confidence = specialist._calculate_confidence(tool_calls)
        assert confidence == 1.0

    def test_calculate_confidence_partial_success(self):
        """Partial success should return proportional confidence."""
        specialist = self._create_mock_specialist(AgentType.COMPANY_RESEARCH)
        tool_calls = [
            {"result": {"success": True}, "allowed": True},
            {"result": {"success": False}, "allowed": True},
        ]
        confidence = specialist._calculate_confidence(tool_calls)
        assert confidence == 0.5

    def test_calculate_confidence_disallowed_tool(self):
        """Disallowed tool should reduce confidence."""
        specialist = self._create_mock_specialist(AgentType.COMPANY_RESEARCH)
        tool_calls = [
            {"result": {"success": True}, "allowed": True},
            {"result": {"success": True}, "allowed": False},
        ]
        confidence = specialist._calculate_confidence(tool_calls)
        assert confidence == 0.5

    def test_format_tool_result_success(self):
        """Successful tool result should be formatted."""
        specialist = self._create_mock_specialist(AgentType.COMPANY_RESEARCH)
        result = {"success": True, "result": "Apple market cap is $3T"}
        formatted = specialist._format_tool_result(result)
        assert "Apple market cap" in formatted

    def test_format_tool_result_error(self):
        """Error tool result should show error."""
        specialist = self._create_mock_specialist(AgentType.COMPANY_RESEARCH)
        result = {"success": False, "error": "Network error"}
        formatted = specialist._format_tool_result(result)
        assert "Error" in formatted
        assert "Network error" in formatted

    def test_build_messages_simple(self):
        """Simple query should build correct messages."""
        specialist = self._create_mock_specialist(AgentType.COMPANY_RESEARCH)
        messages = specialist._build_messages("What is Apple?", None)

        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "What is Apple?"

    def test_build_messages_with_context(self):
        """Query with context should include context messages."""
        specialist = self._create_mock_specialist(AgentType.COMPANY_RESEARCH)
        context = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"},
        ]
        messages = specialist._build_messages("Follow up?", context)

        assert len(messages) == 3
        assert messages[0]["content"] == "Previous question"
        assert messages[1]["content"] == "Previous answer"
        assert messages[2]["content"] == "Follow up?"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
