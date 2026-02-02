"""Evaluation metrics module.

Includes:
- pass^k consensus metrics
- B2B-specific metrics (company research, financial analysis, etc.)
- Depth-aware metrics for long-horizon planning
"""

from .pass_k import PassKCalculator, PassKResult, format_pass_k_summary
from .b2b_metrics import (
    B2BMetrics, CategoryMetrics, QuestionEvaluation,
    calculate_b2b_metrics, calculate_tool_precision, calculate_tool_recall,
    calculate_tool_f1, format_b2b_metrics_report, check_b2b_targets,
    get_score_grade, SCORE_THRESHOLDS
)
from .depth_metrics import (
    StepEvaluation, DepthMetrics, PerStepConsistency, PassKDepthResult,
    AggregateDepthMetrics, calculate_per_step_pass_k,
    calculate_depth_weighted_pass_k, calculate_aggregate_depth_metrics,
    format_depth_metrics_report, check_depth_targets
)

__all__ = [
    # pass^k
    "PassKCalculator",
    "PassKResult",
    "format_pass_k_summary",
    # B2B Metrics
    "B2BMetrics",
    "CategoryMetrics",
    "QuestionEvaluation",
    "calculate_b2b_metrics",
    "calculate_tool_precision",
    "calculate_tool_recall",
    "calculate_tool_f1",
    "format_b2b_metrics_report",
    "check_b2b_targets",
    "get_score_grade",
    "SCORE_THRESHOLDS",
    # Depth Metrics
    "StepEvaluation",
    "DepthMetrics",
    "PerStepConsistency",
    "PassKDepthResult",
    "AggregateDepthMetrics",
    "calculate_per_step_pass_k",
    "calculate_depth_weighted_pass_k",
    "calculate_aggregate_depth_metrics",
    "format_depth_metrics_report",
    "check_depth_targets",
]
