# B2B Account Intelligence Agent

A multi-agent AI system powered by Claude for B2B research, financial analysis, and competitive intelligence.

## Quick Start

### Prerequisites
- Python 3.8+
- Anthropic API key (required)
- Perplexity API key (optional, for deep research)

### Installation

1. Clone the repository
```bash
git clone https://github.com/AdaptableLearner0315/Bardeen.git
cd Bardeen
```

2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up API keys
```bash
export ANTHROPIC_API_KEY=your_anthropic_key_here
export PERPLEXITY_API_KEY=your_perplexity_key_here  # Optional
```

### Run the Application

**Start the web dashboard:**
```bash
python start_dashboard.py --port 8000
```
Then open http://localhost:8000 in your browser.

**Quick test:**
```bash
python test_agent.py
```

**Run evaluation:**
```bash
python run_evaluation.py --max-questions 3
```

## Features

- **6 Core Tools**: Calculator, Wikipedia, Web Search, Perplexity, Gmail, Calendar
- **Multi-Agent System**: 5 specialized agents (Financial, Market, Tech, Strategic, General)
- **B2B Focus**: Company research, financial analysis, competitive intelligence
- **Evaluation Framework**: LLM-as-Judge with 19 B2B test questions
- **Interactive Dashboard**: Real-time query interface with trace visualization

## Project Structure

```
src/
├── agent/           # Main agent, LLM client, tools
├── evaluation/      # Harness, metrics, LLM judge
├── multi_agent/     # Router, specialists, guardrails
├── dashboard/       # FastAPI backend + frontend
└── storage/         # SQLite repositories

tests/              # 630+ tests (96.6% passing)
data/               # Datasets, results, traces
```

## Documentation

- **CLAUDE.md** - Complete guide for Claude Code (183 files, architecture, tools)
- **SYSTEM_DESIGN.md** - System architecture and design patterns
- **PRD.md** - Product requirements and specifications

## Common Commands

```bash
# Run specific test category
pytest tests/unit/ -v

# Run evaluation with full dataset
python run_evaluation.py --dataset data/b2b_dataset.json

# Start dashboard on different port
python start_dashboard.py --port 8002

# Validate refactoring
python scripts/validate_refactoring.py
```

## API Keys Setup (Alternative)

Create a `.env` file in the project root:
```
ANTHROPIC_API_KEY=your_anthropic_key
PERPLEXITY_API_KEY=your_perplexity_key
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Agent not initialized" | Set `ANTHROPIC_API_KEY` environment variable |
| "Port already in use" | Use `--port 8001` or kill process on port 8000 |
| Import errors | Ensure virtual environment is activated |
| Test failures | Run `pytest tests/unit/ -v` to see details |

## Technology Stack

- **LLM**: Claude 4.5 Sonnet (Anthropic)
- **Framework**: FastAPI, SQLite
- **Search**: DuckDuckGo, Tavily, Perplexity
- **Testing**: pytest (630+ tests)
- **Evaluation**: LLM-as-Judge with semantic similarity

## Performance

- **Response Time**: 300ms (simple) to 5s (deep research)
- **Test Coverage**: 96.6% passing
- **Evaluation**: 80%+ pass rate on B2B questions

---

**License**: MIT
**Author**: Sarath Chandra
**Contact**: [GitHub](https://github.com/AdaptableLearner0315/Bardeen)
