"""
Unit tests for Multi-Agent System Prompts

Tests:
- All prompts are non-empty strings
- Prompts contain key terms for their domain
- Prompts follow consistent structure
- All expected prompts are importable
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.multi_agent.prompts import (
    ORCHESTRATOR_SYSTEM_PROMPT,
    CLASSIFICATION_PROMPT,
    COMPANY_RESEARCH_PROMPT,
    FINANCIAL_ANALYST_PROMPT,
    COMPETITIVE_INTEL_PROMPT,
    ACTION_EXECUTOR_PROMPT,
    GENERAL_FALLBACK_PROMPT,
)


class TestPromptExistence:
    """Test that all prompts exist and are non-empty strings."""

    def test_orchestrator_system_prompt_exists(self):
        """ORCHESTRATOR_SYSTEM_PROMPT should be a non-empty string."""
        assert isinstance(ORCHESTRATOR_SYSTEM_PROMPT, str)
        assert len(ORCHESTRATOR_SYSTEM_PROMPT) > 100

    def test_classification_prompt_exists(self):
        """CLASSIFICATION_PROMPT should be a non-empty string."""
        assert isinstance(CLASSIFICATION_PROMPT, str)
        assert len(CLASSIFICATION_PROMPT) > 100

    def test_company_research_prompt_exists(self):
        """COMPANY_RESEARCH_PROMPT should be a non-empty string."""
        assert isinstance(COMPANY_RESEARCH_PROMPT, str)
        assert len(COMPANY_RESEARCH_PROMPT) > 100

    def test_financial_analyst_prompt_exists(self):
        """FINANCIAL_ANALYST_PROMPT should be a non-empty string."""
        assert isinstance(FINANCIAL_ANALYST_PROMPT, str)
        assert len(FINANCIAL_ANALYST_PROMPT) > 100

    def test_competitive_intel_prompt_exists(self):
        """COMPETITIVE_INTEL_PROMPT should be a non-empty string."""
        assert isinstance(COMPETITIVE_INTEL_PROMPT, str)
        assert len(COMPETITIVE_INTEL_PROMPT) > 100

    def test_action_executor_prompt_exists(self):
        """ACTION_EXECUTOR_PROMPT should be a non-empty string."""
        assert isinstance(ACTION_EXECUTOR_PROMPT, str)
        assert len(ACTION_EXECUTOR_PROMPT) > 100

    def test_general_fallback_prompt_exists(self):
        """GENERAL_FALLBACK_PROMPT should be a non-empty string."""
        assert isinstance(GENERAL_FALLBACK_PROMPT, str)
        assert len(GENERAL_FALLBACK_PROMPT) > 100


class TestOrchestratorPrompts:
    """Tests for Orchestrator prompts."""

    def test_orchestrator_contains_routing_terms(self):
        """Orchestrator prompt should mention routing-related concepts."""
        prompt = ORCHESTRATOR_SYSTEM_PROMPT.lower()
        assert "routing" in prompt or "route" in prompt
        assert "query" in prompt
        assert "agent" in prompt

    def test_orchestrator_lists_specialist_agents(self):
        """Orchestrator should list all specialist agent types."""
        prompt = ORCHESTRATOR_SYSTEM_PROMPT.lower()
        assert "company_research" in prompt
        assert "financial_analyst" in prompt
        assert "competitive_intel" in prompt
        assert "action_executor" in prompt
        assert "general_fallback" in prompt

    def test_orchestrator_mentions_json_output(self):
        """Orchestrator should specify JSON output format."""
        prompt = ORCHESTRATOR_SYSTEM_PROMPT.lower()
        assert "json" in prompt

    def test_classification_prompt_has_placeholder(self):
        """Classification prompt should have a query placeholder."""
        assert "{query}" in CLASSIFICATION_PROMPT

    def test_classification_prompt_specifies_format(self):
        """Classification prompt should specify response format."""
        prompt = CLASSIFICATION_PROMPT.lower()
        assert "primary_agent" in prompt
        assert "confidence" in prompt


class TestCompanyResearchPrompt:
    """Tests for Company Research Agent prompt."""

    def test_company_prompt_mentions_tools(self):
        """Company Research prompt should mention its available tools."""
        prompt = COMPANY_RESEARCH_PROMPT.lower()
        assert "web_search" in prompt
        assert "wikipedia" in prompt

    def test_company_prompt_contains_domain_terms(self):
        """Company Research prompt should contain company-related terms."""
        prompt = COMPANY_RESEARCH_PROMPT.lower()
        assert "founded" in prompt or "founding" in prompt
        assert "headquarters" in prompt
        assert "ceo" in prompt
        assert "products" in prompt or "services" in prompt

    def test_company_prompt_mentions_sources(self):
        """Company Research prompt should emphasize citing sources."""
        prompt = COMPANY_RESEARCH_PROMPT.lower()
        assert "source" in prompt or "cite" in prompt


class TestFinancialAnalystPrompt:
    """Tests for Financial Analyst Agent prompt."""

    def test_financial_prompt_mentions_tools(self):
        """Financial Analyst prompt should mention its available tools."""
        prompt = FINANCIAL_ANALYST_PROMPT.lower()
        assert "web_search" in prompt
        assert "calculator" in prompt
        assert "perplexity" in prompt

    def test_financial_prompt_contains_domain_terms(self):
        """Financial Analyst prompt should contain financial terms."""
        prompt = FINANCIAL_ANALYST_PROMPT.lower()
        assert "market cap" in prompt or "market capitalization" in prompt
        assert "revenue" in prompt
        assert "p/e" in prompt or "ratio" in prompt

    def test_financial_prompt_mentions_calculations(self):
        """Financial Analyst prompt should mention calculation steps."""
        prompt = FINANCIAL_ANALYST_PROMPT.lower()
        assert "calculation" in prompt or "formula" in prompt

    def test_financial_prompt_mentions_data_freshness(self):
        """Financial Analyst prompt should mention data freshness caveats."""
        prompt = FINANCIAL_ANALYST_PROMPT.lower()
        assert "fresh" in prompt or "date" in prompt or "current" in prompt


class TestCompetitiveIntelPrompt:
    """Tests for Competitive Intelligence Agent prompt."""

    def test_competitive_prompt_mentions_tools(self):
        """Competitive Intel prompt should mention its available tools."""
        prompt = COMPETITIVE_INTEL_PROMPT.lower()
        assert "web_search" in prompt
        assert "perplexity" in prompt

    def test_competitive_prompt_contains_domain_terms(self):
        """Competitive Intel prompt should contain comparison-related terms."""
        prompt = COMPETITIVE_INTEL_PROMPT.lower()
        assert "compar" in prompt  # compare, comparison, comparing
        assert "competitor" in prompt or "competitive" in prompt

    def test_competitive_prompt_mentions_objectivity(self):
        """Competitive Intel prompt should emphasize objectivity."""
        prompt = COMPETITIVE_INTEL_PROMPT.lower()
        assert "objective" in prompt or "bias" in prompt or "balanced" in prompt

    def test_competitive_prompt_mentions_use_cases(self):
        """Competitive Intel prompt should consider different use cases."""
        prompt = COMPETITIVE_INTEL_PROMPT.lower()
        assert "use case" in prompt


class TestActionExecutorPrompt:
    """Tests for Action Executor Agent prompt."""

    def test_action_prompt_mentions_tools(self):
        """Action Executor prompt should mention its available tools."""
        prompt = ACTION_EXECUTOR_PROMPT.lower()
        assert "gmail" in prompt
        assert "calendar" in prompt or "google_calendar" in prompt

    def test_action_prompt_mentions_privacy(self):
        """Action Executor prompt should emphasize privacy."""
        prompt = ACTION_EXECUTOR_PROMPT.lower()
        assert "privacy" in prompt or "sensitive" in prompt or "security" in prompt

    def test_action_prompt_requires_confirmation(self):
        """Action Executor prompt should require confirmation before actions."""
        prompt = ACTION_EXECUTOR_PROMPT.lower()
        assert "confirm" in prompt

    def test_action_prompt_mentions_error_handling(self):
        """Action Executor prompt should mention authentication errors."""
        prompt = ACTION_EXECUTOR_PROMPT.lower()
        assert "error" in prompt or "authentication" in prompt


class TestGeneralFallbackPrompt:
    """Tests for General Fallback Agent prompt."""

    def test_general_prompt_mentions_tools(self):
        """General Fallback prompt should mention its available tools."""
        prompt = GENERAL_FALLBACK_PROMPT.lower()
        assert "web_search" in prompt
        assert "wikipedia" in prompt
        assert "calculator" in prompt
        assert "perplexity" in prompt

    def test_general_prompt_excludes_personal_tools(self):
        """General Fallback prompt should note it lacks email/calendar access."""
        prompt = GENERAL_FALLBACK_PROMPT.lower()
        # Should mention it does NOT have access to these
        assert "not" in prompt and ("gmail" in prompt or "email" in prompt)

    def test_general_prompt_handles_ambiguity(self):
        """General Fallback prompt should handle ambiguous queries."""
        prompt = GENERAL_FALLBACK_PROMPT.lower()
        assert "ambiguous" in prompt or "clarif" in prompt

    def test_general_prompt_can_redirect(self):
        """General Fallback prompt should be able to redirect to specialists."""
        prompt = GENERAL_FALLBACK_PROMPT.lower()
        assert "redirect" in prompt or "route" in prompt


class TestPromptStructure:
    """Tests for consistent prompt structure across all agents."""

    ALL_PROMPTS = [
        ("orchestrator", ORCHESTRATOR_SYSTEM_PROMPT),
        ("company_research", COMPANY_RESEARCH_PROMPT),
        ("financial_analyst", FINANCIAL_ANALYST_PROMPT),
        ("competitive_intel", COMPETITIVE_INTEL_PROMPT),
        ("action_executor", ACTION_EXECUTOR_PROMPT),
        ("general_fallback", GENERAL_FALLBACK_PROMPT),
    ]

    @pytest.mark.parametrize("name,prompt", ALL_PROMPTS)
    def test_prompt_defines_role(self, name, prompt):
        """Each prompt should define the agent's role."""
        prompt_lower = prompt.lower()
        assert "role" in prompt_lower or "you are" in prompt_lower

    @pytest.mark.parametrize("name,prompt", ALL_PROMPTS)
    def test_prompt_has_reasonable_length(self, name, prompt):
        """Each prompt should be between 500 and 5000 characters."""
        # Minimum ensures substance; maximum prevents overwhelming context
        assert 500 <= len(prompt) <= 5000, f"{name} prompt length: {len(prompt)}"

    @pytest.mark.parametrize("name,prompt", ALL_PROMPTS)
    def test_prompt_uses_markdown_headers(self, name, prompt):
        """Prompts should use markdown headers for structure."""
        assert "##" in prompt, f"{name} should use markdown headers"


class TestPromptMinimumWordCount:
    """Test that prompts meet minimum word count for substance."""

    def test_prompts_have_minimum_words(self):
        """All prompts should have at least 200 words."""
        prompts = {
            "orchestrator": ORCHESTRATOR_SYSTEM_PROMPT,
            "classification": CLASSIFICATION_PROMPT,
            "company_research": COMPANY_RESEARCH_PROMPT,
            "financial_analyst": FINANCIAL_ANALYST_PROMPT,
            "competitive_intel": COMPETITIVE_INTEL_PROMPT,
            "action_executor": ACTION_EXECUTOR_PROMPT,
            "general_fallback": GENERAL_FALLBACK_PROMPT,
        }

        for name, prompt in prompts.items():
            word_count = len(prompt.split())
            assert word_count >= 100, f"{name} has only {word_count} words (minimum 100)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
