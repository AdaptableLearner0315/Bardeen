"""Main research assistant agent."""

import logging
from typing import List, Dict, Any, Optional, Tuple

from .llm_client import ClaudeLLMClient, QueryClassifier
from .tool_registry import ToolRegistry
from ..shared.config import ResearchMode
from .planner import ExecutionPlan
from .core.memory import MemoryManager, get_critical_extractor
from ..evaluation.tracers.tool_tracer import ToolTracer
from ..evaluation.tracers.error_tracer import ErrorTracer
from ..shared.models import ToolCallTrace, ErrorTrace, ConversationMessage, ToolCall, ToolStatus
from ..shared.config import Config

logger = logging.getLogger(__name__)


class ResearchAssistant:
    """
    Research assistant agent with tool calling capabilities.

    Provides a simple interface for asking questions and getting
    answers backed by web search, Wikipedia, and calculations.
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize research assistant.

        Args:
            config: Optional configuration (will create default if not provided)
        """
        from ..shared.config import load_config

        self.config = config or load_config()
        self.tool_registry = ToolRegistry(self.config)
        self.llm_client = ClaudeLLMClient(self.config, self.tool_registry)
        self.conversation_history: List[Dict[str, Any]] = []

        # Initialize memory manager with global session for persistence
        self.memory = MemoryManager(
            session_id="global_demo",
            max_short_term_messages=20,
            enable_long_term=True
        )

        # Initialize trace storage
        self._trace_repo = None
        try:
            from ..storage.repositories.tool_traces import ToolTraceRepository
            from ..storage.database import Database
            db = Database(self.config.storage.database_path)
            self._trace_repo = ToolTraceRepository(db)
            logger.info("Trace storage initialized")
        except Exception as e:
            logger.warning(f"Could not initialize trace storage: {e}")

    def ask(
        self,
        question: str,
        tracer: Optional[ToolTracer] = None,
        error_tracer: Optional[ErrorTracer] = None,
        reset_conversation: bool = False,
        mode: Optional[str] = None,
    ) -> Tuple[str, List[ToolCallTrace], List[ErrorTrace]]:
        """
        Ask the research assistant a question.

        Args:
            question: The question to ask
            tracer: Optional tool tracer for evaluation
            error_tracer: Optional error tracer
            reset_conversation: Whether to reset conversation history
            mode: Research mode - "normal", "deep", or None for auto-detect

        Returns:
            Tuple of (answer, tool_traces, error_traces)
        """
        # Auto-detect research mode if not specified
        if mode is None:
            is_deep = QueryClassifier.is_deep_research(question)
            research_mode = ResearchMode.DEEP if is_deep else ResearchMode.NORMAL
        else:
            research_mode = ResearchMode.DEEP if mode == "deep" else ResearchMode.NORMAL

        # Log the mode being used
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Query mode: {research_mode.value} (auto-detected: {mode is None})")

        if reset_conversation:
            self.memory.clear_short_term()

        # Add user message to memory
        self.memory.add_user_message(question)

        # Get context from memory for LLM
        context = self.memory.get_context_messages()

        # Get response from LLM
        answer, tool_traces, error_traces = self.llm_client.chat(
            user_message=question,
            conversation_history=context,
            tracer=tracer,
            error_tracer=error_tracer,
            mode=research_mode,
        )

        # Store assistant response in memory
        self.memory.add_assistant_message(answer)

        # Extract and store critical information (async, non-blocking)
        try:
            extractor = get_critical_extractor()
            extractor.extract_async(question, answer, self.llm_client)
        except Exception:
            pass  # Don't block on extraction failures

        return answer, tool_traces, error_traces

    def ask_with_plan(
        self,
        question: str,
        tracer: Optional[ToolTracer] = None,
        error_tracer: Optional[ErrorTracer] = None,
        reset_conversation: bool = False,
        mode: Optional[str] = None,
    ) -> Tuple[str, List[ToolCallTrace], List[ErrorTrace], ExecutionPlan, str, bool]:
        """
        Ask the research assistant with explicit planning.

        Args:
            question: The question to ask
            tracer: Optional tool tracer for evaluation
            error_tracer: Optional error tracer
            reset_conversation: Whether to reset conversation history
            mode: Research mode - "normal", "deep", or None for auto-detect

        Returns:
            Tuple of (answer, tool_traces, error_traces, execution_plan, mode_used, is_auto_detected)
        """
        # Auto-detect research mode if not specified
        is_auto_detected = mode is None
        if is_auto_detected:
            is_deep = QueryClassifier.is_deep_research(question)
            research_mode = ResearchMode.DEEP if is_deep else ResearchMode.NORMAL
        else:
            research_mode = ResearchMode.DEEP if mode == "deep" else ResearchMode.NORMAL

        mode_used = research_mode.value

        if reset_conversation:
            self.conversation_history = []

        # Get response with plan
        answer, tool_traces, error_traces, plan = self.llm_client.chat_with_plan(
            user_message=question,
            conversation_history=self.conversation_history.copy(),
            tracer=tracer,
            error_tracer=error_tracer,
            mode=research_mode,
        )

        # Update conversation history
        self.conversation_history.append({
            "role": "user",
            "content": question
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": answer
        })

        # Keep only last 10 messages
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

        # Save traces to database
        self._save_traces(tool_traces, question, mode_used)

        return answer, tool_traces, error_traces, plan, mode_used, is_auto_detected

    def _save_traces(self, tool_traces: List[ToolCallTrace], question: str, mode: str):
        """Save tool traces to database for analysis."""
        if not self._trace_repo or not tool_traces:
            return

        try:
            from datetime import datetime
            session_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            for trace in tool_traces:
                tool_call = ToolCall(
                    tool_name=trace.tool_name,
                    input_data=trace.params,
                    output_data={"result": str(trace.result)[:500]} if trace.result else None,
                    status=trace.status if isinstance(trace.status, ToolStatus) else ToolStatus.SUCCESS,
                    error_message=trace.error,
                    latency_ms=int(trace.latency_ms),
                    timestamp=datetime.now()
                )
                self._trace_repo.save_trace(tool_call, session_id)

            logger.debug(f"Saved {len(tool_traces)} traces for session {session_id}")
        except Exception as e:
            logger.warning(f"Failed to save traces: {e}")

    def reset_conversation(self):
        """Reset the conversation history."""
        self.memory.clear_short_term()

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return self.tool_registry.get_available_tools()

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the current conversation history."""
        return self.memory.get_context_messages()


def create_agent(api_key: Optional[str] = None, tavily_api_key: Optional[str] = None) -> ResearchAssistant:
    """
    Convenience function to create a research assistant agent.

    Args:
        api_key: Anthropic API key (optional, will use env var if not provided)
        tavily_api_key: Tavily API key (optional, currently unused - loaded from env)

    Returns:
        Initialized ResearchAssistant instance
    """
    from ..shared.config import Config, LLMConfig, ToolConfig, EvaluationConfig

    config = Config(
        anthropic_api_key=api_key,
        llm=LLMConfig(),
        tools=ToolConfig(),
        evaluation=EvaluationConfig()
    )

    return ResearchAssistant(config)
