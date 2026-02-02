"""Tests for agent planner module."""

import pytest
from pathlib import Path


class TestPlannerModule:
    """Tests for planner module existence and imports."""

    def test_planner_module_exists(self):
        """Test planner module can be imported."""
        from src.agent.planner import ExecutionPlan, PlanStep, StepStatus
        assert ExecutionPlan is not None
        assert PlanStep is not None
        assert StepStatus is not None

    def test_step_status_enum(self):
        """Test StepStatus enum has expected values."""
        from src.agent.planner import StepStatus

        assert StepStatus.PENDING.value == "pending"
        assert StepStatus.IN_PROGRESS.value == "in_progress"
        assert StepStatus.SUCCESS.value == "success"
        assert StepStatus.FAILED.value == "failed"
        assert StepStatus.SKIPPED.value == "skipped"


class TestPlanStep:
    """Tests for PlanStep dataclass."""

    def test_plan_step_creation(self):
        """Test creating a PlanStep."""
        from src.agent.planner import PlanStep, StepStatus

        step = PlanStep(
            step_number=1,
            description="Search for company information",
            tool="web_search",
            tool_reason="Web search provides current data"
        )

        assert step.step_number == 1
        assert step.description == "Search for company information"
        assert step.tool == "web_search"
        assert step.tool_reason == "Web search provides current data"
        assert step.status == StepStatus.PENDING

    def test_plan_step_with_status(self):
        """Test PlanStep with different statuses."""
        from src.agent.planner import PlanStep, StepStatus

        step = PlanStep(
            step_number=1,
            description="Calculate revenue",
            tool="calculator",
            tool_reason="Need mathematical computation",
            status=StepStatus.SUCCESS,
            result="150000000"
        )

        assert step.status == StepStatus.SUCCESS
        assert step.result == "150000000"

    def test_plan_step_with_error(self):
        """Test PlanStep with error."""
        from src.agent.planner import PlanStep, StepStatus

        step = PlanStep(
            step_number=2,
            description="Fetch Wikipedia article",
            tool="wikipedia",
            tool_reason="Wikipedia has company history",
            status=StepStatus.FAILED,
            error="Page not found"
        )

        assert step.status == StepStatus.FAILED
        assert step.error == "Page not found"


class TestExecutionPlan:
    """Tests for ExecutionPlan dataclass."""

    def test_execution_plan_creation(self):
        """Test creating an ExecutionPlan."""
        from src.agent.planner import ExecutionPlan, PlanStep

        plan = ExecutionPlan(
            query="What is Salesforce's revenue?",
            goal="Find Salesforce's latest revenue figure"
        )

        assert plan.query == "What is Salesforce's revenue?"
        assert plan.goal == "Find Salesforce's latest revenue figure"
        assert plan.steps == []
        assert plan.current_step == 0

    def test_execution_plan_with_steps(self):
        """Test ExecutionPlan with steps."""
        from src.agent.planner import ExecutionPlan, PlanStep

        plan = ExecutionPlan(
            query="What is 2+2?",
            goal="Calculate the result",
            steps=[
                PlanStep(
                    step_number=1,
                    description="Calculate 2+2",
                    tool="calculator",
                    tool_reason="Simple math operation"
                )
            ]
        )

        assert len(plan.steps) == 1
        assert plan.steps[0].tool == "calculator"


class TestExecutionPlanASCII:
    """Tests for ASCII art generation."""

    def test_to_ascii_art_returns_string(self):
        """Test to_ascii_art returns a string."""
        from src.agent.planner import ExecutionPlan, PlanStep

        plan = ExecutionPlan(
            query="Test query",
            goal="Test goal",
            steps=[
                PlanStep(
                    step_number=1,
                    description="Test step",
                    tool="web_search",
                    tool_reason="Test reason"
                )
            ]
        )

        ascii_art = plan.to_ascii_art()
        assert isinstance(ascii_art, str)

    def test_ascii_art_contains_header(self):
        """Test ASCII art contains header."""
        from src.agent.planner import ExecutionPlan, PlanStep

        plan = ExecutionPlan(
            query="Test",
            goal="Test goal",
            steps=[
                PlanStep(1, "Step 1", "web_search", "Reason 1")
            ]
        )

        ascii_art = plan.to_ascii_art()
        assert "EXECUTION PLAN" in ascii_art

    def test_ascii_art_contains_goal(self):
        """Test ASCII art contains goal."""
        from src.agent.planner import ExecutionPlan, PlanStep

        plan = ExecutionPlan(
            query="Test",
            goal="Find the answer",
            steps=[
                PlanStep(1, "Step 1", "web_search", "Reason")
            ]
        )

        ascii_art = plan.to_ascii_art()
        assert "Goal:" in ascii_art

    def test_ascii_art_contains_steps(self):
        """Test ASCII art contains step information."""
        from src.agent.planner import ExecutionPlan, PlanStep

        plan = ExecutionPlan(
            query="Test",
            goal="Goal",
            steps=[
                PlanStep(1, "Search web", "web_search", "Need current info")
            ]
        )

        ascii_art = plan.to_ascii_art()
        assert "Step 1" in ascii_art
        assert "web_search" in ascii_art

    def test_ascii_art_status_icons(self):
        """Test ASCII art shows correct status icons."""
        from src.agent.planner import ExecutionPlan, PlanStep, StepStatus

        plan = ExecutionPlan(
            query="Test",
            goal="Goal",
            steps=[
                PlanStep(1, "Success step", "calculator", "Reason", StepStatus.SUCCESS),
                PlanStep(2, "Failed step", "web_search", "Reason", StepStatus.FAILED),
                PlanStep(3, "Pending step", "wikipedia", "Reason", StepStatus.PENDING)
            ]
        )

        ascii_art = plan.to_ascii_art()
        assert "✓" in ascii_art  # Success
        assert "✗" in ascii_art  # Failed
        assert "○" in ascii_art  # Pending


class TestExecutionPlanTree:
    """Tests for tree visualization."""

    def test_to_tree_returns_string(self):
        """Test to_tree returns a string."""
        from src.agent.planner import ExecutionPlan, PlanStep

        plan = ExecutionPlan(
            query="Test",
            goal="Test goal",
            steps=[
                PlanStep(1, "Step 1", "web_search", "Reason")
            ]
        )

        tree = plan.to_tree()
        assert isinstance(tree, str)

    def test_tree_contains_goal(self):
        """Test tree contains goal."""
        from src.agent.planner import ExecutionPlan, PlanStep

        plan = ExecutionPlan(
            query="Test",
            goal="Find revenue data",
            steps=[
                PlanStep(1, "Step", "web_search", "Reason")
            ]
        )

        tree = plan.to_tree()
        assert "Find revenue data" in tree

    def test_tree_contains_step_info(self):
        """Test tree contains step information."""
        from src.agent.planner import ExecutionPlan, PlanStep, StepStatus

        plan = ExecutionPlan(
            query="Test",
            goal="Goal",
            steps=[
                PlanStep(1, "Search web", "web_search", "Current info needed", StepStatus.SUCCESS)
            ]
        )

        tree = plan.to_tree()
        assert "Step 1" in tree
        assert "Search web" in tree
        assert "web_search" in tree
        assert "PASS" in tree

    def test_tree_shows_tool_reason(self):
        """Test tree shows tool selection reason."""
        from src.agent.planner import ExecutionPlan, PlanStep

        plan = ExecutionPlan(
            query="Test",
            goal="Goal",
            steps=[
                PlanStep(1, "Desc", "calculator", "Math computation required")
            ]
        )

        tree = plan.to_tree()
        assert "Why:" in tree
        assert "Math computation required" in tree


class TestExecutionPlanDict:
    """Tests for dictionary serialization."""

    def test_to_dict_returns_dict(self):
        """Test to_dict returns a dictionary."""
        from src.agent.planner import ExecutionPlan, PlanStep

        plan = ExecutionPlan(
            query="Test",
            goal="Goal",
            steps=[
                PlanStep(1, "Step", "web_search", "Reason")
            ]
        )

        result = plan.to_dict()
        assert isinstance(result, dict)

    def test_to_dict_has_required_keys(self):
        """Test to_dict has all required keys."""
        from src.agent.planner import ExecutionPlan, PlanStep

        plan = ExecutionPlan(
            query="Test query",
            goal="Test goal",
            steps=[
                PlanStep(1, "Step", "web_search", "Reason")
            ]
        )

        result = plan.to_dict()
        assert "query" in result
        assert "goal" in result
        assert "steps" in result
        assert "ascii_plan" in result
        assert "tree_view" in result

    def test_to_dict_steps_serialized(self):
        """Test steps are properly serialized."""
        from src.agent.planner import ExecutionPlan, PlanStep, StepStatus

        plan = ExecutionPlan(
            query="Test",
            goal="Goal",
            steps=[
                PlanStep(1, "Desc", "web_search", "Reason", StepStatus.SUCCESS, "Result")
            ]
        )

        result = plan.to_dict()
        step = result["steps"][0]
        assert step["step_number"] == 1
        assert step["description"] == "Desc"
        assert step["tool"] == "web_search"
        assert step["tool_reason"] == "Reason"
        assert step["status"] == "success"
        assert step["result"] == "Result"


class TestPlanningPrompt:
    """Tests for planning prompt generation."""

    def test_create_planning_prompt(self):
        """Test creating planning prompt."""
        from src.agent.planner import create_planning_prompt

        prompt = create_planning_prompt(
            "What is Salesforce's revenue?",
            ["web_search", "wikipedia", "calculator"]
        )

        assert isinstance(prompt, str)
        assert "What is Salesforce's revenue?" in prompt
        assert "web_search" in prompt
        assert "wikipedia" in prompt
        assert "calculator" in prompt

    def test_planning_prompt_has_json_instruction(self):
        """Test planning prompt asks for JSON."""
        from src.agent.planner import create_planning_prompt

        prompt = create_planning_prompt("Test", ["web_search"])
        assert "JSON" in prompt


class TestParsePlan:
    """Tests for parsing LLM plan response."""

    def test_parse_valid_json(self):
        """Test parsing valid JSON plan."""
        from src.agent.planner import parse_plan_from_llm

        response = '''
        {
            "goal": "Find the answer",
            "steps": [
                {
                    "step_number": 1,
                    "description": "Search the web",
                    "tool": "web_search",
                    "tool_reason": "Get current info"
                }
            ]
        }
        '''

        plan = parse_plan_from_llm(response, "Test query")
        assert plan.goal == "Find the answer"
        assert len(plan.steps) == 1
        assert plan.steps[0].tool == "web_search"

    def test_parse_invalid_json_returns_default(self):
        """Test parsing invalid JSON returns default plan."""
        from src.agent.planner import parse_plan_from_llm

        response = "This is not valid JSON"
        plan = parse_plan_from_llm(response, "Test query")

        assert plan.query == "Test query"
        assert len(plan.steps) >= 1

    def test_parse_embedded_json(self):
        """Test parsing JSON embedded in text."""
        from src.agent.planner import parse_plan_from_llm

        response = '''
        Here is my plan:
        {
            "goal": "Calculate something",
            "steps": [
                {
                    "step_number": 1,
                    "description": "Use calculator",
                    "tool": "calculator",
                    "tool_reason": "Need math"
                }
            ]
        }
        That's my plan.
        '''

        plan = parse_plan_from_llm(response, "Test")
        assert plan.goal == "Calculate something"
        assert plan.steps[0].tool == "calculator"
