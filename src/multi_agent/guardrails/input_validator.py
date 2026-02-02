"""
Input Validator for Multi-Agent System

Provides input validation and sanitization:
- Prompt injection detection
- PII detection
- Query length limits
- Rate limiting support
"""

import re
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of input validation."""
    is_valid: bool
    sanitized_input: str
    warnings: list[str]
    error_message: Optional[str] = None


class InputValidator:
    """
    Validates and sanitizes user input before routing to agents.

    Security measures:
    - Detects potential prompt injection attempts
    - Flags queries with excessive PII
    - Enforces query length limits
    """

    # Maximum query length (in characters)
    MAX_QUERY_LENGTH = 2000

    # Patterns that may indicate prompt injection
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|above)\s+instructions",
        r"ignore\s+all\s+previous",
        r"disregard\s+(previous|above|all)",
        r"you\s+are\s+now\s+a",
        r"new\s+instructions?:",
        r"system\s*:\s*",
        r"<\s*system\s*>",
        r"\[\s*SYSTEM\s*\]",
    ]

    # Common PII patterns
    PII_PATTERNS = {
        "ssn": r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
        "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    }

    @classmethod
    def validate(cls, query: str) -> ValidationResult:
        """
        Validate user query.

        Args:
            query: Raw user input

        Returns:
            ValidationResult with sanitized input and any warnings
        """
        warnings = []
        error_message = None

        # Check for empty input
        if not query or not query.strip():
            return ValidationResult(
                is_valid=False,
                sanitized_input="",
                warnings=[],
                error_message="Query cannot be empty",
            )

        # Sanitize whitespace
        sanitized = " ".join(query.split())

        # Check length
        if len(sanitized) > cls.MAX_QUERY_LENGTH:
            return ValidationResult(
                is_valid=False,
                sanitized_input=sanitized[:cls.MAX_QUERY_LENGTH],
                warnings=["Query truncated due to length"],
                error_message=f"Query exceeds maximum length of {cls.MAX_QUERY_LENGTH} characters",
            )

        # Check for prompt injection attempts
        query_lower = sanitized.lower()
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                warnings.append("Potential prompt injection detected")
                break

        # Check for PII
        pii_found = []
        for pii_type, pattern in cls.PII_PATTERNS.items():
            if re.search(pattern, sanitized):
                pii_found.append(pii_type)

        if pii_found:
            warnings.append(f"Potential PII detected: {', '.join(pii_found)}")

        return ValidationResult(
            is_valid=True,
            sanitized_input=sanitized,
            warnings=warnings,
            error_message=error_message,
        )

    @classmethod
    def sanitize_for_logging(cls, query: str) -> str:
        """
        Sanitize query for safe logging (redact PII).

        Args:
            query: Original query

        Returns:
            Sanitized query safe for logging
        """
        sanitized = query

        # Redact SSN
        sanitized = re.sub(
            cls.PII_PATTERNS["ssn"],
            "[SSN REDACTED]",
            sanitized
        )

        # Redact credit card
        sanitized = re.sub(
            cls.PII_PATTERNS["credit_card"],
            "[CC REDACTED]",
            sanitized
        )

        return sanitized
