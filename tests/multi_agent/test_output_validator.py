"""
Unit tests for OutputValidator

Tests:
- Confidence threshold checking
- Citation requirements per agent
- Response length validation
- Uncertainty notices
- Source formatting
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.multi_agent.guardrails.output_validator import OutputValidator, OutputValidationResult
from src.multi_agent.guardrails.tool_access import AgentType
from src.multi_agent.specialists.base_specialist import AgentResponse, AgentStatus


class TestOutputValidator:
    """Tests for OutputValidator class."""

    def _create_response(
        self,
        agent_type: AgentType = AgentType.GENERAL_FALLBACK,
        answer: str = "Test answer",
        status: AgentStatus = AgentStatus.SUCCESS,
        confidence: float = 1.0,
        sources: list = None,
    ) -> AgentResponse:
        """Helper to create test responses."""
        return AgentResponse(
            agent_type=agent_type,
            query="test query",
            answer=answer,
            status=status,
            confidence=confidence,
            sources=sources or [],
        )

    def test_valid_high_confidence_response(self):
        """High confidence response should be valid."""
        response = self._create_response(confidence=0.9)
        result = OutputValidator.validate(response)
        assert result.is_valid
        assert not result.confidence_warning

    def test_low_confidence_invalid(self):
        """Response below min confidence threshold should be invalid."""
        response = self._create_response(confidence=0.3)
        result = OutputValidator.validate(response)
        assert not result.is_valid
        assert result.confidence_warning
        assert "confidence" in result.message.lower()

    def test_medium_confidence_warning(self):
        """Response below warning threshold should have warning."""
        response = self._create_response(confidence=0.5)
        result = OutputValidator.validate(response)
        # Still valid but with warning
        assert result.confidence_warning

    def test_failed_status_invalid(self):
        """Failed status should be invalid."""
        response = self._create_response(
            status=AgentStatus.FAILED,
            confidence=1.0,
        )
        response.error_message = "Something went wrong"
        result = OutputValidator.validate(response)
        assert not result.is_valid
        assert "failed" in result.message.lower()

    def test_timeout_status_invalid(self):
        """Timeout status should be invalid."""
        response = self._create_response(status=AgentStatus.TIMEOUT)
        response.error_message = "Timed out"
        result = OutputValidator.validate(response)
        assert not result.is_valid

    def test_financial_analyst_requires_citation(self):
        """Financial Analyst responses should require citations."""
        response = self._create_response(
            agent_type=AgentType.FINANCIAL_ANALYST,
            sources=[],
        )
        result = OutputValidator.validate(response)
        assert result.requires_citation
        assert "sources" in result.message.lower()

    def test_competitive_intel_requires_citation(self):
        """Competitive Intel responses should require citations."""
        response = self._create_response(
            agent_type=AgentType.COMPETITIVE_INTEL,
            sources=[],
        )
        result = OutputValidator.validate(response)
        assert result.requires_citation

    def test_company_research_no_citation_required(self):
        """Company Research does not require citations."""
        response = self._create_response(
            agent_type=AgentType.COMPANY_RESEARCH,
            sources=[],
        )
        result = OutputValidator.validate(response)
        assert not result.requires_citation

    def test_response_length_warning(self):
        """Long responses should trigger warning."""
        long_answer = "a" * (OutputValidator.MAX_RESPONSE_LENGTH + 100)
        response = self._create_response(answer=long_answer)
        result = OutputValidator.validate(response)
        assert result.length_warning
        assert "characters" in result.message.lower()

    def test_add_uncertainty_notice_low_confidence(self):
        """Low confidence should add uncertainty notice."""
        response = self._create_response(
            answer="The market cap is $3 trillion.",
            confidence=0.3,
        )
        modified = OutputValidator.add_uncertainty_notice(response)
        assert "verify" in modified.lower()
        assert "Note:" in modified

    def test_add_uncertainty_notice_high_confidence(self):
        """High confidence should not add notice."""
        response = self._create_response(
            answer="The market cap is $3 trillion.",
            confidence=0.9,
        )
        modified = OutputValidator.add_uncertainty_notice(response)
        assert modified == response.answer

    def test_format_with_sources(self):
        """Sources should be formatted as list."""
        response = self._create_response(
            answer="Apple is worth $3T.",
            sources=["https://example.com", "https://another.com"],
        )
        formatted = OutputValidator.format_with_sources(response)
        assert "Sources:" in formatted
        assert "1. https://example.com" in formatted
        assert "2. https://another.com" in formatted

    def test_format_with_no_sources(self):
        """No sources should return original answer."""
        response = self._create_response(answer="Test answer", sources=[])
        formatted = OutputValidator.format_with_sources(response)
        assert formatted == "Test answer"


class TestOutputValidationResult:
    """Tests for OutputValidationResult dataclass."""

    def test_validation_result_creation(self):
        """OutputValidationResult should be created correctly."""
        result = OutputValidationResult(
            is_valid=True,
            requires_citation=False,
            confidence_warning=False,
            length_warning=False,
            message="Valid",
        )
        assert result.is_valid
        assert result.message == "Valid"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
