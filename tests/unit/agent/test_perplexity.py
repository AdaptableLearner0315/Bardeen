"""Tests for Perplexity tool."""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock

# Import will work after module is created
try:
    from src.agent.tools.perplexity import PerplexityTool, create_perplexity_tool
except ImportError:
    PerplexityTool = None
    create_perplexity_tool = None


class TestPerplexityTool:
    """Tests for PerplexityTool class."""

    @pytest.fixture
    def mock_openai(self):
        """Mock OpenAI client."""
        with patch('src.agent.tools.perplexity.OpenAI') as mock:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Test answer with citations"
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 50
            mock_client.chat.completions.create.return_value = mock_response
            mock.return_value = mock_client
            yield mock

    @pytest.fixture
    def tool_with_key(self, mock_openai):
        """Create tool with API key."""
        if PerplexityTool is None:
            pytest.skip("PerplexityTool not available")
        return PerplexityTool(api_key="test_key")

    def test_tool_initialization_with_key(self, tool_with_key):
        """Test tool initializes with API key."""
        assert tool_with_key.is_available is True
        assert tool_with_key.api_key == "test_key"

    def test_tool_initialization_without_key(self):
        """Test tool unavailable without API key."""
        if PerplexityTool is None:
            pytest.skip("PerplexityTool not available")

        with patch.dict(os.environ, {}, clear=True):
            # Remove any existing key
            os.environ.pop("PERPLEXITY_API_KEY", None)
            tool = PerplexityTool(api_key=None)
            assert tool.is_available is False

    def test_tool_name(self, tool_with_key):
        """Test tool name is set correctly."""
        assert tool_with_key.TOOL_NAME == "perplexity_search"

    def test_models_defined(self, tool_with_key):
        """Test models are defined."""
        assert "normal" in tool_with_key.MODELS
        assert "deep" in tool_with_key.MODELS
        assert tool_with_key.MODELS["normal"] == "sonar"
        assert tool_with_key.MODELS["deep"] == "sonar-pro"

    def test_search_normal_mode(self, tool_with_key, mock_openai):
        """Test search in normal mode uses sonar model."""
        result = tool_with_key.search("What is Python?", deep=False)

        assert result["success"] is True
        assert result["model"] == "sonar"
        assert result["answer"] == "Test answer with citations"

    def test_search_deep_mode(self, tool_with_key, mock_openai):
        """Test search in deep mode uses sonar-pro model."""
        result = tool_with_key.search("Analyze Tesla financials", deep=True)

        assert result["success"] is True
        assert result["model"] == "sonar-pro"

    def test_search_returns_usage(self, tool_with_key, mock_openai):
        """Test search returns token usage."""
        result = tool_with_key.search("Test query")

        assert "usage" in result
        assert result["usage"]["prompt_tokens"] == 100
        assert result["usage"]["completion_tokens"] == 50

    def test_search_handles_error(self, tool_with_key, mock_openai):
        """Test search handles API errors gracefully."""
        mock_openai.return_value.chat.completions.create.side_effect = Exception("API Error")

        result = tool_with_key.search("Test query")

        assert result["success"] is False
        assert "API Error" in result["error"]

    def test_tool_callable(self, tool_with_key, mock_openai):
        """Test tool is callable directly."""
        result = tool_with_key("Test query", deep=False)

        assert result["success"] is True

    def test_get_tool_definition(self, tool_with_key):
        """Test tool definition is valid."""
        definition = tool_with_key.get_tool_definition()

        assert definition["name"] == "perplexity_search"
        assert "description" in definition
        assert "input_schema" in definition
        assert definition["input_schema"]["type"] == "object"
        assert "query" in definition["input_schema"]["properties"]
        assert "deep" in definition["input_schema"]["properties"]

    def test_unavailable_tool_returns_error(self):
        """Test unavailable tool returns error on search."""
        if PerplexityTool is None:
            pytest.skip("PerplexityTool not available")

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("PERPLEXITY_API_KEY", None)
            tool = PerplexityTool(api_key=None)
            result = tool.search("Test query")

            assert result["success"] is False
            assert "not available" in result["error"]


class TestCreatePerplexityTool:
    """Tests for factory function."""

    def test_create_with_valid_key(self):
        """Test factory creates tool with valid key."""
        if create_perplexity_tool is None:
            pytest.skip("create_perplexity_tool not available")

        with patch('src.agent.tools.perplexity.OpenAI'):
            tool = create_perplexity_tool(api_key="test_key")
            assert tool is not None
            assert tool.is_available is True

    def test_create_without_key_returns_none(self):
        """Test factory returns None without key."""
        if create_perplexity_tool is None:
            pytest.skip("create_perplexity_tool not available")

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("PERPLEXITY_API_KEY", None)
            tool = create_perplexity_tool(api_key=None)
            assert tool is None
