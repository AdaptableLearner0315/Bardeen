"""
Unit tests for frontend UI components.

Tests the dashboard frontend for:
1. Compact mode selector (Perplexity-style icons)
2. Execution plan hidden by default
3. Response message structure
"""

import pytest
import re
from pathlib import Path


class TestModeSelector:
    """Tests for the compact mode selector UI."""

    @pytest.fixture
    def html_content(self):
        """Load the index.html content."""
        html_path = Path(__file__).parent.parent / "src" / "dashboard" / "frontend" / "index.html"
        return html_path.read_text()

    @pytest.fixture
    def css_content(self):
        """Load the style.css content."""
        css_path = Path(__file__).parent.parent / "src" / "dashboard" / "frontend" / "style.css"
        return css_path.read_text()

    @pytest.fixture
    def js_content(self):
        """Load the app.js content."""
        js_path = Path(__file__).parent.parent / "src" / "dashboard" / "frontend" / "app.js"
        return js_path.read_text()

    def test_compact_mode_selector_exists(self, html_content):
        """Test that compact mode selector with icons exists."""
        # Should have mode-selector class
        assert 'class="mode-selector"' in html_content, \
            "Missing compact mode-selector container"

        # Should have mode-icon buttons instead of large mode-button
        assert 'class="mode-icon' in html_content, \
            "Missing mode-icon buttons"

        # Should NOT have the old large toggle
        assert 'class="mode-toggle"' not in html_content, \
            "Old large mode-toggle should be removed"

    def test_mode_icons_have_tooltips(self, html_content):
        """Test that mode icons have descriptive tooltips."""
        # Auto mode tooltip
        assert 'title="Auto' in html_content, \
            "Auto mode icon missing tooltip"

        # Normal mode tooltip
        assert 'title="Normal' in html_content, \
            "Normal mode icon missing tooltip"

        # Deep mode tooltip
        assert 'title="Deep' in html_content, \
            "Deep mode icon missing tooltip"

    def test_mode_icons_compact_size(self, css_content):
        """Test that mode icons are compact (small size)."""
        # Check for compact icon styling
        assert '.mode-icon' in css_content, \
            "Missing .mode-icon CSS class"

        # Should have small width/height (around 32px)
        mode_icon_match = re.search(r'\.mode-icon\s*\{[^}]*width:\s*(\d+)px', css_content)
        if mode_icon_match:
            width = int(mode_icon_match.group(1))
            assert width <= 40, f"Mode icon too large: {width}px (should be <= 40px)"

    def test_send_button_svg_icon(self, html_content):
        """Test that send button uses SVG icon instead of text."""
        # Should have SVG in send button
        assert '<svg' in html_content and 'send-btn' in html_content, \
            "Send button should use SVG icon"

        # Should NOT have "Send" text button
        send_text_pattern = r'class="primary-button"[^>]*>\s*Send\s*<'
        assert not re.search(send_text_pattern, html_content), \
            "Should not have old text-based Send button"


class TestExecutionPlanHidden:
    """Tests that execution plan is hidden by default."""

    @pytest.fixture
    def js_content(self):
        """Load the app.js content."""
        js_path = Path(__file__).parent.parent / "src" / "dashboard" / "frontend" / "app.js"
        return js_path.read_text()

    def test_execution_plan_not_in_main_display(self, js_content):
        """Test that execution plan is not shown in main message area."""
        # The planHtml variable should not be directly added to messageDiv
        # Check that planHtml is not in the innerHTML template

        # Find the innerHTML assignment for assistant message
        inner_html_match = re.search(
            r'messageDiv\.innerHTML\s*=\s*`([^`]+)`',
            js_content,
            re.DOTALL
        )

        if inner_html_match:
            inner_html_content = inner_html_match.group(1)
            # planHtml and treeHtml should NOT be in the template
            assert '${planHtml}' not in inner_html_content, \
                "Execution plan (planHtml) should not be in main display"
            assert '${treeHtml}' not in inner_html_content, \
                "Step-by-step tree (treeHtml) should not be in main display"

    def test_tool_details_collapsible(self, js_content):
        """Test that tool details are in a collapsible section."""
        # Tool details should be in a <details> element
        assert '<details class="tool-details">' in js_content, \
            "Tool details should be in collapsible <details> element"


class TestModeIndicator:
    """Tests for the compact mode indicator."""

    @pytest.fixture
    def js_content(self):
        """Load the app.js content."""
        js_path = Path(__file__).parent.parent / "src" / "dashboard" / "frontend" / "app.js"
        return js_path.read_text()

    @pytest.fixture
    def css_content(self):
        """Load the style.css content."""
        css_path = Path(__file__).parent.parent / "src" / "dashboard" / "frontend" / "style.css"
        return css_path.read_text()

    def test_mode_indicator_compact_text(self, js_content):
        """Test that mode indicator shows compact text with icon."""
        # Should set short text like "✨ Auto" not "Mode: Auto (AI selects)"
        assert "✨ Auto" in js_content, \
            "Mode indicator should show compact '✨ Auto'"
        assert "⚡ Normal" in js_content, \
            "Mode indicator should show compact '⚡ Normal'"
        assert "🔬 Deep" in js_content, \
            "Mode indicator should show compact '🔬 Deep'"

    def test_mode_indicator_styling(self, css_content):
        """Test that mode indicator has compact styling."""
        assert '.mode-indicator' in css_content, \
            "Missing .mode-indicator CSS"

        # Should have small font size
        mode_indicator_match = re.search(
            r'\.mode-indicator\s*\{[^}]*font-size:\s*([\d.]+)(rem|px)',
            css_content
        )
        if mode_indicator_match:
            size = float(mode_indicator_match.group(1))
            unit = mode_indicator_match.group(2)
            if unit == 'rem':
                assert size <= 1.0, f"Mode indicator font too large: {size}rem"
            elif unit == 'px':
                assert size <= 14, f"Mode indicator font too large: {size}px"


class TestInputAreaLayout:
    """Tests for the Perplexity-style input area layout."""

    @pytest.fixture
    def html_content(self):
        """Load the index.html content."""
        html_path = Path(__file__).parent.parent / "src" / "dashboard" / "frontend" / "index.html"
        return html_path.read_text()

    @pytest.fixture
    def css_content(self):
        """Load the style.css content."""
        css_path = Path(__file__).parent.parent / "src" / "dashboard" / "frontend" / "style.css"
        return css_path.read_text()

    def test_input_wrapper_structure(self, html_content):
        """Test that input has wrapper with textarea and actions."""
        assert 'class="input-wrapper"' in html_content, \
            "Missing input-wrapper container"
        assert 'class="input-actions"' in html_content, \
            "Missing input-actions container"

    def test_input_footer_exists(self, html_content):
        """Test that input footer with options exists."""
        assert 'class="input-footer"' in html_content, \
            "Missing input-footer container"
        assert 'class="reset-option"' in html_content, \
            "Missing reset-option in footer"

    def test_send_button_class(self, html_content):
        """Test that send button has correct class."""
        assert 'class="send-btn"' in html_content, \
            "Send button should have 'send-btn' class"

    def test_input_container_styling(self, css_content):
        """Test that input container has border-radius styling."""
        # Should have rounded corners
        assert 'border-radius: 12px' in css_content or 'border-radius:12px' in css_content, \
            "Input container should have rounded corners"


class TestMessageDisplay:
    """Tests for message display without execution plan clutter."""

    @pytest.fixture
    def js_content(self):
        """Load the app.js content."""
        js_path = Path(__file__).parent.parent / "src" / "dashboard" / "frontend" / "app.js"
        return js_path.read_text()

    @pytest.fixture
    def css_content(self):
        """Load the style.css content."""
        css_path = Path(__file__).parent.parent / "src" / "dashboard" / "frontend" / "style.css"
        return css_path.read_text()

    def test_message_has_mode_badge(self, js_content):
        """Test that messages show mode badge."""
        assert 'mode-badge' in js_content, \
            "Messages should include mode-badge"

    def test_mode_badge_styling(self, css_content):
        """Test that mode badge has compact styling."""
        assert '.mode-badge' in css_content, \
            "Missing .mode-badge CSS"

    def test_answer_content_first(self, js_content):
        """Test that answer content comes before tool details."""
        # Find the innerHTML assignment
        inner_html_match = re.search(
            r'messageDiv\.innerHTML\s*=\s*`([^`]+)`',
            js_content,
            re.DOTALL
        )

        if inner_html_match:
            inner_html_content = inner_html_match.group(1)
            # message-content should come before tool-details/thinking
            message_pos = inner_html_content.find('message-content')
            thinking_pos = inner_html_content.find('thinkingHtml')

            if message_pos != -1 and thinking_pos != -1:
                assert message_pos < thinking_pos, \
                    "Answer content should appear before tool details"


def test_no_large_mode_toggle():
    """Integration test: verify old large mode toggle structure is removed."""
    html_path = Path(__file__).parent.parent / "src" / "dashboard" / "frontend" / "index.html"
    html_content = html_path.read_text()

    # These structural patterns should NOT exist (old large toggle)
    old_patterns = [
        'class="mode-toggle"',
        'class="toggle-buttons"',
        'class="mode-button"',  # Note: mode-icon is new, mode-button is old
    ]

    for pattern in old_patterns:
        assert pattern not in html_content, \
            f"Old mode toggle remnant found: '{pattern}'"

    # Verify new compact mode selector exists
    assert 'class="mode-selector"' in html_content, \
        "New compact mode-selector should exist"
    assert 'class="mode-icon' in html_content, \
        "New mode-icon buttons should exist"


def test_execution_plan_styles_can_be_removed():
    """Test that execution plan styles could be cleaned up if needed."""
    css_path = Path(__file__).parent.parent / "src" / "dashboard" / "frontend" / "style.css"
    css_content = css_path.read_text()

    # These styles exist but are now unused in the main flow
    # They could be removed or kept for potential future use
    unused_styles = [
        '.execution-plan',
        '.execution-tree',
        '.tree-step',
    ]

    # Just document that they exist (not failing - just informational)
    for style in unused_styles:
        if style in css_content:
            print(f"Note: {style} CSS exists but may be unused in main display")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
