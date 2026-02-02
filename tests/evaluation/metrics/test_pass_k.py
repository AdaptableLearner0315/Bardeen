"""Tests for pass^k metric calculator."""

import pytest

from src.evaluation.metrics.pass_k import (
    PassKCalculator,
    PassKResult,
    format_pass_k_summary,
)


class TestPassKResult:
    """Tests for PassKResult dataclass."""

    def test_creation(self):
        """Test basic creation."""
        result = PassKResult(
            k=5,
            passed=True,
            majority_answer="42",
            consensus_strength=0.8,
            answer_distribution={"42": 4, "41": 1},
            correct_answer="42"
        )
        assert result.k == 5
        assert result.passed is True
        assert result.majority_answer == "42"
        assert result.consensus_strength == 0.8
        assert result.correct_answer == "42"

    def test_failed_result(self):
        """Test failed result."""
        result = PassKResult(
            k=10,
            passed=False,
            majority_answer="wrong",
            consensus_strength=0.6,
            answer_distribution={"wrong": 6, "right": 4},
            correct_answer="right"
        )
        assert result.passed is False


class TestPassKCalculator:
    """Tests for PassKCalculator class."""

    def test_initialization_default_threshold(self):
        """Test default consensus threshold."""
        calculator = PassKCalculator()
        assert calculator.consensus_threshold == 0.5

    def test_initialization_custom_threshold(self):
        """Test custom consensus threshold."""
        calculator = PassKCalculator(consensus_threshold=0.6)
        assert calculator.consensus_threshold == 0.6

    def test_calculate_pass_k_all_correct(self):
        """Test pass^k when all answers are correct."""
        calculator = PassKCalculator()
        answers = ["Paris"] * 5
        result = calculator.calculate_pass_k(answers, "Paris", k=5)

        assert result.passed is True
        assert result.majority_answer == "paris"  # normalized
        assert result.consensus_strength == 1.0

    def test_calculate_pass_k_majority_correct(self):
        """Test pass^k when majority is correct."""
        calculator = PassKCalculator()
        answers = ["Paris", "Paris", "Paris", "London", "London"]
        result = calculator.calculate_pass_k(answers, "Paris", k=5)

        assert result.passed is True
        assert result.consensus_strength == 0.6

    def test_calculate_pass_k_majority_wrong(self):
        """Test pass^k when majority is wrong."""
        calculator = PassKCalculator()
        answers = ["London", "London", "London", "Paris", "Paris"]
        result = calculator.calculate_pass_k(answers, "Paris", k=5)

        assert result.passed is False
        assert result.majority_answer == "london"

    def test_calculate_pass_k_below_threshold(self):
        """Test pass^k fails when below consensus threshold."""
        calculator = PassKCalculator(consensus_threshold=0.7)
        answers = ["Paris", "Paris", "Paris", "London", "Rome"]  # 60% consensus
        result = calculator.calculate_pass_k(answers, "Paris", k=5)

        # Correct answer has majority but below threshold
        assert result.passed is False
        assert result.consensus_strength == 0.6

    def test_calculate_pass_k_not_enough_answers(self):
        """Test error when not enough answers."""
        calculator = PassKCalculator()
        answers = ["Paris", "Paris", "Paris"]

        with pytest.raises(ValueError, match="Need at least 5 answers"):
            calculator.calculate_pass_k(answers, "Paris", k=5)

    def test_calculate_pass_k_uses_first_k_answers(self):
        """Test that only first k answers are used."""
        calculator = PassKCalculator()
        # First 5 are London (wrong), rest are Paris (correct)
        answers = ["London"] * 5 + ["Paris"] * 5
        result = calculator.calculate_pass_k(answers, "Paris", k=5)

        assert result.passed is False
        assert result.majority_answer == "london"

    def test_calculate_pass_k_with_similarity_fn(self):
        """Test pass^k with custom similarity function."""
        calculator = PassKCalculator()

        # Custom similarity that considers "42" and "forty-two" equivalent
        def custom_similarity(answer, truth):
            return answer in ["42", "forty-two"] and truth == "42"

        answers = ["forty-two", "forty-two", "forty-two", "42", "43"]
        result = calculator.calculate_pass_k(answers, "42", k=5, similarity_fn=custom_similarity)

        # "forty-two" should be considered correct
        assert result.passed is True

    def test_calculate_pass_k_exact_threshold(self):
        """Test pass^k at exact threshold boundary."""
        calculator = PassKCalculator(consensus_threshold=0.5)
        answers = ["Paris", "Paris", "Paris", "Paris", "Paris",
                   "London", "London", "London", "London", "London"]
        result = calculator.calculate_pass_k(answers, "Paris", k=10)

        # 50% consensus exactly meets threshold
        assert result.consensus_strength == 0.5
        assert result.passed is True  # Paris is majority (appears first)

    def test_normalize_answer(self):
        """Test answer normalization."""
        # Test lowercase
        assert PassKCalculator._normalize_answer("PARIS") == "paris"

        # Test whitespace
        assert PassKCalculator._normalize_answer("  Paris  ") == "paris"

        # Test filler words removal
        assert PassKCalculator._normalize_answer("approximately 100") == "100"
        assert PassKCalculator._normalize_answer("about 42") == "42"
        assert PassKCalculator._normalize_answer("roughly 500") == "500"

    def test_is_answer_correct_exact_match(self):
        """Test exact match correctness."""
        assert PassKCalculator._is_answer_correct("Paris", "Paris") is True
        assert PassKCalculator._is_answer_correct("paris", "Paris") is True
        assert PassKCalculator._is_answer_correct("PARIS", "paris") is True

    def test_is_answer_correct_contains_match(self):
        """Test contains match correctness."""
        # Answer contains truth
        assert PassKCalculator._is_answer_correct(
            "The capital is Paris",
            "Paris"
        ) is True

        # Truth contains answer
        assert PassKCalculator._is_answer_correct(
            "42",
            "The answer is 42"
        ) is True

    def test_is_answer_correct_no_match(self):
        """Test non-matching answers."""
        assert PassKCalculator._is_answer_correct("London", "Paris") is False
        assert PassKCalculator._is_answer_correct("100", "200") is False


class TestPassKCalculatorMultiK:
    """Tests for calculate_multi_k method."""

    def test_calculate_multi_k_basic(self):
        """Test calculating multiple k values."""
        calculator = PassKCalculator()
        answers = ["Paris"] * 10
        results = calculator.calculate_multi_k(answers, "Paris", k_values=[5, 10])

        assert 5 in results
        assert 10 in results
        assert results[5].passed is True
        assert results[10].passed is True

    def test_calculate_multi_k_different_results(self):
        """Test when different k values give different results."""
        calculator = PassKCalculator()
        # First 5 are mixed, next 5 are all Paris
        answers = ["Paris", "London", "Paris", "Rome", "Paris",
                   "Paris", "Paris", "Paris", "Paris", "Paris"]
        results = calculator.calculate_multi_k(answers, "Paris", k_values=[5, 10])

        # pass^5: Paris has 3/5 = 60% consensus
        assert results[5].passed is True
        assert results[5].consensus_strength == 0.6

        # pass^10: Paris has 8/10 = 80% consensus
        assert results[10].passed is True
        assert results[10].consensus_strength == 0.8

    def test_calculate_multi_k_empty_values(self):
        """Test with empty k_values list."""
        calculator = PassKCalculator()
        answers = ["Paris"] * 10
        results = calculator.calculate_multi_k(answers, "Paris", k_values=[])

        assert results == {}


class TestPassKCalculatorAggregates:
    """Tests for aggregate calculation methods."""

    def test_get_aggregate_pass_rate(self):
        """Test aggregate pass rate calculation."""
        calculator = PassKCalculator()

        results = [
            PassKResult(k=5, passed=True, majority_answer="a", consensus_strength=0.8,
                       answer_distribution={}, correct_answer="a"),
            PassKResult(k=5, passed=True, majority_answer="b", consensus_strength=0.8,
                       answer_distribution={}, correct_answer="b"),
            PassKResult(k=5, passed=False, majority_answer="wrong", consensus_strength=0.6,
                       answer_distribution={}, correct_answer="right"),
        ]

        rate = calculator.get_aggregate_pass_rate(results)
        assert rate == pytest.approx(2/3)

    def test_get_aggregate_pass_rate_empty(self):
        """Test aggregate pass rate with empty list."""
        calculator = PassKCalculator()
        rate = calculator.get_aggregate_pass_rate([])
        assert rate == 0.0

    def test_get_aggregate_pass_rate_all_pass(self):
        """Test aggregate pass rate when all pass."""
        calculator = PassKCalculator()
        results = [
            PassKResult(k=5, passed=True, majority_answer="a", consensus_strength=0.8,
                       answer_distribution={}, correct_answer="a")
            for _ in range(5)
        ]
        rate = calculator.get_aggregate_pass_rate(results)
        assert rate == 1.0

    def test_get_aggregate_pass_rate_all_fail(self):
        """Test aggregate pass rate when all fail."""
        calculator = PassKCalculator()
        results = [
            PassKResult(k=5, passed=False, majority_answer="wrong", consensus_strength=0.6,
                       answer_distribution={}, correct_answer="right")
            for _ in range(5)
        ]
        rate = calculator.get_aggregate_pass_rate(results)
        assert rate == 0.0

    def test_get_average_consensus(self):
        """Test average consensus calculation."""
        calculator = PassKCalculator()

        results = [
            PassKResult(k=5, passed=True, majority_answer="a", consensus_strength=0.8,
                       answer_distribution={}, correct_answer="a"),
            PassKResult(k=5, passed=True, majority_answer="b", consensus_strength=0.6,
                       answer_distribution={}, correct_answer="b"),
            PassKResult(k=5, passed=False, majority_answer="c", consensus_strength=0.4,
                       answer_distribution={}, correct_answer="c"),
        ]

        avg = calculator.get_average_consensus(results)
        assert avg == pytest.approx(0.6)

    def test_get_average_consensus_empty(self):
        """Test average consensus with empty list."""
        calculator = PassKCalculator()
        avg = calculator.get_average_consensus([])
        assert avg == 0.0


class TestFormatPassKSummary:
    """Tests for format_pass_k_summary function."""

    def test_format_passing_result(self):
        """Test formatting a passing result."""
        result = PassKResult(
            k=5,
            passed=True,
            majority_answer="paris",
            consensus_strength=0.8,
            answer_distribution={"paris": 4, "london": 1},
            correct_answer="paris"
        )

        summary = format_pass_k_summary(result)

        assert "pass^5" in summary
        assert "PASS" in summary
        assert "paris" in summary
        assert "80%" in summary or "0.8" in summary

    def test_format_failing_result(self):
        """Test formatting a failing result."""
        result = PassKResult(
            k=10,
            passed=False,
            majority_answer="wrong",
            consensus_strength=0.6,
            answer_distribution={"wrong": 6, "right": 4},
            correct_answer="right"
        )

        summary = format_pass_k_summary(result)

        assert "pass^10" in summary
        assert "FAIL" in summary
        assert "wrong" in summary
        assert "right" in summary


class TestPassKEdgeCases:
    """Tests for edge cases in pass^k calculation."""

    def test_tie_breaking(self):
        """Test behavior when there's a tie in answer counts."""
        calculator = PassKCalculator()
        # 5 Paris, 5 London - Counter.most_common returns first encountered
        answers = ["Paris", "London", "Paris", "London", "Paris",
                   "London", "Paris", "London", "Paris", "London"]
        result = calculator.calculate_pass_k(answers, "Paris", k=10)

        # Should handle tie gracefully
        assert result.consensus_strength == 0.5

    def test_whitespace_variations(self):
        """Test handling of whitespace variations."""
        calculator = PassKCalculator()
        answers = ["Paris", " Paris", "Paris ", " Paris ", "  Paris  "]
        result = calculator.calculate_pass_k(answers, "Paris", k=5)

        assert result.passed is True
        assert result.consensus_strength == 1.0  # All normalize to same

    def test_case_insensitivity(self):
        """Test case insensitive comparison."""
        calculator = PassKCalculator()
        answers = ["PARIS", "Paris", "paris", "PaRiS", "PARIS"]
        result = calculator.calculate_pass_k(answers, "paris", k=5)

        assert result.passed is True
        assert result.consensus_strength == 1.0

    def test_numerical_answers(self):
        """Test handling of numerical answers."""
        calculator = PassKCalculator()
        answers = ["42", "42", "42", "42", "41"]
        result = calculator.calculate_pass_k(answers, "42", k=5)

        assert result.passed is True
        assert result.consensus_strength == 0.8

    def test_long_answers(self):
        """Test handling of long text answers."""
        calculator = PassKCalculator()
        long_answer = "The capital of France is Paris, which is located on the Seine River."
        answers = [long_answer] * 5
        result = calculator.calculate_pass_k(answers, "Paris", k=5)

        # Should pass because answer contains "Paris"
        assert result.passed is True

    def test_empty_answer_strings(self):
        """Test handling of empty answer strings."""
        calculator = PassKCalculator()
        answers = ["", "", "", "Paris", "Paris"]
        result = calculator.calculate_pass_k(answers, "", k=5)

        # Empty string is majority
        assert result.majority_answer == ""
        assert result.consensus_strength == 0.6
