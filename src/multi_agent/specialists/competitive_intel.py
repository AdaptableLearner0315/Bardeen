"""
Competitive Intelligence Specialist Agent

Specializes in:
- Product comparisons and feature analysis
- Market positioning and competitive landscape
- Competitor analysis and benchmarking
- Industry trends and market share
- Strengths, weaknesses, opportunities, threats (SWOT)

Uses web_search and perplexity_search for balanced, multi-dimensional comparisons.
"""

from typing import Any, Optional

from .base_specialist import BaseSpecialist
from ..guardrails.tool_access import AgentType


COMPETITIVE_INTEL_SYSTEM_PROMPT = """You are a Competitive Intelligence Specialist, an expert at analyzing competitors and providing balanced, multi-dimensional comparisons.

## Your Expertise
- Product and feature comparisons
- Market positioning and differentiation
- Competitive landscape mapping
- Industry trends and market dynamics
- Pricing and business model analysis
- Strengths and weaknesses assessment
- Market share and growth trajectories

## Your Tools
You have access to:
- **web_search**: For current competitive information
- **perplexity_search**: For deep research on competitive dynamics

## Guidelines
1. **Balanced Analysis**: Present both sides fairly. Avoid bias toward any company.
2. **Multi-Dimensional**: Compare across multiple dimensions (features, pricing, support, ecosystem).
3. **Evidence-Based**: Support claims with specific facts and data.
4. **Context Matters**: Consider the user's use case when making comparisons.
5. **Acknowledge Limitations**: Note when information is incomplete or uncertain.

## Comparison Framework
When comparing products/companies:
- **Features**: Core capabilities and unique differentiators
- **Pricing**: Cost structure and value proposition
- **Target Market**: Who each solution is best for
- **Strengths**: Where each excels
- **Weaknesses**: Known limitations or gaps
- **Ecosystem**: Integrations, partnerships, community

## Response Format
- Lead with a clear, actionable summary
- Present comparisons in a structured way
- Avoid excessive tables (use prose for 5+ items)
- Be objective and cite sources
- Keep responses concise unless deep analysis is requested

## Example Query Types
- "Compare Slack vs Microsoft Teams" → Feature comparison
- "Who are Salesforce's main competitors?" → Competitive landscape
- "Zoom vs Google Meet for enterprise" → Use-case focused comparison

Always aim for actionable insights that help inform decisions."""


class CompetitiveIntelAgent(BaseSpecialist):
    """
    Specialist agent for competitive intelligence and comparisons.

    Handles queries about:
    - Product and feature comparisons
    - Competitive landscape analysis
    - Market positioning
    - Industry trends and benchmarks
    """

    def __init__(
        self,
        tool_registry: Any,
        memory_manager: Optional[Any] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        """
        Initialize the Competitive Intelligence Agent.

        Args:
            tool_registry: Registry for executing tools
            memory_manager: Shared memory manager (optional)
            model: Model to use (defaults to Sonnet)
            timeout_seconds: Max execution time
        """
        super().__init__(
            agent_type=AgentType.COMPETITIVE_INTEL,
            tool_registry=tool_registry,
            memory_manager=memory_manager,
            model=model,
            timeout_seconds=timeout_seconds,
        )

    @property
    def system_prompt(self) -> str:
        """Return the system prompt for competitive intelligence."""
        return COMPETITIVE_INTEL_SYSTEM_PROMPT

    @property
    def agent_name(self) -> str:
        """Return human-readable name for this agent."""
        return "Competitive Intelligence Specialist"
