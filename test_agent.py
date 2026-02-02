"""Quick test script for the research assistant agent."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.agent import create_agent
from src.evaluation.tracers.tool_tracer import ToolTracer
from src.evaluation.tracers.error_tracer import ErrorTracer
from src.evaluation.visualizer import ASCIIVisualizer
from src.shared.models import AttemptResult


def test_agent_basic():
    """Test basic agent functionality."""
    print("=" * 80)
    print("Testing Research Assistant Agent")
    print("=" * 80)
    print()

    # Check for API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it with: export ANTHROPIC_API_KEY=your_key_here")
        return

    # Create agent
    print("Creating agent...")
    try:
        agent = create_agent()
        print(f"✓ Agent created successfully")
        print(f"  Available tools: {', '.join(agent.get_available_tools())}")
        print()
    except Exception as e:
        print(f"✗ Failed to create agent: {e}")
        return

    # Test question
    question = "What is 2 + 2?"
    print(f"Question: {question}")
    print("-" * 80)

    # Create tracers
    tracer = ToolTracer(attempt_number=1)
    error_tracer = ErrorTracer()

    # Ask question
    try:
        answer, tool_traces, error_traces = agent.ask(
            question=question,
            tracer=tracer,
            error_tracer=error_tracer,
            reset_conversation=True
        )

        print(f"\nAnswer: {answer}")
        print()

        # Show tool traces
        if tool_traces:
            print("Tool Calls:")
            for i, trace in enumerate(tool_traces, 1):
                print(f"  {i}. {trace.tool_name}")
                print(f"     Params: {trace.params}")
                print(f"     Status: {trace.status.value}")
                print(f"     Latency: {trace.latency_ms:.0f}ms")
                if trace.result:
                    result_str = str(trace.result)[:100]
                    print(f"     Result: {result_str}...")
                print()

        # Show errors if any
        if error_traces:
            print("Errors:")
            for error in error_traces:
                print(f"  - {error.tool_name}: {error.error_message}")
                print(f"    Recovery: {error.recovery_action} ({'✓' if error.recovery_success else '✗'})")
                print()

        print("=" * 80)
        print("✓ Test completed successfully")

    except Exception as e:
        print(f"✗ Error during test: {e}")
        import traceback
        traceback.print_exc()


def test_agent_with_tools():
    """Test agent with a question that requires tools."""
    print("\n" + "=" * 80)
    print("Testing Agent with Tool Usage")
    print("=" * 80)
    print()

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set")
        return

    # Create agent
    agent = create_agent()

    # Test question that requires Wikipedia
    question = "What is the population of France?"
    print(f"Question: {question}")
    print("-" * 80)

    tracer = ToolTracer(attempt_number=1)
    error_tracer = ErrorTracer()

    try:
        answer, tool_traces, error_traces = agent.ask(
            question=question,
            tracer=tracer,
            error_tracer=error_tracer,
            reset_conversation=True
        )

        # Create a mock attempt result for visualization
        attempt = AttemptResult(
            attempt_number=1,
            question_id="test_001",
            final_answer=answer,
            tool_calls=tool_traces,
            errors=error_traces,
            total_latency_ms=sum(t.latency_ms for t in tool_traces),
            is_correct=True,
            semantic_similarity=1.0,
            timestamp="2024-01-01T00:00:00"
        )

        # Visualize with ASCII art
        visualizer = ASCIIVisualizer(width=80)
        print(visualizer.visualize_attempt(attempt))

        print("=" * 80)
        print("✓ Tool usage test completed")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run tests
    test_agent_basic()

    # Only run tool test if Tavily key is available
    if os.getenv("TAVILY_API_KEY") or True:  # Wikipedia doesn't need key
        test_agent_with_tools()
    else:
        print("\nSkipping tool test (TAVILY_API_KEY not set)")
