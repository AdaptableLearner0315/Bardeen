"""
Step-by-step reasoning tracer for depth-aware evaluation.

Tracks reasoning steps during agent execution, capturing:
- Tool selection at each step
- Parameters and reasoning
- Execution results and timing
- Step-level scoring
"""

import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import json
import copy


@dataclass
class StepTrace:
    """Trace of a single reasoning step."""
    step_number: int
    timestamp: str = ""

    # Tool information
    tool_name: str = ""
    tool_params: Dict[str, Any] = field(default_factory=dict)

    # Reasoning captured from agent
    reasoning: str = ""

    # Execution results
    result: Any = None
    success: bool = True
    error_message: str = ""

    # Timing
    latency_ms: float = 0.0

    # Optional scoring (populated by evaluator)
    tool_selection_score: float = 0.0  # 0-25
    execution_score: float = 0.0       # 0-25
    reasoning_score: float = 0.0       # 0-25

    @property
    def total_step_score(self) -> float:
        """Total score for this step (max 75)."""
        return self.tool_selection_score + self.execution_score + self.reasoning_score

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "step_number": self.step_number,
            "timestamp": self.timestamp,
            "tool_name": self.tool_name,
            "tool_params": self.tool_params,
            "reasoning": self.reasoning,
            "result": str(self.result)[:500] if self.result else None,  # Truncate
            "success": self.success,
            "error_message": self.error_message,
            "latency_ms": self.latency_ms,
            "scores": {
                "tool_selection": self.tool_selection_score,
                "execution": self.execution_score,
                "reasoning": self.reasoning_score,
                "total": self.total_step_score
            }
        }


class StepTracer:
    """
    Tracer for capturing reasoning steps during agent execution.

    Usage:
        tracer = StepTracer(question_id="company_001")

        # Wrap tool calls
        with tracer.trace_step("web_search", {"query": "Stripe founders"}):
            result = web_search(query="Stripe founders")

        # Or manual tracking
        tracer.start_step("calculator", {"expression": "150/5"})
        result = calculator(expression="150/5")
        tracer.end_step(result, success=True)

        # Get results
        traces = tracer.get_traces()
        metrics = tracer.get_depth_metrics()
    """

    def __init__(self, question_id: str, question: str = ""):
        self.question_id = question_id
        self.question = question
        self.traces: List[StepTrace] = []
        self.current_step: Optional[StepTrace] = None
        self._step_counter = 0
        self._start_time: Optional[float] = None

    def start_step(
        self,
        tool_name: str,
        tool_params: Dict[str, Any],
        reasoning: str = ""
    ) -> StepTrace:
        """
        Start tracing a new step.

        Args:
            tool_name: Name of the tool being called
            tool_params: Parameters passed to the tool
            reasoning: Agent's reasoning for this tool choice

        Returns:
            The new StepTrace object
        """
        self._step_counter += 1
        self._start_time = time.time()

        self.current_step = StepTrace(
            step_number=self._step_counter,
            timestamp=datetime.now().isoformat(),
            tool_name=tool_name,
            tool_params=copy.deepcopy(tool_params),
            reasoning=reasoning
        )

        return self.current_step

    def end_step(
        self,
        result: Any = None,
        success: bool = True,
        error_message: str = ""
    ) -> StepTrace:
        """
        End the current step and record results.

        Args:
            result: Result from tool execution
            success: Whether execution succeeded
            error_message: Error message if failed

        Returns:
            The completed StepTrace
        """
        if self.current_step is None:
            raise ValueError("No step in progress. Call start_step first.")

        # Calculate latency
        if self._start_time:
            self.current_step.latency_ms = (time.time() - self._start_time) * 1000

        self.current_step.result = result
        self.current_step.success = success
        self.current_step.error_message = error_message

        # Store completed step
        self.traces.append(self.current_step)
        completed_step = self.current_step

        # Reset current step
        self.current_step = None
        self._start_time = None

        return completed_step

    def trace_step(
        self,
        tool_name: str,
        tool_params: Dict[str, Any],
        reasoning: str = ""
    ):
        """
        Context manager for tracing a step.

        Usage:
            with tracer.trace_step("calculator", {"expression": "1+1"}):
                result = calculator(expression="1+1")
        """
        return _StepTracerContext(self, tool_name, tool_params, reasoning)

    def add_reasoning(self, reasoning: str):
        """Add reasoning to the current step."""
        if self.current_step:
            self.current_step.reasoning = reasoning

    def get_traces(self) -> List[StepTrace]:
        """Get all completed step traces."""
        return self.traces.copy()

    def get_depth(self) -> int:
        """Get the maximum depth (number of steps)."""
        return len(self.traces)

    def get_total_latency_ms(self) -> float:
        """Get total latency across all steps."""
        return sum(t.latency_ms for t in self.traces)

    def get_tools_used(self) -> List[str]:
        """Get list of tools used in order."""
        return [t.tool_name for t in self.traces]

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of traced execution."""
        return {
            "question_id": self.question_id,
            "question": self.question,
            "depth": self.get_depth(),
            "tools_used": self.get_tools_used(),
            "total_latency_ms": self.get_total_latency_ms(),
            "success_rate": sum(1 for t in self.traces if t.success) / max(len(self.traces), 1),
            "steps": [t.to_dict() for t in self.traces]
        }

    def to_json(self) -> str:
        """Export traces as JSON string."""
        return json.dumps(self.get_summary(), indent=2)

    def reset(self):
        """Reset tracer for a new question."""
        self.traces = []
        self.current_step = None
        self._step_counter = 0
        self._start_time = None


class _StepTracerContext:
    """Context manager for step tracing."""

    def __init__(
        self,
        tracer: StepTracer,
        tool_name: str,
        tool_params: Dict[str, Any],
        reasoning: str
    ):
        self.tracer = tracer
        self.tool_name = tool_name
        self.tool_params = tool_params
        self.reasoning = reasoning
        self.result = None
        self.error = None

    def __enter__(self):
        self.tracer.start_step(self.tool_name, self.tool_params, self.reasoning)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.tracer.end_step(
                result=None,
                success=False,
                error_message=str(exc_val)
            )
        else:
            self.tracer.end_step(
                result=self.result,
                success=True
            )
        return False  # Don't suppress exceptions


class MultiAttemptTracer:
    """
    Tracer for multiple attempts of the same question.

    Used for per-step pass^k calculation.
    """

    def __init__(self, question_id: str, question: str = "", k: int = 5):
        self.question_id = question_id
        self.question = question
        self.k = k
        self.attempts: List[StepTracer] = []
        self._current_attempt: Optional[StepTracer] = None

    def start_attempt(self) -> StepTracer:
        """Start a new attempt, returns tracer for this attempt."""
        self._current_attempt = StepTracer(
            question_id=f"{self.question_id}_attempt_{len(self.attempts) + 1}",
            question=self.question
        )
        return self._current_attempt

    def end_attempt(self):
        """End current attempt and store it."""
        if self._current_attempt:
            self.attempts.append(self._current_attempt)
            self._current_attempt = None

    def get_all_traces(self) -> List[List[StepTrace]]:
        """Get traces from all attempts."""
        return [attempt.get_traces() for attempt in self.attempts]

    def get_step_consistency(self, step_number: int) -> Dict[str, Any]:
        """
        Get tool consistency at a specific step.

        Args:
            step_number: 1-indexed step number

        Returns:
            Dict with consensus info
        """
        from collections import Counter

        tools_at_step = []
        for attempt in self.attempts:
            traces = attempt.get_traces()
            if len(traces) >= step_number:
                tools_at_step.append(traces[step_number - 1].tool_name)

        if not tools_at_step:
            return {"step": step_number, "error": "No data for this step"}

        counter = Counter(tools_at_step)
        majority_tool, count = counter.most_common(1)[0]

        return {
            "step": step_number,
            "consensus": count / len(tools_at_step),
            "majority_tool": majority_tool,
            "distribution": dict(counter),
            "total_attempts": len(tools_at_step)
        }

    def get_per_step_pass_k(self, threshold: float = 0.6) -> Dict[str, Any]:
        """
        Calculate per-step pass^k metrics.

        Args:
            threshold: Consensus threshold (default 60%)

        Returns:
            Dict with per-step consistency metrics
        """
        max_depth = max(
            (len(attempt.get_traces()) for attempt in self.attempts),
            default=0
        )

        results = {}
        for step in range(1, max_depth + 1):
            consistency = self.get_step_consistency(step)
            if "error" not in consistency:
                passed = consistency["consensus"] >= threshold
                results[f"step_{step}"] = {
                    **consistency,
                    "passed": passed,
                    "threshold": threshold
                }

        # Overall pass rate
        step_results = [v for v in results.values() if isinstance(v, dict)]
        passed_steps = sum(1 for r in step_results if r.get("passed", False))

        results["overall"] = {
            "steps_evaluated": len(step_results),
            "steps_passed": passed_steps,
            "pass_rate": passed_steps / max(len(step_results), 1)
        }

        return results


def create_tracer_middleware(tracer: StepTracer) -> Callable:
    """
    Create middleware function to wrap tool calls with tracing.

    Returns a function that wraps tool execution with tracing.
    """
    def middleware(tool_name: str, tool_params: Dict[str, Any], tool_fn: Callable) -> Any:
        tracer.start_step(tool_name, tool_params)
        try:
            result = tool_fn(**tool_params)
            tracer.end_step(result=result, success=True)
            return result
        except Exception as e:
            tracer.end_step(result=None, success=False, error_message=str(e))
            raise

    return middleware
