"""Evaluation module for the B2B Account Intelligence Agent.

This module provides:
- Dataset loading and management
- Evaluation harness for running and analyzing agent performance
- pass^k consensus metrics calculation
- B2B-specific metrics (company research, financial analysis, etc.)
- Depth-aware metrics for long-horizon planning
- LLM-as-Judge evaluation
- Tool call and error tracing
- Step-by-step reasoning tracing
- ASCII visualization for results
"""

from .dataset import DatasetLoader, load_dataset
from .harness import EvaluationHarness, B2BEvaluationHarness
from .visualizer import ASCIIVisualizer
from .metrics.pass_k import PassKCalculator, PassKResult, format_pass_k_summary
from .metrics.b2b_metrics import (
    B2BMetrics, CategoryMetrics, QuestionEvaluation,
    calculate_b2b_metrics, format_b2b_metrics_report, check_b2b_targets
)
from .metrics.depth_metrics import (
    StepEvaluation, DepthMetrics, AggregateDepthMetrics,
    calculate_per_step_pass_k, calculate_aggregate_depth_metrics,
    format_depth_metrics_report, check_depth_targets
)
from .tracers.tool_tracer import ToolTracer, TraceHelper
from .tracers.error_tracer import ErrorTracer
from .tracers.step_tracer import StepTracer, MultiAttemptTracer, StepTrace

# Optional LLM Judge
try:
    from .llm_judge import LLMJudge, JudgeResult, DimensionScore, calculate_judge_metrics
    HAS_LLM_JUDGE = True
except ImportError:
    HAS_LLM_JUDGE = False
    LLMJudge = None
    JudgeResult = None
    DimensionScore = None
    calculate_judge_metrics = None

__all__ = [
    # Dataset
    "DatasetLoader",
    "load_dataset",
    # Harness
    "EvaluationHarness",
    "B2BEvaluationHarness",
    # Visualizer
    "ASCIIVisualizer",
    # pass^k Metrics
    "PassKCalculator",
    "PassKResult",
    "format_pass_k_summary",
    # B2B Metrics
    "B2BMetrics",
    "CategoryMetrics",
    "QuestionEvaluation",
    "calculate_b2b_metrics",
    "format_b2b_metrics_report",
    "check_b2b_targets",
    # Depth Metrics
    "StepEvaluation",
    "DepthMetrics",
    "AggregateDepthMetrics",
    "calculate_per_step_pass_k",
    "calculate_aggregate_depth_metrics",
    "format_depth_metrics_report",
    "check_depth_targets",
    # Tracers
    "ToolTracer",
    "TraceHelper",
    "ErrorTracer",
    "StepTracer",
    "MultiAttemptTracer",
    "StepTrace",
    # LLM Judge (optional)
    "LLMJudge",
    "JudgeResult",
    "DimensionScore",
    "calculate_judge_metrics",
    "HAS_LLM_JUDGE",
]
