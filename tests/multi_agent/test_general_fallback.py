"""
Unit tests for GeneralFallbackAgent

Tests:
- Agent initialization with correct type
- Tool filtering (all research tools: web_search, wikipedia, calculator, perplexity_search)
- System prompt content verification (general-purpose, flexible)
- Basic execution flow with mocked LLM client
- Agent name and properties
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.multi_agent.specialists.general_fallback import GeneralFallbackAgent
from src.multi_agent.specialists.base_specialist import AgentResponse, AgentStatus
from src.multi_agent.guardrails.tool_access import AgentType, ToolAccessMatrix


class TestGeneralFallbackAgentInitialization:
    """Tests for GeneralFallbackAgent initialization."""

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

    def test_agent_type_is_general_fallback(self):
        """Agent should have GENERAL_FALLBACK type."""
        with patch('anthropic.Anthropic'):
            agent = GeneralFallbackAgent(
                tool_registry=self._create_mock_registry()
            )
            assert agent.agent_type == AgentType.GENERAL_FALLBACK

    def test_agent_name_exists(self):
        """Agent should have a human-readable name."""
        with patch('anthropic.Anthropic'):
            agent = GeneralFallbackAgent(
                tool_registry=self._create_mock_registry()
            )
            assert agent.agent_name is not None
            assert len(agent.agent_name) > 0
            # Should mention general or fallback
            name_lower = agent.agent_name.lower()
            assert "general" in name_lower or "fallback" in name_lower or "assistant" in name_lower

    def test_allowed_tools_from_matrix(self):
        """Agent should have allowed tools from ToolAccessMatrix."""
        with patch('anthropic.Anthropic'):
            agent = GeneralFallbackAgent(
                tool_registry=self._create_mock_registry()
            )
            expected_tools = ToolAccessMatrix.get_allowed_tools(AgentType.GENERAL_FALLBACK)
            assert agent.allowed_tools == expected_tools

    def test_allowed_tools_includes_web_search(self):
        """Agent should have access to web_search."""
        with patch('anthropic.Anthropic'):
            agent = GeneralFallbackAgent(
                tool_registry=self._create_mock_registry()
            )
            assert "web_search" in agent.allowed_tools

    def test_allowed_tools_includes_wikipedia(self):
        """Agent should have access to wikipedia."""
        with patch('anthropic.Anthropic'):
            agent = GeneralFallbackAgent(
                tool_registry=self._create_mock_registry()
            )
            assert "wikipedia" in agent.allowed_tools

    def test_allowed_tools_includes_calculator(self):
        """Agent should have access to calculator."""
        with patch('anthropic.Anthropic'):
            agent = GeneralFallbackAgent(
                tool_registry=self._create_mock_registry()
            )
            assert "calculator" in agent.allowed_tools

    def test_allowed_tools_includes_perplexity(self):
        """Agent should have access to perplexity_search."""
        with patch('anthropic.Anthropic'):
            agent = GeneralFallbackAgent(
                tool_registry=self._create_mock_registry()
            )
            assert "perplexity_search" in agent.allowed_tools


class TestGeneralFallbackAgentToolFiltering:
    """Tests for GeneralFallbackAgent tool filtering."""

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

    def test_filtered_tools_includes_research_tools(self):
        """Filtered tools should include all research tools."""
        with patch('anthropic.Anthropic'):
            agent = GeneralFallbackAgent(
                tool_registry=self._create_mock_registry()
            )
            tools = agent.get_filtered_tool_definitions()
            tool_names = [t["name"] for t in tools]

            assert "web_search" in tool_names
            assert "wikipedia" in tool_names
            assert "calculator" in tool_names
            assert "perplexity_search" in tool_names

    def test_filtered_tools_count(self):
        """Should have exactly 4 research tools."""
        with patch('anthropic.Anthropic'):
            agent = GeneralFallbackAgent(
                tool_registry=self._create_mock_registry()
            )
            tools = agent.get_filtered_tool_definitions()
            tool_names = [t["name"] for t in tools]

            assert len(tool_names) == 4

    def test_filtered_tools_excludes_gmail(self):
        """Filtered tools should NOT include gmail (personal tool)."""
        with patch('anthropic.Anthropic'):
            agent = GeneralFallbackAgent(
                tool_registry=self._create_mock_registry()
            )
            tools = agent.get_filtered_tool_definitions()
            tool_names = [t["name"] for t in tools]

            assert "gmail" not in tool_names

    def test_filtered_tools_excludes_calendar(self):
        """Filtered tools should NOT include google_calendar (personal tool)."""
        with patch('anthropic.Anthropic'):
            agent = GeneralFallbackAgent(
                tool_registry=self._create_mock_registry()
            )
            tools = agent.get_filtered_tool_definitions()
            tool_names = [t["name"] for t in tools]

            assert "google_calendar" not in tool_names


class TestGeneralFallbackAgentSystemPrompt:
    """Tests for GeneralFallbackAgent system prompt."""

    def _create_mock_registry(self):
        """Create a mock tool registry."""
        mock_registry = Mock()
        mock_registry.get_tool_definitions.return_value = []
        return mock_registry

    def test_system_prompt_exists(self):
        """System prompt should be defined."""
        with patch('anthropic.Anthropic'):
            agent = GeneralFallbackAgent(
                tool_registry=self._create_mock_registry()
            )
            assert agent.system_prompt is not None
            assert len(agent.system_prompt) > 50

    def test_system_prompt_mentions_general(self):
        """System prompt should mention general-purpose nature."""
        with patch('anthropic.Anthropic'):
            agent = GeneralFallbackAgent(
                tool_registry=self._create_mock_registry()
            )
            prompt_lower = agent.system_prompt.lower()
            has_general_term = any(term in prompt_lower for term in [
                "general", "versatile", "flexible", "broad", "various",
                "any", "wide", "diverse"
            ])
            assert has_general_term

    def test_system_prompt_mentions_assistant(self):
        """System prompt should mention assistant capabilities."""
        with patch('anthropic.Anthropic'):
            agent = GeneralFallbackAgent(
                tool_registry=self._create_mock_registry()
            )
            prompt_lower = agent.system_prompt.lower()
            has_assist_term = any(term in prompt_lower for term in [
                "assist", "help", "support", "query", "question",
                "answer", "research"
            ])
            assert has_assist_term

    def test_system_prompt_is_flexible(self):
        """System prompt should emphasize flexibility."""
        with patch('anthropic.Anthropic'):
            agent = GeneralFallbackAgent(
                tool_registry=self._create_mock_registry()
            )
            prompt_lower = agent.system_prompt.lower()
            # Should not be too restrictive in scope
            has_flexible_term = any(term in prompt_lower for term in [
                "topic", "domain", "subject", "question", "type",
                "adapt", "handle", "variety"
            ])
            assert has_flexible_term


class TestGeneralFallbackAgentExecution:
    """Tests for GeneralFallbackAgent execution flow."""

    def _create_mock_registry(self):
        """Create a mock tool registry."""
        mock_registry = Mock()
        mock_registry.get_tool_definitions.return_value = [
            {"name": "web_search", "description": "Search the web"},
            {"name": "wikipedia", "description": "Search Wikipedia"},
            {"name": "calculator", "description": "Do math"},
            {"name": "perplexity_search", "description": "Deep research"},
        ]
        mock_registry.execute_tool.return_value = {
            "success": True,
            "result": "Information about the query",
        }
        return mock_registry

    @pytest.mark.asyncio
    async def test_execute_returns_agent_response(self):
        """Execute should return an AgentResponse."""
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text="Here's information about your query.")]
        mock_response.content[0].type = "text"

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            agent = GeneralFallbackAgent(
                tool_registry=self._create_mock_registry()
            )
            result = await agent.execute("What is the meaning of life?")

            assert isinstance(result, AgentResponse)
            assert result.agent_type == AgentType.GENERAL_FALLBACK

    @pytest.mark.asyncio
    async def test_execute_includes_query(self):
        """Execute response should include the original query."""
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text="Python is a programming language.")]
        mock_response.content[0].type = "text"

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            agent = GeneralFallbackAgent(
                tool_registry=self._create_mock_registry()
            )
            result = await agent.execute("What is Python?")

            assert result.query == "What is Python?"

    @pytest.mark.asyncio
    async def test_execute_handles_errors(self):
        """Execute should handle errors gracefully."""
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("API Error")
            mock_anthropic.return_value = mock_client

            agent = GeneralFallbackAgent(
                tool_registry=self._create_mock_registry()
            )
            result = await agent.execute("Random question")

            assert result.status == AgentStatus.FAILED
            assert result.error_message is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
