# Quick Start Guide: Pilot Evaluation

**Dataset**: v3.0-pilot (5 hard questions with multi-step reasoning)
**Status**: Ready for testing

---

## Prerequisites

### Required Environment Variables
```bash
export ANTHROPIC_API_KEY=your_anthropic_api_key
```

### Optional (for deep mode questions)
```bash
export PERPLEXITY_API_KEY=your_perplexity_api_key
```

---

## Quick Commands

### 1. Validate Dataset Structure (No API Key Needed)
```bash
# Comprehensive validation report
python validate_dataset.py

# Quick JSON check
python -c "import json; data = json.load(open('data/b2b_dataset.json')); print(f'✓ {len(data[\"questions\"])} questions loaded')"
```

### 2. Test Single Question (Fastest)
```bash
# Run just 1 question to verify everything works
python run_evaluation.py --dataset data/b2b_dataset.json --max-questions 1
```

**Expected Output**:
- Question evaluation with tool traces
- Depth metrics (should show depth 4-7)
- pass^5 and pass^10 results
- Consensus strength

### 3. Run Full Pilot (5 Questions)
```bash
# Standard evaluation
python run_evaluation.py --dataset data/b2b_dataset.json

# With LLM judge (if available)
python run_evaluation.py --dataset data/b2b_dataset.json --use-judge
```

**Expected Runtime**: ~5-10 minutes (5 questions × 5 attempts × ~30 sec/attempt)

### 4. Run Specific Category
```bash
# Financial analysis only (2 questions)
python run_evaluation.py --dataset data/b2b_dataset.json --category financial_analysis

# Company research only (1 question)
python run_evaluation.py --dataset data/b2b_dataset.json --category company_research
```

---

## What to Check in Results

### 1. Depth Metrics ✅
**Target**: Avg depth ~4-5 steps

Look for in output:
```
Depth Metrics:
  Max Depth: 5-7 (should be higher than old ~2-3)
  Avg Depth: 4.0-5.0 (should be higher than old ~1.5)
  Avg Step Score: 17-20/25
  Depth-Weighted Score: 23-28
```

### 2. Pass Rates ⚠️
**Target**: pass^5 ≥ 60-70% (lower than v2.0 due to difficulty)

Look for:
```
pass^5: 60-75% (may be lower than old 80%+)
pass^10: 70-80% (may be lower than old 85%+)
Consensus: 70-85%
```

**Note**: Lower pass rates are expected and acceptable for harder questions.

### 3. Tool Usage 🔧
**Expected**: Multiple tool calls per question (3-8 total)

Look for:
```
Tool Traces:
  - web_search or perplexity_search (multiple calls)
  - calculator (for calculations)
  - gmail/google_calendar (for action_execution question)
```

### 4. LLM Judge Scores (If Enabled) 📊
**Target**: Reasoning dimension should improve

Look for:
```
LLM Judge Evaluation:
  Tool Selection: 20-23/25
  Tool Execution: 20-23/25
  Reasoning: 22-25/25 (should be higher - visible multi-step reasoning)
  Answer Quality: 18-22/25
```

---

## Comparing Old vs New

### Run Old Dataset (for comparison)
```bash
# Run 5 questions from old dataset
python run_evaluation.py --dataset data/b2b_dataset_v1_backup.json --max-questions 5
```

### Compare Key Metrics
| Metric | Old (v2.0) | New (v3.0-pilot) | Expected Change |
|--------|-----------|------------------|----------------|
| Avg Depth | ~1.5 | ~4.5 | +200% |
| Max Depth | ~2-3 | ~5-7 | +100% |
| pass^5 | ~85% | ~70% | -15% (acceptable) |

**Look For**: Significant increase in depth metrics, slight decrease in pass rates.

---

## Troubleshooting

### Issue: "ANTHROPIC_API_KEY not set"
```bash
export ANTHROPIC_API_KEY=your_key_here
```

### Issue: "Perplexity unavailable"
```bash
# Set key (optional)
export PERPLEXITY_API_KEY=your_key_here

# OR run without perplexity questions
python run_evaluation.py --dataset data/b2b_dataset.json --category company_research
```

### Issue: Email/Calendar authentication fails
This is **expected** for question `ae_001` if Gmail/Calendar aren't configured.

**Expected behavior**: Agent should gracefully handle auth failure and indicate "authentication required".

### Issue: Questions take too long
```bash
# Reduce k attempts for faster testing
python run_evaluation.py --dataset data/b2b_dataset.json --max-questions 1 --k 3
```

---

## Interpretation Guide

### Good Pilot Results ✅
- Avg depth: 4.0+ (shows multi-step reasoning)
- Max depth: 5+ (reaches expected complexity)
- pass^5: 60%+ (consistency on hard questions)
- Reasoning scores: 20+/25 (LLM judge sees good reasoning)

### Acceptable Results ⚠️
- Avg depth: 3.5-4.0 (slightly below target but improving)
- Max depth: 4-5 (good but could be deeper)
- pass^5: 50-60% (lower but questions are genuinely hard)

### Needs Adjustment ❌
- Avg depth: <3.0 (not reaching multi-step potential)
- Max depth: <4 (questions not deep enough)
- pass^5: <50% (questions may be too hard)

---

## Next Steps After Pilot

### If Results Are Good ✅
1. Document pilot metrics in summary report
2. Proceed to Phase 2: Add remaining 15 questions
3. Update CLAUDE.md with final targets

### If Results Need Tuning ⚠️
1. Adjust difficulty: Mix in 1-2 "medium" questions
2. Review tool availability (is perplexity working?)
3. Check if questions are too ambiguous
4. Re-test with adjusted questions

### If Results Are Poor ❌
1. Investigate: Are tool calls failing?
2. Check: Is agent planning multi-step reasoning?
3. Review: Are questions too complex?
4. Consider: Reduce expected depth targets

---

## Sample Output

### Expected Terminal Output (1 Question)
```
================================================================================
Research Assistant Agent - Evaluation
================================================================================

Starting evaluation run: eval_1738540800
Dataset size: 1
Attempts per question: 5
pass^k values: [5, 10]

[1/1] Evaluating: Compare the founding years of Stripe, Square, and Adyen...

  Attempt 1/5: ✓ (depth: 4, tools: 4)
  Attempt 2/5: ✓ (depth: 5, tools: 4)
  Attempt 3/5: ✓ (depth: 4, tools: 4)
  Attempt 4/5: ✓ (depth: 4, tools: 3)
  Attempt 5/5: ✓ (depth: 4, tools: 4)

           pass^5: ✓, pass^10: N/A, consensus: 85%

Depth Metrics:
  Max Depth: 5
  Avg Depth: 4.2
  Avg Step Score: 21.5/25
  Depth-Weighted Score: 30.1

Overall Results:
  Questions Evaluated: 1
  pass^5 Pass Rate: 100%
  Avg Consensus: 85%
  Tool Precision: 85%

Evaluation complete! Results saved to: results/eval_1738540800/
```

---

## Files & Directories

### Dataset Files
- `data/b2b_dataset.json` - Current pilot dataset (5 questions)
- `data/b2b_dataset_v1_backup.json` - Original dataset (24 questions)

### Documentation
- `PILOT_IMPLEMENTATION.md` - Full implementation details
- `DATASET_COMPARISON.md` - Old vs new comparison
- `PILOT_QUICKSTART.md` - This file

### Validation
- `validate_dataset.py` - Dataset structure validator

### Results (Generated)
- `results/eval_*/` - Evaluation run results
- `results/eval_*/summary.json` - Metrics summary
- `results/eval_*/traces.json` - Tool call traces

---

## Key Questions to Answer

After running pilot evaluation:

1. **Depth**: Is avg depth ~4-5 as expected?
2. **Consistency**: Is pass^5 ≥ 60%?
3. **Tools**: Are 3-8 tools being called per question?
4. **Reasoning**: Does LLM judge score reasoning highly?
5. **Synthesis**: Are answers synthesizing multiple sources?
6. **Calculation**: Are calculations correct?

---

## Tips

- **Start Small**: Test with 1 question first to ensure setup works
- **Check Logs**: Review tool traces to see reasoning steps
- **Compare Depth**: Note how depth metrics change vs v2.0
- **Watch Consensus**: High consensus (>80%) = consistent reasoning
- **Review Failures**: If pass^5 < 60%, check which steps fail

---

## Success Checklist

Before proceeding to Phase 2:

- [ ] JSON structure validates correctly
- [ ] Pilot runs without errors
- [ ] Avg depth ≥ 3.5
- [ ] Max depth ≥ 5
- [ ] pass^5 ≥ 60%
- [ ] Tool calls show multi-step reasoning
- [ ] Depth-weighted scoring applies correctly
- [ ] Questions feel appropriately challenging

---

## Getting Help

If issues arise:

1. **Check Environment**: Verify API keys are set
2. **Review Logs**: Check `results/eval_*/traces.json` for errors
3. **Validate Dataset**: Run `python validate_dataset.py`
4. **Test Single Question**: Isolate with `--max-questions 1`
5. **Check Tool Availability**: Ensure perplexity/gmail/calendar are accessible

---

**Ready to start?** Run the single-question test:

```bash
python run_evaluation.py --dataset data/b2b_dataset.json --max-questions 1
```

Good luck! 🚀
