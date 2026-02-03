"""Query classification logic for auto-detecting research depth.

This module determines whether a query requires normal or deep research mode
based on complexity indicators.
"""

import re
from typing import Dict, List
from src.shared.config import QUERY_PATTERNS


class QueryClassifier:
    """Classifies queries to determine appropriate research depth.

    Uses regex patterns to detect query complexity and recommend
    normal vs deep research mode.

    Attributes:
        deep_patterns: Compiled regex patterns for deep research indicators
        simple_patterns: Compiled regex patterns for simple query indicators
    """

    def __init__(self):
        """Initialize classifier with compiled regex patterns."""
        self.deep_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in QUERY_PATTERNS["deep_indicators"]
        ]
        self.simple_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in QUERY_PATTERNS["simple_indicators"]
        ]

    def is_deep_research(self, query: str) -> bool:
        """Determine if query requires deep research mode.

        Args:
            query: User query string

        Returns:
            True if deep research recommended, False otherwise

        Logic:
            1. Check for simple indicators (high confidence → normal mode)
            2. Check for deep indicators (high confidence → deep mode)
            3. Default to normal mode for ambiguous queries

        Examples:
            >>> classifier = QueryClassifier()
            >>> classifier.is_deep_research("What is Python?")
            False
            >>> classifier.is_deep_research("Research comprehensive Python history")
            True
        """
        if not query:
            return False

        # Check simple indicators first
        for pattern in self.simple_patterns:
            if pattern.search(query):
                return False

        # Check deep indicators
        for pattern in self.deep_patterns:
            if pattern.search(query):
                return True

        # Default to normal mode
        return False
