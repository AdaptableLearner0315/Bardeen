"""
Multi-Agent B2B Account Intelligence System

This module implements a multi-agent architecture with specialized agents
for different B2B intelligence tasks:

- CompanyResearchAgent: Company facts, founding, leadership, products
- FinancialAnalystAgent: Market cap, revenue, financial calculations
- CompetitiveIntelAgent: Market comparisons, competitive landscape
- ActionExecutorAgent: Email and calendar operations
- GeneralFallbackAgent: Handles ambiguous or general queries

The Orchestrator (Claude Opus) routes queries to appropriate specialists
and synthesizes responses from multiple agents when needed.
"""

# Lazy imports - only import what exists
# These will be populated as modules are implemented

__all__ = [
    "Orchestrator",
    "QueryRouter",
    "RoutingDecision",
    "AgentExecutor",
    "ResponseSynthesizer",
]


def __getattr__(name):
    """Lazy import for modules that may not exist yet."""
    if name == "Orchestrator":
        from .orchestrator import Orchestrator
        return Orchestrator
    elif name == "QueryRouter":
        from .router import QueryRouter
        return QueryRouter
    elif name == "RoutingDecision":
        from .router import RoutingDecision
        return RoutingDecision
    elif name == "AgentExecutor":
        from .executor import AgentExecutor
        return AgentExecutor
    elif name == "ResponseSynthesizer":
        from .synthesizer import ResponseSynthesizer
        return ResponseSynthesizer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
