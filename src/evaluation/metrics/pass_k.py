"""pass^k metric calculator using majority voting (consensus)."""

from collections import Counter
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass


@dataclass
class PassKResult:
    """Result of pass^k calculation."""
    k: int
    passed: bool
    majority_answer: str
    consensus_strength: float  # Percentage of attempts that gave majority answer
    answer_distribution: Dict[str, int]  # All answers and their counts
    correct_answer: str


class PassKCalculator:
    """
    Calculates pass^k metrics using majority voting.

    pass^k tests if the MAJORITY of k attempts produce the correct answer.
    This measures consistency and reliability, not just capability.
    """

    def __init__(self, consensus_threshold: float = 0.5):
        """
        Initialize calculator.

        Args:
            consensus_threshold: Minimum fraction needed for majority (default 0.5 = 50%)
        """
        self.consensus_threshold = consensus_threshold

    def calculate_pass_k(
        self,
        answers: List[str],
        ground_truth: str,
        k: int,
        similarity_fn=None
    ) -> PassKResult:
        """
        Calculate pass^k for k attempts.

        Args:
            answers: List of answers from k attempts
            ground_truth: The correct answer
            k: Number of attempts to consider (5 or 10)
            similarity_fn: Optional function to check if answer matches ground truth
                          (default: exact string match after normalization)

        Returns:
            PassKResult with pass/fail and detailed statistics
        """
        if len(answers) < k:
            raise ValueError(f"Need at least {k} answers, got {len(answers)}")

        # Take first k answers
        k_answers = answers[:k]

        # Normalize answers (lowercase, strip whitespace)
        normalized_answers = [self._normalize_answer(ans) for ans in k_answers]

        # Find majority answer
        answer_counts = Counter(normalized_answers)
        majority_answer, majority_count = answer_counts.most_common(1)[0]

        # Calculate consensus strength
        consensus_strength = majority_count / k

        # Check if majority answer is correct
        if similarity_fn is not None:
            is_correct = similarity_fn(majority_answer, ground_truth)
        else:
            is_correct = self._is_answer_correct(majority_answer, ground_truth)

        # Pass if: (1) majority is correct AND (2) meets consensus threshold
        passed = is_correct and (consensus_strength >= self.consensus_threshold)

        return PassKResult(
            k=k,
            passed=passed,
            majority_answer=majority_answer,
            consensus_strength=consensus_strength,
            answer_distribution=dict(answer_counts),
            correct_answer=ground_truth
        )

    def calculate_multi_k(
        self,
        answers: List[str],
        ground_truth: str,
        k_values: List[int],
        similarity_fn=None
    ) -> Dict[int, PassKResult]:
        """
        Calculate pass^k for multiple k values.

        Args:
            answers: List of answers from all attempts
            ground_truth: The correct answer
            k_values: List of k values to calculate (e.g., [5, 10])
            similarity_fn: Optional similarity function

        Returns:
            Dictionary mapping k -> PassKResult
        """
        results = {}
        for k in k_values:
            results[k] = self.calculate_pass_k(answers, ground_truth, k, similarity_fn)
        return results

    @staticmethod
    def _normalize_answer(answer: str) -> str:
        """Normalize answer for comparison."""
        # Remove extra whitespace, lowercase, strip
        normalized = " ".join(answer.lower().split())
        # Remove common filler words
        for filler in ["approximately", "about", "roughly", "~", "around"]:
            normalized = normalized.replace(filler, "")
        return normalized.strip()

    @staticmethod
    def _is_answer_correct(answer: str, ground_truth: str) -> bool:
        """
        Check if answer matches ground truth (simple string matching).

        For semantic similarity, use the similarity_fn parameter instead.
        """
        norm_answer = PassKCalculator._normalize_answer(answer)
        norm_truth = PassKCalculator._normalize_answer(ground_truth)

        # Exact match
        if norm_answer == norm_truth:
            return True

        # Contains match (answer contains the key fact)
        if norm_truth in norm_answer or norm_answer in norm_truth:
            return True

        return False

    def get_aggregate_pass_rate(
        self,
        results: List[PassKResult]
    ) -> float:
        """
        Calculate aggregate pass rate across multiple questions.

        Args:
            results: List of PassKResult for different questions

        Returns:
            Fraction of questions that passed (0.0 to 1.0)
        """
        if not results:
            return 0.0
        passed_count = sum(1 for r in results if r.passed)
        return passed_count / len(results)

    def get_average_consensus(
        self,
        results: List[PassKResult]
    ) -> float:
        """
        Calculate average consensus strength across multiple questions.

        Args:
            results: List of PassKResult for different questions

        Returns:
            Average consensus strength (0.0 to 1.0)
        """
        if not results:
            return 0.0
        return sum(r.consensus_strength for r in results) / len(results)


def format_pass_k_summary(result: PassKResult) -> str:
    """
    Format pass^k result as a human-readable string.

    Args:
        result: PassKResult to format

    Returns:
        Formatted string summary
    """
    status = "✓ PASS" if result.passed else "✗ FAIL"
    distribution_str = ", ".join(
        f'"{ans}": {count}' for ans, count in result.answer_distribution.items()
    )

    return f"""
pass^{result.k}: {status}
Majority Answer: "{result.majority_answer}" ({result.consensus_strength:.0%} consensus)
Ground Truth: "{result.correct_answer}"
Answer Distribution: {{{distribution_str}}}
    """.strip()
