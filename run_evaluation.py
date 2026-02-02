"""Script to run full evaluation on the research assistant agent."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.agent import create_agent
from src.evaluation.dataset import DatasetLoader
from src.evaluation.harness import EvaluationHarness
from src.evaluation.visualizer import ASCIIVisualizer
from src.evaluation.metrics.pass_k import PassKCalculator, format_pass_k_summary
from src.shared.config import load_config
from src.evaluation.tracers.tool_tracer import ToolTracer
from src.evaluation.tracers.error_tracer import ErrorTracer


def run_evaluation(
    dataset_path: str = "data/dataset.json",
    results_dir: str = "data/results",
    filter_category: str = None,
    max_questions: int = None
):
    """
    Run evaluation on the research assistant.

    Args:
        dataset_path: Path to dataset JSON file
        results_dir: Directory to save results
        filter_category: Optional category filter
        max_questions: Optional limit on number of questions
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
    print()

    # Load dataset
    print(f"Loading dataset from: {dataset_path}")
    loader = DatasetLoader(Path(dataset_path))
    questions = loader.load()

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

    # Create evaluation harness
    harness = EvaluationHarness(config)

    # Optional: Use semantic similarity for better answer checking
    # For now, we'll use the default string matching
    similarity_fn = None

    # Run evaluation
    print("Starting evaluation...")
    print("=" * 80)
    print()

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
        help="Filter to specific category (geography, history, science, current_events)"
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

    args = parser.parse_args()

    run_evaluation(
        dataset_path=args.dataset,
        results_dir=args.results_dir,
        filter_category=args.category,
        max_questions=args.max_questions
    )
