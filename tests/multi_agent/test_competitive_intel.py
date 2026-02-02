"""
Unit tests for CompetitiveIntelAgent

Tests:
- Agent initialization with correct type
- Tool filtering (web_search, perplexity_search)
- System prompt content verification
- Basic execution flow with mocked LLM client
- Agent name and properties
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.multi_agent.specialists.competitive_intel import CompetitiveIntelAgent
from src.multi_agent.specialists.base_specialist import AgentResponse, AgentStatus
from src.multi_agent.guardrails.tool_access import AgentType, ToolAccessMatrix


class TestCompetitiveIntelAgentInitialization:
    """Tests for CompetitiveIntelAgent initialization."""

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

    def test_agent_type_is_competitive_intel(self):
        """Agent should have COMPETITIVE_INTEL type."""
        with patch('anthropic.Anthropic'):
            agent = CompetitiveIntelAgent(
                tool_registry=self._create_mock_registry()
            )
            assert agent.agent_type == AgentType.COMPETITIVE_INTEL

    def test_agent_name_exists(self):
        """Agent should have a human-readable name."""
        with patch('anthropic.Anthropic'):
            agent = CompetitiveIntelAgent(
                tool_registry=self._create_mock_registry()
            )
            assert agent.agent_name is not None
            assert len(agent.agent_name) > 0
            assert "compet" in agent.agent_name.lower() or "intel" in agent.agent_name.lower()

    def test_allowed_tools_from_matrix(self):
        """Agent should have allowed tools from ToolAccessMatrix."""
        with patch('anthropic.Anthropic'):
            agent = CompetitiveIntelAgent(
                tool_registry=self._create_mock_registry()
            )
            expected_tools = ToolAccessMatrix.get_allowed_tools(AgentType.COMPETITIVE_INTEL)
            assert agent.allowed_tools == expected_tools

    def test_allowed_tools_includes_web_search(self):
        """Agent should have access to web_search."""
        with patch('anthropic.Anthropic'):
            agent = CompetitiveIntelAgent(
                tool_registry=self._create_mock_registry()
            )
            assert "web_search" in agent.allowed_tools

    def test_allowed_tools_includes_perplexity(self):
        """Agent should have access to perplexity_search."""
        with patch('anthropic.Anthropic'):
            agent = CompetitiveIntelAgent(
                tool_registry=self._create_mock_registry()
            )
            assert "perplexity_search" in agent.allowed_tools


class TestCompetitiveIntelAgentToolFiltering:
    """Tests for CompetitiveIntelAgent tool filtering."""

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
        """Filtered tools should only include web_search and perplexity_search."""
        with patch('anthropic.Anthropic'):
            agent = CompetitiveIntelAgent(
                tool_registry=self._create_mock_registry()
            )
            tools = agent.get_filtered_tool_definitions()
            tool_names = [t["name"] for t in tools]

            assert "web_search" in tool_names
            assert "perplexity_search" in tool_names
            assert len(tool_names) == 2

    def test_filtered_tools_excludes_wikipedia(self):
        """Filtered tools should not include wikipedia."""
        with patch('anthropic.Anthropic'):
            agent = CompetitiveIntelAgent(
                tool_registry=self._create_mock_registry()
            )
            tools = agent.get_filtered_tool_definitions()
            tool_names = [t["name"] for t in tools]

            assert "wikipedia" not in tool_names

    def test_filtered_tools_excludes_calculator(self):
        """Filtered tools should not include calculator."""
        with patch('anthropic.Anthropic'):
            agent = CompetitiveIntelAgent(
                tool_registry=self._create_mock_registry()
            )
            tools = agent.get_filtered_tool_definitions()
            tool_names = [t["name"] for t in tools]

            assert "calculator" not in tool_names

    def test_filtered_tools_excludes_gmail(self):
        """Filtered tools should not include gmail (personal tool)."""
        with patch('anthropic.Anthropic'):
            agent = CompetitiveIntelAgent(
                tool_registry=self._create_mock_registry()
            )
            tools = agent.get_filtered_tool_definitions()
            tool_names = [t["name"] for t in tools]

            assert "gmail" not in tool_names

    def test_filtered_tools_excludes_calendar(self):
        """Filtered tools should not include google_calendar."""
        with patch('anthropic.Anthropic'):
            agent = CompetitiveIntelAgent(
                tool_registry=self._create_mock_registry()
            )
            tools = agent.get_filtered_tool_definitions()
            tool_names = [t["name"] for t in tools]

            assert "google_calendar" not in tool_names


class TestCompetitiveIntelAgentSystemPrompt:
    """Tests for CompetitiveIntelAgent system prompt."""

    def _create_mock_registry(self):
        """Create a mock tool registry."""
        mock_registry = Mock()
        mock_registry.get_tool_definitions.return_value = []
        return mock_registry

    def test_system_prompt_exists(self):
        """System prompt should be defined."""
        with patch('anthropic.Anthropic'):
            agent = CompetitiveIntelAgent(
                tool_registry=self._create_mock_registry()
            )
            assert agent.system_prompt is not None
            assert len(agent.system_prompt) > 50

    def test_system_prompt_mentions_competitive(self):
        """System prompt should mention competitive intelligence domain."""
        with patch('anthropic.Anthropic'):
            agent = CompetitiveIntelAgent(
                tool_registry=self._create_mock_registry()
            )
            prompt_lower = agent.system_prompt.lower()
            assert "compet" in prompt_lower or "market" in prompt_lower

    def test_system_prompt_mentions_comparison(self):
        """System prompt should mention comparisons or analysis."""
        with patch('anthropic.Anthropic'):
            agent = CompetitiveIntelAgent(
                tool_registry=self._create_mock_registry()
            )
            prompt_lower = agent.system_prompt.lower()
            has_comparison_term = any(term in prompt_lower for term in [
                "compar", "analys", "versus", "vs", "alternative",
                "position", "advantage", "differentiat"
            ])
            assert has_comparison_term

    def test_system_prompt_mentions_balanced(self):
        """System prompt should mention balanced or objective analysis."""
        with patch('anthropic.Anthropic'):
            agent = CompetitiveIntelAgent(
                tool_registry=self._create_mock_registry()
            )
            prompt_lower = agent.system_prompt.lower()
            has_balance_term = any(term in prompt_lower for term in [
                "balanced", "objective", "fair", "unbiased", "both",
                "strength", "weakness", "pro", "con", "multi"
            ])
            assert has_balance_term


class TestCompetitiveIntelAgentExecution:
    """Tests for CompetitiveIntelAgent execution flow."""

    def _create_mock_registry(self):
        """Create a mock tool registry."""
        mock_registry = Mock()
        mock_registry.get_tool_definitions.return_value = [
            {"name": "web_search", "description": "Search the web"},
            {"name": "perplexity_search", "description": "Deep research"},
        ]
        mock_registry.execute_tool.return_value = {
            "success": True,
            "result": "Slack vs Teams comparison data",
        }
        return mock_registry

    @pytest.mark.asyncio
    async def test_execute_returns_agent_response(self):
        """Execute should return an AgentResponse."""
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text="Slack and Teams differ in pricing and features.")]
        mock_response.content[0].type = "text"

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            agent = CompetitiveIntelAgent(
                tool_registry=self._create_mock_registry()
            )
            result = await agent.execute("Compare Slack vs Teams")

            assert isinstance(result, AgentResponse)
            assert result.agent_type == AgentType.COMPETITIVE_INTEL

    @pytest.mark.asyncio
    async def test_execute_includes_query(self):
        """Execute response should include the original query."""
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text="AWS and Azure are the top cloud providers.")]
        mock_response.content[0].type = "text"

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            agent = CompetitiveIntelAgent(
                tool_registry=self._create_mock_registry()
            )
            result = await agent.execute("AWS vs Azure comparison")

            assert result.query == "AWS vs Azure comparison"

    @pytest.mark.asyncio
    async def test_execute_handles_errors(self):
        """Execute should handle errors gracefully."""
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("API Error")
            mock_anthropic.return_value = mock_client

            agent = CompetitiveIntelAgent(
                tool_registry=self._create_mock_registry()
            )
            result = await agent.execute("Salesforce competitors analysis")

            assert result.status == AgentStatus.FAILED
            assert result.error_message is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
