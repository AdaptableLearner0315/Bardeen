"""
Unit tests for multi-agent routing functions in dashboard backend.
"""

import pytest
from unittest.mock import MagicMock
from dataclasses import dataclass
from enum import Enum

# Import the functions to test
import sys
sys.path.insert(0, 'src')

from dashboard.backend.app import analyze_query_for_routing, generate_agent_executions


class TestAnalyzeQueryForRouting:
    """Tests for query routing analysis."""

    def test_company_research_routing(self):
        """Should route company queries to Company Research Agent."""
        queries = [
            "When was Apple founded?",
            "Who is the CEO of Google?",
            "Where is Microsoft headquarters?",
            "What products does Tesla offer?"
        ]

        for query in queries:
            result = analyze_query_for_routing(query, [])
            agents = [a["agent"] for a in result["agents"]]
            assert "company_research" in agents, f"Failed for: {query}"

    def test_financial_analyst_routing(self):
        """Should route financial queries to Financial Analyst Agent."""
        queries = [
            "What is Apple's market cap?",
            "Calculate the P/E ratio for Tesla",
            "What is the revenue growth of Amazon?",
            "Show me the stock price of NVIDIA"
        ]

        for query in queries:
            result = analyze_query_for_routing(query, [])
            agents = [a["agent"] for a in result["agents"]]
            assert "financial_analyst" in agents, f"Failed for: {query}"

    def test_competitive_intel_routing(self):
        """Should route comparison queries to Competitive Intel Agent."""
        queries = [
            "Compare Slack vs Teams",
            "Who are Apple's competitors?",
            "What are the alternatives to AWS?",
            "Pros and cons of React vs Vue"
        ]

        for query in queries:
            result = analyze_query_for_routing(query, [])
            agents = [a["agent"] for a in result["agents"]]
            assert "competitive_intel" in agents, f"Failed for: {query}"

    def test_action_executor_routing(self):
        """Should route action queries to Action Executor Agent."""
        queries = [
            "Check my email",
            "Schedule a meeting for tomorrow",
            "Show my calendar",
            "Send an email to John"
        ]

        for query in queries:
            result = analyze_query_for_routing(query, [])
            agents = [a["agent"] for a in result["agents"]]
            assert "action_executor" in agents, f"Failed for: {query}"

    def test_general_fallback_routing(self):
        """Should route unknown queries to General Fallback Agent."""
        queries = [
            "What is the capital of France?",
            "How does photosynthesis work?",
            "Explain quantum computing"
        ]

        for query in queries:
            result = analyze_query_for_routing(query, [])
            agents = [a["agent"] for a in result["agents"]]
            assert "general_fallback" in agents, f"Failed for: {query}"

    def test_multi_agent_routing(self):
        """Should route multi-intent queries to multiple agents."""
        result = analyze_query_for_routing(
            "What is Apple's market cap and who are their competitors?",
            []
        )

        agents = [a["agent"] for a in result["agents"]]
        assert "financial_analyst" in agents
        assert "competitive_intel" in agents
        assert result["mode"] == "multi_agent"
        assert len(result["agents"]) >= 2

    def test_single_agent_mode(self):
        """Should return single_agent mode for simple queries."""
        result = analyze_query_for_routing("When was Tesla founded?", [])

        assert result["mode"] == "single_agent"
        assert result["total_agents"] == 1

    def test_routing_has_required_fields(self):
        """Should return all required fields in routing response."""
        result = analyze_query_for_routing("Test query", [])

        assert "mode" in result
        assert "agents" in result
        assert "synthesis_strategy" in result
        assert "routing_reasoning" in result
        assert "total_agents" in result

    def test_agent_has_required_fields(self):
        """Each agent should have required display fields."""
        result = analyze_query_for_routing("When was Apple founded?", [])

        for agent in result["agents"]:
            assert "agent" in agent
            assert "display_name" in agent
            assert "icon" in agent
            assert "reason" in agent


class TestGenerateAgentExecutions:
    """Tests for agent execution generation."""

    @dataclass
    class MockTrace:
        tool_name: str
        params: dict
        status: MagicMock
        latency_ms: float
        llm_reasoning: str = ""

    def create_mock_trace(self, tool_name, params=None, status="success", latency_ms=100):
        """Create a mock tool trace."""
        trace = self.MockTrace(
            tool_name=tool_name,
            params=params or {},
            status=MagicMock(value=status),
            latency_ms=latency_ms,
            llm_reasoning="Test reasoning"
        )
        return trace

    def test_web_search_company_query(self):
        """Web search for company query should be assigned to company_research."""
        traces = [self.create_mock_trace("web_search", {"query": "Apple founded"})]
        result = generate_agent_executions("When was Apple founded?", traces)

        assert len(result) == 1
        assert result[0]["agent_id"] == "company_research"

    def test_web_search_financial_query(self):
        """Web search for financial query should be assigned to financial_analyst."""
        traces = [self.create_mock_trace("web_search", {"query": "Apple market cap"})]
        result = generate_agent_executions("What is Apple market cap?", traces)

        assert len(result) == 1
        assert result[0]["agent_id"] == "financial_analyst"

    def test_web_search_competitive_query(self):
        """Web search for comparison should be assigned to competitive_intel."""
        traces = [self.create_mock_trace("web_search", {"query": "Slack vs Teams"})]
        result = generate_agent_executions("Compare Slack vs Teams", traces)

        assert len(result) == 1
        assert result[0]["agent_id"] == "competitive_intel"

    def test_gmail_tool_assignment(self):
        """Gmail tool should always be assigned to action_executor."""
        traces = [self.create_mock_trace("gmail", {"action": "read"})]
        result = generate_agent_executions("Check my emails", traces)

        assert len(result) == 1
        assert result[0]["agent_id"] == "action_executor"

    def test_calendar_tool_assignment(self):
        """Calendar tool should always be assigned to action_executor."""
        traces = [self.create_mock_trace("google_calendar", {"action": "list"})]
        result = generate_agent_executions("Show my calendar", traces)

        assert len(result) == 1
        assert result[0]["agent_id"] == "action_executor"

    def test_calculator_financial_assignment(self):
        """Calculator for financial query should go to financial_analyst."""
        traces = [self.create_mock_trace("calculator", {"expression": "100*1.5"})]
        result = generate_agent_executions("Calculate the P/E ratio", traces)

        assert len(result) == 1
        assert result[0]["agent_id"] == "financial_analyst"

    def test_wikipedia_company_assignment(self):
        """Wikipedia for company query should go to company_research."""
        traces = [self.create_mock_trace("wikipedia", {"query": "Apple Inc"})]
        result = generate_agent_executions("Who founded Apple?", traces)

        assert len(result) == 1
        assert result[0]["agent_id"] == "company_research"

    def test_multiple_tools_grouped_by_agent(self):
        """Multiple tools should be grouped by their assigned agent."""
        traces = [
            self.create_mock_trace("web_search", {"query": "Apple stock price"}),
            self.create_mock_trace("calculator", {"expression": "3000/15"})
        ]
        result = generate_agent_executions("What is Apple stock price and calculate growth?", traces)

        # Both should be assigned to financial_analyst based on query keywords
        financial_agent = next((e for e in result if e["agent_id"] == "financial_analyst"), None)
        assert financial_agent is not None
        assert financial_agent["tool_count"] == 2

    def test_execution_has_required_fields(self):
        """Each execution should have required fields."""
        traces = [self.create_mock_trace("web_search")]
        result = generate_agent_executions("Test query", traces)

        for execution in result:
            assert "agent_id" in execution
            assert "display_name" in execution
            assert "icon" in execution
            assert "tools_used" in execution
            assert "tool_count" in execution
            assert "total_latency_ms" in execution
            assert "success_rate" in execution

    def test_success_rate_calculation(self):
        """Should correctly calculate success rate."""
        traces = [
            self.create_mock_trace("web_search", status="success"),
            self.create_mock_trace("wikipedia", status="error")
        ]
        result = generate_agent_executions("Who founded Apple?", traces)

        # Find the agent with both tools
        total_success = sum(e["success_rate"] * e["tool_count"] for e in result)
        total_tools = sum(e["tool_count"] for e in result)
        overall_success = total_success / total_tools if total_tools > 0 else 0

        assert overall_success == 0.5  # 1 success, 1 error

    def test_empty_traces_returns_empty(self):
        """Empty traces should return empty executions."""
        result = generate_agent_executions("Test query", [])
        assert result == []

    def test_latency_sum(self):
        """Should correctly sum latency for tools."""
        traces = [
            self.create_mock_trace("web_search", latency_ms=100),
            self.create_mock_trace("wikipedia", latency_ms=200)
        ]
        result = generate_agent_executions("Who founded Apple?", traces)

        total_latency = sum(e["total_latency_ms"] for e in result)
        assert total_latency == 300
