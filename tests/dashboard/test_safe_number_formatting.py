"""
Unit tests for safe number formatting in evaluation detail rendering.

Tests that the frontend correctly handles undefined/null values when rendering
evaluation details, preventing "Cannot read properties of undefined" errors.
"""

import pytest
from pathlib import Path
from playwright.sync_api import Page, expect
import sys
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestSafeNumberFormatting:
    """Tests for safe number formatting in evaluation details."""

    @pytest.fixture
    def dashboard_url(self):
        """Return the URL of the running dashboard."""
        return "http://localhost:8002"

    def test_evaluation_detail_handles_missing_fields(self, page: Page, dashboard_url):
        """Test that evaluation detail view doesn't crash with missing numeric fields."""
        page.goto(dashboard_url)

        # Switch to evaluations tab
        page.locator('.tab-button[data-tab="evaluations"]').click()
        page.wait_for_timeout(2000)  # Wait for evaluations to load

        # Check if there are evaluation cards
        cards = page.locator('.evaluation-card')
        card_count = cards.count()

        if card_count > 0:
            # Click first card to view details
            cards.first.click()
            page.wait_for_timeout(1000)  # Wait for detail to load

            # Detail should be visible without errors
            detail_content = page.locator('#evaluation-detail-content')
            expect(detail_content).to_be_visible()

            # Should not show error message about undefined
            content_text = detail_content.inner_text()
            assert "undefined" not in content_text.lower(), "Should not display 'undefined' in content"
            assert "cannot read properties" not in content_text.lower(), "Should not show error message"

            # Should display run ID
            assert "b2b_eval_" in content_text, "Should display evaluation run ID"

    def test_evaluation_detail_displays_metrics(self, page: Page, dashboard_url):
        """Test that evaluation detail displays all expected metrics."""
        page.goto(dashboard_url)

        # Switch to evaluations tab
        page.locator('.tab-button[data-tab="evaluations"]').click()
        page.wait_for_timeout(2000)

        cards = page.locator('.evaluation-card')

        if cards.count() > 0:
            # Click first card
            cards.first.click()
            page.wait_for_timeout(1000)

            detail_content = page.locator('#evaluation-detail-content')
            content_text = detail_content.inner_text()

            # Should display key metrics (check for at least some of these)
            has_pass_rate = "Pass Rate" in content_text or "pass^" in content_text
            has_score = "Score" in content_text or "Avg Score" in content_text
            has_category = "By Category" in content_text

            assert has_pass_rate, "Should display pass rate"
            assert has_score, "Should display score"
            assert has_category, "Should display category section"

    def test_evaluation_detail_shows_category_breakdown(self, page: Page, dashboard_url):
        """Test that category breakdown is displayed correctly."""
        page.goto(dashboard_url)

        page.locator('.tab-button[data-tab="evaluations"]').click()
        page.wait_for_timeout(2000)

        cards = page.locator('.evaluation-card')

        if cards.count() > 0:
            cards.first.click()
            page.wait_for_timeout(1000)

            detail_content = page.locator('#evaluation-detail-content')

            # Should have a "By Category" section
            expect(detail_content.locator('h3:has-text("By Category")')).to_be_visible()

            # Should have category metrics
            content_text = detail_content.inner_text()

            # Should show at least one category name
            categories_shown = any(cat in content_text.lower() for cat in [
                'company', 'financial', 'competitive', 'strategic', 'customer', 'standard'
            ])
            assert categories_shown, "Should display at least one category name"

    def test_evaluation_detail_handles_zero_values(self, page: Page, dashboard_url):
        """Test that zero values are displayed correctly (not as 'undefined')."""
        page.goto(dashboard_url)

        page.locator('.tab-button[data-tab="evaluations"]').click()
        page.wait_for_timeout(2000)

        cards = page.locator('.evaluation-card')

        if cards.count() > 0:
            cards.first.click()
            page.wait_for_timeout(1000)

            detail_content = page.locator('#evaluation-detail-content')
            content_text = detail_content.inner_text()

            # If there are metrics with 0 values, they should display as "0.0" or "0%", not "undefined"
            # Check that numbers are formatted properly
            import re

            # Find all percentage values
            percentages = re.findall(r'(\d+\.?\d*)%', content_text)
            assert len(percentages) > 0, "Should display at least one percentage value"

            # All should be valid numbers
            for pct in percentages:
                assert pct != "NaN", f"Percentage should not be NaN: {pct}"
                try:
                    float(pct)
                except ValueError:
                    pytest.fail(f"Invalid percentage format: {pct}")

    def test_back_button_works_after_viewing_detail(self, page: Page, dashboard_url):
        """Test that back button returns to list after viewing detail."""
        page.goto(dashboard_url)

        page.locator('.tab-button[data-tab="evaluations"]').click()
        page.wait_for_timeout(2000)

        cards = page.locator('.evaluation-card')

        if cards.count() > 0:
            # Click to view detail
            cards.first.click()
            page.wait_for_timeout(1000)

            # Click back button
            back_button = page.locator('#back-to-list')
            expect(back_button).to_be_visible()
            back_button.click()

            # Should be back at list view
            list_container = page.locator('#evaluation-list')
            expect(list_container).to_be_visible()

            # Cards should still be visible
            expect(cards.first).to_be_visible()


class TestSafeFixedHelperFunction:
    """Tests for the safeFixed helper function behavior."""

    def test_helper_function_exists_in_javascript(self, page: Page):
        """Test that the safeFixed helper function is defined."""
        page.goto("http://localhost:8002")

        # Evaluate the existence of safeFixed function
        has_safe_fixed = page.evaluate("typeof safeFixed === 'function'")
        assert has_safe_fixed, "safeFixed helper function should be defined"

    def test_safe_fixed_handles_undefined(self, page: Page):
        """Test that safeFixed correctly handles undefined values."""
        page.goto("http://localhost:8002")

        # Test undefined returns default
        result = page.evaluate("safeFixed(undefined, 1, 0)")
        assert result == "0.0", f"Expected '0.0' but got '{result}'"

    def test_safe_fixed_handles_null(self, page: Page):
        """Test that safeFixed correctly handles null values."""
        page.goto("http://localhost:8002")

        result = page.evaluate("safeFixed(null, 1, 0)")
        assert result == "0.0", f"Expected '0.0' but got '{result}'"

    def test_safe_fixed_handles_nan(self, page: Page):
        """Test that safeFixed correctly handles NaN values."""
        page.goto("http://localhost:8002")

        result = page.evaluate("safeFixed(NaN, 1, 0)")
        assert result == "0.0", f"Expected '0.0' but got '{result}'"

    def test_safe_fixed_handles_valid_numbers(self, page: Page):
        """Test that safeFixed correctly formats valid numbers."""
        page.goto("http://localhost:8002")

        # Test integer
        result = page.evaluate("safeFixed(42, 1)")
        assert result == "42.0", f"Expected '42.0' but got '{result}'"

        # Test float
        result = page.evaluate("safeFixed(42.567, 2)")
        assert result == "42.57", f"Expected '42.57' but got '{result}'"

        # Test zero
        result = page.evaluate("safeFixed(0, 1)")
        assert result == "0.0", f"Expected '0.0' but got '{result}'"

    def test_safe_fixed_respects_decimal_places(self, page: Page):
        """Test that safeFixed respects the decimal places parameter."""
        page.goto("http://localhost:8002")

        # 0 decimals
        result = page.evaluate("safeFixed(42.567, 0)")
        assert result == "43", f"Expected '43' but got '{result}'"

        # 2 decimals
        result = page.evaluate("safeFixed(42.567, 2)")
        assert result == "42.57", f"Expected '42.57' but got '{result}'"

        # 3 decimals
        result = page.evaluate("safeFixed(42.567, 3)")
        assert result == "42.567", f"Expected '42.567' but got '{result}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
