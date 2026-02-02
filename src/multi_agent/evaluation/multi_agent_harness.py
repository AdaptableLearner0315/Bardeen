"""
Multi-Agent Evaluation Harness

End-to-end evaluation of the multi-agent system:
- Routing accuracy
- Agent utilization
- Response quality
- Synthesis effectiveness
- Comparison with single-agent baseline
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from .routing_metrics import RoutingMetrics
from .utilization_metrics import UtilizationMetrics
from ..orchestrator import Orchestrator
from ..guardrails.tool_access import AgentType


@dataclass
class EvaluationQuestion:
    """Question for evaluation with expected routing."""
    id: str
    question: str
    category: str
    expected_agents: List[AgentType]
    expected_answer_contains: List[str] = field(default_factory=list)


@dataclass
class EvaluationResult:
    """Result of evaluating a single question."""
    question_id: str
    question: str
    category: str
    expected_agents: List[AgentType]
    actual_agents: List[AgentType]
    answer: str
    routing_correct: bool
    answer_quality_score: float  # 0-1 based on expected content
    latency_ms: float
    error: Optional[str] = None


@dataclass
class EvaluationSummary:
    """Summary of evaluation run."""
    run_id: str
    timestamp: str
    total_questions: int
    routing_accuracy: float
    answer_quality_avg: float
    average_latency_ms: float
    routing_metrics: Dict[str, Any]
    utilization_metrics: Dict[str, Any]
    category_breakdown: Dict[str, Dict[str, float]]
    results: List[EvaluationResult]


class MultiAgentEvaluationHarness:
    """
    Evaluation harness for the multi-agent system.

    Evaluates:
    - Routing accuracy (correct agent selection)
    - Agent utilization patterns
    - Response quality
    - End-to-end latency
    """

    def __init__(
        self,
        orchestrator: Optional[Orchestrator] = None,
    ):
        """
        Initialize the evaluation harness.

        Args:
            orchestrator: Pre-configured orchestrator (created if None)
        """
        self.orchestrator = orchestrator
        self.routing_metrics = RoutingMetrics()
        self.utilization_metrics = UtilizationMetrics()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the orchestrator."""
        if not self.orchestrator:
            self.orchestrator = Orchestrator()
            await self.orchestrator.initialize()
        self._initialized = True

    async def evaluate_question(
        self,
        question: EvaluationQuestion,
    ) -> EvaluationResult:
        """
        Evaluate a single question.

        Args:
            question: Question with expected routing

        Returns:
            EvaluationResult with accuracy metrics
        """
        start_time = time.time()
        error = None
        answer = ""
        actual_agents = []

        try:
            # Process through orchestrator
            response = await self.orchestrator.process(question.question)

            # Extract actual agents used
            actual_agents = response.routing_decision.agents
            answer = (
                response.synthesized.answer
                if response.synthesized
                else response.final_answer
            )

            # Record routing
            routing_result = self.routing_metrics.record_routing(
                query=question.question,
                expected_agents=question.expected_agents,
                actual_agents=actual_agents,
                category=question.category,
            )

            # Record utilization for each agent
            if response.agent_responses:
                for agent_response in response.agent_responses:
                    self.utilization_metrics.record_agent_invocation(
                        agent_type=agent_response.agent_type,
                        status=agent_response.status,
                        latency_ms=agent_response.latency_ms,
                    )

            # Record query routing pattern
            self.utilization_metrics.record_query_routing(actual_agents)

        except Exception as e:
            error = str(e)

        latency_ms = (time.time() - start_time) * 1000

        # Calculate answer quality
        answer_quality = self._calculate_answer_quality(
            answer, question.expected_answer_contains
        )

        return EvaluationResult(
            question_id=question.id,
            question=question.question,
            category=question.category,
            expected_agents=question.expected_agents,
            actual_agents=actual_agents,
            answer=answer,
            routing_correct=set(question.expected_agents) == set(actual_agents),
            answer_quality_score=answer_quality,
            latency_ms=latency_ms,
            error=error,
        )

    def _calculate_answer_quality(
        self,
        answer: str,
        expected_contains: List[str],
    ) -> float:
        """Calculate answer quality based on expected content."""
        if not expected_contains:
            return 1.0 if answer else 0.0

        if not answer:
            return 0.0

        answer_lower = answer.lower()
        matches = sum(
            1 for term in expected_contains
            if term.lower() in answer_lower
        )
        return matches / len(expected_contains)

    async def run_evaluation(
        self,
        questions: List[EvaluationQuestion],
    ) -> EvaluationSummary:
        """
        Run full evaluation on a set of questions.

        Args:
            questions: List of questions with expected routing

        Returns:
            EvaluationSummary with comprehensive metrics
        """
        if not self._initialized:
            await self.initialize()

        results = []
        category_results = {}

        for question in questions:
            result = await self.evaluate_question(question)
            results.append(result)

            # Track by category
            if question.category not in category_results:
                category_results[question.category] = {
                    "total": 0,
                    "routing_correct": 0,
                    "quality_sum": 0.0,
                    "latency_sum": 0.0,
                }

            cat_stats = category_results[question.category]
            cat_stats["total"] += 1
            if result.routing_correct:
                cat_stats["routing_correct"] += 1
            cat_stats["quality_sum"] += result.answer_quality_score
            cat_stats["latency_sum"] += result.latency_ms

        # Calculate category breakdown
        category_breakdown = {}
        for category, stats in category_results.items():
            total = stats["total"]
            category_breakdown[category] = {
                "routing_accuracy": stats["routing_correct"] / total if total > 0 else 0,
                "avg_quality": stats["quality_sum"] / total if total > 0 else 0,
                "avg_latency_ms": stats["latency_sum"] / total if total > 0 else 0,
            }

        # Generate summary
        total = len(results)
        run_id = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return EvaluationSummary(
            run_id=run_id,
            timestamp=datetime.now().isoformat(),
            total_questions=total,
            routing_accuracy=self.routing_metrics.accuracy,
            answer_quality_avg=sum(r.answer_quality_score for r in results) / total if total > 0 else 0,
            average_latency_ms=sum(r.latency_ms for r in results) / total if total > 0 else 0,
            routing_metrics=self.routing_metrics.to_dict(),
            utilization_metrics=self.utilization_metrics.to_dict(),
            category_breakdown=category_breakdown,
            results=results,
        )

    async def save_results(
        self,
        summary: EvaluationSummary,
        output_dir: str = "data/results",
    ) -> str:
        """
        Save evaluation results to file.

        Args:
            summary: Evaluation summary to save
            output_dir: Directory for output files

        Returns:
            Path to saved file
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        filename = f"multi_agent_{summary.run_id}.json"
        filepath = output_path / filename

        # Convert results to serializable format
        results_dict = {
            "run_id": summary.run_id,
            "timestamp": summary.timestamp,
            "total_questions": summary.total_questions,
            "routing_accuracy": summary.routing_accuracy,
            "answer_quality_avg": summary.answer_quality_avg,
            "average_latency_ms": summary.average_latency_ms,
            "routing_metrics": summary.routing_metrics,
            "utilization_metrics": summary.utilization_metrics,
            "category_breakdown": summary.category_breakdown,
            "results": [
                {
                    "question_id": r.question_id,
                    "question": r.question,
                    "category": r.category,
                    "expected_agents": [a.value for a in r.expected_agents],
                    "actual_agents": [a.value for a in r.actual_agents],
                    "routing_correct": r.routing_correct,
                    "answer_quality_score": r.answer_quality_score,
                    "latency_ms": r.latency_ms,
                    "error": r.error,
                }
                for r in summary.results
            ],
        }

        with open(filepath, "w") as f:
            json.dump(results_dict, f, indent=2)

        return str(filepath)

    @staticmethod
    def load_questions_from_b2b_dataset(
        dataset_path: str,
    ) -> List[EvaluationQuestion]:
        """
        Load evaluation questions from B2B dataset.

        Maps categories to expected agents:
        - company_research -> COMPANY_RESEARCH
        - financial_analysis -> FINANCIAL_ANALYST
        - competitive_intelligence -> COMPETITIVE_INTEL
        - action_execution -> ACTION_EXECUTOR

        Args:
            dataset_path: Path to B2B dataset JSON

        Returns:
            List of EvaluationQuestion objects
        """
        with open(dataset_path) as f:
            data = json.load(f)

        # Category to agent mapping
        category_agent_map = {
            "company_research": [AgentType.COMPANY_RESEARCH],
            "financial_analysis": [AgentType.FINANCIAL_ANALYST],
            "competitive_intelligence": [AgentType.COMPETITIVE_INTEL],
            "action_execution": [AgentType.ACTION_EXECUTOR],
        }

        questions = []
        for q in data.get("questions", []):
            category = q.get("category", "general")
            expected_agents = category_agent_map.get(
                category, [AgentType.GENERAL_FALLBACK]
            )

            # Check for multi-agent patterns in question
            question_text = q.get("question", "").lower()
            if any(word in question_text for word in ["and", "also", "compare", "vs"]):
                # May need multiple agents
                if "market cap" in question_text or "revenue" in question_text:
                    if AgentType.FINANCIAL_ANALYST not in expected_agents:
                        expected_agents.append(AgentType.FINANCIAL_ANALYST)
                if "competitor" in question_text or "compare" in question_text:
                    if AgentType.COMPETITIVE_INTEL not in expected_agents:
                        expected_agents.append(AgentType.COMPETITIVE_INTEL)

            questions.append(
                EvaluationQuestion(
                    id=q.get("id", f"q_{len(questions)}"),
                    question=q.get("question", ""),
                    category=category,
                    expected_agents=expected_agents,
                    expected_answer_contains=q.get("evaluation", {}).get(
                        "expected_content", []
                    ),
                )
            )

        return questions
