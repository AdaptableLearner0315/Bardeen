"""Perplexity API for deep research."""
import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Check if OpenAI package is available (used for Perplexity API)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not available, Perplexity tool will be disabled")


@dataclass
class PerplexityResult:
    """Result from Perplexity search."""
    answer: str
    model: str
    citations: List[str]
    success: bool = True
    error: Optional[str] = None


class PerplexityTool:
    """
    Deep research using Perplexity AI.

    Uses OpenAI-compatible API to access Perplexity's search models:
    - sonar: Quick search (127k context)
    - sonar-pro: Deep research (200k context)
    - sonar-reasoning: Analysis tasks (127k context)
    """

    TOOL_NAME = "perplexity_search"
    TOOL_DESCRIPTION = """Deep research using Perplexity AI. Use for:
- Comprehensive research requiring multiple sources
- Questions needing citations and verification
- Complex multi-part queries
- Current events and recent information
Returns synthesized answers with source citations."""

    MODELS = {
        "normal": "sonar",
        "deep": "sonar-pro",
        "reasoning": "sonar-reasoning"
    }

    def __init__(self, api_key: Optional[str] = None, timeout: int = 60):
        """
        Initialize Perplexity tool.

        Args:
            api_key: Perplexity API key (or set PERPLEXITY_API_KEY env var)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        self.timeout = timeout
        self._client = None
        self._available = False

        if not OPENAI_AVAILABLE:
            logger.warning("Perplexity tool unavailable: OpenAI package not installed")
            return

        if not self.api_key:
            logger.warning("Perplexity tool unavailable: PERPLEXITY_API_KEY not set")
            return

        try:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.perplexity.ai",
                timeout=self.timeout
            )
            self._available = True
            logger.info("Perplexity tool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Perplexity client: {e}")

    @property
    def is_available(self) -> bool:
        """Check if tool is available."""
        return self._available

    def search(self, query: str, deep: bool = False) -> Dict[str, Any]:
        """
        Search using Perplexity AI.

        Args:
            query: The search/research query
            deep: Use deep research mode (sonar-pro) for comprehensive results

        Returns:
            Dict with answer, model used, citations, and status
        """
        if not self._available:
            return {
                "success": False,
                "error": "Perplexity tool not available",
                "answer": None,
                "model": None,
                "citations": []
            }

        model = self.MODELS["deep"] if deep else self.MODELS["normal"]

        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Be precise and comprehensive. Always cite your sources when possible."
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ]
            )

            answer = response.choices[0].message.content

            # Try to extract citations if available
            citations = []
            if hasattr(response, 'citations'):
                citations = response.citations
            elif hasattr(response.choices[0].message, 'citations'):
                citations = response.choices[0].message.citations

            return {
                "success": True,
                "answer": answer,
                "model": model,
                "citations": citations or [],
                "usage": {
                    "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0),
                    "completion_tokens": getattr(response.usage, 'completion_tokens', 0)
                }
            }

        except Exception as e:
            logger.error(f"Perplexity search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "answer": None,
                "model": model,
                "citations": []
            }

    def __call__(self, query: str, deep: bool = False) -> Dict[str, Any]:
        """Make tool callable."""
        return self.search(query, deep)

    def get_tool_definition(self) -> Dict[str, Any]:
        """Get Claude tool definition."""
        return {
            "name": self.TOOL_NAME,
            "description": self.TOOL_DESCRIPTION,
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The research query or question to investigate"
                    },
                    "deep": {
                        "type": "boolean",
                        "description": "Use deep research mode for comprehensive multi-source analysis. Default is false for faster results.",
                        "default": False
                    }
                },
                "required": ["query"]
            }
        }


# Factory function
def create_perplexity_tool(api_key: Optional[str] = None) -> Optional[PerplexityTool]:
    """
    Create Perplexity tool if available.

    Returns:
        PerplexityTool instance if available, None otherwise
    """
    tool = PerplexityTool(api_key=api_key)
    return tool if tool.is_available else None
