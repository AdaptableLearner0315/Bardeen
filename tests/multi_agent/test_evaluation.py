"""
Tests for Multi-Agent Evaluation Module

Tests:
- Routing metrics accuracy calculations
- Agent utilization tracking
- Multi-agent harness functionality
- Category breakdown calculations
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

from src.multi_agent.evaluation.routing_metrics import (
    RoutingMetrics,
    RoutingAccuracyResult,
)
from src.multi_agent.evaluation.utilization_metrics import (
    UtilizationMetrics,
    AgentUtilizationResult,
)
from src.multi_agent.evaluation.multi_agent_harness import (
    MultiAgentEvaluationHarness,
    EvaluationQuestion,
    EvaluationResult,
)
from src.multi_agent.guardrails.tool_access import AgentType
from src.multi_agent.specialists.base_specialist import AgentStatus


class TestRoutingMetrics:
    """Tests for routing accuracy metrics."""

    def test_record_exact_match(self):
        """Should record exact match correctly."""
        metrics = RoutingMetrics()

        result = metrics.record_routing(
            query="When was Apple founded?",
            expected_agents=[AgentType.COMPANY_RESEARCH],
            actual_agents=[AgentType.COMPANY_RESEARCH],
        )

        assert result.is_correct is True
        assert result.partial_match_score == 1.0
        assert metrics.accuracy == 1.0

    def test_record_partial_match(self):
        """Should handle partial matches."""
        metrics = RoutingMetrics()

        result = metrics.record_routing(
            query="Company info and financials",
            expected_agents=[AgentType.COMPANY_RESEARCH, AgentType.FINANCIAL_ANALYST],
            actual_agents=[AgentType.COMPANY_RESEARCH],  # Missing one
        )

        assert result.is_correct is False
        assert 0 < result.partial_match_score < 1.0
        assert metrics.partial_matches == 1

    def test_record_no_match(self):
        """Should handle no matches."""
        metrics = RoutingMetrics()

        result = metrics.record_routing(
            query="Check my email",
            expected_agents=[AgentType.ACTION_EXECUTOR],
            actual_agents=[AgentType.GENERAL_FALLBACK],
        )

        assert result.is_correct is False
        assert result.partial_match_score == 0.0

    def test_accuracy_calculation(self):
        """Should calculate accuracy correctly."""
        metrics = RoutingMetrics()

        # 3 correct, 1 incorrect = 75% accuracy
        metrics.record_routing("q1", [AgentType.COMPANY_RESEARCH], [AgentType.COMPANY_RESEARCH])
        metrics.record_routing("q2", [AgentType.FINANCIAL_ANALYST], [AgentType.FINANCIAL_ANALYST])
        metrics.record_routing("q3", [AgentType.COMPETITIVE_INTEL], [AgentType.COMPETITIVE_INTEL])
        metrics.record_routing("q4", [AgentType.ACTION_EXECUTOR], [AgentType.GENERAL_FALLBACK])

        assert metrics.total_queries == 4
        assert metrics.correct_routes == 3
        assert metrics.accuracy == 0.75

    def test_category_accuracy(self):
        """Should track accuracy by category."""
        metrics = RoutingMetrics()

        metrics.record_routing("q1", [AgentType.COMPANY_RESEARCH], [AgentType.COMPANY_RESEARCH], "company")
        metrics.record_routing("q2", [AgentType.COMPANY_RESEARCH], [AgentType.GENERAL_FALLBACK], "company")
        metrics.record_routing("q3", [AgentType.FINANCIAL_ANALYST], [AgentType.FINANCIAL_ANALYST], "financial")

        assert metrics.get_category_accuracy("company") == 0.5
        assert metrics.get_category_accuracy("financial") == 1.0

    def test_agent_precision_recall(self):
        """Should calculate agent precision and recall."""
        metrics = RoutingMetrics()

        # COMPANY_RESEARCH: expected twice, got three times (1 false positive)
        metrics.record_routing("q1", [AgentType.COMPANY_RESEARCH], [AgentType.COMPANY_RESEARCH])
        metrics.record_routing("q2", [AgentType.COMPANY_RESEARCH], [AgentType.COMPANY_RESEARCH])
        metrics.record_routing("q3", [AgentType.FINANCIAL_ANALYST], [AgentType.COMPANY_RESEARCH])  # FP

        precision = metrics.get_agent_precision(AgentType.COMPANY_RESEARCH)
        recall = metrics.get_agent_recall(AgentType.COMPANY_RESEARCH)

        assert precision == 2/3  # 2 TP / (2 TP + 1 FP)
        assert recall == 1.0  # 2 TP / (2 TP + 0 FN)

    def test_to_dict(self):
        """Should convert to dictionary."""
        metrics = RoutingMetrics()
        metrics.record_routing("q1", [AgentType.COMPANY_RESEARCH], [AgentType.COMPANY_RESEARCH])

        result = metrics.to_dict()

        assert "accuracy" in result
        assert "total_queries" in result
        assert result["total_queries"] == 1


class TestUtilizationMetrics:
    """Tests for agent utilization metrics."""

    def test_record_invocation(self):
        """Should record agent invocations."""
        metrics = UtilizationMetrics()

        metrics.record_agent_invocation(
            agent_type=AgentType.COMPANY_RESEARCH,
            status=AgentStatus.SUCCESS,
            latency_ms=150.0,
        )

        result = metrics.get_agent_utilization(AgentType.COMPANY_RESEARCH)
        assert result.total_invocations == 1
        assert result.successful_invocations == 1
        assert result.avg_latency_ms == 150.0

    def test_success_failure_tracking(self):
        """Should track success and failure rates."""
        metrics = UtilizationMetrics()

        metrics.record_agent_invocation(AgentType.FINANCIAL_ANALYST, AgentStatus.SUCCESS, 100)
        metrics.record_agent_invocation(AgentType.FINANCIAL_ANALYST, AgentStatus.SUCCESS, 100)
        metrics.record_agent_invocation(AgentType.FINANCIAL_ANALYST, AgentStatus.FAILED, 50)
        metrics.record_agent_invocation(AgentType.FINANCIAL_ANALYST, AgentStatus.TIMEOUT, 30000)

        result = metrics.get_agent_utilization(AgentType.FINANCIAL_ANALYST)
        assert result.total_invocations == 4
        assert result.successful_invocations == 2
        assert result.failed_invocations == 1
        assert result.timeout_invocations == 1
        assert result.success_rate == 0.5

    def test_multi_agent_rate(self):
        """Should track multi-agent vs single-agent queries."""
        metrics = UtilizationMetrics()

        metrics.record_query_routing([AgentType.COMPANY_RESEARCH])  # Single
        metrics.record_query_routing([AgentType.COMPANY_RESEARCH, AgentType.FINANCIAL_ANALYST])  # Multi
        metrics.record_query_routing([AgentType.FINANCIAL_ANALYST])  # Single

        assert metrics.total_queries == 3
        assert metrics.single_agent_queries == 2
        assert metrics.multi_agent_queries == 1
        assert metrics.multi_agent_rate == 1/3

    def test_collaboration_patterns(self):
        """Should track multi-agent collaboration patterns."""
        metrics = UtilizationMetrics()

        metrics.record_query_routing([AgentType.COMPANY_RESEARCH, AgentType.FINANCIAL_ANALYST])
        metrics.record_query_routing([AgentType.COMPANY_RESEARCH, AgentType.FINANCIAL_ANALYST])
        metrics.record_query_routing([AgentType.COMPETITIVE_INTEL, AgentType.FINANCIAL_ANALYST])

        patterns = metrics.get_collaboration_patterns()

        # Most common pattern should be company_research+financial_analyst
        assert len(patterns) >= 1
        assert patterns[0][1] == 2  # Count of 2

    def test_to_dict(self):
        """Should convert to dictionary."""
        metrics = UtilizationMetrics()
        metrics.record_agent_invocation(AgentType.COMPANY_RESEARCH, AgentStatus.SUCCESS, 100)
        metrics.record_query_routing([AgentType.COMPANY_RESEARCH])

        result = metrics.to_dict()

        assert "total_queries" in result
        assert "multi_agent_rate" in result
        assert "agent_utilization" in result


class TestEvaluationQuestion:
    """Tests for EvaluationQuestion dataclass."""

    def test_question_creation(self):
        """Should create evaluation question."""
        question = EvaluationQuestion(
            id="q1",
            question="When was Apple founded?",
            category="company_research",
            expected_agents=[AgentType.COMPANY_RESEARCH],
            expected_answer_contains=["1976", "Steve Jobs"],
        )

        assert question.id == "q1"
        assert AgentType.COMPANY_RESEARCH in question.expected_agents


class TestMultiAgentHarness:
    """Tests for MultiAgentEvaluationHarness."""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator."""
        mock = MagicMock()
        mock.process = AsyncMock()
        return mock

    @pytest.fixture
    def harness(self, mock_orchestrator):
        """Create harness with mock orchestrator."""
        h = MultiAgentEvaluationHarness(orchestrator=mock_orchestrator)
        h._initialized = True
        return h

    @pytest.mark.asyncio
    async def test_evaluate_correct_routing(self, harness, mock_orchestrator):
        """Should evaluate correct routing."""
        from src.multi_agent.router import RoutingDecision, SynthesisStrategy

        @dataclass
        class MockResponse:
            routing_decision = RoutingDecision(
                mode="single_agent",
                agents=[AgentType.COMPANY_RESEARCH],
                subtasks=[],
                synthesis_strategy=SynthesisStrategy.MERGE,
                confidence=0.95,
                reasoning="Test",
            )
            synthesized = MagicMock()
            synthesized.answer = "Apple was founded in 1976 by Steve Jobs"
            agent_responses = []
            final_answer = "Apple was founded in 1976 by Steve Jobs"

        mock_orchestrator.process.return_value = MockResponse()

        question = EvaluationQuestion(
            id="q1",
            question="When was Apple founded?",
            category="company_research",
            expected_agents=[AgentType.COMPANY_RESEARCH],
            expected_answer_contains=["1976", "Steve Jobs"],
        )

        result = await harness.evaluate_question(question)

        assert result.routing_correct is True
        assert result.answer_quality_score == 1.0

    @pytest.mark.asyncio
    async def test_evaluate_incorrect_routing(self, harness, mock_orchestrator):
        """Should detect incorrect routing."""
        from src.multi_agent.router import RoutingDecision, SynthesisStrategy

        @dataclass
        class MockResponse:
            routing_decision = RoutingDecision(
                mode="single_agent",
                agents=[AgentType.GENERAL_FALLBACK],  # Wrong agent
                subtasks=[],
                synthesis_strategy=SynthesisStrategy.MERGE,
                confidence=0.5,
                reasoning="Test",
            )
            synthesized = MagicMock()
            synthesized.answer = "Apple was founded"
            agent_responses = []
            final_answer = "Apple was founded"

        mock_orchestrator.process.return_value = MockResponse()

        question = EvaluationQuestion(
            id="q1",
            question="When was Apple founded?",
            category="company_research",
            expected_agents=[AgentType.COMPANY_RESEARCH],
        )

        result = await harness.evaluate_question(question)

        assert result.routing_correct is False

    @pytest.mark.asyncio
    async def test_answer_quality_calculation(self, harness, mock_orchestrator):
        """Should calculate answer quality based on expected content."""
        from src.multi_agent.router import RoutingDecision, SynthesisStrategy

        @dataclass
        class MockResponse:
            routing_decision = RoutingDecision(
                mode="single_agent",
                agents=[AgentType.COMPANY_RESEARCH],
                subtasks=[],
                synthesis_strategy=SynthesisStrategy.MERGE,
                confidence=0.9,
                reasoning="Test",
            )
            synthesized = MagicMock()
            synthesized.answer = "Apple was founded in 1976"  # Missing Steve Jobs
            agent_responses = []
            final_answer = "Apple was founded in 1976"

        mock_orchestrator.process.return_value = MockResponse()

        question = EvaluationQuestion(
            id="q1",
            question="When was Apple founded?",
            category="company_research",
            expected_agents=[AgentType.COMPANY_RESEARCH],
            expected_answer_contains=["1976", "Steve Jobs"],  # 2 expected
        )

        result = await harness.evaluate_question(question)

        # Only 1 of 2 expected content found
        assert result.answer_quality_score == 0.5

    @pytest.mark.asyncio
    async def test_tracks_latency(self, harness, mock_orchestrator):
        """Should track evaluation latency."""
        from src.multi_agent.router import RoutingDecision, SynthesisStrategy

        @dataclass
        class MockResponse:
            routing_decision = RoutingDecision(
                mode="single_agent",
                agents=[AgentType.COMPANY_RESEARCH],
                subtasks=[],
                synthesis_strategy=SynthesisStrategy.MERGE,
                confidence=0.9,
                reasoning="Test",
            )
            synthesized = MagicMock()
            synthesized.answer = "Answer"
            agent_responses = []
            final_answer = "Answer"

        mock_orchestrator.process.return_value = MockResponse()

        question = EvaluationQuestion(
            id="q1",
            question="Test",
            category="test",
            expected_agents=[AgentType.COMPANY_RESEARCH],
        )

        result = await harness.evaluate_question(question)

        assert result.latency_ms > 0


class TestLoadQuestionsFromDataset:
    """Tests for loading questions from B2B dataset."""

    def test_load_company_research_category(self, tmp_path):
        """Should map company_research to COMPANY_RESEARCH agent."""
        dataset = {
            "questions": [
                {
                    "id": "q1",
                    "question": "When was Apple founded?",
                    "category": "company_research",
                }
            ]
        }

        dataset_path = tmp_path / "test_dataset.json"
        import json
        with open(dataset_path, "w") as f:
            json.dump(dataset, f)

        questions = MultiAgentEvaluationHarness.load_questions_from_b2b_dataset(
            str(dataset_path)
        )

        assert len(questions) == 1
        assert AgentType.COMPANY_RESEARCH in questions[0].expected_agents

    def test_load_financial_analysis_category(self, tmp_path):
        """Should map financial_analysis to FINANCIAL_ANALYST agent."""
        dataset = {
            "questions": [
                {
                    "id": "q1",
                    "question": "What is Apple's market cap?",
                    "category": "financial_analysis",
                }
            ]
        }

        dataset_path = tmp_path / "test_dataset.json"
        import json
        with open(dataset_path, "w") as f:
            json.dump(dataset, f)

        questions = MultiAgentEvaluationHarness.load_questions_from_b2b_dataset(
            str(dataset_path)
        )

        assert AgentType.FINANCIAL_ANALYST in questions[0].expected_agents

    def test_detect_multi_agent_patterns(self, tmp_path):
        """Should detect multi-agent patterns in questions."""
        dataset = {
            "questions": [
                {
                    "id": "q1",
                    "question": "What is Apple and what's their market cap?",
                    "category": "company_research",
                }
            ]
        }

        dataset_path = tmp_path / "test_dataset.json"
        import json
        with open(dataset_path, "w") as f:
            json.dump(dataset, f)

        questions = MultiAgentEvaluationHarness.load_questions_from_b2b_dataset(
            str(dataset_path)
        )

        # Should detect both company and financial agents needed
        assert AgentType.COMPANY_RESEARCH in questions[0].expected_agents
        assert AgentType.FINANCIAL_ANALYST in questions[0].expected_agents
