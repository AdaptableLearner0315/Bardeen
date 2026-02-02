"""Shared module for the B2B Account Intelligence Agent.

This module contains:
- Configuration management
- Pydantic data models
- Custom exceptions
- Utility functions
"""

from .config import (
    Config,
    LLMConfig,
    ToolConfig,
    ModeConfig,
    MemoryConfig,
    StorageConfig,
    EvaluationConfig,
    DashboardConfig,
    RateLimitConfig,
    ResearchMode,
    load_config,
    get_config,
    reset_config,
)

from .models import (
    # Enums
    ToolStatus,
    ToolMode,
    UserActionType,
    # Tool models
    ToolCall,
    ToolDefinition,
    # API models
    ChatRequest,
    ChatResponse,
    UserAction,
    HealthStatus,
    ErrorDetail,
    ErrorResponse,
    # Memory models
    ConversationMessage,
    ConversationSession,
    # Evaluation models
    AttemptResult,
    QuestionResult,
    EvaluationMetrics,
    EvaluationRun,
    EvaluationSummary,
    # Dataset models
    GroundTruth,
    ExpectedBehavior,
    EvaluationCriteria,
    DatasetQuestion,
    Dataset,
    # Export models
    ExportRequest,
    ExportResponse,
)

from .exceptions import (
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

from .utils import (
    # String
    normalize_text,
    normalize_answer,
    extract_numbers,
    truncate_text,
    sanitize_for_filename,
    # Numeric
    numbers_approximately_equal,
    format_number,
    safe_divide,
    # Time
    utc_now,
    format_timestamp,
    parse_timestamp,
    measure_time,
    Timer,
    # Hash
    generate_hash,
    generate_cache_key,
    # Collection
    chunk_list,
    flatten_dict,
    deep_get,
    merge_dicts,
    # Retry
    retry_with_backoff,
    async_retry_with_backoff,
    # Validation
    is_valid_url,
    is_valid_email,
    is_valid_uuid,
    # Fuzzy matching
    fuzzy_match,
    find_best_match,
)

__all__ = [
    # Config
    "Config",
    "LLMConfig",
    "ToolConfig",
    "ModeConfig",
    "MemoryConfig",
    "StorageConfig",
    "EvaluationConfig",
    "DashboardConfig",
    "RateLimitConfig",
    "ResearchMode",
    "load_config",
    "get_config",
    "reset_config",
    # Enums
    "ToolStatus",
    "ToolMode",
    "UserActionType",
    # Models
    "ToolCall",
    "ToolDefinition",
    "ChatRequest",
    "ChatResponse",
    "UserAction",
    "HealthStatus",
    "ErrorDetail",
    "ErrorResponse",
    "ConversationMessage",
    "ConversationSession",
    "AttemptResult",
    "QuestionResult",
    "EvaluationMetrics",
    "EvaluationRun",
    "EvaluationSummary",
    "GroundTruth",
    "ExpectedBehavior",
    "EvaluationCriteria",
    "DatasetQuestion",
    "Dataset",
    "ExportRequest",
    "ExportResponse",
    # Exceptions
    "AgentBaseException",
    "ConfigurationError",
    "MissingAPIKeyError",
    "ToolError",
    "ToolNotFoundError",
    "ToolExecutionError",
    "ToolTimeoutError",
    "ToolRateLimitError",
    "ToolValidationError",
    "ToolUnavailableError",
    "LLMError",
    "LLMAPIError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "LLMContextOverflowError",
    "LLMInvalidResponseError",
    "MemoryError",
    "SessionNotFoundError",
    "SessionExpiredError",
    "StorageError",
    "DatabaseConnectionError",
    "DatabaseWriteError",
    "CacheError",
    "EvaluationError",
    "DatasetLoadError",
    "EvaluationRunNotFoundError",
    "APIError",
    "ValidationError",
    "RateLimitExceededError",
    "ServiceUnavailableError",
    "ExportError",
    "ExportFormatError",
    "ExportGenerationError",
    # Utils
    "normalize_text",
    "normalize_answer",
    "extract_numbers",
    "truncate_text",
    "sanitize_for_filename",
    "numbers_approximately_equal",
    "format_number",
    "safe_divide",
    "utc_now",
    "format_timestamp",
    "parse_timestamp",
    "measure_time",
    "Timer",
    "generate_hash",
    "generate_cache_key",
    "chunk_list",
    "flatten_dict",
    "deep_get",
    "merge_dicts",
    "retry_with_backoff",
    "async_retry_with_backoff",
    "is_valid_url",
    "is_valid_email",
    "is_valid_uuid",
    "fuzzy_match",
    "find_best_match",
]
