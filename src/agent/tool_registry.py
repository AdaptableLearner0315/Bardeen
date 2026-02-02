"""Tool registry for managing and executing tools."""

from typing import Dict, Any, List, Optional, Callable
import time
import hashlib
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

from .tools.calculator import Calculator
from .tools.wikipedia import Wikipedia
from .tools.web_search import WebSearch
from .tools.duckduckgo_search import DuckDuckGoSearch, DDGS_AVAILABLE
from .tools.gmail import Gmail, GOOGLE_API_AVAILABLE as GMAIL_AVAILABLE
from .tools.google_calendar import GoogleCalendar, GOOGLE_API_AVAILABLE as CALENDAR_AVAILABLE
from .tools.perplexity import PerplexityTool, create_perplexity_tool
from ..evaluation.tracers.tool_tracer import ToolTracer, TraceHelper
from ..evaluation.tracers.error_tracer import ErrorTracer
from ..shared.models import ToolStatus
from ..shared.config import ResearchMode


class ToolMode(Enum):
    """Tool mode for categorizing tools."""
    CORE = "core"          # Available in all modes
    EXTENDED = "extended"  # Only in deep/extended mode


@dataclass
class ToolConfig:
    """Configuration for a registered tool."""
    tool_class: type
    mode: ToolMode
    timeout: float
    enabled: bool = True
    description_override: Optional[str] = None


class ToolRegistry:
    """
    Manages tool registration and execution with tracing support.

    Handles:
    - Tool registration and retrieval
    - Tool execution with error handling
    - Fallback strategies when tools fail
    - Integration with tracers for evaluation
    """

    def __init__(self, config):
        """
        Initialize tool registry.

        Args:
            config: Application configuration
        """
        self.config = config
        self.tools: Dict[str, Any] = {}
        self._tools: Dict[str, ToolConfig] = {}  # Tool configurations
        self._instances: Dict[str, Any] = {}  # Tool instances
        self.tool_modes: Dict[str, ToolMode] = {}  # Track tool modes
        self.fallback_chains: Dict[str, List[str]] = {}

        # Register tools
        self._register_default_tools()
        self._setup_fallback_chains()

    def _register_default_tools(self):
        """Register the default set of tools."""
        # Calculator
        calculator = Calculator(
            max_expression_length=self.config.tools.calculator_max_expression_length
        )
        self.register_tool("calculator", calculator)

        # Wikipedia
        wikipedia = Wikipedia(
            language=self.config.tools.wikipedia_lang,
            timeout=self.config.tools.wikipedia_timeout
        )
        self.register_tool("wikipedia", wikipedia)

        # Web Search - DuckDuckGo (free, no API key required) as primary
        # Falls back to Tavily if DuckDuckGo is not available
        web_search_initialized = False

        if DDGS_AVAILABLE:
            try:
                web_search = DuckDuckGoSearch(
                    max_results=self.config.tools.web_search_max_results,
                    timeout=self.config.tools.web_search_timeout
                )
                self.register_tool("web_search", web_search)
                web_search_initialized = True
                print("Web search: DuckDuckGo initialized (free, real-time search enabled)")
            except Exception as e:
                print(f"Warning: Could not initialize DuckDuckGo search: {e}")

        # Tavily as fallback if DuckDuckGo not available
        if not web_search_initialized and self.config.tools.tavily_api_key:
            try:
                web_search = WebSearch(
                    api_key=self.config.tools.tavily_api_key,
                    max_results=self.config.tools.tavily_max_results,
                    timeout=self.config.tools.tavily_timeout
                )
                self.register_tool("web_search", web_search)
                web_search_initialized = True
                print("Web search: Tavily initialized (API key provided)")
            except Exception as e:
                print(f"Warning: Could not initialize Tavily search: {e}")

        if not web_search_initialized:
            print("Warning: No web search tool available. Install duckduckgo-search or provide TAVILY_API_KEY.")

        # Gmail (if Google API is available)
        if GMAIL_AVAILABLE:
            try:
                gmail = Gmail(
                    timeout=getattr(self.config.tools, 'gmail_timeout', 10)
                )
                self.register_tool("gmail", gmail)
            except Exception as e:
                print(f"Warning: Could not initialize gmail tool: {e}")

        # Google Calendar (if Google API is available)
        if CALENDAR_AVAILABLE:
            try:
                calendar = GoogleCalendar(
                    timeout=getattr(self.config.tools, 'calendar_timeout', 10)
                )
                self.register_tool("google_calendar", calendar)
            except Exception as e:
                print(f"Warning: Could not initialize google_calendar tool: {e}")

        # Perplexity for deep research (requires API key)
        try:
            perplexity = create_perplexity_tool()
            if perplexity and perplexity.is_available:
                self.register(
                    name="perplexity_search",
                    tool_class=type(perplexity),
                    mode=ToolMode.EXTENDED,
                    timeout=60.0,
                    description_override="Deep research using Perplexity AI with citations"
                )
                self._instances["perplexity_search"] = perplexity
                logger.info("Perplexity tool registered for deep research")
        except Exception as e:
            logger.warning(f"Perplexity tool not available: {e}")

    def _setup_fallback_chains(self):
        """Set up fallback chains for error recovery."""
        # If web_search fails, try wikipedia
        self.fallback_chains["web_search"] = ["wikipedia"]

        # Calculator has no fallback (it's deterministic)
        self.fallback_chains["calculator"] = []

        # Wikipedia has no fallback
        self.fallback_chains["wikipedia"] = []

        # Gmail has no fallback
        self.fallback_chains["gmail"] = []

        # Google Calendar has no fallback
        self.fallback_chains["google_calendar"] = []

        # Perplexity has no fallback
        self.fallback_chains["perplexity_search"] = []

    def register(
        self,
        name: str,
        tool_class: type,
        mode: ToolMode = ToolMode.CORE,
        timeout: float = 30.0,
        description_override: Optional[str] = None
    ):
        """
        Register a tool with configuration.

        Args:
            name: Tool name
            tool_class: Tool class type
            mode: Tool mode (CORE or EXTENDED)
            timeout: Execution timeout
            description_override: Optional description to override default
        """
        config = ToolConfig(
            tool_class=tool_class,
            mode=mode,
            timeout=timeout,
            enabled=True,
            description_override=description_override
        )
        self._tools[name] = config
        self.tool_modes[name] = mode

    def _get_or_create_instance(self, name: str) -> Optional[Any]:
        """
        Get or create a tool instance.

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not available
        """
        # Check if instance already exists
        if name in self._instances:
            return self._instances[name]

        # Check if tool is in legacy tools dict
        if name in self.tools:
            return self.tools[name]

        # Tool config must exist
        if name not in self._tools:
            return None

        # Would need to create instance - but for now we pre-create
        return None

    def register_tool(self, name: str, tool: Any):
        """
        Register a tool.

        Args:
            name: Tool name (must match LLM tool definition)
            tool: Tool instance (must be callable and have get_tool_definition())
        """
        if not callable(tool):
            raise ValueError(f"Tool {name} must be callable")

        if not hasattr(tool, 'get_tool_definition'):
            raise ValueError(f"Tool {name} must have get_tool_definition() method")

        self.tools[name] = tool

    def get_tool_definitions(self, mode: Optional[ResearchMode] = None) -> List[Dict[str, Any]]:
        """
        Get tool definitions for LLM, optionally filtered by research mode.

        Args:
            mode: If provided, filter tools by mode (NORMAL only gets CORE tools)

        Returns:
            List of tool definitions in Claude format
        """
        definitions = []

        # First, get definitions from legacy tools dict (these are CORE tools)
        for name, tool in self.tools.items():
            # Skip if filtering by mode and this tool has an EXTENDED mode
            if mode == ResearchMode.NORMAL and self.tool_modes.get(name) == ToolMode.EXTENDED:
                continue  # Skip extended tools in normal mode

            try:
                definition = tool.get_tool_definition()
                definitions.append(definition)
            except Exception as e:
                logger.warning(f"Failed to get definition for {name}: {e}")

        # Then, get definitions from new _tools dict (mode-aware tools)
        for name, config in self._tools.items():
            if not config.enabled:
                continue

            # Filter by mode if specified
            if mode == ResearchMode.NORMAL and config.mode == ToolMode.EXTENDED:
                continue  # Skip extended tools in normal mode

            try:
                tool = self._get_or_create_instance(name)
                if tool:
                    definition = tool.get_tool_definition()
                    if config.description_override:
                        definition["description"] = config.description_override
                    definitions.append(definition)
            except Exception as e:
                logger.warning(f"Failed to get definition for {name}: {e}")

        return definitions

    def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        tracer: Optional[ToolTracer] = None,
        error_tracer: Optional[ErrorTracer] = None,
        llm_reasoning: Optional[str] = None,
        allow_fallback: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a tool with tracing and error handling.

        Args:
            tool_name: Name of the tool to execute
            params: Tool parameters
            tracer: Optional tool tracer for evaluation
            error_tracer: Optional error tracer
            llm_reasoning: Optional LLM reasoning before tool call
            allow_fallback: Whether to try fallback tools on failure

        Returns:
            Tool execution result
        """
        # Check if tool exists (check both legacy tools and new instances)
        tool = self._get_or_create_instance(tool_name)
        if tool is None:
            error_msg = f"Unknown tool: {tool_name}"
            if error_tracer:
                error_tracer.record_error(
                    tool_name=tool_name,
                    error_type="unknown_tool",
                    error_message=error_msg,
                    attempted_params=params,
                    recovery_action="none",
                    recovery_success=False
                )
            return {
                "success": False,
                "error": error_msg
            }

        # Execute with tracing if available
        if tracer:
            with tracer.trace_tool_call(tool_name, params, llm_reasoning) as trace:
                result = self._execute_tool_with_error_handling(
                    tool=tool,
                    tool_name=tool_name,
                    params=params,
                    trace=trace,
                    error_tracer=error_tracer,
                    allow_fallback=allow_fallback
                )
                return result
        else:
            # Execute without tracing
            return self._execute_tool_with_error_handling(
                tool=tool,
                tool_name=tool_name,
                params=params,
                trace=None,
                error_tracer=error_tracer,
                allow_fallback=allow_fallback
            )

    def _execute_tool_with_error_handling(
        self,
        tool: Any,
        tool_name: str,
        params: Dict[str, Any],
        trace: Any,
        error_tracer: Optional[ErrorTracer],
        allow_fallback: bool
    ) -> Dict[str, Any]:
        """Execute tool with error handling and fallback support."""
        try:
            # Execute the tool
            result = tool(**params)

            # Update trace if available
            if trace:
                TraceHelper.set_result(trace, result)

            # Check if tool reported success
            if isinstance(result, dict) and not result.get("success", True):
                # Tool executed but reported failure
                error = result.get("error", "Unknown error")

                if trace:
                    TraceHelper.set_error(trace, error, ToolStatus.ERROR)

                # Try fallback if available
                if allow_fallback and tool_name in self.fallback_chains:
                    return self._try_fallback(
                        original_tool=tool_name,
                        params=params,
                        error=error,
                        trace=trace,
                        error_tracer=error_tracer
                    )

                # Record error
                if error_tracer:
                    error_tracer.record_error(
                        tool_name=tool_name,
                        error_type="tool_failure",
                        error_message=error,
                        attempted_params=params,
                        recovery_action="none",
                        recovery_success=False
                    )

                return result

            # Success
            return result

        except TimeoutError as e:
            error_msg = f"Tool execution timeout: {str(e)}"

            if trace:
                TraceHelper.set_error(trace, error_msg, ToolStatus.TIMEOUT)

            # Try fallback
            if allow_fallback and tool_name in self.fallback_chains:
                return self._try_fallback(
                    original_tool=tool_name,
                    params=params,
                    error=error_msg,
                    trace=trace,
                    error_tracer=error_tracer
                )

            if error_tracer:
                error_tracer.record_error(
                    tool_name=tool_name,
                    error_type="timeout",
                    error_message=error_msg,
                    attempted_params=params,
                    recovery_action="none",
                    recovery_success=False
                )

            return {
                "success": False,
                "error": error_msg
            }

        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"

            if trace:
                TraceHelper.set_error(trace, error_msg, ToolStatus.ERROR)

            # Try fallback
            if allow_fallback and tool_name in self.fallback_chains:
                return self._try_fallback(
                    original_tool=tool_name,
                    params=params,
                    error=error_msg,
                    trace=trace,
                    error_tracer=error_tracer
                )

            if error_tracer:
                error_tracer.record_error(
                    tool_name=tool_name,
                    error_type="exception",
                    error_message=error_msg,
                    attempted_params=params,
                    recovery_action="none",
                    recovery_success=False
                )

            return {
                "success": False,
                "error": error_msg
            }

    def _try_fallback(
        self,
        original_tool: str,
        params: Dict[str, Any],
        error: str,
        trace: Any,
        error_tracer: Optional[ErrorTracer]
    ) -> Dict[str, Any]:
        """Try fallback tools when primary tool fails."""
        fallback_tools = self.fallback_chains.get(original_tool, [])

        if not fallback_tools:
            return {
                "success": False,
                "error": error
            }

        # Try each fallback tool
        for fallback_tool_name in fallback_tools:
            if not self.has_tool(fallback_tool_name):
                continue

            # Attempt fallback
            fallback_result = self.execute_tool(
                tool_name=fallback_tool_name,
                params=params,
                tracer=None,  # Don't double-trace fallback
                error_tracer=None,
                allow_fallback=False  # Don't chain fallbacks
            )

            if fallback_result.get("success", False):
                # Fallback succeeded
                if trace:
                    TraceHelper.set_fallback(trace, fallback_tool_name)
                    trace.result = fallback_result

                if error_tracer:
                    error_tracer.record_error(
                        tool_name=original_tool,
                        error_type="tool_failure",
                        error_message=error,
                        attempted_params=params,
                        recovery_action=f"fallback_to_{fallback_tool_name}",
                        recovery_success=True
                    )

                return fallback_result

        # All fallbacks failed
        if error_tracer:
            error_tracer.record_error(
                tool_name=original_tool,
                error_type="tool_failure",
                error_message=error,
                attempted_params=params,
                recovery_action=f"tried_fallbacks_{','.join(fallback_tools)}",
                recovery_success=False
            )

        return {
            "success": False,
            "error": f"{error}. Fallback attempts also failed."
        }

    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is registered."""
        return tool_name in self.tools or tool_name in self._instances

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        # Combine both legacy tools and new instances
        all_tools = set(self.tools.keys()) | set(self._instances.keys())
        return list(all_tools)


class ToolCache:
    """Cache for tool results with TTL-based expiration."""

    TTL = {
        "wikipedia": timedelta(minutes=30),
        "calculator": timedelta(hours=1),
        "web_search": timedelta(minutes=5),
        "duckduckgo": timedelta(minutes=5),
    }

    MAX_SIZE = 500

    def __init__(self):
        self._cache = {}
        self._access_order = []

    def _hash_params(self, params: dict) -> str:
        """Create hash from parameters for cache key."""
        try:
            param_str = json.dumps(params, sort_keys=True)
            return hashlib.md5(param_str.encode()).hexdigest()
        except (TypeError, ValueError):
            return None

    def get(self, tool_name: str, params: dict) -> Optional[Dict[str, Any]]:
        """Get cached result if valid."""
        params_hash = self._hash_params(params)
        if not params_hash:
            return None

        key = f"{tool_name}:{params_hash}"
        if key in self._cache:
            result, timestamp = self._cache[key]
            ttl = self.TTL.get(tool_name, timedelta(minutes=15))
            if datetime.now() - timestamp < ttl:
                # Update access order for LRU
                if key in self._access_order:
                    self._access_order.remove(key)
                self._access_order.append(key)
                return result
            # Expired
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
        return None

    def set(self, tool_name: str, params: dict, result: Dict[str, Any]):
        """Cache a tool result."""
        params_hash = self._hash_params(params)
        if not params_hash:
            return

        key = f"{tool_name}:{params_hash}"

        # Evict if at max size
        while len(self._cache) >= self.MAX_SIZE and self._access_order:
            oldest_key = self._access_order.pop(0)
            if oldest_key in self._cache:
                del self._cache[oldest_key]

        self._cache[key] = (result, datetime.now())
        self._access_order.append(key)

    def clear(self):
        """Clear the cache."""
        self._cache.clear()
        self._access_order.clear()

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self.MAX_SIZE,
            "keys": list(self._cache.keys())[:10]  # First 10 for debugging
        }


# Global cache instance
_tool_cache: Optional[ToolCache] = None

def get_tool_cache() -> ToolCache:
    """Get or create global tool cache."""
    global _tool_cache
    if _tool_cache is None:
        _tool_cache = ToolCache()
    return _tool_cache

def reset_tool_cache():
    """Reset the global tool cache."""
    global _tool_cache
    _tool_cache = None
