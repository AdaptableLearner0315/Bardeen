"""Unit tests for shared/models.py."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.shared.models import (
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
    # Memory models
    ConversationMessage,
    ConversationSession,
    # Evaluation models
    AttemptResult,
    QuestionResult,
    EvaluationMetrics,
    EvaluationRun,
    # Dataset models
    GroundTruth,
    ExpectedBehavior,
    DatasetQuestion,
    Dataset,
    # Export models
    ExportRequest,
    ExportResponse,
    # Error models
    ErrorDetail,
    ErrorResponse,
)


class TestToolStatus:
    """Tests for ToolStatus enum."""

    def test_all_statuses_defined(self):
        """Test all expected statuses are defined."""
        assert ToolStatus.SUCCESS.value == "success"
        assert ToolStatus.ERROR.value == "error"
        assert ToolStatus.TIMEOUT.value == "timeout"
        assert ToolStatus.RATE_LIMITED.value == "rate_limited"
        assert ToolStatus.EMPTY_RESULT.value == "empty_result"


class TestToolMode:
    """Tests for ToolMode enum."""

    def test_mode_values(self):
        """Test mode values."""
        assert ToolMode.CORE.value == "core"
        assert ToolMode.EXTENDED.value == "extended"


class TestToolCall:
    """Tests for ToolCall model."""

    def test_create_basic_tool_call(self):
        """Test creating a basic tool call."""
        tool_call = ToolCall(
            tool_name="web_search",
            input_data={"query": "test"}
        )
        assert tool_call.tool_name == "web_search"
        assert tool_call.input_data == {"query": "test"}
        assert tool_call.status == ToolStatus.SUCCESS
        assert tool_call.id is not None

    def test_tool_call_with_output(self):
        """Test tool call with output data."""
        tool_call = ToolCall(
            tool_name="calculator",
            input_data={"expression": "2+2"},
            output_data={"result": 4},
            latency_ms=5
        )
        assert tool_call.output_data == {"result": 4}
        assert tool_call.latency_ms == 5

    def test_tool_call_with_error(self):
        """Test tool call with error."""
        tool_call = ToolCall(
            tool_name="web_search",
            input_data={"query": "test"},
            status=ToolStatus.ERROR,
            error_message="Connection failed"
        )
        assert tool_call.status == ToolStatus.ERROR
        assert tool_call.error_message == "Connection failed"

    def test_tool_call_with_fallback(self):
        """Test tool call that used fallback."""
        tool_call = ToolCall(
            tool_name="web_search",
            input_data={"query": "test"},
            status=ToolStatus.FALLBACK,
            fallback_used="wikipedia"
        )
        assert tool_call.fallback_used == "wikipedia"


class TestChatRequest:
    """Tests for ChatRequest model."""

    def test_valid_request(self):
        """Test valid chat request."""
        request = ChatRequest(message="Hello, world!")
        assert request.message == "Hello, world!"
        assert request.mode == "normal"
        assert request.stream is False

    def test_request_with_mode(self):
        """Test request with mode specified."""
        request = ChatRequest(message="Test", mode="deep")
        assert request.mode == "deep"

    def test_empty_message_rejected(self):
        """Test empty message is rejected."""
        with pytest.raises(ValidationError):
            ChatRequest(message="")

    def test_whitespace_only_rejected(self):
        """Test whitespace-only message is rejected."""
        with pytest.raises(ValidationError):
            ChatRequest(message="   ")

    def test_message_trimmed(self):
        """Test message is trimmed."""
        request = ChatRequest(message="  hello  ")
        assert request.message == "hello"

    def test_message_max_length(self):
        """Test message max length enforced."""
        long_message = "a" * 2001
        with pytest.raises(ValidationError):
            ChatRequest(message=long_message)

    def test_message_at_max_length(self):
        """Test message at exactly max length."""
        message = "a" * 2000
        request = ChatRequest(message=message)
        assert len(request.message) == 2000

    def test_invalid_mode_rejected(self):
        """Test invalid mode is rejected."""
        with pytest.raises(ValidationError):
            ChatRequest(message="test", mode="invalid")


class TestChatResponse:
    """Tests for ChatResponse model."""

    def test_basic_response(self):
        """Test basic chat response."""
        response = ChatResponse(
            response="Hello!",
            session_id="test-session"
        )
        assert response.response == "Hello!"
        assert response.session_id == "test-session"
        assert response.tool_calls == []
        assert response.sources == []

    def test_response_with_tool_calls(self):
        """Test response with tool calls."""
        tool_call = ToolCall(tool_name="calculator", input_data={})
        response = ChatResponse(
            response="The result is 4",
            session_id="test",
            tool_calls=[tool_call],
            sources=["calculator"]
        )
        assert len(response.tool_calls) == 1
        assert response.sources == ["calculator"]

    def test_response_with_disclaimer(self):
        """Test response with disclaimer."""
        response = ChatResponse(
            response="Approximately 100",
            session_id="test",
            disclaimer="Value is within 5-10% tolerance"
        )
        assert response.disclaimer is not None

    def test_response_with_user_action(self):
        """Test response requiring user action."""
        action = UserAction(
            type=UserActionType.SEARCH_MORE,
            message="Continue searching?"
        )
        response = ChatResponse(
            response="Partial results",
            session_id="test",
            user_action_required=action
        )
        assert response.user_action_required is not None


class TestConversationSession:
    """Tests for ConversationSession model."""

    def test_create_session(self):
        """Test creating a session."""
        session = ConversationSession()
        assert session.session_id is not None
        assert session.messages == []
        assert session.mode == "normal"

    def test_add_message(self):
        """Test adding a message."""
        session = ConversationSession()
        msg = session.add_message("user", "Hello!")
        assert len(session.messages) == 1
        assert msg.role == "user"
        assert msg.content == "Hello!"

    def test_add_multiple_messages(self):
        """Test adding multiple messages."""
        session = ConversationSession()
        session.add_message("user", "Hello!")
        session.add_message("assistant", "Hi there!")
        assert len(session.messages) == 2

    def test_updated_at_changes(self):
        """Test updated_at changes when message added."""
        session = ConversationSession()
        original_updated = session.updated_at
        import time
        time.sleep(0.01)
        session.add_message("user", "Test")
        assert session.updated_at > original_updated


class TestEvaluationMetrics:
    """Tests for EvaluationMetrics model."""

    def test_default_values(self):
        """Test default metric values."""
        metrics = EvaluationMetrics()
        assert metrics.pass_5 == 0.0
        assert metrics.pass_10 == 0.0
        assert metrics.tool_efficiency == 0.0
        assert metrics.tool_success_rate == 0.0

    def test_custom_values(self):
        """Test custom metric values."""
        metrics = EvaluationMetrics(
            pass_5=0.8,
            pass_10=0.85,
            tool_efficiency=0.75,
            tool_success_rate=0.9
        )
        assert metrics.pass_5 == 0.8
        assert metrics.pass_10 == 0.85


class TestDataset:
    """Tests for Dataset model."""

    def test_empty_dataset(self):
        """Test empty dataset."""
        dataset = Dataset()
        assert dataset.questions == []
        assert dataset.get_categories() == []

    def test_get_by_category(self):
        """Test filtering by category."""
        q1 = DatasetQuestion(
            id="1",
            question="Q1",
            category="company",
            expected_behavior=ExpectedBehavior(tools=["web_search"]),
            ground_truth=GroundTruth(answer="A1")
        )
        q2 = DatasetQuestion(
            id="2",
            question="Q2",
            category="finance",
            expected_behavior=ExpectedBehavior(tools=["yahoo_finance"]),
            ground_truth=GroundTruth(answer="A2")
        )
        dataset = Dataset(questions=[q1, q2])

        company_qs = dataset.get_by_category("company")
        assert len(company_qs) == 1
        assert company_qs[0].id == "1"

    def test_get_categories(self):
        """Test getting unique categories."""
        q1 = DatasetQuestion(
            id="1",
            question="Q1",
            category="company",
            expected_behavior=ExpectedBehavior(tools=[]),
            ground_truth=GroundTruth(answer="A1")
        )
        q2 = DatasetQuestion(
            id="2",
            question="Q2",
            category="finance",
            expected_behavior=ExpectedBehavior(tools=[]),
            ground_truth=GroundTruth(answer="A2")
        )
        q3 = DatasetQuestion(
            id="3",
            question="Q3",
            category="company",
            expected_behavior=ExpectedBehavior(tools=[]),
            ground_truth=GroundTruth(answer="A3")
        )
        dataset = Dataset(questions=[q1, q2, q3])

        categories = dataset.get_categories()
        assert len(categories) == 2
        assert "company" in categories
        assert "finance" in categories


class TestExportRequest:
    """Tests for ExportRequest model."""

    def test_default_format(self):
        """Test default export format."""
        request = ExportRequest()
        assert request.format == "csv"
        assert request.include_traces is True

    def test_pdf_format(self):
        """Test PDF export format."""
        request = ExportRequest(format="pdf")
        assert request.format == "pdf"

    def test_invalid_format(self):
        """Test invalid format rejected."""
        with pytest.raises(ValidationError):
            ExportRequest(format="xlsx")


class TestGroundTruth:
    """Tests for GroundTruth model."""

    def test_basic_ground_truth(self):
        """Test basic ground truth."""
        gt = GroundTruth(answer="2010")
        assert gt.answer == "2010"
        assert gt.answer_variants == []

    def test_with_variants(self):
        """Test ground truth with variants."""
        gt = GroundTruth(
            answer="2010",
            answer_variants=["Twenty ten", "Two thousand ten"]
        )
        assert len(gt.answer_variants) == 2

    def test_with_tolerance(self):
        """Test ground truth with numeric tolerance."""
        gt = GroundTruth(
            answer="100 million",
            tolerance_percent=10.0
        )
        assert gt.tolerance_percent == 10.0


class TestErrorModels:
    """Tests for error models."""

    def test_error_detail(self):
        """Test ErrorDetail model."""
        error = ErrorDetail(
            code="TEST_ERROR",
            message="Test error message"
        )
        assert error.code == "TEST_ERROR"
        assert error.message == "Test error message"
        assert error.timestamp is not None

    def test_error_response(self):
        """Test ErrorResponse model."""
        error = ErrorDetail(code="ERR", message="Error")
        response = ErrorResponse(error=error)
        assert response.error.code == "ERR"


class TestModelSerialization:
    """Tests for model serialization."""

    def test_tool_call_to_dict(self):
        """Test ToolCall serialization."""
        tool_call = ToolCall(
            tool_name="test",
            input_data={"key": "value"}
        )
        data = tool_call.model_dump()
        assert "tool_name" in data
        assert "input_data" in data
        assert data["status"] == "success"

    def test_chat_response_to_json(self):
        """Test ChatResponse JSON serialization."""
        response = ChatResponse(
            response="Test",
            session_id="123"
        )
        json_str = response.model_dump_json()
        assert "Test" in json_str
        assert "123" in json_str

    def test_evaluation_run_serialization(self):
        """Test EvaluationRun serialization."""
        run = EvaluationRun(
            total_questions=20,
            status="completed"
        )
        data = run.model_dump()
        assert data["total_questions"] == 20
        assert data["status"] == "completed"
