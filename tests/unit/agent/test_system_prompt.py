"""Tests for system prompt and response conciseness."""

import pytest
from unittest.mock import Mock, patch, MagicMock

# Import will work after module is updated
try:
    from src.agent.llm_client import ClaudeLLMClient, SYSTEM_PROMPT
except ImportError:
    SYSTEM_PROMPT = None
    ClaudeLLMClient = None


class TestSystemPrompt:
    """Tests for system prompt behavior."""

    def test_system_prompt_exists(self):
        """Verify SYSTEM_PROMPT constant is defined."""
        assert SYSTEM_PROMPT is not None
        assert isinstance(SYSTEM_PROMPT, str)
        assert len(SYSTEM_PROMPT) > 50

    def test_system_prompt_contains_conciseness_instruction(self):
        """Verify system prompt instructs for concise responses."""
        assert "concise" in SYSTEM_PROMPT.lower() or "2-3 sentences" in SYSTEM_PROMPT

    def test_system_prompt_contains_answer_first_instruction(self):
        """Verify system prompt instructs to lead with answer."""
        assert "lead with" in SYSTEM_PROMPT.lower() or "direct answer" in SYSTEM_PROMPT.lower()

    def test_system_prompt_contains_bullet_point_instruction(self):
        """Verify system prompt mentions bullet points for lists."""
        assert "bullet" in SYSTEM_PROMPT.lower()


class TestDynamicMaxTokens:
    """Tests for dynamic max_tokens estimation."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock LLM client."""
        with patch('src.agent.llm_client.Anthropic'):
            from src.shared.config import Config, LLMConfig
            from src.agent.tool_registry import ToolRegistry

            config = Config(
                anthropic_api_key="test_key",
                llm=LLMConfig()
            )
            registry = Mock(spec=ToolRegistry)
            registry.get_tool_definitions.return_value = []

            client = ClaudeLLMClient(config, registry)
            return client

    def test_simple_factual_query_low_tokens(self, mock_client):
        """'What is X' queries get 512 max_tokens."""
        if mock_client is None:
            pytest.skip("ClaudeLLMClient not available")

        tokens = mock_client._estimate_response_tokens("What is the capital of France?")
        assert tokens == 512

    def test_who_is_query_low_tokens(self, mock_client):
        """'Who is X' queries get 512 max_tokens."""
        if mock_client is None:
            pytest.skip("ClaudeLLMClient not available")

        tokens = mock_client._estimate_response_tokens("Who is the president of the USA?")
        assert tokens == 512

    def test_when_did_query_low_tokens(self, mock_client):
        """'When did X' queries get 512 max_tokens."""
        if mock_client is None:
            pytest.skip("ClaudeLLMClient not available")

        tokens = mock_client._estimate_response_tokens("When did World War 2 end?")
        assert tokens == 512

    def test_where_is_query_low_tokens(self, mock_client):
        """'Where is X' queries get 512 max_tokens."""
        if mock_client is None:
            pytest.skip("ClaudeLLMClient not available")

        tokens = mock_client._estimate_response_tokens("Where is the Eiffel Tower?")
        assert tokens == 512

    def test_compare_query_medium_tokens(self, mock_client):
        """'Compare X and Y' queries get 1024 max_tokens."""
        if mock_client is None:
            pytest.skip("ClaudeLLMClient not available")

        tokens = mock_client._estimate_response_tokens("Compare Python and JavaScript")
        assert tokens == 1024

    def test_explain_query_medium_tokens(self, mock_client):
        """'Explain X' queries get 1024 max_tokens."""
        if mock_client is None:
            pytest.skip("ClaudeLLMClient not available")

        tokens = mock_client._estimate_response_tokens("Explain how photosynthesis works")
        assert tokens == 1024

    def test_why_query_medium_tokens(self, mock_client):
        """'Why X' queries get 1024 max_tokens."""
        if mock_client is None:
            pytest.skip("ClaudeLLMClient not available")

        tokens = mock_client._estimate_response_tokens("Why is the sky blue?")
        assert tokens == 1024

    def test_how_does_query_medium_tokens(self, mock_client):
        """'How does X' queries get 1024 max_tokens."""
        if mock_client is None:
            pytest.skip("ClaudeLLMClient not available")

        tokens = mock_client._estimate_response_tokens("How does a car engine work?")
        assert tokens == 1024

    def test_complex_query_with_and_high_tokens(self, mock_client):
        """Queries with 'and' get 2048 max_tokens (when not matching other patterns first)."""
        if mock_client is None:
            pytest.skip("ClaudeLLMClient not available")

        # Use a query that doesn't match simpler patterns but has "and"
        tokens = mock_client._estimate_response_tokens("Tell me about Paris and London and Rome")
        assert tokens == 2048

    def test_long_query_high_tokens(self, mock_client):
        """Queries longer than 200 chars get 2048 max_tokens."""
        if mock_client is None:
            pytest.skip("ClaudeLLMClient not available")

        long_query = "a" * 201
        tokens = mock_client._estimate_response_tokens(long_query)
        assert tokens == 2048

    def test_default_tokens_for_ambiguous_query(self, mock_client):
        """Ambiguous queries default to 1024."""
        if mock_client is None:
            pytest.skip("ClaudeLLMClient not available")

        tokens = mock_client._estimate_response_tokens("Tell me something interesting")
        assert tokens == 1024

    def test_case_insensitive_matching(self, mock_client):
        """Query matching should be case insensitive."""
        if mock_client is None:
            pytest.skip("ClaudeLLMClient not available")

        tokens_lower = mock_client._estimate_response_tokens("what is the capital of france?")
        tokens_upper = mock_client._estimate_response_tokens("WHAT IS THE CAPITAL OF FRANCE?")
        assert tokens_lower == tokens_upper == 512
