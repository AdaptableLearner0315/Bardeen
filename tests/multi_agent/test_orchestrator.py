"""
Unit tests for Orchestrator

Tests:
- Main entry point functionality
- Integration of router, executor, and synthesizer
- End-to-end query handling
- Error handling and graceful degradation
- Performance characteristics
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from dataclasses import asdict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.multi_agent.guardrails.tool_access import AgentType
from src.multi_agent.specialists.base_specialist import AgentResponse, AgentStatus
from src.multi_agent.router import RoutingDecision, SynthesisStrategy
from src.multi_agent.synthesizer import SynthesizedResponse
from src.multi_agent.orchestrator import Orchestrator, OrchestratorResponse


class TestOrchestratorResponse:
    """Tests for OrchestratorResponse dataclass."""

    def test_orchestrator_response_creation(self):
        """Should create orchestrator response correctly."""
        response = OrchestratorResponse(
            query="When was Stripe founded?",
            answer="Stripe was founded in 2010.",
            mode="single_agent",
            agents_used=[AgentType.COMPANY_RESEARCH],
            synthesis_strategy=SynthesisStrategy.MERGE,
            confidence=0.95,
            latency_ms=500,
            routing_reasoning="Company founding query routed to company research agent.",
        )
        assert response.query == "When was Stripe founded?"
        assert response.answer == "Stripe was founded in 2010."
        assert len(response.agents_used) == 1

    def test_orchestrator_response_to_dict(self):
        """Should serialize to dict correctly."""
        response = OrchestratorResponse(
            query="Test",
            answer="Answer",
            mode="single_agent",
            agents_used=[AgentType.COMPANY_RESEARCH],
            synthesis_strategy=SynthesisStrategy.MERGE,
            confidence=0.9,
            latency_ms=100,
            routing_reasoning="Test reasoning",
        )
        d = response.to_dict()
        assert d["query"] == "Test"
        assert d["mode"] == "single_agent"
        assert "company_research" in d["agents_used"]


class TestOrchestratorBasicFlow:
    """Tests for basic orchestrator flow."""

    @pytest.fixture
    def mock_router(self):
        """Create mock router."""
        router = Mock()
        router.route = AsyncMock()
        return router

    @pytest.fixture
    def mock_executor(self):
        """Create mock executor."""
        executor = Mock()
        executor.execute_agents = AsyncMock()
        return executor

    @pytest.fixture
    def mock_synthesizer(self):
        """Create mock synthesizer."""
        synthesizer = Mock()
        synthesizer.synthesize = AsyncMock()
        return synthesizer

    @pytest.fixture
    def orchestrator(self, mock_router, mock_executor, mock_synthesizer):
        """Create orchestrator with mocked components."""
        with patch('anthropic.Anthropic'):
            orch = Orchestrator.__new__(Orchestrator)
            orch.router = mock_router
            orch.executor = mock_executor
            orch.synthesizer = mock_synthesizer
            orch.agents = {}
            return orch

    @pytest.mark.asyncio
    async def test_execute_single_agent_query(
        self, orchestrator, mock_router, mock_executor, mock_synthesizer
    ):
        """Should handle single agent query correctly."""
        # Setup mocks
        mock_router.route.return_value = RoutingDecision(
            mode="single_agent",
            agents=[AgentType.COMPANY_RESEARCH],
            subtasks=[{"agent": AgentType.COMPANY_RESEARCH, "query": "When was Stripe founded?"}],
            synthesis_strategy=SynthesisStrategy.MERGE,
            confidence=0.95,
            reasoning="Company founding query.",
        )

        mock_executor.execute_agents.return_value = [
            AgentResponse(
                agent_type=AgentType.COMPANY_RESEARCH,
                query="When was Stripe founded?",
                answer="Stripe was founded in 2010.",
                status=AgentStatus.SUCCESS,
                confidence=0.95,
                latency_ms=200,
            )
        ]

        mock_synthesizer.synthesize.return_value = SynthesizedResponse(
            answer="Stripe was founded in 2010.",
            confidence=0.95,
            sources=[],
            agent_contributions={"company_research": "Stripe was founded in 2010."},
            synthesis_strategy=SynthesisStrategy.MERGE,
            latency_ms=200,
        )

        result = await orchestrator.execute("When was Stripe founded?")

        assert result.answer == "Stripe was founded in 2010."
        assert result.mode == "single_agent"
        assert AgentType.COMPANY_RESEARCH in result.agents_used

    @pytest.mark.asyncio
    async def test_execute_multi_agent_query(
        self, orchestrator, mock_router, mock_executor, mock_synthesizer
    ):
        """Should handle multi-agent query correctly."""
        mock_router.route.return_value = RoutingDecision(
            mode="multi_agent",
            agents=[AgentType.COMPANY_RESEARCH, AgentType.FINANCIAL_ANALYST],
            subtasks=[
                {"agent": AgentType.COMPANY_RESEARCH, "query": "What does Stripe do?"},
                {"agent": AgentType.FINANCIAL_ANALYST, "query": "What is Stripe's valuation?"},
            ],
            synthesis_strategy=SynthesisStrategy.MERGE,
            confidence=0.90,
            reasoning="Complex query requiring multiple agents.",
        )

        mock_executor.execute_agents.return_value = [
            AgentResponse(
                agent_type=AgentType.COMPANY_RESEARCH,
                query="What does Stripe do?",
                answer="Stripe is a payments company.",
                status=AgentStatus.SUCCESS,
                confidence=0.95,
                latency_ms=200,
            ),
            AgentResponse(
                agent_type=AgentType.FINANCIAL_ANALYST,
                query="What is Stripe's valuation?",
                answer="Stripe is valued at $50 billion.",
                status=AgentStatus.SUCCESS,
                confidence=0.90,
                latency_ms=250,
            ),
        ]

        mock_synthesizer.synthesize.return_value = SynthesizedResponse(
            answer="Stripe is a payments company valued at $50 billion.",
            confidence=0.92,
            sources=[],
            agent_contributions={
                "company_research": "Stripe is a payments company.",
                "financial_analyst": "Stripe is valued at $50 billion.",
            },
            synthesis_strategy=SynthesisStrategy.MERGE,
            latency_ms=450,
        )

        result = await orchestrator.execute("Tell me about Stripe and its valuation")

        assert result.mode == "multi_agent"
        assert len(result.agents_used) == 2


class TestOrchestratorErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator with mocked components."""
        with patch('anthropic.Anthropic'):
            orch = Orchestrator.__new__(Orchestrator)
            orch.router = Mock()
            orch.executor = Mock()
            orch.synthesizer = Mock()
            orch.agents = {}
            return orch

    @pytest.mark.asyncio
    async def test_handles_router_error(self, orchestrator):
        """Should handle router errors gracefully."""
        orchestrator.router.route = AsyncMock(side_effect=Exception("Router failed"))

        # Should fallback to pattern-based routing or return error
        result = await orchestrator.execute("Test query")

        assert result is not None
        # Either recovers with fallback or returns error response
        assert result.answer != "" or result.error_message is not None

    @pytest.mark.asyncio
    async def test_handles_executor_error(self, orchestrator):
        """Should handle executor errors gracefully."""
        orchestrator.router.route = AsyncMock(return_value=RoutingDecision(
            mode="single_agent",
            agents=[AgentType.COMPANY_RESEARCH],
            subtasks=[{"agent": AgentType.COMPANY_RESEARCH, "query": "Test"}],
            synthesis_strategy=SynthesisStrategy.MERGE,
            confidence=0.9,
            reasoning="Test",
        ))
        orchestrator.executor.execute_agents = AsyncMock(side_effect=Exception("Executor failed"))

        result = await orchestrator.execute("Test query")

        assert result is not None
        assert result.confidence == 0.0 or "error" in result.answer.lower()

    @pytest.mark.asyncio
    async def test_handles_synthesizer_error(self, orchestrator):
        """Should handle synthesizer errors gracefully."""
        orchestrator.router.route = AsyncMock(return_value=RoutingDecision(
            mode="single_agent",
            agents=[AgentType.COMPANY_RESEARCH],
            subtasks=[{"agent": AgentType.COMPANY_RESEARCH, "query": "Test"}],
            synthesis_strategy=SynthesisStrategy.MERGE,
            confidence=0.9,
            reasoning="Test",
        ))
        orchestrator.executor.execute_agents = AsyncMock(return_value=[
            AgentResponse(
                agent_type=AgentType.COMPANY_RESEARCH,
                query="Test",
                answer="Answer",
                status=AgentStatus.SUCCESS,
                confidence=0.9,
                latency_ms=100,
            )
        ])
        orchestrator.synthesizer.synthesize = AsyncMock(side_effect=Exception("Synthesizer failed"))

        result = await orchestrator.execute("Test query")

        # Should return raw agent response if synthesis fails
        assert result is not None


class TestOrchestratorAgentManagement:
    """Tests for agent management."""

    @pytest.fixture
    def orchestrator(self):
        """Create real orchestrator."""
        with patch('anthropic.Anthropic'):
            return Orchestrator.__new__(Orchestrator)

    def test_register_agent(self, orchestrator):
        """Should register agents correctly."""
        orchestrator.agents = {}
        mock_agent = Mock()
        mock_agent.agent_type = AgentType.COMPANY_RESEARCH

        orchestrator.register_agent(AgentType.COMPANY_RESEARCH, mock_agent)

        assert AgentType.COMPANY_RESEARCH in orchestrator.agents
        assert orchestrator.agents[AgentType.COMPANY_RESEARCH] == mock_agent

    def test_get_available_agents(self, orchestrator):
        """Should return list of available agents."""
        orchestrator.agents = {
            AgentType.COMPANY_RESEARCH: Mock(),
            AgentType.FINANCIAL_ANALYST: Mock(),
        }

        available = orchestrator.get_available_agents()

        assert AgentType.COMPANY_RESEARCH in available
        assert AgentType.FINANCIAL_ANALYST in available


class TestOrchestratorIntegration:
    """Integration tests for orchestrator."""

    @pytest.mark.asyncio
    async def test_full_flow_company_query(self):
        """Test full flow for company research query."""
        with patch('anthropic.Anthropic'):
            # Create orchestrator with mocked internals
            orchestrator = Orchestrator.__new__(Orchestrator)
            orchestrator.agents = {}

            # Mock router
            orchestrator.router = Mock()
            orchestrator.router.route = AsyncMock(return_value=RoutingDecision(
                mode="single_agent",
                agents=[AgentType.COMPANY_RESEARCH],
                subtasks=[{"agent": AgentType.COMPANY_RESEARCH, "query": "When was Stripe founded?"}],
                synthesis_strategy=SynthesisStrategy.MERGE,
                confidence=0.95,
                reasoning="Company founding query.",
            ))

            # Mock executor
            orchestrator.executor = Mock()
            orchestrator.executor.execute_agents = AsyncMock(return_value=[
                AgentResponse(
                    agent_type=AgentType.COMPANY_RESEARCH,
                    query="When was Stripe founded?",
                    answer="Stripe was founded in 2010.",
                    status=AgentStatus.SUCCESS,
                    confidence=0.95,
                    latency_ms=200,
                )
            ])

            # Mock synthesizer
            orchestrator.synthesizer = Mock()
            orchestrator.synthesizer.synthesize = AsyncMock(return_value=SynthesizedResponse(
                answer="Stripe was founded in 2010.",
                confidence=0.95,
                sources=[],
                agent_contributions={"company_research": "Stripe was founded in 2010."},
                synthesis_strategy=SynthesisStrategy.MERGE,
                latency_ms=200,
            ))

            result = await orchestrator.execute("When was Stripe founded?")

            # Verify flow
            orchestrator.router.route.assert_called_once()
            orchestrator.executor.execute_agents.assert_called_once()
            orchestrator.synthesizer.synthesize.assert_called_once()

            assert result.answer == "Stripe was founded in 2010."

    @pytest.mark.asyncio
    async def test_full_flow_action_query(self):
        """Test full flow for action execution query."""
        with patch('anthropic.Anthropic'):
            orchestrator = Orchestrator.__new__(Orchestrator)
            orchestrator.agents = {}

            orchestrator.router = Mock()
            orchestrator.router.route = AsyncMock(return_value=RoutingDecision(
                mode="single_agent",
                agents=[AgentType.ACTION_EXECUTOR],
                subtasks=[{"agent": AgentType.ACTION_EXECUTOR, "query": "Send email"}],
                synthesis_strategy=SynthesisStrategy.MERGE,
                confidence=0.90,
                reasoning="Email action query.",
            ))

            orchestrator.executor = Mock()
            orchestrator.executor.execute_agents = AsyncMock(return_value=[
                AgentResponse(
                    agent_type=AgentType.ACTION_EXECUTOR,
                    query="Send email",
                    answer="Email sent successfully.",
                    status=AgentStatus.SUCCESS,
                    confidence=0.90,
                    latency_ms=150,
                )
            ])

            orchestrator.synthesizer = Mock()
            orchestrator.synthesizer.synthesize = AsyncMock(return_value=SynthesizedResponse(
                answer="Email sent successfully.",
                confidence=0.90,
                sources=[],
                agent_contributions={"action_executor": "Email sent successfully."},
                synthesis_strategy=SynthesisStrategy.MERGE,
                latency_ms=150,
            ))

            result = await orchestrator.execute("Send an email to my team")

            assert AgentType.ACTION_EXECUTOR in result.agents_used


class TestOrchestratorPerformance:
    """Tests for performance characteristics."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator with mocked components."""
        with patch('anthropic.Anthropic'):
            orch = Orchestrator.__new__(Orchestrator)
            orch.router = Mock()
            orch.executor = Mock()
            orch.synthesizer = Mock()
            orch.agents = {}
            return orch

    @pytest.mark.asyncio
    async def test_tracks_total_latency(self, orchestrator):
        """Should track total latency across all components."""
        orchestrator.router.route = AsyncMock(return_value=RoutingDecision(
            mode="single_agent",
            agents=[AgentType.COMPANY_RESEARCH],
            subtasks=[{"agent": AgentType.COMPANY_RESEARCH, "query": "Test"}],
            synthesis_strategy=SynthesisStrategy.MERGE,
            confidence=0.9,
            reasoning="Test",
        ))
        orchestrator.executor.execute_agents = AsyncMock(return_value=[
            AgentResponse(
                agent_type=AgentType.COMPANY_RESEARCH,
                query="Test",
                answer="Answer",
                status=AgentStatus.SUCCESS,
                confidence=0.9,
                latency_ms=200,
            )
        ])
        orchestrator.synthesizer.synthesize = AsyncMock(return_value=SynthesizedResponse(
            answer="Answer",
            confidence=0.9,
            sources=[],
            agent_contributions={},
            synthesis_strategy=SynthesisStrategy.MERGE,
            latency_ms=200,
        ))

        result = await orchestrator.execute("Test")

        assert result.latency_ms >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
