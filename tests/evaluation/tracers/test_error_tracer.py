"""Tests for error tracer module."""

import pytest

from src.evaluation.tracers.error_tracer import ErrorTracer
from src.shared.models import ErrorTrace


class TestErrorTracer:
    """Tests for ErrorTracer class."""

    def test_initialization(self):
        """Test basic initialization."""
        tracer = ErrorTracer()
        assert tracer.errors == []

    def test_record_error(self):
        """Test recording an error."""
        tracer = ErrorTracer()

        error = tracer.record_error(
            tool_name="web_search",
            error_type="timeout",
            error_message="Request timed out after 30 seconds",
            attempted_params={"query": "test"},
            recovery_action="retry_with_backoff",
            recovery_success=True
        )

        assert isinstance(error, ErrorTrace)
        assert error.tool_name == "web_search"
        assert error.error_type == "timeout"
        assert error.error_message == "Request timed out after 30 seconds"
        assert error.attempted_params == {"query": "test"}
        assert error.recovery_action == "retry_with_backoff"
        assert error.recovery_success is True
        assert error.timestamp is not None

    def test_record_error_adds_to_list(self):
        """Test that recorded errors are added to the list."""
        tracer = ErrorTracer()

        tracer.record_error(
            tool_name="tool1",
            error_type="error1",
            error_message="msg1",
            attempted_params={},
            recovery_action="action1",
            recovery_success=True
        )
        tracer.record_error(
            tool_name="tool2",
            error_type="error2",
            error_message="msg2",
            attempted_params={},
            recovery_action="action2",
            recovery_success=False
        )

        assert len(tracer.errors) == 2
        assert tracer.errors[0].tool_name == "tool1"
        assert tracer.errors[1].tool_name == "tool2"

    def test_get_errors(self):
        """Test getting all errors."""
        tracer = ErrorTracer()

        tracer.record_error(
            tool_name="tool",
            error_type="error",
            error_message="msg",
            attempted_params={},
            recovery_action="action",
            recovery_success=True
        )

        errors = tracer.get_errors()
        assert len(errors) == 1
        assert errors is tracer.errors

    def test_get_error_count(self):
        """Test getting error count."""
        tracer = ErrorTracer()

        assert tracer.get_error_count() == 0

        for i in range(5):
            tracer.record_error(
                tool_name=f"tool{i}",
                error_type="error",
                error_message="msg",
                attempted_params={},
                recovery_action="action",
                recovery_success=True
            )

        assert tracer.get_error_count() == 5

    def test_get_recovery_rate_no_errors(self):
        """Test recovery rate with no errors."""
        tracer = ErrorTracer()
        # No errors = perfect recovery rate
        assert tracer.get_recovery_rate() == 1.0

    def test_get_recovery_rate_all_recovered(self):
        """Test recovery rate when all errors recovered."""
        tracer = ErrorTracer()

        for i in range(5):
            tracer.record_error(
                tool_name="tool",
                error_type="error",
                error_message="msg",
                attempted_params={},
                recovery_action="action",
                recovery_success=True
            )

        assert tracer.get_recovery_rate() == 1.0

    def test_get_recovery_rate_none_recovered(self):
        """Test recovery rate when no errors recovered."""
        tracer = ErrorTracer()

        for i in range(5):
            tracer.record_error(
                tool_name="tool",
                error_type="error",
                error_message="msg",
                attempted_params={},
                recovery_action="action",
                recovery_success=False
            )

        assert tracer.get_recovery_rate() == 0.0

    def test_get_recovery_rate_partial(self):
        """Test recovery rate with partial recovery."""
        tracer = ErrorTracer()

        # 3 recovered
        for _ in range(3):
            tracer.record_error(
                tool_name="tool",
                error_type="error",
                error_message="msg",
                attempted_params={},
                recovery_action="action",
                recovery_success=True
            )

        # 2 not recovered
        for _ in range(2):
            tracer.record_error(
                tool_name="tool",
                error_type="error",
                error_message="msg",
                attempted_params={},
                recovery_action="action",
                recovery_success=False
            )

        assert tracer.get_recovery_rate() == 0.6  # 3/5

    def test_get_errors_by_tool(self):
        """Test grouping errors by tool."""
        tracer = ErrorTracer()

        # 2 web_search errors
        for _ in range(2):
            tracer.record_error(
                tool_name="web_search",
                error_type="timeout",
                error_message="msg",
                attempted_params={},
                recovery_action="retry",
                recovery_success=True
            )

        # 3 calculator errors
        for _ in range(3):
            tracer.record_error(
                tool_name="calculator",
                error_type="invalid_input",
                error_message="msg",
                attempted_params={},
                recovery_action="inform_user",
                recovery_success=False
            )

        # 1 wikipedia error
        tracer.record_error(
            tool_name="wikipedia",
            error_type="not_found",
            error_message="msg",
            attempted_params={},
            recovery_action="try_different_query",
            recovery_success=True
        )

        by_tool = tracer.get_errors_by_tool()

        assert len(by_tool["web_search"]) == 2
        assert len(by_tool["calculator"]) == 3
        assert len(by_tool["wikipedia"]) == 1

    def test_get_errors_by_type(self):
        """Test grouping errors by type."""
        tracer = ErrorTracer()

        # 3 timeout errors
        for _ in range(3):
            tracer.record_error(
                tool_name="web_search",
                error_type="timeout",
                error_message="msg",
                attempted_params={},
                recovery_action="retry",
                recovery_success=True
            )

        # 2 rate_limit errors
        for _ in range(2):
            tracer.record_error(
                tool_name="api",
                error_type="rate_limit",
                error_message="msg",
                attempted_params={},
                recovery_action="wait",
                recovery_success=True
            )

        by_type = tracer.get_errors_by_type()

        assert len(by_type["timeout"]) == 3
        assert len(by_type["rate_limit"]) == 2

    def test_get_most_common_errors(self):
        """Test getting most common errors."""
        tracer = ErrorTracer()

        # 5 web_search:timeout
        for _ in range(5):
            tracer.record_error(
                tool_name="web_search",
                error_type="timeout",
                error_message="msg",
                attempted_params={},
                recovery_action="retry",
                recovery_success=True
            )

        # 3 calculator:invalid_input
        for _ in range(3):
            tracer.record_error(
                tool_name="calculator",
                error_type="invalid_input",
                error_message="msg",
                attempted_params={},
                recovery_action="inform",
                recovery_success=False
            )

        # 1 wikipedia:not_found
        tracer.record_error(
            tool_name="wikipedia",
            error_type="not_found",
            error_message="msg",
            attempted_params={},
            recovery_action="try_different",
            recovery_success=True
        )

        most_common = tracer.get_most_common_errors(top_n=3)

        assert len(most_common) == 3
        assert most_common[0] == ("web_search:timeout", 5)
        assert most_common[1] == ("calculator:invalid_input", 3)
        assert most_common[2] == ("wikipedia:not_found", 1)

    def test_get_most_common_errors_top_n_limit(self):
        """Test top_n limit for most common errors."""
        tracer = ErrorTracer()

        # Create 10 different error types
        for i in range(10):
            for j in range(10 - i):
                tracer.record_error(
                    tool_name=f"tool{i}",
                    error_type=f"error{i}",
                    error_message="msg",
                    attempted_params={},
                    recovery_action="action",
                    recovery_success=True
                )

        most_common = tracer.get_most_common_errors(top_n=5)
        assert len(most_common) == 5

    def test_has_errors_false(self):
        """Test has_errors when no errors."""
        tracer = ErrorTracer()
        assert tracer.has_errors() is False

    def test_has_errors_true(self):
        """Test has_errors when errors exist."""
        tracer = ErrorTracer()

        tracer.record_error(
            tool_name="tool",
            error_type="error",
            error_message="msg",
            attempted_params={},
            recovery_action="action",
            recovery_success=True
        )

        assert tracer.has_errors() is True


class TestErrorTracerEdgeCases:
    """Tests for edge cases in ErrorTracer."""

    def test_record_error_with_complex_params(self):
        """Test recording error with complex params."""
        tracer = ErrorTracer()

        complex_params = {
            "query": "test query",
            "options": {
                "limit": 10,
                "filters": ["a", "b", "c"]
            },
            "nested": {
                "level1": {
                    "level2": "deep value"
                }
            }
        }

        error = tracer.record_error(
            tool_name="tool",
            error_type="error",
            error_message="msg",
            attempted_params=complex_params,
            recovery_action="action",
            recovery_success=True
        )

        assert error.attempted_params == complex_params

    def test_record_error_with_empty_params(self):
        """Test recording error with empty params."""
        tracer = ErrorTracer()

        error = tracer.record_error(
            tool_name="tool",
            error_type="error",
            error_message="msg",
            attempted_params={},
            recovery_action="action",
            recovery_success=True
        )

        assert error.attempted_params == {}

    def test_record_error_with_long_message(self):
        """Test recording error with long message."""
        tracer = ErrorTracer()

        long_message = "Error: " + "x" * 1000

        error = tracer.record_error(
            tool_name="tool",
            error_type="error",
            error_message=long_message,
            attempted_params={},
            recovery_action="action",
            recovery_success=True
        )

        assert error.error_message == long_message

    def test_record_error_timestamp_format(self):
        """Test that timestamp is in ISO format."""
        tracer = ErrorTracer()

        error = tracer.record_error(
            tool_name="tool",
            error_type="error",
            error_message="msg",
            attempted_params={},
            recovery_action="action",
            recovery_success=True
        )

        # Should be parseable as ISO format
        from datetime import datetime
        datetime.fromisoformat(error.timestamp)  # Should not raise
