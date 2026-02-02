"""Custom exceptions for the B2B Account Intelligence Agent."""

from typing import Optional, Dict, Any


class AgentBaseException(Exception):
    """Base exception for all agent errors."""

    def __init__(
        self,
        message: str,
        code: str = "AGENT_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details
        }


# =============================================================================
# Configuration Errors
# =============================================================================

class ConfigurationError(AgentBaseException):
    """Error in configuration."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CONFIG_ERROR", details)


class MissingAPIKeyError(ConfigurationError):
    """Missing required API key."""

    def __init__(self, key_name: str):
        super().__init__(
            f"Missing required API key: {key_name}",
            {"key_name": key_name}
        )
        self.code = "MISSING_API_KEY"


# =============================================================================
# Tool Errors
# =============================================================================

class ToolError(AgentBaseException):
    """Base error for tool-related issues."""

    def __init__(
        self,
        message: str,
        tool_name: str,
        code: str = "TOOL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details["tool_name"] = tool_name
        self.tool_name = tool_name
        super().__init__(message, code, details)


class ToolNotFoundError(ToolError):
    """Tool not found in registry."""

    def __init__(self, tool_name: str):
        super().__init__(
            f"Tool not found: {tool_name}",
            tool_name,
            "TOOL_NOT_FOUND"
        )


class ToolExecutionError(ToolError):
    """Error during tool execution."""

    def __init__(
        self,
        tool_name: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            f"Tool execution failed: {message}",
            tool_name,
            "TOOL_EXECUTION_ERROR",
            details
        )


class ToolTimeoutError(ToolError):
    """Tool execution timed out."""

    def __init__(self, tool_name: str, timeout_seconds: float):
        super().__init__(
            f"Tool timed out after {timeout_seconds}s",
            tool_name,
            "TOOL_TIMEOUT",
            {"timeout_seconds": timeout_seconds}
        )


class ToolRateLimitError(ToolError):
    """Tool rate limit exceeded."""

    def __init__(self, tool_name: str, retry_after_seconds: Optional[float] = None):
        details = {}
        if retry_after_seconds:
            details["retry_after_seconds"] = retry_after_seconds
        super().__init__(
            f"Rate limit exceeded for tool: {tool_name}",
            tool_name,
            "TOOL_RATE_LIMITED",
            details
        )


class ToolValidationError(ToolError):
    """Invalid tool parameters."""

    def __init__(self, tool_name: str, validation_errors: Dict[str, str]):
        super().__init__(
            f"Invalid parameters for tool: {tool_name}",
            tool_name,
            "TOOL_VALIDATION_ERROR",
            {"validation_errors": validation_errors}
        )


class ToolUnavailableError(ToolError):
    """Tool is unavailable (e.g., mode restriction)."""

    def __init__(self, tool_name: str, reason: str):
        super().__init__(
            f"Tool unavailable: {reason}",
            tool_name,
            "TOOL_UNAVAILABLE",
            {"reason": reason}
        )


# =============================================================================
# LLM Errors
# =============================================================================

class LLMError(AgentBaseException):
    """Base error for LLM-related issues."""

    def __init__(
        self,
        message: str,
        code: str = "LLM_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, details)


class LLMAPIError(LLMError):
    """Error from LLM API."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if status_code:
            details["status_code"] = status_code
        super().__init__(message, "LLM_API_ERROR", details)


class LLMRateLimitError(LLMError):
    """LLM API rate limit exceeded."""

    def __init__(self, retry_after_seconds: Optional[float] = None):
        details = {}
        if retry_after_seconds:
            details["retry_after_seconds"] = retry_after_seconds
        super().__init__(
            "LLM API rate limit exceeded",
            "LLM_RATE_LIMITED",
            details
        )


class LLMTimeoutError(LLMError):
    """LLM API request timed out."""

    def __init__(self, timeout_seconds: float):
        super().__init__(
            f"LLM API request timed out after {timeout_seconds}s",
            "LLM_TIMEOUT",
            {"timeout_seconds": timeout_seconds}
        )


class LLMContextOverflowError(LLMError):
    """Context window exceeded."""

    def __init__(self, token_count: int, max_tokens: int):
        super().__init__(
            f"Context window exceeded: {token_count} > {max_tokens}",
            "LLM_CONTEXT_OVERFLOW",
            {"token_count": token_count, "max_tokens": max_tokens}
        )


class LLMInvalidResponseError(LLMError):
    """Invalid response from LLM."""

    def __init__(self, message: str, raw_response: Optional[str] = None):
        details = {}
        if raw_response:
            details["raw_response"] = raw_response[:500]  # Truncate
        super().__init__(message, "LLM_INVALID_RESPONSE", details)


# =============================================================================
# Memory Errors
# =============================================================================

class MemoryError(AgentBaseException):
    """Base error for memory-related issues."""

    def __init__(
        self,
        message: str,
        code: str = "MEMORY_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, details)


class SessionNotFoundError(MemoryError):
    """Session not found."""

    def __init__(self, session_id: str):
        super().__init__(
            f"Session not found: {session_id}",
            "SESSION_NOT_FOUND",
            {"session_id": session_id}
        )


class SessionExpiredError(MemoryError):
    """Session has expired."""

    def __init__(self, session_id: str):
        super().__init__(
            f"Session expired: {session_id}",
            "SESSION_EXPIRED",
            {"session_id": session_id}
        )


# =============================================================================
# Storage Errors
# =============================================================================

class StorageError(AgentBaseException):
    """Base error for storage-related issues."""

    def __init__(
        self,
        message: str,
        code: str = "STORAGE_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, details)


class DatabaseConnectionError(StorageError):
    """Failed to connect to database."""

    def __init__(self, message: str):
        super().__init__(message, "DATABASE_CONNECTION_ERROR")


class DatabaseWriteError(StorageError):
    """Failed to write to database."""

    def __init__(self, message: str, table: Optional[str] = None):
        details = {}
        if table:
            details["table"] = table
        super().__init__(message, "DATABASE_WRITE_ERROR", details)


class CacheError(StorageError):
    """Error with cache operations."""

    def __init__(self, message: str, operation: Optional[str] = None):
        details = {}
        if operation:
            details["operation"] = operation
        super().__init__(message, "CACHE_ERROR", details)


# =============================================================================
# Evaluation Errors
# =============================================================================

class EvaluationError(AgentBaseException):
    """Base error for evaluation-related issues."""

    def __init__(
        self,
        message: str,
        code: str = "EVALUATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, details)


class DatasetLoadError(EvaluationError):
    """Failed to load evaluation dataset."""

    def __init__(self, message: str, path: Optional[str] = None):
        details = {}
        if path:
            details["path"] = path
        super().__init__(message, "DATASET_LOAD_ERROR", details)


class EvaluationRunNotFoundError(EvaluationError):
    """Evaluation run not found."""

    def __init__(self, run_id: str):
        super().__init__(
            f"Evaluation run not found: {run_id}",
            "EVALUATION_RUN_NOT_FOUND",
            {"run_id": run_id}
        )


# =============================================================================
# API Errors
# =============================================================================

class APIError(AgentBaseException):
    """Base error for API-related issues."""

    def __init__(
        self,
        message: str,
        code: str = "API_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.status_code = status_code
        super().__init__(message, code, details)


class ValidationError(APIError):
    """Request validation failed."""

    def __init__(self, message: str, errors: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            "VALIDATION_ERROR",
            422,
            {"errors": errors} if errors else None
        )


class RateLimitExceededError(APIError):
    """API rate limit exceeded."""

    def __init__(self, retry_after_seconds: Optional[float] = None):
        details = {}
        if retry_after_seconds:
            details["retry_after_seconds"] = retry_after_seconds
        super().__init__(
            "Rate limit exceeded",
            "RATE_LIMIT_EXCEEDED",
            429,
            details
        )


class ServiceUnavailableError(APIError):
    """Service temporarily unavailable."""

    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(message, "SERVICE_UNAVAILABLE", 503)


# =============================================================================
# Export Errors
# =============================================================================

class ExportError(AgentBaseException):
    """Base error for export-related issues."""

    def __init__(
        self,
        message: str,
        code: str = "EXPORT_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, details)


class ExportFormatError(ExportError):
    """Unsupported export format."""

    def __init__(self, format: str, supported_formats: list):
        super().__init__(
            f"Unsupported export format: {format}",
            "EXPORT_FORMAT_ERROR",
            {"format": format, "supported_formats": supported_formats}
        )


class ExportGenerationError(ExportError):
    """Failed to generate export."""

    def __init__(self, message: str, format: str):
        super().__init__(
            message,
            "EXPORT_GENERATION_ERROR",
            {"format": format}
        )
