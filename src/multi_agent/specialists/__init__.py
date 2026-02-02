"""
Specialist Agents for B2B Intelligence

Each specialist agent is optimized for a specific domain:

- CompanyResearchAgent: Basic company information (founding, leadership, HQ)
- FinancialAnalystAgent: Financial metrics and calculations (market cap, P/E, revenue)
- CompetitiveIntelAgent: Market comparisons and competitive landscape
- ActionExecutorAgent: Email/calendar actions (privacy-conscious)
- GeneralFallbackAgent: Catch-all for unclassified queries
"""

# Import base classes
from .base_specialist import BaseSpecialist, AgentResponse, AgentStatus

# Import all specialist agents
from .company_research import CompanyResearchAgent
from .financial_analyst import FinancialAnalystAgent
from .competitive_intel import CompetitiveIntelAgent
from .action_executor import ActionExecutorAgent
from .general_fallback import GeneralFallbackAgent

__all__ = [
    # Base classes
    "BaseSpecialist",
    "AgentResponse",
    "AgentStatus",
    # Specialist agents
    "CompanyResearchAgent",
    "FinancialAnalystAgent",
    "CompetitiveIntelAgent",
    "ActionExecutorAgent",
    "GeneralFallbackAgent",
]
