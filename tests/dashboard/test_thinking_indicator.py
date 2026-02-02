"""Tests for thinking/loading indicator."""

import pytest
from pathlib import Path


class TestThinkingIndicatorHTML:
    """Tests for thinking indicator in HTML."""

    def test_html_structure(self):
        """Test that HTML is valid."""
        html_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/index.html"

        with open(html_path, 'r') as f:
            html_content = f.read()

        # Basic HTML structure checks
        assert '<!DOCTYPE html>' in html_content
        assert '<html' in html_content
        assert '</html>' in html_content


class TestThinkingIndicatorCSS:
    """Tests for thinking indicator CSS styles."""

    def test_css_has_thinking_styles(self):
        """Test CSS includes thinking animation styles."""
        css_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/style.css"

        with open(css_path, 'r') as f:
            css_content = f.read()

        # Check for thinking animation classes
        assert '.thinking-message' in css_content
        assert '.thinking-container' in css_content
        assert '.thinking-animation' in css_content
        assert '.thinking-dot' in css_content

    def test_css_has_bounce_animation(self):
        """Test CSS includes bounce animation keyframes."""
        css_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/style.css"

        with open(css_path, 'r') as f:
            css_content = f.read()

        assert '@keyframes thinkingBounce' in css_content

    def test_css_has_progress_animation(self):
        """Test CSS includes progress bar animation."""
        css_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/style.css"

        with open(css_path, 'r') as f:
            css_content = f.read()

        assert '.thinking-progress' in css_content
        assert '.progress-bar' in css_content
        assert '@keyframes progressSlide' in css_content

    def test_css_has_thinking_text_styles(self):
        """Test CSS includes text styles for thinking indicator."""
        css_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/style.css"

        with open(css_path, 'r') as f:
            css_content = f.read()

        assert '.thinking-text' in css_content
        assert '.thinking-title' in css_content
        assert '.thinking-subtitle' in css_content


class TestThinkingIndicatorJS:
    """Tests for thinking indicator JavaScript functions."""

    def test_js_has_thinking_functions(self):
        """Test JavaScript includes thinking indicator functions."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Check for thinking functions
        assert 'addThinkingIndicator' in js_content
        assert 'startThinkingProgress' in js_content
        assert 'stopThinkingProgress' in js_content

    def test_js_calls_thinking_indicator(self):
        """Test JavaScript calls addThinkingIndicator when sending message."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Should call addThinkingIndicator in sendMessage
        assert 'addThinkingIndicator()' in js_content

    def test_js_stops_thinking_on_success(self):
        """Test JavaScript stops thinking progress on success."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Should call stopThinkingProgress
        assert 'stopThinkingProgress()' in js_content

    def test_js_has_progress_steps(self):
        """Test JavaScript has progress step messages."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Should have step messages
        assert 'Analyzing your request' in js_content
        assert 'Selecting relevant tools' in js_content
        assert 'Gathering information' in js_content

    def test_js_has_interval_management(self):
        """Test JavaScript manages thinking interval properly."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Should have interval variable and clear it
        assert 'thinkingInterval' in js_content
        assert 'clearInterval' in js_content
        assert 'setInterval' in js_content

    def test_js_shows_mode_in_thinking(self):
        """Test JavaScript shows current mode in thinking indicator."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Should reference currentMode
        assert 'currentMode' in js_content
        assert 'Deep Research' in js_content or 'deep' in js_content.lower()


class TestThinkingIndicatorIntegration:
    """Integration tests for thinking indicator."""

    def test_thinking_removed_after_response(self):
        """Test that thinking indicator is removed after getting response."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Should remove thinking message after response
        assert 'removeMessage(thinkingId)' in js_content

    def test_thinking_removed_on_error(self):
        """Test that thinking indicator is removed on error."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Check error handling includes removing thinking
        # The catch block should call stopThinkingProgress and removeMessage
        lines = js_content.split('\n')
        in_catch_block = False
        has_stop_in_catch = False

        for i, line in enumerate(lines):
            if 'catch (error)' in line:
                in_catch_block = True
            if in_catch_block and 'stopThinkingProgress()' in line:
                has_stop_in_catch = True
                break
            if in_catch_block and 'finally' in line:
                break

        assert has_stop_in_catch, "stopThinkingProgress should be called in catch block"


class TestThinkingIndicatorAccessibility:
    """Tests for thinking indicator accessibility."""

    def test_has_visible_text(self):
        """Test thinking indicator has visible text for screen readers."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Should have text content
        assert 'thinking-title' in js_content
        assert 'thinking-subtitle' in js_content

    def test_animation_not_too_fast(self):
        """Test thinking animation duration is accessible (not too fast)."""
        css_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/style.css"

        with open(css_path, 'r') as f:
            css_content = f.read()

        # Check specifically for thinking animation durations
        import re

        # Look for thinkingBounce animation duration
        bounce_match = re.search(r'\.thinking-dot[^}]*animation[^;]*?(\d+\.?\d*)s', css_content)
        if bounce_match:
            duration = float(bounce_match.group(1))
            assert duration >= 1.0, f"Thinking bounce animation {duration}s should be >= 1s"

        # Check progress animation exists and has reasonable duration
        progress_match = re.search(r'\.progress-bar[^}]*animation[^;]*?(\d+\.?\d*)s', css_content)
        if progress_match:
            duration = float(progress_match.group(1))
            assert duration >= 1.0, f"Progress animation {duration}s should be >= 1s"


class TestThinkingIndicatorUX:
    """Tests for thinking indicator user experience."""

    def test_shows_meaningful_messages(self):
        """Test thinking indicator shows meaningful progress messages."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Should have descriptive step messages
        expected_keywords = ['Analyzing', 'tools', 'information', 'AI', 'results']
        found_keywords = sum(1 for kw in expected_keywords if kw in js_content)

        assert found_keywords >= 3, "Should have multiple descriptive step messages"

    def test_progress_updates_periodically(self):
        """Test progress text updates at reasonable intervals."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Should have interval of 2000ms (2 seconds) or similar
        assert '2000' in js_content or '3000' in js_content, "Should update every 2-3 seconds"
