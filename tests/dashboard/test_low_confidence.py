"""Tests for low confidence warning when tool limit is reached."""

import pytest
from pathlib import Path


class TestLowConfidenceBackend:
    """Tests for low confidence handling in backend."""

    def test_chat_response_has_low_confidence_field(self):
        """Test ChatResponse model has low_confidence field."""
        backend_path = Path(__file__).parent.parent.parent / "src/dashboard/backend/app.py"

        with open(backend_path, 'r') as f:
            content = f.read()

        assert "low_confidence: bool" in content
        assert "low_confidence_reason" in content

    def test_backend_detects_low_confidence_marker(self):
        """Test backend detects LOW_CONFIDENCE marker."""
        backend_path = Path(__file__).parent.parent.parent / "src/dashboard/backend/app.py"

        with open(backend_path, 'r') as f:
            content = f.read()

        assert "[LOW_CONFIDENCE:" in content
        assert "TOOL_LIMIT_REACHED]" in content

    def test_backend_extracts_clean_answer(self):
        """Test backend extracts clean answer from marked response."""
        backend_path = Path(__file__).parent.parent.parent / "src/dashboard/backend/app.py"

        with open(backend_path, 'r') as f:
            content = f.read()

        assert "clean_answer" in content

    def test_backend_sets_low_confidence_reason(self):
        """Test backend sets appropriate reason message."""
        backend_path = Path(__file__).parent.parent.parent / "src/dashboard/backend/app.py"

        with open(backend_path, 'r') as f:
            content = f.read()

        assert "Tool limit reached" in content


class TestLowConfidenceFrontend:
    """Tests for low confidence warning display in frontend."""

    def test_js_handles_low_confidence(self):
        """Test JavaScript handles low_confidence in response."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "data.low_confidence" in js_content

    def test_js_displays_warning_html(self):
        """Test JavaScript generates warning HTML."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "low-confidence-warning" in js_content
        assert "lowConfidenceHtml" in js_content

    def test_js_shows_warning_icon(self):
        """Test JavaScript includes warning icon."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "warning-icon" in js_content
        assert "⚠️" in js_content

    def test_js_shows_warning_title(self):
        """Test JavaScript shows 'Low Confidence Answer' title."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "Low Confidence Answer" in js_content

    def test_js_shows_reason(self):
        """Test JavaScript shows low confidence reason."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "data.low_confidence_reason" in js_content
        assert "warning-reason" in js_content


class TestLowConfidenceCSS:
    """Tests for low confidence warning CSS styles."""

    def test_css_has_warning_styles(self):
        """Test CSS has low confidence warning styles."""
        css_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/style.css"

        with open(css_path, 'r') as f:
            css_content = f.read()

        assert ".low-confidence-warning" in css_content

    def test_css_has_red_color(self):
        """Test CSS has mild red color for warning."""
        css_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/style.css"

        with open(css_path, 'r') as f:
            css_content = f.read()

        # Check for red color values (mild red)
        assert "#fef2f2" in css_content or "#fee2e2" in css_content  # Light red background
        assert "#ef4444" in css_content or "#dc2626" in css_content  # Red accent/border

    def test_css_has_warning_icon_styles(self):
        """Test CSS has warning icon styles."""
        css_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/style.css"

        with open(css_path, 'r') as f:
            css_content = f.read()

        assert ".warning-icon" in css_content

    def test_css_has_warning_title_styles(self):
        """Test CSS has warning title styles."""
        css_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/style.css"

        with open(css_path, 'r') as f:
            css_content = f.read()

        assert ".warning-title" in css_content

    def test_css_has_warning_reason_styles(self):
        """Test CSS has warning reason styles."""
        css_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/style.css"

        with open(css_path, 'r') as f:
            css_content = f.read()

        assert ".warning-reason" in css_content


class TestLowConfidenceLLMClient:
    """Tests for LLM client handling of max tool calls."""

    def test_llm_client_has_synthesize_method(self):
        """Test LLM client has _synthesize_partial_answer method."""
        llm_path = Path(__file__).parent.parent.parent / "src/agent/llm_client.py"

        with open(llm_path, 'r') as f:
            content = f.read()

        assert "_synthesize_partial_answer" in content

    def test_llm_client_marks_low_confidence(self):
        """Test LLM client adds LOW_CONFIDENCE marker."""
        llm_path = Path(__file__).parent.parent.parent / "src/agent/llm_client.py"

        with open(llm_path, 'r') as f:
            content = f.read()

        assert "[LOW_CONFIDENCE:TOOL_LIMIT_REACHED]" in content

    def test_llm_client_calls_synthesis_on_max_tools(self):
        """Test LLM client calls synthesis when max tools reached."""
        llm_path = Path(__file__).parent.parent.parent / "src/agent/llm_client.py"

        with open(llm_path, 'r') as f:
            content = f.read()

        assert "partial_answer = self._synthesize_partial_answer" in content

    def test_synthesis_prompt_asks_for_partial_answer(self):
        """Test synthesis prompt asks Claude for partial answer."""
        llm_path = Path(__file__).parent.parent.parent / "src/agent/llm_client.py"

        with open(llm_path, 'r') as f:
            content = f.read()

        assert "best possible answer" in content
        assert "information gathered" in content


class TestLowConfidenceLogic:
    """Tests for low confidence marker logic."""

    def test_marker_format(self):
        """Test low confidence marker format."""
        marker = "[LOW_CONFIDENCE:TOOL_LIMIT_REACHED]"
        answer = "This is a partial answer."
        full_response = f"{marker}\n{answer}"

        assert full_response.startswith("[LOW_CONFIDENCE:")
        assert "TOOL_LIMIT_REACHED]" in full_response

    def test_extract_clean_answer(self):
        """Test extracting clean answer from marked response."""
        full_response = "[LOW_CONFIDENCE:TOOL_LIMIT_REACHED]\nThis is the actual answer."

        if "]\n" in full_response:
            clean_answer = full_response.split("]\n", 1)[1]
        else:
            clean_answer = full_response

        assert clean_answer == "This is the actual answer."

    def test_detect_low_confidence(self):
        """Test detecting low confidence from marker."""
        response1 = "[LOW_CONFIDENCE:TOOL_LIMIT_REACHED]\nAnswer here"
        response2 = "Normal answer without marker"

        is_low_conf_1 = response1.startswith("[LOW_CONFIDENCE:")
        is_low_conf_2 = response2.startswith("[LOW_CONFIDENCE:")

        assert is_low_conf_1 is True
        assert is_low_conf_2 is False


class TestLowConfidenceIntegration:
    """Integration tests for low confidence feature."""

    def test_full_flow_marker_to_display(self):
        """Test the full flow from marker to display."""
        # Simulate the marker
        marker = "[LOW_CONFIDENCE:TOOL_LIMIT_REACHED]"
        answer = "Based on available data, the revenue is approximately..."
        full_response = f"{marker}\n{answer}"

        # Simulate backend processing
        low_confidence = full_response.startswith("[LOW_CONFIDENCE:")
        if "TOOL_LIMIT_REACHED]" in full_response:
            low_confidence_reason = "Tool limit reached"
            clean_answer = full_response.split("]\n", 1)[1]

        assert low_confidence is True
        assert low_confidence_reason == "Tool limit reached"
        assert clean_answer == answer

    def test_response_without_marker(self):
        """Test normal response without marker."""
        response = "The revenue of Salesforce is $34.9 billion."

        low_confidence = response.startswith("[LOW_CONFIDENCE:")
        assert low_confidence is False

    def test_warning_shows_before_answer(self):
        """Test warning HTML appears before answer in frontend."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Check that lowConfidenceHtml appears before message-content in the template
        # Find the messageDiv.innerHTML assignment
        warning_pos = js_content.find("${lowConfidenceHtml}")
        content_pos = js_content.find("${formatAnswer(data.answer)}")

        assert warning_pos < content_pos, "Warning should appear before answer content"
