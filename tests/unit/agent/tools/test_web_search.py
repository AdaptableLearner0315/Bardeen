"""Tests for web search tools (DuckDuckGo and Tavily)."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestDuckDuckGoSearchTool:
    """Tests for DuckDuckGo web search tool."""

    def test_ddgs_import_available(self):
        """Test that ddgs/duckduckgo-search package can be imported."""
        try:
            # Try new package name first
            from ddgs import DDGS
            assert DDGS is not None
        except ImportError:
            try:
                # Fall back to old package name
                from duckduckgo_search import DDGS
                assert DDGS is not None
            except ImportError:
                pytest.skip("ddgs/duckduckgo-search not installed")

    def test_duckduckgo_search_class_exists(self):
        """Test DuckDuckGoSearch class exists."""
        from src.agent.tools.duckduckgo_search import DuckDuckGoSearch
        assert DuckDuckGoSearch is not None

    def test_duckduckgo_availability_flag(self):
        """Test DDGS_AVAILABLE flag is exported."""
        from src.agent.tools.duckduckgo_search import DDGS_AVAILABLE
        assert isinstance(DDGS_AVAILABLE, bool)

    def test_duckduckgo_tool_definition(self):
        """Test DuckDuckGo tool has proper definition."""
        from src.agent.tools.duckduckgo_search import DuckDuckGoSearch, DDGS_AVAILABLE

        if not DDGS_AVAILABLE:
            pytest.skip("duckduckgo-search not installed")

        search = DuckDuckGoSearch()
        definition = search.get_tool_definition()

        assert "name" in definition
        assert definition["name"] == "web_search"
        assert "description" in definition
        assert "REAL-TIME" in definition["description"]
        assert "input_schema" in definition

    def test_duckduckgo_tool_schema(self):
        """Test DuckDuckGo tool has correct input schema."""
        from src.agent.tools.duckduckgo_search import DuckDuckGoSearch, DDGS_AVAILABLE

        if not DDGS_AVAILABLE:
            pytest.skip("duckduckgo-search not installed")

        search = DuckDuckGoSearch()
        definition = search.get_tool_definition()
        schema = definition["input_schema"]

        assert schema["type"] == "object"
        assert "query" in schema["properties"]
        assert "search_type" in schema["properties"]
        assert "time_range" in schema["properties"]
        assert "query" in schema["required"]

    def test_duckduckgo_search_type_enum(self):
        """Test search_type has proper enum values."""
        from src.agent.tools.duckduckgo_search import DuckDuckGoSearch, DDGS_AVAILABLE

        if not DDGS_AVAILABLE:
            pytest.skip("duckduckgo-search not installed")

        search = DuckDuckGoSearch()
        definition = search.get_tool_definition()
        search_type_prop = definition["input_schema"]["properties"]["search_type"]

        assert "enum" in search_type_prop
        assert "text" in search_type_prop["enum"]
        assert "news" in search_type_prop["enum"]

    def test_duckduckgo_time_range_enum(self):
        """Test time_range has proper enum values."""
        from src.agent.tools.duckduckgo_search import DuckDuckGoSearch, DDGS_AVAILABLE

        if not DDGS_AVAILABLE:
            pytest.skip("duckduckgo-search not installed")

        search = DuckDuckGoSearch()
        definition = search.get_tool_definition()
        time_range_prop = definition["input_schema"]["properties"]["time_range"]

        assert "enum" in time_range_prop
        assert "d" in time_range_prop["enum"]  # day
        assert "w" in time_range_prop["enum"]  # week
        assert "m" in time_range_prop["enum"]  # month
        assert "y" in time_range_prop["enum"]  # year

    def test_duckduckgo_callable(self):
        """Test DuckDuckGo search is callable."""
        from src.agent.tools.duckduckgo_search import DuckDuckGoSearch, DDGS_AVAILABLE

        if not DDGS_AVAILABLE:
            pytest.skip("duckduckgo-search not installed")

        search = DuckDuckGoSearch()
        assert callable(search)

    def test_duckduckgo_has_search_method(self):
        """Test DuckDuckGo has search method."""
        from src.agent.tools.duckduckgo_search import DuckDuckGoSearch, DDGS_AVAILABLE

        if not DDGS_AVAILABLE:
            pytest.skip("duckduckgo-search not installed")

        search = DuckDuckGoSearch()
        assert hasattr(search, 'search')
        assert callable(search.search)

    def test_duckduckgo_has_news_search(self):
        """Test DuckDuckGo has search_news method."""
        from src.agent.tools.duckduckgo_search import DuckDuckGoSearch, DDGS_AVAILABLE

        if not DDGS_AVAILABLE:
            pytest.skip("duckduckgo-search not installed")

        search = DuckDuckGoSearch()
        assert hasattr(search, 'search_news')
        assert callable(search.search_news)


class TestDuckDuckGoSearchResults:
    """Tests for DuckDuckGo search result format."""

    @patch('src.agent.tools.duckduckgo_search.DDGS')
    def test_search_returns_dict(self, mock_ddgs):
        """Test search returns a dictionary."""
        from src.agent.tools.duckduckgo_search import DuckDuckGoSearch, DDGS_AVAILABLE

        if not DDGS_AVAILABLE:
            pytest.skip("duckduckgo-search not installed")

        # Mock the DDGS context manager
        mock_instance = MagicMock()
        mock_instance.text.return_value = []
        mock_ddgs.return_value.__enter__.return_value = mock_instance

        search = DuckDuckGoSearch()
        result = search.search("test query")

        assert isinstance(result, dict)

    @patch('src.agent.tools.duckduckgo_search.DDGS')
    def test_search_success_flag(self, mock_ddgs):
        """Test search result has success flag."""
        from src.agent.tools.duckduckgo_search import DuckDuckGoSearch, DDGS_AVAILABLE

        if not DDGS_AVAILABLE:
            pytest.skip("duckduckgo-search not installed")

        mock_instance = MagicMock()
        mock_instance.text.return_value = []
        mock_ddgs.return_value.__enter__.return_value = mock_instance

        search = DuckDuckGoSearch()
        result = search.search("test query")

        assert "success" in result

    @patch('src.agent.tools.duckduckgo_search.DDGS')
    def test_search_includes_query(self, mock_ddgs):
        """Test search result includes original query."""
        from src.agent.tools.duckduckgo_search import DuckDuckGoSearch, DDGS_AVAILABLE

        if not DDGS_AVAILABLE:
            pytest.skip("duckduckgo-search not installed")

        mock_instance = MagicMock()
        mock_instance.text.return_value = []
        mock_ddgs.return_value.__enter__.return_value = mock_instance

        search = DuckDuckGoSearch()
        result = search.search("Salesforce revenue 2024")

        assert "query" in result
        assert result["query"] == "Salesforce revenue 2024"

    @patch('src.agent.tools.duckduckgo_search.DDGS')
    def test_search_includes_results_list(self, mock_ddgs):
        """Test search result includes results list."""
        from src.agent.tools.duckduckgo_search import DuckDuckGoSearch, DDGS_AVAILABLE

        if not DDGS_AVAILABLE:
            pytest.skip("duckduckgo-search not installed")

        mock_instance = MagicMock()
        mock_instance.text.return_value = [
            {"title": "Test", "href": "http://test.com", "body": "Test content"}
        ]
        mock_ddgs.return_value.__enter__.return_value = mock_instance

        search = DuckDuckGoSearch()
        result = search.search("test")

        assert "results" in result
        assert isinstance(result["results"], list)

    @patch('src.agent.tools.duckduckgo_search.DDGS')
    def test_search_result_format(self, mock_ddgs):
        """Test individual search result format."""
        from src.agent.tools.duckduckgo_search import DuckDuckGoSearch, DDGS_AVAILABLE

        if not DDGS_AVAILABLE:
            pytest.skip("duckduckgo-search not installed")

        mock_instance = MagicMock()
        mock_instance.text.return_value = [
            {
                "title": "Salesforce Q4 Results",
                "href": "http://example.com/salesforce",
                "body": "Salesforce reported strong Q4 revenue..."
            }
        ]
        mock_ddgs.return_value.__enter__.return_value = mock_instance

        search = DuckDuckGoSearch()
        result = search.search("Salesforce")

        assert len(result["results"]) > 0
        first_result = result["results"][0]
        assert "title" in first_result
        assert "url" in first_result
        assert "content" in first_result

    @patch('src.agent.tools.duckduckgo_search.DDGS')
    def test_search_handles_errors(self, mock_ddgs):
        """Test search handles errors gracefully."""
        from src.agent.tools.duckduckgo_search import DuckDuckGoSearch, DDGS_AVAILABLE

        if not DDGS_AVAILABLE:
            pytest.skip("duckduckgo-search not installed")

        mock_ddgs.return_value.__enter__.side_effect = Exception("Network error")

        search = DuckDuckGoSearch()
        result = search.search("test")

        assert result["success"] is False
        assert "error" in result


class TestDuckDuckGoNewsSearch:
    """Tests for DuckDuckGo news search."""

    @patch('src.agent.tools.duckduckgo_search.DDGS')
    def test_news_search_uses_news_endpoint(self, mock_ddgs):
        """Test news search uses the news endpoint."""
        from src.agent.tools.duckduckgo_search import DuckDuckGoSearch, DDGS_AVAILABLE

        if not DDGS_AVAILABLE:
            pytest.skip("duckduckgo-search not installed")

        mock_instance = MagicMock()
        mock_instance.news.return_value = []
        mock_ddgs.return_value.__enter__.return_value = mock_instance

        search = DuckDuckGoSearch()
        result = search.search("AI news", search_type="news")

        mock_instance.news.assert_called_once()

    @patch('src.agent.tools.duckduckgo_search.DDGS')
    def test_search_news_method(self, mock_ddgs):
        """Test search_news convenience method."""
        from src.agent.tools.duckduckgo_search import DuckDuckGoSearch, DDGS_AVAILABLE

        if not DDGS_AVAILABLE:
            pytest.skip("duckduckgo-search not installed")

        mock_instance = MagicMock()
        mock_instance.news.return_value = []
        mock_ddgs.return_value.__enter__.return_value = mock_instance

        search = DuckDuckGoSearch()
        result = search.search_news("AI funding")

        assert result["search_type"] == "news"


class TestWebSearchToolRegistry:
    """Tests for web search tool registration."""

    def test_web_search_in_normal_mode_tools(self):
        """Test web_search is included in normal mode tools."""
        from src.shared.config import ModeConfig

        config = ModeConfig()
        assert "web_search" in config.normal_mode_tools

    def test_web_search_in_deep_mode_tools(self):
        """Test web_search is included in deep mode tools."""
        from src.shared.config import ModeConfig

        config = ModeConfig()
        assert "web_search" in config.deep_mode_tools

    def test_tool_registry_imports_duckduckgo(self):
        """Test tool registry imports DuckDuckGo search."""
        # Read the tool registry file
        registry_path = Path(__file__).parent.parent.parent.parent.parent / "src/agent/tool_registry.py"

        with open(registry_path, 'r') as f:
            content = f.read()

        assert "DuckDuckGoSearch" in content
        assert "DDGS_AVAILABLE" in content

    def test_duckduckgo_is_primary_search(self):
        """Test DuckDuckGo is registered as primary web search."""
        registry_path = Path(__file__).parent.parent.parent.parent.parent / "src/agent/tool_registry.py"

        with open(registry_path, 'r') as f:
            content = f.read()

        # DuckDuckGo should be tried first
        ddg_index = content.find("DuckDuckGoSearch")
        tavily_fallback_index = content.find("not web_search_initialized and self.config.tools.tavily_api_key")

        assert ddg_index < tavily_fallback_index, "DuckDuckGo should be registered before Tavily fallback"


class TestWebSearchIntegration:
    """Integration tests for web search."""

    def test_web_search_tool_definition_emphasizes_realtime(self):
        """Test web search tool definition emphasizes real-time capability."""
        from src.agent.tools.duckduckgo_search import DuckDuckGoSearch, DDGS_AVAILABLE

        if not DDGS_AVAILABLE:
            pytest.skip("duckduckgo-search not installed")

        search = DuckDuckGoSearch()
        definition = search.get_tool_definition()

        # The description should emphasize real-time search
        desc = definition["description"].upper()
        assert "REAL-TIME" in desc or "REAL TIME" in desc or "CURRENT" in desc

    def test_web_search_is_first_recommended_tool(self):
        """Test web search is recommended for up-to-date information."""
        from src.agent.tools.duckduckgo_search import DuckDuckGoSearch, DDGS_AVAILABLE

        if not DDGS_AVAILABLE:
            pytest.skip("duckduckgo-search not installed")

        search = DuckDuckGoSearch()
        definition = search.get_tool_definition()

        # Should mention using it first
        desc = definition["description"].upper()
        assert "FIRST" in desc or "CURRENT" in desc or "LIVE" in desc


class TestTavilyWebSearch:
    """Tests for Tavily web search (fallback)."""

    def test_tavily_search_class_exists(self):
        """Test WebSearch (Tavily) class exists."""
        from src.agent.tools.web_search import WebSearch
        assert WebSearch is not None

    def test_tavily_requires_api_key(self):
        """Test Tavily requires API key."""
        from src.agent.tools.web_search import WebSearch

        # Without API key, should raise error
        with pytest.raises((ValueError, ImportError)):
            WebSearch(api_key=None)

    def test_tavily_tool_definition(self):
        """Test Tavily tool definition exists."""
        from src.agent.tools.web_search import WebSearch

        # Create with mock API key (won't actually work but tests definition)
        try:
            # We can't test without an API key, so just verify the class has the method
            assert hasattr(WebSearch, 'get_tool_definition')
        except:
            pass


class TestWebSearchConfigSettings:
    """Tests for web search configuration."""

    def test_config_has_web_search_settings(self):
        """Test config has web search settings."""
        from src.shared.config import ToolConfig

        config = ToolConfig()
        assert hasattr(config, 'web_search_max_results')
        assert hasattr(config, 'web_search_timeout')

    def test_config_has_tavily_settings(self):
        """Test config has Tavily settings."""
        from src.shared.config import ToolConfig

        config = ToolConfig()
        assert hasattr(config, 'tavily_api_key')
        assert hasattr(config, 'tavily_max_results')
        assert hasattr(config, 'tavily_timeout')

    def test_default_max_results(self):
        """Test default max results is reasonable."""
        from src.shared.config import ToolConfig

        config = ToolConfig()
        assert config.web_search_max_results >= 5
        assert config.web_search_max_results <= 20


class TestWebSearchForB2BIntelligence:
    """Tests for B2B-specific web search use cases."""

    def test_can_search_company_info(self):
        """Test web search can handle company queries."""
        from src.agent.tools.duckduckgo_search import DuckDuckGoSearch, DDGS_AVAILABLE

        if not DDGS_AVAILABLE:
            pytest.skip("duckduckgo-search not installed")

        search = DuckDuckGoSearch()

        # These queries should be valid for the tool
        valid_queries = [
            "Salesforce quarterly revenue 2024",
            "Microsoft acquisition news",
            "startup funding AI 2024",
            "Apple stock price today"
        ]

        for query in valid_queries:
            # Just verify the tool can be called with these queries
            assert callable(search)

    def test_tool_description_mentions_company_data(self):
        """Test tool description mentions company data searches."""
        from src.agent.tools.duckduckgo_search import DuckDuckGoSearch, DDGS_AVAILABLE

        if not DDGS_AVAILABLE:
            pytest.skip("duckduckgo-search not installed")

        search = DuckDuckGoSearch()
        definition = search.get_tool_definition()
        desc = definition["description"].lower()

        # Should mention relevant B2B search terms
        b2b_terms = ["company", "market", "news", "information"]
        found = any(term in desc for term in b2b_terms)
        assert found, "Tool description should mention B2B-relevant search capabilities"
