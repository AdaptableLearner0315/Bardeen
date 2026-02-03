"""Base class for all tracer implementations.

This module provides the abstract base class TracerBase that all tracers
(ToolTracer, ErrorTracer, StepTracer) inherit from. It defines the common
interface for trace collection, retrieval, and management.

Key Classes:
    TracerBase: Abstract base class for trace collection

Usage:
    from src.evaluation.tracers.base import TracerBase

    class MyTracer(TracerBase[TraceType]):
        def get_traces(self) -> List[TraceType]:
            return self._traces

Notes:
    - Subclasses must implement get_traces() method
    - Uses generic typing for type-safe trace storage
    - Provides enable/disable functionality for conditional tracing
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generic, TypeVar

T = TypeVar('T')


class TracerBase(ABC, Generic[T]):
    """Abstract base class for all tracer implementations.

    Provides common interface for trace collection, retrieval, and management.
    Subclasses must implement specific trace collection logic.

    Type Parameters:
        T: Type of traces being collected (e.g., ToolTrace, ErrorTrace)

    Attributes:
        _traces: Internal list of collected traces
        _enabled: Whether tracing is currently active

    Examples:
        >>> class MyTracer(TracerBase[str]):
        ...     def get_traces(self) -> List[str]:
        ...         return self._traces
        >>> tracer = MyTracer()
        >>> tracer._traces.append("trace1")
        >>> tracer.get_traces()
        ['trace1']
    """

    def __init__(self):
        """Initialize tracer with empty trace list and enabled state."""
        self._traces: List[T] = []
        self._enabled: bool = True

    @abstractmethod
    def get_traces(self) -> List[T]:
        """Retrieve all collected traces.

        Returns:
            List of collected traces of type T

        Note:
            Subclasses must implement this method to define how traces
            are retrieved and potentially formatted.
        """
        pass

    def reset(self):
        """Clear all collected traces.

        This method is useful for starting fresh trace collection
        without creating a new tracer instance.

        Examples:
            >>> tracer._traces = ["trace1", "trace2"]
            >>> tracer.reset()
            >>> len(tracer._traces)
            0
        """
        self._traces.clear()

    def enable(self):
        """Enable trace collection.

        When enabled, traces will be collected according to the
        subclass implementation.

        Examples:
            >>> tracer.disable()
            >>> tracer.enable()
            >>> tracer._enabled
            True
        """
        self._enabled = True

    def disable(self):
        """Disable trace collection.

        When disabled, subclasses should not collect new traces.
        Existing traces are preserved.

        Examples:
            >>> tracer.enable()
            >>> tracer.disable()
            >>> tracer._enabled
            False
        """
        self._enabled = False

    @property
    def is_enabled(self) -> bool:
        """Check if tracing is currently enabled.

        Returns:
            True if tracing is enabled, False otherwise
        """
        return self._enabled

    @property
    def trace_count(self) -> int:
        """Get the number of collected traces.

        Returns:
            Number of traces currently stored
        """
        return len(self._traces)
