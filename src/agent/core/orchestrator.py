"""Agent orchestrator that coordinates LLM, tools, and memory."""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from src.shared.config import get_config, ResearchMode
from src.shared.models import ToolMode
from src.agent.tools.registry import ToolRegistry, get_registry, reset_registry
from src.agent.tools.base import ToolResult
from .llm_client import LLMClient
from .memory import MemoryManager

logger = logging.getLogger(__name__)


@dataclass
class ToolCallRecord:
    """Record of a tool call during agent execution."""
    tool_name: str
    input_params: Dict[str, Any]
    result: Dict[str, Any]
    success: bool
    execution_time: float
    timestamp: float = field(default_factory=time.time)
    reasoning: Optional[str] = None


@dataclass
class AgentResponse:
    """Response from the agent."""
    answer: str
    tool_calls: List[ToolCallRecord] = field(default_factory=list)
    mode: ResearchMode = ResearchMode.NORMAL
    total_time: float = 0.0
    token_usage: Dict[str, int] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None

    @property
    def tool_count(self) -> int:
        """Number of tools called."""
        return len(self.tool_calls)

    @property
    def successful_tool_calls(self) -> int:
        """Number of successful tool calls."""
        return sum(1 for tc in self.tool_calls if tc.success)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "answer": self.answer,
            "tool_calls": [
                {
                    "tool_name": tc.tool_name,
                    "input_params": tc.input_params,
                    "success": tc.success,
                    "execution_time": tc.execution_time,
                }
                for tc in self.tool_calls
            ],
            "mode": self.mode.value,
            "total_time": self.total_time,
            "token_usage": self.token_usage,
            "success": self.success,
            "error": self.error,
        }


class AgentOrchestrator:
    """
    Central orchestrator for the B2B Account Intelligence Agent.

    Coordinates:
    - LLM interactions with Claude
    - Tool execution via registry
    - Memory management (short-term and long-term)
    - Research mode switching (Normal vs Deep)
    """

    # System prompt for the agent
    SYSTEM_PROMPT = """You are a B2B Account Intelligence Agent that helps users research companies and find business information.

You have access to the following tools:
{tool_descriptions}

Guidelines:
1. Use tools to gather accurate, up-to-date information
2. Always cite sources when providing facts
3. If a tool fails, try an alternative approach or inform the user
4. Be concise but thorough in your answers
5. For financial data, note the data timestamp
6. If you can't find information, say so clearly

Current research mode: {mode}
{mode_description}"""

    MODE_DESCRIPTIONS = {
        ResearchMode.NORMAL: "Normal mode uses core tools (web search, Wikipedia, calculator) for quick answers.",
        ResearchMode.DEEP: "Deep mode uses all available tools for comprehensive research including financial data, SEC filings, GitHub, and more."
    }

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        tool_registry: Optional[ToolRegistry] = None,
        memory_manager: Optional[MemoryManager] = None,
        default_mode: ResearchMode = ResearchMode.NORMAL,
        max_tool_calls: int = 10,
    ):
        """
        Initialize the orchestrator.

        Args:
            llm_client: LLM client instance
            tool_registry: Tool registry instance
            memory_manager: Memory manager instance
            default_mode: Default research mode
            max_tool_calls: Maximum tool calls per request
        """
        self.llm_client = llm_client
        self.tool_registry = tool_registry or get_registry()
        self.memory = memory_manager or MemoryManager()

        self.current_mode = default_mode
        self.max_tool_calls = max_tool_calls

        # Statistics
        self._total_requests = 0
        self._total_tool_calls = 0
        self._total_time = 0.0

    def _ensure_llm_client(self) -> LLMClient:
        """Ensure LLM client is initialized."""
        if self.llm_client is None:
            self.llm_client = LLMClient()
        return self.llm_client

    def set_mode(self, mode: ResearchMode) -> None:
        """
        Set the research mode.

        Args:
            mode: Research mode (NORMAL or DEEP)
        """
        self.current_mode = mode
        self.memory.set_mode(mode.value)
        logger.info(f"Research mode set to: {mode.value}")

    def ask(
        self,
        question: str,
        mode: Optional[ResearchMode] = None,
        reset_conversation: bool = False,
        tracer: Optional[Any] = None,
    ) -> AgentResponse:
        """
        Ask the agent a question.

        Args:
            question: User's question
            mode: Override research mode for this request
            reset_conversation: Whether to reset conversation history
            tracer: Optional tracer for tool calls

        Returns:
            AgentResponse with answer and metadata
        """
        start_time = time.time()
        self._total_requests += 1

        # Handle mode
        effective_mode = mode or self.current_mode
        self.memory.set_mode(effective_mode.value)

        # Reset conversation if requested
        if reset_conversation:
            self.memory.clear_short_term()

        # Add user message to memory
        self.memory.add_user_message(question)

        try:
            # Get LLM client
            llm = self._ensure_llm_client()

            # Build system prompt
            system_prompt = self._build_system_prompt(effective_mode)

            # Get tool definitions
            tool_definitions = self.tool_registry.get_tool_definitions(effective_mode)

            # Get conversation context
            messages = self.memory.get_context_messages()

            # Execute with tool calling
            tool_records = []

            def tool_executor(tool_name: str, tool_input: Dict[str, Any]) -> str:
                """Execute a tool and record the result."""
                tool_start = time.time()

                result = self.tool_registry.execute_tool(
                    name=tool_name,
                    params=tool_input,
                    mode=effective_mode,
                    tracer=tracer,
                )

                tool_time = time.time() - tool_start
                self._total_tool_calls += 1

                # Record tool call
                record = ToolCallRecord(
                    tool_name=tool_name,
                    input_params=tool_input,
                    result=result.data if result.success else {"error": result.error},
                    success=result.success,
                    execution_time=tool_time,
                )
                tool_records.append(record)

                # Format result for LLM
                return self._format_tool_result(result)

            # Chat with tools
            answer, raw_tool_calls = llm.chat_with_tools(
                user_message=question,
                conversation_history=messages[:-1],  # Exclude just-added user message
                tools=tool_definitions if tool_definitions else None,
                tool_executor=tool_executor,
                system=system_prompt,
                max_tool_calls=self.max_tool_calls,
            )

            # Add assistant response to memory
            self.memory.add_assistant_message(answer)

            total_time = time.time() - start_time
            self._total_time += total_time

            return AgentResponse(
                answer=answer,
                tool_calls=tool_records,
                mode=effective_mode,
                total_time=total_time,
                token_usage=llm.get_stats(),
                success=True,
            )

        except Exception as e:
            logger.error(f"Agent error: {e}")
            total_time = time.time() - start_time

            error_msg = f"I encountered an error while processing your request: {str(e)}"
            self.memory.add_assistant_message(error_msg)

            return AgentResponse(
                answer=error_msg,
                tool_calls=[],
                mode=effective_mode,
                total_time=total_time,
                success=False,
                error=str(e),
            )

    def _build_system_prompt(self, mode: ResearchMode) -> str:
        """Build the system prompt with tool descriptions."""
        tool_definitions = self.tool_registry.get_tool_definitions(mode)

        tool_descriptions = []
        for tool in tool_definitions:
            tool_descriptions.append(f"- {tool['name']}: {tool['description']}")

        return self.SYSTEM_PROMPT.format(
            tool_descriptions="\n".join(tool_descriptions) if tool_descriptions else "No tools available.",
            mode=mode.value.upper(),
            mode_description=self.MODE_DESCRIPTIONS.get(mode, "")
        )

    def _format_tool_result(self, result: ToolResult) -> str:
        """Format tool result for LLM consumption."""
        if not result.success:
            return f"Error: {result.error}\n\nPlease try an alternative approach."

        data = result.data
        if not isinstance(data, dict):
            return str(data)

        # Format based on tool type and result structure
        if "results" in data:
            # Search results
            results = data.get("results", [])
            if not results:
                return "No results found."

            formatted = []
            if data.get("answer"):
                formatted.append(f"Quick Answer: {data['answer']}\n")

            formatted.append("Results:")
            for i, r in enumerate(results[:5], 1):
                formatted.append(f"{i}. {r.get('title', 'Untitled')}")
                content = r.get('content', '')[:200]
                if content:
                    formatted.append(f"   {content}...")
                if r.get('url'):
                    formatted.append(f"   Source: {r['url']}")

            return "\n".join(formatted)

        elif "summary" in data:
            # Wikipedia-style result
            parts = [data.get("title", "Result")]
            if data.get("summary"):
                parts.append(data["summary"][:1000])
            if data.get("url"):
                parts.append(f"Source: {data['url']}")
            return "\n\n".join(parts)

        elif "result" in data and "expression" in data:
            # Calculator result
            return f"Calculation: {data['expression']} = {data['result']}"

        elif "company_name" in data:
            # Financial data
            parts = [f"Company: {data['company_name']}"]
            for key, value in data.items():
                if key not in ["success", "company_name", "raw_response"]:
                    if isinstance(value, dict):
                        parts.append(f"\n{key.replace('_', ' ').title()}:")
                        for k, v in value.items():
                            parts.append(f"  - {k}: {v}")
                    else:
                        parts.append(f"- {key.replace('_', ' ').title()}: {value}")
            return "\n".join(parts)

        else:
            # Generic formatting
            return str(data)

    def get_available_tools(self, mode: Optional[ResearchMode] = None) -> List[str]:
        """Get list of available tool names."""
        effective_mode = mode or self.current_mode
        return self.tool_registry.get_tool_names(mode=effective_mode)

    def reset_conversation(self) -> None:
        """Reset the conversation history."""
        self.memory.clear_short_term()

    def new_session(self) -> Optional[str]:
        """Start a new session."""
        return self.memory.new_session()

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        stats = {
            "total_requests": self._total_requests,
            "total_tool_calls": self._total_tool_calls,
            "total_time": self._total_time,
            "average_time": self._total_time / self._total_requests if self._total_requests > 0 else 0,
            "current_mode": self.current_mode.value,
            "memory": self.memory.get_stats(),
            "registry": self.tool_registry.get_stats(),
        }

        if self.llm_client:
            stats["llm"] = self.llm_client.get_stats()

        return stats

    def reset_stats(self) -> None:
        """Reset orchestrator statistics."""
        self._total_requests = 0
        self._total_tool_calls = 0
        self._total_time = 0.0

        if self.llm_client:
            self.llm_client.reset_stats()


def create_agent(
    mode: ResearchMode = ResearchMode.NORMAL,
    api_key: Optional[str] = None,
) -> AgentOrchestrator:
    """
    Create a configured agent orchestrator.

    Args:
        mode: Default research mode
        api_key: Optional Anthropic API key

    Returns:
        Configured AgentOrchestrator
    """
    llm_client = None
    if api_key or LLMClient.is_available():
        try:
            llm_client = LLMClient(api_key=api_key)
        except Exception as e:
            logger.warning(f"Could not initialize LLM client: {e}")

    return AgentOrchestrator(
        llm_client=llm_client,
        default_mode=mode,
    )
