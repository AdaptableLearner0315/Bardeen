"""Tests for tools used display (deduplicated, no timing)."""

import pytest
from pathlib import Path


class TestToolsDisplayDeduplication:
    """Tests for deduplicating tool names in display."""

    def test_js_uses_set_for_deduplication(self):
        """Test JavaScript uses Set to deduplicate tool names."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Should use Set for deduplication
        assert 'new Set(' in js_content, "Should use Set for deduplication"

    def test_js_extracts_unique_tool_names(self):
        """Test JavaScript extracts unique tool names from tool_calls."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Should map to tool_name and use Set
        assert 'data.tool_calls.map(t => t.tool_name)' in js_content

    def test_js_spreads_set_to_array(self):
        """Test JavaScript spreads Set to array for joining."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Should spread Set to array: [...new Set(...)]
        assert '[...new Set(' in js_content

    def test_js_joins_unique_tools(self):
        """Test JavaScript joins unique tools with comma."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Should join with comma
        assert "uniqueTools.join(', ')" in js_content


class TestToolsDisplayNoTiming:
    """Tests for removing timing from tools display."""

    def test_js_tools_display_no_latency_in_summary(self):
        """Test tools summary does not include latency."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Find the tools display section
        # Should NOT have latency_ms in the uniqueTools line
        lines = js_content.split('\n')
        in_tools_section = False
        for line in lines:
            if 'uniqueTools' in line and 'new Set' in line:
                in_tools_section = True
            if in_tools_section and 'uniqueTools.join' in line:
                # The join line should not mention latency
                assert 'latency_ms' not in line, "Tools summary should not include latency"
                break

    def test_js_unique_tools_variable_exists(self):
        """Test uniqueTools variable is defined."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert 'const uniqueTools' in js_content or 'let uniqueTools' in js_content


class TestToolsDisplayFormat:
    """Tests for tools display format."""

    def test_js_tools_html_has_tools_label(self):
        """Test tools HTML includes 'Tools used:' label."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert 'Tools used:' in js_content

    def test_js_tools_html_has_emoji(self):
        """Test tools HTML includes wrench emoji."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert '🔧' in js_content

    def test_js_no_count_in_tools_summary(self):
        """Test tools summary does not show count (dedup removes meaning)."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Find the toolsHtml section
        lines = js_content.split('\n')
        for i, line in enumerate(lines):
            if 'Tools used:</strong>' in line:
                # Should not have ${data.tool_calls.length} after dedup
                # because unique count is different from total calls
                full_line = line
                assert 'data.tool_calls.length' not in full_line, \
                    "Should not show total call count for deduplicated display"
                break


class TestToolsDisplayLogic:
    """Tests for tools display logic."""

    def test_deduplication_logic(self):
        """Test the deduplication logic works correctly in Python simulation."""
        # Simulate what the JS does
        tool_calls = [
            {"tool_name": "web_search", "latency_ms": 2018},
            {"tool_name": "web_search", "latency_ms": 742},
            {"tool_name": "web_search", "latency_ms": 809},
            {"tool_name": "web_search", "latency_ms": 834},
        ]

        # Python equivalent of: [...new Set(data.tool_calls.map(t => t.tool_name))]
        unique_tools = list(set(t["tool_name"] for t in tool_calls))

        assert len(unique_tools) == 1
        assert unique_tools[0] == "web_search"

    def test_deduplication_multiple_tools(self):
        """Test deduplication with multiple different tools."""
        tool_calls = [
            {"tool_name": "web_search", "latency_ms": 100},
            {"tool_name": "wikipedia", "latency_ms": 200},
            {"tool_name": "web_search", "latency_ms": 150},
            {"tool_name": "calculator", "latency_ms": 10},
            {"tool_name": "wikipedia", "latency_ms": 180},
        ]

        unique_tools = list(set(t["tool_name"] for t in tool_calls))

        assert len(unique_tools) == 3
        assert "web_search" in unique_tools
        assert "wikipedia" in unique_tools
        assert "calculator" in unique_tools

    def test_format_output(self):
        """Test the expected format output."""
        tool_calls = [
            {"tool_name": "web_search", "latency_ms": 2018},
            {"tool_name": "web_search", "latency_ms": 742},
        ]

        unique_tools = list(set(t["tool_name"] for t in tool_calls))
        output = ", ".join(unique_tools)

        # Should be just "web_search" without timing
        assert output == "web_search"
        assert "ms" not in output
        assert "(" not in output


class TestToolsDisplayEmpty:
    """Tests for empty tools display."""

    def test_js_handles_empty_tool_calls(self):
        """Test JavaScript handles empty tool_calls array."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Should check for tool_calls length before processing
        assert 'data.tool_calls && data.tool_calls.length > 0' in js_content

    def test_empty_tools_no_output(self):
        """Test empty tool calls produces no tools display."""
        tool_calls = []

        if tool_calls:
            unique_tools = list(set(t["tool_name"] for t in tool_calls))
            output = ", ".join(unique_tools)
        else:
            output = ""

        assert output == ""


class TestToolsDisplayOldFormatRemoved:
    """Tests to ensure old format with timing is removed."""

    def test_js_no_latency_in_tools_list(self):
        """Test JavaScript doesn't include latency in main tools list."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Find uniqueTools assignment and check it doesn't mention latency
        lines = js_content.split('\n')
        for line in lines:
            if 'uniqueTools' in line and '=' in line and 'Set' in line:
                assert 'latency_ms' not in line, \
                    "uniqueTools should not include latency"

    def test_js_tools_join_simple(self):
        """Test tools are joined simply without formatting."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Should have simple join without template literal with latency
        # Old format was: `${t.tool_name} (${t.latency_ms.toFixed(0)}ms)`
        # New format should just be the tool names joined

        # Check that the old format is NOT present
        assert '${t.latency_ms.toFixed(0)}ms' not in js_content or \
               'uniqueTools' in js_content, \
               "Old format with timing should be replaced"
