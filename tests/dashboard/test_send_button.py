"""Tests for send button and Enter key functionality."""

import pytest
from pathlib import Path


class TestSendButtonJS:
    """Tests for send button JavaScript functionality."""

    def test_js_has_send_button_click_handler(self):
        """Test JavaScript has click handler for send button."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "sendButton.addEventListener('click'" in js_content or \
               'sendButton.addEventListener("click"' in js_content

    def test_js_has_enter_key_handler(self):
        """Test JavaScript has Enter key handler."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "e.key === 'Enter'" in js_content or \
               'e.key === "Enter"' in js_content

    def test_js_sends_on_enter_without_shift(self):
        """Test JavaScript sends message on Enter (without Shift)."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Should check for Enter AND not Shift
        assert '!e.shiftKey' in js_content, "Should check that Shift is not pressed"

    def test_js_prevents_default_on_enter(self):
        """Test JavaScript prevents default on Enter to avoid new line."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert 'e.preventDefault()' in js_content, "Should prevent default Enter behavior"

    def test_js_has_send_message_function(self):
        """Test JavaScript has sendMessage function."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert 'function sendMessage()' in js_content or \
               'async function sendMessage()' in js_content

    def test_js_calls_send_message_on_enter(self):
        """Test JavaScript calls sendMessage when Enter is pressed."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Find the keydown handler and check it calls sendMessage
        lines = js_content.split('\n')
        in_keydown_handler = False
        found_send_call = False

        for line in lines:
            if 'keydown' in line and 'addEventListener' in line:
                in_keydown_handler = True
            if in_keydown_handler and 'sendMessage()' in line:
                found_send_call = True
                break
            if in_keydown_handler and '});' in line:
                break

        assert found_send_call, "sendMessage should be called in keydown handler"


class TestSendButtonHTML:
    """Tests for send button HTML structure."""

    def test_html_has_send_button(self):
        """Test HTML has send button element."""
        html_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/index.html"

        with open(html_path, 'r') as f:
            html_content = f.read()

        assert 'id="send-button"' in html_content

    def test_html_has_chat_input(self):
        """Test HTML has chat input textarea."""
        html_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/index.html"

        with open(html_path, 'r') as f:
            html_content = f.read()

        assert 'id="chat-input"' in html_content

    def test_html_send_button_has_text(self):
        """Test send button has visible text."""
        html_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/index.html"

        with open(html_path, 'r') as f:
            html_content = f.read()

        # Button should have "Send" text
        assert 'Send' in html_content


class TestSendMessageFlow:
    """Tests for the complete send message flow."""

    def test_js_gets_input_value(self):
        """Test JavaScript gets value from chat input."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert 'input.value' in js_content or 'chatInput.value' in js_content

    def test_js_trims_message(self):
        """Test JavaScript trims whitespace from message."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert '.trim()' in js_content

    def test_js_checks_empty_message(self):
        """Test JavaScript checks for empty message."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Should have a check like "if (!message) return"
        assert '!message' in js_content or 'message === ""' in js_content or \
               'message.length' in js_content

    def test_js_disables_input_while_sending(self):
        """Test JavaScript disables input while sending."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert 'input.disabled = true' in js_content or \
               'disabled = true' in js_content

    def test_js_disables_button_while_sending(self):
        """Test JavaScript disables send button while sending."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert 'sendButton.disabled = true' in js_content

    def test_js_clears_input_after_send(self):
        """Test JavaScript clears input after sending."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "input.value = ''" in js_content or \
               'input.value = ""' in js_content

    def test_js_re_enables_input_after_response(self):
        """Test JavaScript re-enables input after response."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert 'input.disabled = false' in js_content

    def test_js_focuses_input_after_response(self):
        """Test JavaScript focuses input after response."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert 'input.focus()' in js_content


class TestShiftEnterNewLine:
    """Tests for Shift+Enter new line functionality."""

    def test_js_allows_shift_enter_newline(self):
        """Test Shift+Enter allows new line (doesn't send)."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # The condition should be: Enter AND NOT Shift
        # This means Shift+Enter won't trigger send
        assert '!e.shiftKey' in js_content

    def test_js_comment_explains_shift_enter(self):
        """Test code has comment explaining Shift+Enter behavior."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        # Should have a comment about Shift+Enter
        assert 'Shift+Enter' in js_content or 'shift' in js_content.lower()


class TestAPICall:
    """Tests for API call in send message."""

    def test_js_calls_chat_api(self):
        """Test JavaScript calls /api/chat endpoint."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert '/api/chat' in js_content or '/chat' in js_content

    def test_js_sends_post_request(self):
        """Test JavaScript sends POST request."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "method: 'POST'" in js_content or \
               'method: "POST"' in js_content

    def test_js_sends_json_content_type(self):
        """Test JavaScript sends JSON content type."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert 'application/json' in js_content

    def test_js_includes_message_in_body(self):
        """Test JavaScript includes message in request body."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert 'message:' in js_content or '"message"' in js_content

    def test_js_includes_mode_in_body(self):
        """Test JavaScript includes mode in request body."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert 'mode:' in js_content or '"mode"' in js_content


class TestErrorHandling:
    """Tests for error handling in send message."""

    def test_js_has_try_catch(self):
        """Test JavaScript has try-catch for error handling."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert 'try {' in js_content
        assert 'catch' in js_content

    def test_js_handles_http_error(self):
        """Test JavaScript handles HTTP errors."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert 'response.ok' in js_content or 'status' in js_content

    def test_js_shows_error_message(self):
        """Test JavaScript shows error message to user."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert 'Error:' in js_content or 'error.message' in js_content
