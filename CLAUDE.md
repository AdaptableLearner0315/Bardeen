# CLAUDE.md

> **Version**: 3.1.0 | **Last Updated**: 2026-02-02
> **Changelog**: See `.notes/CHANGELOG.md` for version history

This file provides guidance to Claude Code when working with this repository.

## Project Overview

A B2B Account Intelligence Agent with LLM-powered research, adaptive tool calling, and strict response guidelines. Built for the Bardeen.ai interview assignment.

**Key Features:**
- **6 Tools**: Calculator, Wikipedia, Web Search, Perplexity, Gmail, Calendar
- **Auto Mode**: AI detects query complexity and selects appropriate depth
- **Strict Limits**: 50-60 words (normal) or summary + details (deep)
- **Trace Storage**: All tool calls persisted to SQLite
- **B2B Evaluation**: 19 domain-specific questions across 4 categories (v3.1 complete)
- **LLM-as-Judge**: 4-dimension scoring (Tool Selection, Execution, Reasoning, Answer)
- **Depth Metrics**: Per-step pass^k for long-horizon planning evaluation

## Quick Start

```bash
# Setup
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key
export PERPLEXITY_API_KEY=your_key  # Optional, enables deep research

# Run dashboard
python start_dashboard.py --port 8002

# Quick test
python test_agent.py

# Evaluation (B2B dataset)
python run_evaluation.py --max-questions 3
python run_evaluation.py --dataset data/b2b_dataset.json  # Full B2B evaluation
```

## Response Guidelines (Non-Negotiable)

### Normal Mode (50-60 words max)
- Casual tone, like texting a smart friend
- Lead with direct answer
- One paragraph, no bullets unless asked
- Skip formalities and filler

**Good**: "Apple's market cap is around $3 trillion, making it one of the world's most valuable companies."

**Bad**: "That's a great question! Let me help you with that. Apple Inc., the technology company headquartered in Cupertino..." (too long, too formal)

### Deep Mode (Summary + Details)
- Under 100 words summary first
- Detailed analysis with citations below
- Triggered by: "research", "analyze", financial queries, GitHub queries

### CRITICAL: Response Truncation Prevention

**NEVER allow responses to be truncated mid-sentence, mid-table, or mid-list.**

Rules enforced in system prompts (`src/agent/llm_client.py`):
- ALWAYS complete responses within token limit
- If extensive info, PRIORITIZE most important points
- NEVER start sentences you cannot finish
- Tables MUST be complete - use prose for 5+ items
- Max 3-4 table rows; longer comparisons use ranked prose
- End with complete sentences, not mid-word

Recovery mechanism (`_recover_from_truncation`):
1. If `stop_reason == "max_tokens"`, recovery triggers
2. Claude is re-prompted to summarize/paraphrase
3. If still truncated, `_force_minimal_summary` creates 2-3 sentence response
4. Unit tests in `tests/test_response_truncation.py` validate completeness

**Test truncation prevention:**
```bash
pytest tests/test_response_truncation.py -v
```

## Architecture

```
src/
├── agent/
│   ├── agent.py           # ResearchAssistant (main interface)
│   ├── llm_client.py      # Claude API + QueryClassifier + System Prompts
│   ├── tool_registry.py   # Tool management + mode filtering
│   ├── planner.py         # Execution planning
│   ├── core/memory.py     # Short-term + Long-term memory
│   └── tools/
│       ├── calculator.py      # Safe AST math
│       ├── wikipedia.py       # Factual lookups
│       ├── web_search.py      # Tavily fallback
│       ├── duckduckgo_search.py  # Primary search
│       ├── perplexity.py      # Deep research (sonar/sonar-pro)
│       ├── gmail.py           # Email actions
│       └── google_calendar.py # Calendar actions
├── evaluation/
│   ├── harness.py         # EvaluationHarness + B2BEvaluationHarness
│   ├── dataset.py         # Dataset loading
│   ├── visualizer.py      # ASCII visualization
│   ├── llm_judge.py       # LLM-as-Judge (4-dimension scoring)
│   ├── metrics/
│   │   ├── pass_k.py      # pass^k consensus metrics
│   │   ├── b2b_metrics.py # B2B-specific metrics (precision, recall, F1)
│   │   └── depth_metrics.py # Depth-aware & per-step pass^k
│   └── tracers/
│       ├── tool_tracer.py  # Tool call tracing
│       ├── error_tracer.py # Error tracking
│       └── step_tracer.py  # Step-by-step reasoning tracer
├── dashboard/             # FastAPI + Vanilla JS
├── storage/               # SQLite repositories
└── shared/                # Config, models
```

## Tool System

### Mode-Based Availability
| Tool | Normal | Deep | Description |
|------|--------|------|-------------|
| calculator | Yes | Yes | Safe math (AST-based) |
| wikipedia | Yes | Yes | Factual lookups |
| web_search | Yes | Yes | DuckDuckGo/Tavily |
| perplexity_search | No | Yes | Deep research with citations |
| gmail | No | Yes | Email summarization/sending |
| google_calendar | No | Yes | Meeting scheduling |

### Auto-Detection (QueryClassifier)
```python
# Normal mode triggers
"What is Python?"           # Simple "what is"
"Calculate 25% of 400"      # Math
"Who founded Tesla?"        # Simple "who is"

# Deep mode triggers
"Analyze Tesla financials"  # "analyze" keyword
"Research cryptocurrency"   # "research" keyword
"Compare AWS vs GCP"        # Complex comparison
```

### Fallback Chains
```
web_search → wikipedia  (if search fails)
```

## Configuration

```python
# src/shared/config.py
model = "claude-sonnet-4-20250514"
temperature = 0.6
max_tokens = 4096

# Mode settings
normal_mode_max_calls = 5
deep_mode_max_calls = 15
```

### Environment Variables
```bash
ANTHROPIC_API_KEY=required
PERPLEXITY_API_KEY=optional  # Enables deep research
TAVILY_API_KEY=optional      # Fallback search
```

## Memory & Storage

### Short-Term Memory
- Last 20 messages in conversation
- Auto-trimmed when limit exceeded
- Reset with `reset_conversation=True`

### Long-Term Memory (SQLite)
- User preferences and corrections
- Session history
- Critical info auto-extraction

### Trace Storage
All tool calls saved to `tool_traces` table:
```sql
id, session_id, tool_name, input_data, output_data,
status, error_message, latency_ms, timestamp
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Chat with mode selection |
| `/api/health` | GET | Agent status |
| `/api/evaluations` | GET | List evaluation runs |
| `/api/dataset` | GET | Questions (original) |
| `/api/b2b-dataset` | GET | B2B evaluation questions |
| `/api/b2b-evaluations` | GET | B2B evaluation results |

### Chat Request/Response
```json
// Request
{"message": "What is Apple's market cap?", "mode": "auto"}

// Response
{
  "answer": "...",
  "mode": "normal",
  "is_auto_detected": true,
  "latency_ms": 1234,
  "depth_metrics": {
    "max_depth": 2,
    "avg_step_score": 23.5,
    "depth_weighted_score": 85.2
  }
}
```

## Evaluation Framework

### B2B Dataset (19 Questions - v3.1 COMPLETE)

**Status**: Phase 2 complete - 19 production-ready questions with multi-step reasoning trajectories

| Category | Count | Difficulty Mix | Depth Range |
|----------|-------|----------------|-------------|
| Company Research | 5 | 3 hard, 1 medium-hard, 1 medium | 4-5 steps |
| Financial Analysis | 5 | 3 hard, 2 medium-hard | 4-7 steps |
| Competitive Intelligence | 5 | 2 hard, 2 medium-hard, 1 medium | 4-6 steps |
| Strategic Reasoning | 4 | 2 hard, 2 medium-hard | 5-6 steps |

**Dataset Characteristics (v3.1)**:
- **Total Questions**: 19 (5-5-5-4 distribution)
- **Avg Expected Depth**: 4.7 steps (improved from v3.0)
- **Difficulty Distribution**: 53% hard, 37% medium-hard, 11% medium
- **Complexity**: 100% require synthesis, ~70% require calculation
- **New Category**: Strategic reasoning (causal analysis, forecasting, optimization, risk cascade)
- **Change from v3.0**: Replaced action_execution (auth-dependent) with strategic_reasoning (auth-free)

### LLM-as-Judge (4 Dimensions)
| Dimension | Weight | What It Measures |
|-----------|--------|------------------|
| Tool Selection | 25% | Right tool for query type |
| Tool Execution | 25% | Good parameters, correct usage |
| Reasoning | 25% | Explained choices, logical flow |
| Answer Quality | 25% | Factually correct, well-structured |

### Depth-Aware Metrics
| Metric | Description | Old Target | New Target (v3.0) |
|--------|-------------|------------|-------------------|
| Max Depth | Deepest reasoning chain | ≥ 4 | ≥ 5 |
| Avg Depth | Average steps per query | ≥ 2.0 | ≥ 3.5 |
| Avg Step Score | Quality at each step | ≥ 20/25 | ≥ 18/25 |
| pass^5_step1 | First tool consistency | ≥ 70% | ≥ 70% |
| pass^5_step2 | Second tool consistency | ≥ 60% | ≥ 60% |
| Depth-Weighted Score | Quality × depth multiplier | N/A | ≥ 25 |

### Commands
```bash
# B2B evaluation (recommended)
python run_evaluation.py --dataset data/b2b_dataset.json

# Quick test
python run_evaluation.py --max-questions 3

# Category-specific
python run_evaluation.py --category company_research
python run_evaluation.py --category financial_analysis
```

### Metrics Summary
| Metric | Target | Description |
|--------|--------|-------------|
| pass^5 | ≥ 80% | Consensus with 5 attempts |
| pass^10 | ≥ 85% | Consensus with 10 attempts |
| Tool Precision | ≥ 80% | Correct tools / Total used |
| Tool Recall | ≥ 70% | Correct tools / Expected tools |
| Accuracy Score | ≥ 7.5/10 | LLM judge accuracy rating |
| Overall Pass Rate | ≥ 75% | Questions passing all criteria |

## Security

- **Calculator**: AST-based (no exec/eval)
- **API Keys**: Environment variables only
- **Validation**: Pydantic on all endpoints

## Common Issues

| Issue | Fix |
|-------|-----|
| "Agent not initialized" | Set `ANTHROPIC_API_KEY` |
| "Perplexity unavailable" | Set `PERPLEXITY_API_KEY` |
| Pydantic error | `pip install anthropic==0.75.0` |
| Port in use | `--port 8003` |

## Performance

| Operation | Latency |
|-----------|---------|
| Calculator | ~5ms |
| Wikipedia | ~300ms |
| Web Search | ~800ms |
| Perplexity | ~2-5s |
| Typical query | ~1-2s |
| LLM Judge eval | ~3-5s |

## Development

### Adding Tools
```python
# 1. Create in src/agent/tools/
class MyTool:
    def __call__(self, query: str) -> Dict:
        return {"success": True, "result": "..."}

    def get_tool_definition(self) -> Dict:
        return {"name": "my_tool", "description": "...", "input_schema": {...}}

# 2. Register in tool_registry.py
self.register_tool("my_tool", MyTool())
```

### Using the Evaluation Framework
```python
# B2B Evaluation with LLM Judge
from src.evaluation import B2BEvaluationHarness, LLMJudge

harness = B2BEvaluationHarness(agent, llm_judge=LLMJudge())
results = await harness.run_b2b_evaluation(
    dataset_path="data/b2b_dataset.json",
    k=5
)
print(results.b2b_metrics)
print(results.depth_metrics)
```

### Step Tracing
```python
from src.evaluation.tracers import StepTracer

tracer = StepTracer(query="Compare Stripe vs Square")
with tracer.trace_step("perplexity_search", {"query": "Stripe revenue"}):
    result = tool.execute(...)
    tracer.current_step.step_score = 23

depth_metrics = tracer.get_depth_metrics()
```

### Modifying Response Style
Edit `src/agent/llm_client.py`:
- `SYSTEM_PROMPT_NORMAL` - Casual 50-60 word responses
- `SYSTEM_PROMPT_DEEP` - Summary + detailed analysis

## Key Insights

1. **pass^k > pass@k**: Consistency over best-case
2. **Temperature 0.6**: Optimal for consensus
3. **Fallbacks**: Significantly improve reliability
4. **Word limits**: Users prefer concise answers
5. **Auto-detect**: Reduces friction, improves UX
6. **B2B alignment**: Evaluation must match use case
7. **Depth metrics**: Multi-step reasoning is critical for B2B
8. **LLM-as-Judge**: Process matters as much as output
