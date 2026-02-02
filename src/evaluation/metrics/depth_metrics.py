"""
Depth-aware evaluation metrics for long-horizon planning.

Tracks:
- Reasoning chain depth (number of sequential tool calls)
- Per-step scoring (tool selection + execution + reasoning at each step)
- Per-step pass^k (consistency of tool choice at each depth across k attempts)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from collections import Counter
import statistics


@dataclass
class StepEvaluation:
    """Evaluation of a single reasoning step."""
    depth: int                    # Which step (1, 2, 3...)
    tool_name: str                # Tool selected at this step
    tool_params: Dict[str, Any] = field(default_factory=dict)  # Parameters passed
    reasoning: str = ""           # Why this tool was chosen
    step_score: float = 0.0       # Score for this step (0-25)
    latency_ms: float = 0.0       # Execution time
    success: bool = True          # Whether tool executed successfully


@dataclass
class DepthMetrics:
    """Aggregated depth metrics for a single query execution."""
    question_id: str
    max_depth: int = 0                    # Deepest step reached
    avg_step_score: float = 0.0           # Average score across steps
    depth_weighted_score: float = 0.0     # Score with depth bonus
    total_latency_ms: float = 0.0         # Total execution time
    step_evaluations: List[StepEvaluation] = field(default_factory=list)

    def add_step(self, step: StepEvaluation):
        """Add a step evaluation and update metrics."""
        self.step_evaluations.append(step)
        self.max_depth = max(self.max_depth, step.depth)
        self.total_latency_ms += step.latency_ms
        self._recalculate_scores()

    def _recalculate_scores(self):
        """Recalculate aggregate scores after adding steps."""
        if not self.step_evaluations:
            return

        scores = [s.step_score for s in self.step_evaluations]
        self.avg_step_score = statistics.mean(scores)

        # Depth-weighted score: deeper reasoning chains get a bonus
        # Formula: avg_step_score * (1 + 0.1 * (max_depth - 1))
        depth_multiplier = 1 + 0.1 * (self.max_depth - 1)
        self.depth_weighted_score = self.avg_step_score * depth_multiplier


@dataclass
class PerStepConsistency:
    """Consistency metrics for a specific step across k attempts."""
    step_number: int
    consensus: float                      # % of attempts with same tool
    passed: bool                          # Whether consensus >= threshold
    majority_tool: str                    # Most common tool at this step
    distribution: Dict[str, int] = field(default_factory=dict)  # Tool -> count
    threshold: float = 0.6


@dataclass
class PassKDepthResult:
    """Per-step pass^k results for a question."""
    question_id: str
    k: int                                # Number of attempts
    per_step_consistency: List[PerStepConsistency] = field(default_factory=list)
    overall_pass_rate: float = 0.0        # % of steps that passed
    planning_coherence: float = 0.0       # LLM judge rating of tool sequence logic

    @property
    def steps_passed(self) -> int:
        return sum(1 for s in self.per_step_consistency if s.passed)

    @property
    def total_steps(self) -> int:
        return len(self.per_step_consistency)


def calculate_per_step_pass_k(
    attempts: List[List[StepEvaluation]],
    k: int = 5,
    threshold: float = 0.6
) -> Dict[str, Any]:
    """
    Calculate pass^k at each reasoning step.

    Args:
        attempts: List of k attempts, each containing step evaluations
        k: Number of attempts
        threshold: Consensus threshold (default 60%)

    Returns:
        Dict with per-step pass^k and overall metrics
    """
    if not attempts:
        return {"error": "No attempts provided"}

    max_depth = max(len(attempt) for attempt in attempts)
    results: Dict[str, Any] = {}

    for step in range(max_depth):
        # Collect tool choices at this step across all attempts
        tools_at_step = []
        for attempt in attempts:
            if step < len(attempt):
                tools_at_step.append(attempt[step].tool_name)

        if tools_at_step:
            # Calculate consensus
            counter = Counter(tools_at_step)
            most_common_tool, count = counter.most_common(1)[0]
            consensus = count / len(tools_at_step)

            results[f"pass^{k}_step{step+1}"] = {
                "consensus": consensus,
                "passed": consensus >= threshold,
                "majority_tool": most_common_tool,
                "distribution": dict(counter)
            }

    # Overall per-step pass^k
    step_results = [v for k_name, v in results.items() if k_name.startswith("pass^")]
    passed_steps = sum(1 for r in step_results if r["passed"])

    results["overall"] = {
        "steps_passed": passed_steps,
        "total_steps": len(step_results),
        "pass_rate": passed_steps / max(len(step_results), 1)
    }

    return results


def calculate_depth_weighted_pass_k(
    attempts: List[List[StepEvaluation]],
    k: int = 5,
    threshold: float = 0.6
) -> float:
    """
    Calculate depth-weighted pass^k score.

    Weights consistency at deeper steps more heavily.
    Formula: sum(step_consensus * step_weight) / sum(step_weights)
    Where step_weight = 1 + 0.2 * (step_number - 1)

    Args:
        attempts: List of k attempts
        k: Number of attempts
        threshold: Consensus threshold

    Returns:
        Depth-weighted pass^k score (0-1)
    """
    if not attempts:
        return 0.0

    max_depth = max(len(attempt) for attempt in attempts)
    weighted_sum = 0.0
    weight_total = 0.0

    for step in range(max_depth):
        tools_at_step = []
        for attempt in attempts:
            if step < len(attempt):
                tools_at_step.append(attempt[step].tool_name)

        if tools_at_step:
            counter = Counter(tools_at_step)
            _, count = counter.most_common(1)[0]
            consensus = count / len(tools_at_step)

            # Weight increases with depth
            step_weight = 1 + 0.2 * step
            weighted_sum += consensus * step_weight
            weight_total += step_weight

    return weighted_sum / weight_total if weight_total > 0 else 0.0


@dataclass
class AggregateDepthMetrics:
    """Aggregate depth metrics across all questions."""
    total_questions: int = 0
    avg_depth: float = 0.0                    # Average reasoning chain length
    max_depth_achieved: int = 0               # Deepest chain in any query
    avg_step_score: float = 0.0               # Average step score across all
    avg_depth_weighted_score: float = 0.0     # Average depth-weighted score

    # Per-step pass^k metrics
    avg_pass_k_step1: float = 0.0             # Average consistency at step 1
    avg_pass_k_step2: float = 0.0             # Average consistency at step 2
    avg_pass_k_overall: float = 0.0           # Average consistency across all steps

    # Planning coherence
    avg_planning_coherence: float = 0.0       # LLM judge average


def calculate_aggregate_depth_metrics(
    depth_results: List[DepthMetrics],
    pass_k_results: Optional[List[PassKDepthResult]] = None
) -> AggregateDepthMetrics:
    """
    Calculate aggregate depth metrics across all questions.

    Args:
        depth_results: List of DepthMetrics for each question
        pass_k_results: Optional list of per-step pass^k results

    Returns:
        AggregateDepthMetrics with all calculated values
    """
    if not depth_results:
        return AggregateDepthMetrics()

    metrics = AggregateDepthMetrics()
    metrics.total_questions = len(depth_results)

    # Depth metrics
    depths = [d.max_depth for d in depth_results]
    metrics.avg_depth = statistics.mean(depths)
    metrics.max_depth_achieved = max(depths)

    # Score metrics
    step_scores = [d.avg_step_score for d in depth_results]
    metrics.avg_step_score = statistics.mean(step_scores)

    weighted_scores = [d.depth_weighted_score for d in depth_results]
    metrics.avg_depth_weighted_score = statistics.mean(weighted_scores)

    # Per-step pass^k metrics
    if pass_k_results:
        step1_consensus = []
        step2_consensus = []
        overall_rates = []
        coherence_scores = []

        for result in pass_k_results:
            if len(result.per_step_consistency) >= 1:
                step1_consensus.append(result.per_step_consistency[0].consensus)
            if len(result.per_step_consistency) >= 2:
                step2_consensus.append(result.per_step_consistency[1].consensus)
            overall_rates.append(result.overall_pass_rate)
            if result.planning_coherence > 0:
                coherence_scores.append(result.planning_coherence)

        if step1_consensus:
            metrics.avg_pass_k_step1 = statistics.mean(step1_consensus)
        if step2_consensus:
            metrics.avg_pass_k_step2 = statistics.mean(step2_consensus)
        if overall_rates:
            metrics.avg_pass_k_overall = statistics.mean(overall_rates)
        if coherence_scores:
            metrics.avg_planning_coherence = statistics.mean(coherence_scores)

    return metrics


def format_depth_metrics_report(metrics: AggregateDepthMetrics) -> str:
    """Format depth metrics as readable report."""
    lines = [
        "=" * 60,
        "DEPTH-AWARE EVALUATION METRICS",
        "=" * 60,
        "",
        "REASONING DEPTH",
        "-" * 40,
        f"Total Questions: {metrics.total_questions}",
        f"Average Depth: {metrics.avg_depth:.2f} steps",
        f"Max Depth Achieved: {metrics.max_depth_achieved} steps",
        "",
        "STEP SCORING",
        "-" * 40,
        f"Avg Step Score: {metrics.avg_step_score:.1f}/25",
        f"Depth-Weighted Score: {metrics.avg_depth_weighted_score:.1f}",
        "",
        "PER-STEP CONSISTENCY (pass^k)",
        "-" * 40,
        f"Step 1 Consistency: {metrics.avg_pass_k_step1:.1%}",
        f"Step 2 Consistency: {metrics.avg_pass_k_step2:.1%}",
        f"Overall Consistency: {metrics.avg_pass_k_overall:.1%}",
        "",
        "PLANNING COHERENCE",
        "-" * 40,
        f"Avg Coherence Score: {metrics.avg_planning_coherence:.1f}/10",
        "",
        "=" * 60,
    ]
    return "\n".join(lines)


def check_depth_targets(metrics: AggregateDepthMetrics) -> Dict[str, Dict[str, Any]]:
    """
    Check if depth metrics meet targets.

    Returns:
        Dict with target name, value, target, and met status
    """
    return {
        "avg_depth": {
            "value": metrics.avg_depth,
            "target": 2.0,
            "met": metrics.avg_depth >= 2.0,
            "unit": "steps"
        },
        "max_depth": {
            "value": metrics.max_depth_achieved,
            "target": 4,
            "met": metrics.max_depth_achieved >= 4,
            "unit": "steps"
        },
        "avg_step_score": {
            "value": metrics.avg_step_score,
            "target": 20.0,
            "met": metrics.avg_step_score >= 20.0,
            "unit": "/25"
        },
        "pass_k_step1": {
            "value": metrics.avg_pass_k_step1 * 100,
            "target": 70.0,
            "met": metrics.avg_pass_k_step1 >= 0.70,
            "unit": "%"
        },
        "pass_k_step2": {
            "value": metrics.avg_pass_k_step2 * 100,
            "target": 60.0,
            "met": metrics.avg_pass_k_step2 >= 0.60,
            "unit": "%"
        },
        "pass_k_overall": {
            "value": metrics.avg_pass_k_overall * 100,
            "target": 65.0,
            "met": metrics.avg_pass_k_overall >= 0.65,
            "unit": "%"
        },
        "planning_coherence": {
            "value": metrics.avg_planning_coherence,
            "target": 7.0,
            "met": metrics.avg_planning_coherence >= 7.0,
            "unit": "/10"
        }
    }
