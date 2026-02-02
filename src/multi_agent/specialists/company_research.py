"""
Company Research Specialist Agent

Specializes in:
- Company facts (founding date, founders, history)
- Leadership information (CEO, executives, board)
- Headquarters and locations
- Products and services
- IPO information and corporate structure
- Basic company overview and background

Uses web_search and wikipedia tools for factual lookups.
"""

from typing import Any, Optional

from .base_specialist import BaseSpecialist
from ..guardrails.tool_access import AgentType


COMPANY_RESEARCH_SYSTEM_PROMPT = """You are a Company Research Specialist, an expert at finding and presenting factual information about companies and organizations.

## Your Expertise
- Company founding dates, founders, and history
- Leadership teams (CEOs, executives, board members)
- Headquarters locations and office presence
- Products, services, and business lines
- IPO dates, stock symbols, and corporate structure
- Company mission, vision, and values
- Employee count and organizational structure

## Your Tools
You have access to:
- **web_search**: For current company information and news
- **wikipedia**: For established facts and historical data

## Guidelines
1. **Accuracy First**: Always verify facts from reliable sources. If uncertain, say so.
2. **Structured Data**: Present information in a clear, organized format.
3. **Source Attribution**: Cite your sources when providing information.
4. **Recency Awareness**: Note when information might be outdated (e.g., CEO changes).
5. **Disambiguation**: If a company name is ambiguous, clarify which company you're researching.

## Response Format
- Lead with the direct answer to the question
- Keep responses concise (50-60 words for simple queries)
- Use bullet points only when listing multiple items
- Include the data source when providing specific facts

## Example Query Types
- "When was Stripe founded?" → Factual lookup
- "Who is the CEO of Microsoft?" → Leadership query
- "Where is Apple headquartered?" → Location query
- "What products does Salesforce offer?" → Product overview

Always prioritize factual accuracy over comprehensiveness."""


class CompanyResearchAgent(BaseSpecialist):
    """
    Specialist agent for company research and factual lookups.

    Handles queries about:
    - Company founding, history, and background
    - Leadership and executives
    - Headquarters and locations
    - Products and services
    - IPO and corporate structure
    """

    def __init__(
        self,
        tool_registry: Any,
        memory_manager: Optional[Any] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        """
        Initialize the Company Research Agent.

        Args:
            tool_registry: Registry for executing tools
            memory_manager: Shared memory manager (optional)
            model: Model to use (defaults to Sonnet)
            timeout_seconds: Max execution time
        """
        super().__init__(
            agent_type=AgentType.COMPANY_RESEARCH,
            tool_registry=tool_registry,
            memory_manager=memory_manager,
            model=model,
            timeout_seconds=timeout_seconds,
        )

    @property
    def system_prompt(self) -> str:
        """Return the system prompt for company research."""
        return COMPANY_RESEARCH_SYSTEM_PROMPT

    @property
    def agent_name(self) -> str:
        """Return human-readable name for this agent."""
        return "Company Research Specialist"
