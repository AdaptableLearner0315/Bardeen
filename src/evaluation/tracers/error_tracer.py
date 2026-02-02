"""Error tracer for tracking failures and recovery actions."""

from datetime import datetime
from typing import Dict, Any, List, Optional

from ...shared.models import ErrorTrace


class ErrorTracer:
    """Tracks errors and recovery attempts during tool execution."""

    def __init__(self):
        self.errors: List[ErrorTrace] = []

    def record_error(
        self,
        tool_name: str,
        error_type: str,
        error_message: str,
        attempted_params: Dict[str, Any],
        recovery_action: str,
        recovery_success: bool
    ) -> ErrorTrace:
        """Record an error and its recovery attempt."""
        error_trace = ErrorTrace(
            tool_name=tool_name,
            error_type=error_type,
            error_message=error_message,
            attempted_params=attempted_params,
            recovery_action=recovery_action,
            recovery_success=recovery_success,
            timestamp=datetime.now().isoformat()
        )
        self.errors.append(error_trace)
        return error_trace

    def get_errors(self) -> List[ErrorTrace]:
        """Get all recorded errors."""
        return self.errors

    def get_error_count(self) -> int:
        """Get total number of errors."""
        return len(self.errors)

    def get_recovery_rate(self) -> float:
        """Calculate the rate of successful error recoveries."""
        if not self.errors:
            return 1.0  # No errors = perfect recovery rate
        successful = sum(1 for e in self.errors if e.recovery_success)
        return successful / len(self.errors)

    def get_errors_by_tool(self) -> Dict[str, List[ErrorTrace]]:
        """Group errors by tool name."""
        errors_by_tool: Dict[str, List[ErrorTrace]] = {}
        for error in self.errors:
            if error.tool_name not in errors_by_tool:
                errors_by_tool[error.tool_name] = []
            errors_by_tool[error.tool_name].append(error)
        return errors_by_tool

    def get_errors_by_type(self) -> Dict[str, List[ErrorTrace]]:
        """Group errors by error type."""
        errors_by_type: Dict[str, List[ErrorTrace]] = {}
        for error in self.errors:
            if error.error_type not in errors_by_type:
                errors_by_type[error.error_type] = []
            errors_by_type[error.error_type].append(error)
        return errors_by_type

    def get_most_common_errors(self, top_n: int = 5) -> List[tuple]:
        """
        Get the most common error types.

        Returns:
            List of (error_type, count) tuples, sorted by count descending.
        """
        error_counts: Dict[str, int] = {}
        for error in self.errors:
            error_type = f"{error.tool_name}:{error.error_type}"
            error_counts[error_type] = error_counts.get(error_type, 0) + 1

        sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_errors[:top_n]

    def has_errors(self) -> bool:
        """Check if any errors were recorded."""
        return len(self.errors) > 0
