"""
Unit tests for ToolAccessMatrix

Tests:
- Tool access permissions per agent type
- Personal tool restrictions
- Tool filtering
- Validation with error messages
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.multi_agent.guardrails.tool_access import ToolAccessMatrix, AgentType


class TestToolAccessMatrix:
    """Tests for ToolAccessMatrix class."""

    def test_company_research_tools(self):
        """Company Research Agent should only have web_search and wikipedia."""
        tools = ToolAccessMatrix.get_allowed_tools(AgentType.COMPANY_RESEARCH)
        assert tools == {"web_search", "wikipedia"}

    def test_financial_analyst_tools(self):
        """Financial Analyst should have web_search, calculator, perplexity."""
        tools = ToolAccessMatrix.get_allowed_tools(AgentType.FINANCIAL_ANALYST)
        assert tools == {"web_search", "calculator", "perplexity_search"}

    def test_competitive_intel_tools(self):
        """Competitive Intel should have web_search and perplexity."""
        tools = ToolAccessMatrix.get_allowed_tools(AgentType.COMPETITIVE_INTEL)
        assert tools == {"web_search", "perplexity_search"}

    def test_action_executor_tools(self):
        """Action Executor should have gmail, calendar, calculator."""
        tools = ToolAccessMatrix.get_allowed_tools(AgentType.ACTION_EXECUTOR)
        assert tools == {"gmail", "google_calendar", "calculator"}

    def test_general_fallback_tools(self):
        """General Fallback should have all tools EXCEPT personal ones."""
        tools = ToolAccessMatrix.get_allowed_tools(AgentType.GENERAL_FALLBACK)
        assert "web_search" in tools
        assert "wikipedia" in tools
        assert "calculator" in tools
        assert "perplexity_search" in tools
        # Personal tools should NOT be in general fallback
        assert "gmail" not in tools
        assert "google_calendar" not in tools

    def test_orchestrator_no_tools(self):
        """Orchestrator should have no direct tool access."""
        tools = ToolAccessMatrix.get_allowed_tools(AgentType.ORCHESTRATOR)
        assert tools == set()

    def test_can_access_tool_positive(self):
        """Test positive access checks."""
        assert ToolAccessMatrix.can_access_tool(AgentType.COMPANY_RESEARCH, "web_search")
        assert ToolAccessMatrix.can_access_tool(AgentType.FINANCIAL_ANALYST, "calculator")
        assert ToolAccessMatrix.can_access_tool(AgentType.ACTION_EXECUTOR, "gmail")

    def test_can_access_tool_negative(self):
        """Test negative access checks."""
        # Company Research cannot access calculator
        assert not ToolAccessMatrix.can_access_tool(AgentType.COMPANY_RESEARCH, "calculator")
        # Financial Analyst cannot access gmail
        assert not ToolAccessMatrix.can_access_tool(AgentType.FINANCIAL_ANALYST, "gmail")
        # General Fallback cannot access gmail
        assert not ToolAccessMatrix.can_access_tool(AgentType.GENERAL_FALLBACK, "gmail")

    def test_personal_tools_identification(self):
        """Personal tools should be correctly identified."""
        assert ToolAccessMatrix.is_personal_tool("gmail")
        assert ToolAccessMatrix.is_personal_tool("google_calendar")
        assert not ToolAccessMatrix.is_personal_tool("web_search")
        assert not ToolAccessMatrix.is_personal_tool("calculator")

    def test_filter_tools_for_agent(self):
        """Test tool filtering for specific agents."""
        all_tools = ["web_search", "wikipedia", "calculator", "gmail", "perplexity_search"]

        # Company Research should only keep web_search and wikipedia
        filtered = ToolAccessMatrix.filter_tools_for_agent(
            AgentType.COMPANY_RESEARCH, all_tools
        )
        assert filtered == ["web_search", "wikipedia"]

        # Action Executor should only keep gmail and calculator
        filtered = ToolAccessMatrix.filter_tools_for_agent(
            AgentType.ACTION_EXECUTOR, all_tools
        )
        assert filtered == ["calculator", "gmail"]

    def test_validate_tool_request_success(self):
        """Test successful tool validation."""
        is_allowed, error = ToolAccessMatrix.validate_tool_request(
            AgentType.FINANCIAL_ANALYST, "calculator"
        )
        assert is_allowed
        assert error == ""

    def test_validate_tool_request_denied_personal(self):
        """Test denied access to personal tools with proper error."""
        is_allowed, error = ToolAccessMatrix.validate_tool_request(
            AgentType.COMPANY_RESEARCH, "gmail"
        )
        assert not is_allowed
        assert "personal tool" in error.lower()
        assert "Action Executor" in error

    def test_validate_tool_request_denied_regular(self):
        """Test denied access to regular tools."""
        is_allowed, error = ToolAccessMatrix.validate_tool_request(
            AgentType.COMPANY_RESEARCH, "calculator"
        )
        assert not is_allowed
        assert "company_research" in error.lower()

    def test_validate_tool_request_unknown_tool(self):
        """Test validation of unknown tool."""
        is_allowed, error = ToolAccessMatrix.validate_tool_request(
            AgentType.GENERAL_FALLBACK, "unknown_tool"
        )
        assert not is_allowed
        assert "Unknown tool" in error

    def test_action_executor_exclusive_personal_access(self):
        """Only Action Executor should access personal tools."""
        for agent_type in AgentType:
            can_gmail = ToolAccessMatrix.can_access_tool(agent_type, "gmail")
            can_calendar = ToolAccessMatrix.can_access_tool(agent_type, "google_calendar")

            if agent_type == AgentType.ACTION_EXECUTOR:
                assert can_gmail, f"{agent_type} should access gmail"
                assert can_calendar, f"{agent_type} should access calendar"
            else:
                assert not can_gmail, f"{agent_type} should NOT access gmail"
                assert not can_calendar, f"{agent_type} should NOT access calendar"


class TestAgentType:
    """Tests for AgentType enum."""

    def test_all_agent_types_exist(self):
        """All expected agent types should exist."""
        expected = [
            "COMPANY_RESEARCH",
            "FINANCIAL_ANALYST",
            "COMPETITIVE_INTEL",
            "ACTION_EXECUTOR",
            "GENERAL_FALLBACK",
            "ORCHESTRATOR",
        ]
        for name in expected:
            assert hasattr(AgentType, name)

    def test_agent_type_values(self):
        """Agent type values should be lowercase strings."""
        assert AgentType.COMPANY_RESEARCH.value == "company_research"
        assert AgentType.FINANCIAL_ANALYST.value == "financial_analyst"
        assert AgentType.ORCHESTRATOR.value == "orchestrator"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
