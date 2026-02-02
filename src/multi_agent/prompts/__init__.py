"""
System Prompts for Multi-Agent System

Contains specialized prompts for:
- Orchestrator: Query classification and routing
- Company Research Agent: Structured company data extraction
- Financial Analyst Agent: Financial metrics and calculations
- Competitive Intel Agent: Market comparisons
- Action Executor Agent: Email/calendar operations
- General Fallback Agent: General-purpose reasoning
"""

__all__ = [
    "ORCHESTRATOR_SYSTEM_PROMPT",
    "CLASSIFICATION_PROMPT",
    "COMPANY_RESEARCH_PROMPT",
    "FINANCIAL_ANALYST_PROMPT",
    "COMPETITIVE_INTEL_PROMPT",
    "ACTION_EXECUTOR_PROMPT",
    "GENERAL_FALLBACK_PROMPT",
]


def __getattr__(name):
    """Lazy import for prompts."""
    if name in ("ORCHESTRATOR_SYSTEM_PROMPT", "CLASSIFICATION_PROMPT"):
        from .orchestrator_prompt import ORCHESTRATOR_SYSTEM_PROMPT, CLASSIFICATION_PROMPT
        if name == "ORCHESTRATOR_SYSTEM_PROMPT":
            return ORCHESTRATOR_SYSTEM_PROMPT
        return CLASSIFICATION_PROMPT
    elif name == "COMPANY_RESEARCH_PROMPT":
        from .company_prompt import COMPANY_RESEARCH_PROMPT
        return COMPANY_RESEARCH_PROMPT
    elif name == "FINANCIAL_ANALYST_PROMPT":
        from .financial_prompt import FINANCIAL_ANALYST_PROMPT
        return FINANCIAL_ANALYST_PROMPT
    elif name == "COMPETITIVE_INTEL_PROMPT":
        from .competitive_prompt import COMPETITIVE_INTEL_PROMPT
        return COMPETITIVE_INTEL_PROMPT
    elif name == "ACTION_EXECUTOR_PROMPT":
        from .action_prompt import ACTION_EXECUTOR_PROMPT
        return ACTION_EXECUTOR_PROMPT
    elif name == "GENERAL_FALLBACK_PROMPT":
        from .general_prompt import GENERAL_FALLBACK_PROMPT
        return GENERAL_FALLBACK_PROMPT
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
