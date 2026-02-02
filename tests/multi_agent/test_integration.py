"""
Integration Tests for Multi-Agent System

Tests critical integration points:
- Router → Executor → Synthesizer pipeline
- Orchestrator coordination
- Guardrails integration
- Tool access enforcement
- Error propagation and handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

from src.multi_agent.orchestrator import Orchestrator, OrchestratorResponse
from src.multi_agent.router import QueryRouter, RoutingDecision, SynthesisStrategy
from src.multi_agent.executor import AgentExecutor, ExecutionMode
from src.multi_agent.synthesizer import ResponseSynthesizer, SynthesizedResponse
from src.multi_agent.guardrails.tool_access import AgentType, ToolAccessMatrix
from src.multi_agent.guardrails.input_validator import InputValidator
from src.multi_agent.guardrails.output_validator import OutputValidator
from src.multi_agent.specialists.base_specialist import AgentResponse, AgentStatus


class TestRouterExecutorIntegration:
    """Tests for Router → Executor integration."""

    @pytest.fixture
    def router(self):
        """Create router with mocked LLM."""
        with patch('anthropic.Anthropic'):
            return QueryRouter()

    @pytest.fixture
    def executor(self):
        """Create executor instance."""
        return AgentExecutor(timeout_seconds=5.0)

    def test_router_output_compatible_with_executor(self, router):
        """Router output should be consumable by Executor."""
        # Get routing decision using pattern-based classification
        decision = router._classify_with_patterns("When was Apple founded?")

        # Verify it has all fields executor needs
        assert hasattr(decision, 'agents')
        assert hasattr(decision, 'subtasks')
        assert hasattr(decision, 'synthesis_strategy')
        assert isinstance(decision.agents, list)
        assert isinstance(decision.subtasks, list)

    @pytest.mark.asyncio
    async def test_executor_handles_router_single_agent(self, router, executor):
        """Executor should handle single-agent routing decisions."""
        decision = RoutingDecision(
            mode="single_agent",
            agents=[AgentType.COMPANY_RESEARCH],
            subtasks=[{"agent": AgentType.COMPANY_RESEARCH, "query": "Test"}],
            synthesis_strategy=SynthesisStrategy.MERGE,
            confidence=0.9,
            reasoning="Test",
        )

        # Create mock agent
        mock_agent = MagicMock()
        mock_agent.execute = AsyncMock(return_value=AgentResponse(
            agent_type=AgentType.COMPANY_RESEARCH,
            query="Test",
            answer="Test answer",
            status=AgentStatus.SUCCESS,
            confidence=0.9,
            latency_ms=100,
        ))

        agents = {AgentType.COMPANY_RESEARCH: mock_agent}

        responses = await executor.execute_agents(decision, agents)

        assert len(responses) == 1
        assert responses[0].agent_type == AgentType.COMPANY_RESEARCH

    @pytest.mark.asyncio
    async def test_executor_handles_router_multi_agent(self, router, executor):
        """Executor should handle multi-agent routing decisions."""
        decision = RoutingDecision(
            mode="multi_agent",
            agents=[AgentType.COMPANY_RESEARCH, AgentType.FINANCIAL_ANALYST],
            subtasks=[
                {"agent": AgentType.COMPANY_RESEARCH, "query": "Company info"},
                {"agent": AgentType.FINANCIAL_ANALYST, "query": "Financial data"},
            ],
            synthesis_strategy=SynthesisStrategy.MERGE,
            confidence=0.85,
            reasoning="Multi-intent query",
        )

        # Create mock agents
        def create_mock_agent(agent_type):
            mock = MagicMock()
            mock.execute = AsyncMock(return_value=AgentResponse(
                agent_type=agent_type,
                query="Test",
                answer=f"{agent_type.value} answer",
                status=AgentStatus.SUCCESS,
                confidence=0.9,
                latency_ms=100,
            ))
            return mock

        agents = {
            AgentType.COMPANY_RESEARCH: create_mock_agent(AgentType.COMPANY_RESEARCH),
            AgentType.FINANCIAL_ANALYST: create_mock_agent(AgentType.FINANCIAL_ANALYST),
        }

        responses = await executor.execute_agents(decision, agents)

        assert len(responses) == 2
        agent_types = {r.agent_type for r in responses}
        assert AgentType.COMPANY_RESEARCH in agent_types
        assert AgentType.FINANCIAL_ANALYST in agent_types


class TestExecutorSynthesizerIntegration:
    """Tests for Executor → Synthesizer integration."""

    @pytest.fixture
    def executor(self):
        """Create executor instance."""
        return AgentExecutor()

    @pytest.fixture
    def synthesizer(self):
        """Create synthesizer with mocked LLM."""
        with patch('anthropic.Anthropic'):
            return ResponseSynthesizer()

    @pytest.mark.asyncio
    async def test_executor_output_compatible_with_synthesizer(
        self, executor, synthesizer
    ):
        """Executor output should be consumable by Synthesizer."""
        # Create sample executor responses
        responses = [
            AgentResponse(
                agent_type=AgentType.COMPANY_RESEARCH,
                query="About Apple",
                answer="Apple was founded in 1976",
                status=AgentStatus.SUCCESS,
                confidence=0.95,
                sources=["wikipedia.org"],
                latency_ms=150,
            ),
            AgentResponse(
                agent_type=AgentType.FINANCIAL_ANALYST,
                query="Apple market cap",
                answer="Apple's market cap is $3 trillion",
                status=AgentStatus.SUCCESS,
                confidence=0.90,
                sources=["finance.yahoo.com"],
                latency_ms=200,
            ),
        ]

        # Synthesize responses
        with patch.object(synthesizer, '_merge_with_llm', new_callable=AsyncMock) as mock:
            mock.return_value = "Apple was founded in 1976 and has a market cap of $3 trillion"
            result = await synthesizer.synthesize(responses, SynthesisStrategy.MERGE)

        assert isinstance(result, SynthesizedResponse)
        assert result.answer is not None
        assert len(result.sources) == 2

    @pytest.mark.asyncio
    async def test_synthesizer_handles_mixed_status_responses(self, synthesizer):
        """Synthesizer should handle mix of success and failed responses."""
        responses = [
            AgentResponse(
                agent_type=AgentType.COMPANY_RESEARCH,
                query="Test",
                answer="Good answer",
                status=AgentStatus.SUCCESS,
                confidence=0.9,
                latency_ms=100,
            ),
            AgentResponse(
                agent_type=AgentType.FINANCIAL_ANALYST,
                query="Test",
                answer="Error occurred",
                status=AgentStatus.FAILED,
                confidence=0.0,
                error_message="API error",
                latency_ms=50,
            ),
        ]

        with patch.object(synthesizer, '_merge_with_llm', new_callable=AsyncMock) as mock:
            mock.return_value = "Good answer (financial data unavailable)"
            result = await synthesizer.synthesize(responses, SynthesisStrategy.MERGE)

        assert result is not None
        # Should still produce result from successful response


class TestGuardrailsIntegration:
    """Tests for guardrails integration with the pipeline."""

    def test_input_validation_before_routing(self):
        """Input validation should run before routing."""
        # Valid query
        valid_result = InputValidator.validate("When was Apple founded?")
        assert valid_result.is_valid is True

        # Invalid query (empty)
        invalid_result = InputValidator.validate("")
        assert invalid_result.is_valid is False

        # Query with PII warning (still valid but flagged)
        pii_result = InputValidator.validate("My SSN is 123-45-6789")
        assert pii_result.is_valid is True
        assert len(pii_result.warnings) > 0

    def test_output_validation_after_synthesis(self):
        """Output validation should validate synthesized responses."""
        # High confidence response
        good_response = AgentResponse(
            agent_type=AgentType.COMPANY_RESEARCH,
            query="Test",
            answer="Apple was founded in 1976",
            status=AgentStatus.SUCCESS,
            confidence=0.9,
            latency_ms=100,
        )
        good_result = OutputValidator.validate(good_response)
        assert good_result.is_valid is True

        # Low confidence response
        low_conf_response = AgentResponse(
            agent_type=AgentType.COMPANY_RESEARCH,
            query="Test",
            answer="Maybe Apple was founded sometime",
            status=AgentStatus.SUCCESS,
            confidence=0.3,
            latency_ms=100,
        )
        low_conf_result = OutputValidator.validate(low_conf_response)
        assert low_conf_result.confidence_warning is True

    def test_tool_access_enforcement(self):
        """Tool access matrix should be enforced."""
        # Company Research can use web_search
        assert ToolAccessMatrix.can_access_tool(
            AgentType.COMPANY_RESEARCH, "web_search"
        ) is True

        # Company Research cannot use gmail
        assert ToolAccessMatrix.can_access_tool(
            AgentType.COMPANY_RESEARCH, "gmail"
        ) is False

        # Only Action Executor can use personal tools
        for agent_type in AgentType:
            if agent_type == AgentType.ACTION_EXECUTOR:
                assert ToolAccessMatrix.can_access_tool(agent_type, "gmail") is True
            elif agent_type != AgentType.ORCHESTRATOR:
                assert ToolAccessMatrix.can_access_tool(agent_type, "gmail") is False


class TestToolAccessEnforcement:
    """Tests for tool access enforcement across agents."""

    @pytest.mark.parametrize("agent_type,expected_tools", [
        (AgentType.COMPANY_RESEARCH, {"web_search", "wikipedia"}),
        (AgentType.FINANCIAL_ANALYST, {"web_search", "calculator", "perplexity_search"}),
        (AgentType.COMPETITIVE_INTEL, {"web_search", "perplexity_search"}),
        (AgentType.ACTION_EXECUTOR, {"gmail", "google_calendar", "calculator"}),
        (AgentType.GENERAL_FALLBACK, {"web_search", "wikipedia", "calculator", "perplexity_search"}),
    ])
    def test_agent_tool_access(self, agent_type, expected_tools):
        """Each agent should only have access to their designated tools."""
        allowed = ToolAccessMatrix.get_allowed_tools(agent_type)
        assert allowed == expected_tools

    def test_personal_tools_restricted(self):
        """Personal tools should only be accessible by Action Executor."""
        personal_tools = ToolAccessMatrix.PERSONAL_TOOLS

        for tool in personal_tools:
            # Only Action Executor should have access
            for agent_type in AgentType:
                if agent_type == AgentType.ACTION_EXECUTOR:
                    assert ToolAccessMatrix.can_access_tool(agent_type, tool) is True
                elif agent_type != AgentType.ORCHESTRATOR:
                    assert ToolAccessMatrix.can_access_tool(agent_type, tool) is False

    def test_tool_request_validation(self):
        """Tool request validation should provide clear error messages."""
        # Valid request
        allowed, msg = ToolAccessMatrix.validate_tool_request(
            AgentType.COMPANY_RESEARCH, "web_search"
        )
        assert allowed is True
        assert msg == ""

        # Invalid personal tool request
        allowed, msg = ToolAccessMatrix.validate_tool_request(
            AgentType.COMPANY_RESEARCH, "gmail"
        )
        assert allowed is False
        assert "personal tool" in msg.lower()

        # Unknown tool
        allowed, msg = ToolAccessMatrix.validate_tool_request(
            AgentType.COMPANY_RESEARCH, "unknown_tool"
        )
        assert allowed is False
        assert "unknown" in msg.lower()


class TestErrorPropagation:
    """Tests for error propagation through the pipeline."""

    @pytest.fixture
    def executor(self):
        """Create executor instance."""
        return AgentExecutor(timeout_seconds=1.0)

    @pytest.mark.asyncio
    async def test_agent_timeout_creates_timeout_response(self, executor):
        """Agent timeout should create TIMEOUT status response."""
        import asyncio

        decision = RoutingDecision(
            mode="single_agent",
            agents=[AgentType.COMPANY_RESEARCH],
            subtasks=[{"agent": AgentType.COMPANY_RESEARCH, "query": "Test"}],
            synthesis_strategy=SynthesisStrategy.MERGE,
            confidence=0.9,
            reasoning="Test",
        )

        # Create slow mock agent
        async def slow_execute(query, context=None):
            await asyncio.sleep(5)  # Longer than timeout
            return AgentResponse(
                agent_type=AgentType.COMPANY_RESEARCH,
                query=query,
                answer="Answer",
                status=AgentStatus.SUCCESS,
                confidence=0.9,
                latency_ms=5000,
            )

        mock_agent = MagicMock()
        mock_agent.execute = slow_execute

        agents = {AgentType.COMPANY_RESEARCH: mock_agent}

        responses = await executor.execute_agents(
            decision, agents, timeout_seconds=0.1
        )

        assert len(responses) == 1
        assert responses[0].status == AgentStatus.TIMEOUT

    @pytest.mark.asyncio
    async def test_agent_exception_creates_failed_response(self, executor):
        """Agent exception should create FAILED status response."""
        decision = RoutingDecision(
            mode="single_agent",
            agents=[AgentType.COMPANY_RESEARCH],
            subtasks=[{"agent": AgentType.COMPANY_RESEARCH, "query": "Test"}],
            synthesis_strategy=SynthesisStrategy.MERGE,
            confidence=0.9,
            reasoning="Test",
        )

        # Create failing mock agent
        mock_agent = MagicMock()
        mock_agent.execute = AsyncMock(side_effect=Exception("API Error"))

        agents = {AgentType.COMPANY_RESEARCH: mock_agent}

        responses = await executor.execute_agents(decision, agents)

        assert len(responses) == 1
        assert responses[0].status == AgentStatus.FAILED
        assert "API Error" in responses[0].error_message

    @pytest.mark.asyncio
    async def test_missing_agent_creates_error_response(self, executor):
        """Missing agent should create FAILED status response."""
        decision = RoutingDecision(
            mode="single_agent",
            agents=[AgentType.COMPANY_RESEARCH],
            subtasks=[{"agent": AgentType.COMPANY_RESEARCH, "query": "Test"}],
            synthesis_strategy=SynthesisStrategy.MERGE,
            confidence=0.9,
            reasoning="Test",
        )

        # Empty agents dict
        agents = {}

        responses = await executor.execute_agents(decision, agents)

        assert len(responses) == 1
        assert responses[0].status == AgentStatus.FAILED
        assert "not available" in responses[0].answer.lower()


class TestDependencyAnalysis:
    """Tests for execution dependency analysis."""

    @pytest.fixture
    def executor(self):
        """Create executor instance."""
        return AgentExecutor()

    def test_research_agents_are_parallel(self, executor):
        """Research agents should be detected as parallel-safe."""
        decision = RoutingDecision(
            mode="multi_agent",
            agents=[AgentType.COMPANY_RESEARCH, AgentType.FINANCIAL_ANALYST],
            subtasks=[
                {"agent": AgentType.COMPANY_RESEARCH, "query": "Company info"},
                {"agent": AgentType.FINANCIAL_ANALYST, "query": "Financial data"},
            ],
            synthesis_strategy=SynthesisStrategy.MERGE,
            confidence=0.9,
            reasoning="Test",
        )

        plan = executor._analyze_dependencies(decision)

        assert plan.has_dependencies is False
        assert len(plan.parallel_groups) > 0

    def test_action_executor_detected_as_dependent(self, executor):
        """Action executor with other agents should be detected as dependent."""
        decision = RoutingDecision(
            mode="multi_agent",
            agents=[AgentType.COMPANY_RESEARCH, AgentType.ACTION_EXECUTOR],
            subtasks=[
                {"agent": AgentType.COMPANY_RESEARCH, "query": "Research company"},
                {"agent": AgentType.ACTION_EXECUTOR, "query": "Email summary"},
            ],
            synthesis_strategy=SynthesisStrategy.SEQUENTIAL,
            confidence=0.9,
            reasoning="Test",
        )

        plan = executor._analyze_dependencies(decision)

        assert plan.has_dependencies is True
        # Action executor should be last in chain
        assert plan.dependency_chain[-1] == AgentType.ACTION_EXECUTOR

    def test_sequential_strategy_indicates_dependency(self, executor):
        """Sequential synthesis strategy should indicate dependencies."""
        decision = RoutingDecision(
            mode="multi_agent",
            agents=[AgentType.COMPANY_RESEARCH, AgentType.COMPETITIVE_INTEL],
            subtasks=[
                {"agent": AgentType.COMPANY_RESEARCH, "query": "Research company"},
                {"agent": AgentType.COMPETITIVE_INTEL, "query": "Find competitors"},
            ],
            synthesis_strategy=SynthesisStrategy.SEQUENTIAL,
            confidence=0.9,
            reasoning="Dependent tasks",
        )

        plan = executor._analyze_dependencies(decision)

        assert plan.has_dependencies is True
