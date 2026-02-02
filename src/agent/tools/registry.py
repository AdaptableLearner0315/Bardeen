"""Tool Registry for managing and orchestrating tools."""

import logging
from typing import Dict, Any, Optional, List, Type, Set
from dataclasses import dataclass, field
from enum import Enum

from src.agent.tools.base import BaseTool, ToolResult
from src.shared.models import ToolMode
from src.shared.config import ResearchMode
from src.shared.exceptions import ToolNotFoundError, ToolUnavailableError

logger = logging.getLogger(__name__)


@dataclass
class ToolConfig:
    """Configuration for a registered tool."""
    tool_class: Type[BaseTool]
    mode: ToolMode
    fallback_tool: Optional[str] = None
    timeout: float = 10.0
    max_retries: int = 2
    enabled: bool = True
    description_override: Optional[str] = None

    def create_instance(self, **kwargs) -> BaseTool:
        """Create a tool instance with configured settings."""
        return self.tool_class(
            timeout=kwargs.get("timeout", self.timeout),
            max_retries=kwargs.get("max_retries", self.max_retries),
            **{k: v for k, v in kwargs.items() if k not in ("timeout", "max_retries")}
        )


class ToolRegistry:
    """
    Central registry for managing all available tools.

    Features:
    - Tool registration and discovery
    - Mode-based tool filtering (Normal vs Deep)
    - Fallback chain management
    - Tool execution with automatic fallback
    - LLM-compatible tool definitions
    """

    def __init__(self):
        """Initialize empty registry."""
        self._tools: Dict[str, ToolConfig] = {}
        self._instances: Dict[str, BaseTool] = {}
        self._fallback_chains: Dict[str, List[str]] = {}

    def register(
        self,
        name: str,
        tool_class: Type[BaseTool],
        mode: ToolMode = ToolMode.CORE,
        fallback_tool: Optional[str] = None,
        timeout: float = 10.0,
        max_retries: int = 2,
        enabled: bool = True,
        **kwargs
    ) -> None:
        """
        Register a tool with the registry.

        Args:
            name: Unique tool name
            tool_class: Tool class (must inherit from BaseTool)
            mode: Tool mode (CORE or EXTENDED)
            fallback_tool: Name of fallback tool if this one fails
            timeout: Default timeout in seconds
            max_retries: Default max retries
            enabled: Whether tool is enabled
            **kwargs: Additional tool-specific configuration
        """
        if not issubclass(tool_class, BaseTool):
            raise ValueError(f"Tool class must inherit from BaseTool: {tool_class}")

        self._tools[name] = ToolConfig(
            tool_class=tool_class,
            mode=mode,
            fallback_tool=fallback_tool,
            timeout=timeout,
            max_retries=max_retries,
            enabled=enabled,
        )

        # Clear cached instance if re-registering
        if name in self._instances:
            del self._instances[name]

        # Rebuild all fallback chains (since new tool might be a fallback for others)
        self._rebuild_all_fallback_chains()

        logger.debug(f"Registered tool: {name} (mode={mode.value})")

    def unregister(self, name: str) -> bool:
        """
        Unregister a tool from the registry.

        Args:
            name: Tool name to unregister

        Returns:
            True if tool was unregistered, False if not found
        """
        if name in self._tools:
            del self._tools[name]
            if name in self._instances:
                del self._instances[name]
            if name in self._fallback_chains:
                del self._fallback_chains[name]
            logger.debug(f"Unregistered tool: {name}")
            return True
        return False

    def get_tool(self, name: str) -> BaseTool:
        """
        Get a tool instance by name.

        Args:
            name: Tool name

        Returns:
            Tool instance

        Raises:
            ToolNotFoundError: If tool not found
        """
        if name not in self._tools:
            raise ToolNotFoundError(name)

        config = self._tools[name]

        if not config.enabled:
            raise ToolUnavailableError(name, "Tool is disabled")

        # Create instance if not cached
        if name not in self._instances:
            instance = config.create_instance()

            # Set up fallback chain
            if config.fallback_tool and config.fallback_tool in self._tools:
                try:
                    fallback_instance = self.get_tool(config.fallback_tool)
                    instance.set_fallback(fallback_instance)
                except (ToolNotFoundError, ToolUnavailableError):
                    logger.warning(f"Fallback tool {config.fallback_tool} not available for {name}")

            self._instances[name] = instance

        return self._instances[name]

    def get_tools_for_mode(self, mode: ResearchMode) -> List[BaseTool]:
        """
        Get all tools available for a research mode.

        Args:
            mode: Research mode (NORMAL or DEEP)

        Returns:
            List of available tool instances
        """
        tools = []

        for name, config in self._tools.items():
            if not config.enabled:
                continue

            # In NORMAL mode, only CORE tools
            # In DEEP mode, all tools
            if mode == ResearchMode.NORMAL and config.mode != ToolMode.CORE:
                continue

            try:
                tool = self.get_tool(name)
                tools.append(tool)
            except (ToolNotFoundError, ToolUnavailableError) as e:
                logger.warning(f"Could not get tool {name}: {e}")

        return tools

    def get_tool_definitions(self, mode: ResearchMode) -> List[Dict[str, Any]]:
        """
        Get tool definitions for LLM tool calling.

        Args:
            mode: Research mode to filter tools

        Returns:
            List of tool definitions compatible with Claude API
        """
        definitions = []

        for name, config in self._tools.items():
            if not config.enabled:
                continue

            # Filter by mode
            if mode == ResearchMode.NORMAL and config.mode != ToolMode.CORE:
                continue

            try:
                tool = self.get_tool(name)
                definition = tool.get_tool_definition()

                # Apply description override if set
                if config.description_override:
                    definition["description"] = config.description_override

                definitions.append(definition)
            except (ToolNotFoundError, ToolUnavailableError) as e:
                logger.warning(f"Could not get definition for {name}: {e}")

        return definitions

    def get_tool_names(self, mode: Optional[ResearchMode] = None) -> List[str]:
        """
        Get names of all registered tools.

        Args:
            mode: Optional mode filter

        Returns:
            List of tool names
        """
        names = []

        for name, config in self._tools.items():
            if not config.enabled:
                continue

            if mode is not None:
                if mode == ResearchMode.NORMAL and config.mode != ToolMode.CORE:
                    continue

            names.append(name)

        return names

    def execute_tool(
        self,
        name: str,
        params: Dict[str, Any],
        mode: ResearchMode = ResearchMode.DEEP,
        tracer: Optional[Any] = None,
    ) -> ToolResult:
        """
        Execute a tool by name with parameters.

        Args:
            name: Tool name
            params: Tool parameters
            mode: Current research mode
            tracer: Optional tracer for logging

        Returns:
            ToolResult with execution outcome
        """
        # Check if tool exists
        if name not in self._tools:
            logger.error(f"Tool not found: {name}")
            return ToolResult(
                success=False,
                error=f"Tool not found: {name}",
                error_code="TOOL_NOT_FOUND",
                tool_name=name
            )

        config = self._tools[name]

        # Check mode compatibility
        if mode == ResearchMode.NORMAL and config.mode != ToolMode.CORE:
            logger.warning(f"Tool {name} not available in NORMAL mode")
            return ToolResult(
                success=False,
                error=f"Tool {name} is not available in Normal mode. Switch to Deep mode to use extended tools.",
                error_code="MODE_MISMATCH",
                tool_name=name
            )

        # Check if enabled
        if not config.enabled:
            logger.warning(f"Tool {name} is disabled")
            return ToolResult(
                success=False,
                error=f"Tool {name} is currently disabled",
                error_code="TOOL_DISABLED",
                tool_name=name
            )

        try:
            tool = self.get_tool(name)
            return tool.execute(tracer=tracer, **params)
        except Exception as e:
            logger.error(f"Tool execution error for {name}: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_code="EXECUTION_ERROR",
                tool_name=name
            )

    def _build_fallback_chain(self, name: str) -> None:
        """Build fallback chain for a tool to detect cycles."""
        if name not in self._tools:
            return

        chain = [name]
        visited = {name}
        current = name

        while True:
            config = self._tools.get(current)
            if not config or not config.fallback_tool:
                break

            fallback = config.fallback_tool
            if fallback in visited:
                logger.warning(f"Circular fallback detected: {chain} -> {fallback}")
                break

            if fallback not in self._tools:
                logger.warning(f"Fallback tool not registered: {fallback}")
                break

            chain.append(fallback)
            visited.add(fallback)
            current = fallback

        self._fallback_chains[name] = chain

    def _rebuild_all_fallback_chains(self) -> None:
        """Rebuild fallback chains for all registered tools."""
        for name in self._tools:
            self._build_fallback_chain(name)

    def get_fallback_chain(self, name: str) -> List[str]:
        """
        Get the fallback chain for a tool.

        Args:
            name: Tool name

        Returns:
            List of tool names in fallback order
        """
        return self._fallback_chains.get(name, [name])

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        core_count = sum(1 for c in self._tools.values() if c.mode == ToolMode.CORE and c.enabled)
        extended_count = sum(1 for c in self._tools.values() if c.mode == ToolMode.EXTENDED and c.enabled)
        disabled_count = sum(1 for c in self._tools.values() if not c.enabled)

        tool_stats = {}
        for name, instance in self._instances.items():
            tool_stats[name] = instance.get_stats()

        return {
            "total_tools": len(self._tools),
            "core_tools": core_count,
            "extended_tools": extended_count,
            "disabled_tools": disabled_count,
            "cached_instances": len(self._instances),
            "tool_stats": tool_stats
        }

    def reset(self) -> None:
        """Reset registry to empty state."""
        self._tools.clear()
        self._instances.clear()
        self._fallback_chains.clear()

    def is_registered(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools

    def is_available(self, name: str, mode: ResearchMode = ResearchMode.DEEP) -> bool:
        """
        Check if a tool is available for use.

        Args:
            name: Tool name
            mode: Research mode

        Returns:
            True if tool is available
        """
        if name not in self._tools:
            return False

        config = self._tools[name]

        if not config.enabled:
            return False

        if mode == ResearchMode.NORMAL and config.mode != ToolMode.CORE:
            return False

        return True

    def __len__(self) -> int:
        """Return number of registered tools."""
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        """Check if tool is registered."""
        return name in self._tools


def create_default_registry() -> ToolRegistry:
    """
    Create a registry with all default tools configured.

    Returns:
        Configured ToolRegistry instance
    """
    from src.agent.tools.research import (
        DuckDuckGoSearchTool,
        WikipediaTool,
        CalculatorTool,
        YahooFinanceTool,
        SECEdgarTool,
        GitHubTool,
        HackerNewsTool,
        WebScraperTool,
    )

    registry = ToolRegistry()

    # Core Tools
    registry.register(
        name="web_search",
        tool_class=DuckDuckGoSearchTool,
        mode=ToolMode.CORE,
        fallback_tool="wikipedia",
        timeout=10.0,
        max_retries=2,
    )

    registry.register(
        name="wikipedia",
        tool_class=WikipediaTool,
        mode=ToolMode.CORE,
        fallback_tool=None,
        timeout=5.0,
        max_retries=2,
    )

    registry.register(
        name="calculator",
        tool_class=CalculatorTool,
        mode=ToolMode.CORE,
        fallback_tool=None,
        timeout=1.0,
        max_retries=0,
    )

    # Extended Tools
    registry.register(
        name="yahoo_finance",
        tool_class=YahooFinanceTool,
        mode=ToolMode.EXTENDED,
        fallback_tool="web_search",
        timeout=10.0,
        max_retries=2,
    )

    registry.register(
        name="sec_edgar",
        tool_class=SECEdgarTool,
        mode=ToolMode.EXTENDED,
        fallback_tool="web_search",
        timeout=15.0,
        max_retries=2,
    )

    registry.register(
        name="github",
        tool_class=GitHubTool,
        mode=ToolMode.EXTENDED,
        fallback_tool="web_search",
        timeout=10.0,
        max_retries=2,
    )

    registry.register(
        name="hackernews",
        tool_class=HackerNewsTool,
        mode=ToolMode.EXTENDED,
        fallback_tool="web_search",
        timeout=5.0,
        max_retries=2,
    )

    registry.register(
        name="web_scraper",
        tool_class=WebScraperTool,
        mode=ToolMode.EXTENDED,
        fallback_tool=None,
        timeout=15.0,
        max_retries=1,
    )

    logger.info(f"Created default registry with {len(registry)} tools")

    return registry


# Singleton instance
_default_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get the default tool registry singleton."""
    global _default_registry
    if _default_registry is None:
        _default_registry = create_default_registry()
    return _default_registry


def reset_registry() -> None:
    """Reset the default registry singleton."""
    global _default_registry
    if _default_registry:
        _default_registry.reset()
    _default_registry = None
