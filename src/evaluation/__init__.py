"""Evaluation module for the B2B Account Intelligence Agent.

This module provides:
- Dataset loading and management
- Evaluation harness for running and analyzing agent performance
- pass^k consensus metrics calculation
- Tool call and error tracing
- ASCII visualization for results
"""

from .dataset import DatasetLoader, load_dataset
from .harness import EvaluationHarness
from .visualizer import ASCIIVisualizer
from .metrics.pass_k import PassKCalculator, PassKResult, format_pass_k_summary
from .tracers.tool_tracer import ToolTracer, TraceHelper
from .tracers.error_tracer import ErrorTracer

__all__ = [
    # Dataset
    "DatasetLoader",
    "load_dataset",
    # Harness
    "EvaluationHarness",
    # Visualizer
    "ASCIIVisualizer",
    # Metrics
    "PassKCalculator",
    "PassKResult",
    "format_pass_k_summary",
    # Tracers
    "ToolTracer",
    "TraceHelper",
    "ErrorTracer",
]
