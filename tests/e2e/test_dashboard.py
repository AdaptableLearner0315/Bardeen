"""End-to-end tests for the Research Assistant Dashboard using Playwright."""

import pytest
import json
import re
import asyncio
from pathlib import Path
from typing import Generator
import threading
import time

import uvicorn
from playwright.sync_api import Page, expect, Playwright

# Server configuration
TEST_PORT = 8765
TEST_BASE_URL = f"http://localhost:{TEST_PORT}"


class ServerThread(threading.Thread):
    """Run the FastAPI server in a background thread."""

    def __init__(self, port: int):
        super().__init__(daemon=True)
        self.port = port
        self.server = None

    def run(self):
        """Start the server."""
        from src.dashboard.backend.app import app
        config = uvicorn.Config(app, host="127.0.0.1", port=self.port, log_level="warning")
        self.server = uvicorn.Server(config)
        self.server.run()

    def stop(self):
        """Stop the server."""
        if self.server:
            self.server.should_exit = True


@pytest.fixture(scope="module")
def server():
    """Start the test server."""
    server_thread = ServerThread(TEST_PORT)
    server_thread.start()
    # Wait for server to start
    time.sleep(2)
    yield server_thread
    server_thread.stop()


@pytest.fixture(scope="module")
def browser_context(playwright: Playwright, server):
    """Create browser context for tests."""
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    yield context
    context.close()
    browser.close()


@pytest.fixture
def page(browser_context) -> Generator[Page, None, None]:
    """Create a new page for each test."""
    page = browser_context.new_page()
    yield page
    page.close()


class TestDashboardLoad:
    """Tests for dashboard loading."""

    def test_dashboard_loads(self, page: Page):
        """Test that the dashboard loads successfully."""
        page.goto(TEST_BASE_URL)

        # Check title
        expect(page).to_have_title("Research Assistant Dashboard")

    def test_header_displays(self, page: Page):
        """Test that header is displayed."""
        page.goto(TEST_BASE_URL)

        # Check header text
        header = page.locator("h1")
        expect(header).to_contain_text("Research Assistant Dashboard")

    def test_tabs_display(self, page: Page):
        """Test that navigation tabs are displayed."""
        page.goto(TEST_BASE_URL)

        # Check all tabs are present
        expect(page.locator('[data-tab="chat"]')).to_be_visible()
        expect(page.locator('[data-tab="evaluations"]')).to_be_visible()
        expect(page.locator('[data-tab="dataset"]')).to_be_visible()

    def test_chat_tab_active_by_default(self, page: Page):
        """Test that chat tab is active by default."""
        page.goto(TEST_BASE_URL)

        # Chat tab should be active
        chat_tab = page.locator('[data-tab="chat"]')
        expect(chat_tab).to_have_class(re.compile(r"active"))

        # Chat content should be visible
        chat_content = page.locator("#chat-tab")
        expect(chat_content).to_have_class(re.compile(r"active"))


class TestStatusIndicator:
    """Tests for health status indicator."""

    def test_status_indicator_displays(self, page: Page):
        """Test that status indicator is present."""
        page.goto(TEST_BASE_URL)

        status_dot = page.locator("#status-dot")
        status_text = page.locator("#status-text")

        expect(status_dot).to_be_visible()
        expect(status_text).to_be_visible()

    def test_status_updates_after_health_check(self, page: Page):
        """Test that status updates after health check."""
        page.goto(TEST_BASE_URL)

        # Wait for health check to complete
        page.wait_for_timeout(1000)

        # Status should update from "Checking connection..."
        status_text = page.locator("#status-text")
        # Either "Connected" or "Offline" depending on agent status
        expect(status_text).not_to_have_text("Checking connection...")


class TestTabNavigation:
    """Tests for tab navigation."""

    def test_switch_to_evaluations_tab(self, page: Page):
        """Test switching to evaluations tab."""
        page.goto(TEST_BASE_URL)

        # Click evaluations tab
        page.click('[data-tab="evaluations"]')

        # Evaluations tab should be active
        eval_tab = page.locator('[data-tab="evaluations"]')
        expect(eval_tab).to_have_class(re.compile(r"active"))

        # Evaluations content should be visible
        eval_content = page.locator("#evaluations-tab")
        expect(eval_content).to_have_class(re.compile(r"active"))

        # Chat content should be hidden
        chat_content = page.locator("#chat-tab")
        expect(chat_content).not_to_have_class(re.compile(r"active"))

    def test_switch_to_dataset_tab(self, page: Page):
        """Test switching to dataset tab."""
        page.goto(TEST_BASE_URL)

        # Click dataset tab
        page.click('[data-tab="dataset"]')

        # Dataset tab should be active
        dataset_tab = page.locator('[data-tab="dataset"]')
        expect(dataset_tab).to_have_class(re.compile(r"active"))

        # Dataset content should be visible
        dataset_content = page.locator("#dataset-tab")
        expect(dataset_content).to_have_class(re.compile(r"active"))

    def test_switch_back_to_chat_tab(self, page: Page):
        """Test switching back to chat tab."""
        page.goto(TEST_BASE_URL)

        # Switch to evaluations first
        page.click('[data-tab="evaluations"]')

        # Switch back to chat
        page.click('[data-tab="chat"]')

        # Chat tab should be active again
        chat_tab = page.locator('[data-tab="chat"]')
        expect(chat_tab).to_have_class(re.compile(r"active"))

    def test_tab_switching_multiple_times(self, page: Page):
        """Test switching tabs multiple times."""
        page.goto(TEST_BASE_URL)

        tabs = ["evaluations", "dataset", "chat", "evaluations", "chat"]

        for tab in tabs:
            page.click(f'[data-tab="{tab}"]')
            tab_button = page.locator(f'[data-tab="{tab}"]')
            expect(tab_button).to_have_class(re.compile(r"active"))


class TestChatTab:
    """Tests for chat tab functionality."""

    def test_chat_input_displays(self, page: Page):
        """Test that chat input is displayed."""
        page.goto(TEST_BASE_URL)

        chat_input = page.locator("#chat-input")
        expect(chat_input).to_be_visible()

    def test_send_button_displays(self, page: Page):
        """Test that send button is displayed."""
        page.goto(TEST_BASE_URL)

        send_button = page.locator("#send-button")
        expect(send_button).to_be_visible()
        expect(send_button).to_have_text("Send")

    def test_reset_conversation_checkbox(self, page: Page):
        """Test that reset conversation checkbox is present."""
        page.goto(TEST_BASE_URL)

        reset_checkbox = page.locator("#reset-conversation")
        expect(reset_checkbox).to_be_visible()
        expect(reset_checkbox).not_to_be_checked()

    def test_welcome_message_displays(self, page: Page):
        """Test that welcome message is displayed."""
        page.goto(TEST_BASE_URL)

        welcome = page.locator(".welcome-message")
        expect(welcome).to_be_visible()
        expect(welcome).to_contain_text("Welcome to the Research Assistant")

    def test_available_tools_section(self, page: Page):
        """Test that available tools section is present."""
        page.goto(TEST_BASE_URL)

        tools_element = page.locator("#available-tools")
        expect(tools_element).to_be_visible()

    def test_type_in_chat_input(self, page: Page):
        """Test typing in chat input."""
        page.goto(TEST_BASE_URL)

        chat_input = page.locator("#chat-input")
        chat_input.fill("What is 2+2?")

        expect(chat_input).to_have_value("What is 2+2?")

    def test_clear_chat_input(self, page: Page):
        """Test clearing chat input."""
        page.goto(TEST_BASE_URL)

        chat_input = page.locator("#chat-input")
        chat_input.fill("Some text")
        chat_input.fill("")

        expect(chat_input).to_have_value("")

    def test_check_reset_checkbox(self, page: Page):
        """Test checking reset conversation checkbox."""
        page.goto(TEST_BASE_URL)

        reset_checkbox = page.locator("#reset-conversation")
        reset_checkbox.check()

        expect(reset_checkbox).to_be_checked()


class TestEvaluationsTab:
    """Tests for evaluations tab functionality."""

    def test_evaluation_list_container(self, page: Page):
        """Test that evaluation list container is present."""
        page.goto(TEST_BASE_URL)
        page.click('[data-tab="evaluations"]')

        eval_list = page.locator("#evaluation-list")
        expect(eval_list).to_be_visible()

    def test_refresh_button_displays(self, page: Page):
        """Test that refresh button is displayed."""
        page.goto(TEST_BASE_URL)
        page.click('[data-tab="evaluations"]')

        refresh_button = page.locator("#refresh-evaluations")
        expect(refresh_button).to_be_visible()
        expect(refresh_button).to_contain_text("Refresh")

    def test_loading_state(self, page: Page):
        """Test loading state is shown initially."""
        page.goto(TEST_BASE_URL)
        page.click('[data-tab="evaluations"]')

        # Initially shows loading or results
        eval_list = page.locator("#evaluation-list")
        expect(eval_list).to_be_visible()

    def test_back_button_hidden_initially(self, page: Page):
        """Test that back button is hidden initially."""
        page.goto(TEST_BASE_URL)
        page.click('[data-tab="evaluations"]')

        back_button = page.locator("#back-to-list")
        detail_container = page.locator("#evaluation-detail")

        # Detail view should be hidden
        expect(detail_container).to_be_hidden()


class TestDatasetTab:
    """Tests for dataset tab functionality."""

    def test_dataset_stats_container(self, page: Page):
        """Test that dataset stats container is present."""
        page.goto(TEST_BASE_URL)
        page.click('[data-tab="dataset"]')

        stats = page.locator("#dataset-stats")
        expect(stats).to_be_visible()

    def test_dataset_questions_container(self, page: Page):
        """Test that dataset questions container is present."""
        page.goto(TEST_BASE_URL)
        page.click('[data-tab="dataset"]')

        questions = page.locator("#dataset-questions")
        expect(questions).to_be_visible()

    def test_dataset_header(self, page: Page):
        """Test that dataset header is displayed."""
        page.goto(TEST_BASE_URL)
        page.click('[data-tab="dataset"]')

        header = page.locator(".dataset-container h2")
        expect(header).to_contain_text("Evaluation Dataset")


class TestResponsiveDesign:
    """Tests for responsive design elements."""

    def test_container_is_centered(self, page: Page):
        """Test that main container exists."""
        page.goto(TEST_BASE_URL)

        container = page.locator(".container")
        expect(container).to_be_visible()

    def test_chat_container_in_chat_tab(self, page: Page):
        """Test chat container exists in chat tab."""
        page.goto(TEST_BASE_URL)

        chat_container = page.locator(".chat-container")
        expect(chat_container).to_be_visible()

    def test_messages_container_exists(self, page: Page):
        """Test chat messages container exists."""
        page.goto(TEST_BASE_URL)

        messages = page.locator("#chat-messages")
        expect(messages).to_be_visible()


class TestAccessibility:
    """Tests for accessibility features."""

    def test_page_has_language(self, page: Page):
        """Test that page has language attribute."""
        page.goto(TEST_BASE_URL)

        html = page.locator("html")
        expect(html).to_have_attribute("lang", "en")

    def test_chat_input_has_placeholder(self, page: Page):
        """Test that chat input has placeholder text."""
        page.goto(TEST_BASE_URL)

        chat_input = page.locator("#chat-input")
        expect(chat_input).to_have_attribute("placeholder", "Ask a question...")

    def test_buttons_have_text(self, page: Page):
        """Test that buttons have descriptive text."""
        page.goto(TEST_BASE_URL)

        send_button = page.locator("#send-button")
        expect(send_button).to_have_text("Send")

    def test_tabs_have_labels(self, page: Page):
        """Test that tabs have readable labels."""
        page.goto(TEST_BASE_URL)

        chat_tab = page.locator('[data-tab="chat"]')
        eval_tab = page.locator('[data-tab="evaluations"]')
        dataset_tab = page.locator('[data-tab="dataset"]')

        expect(chat_tab).to_contain_text("Live Chat")
        expect(eval_tab).to_contain_text("Evaluations")
        expect(dataset_tab).to_contain_text("Dataset")


class TestKeyboardNavigation:
    """Tests for keyboard navigation."""

    def test_tab_navigation(self, page: Page):
        """Test that elements can be focused via Tab key."""
        page.goto(TEST_BASE_URL)

        # Focus first tab
        page.keyboard.press("Tab")

        # Should be able to navigate through tabs
        # At least the page should not crash
        page.keyboard.press("Tab")
        page.keyboard.press("Tab")

    def test_enter_key_in_chat(self, page: Page):
        """Test that Enter key behavior in chat input."""
        page.goto(TEST_BASE_URL)

        chat_input = page.locator("#chat-input")
        chat_input.focus()
        chat_input.fill("Test message")

        # Regular Enter should not submit (it's for newlines)
        # Ctrl+Enter or Cmd+Enter should submit
        # Just verify the input is still there after Enter
        page.keyboard.press("Enter")
        expect(chat_input).to_have_value("Test message\n")


class TestChatInteraction:
    """Tests for chat interaction (requires server)."""

    def test_empty_message_not_sent(self, page: Page):
        """Test that empty messages are not sent."""
        page.goto(TEST_BASE_URL)

        # Don't type anything, just click send
        page.click("#send-button")

        # No user message should appear
        user_messages = page.locator(".message.user")
        expect(user_messages).to_have_count(0)

    def test_message_added_to_chat(self, page: Page):
        """Test that user message appears in chat."""
        page.goto(TEST_BASE_URL)

        # Wait for page to load
        page.wait_for_timeout(500)

        chat_input = page.locator("#chat-input")
        chat_input.fill("Test question")

        # Click send
        page.click("#send-button")

        # User message should appear
        page.wait_for_timeout(500)
        user_message = page.locator(".message.user")
        expect(user_message).to_be_visible()

    def test_input_cleared_after_send(self, page: Page):
        """Test that input is cleared after sending."""
        page.goto(TEST_BASE_URL)
        page.wait_for_timeout(500)

        chat_input = page.locator("#chat-input")
        chat_input.fill("Test message")
        page.click("#send-button")

        # Input should be cleared
        page.wait_for_timeout(500)
        expect(chat_input).to_have_value("")


class TestAPIIntegration:
    """Tests for API integration."""

    def test_health_endpoint_called(self, page: Page):
        """Test that health endpoint is called on load."""
        # Set up request interception
        health_called = []

        def handle_request(route):
            if "/api/health" in route.request.url:
                health_called.append(True)
            route.continue_()

        page.route("**/api/health", handle_request)
        page.goto(TEST_BASE_URL)

        # Wait for health check
        page.wait_for_timeout(1000)

        assert len(health_called) > 0, "Health endpoint was not called"

    def test_evaluations_endpoint_called_on_tab_switch(self, page: Page):
        """Test that evaluations endpoint is called when switching tabs."""
        eval_called = []

        def handle_request(route):
            if "/api/evaluations" in route.request.url:
                eval_called.append(True)
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps({"evaluations": []})
                )
            else:
                route.continue_()

        page.route("**/api/evaluations", handle_request)
        page.goto(TEST_BASE_URL)

        # Switch to evaluations tab
        page.click('[data-tab="evaluations"]')
        page.wait_for_timeout(500)

        assert len(eval_called) > 0, "Evaluations endpoint was not called"

    def test_dataset_endpoint_called_on_tab_switch(self, page: Page):
        """Test that dataset endpoint is called when switching tabs."""
        dataset_called = []

        def handle_request(route):
            if "/api/dataset" in route.request.url:
                dataset_called.append(True)
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps({
                        "metadata": {},
                        "statistics": {"total_questions": 0, "categories": {}},
                        "questions": []
                    })
                )
            else:
                route.continue_()

        page.route("**/api/dataset", handle_request)
        page.goto(TEST_BASE_URL)

        # Switch to dataset tab
        page.click('[data-tab="dataset"]')
        page.wait_for_timeout(500)

        assert len(dataset_called) > 0, "Dataset endpoint was not called"


class TestErrorHandling:
    """Tests for error handling in the UI."""

    def test_handles_api_error_gracefully(self, page: Page):
        """Test that API errors are handled gracefully."""
        # Mock health endpoint to return error
        def handle_request(route):
            if "/api/health" in route.request.url:
                route.fulfill(status=500, body="Internal Server Error")
            else:
                route.continue_()

        page.route("**/api/health", handle_request)
        page.goto(TEST_BASE_URL)

        # Wait for health check
        page.wait_for_timeout(1000)

        # Page should still be functional
        expect(page.locator("h1")).to_be_visible()
        # Status should show offline
        status_text = page.locator("#status-text")
        expect(status_text).to_contain_text("Offline")

    def test_handles_network_error(self, page: Page):
        """Test that network errors are handled."""
        # Abort all health requests
        page.route("**/api/health", lambda route: route.abort())
        page.goto(TEST_BASE_URL)

        # Wait for error handling
        page.wait_for_timeout(1000)

        # Page should still display
        expect(page.locator("h1")).to_be_visible()


class TestMockedChatResponse:
    """Tests with mocked chat responses."""

    def test_displays_assistant_response(self, page: Page):
        """Test that assistant response is displayed."""
        # Mock chat endpoint
        def handle_chat(route):
            if "/api/chat" in route.request.url:
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps({
                        "answer": "The answer is 4",
                        "tool_calls": [],
                        "errors": [],
                        "ascii_trace": "[trace]",
                        "latency_ms": 100
                    })
                )
            else:
                route.continue_()

        page.route("**/api/chat", handle_chat)
        page.goto(TEST_BASE_URL)

        # Send a message
        chat_input = page.locator("#chat-input")
        chat_input.fill("What is 2+2?")
        page.click("#send-button")

        # Wait for response
        page.wait_for_timeout(1000)

        # Assistant message should appear
        assistant_message = page.locator(".message.assistant")
        expect(assistant_message).to_be_visible()
        expect(assistant_message).to_contain_text("The answer is 4")

    def test_displays_tool_calls(self, page: Page):
        """Test that tool calls are displayed."""
        def handle_chat(route):
            if "/api/chat" in route.request.url:
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps({
                        "answer": "The answer is 4",
                        "tool_calls": [
                            {"tool_name": "calculator", "latency_ms": 50, "status": "success"}
                        ],
                        "errors": [],
                        "ascii_trace": "[trace]",
                        "latency_ms": 100
                    })
                )
            else:
                route.continue_()

        page.route("**/api/chat", handle_chat)
        page.goto(TEST_BASE_URL)

        chat_input = page.locator("#chat-input")
        chat_input.fill("Calculate something")
        page.click("#send-button")

        page.wait_for_timeout(1000)

        # Tool info should appear
        tool_info = page.locator(".tool-info")
        expect(tool_info).to_be_visible()
        expect(tool_info).to_contain_text("calculator")

    def test_displays_latency(self, page: Page):
        """Test that latency is displayed."""
        def handle_chat(route):
            if "/api/chat" in route.request.url:
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps({
                        "answer": "Response",
                        "tool_calls": [],
                        "errors": [],
                        "ascii_trace": "",
                        "latency_ms": 250
                    })
                )
            else:
                route.continue_()

        page.route("**/api/chat", handle_chat)
        page.goto(TEST_BASE_URL)

        chat_input = page.locator("#chat-input")
        chat_input.fill("Test")
        page.click("#send-button")

        page.wait_for_timeout(1000)

        # Latency should be displayed
        latency = page.locator(".latency")
        expect(latency).to_be_visible()
        expect(latency).to_contain_text("250ms")
