"""Claude LLM client with tool calling support and explainable planning."""

from typing import List, Dict, Any, Optional, Tuple
from anthropic import Anthropic
import time
import re

from .tool_registry import ToolRegistry
from .planner import (
    ExecutionPlan, PlanStep, StepStatus,
    create_planning_prompt, parse_plan_from_llm
)
from ..evaluation.tracers.tool_tracer import ToolTracer
from ..evaluation.tracers.error_tracer import ErrorTracer
from ..shared.models import ToolCallTrace, ErrorTrace
from ..shared.config import ResearchMode

SYSTEM_PROMPT_NORMAL = """You are a casual, friendly research assistant. STRICT RULES (non-negotiable):

1. WORD LIMIT: Maximum 50-60 words. No exceptions.
2. Be conversational and warm - like texting a smart friend
3. Lead with the direct answer immediately
4. Skip formalities, filler words, and unnecessary context
5. One short paragraph only - no bullet points unless asked
6. If uncertain, just say "Not sure, but..." briefly

CRITICAL - RESPONSE LENGTH MANAGEMENT:
- ALWAYS complete your response within the token limit
- If you have extensive information, PRIORITIZE the most important points
- NEVER start sentences you cannot finish
- If comparing multiple items, summarize key differences concisely
- Tables MUST be complete - if space is limited, use prose instead
- End with a complete sentence, not mid-word or mid-row

Example good response: "Apple's market cap is around $3 trillion as of late 2024, making it one of the world's most valuable companies."

Example bad response: "That's a great question! Let me help you with that. Apple Inc., the technology company headquartered in Cupertino..." (too long, too formal)"""

SYSTEM_PROMPT_DEEP = """You are a thorough research assistant for deep analysis. STRICT FORMAT:

**SUMMARY (under 100 words):**
Start with a concise executive summary answering the core question directly.

**DETAILED ANALYSIS:**
Then provide comprehensive details with:
- Key facts and figures
- Multiple source perspectives
- Relevant context and implications

Be warm but professional. Cite sources inline.

CRITICAL - RESPONSE LENGTH MANAGEMENT:
- ALWAYS ensure your response is COMPLETE within the token limit
- Monitor response length - if approaching limit, WRAP UP with a conclusion
- NEVER create tables you cannot finish - if comparing 5+ items, use concise prose
- If space is limited, PRIORITIZE: summary > key facts > supporting details
- NEVER end mid-sentence, mid-table-row, or mid-list
- If you have more to say, end with "Key points covered above; ask for specifics if needed."
- Tables are DANGEROUS for truncation - prefer bullet points for long comparisons
- Max 3-4 table rows; for more items, use ranked prose summary"""

def get_system_prompt(is_deep: bool) -> str:
    """Get appropriate system prompt based on research mode."""
    return SYSTEM_PROMPT_DEEP if is_deep else SYSTEM_PROMPT_NORMAL


class QueryClassifier:
    """Auto-detect if query needs deep research vs simple lookup."""

    DEEP_INDICATORS = [
        r"research|analyze|comprehensive|detailed|in-depth|thorough",
        r"compare.*and.*and",  # Multiple comparisons
        r"history.*of|evolution.*of|background.*on",
        r"explain.*how.*works|explain.*in.*detail",
        r"what.*factors|what.*causes|what.*influences",
        r"financial|revenue|market.*cap|stock.*price|earnings",
        r"github|repository|open.*source|codebase",
        r"company.*overview|business.*model|competitive.*landscape",
        r"pros.*and.*cons|advantages.*disadvantages",
        r"step.*by.*step|walkthrough|tutorial",
    ]

    SIMPLE_INDICATORS = [
        r"^what is\s",
        r"^who is\s",
        r"^when did\s",
        r"^where is\s",
        r"^how many\s",
        r"^how much\s",
        r"calculate|compute|\d+\s*[\+\-\*\/]",
        r"^define\s",
        r"capital of|population of|president of",
    ]

    @classmethod
    def is_deep_research(cls, query: str) -> bool:
        """
        Determine if query requires deep research mode.

        Args:
            query: User's question/query

        Returns:
            True if deep research recommended, False for simple lookup
        """
        query_lower = query.lower().strip()

        # Empty or very short queries are simple
        if len(query_lower) < 10:
            return False

        # Check for simple indicators first (fast path)
        for pattern in cls.SIMPLE_INDICATORS:
            if re.search(pattern, query_lower):
                return False

        # Check for deep indicators
        for pattern in cls.DEEP_INDICATORS:
            if re.search(pattern, query_lower):
                return True

        # Long queries (>150 chars) likely need more research
        if len(query) > 150:
            return True

        # Multiple question marks suggest complex query
        if query.count("?") > 1:
            return True

        # Default to simple for ambiguous cases
        return False

    @classmethod
    def get_recommended_tools(cls, query: str) -> list:
        """
        Get recommended tools based on query content.

        Args:
            query: User's question/query

        Returns:
            List of recommended tool names
        """
        import re
        query_lower = query.lower()
        tools = []

        # Math/calculation
        if re.search(r"calculate|compute|\d+\s*[\+\-\*\/\^]|percent|average", query_lower):
            tools.append("calculator")

        # Financial data
        if re.search(r"stock|market.*cap|revenue|earnings|financial|price.*of.*\$", query_lower):
            tools.append("yahoo_finance")
            tools.append("perplexity_search")

        # GitHub/code
        if re.search(r"github|repository|repo|open.*source|stars|forks", query_lower):
            tools.append("github_api")

        # News/current events
        if re.search(r"news|latest|recent|today|this week|breaking", query_lower):
            tools.append("perplexity_search")
            tools.append("web_search")

        # General research
        if re.search(r"research|analyze|explain|compare", query_lower):
            tools.append("perplexity_search")

        # Factual lookups
        if re.search(r"what is|who is|when|where|capital|population", query_lower):
            tools.append("wikipedia")

        # Default fallback
        if not tools:
            tools = ["wikipedia", "web_search"]

        return tools


class ClaudeLLMClient:
    """
    Claude LLM client with tool calling capabilities.

    Handles:
    - Message formatting for Claude API
    - Tool calling loop
    - Integration with tool registry
    - Tracing support for evaluation
    """

    def __init__(self, config, tool_registry: ToolRegistry):
        """
        Initialize Claude client.

        Args:
            config: Application configuration
            tool_registry: Tool registry instance
        """
        self.config = config
        self.tool_registry = tool_registry

        if not config.anthropic_api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable."
            )

        self.client = Anthropic(api_key=config.anthropic_api_key)
        self.model = config.llm.model
        self.temperature = config.llm.temperature
        self.max_tokens = config.llm.max_tokens

    def _estimate_response_tokens(self, query: str) -> int:
        """Estimate appropriate max_tokens based on query type."""
        query_lower = query.lower()

        # Simple factual queries
        if any(w in query_lower for w in ["what is", "who is", "when did", "where is"]):
            return 512

        # Comparison/analysis queries
        if any(w in query_lower for w in ["compare", "explain", "why", "how does"]):
            return 1024

        # Complex multi-part queries
        if "and" in query_lower or len(query) > 200:
            return 2048

        return 1024  # Default

    def create_plan(self, user_message: str) -> ExecutionPlan:
        """
        Create an execution plan for the user's query.

        Args:
            user_message: The user's question

        Returns:
            ExecutionPlan with steps and reasoning
        """
        available_tools = self.tool_registry.get_available_tools()
        planning_prompt = create_planning_prompt(user_message, available_tools)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.3,  # Lower temperature for more consistent planning
                messages=[{"role": "user", "content": planning_prompt}]
            )

            plan_text = self._extract_text_response(response)
            return parse_plan_from_llm(plan_text, user_message)

        except Exception as e:
            # Return default plan on error
            return ExecutionPlan(
                query=user_message,
                goal="Answer the user's question",
                steps=[
                    PlanStep(
                        step_number=1,
                        description="Search for relevant information",
                        tool="web_search",
                        tool_reason="Web search provides current information"
                    )
                ]
            )

    def chat_with_plan(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        tracer: Optional[ToolTracer] = None,
        error_tracer: Optional[ErrorTracer] = None,
        max_tool_calls: int = 10,
        mode: Optional[ResearchMode] = None
    ) -> Tuple[str, List[ToolCallTrace], List[ErrorTrace], ExecutionPlan]:
        """
        Send a message with explicit planning and step-by-step execution.

        Args:
            user_message: The user's question
            conversation_history: Previous conversation messages
            tracer: Optional tool tracer
            error_tracer: Optional error tracer
            max_tool_calls: Maximum tool calls allowed
            mode: Optional research mode (NORMAL or DEEP)

        Returns:
            Tuple of (final_answer, tool_traces, error_traces, execution_plan)
        """
        # Step 1: Create the plan
        plan = self.create_plan(user_message)

        # Step 2: Execute with tool calling (Claude will follow its plan)
        answer, tool_traces, error_traces = self.chat(
            user_message=user_message,
            conversation_history=conversation_history,
            tracer=tracer,
            error_tracer=error_tracer,
            max_tool_calls=max_tool_calls,
            mode=mode
        )

        # Step 3: Update plan steps with actual execution results
        self._update_plan_with_traces(plan, tool_traces)

        return answer, tool_traces, error_traces, plan

    def _update_plan_with_traces(self, plan: ExecutionPlan, traces: List[ToolCallTrace]):
        """Update plan steps with actual execution results."""
        # Match traces to plan steps by tool name
        trace_index = 0

        for step in plan.steps:
            # Find matching trace
            matching_traces = [t for t in traces if t.tool_name == step.tool]

            if matching_traces:
                trace = matching_traces[0]
                step.status = StepStatus.SUCCESS if trace.status.value == "success" else StepStatus.FAILED
                step.latency_ms = trace.latency_ms

                if trace.result:
                    # Extract brief result
                    result_str = str(trace.result)
                    step.result = result_str[:100] if len(result_str) > 100 else result_str

                if trace.error:
                    step.error = trace.error

                # Remove used trace to handle multiple calls to same tool
                traces = [t for t in traces if t != trace]
            else:
                # No trace found - step was skipped or planned but not executed
                step.status = StepStatus.SKIPPED

    def chat(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        tracer: Optional[ToolTracer] = None,
        error_tracer: Optional[ErrorTracer] = None,
        max_tool_calls: int = 10,
        mode: Optional[ResearchMode] = None,
    ) -> Tuple[str, List[ToolCallTrace], List[ErrorTrace]]:
        """
        Send a message to Claude with tool calling support.

        Args:
            user_message: The user's question/message
            conversation_history: Optional previous conversation messages
            tracer: Optional tool tracer for evaluation
            error_tracer: Optional error tracer
            max_tool_calls: Maximum number of tool calls to allow (prevent loops)
            mode: Optional research mode to filter available tools

        Returns:
            Tuple of (final_answer, tool_traces, error_traces)
        """
        # Initialize conversation
        messages = conversation_history or []
        messages.append({
            "role": "user",
            "content": user_message
        })

        # Get tool definitions
        tools = self.tool_registry.get_tool_definitions(mode=mode)

        # Tool calling loop
        tool_call_count = 0

        # Determine if deep mode for system prompt
        is_deep_mode = mode == ResearchMode.DEEP
        system_prompt = get_system_prompt(is_deep_mode)

        while tool_call_count < max_tool_calls:
            # Call Claude
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self._estimate_response_tokens(user_message),
                    temperature=self.temperature,
                    system=system_prompt,
                    tools=tools,
                    messages=messages
                )
            except Exception as e:
                # LLM API error
                error_msg = f"LLM API error: {str(e)}"
                if error_tracer:
                    error_tracer.record_error(
                        tool_name="llm",
                        error_type="api_error",
                        error_message=error_msg,
                        attempted_params={"user_message": user_message},
                        recovery_action="none",
                        recovery_success=False
                    )
                return error_msg, [], error_tracer.get_errors() if error_tracer else []

            # Check stop reason
            if response.stop_reason == "end_turn":
                # Claude is done, extract final answer
                final_answer = self._extract_text_response(response)
                return (
                    final_answer,
                    tracer.get_traces() if tracer else [],
                    error_tracer.get_errors() if error_tracer else []
                )

            elif response.stop_reason == "tool_use":
                # Claude wants to use tools
                tool_call_count += 1

                # Add assistant's response to conversation
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Execute tool calls
                tool_results = []
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        # Extract tool call info
                        tool_name = content_block.name
                        tool_input = content_block.input
                        tool_use_id = content_block.id

                        # Extract LLM reasoning (text before tool call)
                        llm_reasoning = self._extract_reasoning_before_tool(response.content, content_block)

                        # Execute tool
                        tool_result = self.tool_registry.execute_tool(
                            tool_name=tool_name,
                            params=tool_input,
                            tracer=tracer,
                            error_tracer=error_tracer,
                            llm_reasoning=llm_reasoning,
                            allow_fallback=True
                        )

                        # Format result for Claude
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": self._format_tool_result_for_llm(tool_result)
                        })

                # Add tool results to conversation
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

                # Continue loop to get Claude's response
                continue

            elif response.stop_reason == "max_tokens":
                # Hit token limit - attempt recovery by asking Claude to summarize
                truncated_response = self._extract_text_response(response)
                recovered_answer = self._recover_from_truncation(
                    truncated_response,
                    user_message,
                    messages,
                    is_deep_mode
                )
                return (
                    recovered_answer,
                    tracer.get_traces() if tracer else [],
                    error_tracer.get_errors() if error_tracer else []
                )

            else:
                # Unexpected stop reason
                final_answer = f"Unexpected stop reason: {response.stop_reason}"
                return (
                    final_answer,
                    tracer.get_traces() if tracer else [],
                    error_tracer.get_errors() if error_tracer else []
                )

        # Hit max tool calls - synthesize partial answer from gathered information
        partial_answer = self._synthesize_partial_answer(messages, user_message)

        if error_tracer:
            error_tracer.record_error(
                tool_name="llm",
                error_type="max_tool_calls",
                error_message="Tool limit reached, providing partial answer",
                attempted_params={"user_message": user_message},
                recovery_action="synthesize_partial",
                recovery_success=True
            )

        # Mark as low confidence by prefixing with special marker
        final_answer = f"[LOW_CONFIDENCE:TOOL_LIMIT_REACHED]\n{partial_answer}"

        return (
            final_answer,
            tracer.get_traces() if tracer else [],
            error_tracer.get_errors() if error_tracer else []
        )

    def _recover_from_truncation(
        self,
        truncated_response: str,
        original_question: str,
        conversation_history: List[Dict[str, Any]],
        is_deep_mode: bool
    ) -> str:
        """
        Recover from a truncated response by asking Claude to summarize/complete it.

        Args:
            truncated_response: The truncated response text
            original_question: The user's original question
            conversation_history: Full conversation for context
            is_deep_mode: Whether deep research mode is active

        Returns:
            A complete, non-truncated response
        """
        try:
            # Create recovery prompt
            if is_deep_mode:
                recovery_prompt = f"""Your previous response was truncated. Here's what you wrote so far:

---
{truncated_response}
---

IMPORTANT: Provide a COMPLETE response to the original question that fits within the token limit.
- Keep the summary under 100 words
- Limit detailed analysis to 2-3 key points maximum
- NO tables - use concise prose only
- End with a complete sentence
- If comparing items, pick top 3 most important differences

Original question: {original_question}

Provide your complete response now:"""
            else:
                recovery_prompt = f"""Your previous response was truncated. Rewrite it in 50-60 words maximum.

Original question: {original_question}

Truncated attempt: {truncated_response[:200]}...

Provide a COMPLETE 50-60 word response:"""

            # Call Claude without tools to get the recovered response
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048 if is_deep_mode else 512,  # More conservative limits
                temperature=self.temperature,
                system="You must provide a COMPLETE response. Never truncate. Prioritize completeness over comprehensiveness.",
                messages=[{"role": "user", "content": recovery_prompt}]
            )

            recovered_text = self._extract_text_response(response)

            # Check if recovery also got truncated
            if response.stop_reason == "max_tokens":
                # Second truncation - force a minimal summary
                return self._force_minimal_summary(original_question, truncated_response)

            return recovered_text

        except Exception as e:
            # If recovery fails, return truncated response with note
            return f"{truncated_response}\n\n[Response was lengthy - key information above]"

    def _force_minimal_summary(self, question: str, partial_content: str) -> str:
        """
        Force a minimal summary when even recovery attempts get truncated.

        Args:
            question: Original question
            partial_content: Whatever content we managed to gather

        Returns:
            A very brief summary
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=256,  # Very conservative
                temperature=0.3,
                system="Respond in exactly 2-3 sentences. No tables, no lists.",
                messages=[{
                    "role": "user",
                    "content": f"In 2-3 sentences only, answer: {question}\n\nContext from research: {partial_content[:500]}"
                }]
            )
            return self._extract_text_response(response)
        except Exception:
            # Last resort - return what we have
            return f"Based on research: {partial_content[:300]}..."

    def _synthesize_partial_answer(self, messages: List[Dict[str, Any]], original_question: str) -> str:
        """
        Synthesize a partial answer from gathered tool results when max tools is reached.
        """
        try:
            # Ask Claude to synthesize from what we have
            synthesis_prompt = f"""Based on the information gathered so far, please provide the best possible answer to the original question.

Original question: {original_question}

Important: You have reached the maximum number of tool calls. Please synthesize an answer using ONLY the information already gathered from the tool results in this conversation. Do not try to call any more tools.

If the information is incomplete, acknowledge this and provide what you can based on available data."""

            # Add synthesis request to messages
            synthesis_messages = messages.copy()
            synthesis_messages.append({
                "role": "user",
                "content": synthesis_prompt
            })

            # Call Claude without tools to force text response
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=synthesis_messages
            )

            return self._extract_text_response(response)

        except Exception as e:
            return f"Unable to synthesize answer due to error: {str(e)}. The tool limit was reached before gathering sufficient information."

    def _extract_text_response(self, response) -> str:
        """Extract text content from Claude's response."""
        text_parts = []
        for content_block in response.content:
            if content_block.type == "text":
                text_parts.append(content_block.text)
        return "\n".join(text_parts) if text_parts else ""

    def _extract_reasoning_before_tool(self, content_blocks, tool_block) -> Optional[str]:
        """Extract Claude's reasoning text that appears before a tool call."""
        reasoning_parts = []
        for block in content_blocks:
            if block == tool_block:
                # Stop when we reach the tool block
                break
            if block.type == "text":
                reasoning_parts.append(block.text)

        return "\n".join(reasoning_parts) if reasoning_parts else None

    def _format_tool_result_for_llm(self, tool_result: Dict[str, Any]) -> str:
        """
        Format tool result for Claude to understand.

        Converts structured tool result into a string that Claude can parse.
        """
        if not tool_result.get("success", True):
            # Tool failed
            error = tool_result.get("error", "Unknown error")
            return f"Error: {error}\n\nPlease try an alternative approach or provide a partial answer based on available information."

        # Tool succeeded - format based on tool type
        if "results" in tool_result:
            # Web search results
            results = tool_result["results"]
            if not results:
                return "No results found."

            formatted = []
            if tool_result.get("answer"):
                formatted.append(f"Quick Answer: {tool_result['answer']}\n")

            formatted.append("Search Results:")
            for i, result in enumerate(results[:3], 1):
                formatted.append(f"\n{i}. {result.get('title', 'Untitled')}")
                formatted.append(f"   {result.get('content', '')[:200]}...")
                formatted.append(f"   Source: {result.get('url', '')}")

            return "\n".join(formatted)

        elif "title" in tool_result and "summary" in tool_result:
            # Wikipedia result
            formatted = [
                f"Wikipedia: {tool_result['title']}",
                f"\n{tool_result['summary'][:500]}...",
                f"\nSource: {tool_result.get('url', '')}"
            ]

            if "data" in tool_result and tool_result["data"]:
                formatted.append("\nKey Data:")
                for key, value in tool_result["data"].items():
                    formatted.append(f"  - {key}: {value}")

            return "\n".join(formatted)

        elif "result" in tool_result and "expression" in tool_result:
            # Calculator result
            return f"Calculation: {tool_result['expression']} = {tool_result['result']}"

        else:
            # Generic result
            return str(tool_result)
