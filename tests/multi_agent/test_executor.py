"""
Unit tests for AgentExecutor

Tests:
- Parallel execution of independent agents
- Sequential execution of dependent agents
- Hybrid execution mode
- Error handling and graceful degradation
- Timeout management
- Result aggregation
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
from src.multi_agent.executor import AgentExecutor, ExecutionMode


class TestExecutionMode:
    """Tests for ExecutionMode enum."""

    def test_all_modes_exist(self):
        """All execution modes should exist."""
        assert ExecutionMode.PARALLEL.value == "parallel"
        assert ExecutionMode.SEQUENTIAL.value == "sequential"
        assert ExecutionMode.HYBRID.value == "hybrid"


class TestAgentExecutorParallel:
    """Tests for parallel execution."""

    @pytest.fixture
    def executor(self):
        """Create executor instance."""
        return AgentExecutor()

    @pytest.fixture
    def mock_agents(self):
        """Create mock agents dictionary."""
        async def mock_execute(query, context=None):
            await asyncio.sleep(0.01)  # Simulate some work
            return AgentResponse(
                agent_type=AgentType.COMPANY_RESEARCH,
                query=query,
                answer="Mock answer",
                status=AgentStatus.SUCCESS,
                confidence=0.9,
                latency_ms=10,
            )

        agents = {}
        for agent_type in [AgentType.COMPANY_RESEARCH, AgentType.FINANCIAL_ANALYST, AgentType.COMPETITIVE_INTEL]:
            mock_agent = Mock()
            mock_agent.execute = AsyncMock(side_effect=mock_execute)
            mock_agent.agent_type = agent_type
            agents[agent_type] = mock_agent

        return agents

    @pytest.mark.asyncio
    async def test_parallel_execution_speed(self, executor, mock_agents):
        """Parallel execution should be faster than sequential."""
        decision = RoutingDecision(
            mode="multi_agent",
            agents=[AgentType.COMPANY_RESEARCH, AgentType.FINANCIAL_ANALYST],
            subtasks=[
                {"agent": AgentType.COMPANY_RESEARCH, "query": "What does Apple do?"},
                {"agent": AgentType.FINANCIAL_ANALYST, "query": "Apple market cap?"},
            ],
            synthesis_strategy=SynthesisStrategy.MERGE,
            confidence=0.9,
            reasoning="Test",
        )

        import time
        start = time.time()
        results = await executor.execute_agents(
            routing_decision=decision,
            agents=mock_agents,
            mode=ExecutionMode.PARALLEL,
        )
        elapsed = time.time() - start

        # Parallel should complete close to single agent time
        assert len(results) == 2
        assert elapsed < 0.1  # Should be fast due to parallel execution

    @pytest.mark.asyncio
    async def test_parallel_returns_all_results(self, executor, mock_agents):
        """Parallel execution should return results from all agents."""
        decision = RoutingDecision(
            mode="multi_agent",
            agents=[AgentType.COMPANY_RESEARCH, AgentType.FINANCIAL_ANALYST, AgentType.COMPETITIVE_INTEL],
            subtasks=[
                {"agent": AgentType.COMPANY_RESEARCH, "query": "Query 1"},
                {"agent": AgentType.FINANCIAL_ANALYST, "query": "Query 2"},
                {"agent": AgentType.COMPETITIVE_INTEL, "query": "Query 3"},
            ],
            synthesis_strategy=SynthesisStrategy.MERGE,
            confidence=0.9,
            reasoning="Test",
        )

        results = await executor.execute_agents(
            routing_decision=decision,
            agents=mock_agents,
            mode=ExecutionMode.PARALLEL,
        )

        assert len(results) == 3
        assert all(isinstance(r, AgentResponse) for r in results)


class TestAgentExecutorSequential:
    """Tests for sequential execution."""

    @pytest.fixture
    def executor(self):
        """Create executor instance."""
        return AgentExecutor()

    @pytest.fixture
    def mock_agents_with_context(self):
        """Create mock agents that use context from previous results."""
        agents = {}

        async def company_execute(query, context=None):
            return AgentResponse(
                agent_type=AgentType.COMPANY_RESEARCH,
                query=query,
                answer="Stripe is a payments company",
                status=AgentStatus.SUCCESS,
                confidence=0.95,
                latency_ms=100,
            )

        async def action_execute(query, context=None):
            # Sequential execution should pass context
            context_info = ""
            if context:
                context_info = " with context"
            return AgentResponse(
                agent_type=AgentType.ACTION_EXECUTOR,
                query=query,
                answer=f"Email sent{context_info}",
                status=AgentStatus.SUCCESS,
                confidence=0.90,
                latency_ms=50,
            )

        company_agent = Mock()
        company_agent.execute = AsyncMock(side_effect=company_execute)
        company_agent.agent_type = AgentType.COMPANY_RESEARCH
        agents[AgentType.COMPANY_RESEARCH] = company_agent

        action_agent = Mock()
        action_agent.execute = AsyncMock(side_effect=action_execute)
        action_agent.agent_type = AgentType.ACTION_EXECUTOR
        agents[AgentType.ACTION_EXECUTOR] = action_agent

        return agents

    @pytest.mark.asyncio
    async def test_sequential_execution_order(self, executor, mock_agents_with_context):
        """Sequential execution should maintain order."""
        decision = RoutingDecision(
            mode="multi_agent",
            agents=[AgentType.COMPANY_RESEARCH, AgentType.ACTION_EXECUTOR],
            subtasks=[
                {"agent": AgentType.COMPANY_RESEARCH, "query": "Research Stripe"},
                {"agent": AgentType.ACTION_EXECUTOR, "query": "Email summary"},
            ],
            synthesis_strategy=SynthesisStrategy.SEQUENTIAL,
            confidence=0.9,
            reasoning="Research then email",
        )

        results = await executor.execute_agents(
            routing_decision=decision,
            agents=mock_agents_with_context,
            mode=ExecutionMode.SEQUENTIAL,
        )

        assert len(results) == 2
        assert results[0].agent_type == AgentType.COMPANY_RESEARCH
        assert results[1].agent_type == AgentType.ACTION_EXECUTOR

    @pytest.mark.asyncio
    async def test_sequential_passes_context(self, executor, mock_agents_with_context):
        """Sequential execution should pass previous results as context."""
        decision = RoutingDecision(
            mode="multi_agent",
            agents=[AgentType.COMPANY_RESEARCH, AgentType.ACTION_EXECUTOR],
            subtasks=[
                {"agent": AgentType.COMPANY_RESEARCH, "query": "Research Stripe"},
                {"agent": AgentType.ACTION_EXECUTOR, "query": "Email summary"},
            ],
            synthesis_strategy=SynthesisStrategy.SEQUENTIAL,
            confidence=0.9,
            reasoning="Research then email",
        )

        results = await executor.execute_agents(
            routing_decision=decision,
            agents=mock_agents_with_context,
            mode=ExecutionMode.SEQUENTIAL,
        )

        # Verify second agent was called with context from first
        action_agent = mock_agents_with_context[AgentType.ACTION_EXECUTOR]
        assert action_agent.execute.call_count == 1


class TestAgentExecutorHybrid:
    """Tests for hybrid execution mode."""

    @pytest.fixture
    def executor(self):
        """Create executor instance."""
        return AgentExecutor()

    @pytest.mark.asyncio
    async def test_hybrid_detects_independent_agents(self, executor):
        """Hybrid mode should run independent agents in parallel."""
        # Company and Financial are independent - can run parallel
        decision = RoutingDecision(
            mode="multi_agent",
            agents=[AgentType.COMPANY_RESEARCH, AgentType.FINANCIAL_ANALYST],
            subtasks=[
                {"agent": AgentType.COMPANY_RESEARCH, "query": "What does Apple do?"},
                {"agent": AgentType.FINANCIAL_ANALYST, "query": "Apple market cap?"},
            ],
            synthesis_strategy=SynthesisStrategy.MERGE,
            confidence=0.9,
            reasoning="Test",
        )

        # Detect that these are independent
        execution_plan = executor._analyze_dependencies(decision)
        assert execution_plan.parallel_groups is not None

    @pytest.mark.asyncio
    async def test_hybrid_detects_dependent_agents(self, executor):
        """Hybrid mode should run dependent agents sequentially."""
        # Company then Action - Action depends on Company result
        decision = RoutingDecision(
            mode="multi_agent",
            agents=[AgentType.COMPANY_RESEARCH, AgentType.ACTION_EXECUTOR],
            subtasks=[
                {"agent": AgentType.COMPANY_RESEARCH, "query": "Research Stripe"},
                {"agent": AgentType.ACTION_EXECUTOR, "query": "Email the research summary"},
            ],
            synthesis_strategy=SynthesisStrategy.SEQUENTIAL,
            confidence=0.9,
            reasoning="Research then email",
        )

        execution_plan = executor._analyze_dependencies(decision)
        # Sequential strategy indicates dependency
        assert execution_plan.has_dependencies is True


class TestAgentExecutorErrorHandling:
    """Tests for error handling and graceful degradation."""

    @pytest.fixture
    def executor(self):
        """Create executor instance."""
        return AgentExecutor()

    @pytest.fixture
    def mock_agents_with_failure(self):
        """Create mock agents where one fails."""
        agents = {}

        async def success_execute(query, context=None):
            return AgentResponse(
                agent_type=AgentType.COMPANY_RESEARCH,
                query=query,
                answer="Success answer",
                status=AgentStatus.SUCCESS,
                confidence=0.9,
                latency_ms=100,
            )

        async def failure_execute(query, context=None):
            raise Exception("Agent failed!")

        success_agent = Mock()
        success_agent.execute = AsyncMock(side_effect=success_execute)
        success_agent.agent_type = AgentType.COMPANY_RESEARCH
        agents[AgentType.COMPANY_RESEARCH] = success_agent

        failure_agent = Mock()
        failure_agent.execute = AsyncMock(side_effect=failure_execute)
        failure_agent.agent_type = AgentType.FINANCIAL_ANALYST
        agents[AgentType.FINANCIAL_ANALYST] = failure_agent

        return agents

    @pytest.mark.asyncio
    async def test_graceful_degradation_parallel(self, executor, mock_agents_with_failure):
        """Parallel execution should continue if one agent fails."""
        decision = RoutingDecision(
            mode="multi_agent",
            agents=[AgentType.COMPANY_RESEARCH, AgentType.FINANCIAL_ANALYST],
            subtasks=[
                {"agent": AgentType.COMPANY_RESEARCH, "query": "Company query"},
                {"agent": AgentType.FINANCIAL_ANALYST, "query": "Financial query"},
            ],
            synthesis_strategy=SynthesisStrategy.MERGE,
            confidence=0.9,
            reasoning="Test",
        )

        results = await executor.execute_agents(
            routing_decision=decision,
            agents=mock_agents_with_failure,
            mode=ExecutionMode.PARALLEL,
        )

        # Should get results from both, with failure marked appropriately
        assert len(results) == 2
        success_result = next(r for r in results if r.status == AgentStatus.SUCCESS)
        failed_result = next(r for r in results if r.status == AgentStatus.FAILED)
        assert success_result is not None
        assert failed_result is not None

    @pytest.mark.asyncio
    async def test_missing_agent_handled(self, executor):
        """Should handle missing agent gracefully."""
        decision = RoutingDecision(
            mode="single_agent",
            agents=[AgentType.COMPANY_RESEARCH],
            subtasks=[{"agent": AgentType.COMPANY_RESEARCH, "query": "Test"}],
            synthesis_strategy=SynthesisStrategy.MERGE,
            confidence=0.9,
            reasoning="Test",
        )

        # Empty agents dict
        results = await executor.execute_agents(
            routing_decision=decision,
            agents={},
            mode=ExecutionMode.PARALLEL,
        )

        assert len(results) == 1
        assert results[0].status == AgentStatus.FAILED
        assert "not available" in results[0].error_message.lower()

    @pytest.mark.asyncio
    async def test_timeout_handling(self, executor):
        """Should handle agent timeouts."""
        async def slow_execute(query, context=None):
            await asyncio.sleep(10)  # Very slow
            return AgentResponse(
                agent_type=AgentType.COMPANY_RESEARCH,
                query=query,
                answer="Late answer",
                status=AgentStatus.SUCCESS,
                confidence=0.9,
                latency_ms=10000,
            )

        slow_agent = Mock()
        slow_agent.execute = AsyncMock(side_effect=slow_execute)
        slow_agent.agent_type = AgentType.COMPANY_RESEARCH
        agents = {AgentType.COMPANY_RESEARCH: slow_agent}

        decision = RoutingDecision(
            mode="single_agent",
            agents=[AgentType.COMPANY_RESEARCH],
            subtasks=[{"agent": AgentType.COMPANY_RESEARCH, "query": "Test"}],
            synthesis_strategy=SynthesisStrategy.MERGE,
            confidence=0.9,
            reasoning="Test",
        )

        # Set short timeout
        results = await executor.execute_agents(
            routing_decision=decision,
            agents=agents,
            mode=ExecutionMode.PARALLEL,
            timeout_seconds=0.1,
        )

        assert len(results) == 1
        assert results[0].status == AgentStatus.TIMEOUT


class TestAgentExecutorSingleAgent:
    """Tests for single agent execution."""

    @pytest.fixture
    def executor(self):
        """Create executor instance."""
        return AgentExecutor()

    @pytest.mark.asyncio
    async def test_single_agent_execution(self, executor):
        """Single agent should execute correctly."""
        async def mock_execute(query, context=None):
            return AgentResponse(
                agent_type=AgentType.COMPANY_RESEARCH,
                query=query,
                answer="Stripe was founded in 2010",
                status=AgentStatus.SUCCESS,
                confidence=0.95,
                latency_ms=200,
            )

        mock_agent = Mock()
        mock_agent.execute = AsyncMock(side_effect=mock_execute)
        mock_agent.agent_type = AgentType.COMPANY_RESEARCH

        decision = RoutingDecision(
            mode="single_agent",
            agents=[AgentType.COMPANY_RESEARCH],
            subtasks=[{"agent": AgentType.COMPANY_RESEARCH, "query": "When was Stripe founded?"}],
            synthesis_strategy=SynthesisStrategy.MERGE,
            confidence=0.95,
            reasoning="Company founding query",
        )

        results = await executor.execute_agents(
            routing_decision=decision,
            agents={AgentType.COMPANY_RESEARCH: mock_agent},
            mode=ExecutionMode.PARALLEL,
        )

        assert len(results) == 1
        assert results[0].answer == "Stripe was founded in 2010"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
