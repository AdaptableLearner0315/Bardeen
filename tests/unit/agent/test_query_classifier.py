"""Tests for QueryClassifier."""

import pytest

try:
    from src.agent.llm_client import QueryClassifier
except ImportError:
    QueryClassifier = None


class TestQueryClassifierDeepDetection:
    """Tests for is_deep_research method."""

    @pytest.fixture(autouse=True)
    def skip_if_unavailable(self):
        """Skip if QueryClassifier not available."""
        if QueryClassifier is None:
            pytest.skip("QueryClassifier not available")

    def test_simple_what_is_query(self):
        """'What is X' queries are simple."""
        assert QueryClassifier.is_deep_research("What is Python?") is False
        assert QueryClassifier.is_deep_research("What is the capital of France?") is False

    def test_simple_who_is_query(self):
        """'Who is X' queries are simple."""
        assert QueryClassifier.is_deep_research("Who is Elon Musk?") is False

    def test_simple_when_query(self):
        """'When did X' queries are simple."""
        assert QueryClassifier.is_deep_research("When did World War 2 end?") is False

    def test_simple_where_query(self):
        """'Where is X' queries are simple."""
        assert QueryClassifier.is_deep_research("Where is the Eiffel Tower?") is False

    def test_simple_calculation(self):
        """Calculation queries are simple."""
        assert QueryClassifier.is_deep_research("Calculate 25% of 400") is False
        assert QueryClassifier.is_deep_research("What is 100 + 200?") is False

    def test_deep_research_keyword(self):
        """'Research' keyword triggers deep mode."""
        assert QueryClassifier.is_deep_research("Research the history of Python") is True

    def test_deep_analyze_keyword(self):
        """'Analyze' keyword triggers deep mode."""
        assert QueryClassifier.is_deep_research("Analyze the financial performance of Apple") is True

    def test_deep_comprehensive_keyword(self):
        """'Comprehensive' keyword triggers deep mode."""
        assert QueryClassifier.is_deep_research("Give me a comprehensive overview of Tesla") is True

    def test_deep_financial_query(self):
        """Financial queries trigger deep mode (when not starting with 'what is')."""
        # "What is X" is simple even with financial terms
        assert QueryClassifier.is_deep_research("Analyze the financial performance of Google") is True
        assert QueryClassifier.is_deep_research("Show me Tesla revenue history and earnings") is True

    def test_deep_github_query(self):
        """GitHub-related queries trigger deep mode."""
        assert QueryClassifier.is_deep_research("Tell me about the React repository on GitHub") is True

    def test_deep_compare_multiple(self):
        """Multiple comparisons trigger deep mode."""
        assert QueryClassifier.is_deep_research("Compare Python and JavaScript and Ruby") is True

    def test_deep_long_query(self):
        """Long queries (>150 chars) trigger deep mode."""
        long_query = "I need to understand " + "a" * 150
        assert QueryClassifier.is_deep_research(long_query) is True

    def test_deep_multiple_questions(self):
        """Multiple question marks with complex content trigger deep mode."""
        # Simple "what is" still dominates, so use complex phrasing
        assert QueryClassifier.is_deep_research("How does X compare to Y? What factors influence Z? Explain the differences.") is True

    def test_empty_query_is_simple(self):
        """Empty or short queries are simple."""
        assert QueryClassifier.is_deep_research("") is False
        assert QueryClassifier.is_deep_research("Hi") is False

    def test_ambiguous_defaults_simple(self):
        """Ambiguous queries default to simple."""
        assert QueryClassifier.is_deep_research("Tell me something interesting") is False


class TestQueryClassifierToolRecommendations:
    """Tests for get_recommended_tools method."""

    @pytest.fixture(autouse=True)
    def skip_if_unavailable(self):
        """Skip if QueryClassifier not available."""
        if QueryClassifier is None:
            pytest.skip("QueryClassifier not available")

    def test_calculation_query(self):
        """Math queries recommend calculator."""
        tools = QueryClassifier.get_recommended_tools("Calculate 25% of 400")
        assert "calculator" in tools

    def test_stock_query(self):
        """Stock queries recommend yahoo_finance."""
        tools = QueryClassifier.get_recommended_tools("What is Apple stock price?")
        assert "yahoo_finance" in tools

    def test_github_query(self):
        """GitHub queries recommend github_api."""
        tools = QueryClassifier.get_recommended_tools("Show me the React repository")
        assert "github_api" in tools

    def test_news_query(self):
        """News queries recommend perplexity and web_search."""
        tools = QueryClassifier.get_recommended_tools("What's the latest news about AI?")
        assert "perplexity_search" in tools or "web_search" in tools

    def test_research_query(self):
        """Research queries recommend perplexity."""
        tools = QueryClassifier.get_recommended_tools("Research the history of Python")
        assert "perplexity_search" in tools

    def test_factual_query(self):
        """Factual queries recommend wikipedia."""
        tools = QueryClassifier.get_recommended_tools("What is the capital of France?")
        assert "wikipedia" in tools

    def test_default_tools(self):
        """Ambiguous queries get default tools."""
        tools = QueryClassifier.get_recommended_tools("Tell me something")
        assert len(tools) > 0
        # Should have some defaults
        assert "wikipedia" in tools or "web_search" in tools

    def test_combined_query(self):
        """Combined queries get multiple tools."""
        tools = QueryClassifier.get_recommended_tools("Calculate the stock price of Apple and research its history")
        assert "calculator" in tools
        assert "yahoo_finance" in tools or "perplexity_search" in tools
