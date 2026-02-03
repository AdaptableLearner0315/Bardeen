"""Base class for all agent tools.

This module provides the abstract base class ToolBase that all agent tools
(Calculator, Wikipedia, WebSearch, etc.) inherit from. It standardizes the
tool interface, error handling, and result formatting.

Key Classes:
    ToolBase: Abstract base class for tool implementations

Usage:
    from src.agent.tools.base_tool import ToolBase

    class MyTool(ToolBase):
        def get_tool_definition(self) -> Dict[str, Any]:
            return {"name": "my_tool", ...}

        def _execute_internal(self, **kwargs) -> Any:
            return "result"

Notes:
    - All tools should inherit from this base class
    - Provides standard error handling and logging
    - Implements timeout and exception management
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ToolBase(ABC):
    """Abstract base class for all agent tools.

    Provides:
    - Standard error handling pattern
    - Tool definition interface
    - Result formatting
    - Logging infrastructure
    - Timeout management

    Attributes:
        name: Tool name identifier
        timeout: Maximum execution time in seconds
        logger: Tool-specific logger instance

    Examples:
        >>> class SimpleTool(ToolBase):
        ...     def get_tool_definition(self) -> Dict[str, Any]:
        ...         return {"name": "simple", "description": "A simple tool"}
        ...     def _execute_internal(self, **kwargs) -> Any:
        ...         return {"data": "value"}
        >>> tool = SimpleTool("simple", timeout=10)
        >>> result = tool()
        >>> result["success"]
        True
    """

    def __init__(self, name: str, timeout: int = 10):
        """Initialize tool with name and timeout.

        Args:
            name: Tool name identifier
            timeout: Maximum execution time in seconds (default: 10)
        """
        self.name = name
        self.timeout = timeout
        self.logger = logging.getLogger(f"tools.{name}")

    @abstractmethod
    def get_tool_definition(self) -> Dict[str, Any]:
        """Return Anthropic tool definition schema.

        Returns:
            Dict with keys: name, description, input_schema

        Note:
            This method must be implemented by all tool subclasses to
            define the tool's interface for the LLM.

        Examples:
            >>> def get_tool_definition(self) -> Dict[str, Any]:
            ...     return {
            ...         "name": "calculator",
            ...         "description": "Perform mathematical calculations",
            ...         "input_schema": {
            ...             "type": "object",
            ...             "properties": {
            ...                 "expression": {"type": "string"}
            ...             },
            ...             "required": ["expression"]
            ...         }
            ...     }
        """
        pass

    @abstractmethod
    def _execute_internal(self, **kwargs) -> Any:
        """Internal execution logic. Subclasses implement tool-specific logic.

        Args:
            **kwargs: Tool-specific parameters defined in input_schema

        Returns:
            Tool-specific result (will be wrapped in standard format)

        Raises:
            Exception: Any exception raised will be caught and formatted

        Note:
            This method should contain the core tool logic without
            worrying about error handling or result formatting.
        """
        pass

    def __call__(self, **kwargs) -> Dict[str, Any]:
        """Standard execution wrapper with error handling.

        This method wraps _execute_internal() with consistent error
        handling, logging, and result formatting.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            Dict with keys:
            - success (bool): Whether execution succeeded
            - result (Any): Tool result if successful
            - error (str): Error message if failed
            - error_type (str): Error category if failed
            - tool (str): Tool name

        Examples:
            >>> tool = SimpleTool("simple")
            >>> result = tool(param="value")
            >>> if result["success"]:
            ...     print(result["result"])
            ... else:
            ...     print(result["error"])
        """
        try:
            self.logger.debug(f"Executing {self.name} with kwargs: {kwargs}")
            result = self._execute_internal(**kwargs)
            self.logger.info(f"{self.name} executed successfully")
            return self._format_success(result)
        except TimeoutError as e:
            error_msg = f"Tool timeout after {self.timeout}s"
            self.logger.warning(error_msg)
            return self._format_error(error_msg, error_type="timeout")
        except ValueError as e:
            error_msg = f"Invalid input: {str(e)}"
            self.logger.error(error_msg)
            return self._format_error(error_msg, error_type="invalid_input")
        except ConnectionError as e:
            error_msg = f"Connection failed: {str(e)}"
            self.logger.error(error_msg)
            return self._format_error(error_msg, error_type="connection_error")
        except Exception as e:
            self.logger.error(f"Tool execution failed: {e}", exc_info=True)
            return self._format_error(str(e), error_type="execution_error")

    def _format_success(self, result: Any) -> Dict[str, Any]:
        """Format successful result.

        Args:
            result: Raw result from _execute_internal()

        Returns:
            Standardized success response dict

        Examples:
            >>> tool._format_success({"data": "value"})
            {'success': True, 'result': {'data': 'value'}, 'tool': 'simple'}
        """
        return {
            "success": True,
            "result": result,
            "tool": self.name
        }

    def _format_error(self, error_msg: str, error_type: str = "error") -> Dict[str, Any]:
        """Format error result.

        Args:
            error_msg: Human-readable error message
            error_type: Error category (timeout, invalid_input, connection_error, execution_error)

        Returns:
            Standardized error response dict

        Examples:
            >>> tool._format_error("Something failed", "execution_error")
            {'success': False, 'error': 'Something failed', 'error_type': 'execution_error', 'tool': 'simple'}
        """
        return {
            "success": False,
            "error": error_msg,
            "error_type": error_type,
            "tool": self.name
        }

    def __repr__(self) -> str:
        """String representation of tool.

        Returns:
            Tool representation string
        """
        return f"{self.__class__.__name__}(name='{self.name}', timeout={self.timeout})"
