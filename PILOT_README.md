# Enhanced B2B Dataset v3.0-pilot

**Status**: ✅ Phase 1 Complete - Ready for Testing
**Date**: 2026-02-02

---

## Quick Links

- **[Quick Start Guide](PILOT_QUICKSTART.md)** - Start here to run pilot evaluation
- **[Implementation Details](PILOT_IMPLEMENTATION.md)** - Full technical documentation
- **[Dataset Comparison](DATASET_COMPARISON.md)** - Old vs new visual comparison
- **[Implementation Summary](IMPLEMENTATION_SUMMARY.md)** - Executive summary

---

## What Is This?

This is Phase 1 of the Enhanced B2B Dataset project, which replaces shallow single-lookup questions with **5 hard multi-step reasoning questions** (4-7 steps each) to genuinely test agent capabilities.

---

## Key Improvements

| Metric | Before (v2.0) | After (v3.0-pilot) | Improvement |
|--------|--------------|-------------------|-------------|
| **Avg Depth** | ~1.5 steps | 5.2 steps | **+247%** |
| **Multi-Step Questions** | 30% | 100% | **+233%** |
| **Requires Synthesis** | 25% | 100% | **+300%** |
| **Requires Calculation** | 33% | 100% | **+200%** |

**Bottom Line**: 3.5x deeper reasoning required.

---

## The 5 Pilot Questions

1. **Company Research** (depth: 4) - Compare Stripe/Square/Adyen founding years
2. **Financial Analysis** (depth: 7) - Calculate NVIDIA/AMD P/E ratios comparison
3. **Financial Analysis** (depth: 4) - Anthropic burn rate & runway analysis
4. **Competitive Intelligence** (depth: 6) - Snowflake/Databricks/BigQuery market share
5. **Action Execution** (depth: 5) - Email vs meeting volume analysis

---

## Quick Start

### 1. Validate (No API Key Required)
```bash
python validate_dataset.py
```

### 2. Test Single Question
```bash
export ANTHROPIC_API_KEY=your_key
python run_evaluation.py --dataset data/b2b_dataset.json --max-questions 1
```

### 3. Run Full Pilot
```bash
python run_evaluation.py --dataset data/b2b_dataset.json
```

---

## What Changed?

### Old Question Example (Shallow)
```
Q: "When was Stripe founded?"
Steps: 1 (single lookup)
Tools: web_search
```

### New Question Example (Deep)
```
Q: "Compare Stripe, Square, and Adyen founding years.
    Which is oldest? How many years advantage?"
Steps: 4 (multi-source lookup + calculation + synthesis)
Tools: web_search (×3) + calculator
```

---

## Files

### Dataset
- `data/b2b_dataset.json` - **New pilot dataset** (5 hard questions)
- `data/b2b_dataset_v1_backup.json` - Original dataset backup (24 questions)

### Documentation
- `PILOT_QUICKSTART.md` - Quick start guide
- `PILOT_IMPLEMENTATION.md` - Full implementation docs
- `DATASET_COMPARISON.md` - Visual comparison old vs new
- `IMPLEMENTATION_SUMMARY.md` - Executive summary

### Tools
- `validate_dataset.py` - Dataset validation script

---

## Expected Results

When you run the pilot evaluation, expect:

✅ **Good Results**:
- Avg depth: 4.0-5.0 steps
- Max depth: 5-7 steps
- pass^5: 60-75%
- Tool calls: 3-8 per question

⚠️ **Acceptable** (questions are hard):
- pass^5: 50-60% (lower than old 80%+)
- Avg step score: 17-19/25

❌ **Needs Adjustment**:
- Avg depth: <3.0 steps
- pass^5: <50%

---

## Next Steps

### After Pilot Testing
1. Review depth metrics (should be ~4-5)
2. Check pass^5 (should be ≥60%)
3. Verify multi-step reasoning occurs
4. Proceed to Phase 2: Add remaining 15 questions

### Phase 2 (Future)
- Implement 15 more questions (4 per category)
- Total: 20 questions (5 per category)
- Update to v3.0 final
- Generate comparison report

---

## Why This Matters

### Problem
Original dataset had **70% single-tool lookups** - too easy, couldn't test real reasoning.

### Solution
New dataset has **100% multi-step questions (4-7 steps)** - tests planning, synthesis, calculation.

### Impact
- **Before**: Agent passes with basic lookups
- **After**: Agent must demonstrate multi-step reasoning
- **Depth metrics**: Fully utilized (5.2 vs 1.5 steps)
- **LLM judge**: Can evaluate reasoning quality

---

## Help & Troubleshooting

### Need help?
See [PILOT_QUICKSTART.md](PILOT_QUICKSTART.md) for:
- Command reference
- Troubleshooting guide
- Expected output examples
- Interpretation tips

### Common Issues

**API Key Error**:
```bash
export ANTHROPIC_API_KEY=your_key
```

**Perplexity Unavailable**:
```bash
export PERPLEXITY_API_KEY=your_key  # Optional
```

**Auth Failures** (Gmail/Calendar):
- Expected for ae_001 if not configured
- Agent should handle gracefully

---

## Documentation Structure

```
PILOT_README.md                    ← You are here (overview)
├── PILOT_QUICKSTART.md           ← Start testing here
├── PILOT_IMPLEMENTATION.md       ← Technical details
├── DATASET_COMPARISON.md         ← Old vs new comparison
└── IMPLEMENTATION_SUMMARY.md     ← Executive summary
```

**Recommendation**: Start with [PILOT_QUICKSTART.md](PILOT_QUICKSTART.md) for hands-on testing.

---

## Status

- ✅ **Phase 1**: 5 pilot questions implemented
- ⏳ **Testing**: Blocked by API key availability
- 🔜 **Phase 2**: 15 more questions (after pilot validation)

---

## Questions?

1. **How do I run the pilot?** → See [PILOT_QUICKSTART.md](PILOT_QUICKSTART.md)
2. **What changed technically?** → See [PILOT_IMPLEMENTATION.md](PILOT_IMPLEMENTATION.md)
3. **How does it compare to old?** → See [DATASET_COMPARISON.md](DATASET_COMPARISON.md)
4. **What's the summary?** → See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

---

**Ready to start?**

```bash
python validate_dataset.py  # Validate structure (no API key)
python run_evaluation.py --dataset data/b2b_dataset.json --max-questions 1  # Test
```

Good luck! 🚀
