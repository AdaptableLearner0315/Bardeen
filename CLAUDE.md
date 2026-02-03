# CLAUDE.md

> **Version**: 4.0.0 | **Last Updated**: 2026-02-02  
> **Comprehensive Guide for Claude Code**

This document provides complete guidance for Claude Code when working with the B2B Account Intelligence Agent.

---

## 📋 Quick Reference

- **183 Python files** (94 source, 83 tests)
- **630+ tests passing** (96.6%)
- **6 core tools** + 8 extended tools
- **19 B2B evaluation questions**
- **Multi-agent system** with 5 specialists

---

## Quick Start

```bash
# Install
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key
export PERPLEXITY_API_KEY=your_key  # Optional

# Run
python start_dashboard.py --port 8002  # Dashboard at http://localhost:8002
python test_agent.py                    # Quick test
python run_evaluation.py --max-questions 3  # Evaluation
```

---

## Response Guidelines (Non-Negotiable)

### Normal Mode (50-60 words max)
- Casual tone, like texting a smart friend
- Lead with direct answer
- One paragraph, no bullets unless asked
- Skip formalities ("That's a great question!" ❌)

**Good**: "Apple's market cap is around $3 trillion, making it one of the world's most valuable companies."

### Deep Mode (Summary + Details)
- Under 100 words summary first
- Detailed analysis with citations below
- Triggered by: "research", "analyze", financial queries

### Truncation Prevention (CRITICAL)
- ALWAYS complete responses within token limit
- NEVER start sentences you cannot finish
- Tables max 3-4 rows; use prose for 5+ items
- Recovery: `src/agent/llm_client.py` has `_recover_from_truncation()`

---

## Architecture

```
User → Agent Layer (ResearchAssistant) 
     → LLM Client (Claude 4.5 Sonnet)
     → Tools (Calculator, Wikipedia, WebSearch, Perplexity, Gmail, Calendar)
     → Storage (SQLite)
```

### Directory Structure
```
src/
├── agent/           32 files - Main agent, LLM client, tools
├── evaluation/      16 files - Harness, metrics, tracers
├── multi_agent/     28 files - 5 specialists, routing, guardrails
├── dashboard/        4 files - FastAPI backend + JS frontend
├── storage/          8 files - SQLite + repositories
└── shared/           5 files - Config, models, utils

tests/              83 files - Unit, integration, E2E
scripts/             1 file  - Validation script
```

---

## Tool System

| Tool | Normal | Deep | Timeout | Use Case |
|------|--------|------|---------|----------|
| calculator | ✅ | ✅ | 1s | Math (AST-based, safe) |
| wikipedia | ✅ | ✅ | 5s | Factual lookups |
| web_search | ✅ | ✅ | 10s | DuckDuckGo/Tavily |
| perplexity_search | ❌ | ✅ | 60s | Deep research + citations |
| gmail | ❌ | ✅ | 10s | Email actions |
| google_calendar | ❌ | ✅ | 10s | Calendar actions |

**Auto-Detection** (`src/agent/llm/query_classifier.py`):
- Normal: "What is Python?", "Calculate 25% of 400"
- Deep: "Analyze Tesla financials", "Research cryptocurrency"

**Fallback**: web_search → wikipedia (if search fails)

---

## Evaluation

### B2B Dataset (19 questions - v3.1)
| Category | Count | Difficulty | Depth |
|----------|-------|------------|-------|
| Company Research | 5 | 3 hard, 1 med-hard, 1 med | 4-5 steps |
| Financial Analysis | 5 | 3 hard, 2 med-hard | 4-7 steps |
| Competitive Intel | 5 | 2 hard, 2 med-hard, 1 med | 4-6 steps |
| Strategic Reasoning | 4 | 2 hard, 2 med-hard | 5-6 steps |

### LLM-as-Judge (4 dimensions, 25% each)
1. **Tool Selection** - Right tool for query?
2. **Tool Execution** - Good parameters?
3. **Reasoning** - Logical flow?
4. **Answer Quality** - Factually correct?

### Commands
```bash
# Full B2B evaluation
python run_evaluation.py --dataset data/b2b_dataset.json

# Quick test
python run_evaluation.py --max-questions 3

# By category
python run_evaluation.py --category company_research
```

### Target Metrics
- pass^5: ≥ 80% | pass^10: ≥ 85%
- Tool Precision: ≥ 80% | Recall: ≥ 70%
- Accuracy: ≥ 7.5/10 | Pass Rate: ≥ 75%

---

## Development

### Add New Tool
```python
# src/agent/tools/my_tool.py
from src.agent.tools.base_tool import ToolBase

class MyTool(ToolBase):
    def __init__(self):
        super().__init__(name="my_tool", timeout=10)
    
    def get_tool_definition(self) -> Dict:
        return {"name": "my_tool", "description": "...", "input_schema": {...}}
    
    def _execute_internal(self, **kwargs) -> Any:
        return result  # Errors handled by ToolBase
```

Register in `src/agent/tool_registry.py`:
```python
self.register_tool("my_tool", MyTool())
```

### Configuration
All in `src/shared/config.py`:
- `RESPONSE_LIMITS` - Word/char limits
- `TOKEN_LIMITS` - LLM token allocations
- `TIMEOUTS` - Tool timeouts
- `QUERY_PATTERNS` - Auto-detection regex

---

## Common Tasks

```bash
# Tests
pytest tests/unit/ -v
pytest tests/unit/ --cov=src --cov-report=html

# Validation
python scripts/validate_refactoring.py

# Database
sqlite3 data/agent.db
SELECT * FROM tool_traces ORDER BY timestamp DESC LIMIT 10;

# Results
ls data/results/
cat data/results/b2b_eval_*.json | jq
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Agent not initialized" | `export ANTHROPIC_API_KEY=your_key` |
| "Perplexity unavailable" | `export PERPLEXITY_API_KEY=your_key` (optional) |
| Pydantic error | `pip install anthropic==0.75.0` |
| Port in use | `--port 8003` |
| Tests failing | Check venv active, deps installed, API keys set |

---

## Refactoring Status

### ✅ Phase 1: Foundation
- TracerBase (128 lines), ToolBase (220 lines)
- MetricsCalculator (290 lines), ReportFormatter (320 lines)
- Config centralization (45+ values)
- 23 unit tests (100% passing)

### ✅ Phase 2: Modularization
- LLM module (`src/agent/llm/`)
- PromptManager, QueryClassifier
- Dashboard service layer

### ✅ Phase 5: Validation
- `scripts/validate_refactoring.py`
- 630/652 tests passing (96.6%)

**Details**: See `SYSTEM_DESIGN.md` for refactoring architecture

---

## Key Files

**Core**:
- `src/agent/agent.py` - ResearchAssistant class
- `src/agent/llm_client.py` - Claude API (709 lines)
- `src/agent/tool_registry.py` - Tool management

**Evaluation**:
- `src/evaluation/harness.py` - Evaluation harnesses
- `src/evaluation/llm_judge.py` - 4-dimension scoring
- `src/evaluation/metrics/` - pass^k, depth, B2B metrics

**Multi-Agent**:
- `src/multi_agent/router.py` - Query categorization
- `src/multi_agent/specialists/` - 5 domain experts

**Dashboard**:
- `src/dashboard/backend/app.py` - FastAPI (600+ lines)
- `src/dashboard/frontend/` - HTML, JS, CSS

---

## Performance

| Operation | Latency |
|-----------|---------|
| Calculator | ~5ms |
| Wikipedia | ~300ms |
| Web Search | ~800ms |
| Perplexity | ~2-5s |
| Full eval (19q × 5k) | ~10-15min |

---

## Security

- **Calculator**: AST-based (no exec/eval)
- **API Keys**: Environment variables only
- **Validation**: Pydantic on all endpoints
- **Timeouts**: Prevent hanging requests

---

**For architecture details, see `SYSTEM_DESIGN.md`**  
**For product requirements, see `PRD.md`**
