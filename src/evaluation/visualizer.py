"""ASCII art visualizer for tool call traces and evaluation results."""

from typing import List, Dict
from ..shared.models import (
    ToolCallTrace, AttemptResult, QuestionResult,
    ToolStatus, ErrorTrace
)
from .metrics.pass_k import PassKResult


class ASCIIVisualizer:
    """Generate ASCII art visualizations for traces and results."""

    # Unicode box drawing characters
    HORIZONTAL = "─"
    VERTICAL = "│"
    DOWN_RIGHT = "┌"
    DOWN_LEFT = "┐"
    UP_RIGHT = "└"
    UP_LEFT = "┘"
    VERTICAL_RIGHT = "├"
    VERTICAL_LEFT = "┤"
    DOWN_HORIZONTAL = "┬"
    UP_HORIZONTAL = "┴"
    VERTICAL_HORIZONTAL = "┼"
    DOUBLE_HORIZONTAL = "═"

    def __init__(self, width: int = 80):
        self.width = width

    def visualize_attempt(self, attempt: AttemptResult) -> str:
        """Visualize a single attempt with tool call traces."""
        lines = []

        # Header
        status_symbol = "✓" if attempt.is_correct else "✗"
        status_text = "SUCCESS" if attempt.is_correct else "FAIL"
        lines.append(f"\nAttempt {attempt.attempt_number}/10: {status_symbol} {status_text}")
        lines.append(self.HORIZONTAL * self.width)

        # Tool calls
        if not attempt.tool_calls:
            lines.append("START → LLM Reasoning")
            lines.append("  └─→ FINAL ANSWER (no tools used)")
        else:
            lines.append("START → LLM Reasoning")

            for i, trace in enumerate(attempt.tool_calls, 1):
                lines.extend(self._format_tool_call(trace, i, is_last=(i == len(attempt.tool_calls))))

            # Final answer section
            lines.append("  │")
            lines.append(f"  └─→ FINAL ANSWER: \"{attempt.final_answer}\"")
            lines.append(f"       └─ Correctness: {status_symbol} {status_text} "
                        f"(similarity: {attempt.semantic_similarity:.2f})")

        # Summary
        lines.append("")
        lines.append(f"Total Latency: {attempt.total_latency_ms:.0f}ms")
        if attempt.errors:
            lines.append(f"Errors: {len(attempt.errors)} (recovered gracefully)")

        lines.append(self.HORIZONTAL * self.width)

        return "\n".join(lines)

    def _format_tool_call(self, trace: ToolCallTrace, number: int, is_last: bool) -> List[str]:
        """Format a single tool call trace."""
        lines = []

        # LLM reasoning before tool call
        if trace.llm_reasoning:
            lines.append("  │")
            reasoning_lines = self._wrap_text(trace.llm_reasoning, self.width - 30)
            for line in reasoning_lines:
                lines.append(f"  │ LLM Reasoning: {line}")

        # Tool call header
        lines.append("  │")
        prefix = "  └─→" if is_last else "  ├─→"

        # Mark fallback calls
        fallback_marker = " [FALLBACK]" if trace.status == ToolStatus.FALLBACK else ""
        lines.append(f"{prefix} [{number}] {trace.tool_name}{fallback_marker}")

        # Parameters
        params_str = self._format_params(trace.params)
        lines.append(f"  │    └─ Params: {params_str}")

        # Latency
        latency_str = f"{trace.latency_ms:.0f}ms"
        if trace.status == ToolStatus.TIMEOUT:
            latency_str = "TIMEOUT"
        lines.append(f"  │    └─ Latency: {latency_str}")

        # Result or error
        if trace.status == ToolStatus.SUCCESS:
            result_preview = self._format_result(trace.result)
            lines.append(f"  │    └─ Result: {result_preview}")
            lines.append(f"  │    └─ Status: ✓ OK")
        elif trace.status == ToolStatus.TIMEOUT:
            lines.append(f"  │    └─ Result: None")
            lines.append(f"  │    └─ Status: ✗ ERROR (timeout)")
            if trace.recovery_action:
                lines.append(f"  │    └─ Recovery: {trace.recovery_action}")
        elif trace.status == ToolStatus.ERROR:
            lines.append(f"  │    └─ Result: None")
            lines.append(f"  │    └─ Status: ✗ ERROR ({trace.error})")
            if trace.recovery_action:
                lines.append(f"  │    └─ Recovery: {trace.recovery_action}")
        elif trace.status == ToolStatus.FALLBACK:
            result_preview = self._format_result(trace.result)
            lines.append(f"  │    └─ Result: {result_preview}")
            lines.append(f"  │    └─ Status: ⚠ FALLBACK (original tool failed)")

        return lines

    def visualize_consensus(
        self,
        question_result: QuestionResult,
        pass_5_result: PassKResult,
        pass_10_result: PassKResult
    ) -> str:
        """Visualize consensus analysis for all k attempts."""
        lines = []

        lines.append("")
        lines.append(self.DOUBLE_HORIZONTAL * self.width)
        lines.append("CONSENSUS ANALYSIS (10 attempts):")
        lines.append(self.DOUBLE_HORIZONTAL * self.width)

        # Show all answers
        answers = [att.final_answer for att in question_result.attempts]
        lines.append(f"Answers: {answers[:5]}")  # Show first 5
        if len(answers) > 5:
            lines.append(f"         {answers[5:]}")  # Show remaining

        lines.append("")

        # Majority answer
        lines.append(f"Majority Answer: \"{question_result.majority_answer}\" "
                    f"({question_result.consensus_strength:.0%} consensus)")
        lines.append(f"Ground Truth: \"{question_result.ground_truth}\"")
        lines.append("")

        # pass^k results
        pass_5_symbol = "✓" if pass_5_result.passed else "✗"
        pass_10_symbol = "✓" if pass_10_result.passed else "✗"

        lines.append(f"{pass_5_symbol} pass^5:  {'PASS' if pass_5_result.passed else 'FAIL'} "
                    f"(majority: \"{pass_5_result.majority_answer}\", "
                    f"{pass_5_result.consensus_strength:.0%} consensus)")
        lines.append(f"{pass_10_symbol} pass^10: {'PASS' if pass_10_result.passed else 'FAIL'} "
                    f"(majority: \"{pass_10_result.majority_answer}\", "
                    f"{pass_10_result.consensus_strength:.0%} consensus)")
        lines.append("")

        # Tool statistics
        lines.append("Tool Statistics:")
        for tool, count in question_result.tool_call_distribution.items():
            error_rate = question_result.tool_error_rates.get(tool, 0.0)
            error_str = f"{error_rate:.0%} error rate" if error_rate > 0 else "100% success"
            lines.append(f"  └─ {tool}: {count} calls, {error_str}")

        lines.append("")

        # Performance metrics
        consistency = "HIGH" if question_result.consensus_strength >= 0.8 else \
                     "MEDIUM" if question_result.consensus_strength >= 0.6 else "LOW"
        lines.append(f"Consistency: {consistency} ({question_result.consensus_strength:.0%} consensus)")
        lines.append(f"Avg Latency: {question_result.avg_latency_ms:.0f}ms")
        lines.append(f"Error Recovery: {question_result.error_recovery_rate:.0%} "
                    f"({question_result.error_recovery_rate * 100:.0f}% of errors recovered)")

        return "\n".join(lines)

    def visualize_question_summary(self, question_result: QuestionResult) -> str:
        """Visualize a complete question result summary."""
        lines = []

        lines.append("")
        lines.append(self.DOUBLE_HORIZONTAL * self.width)
        lines.append(f"Question: \"{question_result.question_text}\"")
        lines.append(self.DOUBLE_HORIZONTAL * self.width)

        # Category and basic info
        lines.append(f"Category: {question_result.category}")
        lines.append(f"Question ID: {question_result.question_id}")
        lines.append("")

        return "\n".join(lines)

    def _format_params(self, params: Dict) -> str:
        """Format parameters for display."""
        if not params:
            return "{}"

        items = []
        for key, value in params.items():
            if isinstance(value, str) and len(value) > 50:
                value = value[:47] + "..."
            items.append(f"{key}: \"{value}\"")

        return "{" + ", ".join(items) + "}"

    def _format_result(self, result) -> str:
        """Format result for display."""
        if result is None:
            return "None"

        result_str = str(result)
        if len(result_str) > 60:
            return result_str[:57] + "..."
        return result_str

    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            if current_length + len(word) + 1 <= max_width:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)

        if current_line:
            lines.append(" ".join(current_line))

        return lines if lines else [text[:max_width]]
