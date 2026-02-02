"""
Unit tests for QueryRouter

Tests:
- Query classification accuracy
- Routing to correct agents
- Multi-agent vs single-agent decision
- Synthesis strategy selection
- Subtask decomposition
- Edge cases and error handling
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from dataclasses import asdict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.multi_agent.guardrails.tool_access import AgentType
from src.multi_agent.router import (
    QueryRouter,
    RoutingDecision,
    SynthesisStrategy,
    QueryComplexity,
)


class TestRoutingDecision:
    """Tests for RoutingDecision dataclass."""

    def test_routing_decision_single_agent(self):
        """Single agent routing should have one agent."""
        decision = RoutingDecision(
            mode="single_agent",
            agents=[AgentType.COMPANY_RESEARCH],
            subtasks=[{"agent": AgentType.COMPANY_RESEARCH, "query": "When was Stripe founded?"}],
            synthesis_strategy=SynthesisStrategy.MERGE,
            confidence=0.95,
            reasoning="Company founding date is a company research query.",
        )
        assert decision.mode == "single_agent"
        assert len(decision.agents) == 1
        assert decision.agents[0] == AgentType.COMPANY_RESEARCH

    def test_routing_decision_multi_agent(self):
        """Multi-agent routing should have multiple agents."""
        decision = RoutingDecision(
            mode="multi_agent",
            agents=[AgentType.COMPANY_RESEARCH, AgentType.FINANCIAL_ANALYST],
            subtasks=[
                {"agent": AgentType.COMPANY_RESEARCH, "query": "What does Apple do?"},
                {"agent": AgentType.FINANCIAL_ANALYST, "query": "What is Apple's market cap?"},
            ],
            synthesis_strategy=SynthesisStrategy.MERGE,
            confidence=0.90,
            reasoning="Query requires both company info and financial data.",
        )
        assert decision.mode == "multi_agent"
        assert len(decision.agents) == 2
        assert len(decision.subtasks) == 2

    def test_routing_decision_to_dict(self):
        """to_dict should serialize all fields."""
        decision = RoutingDecision(
            mode="single_agent",
            agents=[AgentType.ACTION_EXECUTOR],
            subtasks=[{"agent": AgentType.ACTION_EXECUTOR, "query": "Send email"}],
            synthesis_strategy=SynthesisStrategy.SEQUENTIAL,
            confidence=0.85,
            reasoning="Email task requires action executor.",
        )
        d = decision.to_dict()
        assert d["mode"] == "single_agent"
        assert "action_executor" in d["agents"]
        assert d["synthesis_strategy"] == "sequential"


class TestQueryComplexity:
    """Tests for QueryComplexity enum."""

    def test_complexity_levels(self):
        """All complexity levels should exist."""
        assert QueryComplexity.SIMPLE.value == "simple"
        assert QueryComplexity.MODERATE.value == "moderate"
        assert QueryComplexity.COMPLEX.value == "complex"


class TestQueryRouterPatternDetection:
    """Tests for QueryRouter pattern detection methods."""

    @pytest.fixture
    def router(self):
        """Create router with mocked LLM client."""
        with patch('anthropic.Anthropic'):
            return QueryRouter()

    # Company Research Detection
    def test_detect_company_query_founded(self, router):
        """Should detect company founding questions."""
        query = "When was Stripe founded?"
        is_company = router._is_company_research_query(query)
        assert is_company is True

    def test_detect_company_query_headquarters(self, router):
        """Should detect company headquarters questions."""
        query = "Where is Tesla headquartered?"
        is_company = router._is_company_research_query(query)
        assert is_company is True

    def test_detect_company_query_ceo(self, router):
        """Should detect CEO/leadership questions."""
        query = "Who is the CEO of Microsoft?"
        is_company = router._is_company_research_query(query)
        assert is_company is True

    def test_detect_company_query_products(self, router):
        """Should detect product questions."""
        query = "What products does Salesforce sell?"
        is_company = router._is_company_research_query(query)
        assert is_company is True

    # Financial Analysis Detection
    def test_detect_financial_query_market_cap(self, router):
        """Should detect market cap questions."""
        query = "What is Apple's market cap?"
        is_financial = router._is_financial_query(query)
        assert is_financial is True

    def test_detect_financial_query_revenue(self, router):
        """Should detect revenue questions."""
        query = "What is Amazon's annual revenue?"
        is_financial = router._is_financial_query(query)
        assert is_financial is True

    def test_detect_financial_query_stock(self, router):
        """Should detect stock price questions."""
        query = "What is NVIDIA's stock price?"
        is_financial = router._is_financial_query(query)
        assert is_financial is True

    def test_detect_financial_query_calculation(self, router):
        """Should detect financial calculations."""
        query = "Calculate the P/E ratio for Google"
        is_financial = router._is_financial_query(query)
        assert is_financial is True

    # Competitive Intelligence Detection
    def test_detect_competitive_query_compare(self, router):
        """Should detect comparison queries."""
        query = "Compare Slack vs Microsoft Teams"
        is_competitive = router._is_competitive_query(query)
        assert is_competitive is True

    def test_detect_competitive_query_vs(self, router):
        """Should detect 'vs' pattern."""
        query = "AWS vs Azure vs GCP"
        is_competitive = router._is_competitive_query(query)
        assert is_competitive is True

    def test_detect_competitive_query_competitors(self, router):
        """Should detect competitor questions."""
        query = "Who are Stripe's main competitors?"
        is_competitive = router._is_competitive_query(query)
        assert is_competitive is True

    def test_detect_competitive_query_market_position(self, router):
        """Should detect market position questions."""
        query = "What is Salesforce's market position?"
        is_competitive = router._is_competitive_query(query)
        assert is_competitive is True

    # Action Execution Detection
    def test_detect_action_query_email(self, router):
        """Should detect email queries."""
        query = "Summarize my unread emails"
        is_action = router._is_action_query(query)
        assert is_action is True

    def test_detect_action_query_calendar(self, router):
        """Should detect calendar queries."""
        query = "Schedule a meeting for tomorrow"
        is_action = router._is_action_query(query)
        assert is_action is True

    def test_detect_action_query_send_email(self, router):
        """Should detect send email queries."""
        query = "Send an email to John about the proposal"
        is_action = router._is_action_query(query)
        assert is_action is True

    def test_detect_action_query_meeting(self, router):
        """Should detect meeting queries."""
        query = "What meetings do I have today?"
        is_action = router._is_action_query(query)
        assert is_action is True


class TestQueryRouterSynthesisStrategy:
    """Tests for synthesis strategy selection."""

    @pytest.fixture
    def router(self):
        """Create router with mocked LLM client."""
        with patch('anthropic.Anthropic'):
            return QueryRouter()

    def test_strategy_merge_for_company_plus_financial(self, router):
        """Company + Financial queries should use merge strategy."""
        agents = [AgentType.COMPANY_RESEARCH, AgentType.FINANCIAL_ANALYST]
        strategy = router._select_synthesis_strategy(agents, "Tell me about Apple")
        assert strategy == SynthesisStrategy.MERGE

    def test_strategy_sequential_for_dependent_tasks(self, router):
        """Sequential tasks should use sequential strategy."""
        # When one agent's output feeds into another
        agents = [AgentType.COMPANY_RESEARCH, AgentType.ACTION_EXECUTOR]
        query = "Research Stripe and then email the summary to my team"
        strategy = router._select_synthesis_strategy(agents, query)
        assert strategy == SynthesisStrategy.SEQUENTIAL

    def test_strategy_consensus_for_competitive(self, router):
        """Competitive queries may use consensus strategy."""
        agents = [AgentType.COMPETITIVE_INTEL]
        query = "Compare Stripe vs Square"
        strategy = router._select_synthesis_strategy(agents, query)
        # Single agent doesn't need consensus, but multi-agent comparison might
        assert strategy in [SynthesisStrategy.MERGE, SynthesisStrategy.RANKED]

    def test_strategy_ranked_for_comparisons(self, router):
        """Comparison queries should use ranked strategy."""
        agents = [AgentType.COMPETITIVE_INTEL]
        query = "Which is better: AWS or Azure?"
        strategy = router._select_synthesis_strategy(agents, query)
        assert strategy == SynthesisStrategy.RANKED


class TestQueryRouterRouteMethod:
    """Tests for the main route() method."""

    @pytest.fixture
    def router(self):
        """Create router with mocked LLM client."""
        with patch('anthropic.Anthropic'):
            return QueryRouter()

    @pytest.mark.asyncio
    async def test_route_company_query(self, router):
        """Company query should route to CompanyResearchAgent."""
        with patch.object(router, '_classify_with_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "mode": "single_agent",
                "agents": ["company_research"],
                "subtasks": [{"agent": "company_research", "query": "When was Stripe founded?"}],
                "synthesis_strategy": "merge",
                "confidence": 0.95,
                "reasoning": "Company founding query.",
            }
            decision = await router.route("When was Stripe founded?")
            assert AgentType.COMPANY_RESEARCH in decision.agents

    @pytest.mark.asyncio
    async def test_route_financial_query(self, router):
        """Financial query should route to FinancialAnalystAgent."""
        with patch.object(router, '_classify_with_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "mode": "single_agent",
                "agents": ["financial_analyst"],
                "subtasks": [{"agent": "financial_analyst", "query": "What is Apple's market cap?"}],
                "synthesis_strategy": "merge",
                "confidence": 0.92,
                "reasoning": "Market cap is financial query.",
            }
            decision = await router.route("What is Apple's market cap?")
            assert AgentType.FINANCIAL_ANALYST in decision.agents

    @pytest.mark.asyncio
    async def test_route_comparison_query(self, router):
        """Comparison query should route to CompetitiveIntelAgent."""
        with patch.object(router, '_classify_with_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "mode": "single_agent",
                "agents": ["competitive_intel"],
                "subtasks": [{"agent": "competitive_intel", "query": "Compare Slack vs Teams"}],
                "synthesis_strategy": "ranked",
                "confidence": 0.88,
                "reasoning": "Product comparison query.",
            }
            decision = await router.route("Compare Slack vs Teams")
            assert AgentType.COMPETITIVE_INTEL in decision.agents

    @pytest.mark.asyncio
    async def test_route_action_query(self, router):
        """Action query should route to ActionExecutorAgent."""
        with patch.object(router, '_classify_with_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "mode": "single_agent",
                "agents": ["action_executor"],
                "subtasks": [{"agent": "action_executor", "query": "Summarize my emails"}],
                "synthesis_strategy": "merge",
                "confidence": 0.90,
                "reasoning": "Email action query.",
            }
            decision = await router.route("Summarize my unread emails")
            assert AgentType.ACTION_EXECUTOR in decision.agents

    @pytest.mark.asyncio
    async def test_route_ambiguous_query(self, router):
        """Ambiguous query should route to GeneralFallbackAgent."""
        with patch.object(router, '_classify_with_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "mode": "single_agent",
                "agents": ["general_fallback"],
                "subtasks": [{"agent": "general_fallback", "query": "What's the weather?"}],
                "synthesis_strategy": "merge",
                "confidence": 0.60,
                "reasoning": "General query, not B2B specific.",
            }
            decision = await router.route("What's the weather today?")
            assert AgentType.GENERAL_FALLBACK in decision.agents

    @pytest.mark.asyncio
    async def test_route_multi_agent_query(self, router):
        """Complex query should route to multiple agents."""
        with patch.object(router, '_classify_with_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "mode": "multi_agent",
                "agents": ["company_research", "financial_analyst"],
                "subtasks": [
                    {"agent": "company_research", "query": "What does Apple do?"},
                    {"agent": "financial_analyst", "query": "What is Apple's market cap?"},
                ],
                "synthesis_strategy": "merge",
                "confidence": 0.85,
                "reasoning": "Query requires company info and financial data.",
            }
            decision = await router.route("Tell me about Apple and its market cap")
            assert decision.mode == "multi_agent"
            assert len(decision.agents) == 2


class TestQueryRouterFallback:
    """Tests for fallback and error handling."""

    @pytest.fixture
    def router(self):
        """Create router with mocked LLM client."""
        with patch('anthropic.Anthropic'):
            return QueryRouter()

    @pytest.mark.asyncio
    async def test_fallback_on_llm_error(self, router):
        """Should fallback to pattern matching on LLM error."""
        with patch.object(router, '_classify_with_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = Exception("API Error")
            decision = await router.route("When was Stripe founded?")
            # Should still route correctly using pattern matching
            assert decision is not None
            assert len(decision.agents) > 0

    @pytest.mark.asyncio
    async def test_fallback_on_invalid_response(self, router):
        """Should fallback on invalid LLM response."""
        with patch.object(router, '_classify_with_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {"invalid": "response"}
            decision = await router.route("When was Stripe founded?")
            # Should fallback to pattern matching
            assert decision is not None

    @pytest.mark.asyncio
    async def test_empty_query(self, router):
        """Empty query should route to fallback agent."""
        decision = await router.route("")
        assert AgentType.GENERAL_FALLBACK in decision.agents

    @pytest.mark.asyncio
    async def test_very_long_query(self, router):
        """Very long query should still be handled."""
        long_query = "Tell me about " + "Apple " * 500
        with patch.object(router, '_classify_with_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "mode": "single_agent",
                "agents": ["company_research"],
                "subtasks": [{"agent": "company_research", "query": long_query[:200]}],
                "synthesis_strategy": "merge",
                "confidence": 0.70,
                "reasoning": "Long query about Apple.",
            }
            decision = await router.route(long_query)
            assert decision is not None


class TestQueryRouterSubtaskDecomposition:
    """Tests for subtask decomposition."""

    @pytest.fixture
    def router(self):
        """Create router with mocked LLM client."""
        with patch('anthropic.Anthropic'):
            return QueryRouter()

    @pytest.mark.asyncio
    async def test_decompose_complex_query(self, router):
        """Complex query should be decomposed into subtasks."""
        with patch.object(router, '_classify_with_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "mode": "multi_agent",
                "agents": ["company_research", "financial_analyst", "competitive_intel"],
                "subtasks": [
                    {"agent": "company_research", "query": "What does Stripe do?"},
                    {"agent": "financial_analyst", "query": "What is Stripe's valuation?"},
                    {"agent": "competitive_intel", "query": "Who are Stripe's competitors?"},
                ],
                "synthesis_strategy": "merge",
                "confidence": 0.85,
                "reasoning": "Complex query requires multiple specialists.",
            }
            decision = await router.route(
                "Research Stripe: what they do, their valuation, and main competitors"
            )
            assert len(decision.subtasks) == 3
            assert len(decision.agents) == 3

    @pytest.mark.asyncio
    async def test_subtask_agent_matches(self, router):
        """Each subtask should be assigned to correct agent."""
        with patch.object(router, '_classify_with_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "mode": "multi_agent",
                "agents": ["company_research", "action_executor"],
                "subtasks": [
                    {"agent": "company_research", "query": "Research Stripe"},
                    {"agent": "action_executor", "query": "Email summary to team"},
                ],
                "synthesis_strategy": "sequential",
                "confidence": 0.88,
                "reasoning": "Research then email.",
            }
            decision = await router.route("Research Stripe and email the summary to my team")

            # Verify subtasks are assigned correctly
            company_subtask = next(
                (s for s in decision.subtasks if s["agent"] == AgentType.COMPANY_RESEARCH),
                None
            )
            action_subtask = next(
                (s for s in decision.subtasks if s["agent"] == AgentType.ACTION_EXECUTOR),
                None
            )
            assert company_subtask is not None
            assert action_subtask is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
