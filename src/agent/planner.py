"""Agent planner for explicit task decomposition and reasoning."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class StepStatus(Enum):
    """Status of a plan step."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """A single step in the execution plan."""
    step_number: int
    description: str
    tool: str
    tool_reason: str  # 1-line reason for choosing this tool
    status: StepStatus = StepStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    latency_ms: float = 0


@dataclass
class ExecutionPlan:
    """Complete execution plan for a query."""
    query: str
    goal: str
    steps: List[PlanStep] = field(default_factory=list)
    current_step: int = 0

    def to_ascii_art(self) -> str:
        """Convert plan to ASCII art visualization."""
        lines = []

        # Header
        lines.append("┌" + "─" * 70 + "┐")
        lines.append("│" + " 🎯 EXECUTION PLAN".ljust(70) + "│")
        lines.append("├" + "─" * 70 + "┤")

        # Goal
        goal_line = f"│ Goal: {self.goal[:62]}"
        lines.append(goal_line.ljust(71) + "│")
        lines.append("├" + "─" * 70 + "┤")

        # Steps
        for i, step in enumerate(self.steps):
            # Status indicator
            if step.status == StepStatus.SUCCESS:
                status_icon = "✓"
            elif step.status == StepStatus.FAILED:
                status_icon = "✗"
            elif step.status == StepStatus.IN_PROGRESS:
                status_icon = "►"
            elif step.status == StepStatus.SKIPPED:
                status_icon = "○"
            else:
                status_icon = "○"

            # Step line
            step_line = f"│ {status_icon} Step {step.step_number}: {step.description[:50]}"
            lines.append(step_line.ljust(71) + "│")

            # Tool line
            tool_line = f"│   └─ Tool: {step.tool} → {step.tool_reason[:45]}"
            lines.append(tool_line.ljust(71) + "│")

            if i < len(self.steps) - 1:
                lines.append("│" + " " * 70 + "│")

        # Footer
        lines.append("└" + "─" * 70 + "┘")

        return "\n".join(lines)

    def to_tree(self) -> str:
        """Convert plan execution to tree visualization with results."""
        lines = []

        lines.append(f"🎯 {self.goal}")
        lines.append("│")

        for i, step in enumerate(self.steps):
            is_last = (i == len(self.steps) - 1)
            prefix = "└──" if is_last else "├──"
            child_prefix = "    " if is_last else "│   "

            # Status indicator
            if step.status == StepStatus.SUCCESS:
                status = "✓ PASS"
                status_color = "success"
            elif step.status == StepStatus.FAILED:
                status = "✗ FAIL"
                status_color = "error"
            elif step.status == StepStatus.IN_PROGRESS:
                status = "► RUNNING"
                status_color = "running"
            else:
                status = "○ PENDING"
                status_color = "pending"

            # Step line with status
            lines.append(f"{prefix} Step {step.step_number}: {step.description} [{status}]")

            # Tool info
            lines.append(f"{child_prefix}├─ Tool: {step.tool}")
            lines.append(f"{child_prefix}├─ Why: {step.tool_reason}")

            # Result or error
            if step.status == StepStatus.SUCCESS and step.result:
                result_preview = step.result[:50] + "..." if len(step.result) > 50 else step.result
                lines.append(f"{child_prefix}└─ Result: {result_preview}")
            elif step.status == StepStatus.FAILED and step.error:
                lines.append(f"{child_prefix}└─ Error: {step.error}")

            if not is_last:
                lines.append("│")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert plan to dictionary for JSON serialization."""
        return {
            "query": self.query,
            "goal": self.goal,
            "steps": [
                {
                    "step_number": s.step_number,
                    "description": s.description,
                    "tool": s.tool,
                    "tool_reason": s.tool_reason,
                    "status": s.status.value,
                    "result": s.result,
                    "error": s.error,
                    "latency_ms": s.latency_ms
                }
                for s in self.steps
            ],
            "current_step": self.current_step,
            "ascii_plan": self.to_ascii_art(),
            "tree_view": self.to_tree()
        }


PLANNING_PROMPT = """You are a research assistant. Before answering, create an explicit execution plan.

Given the user's question, output a JSON plan with this EXACT format:
{
  "goal": "One sentence describing what we need to find",
  "steps": [
    {
      "step_number": 1,
      "description": "Brief description of what this step does",
      "tool": "tool_name",
      "tool_reason": "One short sentence why this tool is best for this step"
    }
  ]
}

Available tools:
%TOOLS%

Rules:
- Use 1-5 steps (fewer is better)
- Each step should have exactly ONE tool
- tool_reason must be ONE short sentence (under 60 chars)
- Be specific in descriptions
- Only use tools from the available list

User question: %QUESTION%

Output ONLY the JSON plan, nothing else:"""


def parse_plan_from_llm(response: str, query: str) -> ExecutionPlan:
    """Parse LLM response into ExecutionPlan."""
    import json
    import re

    # Try to extract JSON from response
    try:
        # Find JSON in response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            plan_data = json.loads(json_match.group())
        else:
            raise ValueError("No JSON found in response")

        # Create plan
        plan = ExecutionPlan(
            query=query,
            goal=plan_data.get("goal", "Answer the user's question")
        )

        # Add steps
        for step_data in plan_data.get("steps", []):
            step = PlanStep(
                step_number=step_data.get("step_number", len(plan.steps) + 1),
                description=step_data.get("description", "Execute tool"),
                tool=step_data.get("tool", "web_search"),
                tool_reason=step_data.get("tool_reason", "Best available option")
            )
            plan.steps.append(step)

        return plan

    except Exception as e:
        # Return a default plan if parsing fails
        return ExecutionPlan(
            query=query,
            goal="Answer the user's question",
            steps=[
                PlanStep(
                    step_number=1,
                    description="Search for information",
                    tool="web_search",
                    tool_reason="Web search provides current information"
                )
            ]
        )


def create_planning_prompt(question: str, available_tools: List[str]) -> str:
    """Create the planning prompt with available tools."""
    tools_str = "\n".join(f"- {tool}" for tool in available_tools)

    prompt = PLANNING_PROMPT.replace("%TOOLS%", tools_str)
    prompt = prompt.replace("%QUESTION%", question)

    return prompt
