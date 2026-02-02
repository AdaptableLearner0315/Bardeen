"""
Unit tests for ActionExecutorAgent

Tests:
- Agent initialization with correct type
- Tool filtering (gmail, google_calendar, calculator)
- System prompt content verification (privacy-conscious, confirmation)
- Basic execution flow with mocked LLM client
- Agent name and properties
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.multi_agent.specialists.action_executor import ActionExecutorAgent
from src.multi_agent.specialists.base_specialist import AgentResponse, AgentStatus
from src.multi_agent.guardrails.tool_access import AgentType, ToolAccessMatrix


class TestActionExecutorAgentInitialization:
    """Tests for ActionExecutorAgent initialization."""

    def _create_mock_registry(self):
        """Create a mock tool registry."""
        mock_registry = Mock()
        mock_registry.get_tool_definitions.return_value = [
            {"name": "web_search", "description": "Search the web"},
            {"name": "wikipedia", "description": "Search Wikipedia"},
            {"name": "calculator", "description": "Do math"},
            {"name": "gmail", "description": "Email operations"},
            {"name": "perplexity_search", "description": "Deep research"},
            {"name": "google_calendar", "description": "Calendar operations"},
        ]
        return mock_registry

    def test_agent_type_is_action_executor(self):
        """Agent should have ACTION_EXECUTOR type."""
        with patch('anthropic.Anthropic'):
            agent = ActionExecutorAgent(
                tool_registry=self._create_mock_registry()
            )
            assert agent.agent_type == AgentType.ACTION_EXECUTOR

    def test_agent_name_exists(self):
        """Agent should have a human-readable name."""
        with patch('anthropic.Anthropic'):
            agent = ActionExecutorAgent(
                tool_registry=self._create_mock_registry()
            )
            assert agent.agent_name is not None
            assert len(agent.agent_name) > 0
            assert "action" in agent.agent_name.lower() or "executor" in agent.agent_name.lower()

    def test_allowed_tools_from_matrix(self):
        """Agent should have allowed tools from ToolAccessMatrix."""
        with patch('anthropic.Anthropic'):
            agent = ActionExecutorAgent(
                tool_registry=self._create_mock_registry()
            )
            expected_tools = ToolAccessMatrix.get_allowed_tools(AgentType.ACTION_EXECUTOR)
            assert agent.allowed_tools == expected_tools

    def test_allowed_tools_includes_gmail(self):
        """Agent should have access to gmail (personal tool)."""
        with patch('anthropic.Anthropic'):
            agent = ActionExecutorAgent(
                tool_registry=self._create_mock_registry()
            )
            assert "gmail" in agent.allowed_tools

    def test_allowed_tools_includes_google_calendar(self):
        """Agent should have access to google_calendar (personal tool)."""
        with patch('anthropic.Anthropic'):
            agent = ActionExecutorAgent(
                tool_registry=self._create_mock_registry()
            )
            assert "google_calendar" in agent.allowed_tools

    def test_allowed_tools_includes_calculator(self):
        """Agent should have access to calculator."""
        with patch('anthropic.Anthropic'):
            agent = ActionExecutorAgent(
                tool_registry=self._create_mock_registry()
            )
            assert "calculator" in agent.allowed_tools


class TestActionExecutorAgentToolFiltering:
    """Tests for ActionExecutorAgent tool filtering."""

    def _create_mock_registry(self):
        """Create a mock tool registry."""
        mock_registry = Mock()
        mock_registry.get_tool_definitions.return_value = [
            {"name": "web_search", "description": "Search the web"},
            {"name": "wikipedia", "description": "Search Wikipedia"},
            {"name": "calculator", "description": "Do math"},
            {"name": "gmail", "description": "Email operations"},
            {"name": "perplexity_search", "description": "Deep research"},
            {"name": "google_calendar", "description": "Calendar operations"},
        ]
        return mock_registry

    def test_filtered_tools_only_includes_allowed(self):
        """Filtered tools should only include gmail, google_calendar, calculator."""
        with patch('anthropic.Anthropic'):
            agent = ActionExecutorAgent(
                tool_registry=self._create_mock_registry()
            )
            tools = agent.get_filtered_tool_definitions()
            tool_names = [t["name"] for t in tools]

            assert "gmail" in tool_names
            assert "google_calendar" in tool_names
            assert "calculator" in tool_names
            assert len(tool_names) == 3

    def test_filtered_tools_excludes_web_search(self):
        """Filtered tools should not include web_search."""
        with patch('anthropic.Anthropic'):
            agent = ActionExecutorAgent(
                tool_registry=self._create_mock_registry()
            )
            tools = agent.get_filtered_tool_definitions()
            tool_names = [t["name"] for t in tools]

            assert "web_search" not in tool_names

    def test_filtered_tools_excludes_wikipedia(self):
        """Filtered tools should not include wikipedia."""
        with patch('anthropic.Anthropic'):
            agent = ActionExecutorAgent(
                tool_registry=self._create_mock_registry()
            )
            tools = agent.get_filtered_tool_definitions()
            tool_names = [t["name"] for t in tools]

            assert "wikipedia" not in tool_names

    def test_filtered_tools_excludes_perplexity(self):
        """Filtered tools should not include perplexity_search."""
        with patch('anthropic.Anthropic'):
            agent = ActionExecutorAgent(
                tool_registry=self._create_mock_registry()
            )
            tools = agent.get_filtered_tool_definitions()
            tool_names = [t["name"] for t in tools]

            assert "perplexity_search" not in tool_names


class TestActionExecutorAgentSystemPrompt:
    """Tests for ActionExecutorAgent system prompt."""

    def _create_mock_registry(self):
        """Create a mock tool registry."""
        mock_registry = Mock()
        mock_registry.get_tool_definitions.return_value = []
        return mock_registry

    def test_system_prompt_exists(self):
        """System prompt should be defined."""
        with patch('anthropic.Anthropic'):
            agent = ActionExecutorAgent(
                tool_registry=self._create_mock_registry()
            )
            assert agent.system_prompt is not None
            assert len(agent.system_prompt) > 50

    def test_system_prompt_mentions_action(self):
        """System prompt should mention action execution domain."""
        with patch('anthropic.Anthropic'):
            agent = ActionExecutorAgent(
                tool_registry=self._create_mock_registry()
            )
            prompt_lower = agent.system_prompt.lower()
            has_action_term = any(term in prompt_lower for term in [
                "action", "execute", "perform", "email", "calendar",
                "meeting", "schedule", "send"
            ])
            assert has_action_term

    def test_system_prompt_mentions_privacy(self):
        """System prompt should mention privacy or security concerns."""
        with patch('anthropic.Anthropic'):
            agent = ActionExecutorAgent(
                tool_registry=self._create_mock_registry()
            )
            prompt_lower = agent.system_prompt.lower()
            has_privacy_term = any(term in prompt_lower for term in [
                "privacy", "secure", "confidential", "sensitive",
                "personal", "careful", "cautious", "protect"
            ])
            assert has_privacy_term

    def test_system_prompt_mentions_confirmation(self):
        """System prompt should mention confirmation or verification."""
        with patch('anthropic.Anthropic'):
            agent = ActionExecutorAgent(
                tool_registry=self._create_mock_registry()
            )
            prompt_lower = agent.system_prompt.lower()
            has_confirm_term = any(term in prompt_lower for term in [
                "confirm", "verify", "clarify", "explicit", "ask",
                "before", "permission", "consent", "approve"
            ])
            assert has_confirm_term


class TestActionExecutorAgentExecution:
    """Tests for ActionExecutorAgent execution flow."""

    def _create_mock_registry(self):
        """Create a mock tool registry."""
        mock_registry = Mock()
        mock_registry.get_tool_definitions.return_value = [
            {"name": "gmail", "description": "Email operations"},
            {"name": "google_calendar", "description": "Calendar operations"},
            {"name": "calculator", "description": "Do math"},
        ]
        mock_registry.execute_tool.return_value = {
            "success": True,
            "result": "You have 5 unread emails.",
        }
        return mock_registry

    @pytest.mark.asyncio
    async def test_execute_returns_agent_response(self):
        """Execute should return an AgentResponse."""
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text="You have 5 unread emails from today.")]
        mock_response.content[0].type = "text"

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            agent = ActionExecutorAgent(
                tool_registry=self._create_mock_registry()
            )
            result = await agent.execute("Summarize my unread emails")

            assert isinstance(result, AgentResponse)
            assert result.agent_type == AgentType.ACTION_EXECUTOR

    @pytest.mark.asyncio
    async def test_execute_includes_query(self):
        """Execute response should include the original query."""
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text="Meeting scheduled for tomorrow.")]
        mock_response.content[0].type = "text"

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            agent = ActionExecutorAgent(
                tool_registry=self._create_mock_registry()
            )
            result = await agent.execute("Schedule a meeting for tomorrow at 3pm")

            assert result.query == "Schedule a meeting for tomorrow at 3pm"

    @pytest.mark.asyncio
    async def test_execute_handles_errors(self):
        """Execute should handle errors gracefully."""
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("API Error")
            mock_anthropic.return_value = mock_client

            agent = ActionExecutorAgent(
                tool_registry=self._create_mock_registry()
            )
            result = await agent.execute("Send an email to john@example.com")

            assert result.status == AgentStatus.FAILED
            assert result.error_message is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
