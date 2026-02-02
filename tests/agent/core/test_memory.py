"""Tests for memory management module."""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock

from src.agent.core.memory import (
    Message,
    ShortTermMemory,
    LongTermMemory,
    MemoryManager,
)


class TestMessage:
    """Tests for Message dataclass."""

    def test_message_creation(self):
        """Test basic message creation."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.timestamp > 0
        assert msg.metadata == {}

    def test_message_with_metadata(self):
        """Test message with metadata."""
        metadata = {"source": "test", "priority": 1}
        msg = Message(role="assistant", content="Hi there", metadata=metadata)
        assert msg.metadata == metadata

    def test_message_to_dict(self):
        """Test conversion to API dict format."""
        msg = Message(role="user", content="Test message")
        result = msg.to_dict()
        assert result == {"role": "user", "content": "Test message"}
        # Should not include timestamp or metadata
        assert "timestamp" not in result
        assert "metadata" not in result

    def test_message_to_storage_dict(self):
        """Test conversion to storage dict format."""
        metadata = {"key": "value"}
        msg = Message(role="user", content="Test", metadata=metadata)
        result = msg.to_storage_dict()
        assert result["role"] == "user"
        assert result["content"] == "Test"
        assert "timestamp" in result
        assert result["metadata"] == metadata


class TestShortTermMemory:
    """Tests for ShortTermMemory class."""

    def test_initialization_defaults(self):
        """Test default initialization."""
        memory = ShortTermMemory()
        assert memory.max_messages == 20  # Default from config
        assert len(memory) == 0

    def test_initialization_custom_limits(self):
        """Test initialization with custom limits."""
        memory = ShortTermMemory(max_messages=10, max_tokens=4000)
        assert memory.max_messages == 10
        assert memory.max_tokens == 4000

    def test_add_message(self):
        """Test adding a generic message."""
        memory = ShortTermMemory()
        memory.add_message("user", "Hello")
        assert len(memory) == 1
        messages = memory.get_messages()
        assert messages[0].role == "user"
        assert messages[0].content == "Hello"

    def test_add_user_message(self):
        """Test adding user message."""
        memory = ShortTermMemory()
        memory.add_user_message("What is the weather?")
        messages = memory.get_messages()
        assert len(messages) == 1
        assert messages[0].role == "user"
        assert messages[0].content == "What is the weather?"

    def test_add_assistant_message(self):
        """Test adding assistant message."""
        memory = ShortTermMemory()
        memory.add_assistant_message("The weather is sunny.")
        messages = memory.get_messages()
        assert len(messages) == 1
        assert messages[0].role == "assistant"

    def test_add_message_with_metadata(self):
        """Test adding message with metadata."""
        memory = ShortTermMemory()
        metadata = {"tool_call": "web_search"}
        memory.add_message("assistant", "Here are the results", metadata)
        messages = memory.get_messages()
        assert messages[0].metadata == metadata

    def test_get_messages_for_api(self):
        """Test getting messages formatted for API."""
        memory = ShortTermMemory()
        memory.add_user_message("Question")
        memory.add_assistant_message("Answer")

        api_messages = memory.get_messages_for_api()
        assert len(api_messages) == 2
        assert api_messages[0] == {"role": "user", "content": "Question"}
        assert api_messages[1] == {"role": "assistant", "content": "Answer"}

    def test_get_recent_messages(self):
        """Test getting recent messages."""
        memory = ShortTermMemory()
        for i in range(5):
            memory.add_user_message(f"Message {i}")

        recent = memory.get_recent_messages(3)
        assert len(recent) == 3
        assert recent[0].content == "Message 2"
        assert recent[2].content == "Message 4"

    def test_get_recent_messages_fewer_than_count(self):
        """Test getting recent messages when fewer exist."""
        memory = ShortTermMemory()
        memory.add_user_message("Only one")

        recent = memory.get_recent_messages(5)
        assert len(recent) == 1

    def test_clear(self):
        """Test clearing memory."""
        memory = ShortTermMemory()
        memory.add_user_message("Message 1")
        memory.add_user_message("Message 2")

        count = memory.clear()
        assert count == 2
        assert len(memory) == 0

    def test_clear_empty_memory(self):
        """Test clearing empty memory."""
        memory = ShortTermMemory()
        count = memory.clear()
        assert count == 0

    def test_trim_by_message_count(self):
        """Test trimming when message count exceeds limit."""
        memory = ShortTermMemory(max_messages=3)

        for i in range(5):
            memory.add_user_message(f"Message {i}")

        assert len(memory) == 3
        messages = memory.get_messages()
        # Should have the most recent messages
        assert messages[0].content == "Message 2"
        assert messages[2].content == "Message 4"

    def test_trim_by_token_estimate(self):
        """Test trimming when token count exceeds limit."""
        # 4 chars ~ 1 token, so 4000 chars ~ 1000 tokens
        memory = ShortTermMemory(max_messages=100, max_tokens=100)

        # Add messages with ~400 chars each (~100 tokens)
        long_content = "x" * 400
        for i in range(5):
            memory.add_user_message(long_content)

        # Should trim to fit token limit
        assert len(memory) < 5

    def test_estimate_tokens(self):
        """Test token estimation."""
        memory = ShortTermMemory()
        # 4 chars = 1 token
        assert memory._estimate_tokens("1234") == 1
        assert memory._estimate_tokens("12345678") == 2
        assert memory._estimate_tokens("") == 0

    def test_len(self):
        """Test __len__ method."""
        memory = ShortTermMemory()
        assert len(memory) == 0
        memory.add_user_message("Test")
        assert len(memory) == 1

    def test_thread_safety(self):
        """Test thread-safe operations."""
        memory = ShortTermMemory(max_messages=1000)
        errors = []

        def add_messages(thread_id: int):
            try:
                for i in range(50):
                    memory.add_user_message(f"Thread {thread_id} message {i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=add_messages, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        # Should have messages from all threads (may be trimmed)
        assert len(memory) > 0


class TestLongTermMemory:
    """Tests for LongTermMemory class."""

    def test_initialization_without_session_id(self):
        """Test initialization generates session ID."""
        with patch("src.agent.core.memory.get_database") as mock_db:
            memory = LongTermMemory()
            assert memory.session_id is not None
            assert memory.session_id.startswith("session_")

    def test_initialization_with_session_id(self):
        """Test initialization with provided session ID."""
        memory = LongTermMemory(session_id="test_session_123")
        assert memory.session_id == "test_session_123"

    def test_generate_session_id_format(self):
        """Test session ID format."""
        memory = LongTermMemory()
        session_id = memory._generate_session_id()
        # Format: session_YYYYMMDD_HHMMSS_hexchars
        parts = session_id.split("_")
        assert parts[0] == "session"
        assert len(parts) == 4
        assert len(parts[1]) == 8  # Date
        assert len(parts[2]) == 6  # Time
        assert len(parts[3]) == 8  # UUID hex

    def test_save_message_success(self):
        """Test saving message to storage."""
        mock_repo = Mock()
        mock_repo.save_message.return_value = "msg_123"

        with patch("src.agent.core.memory.get_database") as mock_get_db:
            with patch("src.agent.core.memory.ConversationRepository") as mock_repo_class:
                mock_repo_class.return_value = mock_repo

                memory = LongTermMemory(session_id="test_session")
                result = memory.save_message("user", "Hello", "normal", {"key": "value"})

                assert result == "msg_123"
                mock_repo.save_message.assert_called_once_with(
                    session_id="test_session",
                    role="user",
                    content="Hello",
                    mode="normal",
                    metadata={"key": "value"}
                )

    def test_save_message_storage_failure(self):
        """Test saving message when storage fails."""
        with patch("src.agent.core.memory.get_database") as mock_get_db:
            mock_get_db.side_effect = Exception("Database error")

            memory = LongTermMemory(session_id="test_session")
            result = memory.save_message("user", "Hello")

            assert result is None

    def test_get_session_history(self):
        """Test getting session history."""
        mock_repo = Mock()
        mock_repo.get_session_messages.return_value = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"}
        ]

        with patch("src.agent.core.memory.get_database"):
            with patch("src.agent.core.memory.ConversationRepository") as mock_repo_class:
                mock_repo_class.return_value = mock_repo

                memory = LongTermMemory(session_id="test_session")
                history = memory.get_session_history(limit=10)

                assert len(history) == 2
                mock_repo.get_session_messages.assert_called_once_with("test_session", limit=10)

    def test_get_session_history_failure(self):
        """Test getting history when storage fails."""
        with patch("src.agent.core.memory.get_database") as mock_get_db:
            mock_get_db.side_effect = Exception("Database error")

            memory = LongTermMemory(session_id="test_session")
            history = memory.get_session_history()

            assert history == []

    def test_get_recent_sessions(self):
        """Test getting recent sessions."""
        mock_repo = Mock()
        mock_repo.get_sessions.return_value = [
            {"session_id": "session_1"},
            {"session_id": "session_2"}
        ]

        with patch("src.agent.core.memory.get_database"):
            with patch("src.agent.core.memory.ConversationRepository") as mock_repo_class:
                mock_repo_class.return_value = mock_repo

                memory = LongTermMemory()
                sessions = memory.get_recent_sessions(limit=5)

                assert len(sessions) == 2

    def test_search_history(self):
        """Test searching conversation history."""
        mock_repo = Mock()
        mock_repo.search_messages.return_value = [
            {"role": "user", "content": "weather query"}
        ]

        with patch("src.agent.core.memory.get_database"):
            with patch("src.agent.core.memory.ConversationRepository") as mock_repo_class:
                mock_repo_class.return_value = mock_repo

                memory = LongTermMemory()
                results = memory.search_history("weather", limit=10)

                assert len(results) == 1
                mock_repo.search_messages.assert_called_once_with("weather", limit=10)

    def test_delete_session(self):
        """Test deleting session."""
        mock_repo = Mock()
        mock_repo.delete_session.return_value = True

        with patch("src.agent.core.memory.get_database"):
            with patch("src.agent.core.memory.ConversationRepository") as mock_repo_class:
                mock_repo_class.return_value = mock_repo

                memory = LongTermMemory(session_id="test_session")
                result = memory.delete_session()

                assert result is True
                mock_repo.delete_session.assert_called_once_with("test_session")

    def test_new_session(self):
        """Test starting new session."""
        memory = LongTermMemory(session_id="old_session")
        old_id = memory.session_id

        new_id = memory.new_session()

        assert new_id != old_id
        assert memory.session_id == new_id
        assert new_id.startswith("session_")

    def test_is_available_true(self):
        """Test availability check when storage works."""
        with patch("src.agent.core.memory.get_database"):
            with patch("src.agent.core.memory.ConversationRepository"):
                memory = LongTermMemory()
                assert memory.is_available is True

    def test_is_available_false(self):
        """Test availability check when storage fails."""
        with patch("src.agent.core.memory.get_database") as mock_get_db:
            mock_get_db.side_effect = Exception("Database error")

            memory = LongTermMemory()
            assert memory.is_available is False


class TestMemoryManager:
    """Tests for MemoryManager class."""

    def test_initialization_defaults(self):
        """Test default initialization."""
        with patch("src.agent.core.memory.LongTermMemory"):
            manager = MemoryManager()
            assert manager.short_term is not None
            assert manager._enable_long_term is True

    def test_initialization_disable_long_term(self):
        """Test initialization with long-term disabled."""
        manager = MemoryManager(enable_long_term=False)
        assert manager.short_term is not None
        assert manager.long_term is None
        assert manager._enable_long_term is False

    def test_initialization_with_session_id(self):
        """Test initialization with session ID."""
        with patch("src.agent.core.memory.LongTermMemory") as mock_ltm:
            manager = MemoryManager(session_id="test_session")
            mock_ltm.assert_called_once_with(session_id="test_session")

    def test_initialization_long_term_failure(self):
        """Test graceful handling of long-term memory failure."""
        with patch("src.agent.core.memory.LongTermMemory") as mock_ltm:
            mock_ltm.side_effect = Exception("Database error")

            manager = MemoryManager()
            assert manager.long_term is None
            assert manager._enable_long_term is False

    def test_add_user_message(self):
        """Test adding user message to both memories."""
        mock_ltm = Mock()

        with patch("src.agent.core.memory.LongTermMemory", return_value=mock_ltm):
            manager = MemoryManager()
            manager.add_user_message("Hello", {"key": "value"})

            # Should be in short-term
            assert len(manager.short_term) == 1
            messages = manager.short_term.get_messages()
            assert messages[0].role == "user"
            assert messages[0].content == "Hello"

            # Should be saved to long-term
            mock_ltm.save_message.assert_called_once()

    def test_add_user_message_long_term_disabled(self):
        """Test adding user message when long-term is disabled."""
        manager = MemoryManager(enable_long_term=False)
        manager.add_user_message("Hello")

        # Should only be in short-term
        assert len(manager.short_term) == 1

    def test_add_assistant_message(self):
        """Test adding assistant message."""
        mock_ltm = Mock()

        with patch("src.agent.core.memory.LongTermMemory", return_value=mock_ltm):
            manager = MemoryManager()
            manager.add_assistant_message("Response")

            messages = manager.short_term.get_messages()
            assert messages[0].role == "assistant"
            mock_ltm.save_message.assert_called_once()

    def test_add_system_message(self):
        """Test adding system message (short-term only)."""
        mock_ltm = Mock()

        with patch("src.agent.core.memory.LongTermMemory", return_value=mock_ltm):
            manager = MemoryManager()
            manager.add_system_message("System prompt")

            messages = manager.short_term.get_messages()
            assert messages[0].role == "system"
            # Should NOT be saved to long-term
            mock_ltm.save_message.assert_not_called()

    def test_get_context_messages(self):
        """Test getting messages for LLM context."""
        manager = MemoryManager(enable_long_term=False)
        manager.add_user_message("Question")
        manager.add_assistant_message("Answer")

        context = manager.get_context_messages()
        assert len(context) == 2
        assert context[0]["role"] == "user"
        assert context[1]["role"] == "assistant"

    def test_get_recent_context(self):
        """Test getting recent context."""
        manager = MemoryManager(enable_long_term=False)
        for i in range(5):
            manager.add_user_message(f"Message {i}")

        recent = manager.get_recent_context(3)
        assert len(recent) == 3

    def test_set_mode(self):
        """Test setting research mode."""
        manager = MemoryManager(enable_long_term=False)
        manager.set_mode("deep")
        assert manager._current_mode == "deep"

    def test_clear_short_term(self):
        """Test clearing short-term memory."""
        manager = MemoryManager(enable_long_term=False)
        manager.add_user_message("Message 1")
        manager.add_user_message("Message 2")

        count = manager.clear_short_term()
        assert count == 2
        assert len(manager.short_term) == 0

    def test_new_session(self):
        """Test starting new session."""
        mock_ltm = Mock()
        mock_ltm.new_session.return_value = "new_session_id"

        with patch("src.agent.core.memory.LongTermMemory", return_value=mock_ltm):
            manager = MemoryManager()
            manager.add_user_message("Old message")

            new_id = manager.new_session()

            assert new_id == "new_session_id"
            assert len(manager.short_term) == 0

    def test_new_session_no_long_term(self):
        """Test new session without long-term memory."""
        manager = MemoryManager(enable_long_term=False)
        manager.add_user_message("Old message")

        result = manager.new_session()

        assert result is None
        assert len(manager.short_term) == 0

    def test_get_session_id(self):
        """Test getting session ID."""
        mock_ltm = Mock()
        mock_ltm.session_id = "test_session"

        with patch("src.agent.core.memory.LongTermMemory", return_value=mock_ltm):
            manager = MemoryManager()
            assert manager.get_session_id() == "test_session"

    def test_get_session_id_no_long_term(self):
        """Test getting session ID without long-term memory."""
        manager = MemoryManager(enable_long_term=False)
        assert manager.get_session_id() is None

    def test_get_stats(self):
        """Test getting memory statistics."""
        mock_ltm = Mock()
        mock_ltm.session_id = "test_session"

        with patch("src.agent.core.memory.LongTermMemory", return_value=mock_ltm):
            manager = MemoryManager()
            manager.add_user_message("Test")
            manager.set_mode("deep")

            stats = manager.get_stats()

            assert stats["short_term_messages"] == 1
            assert stats["long_term_enabled"] is True
            assert stats["current_mode"] == "deep"
            assert stats["session_id"] == "test_session"

    def test_load_session_context(self):
        """Test loading session context from long-term memory."""
        mock_ltm = Mock()
        mock_ltm.get_session_history.return_value = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"}
        ]

        with patch("src.agent.core.memory.LongTermMemory", return_value=mock_ltm):
            manager = MemoryManager()
            count = manager.load_session_context(message_count=10)

            assert count == 2
            assert len(manager.short_term) == 2

    def test_load_session_context_no_long_term(self):
        """Test loading context without long-term memory."""
        manager = MemoryManager(enable_long_term=False)
        count = manager.load_session_context()
        assert count == 0

    def test_load_session_context_failure(self):
        """Test loading context when retrieval fails."""
        mock_ltm = Mock()
        mock_ltm.get_session_history.side_effect = Exception("Database error")

        with patch("src.agent.core.memory.LongTermMemory", return_value=mock_ltm):
            manager = MemoryManager()
            count = manager.load_session_context()
            assert count == 0

    def test_mode_passed_to_long_term(self):
        """Test that mode is passed when saving to long-term."""
        mock_ltm = Mock()

        with patch("src.agent.core.memory.LongTermMemory", return_value=mock_ltm):
            manager = MemoryManager()
            manager.set_mode("deep")
            manager.add_user_message("Test question")

            # Check mode was passed to save_message
            call_args = mock_ltm.save_message.call_args
            assert call_args[0][2] == "deep"  # mode argument
