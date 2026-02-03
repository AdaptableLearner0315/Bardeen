# Dataset Comparison: v2.0 vs v3.0-pilot

## Overview

This document compares the original B2B dataset (v2.0) with the enhanced pilot dataset (v3.0-pilot) to demonstrate the complexity improvements.

---

## High-Level Comparison

| Metric | v2.0 (Original) | v3.0-pilot (Enhanced) | Change |
|--------|----------------|---------------------|--------|
| **Total Questions** | 24 | 5 (pilot) | -79% (intentional) |
| **Avg Depth** | ~1.5 steps | 5.2 steps | +247% |
| **Max Depth** | 2-3 steps | 7 steps | +133% |
| **Single-Tool Questions** | 70% (17/24) | 0% (0/5) | -100% |
| **Requires Synthesis** | ~25% (6/24) | 100% (5/5) | +300% |
| **Requires Calculation** | ~33% (8/24) | 100% (5/5) | +200% |
| **Hard Questions** | 25% (6/24) | 100% (5/5) | +300% |
| **Avg Min Tools** | 1.0 | 3.8 | +280% |
| **Avg Max Tools** | 2.3 | 6.2 | +170% |

---

## Depth Distribution

### v2.0 (Original)
```
Depth 1 (single tool):  ████████████████  70% (17 questions)
Depth 2 (two tools):    █████             25% (6 questions)
Depth 3+ (multi-step):  ██                5% (1 question)
```

### v3.0-pilot (Enhanced)
```
Depth 1 (single tool):  ∅                 0%
Depth 2 (two tools):    ∅                 0%
Depth 3+ (multi-step):  ██████████████    100% (5 questions)
  - Depth 4:            ████              40% (2 questions)
  - Depth 5:            ██                20% (1 question)
  - Depth 6:            ██                20% (1 question)
  - Depth 7:            ██                20% (1 question)
```

---

## Category Comparison

### v2.0 Distribution (24 questions)
```
Company Research:           ██████  6 questions (25%)
Financial Analysis:         ██████  6 questions (25%)
Competitive Intelligence:   ██████  6 questions (25%)
Action Execution:           ██████  6 questions (25%)
```

### v3.0-pilot Distribution (5 questions)
```
Company Research:           ██      1 question (20%)
Financial Analysis:         ████    2 questions (40%)
Competitive Intelligence:   ██      1 question (20%)
Action Execution:           ██      1 question (20%)
```

---

## Difficulty Distribution

### v2.0 (Original)
```
Easy:    ████████  33% (8 questions)
Medium:  ██████████ 42% (10 questions)
Hard:    ██████     25% (6 questions)
```

### v3.0-pilot (Enhanced)
```
Easy:    ∅         0%
Medium:  ∅         0%
Hard:    ██████████ 100% (5 questions)
```

---

## Side-by-Side Question Examples

### Example 1: Company Research

#### v2.0 (Shallow)
```yaml
Question: "When was Stripe founded and who are the founders?"
Difficulty: easy
Expected Steps: 1
Tools: [web_search OR wikipedia]
Depth: 1

Reasoning:
  1. Search "Stripe founders" → Answer

Why Shallow:
  - Single lookup
  - No synthesis required
  - No calculation
  - Obvious tool choice
```

#### v3.0-pilot (Deep)
```yaml
Question: "Compare founding years of Stripe, Square, and Adyen.
           Which is oldest, and how many years advantage over youngest?"
Difficulty: hard
Expected Steps: 4
Tools: [web_search (×3), calculator]
Depth: 4

Reasoning:
  1. Search "Stripe founding year" → Extract 2010
  2. Search "Square founding year" → Extract 2009
  3. Search "Adyen founding year" → Extract 2006
  4. Calculate age gap: 2010 - 2006 = 4 years
  5. Synthesize: Adyen oldest, 4-year advantage over Stripe

Why Deep:
  - Multi-source lookup (3 separate searches)
  - Cross-referencing required
  - Calculation step
  - Comparative analysis
  - Temporal reasoning
```

---

### Example 2: Financial Analysis

#### v2.0 (Shallow)
```yaml
Question: "What is Apple's current market capitalization?"
Difficulty: easy
Expected Steps: 1
Tools: [web_search OR perplexity_search]
Depth: 1

Reasoning:
  1. Search "Apple market cap" → Answer

Why Shallow:
  - Single metric lookup
  - No comparison
  - No calculation
  - Direct factoid retrieval
```

#### v3.0-pilot (Deep)
```yaml
Question: "Compare NVIDIA and AMD by calculating their P/E ratios.
           Find stock prices, shares outstanding, and earnings.
           Which is more expensive relative to earnings?"
Difficulty: hard
Expected Steps: 7
Tools: [perplexity_search (×4), calculator (×2)]
Depth: 7

Reasoning:
  1. Search "NVIDIA stock price" → $X
  2. Search "NVIDIA EPS" → $Y
  3. Calculate NVIDIA P/E: X/Y = Z
  4. Search "AMD stock price" → $A
  5. Search "AMD EPS" → $B
  6. Calculate AMD P/E: A/B = C
  7. Compare: Which P/E is higher? What does it mean?

Why Deep:
  - Parallel data collection (2 companies)
  - Multiple data points per entity (4 total)
  - Two calculations required
  - Comparative valuation analysis
  - Interpretation of relative valuation
```

---

### Example 3: Action Execution

#### v2.0 (Shallow)
```yaml
Question: "Summarize my unread emails from today"
Difficulty: medium
Expected Steps: 1
Tools: [gmail]
Depth: 1

Reasoning:
  1. Query Gmail for unread emails → Summarize

Why Shallow:
  - Single tool call
  - Direct retrieval
  - No cross-referencing
  - No calculation
```

#### v3.0-pilot (Deep)
```yaml
Question: "Summarize unread emails from past week, calculate daily average.
           Compare to meeting count per day from calendar.
           Do I have an email-to-meeting imbalance?"
Difficulty: hard
Expected Steps: 5
Tools: [gmail, calculator (×2), google_calendar]
Depth: 5

Reasoning:
  1. Query Gmail for unread (7 days) → Count + summary
  2. Calculate email daily avg: count / 7
  3. Query Calendar for meetings this week → Count
  4. Calculate meeting daily avg: count / 7
  5. Compare ratios: Assess communication balance

Why Deep:
  - Multi-source data (email + calendar)
  - Two calculations (daily averages)
  - Cross-referencing required
  - Ratio analysis
  - Qualitative assessment
```

---

## Tool Usage Comparison

### v2.0 Tool Distribution
```
web_search:          ████████████  18 uses (75%)
perplexity_search:   ████          8 uses (33%)
calculator:          ███           6 uses (25%)
wikipedia:           ███           6 uses (25%)
gmail:               ██            4 uses (17%)
google_calendar:     ██            3 uses (13%)
```

### v3.0-pilot Tool Distribution
```
calculator:          ██████████    5 uses (100%)
perplexity_search:   ██████        3 uses (60%)
web_search:          ██            1 use (20%)
gmail:               ██            1 use (20%)
google_calendar:     ██            1 use (20%)
wikipedia:           ∅             0 uses
```

**Key Difference**: 100% of v3.0 questions require calculator (synthesis/calculation), vs only 25% in v2.0.

---

## Reasoning Pattern Analysis

### v2.0 Patterns (Implicit)
```
Single-lookup:            ████████████████  70%
Comparison:               ████              15%
Multi-step:               ██                10%
Calculation:              █                 5%
```

### v3.0-pilot Patterns (Explicit)
```
multi-source_lookup_with_comparison:                    ██  20%
parallel_data_collection_with_comparative_calculation:  ██  20%
verification_calculation_with_industry_benchmarking:    ██  20%
multi-entity_temporal_comparison_with_ranking:          ██  20%
multi-source_data_aggregation_with_ratio_analysis:      ██  20%
```

**Key Difference**: v3.0 explicitly tracks and diversifies reasoning patterns.

---

## Complexity Indicators

### Synthesis Requirement

| Dataset | Requires Synthesis | Percentage |
|---------|-------------------|------------|
| v2.0 | ~6/24 | 25% |
| v3.0-pilot | 5/5 | **100%** |

### Calculation Requirement

| Dataset | Requires Calculation | Percentage |
|---------|---------------------|------------|
| v2.0 | ~8/24 | 33% |
| v3.0-pilot | 5/5 | **100%** |

### Tool Orchestration Decisions

| Dataset | Non-Obvious Tool Choice | Percentage |
|---------|------------------------|------------|
| v2.0 | ~4/24 | 17% |
| v3.0-pilot | 5/5 | **100%** |

---

## Expected Metric Changes

### Pass Rates

| Metric | v2.0 Target | v3.0-pilot Target | Expected Change |
|--------|------------|------------------|----------------|
| pass^5 | ≥ 80% | ≥ 70% | -10% (harder questions) |
| pass^10 | ≥ 85% | ≥ 75% | -10% (harder questions) |

### Depth Metrics

| Metric | v2.0 Target | v3.0-pilot Target | Expected Change |
|--------|------------|------------------|----------------|
| Avg Depth | ≥ 2.0 | ≥ 3.5 | +75% |
| Max Depth | ≥ 4 | ≥ 5 | +25% |
| Avg Step Score | ≥ 20/25 | ≥ 18/25 | -10% (harder evaluation) |

### Quality Metrics

| Metric | v2.0 | v3.0-pilot | Expected Change |
|--------|------|-----------|----------------|
| Tool Precision | ≥ 80% | ≥ 75% | -5% (more complex decisions) |
| Tool Recall | ≥ 70% | ≥ 70% | No change |
| LLM Judge Reasoning Score | ~20/25 | ~22/25 | +10% (visible reasoning) |

---

## JSON Structure Enhancements

### v2.0 Fields
```json
{
  "id": "...",
  "question": "...",
  "category": "...",
  "difficulty": "...",
  "expected_behavior": {
    "tools": [...],
    "tool_order": "...",
    "min_tools": X,
    "max_tools": Y
  },
  "ground_truth": {...},
  "evaluation": {...}
}
```

### v3.0-pilot Added Fields
```json
{
  // All v2.0 fields, PLUS:

  "reasoning_trajectory": {
    "expected_steps": 4-7,
    "step_descriptions": ["Step 1", "Step 2", ...],
    "requires_synthesis": true,
    "requires_calculation": true,
    "reasoning_pattern": "pattern_name"
  },

  "expected_behavior": {
    // All v2.0 fields, PLUS:
    "depth_target": 4-7
  },

  "evaluation": {
    // All v2.0 fields, PLUS:
    "depth_bonus": true
  }
}
```

**Benefit**: Explicit tracking of reasoning trajectories enables:
- Per-step pass^k metrics
- Depth-weighted scoring
- Reasoning pattern analysis
- Better LLM judge evaluation

---

## Why This Matters

### Problem: v2.0 Questions Were Too Easy
- 70% single-tool lookups = trivial for capable agents
- Depth metrics infrastructure existed but was underutilized
- Couldn't distinguish between shallow and deep reasoning
- LLM judge couldn't evaluate multi-step reasoning quality

### Solution: v3.0 Questions Test Real Capabilities
- 100% multi-step (4-7 steps) = genuine reasoning challenge
- Forces tool orchestration decisions (not obvious which tool)
- Requires synthesis across multiple sources
- Tests calculation + analysis capabilities
- LLM judge can evaluate reasoning trajectory quality
- Depth-weighted scoring rewards deeper reasoning

### Impact on Agent Development
- **Before (v2.0)**: Agent could ace eval with simple lookups
- **After (v3.0)**: Agent must demonstrate true multi-step reasoning, planning, and synthesis

---

## Conclusion

The v3.0-pilot dataset represents a **3.5x increase in reasoning depth** and **100% coverage of synthesis/calculation requirements**, transforming the evaluation from testing basic lookup capabilities to testing genuine multi-step reasoning and tool orchestration.

**Key Takeaway**: These aren't just "harder questions" - they're qualitatively different questions that test the agent's ability to plan, execute multi-step reasoning trajectories, and synthesize information across sources.
