# CLAUDE.md

> **Version**: 2.0.0 | **Last Updated**: 2026-02-01
> **Changelog**: See `.notes/CHANGELOG.md` for version history

This file provides guidance to Claude Code when working with this repository.

## Project Overview

A B2B Account Intelligence Agent with LLM-powered research, adaptive tool calling, and strict response guidelines. Built for the Bardeen.ai interview assignment.

**Key Features:**
- **6 Tools**: Calculator, Wikipedia, Web Search, Perplexity, Gmail, Calendar
- **Auto Mode**: AI detects query complexity and selects appropriate depth
- **Strict Limits**: 50-60 words (normal) or summary + details (deep)
- **Trace Storage**: All tool calls persisted to SQLite

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

# Evaluation
python run_evaluation.py --max-questions 3
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
├── evaluation/            # pass^k harness
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
| `/api/evaluations` | GET | List runs |
| `/api/dataset` | GET | Questions |

### Chat Request/Response
```json
// Request
{"message": "What is Apple's market cap?", "mode": "auto"}

// Response
{"answer": "...", "mode": "normal", "is_auto_detected": true, "latency_ms": 1234}
```

## Evaluation (pass^k)

### Metrics
- **pass^5**: 5 attempts, majority correct
- **pass^10**: 10 attempts, majority correct
- **Consensus**: 60% agreement required

### Commands
```bash
python run_evaluation.py                    # Full (200 calls)
python run_evaluation.py --max-questions 3  # Quick test
python run_evaluation.py --category geography
```

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
