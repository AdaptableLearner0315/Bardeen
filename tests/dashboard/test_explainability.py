"""Tests for explainability features - execution plan, tree, and reasoning display."""

import pytest
from pathlib import Path


class TestExecutionPlanDisplay:
    """Tests for execution plan ASCII art display in frontend."""

    def test_js_handles_execution_plan(self):
        """Test JavaScript handles execution_plan in response."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "execution_plan" in js_content
        assert "data.execution_plan" in js_content

    def test_js_displays_plan_header(self):
        """Test JavaScript displays plan header."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "Execution Plan" in js_content
        assert "plan-header" in js_content

    def test_js_displays_ascii_plan(self):
        """Test JavaScript displays ASCII plan."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "plan.ascii_plan" in js_content
        assert "plan-ascii" in js_content

    def test_css_has_plan_styles(self):
        """Test CSS has execution plan styles."""
        css_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/style.css"

        with open(css_path, 'r') as f:
            css_content = f.read()

        assert ".execution-plan" in css_content
        assert ".plan-header" in css_content
        assert ".plan-ascii" in css_content


class TestTreeVisualization:
    """Tests for step-by-step tree visualization."""

    def test_js_displays_tree(self):
        """Test JavaScript displays execution tree."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "execution-tree" in js_content
        assert "tree-steps" in js_content

    def test_js_displays_tree_goal(self):
        """Test JavaScript displays goal in tree."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "tree-goal" in js_content
        assert "plan.goal" in js_content

    def test_js_displays_step_status(self):
        """Test JavaScript displays step status."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "tree-status" in js_content
        assert "PASS" in js_content
        assert "FAIL" in js_content

    def test_js_displays_tool_reason(self):
        """Test JavaScript displays tool selection reason."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "tree-reason" in js_content
        assert "step.tool_reason" in js_content
        assert "Why:" in js_content

    def test_css_has_tree_styles(self):
        """Test CSS has tree visualization styles."""
        css_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/style.css"

        with open(css_path, 'r') as f:
            css_content = f.read()

        assert ".execution-tree" in css_content
        assert ".tree-step" in css_content
        assert ".tree-connector" in css_content
        assert ".tree-status" in css_content


class TestStepStatusDisplay:
    """Tests for step status (pass/fail) display."""

    def test_js_has_success_status(self):
        """Test JavaScript handles success status."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "'success'" in js_content
        assert "PASS" in js_content

    def test_js_has_failed_status(self):
        """Test JavaScript handles failed status."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "'failed'" in js_content
        assert "FAIL" in js_content

    def test_css_has_status_colors(self):
        """Test CSS has different colors for status."""
        css_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/style.css"

        with open(css_path, 'r') as f:
            css_content = f.read()

        assert ".tree-status.success" in css_content
        assert ".tree-status.error" in css_content
        assert ".tree-status.pending" in css_content


class TestToolReasonDisplay:
    """Tests for tool selection reason display."""

    def test_js_shows_tool_in_step(self):
        """Test JavaScript shows tool name in step."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "step.tool" in js_content
        assert "tree-tool" in js_content

    def test_js_shows_reason_in_step(self):
        """Test JavaScript shows reason in step."""
        js_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/app.js"

        with open(js_path, 'r') as f:
            js_content = f.read()

        assert "step.tool_reason" in js_content

    def test_css_has_reason_styling(self):
        """Test CSS has reason styling."""
        css_path = Path(__file__).parent.parent.parent / "src/dashboard/frontend/style.css"

        with open(css_path, 'r') as f:
            css_content = f.read()

        assert ".tree-reason" in css_content


class TestBackendPlanIntegration:
    """Tests for backend plan integration."""

    def test_chat_response_model_has_plan(self):
        """Test ChatResponse model includes execution_plan."""
        backend_path = Path(__file__).parent.parent.parent / "src/dashboard/backend/app.py"

        with open(backend_path, 'r') as f:
            content = f.read()

        assert "execution_plan" in content
        assert "Optional[Dict[str, Any]]" in content

    def test_backend_uses_ask_with_plan(self):
        """Test backend uses ask_with_plan method."""
        backend_path = Path(__file__).parent.parent.parent / "src/dashboard/backend/app.py"

        with open(backend_path, 'r') as f:
            content = f.read()

        assert "ask_with_plan" in content

    def test_backend_returns_plan_dict(self):
        """Test backend returns plan as dict."""
        backend_path = Path(__file__).parent.parent.parent / "src/dashboard/backend/app.py"

        with open(backend_path, 'r') as f:
            content = f.read()

        assert "execution_plan.to_dict()" in content


class TestLLMClientPlanning:
    """Tests for LLM client planning functionality."""

    def test_llm_client_has_create_plan(self):
        """Test LLM client has create_plan method."""
        llm_path = Path(__file__).parent.parent.parent / "src/agent/llm_client.py"

        with open(llm_path, 'r') as f:
            content = f.read()

        assert "def create_plan" in content

    def test_llm_client_has_chat_with_plan(self):
        """Test LLM client has chat_with_plan method."""
        llm_path = Path(__file__).parent.parent.parent / "src/agent/llm_client.py"

        with open(llm_path, 'r') as f:
            content = f.read()

        assert "def chat_with_plan" in content

    def test_llm_client_imports_planner(self):
        """Test LLM client imports planner module."""
        llm_path = Path(__file__).parent.parent.parent / "src/agent/llm_client.py"

        with open(llm_path, 'r') as f:
            content = f.read()

        assert "from .planner import" in content
        assert "ExecutionPlan" in content


class TestAgentPlanning:
    """Tests for agent planning functionality."""

    def test_agent_has_ask_with_plan(self):
        """Test agent has ask_with_plan method."""
        agent_path = Path(__file__).parent.parent.parent / "src/agent/agent.py"

        with open(agent_path, 'r') as f:
            content = f.read()

        assert "def ask_with_plan" in content

    def test_agent_imports_plan(self):
        """Test agent imports ExecutionPlan."""
        agent_path = Path(__file__).parent.parent.parent / "src/agent/agent.py"

        with open(agent_path, 'r') as f:
            content = f.read()

        assert "ExecutionPlan" in content


class TestExplainabilityIntegration:
    """Integration tests for explainability features."""

    def test_planner_module_importable(self):
        """Test planner module can be imported."""
        from src.agent.planner import ExecutionPlan, PlanStep, StepStatus
        assert ExecutionPlan is not None

    def test_plan_serialization_complete(self):
        """Test plan serialization includes all fields."""
        from src.agent.planner import ExecutionPlan, PlanStep, StepStatus

        plan = ExecutionPlan(
            query="Test query",
            goal="Test goal",
            steps=[
                PlanStep(
                    step_number=1,
                    description="Test step",
                    tool="web_search",
                    tool_reason="Test reason",
                    status=StepStatus.SUCCESS
                )
            ]
        )

        plan_dict = plan.to_dict()

        # Check all required fields present
        assert "query" in plan_dict
        assert "goal" in plan_dict
        assert "steps" in plan_dict
        assert "ascii_plan" in plan_dict
        assert "tree_view" in plan_dict

        # Check step fields
        step = plan_dict["steps"][0]
        assert "step_number" in step
        assert "description" in step
        assert "tool" in step
        assert "tool_reason" in step
        assert "status" in step

    def test_ascii_art_format(self):
        """Test ASCII art has proper box characters."""
        from src.agent.planner import ExecutionPlan, PlanStep

        plan = ExecutionPlan(
            query="Test",
            goal="Goal",
            steps=[PlanStep(1, "Desc", "web_search", "Reason")]
        )

        ascii_art = plan.to_ascii_art()

        # Check box drawing characters
        assert "┌" in ascii_art
        assert "┐" in ascii_art
        assert "└" in ascii_art
        assert "┘" in ascii_art
        assert "─" in ascii_art
        assert "│" in ascii_art

    def test_tree_format(self):
        """Test tree has proper connector characters."""
        from src.agent.planner import ExecutionPlan, PlanStep

        plan = ExecutionPlan(
            query="Test",
            goal="Goal",
            steps=[
                PlanStep(1, "Step 1", "web_search", "Reason 1"),
                PlanStep(2, "Step 2", "calculator", "Reason 2")
            ]
        )

        tree = plan.to_tree()

        # Check tree characters
        assert "├─" in tree or "└─" in tree
        assert "Tool:" in tree
        assert "Why:" in tree
