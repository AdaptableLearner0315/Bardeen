"""Shared data models for the B2B Account Intelligence Agent.

Uses Pydantic for validation and serialization.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from enum import Enum
import uuid


# =============================================================================
# Enums
# =============================================================================

class ToolStatus(str, Enum):
    """Status of a tool call execution."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    INVALID_PARAMS = "invalid_params"
    FALLBACK = "fallback"
    RATE_LIMITED = "rate_limited"
    EMPTY_RESULT = "empty_result"


class ToolMode(str, Enum):
    """Tool availability mode."""
    CORE = "core"          # Available in Normal mode
    EXTENDED = "extended"  # Only available in Deep mode


class UserActionType(str, Enum):
    """Types of user actions that can be requested."""
    SEARCH_MORE = "search_more"
    AUTHENTICATE = "authenticate"
    CLARIFY = "clarify"
    END_SEARCH = "end_search"


# =============================================================================
# Tool Models
# =============================================================================

class ToolCall(BaseModel):
    """A single tool call with input, output, and metadata."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    status: ToolStatus = ToolStatus.SUCCESS
    error_message: Optional[str] = None
    latency_ms: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    retry_count: int = 0
    fallback_used: Optional[str] = None

    class Config:
        use_enum_values = True


class ToolDefinition(BaseModel):
    """Definition of a tool for LLM tool calling."""
    name: str
    description: str
    mode: ToolMode = ToolMode.CORE
    parameters: Dict[str, Any]  # JSON Schema
    fallback_tool: Optional[str] = None

    class Config:
        use_enum_values = True


# =============================================================================
# API Request/Response Models
# =============================================================================

class ChatRequest(BaseModel):
    """Request to chat endpoint."""
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    mode: Literal["normal", "deep"] = "normal"
    stream: bool = False

    @field_validator('message')
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Message cannot be empty or whitespace only')
        return v.strip()


class UserAction(BaseModel):
    """Action requested from user."""
    type: UserActionType
    message: str
    options: Optional[List[str]] = None

    class Config:
        use_enum_values = True


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    response: str
    session_id: str
    tool_calls: List[ToolCall] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    disclaimer: Optional[str] = None
    user_action_required: Optional[UserAction] = None
    latency_ms: int = 0
    mode_used: Literal["normal", "deep"] = "normal"


class HealthStatus(BaseModel):
    """System health status."""
    status: Literal["healthy", "degraded", "unhealthy"]
    components: Dict[str, str]  # component_name -> "ok" | "error"
    available_tools: List[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Memory Models
# =============================================================================

class ConversationMessage(BaseModel):
    """A message in conversation history."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tool_calls: Optional[List[ToolCall]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationSession(BaseModel):
    """A conversation session with history."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[ConversationMessage] = Field(default_factory=list)
    mode: Literal["normal", "deep"] = "normal"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_message(self, role: str, content: str, **kwargs) -> ConversationMessage:
        """Add a message to the conversation."""
        msg = ConversationMessage(role=role, content=content, **kwargs)
        self.messages.append(msg)
        self.updated_at = datetime.utcnow()
        return msg


# =============================================================================
# Evaluation Trace Models
# =============================================================================

class ToolCallTrace(BaseModel):
    """Trace of a single tool call during evaluation."""
    call_id: str
    attempt_number: int
    tool_name: str
    params: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    status: ToolStatus = ToolStatus.SUCCESS
    latency_ms: float = 0.0
    timestamp: str
    llm_reasoning: Optional[str] = None
    recovery_action: Optional[str] = None

    class Config:
        use_enum_values = True


class ErrorTrace(BaseModel):
    """Trace of an error during evaluation."""
    tool_name: str
    error_type: str
    error_message: str
    attempted_params: Dict[str, Any]
    recovery_action: str
    recovery_success: bool
    timestamp: str


# =============================================================================
# Evaluation Models
# =============================================================================

class AttemptResult(BaseModel):
    """Result of a single attempt to answer a question."""
    attempt_number: int
    question_id: str = ""  # Optional for backward compatibility
    answer: str = ""  # Backward compatibility alias
    final_answer: str = ""  # New field name
    tool_calls: List[Any] = Field(default_factory=list)  # Accept both ToolCall and ToolCallTrace
    errors: List[Any] = Field(default_factory=list)  # Accept both old and new format
    latency_ms: int = 0  # Backward compatibility
    total_latency_ms: float = 0.0
    is_correct: bool = False
    semantic_similarity: float = 0.0
    error: Optional[str] = None  # Backward compatibility
    timestamp: Any = Field(default_factory=datetime.utcnow)  # Accept both


class QuestionResult(BaseModel):
    """Results for a single evaluation question."""
    question_id: str
    question_text: str
    category: str
    ground_truth: str
    expected_tools: List[str] = Field(default_factory=list)

    # Attempt results
    attempts: List[AttemptResult] = Field(default_factory=list)

    # Consensus - support both old and new field names
    consensus_answer: Optional[str] = None  # Backward compatibility
    majority_answer: Optional[str] = None
    consensus_strength: float = 0.0  # % agreeing on majority answer

    # pass^k results
    pass_5: bool = False
    pass_10: bool = False

    # Tool metrics
    total_tool_calls: int = 0
    tool_call_distribution: Dict[str, int] = Field(default_factory=dict)
    tool_error_rates: Dict[str, float] = Field(default_factory=dict)
    avg_tools_per_attempt: float = 0.0
    tool_efficiency: float = 0.0  # optimal_calls / actual_calls
    tool_success_rate: float = 0.0  # successful_calls / total_calls

    # Error metrics
    error_recovery_rate: float = 1.0

    # Aggregates
    avg_latency_ms: float = 0.0
    timestamp: Any = ""


class EvaluationMetrics(BaseModel):
    """Aggregate metrics for an evaluation run."""
    pass_5: float = 0.0  # % of questions passing pass^5
    pass_10: float = 0.0  # % of questions passing pass^10
    tool_efficiency: float = 0.0  # Average tool efficiency
    tool_success_rate: float = 0.0  # Average tool success rate
    avg_latency_ms: float = 0.0
    total_tool_calls: int = 0
    total_errors: int = 0


class EvaluationRun(BaseModel):
    """Complete evaluation run."""
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: Any = Field(default_factory=datetime.utcnow)  # Accepts both str and datetime
    status: Literal["running", "completed", "failed"] = "running"

    # Configuration
    total_questions: int = 0  # Alias for dataset_size (backward compat)
    dataset_size: int = 0
    k_attempts: int = 10
    temperature: float = 0.6
    config: Dict[str, Any] = Field(default_factory=dict)
    questions_completed: int = 0

    # Results
    question_results: List[QuestionResult] = Field(default_factory=list)
    metrics: Optional["EvaluationMetrics"] = None  # Backward compatibility

    # Aggregate metrics
    overall_pass_5: float = 0.0
    overall_pass_10: float = 0.0
    avg_consensus_strength: float = 0.0
    avg_tool_accuracy: float = 0.0
    avg_latency_ms: float = 0.0
    overall_error_rate: float = 0.0
    error_recovery_rate: float = 1.0

    # Category breakdown
    category_metrics: Dict[str, Any] = Field(default_factory=dict)

    @property
    def id(self) -> str:
        """Backward compatibility alias for run_id."""
        return self.run_id


class EvaluationSummary(BaseModel):
    """Summary of an evaluation run for listing."""
    id: str
    timestamp: datetime
    status: str
    total_questions: int
    questions_completed: int
    metrics: EvaluationMetrics


# =============================================================================
# Dataset Models
# =============================================================================

class GroundTruth(BaseModel):
    """Ground truth for a question."""
    answer: str
    answer_variants: List[str] = Field(default_factory=list)
    facts: Dict[str, Any] = Field(default_factory=dict)
    tolerance_percent: Optional[float] = None  # For numeric answers


class ExpectedBehavior(BaseModel):
    """Expected tool behavior for a question."""
    tools: List[str]
    tool_order: Literal["any", "sequential"] = "any"
    min_tools: int = 1
    max_tools: int = 10


class EvaluationCriteria(BaseModel):
    """Evaluation criteria for a question."""
    correctness_threshold: float = 0.85
    must_cite_sources: bool = False
    allows_approximation: bool = True


class DatasetQuestion(BaseModel):
    """A question in the evaluation dataset."""
    id: str
    question: str
    category: str
    difficulty: str = "medium"
    expected_behavior: Any = Field(default_factory=dict)  # Accept both dict and ExpectedBehavior
    ground_truth: Any = Field(default_factory=dict)  # Accept both dict and GroundTruth
    evaluation: Any = Field(default_factory=dict)  # Accept both dict and EvaluationCriteria


class Dataset(BaseModel):
    """Evaluation dataset."""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    questions: List[DatasetQuestion] = Field(default_factory=list)

    def get_by_category(self, category: str) -> List[DatasetQuestion]:
        """Get questions by category."""
        return [q for q in self.questions if q.category == category]

    def get_categories(self) -> List[str]:
        """Get unique categories."""
        return list(set(q.category for q in self.questions))


# =============================================================================
# Export Models
# =============================================================================

class ExportRequest(BaseModel):
    """Request to export evaluation results."""
    format: Literal["csv", "pdf"] = "csv"
    evaluation_id: Optional[str] = None
    category: Optional[str] = None
    include_traces: bool = True


class ExportResponse(BaseModel):
    """Response with export file info."""
    filename: str
    format: str
    size_bytes: int
    download_url: str


# =============================================================================
# Error Models
# =============================================================================

class ErrorDetail(BaseModel):
    """Detailed error information."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """API error response."""
    error: ErrorDetail
