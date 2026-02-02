"""Tests for critical information extraction."""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock

# Import will work after module is updated
try:
    from src.agent.core.memory import CriticalInfoExtractor, get_critical_extractor
except ImportError:
    CriticalInfoExtractor = None
    get_critical_extractor = None


class TestCriticalInfoExtractor:
    """Tests for CriticalInfoExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        if CriticalInfoExtractor is None:
            pytest.skip("CriticalInfoExtractor not available")
        return CriticalInfoExtractor()

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        client = Mock()
        client.model = "test-model"
        client.client = Mock()
        return client

    def test_extractor_initialization(self, extractor):
        """Test extractor initializes properly."""
        assert extractor._llm_client is None
        assert extractor.EXTRACTION_PROMPT is not None

    def test_extraction_prompt_contains_types(self, extractor):
        """Verify extraction prompt mentions all types."""
        prompt = extractor.EXTRACTION_PROMPT
        assert "preference" in prompt.lower()
        assert "context" in prompt.lower()
        assert "correction" in prompt.lower()

    def test_extract_user_preference(self, extractor, mock_llm_client):
        """Extract preference from 'I prefer metric units'."""
        mock_response = Mock()
        mock_response.content = [Mock(type="text", text='{"items": [{"type": "preference", "content": "prefers metric units", "importance": "high"}]}')]
        mock_llm_client.client.messages.create.return_value = mock_response

        result = extractor.extract(
            "I prefer metric units",
            "Noted, I'll use metric units for measurements.",
            mock_llm_client
        )

        assert len(result) == 1
        assert result[0]["type"] == "preference"
        assert "metric" in result[0]["content"].lower()

    def test_extract_user_context(self, extractor, mock_llm_client):
        """Extract context from 'I'm a software engineer'."""
        mock_response = Mock()
        mock_response.content = [Mock(type="text", text='{"items": [{"type": "context", "content": "user is a software engineer", "importance": "high"}]}')]
        mock_llm_client.client.messages.create.return_value = mock_response

        result = extractor.extract(
            "I'm a software engineer working on Python projects",
            "Great! I can help with Python development.",
            mock_llm_client
        )

        assert len(result) == 1
        assert result[0]["type"] == "context"

    def test_extract_correction(self, extractor, mock_llm_client):
        """Extract when user corrects wrong answer."""
        mock_response = Mock()
        mock_response.content = [Mock(type="text", text='{"items": [{"type": "correction", "content": "Paris is not in Germany, it is in France", "importance": "high"}]}')]
        mock_llm_client.client.messages.create.return_value = mock_response

        result = extractor.extract(
            "Actually that's wrong, Paris is in France not Germany",
            "You're right, I apologize for the error.",
            mock_llm_client
        )

        assert len(result) == 1
        assert result[0]["type"] == "correction"

    def test_no_critical_info_returns_empty(self, extractor, mock_llm_client):
        """Normal Q&A returns empty list."""
        mock_response = Mock()
        mock_response.content = [Mock(type="text", text='{"items": []}')]
        mock_llm_client.client.messages.create.return_value = mock_response

        result = extractor.extract(
            "What is 2 + 2?",
            "2 + 2 equals 4.",
            mock_llm_client
        )

        assert result == []

    def test_malformed_json_handled(self, extractor, mock_llm_client):
        """Invalid JSON from LLM returns empty list."""
        mock_response = Mock()
        mock_response.content = [Mock(type="text", text='This is not valid JSON')]
        mock_llm_client.client.messages.create.return_value = mock_response

        result = extractor.extract(
            "Test question",
            "Test answer",
            mock_llm_client
        )

        # Should not raise, just return empty
        assert result == []

    def test_low_importance_filtered(self, extractor, mock_llm_client):
        """Only high/medium importance items stored."""
        mock_response = Mock()
        mock_response.content = [Mock(type="text", text='{"items": [{"type": "fact", "content": "some trivial fact", "importance": "low"}]}')]
        mock_llm_client.client.messages.create.return_value = mock_response

        result = extractor.extract(
            "Test question",
            "Test answer with trivial fact",
            mock_llm_client
        )

        # Low importance should be filtered out
        assert result == []

    def test_medium_importance_included(self, extractor, mock_llm_client):
        """Medium importance items are included."""
        mock_response = Mock()
        mock_response.content = [Mock(type="text", text='{"items": [{"type": "preference", "content": "likes detailed explanations", "importance": "medium"}]}')]
        mock_llm_client.client.messages.create.return_value = mock_response

        result = extractor.extract(
            "Can you explain that in more detail?",
            "Sure, here's a detailed explanation...",
            mock_llm_client
        )

        assert len(result) == 1

    def test_extraction_without_client_returns_empty(self, extractor):
        """Extraction without LLM client returns empty."""
        result = extractor.extract(
            "Test question",
            "Test answer",
            None
        )

        assert result == []

    def test_api_error_handled(self, extractor, mock_llm_client):
        """API errors are handled gracefully."""
        mock_llm_client.client.messages.create.side_effect = Exception("API Error")

        result = extractor.extract(
            "Test question",
            "Test answer",
            mock_llm_client
        )

        # Should not raise, just return empty
        assert result == []

    def test_extract_async_returns_immediately(self, extractor, mock_llm_client):
        """extract_async returns None immediately."""
        mock_response = Mock()
        mock_response.content = [Mock(type="text", text='{"items": []}')]
        mock_llm_client.client.messages.create.return_value = mock_response

        result = extractor.extract_async(
            "Test question",
            "Test answer",
            mock_llm_client
        )

        # Should return None immediately
        assert result is None


class TestCriticalExtractorSingleton:
    """Tests for global extractor singleton."""

    def test_get_critical_extractor_returns_instance(self):
        """get_critical_extractor returns an instance."""
        if get_critical_extractor is None:
            pytest.skip("get_critical_extractor not available")

        extractor = get_critical_extractor()
        assert extractor is not None
        assert isinstance(extractor, CriticalInfoExtractor)

    def test_get_critical_extractor_returns_singleton(self):
        """get_critical_extractor returns same instance."""
        if get_critical_extractor is None:
            pytest.skip("get_critical_extractor not available")

        ext1 = get_critical_extractor()
        ext2 = get_critical_extractor()

        assert ext1 is ext2
