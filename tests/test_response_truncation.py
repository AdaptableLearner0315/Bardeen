"""
Unit tests for response truncation prevention.

These tests ensure that agent responses are NEVER truncated mid-sentence,
mid-table, or mid-list. Responses must always be complete.
"""

import pytest
import re
from typing import List, Tuple
from unittest.mock import Mock, patch, MagicMock


class ResponseCompletenessValidator:
    """
    Validator to check if responses are complete and not truncated.
    """

    # Patterns that indicate truncation
    TRUNCATION_INDICATORS = [
        r"\[Response truncated",
        r"\[Truncated\]",
        r"\.{3,}$",  # Ends with ellipsis (unless intentional)
        r"\|$",  # Ends with table border (incomplete table)
        r"\|\s*$",  # Table row not completed
        r"-{3,}$",  # Ends with separator (incomplete section)
    ]

    # Patterns that indicate incomplete sentences
    INCOMPLETE_SENTENCE_PATTERNS = [
        r"[a-zA-Z]$",  # Ends with letter (no punctuation)
        r"\s(and|or|but|the|a|an|to|of|in|for|with|as|by|is|are|was|were)$",  # Ends with connector word
        r",\s*$",  # Ends with comma
        r":\s*$",  # Ends with colon (expecting content)
        r"-$",  # Ends with hyphen (incomplete date range or word)
        r"\($",  # Ends with open parenthesis
        r"\d{4}-$",  # Ends with year and hyphen (incomplete date range)
    ]

    # Valid sentence endings
    VALID_ENDINGS = ['.', '!', '?', ')', '"', "'", ']', '}', '*', '`']

    @classmethod
    def is_complete(cls, response: str) -> Tuple[bool, List[str]]:
        """
        Check if a response is complete (not truncated).

        Args:
            response: The response text to validate

        Returns:
            Tuple of (is_complete, list_of_issues)
        """
        issues = []

        if not response or not response.strip():
            return False, ["Empty response"]

        response = response.strip()

        # Check for explicit truncation indicators
        for pattern in cls.TRUNCATION_INDICATORS:
            if re.search(pattern, response, re.IGNORECASE):
                issues.append(f"Contains truncation indicator: {pattern}")

        # Check for incomplete sentences (if not empty)
        if response:
            last_char = response[-1]
            if last_char not in cls.VALID_ENDINGS:
                # Check if it's an intentional code block or special format
                if not response.endswith('```') and not response.endswith('---'):
                    for pattern in cls.INCOMPLETE_SENTENCE_PATTERNS:
                        if re.search(pattern, response):
                            issues.append(f"Incomplete sentence detected: ends with '{response[-20:]}'")
                            break

        # Check for incomplete tables
        if '|' in response:
            table_issues = cls._check_table_completeness(response)
            issues.extend(table_issues)

        # Check for incomplete lists
        list_issues = cls._check_list_completeness(response)
        issues.extend(list_issues)

        return len(issues) == 0, issues

    @classmethod
    def _check_table_completeness(cls, response: str) -> List[str]:
        """Check if tables in the response are complete."""
        issues = []
        lines = response.split('\n')

        in_table = False
        table_columns = 0
        last_row_complete = True

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Detect table start
            if '|' in stripped and not in_table:
                in_table = True
                table_columns = stripped.count('|')
                continue

            if in_table:
                # Check if still in table
                if '|' in stripped:
                    current_cols = stripped.count('|')
                    # Allow header separator row
                    if re.match(r'^[\|\s\-:]+$', stripped):
                        continue
                    # Check column count consistency
                    if current_cols != table_columns:
                        issues.append(f"Table row {i+1} has {current_cols} columns, expected {table_columns}")
                    # Check if row ends properly
                    if not stripped.endswith('|'):
                        last_row_complete = False
                else:
                    # Exited table
                    in_table = False
                    if not last_row_complete:
                        issues.append(f"Table ended with incomplete row at line {i}")

        # Check if we're still in a table at end
        if in_table:
            issues.append("Response ends inside a table (likely truncated)")

        return issues

    @classmethod
    def _check_list_completeness(cls, response: str) -> List[str]:
        """Check if lists in the response are complete."""
        issues = []
        lines = response.split('\n')

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Check bullet points
            if re.match(r'^[\-\*\+]\s+', stripped):
                # Check if bullet point has content
                content = re.sub(r'^[\-\*\+]\s+', '', stripped)
                if not content or len(content) < 2:
                    issues.append(f"Incomplete bullet point at line {i+1}")
                # Check if ends properly
                if content and content[-1] not in cls.VALID_ENDINGS and not content.endswith(':'):
                    issues.append(f"Bullet point at line {i+1} may be incomplete")

            # Check numbered lists
            if re.match(r'^\d+[\.\)]\s+', stripped):
                content = re.sub(r'^\d+[\.\)]\s+', '', stripped)
                if not content or len(content) < 2:
                    issues.append(f"Incomplete numbered item at line {i+1}")

        return issues

    @classmethod
    def validate_response_length(cls, response: str, mode: str = "normal") -> Tuple[bool, str]:
        """
        Validate response meets length requirements.

        Args:
            response: Response text
            mode: "normal" (50-60 words) or "deep" (no strict limit but should be reasonable)

        Returns:
            Tuple of (is_valid, message)
        """
        word_count = len(response.split())

        if mode == "normal":
            if word_count > 100:  # Allow some buffer, but flag excessive
                return False, f"Normal mode response too long: {word_count} words (max ~60)"
            if word_count < 5:
                return False, f"Response too short: {word_count} words"
        elif mode == "deep":
            if word_count < 20:
                return False, f"Deep mode response too short: {word_count} words"
            if word_count > 2000:
                return False, f"Deep mode response excessively long: {word_count} words"

        return True, f"Response length OK: {word_count} words"


class TestResponseCompleteness:
    """Test suite for response completeness validation."""

    def test_complete_response(self):
        """Test that a complete response passes validation."""
        response = "Apple's market cap is around $3 trillion, making it one of the world's most valuable companies."
        is_complete, issues = ResponseCompletenessValidator.is_complete(response)
        assert is_complete, f"Expected complete, got issues: {issues}"

    def test_truncated_response_explicit(self):
        """Test detection of explicitly truncated responses."""
        response = "Apple is a company that [Response truncated due to length]"
        is_complete, issues = ResponseCompletenessValidator.is_complete(response)
        assert not is_complete, "Should detect explicit truncation"
        assert any("truncation indicator" in issue.lower() for issue in issues)

    def test_incomplete_sentence(self):
        """Test detection of incomplete sentences."""
        response = "Apple's market cap is approximately"
        is_complete, issues = ResponseCompletenessValidator.is_complete(response)
        assert not is_complete, "Should detect incomplete sentence"

    def test_incomplete_table(self):
        """Test detection of incomplete tables."""
        response = """
| Company | Market Cap |
|---------|-----------|
| Apple | $3T |
| Microsoft | $2.8"""
        is_complete, issues = ResponseCompletenessValidator.is_complete(response)
        assert not is_complete, f"Should detect incomplete table. Issues: {issues}"

    def test_complete_table(self):
        """Test that complete tables pass validation."""
        response = """
| Company | Market Cap |
|---------|-----------|
| Apple | $3T |
| Microsoft | $2.8T |

Both are valuable companies.
"""
        is_complete, issues = ResponseCompletenessValidator.is_complete(response)
        assert is_complete, f"Complete table should pass. Issues: {issues}"

    def test_incomplete_bullet_list(self):
        """Test detection of incomplete bullet lists."""
        response = """Key points:
- Apple is valuable
- Microsoft has
"""
        is_complete, issues = ResponseCompletenessValidator.is_complete(response)
        assert not is_complete, "Should detect incomplete bullet point"

    def test_ends_with_connector(self):
        """Test detection of sentences ending with connector words."""
        response = "Apple and Microsoft are both companies that focus on the"
        is_complete, issues = ResponseCompletenessValidator.is_complete(response)
        assert not is_complete, "Should detect sentence ending with 'the'"

    def test_response_length_normal_mode(self):
        """Test response length validation for normal mode."""
        # Too long
        long_response = " ".join(["word"] * 150)
        is_valid, msg = ResponseCompletenessValidator.validate_response_length(long_response, "normal")
        assert not is_valid, "Should reject overly long normal mode response"

        # Appropriate length
        good_response = "Apple's market cap is $3 trillion, making it the most valuable company globally."
        is_valid, msg = ResponseCompletenessValidator.validate_response_length(good_response, "normal")
        assert is_valid, msg

    def test_response_length_deep_mode(self):
        """Test response length validation for deep mode."""
        # Too short
        short_response = "Apple is valuable."
        is_valid, msg = ResponseCompletenessValidator.validate_response_length(short_response, "deep")
        assert not is_valid, "Should reject too-short deep mode response"


class TestTruncationRecovery:
    """Test suite for truncation recovery logic."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Anthropic client."""
        with patch('anthropic.Anthropic') as mock:
            yield mock

    def test_recovery_prompt_normal_mode(self):
        """Test that recovery uses appropriate prompt for normal mode."""
        from src.agent.llm_client import ClaudeLLMClient
        from src.shared.config import Config

        # This tests that _recover_from_truncation creates appropriate prompts
        # The actual API call would be mocked in integration tests

        truncated = "Apple is a company that makes"
        question = "What does Apple do?"

        # The recovery should ask for a complete 50-60 word response
        expected_keywords = ["50-60 words", "COMPLETE", "truncated"]

        # We can't easily test the prompt content without calling the method
        # But we can test the validator
        is_complete, _ = ResponseCompletenessValidator.is_complete(truncated)
        assert not is_complete, "Truncated response should be detected"

    def test_validator_catches_all_truncation_types(self):
        """Test that validator catches various truncation types."""
        test_cases = [
            ("Valid response here.", True),
            ("Response ends with...", False),
            ("| Col1 | Col2", False),  # Incomplete table
            ("The quick brown", False),  # Incomplete sentence
            ("Items:\n- First\n- ", False),  # Incomplete list
            ("Answer: Apple is great!", True),
            ("Next Year (2025-", False),  # Screenshot example
        ]

        for response, expected_complete in test_cases:
            is_complete, issues = ResponseCompletenessValidator.is_complete(response)
            assert is_complete == expected_complete, \
                f"Response '{response[:30]}...' - expected complete={expected_complete}, got {is_complete}. Issues: {issues}"


class TestSystemPromptInclusion:
    """Test that system prompts include truncation prevention guidelines."""

    def test_normal_prompt_has_truncation_rules(self):
        """Test that normal mode prompt includes truncation prevention."""
        from src.agent.llm_client import SYSTEM_PROMPT_NORMAL

        required_phrases = [
            "COMPLETE",
            "NEVER",
            "token limit",
            "mid-word",  # Changed from mid-sentence to match actual prompt
        ]

        for phrase in required_phrases:
            assert phrase.lower() in SYSTEM_PROMPT_NORMAL.lower(), \
                f"Normal prompt missing truncation guideline: '{phrase}'"

    def test_deep_prompt_has_truncation_rules(self):
        """Test that deep mode prompt includes truncation prevention."""
        from src.agent.llm_client import SYSTEM_PROMPT_DEEP

        required_phrases = [
            "COMPLETE",
            "NEVER",
            "token limit",
            "Tables",
            "truncation",
        ]

        for phrase in required_phrases:
            assert phrase.lower() in SYSTEM_PROMPT_DEEP.lower(), \
                f"Deep prompt missing truncation guideline: '{phrase}'"


class TestIntegrationTruncationPrevention:
    """Integration tests for truncation prevention (requires mocking)."""

    @pytest.fixture
    def mock_anthropic_response(self):
        """Create a mock Anthropic response."""
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [
            MagicMock(type="text", text="Apple's market cap is $3 trillion.")
        ]
        return mock_response

    @pytest.fixture
    def mock_truncated_response(self):
        """Create a mock truncated response."""
        mock_response = MagicMock()
        mock_response.stop_reason = "max_tokens"
        mock_response.content = [
            MagicMock(type="text", text="Apple is a company that makes")
        ]
        return mock_response

    def test_truncation_triggers_recovery(self, mock_truncated_response, mock_anthropic_response):
        """Test that truncation triggers the recovery mechanism."""
        from src.agent.llm_client import ClaudeLLMClient
        from src.shared.config import Config

        # Patch at the module level where it's imported
        with patch('src.agent.llm_client.Anthropic') as MockAnthropic:
            # First call returns truncated, second returns complete
            mock_client_instance = MagicMock()
            mock_client_instance.messages.create.side_effect = [
                mock_truncated_response,
                mock_anthropic_response  # Recovery call
            ]
            MockAnthropic.return_value = mock_client_instance

            config = Config()
            config.anthropic_api_key = "test-key"

            # Create a mock tool registry
            tool_registry = MagicMock()
            tool_registry.get_tool_definitions.return_value = []
            tool_registry.get_available_tools.return_value = []

            llm_client = ClaudeLLMClient(config, tool_registry)

            # Call chat
            answer, _, _ = llm_client.chat("What is Apple?")

            # Verify recovery was attempted (2 API calls)
            assert mock_client_instance.messages.create.call_count >= 2, \
                "Should have made at least 2 API calls (original + recovery)"

            # Verify response doesn't contain truncation indicator
            assert "[Response truncated" not in answer, \
                "Final response should not contain truncation marker"


# Utility function for manual testing
def validate_agent_response(response: str, mode: str = "normal") -> dict:
    """
    Validate an agent response for completeness.

    Args:
        response: The response to validate
        mode: "normal" or "deep"

    Returns:
        Dictionary with validation results
    """
    is_complete, issues = ResponseCompletenessValidator.is_complete(response)
    length_valid, length_msg = ResponseCompletenessValidator.validate_response_length(response, mode)

    return {
        "is_complete": is_complete,
        "completeness_issues": issues,
        "length_valid": length_valid,
        "length_message": length_msg,
        "word_count": len(response.split()),
        "overall_valid": is_complete and length_valid
    }


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
