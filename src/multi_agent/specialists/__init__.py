"""
Specialist Agents for B2B Intelligence

Each specialist agent is optimized for a specific domain:

- CompanyResearchAgent: Basic company information
- FinancialAnalystAgent: Financial metrics and calculations
- CompetitiveIntelAgent: Market comparisons
- ActionExecutorAgent: Email/calendar actions
- GeneralFallbackAgent: Catch-all for unclassified queries
"""

# Import base classes that exist
from .base_specialist import BaseSpecialist, AgentResponse, AgentStatus

__all__ = [
    "BaseSpecialist",
    "AgentResponse",
    "AgentStatus",
    "CompanyResearchAgent",
    "FinancialAnalystAgent",
    "CompetitiveIntelAgent",
    "ActionExecutorAgent",
    "GeneralFallbackAgent",
]


def __getattr__(name):
    """Lazy import for specialist agents."""
    if name == "CompanyResearchAgent":
        from .company_research import CompanyResearchAgent
        return CompanyResearchAgent
    elif name == "FinancialAnalystAgent":
        from .financial_analyst import FinancialAnalystAgent
        return FinancialAnalystAgent
    elif name == "CompetitiveIntelAgent":
        from .competitive_intel import CompetitiveIntelAgent
        return CompetitiveIntelAgent
    elif name == "ActionExecutorAgent":
        from .action_executor import ActionExecutorAgent
        return ActionExecutorAgent
    elif name == "GeneralFallbackAgent":
        from .general_fallback import GeneralFallbackAgent
        return GeneralFallbackAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
