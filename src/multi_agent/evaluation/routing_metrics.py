"""
Routing Metrics for Multi-Agent System Evaluation

Measures how accurately the router selects agents for queries:
- Correct agent selection rate
- Multi-agent vs single-agent accuracy
- Category-specific routing accuracy
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from collections import defaultdict

from ..guardrails.tool_access import AgentType


@dataclass
class RoutingAccuracyResult:
    """Result of routing accuracy evaluation for a single query."""
    query: str
    expected_agents: List[AgentType]
    actual_agents: List[AgentType]
    is_correct: bool
    partial_match_score: float  # 0.0 to 1.0
    reasoning: str


@dataclass
class RoutingMetrics:
    """
    Metrics for evaluating routing accuracy.

    Tracks:
    - Overall routing accuracy
    - Per-category accuracy
    - Multi-agent detection rate
    - Agent selection precision/recall
    """

    total_queries: int = 0
    correct_routes: int = 0
    partial_matches: int = 0
    category_accuracy: Dict[str, Dict[str, int]] = field(
        default_factory=lambda: defaultdict(lambda: {"correct": 0, "total": 0})
    )
    agent_selection_stats: Dict[AgentType, Dict[str, int]] = field(
        default_factory=lambda: defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    )
    results: List[RoutingAccuracyResult] = field(default_factory=list)

    def record_routing(
        self,
        query: str,
        expected_agents: List[AgentType],
        actual_agents: List[AgentType],
        category: Optional[str] = None,
    ) -> RoutingAccuracyResult:
        """
        Record a routing decision and evaluate accuracy.

        Args:
            query: The query that was routed
            expected_agents: Expected agent assignments
            actual_agents: Actual agent assignments
            category: Optional query category

        Returns:
            RoutingAccuracyResult with evaluation details
        """
        self.total_queries += 1

        expected_set = set(expected_agents)
        actual_set = set(actual_agents)

        # Check for exact match
        is_correct = expected_set == actual_set

        # Calculate partial match score (Jaccard similarity)
        if expected_set or actual_set:
            intersection = len(expected_set & actual_set)
            union = len(expected_set | actual_set)
            partial_match_score = intersection / union if union > 0 else 0.0
        else:
            partial_match_score = 1.0  # Both empty

        # Generate reasoning
        if is_correct:
            reasoning = "Exact match"
            self.correct_routes += 1
        elif partial_match_score > 0:
            self.partial_matches += 1
            missing = expected_set - actual_set
            extra = actual_set - expected_set
            reasoning_parts = []
            if missing:
                reasoning_parts.append(f"Missing: {[a.value for a in missing]}")
            if extra:
                reasoning_parts.append(f"Extra: {[a.value for a in extra]}")
            reasoning = "; ".join(reasoning_parts)
        else:
            reasoning = f"No match: expected {[a.value for a in expected_agents]}, got {[a.value for a in actual_agents]}"

        # Update category accuracy
        if category:
            self.category_accuracy[category]["total"] += 1
            if is_correct:
                self.category_accuracy[category]["correct"] += 1

        # Update agent selection stats (for precision/recall)
        for agent in expected_set:
            if agent in actual_set:
                self.agent_selection_stats[agent]["tp"] += 1
            else:
                self.agent_selection_stats[agent]["fn"] += 1

        for agent in actual_set:
            if agent not in expected_set:
                self.agent_selection_stats[agent]["fp"] += 1

        # Create result
        result = RoutingAccuracyResult(
            query=query,
            expected_agents=expected_agents,
            actual_agents=actual_agents,
            is_correct=is_correct,
            partial_match_score=partial_match_score,
            reasoning=reasoning,
        )
        self.results.append(result)

        return result

    @property
    def accuracy(self) -> float:
        """Overall routing accuracy (exact matches only)."""
        if self.total_queries == 0:
            return 0.0
        return self.correct_routes / self.total_queries

    @property
    def partial_accuracy(self) -> float:
        """Accuracy including partial matches."""
        if self.total_queries == 0:
            return 0.0
        return (self.correct_routes + self.partial_matches) / self.total_queries

    @property
    def average_partial_score(self) -> float:
        """Average partial match score across all queries."""
        if not self.results:
            return 0.0
        return sum(r.partial_match_score for r in self.results) / len(self.results)

    def get_category_accuracy(self, category: str) -> float:
        """Get accuracy for a specific category."""
        stats = self.category_accuracy.get(category)
        if not stats or stats["total"] == 0:
            return 0.0
        return stats["correct"] / stats["total"]

    def get_agent_precision(self, agent: AgentType) -> float:
        """Get precision for a specific agent selection."""
        stats = self.agent_selection_stats.get(agent)
        if not stats:
            return 0.0
        tp = stats["tp"]
        fp = stats["fp"]
        if tp + fp == 0:
            return 0.0
        return tp / (tp + fp)

    def get_agent_recall(self, agent: AgentType) -> float:
        """Get recall for a specific agent selection."""
        stats = self.agent_selection_stats.get(agent)
        if not stats:
            return 0.0
        tp = stats["tp"]
        fn = stats["fn"]
        if tp + fn == 0:
            return 0.0
        return tp / (tp + fn)

    def get_agent_f1(self, agent: AgentType) -> float:
        """Get F1 score for a specific agent selection."""
        precision = self.get_agent_precision(agent)
        recall = self.get_agent_recall(agent)
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary."""
        return {
            "total_queries": self.total_queries,
            "correct_routes": self.correct_routes,
            "accuracy": self.accuracy,
            "partial_accuracy": self.partial_accuracy,
            "average_partial_score": self.average_partial_score,
            "category_accuracy": {
                cat: self.get_category_accuracy(cat)
                for cat in self.category_accuracy.keys()
            },
            "agent_metrics": {
                agent.value: {
                    "precision": self.get_agent_precision(agent),
                    "recall": self.get_agent_recall(agent),
                    "f1": self.get_agent_f1(agent),
                }
                for agent in AgentType
                if agent in self.agent_selection_stats
            },
        }
