"""Agent tools module.

This module provides:
- Base tool infrastructure (BaseTool, RateLimiter)
- Tool registry for managing and orchestrating tools
- Core tools (WebSearch, Wikipedia, Calculator)
- Extended tools (Yahoo Finance, SEC EDGAR, GitHub, HackerNews, etc.)
"""

from .base import (
    BaseTool,
    ToolResult,
    RateLimiter,
    RateLimitConfig,
    RateLimiters,
    with_rate_limit,
    with_timeout,
)
from .registry import (
    ToolRegistry,
    ToolConfig,
    create_default_registry,
    get_registry,
    reset_registry,
)
from .calculator import Calculator
from .wikipedia import Wikipedia
from .web_search import WebSearch

__all__ = [
    # Base infrastructure
    "BaseTool",
    "ToolResult",
    "RateLimiter",
    "RateLimitConfig",
    "RateLimiters",
    "with_rate_limit",
    "with_timeout",
    # Registry
    "ToolRegistry",
    "ToolConfig",
    "create_default_registry",
    "get_registry",
    "reset_registry",
    # Legacy Core tools (kept for backward compatibility)
    "Calculator",
    "Wikipedia",
    "WebSearch",
]
