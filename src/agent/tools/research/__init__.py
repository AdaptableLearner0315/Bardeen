"""Research tools for the B2B Account Intelligence Agent.

This module provides:
- Core Tools: DuckDuckGo Search, Wikipedia, Calculator
- Extended Tools: Yahoo Finance, SEC EDGAR, GitHub, HackerNews, Website Scraper
"""

from .duckduckgo import DuckDuckGoSearchTool
from .wikipedia_tool import WikipediaTool
from .calculator_tool import CalculatorTool
from .yahoo_finance import YahooFinanceTool
from .sec_edgar import SECEdgarTool
from .github_tool import GitHubTool
from .hackernews import HackerNewsTool
from .web_scraper import WebScraperTool

__all__ = [
    # Core tools
    "DuckDuckGoSearchTool",
    "WikipediaTool",
    "CalculatorTool",
    # Extended tools
    "YahooFinanceTool",
    "SECEdgarTool",
    "GitHubTool",
    "HackerNewsTool",
    "WebScraperTool",
]
