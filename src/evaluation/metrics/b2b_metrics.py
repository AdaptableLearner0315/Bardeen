"""
B2B-specific evaluation metrics for Account Intelligence Agent.

Metrics aligned with actual B2B use cases:
- Company research accuracy
- Financial data currency
- Competitive intelligence quality
- Action execution success
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from collections import Counter
import statistics


@dataclass
class CategoryMetrics:
    """Metrics for a specific question category."""
    category: str
    total_questions: int = 0
    passed: int = 0
    failed: int = 0
    avg_score: float = 0.0
    avg_tool_count: float = 0.0
    tool_precision: float = 0.0  # correct tools / total tools used


@dataclass
class B2BMetrics:
    """Aggregate B2B evaluation metrics."""
    # Overall metrics
    total_questions: int = 0
    overall_pass_rate: float = 0.0
    avg_accuracy_score: float = 0.0
    avg_completeness_score: float = 0.0

    # Tool metrics
    tool_precision: float = 0.0  # correct tools / total tools
    multi_tool_rate: float = 0.0  # questions using 2+ tools

    # Action metrics
    action_success_rate: float = 0.0  # successful actions / action attempts

    # Category breakdowns
    category_metrics: Dict[str, CategoryMetrics] = field(default_factory=dict)

    # Tool usage distribution
    tool_usage: Dict[str, int] = field(default_factory=dict)


@dataclass
class QuestionEvaluation:
    """Evaluation data for a single question."""
    question_id: str
    category: str
    question: str
    answer: str
    tools_used: List[str]
    expected_tools: List[str]
    score: float  # 0-100
    passed: bool
    dimension_scores: Optional[Dict[str, float]] = None


def calculate_tool_precision(
    tools_used: List[str],
    expected_tools: List[str]
) -> float:
    """
    Calculate precision of tool selection.

    Precision = |correct tools| / |tools used|
    """
    if not tools_used:
        return 0.0

    expected_set = set(expected_tools)
    correct = sum(1 for t in tools_used if t in expected_set)
    return correct / len(tools_used)


def calculate_tool_recall(
    tools_used: List[str],
    expected_tools: List[str]
) -> float:
    """
    Calculate recall of tool selection.

    Recall = |correct tools| / |expected tools|
    """
    if not expected_tools:
        return 1.0  # If no tools expected, any usage is acceptable

    used_set = set(tools_used)
    correct = sum(1 for t in expected_tools if t in used_set)
    return correct / len(expected_tools)


def calculate_tool_f1(
    tools_used: List[str],
    expected_tools: List[str]
) -> float:
    """Calculate F1 score for tool selection."""
    precision = calculate_tool_precision(tools_used, expected_tools)
    recall = calculate_tool_recall(tools_used, expected_tools)

    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)


def calculate_b2b_metrics(evaluations: List[QuestionEvaluation]) -> B2BMetrics:
    """
    Calculate comprehensive B2B metrics from evaluations.

    Args:
        evaluations: List of QuestionEvaluation objects

    Returns:
        B2BMetrics with all calculated metrics
    """
    if not evaluations:
        return B2BMetrics()

    metrics = B2BMetrics()
    metrics.total_questions = len(evaluations)

    # Overall pass rate
    passed_count = sum(1 for e in evaluations if e.passed)
    metrics.overall_pass_rate = passed_count / len(evaluations)

    # Average scores
    scores = [e.score for e in evaluations]
    metrics.avg_accuracy_score = statistics.mean(scores)

    # Calculate completeness from dimension scores if available
    completeness_scores = []
    for e in evaluations:
        if e.dimension_scores and "answer_quality" in e.dimension_scores:
            completeness_scores.append(e.dimension_scores["answer_quality"])
    if completeness_scores:
        metrics.avg_completeness_score = statistics.mean(completeness_scores)

    # Tool precision (aggregate)
    all_precision = []
    for e in evaluations:
        precision = calculate_tool_precision(e.tools_used, e.expected_tools)
        all_precision.append(precision)
    metrics.tool_precision = statistics.mean(all_precision) if all_precision else 0.0

    # Multi-tool rate
    multi_tool_count = sum(1 for e in evaluations if len(e.tools_used) >= 2)
    metrics.multi_tool_rate = multi_tool_count / len(evaluations)

    # Action success rate (for action_execution category)
    action_evals = [e for e in evaluations if e.category == "action_execution"]
    if action_evals:
        action_passed = sum(1 for e in action_evals if e.passed)
        metrics.action_success_rate = action_passed / len(action_evals)

    # Tool usage distribution
    tool_counter: Counter = Counter()
    for e in evaluations:
        tool_counter.update(e.tools_used)
    metrics.tool_usage = dict(tool_counter)

    # Category breakdowns
    categories = set(e.category for e in evaluations)
    for category in categories:
        cat_evals = [e for e in evaluations if e.category == category]

        cat_metrics = CategoryMetrics(category=category)
        cat_metrics.total_questions = len(cat_evals)
        cat_metrics.passed = sum(1 for e in cat_evals if e.passed)
        cat_metrics.failed = cat_metrics.total_questions - cat_metrics.passed
        cat_metrics.avg_score = statistics.mean([e.score for e in cat_evals])
        cat_metrics.avg_tool_count = statistics.mean(
            [len(e.tools_used) for e in cat_evals]
        )

        # Category tool precision
        cat_precisions = [
            calculate_tool_precision(e.tools_used, e.expected_tools)
            for e in cat_evals
        ]
        cat_metrics.tool_precision = statistics.mean(cat_precisions) if cat_precisions else 0.0

        metrics.category_metrics[category] = cat_metrics

    return metrics


def format_b2b_metrics_report(metrics: B2BMetrics) -> str:
    """
    Format B2B metrics as a readable report.

    Args:
        metrics: B2BMetrics object

    Returns:
        Formatted string report
    """
    lines = [
        "=" * 60,
        "B2B ACCOUNT INTELLIGENCE EVALUATION REPORT",
        "=" * 60,
        "",
        "OVERALL METRICS",
        "-" * 40,
        f"Total Questions: {metrics.total_questions}",
        f"Pass Rate: {metrics.overall_pass_rate:.1%}",
        f"Average Score: {metrics.avg_accuracy_score:.1f}/100",
        f"Completeness Score: {metrics.avg_completeness_score:.1f}/25",
        "",
        "TOOL METRICS",
        "-" * 40,
        f"Tool Precision: {metrics.tool_precision:.1%}",
        f"Multi-Tool Rate: {metrics.multi_tool_rate:.1%}",
        f"Action Success Rate: {metrics.action_success_rate:.1%}",
        "",
        "TOOL USAGE DISTRIBUTION",
        "-" * 40,
    ]

    for tool, count in sorted(metrics.tool_usage.items(), key=lambda x: -x[1]):
        lines.append(f"  {tool}: {count} uses")

    lines.extend([
        "",
        "CATEGORY BREAKDOWN",
        "-" * 40,
    ])

    for category, cat_metrics in metrics.category_metrics.items():
        lines.extend([
            f"",
            f"  {category.upper().replace('_', ' ')}",
            f"    Questions: {cat_metrics.total_questions}",
            f"    Pass Rate: {cat_metrics.passed}/{cat_metrics.total_questions} "
            f"({cat_metrics.passed/cat_metrics.total_questions:.1%})",
            f"    Avg Score: {cat_metrics.avg_score:.1f}",
            f"    Avg Tools: {cat_metrics.avg_tool_count:.1f}",
            f"    Tool Precision: {cat_metrics.tool_precision:.1%}",
        ])

    lines.extend([
        "",
        "=" * 60,
    ])

    return "\n".join(lines)


# Score thresholds for evaluation
SCORE_THRESHOLDS = {
    "excellent": 90,
    "good": 75,
    "acceptable": 60,
    "failing": 0
}


def get_score_grade(score: float) -> str:
    """Get grade label for a score."""
    if score >= SCORE_THRESHOLDS["excellent"]:
        return "EXCELLENT"
    elif score >= SCORE_THRESHOLDS["good"]:
        return "GOOD"
    elif score >= SCORE_THRESHOLDS["acceptable"]:
        return "ACCEPTABLE"
    else:
        return "FAILING"


def check_b2b_targets(metrics: B2BMetrics) -> Dict[str, Dict[str, Any]]:
    """
    Check if metrics meet B2B targets.

    Returns:
        Dict with target name, value, target, and met status
    """
    targets = {
        "accuracy_score": {
            "value": metrics.avg_accuracy_score,
            "target": 75.0,
            "met": metrics.avg_accuracy_score >= 75.0,
            "unit": "/100"
        },
        "pass_rate": {
            "value": metrics.overall_pass_rate * 100,
            "target": 75.0,
            "met": metrics.overall_pass_rate >= 0.75,
            "unit": "%"
        },
        "tool_precision": {
            "value": metrics.tool_precision * 100,
            "target": 80.0,
            "met": metrics.tool_precision >= 0.80,
            "unit": "%"
        },
        "multi_tool_rate": {
            "value": metrics.multi_tool_rate * 100,
            "target": 60.0,
            "met": metrics.multi_tool_rate >= 0.60,
            "unit": "%"
        },
        "action_success": {
            "value": metrics.action_success_rate * 100,
            "target": 70.0,
            "met": metrics.action_success_rate >= 0.70,
            "unit": "%"
        }
    }
    return targets
