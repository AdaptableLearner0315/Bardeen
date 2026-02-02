"""Tests for evaluation harness module."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.evaluation.harness import EvaluationHarness
from src.shared.config import Config, EvaluationConfig, LLMConfig
from src.shared.models import (
    DatasetQuestion, AttemptResult, QuestionResult,
    EvaluationRun, ToolCallTrace, ErrorTrace, ToolStatus
)
from src.evaluation.tracers.tool_tracer import ToolTracer
from src.evaluation.tracers.error_tracer import ErrorTracer


class TestEvaluationHarness:
    """Tests for EvaluationHarness class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock config for testing."""
        config = Mock(spec=Config)
        config.evaluation = Mock(spec=EvaluationConfig)
        config.evaluation.consensus_threshold = 0.5
        config.evaluation.k_attempts = 5
        config.evaluation.pass_k_values = [5]
        config.evaluation.save_traces = False

        config.llm = Mock(spec=LLMConfig)
        config.llm.temperature = 0.6

        config.results_dir = Path(tempfile.mkdtemp())
        return config

    @pytest.fixture
    def sample_question(self):
        """Create a sample question for testing."""
        return DatasetQuestion(
            id="test_001",
            question="What is 2+2?",
            category="math",
            difficulty="easy",
            expected_behavior={"tools": ["calculator"]},
            ground_truth={"answer": "4"},
            evaluation={"correctness_threshold": 0.85}
        )

    @pytest.fixture
    def harness(self, mock_config):
        """Create harness instance."""
        return EvaluationHarness(mock_config)

    def test_initialization(self, harness, mock_config):
        """Test harness initialization."""
        assert harness.config == mock_config
        assert harness.pass_k_calculator is not None
        assert harness.visualizer is not None

    def test_simple_similarity_exact_match(self, harness):
        """Test simple similarity with exact match."""
        similarity = harness._simple_similarity("Paris", "Paris")
        assert similarity == 1.0

    def test_simple_similarity_case_insensitive(self, harness):
        """Test simple similarity is case insensitive."""
        similarity = harness._simple_similarity("PARIS", "paris")
        assert similarity == 1.0

    def test_simple_similarity_contains(self, harness):
        """Test simple similarity with contains match."""
        similarity = harness._simple_similarity("The capital is Paris", "Paris")
        assert similarity == 0.9

    def test_simple_similarity_no_match(self, harness):
        """Test simple similarity with no match."""
        similarity = harness._simple_similarity("London", "Paris")
        assert similarity == 0.0


class TestEvaluationHarnessStatistics:
    """Tests for statistics aggregation methods."""

    @pytest.fixture
    def mock_config(self):
        """Create mock config."""
        config = Mock(spec=Config)
        config.evaluation = Mock(spec=EvaluationConfig)
        config.evaluation.consensus_threshold = 0.5
        config.evaluation.k_attempts = 5
        config.evaluation.pass_k_values = [5]
        config.evaluation.save_traces = False
        config.llm = Mock()
        config.llm.temperature = 0.6
        config.results_dir = Path(tempfile.mkdtemp())
        return config

    @pytest.fixture
    def harness(self, mock_config):
        """Create harness instance."""
        return EvaluationHarness(mock_config)

    def test_aggregate_tool_statistics(self, harness):
        """Test tool statistics aggregation."""
        # Create sample attempts with tool calls
        attempts = []
        for i in range(3):
            tool_trace = ToolCallTrace(
                call_id=f"call_{i}",
                attempt_number=i + 1,
                tool_name="calculator" if i < 2 else "web_search",
                params={},
                result={"answer": 4},
                error=None,
                status=ToolStatus.SUCCESS if i < 2 else ToolStatus.ERROR,
                latency_ms=100.0,
                timestamp=datetime.now().isoformat(),
                llm_reasoning=None,
                recovery_action=None
            )
            attempt = AttemptResult(
                attempt_number=i + 1,
                question_id="test",
                final_answer="4",
                tool_calls=[tool_trace],
                errors=[],
                total_latency_ms=100.0,
                is_correct=True,
                semantic_similarity=0.9,
                timestamp=datetime.now().isoformat()
            )
            attempts.append(attempt)

        stats = harness._aggregate_tool_statistics(attempts)

        assert stats["total_calls"] == 3
        assert stats["distribution"]["calculator"] == 2
        assert stats["distribution"]["web_search"] == 1
        assert stats["avg_per_attempt"] == 1.0

    def test_aggregate_tool_statistics_empty(self, harness):
        """Test tool statistics with empty attempts."""
        stats = harness._aggregate_tool_statistics([])
        assert stats["total_calls"] == 0
        assert stats["distribution"] == {}
        assert stats["error_rates"] == {}
        assert stats["avg_per_attempt"] == 0

    def test_aggregate_error_statistics(self, harness):
        """Test error statistics aggregation."""
        attempts = []
        for i in range(3):
            errors = []
            if i < 2:
                error = ErrorTrace(
                    tool_name="tool",
                    error_type="timeout",
                    error_message="msg",
                    attempted_params={},
                    recovery_action="retry",
                    recovery_success=i == 0,  # First one recovered
                    timestamp=datetime.now().isoformat()
                )
                errors.append(error)

            attempt = AttemptResult(
                attempt_number=i + 1,
                question_id="test",
                final_answer="4",
                tool_calls=[],
                errors=errors,
                total_latency_ms=100.0,
                is_correct=True,
                semantic_similarity=0.9,
                timestamp=datetime.now().isoformat()
            )
            attempts.append(attempt)

        stats = harness._aggregate_error_statistics(attempts)

        assert stats["total_errors"] == 2
        assert stats["recovered_errors"] == 1
        assert stats["recovery_rate"] == 0.5

    def test_aggregate_error_statistics_no_errors(self, harness):
        """Test error statistics with no errors."""
        attempts = [
            AttemptResult(
                attempt_number=1,
                question_id="test",
                final_answer="4",
                tool_calls=[],
                errors=[],
                total_latency_ms=100.0,
                is_correct=True,
                semantic_similarity=0.9,
                timestamp=datetime.now().isoformat()
            )
        ]

        stats = harness._aggregate_error_statistics(attempts)

        assert stats["total_errors"] == 0
        assert stats["recovery_rate"] == 1.0  # No errors = perfect rate


class TestEvaluationHarnessAggregateMetrics:
    """Tests for aggregate metrics calculation."""

    @pytest.fixture
    def mock_config(self):
        """Create mock config."""
        config = Mock(spec=Config)
        config.evaluation = Mock(spec=EvaluationConfig)
        config.evaluation.consensus_threshold = 0.5
        config.evaluation.k_attempts = 5
        config.evaluation.pass_k_values = [5]
        config.evaluation.save_traces = False
        config.llm = Mock()
        config.llm.temperature = 0.6
        config.results_dir = Path(tempfile.mkdtemp())
        return config

    @pytest.fixture
    def harness(self, mock_config):
        """Create harness instance."""
        return EvaluationHarness(mock_config)

    @pytest.fixture
    def sample_question_results(self):
        """Create sample question results."""
        results = []
        for i, (pass_5, pass_10, cat) in enumerate([
            (True, True, "math"),
            (True, False, "math"),
            (False, False, "science"),
        ]):
            attempts = [
                AttemptResult(
                    attempt_number=j + 1,
                    question_id=f"q_{i}",
                    final_answer="answer",
                    tool_calls=[],
                    errors=[],
                    total_latency_ms=100.0 + j * 10,
                    is_correct=True,
                    semantic_similarity=0.9,
                    timestamp=datetime.now().isoformat()
                )
                for j in range(10)
            ]

            result = QuestionResult(
                question_id=f"q_{i}",
                question_text=f"Question {i}?",
                category=cat,
                ground_truth="answer",
                attempts=attempts,
                pass_5=pass_5,
                pass_10=pass_10,
                majority_answer="answer",
                consensus_strength=0.8 if pass_5 else 0.4,
                total_tool_calls=10,
                tool_call_distribution={},
                tool_error_rates={},
                avg_tools_per_attempt=1.0,
                avg_latency_ms=145.0,
                error_recovery_rate=1.0,
                timestamp=datetime.now().isoformat()
            )
            results.append(result)

        return results

    def test_calculate_aggregate_metrics(self, harness, sample_question_results):
        """Test aggregate metrics calculation."""
        metrics = harness._calculate_aggregate_metrics(
            sample_question_results,
            k_values=[5, 10]
        )

        assert "overall_pass_5" in metrics
        assert "overall_pass_10" in metrics
        assert "avg_consensus_strength" in metrics
        assert "avg_latency_ms" in metrics
        assert "category_metrics" in metrics

    def test_calculate_aggregate_metrics_pass_rates(self, harness, sample_question_results):
        """Test pass rate calculations."""
        metrics = harness._calculate_aggregate_metrics(
            sample_question_results,
            k_values=[5, 10]
        )

        # 2/3 pass^5, 1/3 pass^10
        assert metrics["overall_pass_5"] == pytest.approx(2/3)
        assert metrics["overall_pass_10"] == pytest.approx(1/3)

    def test_calculate_aggregate_metrics_category_breakdown(self, harness, sample_question_results):
        """Test category metrics breakdown."""
        metrics = harness._calculate_aggregate_metrics(
            sample_question_results,
            k_values=[5, 10]
        )

        assert "math" in metrics["category_metrics"]
        assert "science" in metrics["category_metrics"]
        assert metrics["category_metrics"]["math"]["count"] == 2
        assert metrics["category_metrics"]["science"]["count"] == 1


class TestEvaluationHarnessRunEvaluation:
    """Tests for run_evaluation method."""

    @pytest.fixture
    def mock_config(self):
        """Create mock config."""
        config = Mock(spec=Config)
        config.evaluation = Mock(spec=EvaluationConfig)
        config.evaluation.consensus_threshold = 0.5
        config.evaluation.k_attempts = 3  # Small for testing
        config.evaluation.pass_k_values = [3]
        config.evaluation.save_traces = False
        config.llm = Mock()
        config.llm.temperature = 0.6
        config.results_dir = Path(tempfile.mkdtemp())
        return config

    @pytest.fixture
    def sample_questions(self):
        """Create sample questions."""
        return [
            DatasetQuestion(
                id="q1",
                question="What is 2+2?",
                category="math",
                difficulty="easy",
                expected_behavior={"tools": ["calculator"]},
                ground_truth={"answer": "4"},
                evaluation={"correctness_threshold": 0.85}
            )
        ]

    def test_run_evaluation_calls_agent(self, mock_config, sample_questions):
        """Test that run_evaluation calls agent function."""
        harness = EvaluationHarness(mock_config)

        agent_call_count = 0

        def mock_agent(question, tool_tracer, error_tracer):
            nonlocal agent_call_count
            agent_call_count += 1
            return "4", [], []

        result = harness.run_evaluation(sample_questions, mock_agent)

        # Should call agent k times per question
        assert agent_call_count == 3  # 1 question * 3 attempts

    def test_run_evaluation_returns_evaluation_run(self, mock_config, sample_questions):
        """Test that run_evaluation returns EvaluationRun."""
        harness = EvaluationHarness(mock_config)

        def mock_agent(question, tool_tracer, error_tracer):
            return "4", [], []

        result = harness.run_evaluation(sample_questions, mock_agent)

        assert isinstance(result, EvaluationRun)
        assert result.dataset_size == 1
        assert result.k_attempts == 3

    def test_run_evaluation_handles_agent_error(self, mock_config, sample_questions):
        """Test that run_evaluation handles agent exceptions."""
        harness = EvaluationHarness(mock_config)

        call_count = 0

        def failing_agent(question, tool_tracer, error_tracer):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Agent failed")
            return "4", [], []

        # Should not raise, should handle gracefully
        result = harness.run_evaluation(sample_questions, failing_agent)

        assert result is not None
        # First attempt should have error recorded
        assert any("ERROR" in a.final_answer for a in result.question_results[0].attempts)

    def test_run_evaluation_with_similarity_fn(self, mock_config, sample_questions):
        """Test run_evaluation with custom similarity function."""
        harness = EvaluationHarness(mock_config)

        def mock_agent(question, tool_tracer, error_tracer):
            return "4", [], []

        similarity_called = False

        def custom_similarity(answer, ground_truth):
            nonlocal similarity_called
            similarity_called = True
            return 0.95

        result = harness.run_evaluation(
            sample_questions,
            mock_agent,
            similarity_fn=custom_similarity
        )

        assert similarity_called


class TestEvaluationHarnessSaveResults:
    """Tests for save results functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create mock config with temp dir."""
        config = Mock(spec=Config)
        config.evaluation = Mock(spec=EvaluationConfig)
        config.evaluation.consensus_threshold = 0.5
        config.evaluation.k_attempts = 1
        config.evaluation.pass_k_values = [1]
        config.evaluation.save_traces = True
        config.llm = Mock()
        config.llm.temperature = 0.6
        config.results_dir = Path(tempfile.mkdtemp())
        return config

    def test_save_results_creates_file(self, mock_config):
        """Test that results are saved to file."""
        harness = EvaluationHarness(mock_config)

        questions = [
            DatasetQuestion(
                id="q1",
                question="Test?",
                category="test",
                difficulty="easy",
                expected_behavior={},
                ground_truth={"answer": "test"},
                evaluation={"correctness_threshold": 0.5}
            )
        ]

        def mock_agent(question, tool_tracer, error_tracer):
            return "test", [], []

        result = harness.run_evaluation(questions, mock_agent)

        # Check file was created
        files = list(mock_config.results_dir.glob("eval_*.json"))
        assert len(files) == 1
