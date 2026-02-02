"""Unit tests for shared/exceptions.py."""

import pytest

from src.shared.exceptions import (
    # Base
    AgentBaseException,
    # Config
    ConfigurationError,
    MissingAPIKeyError,
    # Tool
    ToolError,
    ToolNotFoundError,
    ToolExecutionError,
    ToolTimeoutError,
    ToolRateLimitError,
    ToolValidationError,
    ToolUnavailableError,
    # LLM
    LLMError,
    LLMAPIError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMContextOverflowError,
    LLMInvalidResponseError,
    # Memory
    MemoryError,
    SessionNotFoundError,
    SessionExpiredError,
    # Storage
    StorageError,
    DatabaseConnectionError,
    DatabaseWriteError,
    CacheError,
    # Evaluation
    EvaluationError,
    DatasetLoadError,
    EvaluationRunNotFoundError,
    # API
    APIError,
    ValidationError,
    RateLimitExceededError,
    ServiceUnavailableError,
    # Export
    ExportError,
    ExportFormatError,
    ExportGenerationError,
)


class TestAgentBaseException:
    """Tests for AgentBaseException."""

    def test_basic_exception(self):
        """Test basic exception creation."""
        exc = AgentBaseException("Test error")
        assert str(exc) == "Test error"
        assert exc.code == "AGENT_ERROR"
        assert exc.details == {}

    def test_exception_with_code(self):
        """Test exception with custom code."""
        exc = AgentBaseException("Error", code="CUSTOM_ERROR")
        assert exc.code == "CUSTOM_ERROR"

    def test_exception_with_details(self):
        """Test exception with details."""
        exc = AgentBaseException(
            "Error",
            details={"key": "value"}
        )
        assert exc.details == {"key": "value"}

    def test_to_dict(self):
        """Test to_dict conversion."""
        exc = AgentBaseException(
            "Test error",
            code="TEST",
            details={"info": "test"}
        )
        d = exc.to_dict()
        assert d["code"] == "TEST"
        assert d["message"] == "Test error"
        assert d["details"] == {"info": "test"}

    def test_exception_is_raisable(self):
        """Test exception can be raised and caught."""
        with pytest.raises(AgentBaseException) as exc_info:
            raise AgentBaseException("Test")
        assert exc_info.value.message == "Test"


class TestConfigurationErrors:
    """Tests for configuration errors."""

    def test_configuration_error(self):
        """Test ConfigurationError."""
        exc = ConfigurationError("Invalid config")
        assert exc.code == "CONFIG_ERROR"
        assert "Invalid config" in str(exc)

    def test_missing_api_key_error(self):
        """Test MissingAPIKeyError."""
        exc = MissingAPIKeyError("ANTHROPIC_API_KEY")
        assert exc.code == "MISSING_API_KEY"
        assert "ANTHROPIC_API_KEY" in str(exc)
        assert exc.details["key_name"] == "ANTHROPIC_API_KEY"


class TestToolErrors:
    """Tests for tool-related errors."""

    def test_tool_error_base(self):
        """Test ToolError base class."""
        exc = ToolError("Error", "web_search")
        assert exc.tool_name == "web_search"
        assert exc.details["tool_name"] == "web_search"

    def test_tool_not_found_error(self):
        """Test ToolNotFoundError."""
        exc = ToolNotFoundError("unknown_tool")
        assert exc.code == "TOOL_NOT_FOUND"
        assert "unknown_tool" in str(exc)

    def test_tool_execution_error(self):
        """Test ToolExecutionError."""
        exc = ToolExecutionError("calculator", "Division by zero")
        assert exc.code == "TOOL_EXECUTION_ERROR"
        assert "Division by zero" in str(exc)
        assert exc.tool_name == "calculator"

    def test_tool_timeout_error(self):
        """Test ToolTimeoutError."""
        exc = ToolTimeoutError("web_search", 10.0)
        assert exc.code == "TOOL_TIMEOUT"
        assert "10" in str(exc)
        assert exc.details["timeout_seconds"] == 10.0

    def test_tool_rate_limit_error(self):
        """Test ToolRateLimitError."""
        exc = ToolRateLimitError("github_api", retry_after_seconds=60)
        assert exc.code == "TOOL_RATE_LIMITED"
        assert exc.details["retry_after_seconds"] == 60

    def test_tool_rate_limit_no_retry_after(self):
        """Test ToolRateLimitError without retry_after."""
        exc = ToolRateLimitError("github_api")
        assert exc.code == "TOOL_RATE_LIMITED"
        assert "retry_after_seconds" not in exc.details

    def test_tool_validation_error(self):
        """Test ToolValidationError."""
        errors = {"query": "required", "limit": "must be positive"}
        exc = ToolValidationError("web_search", errors)
        assert exc.code == "TOOL_VALIDATION_ERROR"
        assert exc.details["validation_errors"] == errors

    def test_tool_unavailable_error(self):
        """Test ToolUnavailableError."""
        exc = ToolUnavailableError("yahoo_finance", "Not available in Normal mode")
        assert exc.code == "TOOL_UNAVAILABLE"
        assert "Not available in Normal mode" in str(exc)


class TestLLMErrors:
    """Tests for LLM-related errors."""

    def test_llm_api_error(self):
        """Test LLMAPIError."""
        exc = LLMAPIError("API request failed", status_code=500)
        assert exc.code == "LLM_API_ERROR"
        assert exc.details["status_code"] == 500

    def test_llm_api_error_no_status(self):
        """Test LLMAPIError without status code."""
        exc = LLMAPIError("API error")
        assert "status_code" not in exc.details

    def test_llm_rate_limit_error(self):
        """Test LLMRateLimitError."""
        exc = LLMRateLimitError(retry_after_seconds=30)
        assert exc.code == "LLM_RATE_LIMITED"
        assert exc.details["retry_after_seconds"] == 30

    def test_llm_timeout_error(self):
        """Test LLMTimeoutError."""
        exc = LLMTimeoutError(60.0)
        assert exc.code == "LLM_TIMEOUT"
        assert "60" in str(exc)

    def test_llm_context_overflow_error(self):
        """Test LLMContextOverflowError."""
        exc = LLMContextOverflowError(150000, 128000)
        assert exc.code == "LLM_CONTEXT_OVERFLOW"
        assert exc.details["token_count"] == 150000
        assert exc.details["max_tokens"] == 128000

    def test_llm_invalid_response_error(self):
        """Test LLMInvalidResponseError."""
        exc = LLMInvalidResponseError("Malformed JSON", raw_response='{"invalid":')
        assert exc.code == "LLM_INVALID_RESPONSE"
        assert "raw_response" in exc.details

    def test_llm_invalid_response_truncates(self):
        """Test raw response is truncated."""
        long_response = "x" * 1000
        exc = LLMInvalidResponseError("Error", raw_response=long_response)
        assert len(exc.details["raw_response"]) == 500


class TestMemoryErrors:
    """Tests for memory-related errors."""

    def test_session_not_found_error(self):
        """Test SessionNotFoundError."""
        exc = SessionNotFoundError("session-123")
        assert exc.code == "SESSION_NOT_FOUND"
        assert exc.details["session_id"] == "session-123"

    def test_session_expired_error(self):
        """Test SessionExpiredError."""
        exc = SessionExpiredError("session-456")
        assert exc.code == "SESSION_EXPIRED"
        assert exc.details["session_id"] == "session-456"


class TestStorageErrors:
    """Tests for storage-related errors."""

    def test_database_connection_error(self):
        """Test DatabaseConnectionError."""
        exc = DatabaseConnectionError("Cannot connect to SQLite")
        assert exc.code == "DATABASE_CONNECTION_ERROR"

    def test_database_write_error(self):
        """Test DatabaseWriteError."""
        exc = DatabaseWriteError("Write failed", table="conversations")
        assert exc.code == "DATABASE_WRITE_ERROR"
        assert exc.details["table"] == "conversations"

    def test_cache_error(self):
        """Test CacheError."""
        exc = CacheError("Cache full", operation="set")
        assert exc.code == "CACHE_ERROR"
        assert exc.details["operation"] == "set"


class TestEvaluationErrors:
    """Tests for evaluation-related errors."""

    def test_dataset_load_error(self):
        """Test DatasetLoadError."""
        exc = DatasetLoadError("File not found", path="/data/dataset.json")
        assert exc.code == "DATASET_LOAD_ERROR"
        assert exc.details["path"] == "/data/dataset.json"

    def test_evaluation_run_not_found_error(self):
        """Test EvaluationRunNotFoundError."""
        exc = EvaluationRunNotFoundError("run-123")
        assert exc.code == "EVALUATION_RUN_NOT_FOUND"
        assert exc.details["run_id"] == "run-123"


class TestAPIErrors:
    """Tests for API-related errors."""

    def test_api_error_has_status_code(self):
        """Test APIError has status code."""
        exc = APIError("Error", status_code=400)
        assert exc.status_code == 400

    def test_validation_error(self):
        """Test ValidationError."""
        errors = {"field": "required"}
        exc = ValidationError("Validation failed", errors=errors)
        assert exc.code == "VALIDATION_ERROR"
        assert exc.status_code == 422
        assert exc.details["errors"] == errors

    def test_rate_limit_exceeded_error(self):
        """Test RateLimitExceededError."""
        exc = RateLimitExceededError(retry_after_seconds=60)
        assert exc.code == "RATE_LIMIT_EXCEEDED"
        assert exc.status_code == 429

    def test_service_unavailable_error(self):
        """Test ServiceUnavailableError."""
        exc = ServiceUnavailableError()
        assert exc.code == "SERVICE_UNAVAILABLE"
        assert exc.status_code == 503


class TestExportErrors:
    """Tests for export-related errors."""

    def test_export_format_error(self):
        """Test ExportFormatError."""
        exc = ExportFormatError("xlsx", ["csv", "pdf"])
        assert exc.code == "EXPORT_FORMAT_ERROR"
        assert exc.details["format"] == "xlsx"
        assert exc.details["supported_formats"] == ["csv", "pdf"]

    def test_export_generation_error(self):
        """Test ExportGenerationError."""
        exc = ExportGenerationError("PDF generation failed", "pdf")
        assert exc.code == "EXPORT_GENERATION_ERROR"
        assert exc.details["format"] == "pdf"


class TestExceptionInheritance:
    """Tests for exception inheritance."""

    def test_all_exceptions_inherit_from_base(self):
        """Test all exceptions inherit from AgentBaseException."""
        exceptions = [
            ConfigurationError("test"),
            ToolError("test", "tool"),
            LLMError("test"),
            MemoryError("test"),
            StorageError("test"),
            EvaluationError("test"),
            APIError("test"),
            ExportError("test"),
        ]
        for exc in exceptions:
            assert isinstance(exc, AgentBaseException)

    def test_specific_exceptions_inherit_correctly(self):
        """Test specific exceptions inherit from category base."""
        assert isinstance(ToolNotFoundError("t"), ToolError)
        assert isinstance(LLMAPIError("e"), LLMError)
        assert isinstance(SessionNotFoundError("s"), MemoryError)
        assert isinstance(DatabaseConnectionError("d"), StorageError)
        assert isinstance(DatasetLoadError("d"), EvaluationError)
        assert isinstance(ValidationError("v"), APIError)
        assert isinstance(ExportFormatError("f", []), ExportError)
