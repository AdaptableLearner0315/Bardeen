#!/usr/bin/env python3
"""
Verification script for B2B Dataset v3.1
Validates the strategic reasoning category implementation
"""

import json
from collections import Counter


def verify_dataset():
    """Verify dataset structure and content"""
    
    print("=" * 70)
    print("B2B DATASET V3.1 VERIFICATION")
    print("=" * 70)
    print()
    
    # Load dataset
    with open('data/b2b_dataset.json', 'r') as f:
        data = json.load(f)
    
    # Test 1: Metadata
    print("TEST 1: Metadata Validation")
    meta = data['metadata']
    assert meta['version'] == '3.1', f"Version mismatch: {meta['version']}"
    assert meta['total_questions'] == 19, f"Total questions mismatch: {meta['total_questions']}"
    assert len(data['questions']) == 19, f"Actual questions mismatch: {len(data['questions'])}"
    assert 'strategic_reasoning' in meta['categories'], "Missing strategic_reasoning category"
    assert 'action_execution' not in meta['categories'], "action_execution should be removed"
    print("  ✓ Version: 3.1")
    print("  ✓ Total questions: 19")
    print("  ✓ Categories: strategic_reasoning present, action_execution removed")
    print()
    
    # Test 2: Category Distribution
    print("TEST 2: Category Distribution")
    cats = Counter(q['category'] for q in data['questions'])
    assert cats['company_research'] == 5, f"Company research count wrong: {cats['company_research']}"
    assert cats['financial_analysis'] == 5, f"Financial analysis count wrong: {cats['financial_analysis']}"
    assert cats['competitive_intelligence'] == 5, f"Competitive intelligence count wrong: {cats['competitive_intelligence']}"
    assert cats['strategic_reasoning'] == 4, f"Strategic reasoning count wrong: {cats['strategic_reasoning']}"
    assert 'action_execution' not in cats, "action_execution category should be removed"
    print(f"  ✓ company_research: {cats['company_research']}")
    print(f"  ✓ financial_analysis: {cats['financial_analysis']}")
    print(f"  ✓ competitive_intelligence: {cats['competitive_intelligence']}")
    print(f"  ✓ strategic_reasoning: {cats['strategic_reasoning']}")
    print()
    
    # Test 3: Strategic Reasoning Questions
    print("TEST 3: Strategic Reasoning Questions")
    sr_questions = [q for q in data['questions'] if q['category'] == 'strategic_reasoning']
    expected_ids = ['sr_001', 'sr_002', 'sr_003', 'sr_004']
    actual_ids = [q['id'] for q in sr_questions]
    assert actual_ids == expected_ids, f"Strategic reasoning IDs mismatch: {actual_ids}"
    
    for q in sr_questions:
        # Check structure
        assert 'reasoning_trajectory' in q, f"{q['id']} missing reasoning_trajectory"
        assert 'reasoning_pattern' in q['reasoning_trajectory'], f"{q['id']} missing reasoning_pattern"
        assert q['reasoning_trajectory']['expected_steps'] >= 5, f"{q['id']} depth too low"
        
        # Check no auth tools
        tools = q['expected_behavior']['tools']
        assert 'gmail' not in tools, f"{q['id']} uses gmail"
        assert 'google_calendar' not in tools, f"{q['id']} uses google_calendar"
        
        print(f"  ✓ {q['id']}: {q['difficulty']} - {q['reasoning_trajectory']['expected_steps']} steps - {q['reasoning_trajectory']['reasoning_pattern']}")
    print()
    
    # Test 4: No Action Execution Remnants
    print("TEST 4: No Action Execution Remnants")
    ae_questions = [q for q in data['questions'] if q['category'] == 'action_execution']
    assert len(ae_questions) == 0, f"Found {len(ae_questions)} action_execution questions"
    
    ae_ids = [q['id'] for q in data['questions'] if q['id'].startswith('ae_')]
    assert len(ae_ids) == 0, f"Found action_execution IDs: {ae_ids}"
    print("  ✓ No action_execution questions found")
    print("  ✓ No ae_* question IDs found")
    print()
    
    # Test 5: No Authentication Dependencies
    print("TEST 5: No Authentication Dependencies")
    auth_tools = ['gmail', 'google_calendar']
    auth_questions = [q for q in data['questions'] 
                      if any(tool in q['expected_behavior']['tools'] for tool in auth_tools)]
    assert len(auth_questions) == 0, f"Found {len(auth_questions)} questions with auth tools"
    print("  ✓ No gmail usage found")
    print("  ✓ No google_calendar usage found")
    print()
    
    # Test 6: Depth Metrics
    print("TEST 6: Depth Metrics")
    depths = [q['reasoning_trajectory']['expected_steps'] for q in data['questions']]
    sr_depths = [q['reasoning_trajectory']['expected_steps'] for q in sr_questions]
    
    avg_depth = sum(depths) / len(depths)
    sr_avg_depth = sum(sr_depths) / len(sr_depths)
    
    assert avg_depth >= 4.5, f"Average depth too low: {avg_depth}"
    assert sr_avg_depth >= 5.0, f"Strategic reasoning avg depth too low: {sr_avg_depth}"
    assert max(sr_depths) >= 6, f"Strategic reasoning max depth too low: {max(sr_depths)}"
    
    print(f"  ✓ Overall average depth: {avg_depth:.2f} steps")
    print(f"  ✓ Strategic reasoning avg depth: {sr_avg_depth:.2f} steps")
    print(f"  ✓ Strategic reasoning max depth: {max(sr_depths)} steps")
    print()
    
    # Test 7: Difficulty Distribution
    print("TEST 7: Difficulty Distribution")
    diffs = Counter(q['difficulty'] for q in data['questions'])
    sr_diffs = Counter(q['difficulty'] for q in sr_questions)
    
    assert diffs['hard'] >= 10, f"Not enough hard questions: {diffs['hard']}"
    assert sr_diffs['hard'] == 2, f"Strategic reasoning hard count wrong: {sr_diffs['hard']}"
    assert sr_diffs['medium-hard'] == 2, f"Strategic reasoning medium-hard count wrong: {sr_diffs['medium-hard']}"
    
    print(f"  ✓ Total hard: {diffs['hard']}")
    print(f"  ✓ Total medium-hard: {diffs['medium-hard']}")
    print(f"  ✓ Strategic reasoning: {sr_diffs['hard']} hard, {sr_diffs['medium-hard']} medium-hard")
    print()
    
    # Summary
    print("=" * 70)
    print("ALL TESTS PASSED ✓")
    print("=" * 70)
    print()
    print("Dataset v3.1 is ready for evaluation!")
    print()
    print("Next steps:")
    print("  1. Run full evaluation: python run_evaluation.py --dataset data/b2b_dataset.json")
    print("  2. Test strategic reasoning: python run_evaluation.py --category strategic_reasoning")
    print("  3. Review documentation: CATEGORY_REPLACEMENT.md")


if __name__ == '__main__':
    try:
        verify_dataset()
    except AssertionError as e:
        print(f"\n❌ VERIFICATION FAILED: {e}\n")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        exit(1)
