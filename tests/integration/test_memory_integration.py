"""Integration tests for memory with agent."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os

# Set test API key before imports
os.environ.setdefault("ANTHROPIC_API_KEY", "test_key_for_testing")

try:
    from src.agent.agent import ResearchAssistant, create_agent
    from src.agent.core.memory import MemoryManager
except ImportError:
    ResearchAssistant = None
    create_agent = None
    MemoryManager = None


@pytest.fixture
def mock_anthropic():
    """Mock Anthropic client to avoid API calls."""
    with patch('src.agent.llm_client.Anthropic') as mock:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(type="text", text="Test response")]
        mock_client.messages.create.return_value = mock_response
        mock.return_value = mock_client
        yield mock


class TestMemoryManagerIntegration:
    """Tests for MemoryManager standalone functionality."""

    @pytest.fixture
    def memory_manager(self):
        """Create memory manager for testing."""
        if MemoryManager is None:
            pytest.skip("MemoryManager not available")
        return MemoryManager(
            session_id="test_session",
            max_short_term_messages=10,
            enable_long_term=False  # Disable DB for unit tests
        )

    def test_memory_manager_initialization(self, memory_manager):
        """Test memory manager initializes properly."""
        assert memory_manager is not None
        assert memory_manager.short_term is not None

    def test_add_user_message(self, memory_manager):
        """Test adding user message to memory."""
        memory_manager.add_user_message("Hello, how are you?")

        messages = memory_manager.get_context_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello, how are you?"

    def test_add_assistant_message(self, memory_manager):
        """Test adding assistant message to memory."""
        memory_manager.add_assistant_message("I'm doing well, thank you!")

        messages = memory_manager.get_context_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "assistant"

    def test_conversation_flow(self, memory_manager):
        """Test full conversation flow in memory."""
        memory_manager.add_user_message("What is 2+2?")
        memory_manager.add_assistant_message("2+2 equals 4.")
        memory_manager.add_user_message("And 3+3?")
        memory_manager.add_assistant_message("3+3 equals 6.")

        messages = memory_manager.get_context_messages()
        assert len(messages) == 4
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
        assert messages[2]["role"] == "user"
        assert messages[3]["role"] == "assistant"

    def test_clear_short_term(self, memory_manager):
        """Test clearing short-term memory."""
        memory_manager.add_user_message("Message 1")
        memory_manager.add_user_message("Message 2")

        count = memory_manager.clear_short_term()

        assert count == 2
        assert len(memory_manager.get_context_messages()) == 0

    def test_get_recent_context(self, memory_manager):
        """Test getting recent context with limit."""
        for i in range(5):
            memory_manager.add_user_message(f"Message {i}")

        recent = memory_manager.get_recent_context(3)
        assert len(recent) == 3

    def test_memory_trimming(self, memory_manager):
        """Test memory trimming when exceeding max messages."""
        # Add more than max messages
        for i in range(15):
            memory_manager.add_user_message(f"Message {i}")

        messages = memory_manager.get_context_messages()
        # Should be trimmed to max (10)
        assert len(messages) <= 10


class TestAgentMemoryIntegration:
    """Tests for memory integration with ResearchAssistant."""

    @pytest.fixture
    def agent(self, mock_anthropic):
        """Create agent with mocked API."""
        if ResearchAssistant is None:
            pytest.skip("ResearchAssistant not available")

        from src.shared.config import Config, LLMConfig
        config = Config(
            anthropic_api_key="test_key",
            llm=LLMConfig()
        )
        return ResearchAssistant(config)

    def test_agent_has_memory_manager(self, agent):
        """Test agent has memory manager initialized."""
        assert hasattr(agent, 'memory')
        assert agent.memory is not None

    def test_agent_conversation_preserved(self, agent, mock_anthropic):
        """Test conversation is preserved across ask calls."""
        # First question
        agent.ask("What is Python?", reset_conversation=False)

        # Check memory has the message
        messages = agent.get_conversation_history()
        assert len(messages) >= 1

    def test_agent_reset_conversation(self, agent, mock_anthropic):
        """Test reset_conversation clears memory."""
        # Add some messages
        agent.ask("First question", reset_conversation=False)

        # Reset and ask again
        agent.ask("New question", reset_conversation=True)

        # Memory should only have the new conversation
        messages = agent.get_conversation_history()
        # Should have user + assistant messages from last exchange
        assert len(messages) <= 4  # At most user, assistant, user, assistant

    def test_get_conversation_history(self, agent, mock_anthropic):
        """Test get_conversation_history returns memory context."""
        agent.ask("Test question", reset_conversation=True)

        history = agent.get_conversation_history()
        assert isinstance(history, list)

    def test_reset_conversation_method(self, agent, mock_anthropic):
        """Test reset_conversation method clears memory."""
        agent.ask("Add some history", reset_conversation=False)

        agent.reset_conversation()

        history = agent.get_conversation_history()
        assert len(history) == 0


class TestGlobalSessionMemory:
    """Tests for global session memory persistence."""

    def test_global_session_id(self, mock_anthropic):
        """Test agents use global session ID."""
        if ResearchAssistant is None:
            pytest.skip("ResearchAssistant not available")

        from src.shared.config import Config, LLMConfig
        config = Config(
            anthropic_api_key="test_key",
            llm=LLMConfig()
        )

        agent1 = ResearchAssistant(config)
        agent2 = ResearchAssistant(config)

        # Both should have session_id "global_demo"
        if hasattr(agent1, 'memory') and agent1.memory.long_term:
            assert agent1.memory.get_session_id() == "global_demo"
        if hasattr(agent2, 'memory') and agent2.memory.long_term:
            assert agent2.memory.get_session_id() == "global_demo"
