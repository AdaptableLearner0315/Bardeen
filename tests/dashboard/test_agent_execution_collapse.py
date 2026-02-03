"""Tests for agent execution details collapse functionality."""

import pytest
from pathlib import Path


class TestAgentExecutionDetailsCollapse:
    """Tests for agent execution details being collapsed by default."""

    def test_agent_executions_details_exists(self):
        """Test that agent-executions-details class exists."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "agent-executions-details" in js_content

    def test_details_element_used(self):
        """Test that HTML details element is used for collapsible section."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "<details class=\"agent-executions-details\">" in js_content
        assert "</details>" in js_content

    def test_details_not_open_by_default(self):
        """Test that details element does NOT have open attribute (collapsed by default)."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Check that the details element for agent executions does NOT have 'open' attribute
        assert '<details class="agent-executions-details" open>' not in js_content

    def test_summary_element_exists(self):
        """Test that summary element exists for expandable header."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "<summary>" in js_content
        assert "</summary>" in js_content

    def test_agent_execution_title_in_summary(self):
        """Test that agent execution title is in the summary element."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "Agent Execution Details" in js_content
        assert "🤖 Agent Execution Details" in js_content

    def test_agent_executions_content_class_exists(self):
        """Test that agent-executions-content class exists for details content."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "agent-executions-content" in js_content

    def test_agent_execution_html_structure(self):
        """Test overall HTML structure of agent execution details."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Check for nested structure: details > summary + content
        assert 'class="agent-executions-details"' in js_content
        assert 'class="agent-executions-content"' in js_content

    def test_agent_count_displayed_in_summary(self):
        """Test that agent count is displayed in summary header."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Check for agent count logic in summary
        assert "data.agent_executions.length" in js_content
        assert "agent${data.agent_executions.length > 1 ? 's' : ''}" in js_content


class TestDetailsCollapseInteraction:
    """Tests for user interaction with collapsed details."""

    def test_details_is_native_html(self):
        """Test that native HTML details/summary elements are used (no custom JS needed)."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Native <details> doesn't need custom toggle JavaScript
        # Just verify it uses the standard HTML elements
        assert "<details" in js_content
        assert "<summary>" in js_content


class TestRawToolCallTraceCollapse:
    """Tests for raw tool call trace collapse (should also be collapsed)."""

    def test_raw_trace_details_collapsed(self):
        """Test that raw tool call trace is also collapsed by default."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Raw Tool Call Trace should also be in a collapsible details element
        assert "Raw Tool Call Trace" in js_content
        assert '<details class="tool-details">' in js_content

    def test_ascii_trace_collapsed(self):
        """Test that ASCII trace is also collapsed by default."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # ASCII trace should also be collapsible
        assert "View Full Execution Trace" in js_content
        assert "<details>" in js_content


class TestAgentExecutionDisplay:
    """Tests for agent execution display content."""

    def test_agent_execution_header_displayed(self):
        """Test that agent execution header shows agent info."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "agent-exec-header" in js_content
        assert "agent.display_name" in js_content
        assert "agent.icon" in js_content

    def test_agent_stats_displayed(self):
        """Test that agent stats (tool count, latency, success rate) are displayed."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "agent.tool_count" in js_content
        assert "agent.total_latency_ms" in js_content
        assert "agent.success_rate" in js_content

    def test_tool_calls_displayed_in_agent(self):
        """Test that individual tool calls are displayed within agent execution."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "agent-tool-call" in js_content
        assert "tool-header" in js_content
        assert "tool-status" in js_content
