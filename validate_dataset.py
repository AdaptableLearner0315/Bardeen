#!/usr/bin/env python3
"""Validate the enhanced B2B dataset structure and complexity."""

import json
from pathlib import Path
from collections import Counter, defaultdict

def validate_dataset(dataset_path: str):
    """Validate dataset JSON structure and report complexity metrics."""

    print("=" * 80)
    print("B2B Dataset Validation & Complexity Analysis")
    print("=" * 80)
    print()

    # Load dataset
    with open(dataset_path, 'r') as f:
        data = json.load(f)

    metadata = data['metadata']
    questions = data['questions']

    # Basic validation
    print("✓ Valid JSON structure")
    print(f"✓ Version: {metadata['version']}")
    print(f"✓ Total questions: {metadata['total_questions']}")
    print(f"✓ Expected avg depth: {metadata['avg_expected_depth']}")
    print()

    # Category distribution
    print("Category Distribution:")
    print("-" * 40)
    category_counts = Counter(q['category'] for q in questions)
    for category, count in sorted(category_counts.items()):
        print(f"  {category}: {count} questions")
    print()

    # Difficulty distribution
    print("Difficulty Distribution:")
    print("-" * 40)
    difficulty_counts = Counter(q['difficulty'] for q in questions)
    for difficulty, count in sorted(difficulty_counts.items()):
        print(f"  {difficulty}: {count} questions")
    print()

    # New fields validation
    print("Enhanced Fields Validation:")
    print("-" * 40)
    has_reasoning_trajectory = sum(1 for q in questions if 'reasoning_trajectory' in q)
    has_depth_target = sum(1 for q in questions if 'depth_target' in q.get('expected_behavior', {}))
    has_depth_bonus = sum(1 for q in questions if q.get('evaluation', {}).get('depth_bonus', False))

    print(f"  Questions with reasoning_trajectory: {has_reasoning_trajectory}/{len(questions)}")
    print(f"  Questions with depth_target: {has_depth_target}/{len(questions)}")
    print(f"  Questions with depth_bonus enabled: {has_depth_bonus}/{len(questions)}")
    print()

    # Depth analysis
    print("Reasoning Depth Analysis:")
    print("-" * 40)
    depths = [q['reasoning_trajectory']['expected_steps'] for q in questions
              if 'reasoning_trajectory' in q]
    if depths:
        print(f"  Min expected steps: {min(depths)}")
        print(f"  Max expected steps: {max(depths)}")
        print(f"  Avg expected steps: {sum(depths) / len(depths):.1f}")

    depth_targets = [q['expected_behavior']['depth_target'] for q in questions
                     if 'depth_target' in q.get('expected_behavior', {})]
    if depth_targets:
        print(f"  Avg depth target: {sum(depth_targets) / len(depth_targets):.1f}")
    print()

    # Reasoning patterns
    print("Reasoning Patterns:")
    print("-" * 40)
    patterns = [q['reasoning_trajectory']['reasoning_pattern'] for q in questions
                if 'reasoning_trajectory' in q]
    pattern_counts = Counter(patterns)
    for pattern, count in pattern_counts.items():
        print(f"  {pattern}: {count}")
    print()

    # Tool requirements
    print("Tool Requirements Analysis:")
    print("-" * 40)
    tool_usage = defaultdict(int)
    for q in questions:
        tools = q.get('expected_behavior', {}).get('tools', [])
        for tool in tools:
            tool_usage[tool] += 1

    for tool, count in sorted(tool_usage.items(), key=lambda x: x[1], reverse=True):
        print(f"  {tool}: {count} questions")
    print()

    # Min/max tools
    min_tools = [q['expected_behavior']['min_tools'] for q in questions
                 if 'min_tools' in q.get('expected_behavior', {})]
    max_tools = [q['expected_behavior']['max_tools'] for q in questions
                 if 'max_tools' in q.get('expected_behavior', {})]

    if min_tools:
        print(f"  Avg min_tools: {sum(min_tools) / len(min_tools):.1f}")
    if max_tools:
        print(f"  Avg max_tools: {sum(max_tools) / len(max_tools):.1f}")
    print()

    # Synthesis & calculation requirements
    print("Complexity Requirements:")
    print("-" * 40)
    requires_synthesis = sum(1 for q in questions
                            if q.get('reasoning_trajectory', {}).get('requires_synthesis', False))
    requires_calculation = sum(1 for q in questions
                              if q.get('reasoning_trajectory', {}).get('requires_calculation', False))

    print(f"  Requires synthesis: {requires_synthesis}/{len(questions)} ({requires_synthesis/len(questions)*100:.0f}%)")
    print(f"  Requires calculation: {requires_calculation}/{len(questions)} ({requires_calculation/len(questions)*100:.0f}%)")
    print()

    # Detailed question breakdown
    print("Detailed Question Breakdown:")
    print("=" * 80)
    for q in questions:
        print(f"\n{q['id']}: {q['question'][:70]}...")
        print(f"  Category: {q['category']}")
        print(f"  Difficulty: {q['difficulty']}")

        if 'reasoning_trajectory' in q:
            traj = q['reasoning_trajectory']
            print(f"  Expected steps: {traj['expected_steps']}")
            print(f"  Reasoning pattern: {traj['reasoning_pattern']}")
            print(f"  Requires synthesis: {traj.get('requires_synthesis', False)}")
            print(f"  Requires calculation: {traj.get('requires_calculation', False)}")

        if 'expected_behavior' in q:
            behavior = q['expected_behavior']
            print(f"  Tools: {', '.join(behavior.get('tools', []))}")
            print(f"  Tool range: {behavior.get('min_tools', '?')}-{behavior.get('max_tools', '?')}")
            print(f"  Depth target: {behavior.get('depth_target', 'N/A')}")

        if 'evaluation' in q:
            eval_info = q['evaluation']
            print(f"  Depth bonus: {eval_info.get('depth_bonus', False)}")

    print()
    print("=" * 80)
    print("Validation Complete!")
    print("=" * 80)


if __name__ == "__main__":
    dataset_path = Path(__file__).parent / "data" / "b2b_dataset.json"
    validate_dataset(dataset_path)
