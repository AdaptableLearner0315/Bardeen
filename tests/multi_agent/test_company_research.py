"""
Unit tests for CompanyResearchAgent

Tests:
- Agent initialization with correct type
- Tool filtering (only web_search and wikipedia)
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

from src.multi_agent.specialists.company_research import CompanyResearchAgent
from src.multi_agent.specialists.base_specialist import AgentResponse, AgentStatus
from src.multi_agent.guardrails.tool_access import AgentType, ToolAccessMatrix


class TestCompanyResearchAgentInitialization:
    """Tests for CompanyResearchAgent initialization."""

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

    def test_agent_type_is_company_research(self):
        """Agent should have COMPANY_RESEARCH type."""
        with patch('anthropic.Anthropic'):
            agent = CompanyResearchAgent(
                tool_registry=self._create_mock_registry()
            )
            assert agent.agent_type == AgentType.COMPANY_RESEARCH

    def test_agent_name_exists(self):
        """Agent should have a human-readable name."""
        with patch('anthropic.Anthropic'):
            agent = CompanyResearchAgent(
                tool_registry=self._create_mock_registry()
            )
            assert agent.agent_name is not None
            assert len(agent.agent_name) > 0
            assert "company" in agent.agent_name.lower() or "research" in agent.agent_name.lower()

    def test_allowed_tools_from_matrix(self):
        """Agent should have allowed tools from ToolAccessMatrix."""
        with patch('anthropic.Anthropic'):
            agent = CompanyResearchAgent(
                tool_registry=self._create_mock_registry()
            )
            expected_tools = ToolAccessMatrix.get_allowed_tools(AgentType.COMPANY_RESEARCH)
            assert agent.allowed_tools == expected_tools

    def test_allowed_tools_includes_web_search(self):
        """Agent should have access to web_search."""
        with patch('anthropic.Anthropic'):
            agent = CompanyResearchAgent(
                tool_registry=self._create_mock_registry()
            )
            assert "web_search" in agent.allowed_tools

    def test_allowed_tools_includes_wikipedia(self):
        """Agent should have access to wikipedia."""
        with patch('anthropic.Anthropic'):
            agent = CompanyResearchAgent(
                tool_registry=self._create_mock_registry()
            )
            assert "wikipedia" in agent.allowed_tools


class TestCompanyResearchAgentToolFiltering:
    """Tests for CompanyResearchAgent tool filtering."""

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
        """Filtered tools should only include web_search and wikipedia."""
        with patch('anthropic.Anthropic'):
            agent = CompanyResearchAgent(
                tool_registry=self._create_mock_registry()
            )
            tools = agent.get_filtered_tool_definitions()
            tool_names = [t["name"] for t in tools]

            assert "web_search" in tool_names
            assert "wikipedia" in tool_names
            assert len(tool_names) == 2

    def test_filtered_tools_excludes_calculator(self):
        """Filtered tools should not include calculator."""
        with patch('anthropic.Anthropic'):
            agent = CompanyResearchAgent(
                tool_registry=self._create_mock_registry()
            )
            tools = agent.get_filtered_tool_definitions()
            tool_names = [t["name"] for t in tools]

            assert "calculator" not in tool_names

    def test_filtered_tools_excludes_gmail(self):
        """Filtered tools should not include gmail (personal tool)."""
        with patch('anthropic.Anthropic'):
            agent = CompanyResearchAgent(
                tool_registry=self._create_mock_registry()
            )
            tools = agent.get_filtered_tool_definitions()
            tool_names = [t["name"] for t in tools]

            assert "gmail" not in tool_names

    def test_filtered_tools_excludes_perplexity(self):
        """Filtered tools should not include perplexity_search."""
        with patch('anthropic.Anthropic'):
            agent = CompanyResearchAgent(
                tool_registry=self._create_mock_registry()
            )
            tools = agent.get_filtered_tool_definitions()
            tool_names = [t["name"] for t in tools]

            assert "perplexity_search" not in tool_names


class TestCompanyResearchAgentSystemPrompt:
    """Tests for CompanyResearchAgent system prompt."""

    def _create_mock_registry(self):
        """Create a mock tool registry."""
        mock_registry = Mock()
        mock_registry.get_tool_definitions.return_value = []
        return mock_registry

    def test_system_prompt_exists(self):
        """System prompt should be defined."""
        with patch('anthropic.Anthropic'):
            agent = CompanyResearchAgent(
                tool_registry=self._create_mock_registry()
            )
            assert agent.system_prompt is not None
            assert len(agent.system_prompt) > 50

    def test_system_prompt_mentions_company(self):
        """System prompt should mention company research domain."""
        with patch('anthropic.Anthropic'):
            agent = CompanyResearchAgent(
                tool_registry=self._create_mock_registry()
            )
            prompt_lower = agent.system_prompt.lower()
            assert "company" in prompt_lower or "organization" in prompt_lower

    def test_system_prompt_mentions_facts(self):
        """System prompt should mention structured facts extraction."""
        with patch('anthropic.Anthropic'):
            agent = CompanyResearchAgent(
                tool_registry=self._create_mock_registry()
            )
            prompt_lower = agent.system_prompt.lower()
            # Should mention facts, data, information, founding, leadership, etc.
            has_fact_term = any(term in prompt_lower for term in [
                "fact", "data", "information", "founding", "founder",
                "headquarters", "hq", "leadership", "ceo", "ipo"
            ])
            assert has_fact_term


class TestCompanyResearchAgentExecution:
    """Tests for CompanyResearchAgent execution flow."""

    def _create_mock_registry(self):
        """Create a mock tool registry."""
        mock_registry = Mock()
        mock_registry.get_tool_definitions.return_value = [
            {"name": "web_search", "description": "Search the web"},
            {"name": "wikipedia", "description": "Search Wikipedia"},
        ]
        mock_registry.execute_tool.return_value = {
            "success": True,
            "result": "Apple Inc. was founded in 1976",
        }
        return mock_registry

    @pytest.mark.asyncio
    async def test_execute_returns_agent_response(self):
        """Execute should return an AgentResponse."""
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text="Apple was founded in 1976.")]
        mock_response.content[0].type = "text"

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            agent = CompanyResearchAgent(
                tool_registry=self._create_mock_registry()
            )
            result = await agent.execute("When was Apple founded?")

            assert isinstance(result, AgentResponse)
            assert result.agent_type == AgentType.COMPANY_RESEARCH

    @pytest.mark.asyncio
    async def test_execute_includes_query(self):
        """Execute response should include the original query."""
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text="Stripe was founded in 2010.")]
        mock_response.content[0].type = "text"

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            agent = CompanyResearchAgent(
                tool_registry=self._create_mock_registry()
            )
            result = await agent.execute("When was Stripe founded?")

            assert result.query == "When was Stripe founded?"

    @pytest.mark.asyncio
    async def test_execute_handles_errors(self):
        """Execute should handle errors gracefully."""
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("API Error")
            mock_anthropic.return_value = mock_client

            agent = CompanyResearchAgent(
                tool_registry=self._create_mock_registry()
            )
            result = await agent.execute("What is Tesla?")

            assert result.status == AgentStatus.FAILED
            assert result.error_message is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
