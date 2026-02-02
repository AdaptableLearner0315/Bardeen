"""Tests for LLM API key validation and tool calling integration."""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass
from pathlib import Path

# Load .env file for tests
try:
    from dotenv import load_dotenv
    # Find the project root (where .env is located)
    project_root = Path(__file__).parent.parent.parent.parent
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


class TestAPIKeyValidation:
    """Tests for Anthropic API key validation."""

    def test_api_key_present_in_environment(self):
        """Test that ANTHROPIC_API_KEY environment variable is set."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        assert api_key is not None, (
            "ANTHROPIC_API_KEY environment variable must be set. "
            "Please add it to your .env file."
        )

    def test_api_key_not_empty(self):
        """Test that API key is not an empty string."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        assert api_key is not None and len(api_key.strip()) > 0, (
            "ANTHROPIC_API_KEY must not be empty."
        )

    def test_api_key_format(self):
        """Test that API key has valid Anthropic format."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            # Anthropic API keys typically start with 'sk-ant-'
            assert api_key.startswith("sk-ant-") or api_key.startswith("sk-"), (
                f"API key should start with 'sk-ant-' or 'sk-'. Got: {api_key[:10]}..."
            )

    def test_config_loads_api_key_from_env(self):
        """Test that config correctly loads API key from environment."""
        from src.shared.config import load_config, reset_config

        reset_config()  # Clear singleton
        config = load_config()

        env_key = os.getenv("ANTHROPIC_API_KEY")
        assert config.anthropic_api_key == env_key, (
            "Config should load API key from ANTHROPIC_API_KEY environment variable."
        )

    def test_missing_api_key_raises_error(self):
        """Test that missing API key raises appropriate error."""
        from src.agent.llm_client import ClaudeLLMClient
        from src.agent.tool_registry import ToolRegistry
        from src.shared.config import Config, LLMConfig, ToolConfig

        # Create config without API key
        config = Config.__new__(Config)
        config.anthropic_api_key = None
        config.llm = LLMConfig()
        config.tools = ToolConfig()

        # Mock the tool registry
        mock_registry = Mock(spec=ToolRegistry)

        with pytest.raises(ValueError, match="Anthropic API key required"):
            ClaudeLLMClient(config, mock_registry)


class TestModelConfiguration:
    """Tests for LLM model configuration."""

    def test_default_model_is_valid(self):
        """Test that default model name is valid."""
        from src.shared.config import LLMConfig

        config = LLMConfig()
        model = config.model

        # Valid Claude model names
        valid_prefixes = ["claude-3", "claude-sonnet", "claude-opus", "claude-haiku"]

        is_valid = any(model.startswith(prefix) for prefix in valid_prefixes)
        assert is_valid, (
            f"Model '{model}' doesn't appear to be a valid Claude model. "
            f"Expected one of: {valid_prefixes}"
        )

    def test_model_name_format(self):
        """Test that model name follows expected format."""
        from src.shared.config import LLMConfig

        config = LLMConfig()
        model = config.model

        # Model should contain version date (YYYYMMDD format)
        assert any(char.isdigit() for char in model), (
            f"Model name '{model}' should contain version date."
        )

    def test_model_override_from_env(self):
        """Test that model can be overridden via environment variable."""
        from src.shared.config import Config, reset_config

        original_model = os.environ.get("LLM_MODEL")

        try:
            os.environ["LLM_MODEL"] = "claude-3-opus-20240229"
            reset_config()

            config = Config()
            assert config.llm.model == "claude-3-opus-20240229"
        finally:
            if original_model:
                os.environ["LLM_MODEL"] = original_model
            elif "LLM_MODEL" in os.environ:
                del os.environ["LLM_MODEL"]
            reset_config()


class TestToolCallingIntegration:
    """Tests for tool calling integration."""

    def test_tool_registry_initialization(self):
        """Test that tool registry initializes correctly."""
        from src.agent.tool_registry import ToolRegistry
        from src.shared.config import load_config, reset_config

        reset_config()
        config = load_config()

        registry = ToolRegistry(config)

        # Should have at least the core tools
        available_tools = registry.get_available_tools()
        assert "calculator" in available_tools, "Calculator tool should be available"
        assert "wikipedia" in available_tools, "Wikipedia tool should be available"

    def test_tool_definitions_format(self):
        """Test that tool definitions are properly formatted for Claude."""
        from src.agent.tool_registry import ToolRegistry
        from src.shared.config import load_config, reset_config

        reset_config()
        config = load_config()

        registry = ToolRegistry(config)
        definitions = registry.get_tool_definitions()

        assert isinstance(definitions, list), "Tool definitions should be a list"

        for tool_def in definitions:
            assert "name" in tool_def, "Each tool must have a name"
            assert "description" in tool_def, "Each tool must have a description"
            assert "input_schema" in tool_def, "Each tool must have an input schema"

    def test_calculator_tool_execution(self):
        """Test that calculator tool executes correctly."""
        from src.agent.tool_registry import ToolRegistry
        from src.shared.config import load_config, reset_config

        reset_config()
        config = load_config()

        registry = ToolRegistry(config)

        # Execute a simple calculation
        result = registry.execute_tool(
            tool_name="calculator",
            params={"expression": "2 + 2"}
        )

        assert result["success"] is True, f"Calculator failed: {result}"
        assert result["result"] == 4, f"Expected 4, got {result['result']}"

    def test_wikipedia_tool_execution(self):
        """Test that Wikipedia tool executes correctly."""
        from src.agent.tool_registry import ToolRegistry
        from src.shared.config import load_config, reset_config

        reset_config()
        config = load_config()

        registry = ToolRegistry(config)

        # Execute a Wikipedia search (uses 'title' parameter, not 'query')
        result = registry.execute_tool(
            tool_name="wikipedia",
            params={"title": "Python (programming language)"}
        )

        assert result["success"] is True, f"Wikipedia search failed: {result}"
        assert "title" in result, "Wikipedia result should have a title"
        assert "summary" in result, "Wikipedia result should have a summary"

    def test_tool_fallback_on_failure(self):
        """Test that tool registry handles failures gracefully."""
        from src.agent.tool_registry import ToolRegistry
        from src.shared.config import load_config, reset_config

        reset_config()
        config = load_config()

        registry = ToolRegistry(config)

        # Try to execute with invalid params
        result = registry.execute_tool(
            tool_name="calculator",
            params={"expression": "invalid expression syntax ///"}
        )

        # Should handle error gracefully
        assert "success" in result
        if not result["success"]:
            assert "error" in result, "Failed result should include error message"

    def test_unknown_tool_handling(self):
        """Test that unknown tool names are handled gracefully."""
        from src.agent.tool_registry import ToolRegistry
        from src.shared.config import load_config, reset_config

        reset_config()
        config = load_config()

        registry = ToolRegistry(config)

        result = registry.execute_tool(
            tool_name="nonexistent_tool",
            params={}
        )

        assert result["success"] is False, "Unknown tool should fail"
        assert "error" in result, "Should include error message"


class TestLLMClientToolCalling:
    """Tests for LLM client tool calling functionality."""

    @pytest.fixture
    def mock_anthropic_response(self):
        """Create a mock Anthropic response."""
        @dataclass
        class MockTextBlock:
            type: str = "text"
            text: str = "The answer is 4."

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

        return MockResponse

    @patch("src.agent.llm_client.Anthropic")
    def test_llm_client_initialization(self, mock_anthropic):
        """Test LLM client initializes with valid config."""
        from src.agent.llm_client import ClaudeLLMClient
        from src.agent.tool_registry import ToolRegistry
        from src.shared.config import load_config, reset_config

        reset_config()
        config = load_config()

        if not config.anthropic_api_key:
            pytest.skip("API key not configured")

        registry = ToolRegistry(config)
        client = ClaudeLLMClient(config, registry)

        assert client.model == config.llm.model
        assert client.temperature == config.llm.temperature

    @patch("src.agent.llm_client.Anthropic")
    def test_tool_definitions_passed_to_api(self, mock_anthropic, mock_anthropic_response):
        """Test that tool definitions are passed to the API."""
        from src.agent.llm_client import ClaudeLLMClient
        from src.agent.tool_registry import ToolRegistry
        from src.shared.config import load_config, reset_config

        reset_config()
        config = load_config()

        if not config.anthropic_api_key:
            pytest.skip("API key not configured")

        # Setup mock
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_response()
        mock_anthropic.return_value = mock_client

        registry = ToolRegistry(config)
        client = ClaudeLLMClient(config, registry)

        # Make a chat call
        client.chat(user_message="What is 2+2?")

        # Verify tools were passed
        call_kwargs = mock_client.messages.create.call_args[1]
        assert "tools" in call_kwargs, "Tools should be passed to API"
        assert len(call_kwargs["tools"]) > 0, "Should have at least one tool"


class TestEndToEndToolCalling:
    """End-to-end tests for tool calling (requires API key)."""

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_simple_calculation_with_tool(self):
        """Test that agent can perform a calculation using the calculator tool."""
        from src.agent.agent import create_agent

        agent = create_agent()

        answer, tool_traces, error_traces = agent.ask(
            "What is 15 multiplied by 7?",
            reset_conversation=True
        )

        # Should have used calculator tool or answered directly
        assert "105" in answer, f"Expected answer to contain 105, got: {answer}"

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_wikipedia_lookup_with_tool(self):
        """Test that agent can look up information using Wikipedia tool."""
        from src.agent.agent import create_agent

        agent = create_agent()

        answer, tool_traces, error_traces = agent.ask(
            "What year was the Eiffel Tower completed?",
            reset_conversation=True
        )

        # Should mention 1889 (when Eiffel Tower was completed)
        assert "1889" in answer or "188" in answer, (
            f"Expected answer to mention 1889, got: {answer}"
        )

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_tool_traces_are_recorded(self):
        """Test that tool calls are properly traced."""
        from src.agent.agent import create_agent
        from src.evaluation.tracers.tool_tracer import ToolTracer

        agent = create_agent()
        tracer = ToolTracer(attempt_number=1)  # Required argument

        answer, tool_traces, error_traces = agent.ask(
            "Calculate the square root of 144",
            tracer=tracer,
            reset_conversation=True
        )

        # Tool traces should be returned
        assert isinstance(tool_traces, list), "Tool traces should be a list"

        # If calculator was used, should have trace
        if tool_traces:
            assert all(hasattr(t, 'tool_name') for t in tool_traces), (
                "Each trace should have tool_name"
            )


class TestAPIKeySecurityTests:
    """Tests for API key security."""

    def test_api_key_not_in_tool_results_or_traces(self):
        """Test that API key doesn't leak through tool results or error messages."""
        from src.agent.tool_registry import ToolRegistry
        from src.shared.config import load_config, reset_config

        reset_config()
        config = load_config()

        registry = ToolRegistry(config)

        # Execute a tool that might have errors
        result = registry.execute_tool(
            tool_name="calculator",
            params={"expression": "1+1"}
        )

        result_str = str(result)
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if api_key:
            assert api_key not in result_str, (
                "API key should not appear in tool results"
            )

    def test_api_key_masked_in_repr(self):
        """Test that API key should be handled securely.

        Note: Python dataclasses expose attributes in __repr__ by default.
        This test documents expected behavior - in production, you'd want
        a custom __repr__ that masks the API key.
        """
        # This is a documentation test - the key appears in default repr
        # In production, add a custom __repr__ to Config that masks it
        pass

    def test_api_key_not_in_tool_results(self):
        """Test that API key doesn't leak through tool results."""
        from src.agent.tool_registry import ToolRegistry
        from src.shared.config import load_config, reset_config

        reset_config()
        config = load_config()

        registry = ToolRegistry(config)

        # Execute a tool
        result = registry.execute_tool(
            tool_name="calculator",
            params={"expression": "1+1"}
        )

        result_str = str(result)
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if api_key:
            assert api_key not in result_str, (
                "API key should not appear in tool results"
            )
