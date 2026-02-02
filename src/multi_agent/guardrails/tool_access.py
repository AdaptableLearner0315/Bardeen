"""
Tool Access Matrix for Multi-Agent System

Defines which tools each specialist agent can access.
This enforces the principle of least privilege - agents only
have access to tools they need for their specific domain.

Key restriction: Personal tools (gmail, google_calendar) are
ONLY available to the Action Executor Agent.
"""

from enum import Enum
from typing import Set, Dict, List


class AgentType(Enum):
    """Types of specialist agents in the system."""
    COMPANY_RESEARCH = "company_research"
    FINANCIAL_ANALYST = "financial_analyst"
    COMPETITIVE_INTEL = "competitive_intel"
    ACTION_EXECUTOR = "action_executor"
    GENERAL_FALLBACK = "general_fallback"
    ORCHESTRATOR = "orchestrator"


class ToolAccessMatrix:
    """
    Manages tool access permissions for each agent type.

    Tool Access Matrix:
    ┌─────────────────┬───────┬───────┬───────┬───────┬─────────┐
    │ Tool            │Company│Finance│Compet.│Action │General  │
    ├─────────────────┼───────┼───────┼───────┼───────┼─────────┤
    │ web_search      │  ✓    │  ✓    │  ✓    │  ✗    │  ✓      │
    │ wikipedia       │  ✓    │  ✗    │  ✗    │  ✗    │  ✓      │
    │ calculator      │  ✗    │  ✓    │  ✗    │  ✓    │  ✓      │
    │ perplexity      │  ✗    │  ✓    │  ✓    │  ✗    │  ✓      │
    │ gmail           │  ✗    │  ✗    │  ✗    │  ✓    │  ✗      │
    │ google_calendar │  ✗    │  ✗    │  ✗    │  ✓    │  ✗      │
    └─────────────────┴───────┴───────┴───────┴───────┴─────────┘
    """

    # Define tool access for each agent type
    _ACCESS_MATRIX: Dict[AgentType, Set[str]] = {
        AgentType.COMPANY_RESEARCH: {
            "web_search",
            "wikipedia",
        },
        AgentType.FINANCIAL_ANALYST: {
            "web_search",
            "calculator",
            "perplexity_search",
        },
        AgentType.COMPETITIVE_INTEL: {
            "web_search",
            "perplexity_search",
        },
        AgentType.ACTION_EXECUTOR: {
            "gmail",
            "google_calendar",
            "calculator",
        },
        AgentType.GENERAL_FALLBACK: {
            "web_search",
            "wikipedia",
            "calculator",
            "perplexity_search",
            # Note: NO gmail or google_calendar - those are Action-only
        },
        AgentType.ORCHESTRATOR: set(),  # Orchestrator doesn't use tools directly
    }

    # Personal/sensitive tools that require extra protection
    PERSONAL_TOOLS: Set[str] = {"gmail", "google_calendar"}

    # All available tools in the system
    ALL_TOOLS: Set[str] = {
        "web_search",
        "wikipedia",
        "calculator",
        "perplexity_search",
        "gmail",
        "google_calendar",
    }

    @classmethod
    def get_allowed_tools(cls, agent_type: AgentType) -> Set[str]:
        """
        Get the set of tools an agent type is allowed to use.

        Args:
            agent_type: The type of agent

        Returns:
            Set of tool names the agent can access
        """
        return cls._ACCESS_MATRIX.get(agent_type, set()).copy()

    @classmethod
    def can_access_tool(cls, agent_type: AgentType, tool_name: str) -> bool:
        """
        Check if an agent type can access a specific tool.

        Args:
            agent_type: The type of agent
            tool_name: Name of the tool to check

        Returns:
            True if agent can access the tool, False otherwise
        """
        allowed = cls._ACCESS_MATRIX.get(agent_type, set())
        return tool_name in allowed

    @classmethod
    def is_personal_tool(cls, tool_name: str) -> bool:
        """
        Check if a tool is classified as personal/sensitive.

        Args:
            tool_name: Name of the tool

        Returns:
            True if tool handles personal data
        """
        return tool_name in cls.PERSONAL_TOOLS

    @classmethod
    def filter_tools_for_agent(
        cls,
        agent_type: AgentType,
        available_tools: List[str]
    ) -> List[str]:
        """
        Filter a list of tools to only those accessible by an agent.

        Args:
            agent_type: The type of agent
            available_tools: List of tool names to filter

        Returns:
            Filtered list containing only accessible tools
        """
        allowed = cls.get_allowed_tools(agent_type)
        return [tool for tool in available_tools if tool in allowed]

    @classmethod
    def validate_tool_request(
        cls,
        agent_type: AgentType,
        tool_name: str
    ) -> tuple[bool, str]:
        """
        Validate a tool access request with detailed error message.

        Args:
            agent_type: The type of agent making the request
            tool_name: Name of the tool being requested

        Returns:
            Tuple of (is_allowed, error_message)
        """
        if tool_name not in cls.ALL_TOOLS:
            return False, f"Unknown tool: {tool_name}"

        if not cls.can_access_tool(agent_type, tool_name):
            if cls.is_personal_tool(tool_name):
                return False, (
                    f"Tool '{tool_name}' is a personal tool that can only be "
                    f"accessed by the Action Executor Agent. "
                    f"Agent '{agent_type.value}' does not have permission."
                )
            else:
                allowed = cls.get_allowed_tools(agent_type)
                return False, (
                    f"Agent '{agent_type.value}' cannot access tool '{tool_name}'. "
                    f"Allowed tools: {sorted(allowed)}"
                )

        return True, ""

    @classmethod
    def get_agent_description(cls, agent_type: AgentType) -> str:
        """
        Get a description of an agent's tool capabilities.

        Args:
            agent_type: The type of agent

        Returns:
            Human-readable description of agent's tools
        """
        tools = cls.get_allowed_tools(agent_type)
        if not tools:
            return f"{agent_type.value}: No direct tool access"
        return f"{agent_type.value}: {', '.join(sorted(tools))}"
