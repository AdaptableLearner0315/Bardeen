"""Wikipedia search and retrieval tool."""

import wikipediaapi
from typing import Dict, Any, Optional


class Wikipedia:
    """
    Wikipedia search and content retrieval tool.

    Uses the wikipedia-api library to fetch structured information from Wikipedia.
    """

    def __init__(self, language: str = "en", timeout: int = 10):
        """
        Initialize Wikipedia tool.

        Args:
            language: Wikipedia language edition (default: "en")
            timeout: Request timeout in seconds
        """
        self.language = language
        self.timeout = timeout
        self.wiki = wikipediaapi.Wikipedia(
            language=language,
            user_agent='ResearchAssistantAgent/1.0'
        )

    def search(self, title: str, auto_suggest: bool = True) -> Dict[str, Any]:
        """
        Search for a Wikipedia page and return key information.

        Args:
            title: Page title to search for
            auto_suggest: Whether to enable auto-suggest for page titles

        Returns:
            Dictionary with page information or error
        """
        try:
            # Get the page
            page = self.wiki.page(title)

            if not page.exists():
                return {
                    "success": False,
                    "error": f"Page '{title}' not found on Wikipedia",
                    "title": title
                }

            # Extract key information
            result = {
                "success": True,
                "title": page.title,
                "summary": page.summary[:1000] if page.summary else "",  # First 1000 chars
                "url": page.fullurl,
                "categories": [cat for cat in list(page.categories.keys())[:5]],  # Top 5 categories
            }

            # Try to extract common infobox data if available
            infobox_data = self._extract_infobox_data(page)
            if infobox_data:
                result["data"] = infobox_data

            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Error accessing Wikipedia: {str(e)}",
                "title": title
            }

    def _extract_infobox_data(self, page) -> Optional[Dict[str, Any]]:
        """
        Attempt to extract common infobox data from page text.

        This is a simple parser that looks for common patterns.
        For production, you'd want a more robust parser.
        """
        # This is a simplified version - in practice, you'd use the text
        # or parse the page content more carefully
        text = page.text
        data = {}

        # Common patterns (very basic extraction)
        patterns = {
            "population": ["Population:", "population"],
            "area": ["Area:", "area"],
            "capital": ["Capital:", "capital"],
            "founded": ["Founded:", "Established:"],
            "born": ["Born:", "born"],
            "died": ["Died:", "died"],
        }

        # Note: This is a very basic implementation
        # A real implementation would parse the infobox structure
        # For now, we'll just return None and rely on the summary
        return None

    def get_tool_definition(self) -> Dict[str, Any]:
        """Get tool definition for LLM tool calling."""
        return {
            "name": "wikipedia",
            "description": (
                "Search Wikipedia for factual information. Returns a summary, "
                "URL, and key data from Wikipedia articles. Use this for getting "
                "factual information about people, places, events, and concepts. "
                "Especially useful for population, area, historical dates, and biographical information."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": (
                            "The title of the Wikipedia page to search for. "
                            "Examples: 'France', 'Albert Einstein', '2022 FIFA World Cup'"
                        )
                    }
                },
                "required": ["title"]
            }
        }

    def __call__(self, title: str) -> Dict[str, Any]:
        """
        Execute the Wikipedia tool.

        Args:
            title: Page title to search for

        Returns:
            Dictionary with page information or error
        """
        return self.search(title)
