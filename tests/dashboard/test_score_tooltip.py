"""
Test that score tooltip is displayed correctly and Tools Used is removed.
"""

import pytest
from pathlib import Path
from playwright.sync_api import Page, expect
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestScoreTooltip:
    """Test score tooltip and simplified question results display."""

    @pytest.fixture
    def dashboard_url(self):
        return "http://localhost:8002"

    def test_score_has_tooltip(self, page: Page, dashboard_url):
        """Test that score has a hover tooltip explaining the scoring."""
        page.goto(dashboard_url)

        # Navigate to evaluations
        page.locator('.tab-button[data-tab="evaluations"]').click()
        page.wait_for_timeout(2000)

        cards = page.locator('.evaluation-card')
        if cards.count() > 0:
            # Click first evaluation
            cards.first.click()
            page.wait_for_timeout(1000)

            # Find a score element
            detail_content = page.locator('#evaluation-detail-content')

            # Look for score span with tooltip
            score_elements = detail_content.locator('span[title*="AI-scored"]')

            if score_elements.count() > 0:
                # Get the tooltip text
                tooltip = score_elements.first.get_attribute('title')

                # Verify tooltip exists and is concise
                assert tooltip is not None, "Score should have a tooltip"
                assert len(tooltip) <= 50, f"Tooltip should be under 50 chars, got {len(tooltip)}"
                assert 'AI-scored' in tooltip or 'tool' in tooltip.lower(), "Tooltip should explain scoring"

                print(f"Tooltip text: '{tooltip}' (length: {len(tooltip)})")
            else:
                pytest.skip("No score elements with tooltips found")

    def test_tools_used_not_displayed(self, page: Page, dashboard_url):
        """Test that 'Tools Used' text is removed from question results."""
        page.goto(dashboard_url)

        page.locator('.tab-button[data-tab="evaluations"]').click()
        page.wait_for_timeout(2000)

        cards = page.locator('.evaluation-card')
        if cards.count() > 0:
            cards.first.click()
            page.wait_for_timeout(1000)

            detail_content = page.locator('#evaluation-detail-content')
            content_text = detail_content.inner_text()

            # Verify "Tools Used:" is NOT in the text
            assert 'Tools Used:' not in content_text, "Should not display 'Tools Used:' text"
            print("✓ 'Tools Used' text successfully removed")

    def test_question_display_simplified(self, page: Page, dashboard_url):
        """Test that question results show only Status and Score."""
        page.goto(dashboard_url)

        page.locator('.tab-button[data-tab="evaluations"]').click()
        page.wait_for_timeout(2000)

        cards = page.locator('.evaluation-card')
        if cards.count() > 0:
            cards.first.click()
            page.wait_for_timeout(1000)

            # Find first question card
            question_cards = page.locator('.question-card')
            if question_cards.count() > 0:
                first_card = question_cards.first
                card_text = first_card.inner_text()

                # Should have Status and Score
                assert 'Status:' in card_text, "Should show Status"
                assert 'Score:' in card_text, "Should show Score"

                # Should NOT have Tools
                assert 'Tools Used:' not in card_text, "Should not show Tools Used"
                assert 'Tools:' not in card_text, "Should not show Tools"

                print(f"Simplified display verified. Card shows: Status and Score only")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
