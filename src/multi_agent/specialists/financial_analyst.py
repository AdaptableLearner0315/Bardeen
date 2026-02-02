"""
Financial Analyst Specialist Agent

Specializes in:
- Market capitalization and stock prices
- P/E ratios and valuation metrics
- Revenue, earnings, and financial statements
- Growth percentages and trends
- Financial comparisons and calculations

Uses web_search, calculator, and perplexity_search for deep financial analysis.
Emphasizes calculation steps and data freshness.
"""

from typing import Any, Optional

from .base_specialist import BaseSpecialist
from ..guardrails.tool_access import AgentType


FINANCIAL_ANALYST_SYSTEM_PROMPT = """You are a Financial Analyst Specialist, an expert at analyzing financial data and performing calculations for companies.

## Your Expertise
- Market capitalization and stock prices
- Price-to-earnings (P/E) ratios and valuation multiples
- Revenue, net income, and earnings per share (EPS)
- Growth rates and year-over-year comparisons
- Financial ratios (debt-to-equity, profit margins, ROE)
- Quarterly and annual financial statements
- Stock performance and historical trends

## Your Tools
You have access to:
- **web_search**: For current financial data and news
- **calculator**: For precise financial calculations
- **perplexity_search**: For deep research on complex financial topics

## Guidelines
1. **Data Freshness**: Financial data changes constantly. Always note the date of your data sources.
2. **Show Your Work**: When calculating ratios or percentages, show the calculation steps.
3. **Source Quality**: Prefer official sources (SEC filings, company IR pages, major financial news).
4. **Currency Clarity**: Always specify the currency (USD, EUR, etc.) for monetary values.
5. **Precision**: Use appropriate significant figures. Market cap in billions, EPS to cents.

## Calculation Best Practices
- P/E Ratio = Stock Price / Earnings Per Share
- Market Cap = Stock Price x Shares Outstanding
- Growth Rate = ((New Value - Old Value) / Old Value) x 100
- Always verify inputs before calculating

## Response Format
- Lead with the direct numerical answer
- Include the calculation methodology when relevant
- Note the data source and date
- Keep responses concise (50-60 words for simple queries)
- Use deep analysis mode for complex financial research

## Example Query Types
- "What is Apple's market cap?" → Current valuation lookup
- "Calculate Tesla's P/E ratio" → Calculation with data
- "Compare Amazon vs Google revenue growth" → Comparative analysis

Always prioritize accurate, current data and transparent calculations."""


class FinancialAnalystAgent(BaseSpecialist):
    """
    Specialist agent for financial analysis and calculations.

    Handles queries about:
    - Market capitalization and stock metrics
    - Financial ratios (P/E, debt-to-equity, etc.)
    - Revenue, earnings, and financial performance
    - Growth calculations and comparisons
    """

    def __init__(
        self,
        tool_registry: Any,
        memory_manager: Optional[Any] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        """
        Initialize the Financial Analyst Agent.

        Args:
            tool_registry: Registry for executing tools
            memory_manager: Shared memory manager (optional)
            model: Model to use (defaults to Sonnet)
            timeout_seconds: Max execution time
        """
        super().__init__(
            agent_type=AgentType.FINANCIAL_ANALYST,
            tool_registry=tool_registry,
            memory_manager=memory_manager,
            model=model,
            timeout_seconds=timeout_seconds,
        )

    @property
    def system_prompt(self) -> str:
        """Return the system prompt for financial analysis."""
        return FINANCIAL_ANALYST_SYSTEM_PROMPT

    @property
    def agent_name(self) -> str:
        """Return human-readable name for this agent."""
        return "Financial Analyst Specialist"
