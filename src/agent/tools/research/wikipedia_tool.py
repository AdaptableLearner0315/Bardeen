"""Wikipedia search and retrieval tool implementation."""

import logging
from typing import Dict, Any, Optional, List

from src.agent.tools.base import BaseTool, RateLimiter
from src.shared.models import ToolMode

logger = logging.getLogger(__name__)

# Try to import wikipedia-api
try:
    import wikipediaapi
    WIKIPEDIA_AVAILABLE = True
except ImportError:
    wikipediaapi = None
    WIKIPEDIA_AVAILABLE = False


class WikipediaTool(BaseTool):
    """
    Wikipedia search and content retrieval tool.

    Provides factual information from Wikipedia articles.
    Excellent for historical data, company backgrounds, and verified facts.
    """

    TOOL_NAME = "wikipedia"
    TOOL_DESCRIPTION = (
        "Search Wikipedia for factual information. Returns article summaries, "
        "URLs, and key data. Use this for getting verified information about "
        "companies, people, places, events, and concepts. "
        "Especially useful for historical facts, founding dates, and background information."
    )
    TOOL_MODE = ToolMode.CORE
    DEFAULT_TIMEOUT = 5.0
    MAX_RETRIES = 2
    CACHE_TTL = 86400.0  # 24 hour cache for Wikipedia content

    RATE_LIMIT_RPS = 10.0  # Wikipedia is generous
    RATE_LIMIT_BURST = 10

    def __init__(
        self,
        language: str = "en",
        max_summary_length: int = 2000,
        user_agent: str = "B2BAccountAgent/1.0",
        **kwargs
    ):
        """
        Initialize Wikipedia tool.

        Args:
            language: Wikipedia language edition (default: en)
            max_summary_length: Maximum summary length to return
            user_agent: User agent for Wikipedia API
            **kwargs: Additional BaseTool arguments
        """
        super().__init__(**kwargs)

        self.language = language
        self.max_summary_length = max_summary_length
        self.user_agent = user_agent

        if WIKIPEDIA_AVAILABLE:
            self._wiki = wikipediaapi.Wikipedia(
                language=language,
                user_agent=user_agent
            )
        else:
            self._wiki = None
            logger.warning(
                "wikipedia-api not installed. "
                "Install with: pip install wikipedia-api"
            )

    def _execute(self, title: str) -> Dict[str, Any]:
        """
        Search for a Wikipedia page.

        Args:
            title: Page title to search for

        Returns:
            Dictionary with page information
        """
        if not WIKIPEDIA_AVAILABLE:
            return {
                "success": False,
                "error": "Wikipedia API not available. Install wikipedia-api package.",
                "title": title
            }

        # Validate input
        if not title or not title.strip():
            return {
                "success": False,
                "error": "Empty search title",
                "title": title
            }

        title = title.strip()

        try:
            page = self._wiki.page(title)

            if not page.exists():
                # Try with different capitalization
                alt_title = title.title()  # Capitalize first letter of each word
                if alt_title != title:
                    page = self._wiki.page(alt_title)

                if not page.exists():
                    return {
                        "success": False,
                        "error": f"No Wikipedia page found for: {title}",
                        "title": title,
                        "suggestions": self._get_suggestions(title)
                    }

            # Check if it's a disambiguation page
            if "disambiguation" in page.title.lower() or self._is_disambiguation(page):
                options = self._extract_disambiguation_options(page)
                return {
                    "success": True,
                    "is_disambiguation": True,
                    "title": page.title,
                    "message": f"'{title}' is ambiguous. Please specify:",
                    "options": options[:5],  # Top 5 options
                    "url": page.fullurl
                }

            # Extract summary
            summary = page.summary
            if len(summary) > self.max_summary_length:
                summary = summary[:self.max_summary_length] + "..."

            # Check if it's a stub
            is_stub = len(page.text) < 500

            result = {
                "success": True,
                "title": page.title,
                "summary": summary,
                "url": page.fullurl,
                "categories": list(page.categories.keys())[:5],
            }

            if is_stub:
                result["note"] = "Limited information available (stub article)"

            # Try to extract structured data
            sections = self._extract_sections(page)
            if sections:
                result["sections"] = sections

            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Wikipedia error for '{title}': {error_msg}")

            return {
                "success": False,
                "error": f"Wikipedia lookup failed: {error_msg}",
                "title": title
            }

    def _is_disambiguation(self, page) -> bool:
        """Check if a page is a disambiguation page."""
        categories = page.categories.keys()
        return any(
            "disambiguation" in cat.lower()
            for cat in categories
        )

    def _extract_disambiguation_options(self, page) -> List[str]:
        """Extract options from a disambiguation page."""
        options = []
        text = page.text

        # Simple extraction - look for lines that look like options
        for line in text.split("\n"):
            line = line.strip()
            if line and not line.startswith("==") and len(line) < 200:
                # Remove common wiki markup
                if not any(x in line.lower() for x in ["may refer to", "see also"]):
                    options.append(line)

        return options[:10]

    def _extract_sections(self, page) -> Dict[str, str]:
        """Extract key sections from the page."""
        sections = {}
        key_sections = ["History", "Overview", "Description", "Background"]

        for section_name in key_sections:
            section = page.section_by_title(section_name)
            if section:
                text = section.text
                if text and len(text) > 50:
                    sections[section_name] = text[:500] + "..." if len(text) > 500 else text

        return sections

    def _get_suggestions(self, title: str) -> List[str]:
        """Get search suggestions for a failed lookup."""
        # Simple suggestions - just variations
        suggestions = []

        # Try without special characters
        clean_title = "".join(c for c in title if c.isalnum() or c.isspace())
        if clean_title != title:
            suggestions.append(clean_title)

        # Try with (company) suffix for business queries
        if not any(x in title.lower() for x in ["company", "inc", "corp", "llc"]):
            suggestions.append(f"{title} (company)")

        return suggestions[:3]

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool input."""
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": (
                        "The Wikipedia page title to search for. "
                        "Examples: 'Stripe (company)', 'Amazon (company)', "
                        "'Artificial intelligence', 'Cloud computing'"
                    )
                }
            },
            "required": ["title"]
        }

    @staticmethod
    def is_available() -> bool:
        """Check if Wikipedia API is available."""
        return WIKIPEDIA_AVAILABLE
