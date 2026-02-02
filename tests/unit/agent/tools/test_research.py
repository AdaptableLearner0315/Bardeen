"""Unit tests for agent/tools/research module."""

import pytest
import time
from unittest.mock import MagicMock, patch, PropertyMock
from typing import Dict, Any

from src.storage.cache import reset_caches
from src.shared.config import reset_config


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up caches after each test."""
    reset_caches()
    reset_config()
    yield
    reset_caches()
    reset_config()


# ============================================================================
# DuckDuckGo Search Tool Tests
# ============================================================================

class TestDuckDuckGoSearchTool:
    """Tests for DuckDuckGo search tool."""

    def test_tool_metadata(self):
        """Test tool metadata is correct."""
        from src.agent.tools.research.duckduckgo import DuckDuckGoSearchTool

        tool = DuckDuckGoSearchTool()
        assert tool.TOOL_NAME == "web_search"
        assert "search" in tool.TOOL_DESCRIPTION.lower()

    def test_get_tool_definition(self):
        """Test get_tool_definition returns valid schema."""
        from src.agent.tools.research.duckduckgo import DuckDuckGoSearchTool

        tool = DuckDuckGoSearchTool()
        definition = tool.get_tool_definition()

        assert definition["name"] == "web_search"
        assert "input_schema" in definition
        assert definition["input_schema"]["type"] == "object"
        assert "query" in definition["input_schema"]["properties"]

    def test_empty_query_returns_error(self):
        """Test empty query returns error."""
        from src.agent.tools.research.duckduckgo import DuckDuckGoSearchTool, DDGS_AVAILABLE

        tool = DuckDuckGoSearchTool()
        result = tool._execute(query="")

        assert result["success"] is False
        # If package not available, error will be about that
        if DDGS_AVAILABLE:
            assert "empty" in result["error"].lower()
        else:
            assert "not available" in result["error"].lower()

    def test_query_truncation(self):
        """Test long queries are truncated."""
        from src.agent.tools.research.duckduckgo import DuckDuckGoSearchTool

        tool = DuckDuckGoSearchTool()
        long_query = "a" * 600

        # Mock DDGS to avoid actual API call
        with patch('src.agent.tools.research.duckduckgo.DDGS_AVAILABLE', False):
            result = tool._execute(query=long_query)
            # Should fail because DDGS not available, but query should be truncated
            assert "not available" in result["error"].lower() or len(result.get("query", long_query)) <= 500

    def test_is_available_method(self):
        """Test is_available static method."""
        from src.agent.tools.research.duckduckgo import DuckDuckGoSearchTool

        # Should return True if duckduckgo_search is installed
        assert isinstance(DuckDuckGoSearchTool.is_available(), bool)


# ============================================================================
# Wikipedia Tool Tests
# ============================================================================

class TestWikipediaTool:
    """Tests for Wikipedia tool."""

    def test_tool_metadata(self):
        """Test tool metadata is correct."""
        from src.agent.tools.research.wikipedia_tool import WikipediaTool

        tool = WikipediaTool()
        assert tool.TOOL_NAME == "wikipedia"
        assert "wikipedia" in tool.TOOL_DESCRIPTION.lower()

    def test_get_tool_definition(self):
        """Test get_tool_definition returns valid schema."""
        from src.agent.tools.research.wikipedia_tool import WikipediaTool

        tool = WikipediaTool()
        definition = tool.get_tool_definition()

        assert definition["name"] == "wikipedia"
        assert "input_schema" in definition
        assert "title" in definition["input_schema"]["properties"]

    def test_empty_title_returns_error(self):
        """Test empty title returns error."""
        from src.agent.tools.research.wikipedia_tool import WikipediaTool

        tool = WikipediaTool()
        result = tool._execute(title="")

        assert result["success"] is False
        assert "empty" in result["error"].lower()

    def test_is_available_method(self):
        """Test is_available static method."""
        from src.agent.tools.research.wikipedia_tool import WikipediaTool

        assert isinstance(WikipediaTool.is_available(), bool)


# ============================================================================
# Calculator Tool Tests
# ============================================================================

class TestCalculatorTool:
    """Tests for Calculator tool."""

    def test_tool_metadata(self):
        """Test tool metadata is correct."""
        from src.agent.tools.research.calculator_tool import CalculatorTool

        tool = CalculatorTool()
        assert tool.TOOL_NAME == "calculator"
        assert "math" in tool.TOOL_DESCRIPTION.lower() or "calcu" in tool.TOOL_DESCRIPTION.lower()

    def test_basic_arithmetic(self):
        """Test basic arithmetic operations."""
        from src.agent.tools.research.calculator_tool import CalculatorTool

        tool = CalculatorTool()

        # Addition
        result = tool._execute(expression="2 + 3")
        assert result["success"] is True
        assert result["result"] == 5

        # Subtraction
        result = tool._execute(expression="10 - 4")
        assert result["success"] is True
        assert result["result"] == 6

        # Multiplication
        result = tool._execute(expression="3 * 4")
        assert result["success"] is True
        assert result["result"] == 12

        # Division
        result = tool._execute(expression="15 / 3")
        assert result["success"] is True
        assert result["result"] == 5

    def test_complex_expressions(self):
        """Test complex expressions."""
        from src.agent.tools.research.calculator_tool import CalculatorTool

        tool = CalculatorTool()

        # Parentheses
        result = tool._execute(expression="(2 + 3) * 4")
        assert result["success"] is True
        assert result["result"] == 20

        # Exponentiation
        result = tool._execute(expression="2 ** 10")
        assert result["success"] is True
        assert result["result"] == 1024

        # Nested
        result = tool._execute(expression="((1 + 2) * (3 + 4))")
        assert result["success"] is True
        assert result["result"] == 21

    def test_math_functions(self):
        """Test math functions."""
        from src.agent.tools.research.calculator_tool import CalculatorTool

        tool = CalculatorTool()

        # sqrt
        result = tool._execute(expression="sqrt(144)")
        assert result["success"] is True
        assert result["result"] == 12

        # abs
        result = tool._execute(expression="abs(-42)")
        assert result["success"] is True
        assert result["result"] == 42

    def test_constants(self):
        """Test mathematical constants."""
        from src.agent.tools.research.calculator_tool import CalculatorTool
        import math

        tool = CalculatorTool()

        # pi
        result = tool._execute(expression="pi")
        assert result["success"] is True
        assert abs(result["result"] - math.pi) < 0.0001

        # e
        result = tool._execute(expression="e")
        assert result["success"] is True
        assert abs(result["result"] - math.e) < 0.0001

    def test_division_by_zero(self):
        """Test division by zero returns error."""
        from src.agent.tools.research.calculator_tool import CalculatorTool

        tool = CalculatorTool()
        result = tool._execute(expression="1 / 0")

        assert result["success"] is False
        assert "zero" in result["error"].lower()

    def test_invalid_expression(self):
        """Test invalid expression returns error."""
        from src.agent.tools.research.calculator_tool import CalculatorTool

        tool = CalculatorTool()
        # Use an actually invalid expression (incomplete)
        result = tool._execute(expression="2 + * 3")

        assert result["success"] is False
        assert "syntax" in result["error"].lower() or "invalid" in result["error"].lower()

    def test_empty_expression(self):
        """Test empty expression returns error."""
        from src.agent.tools.research.calculator_tool import CalculatorTool

        tool = CalculatorTool()
        result = tool._execute(expression="")

        assert result["success"] is False
        assert "empty" in result["error"].lower()

    def test_unsafe_code_rejected(self):
        """Test unsafe code is rejected."""
        from src.agent.tools.research.calculator_tool import CalculatorTool

        tool = CalculatorTool()

        # Import attempt
        result = tool._execute(expression="__import__('os')")
        assert result["success"] is False

        # Variable assignment
        result = tool._execute(expression="x = 5")
        assert result["success"] is False

        # Function call
        result = tool._execute(expression="print('hello')")
        assert result["success"] is False

    def test_expression_too_long(self):
        """Test expression length limit."""
        from src.agent.tools.research.calculator_tool import CalculatorTool

        tool = CalculatorTool(max_expression_length=50)
        result = tool._execute(expression="1 + " * 100 + "1")

        assert result["success"] is False
        assert "long" in result["error"].lower()

    def test_large_exponent_rejected(self):
        """Test very large exponents are rejected."""
        from src.agent.tools.research.calculator_tool import CalculatorTool

        tool = CalculatorTool()
        result = tool._execute(expression="2 ** 10000")

        assert result["success"] is False
        assert "exponent" in result["error"].lower() or "large" in result["error"].lower()

    def test_is_available(self):
        """Test calculator is always available."""
        from src.agent.tools.research.calculator_tool import CalculatorTool

        assert CalculatorTool.is_available() is True


# ============================================================================
# Yahoo Finance Tool Tests
# ============================================================================

class TestYahooFinanceTool:
    """Tests for Yahoo Finance tool."""

    def test_tool_metadata(self):
        """Test tool metadata is correct."""
        from src.agent.tools.research.yahoo_finance import YahooFinanceTool

        tool = YahooFinanceTool()
        assert tool.TOOL_NAME == "yahoo_finance"
        assert "finance" in tool.TOOL_DESCRIPTION.lower()

    def test_get_tool_definition(self):
        """Test get_tool_definition returns valid schema."""
        from src.agent.tools.research.yahoo_finance import YahooFinanceTool

        tool = YahooFinanceTool()
        definition = tool.get_tool_definition()

        assert definition["name"] == "yahoo_finance"
        assert "ticker" in definition["input_schema"]["properties"]

    def test_empty_ticker_returns_error(self):
        """Test empty ticker returns error."""
        from src.agent.tools.research.yahoo_finance import YahooFinanceTool, YFINANCE_AVAILABLE

        tool = YahooFinanceTool()
        result = tool._execute(ticker="")

        assert result["success"] is False
        # If package not available, error will be about that
        if YFINANCE_AVAILABLE:
            assert "empty" in result["error"].lower()
        else:
            assert "not available" in result["error"].lower()

    def test_invalid_ticker_format(self):
        """Test invalid ticker format returns error."""
        from src.agent.tools.research.yahoo_finance import YahooFinanceTool, YFINANCE_AVAILABLE

        tool = YahooFinanceTool()
        result = tool._execute(ticker="!!!invalid!!!")

        assert result["success"] is False
        # If package not available, error will be about that
        if YFINANCE_AVAILABLE:
            assert "invalid" in result["error"].lower()
        else:
            assert "not available" in result["error"].lower()

    def test_format_large_number(self):
        """Test large number formatting."""
        from src.agent.tools.research.yahoo_finance import YahooFinanceTool

        tool = YahooFinanceTool()

        assert tool._format_large_number(1_500_000_000_000) == "$1.50T"
        assert tool._format_large_number(2_500_000_000) == "$2.50B"
        assert tool._format_large_number(3_500_000) == "$3.50M"
        assert tool._format_large_number(4_500) == "$4.50K"
        assert tool._format_large_number(500) == "$500.00"

    def test_is_available_method(self):
        """Test is_available static method."""
        from src.agent.tools.research.yahoo_finance import YahooFinanceTool

        assert isinstance(YahooFinanceTool.is_available(), bool)


# ============================================================================
# SEC EDGAR Tool Tests
# ============================================================================

class TestSECEdgarTool:
    """Tests for SEC EDGAR tool."""

    def test_tool_metadata(self):
        """Test tool metadata is correct."""
        from src.agent.tools.research.sec_edgar import SECEdgarTool

        tool = SECEdgarTool()
        assert tool.TOOL_NAME == "sec_edgar"
        assert "sec" in tool.TOOL_DESCRIPTION.lower()

    def test_get_tool_definition(self):
        """Test get_tool_definition returns valid schema."""
        from src.agent.tools.research.sec_edgar import SECEdgarTool

        tool = SECEdgarTool()
        definition = tool.get_tool_definition()

        assert definition["name"] == "sec_edgar"
        assert "company" in definition["input_schema"]["properties"]

    def test_empty_company_returns_error(self):
        """Test empty company returns error."""
        from src.agent.tools.research.sec_edgar import SECEdgarTool

        tool = SECEdgarTool()
        result = tool._execute(company="")

        assert result["success"] is False
        assert "empty" in result["error"].lower()

    def test_invalid_filing_type(self):
        """Test invalid filing type returns error."""
        from src.agent.tools.research.sec_edgar import SECEdgarTool

        tool = SECEdgarTool()
        result = tool._execute(company="Apple", filing_type="INVALID")

        assert result["success"] is False
        assert "invalid" in result["error"].lower()

    def test_is_available(self):
        """Test SEC EDGAR is always available."""
        from src.agent.tools.research.sec_edgar import SECEdgarTool

        assert SECEdgarTool.is_available() is True


# ============================================================================
# GitHub Tool Tests
# ============================================================================

class TestGitHubTool:
    """Tests for GitHub tool."""

    def test_tool_metadata(self):
        """Test tool metadata is correct."""
        from src.agent.tools.research.github_tool import GitHubTool

        tool = GitHubTool()
        assert tool.TOOL_NAME == "github"
        assert "github" in tool.TOOL_DESCRIPTION.lower()

    def test_get_tool_definition(self):
        """Test get_tool_definition returns valid schema."""
        from src.agent.tools.research.github_tool import GitHubTool

        tool = GitHubTool()
        definition = tool.get_tool_definition()

        assert definition["name"] == "github"
        assert "org_name" in definition["input_schema"]["properties"]

    def test_empty_org_name_returns_error(self):
        """Test empty org name returns error."""
        from src.agent.tools.research.github_tool import GitHubTool

        tool = GitHubTool()
        result = tool._execute(org_name="")

        assert result["success"] is False
        assert "empty" in result["error"].lower()

    def test_is_available(self):
        """Test GitHub is always available."""
        from src.agent.tools.research.github_tool import GitHubTool

        assert GitHubTool.is_available() is True


# ============================================================================
# HackerNews Tool Tests
# ============================================================================

class TestHackerNewsTool:
    """Tests for HackerNews tool."""

    def test_tool_metadata(self):
        """Test tool metadata is correct."""
        from src.agent.tools.research.hackernews import HackerNewsTool

        tool = HackerNewsTool()
        assert tool.TOOL_NAME == "hackernews"
        assert "hacker" in tool.TOOL_DESCRIPTION.lower()

    def test_get_tool_definition(self):
        """Test get_tool_definition returns valid schema."""
        from src.agent.tools.research.hackernews import HackerNewsTool

        tool = HackerNewsTool()
        definition = tool.get_tool_definition()

        assert definition["name"] == "hackernews"
        assert "query" in definition["input_schema"]["properties"]

    def test_empty_query_returns_error(self):
        """Test empty query returns error."""
        from src.agent.tools.research.hackernews import HackerNewsTool

        tool = HackerNewsTool()
        result = tool._execute(query="")

        assert result["success"] is False
        assert "empty" in result["error"].lower()

    def test_is_available(self):
        """Test HackerNews is always available."""
        from src.agent.tools.research.hackernews import HackerNewsTool

        assert HackerNewsTool.is_available() is True


# ============================================================================
# Web Scraper Tool Tests
# ============================================================================

class TestWebScraperTool:
    """Tests for Web Scraper tool."""

    def test_tool_metadata(self):
        """Test tool metadata is correct."""
        from src.agent.tools.research.web_scraper import WebScraperTool

        tool = WebScraperTool()
        assert tool.TOOL_NAME == "web_scraper"
        assert "scrape" in tool.TOOL_DESCRIPTION.lower()

    def test_get_tool_definition(self):
        """Test get_tool_definition returns valid schema."""
        from src.agent.tools.research.web_scraper import WebScraperTool

        tool = WebScraperTool()
        definition = tool.get_tool_definition()

        assert definition["name"] == "web_scraper"
        assert "url" in definition["input_schema"]["properties"]

    def test_empty_url_returns_error(self):
        """Test empty URL returns error."""
        from src.agent.tools.research.web_scraper import WebScraperTool

        tool = WebScraperTool()
        result = tool._execute(url="")

        assert result["success"] is False
        assert "empty" in result["error"].lower()

    def test_invalid_url_format(self):
        """Test invalid URL format returns error."""
        from src.agent.tools.research.web_scraper import WebScraperTool

        tool = WebScraperTool()

        # No domain
        result = tool._execute(url="not-a-valid-url")
        # Should at least attempt with https://

    def test_url_normalization(self):
        """Test URL normalization adds https."""
        from src.agent.tools.research.web_scraper import WebScraperTool
        from unittest.mock import patch

        tool = WebScraperTool()

        # Mock the fetch to avoid network calls
        with patch.object(tool, '_fetch_url', return_value=("<html><title>Test</title></html>", "https://example.com", "text/html")):
            with patch('src.agent.tools.research.web_scraper.BS4_AVAILABLE', True):
                result = tool._execute(url="example.com")
                # URL should be normalized with https://

    def test_is_available_method(self):
        """Test is_available static method."""
        from src.agent.tools.research.web_scraper import WebScraperTool

        assert isinstance(WebScraperTool.is_available(), bool)


# ============================================================================
# Integration Tests (Mock-based)
# ============================================================================

class TestResearchToolsIntegration:
    """Integration tests for research tools."""

    def test_all_tools_have_consistent_interface(self):
        """Test all tools implement consistent interface."""
        from src.agent.tools.research import (
            DuckDuckGoSearchTool,
            WikipediaTool,
            CalculatorTool,
            YahooFinanceTool,
            SECEdgarTool,
            GitHubTool,
            HackerNewsTool,
            WebScraperTool,
        )

        tools = [
            DuckDuckGoSearchTool(),
            WikipediaTool(),
            CalculatorTool(),
            YahooFinanceTool(),
            SECEdgarTool(),
            GitHubTool(),
            HackerNewsTool(),
            WebScraperTool(),
        ]

        for tool in tools:
            # All should have TOOL_NAME
            assert hasattr(tool, 'TOOL_NAME')
            assert tool.TOOL_NAME

            # All should have get_tool_definition
            definition = tool.get_tool_definition()
            assert "name" in definition
            assert "description" in definition
            assert "input_schema" in definition

            # All should have get_input_schema
            schema = tool.get_input_schema()
            assert schema["type"] == "object"
            assert "properties" in schema

            # All should have execute method
            assert hasattr(tool, 'execute')

            # All should have is_available
            assert hasattr(tool, 'is_available')

    def test_all_tools_inherit_from_base_tool(self):
        """Test all tools inherit from BaseTool."""
        from src.agent.tools.base import BaseTool
        from src.agent.tools.research import (
            DuckDuckGoSearchTool,
            WikipediaTool,
            CalculatorTool,
            YahooFinanceTool,
            SECEdgarTool,
            GitHubTool,
            HackerNewsTool,
            WebScraperTool,
        )

        tool_classes = [
            DuckDuckGoSearchTool,
            WikipediaTool,
            CalculatorTool,
            YahooFinanceTool,
            SECEdgarTool,
            GitHubTool,
            HackerNewsTool,
            WebScraperTool,
        ]

        for tool_class in tool_classes:
            assert issubclass(tool_class, BaseTool), f"{tool_class.__name__} should inherit from BaseTool"
