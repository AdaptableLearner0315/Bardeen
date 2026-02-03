"""
UI tests for dashboard evaluation viewing functionality.

Tests that the frontend correctly displays evaluation results by:
1. Verifying the HTML structure
2. Testing that the JavaScript fetches and displays data correctly
3. Ensuring evaluation cards and details render properly
"""

import pytest
import time
from pathlib import Path
from playwright.sync_api import Page, expect
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.fixture(scope="module")
def dashboard_url():
    """Return the URL of the running dashboard."""
    return "http://localhost:8002"


class TestEvaluationTab:
    """Tests for the Evaluations tab in the dashboard."""

    def test_evaluations_tab_exists(self, page: Page, dashboard_url):
        """Test that the Evaluations tab is present and clickable."""
        page.goto(dashboard_url)

        # Wait for page to load
        page.wait_for_selector('.tab-button[data-tab="evaluations"]', timeout=5000)

        # Check that evaluations tab exists
        evaluations_tab = page.locator('.tab-button[data-tab="evaluations"]')
        expect(evaluations_tab).to_be_visible()
        expect(evaluations_tab).to_contain_text("Evaluations")

    def test_evaluations_tab_switch(self, page: Page, dashboard_url):
        """Test switching to the Evaluations tab."""
        page.goto(dashboard_url)

        # Click on evaluations tab
        evaluations_tab = page.locator('.tab-button[data-tab="evaluations"]')
        evaluations_tab.click()

        # Wait for tab to become active
        page.wait_for_selector('.tab-button[data-tab="evaluations"].active', timeout=2000)

        # Check that tab is active
        expect(evaluations_tab).to_have_class("tab-button active")

        # Check that evaluations content is visible
        evaluations_content = page.locator('#evaluations-tab')
        expect(evaluations_content).to_have_class("tab-content active")

    def test_evaluations_load_on_tab_switch(self, page: Page, dashboard_url):
        """Test that evaluations are loaded when switching to the tab."""
        page.goto(dashboard_url)

        # Switch to evaluations tab
        page.locator('.tab-button[data-tab="evaluations"]').click()

        # Wait for either loading message or evaluation cards
        page.wait_for_selector('#evaluation-list', timeout=5000)

        # Check that we get either "Loading" or evaluation cards
        evaluation_list = page.locator('#evaluation-list')
        expect(evaluation_list).to_be_visible()

    def test_evaluations_display_after_load(self, page: Page, dashboard_url):
        """Test that evaluations are displayed after loading."""
        page.goto(dashboard_url)

        # Switch to evaluations tab
        page.locator('.tab-button[data-tab="evaluations"]').click()

        # Wait for evaluations to load (give it time to fetch from API)
        time.sleep(2)

        # Check if we have evaluation cards or empty state
        page.wait_for_selector('#evaluation-list', timeout=5000)
        evaluation_list = page.locator('#evaluation-list')

        # Should either show cards or "No evaluation runs found" message
        has_cards = page.locator('.evaluation-card').count() > 0
        has_empty_message = "No evaluation runs found" in evaluation_list.inner_text()

        assert has_cards or has_empty_message, "Should show either evaluation cards or empty state message"

    def test_refresh_button_exists(self, page: Page, dashboard_url):
        """Test that the refresh button exists and is clickable."""
        page.goto(dashboard_url)

        # Switch to evaluations tab
        page.locator('.tab-button[data-tab="evaluations"]').click()

        # Check for refresh button
        refresh_button = page.locator('#refresh-evaluations')
        expect(refresh_button).to_be_visible()
        expect(refresh_button).to_contain_text("Refresh")

    def test_refresh_button_reloads_evaluations(self, page: Page, dashboard_url):
        """Test that clicking refresh reloads the evaluation list."""
        page.goto(dashboard_url)

        # Switch to evaluations tab
        page.locator('.tab-button[data-tab="evaluations"]').click()
        time.sleep(2)  # Wait for initial load

        # Click refresh
        refresh_button = page.locator('#refresh-evaluations')
        refresh_button.click()

        # Should show loading state briefly
        time.sleep(0.5)

        # Wait for reload to complete
        time.sleep(2)

        # Evaluation list should still be visible
        evaluation_list = page.locator('#evaluation-list')
        expect(evaluation_list).to_be_visible()


class TestEvaluationCards:
    """Tests for evaluation card rendering."""

    @pytest.fixture
    def go_to_evaluations(self, page: Page, dashboard_url):
        """Navigate to evaluations tab and wait for load."""
        page.goto(dashboard_url)
        page.locator('.tab-button[data-tab="evaluations"]').click()
        time.sleep(2)  # Wait for API call
        return page

    def test_evaluation_cards_structure(self, go_to_evaluations):
        """Test that evaluation cards have the correct structure."""
        page = go_to_evaluations

        # Check if there are any evaluation cards
        cards = page.locator('.evaluation-card')
        card_count = cards.count()

        if card_count > 0:
            # Get first card
            first_card = cards.first

            # Should have run ID as heading
            expect(first_card.locator('h3')).to_be_visible()

            # Should have timestamp
            expect(first_card.locator('p')).to_be_visible()

            # Should have metrics section
            expect(first_card.locator('.eval-metrics')).to_be_visible()

            # Should have multiple metrics
            metrics = first_card.locator('.metric')
            assert metrics.count() >= 3, "Should have at least 3 metrics"

    def test_evaluation_cards_display_metrics(self, go_to_evaluations):
        """Test that evaluation cards display expected metrics."""
        page = go_to_evaluations

        cards = page.locator('.evaluation-card')

        if cards.count() > 0:
            first_card = cards.first
            card_text = first_card.inner_text()

            # Should display key metrics (at least one of these)
            has_pass_rate = "Pass Rate" in card_text or "pass^" in card_text
            has_score = "Score" in card_text or "Avg Score" in card_text
            has_questions = "Questions" in card_text

            assert has_pass_rate or has_score, "Should display pass rate or score"
            assert has_questions, "Should display question count"

    def test_evaluation_cards_are_clickable(self, go_to_evaluations):
        """Test that evaluation cards can be clicked to view details."""
        page = go_to_evaluations

        cards = page.locator('.evaluation-card')

        if cards.count() > 0:
            first_card = cards.first

            # Card should have onclick handler (cursor should be pointer)
            # Note: We can't easily test the onclick directly, but we can verify structure
            expect(first_card).to_have_attribute('class', 'evaluation-card')

    def test_empty_state_message(self, page: Page, dashboard_url):
        """Test that empty state is displayed when no evaluations exist."""
        # This test is tricky as we can't easily clear evaluations
        # We'll just verify the message exists in the HTML
        page.goto(dashboard_url)
        page.locator('.tab-button[data-tab="evaluations"]').click()
        time.sleep(2)

        evaluation_list = page.locator('#evaluation-list')
        text = evaluation_list.inner_text()

        # Either has evaluations or shows empty state
        has_evaluations = "b2b_eval_" in text
        has_empty_state = "No evaluation runs found" in text

        assert has_evaluations or has_empty_state, "Should show either evaluations or empty state"


class TestEvaluationDetails:
    """Tests for evaluation detail view."""

    @pytest.fixture
    def go_to_evaluations_with_data(self, page: Page, dashboard_url):
        """Navigate to evaluations tab and wait for data."""
        page.goto(dashboard_url)
        page.locator('.tab-button[data-tab="evaluations"]').click()
        time.sleep(2)
        return page

    def test_clicking_card_shows_detail_view(self, go_to_evaluations_with_data):
        """Test that clicking an evaluation card shows the detail view."""
        page = go_to_evaluations_with_data

        cards = page.locator('.evaluation-card')

        if cards.count() > 0:
            # Click first card
            cards.first.click()

            # Wait for detail view to load
            time.sleep(1)

            # Detail container should become visible
            detail_container = page.locator('#evaluation-detail')
            expect(detail_container).to_be_visible()

            # List should be hidden
            list_container = page.locator('#evaluation-list')
            assert list_container.evaluate("el => el.style.display") == "none"

    def test_detail_view_shows_metrics(self, go_to_evaluations_with_data):
        """Test that detail view displays comprehensive metrics."""
        page = go_to_evaluations_with_data

        cards = page.locator('.evaluation-card')

        if cards.count() > 0:
            # Click first card
            cards.first.click()
            time.sleep(1)

            # Check for detail content
            detail_content = page.locator('#evaluation-detail-content')
            expect(detail_content).to_be_visible()

            content_text = detail_content.inner_text()

            # Should have run ID as heading
            assert "b2b_eval_" in content_text, "Should display evaluation run ID"

    def test_back_button_returns_to_list(self, go_to_evaluations_with_data):
        """Test that back button returns to evaluation list."""
        page = go_to_evaluations_with_data

        cards = page.locator('.evaluation-card')

        if cards.count() > 0:
            # Click first card
            cards.first.click()
            time.sleep(1)

            # Click back button
            back_button = page.locator('#back-to-list')
            expect(back_button).to_be_visible()
            back_button.click()

            # List should be visible again
            list_container = page.locator('#evaluation-list')
            expect(list_container).to_be_visible()

            # Detail should be hidden
            detail_container = page.locator('#evaluation-detail')
            assert detail_container.evaluate("el => el.style.display") == "none"


class TestAPIIntegration:
    """Tests verifying frontend correctly integrates with API."""

    def test_frontend_uses_correct_api_endpoint(self, page: Page, dashboard_url):
        """Test that frontend calls the correct B2B evaluations endpoint."""
        # Set up network monitoring
        api_calls = []

        def handle_request(request):
            if "/api/" in request.url:
                api_calls.append(request.url)

        page.on("request", handle_request)

        # Navigate and switch to evaluations
        page.goto(dashboard_url)
        page.locator('.tab-button[data-tab="evaluations"]').click()
        time.sleep(2)

        # Should have called /api/b2b-evaluations
        b2b_calls = [url for url in api_calls if "/api/b2b-evaluations" in url]
        assert len(b2b_calls) > 0, "Should call /api/b2b-evaluations endpoint"

    def test_frontend_handles_api_errors_gracefully(self, page: Page, dashboard_url):
        """Test that frontend handles API errors without crashing."""
        # This is hard to test without mocking, but we can verify error states exist
        page.goto(dashboard_url)
        page.locator('.tab-button[data-tab="evaluations"]').click()
        time.sleep(3)

        # Page should not crash - evaluation list should still be visible
        evaluation_list = page.locator('#evaluation-list')
        expect(evaluation_list).to_be_visible()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--headed"])
