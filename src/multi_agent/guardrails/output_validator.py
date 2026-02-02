"""
Output Validator for Multi-Agent System

Validates agent responses:
- Confidence threshold checking
- Response length limits
- Source citation requirements
- Uncertainty flagging
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass

from .tool_access import AgentType

# Avoid circular import
if TYPE_CHECKING:
    from ..specialists.base_specialist import AgentResponse, AgentStatus


@dataclass
class OutputValidationResult:
    """Result of output validation."""
    is_valid: bool
    requires_citation: bool
    confidence_warning: bool
    length_warning: bool
    message: str


class OutputValidator:
    """
    Validates agent responses before returning to user.

    Ensures:
    - Responses meet minimum confidence thresholds
    - Citations are present when required
    - Response length is appropriate
    """

    # Minimum confidence for full acceptance
    MIN_CONFIDENCE_THRESHOLD = 0.6

    # Warning threshold for low confidence
    LOW_CONFIDENCE_THRESHOLD = 0.4

    # Maximum response length (characters)
    MAX_RESPONSE_LENGTH = 4000

    # Agents that must cite sources
    CITATION_REQUIRED_AGENTS = {
        AgentType.FINANCIAL_ANALYST,
        AgentType.COMPETITIVE_INTEL,
    }

    @classmethod
    def validate(cls, response: "AgentResponse") -> OutputValidationResult:
        """
        Validate an agent response.

        Args:
            response: AgentResponse to validate

        Returns:
            OutputValidationResult with validation details
        """
        # Runtime import to avoid circular dependency
        from ..specialists.base_specialist import AgentStatus

        is_valid = True
        requires_citation = False
        confidence_warning = False
        length_warning = False
        messages = []

        # Check for failed status
        if response.status in (AgentStatus.FAILED, AgentStatus.TIMEOUT):
            return OutputValidationResult(
                is_valid=False,
                requires_citation=False,
                confidence_warning=True,
                length_warning=False,
                message=f"Agent failed: {response.error_message}",
            )

        # Check confidence
        if response.confidence < cls.MIN_CONFIDENCE_THRESHOLD:
            is_valid = False
            confidence_warning = True
            messages.append(
                f"Low confidence ({response.confidence:.0%})"
            )
        elif response.confidence < cls.LOW_CONFIDENCE_THRESHOLD:
            confidence_warning = True
            messages.append(
                f"Warning: confidence below threshold ({response.confidence:.0%})"
            )

        # Check citation requirements
        if response.agent_type in cls.CITATION_REQUIRED_AGENTS:
            requires_citation = True
            if not response.sources:
                messages.append(
                    f"{response.agent_type.value} should provide sources"
                )

        # Check response length
        if len(response.answer) > cls.MAX_RESPONSE_LENGTH:
            length_warning = True
            messages.append(
                f"Response exceeds {cls.MAX_RESPONSE_LENGTH} characters"
            )

        return OutputValidationResult(
            is_valid=is_valid,
            requires_citation=requires_citation,
            confidence_warning=confidence_warning,
            length_warning=length_warning,
            message="; ".join(messages) if messages else "Valid",
        )

    @classmethod
    def add_uncertainty_notice(cls, response: AgentResponse) -> str:
        """
        Add uncertainty notice to response if confidence is low.

        Args:
            response: AgentResponse to check

        Returns:
            Modified answer with uncertainty notice if needed
        """
        if response.confidence < cls.LOW_CONFIDENCE_THRESHOLD:
            notice = (
                "\n\n*Note: This response has lower confidence. "
                "Please verify the information from additional sources.*"
            )
            return response.answer + notice

        return response.answer

    @classmethod
    def format_with_sources(cls, response: AgentResponse) -> str:
        """
        Format response with source citations.

        Args:
            response: AgentResponse with sources

        Returns:
            Formatted answer with sources section
        """
        if not response.sources:
            return response.answer

        sources_section = "\n\n**Sources:**\n"
        for i, source in enumerate(response.sources, 1):
            sources_section += f"{i}. {source}\n"

        return response.answer + sources_section
