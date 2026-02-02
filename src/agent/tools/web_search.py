"""Web search tool using Tavily API."""

from typing import Dict, Any, List, Optional
import os

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None


class WebSearch:
    """
    Web search tool powered by Tavily API.

    Tavily is optimized for AI applications and provides clean,
    relevant search results without ads or clutter.
    """

    def __init__(self, api_key: Optional[str] = None, max_results: int = 3, timeout: int = 10):
        """
        Initialize web search tool.

        Args:
            api_key: Tavily API key (or from TAVILY_API_KEY env var)
            max_results: Maximum number of results to return
            timeout: Request timeout in seconds
        """
        if TavilyClient is None:
            raise ImportError(
                "tavily-python is required for WebSearch. "
                "Install with: pip install tavily-python"
            )

        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Tavily API key required. Set TAVILY_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.max_results = max_results
        self.timeout = timeout
        self.client = TavilyClient(api_key=self.api_key)

    def search(self, query: str, search_depth: str = "basic") -> Dict[str, Any]:
        """
        Search the web for information.

        Args:
            query: Search query
            search_depth: Either "basic" or "advanced" (advanced is more thorough)

        Returns:
            Dictionary with search results or error
        """
        try:
            # Perform search
            response = self.client.search(
                query=query,
                search_depth=search_depth,
                max_results=self.max_results
            )

            # Extract results
            results = []
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0.0)
                })

            # Get answer if available (Tavily sometimes provides a direct answer)
            answer = response.get("answer", "")

            return {
                "success": True,
                "query": query,
                "answer": answer,
                "results": results,
                "result_count": len(results)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Search failed: {str(e)}",
                "query": query
            }

    def get_tool_definition(self) -> Dict[str, Any]:
        """Get tool definition for LLM tool calling."""
        return {
            "name": "web_search",
            "description": (
                "Search the web for current information, news, and facts. "
                "Use this when you need up-to-date information that might not be "
                "in Wikipedia, or when you need recent news and events. "
                "Returns search results with titles, URLs, and content snippets."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "The search query. Be specific for better results. "
                            "Examples: 'France population 2024', 'SpaceX founding date'"
                        )
                    }
                },
                "required": ["query"]
            }
        }

    def __call__(self, query: str) -> Dict[str, Any]:
        """
        Execute the web search tool.

        Args:
            query: Search query

        Returns:
            Dictionary with search results or error
        """
        return self.search(query)
