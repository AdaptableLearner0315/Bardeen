"""Unit tests for agent/tools/registry.py."""

import pytest
from typing import Dict, Any
from unittest.mock import MagicMock, patch

from src.agent.tools.base import BaseTool, ToolResult
from src.agent.tools.registry import (
    ToolRegistry,
    ToolConfig,
    create_default_registry,
    get_registry,
    reset_registry,
)
from src.shared.models import ToolMode
from src.shared.config import ResearchMode
from src.shared.exceptions import ToolNotFoundError, ToolUnavailableError
from src.storage.cache import reset_caches
from src.shared.config import reset_config


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up after each test."""
    reset_caches()
    reset_config()
    reset_registry()
    yield
    reset_caches()
    reset_config()
    reset_registry()


# Mock Tool for testing
class MockTool(BaseTool):
    """Mock tool for testing."""

    TOOL_NAME = "mock_tool"
    TOOL_DESCRIPTION = "A mock tool for testing"

    def __init__(self, return_value=None, **kwargs):
        super().__init__(**kwargs)
        self.return_value = return_value or {"success": True, "result": "mock"}
        self.call_count = 0

    def _execute(self, **kwargs) -> Dict[str, Any]:
        self.call_count += 1
        return self.return_value

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Test query"}
            },
            "required": ["query"]
        }


class MockCoreTool(MockTool):
    """Mock core tool."""
    TOOL_NAME = "mock_core"
    TOOL_DESCRIPTION = "Mock core tool"


class MockExtendedTool(MockTool):
    """Mock extended tool."""
    TOOL_NAME = "mock_extended"
    TOOL_DESCRIPTION = "Mock extended tool"


# ============================================================================
# ToolConfig Tests
# ============================================================================

class TestToolConfig:
    """Tests for ToolConfig dataclass."""

    def test_create_config(self):
        """Test creating a tool config."""
        config = ToolConfig(
            tool_class=MockTool,
            mode=ToolMode.CORE,
            timeout=5.0,
            max_retries=2
        )

        assert config.tool_class == MockTool
        assert config.mode == ToolMode.CORE
        assert config.timeout == 5.0
        assert config.max_retries == 2
        assert config.enabled is True

    def test_create_instance(self):
        """Test creating a tool instance from config."""
        config = ToolConfig(
            tool_class=MockTool,
            mode=ToolMode.CORE,
            timeout=10.0,
            max_retries=3
        )

        instance = config.create_instance()

        assert isinstance(instance, MockTool)
        assert instance.timeout == 10.0
        assert instance.max_retries == 3

    def test_create_instance_with_overrides(self):
        """Test creating instance with parameter overrides."""
        config = ToolConfig(
            tool_class=MockTool,
            mode=ToolMode.CORE,
            timeout=10.0,
            max_retries=3
        )

        instance = config.create_instance(timeout=5.0)

        assert instance.timeout == 5.0


# ============================================================================
# ToolRegistry Tests
# ============================================================================

class TestToolRegistry:
    """Tests for ToolRegistry class."""

    def test_create_empty_registry(self):
        """Test creating an empty registry."""
        registry = ToolRegistry()
        assert len(registry) == 0

    def test_register_tool(self):
        """Test registering a tool."""
        registry = ToolRegistry()
        registry.register(
            name="test_tool",
            tool_class=MockTool,
            mode=ToolMode.CORE
        )

        assert len(registry) == 1
        assert "test_tool" in registry

    def test_register_invalid_class(self):
        """Test registering invalid tool class raises error."""
        registry = ToolRegistry()

        class NotATool:
            pass

        with pytest.raises(ValueError, match="must inherit from BaseTool"):
            registry.register(name="invalid", tool_class=NotATool)

    def test_unregister_tool(self):
        """Test unregistering a tool."""
        registry = ToolRegistry()
        registry.register(name="test", tool_class=MockTool)

        assert registry.unregister("test") is True
        assert "test" not in registry

    def test_unregister_nonexistent(self):
        """Test unregistering nonexistent tool."""
        registry = ToolRegistry()
        assert registry.unregister("nonexistent") is False

    def test_get_tool(self):
        """Test getting a tool instance."""
        registry = ToolRegistry()
        registry.register(name="test", tool_class=MockTool)

        tool = registry.get_tool("test")

        assert isinstance(tool, MockTool)

    def test_get_tool_not_found(self):
        """Test getting nonexistent tool raises error."""
        registry = ToolRegistry()

        with pytest.raises(ToolNotFoundError):
            registry.get_tool("nonexistent")

    def test_get_tool_disabled(self):
        """Test getting disabled tool raises error."""
        registry = ToolRegistry()
        registry.register(name="test", tool_class=MockTool, enabled=False)

        with pytest.raises(ToolUnavailableError):
            registry.get_tool("test")

    def test_tool_caching(self):
        """Test tool instances are cached."""
        registry = ToolRegistry()
        registry.register(name="test", tool_class=MockTool)

        tool1 = registry.get_tool("test")
        tool2 = registry.get_tool("test")

        assert tool1 is tool2

    def test_get_tool_names(self):
        """Test getting all tool names."""
        registry = ToolRegistry()
        registry.register(name="tool1", tool_class=MockTool)
        registry.register(name="tool2", tool_class=MockTool)

        names = registry.get_tool_names()

        assert "tool1" in names
        assert "tool2" in names

    def test_is_registered(self):
        """Test is_registered method."""
        registry = ToolRegistry()
        registry.register(name="test", tool_class=MockTool)

        assert registry.is_registered("test") is True
        assert registry.is_registered("nonexistent") is False

    def test_reset(self):
        """Test reset clears registry."""
        registry = ToolRegistry()
        registry.register(name="test", tool_class=MockTool)
        registry.get_tool("test")  # Create instance

        registry.reset()

        assert len(registry) == 0


class TestToolRegistryModeFiltering:
    """Tests for mode-based tool filtering."""

    def test_get_tools_for_normal_mode(self):
        """Test getting tools for NORMAL mode."""
        registry = ToolRegistry()
        registry.register(name="core1", tool_class=MockTool, mode=ToolMode.CORE)
        registry.register(name="core2", tool_class=MockTool, mode=ToolMode.CORE)
        registry.register(name="extended1", tool_class=MockTool, mode=ToolMode.EXTENDED)

        tools = registry.get_tools_for_mode(ResearchMode.NORMAL)

        assert len(tools) == 2
        tool_names = [t.TOOL_NAME for t in tools]
        assert "mock_tool" in tool_names  # All MockTool have same name

    def test_get_tools_for_deep_mode(self):
        """Test getting tools for DEEP mode."""
        registry = ToolRegistry()
        registry.register(name="core1", tool_class=MockTool, mode=ToolMode.CORE)
        registry.register(name="extended1", tool_class=MockTool, mode=ToolMode.EXTENDED)

        tools = registry.get_tools_for_mode(ResearchMode.DEEP)

        assert len(tools) == 2

    def test_get_tool_names_with_mode_filter(self):
        """Test getting tool names with mode filter."""
        registry = ToolRegistry()
        registry.register(name="core1", tool_class=MockTool, mode=ToolMode.CORE)
        registry.register(name="extended1", tool_class=MockTool, mode=ToolMode.EXTENDED)

        names = registry.get_tool_names(mode=ResearchMode.NORMAL)

        assert "core1" in names
        assert "extended1" not in names

    def test_is_available_mode_check(self):
        """Test is_available respects mode."""
        registry = ToolRegistry()
        registry.register(name="extended", tool_class=MockTool, mode=ToolMode.EXTENDED)

        assert registry.is_available("extended", ResearchMode.DEEP) is True
        assert registry.is_available("extended", ResearchMode.NORMAL) is False


class TestToolRegistryDefinitions:
    """Tests for tool definition generation."""

    def test_get_tool_definitions(self):
        """Test getting tool definitions."""
        registry = ToolRegistry()
        registry.register(name="test", tool_class=MockTool)

        definitions = registry.get_tool_definitions(ResearchMode.DEEP)

        assert len(definitions) == 1
        assert definitions[0]["name"] == "mock_tool"
        assert "description" in definitions[0]
        assert "input_schema" in definitions[0]

    def test_get_tool_definitions_filtered_by_mode(self):
        """Test tool definitions are filtered by mode."""
        registry = ToolRegistry()
        registry.register(name="core", tool_class=MockTool, mode=ToolMode.CORE)
        registry.register(name="extended", tool_class=MockTool, mode=ToolMode.EXTENDED)

        definitions = registry.get_tool_definitions(ResearchMode.NORMAL)

        assert len(definitions) == 1

    def test_description_override(self):
        """Test description override in definitions."""
        registry = ToolRegistry()
        registry._tools["test"] = ToolConfig(
            tool_class=MockTool,
            mode=ToolMode.CORE,
            description_override="Custom description"
        )

        definitions = registry.get_tool_definitions(ResearchMode.DEEP)

        assert definitions[0]["description"] == "Custom description"


class TestToolRegistryFallback:
    """Tests for fallback chain management."""

    def test_fallback_chain_setup(self):
        """Test fallback chain is set up correctly."""
        registry = ToolRegistry()
        registry.register(name="fallback", tool_class=MockTool)
        registry.register(name="primary", tool_class=MockTool, fallback_tool="fallback")

        primary = registry.get_tool("primary")

        assert primary._fallback_tool is not None

    def test_get_fallback_chain(self):
        """Test getting fallback chain."""
        registry = ToolRegistry()
        registry.register(name="c", tool_class=MockTool)
        registry.register(name="b", tool_class=MockTool, fallback_tool="c")
        registry.register(name="a", tool_class=MockTool, fallback_tool="b")

        chain = registry.get_fallback_chain("a")

        assert chain == ["a", "b", "c"]

    def test_circular_fallback_detection(self):
        """Test circular fallback is detected."""
        registry = ToolRegistry()
        # Register both tools - order matters, so register b first
        registry.register(name="b", tool_class=MockTool, fallback_tool="a")
        registry.register(name="a", tool_class=MockTool, fallback_tool="b")

        chain = registry.get_fallback_chain("a")

        # Should include both tools before cycle is detected
        assert "a" in chain
        assert "b" in chain
        # Should not have duplicates
        assert len(chain) == len(set(chain))

    def test_missing_fallback_tool(self):
        """Test handling of missing fallback tool."""
        registry = ToolRegistry()
        registry.register(name="primary", tool_class=MockTool, fallback_tool="nonexistent")

        # Should not raise, just log warning
        tool = registry.get_tool("primary")
        assert tool._fallback_tool is None


class TestToolRegistryExecution:
    """Tests for tool execution."""

    def test_execute_tool(self):
        """Test executing a tool."""
        registry = ToolRegistry()
        registry.register(name="test", tool_class=MockTool)

        result = registry.execute_tool("test", {"query": "test"})

        assert result.success is True

    def test_execute_nonexistent_tool(self):
        """Test executing nonexistent tool."""
        registry = ToolRegistry()

        result = registry.execute_tool("nonexistent", {})

        assert result.success is False
        assert result.error_code == "TOOL_NOT_FOUND"

    def test_execute_mode_mismatch(self):
        """Test executing extended tool in NORMAL mode."""
        registry = ToolRegistry()
        registry.register(name="extended", tool_class=MockTool, mode=ToolMode.EXTENDED)

        result = registry.execute_tool("extended", {}, mode=ResearchMode.NORMAL)

        assert result.success is False
        assert result.error_code == "MODE_MISMATCH"

    def test_execute_disabled_tool(self):
        """Test executing disabled tool."""
        registry = ToolRegistry()
        registry.register(name="test", tool_class=MockTool, enabled=False)

        result = registry.execute_tool("test", {})

        assert result.success is False
        assert result.error_code == "TOOL_DISABLED"

    def test_execute_with_tracer(self):
        """Test executing tool with tracer."""
        registry = ToolRegistry()
        registry.register(name="test", tool_class=MockTool)

        tracer = MagicMock()
        result = registry.execute_tool("test", {"query": "test"}, tracer=tracer)

        assert result.success is True


class TestToolRegistryStats:
    """Tests for registry statistics."""

    def test_get_stats(self):
        """Test getting registry statistics."""
        registry = ToolRegistry()
        registry.register(name="core1", tool_class=MockTool, mode=ToolMode.CORE)
        registry.register(name="core2", tool_class=MockTool, mode=ToolMode.CORE)
        registry.register(name="extended1", tool_class=MockTool, mode=ToolMode.EXTENDED)
        registry.register(name="disabled", tool_class=MockTool, enabled=False)

        stats = registry.get_stats()

        assert stats["total_tools"] == 4
        assert stats["core_tools"] == 2
        assert stats["extended_tools"] == 1
        assert stats["disabled_tools"] == 1


# ============================================================================
# Default Registry Tests
# ============================================================================

class TestDefaultRegistry:
    """Tests for default registry creation."""

    def test_create_default_registry(self):
        """Test creating default registry."""
        registry = create_default_registry()

        # Should have 8 tools (3 core + 5 extended)
        assert len(registry) == 8

        # Check core tools
        assert registry.is_registered("web_search")
        assert registry.is_registered("wikipedia")
        assert registry.is_registered("calculator")

        # Check extended tools
        assert registry.is_registered("yahoo_finance")
        assert registry.is_registered("sec_edgar")
        assert registry.is_registered("github")
        assert registry.is_registered("hackernews")
        assert registry.is_registered("web_scraper")

    def test_default_registry_modes(self):
        """Test default registry has correct modes."""
        registry = create_default_registry()

        # Get core tools in NORMAL mode
        names = registry.get_tool_names(mode=ResearchMode.NORMAL)

        assert "web_search" in names
        assert "wikipedia" in names
        assert "calculator" in names
        assert "yahoo_finance" not in names

    def test_default_registry_fallback_chains(self):
        """Test default registry fallback chains."""
        registry = create_default_registry()

        # web_search -> wikipedia
        chain = registry.get_fallback_chain("web_search")
        assert chain == ["web_search", "wikipedia"]

        # yahoo_finance -> web_search -> wikipedia
        chain = registry.get_fallback_chain("yahoo_finance")
        assert chain == ["yahoo_finance", "web_search", "wikipedia"]


class TestRegistrySingleton:
    """Tests for registry singleton."""

    def test_get_registry_singleton(self):
        """Test get_registry returns singleton."""
        registry1 = get_registry()
        registry2 = get_registry()

        assert registry1 is registry2

    def test_reset_registry_singleton(self):
        """Test reset_registry clears singleton."""
        registry1 = get_registry()
        reset_registry()
        registry2 = get_registry()

        assert registry1 is not registry2


# ============================================================================
# Edge Cases
# ============================================================================

class TestToolRegistryEdgeCases:
    """Edge case tests for tool registry."""

    def test_register_same_name_twice(self):
        """Test registering same name twice replaces tool."""
        registry = ToolRegistry()

        class Tool1(MockTool):
            TOOL_NAME = "tool1"

        class Tool2(MockTool):
            TOOL_NAME = "tool2"

        registry.register(name="test", tool_class=Tool1)
        registry.register(name="test", tool_class=Tool2)

        tool = registry.get_tool("test")
        assert tool.TOOL_NAME == "tool2"

    def test_empty_tool_names(self):
        """Test getting tool names from empty registry."""
        registry = ToolRegistry()
        names = registry.get_tool_names()
        assert names == []

    def test_empty_tool_definitions(self):
        """Test getting definitions from empty registry."""
        registry = ToolRegistry()
        definitions = registry.get_tool_definitions(ResearchMode.DEEP)
        assert definitions == []

    def test_len_and_contains(self):
        """Test __len__ and __contains__ methods."""
        registry = ToolRegistry()
        assert len(registry) == 0
        assert "test" not in registry

        registry.register(name="test", tool_class=MockTool)
        assert len(registry) == 1
        assert "test" in registry

    def test_disabled_tools_excluded_from_mode_tools(self):
        """Test disabled tools are excluded from get_tools_for_mode."""
        registry = ToolRegistry()
        registry.register(name="enabled", tool_class=MockTool, enabled=True)
        registry.register(name="disabled", tool_class=MockTool, enabled=False)

        tools = registry.get_tools_for_mode(ResearchMode.DEEP)

        assert len(tools) == 1

    def test_fallback_to_disabled_tool(self):
        """Test fallback to disabled tool is not set."""
        registry = ToolRegistry()
        registry.register(name="fallback", tool_class=MockTool, enabled=False)
        registry.register(name="primary", tool_class=MockTool, fallback_tool="fallback")

        primary = registry.get_tool("primary")

        # Fallback should not be set since it's disabled
        assert primary._fallback_tool is None
