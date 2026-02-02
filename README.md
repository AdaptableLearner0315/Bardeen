# Research Assistant Agent

An LLM-powered research assistant with tool calling capabilities, comprehensive evaluation harness, and web dashboard.

## Project Structure

```
bardeen-research-agent/
├── src/
│   ├── agent/              # ✅ COMPLETE
│   │   ├── agent.py
│   │   ├── llm_client.py
│   │   ├── tool_registry.py
│   │   └── tools/
│   │       ├── web_search.py
│   │       ├── wikipedia.py
│   │       └── calculator.py
│   │
│   ├── evaluation/         # ✅ COMPLETE
│   │   ├── harness.py
│   │   ├── visualizer.py
│   │   ├── metrics/
│   │   │   └── pass_k.py
│   │   └── tracers/
│   │       ├── tool_tracer.py
│   │       └── error_tracer.py
│   │
│   ├── dashboard/          # ✅ COMPLETE
│   │   ├── backend/
│   │   │   └── app.py
│   │   └── frontend/
│   │       ├── index.html
│   │       ├── style.css
│   │       └── app.js
│   │
│   └── shared/             # ✅ COMPLETE
│       ├── models.py
│       └── config.py
│
├── data/
│   ├── dataset.json        # ✅ 20 questions
│   └── results/            # Evaluation results stored here
│
├── tests/
├── start_dashboard.py      # ✅ Start web dashboard
├── run_evaluation.py       # ✅ Run evaluation harness
├── test_agent.py           # ✅ Quick testing script
├── requirements.txt
├── .env.example
├── README.md
└── GETTING_STARTED.md      # ✅ Quick start guide
```

## Features

### Evaluation Harness ✅ COMPLETE

The evaluation harness provides:

- **Tool Call Tracing**: Captures every tool call with parameters, results, latency, and errors
- **Error Tracing**: Tracks error recovery attempts and success rates
- **pass^k Metrics**: Implements pass^5 and pass^10 using majority voting (consensus)
- **ASCII Visualization**: Beautiful ASCII art display of reasoning chains
- **Comprehensive Results**: Saves detailed JSON results with timestamps

### Agent Core ✅ COMPLETE

Features:
- Claude 3.5 Sonnet with tool calling
- Three tools: Web Search (Tavily), Wikipedia, Calculator
- Graceful error handling with fallbacks
- Automatic fallback chains (web_search → wikipedia)
- Full integration with evaluation tracers
- Temperature: 0.6 for consistency

### Evaluation Dataset ✅ COMPLETE

20 carefully crafted questions across 4 categories:
- **Geography** (5): Population density, land area comparisons, distance calculations
- **History** (5): Historical dates, events, biographical information
- **Science** (5): Physical constants, planetary facts, biology
- **Current Events** (5): Recent world events, leaders, organizations

Each question includes:
- Expected tools to be used
- Ground truth answer with variants
- Correctness threshold for evaluation
- Whether citations are required

### Web Dashboard ✅ COMPLETE

A beautiful web interface built with FastAPI and vanilla JavaScript:

**Features:**
- **💬 Live Chat**: Interactive chat interface with real-time responses
- **📊 ASCII Trace Visualization**: View tool calls and LLM reasoning in detailed ASCII format
- **📈 Evaluation Viewer**: Browse all evaluation runs with detailed metrics
- **📚 Dataset Explorer**: View all evaluation questions by category
- **⚡ Real-time Status**: Connection status and available tools display
- **🎨 Clean UI**: Gradient design with smooth animations

**Pages:**
1. **Chat Tab**: Ask questions and see tool usage in real-time
2. **Evaluations Tab**: View pass^5, pass^10, consensus metrics, and drill down into individual runs
3. **Dataset Tab**: Browse the 20-question evaluation dataset

## Metrics

### pass^k (Consensus Voting)

Unlike pass@k (which checks if ANY attempt succeeds), pass^k measures **consistency**:

- **pass^5**: Run 5 times, take majority vote, check if correct
- **pass^10**: Run 10 times, take majority vote, check if correct

This tests whether the agent reliably produces the correct answer, not just whether it can occasionally get lucky.

### Additional Metrics

- **Consensus Strength**: % of attempts agreeing on majority answer
- **Tool Selection Accuracy**: Did it call the expected tools?
- **Error Recovery Rate**: % of errors recovered gracefully
- **Average Latency**: Response time across all attempts

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

## Usage

### Run Evaluation

```bash
# Run full evaluation (all 20 questions, 10 attempts each)
python run_evaluation.py

# Run on specific category only
python run_evaluation.py --category geography

# Run on limited set (for testing)
python run_evaluation.py --max-questions 5

# Combine filters
python run_evaluation.py --category history --max-questions 3
```

### Test Agent Interactively

```bash
# Quick test with simple questions
python test_agent.py
```

### Start Dashboard

```bash
# Start the web dashboard
python start_dashboard.py

# Or run directly
python -m src.dashboard.backend.app
```

Then open your browser to: **http://localhost:8000**

The dashboard provides:
- Live chat interface with ASCII trace visualization
- Evaluation results browser (view all runs)
- Dataset explorer
- Interactive API docs at http://localhost:8000/docs

## Development Status

- [x] Evaluation harness infrastructure
- [x] Agent core implementation
- [x] Dataset creation (20 questions across 4 categories)
- [x] Web dashboard with live chat and evaluation viewer
- [ ] End-to-end integration testing

## System Complete! 🎉

All major components are now functional:
1. ✅ **Agent Core**: Claude 3.5 Sonnet with 3 tools (web_search, wikipedia, calculator)
2. ✅ **Evaluation Harness**: pass^5 and pass^10 metrics with tool tracing
3. ✅ **Dataset**: 20 questions across 4 categories
4. ✅ **Web Dashboard**: Interactive UI for chat and evaluation results

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY=your_key_here
export TAVILY_API_KEY=your_key_here  # Optional but recommended

# Test the agent
python test_agent.py
```

## License

MIT
