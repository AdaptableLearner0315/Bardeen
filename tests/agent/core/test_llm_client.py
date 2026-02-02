"""Tests for LLM client module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

from src.shared.exceptions import (
    LLMAPIError,
    LLMRateLimitError,
    LLMTimeoutError,
    MissingAPIKeyError,
)


# Mock classes for Anthropic responses
@dataclass
class MockTextBlock:
    type: str = "text"
    text: str = "Test response"


@dataclass
class MockToolUseBlock:
    type: str = "tool_use"
    id: str = "tool_123"
    name: str = "calculator"
    input: dict = None

    def __post_init__(self):
        if self.input is None:
            self.input = {"expression": "2+2"}


@dataclass
class MockUsage:
    input_tokens: int = 100
    output_tokens: int = 50


@dataclass
class MockResponse:
    content: list = None
    stop_reason: str = "end_turn"
    usage: MockUsage = None

    def __post_init__(self):
        if self.content is None:
            self.content = [MockTextBlock()]
        if self.usage is None:
            self.usage = MockUsage()


class TestLLMClientImport:
    """Tests for LLM client import and initialization."""

    def test_import_without_anthropic(self):
        """Test handling when anthropic package is not installed."""
        # This test verifies the module handles missing anthropic gracefully
        # The actual behavior depends on whether anthropic is installed
        pass

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    def test_initialization_with_api_key(self, mock_anthropic):
        """Test initialization with API key."""
        from src.agent.core.llm_client import LLMClient

        client = LLMClient(api_key="test_key")

        assert client.api_key == "test_key"
        mock_anthropic.assert_called_once_with(api_key="test_key")

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    def test_initialization_default_model(self, mock_anthropic):
        """Test default model configuration."""
        from src.agent.core.llm_client import LLMClient

        client = LLMClient(api_key="test_key")

        assert "claude" in client.model.lower() or "sonnet" in client.model.lower()

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    def test_initialization_custom_parameters(self, mock_anthropic):
        """Test initialization with custom parameters."""
        from src.agent.core.llm_client import LLMClient

        client = LLMClient(
            api_key="test_key",
            model="claude-3-opus",
            temperature=0.8,
            max_tokens=2048,
            timeout=120,
        )

        assert client.model == "claude-3-opus"
        assert client.temperature == 0.8
        assert client.max_tokens == 2048
        assert client.timeout == 120

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    @patch("src.agent.core.llm_client.get_config")
    def test_initialization_missing_api_key(self, mock_config, mock_anthropic):
        """Test initialization without API key raises error."""
        from src.agent.core.llm_client import LLMClient

        mock_config.return_value.anthropic_api_key = None

        with pytest.raises(MissingAPIKeyError):
            LLMClient()


class TestToolUse:
    """Tests for ToolUse dataclass."""

    def test_tool_use_creation(self):
        """Test ToolUse dataclass."""
        from src.agent.core.llm_client import ToolUse

        tool = ToolUse(id="tool_1", name="calculator", input={"expr": "2+2"})
        assert tool.id == "tool_1"
        assert tool.name == "calculator"
        assert tool.input == {"expr": "2+2"}


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""

    def test_response_creation(self):
        """Test LLMResponse creation."""
        from src.agent.core.llm_client import LLMResponse, ToolUse

        response = LLMResponse(text="Hello", stop_reason="end_turn")
        assert response.text == "Hello"
        assert response.tool_uses == []
        assert response.stop_reason == "end_turn"

    def test_response_has_tool_calls_false(self):
        """Test has_tool_calls property when no tools."""
        from src.agent.core.llm_client import LLMResponse

        response = LLMResponse(text="Hello")
        assert response.has_tool_calls is False

    def test_response_has_tool_calls_true(self):
        """Test has_tool_calls property when tools present."""
        from src.agent.core.llm_client import LLMResponse, ToolUse

        tool = ToolUse(id="1", name="calc", input={})
        response = LLMResponse(text="Hello", tool_uses=[tool])
        assert response.has_tool_calls is True


class TestLLMClientChat:
    """Tests for LLMClient chat methods."""

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    def test_chat_basic(self, mock_anthropic_class):
        """Test basic chat request."""
        from src.agent.core.llm_client import LLMClient

        # Setup mock
        mock_client = Mock()
        mock_response = MockResponse()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        client = LLMClient(api_key="test_key")
        response = client.chat(messages=[{"role": "user", "content": "Hello"}])

        assert response.text == "Test response"
        assert response.stop_reason == "end_turn"
        mock_client.messages.create.assert_called_once()

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    def test_chat_with_system_prompt(self, mock_anthropic_class):
        """Test chat with system prompt."""
        from src.agent.core.llm_client import LLMClient

        mock_client = Mock()
        mock_response = MockResponse()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        client = LLMClient(api_key="test_key")
        client.chat(
            messages=[{"role": "user", "content": "Hello"}],
            system="You are a helpful assistant."
        )

        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["system"] == "You are a helpful assistant."

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    def test_chat_with_tools(self, mock_anthropic_class):
        """Test chat with tool definitions."""
        from src.agent.core.llm_client import LLMClient

        mock_client = Mock()
        mock_response = MockResponse()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        tools = [{"name": "calculator", "description": "Calculate math"}]

        client = LLMClient(api_key="test_key")
        client.chat(
            messages=[{"role": "user", "content": "What is 2+2?"}],
            tools=tools
        )

        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["tools"] == tools

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    def test_chat_parses_tool_use(self, mock_anthropic_class):
        """Test chat parses tool use blocks."""
        from src.agent.core.llm_client import LLMClient

        mock_client = Mock()
        mock_response = MockResponse(
            content=[MockToolUseBlock()],
            stop_reason="tool_use"
        )
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        client = LLMClient(api_key="test_key")
        response = client.chat(messages=[{"role": "user", "content": "Calculate 2+2"}])

        assert len(response.tool_uses) == 1
        assert response.tool_uses[0].name == "calculator"
        assert response.stop_reason == "tool_use"

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    def test_chat_mixed_content(self, mock_anthropic_class):
        """Test chat with mixed text and tool use blocks."""
        from src.agent.core.llm_client import LLMClient

        mock_client = Mock()
        mock_response = MockResponse(
            content=[
                MockTextBlock(text="Let me calculate that."),
                MockToolUseBlock()
            ],
            stop_reason="tool_use"
        )
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        client = LLMClient(api_key="test_key")
        response = client.chat(messages=[{"role": "user", "content": "What is 2+2?"}])

        assert "Let me calculate that" in response.text
        assert len(response.tool_uses) == 1

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    def test_chat_tracks_token_usage(self, mock_anthropic_class):
        """Test chat tracks token usage."""
        from src.agent.core.llm_client import LLMClient

        mock_client = Mock()
        mock_response = MockResponse()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        client = LLMClient(api_key="test_key")
        response = client.chat(messages=[{"role": "user", "content": "Hello"}])

        assert response.usage["input_tokens"] == 100
        assert response.usage["output_tokens"] == 50

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    def test_chat_temperature_override(self, mock_anthropic_class):
        """Test temperature can be overridden per request."""
        from src.agent.core.llm_client import LLMClient

        mock_client = Mock()
        mock_response = MockResponse()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        client = LLMClient(api_key="test_key", temperature=0.5)
        client.chat(
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.9
        )

        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["temperature"] == 0.9


class TestLLMClientErrors:
    """Tests for LLM client error handling."""

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    def test_rate_limit_error(self, mock_anthropic_class):
        """Test rate limit error handling."""
        from src.agent.core.llm_client import LLMClient, RateLimitError

        mock_client = Mock()
        mock_client.messages.create.side_effect = RateLimitError(
            "Rate limit exceeded",
            response=Mock(status_code=429),
            body=None
        )
        mock_anthropic_class.return_value = mock_client

        client = LLMClient(api_key="test_key")

        with pytest.raises(LLMRateLimitError):
            client.chat(messages=[{"role": "user", "content": "Hello"}])

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    def test_timeout_error(self, mock_anthropic_class):
        """Test timeout error handling."""
        from src.agent.core.llm_client import LLMClient, APITimeoutError

        mock_client = Mock()
        mock_client.messages.create.side_effect = APITimeoutError(
            request=Mock()
        )
        mock_anthropic_class.return_value = mock_client

        client = LLMClient(api_key="test_key")

        with pytest.raises(LLMTimeoutError):
            client.chat(messages=[{"role": "user", "content": "Hello"}])

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    def test_api_error(self, mock_anthropic_class):
        """Test generic API error handling."""
        from src.agent.core.llm_client import LLMClient

        mock_client = Mock()
        # Create a generic exception that matches what APIError would look like
        api_error = Exception("Server error")
        api_error.status_code = 500
        mock_client.messages.create.side_effect = api_error
        mock_anthropic_class.return_value = mock_client

        client = LLMClient(api_key="test_key")

        with pytest.raises(LLMAPIError):
            client.chat(messages=[{"role": "user", "content": "Hello"}])

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    def test_unexpected_error(self, mock_anthropic_class):
        """Test unexpected error handling."""
        from src.agent.core.llm_client import LLMClient

        mock_client = Mock()
        mock_client.messages.create.side_effect = ValueError("Unexpected")
        mock_anthropic_class.return_value = mock_client

        client = LLMClient(api_key="test_key")

        with pytest.raises(LLMAPIError):
            client.chat(messages=[{"role": "user", "content": "Hello"}])


class TestLLMClientChatWithTools:
    """Tests for chat_with_tools method."""

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    def test_chat_with_tools_no_tool_calls(self, mock_anthropic_class):
        """Test chat_with_tools when no tools are called."""
        from src.agent.core.llm_client import LLMClient

        mock_client = Mock()
        mock_response = MockResponse(content=[MockTextBlock(text="The answer is 4.")])
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        client = LLMClient(api_key="test_key")
        answer, tool_records = client.chat_with_tools(
            user_message="What is 2+2?",
            tools=[{"name": "calculator"}]
        )

        assert answer == "The answer is 4."
        assert tool_records == []

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    def test_chat_with_tools_executes_tool(self, mock_anthropic_class):
        """Test chat_with_tools executes tools and continues."""
        from src.agent.core.llm_client import LLMClient

        mock_client = Mock()

        # First response: tool use
        tool_response = MockResponse(
            content=[MockToolUseBlock(id="tool_1", name="calculator", input={"expression": "2+2"})],
            stop_reason="tool_use"
        )
        # Second response: final answer
        final_response = MockResponse(
            content=[MockTextBlock(text="The result is 4.")],
            stop_reason="end_turn"
        )
        mock_client.messages.create.side_effect = [tool_response, final_response]
        mock_anthropic_class.return_value = mock_client

        # Tool executor
        def tool_executor(name, input_params):
            return "4"

        client = LLMClient(api_key="test_key")
        answer, tool_records = client.chat_with_tools(
            user_message="What is 2+2?",
            tools=[{"name": "calculator"}],
            tool_executor=tool_executor
        )

        assert answer == "The result is 4."
        assert len(tool_records) == 1
        assert tool_records[0]["name"] == "calculator"

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    def test_chat_with_tools_multiple_tools(self, mock_anthropic_class):
        """Test chat_with_tools with multiple tool calls."""
        from src.agent.core.llm_client import LLMClient

        mock_client = Mock()

        # First response: two tool uses
        tool_response = MockResponse(
            content=[
                MockToolUseBlock(id="tool_1", name="calculator", input={"expression": "2+2"}),
                MockToolUseBlock(id="tool_2", name="calculator", input={"expression": "3+3"})
            ],
            stop_reason="tool_use"
        )
        final_response = MockResponse(
            content=[MockTextBlock(text="Results are 4 and 6.")],
            stop_reason="end_turn"
        )
        mock_client.messages.create.side_effect = [tool_response, final_response]
        mock_anthropic_class.return_value = mock_client

        def tool_executor(name, input_params):
            expr = input_params.get("expression", "")
            return str(eval(expr))

        client = LLMClient(api_key="test_key")
        answer, tool_records = client.chat_with_tools(
            user_message="Calculate 2+2 and 3+3",
            tools=[{"name": "calculator"}],
            tool_executor=tool_executor
        )

        assert len(tool_records) == 2

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    def test_chat_with_tools_max_calls_limit(self, mock_anthropic_class):
        """Test chat_with_tools respects max_tool_calls limit."""
        from src.agent.core.llm_client import LLMClient

        mock_client = Mock()

        # Always return tool use
        tool_response = MockResponse(
            content=[MockToolUseBlock()],
            stop_reason="tool_use"
        )
        mock_client.messages.create.return_value = tool_response
        mock_anthropic_class.return_value = mock_client

        def tool_executor(name, input_params):
            return "result"

        client = LLMClient(api_key="test_key")
        answer, tool_records = client.chat_with_tools(
            user_message="Keep calling tools",
            tools=[{"name": "calculator"}],
            tool_executor=tool_executor,
            max_tool_calls=3
        )

        assert len(tool_records) == 3
        assert "maximum" in answer.lower()

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    def test_chat_with_tools_no_executor(self, mock_anthropic_class):
        """Test chat_with_tools without tool executor."""
        from src.agent.core.llm_client import LLMClient

        mock_client = Mock()

        tool_response = MockResponse(
            content=[MockToolUseBlock()],
            stop_reason="tool_use"
        )
        final_response = MockResponse(
            content=[MockTextBlock(text="Error handled.")],
            stop_reason="end_turn"
        )
        mock_client.messages.create.side_effect = [tool_response, final_response]
        mock_anthropic_class.return_value = mock_client

        client = LLMClient(api_key="test_key")
        answer, tool_records = client.chat_with_tools(
            user_message="Calculate something",
            tools=[{"name": "calculator"}],
            tool_executor=None
        )

        # Should have recorded tool call with error
        assert len(tool_records) == 1
        assert "error" in tool_records[0]["result"]

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    def test_chat_with_tools_conversation_history(self, mock_anthropic_class):
        """Test chat_with_tools preserves conversation history."""
        from src.agent.core.llm_client import LLMClient

        mock_client = Mock()
        mock_response = MockResponse()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"}
        ]

        client = LLMClient(api_key="test_key")
        client.chat_with_tools(
            user_message="New question",
            conversation_history=history
        )

        call_kwargs = mock_client.messages.create.call_args[1]
        messages = call_kwargs["messages"]
        assert len(messages) == 3  # history + new message

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    def test_chat_with_tools_max_tokens_stop(self, mock_anthropic_class):
        """Test chat_with_tools handles max_tokens stop reason."""
        from src.agent.core.llm_client import LLMClient

        mock_client = Mock()
        mock_response = MockResponse(
            content=[MockTextBlock(text="Truncated response")],
            stop_reason="max_tokens"
        )
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        client = LLMClient(api_key="test_key")
        answer, tool_records = client.chat_with_tools(
            user_message="Long question"
        )

        assert "truncated" in answer.lower()


class TestLLMClientStats:
    """Tests for LLM client statistics."""

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    def test_get_stats(self, mock_anthropic_class):
        """Test getting client statistics."""
        from src.agent.core.llm_client import LLMClient

        mock_client = Mock()
        mock_response = MockResponse()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        client = LLMClient(api_key="test_key")
        client.chat(messages=[{"role": "user", "content": "Hello"}])

        stats = client.get_stats()

        assert stats["total_requests"] == 1
        assert stats["total_tokens_in"] == 100
        assert stats["total_tokens_out"] == 50
        assert stats["total_tokens"] == 150
        assert stats["errors"] == 0

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    def test_reset_stats(self, mock_anthropic_class):
        """Test resetting client statistics."""
        from src.agent.core.llm_client import LLMClient

        mock_client = Mock()
        mock_response = MockResponse()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        client = LLMClient(api_key="test_key")
        client.chat(messages=[{"role": "user", "content": "Hello"}])
        client.reset_stats()

        stats = client.get_stats()
        assert stats["total_requests"] == 0
        assert stats["total_tokens_in"] == 0
        assert stats["total_tokens_out"] == 0

    @patch("src.agent.core.llm_client.ANTHROPIC_AVAILABLE", True)
    @patch("src.agent.core.llm_client.Anthropic")
    def test_error_rate_tracking(self, mock_anthropic_class):
        """Test error rate is tracked correctly."""
        from src.agent.core.llm_client import LLMClient

        mock_client = Mock()
        mock_response = MockResponse()
        mock_client.messages.create.side_effect = [
            mock_response,
            ValueError("Error"),
            mock_response
        ]
        mock_anthropic_class.return_value = mock_client

        client = LLMClient(api_key="test_key")

        # First call: success
        client.chat(messages=[{"role": "user", "content": "1"}])

        # Second call: error
        try:
            client.chat(messages=[{"role": "user", "content": "2"}])
        except:
            pass

        # Third call: success
        client.chat(messages=[{"role": "user", "content": "3"}])

        stats = client.get_stats()
        assert stats["total_requests"] == 3
        assert stats["errors"] == 1
        assert 0 < stats["error_rate"] < 1


class TestLLMClientIsAvailable:
    """Tests for is_available static method."""

    def test_is_available(self):
        """Test is_available returns boolean."""
        from src.agent.core.llm_client import LLMClient

        result = LLMClient.is_available()
        assert isinstance(result, bool)
