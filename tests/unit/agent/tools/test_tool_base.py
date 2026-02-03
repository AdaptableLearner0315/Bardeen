"""Unit tests for ToolBase abstract class."""

import pytest
from src.agent.tools.base_tool import ToolBase
from typing import Dict, Any


class SimpleTool(ToolBase):
    """Simple concrete tool for testing."""

    def get_tool_definition(self) -> Dict[str, Any]:
        return {
            "name": "simple",
            "description": "A simple test tool",
            "input_schema": {
                "type": "object",
                "properties": {
                    "param": {"type": "string"}
                },
                "required": ["param"]
            }
        }

    def _execute_internal(self, param: str) -> str:
        if param == "fail":
            raise ValueError("Intentional failure")
        return f"processed: {param}"


class TestToolBase:
    """Test ToolBase functionality."""

    def test_tool_base_is_abstract(self):
        """Test that ToolBase cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ToolBase("test", timeout=10)

    def test_concrete_tool_instantiation(self):
        """Test concrete implementation can be instantiated."""
        tool = SimpleTool("simple", timeout=10)
        assert tool.name == "simple"
        assert tool.timeout == 10

    def test_format_success_structure(self):
        """Test _format_success() returns correct structure."""
        tool = SimpleTool("simple")
        result = tool._format_success({"data": "value"})
        assert result["success"] is True
        assert result["result"] == {"data": "value"}
        assert result["tool"] == "simple"

    def test_format_error_structure(self):
        """Test _format_error() returns correct structure."""
        tool = SimpleTool("simple")
        result = tool._format_error("Error message", "timeout")
        assert result["success"] is False
        assert result["error"] == "Error message"
        assert result["error_type"] == "timeout"
        assert result["tool"] == "simple"

    def test_successful_execution(self):
        """Test successful tool execution."""
        tool = SimpleTool("simple")
        result = tool(param="test")
        assert result["success"] is True
        assert result["result"] == "processed: test"
        assert result["tool"] == "simple"

    def test_error_handling(self):
        """Test error handling in execution."""
        tool = SimpleTool("simple")
        result = tool(param="fail")
        assert result["success"] is False
        assert "Intentional failure" in result["error"]
        assert result["error_type"] == "invalid_input"
