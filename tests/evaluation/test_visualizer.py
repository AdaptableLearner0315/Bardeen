"""Tests for ASCII visualizer module."""

import pytest
from datetime import datetime

from src.evaluation.visualizer import ASCIIVisualizer
from src.shared.models import (
    AttemptResult, QuestionResult, ToolCallTrace, ErrorTrace, ToolStatus
)
from src.evaluation.metrics.pass_k import PassKResult


class TestASCIIVisualizer:
    """Tests for ASCIIVisualizer class."""

    @pytest.fixture
    def visualizer(self):
        """Create a visualizer instance."""
        return ASCIIVisualizer(width=80)

    @pytest.fixture
    def sample_tool_trace(self):
        """Create a sample tool trace."""
        return ToolCallTrace(
            call_id="test123",
            attempt_number=1,
            tool_name="web_search",
            params={"query": "test query"},
            result={"results": ["result1", "result2"]},
            error=None,
            status=ToolStatus.SUCCESS,
            latency_ms=150.0,
            timestamp=datetime.now().isoformat(),
            llm_reasoning="Searching for test query",
            recovery_action=None
        )

    @pytest.fixture
    def sample_attempt_result(self, sample_tool_trace):
        """Create a sample attempt result."""
        return AttemptResult(
            attempt_number=1,
            question_id="test_001",
            final_answer="The answer is 42",
            tool_calls=[sample_tool_trace],
            errors=[],
            total_latency_ms=250.0,
            is_correct=True,
            semantic_similarity=0.95,
            timestamp=datetime.now().isoformat()
        )

    @pytest.fixture
    def sample_question_result(self, sample_attempt_result):
        """Create a sample question result."""
        attempts = [sample_attempt_result] * 10
        return QuestionResult(
            question_id="test_001",
            question_text="What is the answer?",
            category="test",
            ground_truth="42",
            attempts=attempts,
            pass_5=True,
            pass_10=True,
            majority_answer="The answer is 42",
            consensus_strength=0.8,
            total_tool_calls=10,
            tool_call_distribution={"web_search": 10},
            tool_error_rates={"web_search": 0.0},
            avg_tools_per_attempt=1.0,
            avg_latency_ms=250.0,
            error_recovery_rate=1.0,
            timestamp=datetime.now().isoformat()
        )

    def test_initialization(self, visualizer):
        """Test visualizer initialization."""
        assert visualizer.width == 80

    def test_initialization_custom_width(self):
        """Test custom width initialization."""
        viz = ASCIIVisualizer(width=100)
        assert viz.width == 100

    def test_visualize_attempt_success(self, visualizer, sample_attempt_result):
        """Test visualizing a successful attempt."""
        output = visualizer.visualize_attempt(sample_attempt_result)

        assert "Attempt 1/10" in output
        assert "SUCCESS" in output
        assert "✓" in output
        assert "web_search" in output
        assert "The answer is 42" in output
        assert "250" in output  # latency

    def test_visualize_attempt_failure(self, visualizer, sample_tool_trace):
        """Test visualizing a failed attempt."""
        attempt = AttemptResult(
            attempt_number=3,
            question_id="test_001",
            final_answer="Wrong answer",
            tool_calls=[sample_tool_trace],
            errors=[],
            total_latency_ms=300.0,
            is_correct=False,
            semantic_similarity=0.2,
            timestamp=datetime.now().isoformat()
        )

        output = visualizer.visualize_attempt(attempt)

        assert "FAIL" in output
        assert "✗" in output

    def test_visualize_attempt_no_tools(self, visualizer):
        """Test visualizing attempt with no tool calls."""
        attempt = AttemptResult(
            attempt_number=1,
            question_id="test_001",
            final_answer="Direct answer",
            tool_calls=[],
            errors=[],
            total_latency_ms=100.0,
            is_correct=True,
            semantic_similarity=0.9,
            timestamp=datetime.now().isoformat()
        )

        output = visualizer.visualize_attempt(attempt)

        assert "no tools used" in output.lower()

    def test_visualize_attempt_with_errors(self, visualizer, sample_tool_trace):
        """Test visualizing attempt with errors."""
        error = ErrorTrace(
            tool_name="web_search",
            error_type="timeout",
            error_message="Request timed out",
            attempted_params={},
            recovery_action="retry",
            recovery_success=True,
            timestamp=datetime.now().isoformat()
        )

        attempt = AttemptResult(
            attempt_number=1,
            question_id="test_001",
            final_answer="Answer",
            tool_calls=[sample_tool_trace],
            errors=[error],
            total_latency_ms=200.0,
            is_correct=True,
            semantic_similarity=0.9,
            timestamp=datetime.now().isoformat()
        )

        output = visualizer.visualize_attempt(attempt)

        assert "Error" in output or "error" in output

    def test_visualize_attempt_timeout_tool(self, visualizer):
        """Test visualizing attempt with timeout tool."""
        trace = ToolCallTrace(
            call_id="test",
            attempt_number=1,
            tool_name="slow_api",
            params={},
            result=None,
            error="Timeout exceeded",
            status=ToolStatus.TIMEOUT,
            latency_ms=30000.0,
            timestamp=datetime.now().isoformat(),
            llm_reasoning=None,
            recovery_action="fallback_to_cache"
        )

        attempt = AttemptResult(
            attempt_number=1,
            question_id="test",
            final_answer="Fallback answer",
            tool_calls=[trace],
            errors=[],
            total_latency_ms=30000.0,
            is_correct=False,
            semantic_similarity=0.5,
            timestamp=datetime.now().isoformat()
        )

        output = visualizer.visualize_attempt(attempt)

        assert "TIMEOUT" in output

    def test_visualize_attempt_fallback_tool(self, visualizer):
        """Test visualizing attempt with fallback tool."""
        trace = ToolCallTrace(
            call_id="test",
            attempt_number=1,
            tool_name="wikipedia",
            params={"query": "test"},
            result={"summary": "Fallback result"},
            error=None,
            status=ToolStatus.FALLBACK,
            latency_ms=200.0,
            timestamp=datetime.now().isoformat(),
            llm_reasoning=None,
            recovery_action="fallback_from_web_search"
        )

        attempt = AttemptResult(
            attempt_number=1,
            question_id="test",
            final_answer="Answer",
            tool_calls=[trace],
            errors=[],
            total_latency_ms=200.0,
            is_correct=True,
            semantic_similarity=0.9,
            timestamp=datetime.now().isoformat()
        )

        output = visualizer.visualize_attempt(attempt)

        assert "FALLBACK" in output

    def test_visualize_consensus(self, visualizer, sample_question_result):
        """Test visualizing consensus analysis."""
        pass_5 = PassKResult(
            k=5,
            passed=True,
            majority_answer="The answer is 42",
            consensus_strength=0.8,
            answer_distribution={"The answer is 42": 4, "Other": 1},
            correct_answer="42"
        )
        pass_10 = PassKResult(
            k=10,
            passed=True,
            majority_answer="The answer is 42",
            consensus_strength=0.8,
            answer_distribution={"The answer is 42": 8, "Other": 2},
            correct_answer="42"
        )

        output = visualizer.visualize_consensus(
            sample_question_result,
            pass_5,
            pass_10
        )

        assert "CONSENSUS ANALYSIS" in output
        assert "pass^5" in output
        assert "pass^10" in output
        assert "80%" in output or "0.8" in output

    def test_visualize_consensus_failed(self, visualizer, sample_question_result):
        """Test visualizing failed consensus."""
        pass_5 = PassKResult(
            k=5,
            passed=False,
            majority_answer="Wrong answer",
            consensus_strength=0.4,
            answer_distribution={},
            correct_answer="42"
        )
        pass_10 = PassKResult(
            k=10,
            passed=False,
            majority_answer="Wrong answer",
            consensus_strength=0.4,
            answer_distribution={},
            correct_answer="42"
        )

        output = visualizer.visualize_consensus(
            sample_question_result,
            pass_5,
            pass_10
        )

        assert "✗" in output or "FAIL" in output

    def test_visualize_question_summary(self, visualizer, sample_question_result):
        """Test visualizing question summary."""
        output = visualizer.visualize_question_summary(sample_question_result)

        assert sample_question_result.question_text in output
        assert sample_question_result.category in output
        assert sample_question_result.question_id in output


class TestASCIIVisualizerFormatters:
    """Tests for private formatting methods."""

    @pytest.fixture
    def visualizer(self):
        """Create a visualizer instance."""
        return ASCIIVisualizer(width=80)

    def test_format_params_empty(self, visualizer):
        """Test formatting empty params."""
        result = visualizer._format_params({})
        assert result == "{}"

    def test_format_params_simple(self, visualizer):
        """Test formatting simple params."""
        params = {"query": "test", "limit": "10"}
        result = visualizer._format_params(params)

        assert "query" in result
        assert "test" in result
        assert "limit" in result

    def test_format_params_long_value(self, visualizer):
        """Test formatting params with long value."""
        params = {"query": "x" * 100}
        result = visualizer._format_params(params)

        # Should be truncated
        assert "..." in result
        assert len(result) < 200

    def test_format_result_none(self, visualizer):
        """Test formatting None result."""
        result = visualizer._format_result(None)
        assert result == "None"

    def test_format_result_short(self, visualizer):
        """Test formatting short result."""
        result = visualizer._format_result("Short result")
        assert result == "Short result"

    def test_format_result_long(self, visualizer):
        """Test formatting long result."""
        long_result = "x" * 100
        result = visualizer._format_result(long_result)

        assert "..." in result
        assert len(result) <= 63

    def test_wrap_text_short(self, visualizer):
        """Test wrapping short text."""
        text = "Short text"
        lines = visualizer._wrap_text(text, 50)

        assert len(lines) == 1
        assert lines[0] == "Short text"

    def test_wrap_text_long(self, visualizer):
        """Test wrapping long text."""
        text = "This is a longer piece of text that should be wrapped across multiple lines"
        lines = visualizer._wrap_text(text, 30)

        assert len(lines) > 1
        for line in lines:
            assert len(line) <= 35  # Some tolerance for word boundaries

    def test_wrap_text_single_long_word(self, visualizer):
        """Test wrapping text with single long word."""
        text = "x" * 100
        lines = visualizer._wrap_text(text, 50)

        # Should return something, even if truncated
        assert len(lines) >= 1


class TestASCIIVisualizerToolCall:
    """Tests for tool call formatting."""

    @pytest.fixture
    def visualizer(self):
        """Create a visualizer instance."""
        return ASCIIVisualizer(width=80)

    def test_format_tool_call_success(self, visualizer):
        """Test formatting successful tool call."""
        trace = ToolCallTrace(
            call_id="test",
            attempt_number=1,
            tool_name="calculator",
            params={"expression": "2+2"},
            result={"answer": 4},
            error=None,
            status=ToolStatus.SUCCESS,
            latency_ms=5.0,
            timestamp=datetime.now().isoformat(),
            llm_reasoning=None,
            recovery_action=None
        )

        lines = visualizer._format_tool_call(trace, 1, is_last=False)

        assert any("calculator" in line for line in lines)
        assert any("OK" in line or "SUCCESS" in line.upper() for line in lines)

    def test_format_tool_call_error(self, visualizer):
        """Test formatting error tool call."""
        trace = ToolCallTrace(
            call_id="test",
            attempt_number=1,
            tool_name="web_search",
            params={"query": "test"},
            result=None,
            error="Connection failed",
            status=ToolStatus.ERROR,
            latency_ms=1000.0,
            timestamp=datetime.now().isoformat(),
            llm_reasoning=None,
            recovery_action="retry"
        )

        lines = visualizer._format_tool_call(trace, 1, is_last=True)

        assert any("ERROR" in line for line in lines)
        assert any("Connection failed" in line for line in lines)

    def test_format_tool_call_with_reasoning(self, visualizer):
        """Test formatting tool call with LLM reasoning."""
        trace = ToolCallTrace(
            call_id="test",
            attempt_number=1,
            tool_name="wikipedia",
            params={"query": "Python"},
            result={"summary": "Python is a language"},
            error=None,
            status=ToolStatus.SUCCESS,
            latency_ms=200.0,
            timestamp=datetime.now().isoformat(),
            llm_reasoning="I need to look up information about Python",
            recovery_action=None
        )

        lines = visualizer._format_tool_call(trace, 1, is_last=False)

        assert any("Reasoning" in line or "reasoning" in line for line in lines)
