"""Unit tests for MetricsCalculator utility."""

import pytest
from src.evaluation.metrics.calculator import MetricsCalculator


class TestPrecisionRecallF1:
    """Test precision/recall/F1 calculations."""

    def test_perfect_match(self):
        """Test perfect precision/recall/F1."""
        result = MetricsCalculator.calculate_precision_recall_f1(
            correct_tools=["tool1", "tool2"],
            used_tools=["tool1", "tool2"]
        )
        assert result["precision"] == 1.0
        assert result["recall"] == 1.0
        assert result["f1_score"] == 1.0

    def test_empty_used_tools(self):
        """Test with no tools used."""
        result = MetricsCalculator.calculate_precision_recall_f1(
            correct_tools=["tool1"],
            used_tools=[]
        )
        assert result["precision"] == 0.0
        assert result["recall"] == 0.0
        assert result["f1_score"] == 0.0

    def test_partial_match(self):
        """Test partial tool overlap."""
        result = MetricsCalculator.calculate_precision_recall_f1(
            correct_tools=["tool1", "tool2"],
            used_tools=["tool1", "tool3"]
        )
        assert result["precision"] == 0.5
        assert result["recall"] == 0.5
        assert result["f1_score"] == 0.5


class TestConsensus:
    """Test consensus calculations."""

    def test_consensus_exact_match(self):
        """Test consensus with exact string matches."""
        result = MetricsCalculator.calculate_consensus(
            answers=["answer1", "answer1", "answer2"]
        )
        assert result["consensus_answer"] == "answer1"
        assert result["consensus_count"] == 2
        assert result["pass_rate"] == pytest.approx(2/3)

    def test_consensus_empty_list(self):
        """Test consensus with empty answers list."""
        result = MetricsCalculator.calculate_consensus(answers=[])
        assert result["consensus_answer"] is None
        assert result["consensus_count"] == 0
        assert result["pass_rate"] == 0.0


class TestNormalization:
    """Test answer normalization."""

    def test_normalize_answer(self):
        """Test answer normalization."""
        normalized = MetricsCalculator.normalize_answer("  Hello, World!  ")
        assert normalized == "hello world"

    def test_normalize_punctuation(self):
        """Test punctuation removal."""
        normalized = MetricsCalculator.normalize_answer("Apple Inc.")
        assert normalized == "apple inc"


class TestAverages:
    """Test average calculations."""

    def test_calculate_average(self):
        """Test simple average calculation."""
        avg = MetricsCalculator.calculate_average([1.0, 2.0, 3.0])
        assert avg == 2.0

    def test_calculate_average_empty(self):
        """Test average of empty list."""
        avg = MetricsCalculator.calculate_average([])
        assert avg == 0.0

    def test_weighted_average(self):
        """Test weighted average calculation."""
        avg = MetricsCalculator.calculate_weighted_average(
            values=[1.0, 2.0, 3.0],
            weights=[1.0, 2.0, 1.0]
        )
        assert avg == 2.0
