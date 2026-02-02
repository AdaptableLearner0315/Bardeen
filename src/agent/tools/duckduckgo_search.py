"""DuckDuckGo web search tool - free, no API key required."""

from typing import Dict, Any, List, Optional
import time
import warnings


# Try new package name first, then fall back to old
DDGS = None
DDGS_AVAILABLE = False

try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    try:
        # Fall back to old package name (suppress deprecation warning)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from duckduckgo_search import DDGS
        DDGS_AVAILABLE = True
    except ImportError:
        DDGS = None
        DDGS_AVAILABLE = False


class DuckDuckGoSearch:
    """
    Web search tool powered by DuckDuckGo.

    Free to use, no API key required. Great for real-time web searches
    during the agent's thinking process.
    """

    def __init__(self, max_results: int = 5, timeout: int = 10):
        """
        Initialize DuckDuckGo search tool.

        Args:
            max_results: Maximum number of results to return
            timeout: Request timeout in seconds
        """
        if not DDGS_AVAILABLE:
            raise ImportError(
                "duckduckgo-search is required for DuckDuckGoSearch. "
                "Install with: pip install duckduckgo-search"
            )

        self.max_results = max_results
        self.timeout = timeout

    def search(
        self,
        query: str,
        search_type: str = "text",
        time_range: Optional[str] = None,
        region: str = "wt-wt"
    ) -> Dict[str, Any]:
        """
        Search the web using DuckDuckGo.

        Args:
            query: Search query
            search_type: Type of search - "text", "news", or "instant"
            time_range: Time filter - "d" (day), "w" (week), "m" (month), "y" (year)
            region: Region code (wt-wt for worldwide)

        Returns:
            Dictionary with search results or error
        """
        try:
            start_time = time.time()

            with DDGS() as ddgs:
                if search_type == "news":
                    # News search for current events
                    raw_results = list(ddgs.news(
                        query,
                        max_results=self.max_results,
                        timelimit=time_range
                    ))
                elif search_type == "instant":
                    # Instant answers (like weather, calculations)
                    raw_results = ddgs.answers(query)
                    if raw_results:
                        return {
                            "success": True,
                            "query": query,
                            "search_type": "instant",
                            "answer": raw_results[0].get("text", "") if raw_results else None,
                            "source": raw_results[0].get("url", "") if raw_results else None,
                            "latency_ms": int((time.time() - start_time) * 1000)
                        }
                    # Fall back to text search if no instant answer
                    raw_results = list(ddgs.text(
                        query,
                        max_results=self.max_results,
                        timelimit=time_range,
                        region=region
                    ))
                else:
                    # Standard text search
                    raw_results = list(ddgs.text(
                        query,
                        max_results=self.max_results,
                        timelimit=time_range,
                        region=region
                    ))

            # Format results
            results = []
            for item in raw_results:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("href", item.get("url", "")),
                    "content": item.get("body", item.get("text", "")),
                    "source": item.get("source", ""),
                    "date": item.get("date", item.get("published", ""))
                })

            latency_ms = int((time.time() - start_time) * 1000)

            return {
                "success": True,
                "query": query,
                "search_type": search_type,
                "results": results,
                "result_count": len(results),
                "latency_ms": latency_ms
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"DuckDuckGo search failed: {str(e)}",
                "query": query
            }

    def search_news(self, query: str, time_range: str = "w") -> Dict[str, Any]:
        """
        Search for recent news articles.

        Args:
            query: Search query
            time_range: Time filter - "d" (day), "w" (week), "m" (month)

        Returns:
            Dictionary with news results
        """
        return self.search(query, search_type="news", time_range=time_range)

    def get_tool_definition(self) -> Dict[str, Any]:
        """Get tool definition for LLM tool calling."""
        return {
            "name": "web_search",
            "description": (
                "Search the web in REAL-TIME to find current information, recent news, "
                "company data, market trends, and any factual information. "
                "USE THIS TOOL FIRST when you need up-to-date information or to verify facts. "
                "This tool searches the live internet and returns fresh results. "
                "Supports text search for general queries and news search for recent events."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "The search query. Be specific and include relevant keywords. "
                            "Examples: 'Salesforce quarterly revenue 2024', "
                            "'latest AI startup funding news', 'Apple stock price today'"
                        )
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["text", "news"],
                        "description": (
                            "Type of search: 'text' for general web search, "
                            "'news' for recent news articles. Default is 'text'."
                        )
                    },
                    "time_range": {
                        "type": "string",
                        "enum": ["d", "w", "m", "y"],
                        "description": (
                            "Time filter for results: 'd' (past day), 'w' (past week), "
                            "'m' (past month), 'y' (past year). Optional."
                        )
                    }
                },
                "required": ["query"]
            }
        }

    def __call__(
        self,
        query: str,
        search_type: str = "text",
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute the web search tool.

        Args:
            query: Search query
            search_type: Type of search (text/news)
            time_range: Time filter

        Returns:
            Dictionary with search results or error
        """
        return self.search(query, search_type=search_type, time_range=time_range)


# Export availability flag
__all__ = ['DuckDuckGoSearch', 'DDGS_AVAILABLE']
