"""DuckDuckGo web search tool implementation."""

import logging
from typing import Dict, Any, Optional, List
from urllib.parse import quote_plus

from src.agent.tools.base import BaseTool, RateLimiter
from src.shared.models import ToolMode

logger = logging.getLogger(__name__)

# Try to import duckduckgo_search
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS = None
    DDGS_AVAILABLE = False


class DuckDuckGoSearchTool(BaseTool):
    """
    DuckDuckGo web search tool.

    Provides free web search without API key requirements.
    Falls back to Wikipedia if rate limited.
    """

    TOOL_NAME = "web_search"
    TOOL_DESCRIPTION = (
        "Search the web for current information using DuckDuckGo. "
        "Use this for finding recent news, current events, company information, "
        "or any factual data that may not be in encyclopedias. "
        "Returns search results with titles, URLs, and content snippets."
    )
    TOOL_MODE = ToolMode.CORE
    DEFAULT_TIMEOUT = 10.0
    MAX_RETRIES = 2
    CACHE_TTL = 3600.0  # 1 hour cache for search results

    RATE_LIMIT_RPS = 1.0  # DuckDuckGo rate limit
    RATE_LIMIT_BURST = 3

    def __init__(
        self,
        max_results: int = 10,
        region: str = "wt-wt",  # Worldwide
        safesearch: str = "moderate",
        **kwargs
    ):
        """
        Initialize DuckDuckGo search tool.

        Args:
            max_results: Maximum number of results to return
            region: Search region (default: worldwide)
            safesearch: Safe search level (off, moderate, strict)
            **kwargs: Additional BaseTool arguments
        """
        super().__init__(**kwargs)

        if not DDGS_AVAILABLE:
            logger.warning(
                "duckduckgo-search not installed. "
                "Install with: pip install duckduckgo-search"
            )

        self.max_results = max_results
        self.region = region
        self.safesearch = safesearch

    def _execute(self, query: str) -> Dict[str, Any]:
        """
        Execute web search.

        Args:
            query: Search query

        Returns:
            Dictionary with search results
        """
        if not DDGS_AVAILABLE:
            return {
                "success": False,
                "error": "DuckDuckGo search not available. Install duckduckgo-search package.",
                "query": query
            }

        # Validate and sanitize query
        if not query or not query.strip():
            return {
                "success": False,
                "error": "Empty search query",
                "query": query
            }

        query = query.strip()

        # Truncate very long queries
        if len(query) > 500:
            original_length = len(query)
            query = query[:500]
            logger.warning(f"Query truncated from {original_length} to 500 characters")

        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(
                    query,
                    region=self.region,
                    safesearch=self.safesearch,
                    max_results=self.max_results
                ))

            # Process and deduplicate results
            seen_urls = set()
            processed_results = []

            for item in results:
                url = item.get("href", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    processed_results.append({
                        "title": item.get("title", ""),
                        "url": url,
                        "content": item.get("body", ""),
                    })

            if not processed_results:
                return {
                    "success": True,
                    "query": query,
                    "results": [],
                    "result_count": 0,
                    "message": f"No results found for: {query}"
                }

            return {
                "success": True,
                "query": query,
                "results": processed_results,
                "result_count": len(processed_results)
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"DuckDuckGo search error: {error_msg}")

            # Check for rate limiting
            if "rate" in error_msg.lower() or "blocked" in error_msg.lower():
                return {
                    "success": False,
                    "error": "Rate limited by DuckDuckGo. Please try again later.",
                    "query": query,
                    "error_code": "RATE_LIMITED"
                }

            return {
                "success": False,
                "error": f"Search failed: {error_msg}",
                "query": query
            }

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool input."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "The search query. Be specific for better results. "
                        "Examples: 'Stripe funding 2024', 'Datadog revenue growth', "
                        "'Tesla stock price today'"
                    )
                }
            },
            "required": ["query"]
        }

    @staticmethod
    def is_available() -> bool:
        """Check if DuckDuckGo search is available."""
        return DDGS_AVAILABLE
