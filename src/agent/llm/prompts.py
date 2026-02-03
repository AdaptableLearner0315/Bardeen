"""System prompts and prompt templates for LLM interactions.

This module manages all system prompts used for different interaction modes.
Separated from llm_client.py for better organization and maintainability.
"""

from typing import Dict, List
from src.shared.config import RESPONSE_LIMITS


class PromptManager:
    """Manages system prompts for different interaction modes.

    Provides centralized prompt management with mode-specific templates.
    """

    SYSTEM_PROMPT_NORMAL = """You are a helpful research assistant. Keep responses concise and casual.

CRITICAL RESPONSE GUIDELINES:
- Keep responses to {min_words}-{max_words} words MAXIMUM
- Be direct and conversational
- Lead with the answer, skip formalities
- One paragraph, no bullets unless asked
- Like texting a smart friend

Examples:
- Good: "Apple's market cap is around $3 trillion."
- Bad: "That's a great question! Let me help you..." (too formal)
"""

    SYSTEM_PROMPT_DEEP = """You are a research assistant providing comprehensive analysis.

Format your response as:

**SUMMARY** (under {summary_words} words):
[Direct answer to the question]

**DETAILED ANALYSIS**:
[In-depth explanation with sources]

Guidelines:
- Summary first, details below
- Include citations where applicable
- Organize details with clear sections
"""

    @staticmethod
    def get_prompt(mode: str) -> str:
        """Get system prompt for specified mode.

        Args:
            mode: "normal" or "deep"

        Returns:
            System prompt string
        """
        if mode == "deep":
            return PromptManager.SYSTEM_PROMPT_DEEP.format(
                summary_words=RESPONSE_LIMITS["deep_mode_summary_words"]
            )
        else:
            return PromptManager.SYSTEM_PROMPT_NORMAL.format(
                min_words=RESPONSE_LIMITS["normal_mode_words_min"],
                max_words=RESPONSE_LIMITS["normal_mode_words_max"]
            )

    @staticmethod
    def build_conversation_context(messages: List[Dict]) -> List[Dict]:
        """Build conversation context with proper formatting.

        Args:
            messages: List of message dicts

        Returns:
            Formatted message list
        """
        return messages
