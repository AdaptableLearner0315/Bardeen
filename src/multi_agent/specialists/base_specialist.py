"""
Base Specialist Agent

Provides the foundation for all specialist agents with:
- Tool filtering based on agent type
- Shared memory access
- Standard response format
- Error handling with graceful degradation
- Timeout management
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum

import anthropic

from ..guardrails.tool_access import ToolAccessMatrix, AgentType


class AgentStatus(Enum):
    """Status of agent execution."""
    SUCCESS = "success"
    PARTIAL = "partial"  # Completed with some issues
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class AgentResponse:
    """
    Standardized response from a specialist agent.

    Attributes:
        agent_type: Type of agent that generated this response
        query: Original query sent to the agent
        answer: The agent's response text
        status: Execution status
        confidence: Agent's confidence in the response (0.0-1.0)
        tool_calls: List of tools called during execution
        sources: Citations/sources used
        latency_ms: Time taken to generate response
        error_message: Error details if status is not SUCCESS
        metadata: Additional agent-specific data
    """
    agent_type: AgentType
    query: str
    answer: str
    status: AgentStatus
    confidence: float = 1.0
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    latency_ms: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "agent_type": self.agent_type.value,
            "query": self.query,
            "answer": self.answer,
            "status": self.status.value,
            "confidence": self.confidence,
            "tool_calls": self.tool_calls,
            "sources": self.sources,
            "latency_ms": self.latency_ms,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


class BaseSpecialist(ABC):
    """
    Abstract base class for all specialist agents.

    Provides common functionality:
    - Tool access control via ToolAccessMatrix
    - LLM client management
    - Standard execution flow with error handling
    - Response formatting
    """

    # Default model for specialist agents (can be overridden)
    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    DEFAULT_MAX_TOKENS = 4096
    DEFAULT_TEMPERATURE = 0.6
    DEFAULT_TIMEOUT_SECONDS = 30.0

    def __init__(
        self,
        agent_type: AgentType,
        tool_registry: Any,  # Avoid circular import
        memory_manager: Optional[Any] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        """
        Initialize base specialist.

        Args:
            agent_type: The type of this specialist agent
            tool_registry: Registry for executing tools
            memory_manager: Shared memory manager (optional)
            model: Model to use (defaults to Sonnet)
            timeout_seconds: Max execution time
        """
        self.agent_type = agent_type
        self.tool_registry = tool_registry
        self.memory_manager = memory_manager
        self.model = model or self.DEFAULT_MODEL
        self.timeout_seconds = timeout_seconds or self.DEFAULT_TIMEOUT_SECONDS

        # Get allowed tools for this agent
        self.allowed_tools = ToolAccessMatrix.get_allowed_tools(agent_type)

        # Initialize Anthropic client
        self.client = anthropic.Anthropic()

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt for this specialist."""
        pass

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Return human-readable name for this agent."""
        pass

    def get_filtered_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get tool definitions filtered for this agent's access level.

        Returns:
            List of tool definitions this agent can use
        """
        all_definitions = self.tool_registry.get_tool_definitions()
        filtered = []

        for tool_def in all_definitions:
            tool_name = tool_def.get("name", "")
            if tool_name in self.allowed_tools:
                filtered.append(tool_def)

        return filtered

    async def execute(
        self,
        query: str,
        context_messages: Optional[List[Dict[str, Any]]] = None,
    ) -> AgentResponse:
        """
        Execute the agent on a query.

        Args:
            query: The query to process
            context_messages: Previous conversation context

        Returns:
            AgentResponse with results
        """
        start_time = time.time()
        tool_calls_made = []
        sources = []

        try:
            # Build messages
            messages = self._build_messages(query, context_messages)

            # Get filtered tools
            tools = self.get_filtered_tool_definitions()

            # Execute LLM with tool loop
            answer, tool_calls_made, sources = await self._execute_with_tools(
                messages=messages,
                tools=tools,
            )

            latency_ms = (time.time() - start_time) * 1000

            # Determine confidence based on tool success rate
            confidence = self._calculate_confidence(tool_calls_made)

            return AgentResponse(
                agent_type=self.agent_type,
                query=query,
                answer=answer,
                status=AgentStatus.SUCCESS,
                confidence=confidence,
                tool_calls=tool_calls_made,
                sources=sources,
                latency_ms=latency_ms,
            )

        except TimeoutError:
            return AgentResponse(
                agent_type=self.agent_type,
                query=query,
                answer="Request timed out. Please try again.",
                status=AgentStatus.TIMEOUT,
                confidence=0.0,
                tool_calls=tool_calls_made,
                latency_ms=(time.time() - start_time) * 1000,
                error_message=f"Timeout after {self.timeout_seconds}s",
            )

        except Exception as e:
            return AgentResponse(
                agent_type=self.agent_type,
                query=query,
                answer=f"An error occurred: {str(e)}",
                status=AgentStatus.FAILED,
                confidence=0.0,
                tool_calls=tool_calls_made,
                latency_ms=(time.time() - start_time) * 1000,
                error_message=str(e),
            )

    def _build_messages(
        self,
        query: str,
        context_messages: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Build message list for LLM call.

        Args:
            query: Current user query
            context_messages: Previous conversation messages

        Returns:
            List of messages in Anthropic format
        """
        messages = []

        # Add context if provided
        if context_messages:
            messages.extend(context_messages)

        # Add current query
        messages.append({
            "role": "user",
            "content": query,
        })

        return messages

    async def _execute_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        max_iterations: int = 10,
    ) -> tuple[str, List[Dict[str, Any]], List[str]]:
        """
        Execute LLM with tool calling loop.

        Args:
            messages: Conversation messages
            tools: Available tool definitions
            max_iterations: Max tool call iterations

        Returns:
            Tuple of (answer, tool_calls, sources)
        """
        tool_calls_made = []
        sources = []
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Call LLM
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.DEFAULT_MAX_TOKENS,
                temperature=self.DEFAULT_TEMPERATURE,
                system=self.system_prompt,
                tools=tools if tools else None,
                messages=messages,
            )

            # Check stop reason
            if response.stop_reason == "end_turn":
                # Extract text response
                answer = self._extract_text_response(response)
                return answer, tool_calls_made, sources

            elif response.stop_reason == "tool_use":
                # Extract and execute tool calls
                tool_results = []

                for content_block in response.content:
                    if content_block.type == "tool_use":
                        tool_name = content_block.name
                        tool_input = content_block.input
                        tool_use_id = content_block.id

                        # Validate tool access
                        is_allowed, error_msg = ToolAccessMatrix.validate_tool_request(
                            self.agent_type, tool_name
                        )

                        if not is_allowed:
                            # Tool not allowed - return error
                            tool_result = {
                                "success": False,
                                "error": error_msg,
                            }
                        else:
                            # Execute tool
                            tool_result = self.tool_registry.execute_tool(
                                tool_name=tool_name,
                                params=tool_input,
                            )

                        # Record tool call
                        tool_calls_made.append({
                            "tool": tool_name,
                            "input": tool_input,
                            "result": tool_result,
                            "allowed": is_allowed,
                        })

                        # Extract sources if present
                        if isinstance(tool_result, dict):
                            if "source" in tool_result:
                                sources.append(tool_result["source"])
                            if "url" in tool_result:
                                sources.append(tool_result["url"])

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": self._format_tool_result(tool_result),
                        })

                # Add assistant response and tool results to messages
                messages.append({
                    "role": "assistant",
                    "content": response.content,
                })
                messages.append({
                    "role": "user",
                    "content": tool_results,
                })

            else:
                # Unexpected stop reason
                answer = self._extract_text_response(response)
                return answer, tool_calls_made, sources

        # Max iterations reached
        return "Maximum iterations reached.", tool_calls_made, sources

    def _extract_text_response(self, response) -> str:
        """Extract text content from LLM response."""
        for content_block in response.content:
            if hasattr(content_block, "text"):
                return content_block.text
        return ""

    def _format_tool_result(self, result: Any) -> str:
        """Format tool result for LLM consumption."""
        if isinstance(result, dict):
            if result.get("success") is False:
                return f"Error: {result.get('error', 'Unknown error')}"
            # Format successful result
            if "result" in result:
                return str(result["result"])
            return str(result)
        return str(result)

    def _calculate_confidence(self, tool_calls: List[Dict[str, Any]]) -> float:
        """
        Calculate confidence based on tool execution success.

        Args:
            tool_calls: List of tool calls made

        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not tool_calls:
            return 1.0  # No tools needed = high confidence

        successful = sum(
            1 for tc in tool_calls
            if tc.get("result", {}).get("success", True) and tc.get("allowed", True)
        )

        return successful / len(tool_calls)
