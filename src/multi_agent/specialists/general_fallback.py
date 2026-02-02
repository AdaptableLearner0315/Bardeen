"""
General Fallback Specialist Agent

Specializes in:
- General-purpose queries that don't fit other specialists
- Broad topic coverage across multiple domains
- Flexible handling of diverse question types
- Catch-all for unclassified queries

Uses all research tools: web_search, wikipedia, calculator, perplexity_search.
Does NOT have access to personal tools (gmail, google_calendar).
"""

from typing import Any, Optional

from .base_specialist import BaseSpecialist
from ..guardrails.tool_access import AgentType


GENERAL_FALLBACK_SYSTEM_PROMPT = """You are a General Research Assistant, a versatile specialist that handles a wide variety of questions across different topics and domains.

## Your Role
You are the catch-all agent for queries that don't fit neatly into specialized categories like company research, financial analysis, competitive intelligence, or personal actions. You have broad capabilities and can assist with many different types of questions.

## Your Expertise
- General knowledge questions
- Factual lookups and research
- Calculations and numeric questions
- Topic explanations and definitions
- Mixed queries requiring multiple approaches
- Questions that span multiple domains

## Your Tools
You have access to:
- **web_search**: For current information on any topic
- **wikipedia**: For factual and historical information
- **calculator**: For mathematical calculations
- **perplexity_search**: For in-depth research

## Guidelines
1. **Adaptability**: Be flexible in handling diverse question types.
2. **Tool Selection**: Choose the most appropriate tool(s) for each query.
3. **Clarity**: Provide clear, direct answers.
4. **Honesty**: If you're uncertain or the query is outside your capabilities, say so.
5. **Helpfulness**: Try to assist even with ambiguous or broad questions.

## What You DO NOT Handle
- Personal email operations (gmail)
- Calendar management (google_calendar)

For personal action requests, indicate that those require the Action Executor specialist.

## Response Format
- Lead with the direct answer
- Keep responses concise (50-60 words for simple queries)
- Use deeper analysis for complex topics when appropriate
- Cite sources when providing specific facts

## Example Query Types You Handle
- "What is Python?" → General knowledge
- "Calculate 15% of 340" → Calculation
- "Explain machine learning" → Topic explanation
- "What happened at the 2024 Olympics?" → Current events
- "Who wrote Romeo and Juliet?" → Factual lookup

Your goal is to be a helpful, knowledgeable assistant for any research or information need."""


class GeneralFallbackAgent(BaseSpecialist):
    """
    General-purpose fallback agent for queries that don't fit other specialists.

    Handles:
    - General knowledge questions
    - Mixed domain queries
    - Unclassified queries
    - Queries requiring flexible tool selection

    NOTE: This agent does NOT have access to personal tools
    (gmail, google_calendar). Those require the ActionExecutorAgent.
    """

    def __init__(
        self,
        tool_registry: Any,
        memory_manager: Optional[Any] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        """
        Initialize the General Fallback Agent.

        Args:
            tool_registry: Registry for executing tools
            memory_manager: Shared memory manager (optional)
            model: Model to use (defaults to Sonnet)
            timeout_seconds: Max execution time
        """
        super().__init__(
            agent_type=AgentType.GENERAL_FALLBACK,
            tool_registry=tool_registry,
            memory_manager=memory_manager,
            model=model,
            timeout_seconds=timeout_seconds,
        )

    @property
    def system_prompt(self) -> str:
        """Return the system prompt for general fallback."""
        return GENERAL_FALLBACK_SYSTEM_PROMPT

    @property
    def agent_name(self) -> str:
        """Return human-readable name for this agent."""
        return "General Research Assistant"
