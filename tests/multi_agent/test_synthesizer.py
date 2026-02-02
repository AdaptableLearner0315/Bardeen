"""
Unit tests for ResponseSynthesizer

Tests:
- Merge strategy combining non-conflicting data
- Sequential strategy chaining outputs
- Consensus strategy validating agreement
- Ranked strategy presenting options
- Conflict resolution
- Error handling
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.multi_agent.guardrails.tool_access import AgentType
from src.multi_agent.specialists.base_specialist import AgentResponse, AgentStatus
from src.multi_agent.router import SynthesisStrategy
from src.multi_agent.synthesizer import ResponseSynthesizer, SynthesizedResponse


class TestSynthesizedResponse:
    """Tests for SynthesizedResponse dataclass."""

    def test_synthesized_response_creation(self):
        """Should create synthesized response correctly."""
        response = SynthesizedResponse(
            answer="Combined answer from multiple agents",
            confidence=0.85,
            sources=["https://example.com", "https://other.com"],
            agent_contributions={
                "company_research": "Stripe was founded in 2010",
                "financial_analyst": "Stripe is valued at $50B",
            },
            synthesis_strategy=SynthesisStrategy.MERGE,
            latency_ms=500,
        )
        assert "Combined answer" in response.answer
        assert response.confidence == 0.85
        assert len(response.sources) == 2
        assert len(response.agent_contributions) == 2

    def test_synthesized_response_to_dict(self):
        """Should serialize to dict correctly."""
        response = SynthesizedResponse(
            answer="Test answer",
            confidence=0.9,
            sources=["source1"],
            agent_contributions={"agent1": "contribution1"},
            synthesis_strategy=SynthesisStrategy.MERGE,
            latency_ms=100,
        )
        d = response.to_dict()
        assert d["answer"] == "Test answer"
        assert d["confidence"] == 0.9
        assert d["synthesis_strategy"] == "merge"


class TestMergeStrategy:
    """Tests for merge synthesis strategy."""

    @pytest.fixture
    def synthesizer(self):
        """Create synthesizer with mocked LLM."""
        with patch('anthropic.Anthropic'):
            return ResponseSynthesizer()

    @pytest.mark.asyncio
    async def test_merge_non_conflicting_responses(self, synthesizer):
        """Should merge non-conflicting information."""
        responses = [
            AgentResponse(
                agent_type=AgentType.COMPANY_RESEARCH,
                query="Tell me about Stripe",
                answer="Stripe was founded in 2010 by Patrick and John Collison.",
                status=AgentStatus.SUCCESS,
                confidence=0.95,
                latency_ms=200,
            ),
            AgentResponse(
                agent_type=AgentType.FINANCIAL_ANALYST,
                query="Stripe valuation",
                answer="Stripe is valued at approximately $50 billion.",
                status=AgentStatus.SUCCESS,
                confidence=0.90,
                latency_ms=300,
            ),
        ]

        with patch.object(synthesizer, '_merge_with_llm', new_callable=AsyncMock) as mock_merge:
            mock_merge.return_value = (
                "Stripe was founded in 2010 by Patrick and John Collison. "
                "The company is currently valued at approximately $50 billion."
            )
            result = await synthesizer.synthesize(responses, SynthesisStrategy.MERGE)

        assert result is not None
        assert result.synthesis_strategy == SynthesisStrategy.MERGE

    @pytest.mark.asyncio
    async def test_merge_preserves_all_sources(self, synthesizer):
        """Merge should preserve sources from all agents."""
        responses = [
            AgentResponse(
                agent_type=AgentType.COMPANY_RESEARCH,
                query="Test",
                answer="Answer 1",
                status=AgentStatus.SUCCESS,
                sources=["source1.com"],
                confidence=0.9,
                latency_ms=100,
            ),
            AgentResponse(
                agent_type=AgentType.FINANCIAL_ANALYST,
                query="Test",
                answer="Answer 2",
                status=AgentStatus.SUCCESS,
                sources=["source2.com", "source3.com"],
                confidence=0.85,
                latency_ms=150,
            ),
        ]

        with patch.object(synthesizer, '_merge_with_llm', new_callable=AsyncMock) as mock_merge:
            mock_merge.return_value = "Merged answer"
            result = await synthesizer.synthesize(responses, SynthesisStrategy.MERGE)

        assert len(result.sources) == 3

    @pytest.mark.asyncio
    async def test_merge_calculates_weighted_confidence(self, synthesizer):
        """Merge should calculate weighted average confidence."""
        responses = [
            AgentResponse(
                agent_type=AgentType.COMPANY_RESEARCH,
                query="Test",
                answer="Answer 1",
                status=AgentStatus.SUCCESS,
                confidence=0.8,
                latency_ms=100,
            ),
            AgentResponse(
                agent_type=AgentType.FINANCIAL_ANALYST,
                query="Test",
                answer="Answer 2",
                status=AgentStatus.SUCCESS,
                confidence=1.0,
                latency_ms=100,
            ),
        ]

        with patch.object(synthesizer, '_merge_with_llm', new_callable=AsyncMock) as mock_merge:
            mock_merge.return_value = "Merged answer"
            result = await synthesizer.synthesize(responses, SynthesisStrategy.MERGE)

        # Average of 0.8 and 1.0 = 0.9
        assert result.confidence == pytest.approx(0.9, abs=0.01)


class TestSequentialStrategy:
    """Tests for sequential synthesis strategy."""

    @pytest.fixture
    def synthesizer(self):
        """Create synthesizer with mocked LLM."""
        with patch('anthropic.Anthropic'):
            return ResponseSynthesizer()

    @pytest.mark.asyncio
    async def test_sequential_chains_outputs(self, synthesizer):
        """Sequential should chain outputs in order."""
        responses = [
            AgentResponse(
                agent_type=AgentType.COMPANY_RESEARCH,
                query="Research Stripe",
                answer="Stripe is a payments company founded in 2010.",
                status=AgentStatus.SUCCESS,
                confidence=0.95,
                latency_ms=200,
            ),
            AgentResponse(
                agent_type=AgentType.ACTION_EXECUTOR,
                query="Email summary",
                answer="Email sent successfully to team@example.com",
                status=AgentStatus.SUCCESS,
                confidence=0.90,
                latency_ms=100,
            ),
        ]

        with patch.object(synthesizer, '_chain_outputs', new_callable=AsyncMock) as mock_chain:
            mock_chain.return_value = (
                "I researched Stripe (a payments company founded in 2010) "
                "and sent a summary to team@example.com."
            )
            result = await synthesizer.synthesize(responses, SynthesisStrategy.SEQUENTIAL)

        assert result is not None
        assert result.synthesis_strategy == SynthesisStrategy.SEQUENTIAL

    @pytest.mark.asyncio
    async def test_sequential_reports_final_action(self, synthesizer):
        """Sequential should emphasize the final action result."""
        responses = [
            AgentResponse(
                agent_type=AgentType.COMPANY_RESEARCH,
                query="Research",
                answer="Company info gathered",
                status=AgentStatus.SUCCESS,
                confidence=0.95,
                latency_ms=200,
            ),
            AgentResponse(
                agent_type=AgentType.ACTION_EXECUTOR,
                query="Send email",
                answer="Email sent",
                status=AgentStatus.SUCCESS,
                confidence=0.90,
                latency_ms=100,
            ),
        ]

        with patch.object(synthesizer, '_chain_outputs', new_callable=AsyncMock) as mock_chain:
            mock_chain.return_value = "Final result"
            result = await synthesizer.synthesize(responses, SynthesisStrategy.SEQUENTIAL)

        # Should track contributions from both
        assert len(result.agent_contributions) == 2


class TestConsensusStrategy:
    """Tests for consensus synthesis strategy."""

    @pytest.fixture
    def synthesizer(self):
        """Create synthesizer with mocked LLM."""
        with patch('anthropic.Anthropic'):
            return ResponseSynthesizer()

    @pytest.mark.asyncio
    async def test_consensus_with_agreement(self, synthesizer):
        """Consensus should validate when agents agree."""
        responses = [
            AgentResponse(
                agent_type=AgentType.COMPANY_RESEARCH,
                query="When was Stripe founded?",
                answer="Stripe was founded in 2010.",
                status=AgentStatus.SUCCESS,
                confidence=0.95,
                latency_ms=200,
            ),
            AgentResponse(
                agent_type=AgentType.GENERAL_FALLBACK,
                query="When was Stripe founded?",
                answer="Stripe was founded in 2010 by the Collison brothers.",
                status=AgentStatus.SUCCESS,
                confidence=0.90,
                latency_ms=250,
            ),
        ]

        with patch.object(synthesizer, '_validate_consensus', new_callable=AsyncMock) as mock_consensus:
            mock_consensus.return_value = {
                "has_consensus": True,
                "answer": "Stripe was founded in 2010.",
                "confidence": 0.95,
            }
            result = await synthesizer.synthesize(responses, SynthesisStrategy.CONSENSUS)

        assert result.confidence >= 0.9  # High confidence due to agreement

    @pytest.mark.asyncio
    async def test_consensus_with_disagreement(self, synthesizer):
        """Consensus should flag disagreement."""
        responses = [
            AgentResponse(
                agent_type=AgentType.COMPANY_RESEARCH,
                query="Company value?",
                answer="Valued at $50 billion",
                status=AgentStatus.SUCCESS,
                confidence=0.90,
                latency_ms=200,
            ),
            AgentResponse(
                agent_type=AgentType.FINANCIAL_ANALYST,
                query="Company value?",
                answer="Valued at $65 billion",
                status=AgentStatus.SUCCESS,
                confidence=0.85,
                latency_ms=250,
            ),
        ]

        with patch.object(synthesizer, '_validate_consensus', new_callable=AsyncMock) as mock_consensus:
            mock_consensus.return_value = {
                "has_consensus": False,
                "answer": "Valuation estimates vary: $50B to $65B.",
                "confidence": 0.70,
            }
            result = await synthesizer.synthesize(responses, SynthesisStrategy.CONSENSUS)

        # Lower confidence when there's disagreement
        assert result.confidence < 0.85


class TestRankedStrategy:
    """Tests for ranked synthesis strategy."""

    @pytest.fixture
    def synthesizer(self):
        """Create synthesizer with mocked LLM."""
        with patch('anthropic.Anthropic'):
            return ResponseSynthesizer()

    @pytest.mark.asyncio
    async def test_ranked_presents_options(self, synthesizer):
        """Ranked should present options in priority order."""
        responses = [
            AgentResponse(
                agent_type=AgentType.COMPETITIVE_INTEL,
                query="Compare AWS vs Azure",
                answer="AWS leads in market share, Azure in enterprise integration.",
                status=AgentStatus.SUCCESS,
                confidence=0.90,
                latency_ms=300,
            ),
        ]

        with patch.object(synthesizer, '_rank_options', new_callable=AsyncMock) as mock_rank:
            mock_rank.return_value = (
                "Comparison of AWS vs Azure:\n"
                "1. Market Share: AWS leads\n"
                "2. Enterprise: Azure has better Microsoft integration"
            )
            result = await synthesizer.synthesize(responses, SynthesisStrategy.RANKED)

        assert result is not None
        assert result.synthesis_strategy == SynthesisStrategy.RANKED

    @pytest.mark.asyncio
    async def test_ranked_for_comparison_queries(self, synthesizer):
        """Ranked strategy should be used for comparison queries."""
        responses = [
            AgentResponse(
                agent_type=AgentType.COMPETITIVE_INTEL,
                query="Which is better: Stripe or Square?",
                answer="Stripe is better for developers, Square for retail.",
                status=AgentStatus.SUCCESS,
                confidence=0.85,
                latency_ms=400,
            ),
        ]

        with patch.object(synthesizer, '_rank_options', new_callable=AsyncMock) as mock_rank:
            mock_rank.return_value = "Ranked comparison result"
            result = await synthesizer.synthesize(responses, SynthesisStrategy.RANKED)

        assert result is not None


class TestSynthesizerErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def synthesizer(self):
        """Create synthesizer with mocked LLM."""
        with patch('anthropic.Anthropic'):
            return ResponseSynthesizer()

    @pytest.mark.asyncio
    async def test_handles_failed_responses(self, synthesizer):
        """Should handle responses with failures."""
        responses = [
            AgentResponse(
                agent_type=AgentType.COMPANY_RESEARCH,
                query="Test",
                answer="Good answer",
                status=AgentStatus.SUCCESS,
                confidence=0.9,
                latency_ms=100,
            ),
            AgentResponse(
                agent_type=AgentType.FINANCIAL_ANALYST,
                query="Test",
                answer="Failed to get data",
                status=AgentStatus.FAILED,
                confidence=0.0,
                error_message="API error",
                latency_ms=50,
            ),
        ]

        with patch.object(synthesizer, '_merge_with_llm', new_callable=AsyncMock) as mock_merge:
            mock_merge.return_value = "Good answer (financial data unavailable)"
            result = await synthesizer.synthesize(responses, SynthesisStrategy.MERGE)

        # Should still produce result from successful agent
        assert result is not None
        # Confidence should be reduced due to failure (or at most same as successful response)
        assert result.confidence <= 0.9

    @pytest.mark.asyncio
    async def test_handles_all_failed_responses(self, synthesizer):
        """Should handle case where all responses failed."""
        responses = [
            AgentResponse(
                agent_type=AgentType.COMPANY_RESEARCH,
                query="Test",
                answer="Error",
                status=AgentStatus.FAILED,
                confidence=0.0,
                error_message="API error",
                latency_ms=50,
            ),
        ]

        result = await synthesizer.synthesize(responses, SynthesisStrategy.MERGE)

        assert result is not None
        assert result.confidence == 0.0
        assert "error" in result.answer.lower() or "failed" in result.answer.lower()

    @pytest.mark.asyncio
    async def test_handles_empty_responses(self, synthesizer):
        """Should handle empty response list."""
        result = await synthesizer.synthesize([], SynthesisStrategy.MERGE)

        assert result is not None
        assert "no responses" in result.answer.lower() or result.answer == ""

    @pytest.mark.asyncio
    async def test_handles_single_response(self, synthesizer):
        """Single response should pass through without synthesis."""
        responses = [
            AgentResponse(
                agent_type=AgentType.COMPANY_RESEARCH,
                query="When was Stripe founded?",
                answer="Stripe was founded in 2010.",
                status=AgentStatus.SUCCESS,
                confidence=0.95,
                sources=["wikipedia"],
                latency_ms=200,
            ),
        ]

        result = await synthesizer.synthesize(responses, SynthesisStrategy.MERGE)

        # Single response should be returned as-is
        assert result.answer == "Stripe was founded in 2010."
        assert result.confidence == 0.95


class TestSynthesizerLatency:
    """Tests for latency tracking."""

    @pytest.fixture
    def synthesizer(self):
        """Create synthesizer with mocked LLM."""
        with patch('anthropic.Anthropic'):
            return ResponseSynthesizer()

    @pytest.mark.asyncio
    async def test_calculates_total_latency(self, synthesizer):
        """Should calculate total latency from all responses."""
        responses = [
            AgentResponse(
                agent_type=AgentType.COMPANY_RESEARCH,
                query="Test",
                answer="Answer 1",
                status=AgentStatus.SUCCESS,
                confidence=0.9,
                latency_ms=200,
            ),
            AgentResponse(
                agent_type=AgentType.FINANCIAL_ANALYST,
                query="Test",
                answer="Answer 2",
                status=AgentStatus.SUCCESS,
                confidence=0.85,
                latency_ms=300,
            ),
        ]

        with patch.object(synthesizer, '_merge_with_llm', new_callable=AsyncMock) as mock_merge:
            mock_merge.return_value = "Merged answer"
            result = await synthesizer.synthesize(responses, SynthesisStrategy.MERGE)

        # Latency should be sum of individual latencies plus synthesis time
        assert result.latency_ms >= 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
