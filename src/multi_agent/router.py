"""
Query Router for Multi-Agent System

Routes incoming queries to appropriate specialist agents based on:
- Query intent classification
- Query complexity analysis
- Pattern matching for known query types
- LLM-based classification for ambiguous queries

Supports both single-agent and multi-agent routing decisions.
"""

import re
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

import anthropic

from .guardrails.tool_access import AgentType


class SynthesisStrategy(Enum):
    """Strategy for synthesizing responses from multiple agents."""
    MERGE = "merge"           # Combine non-conflicting data
    SEQUENTIAL = "sequential"  # Chain outputs where A feeds into B
    CONSENSUS = "consensus"    # Validate agreement between agents
    RANKED = "ranked"          # Present options in priority order


class QueryComplexity(Enum):
    """Complexity level of a query."""
    SIMPLE = "simple"       # Single fact lookup
    MODERATE = "moderate"   # Multiple related facts
    COMPLEX = "complex"     # Analysis across domains


@dataclass
class RoutingDecision:
    """
    Decision about how to route a query.

    Attributes:
        mode: "single_agent" or "multi_agent"
        agents: List of AgentType to invoke
        subtasks: List of {agent, query} for decomposed queries
        synthesis_strategy: How to combine responses
        confidence: Router's confidence in the decision (0.0-1.0)
        reasoning: Explanation of routing decision
    """
    mode: str
    agents: List[AgentType]
    subtasks: List[Dict[str, Any]]
    synthesis_strategy: SynthesisStrategy
    confidence: float
    reasoning: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "mode": self.mode,
            "agents": [a.value for a in self.agents],
            "subtasks": [
                {"agent": s["agent"].value if isinstance(s["agent"], AgentType) else s["agent"],
                 "query": s["query"]}
                for s in self.subtasks
            ],
            "synthesis_strategy": self.synthesis_strategy.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }


# Classification prompt for Claude Opus
CLASSIFICATION_PROMPT = """You are a query router for a B2B Account Intelligence system.

Analyze the user's query and determine:
1. Which specialist agent(s) should handle it
2. Whether it needs single-agent or multi-agent processing
3. How to decompose complex queries into subtasks

AVAILABLE AGENTS:
- company_research: Company facts (founding date, headquarters, CEO, products, employees)
- financial_analyst: Financial data (market cap, revenue, stock price, valuations, P/E ratios)
- competitive_intel: Competitive analysis (comparisons, competitors, market position, vs queries)
- action_executor: Personal actions (email, calendar, scheduling, sending messages)
- general_fallback: General queries that don't fit other categories

ROUTING RULES:
1. "When was X founded?" -> company_research
2. "What is X's market cap/revenue/stock?" -> financial_analyst
3. "Compare X vs Y" or "X competitors" -> competitive_intel
4. "Email/calendar/schedule/meeting" -> action_executor
5. Ambiguous or off-topic -> general_fallback

MULTI-AGENT TRIGGERS:
- Query spans multiple domains (e.g., "Tell me about Stripe and its valuation")
- Query requires sequential actions (e.g., "Research X and email summary")
- Query needs validation across sources

SYNTHESIS STRATEGIES:
- merge: Combine non-conflicting info from multiple agents
- sequential: Chain outputs (first agent result feeds into second)
- consensus: Validate agreement when multiple agents answer same question
- ranked: Present options in order (for comparisons)

Respond with JSON only:
{
    "mode": "single_agent" or "multi_agent",
    "agents": ["agent_name", ...],
    "subtasks": [{"agent": "agent_name", "query": "specific query"}, ...],
    "synthesis_strategy": "merge|sequential|consensus|ranked",
    "confidence": 0.0-1.0,
    "reasoning": "explanation"
}"""


class QueryRouter:
    """
    Routes queries to appropriate specialist agents.

    Uses a combination of:
    1. Pattern matching for common query types
    2. LLM classification for complex/ambiguous queries

    The router aims for high accuracy while minimizing latency.
    """

    # Model for classification (use Sonnet for cost efficiency, Opus for accuracy)
    CLASSIFICATION_MODEL = "claude-sonnet-4-20250514"

    # Pattern matchers for quick classification
    COMPANY_PATTERNS = [
        r'\b(founded|established|started|created|when was .* founded)\b',
        r'\b(headquarters|headquartered|hq|located|based in)\b',
        r'\b(ceo|chief executive|founder|leadership|who (runs|leads|founded))\b',
        r'\b(products?|services?|what does .* (do|sell|make|offer))\b',
        r'\b(employees?|workforce|staff|team size|how many people)\b',
        r'\b(history|background|about .* company)\b',
    ]

    FINANCIAL_PATTERNS = [
        r'\b(market cap|market capitalization|valuation|worth)\b',
        r'\b(revenue|sales|earnings|income|profit)\b',
        r'\b(stock|share|price|ticker|trading)\b',
        r'\b(p/e ratio|pe ratio|price.to.earnings)\b',
        r'\b(financial|financials|fiscal|quarter|annual)\b',
        r'\b(calculate|computation|percentage|growth rate)\b',
    ]

    COMPETITIVE_PATTERNS = [
        r'\b(compare|comparison|versus|vs\.?)\b',
        r'\b(competitor|competitors|competition|rival)\b',
        r'\b(better|worse|best|worst|which is)\b',
        r'\b(market (share|position|leader))\b',
        r'\b(alternative|alternatives|instead of)\b',
        r'\b(advantage|disadvantage|pros|cons)\b',
    ]

    ACTION_PATTERNS = [
        r'\b(emails?|e-mails?|mail|inbox|unread)\b',
        r'\b(calendar|schedule|meetings?|appointments?)\b',
        r'\b(send|forward|reply|respond)\b',
        r'\b(remind|reminders?|notifications?)\b',
        r'\b(book|reserve|set up)\b',
    ]

    def __init__(self, model: Optional[str] = None):
        """
        Initialize the router.

        Args:
            model: Model to use for classification (defaults to Sonnet)
        """
        self.model = model or self.CLASSIFICATION_MODEL
        self.client = anthropic.Anthropic()

        # Compile patterns for efficiency
        self._company_regex = [re.compile(p, re.IGNORECASE) for p in self.COMPANY_PATTERNS]
        self._financial_regex = [re.compile(p, re.IGNORECASE) for p in self.FINANCIAL_PATTERNS]
        self._competitive_regex = [re.compile(p, re.IGNORECASE) for p in self.COMPETITIVE_PATTERNS]
        self._action_regex = [re.compile(p, re.IGNORECASE) for p in self.ACTION_PATTERNS]

    async def route(self, query: str) -> RoutingDecision:
        """
        Route a query to appropriate agent(s).

        Args:
            query: User's query string

        Returns:
            RoutingDecision with agents and synthesis strategy
        """
        # Handle empty query
        if not query or not query.strip():
            return RoutingDecision(
                mode="single_agent",
                agents=[AgentType.GENERAL_FALLBACK],
                subtasks=[{"agent": AgentType.GENERAL_FALLBACK, "query": query}],
                synthesis_strategy=SynthesisStrategy.MERGE,
                confidence=1.0,
                reasoning="Empty query routed to fallback agent.",
            )

        # Try LLM classification first
        try:
            llm_result = await self._classify_with_llm(query)
            if llm_result and self._validate_llm_result(llm_result):
                return self._build_decision_from_llm(llm_result, query)
        except Exception as e:
            # Fall back to pattern matching
            pass

        # Pattern-based fallback
        return self._classify_with_patterns(query)

    async def _classify_with_llm(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Use LLM to classify the query.

        Args:
            query: User's query

        Returns:
            Classification result dict or None
        """
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=0.3,  # Lower temperature for more consistent classification
            system=CLASSIFICATION_PROMPT,
            messages=[
                {"role": "user", "content": f"Classify this query: {query}"}
            ],
        )

        # Extract text and parse JSON
        text = ""
        for block in response.content:
            if hasattr(block, "text"):
                text = block.text
                break

        # Try to parse JSON from response
        try:
            # Handle markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            return json.loads(text.strip())
        except json.JSONDecodeError:
            return None

    def _validate_llm_result(self, result: Dict[str, Any]) -> bool:
        """Validate that LLM result has required fields."""
        required = ["mode", "agents", "subtasks", "synthesis_strategy"]
        return all(key in result for key in required)

    def _build_decision_from_llm(
        self, result: Dict[str, Any], original_query: str
    ) -> RoutingDecision:
        """Build RoutingDecision from LLM result."""
        # Map agent strings to AgentType
        agent_map = {
            "company_research": AgentType.COMPANY_RESEARCH,
            "financial_analyst": AgentType.FINANCIAL_ANALYST,
            "competitive_intel": AgentType.COMPETITIVE_INTEL,
            "action_executor": AgentType.ACTION_EXECUTOR,
            "general_fallback": AgentType.GENERAL_FALLBACK,
        }

        agents = [
            agent_map.get(a, AgentType.GENERAL_FALLBACK)
            for a in result.get("agents", ["general_fallback"])
        ]

        # Build subtasks with proper AgentType
        subtasks = []
        for st in result.get("subtasks", []):
            agent_str = st.get("agent", "general_fallback")
            subtasks.append({
                "agent": agent_map.get(agent_str, AgentType.GENERAL_FALLBACK),
                "query": st.get("query", original_query),
            })

        # Map synthesis strategy
        strategy_map = {
            "merge": SynthesisStrategy.MERGE,
            "sequential": SynthesisStrategy.SEQUENTIAL,
            "consensus": SynthesisStrategy.CONSENSUS,
            "ranked": SynthesisStrategy.RANKED,
        }
        strategy = strategy_map.get(
            result.get("synthesis_strategy", "merge"),
            SynthesisStrategy.MERGE
        )

        return RoutingDecision(
            mode=result.get("mode", "single_agent"),
            agents=agents,
            subtasks=subtasks,
            synthesis_strategy=strategy,
            confidence=result.get("confidence", 0.8),
            reasoning=result.get("reasoning", "LLM classification"),
        )

    def _classify_with_patterns(self, query: str) -> RoutingDecision:
        """
        Classify query using pattern matching.

        Args:
            query: User's query

        Returns:
            RoutingDecision based on pattern matches
        """
        scores = {
            AgentType.COMPANY_RESEARCH: self._score_patterns(query, self._company_regex),
            AgentType.FINANCIAL_ANALYST: self._score_patterns(query, self._financial_regex),
            AgentType.COMPETITIVE_INTEL: self._score_patterns(query, self._competitive_regex),
            AgentType.ACTION_EXECUTOR: self._score_patterns(query, self._action_regex),
        }

        # Find agents with matches
        matched = [(agent, score) for agent, score in scores.items() if score > 0]

        if not matched:
            # No patterns matched - use fallback
            return RoutingDecision(
                mode="single_agent",
                agents=[AgentType.GENERAL_FALLBACK],
                subtasks=[{"agent": AgentType.GENERAL_FALLBACK, "query": query}],
                synthesis_strategy=SynthesisStrategy.MERGE,
                confidence=0.5,
                reasoning="No patterns matched, using general fallback.",
            )

        # Sort by score
        matched.sort(key=lambda x: x[1], reverse=True)

        if len(matched) == 1:
            agent, score = matched[0]
            return RoutingDecision(
                mode="single_agent",
                agents=[agent],
                subtasks=[{"agent": agent, "query": query}],
                synthesis_strategy=self._select_synthesis_strategy([agent], query),
                confidence=min(0.9, 0.5 + score * 0.1),
                reasoning=f"Pattern match: {agent.value}",
            )
        else:
            # Multiple matches - multi-agent
            agents = [m[0] for m in matched[:3]]  # Max 3 agents
            return RoutingDecision(
                mode="multi_agent",
                agents=agents,
                subtasks=[{"agent": a, "query": query} for a in agents],
                synthesis_strategy=self._select_synthesis_strategy(agents, query),
                confidence=min(0.85, 0.5 + sum(m[1] for m in matched) * 0.05),
                reasoning=f"Multiple pattern matches: {[a.value for a in agents]}",
            )

    def _score_patterns(self, query: str, patterns: List[re.Pattern]) -> int:
        """Count pattern matches for a query."""
        return sum(1 for p in patterns if p.search(query))

    def _is_company_research_query(self, query: str) -> bool:
        """Check if query is about company research."""
        return self._score_patterns(query, self._company_regex) > 0

    def _is_financial_query(self, query: str) -> bool:
        """Check if query is about financial data."""
        return self._score_patterns(query, self._financial_regex) > 0

    def _is_competitive_query(self, query: str) -> bool:
        """Check if query is about competitive intelligence."""
        return self._score_patterns(query, self._competitive_regex) > 0

    def _is_action_query(self, query: str) -> bool:
        """Check if query is about actions."""
        return self._score_patterns(query, self._action_regex) > 0

    def _select_synthesis_strategy(
        self, agents: List[AgentType], query: str
    ) -> SynthesisStrategy:
        """
        Select appropriate synthesis strategy based on agents and query.

        Args:
            agents: List of agents involved
            query: Original query

        Returns:
            Appropriate SynthesisStrategy
        """
        query_lower = query.lower()

        # Sequential for action + research combinations
        if AgentType.ACTION_EXECUTOR in agents and len(agents) > 1:
            return SynthesisStrategy.SEQUENTIAL

        # Ranked for comparison queries
        if any(word in query_lower for word in ["compare", "vs", "versus", "better", "which"]):
            return SynthesisStrategy.RANKED

        # Consensus when multiple agents answer same question
        if len(agents) > 1 and AgentType.COMPETITIVE_INTEL not in agents:
            if AgentType.COMPANY_RESEARCH in agents and AgentType.GENERAL_FALLBACK in agents:
                return SynthesisStrategy.CONSENSUS

        # Default to merge
        return SynthesisStrategy.MERGE
