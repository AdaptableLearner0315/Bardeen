"""Unit tests for storage/repositories."""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime

from src.storage.database import Database
from src.storage.repositories import (
    ConversationRepository,
    ToolTraceRepository,
    EvaluationRepository,
)
from src.shared.models import ToolCall, ToolStatus, QuestionResult, AttemptResult
from src.shared.config import reset_config


@pytest.fixture
def temp_db_path():
    """Create a temporary database path."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        path = Path(f.name)
    yield path
    if path.exists():
        os.unlink(path)
    for suffix in ['-wal', '-shm']:
        wal_path = Path(str(path) + suffix)
        if wal_path.exists():
            os.unlink(wal_path)


@pytest.fixture
def db(temp_db_path):
    """Create a fresh database instance."""
    reset_config()
    Database.reset_instance()
    database = Database(temp_db_path)
    database.initialize_schema()
    yield database
    database.close_all()
    Database.reset_instance()


@pytest.fixture
def conversation_repo(db):
    """Create conversation repository."""
    return ConversationRepository(db)


@pytest.fixture
def tool_trace_repo(db):
    """Create tool trace repository."""
    return ToolTraceRepository(db)


@pytest.fixture
def evaluation_repo(db):
    """Create evaluation repository."""
    return EvaluationRepository(db)


class TestConversationRepository:
    """Tests for ConversationRepository."""

    def test_save_message(self, conversation_repo):
        """Test saving a message."""
        msg = conversation_repo.save_message(
            session_id="session-1",
            role="user",
            content="Hello, world!"
        )
        assert msg.id is not None
        assert msg.role == "user"
        assert msg.content == "Hello, world!"

    def test_save_message_with_mode(self, conversation_repo):
        """Test saving a message with mode."""
        msg = conversation_repo.save_message(
            session_id="session-1",
            role="user",
            content="Test",
            mode="deep"
        )
        assert msg is not None

    def test_get_session_messages(self, conversation_repo):
        """Test getting messages for a session."""
        conversation_repo.save_message("session-1", "user", "Hello")
        conversation_repo.save_message("session-1", "assistant", "Hi")
        conversation_repo.save_message("session-2", "user", "Different session")

        messages = conversation_repo.get_session_messages("session-1")
        assert len(messages) == 2
        assert messages[0].content == "Hello"
        assert messages[1].content == "Hi"

    def test_get_session_messages_with_limit(self, conversation_repo):
        """Test getting messages with limit."""
        for i in range(10):
            conversation_repo.save_message("session-1", "user", f"Message {i}")

        messages = conversation_repo.get_session_messages("session-1", limit=5)
        assert len(messages) == 5

    def test_get_recent_messages(self, conversation_repo):
        """Test getting recent messages."""
        for i in range(10):
            conversation_repo.save_message("session-1", "user", f"Message {i}")

        messages = conversation_repo.get_recent_messages("session-1", count=5)
        assert len(messages) == 5
        # Should be in chronological order (oldest to newest)
        assert messages[0].content == "Message 5"
        assert messages[-1].content == "Message 9"

    def test_get_session_count(self, conversation_repo):
        """Test getting message count."""
        conversation_repo.save_message("session-1", "user", "Message 1")
        conversation_repo.save_message("session-1", "assistant", "Message 2")

        count = conversation_repo.get_session_count("session-1")
        assert count == 2

    def test_delete_session(self, conversation_repo):
        """Test deleting a session."""
        conversation_repo.save_message("session-1", "user", "Message 1")
        conversation_repo.save_message("session-1", "assistant", "Message 2")

        deleted = conversation_repo.delete_session("session-1")
        assert deleted == 2
        assert conversation_repo.get_session_count("session-1") == 0

    def test_session_exists(self, conversation_repo):
        """Test checking if session exists."""
        assert conversation_repo.session_exists("session-1") is False
        conversation_repo.save_message("session-1", "user", "Hello")
        assert conversation_repo.session_exists("session-1") is True

    def test_get_sessions(self, conversation_repo):
        """Test getting list of sessions."""
        conversation_repo.save_message("session-1", "user", "Hello")
        conversation_repo.save_message("session-2", "user", "World")
        conversation_repo.save_message("session-2", "assistant", "Hi")

        sessions = conversation_repo.get_sessions()
        assert len(sessions) == 2

    def test_empty_session_messages(self, conversation_repo):
        """Test getting messages from empty session."""
        messages = conversation_repo.get_session_messages("nonexistent")
        assert messages == []


class TestToolTraceRepository:
    """Tests for ToolTraceRepository."""

    def test_save_trace(self, tool_trace_repo):
        """Test saving a tool trace."""
        tool_call = ToolCall(
            tool_name="web_search",
            input_data={"query": "test"},
            output_data={"results": []},
            status=ToolStatus.SUCCESS,
            latency_ms=100
        )

        saved = tool_trace_repo.save_trace(tool_call, "session-1")
        assert saved.id is not None

    def test_save_traces(self, tool_trace_repo):
        """Test saving multiple traces."""
        tool_calls = [
            ToolCall(tool_name="web_search", input_data={"query": "test1"}),
            ToolCall(tool_name="wikipedia", input_data={"topic": "test2"}),
        ]

        saved = tool_trace_repo.save_traces(tool_calls, "session-1")
        assert len(saved) == 2

    def test_get_by_id(self, tool_trace_repo):
        """Test getting trace by ID."""
        tool_call = ToolCall(
            tool_name="calculator",
            input_data={"expression": "2+2"},
            output_data={"result": 4}
        )
        saved = tool_trace_repo.save_trace(tool_call, "session-1")

        retrieved = tool_trace_repo.get_by_id(saved.id)
        assert retrieved is not None
        assert retrieved.tool_name == "calculator"
        assert retrieved.input_data == {"expression": "2+2"}

    def test_get_by_id_not_found(self, tool_trace_repo):
        """Test getting non-existent trace."""
        retrieved = tool_trace_repo.get_by_id("nonexistent")
        assert retrieved is None

    def test_get_by_session(self, tool_trace_repo):
        """Test getting traces by session."""
        tool_trace_repo.save_trace(
            ToolCall(tool_name="tool1", input_data={}),
            "session-1"
        )
        tool_trace_repo.save_trace(
            ToolCall(tool_name="tool2", input_data={}),
            "session-1"
        )
        tool_trace_repo.save_trace(
            ToolCall(tool_name="tool3", input_data={}),
            "session-2"
        )

        traces = tool_trace_repo.get_by_session("session-1")
        assert len(traces) == 2

    def test_get_by_tool(self, tool_trace_repo):
        """Test getting traces by tool name."""
        tool_trace_repo.save_trace(
            ToolCall(tool_name="web_search", input_data={}),
            "session-1"
        )
        tool_trace_repo.save_trace(
            ToolCall(tool_name="web_search", input_data={}),
            "session-2"
        )
        tool_trace_repo.save_trace(
            ToolCall(tool_name="calculator", input_data={}),
            "session-1"
        )

        traces = tool_trace_repo.get_by_tool("web_search")
        assert len(traces) == 2

    def test_get_stats_by_tool(self, tool_trace_repo):
        """Test getting statistics by tool."""
        tool_trace_repo.save_trace(
            ToolCall(tool_name="web_search", input_data={}, status=ToolStatus.SUCCESS, latency_ms=100),
            "session-1"
        )
        tool_trace_repo.save_trace(
            ToolCall(tool_name="web_search", input_data={}, status=ToolStatus.SUCCESS, latency_ms=200),
            "session-2"
        )
        tool_trace_repo.save_trace(
            ToolCall(tool_name="web_search", input_data={}, status=ToolStatus.ERROR, latency_ms=50),
            "session-3"
        )

        stats = tool_trace_repo.get_stats_by_tool()
        assert "web_search" in stats
        assert stats["web_search"]["total_calls"] == 3
        assert stats["web_search"]["success_count"] == 2
        assert stats["web_search"]["error_count"] == 1

    def test_get_session_stats(self, tool_trace_repo):
        """Test getting session statistics."""
        tool_trace_repo.save_trace(
            ToolCall(tool_name="tool1", input_data={}, status=ToolStatus.SUCCESS, latency_ms=100),
            "session-1"
        )
        tool_trace_repo.save_trace(
            ToolCall(tool_name="tool2", input_data={}, status=ToolStatus.SUCCESS, latency_ms=200),
            "session-1"
        )

        stats = tool_trace_repo.get_session_stats("session-1")
        assert stats["total_calls"] == 2
        assert stats["success_count"] == 2
        assert stats["success_rate"] == 1.0
        assert stats["unique_tools"] == 2

    def test_delete_by_session(self, tool_trace_repo):
        """Test deleting traces by session."""
        tool_trace_repo.save_trace(ToolCall(tool_name="tool1", input_data={}), "session-1")
        tool_trace_repo.save_trace(ToolCall(tool_name="tool2", input_data={}), "session-1")

        deleted = tool_trace_repo.delete_by_session("session-1")
        assert deleted == 2

    def test_trace_with_error(self, tool_trace_repo):
        """Test saving trace with error."""
        tool_call = ToolCall(
            tool_name="web_search",
            input_data={"query": "test"},
            status=ToolStatus.ERROR,
            error_message="Connection failed",
            retry_count=2
        )

        saved = tool_trace_repo.save_trace(tool_call, "session-1")
        retrieved = tool_trace_repo.get_by_id(saved.id)

        assert retrieved.status == ToolStatus.ERROR
        assert retrieved.error_message == "Connection failed"
        assert retrieved.retry_count == 2


class TestEvaluationRepository:
    """Tests for EvaluationRepository."""

    def test_create_run(self, evaluation_repo):
        """Test creating an evaluation run."""
        run = evaluation_repo.create_run(
            total_questions=20,
            config={"k_attempts": 10}
        )
        assert run.id is not None
        assert run.status == "running"
        assert run.total_questions == 20

    def test_update_run_status(self, evaluation_repo):
        """Test updating run status."""
        run = evaluation_repo.create_run(total_questions=10)

        updated = evaluation_repo.update_run_status(
            run.id,
            status="completed",
            questions_completed=10
        )
        assert updated is True

        retrieved = evaluation_repo.get_run_summary(run.id)
        assert retrieved.status == "completed"
        assert retrieved.questions_completed == 10

    def test_save_question_result(self, evaluation_repo):
        """Test saving a question result."""
        run = evaluation_repo.create_run(total_questions=5)

        result = QuestionResult(
            question_id="q1",
            question_text="What is 2+2?",
            category="math",
            ground_truth="4",
            attempts=[
                AttemptResult(attempt_number=1, answer="4", is_correct=True, latency_ms=100)
            ],
            consensus_answer="4",
            pass_5=True,
            pass_10=True,
            tool_efficiency=0.9,
            tool_success_rate=1.0,
            avg_latency_ms=100
        )

        result_id = evaluation_repo.save_question_result(run.id, result)
        assert result_id is not None

        # Check run progress updated
        updated_run = evaluation_repo.get_run_summary(run.id)
        assert updated_run.questions_completed == 1

    def test_get_run(self, evaluation_repo):
        """Test getting full evaluation run."""
        run = evaluation_repo.create_run(total_questions=2)

        result1 = QuestionResult(
            question_id="q1",
            question_text="Question 1",
            category="cat1",
            ground_truth="answer1",
            pass_5=True,
            pass_10=True
        )
        result2 = QuestionResult(
            question_id="q2",
            question_text="Question 2",
            category="cat2",
            ground_truth="answer2",
            pass_5=False,
            pass_10=False
        )

        evaluation_repo.save_question_result(run.id, result1)
        evaluation_repo.save_question_result(run.id, result2)

        retrieved = evaluation_repo.get_run(run.id)
        assert retrieved is not None
        assert len(retrieved.question_results) == 2

    def test_get_run_not_found(self, evaluation_repo):
        """Test getting non-existent run."""
        run = evaluation_repo.get_run("nonexistent")
        assert run is None

    def test_list_runs(self, evaluation_repo):
        """Test listing evaluation runs."""
        evaluation_repo.create_run(total_questions=10)
        evaluation_repo.create_run(total_questions=20)

        runs = evaluation_repo.list_runs()
        assert len(runs) == 2

    def test_list_runs_with_status_filter(self, evaluation_repo):
        """Test listing runs with status filter."""
        run1 = evaluation_repo.create_run(total_questions=10)
        run2 = evaluation_repo.create_run(total_questions=20)

        evaluation_repo.update_run_status(run1.id, "completed")

        running = evaluation_repo.list_runs(status="running")
        completed = evaluation_repo.list_runs(status="completed")

        assert len(running) == 1
        assert len(completed) == 1

    def test_get_results_by_category(self, evaluation_repo):
        """Test getting results by category."""
        run = evaluation_repo.create_run(total_questions=3)

        for i, cat in enumerate(["math", "math", "science"]):
            result = QuestionResult(
                question_id=f"q{i}",
                question_text=f"Question {i}",
                category=cat,
                ground_truth="answer"
            )
            evaluation_repo.save_question_result(run.id, result)

        math_results = evaluation_repo.get_results_by_category(run.id, "math")
        assert len(math_results) == 2

        science_results = evaluation_repo.get_results_by_category(run.id, "science")
        assert len(science_results) == 1

    def test_get_category_stats(self, evaluation_repo):
        """Test getting category statistics."""
        run = evaluation_repo.create_run(total_questions=3)

        for i, (cat, pass5) in enumerate([("math", True), ("math", True), ("science", False)]):
            result = QuestionResult(
                question_id=f"q{i}",
                question_text=f"Question {i}",
                category=cat,
                ground_truth="answer",
                pass_5=pass5,
                pass_10=pass5
            )
            evaluation_repo.save_question_result(run.id, result)

        stats = evaluation_repo.get_category_stats(run.id)

        assert "math" in stats
        assert stats["math"]["total"] == 2
        assert stats["math"]["pass_5"] == 1.0

        assert "science" in stats
        assert stats["science"]["total"] == 1
        assert stats["science"]["pass_5"] == 0.0

    def test_delete_run(self, evaluation_repo):
        """Test deleting an evaluation run."""
        run = evaluation_repo.create_run(total_questions=2)

        result = QuestionResult(
            question_id="q1",
            question_text="Question",
            category="cat",
            ground_truth="answer"
        )
        evaluation_repo.save_question_result(run.id, result)

        deleted = evaluation_repo.delete_run(run.id)
        assert deleted is True

        retrieved = evaluation_repo.get_run(run.id)
        assert retrieved is None


class TestRepositoryEdgeCases:
    """Edge case tests for repositories."""

    def test_unicode_content(self, conversation_repo):
        """Test storing unicode content."""
        content = "Hello 你好 مرحبا 🚀"
        msg = conversation_repo.save_message("session-1", "user", content)

        messages = conversation_repo.get_session_messages("session-1")
        assert messages[0].content == content

    def test_large_content(self, conversation_repo):
        """Test storing large content."""
        content = "x" * 100000
        msg = conversation_repo.save_message("session-1", "user", content)

        messages = conversation_repo.get_session_messages("session-1")
        assert len(messages[0].content) == 100000

    def test_special_characters(self, conversation_repo):
        """Test storing content with special characters."""
        content = "Test's \"quoted\" content; DROP TABLE users;--"
        msg = conversation_repo.save_message("session-1", "user", content)

        messages = conversation_repo.get_session_messages("session-1")
        assert messages[0].content == content

    def test_json_serialization(self, tool_trace_repo):
        """Test JSON serialization of complex data."""
        tool_call = ToolCall(
            tool_name="test",
            input_data={
                "nested": {"a": {"b": [1, 2, 3]}},
                "list": [{"x": 1}, {"y": 2}],
                "unicode": "你好"
            },
            output_data={"result": "success"}
        )

        saved = tool_trace_repo.save_trace(tool_call, "session-1")
        retrieved = tool_trace_repo.get_by_id(saved.id)

        assert retrieved.input_data["nested"]["a"]["b"] == [1, 2, 3]
        assert retrieved.input_data["unicode"] == "你好"
