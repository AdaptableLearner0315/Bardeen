# Category Replacement: Action Execution → Strategic Reasoning

**Date**: 2026-02-02
**Version**: B2B Dataset v3.1
**Change**: Replaced 5 action_execution questions with 4 strategic_reasoning questions

---

## Summary

The B2B evaluation dataset has been updated from v3.0 to v3.1, replacing the `action_execution` category (5 questions) with a new `strategic_reasoning` category (4 questions). This change reduces the total question count from 20 to 19 while improving the dataset's evaluation capabilities.

---

## Motivation

### Problems with Action Execution Category

The `action_execution` category had fundamental limitations:

1. **Authentication Dependency**: All 5 questions (ae_001 through ae_005) required Gmail and/or Google Calendar authentication
2. **Evaluation Blocker**: Cannot run evaluations without working OAuth setup
3. **User Setup Burden**: Requires users to configure and authorize Gmail/Calendar access
4. **Limited Portability**: Difficult to share dataset or run in CI/CD environments
5. **Narrow Focus**: Only tested email/calendar tool usage, not broader reasoning

### Benefits of Strategic Reasoning Category

The new `strategic_reasoning` category addresses these issues:

1. **No Authentication Required**: Uses only public tools (perplexity_search, web_search, calculator, wikipedia)
2. **Evaluation Ready**: Can be run immediately without setup
3. **Higher-Order Reasoning**: Tests causal analysis, forecasting, optimization, and risk assessment
4. **B2B Relevant**: Strategic reasoning is core to B2B intelligence work
5. **Mutually Exclusive**: Distinct from other categories (company research, financial analysis, competitive intelligence)

---

## Category Comparison

| Aspect | Action Execution (v3.0) | Strategic Reasoning (v3.1) |
|--------|------------------------|---------------------------|
| **Question Count** | 5 | 4 |
| **Auth Required** | Yes (Gmail, Calendar) | No |
| **Tools Used** | gmail, google_calendar, calculator | perplexity_search, calculator, web_search |
| **Avg Depth** | 3.8 steps | 5.25 steps |
| **Difficulty** | 2 hard, 2 medium-hard, 1 medium | 2 hard, 2 medium-hard |
| **Reasoning Patterns** | Email/calendar analysis | Causal analysis, forecasting, optimization, risk cascade |
| **B2B Relevance** | Medium (productivity focus) | High (strategic decision-making) |
| **Evaluation Portability** | Low | High |

---

## Strategic Reasoning Questions

The 4 new strategic reasoning questions test different reasoning patterns:

### SR-01: M&A Strategic Rationale Analysis [HARD]
- **Pattern**: Causal analysis with alternative generation
- **Depth**: 5 steps
- **Tests**: Market gap analysis, risk identification, strategy comparison

**Question**: "If a company like Stripe acquires a payment infrastructure provider in Latin America, analyze: (1) What market gap does this fill? (2) What are the 3 biggest risks? (3) What alternative growth strategies could achieve similar goals with less capital?"

### SR-02: Technology Adoption Forecasting [HARD]
- **Pattern**: Forecasting with multi-variable analysis
- **Depth**: 6 steps (highest in category)
- **Tests**: Technology trajectory prediction, variable identification, uncertainty quantification

**Question**: "Quantum computing companies claim they'll disrupt RSA encryption by 2030. Based on current progress, government investment trends, and cryptography migration timelines: Will enterprises realistically need to adopt post-quantum cryptography by 2030? What are the 2-3 key variables that determine this timeline?"

### SR-03: Platform Economics Optimization [MEDIUM-HARD]
- **Pattern**: Optimization with scenario analysis
- **Depth**: 5 steps
- **Tests**: Breakeven calculation, NDR analysis, recession risk assessment

**Question**: "A B2B SaaS company has two pricing strategies: (A) $99/month unlimited users, or (B) $10/user/month. Given typical B2B team sizes are 5-50 people: (1) At what team size does revenue equal out? (2) Which strategy likely has better Net Dollar Retention and why? (3) Which is riskier in a recession?"

### SR-04: Supply Chain Risk Cascade Analysis [MEDIUM-HARD]
- **Pattern**: Cascade analysis with risk mitigation
- **Depth**: 5 steps
- **Tests**: Dependency mapping, timeline estimation, mitigation strategy identification

**Question**: "If Taiwan's semiconductor production drops 30% due to a natural disaster, trace the impact: (1) Which industries get hit first and hardest? (2) What's the likely timeline for price increases to reach consumers? (3) Which companies have the best risk mitigation (geographic diversification, inventory buffers)?"

---

## Updated Dataset Statistics

### Question Distribution
```
Total: 19 questions (down from 20)

company_research:          5 (26%)
financial_analysis:        5 (26%)
competitive_intelligence:  5 (26%)
strategic_reasoning:       4 (21%)
```

### Difficulty Distribution
```
Total: 19 questions

hard:        10 (53%) - up from 50%
medium-hard:  7 (37%) - up from 35%
medium:       2 (11%) - down from 15%

Note: Strategic reasoning has higher average difficulty than action_execution
```

### Depth Metrics
```
Average Expected Depth: 4.7 steps (up from 4.6 in v3.0)
Min Depth: 3 steps
Max Depth: 7 steps
Strategic Reasoning Avg: 5.25 steps (highest of all categories)
```

### Tool Requirements
```
Strategic Reasoning Tools:
✓ perplexity_search (all 4 questions)
✓ calculator (3 out of 4 questions)
✓ web_search (fallback)
✗ gmail (removed)
✗ google_calendar (removed)
```

---

## Why Strategic Reasoning is Mutually Exclusive

Strategic reasoning is distinct from the other 3 categories:

| Category | Focus | Example |
|----------|-------|---------|
| **Company Research** | Gathering specific facts about companies | "What year was Stripe founded?" |
| **Financial Analysis** | Calculating financial metrics | "What is NVIDIA's P/E ratio?" |
| **Competitive Intelligence** | Direct competitor comparisons | "Compare Snowflake vs Databricks market share" |
| **Strategic Reasoning** | Higher-order reasoning about causality, forecasting, trade-offs | "What if Taiwan semiconductor production drops 30%?" |

Strategic reasoning questions:
- Don't focus on researching specific companies (not company research)
- Aren't primarily about calculating financial metrics (not financial analysis)
- Aren't about direct competitor comparisons (not competitive intelligence)
- Test causal thinking, prediction, optimization, and risk analysis (unique focus)

---

## Migration Guide

### For Evaluation Scripts

No code changes required! The evaluation harness (`src/evaluation/harness.py`) already supports arbitrary category names.

**Before (v3.0)**:
```bash
python run_evaluation.py --category action_execution
```

**After (v3.1)**:
```bash
python run_evaluation.py --category strategic_reasoning
```

### For Test Suites

If you have tests that specifically reference `action_execution`, update them:

```python
# Before
categories = ["company_research", "financial_analysis", "competitive_intelligence", "action_execution"]

# After
categories = ["company_research", "financial_analysis", "competitive_intelligence", "strategic_reasoning"]
```

### For Metrics Tracking

Update expected counts:

```python
# Before
assert len(dataset["questions"]) == 20
assert all(category_count == 5 for category_count in category_distribution.values())

# After
assert len(dataset["questions"]) == 19
assert category_distribution == {
    "company_research": 5,
    "financial_analysis": 5,
    "competitive_intelligence": 5,
    "strategic_reasoning": 4
}
```

---

## Impact Assessment

### Improvements ✓

1. **Evaluation Portability**: Dataset can now run anywhere without authentication setup
2. **Higher Reasoning Depth**: Strategic reasoning avg depth (5.25) > action_execution avg depth (3.8)
3. **Better B2B Alignment**: Strategic reasoning is core to B2B intelligence work
4. **Richer Reasoning Patterns**: Tests causal analysis, forecasting, optimization, risk cascade
5. **More Challenging**: Higher difficulty mix (53% hard vs 50% in v3.0)

### Trade-offs ⚠️

1. **Fewer Total Questions**: 19 instead of 20 (user requested 4, not 5)
2. **No Gmail/Calendar Testing**: Can no longer evaluate email/calendar tool capabilities
3. **Slightly Harder**: May lower overall pass rates initially

### Neutral Changes ~

1. **Question Count**: -1 question (19 vs 20) is negligible for statistical significance
2. **Category Balance**: Still well-distributed (5-5-5-4 vs 5-5-5-5)

---

## Validation

### Structural Validation ✓

```bash
# Validate JSON structure
python -c "import json; json.load(open('data/b2b_dataset.json'))"

# Count questions per category
python -c "
import json
from collections import Counter
data = json.load(open('data/b2b_dataset.json'))
cats = Counter(q['category'] for q in data['questions'])
print('Category distribution:', dict(cats))
print('Total questions:', len(data['questions']))
"
```

**Expected Output**:
```
Category distribution: {'company_research': 5, 'financial_analysis': 5, 'competitive_intelligence': 5, 'strategic_reasoning': 4}
Total questions: 19
```

### Content Validation ✓

All strategic reasoning questions have:
- ✓ `reasoning_trajectory` with 5-6 expected steps
- ✓ `depth_target` field specified
- ✓ Clear `reasoning_pattern` (causal_analysis, forecasting, optimization, cascade_analysis)
- ✓ No authentication-dependent tools
- ✓ Multi-step ground truth answers

### Backward Compatibility ✓

- Evaluation harness works without changes
- `--category` flag supports new category name
- Metrics calculation logic unchanged
- No breaking changes to API

---

## Testing the Changes

### Quick Test (3 questions)
```bash
python run_evaluation.py --max-questions 3
```

### Test Strategic Reasoning Category
```bash
python run_evaluation.py --category strategic_reasoning
```

### Full Evaluation (all 19 questions)
```bash
python run_evaluation.py --dataset data/b2b_dataset.json
```

### Validate Dataset Structure
```bash
python validate_dataset.py
```

---

## Rollback Instructions

If you need to revert to v3.0 with action_execution:

```bash
# Restore backup
cp data/b2b_dataset_v3.0_backup.json data/b2b_dataset.json

# Verify restoration
python -c "
import json
data = json.load(open('data/b2b_dataset.json'))
print('Version:', data['metadata']['version'])
print('Total questions:', len(data['questions']))
print('Categories:', data['metadata']['categories'])
"
```

**Note**: Rollback will restore authentication dependencies!

---

## Conclusion

The replacement of `action_execution` with `strategic_reasoning` improves the B2B evaluation dataset by:
- Removing authentication blockers
- Increasing reasoning depth and difficulty
- Testing higher-order strategic thinking
- Maintaining category diversity and mutual exclusivity

The new v3.1 dataset is production-ready and can be evaluated immediately without setup.

---

## Related Files

- **Dataset**: `data/b2b_dataset.json` (v3.1)
- **Backup**: `data/b2b_dataset_v3.0_backup.json`
- **Documentation**: `CLAUDE.md` (updated to v3.1)
- **Evaluation**: `run_evaluation.py` (no changes needed)
- **This Document**: `CATEGORY_REPLACEMENT.md`
