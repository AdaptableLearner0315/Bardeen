"""Utility class for common metrics calculations.

This module provides centralized metrics calculation logic to eliminate
duplication across evaluation modules. Includes precision/recall/F1,
consensus calculations, and answer normalization.

Key Classes:
    MetricsCalculator: Static methods for metrics calculations

Usage:
    from src.evaluation.metrics.calculator import MetricsCalculator

    result = MetricsCalculator.calculate_precision_recall_f1(
        correct_tools=["tool1", "tool2"],
        used_tools=["tool1", "tool3"]
    )
    print(result["f1_score"])

Notes:
    - All methods are static (no instance needed)
    - Handles edge cases (empty lists, zero division)
    - Supports custom similarity functions for consensus
"""

from typing import List, Dict, Any, Callable, Optional
from collections import Counter
import re


class MetricsCalculator:
    """Utility class for common metrics calculations.

    Provides:
    - Precision, Recall, F1 calculations
    - Consensus calculations (pass^k)
    - Answer normalization and comparison
    - Statistical aggregations

    All methods are static and can be called without instantiation.
    """

    @staticmethod
    def calculate_precision_recall_f1(
        correct_tools: List[str],
        used_tools: List[str]
    ) -> Dict[str, float]:
        """Calculate precision, recall, and F1 score for tool usage.

        Precision = True Positives / (True Positives + False Positives)
        Recall = True Positives / (True Positives + False Negatives)
        F1 = 2 * (Precision * Recall) / (Precision + Recall)

        Args:
            correct_tools: Expected/ground truth tools
            used_tools: Actually used tools

        Returns:
            Dict with precision, recall, f1_score keys (values 0.0-1.0)

        Examples:
            >>> MetricsCalculator.calculate_precision_recall_f1(
            ...     correct_tools=["tool1", "tool2"],
            ...     used_tools=["tool1", "tool2"]
            ... )
            {'precision': 1.0, 'recall': 1.0, 'f1_score': 1.0}

            >>> MetricsCalculator.calculate_precision_recall_f1(
            ...     correct_tools=["tool1", "tool2"],
            ...     used_tools=["tool1", "tool3"]
            ... )
            {'precision': 0.5, 'recall': 0.5, 'f1_score': 0.5}

        Note:
            Returns 0.0 for all metrics if used_tools is empty
        """
        if not used_tools:
            return {"precision": 0.0, "recall": 0.0, "f1_score": 0.0}

        correct_set = set(correct_tools)
        used_set = set(used_tools)

        true_positives = len(correct_set & used_set)
        false_positives = len(used_set - correct_set)
        false_negatives = len(correct_set - used_set)

        precision = true_positives / len(used_set) if used_set else 0.0
        recall = true_positives / len(correct_set) if correct_set else 0.0

        if precision + recall > 0:
            f1_score = (2 * precision * recall) / (precision + recall)
        else:
            f1_score = 0.0

        return {
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score
        }

    @staticmethod
    def calculate_consensus(
        answers: List[str],
        threshold: float = 0.5,
        similarity_fn: Optional[Callable[[str, str], bool]] = None
    ) -> Dict[str, Any]:
        """Calculate consensus from multiple answer attempts.

        Used for pass^k metrics to determine if multiple attempts agree
        on the same answer.

        Args:
            answers: List of answer strings
            threshold: Minimum fraction for consensus (default 0.5 = majority)
            similarity_fn: Optional function to compare answer similarity
                          If None, uses exact string matching

        Returns:
            Dict with keys:
            - consensus_answer (str): Most common answer
            - consensus_count (int): Number of times it appears
            - pass_rate (float): Fraction of answers matching consensus
            - distribution (dict): Full answer frequency distribution

        Examples:
            >>> MetricsCalculator.calculate_consensus(
            ...     answers=["answer1", "answer1", "answer2"]
            ... )
            {'consensus_answer': 'answer1', 'consensus_count': 2, 'pass_rate': 0.666..., 'distribution': {'answer1': 2, 'answer2': 1}}

        Note:
            Returns None for consensus_answer if answers list is empty
        """
        if not answers:
            return {
                "consensus_answer": None,
                "consensus_count": 0,
                "pass_rate": 0.0,
                "distribution": {}
            }

        if similarity_fn:
            # Cluster similar answers using custom similarity function
            clusters = []
            for answer in answers:
                found_cluster = False
                for cluster in clusters:
                    if similarity_fn(answer, cluster[0]):
                        cluster.append(answer)
                        found_cluster = True
                        break
                if not found_cluster:
                    clusters.append([answer])

            # Find largest cluster
            largest_cluster = max(clusters, key=len)
            consensus_answer = largest_cluster[0]
            consensus_count = len(largest_cluster)

            # Build distribution from clusters
            distribution = {}
            for cluster in clusters:
                representative = cluster[0]
                distribution[representative] = len(cluster)
        else:
            # Simple exact matching
            counter = Counter(answers)
            consensus_answer, consensus_count = counter.most_common(1)[0]
            distribution = dict(counter)

        pass_rate = consensus_count / len(answers)

        return {
            "consensus_answer": consensus_answer,
            "consensus_count": consensus_count,
            "pass_rate": pass_rate,
            "distribution": distribution
        }

    @staticmethod
    def normalize_answer(answer: str) -> str:
        """Normalize answer for comparison.

        Normalization steps:
        1. Convert to lowercase
        2. Strip leading/trailing whitespace
        3. Remove punctuation
        4. Collapse multiple spaces to single space

        Args:
            answer: Raw answer string

        Returns:
            Normalized answer string

        Examples:
            >>> MetricsCalculator.normalize_answer("  Hello, World!  ")
            'hello world'

            >>> MetricsCalculator.normalize_answer("Apple Inc.")
            'apple inc'

        Note:
            Useful for fuzzy answer comparison where formatting
            differences should not affect correctness
        """
        # Convert to lowercase and strip whitespace
        normalized = answer.lower().strip()

        # Remove punctuation (keep alphanumeric and spaces)
        normalized = re.sub(r'[^\w\s]', '', normalized)

        # Collapse multiple spaces
        normalized = ' '.join(normalized.split())

        return normalized

    @staticmethod
    def calculate_average(values: List[float]) -> float:
        """Calculate average of numeric values.

        Args:
            values: List of numeric values

        Returns:
            Average value, or 0.0 if list is empty

        Examples:
            >>> MetricsCalculator.calculate_average([1.0, 2.0, 3.0])
            2.0

            >>> MetricsCalculator.calculate_average([])
            0.0
        """
        if not values:
            return 0.0
        return sum(values) / len(values)

    @staticmethod
    def calculate_weighted_average(
        values: List[float],
        weights: List[float]
    ) -> float:
        """Calculate weighted average of numeric values.

        Args:
            values: List of numeric values
            weights: List of weight values (same length as values)

        Returns:
            Weighted average, or 0.0 if lists are empty

        Raises:
            ValueError: If values and weights have different lengths

        Examples:
            >>> MetricsCalculator.calculate_weighted_average(
            ...     values=[1.0, 2.0, 3.0],
            ...     weights=[1.0, 2.0, 1.0]
            ... )
            2.0

        Note:
            Weight sum is normalized to 1.0 before calculation
        """
        if not values or not weights:
            return 0.0

        if len(values) != len(weights):
            raise ValueError("values and weights must have same length")

        total_weight = sum(weights)
        if total_weight == 0:
            return 0.0

        weighted_sum = sum(v * w for v, w in zip(values, weights))
        return weighted_sum / total_weight

    @staticmethod
    def calculate_pass_rate(
        passed_count: int,
        total_count: int
    ) -> float:
        """Calculate pass rate as a fraction.

        Args:
            passed_count: Number of passed items
            total_count: Total number of items

        Returns:
            Pass rate as float (0.0-1.0), or 0.0 if total is 0

        Examples:
            >>> MetricsCalculator.calculate_pass_rate(8, 10)
            0.8

            >>> MetricsCalculator.calculate_pass_rate(0, 0)
            0.0
        """
        if total_count == 0:
            return 0.0
        return passed_count / total_count
