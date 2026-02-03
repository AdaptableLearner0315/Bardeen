"""
Unit tests for question results display with correct field mapping.

Tests that score and depth are correctly extracted from the actual data structure
where questions have 'score' (not 'avg_score') and 'tools_used' array.
"""

import pytest
from pathlib import Path
from playwright.sync_api import Page, expect
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestQuestionResultsDisplay:
    """Tests for correct display of question scores and depths."""

    @pytest.fixture
    def dashboard_url(self):
        """Return the URL of the running dashboard."""
        return "http://localhost:8002"

    def test_question_scores_are_not_zero(self, page: Page, dashboard_url):
        """Test that question scores display actual values, not 0.0."""
        page.goto(dashboard_url)

        # Navigate to evaluations and click first card
        page.locator('.tab-button[data-tab="evaluations"]').click()
        page.wait_for_timeout(2000)

        cards = page.locator('.evaluation-card')
        if cards.count() > 0:
            cards.first.click()
            page.wait_for_timeout(1000)

            # Get question results section
            detail_content = page.locator('#evaluation-detail-content')
            content_text = detail_content.inner_text()

            # Check that scores are NOT all "0.0/100" or "0/100"
            # Should have at least some scores > 0
            import re
            scores = re.findall(r'Score: (\d+(?:\.\d+)?)/100', content_text)

            assert len(scores) > 0, "Should find score values in content"

            # At least one score should be non-zero
            non_zero_scores = [s for s in scores if float(s) > 0]
            assert len(non_zero_scores) > 0, f"Should have at least one non-zero score, found: {scores}"

            # Print for debugging
            print(f"Found scores: {scores}")
            print(f"Non-zero scores: {non_zero_scores}")

    def test_tool_count_displays_correctly(self, page: Page, dashboard_url):
        """Test that tool count (depth) displays correctly from tools_used array."""
        page.goto(dashboard_url)

        page.locator('.tab-button[data-tab="evaluations"]').click()
        page.wait_for_timeout(2000)

        cards = page.locator('.evaluation-card')
        if cards.count() > 0:
            cards.first.click()
            page.wait_for_timeout(1000)

            detail_content = page.locator('#evaluation-detail-content')
            content_text = detail_content.inner_text()

            # Should show "Tools Used: N" where N > 0 for most questions
            import re
            tool_counts = re.findall(r'Tools Used: (\d+)', content_text)

            assert len(tool_counts) > 0, "Should find tool count values"

            # At least one tool count should be non-zero
            non_zero_tools = [t for t in tool_counts if int(t) > 0]
            assert len(non_zero_tools) > 0, f"Should have questions with tools used, found: {tool_counts}"

            print(f"Found tool counts: {tool_counts}")

    def test_question_cards_show_complete_information(self, page: Page, dashboard_url):
        """Test that question cards show status, score, and tool count."""
        page.goto(dashboard_url)

        page.locator('.tab-button[data-tab="evaluations"]').click()
        page.wait_for_timeout(2000)

        cards = page.locator('.evaluation-card')
        if cards.count() > 0:
            cards.first.click()
            page.wait_for_timeout(1000)

            # Find all question cards
            question_cards = page.locator('.question-card')
            card_count = question_cards.count()

            assert card_count > 0, "Should have at least one question card"

            # Check first question card has all required elements
            first_card = question_cards.first
            card_text = first_card.inner_text()

            # Should have status indicator
            has_status = '✓' in card_text or '✗' in card_text
            assert has_status, "Should show status icon (✓ or ✗)"

            # Should have score (not 0.0)
            assert 'Score:' in card_text, "Should show score label"
            assert '/100' in card_text, "Should show score out of 100"

            # Should have tools used
            assert 'Tools Used:' in card_text, "Should show tools used label"

            print(f"First question card content: {card_text[:200]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
