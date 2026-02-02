"""Main evaluation harness for running and analyzing agent performance."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
from dataclasses import asdict

from ..shared.models import (
    AttemptResult, QuestionResult, EvaluationRun,
    DatasetQuestion, ToolCallTrace, ErrorTrace
)
from ..shared.config import Config
from .tracers.tool_tracer import ToolTracer
from .tracers.error_tracer import ErrorTracer
from .tracers.step_tracer import StepTracer, MultiAttemptTracer
from .metrics.pass_k import PassKCalculator, PassKResult
from .metrics.b2b_metrics import (
    B2BMetrics, QuestionEvaluation, calculate_b2b_metrics,
    format_b2b_metrics_report, check_b2b_targets
)
from .metrics.depth_metrics import (
    StepEvaluation, DepthMetrics, AggregateDepthMetrics,
    calculate_per_step_pass_k, calculate_aggregate_depth_metrics,
    format_depth_metrics_report, check_depth_targets
)
from .visualizer import ASCIIVisualizer

# Optional LLM judge import
try:
    from .llm_judge import LLMJudge, JudgeResult, calculate_judge_metrics
    HAS_LLM_JUDGE = True
except ImportError:
    HAS_LLM_JUDGE = False


class EvaluationHarness:
    """
    Orchestrates evaluation runs with tracing and metrics calculation.

    The harness:
    1. Loads dataset questions
    2. Runs agent k times per question (with tracing)
    3. Calculates pass^k metrics
    4. Generates visualizations
    5. Saves detailed results
    """

    def __init__(self, config: Config):
        self.config = config
        self.pass_k_calculator = PassKCalculator(
            consensus_threshold=config.evaluation.consensus_threshold
        )
        self.visualizer = ASCIIVisualizer(width=80)

    def run_evaluation(
        self,
        dataset: List[DatasetQuestion],
        agent_fn: Callable[[str, ToolTracer, ErrorTracer], tuple[str, List[ToolCallTrace], List[ErrorTrace]]],
        similarity_fn: Optional[Callable[[str, str], float]] = None
    ) -> EvaluationRun:
        """
        Run complete evaluation on dataset.

        Args:
            dataset: List of questions to evaluate
            agent_fn: Function that takes (question, tool_tracer, error_tracer) and returns
                     (answer, tool_traces, error_traces)
            similarity_fn: Optional function to compute semantic similarity between answers

        Returns:
            Complete EvaluationRun with all results
        """
        run_id = f"eval_{int(time.time())}"
        k = self.config.evaluation.k_attempts
        k_values = self.config.evaluation.pass_k_values

        print(f"Starting evaluation run: {run_id}")
        print(f"Dataset size: {len(dataset)}")
        print(f"Attempts per question: {k}")
        print(f"pass^k values: {k_values}")
        print()

        question_results = []

        for i, question in enumerate(dataset, 1):
            print(f"[{i}/{len(dataset)}] Evaluating: {question.question[:60]}...")

            question_result = self._evaluate_question(
                question, agent_fn, k, k_values, similarity_fn
            )
            question_results.append(question_result)

            # Print quick summary
            pass_5 = "✓" if question_result.pass_5 else "✗"
            pass_10 = "✓" if question_result.pass_10 else "✗"
            print(f"           pass^5: {pass_5}, pass^10: {pass_10}, "
                  f"consensus: {question_result.consensus_strength:.0%}")
            print()

        # Calculate aggregate metrics
        aggregate_metrics = self._calculate_aggregate_metrics(question_results, k_values)

        eval_run = EvaluationRun(
            run_id=run_id,
            timestamp=datetime.now().isoformat(),
            dataset_size=len(dataset),
            k_attempts=k,
            temperature=self.config.llm.temperature,
            question_results=question_results,
            **aggregate_metrics
        )

        # Save results
        if self.config.evaluation.save_traces:
            self._save_results(eval_run)

        return eval_run

    def _evaluate_question(
        self,
        question: DatasetQuestion,
        agent_fn: Callable,
        k: int,
        k_values: List[int],
        similarity_fn: Optional[Callable]
    ) -> QuestionResult:
        """Run k attempts on a single question and calculate metrics."""
        attempts = []
        all_answers = []

        for attempt_num in range(1, k + 1):
            # Create tracers for this attempt
            tool_tracer = ToolTracer(attempt_number=attempt_num)
            error_tracer = ErrorTracer()

            # Run agent
            start_time = time.time()
            try:
                answer, tool_traces, error_traces = agent_fn(
                    question.question,
                    tool_tracer,
                    error_tracer
                )
            except Exception as e:
                # If agent completely fails, record it
                print(f"  Attempt {attempt_num} failed with exception: {e}")
                answer = f"ERROR: {str(e)}"
                tool_traces = tool_tracer.get_traces()
                error_traces = error_tracer.get_errors()

            end_time = time.time()
            total_latency_ms = (end_time - start_time) * 1000

            # Calculate semantic similarity
            ground_truth_answer = question.ground_truth.get("answer", "")
            if similarity_fn:
                semantic_similarity = similarity_fn(answer, ground_truth_answer)
            else:
                # Fallback to simple string matching
                semantic_similarity = self._simple_similarity(answer, ground_truth_answer)

            threshold = question.evaluation.get("correctness_threshold", 0.85)
            is_correct = semantic_similarity >= threshold

            # Create attempt result
            attempt_result = AttemptResult(
                attempt_number=attempt_num,
                question_id=question.id,
                final_answer=answer,
                tool_calls=tool_traces,
                errors=error_traces,
                total_latency_ms=total_latency_ms,
                is_correct=is_correct,
                semantic_similarity=semantic_similarity,
                timestamp=datetime.now().isoformat()
            )

            attempts.append(attempt_result)
            all_answers.append(answer)

        # Calculate pass^k metrics
        pass_k_results = self.pass_k_calculator.calculate_multi_k(
            answers=all_answers,
            ground_truth=ground_truth_answer,
            k_values=k_values,
            similarity_fn=lambda a, g: similarity_fn(a, g) >= question.evaluation.get("correctness_threshold", 0.85)
                                      if similarity_fn else None
        )

        # Aggregate statistics
        tool_stats = self._aggregate_tool_statistics(attempts)
        error_stats = self._aggregate_error_statistics(attempts)

        question_result = QuestionResult(
            question_id=question.id,
            question_text=question.question,
            category=question.category,
            ground_truth=ground_truth_answer,
            attempts=attempts,
            pass_5=pass_k_results[5].passed if 5 in pass_k_results else False,
            pass_10=pass_k_results[10].passed if 10 in pass_k_results else False,
            majority_answer=pass_k_results[max(k_values)].majority_answer,
            consensus_strength=pass_k_results[max(k_values)].consensus_strength,
            total_tool_calls=tool_stats["total_calls"],
            tool_call_distribution=tool_stats["distribution"],
            tool_error_rates=tool_stats["error_rates"],
            avg_tools_per_attempt=tool_stats["avg_per_attempt"],
            avg_latency_ms=sum(a.total_latency_ms for a in attempts) / len(attempts),
            error_recovery_rate=error_stats["recovery_rate"],
            timestamp=datetime.now().isoformat()
        )

        return question_result

    def _aggregate_tool_statistics(self, attempts: List[AttemptResult]) -> Dict[str, Any]:
        """Aggregate tool usage statistics across attempts."""
        total_calls = sum(len(a.tool_calls) for a in attempts)
        distribution = {}
        tool_errors = {}
        tool_calls_count = {}

        for attempt in attempts:
            for trace in attempt.tool_calls:
                distribution[trace.tool_name] = distribution.get(trace.tool_name, 0) + 1
                tool_calls_count[trace.tool_name] = tool_calls_count.get(trace.tool_name, 0) + 1

                status_val = trace.status.value if hasattr(trace.status, 'value') else trace.status
                if status_val in ["error", "timeout"]:
                    tool_errors[trace.tool_name] = tool_errors.get(trace.tool_name, 0) + 1

        # Calculate error rates
        error_rates = {}
        for tool, calls in tool_calls_count.items():
            errors = tool_errors.get(tool, 0)
            error_rates[tool] = errors / calls if calls > 0 else 0.0

        avg_per_attempt = total_calls / len(attempts) if attempts else 0

        return {
            "total_calls": total_calls,
            "distribution": distribution,
            "error_rates": error_rates,
            "avg_per_attempt": avg_per_attempt
        }

    def _aggregate_error_statistics(self, attempts: List[AttemptResult]) -> Dict[str, Any]:
        """Aggregate error recovery statistics."""
        total_errors = sum(len(a.errors) for a in attempts)
        recovered_errors = sum(sum(1 for e in a.errors if e.recovery_success) for a in attempts)

        recovery_rate = recovered_errors / total_errors if total_errors > 0 else 1.0

        return {
            "total_errors": total_errors,
            "recovered_errors": recovered_errors,
            "recovery_rate": recovery_rate
        }

    def _calculate_aggregate_metrics(
        self,
        question_results: List[QuestionResult],
        k_values: List[int]
    ) -> Dict[str, Any]:
        """Calculate aggregate metrics across all questions."""
        pass_5_rate = sum(1 for q in question_results if q.pass_5) / len(question_results)
        pass_10_rate = sum(1 for q in question_results if q.pass_10) / len(question_results)

        avg_consensus = sum(q.consensus_strength for q in question_results) / len(question_results)
        avg_latency = sum(q.avg_latency_ms for q in question_results) / len(question_results)

        # Error rate calculation
        total_calls = sum(q.total_tool_calls for q in question_results)
        total_errors = sum(
            sum(len(a.errors) for a in q.attempts)
            for q in question_results
        )
        overall_error_rate = total_errors / total_calls if total_calls > 0 else 0.0

        # Error recovery rate
        total_recovered = sum(
            sum(sum(1 for e in a.errors if e.recovery_success) for a in q.attempts)
            for q in question_results
        )
        error_recovery_rate = total_recovered / total_errors if total_errors > 0 else 1.0

        # Category breakdown
        category_metrics = {}
        for question_result in question_results:
            cat = question_result.category
            if cat not in category_metrics:
                category_metrics[cat] = {
                    "count": 0,
                    "pass_5": 0,
                    "pass_10": 0,
                    "avg_consensus": 0.0,
                    "avg_latency": 0.0
                }

            category_metrics[cat]["count"] += 1
            if question_result.pass_5:
                category_metrics[cat]["pass_5"] += 1
            if question_result.pass_10:
                category_metrics[cat]["pass_10"] += 1
            category_metrics[cat]["avg_consensus"] += question_result.consensus_strength
            category_metrics[cat]["avg_latency"] += question_result.avg_latency_ms

        # Convert counts to rates
        for cat, metrics in category_metrics.items():
            count = metrics["count"]
            metrics["pass_5_rate"] = metrics["pass_5"] / count
            metrics["pass_10_rate"] = metrics["pass_10"] / count
            metrics["avg_consensus"] /= count
            metrics["avg_latency"] /= count

        return {
            "overall_pass_5": pass_5_rate,
            "overall_pass_10": pass_10_rate,
            "avg_consensus_strength": avg_consensus,
            "avg_tool_accuracy": 0.0,  # TODO: Calculate based on expected tools
            "avg_latency_ms": avg_latency,
            "overall_error_rate": overall_error_rate,
            "error_recovery_rate": error_recovery_rate,
            "category_metrics": category_metrics
        }

    def _simple_similarity(self, answer: str, ground_truth: str) -> float:
        """Simple string-based similarity (fallback)."""
        answer_norm = answer.lower().strip()
        truth_norm = ground_truth.lower().strip()

        if answer_norm == truth_norm:
            return 1.0
        if truth_norm in answer_norm or answer_norm in truth_norm:
            return 0.9
        return 0.0

    def _save_results(self, eval_run: EvaluationRun):
        """Save evaluation results to JSON file."""
        results_dir = self.config.results_dir
        results_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{eval_run.run_id}.json"
        filepath = results_dir / filename

        # Convert to dict for JSON serialization
        if hasattr(eval_run, 'model_dump'):
            results_dict = eval_run.model_dump()
        elif hasattr(eval_run, 'dict'):
            results_dict = eval_run.dict()
        else:
            results_dict = asdict(eval_run)

        with open(filepath, 'w') as f:
            json.dump(results_dict, f, indent=2)

        print(f"Results saved to: {filepath}")


class B2BEvaluationHarness(EvaluationHarness):
    """
    Extended evaluation harness for B2B-aligned evaluation.

    Adds:
    - LLM-as-Judge evaluation
    - Depth-aware metrics
    - Per-step pass^k consistency
    - B2B-specific metrics
    """

    def __init__(self, config: Config, use_llm_judge: bool = True):
        super().__init__(config)
        self.use_llm_judge = use_llm_judge and HAS_LLM_JUDGE
        if self.use_llm_judge:
            self.llm_judge = LLMJudge()
        self.step_tracers: Dict[str, MultiAttemptTracer] = {}

    def run_b2b_evaluation(
        self,
        dataset: List[DatasetQuestion],
        agent_fn: Callable[[str, ToolTracer, ErrorTracer], tuple[str, List[ToolCallTrace], List[ErrorTrace]]],
        similarity_fn: Optional[Callable[[str, str], float]] = None
    ) -> Dict[str, Any]:
        """
        Run B2B-aligned evaluation with depth tracking and LLM judging.

        Args:
            dataset: List of B2B questions to evaluate
            agent_fn: Agent function
            similarity_fn: Optional similarity function

        Returns:
            Dict with B2B metrics, depth metrics, and detailed results
        """
        run_id = f"b2b_eval_{int(time.time())}"
        k = self.config.evaluation.k_attempts

        print(f"Starting B2B evaluation run: {run_id}")
        print(f"Dataset size: {len(dataset)}")
        print(f"Attempts per question: {k}")
        print(f"LLM Judge: {'Enabled' if self.use_llm_judge else 'Disabled'}")
        print()

        question_evaluations = []
        depth_results = []
        pass_k_depth_results = []
        judge_results = []

        for i, question in enumerate(dataset, 1):
            print(f"[{i}/{len(dataset)}] Evaluating: {question.question[:60]}...")

            # Create multi-attempt tracer for this question
            multi_tracer = MultiAttemptTracer(
                question_id=question.id,
                question=question.question,
                k=k
            )
            self.step_tracers[question.id] = multi_tracer

            # Run k attempts and collect results
            attempts_data = []
            for attempt_num in range(1, k + 1):
                step_tracer = multi_tracer.start_attempt()
                tool_tracer = ToolTracer(attempt_number=attempt_num)
                error_tracer = ErrorTracer()

                start_time = time.time()
                try:
                    answer, tool_traces, error_traces = agent_fn(
                        question.question,
                        tool_tracer,
                        error_tracer
                    )

                    # Record steps from tool traces
                    for idx, trace in enumerate(tool_traces):
                        step_tracer.start_step(
                            tool_name=trace.tool_name,
                            tool_params=trace.params,
                            reasoning=getattr(trace, 'llm_reasoning', '')
                        )
                        step_tracer.end_step(
                            result=trace.result,
                            success=trace.status.value == "success" if hasattr(trace.status, 'value') else True
                        )

                except Exception as e:
                    print(f"  Attempt {attempt_num} failed: {e}")
                    answer = f"ERROR: {str(e)}"
                    tool_traces = tool_tracer.get_traces()
                    error_traces = error_tracer.get_errors()

                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000

                multi_tracer.end_attempt()

                attempts_data.append({
                    "attempt": attempt_num,
                    "answer": answer,
                    "tools_used": [t.tool_name for t in tool_traces],
                    "latency_ms": latency_ms,
                    "depth": len(tool_traces)
                })

            # Calculate depth metrics for this question
            step_traces = multi_tracer.get_all_traces()
            if step_traces:
                # Convert to StepEvaluation format
                step_evals_list = []
                for attempt_traces in step_traces:
                    attempt_step_evals = [
                        StepEvaluation(
                            depth=t.step_number,
                            tool_name=t.tool_name,
                            tool_params=t.tool_params,
                            reasoning=t.reasoning,
                            step_score=20.0,  # Default score
                            latency_ms=t.latency_ms,
                            success=t.success
                        )
                        for t in attempt_traces
                    ]
                    step_evals_list.append(attempt_step_evals)

                # Calculate per-step pass^k
                per_step_results = calculate_per_step_pass_k(step_evals_list, k=k)

                # Create depth metrics
                avg_depth = sum(len(traces) for traces in step_traces) / len(step_traces) if step_traces else 0
                depth_result = DepthMetrics(
                    question_id=question.id,
                    max_depth=max(len(traces) for traces in step_traces) if step_traces else 0,
                    avg_step_score=20.0,
                    depth_weighted_score=20.0 * (1 + 0.1 * (avg_depth - 1)) if avg_depth > 0 else 0
                )
                depth_results.append(depth_result)

            # Get best answer (most common)
            answers = [a["answer"] for a in attempts_data]
            from collections import Counter
            best_answer = Counter(answers).most_common(1)[0][0] if answers else ""
            tools_used = attempts_data[0]["tools_used"] if attempts_data else []
            expected_tools = question.expected_behavior.get("tools", [])

            # LLM Judge evaluation (if enabled)
            score = 60.0  # Default
            passed = False
            dimension_scores = None

            if self.use_llm_judge:
                try:
                    judge_result = self.llm_judge.evaluate(
                        question=question.question,
                        answer=best_answer,
                        tools_used=tools_used,
                        expected_tools=expected_tools,
                        evaluation_criteria=question.evaluation.get("criteria", ""),
                        pass_threshold=60.0
                    )
                    score = judge_result.total_score
                    passed = judge_result.passed
                    dimension_scores = {
                        d.dimension: d.score for d in judge_result.dimension_scores
                    }
                    judge_results.append(judge_result)
                    print(f"           LLM Judge Score: {score:.0f}/100 {'✓' if passed else '✗'}")
                except Exception as e:
                    print(f"           LLM Judge failed: {e}")

            # Create question evaluation
            question_eval = QuestionEvaluation(
                question_id=question.id,
                category=question.category,
                question=question.question,
                answer=best_answer,
                tools_used=tools_used,
                expected_tools=expected_tools,
                score=score,
                passed=passed,
                dimension_scores=dimension_scores
            )
            question_evaluations.append(question_eval)

            print(f"           Depth: {avg_depth:.1f} steps, Pass: {'✓' if passed else '✗'}")
            print()

        # Calculate aggregate metrics
        b2b_metrics = calculate_b2b_metrics(question_evaluations)
        depth_aggregate = calculate_aggregate_depth_metrics(depth_results)

        # Print reports
        print("\n" + "=" * 60)
        print(format_b2b_metrics_report(b2b_metrics))
        print(format_depth_metrics_report(depth_aggregate))

        # Check targets
        b2b_targets = check_b2b_targets(b2b_metrics)
        depth_targets = check_depth_targets(depth_aggregate)

        print("\nTARGET CHECK")
        print("-" * 40)
        all_targets_met = True
        for name, target in {**b2b_targets, **depth_targets}.items():
            status = "✓" if target["met"] else "✗"
            print(f"  {name}: {target['value']:.1f}{target['unit']} "
                  f"(target: {target['target']}{target['unit']}) {status}")
            if not target["met"]:
                all_targets_met = False

        print(f"\nOverall: {'ALL TARGETS MET ✓' if all_targets_met else 'SOME TARGETS NOT MET ✗'}")
        print("=" * 60)

        # Prepare results
        results = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "dataset_type": "b2b",
            "total_questions": len(dataset),

            # B2B metrics
            "overall_pass_rate": b2b_metrics.overall_pass_rate,
            "avg_accuracy_score": b2b_metrics.avg_accuracy_score,
            "tool_precision": b2b_metrics.tool_precision,
            "multi_tool_rate": b2b_metrics.multi_tool_rate,
            "action_success_rate": b2b_metrics.action_success_rate,
            "category_metrics": {
                cat: {
                    "total": m.total_questions,
                    "passed": m.passed,
                    "pass_rate": m.passed / m.total_questions if m.total_questions > 0 else 0,
                    "avg_score": m.avg_score,
                    "tool_precision": m.tool_precision
                }
                for cat, m in b2b_metrics.category_metrics.items()
            },

            # Depth metrics
            "avg_depth": depth_aggregate.avg_depth,
            "max_depth_achieved": depth_aggregate.max_depth_achieved,
            "avg_step_score": depth_aggregate.avg_step_score,
            "pass_k_step1": depth_aggregate.avg_pass_k_step1,
            "pass_k_step2": depth_aggregate.avg_pass_k_step2,
            "pass_k_overall": depth_aggregate.avg_pass_k_overall,

            # Targets
            "targets_met": all_targets_met,
            "b2b_targets": b2b_targets,
            "depth_targets": depth_targets,

            # Detailed results
            "question_results": [
                {
                    "question_id": e.question_id,
                    "category": e.category,
                    "question": e.question,
                    "answer": e.answer[:200],
                    "tools_used": e.tools_used,
                    "expected_tools": e.expected_tools,
                    "score": e.score,
                    "passed": e.passed,
                    "dimension_scores": e.dimension_scores
                }
                for e in question_evaluations
            ]
        }

        # Save results
        if self.config.evaluation.save_traces:
            self._save_b2b_results(results)

        return results

    def _save_b2b_results(self, results: Dict[str, Any]):
        """Save B2B evaluation results."""
        results_dir = self.config.results_dir
        results_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{results['run_id']}.json"
        filepath = results_dir / filename

        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"B2B results saved to: {filepath}")
