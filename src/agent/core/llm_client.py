"""Claude LLM client with tool calling support."""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Generator
from dataclasses import dataclass, field

from src.shared.config import get_config, ResearchMode
from src.shared.exceptions import (
    LLMAPIError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMInvalidResponseError,
    LLMContextOverflowError,
    MissingAPIKeyError,
)
from src.shared.utils import retry_with_backoff

logger = logging.getLogger(__name__)

# Try to import Anthropic
try:
    from anthropic import Anthropic, APIError, RateLimitError, APITimeoutError
    ANTHROPIC_AVAILABLE = True
except ImportError:
    Anthropic = None
    APIError = Exception
    RateLimitError = Exception
    APITimeoutError = Exception
    ANTHROPIC_AVAILABLE = False


@dataclass
class ToolUse:
    """Represents a tool use request from the LLM."""
    id: str
    name: str
    input: Dict[str, Any]


@dataclass
class LLMResponse:
    """Response from the LLM."""
    text: str
    tool_uses: List[ToolUse] = field(default_factory=list)
    stop_reason: str = "end_turn"
    usage: Dict[str, int] = field(default_factory=dict)
    raw_response: Optional[Any] = None

    @property
    def has_tool_calls(self) -> bool:
        """Check if response contains tool calls."""
        return len(self.tool_uses) > 0


class LLMClient:
    """
    Claude LLM client with tool calling capabilities.

    Features:
    - Claude Sonnet 4.5 integration
    - Tool calling with parallel execution support
    - Automatic retry with exponential backoff
    - Token limit management
    - Streaming support (optional)
    """

    # Default model as per PRD
    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    DEFAULT_TEMPERATURE = 0.6
    DEFAULT_MAX_TOKENS = 4096
    DEFAULT_TIMEOUT = 60

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
    ):
        """
        Initialize LLM client.

        Args:
            api_key: Anthropic API key (uses config/env if not provided)
            model: Model ID (default: claude-sonnet-4-20250514)
            temperature: Temperature for responses (default: 0.6)
            max_tokens: Max tokens in response (default: 4096)
            timeout: Request timeout in seconds (default: 60)
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package is required. Install with: pip install anthropic"
            )

        config = get_config()

        # Get API key
        self.api_key = api_key or config.anthropic_api_key
        if not self.api_key:
            raise MissingAPIKeyError("ANTHROPIC_API_KEY")

        # Set parameters
        self.model = model or config.llm.model or self.DEFAULT_MODEL
        self.temperature = temperature if temperature is not None else config.llm.temperature
        self.max_tokens = max_tokens or config.llm.max_tokens or self.DEFAULT_MAX_TOKENS
        self.timeout = timeout or config.llm.timeout_seconds or self.DEFAULT_TIMEOUT

        # Initialize client
        self._client = Anthropic(api_key=self.api_key)

        # Statistics
        self._total_requests = 0
        self._total_tokens_in = 0
        self._total_tokens_out = 0
        self._errors = 0

        logger.info(f"LLM Client initialized with model: {self.model}")

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Send a chat request to Claude.

        Args:
            messages: List of conversation messages
            tools: Optional list of tool definitions
            system: Optional system prompt
            temperature: Override temperature for this request
            max_tokens: Override max tokens for this request

        Returns:
            LLMResponse with text and any tool calls
        """
        self._total_requests += 1

        # Build request parameters
        params = {
            "model": self.model,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature if temperature is not None else self.temperature,
            "messages": messages,
        }

        if system:
            params["system"] = system

        if tools:
            params["tools"] = tools

        try:
            response = self._make_request(params)
            return self._parse_response(response)

        except RateLimitError as e:
            self._errors += 1
            logger.warning(f"Rate limit exceeded: {e}")
            raise LLMRateLimitError(retry_after_seconds=60)

        except APITimeoutError as e:
            self._errors += 1
            logger.warning(f"API timeout: {e}")
            raise LLMTimeoutError(timeout_seconds=self.timeout)

        except APIError as e:
            self._errors += 1
            logger.error(f"API error: {e}")
            raise LLMAPIError(str(e), status_code=getattr(e, "status_code", None))

        except Exception as e:
            self._errors += 1
            logger.error(f"Unexpected error: {e}")
            raise LLMAPIError(f"Unexpected error: {str(e)}")

    def _make_request(self, params: Dict[str, Any]) -> Any:
        """Make API request with retry logic."""

        def do_request():
            return self._client.messages.create(**params)

        # Retry with backoff for transient errors
        try:
            return retry_with_backoff(
                do_request,
                max_retries=3,
                base_delay=1.0,
                max_delay=30.0,
                exceptions=(RateLimitError,)
            )
        except Exception:
            # Final attempt without retry wrapper
            return do_request()

    def _parse_response(self, response) -> LLMResponse:
        """Parse Claude API response into LLMResponse."""
        text_parts = []
        tool_uses = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_uses.append(ToolUse(
                    id=block.id,
                    name=block.name,
                    input=block.input
                ))

        # Track token usage
        if hasattr(response, "usage"):
            self._total_tokens_in += response.usage.input_tokens
            self._total_tokens_out += response.usage.output_tokens

        return LLMResponse(
            text="\n".join(text_parts),
            tool_uses=tool_uses,
            stop_reason=response.stop_reason,
            usage={
                "input_tokens": response.usage.input_tokens if hasattr(response, "usage") else 0,
                "output_tokens": response.usage.output_tokens if hasattr(response, "usage") else 0,
            },
            raw_response=response
        )

    def chat_with_tools(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_executor: Optional[callable] = None,
        system: Optional[str] = None,
        max_tool_calls: int = 10,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Chat with automatic tool execution loop.

        Args:
            user_message: User's message
            conversation_history: Previous messages
            tools: Tool definitions
            tool_executor: Function to execute tools (name, input) -> result
            system: System prompt
            max_tool_calls: Maximum tool calls before stopping

        Returns:
            Tuple of (final_answer, tool_call_records)
        """
        messages = list(conversation_history or [])
        messages.append({"role": "user", "content": user_message})

        tool_records = []
        tool_call_count = 0

        while tool_call_count < max_tool_calls:
            response = self.chat(messages, tools=tools, system=system)

            if response.stop_reason == "end_turn" or not response.has_tool_calls:
                # Done - return final answer
                return response.text, tool_records

            if response.stop_reason == "tool_use":
                tool_call_count += len(response.tool_uses)

                # Add assistant's response
                assistant_content = []
                if response.text:
                    assistant_content.append({"type": "text", "text": response.text})

                for tool_use in response.tool_uses:
                    assistant_content.append({
                        "type": "tool_use",
                        "id": tool_use.id,
                        "name": tool_use.name,
                        "input": tool_use.input
                    })

                messages.append({"role": "assistant", "content": assistant_content})

                # Execute tools
                tool_results = []
                for tool_use in response.tool_uses:
                    if tool_executor:
                        result = tool_executor(tool_use.name, tool_use.input)
                    else:
                        result = {"error": "No tool executor provided"}

                    tool_records.append({
                        "id": tool_use.id,
                        "name": tool_use.name,
                        "input": tool_use.input,
                        "result": result
                    })

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": str(result) if isinstance(result, dict) else result
                    })

                messages.append({"role": "user", "content": tool_results})
                continue

            elif response.stop_reason == "max_tokens":
                return response.text + "\n[Response truncated]", tool_records

            else:
                logger.warning(f"Unexpected stop reason: {response.stop_reason}")
                return response.text, tool_records

        # Max tool calls reached
        logger.warning(f"Max tool calls ({max_tool_calls}) reached")
        return "I've gathered information but reached the maximum number of tool calls. Here's what I found so far.", tool_records

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            "model": self.model,
            "total_requests": self._total_requests,
            "total_tokens_in": self._total_tokens_in,
            "total_tokens_out": self._total_tokens_out,
            "total_tokens": self._total_tokens_in + self._total_tokens_out,
            "errors": self._errors,
            "error_rate": self._errors / self._total_requests if self._total_requests > 0 else 0
        }

    def reset_stats(self) -> None:
        """Reset client statistics."""
        self._total_requests = 0
        self._total_tokens_in = 0
        self._total_tokens_out = 0
        self._errors = 0

    @staticmethod
    def is_available() -> bool:
        """Check if Anthropic client is available."""
        return ANTHROPIC_AVAILABLE
