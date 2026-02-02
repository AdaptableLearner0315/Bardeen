"""HackerNews API tool implementation."""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import urllib.request
import urllib.parse

from src.agent.tools.base import BaseTool
from src.shared.models import ToolMode

logger = logging.getLogger(__name__)


class HackerNewsTool(BaseTool):
    """
    HackerNews API tool for accessing tech community discussions.

    Provides information about company mentions, product discussions,
    and tech community sentiment from Hacker News.
    """

    TOOL_NAME = "hackernews"
    TOOL_DESCRIPTION = (
        "Search HackerNews for company mentions and tech discussions. "
        "Returns stories, comments, and discussions about companies. "
        "Use this to understand tech community perception, product feedback, "
        "and industry discussions about a company."
    )
    TOOL_MODE = ToolMode.EXTENDED
    DEFAULT_TIMEOUT = 5.0
    MAX_RETRIES = 2
    CACHE_TTL = 1800.0  # 30 minutes for HN data

    RATE_LIMIT_RPS = 10.0
    RATE_LIMIT_BURST = 10

    # HN Algolia API
    BASE_URL = "https://hn.algolia.com/api/v1"

    def __init__(
        self,
        max_results: int = 20,
        **kwargs
    ):
        """
        Initialize HackerNews tool.

        Args:
            max_results: Maximum number of results to return
            **kwargs: Additional BaseTool arguments
        """
        super().__init__(**kwargs)
        self.max_results = max_results

    def _execute(self, query: str, search_type: str = "story") -> Dict[str, Any]:
        """
        Search HackerNews for mentions.

        Args:
            query: Search query (company name, product, etc.)
            search_type: Type of content (story, comment, all)

        Returns:
            Dictionary with search results
        """
        # Validate input
        if not query or not query.strip():
            return {
                "success": False,
                "error": "Empty search query",
                "query": query
            }

        query = query.strip()
        search_type = search_type.lower()

        # Build search URL
        if search_type == "comment":
            tags = "comment"
        elif search_type == "story":
            tags = "story"
        else:
            tags = "(story,comment)"

        try:
            url = (
                f"{self.BASE_URL}/search?"
                f"query={urllib.parse.quote(query)}"
                f"&tags={tags}"
                f"&hitsPerPage={self.max_results}"
            )

            req = urllib.request.Request(
                url,
                headers={"User-Agent": "B2BAccountAgent/1.0"}
            )

            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode())

            hits = data.get("hits", [])

            if not hits:
                return {
                    "success": True,
                    "query": query,
                    "results": [],
                    "result_count": 0,
                    "message": f"No HackerNews discussions found for: {query}"
                }

            # Process results
            results = []
            for hit in hits:
                result = {
                    "type": "story" if hit.get("story_id") is None else "comment",
                    "title": hit.get("title") or hit.get("story_title"),
                    "url": hit.get("url"),
                    "points": hit.get("points", 0),
                    "author": hit.get("author"),
                    "created_at": hit.get("created_at"),
                    "num_comments": hit.get("num_comments", 0),
                    "hn_url": f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                }

                # Add text snippet for comments
                if hit.get("comment_text"):
                    text = hit.get("comment_text", "")
                    # Clean HTML
                    text = text.replace("<p>", " ").replace("</p>", " ")
                    result["text_snippet"] = text[:300] + "..." if len(text) > 300 else text

                results.append(result)

            # Calculate basic sentiment indicators
            total_points = sum(r.get("points", 0) for r in results if r.get("points"))
            total_comments = sum(r.get("num_comments", 0) for r in results if r.get("num_comments"))

            # Find most recent mention
            dates = [r.get("created_at") for r in results if r.get("created_at")]
            most_recent = max(dates) if dates else None

            return {
                "success": True,
                "query": query,
                "results": results,
                "result_count": len(results),
                "total_points": total_points,
                "total_comments": total_comments,
                "most_recent_mention": most_recent,
                "search_type": search_type
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"HackerNews error: {error_msg}")

            return {
                "success": False,
                "error": f"HackerNews search failed: {error_msg}",
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
                        "Search query for HackerNews. "
                        "Examples: 'Stripe', 'OpenAI GPT', 'Tesla Autopilot'"
                    )
                },
                "search_type": {
                    "type": "string",
                    "description": (
                        "Type of content to search. Default: 'story'. "
                        "Options: 'story' (articles), 'comment' (discussions), 'all'"
                    ),
                    "default": "story"
                }
            },
            "required": ["query"]
        }

    @staticmethod
    def is_available() -> bool:
        """HackerNews API is always available."""
        return True
