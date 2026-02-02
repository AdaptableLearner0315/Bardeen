"""
Response Synthesizer for Multi-Agent System

Combines responses from multiple specialist agents into a unified response.
Supports multiple synthesis strategies:
- merge: Combine non-conflicting information
- sequential: Chain outputs where one feeds into another
- consensus: Validate agreement between agents
- ranked: Present options in priority order
"""

import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

import anthropic

from .guardrails.tool_access import AgentType
from .specialists.base_specialist import AgentResponse, AgentStatus
from .router import SynthesisStrategy


@dataclass
class SynthesizedResponse:
    """
    Final synthesized response from multiple agents.

    Attributes:
        answer: Combined/synthesized answer
        confidence: Overall confidence score
        sources: All sources from contributing agents
        agent_contributions: What each agent contributed
        synthesis_strategy: Strategy used
        latency_ms: Total processing time
    """
    answer: str
    confidence: float
    sources: List[str]
    agent_contributions: Dict[str, str]
    synthesis_strategy: SynthesisStrategy
    latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "answer": self.answer,
            "confidence": self.confidence,
            "sources": self.sources,
            "agent_contributions": self.agent_contributions,
            "synthesis_strategy": self.synthesis_strategy.value,
            "latency_ms": self.latency_ms,
        }


# Synthesis prompt for merging responses
MERGE_PROMPT = """You are a response synthesizer for a B2B intelligence system.

Combine the following agent responses into a single, coherent answer.
- Preserve all factual information
- Resolve any minor discrepancies by favoring higher-confidence sources
- Keep the response concise (under 100 words for simple queries)
- Cite sources when available

Agent responses to synthesize:
{responses}

Provide a unified answer that incorporates all relevant information."""


# Prompt for consensus validation
CONSENSUS_PROMPT = """Analyze these agent responses and determine if they agree.

Agent responses:
{responses}

Determine:
1. Do the responses agree on key facts?
2. Are there any conflicts?
3. What is the consensus answer?

Respond in JSON format:
{{
    "has_consensus": true/false,
    "answer": "the consensus or best answer",
    "confidence": 0.0-1.0,
    "conflicts": ["list any conflicts"]
}}"""


class ResponseSynthesizer:
    """
    Synthesizes responses from multiple agents.

    Uses different strategies based on the routing decision:
    - Merge: Combine complementary information
    - Sequential: Report final result with context
    - Consensus: Validate agreement between agents
    - Ranked: Present options in order
    """

    SYNTHESIS_MODEL = "claude-sonnet-4-20250514"

    def __init__(self, model: Optional[str] = None):
        """
        Initialize synthesizer.

        Args:
            model: Model to use for synthesis (defaults to Sonnet)
        """
        self.model = model or self.SYNTHESIS_MODEL
        self.client = anthropic.Anthropic()

    async def synthesize(
        self,
        responses: List[AgentResponse],
        strategy: SynthesisStrategy,
    ) -> SynthesizedResponse:
        """
        Synthesize multiple agent responses.

        Args:
            responses: List of AgentResponse from agents
            strategy: Synthesis strategy to use

        Returns:
            SynthesizedResponse with combined answer
        """
        start_time = time.time()

        # Handle edge cases
        if not responses:
            return SynthesizedResponse(
                answer="No responses available to synthesize.",
                confidence=0.0,
                sources=[],
                agent_contributions={},
                synthesis_strategy=strategy,
                latency_ms=0,
            )

        # Filter to successful responses
        successful = [r for r in responses if r.status == AgentStatus.SUCCESS]
        failed = [r for r in responses if r.status != AgentStatus.SUCCESS]

        if not successful:
            # All responses failed
            error_msgs = [r.error_message or "Unknown error" for r in failed]
            return SynthesizedResponse(
                answer=f"All agents failed. Errors: {'; '.join(error_msgs)}",
                confidence=0.0,
                sources=[],
                agent_contributions={r.agent_type.value: r.error_message or "Failed" for r in responses},
                synthesis_strategy=strategy,
                latency_ms=(time.time() - start_time) * 1000,
            )

        # Single successful response - pass through
        if len(successful) == 1:
            r = successful[0]
            return SynthesizedResponse(
                answer=r.answer,
                confidence=r.confidence,
                sources=r.sources,
                agent_contributions={r.agent_type.value: r.answer},
                synthesis_strategy=strategy,
                latency_ms=r.latency_ms,
            )

        # Apply strategy
        if strategy == SynthesisStrategy.MERGE:
            result = await self._synthesize_merge(successful)
        elif strategy == SynthesisStrategy.SEQUENTIAL:
            result = await self._synthesize_sequential(successful)
        elif strategy == SynthesisStrategy.CONSENSUS:
            result = await self._synthesize_consensus(successful)
        elif strategy == SynthesisStrategy.RANKED:
            result = await self._synthesize_ranked(successful)
        else:
            result = await self._synthesize_merge(successful)

        # Calculate total latency
        agent_latency = sum(r.latency_ms for r in responses)
        synthesis_latency = (time.time() - start_time) * 1000
        result.latency_ms = agent_latency + synthesis_latency

        # Adjust confidence if there were failures
        if failed:
            failure_penalty = len(failed) / len(responses) * 0.2
            result.confidence = max(0.0, result.confidence - failure_penalty)

        return result

    async def _synthesize_merge(
        self, responses: List[AgentResponse]
    ) -> SynthesizedResponse:
        """
        Merge non-conflicting information from multiple agents.

        Args:
            responses: Successful responses to merge

        Returns:
            Synthesized response
        """
        # Collect all sources
        all_sources = []
        for r in responses:
            all_sources.extend(r.sources)
        all_sources = list(set(all_sources))

        # Build contributions dict
        contributions = {r.agent_type.value: r.answer for r in responses}

        # Use LLM to merge
        merged_answer = await self._merge_with_llm(responses)

        # Calculate weighted confidence
        total_confidence = sum(r.confidence for r in responses)
        avg_confidence = total_confidence / len(responses)

        return SynthesizedResponse(
            answer=merged_answer,
            confidence=avg_confidence,
            sources=all_sources,
            agent_contributions=contributions,
            synthesis_strategy=SynthesisStrategy.MERGE,
        )

    async def _synthesize_sequential(
        self, responses: List[AgentResponse]
    ) -> SynthesizedResponse:
        """
        Synthesize sequential responses, emphasizing final result.

        Args:
            responses: Responses in execution order

        Returns:
            Synthesized response
        """
        all_sources = []
        contributions = {}

        for r in responses:
            all_sources.extend(r.sources)
            contributions[r.agent_type.value] = r.answer

        all_sources = list(set(all_sources))

        # Chain outputs
        chained_answer = await self._chain_outputs(responses)

        # Confidence is minimum of chain (weakest link)
        min_confidence = min(r.confidence for r in responses)

        return SynthesizedResponse(
            answer=chained_answer,
            confidence=min_confidence,
            sources=all_sources,
            agent_contributions=contributions,
            synthesis_strategy=SynthesisStrategy.SEQUENTIAL,
        )

    async def _synthesize_consensus(
        self, responses: List[AgentResponse]
    ) -> SynthesizedResponse:
        """
        Validate consensus between agents.

        Args:
            responses: Responses to check for agreement

        Returns:
            Synthesized response with consensus info
        """
        all_sources = []
        contributions = {}

        for r in responses:
            all_sources.extend(r.sources)
            contributions[r.agent_type.value] = r.answer

        all_sources = list(set(all_sources))

        # Check consensus
        consensus_result = await self._validate_consensus(responses)

        return SynthesizedResponse(
            answer=consensus_result["answer"],
            confidence=consensus_result["confidence"],
            sources=all_sources,
            agent_contributions=contributions,
            synthesis_strategy=SynthesisStrategy.CONSENSUS,
        )

    async def _synthesize_ranked(
        self, responses: List[AgentResponse]
    ) -> SynthesizedResponse:
        """
        Rank and present options from responses.

        Args:
            responses: Responses to rank

        Returns:
            Synthesized response with ranked options
        """
        all_sources = []
        contributions = {}

        for r in responses:
            all_sources.extend(r.sources)
            contributions[r.agent_type.value] = r.answer

        all_sources = list(set(all_sources))

        # Rank options
        ranked_answer = await self._rank_options(responses)

        # Average confidence
        avg_confidence = sum(r.confidence for r in responses) / len(responses)

        return SynthesizedResponse(
            answer=ranked_answer,
            confidence=avg_confidence,
            sources=all_sources,
            agent_contributions=contributions,
            synthesis_strategy=SynthesisStrategy.RANKED,
        )

    async def _merge_with_llm(self, responses: List[AgentResponse]) -> str:
        """
        Use LLM to merge responses.

        Args:
            responses: Responses to merge

        Returns:
            Merged answer string
        """
        # Format responses for LLM
        responses_text = "\n\n".join([
            f"**{r.agent_type.value}** (confidence: {r.confidence:.2f}):\n{r.answer}"
            for r in responses
        ])

        prompt = MERGE_PROMPT.format(responses=responses_text)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract text
        for block in response.content:
            if hasattr(block, "text"):
                return block.text

        return responses[0].answer  # Fallback

    async def _chain_outputs(self, responses: List[AgentResponse]) -> str:
        """
        Chain sequential outputs into narrative.

        Args:
            responses: Responses in order

        Returns:
            Chained answer
        """
        if len(responses) == 1:
            return responses[0].answer

        # Build narrative showing the chain
        parts = []
        for i, r in enumerate(responses):
            if i == len(responses) - 1:
                # Final step - emphasize result
                parts.append(f"Final result: {r.answer}")
            else:
                parts.append(f"Step {i+1} ({r.agent_type.value}): {r.answer}")

        # Use LLM to create coherent narrative
        chain_text = "\n".join(parts)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=512,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": f"Summarize this sequence of actions into a coherent response:\n\n{chain_text}"
            }],
        )

        for block in response.content:
            if hasattr(block, "text"):
                return block.text

        return responses[-1].answer  # Fallback to final result

    async def _validate_consensus(
        self, responses: List[AgentResponse]
    ) -> Dict[str, Any]:
        """
        Validate agreement between responses.

        Args:
            responses: Responses to check

        Returns:
            Dict with consensus info
        """
        # Format responses for LLM
        responses_text = "\n\n".join([
            f"**{r.agent_type.value}**: {r.answer}"
            for r in responses
        ])

        prompt = CONSENSUS_PROMPT.format(responses=responses_text)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=512,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract and parse JSON
        text = ""
        for block in response.content:
            if hasattr(block, "text"):
                text = block.text
                break

        try:
            import json
            # Handle markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            result = json.loads(text.strip())
            return {
                "has_consensus": result.get("has_consensus", False),
                "answer": result.get("answer", responses[0].answer),
                "confidence": result.get("confidence", 0.7),
            }
        except (json.JSONDecodeError, KeyError):
            # Fallback to highest confidence response
            best = max(responses, key=lambda r: r.confidence)
            return {
                "has_consensus": False,
                "answer": best.answer,
                "confidence": best.confidence * 0.8,
            }

    async def _rank_options(self, responses: List[AgentResponse]) -> str:
        """
        Rank options from responses.

        Args:
            responses: Responses to rank

        Returns:
            Ranked options as formatted string
        """
        if len(responses) == 1:
            return responses[0].answer

        # Sort by confidence
        sorted_responses = sorted(responses, key=lambda r: r.confidence, reverse=True)

        # Build ranked list
        parts = ["Comparison results:"]
        for i, r in enumerate(sorted_responses, 1):
            parts.append(f"{i}. {r.answer}")

        # Use LLM to format nicely
        ranking_text = "\n".join(parts)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=512,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": f"Format this comparison into a clear, readable format:\n\n{ranking_text}"
            }],
        )

        for block in response.content:
            if hasattr(block, "text"):
                return block.text

        return ranking_text  # Fallback
