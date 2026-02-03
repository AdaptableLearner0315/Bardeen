"""Script to run full evaluation on the research assistant agent."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.agent import create_agent
from src.evaluation.dataset import DatasetLoader
from src.evaluation.harness import EvaluationHarness, B2BEvaluationHarness
from src.evaluation.visualizer import ASCIIVisualizer
from src.evaluation.metrics.pass_k import PassKCalculator, format_pass_k_summary
from src.shared.config import load_config
from src.evaluation.tracers.tool_tracer import ToolTracer
from src.evaluation.tracers.error_tracer import ErrorTracer


def run_evaluation(
    dataset_path: str = "data/dataset.json",
    results_dir: str = "data/results",
    filter_category: str = None,
    max_questions: int = None,
    use_llm_judge: bool = False
):
    """
    Run evaluation on the research assistant.

    Args:
        dataset_path: Path to dataset JSON file
        results_dir: Directory to save results
        filter_category: Optional category filter
        max_questions: Optional limit on number of questions
        use_llm_judge: Use LLM-as-judge for semantic evaluation (default: False)
    """
    print("=" * 80)
    print("Research Assistant Agent - Evaluation")
    print("=" * 80)
    print()

    # Check API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        return

    # Load config
    config = load_config()
    print("Configuration:")
    print(f"  Model: {config.llm.model}")
    print(f"  Temperature: {config.llm.temperature}")
    print(f"  K attempts: {config.evaluation.k_attempts}")
    print(f"  Pass^k values: {config.evaluation.pass_k_values}")
    print(f"  LLM Judge: {'Enabled' if use_llm_judge else 'Disabled'}")
    print()

    # Load dataset
    print(f"Loading dataset from: {dataset_path}")
    loader = DatasetLoader(Path(dataset_path))
    questions = loader.load()

    # Detect if this is a B2B dataset
    b2b_categories = ["company_research", "financial_analysis", "competitive_intelligence", "action_execution", "customer_market"]
    is_b2b_dataset = "b2b" in dataset_path.lower() or any(
        q.category in b2b_categories
        for q in questions[:5]  # Check first 5 questions
    )

    if is_b2b_dataset:
        print("  Detected B2B dataset - will use B2B evaluation harness")
        use_llm_judge = True  # Auto-enable LLM judge for B2B datasets

    # Filter if requested
    if filter_category:
        questions = loader.filter_by_category(filter_category)
        print(f"Filtered to category '{filter_category}': {len(questions)} questions")

    if max_questions:
        questions = questions[:max_questions]
        print(f"Limited to first {max_questions} questions")

    print()
    loader.print_statistics()
    print()

    # Create agent
    print("Initializing agent...")
    agent = create_agent()
    print(f"  Available tools: {', '.join(agent.get_available_tools())}")
    print()

    # Define agent function for harness
    def agent_fn(question_text, tool_tracer, error_tracer):
        """Wrapper function for harness."""
        answer, tool_traces, error_traces = agent.ask(
            question=question_text,
            tracer=tool_tracer,
            error_tracer=error_tracer,
            reset_conversation=True
        )
        return answer, tool_traces, error_traces

    # Run evaluation
    print("Starting evaluation...")
    print("=" * 80)
    print()

    if is_b2b_dataset and use_llm_judge:
        # Use B2B harness with LLM judge
        harness = B2BEvaluationHarness(config, use_llm_judge=True)

        results = harness.run_b2b_evaluation(
            dataset=questions,
            agent_fn=agent_fn
        )

        # Print B2B-specific summary
        print()
        print("=" * 80)
        print("B2B Evaluation Complete!")
        print("=" * 80)
        print()
        print("Overall Results (LLM Judge):")
        print(f"  Pass Rate: {results['overall_pass_rate']:.1%} ({int(results['overall_pass_rate'] * len(questions))}/{len(questions)} questions)")
        print(f"  Avg Score: {results['avg_accuracy_score']:.1f}/100")
        print(f"  Tool Precision: {results['tool_precision']:.1%}")
        print(f"  Multi-Tool Rate: {results['multi_tool_rate']:.1%}")
        print()

        print("Depth Metrics:")
        print(f"  Avg Depth: {results['avg_depth']:.1f} steps")
        print(f"  Max Depth: {results['max_depth_achieved']} steps")
        print(f"  Step Consistency: {results['pass_k_overall']:.1%}")
        print()

        print("By Category:")
        for category, metrics in results['category_metrics'].items():
            print(f"  {category}:")
            print(f"    Pass Rate: {metrics['pass_rate']:.1%}")
            print(f"    Avg Score: {metrics['avg_score']:.1f}/100")
            print(f"    Tool Precision: {metrics['tool_precision']:.1%}")
        print()

        print(f"Detailed results saved to: {config.results_dir}/{results['run_id']}.json")

    else:
        # Use standard harness
        harness = EvaluationHarness(config)

        # Optional: Create LLM-based similarity function
        similarity_fn = None
        if use_llm_judge:
            try:
                from src.evaluation.llm_judge import LLMJudge
                llm_judge = LLMJudge()

                def llm_similarity(answer: str, ground_truth: str) -> float:
                    """Use LLM judge to compute semantic similarity."""
                    result = llm_judge.evaluate(
                        question="(Evaluating answer similarity)",
                        answer=answer,
                        tools_used=[],
                        expected_tools=[],
                        evaluation_criteria=f"The answer should match: {ground_truth}",
                        pass_threshold=60.0
                    )
                    # Return normalized score (0-1)
                    return result.total_score / 100.0

                similarity_fn = llm_similarity
                print("  Using LLM Judge for similarity evaluation")
            except Exception as e:
                print(f"  Warning: Could not initialize LLM Judge: {e}")
                print("  Falling back to string similarity")

        eval_run = harness.run_evaluation(
            dataset=questions,
            agent_fn=agent_fn,
            similarity_fn=similarity_fn
        )

        # Print summary
        print()
        print("=" * 80)
        print("Evaluation Complete!")
        print("=" * 80)
        print()
        print("Overall Results:")
        print(f"  pass^5:  {eval_run.overall_pass_5:.1%} ({int(eval_run.overall_pass_5 * len(questions))}/{len(questions)} questions)")
        print(f"  pass^10: {eval_run.overall_pass_10:.1%} ({int(eval_run.overall_pass_10 * len(questions))}/{len(questions)} questions)")
        print(f"  Avg Consensus: {eval_run.avg_consensus_strength:.1%}")
        print(f"  Avg Latency: {eval_run.avg_latency_ms:.0f}ms")
        print(f"  Error Recovery Rate: {eval_run.error_recovery_rate:.1%}")
        print()

        print("By Category:")
        for category, metrics in eval_run.category_metrics.items():
            print(f"  {category}:")
            print(f"    pass^5:  {metrics['pass_5_rate']:.1%}")
            print(f"    pass^10: {metrics['pass_10_rate']:.1%}")
            print(f"    consensus: {metrics['avg_consensus']:.1%}")
        print()

        print(f"Detailed results saved to: {config.results_dir}/{eval_run.run_id}.json")
        print()

        # Optionally visualize a sample question
        if eval_run.question_results:
            print("=" * 80)
            print("Sample Question Visualization")
            print("=" * 80)

            sample_q = eval_run.question_results[0]
            visualizer = ASCIIVisualizer(width=80)

            # Show question summary
            print(visualizer.visualize_question_summary(sample_q))

            # Show first attempt
            if sample_q.attempts:
                print(visualizer.visualize_attempt(sample_q.attempts[0]))

            # Show consensus analysis
            pass_k_calc = PassKCalculator()
            pass_5_result = pass_k_calc.calculate_pass_k(
                answers=[a.final_answer for a in sample_q.attempts],
                ground_truth=sample_q.ground_truth,
                k=5
            )
            pass_10_result = pass_k_calc.calculate_pass_k(
                answers=[a.final_answer for a in sample_q.attempts],
                ground_truth=sample_q.ground_truth,
                k=10
            )

            print(visualizer.visualize_consensus(sample_q, pass_5_result, pass_10_result))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run evaluation on research assistant")
    parser.add_argument(
        "--dataset",
        default="data/dataset.json",
        help="Path to dataset JSON file"
    )
    parser.add_argument(
        "--category",
        help="Filter to specific category"
    )
    parser.add_argument(
        "--max-questions",
        type=int,
        help="Maximum number of questions to evaluate"
    )
    parser.add_argument(
        "--results-dir",
        default="data/results",
        help="Directory to save results"
    )
    parser.add_argument(
        "--use-llm-judge",
        action="store_true",
        help="Use LLM-as-judge for semantic evaluation (auto-enabled for B2B datasets)"
    )
    parser.add_argument(
        "--no-llm-judge",
        action="store_true",
        help="Disable LLM judge even for B2B datasets"
    )

    args = parser.parse_args()

    # Determine LLM judge setting
    use_llm_judge = args.use_llm_judge
    if args.no_llm_judge:
        use_llm_judge = False

    run_evaluation(
        dataset_path=args.dataset,
        results_dir=args.results_dir,
        filter_category=args.category,
        max_questions=args.max_questions,
        use_llm_judge=use_llm_judge
    )
