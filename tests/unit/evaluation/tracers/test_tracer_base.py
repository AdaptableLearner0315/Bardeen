"""Unit tests for TracerBase abstract class."""

import pytest
from src.evaluation.tracers.base import TracerBase
from typing import List


class ConcreteTracer(TracerBase[str]):
    """Concrete implementation for testing."""

    def get_traces(self) -> List[str]:
        return self._traces


class TestTracerBase:
    """Test TracerBase functionality."""

    def test_tracer_base_is_abstract(self):
        """Test that TracerBase cannot be instantiated directly."""
        with pytest.raises(TypeError):
            TracerBase()

    def test_concrete_tracer_instantiation(self):
        """Test that concrete implementation can be instantiated."""
        tracer = ConcreteTracer()
        assert tracer is not None
        assert tracer.is_enabled is True

    def test_initial_state(self):
        """Test initial tracer state."""
        tracer = ConcreteTracer()
        assert tracer.trace_count == 0
        assert tracer.is_enabled is True

    def test_reset_clears_traces(self):
        """Test reset() clears all collected traces."""
        tracer = ConcreteTracer()
        tracer._traces = ["trace1", "trace2"]
        tracer.reset()
        assert len(tracer._traces) == 0
        assert tracer.trace_count == 0

    def test_enable_disable_toggle(self):
        """Test enable() and disable() toggle state."""
        tracer = ConcreteTracer()

        tracer.disable()
        assert not tracer.is_enabled

        tracer.enable()
        assert tracer.is_enabled

    def test_trace_count_property(self):
        """Test trace_count property."""
        tracer = ConcreteTracer()
        tracer._traces = ["trace1", "trace2", "trace3"]
        assert tracer.trace_count == 3

    def test_get_traces_implementation(self):
        """Test get_traces() returns collected traces."""
        tracer = ConcreteTracer()
        tracer._traces = ["trace1", "trace2"]
        traces = tracer.get_traces()
        assert traces == ["trace1", "trace2"]
