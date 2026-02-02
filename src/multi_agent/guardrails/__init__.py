"""
Guardrails and Safety for Multi-Agent System

Provides:
- Tool access control per agent type
- Input validation and sanitization
- Output validation and confidence checking
- Rate limiting and timeout handling
"""

# Import modules that don't have circular dependencies
from .tool_access import ToolAccessMatrix, AgentType
from .input_validator import InputValidator, ValidationResult

__all__ = [
    "ToolAccessMatrix",
    "AgentType",
    "InputValidator",
    "ValidationResult",
    "OutputValidator",
    "OutputValidationResult",
]


def __getattr__(name):
    """Lazy import for modules with circular dependencies."""
    if name == "OutputValidator":
        from .output_validator import OutputValidator
        return OutputValidator
    elif name == "OutputValidationResult":
        from .output_validator import OutputValidationResult
        return OutputValidationResult
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
