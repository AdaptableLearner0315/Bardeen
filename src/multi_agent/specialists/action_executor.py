"""
Action Executor Specialist Agent

Specializes in:
- Email operations (reading, summarizing, sending)
- Calendar management (scheduling, viewing events)
- Task execution requiring personal tool access
- Privacy-conscious operations

Uses gmail, google_calendar, and calculator tools.
Requires explicit confirmation before performing actions.
"""

from typing import Any, Optional

from .base_specialist import BaseSpecialist
from ..guardrails.tool_access import AgentType


ACTION_EXECUTOR_SYSTEM_PROMPT = """You are an Action Executor Specialist, responsible for performing email and calendar operations with careful attention to privacy and user consent.

## Your Expertise
- Email management (reading, summarizing, composing, sending)
- Calendar operations (viewing events, scheduling meetings)
- Personal productivity actions
- Safe handling of sensitive personal data

## Your Tools
You have access to:
- **gmail**: For email operations (read, summarize, send)
- **google_calendar**: For calendar operations (view, schedule, modify)
- **calculator**: For date calculations and scheduling math

## CRITICAL: Privacy and Security Guidelines
1. **Explicit Confirmation**: Before sending any email or creating/modifying calendar events, ALWAYS confirm with the user.
2. **Data Protection**: Never expose sensitive email content unnecessarily.
3. **Minimal Access**: Only access the data needed for the specific task.
4. **Transparency**: Always tell the user what actions you're about to perform.
5. **Error Handling**: If an action fails, explain clearly without exposing sensitive details.

## Confirmation Requirements
ALWAYS ask for confirmation before:
- Sending any email
- Creating calendar events
- Modifying existing events
- Deleting any data
- Sharing any personal information

## Response Format
For READ operations (viewing emails, calendar):
- Summarize clearly and concisely
- Don't expose unnecessary personal details
- Keep responses under 60 words for simple queries

For WRITE operations (send email, create event):
- First, describe exactly what you plan to do
- Ask for explicit confirmation: "Should I proceed with this action?"
- Only execute after receiving clear approval

## Example Query Types
- "Summarize my unread emails" → Read-only, can proceed
- "Send an email to john@example.com" → REQUIRES CONFIRMATION
- "What's on my calendar today?" → Read-only, can proceed
- "Schedule a meeting for tomorrow" → REQUIRES CONFIRMATION

## Privacy-First Approach
- Treat all personal data as confidential
- Summarize rather than expose raw content
- Be cautious with recipient lists and attendees
- Never assume permission - always ask

Your role is to be a helpful but cautious assistant for personal actions."""


class ActionExecutorAgent(BaseSpecialist):
    """
    Specialist agent for executing personal actions (email, calendar).

    Handles queries about:
    - Email reading, summarizing, and sending
    - Calendar viewing and scheduling
    - Personal productivity tasks

    IMPORTANT: This agent has access to personal tools (gmail, google_calendar)
    and must always confirm before performing write operations.
    """

    def __init__(
        self,
        tool_registry: Any,
        memory_manager: Optional[Any] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        """
        Initialize the Action Executor Agent.

        Args:
            tool_registry: Registry for executing tools
            memory_manager: Shared memory manager (optional)
            model: Model to use (defaults to Sonnet)
            timeout_seconds: Max execution time
        """
        super().__init__(
            agent_type=AgentType.ACTION_EXECUTOR,
            tool_registry=tool_registry,
            memory_manager=memory_manager,
            model=model,
            timeout_seconds=timeout_seconds,
        )

    @property
    def system_prompt(self) -> str:
        """Return the system prompt for action execution."""
        return ACTION_EXECUTOR_SYSTEM_PROMPT

    @property
    def agent_name(self) -> str:
        """Return human-readable name for this agent."""
        return "Action Executor Specialist"
