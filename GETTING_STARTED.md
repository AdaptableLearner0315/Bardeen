# Getting Started with Research Assistant

This guide will help you get the Research Assistant up and running quickly.

## Prerequisites

- Python 3.8 or higher
- Anthropic API key (required)
- Tavily API key (optional but recommended for web search)

## Quick Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Mac/Linux
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Set API Keys

```bash
# Set Anthropic API key (REQUIRED)
export ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Set Tavily API key (OPTIONAL but recommended)
export TAVILY_API_KEY=your_tavily_api_key_here
```

**Note**: Without Tavily, the agent can still use Wikipedia and Calculator, but web search won't be available.

---

## Usage Examples

### Option 1: Web Dashboard (Recommended)

The easiest way to interact with the Research Assistant:

```bash
python start_dashboard.py
```

Then open your browser to: **http://localhost:8000**

**Features:**
- 💬 **Chat Interface**: Ask questions and see real-time responses
- 📊 **ASCII Traces**: View detailed tool execution traces
- 📈 **Evaluation Results**: Browse all evaluation runs
- 📚 **Dataset Explorer**: See all 20 evaluation questions

**Example Questions to Try:**
- "What is the population density of France?"
- "How many years between moon landing and Berlin Wall fall?"
- "What is 125 million plus 51 million?"

---

### Option 2: Quick Testing

Test the agent with simple examples:

```bash
python test_agent.py
```

This will:
1. Test basic agent functionality
2. Run a question that uses tools
3. Display ASCII trace visualization

---

### Option 3: Full Evaluation

Run the complete evaluation on 20 questions:

```bash
# Run full evaluation (200 total agent calls: 20 questions × 10 attempts)
python run_evaluation.py

# Run on just 3 questions (for testing)
python run_evaluation.py --max-questions 3

# Run on specific category
python run_evaluation.py --category geography

# Combine filters
python run_evaluation.py --category history --max-questions 2
```

**What this does:**
- Runs agent 10 times per question
- Calculates pass^5 and pass^10 (majority voting)
- Tracks tool usage and errors
- Generates ASCII traces
- Saves results to `data/results/`

**Example Output:**
```
Overall Results:
  pass^5:  85.0% (17/20 questions)
  pass^10: 90.0% (18/20 questions)
  Avg Consensus: 82%
  Avg Latency: 1250ms
  Error Recovery Rate: 95%
```

---

### Option 4: Python API

Use the agent programmatically:

```python
from src.agent.agent import create_agent

# Create agent
agent = create_agent()

# Ask a question
answer, tool_traces, error_traces = agent.ask(
    "What is the capital of France?",
    reset_conversation=True
)

print(f"Answer: {answer}")
print(f"Tools used: {[t.tool_name for t in tool_traces]}")
```

---

## Understanding the Output

### Tool Traces

When you ask a question, you'll see which tools were used:

```
Tool Calls:
  1. wikipedia
     Params: {title: "France"}
     Status: success
     Latency: 320ms

  2. calculator
     Params: {expression: "67000000 / 643801"}
     Status: success
     Latency: 5ms
```

### ASCII Visualization

Detailed execution trace:

```
START → LLM Reasoning
  │
  ├─→ [1] wikipedia(title="France")
  │    ├─ Latency: 320ms
  │    ├─ Result: {population: 67M, area: 643,801 km²}
  │    └─ Status: ✓ OK
  │
  └─→ FINAL ANSWER: "France has ~104 people per km²"
```

### pass^k Metrics

**pass^5**: Run 5 times, take majority vote
**pass^10**: Run 10 times, take majority vote

Example:
```
Answers: ["104", "104", "105", "104", "104"]
Majority: "104" (4/5 = 80% consensus)
pass^5: ✓ PASS (if "104" is correct)
```

---

## Dashboard Features

### 1. Live Chat Tab

- Type any question
- See real-time responses
- View tool usage
- Expand "View Execution Trace" to see ASCII visualization
- Check "Reset conversation" to clear history

### 2. Evaluations Tab

- View all evaluation runs
- Click on a run to see detailed results
- See pass^5, pass^10, consensus for each question
- View performance by category

### 3. Dataset Tab

- Browse all 20 evaluation questions
- Filter by category
- See expected tools for each question

---

## Troubleshooting

### "Agent not initialized" error

**Cause**: ANTHROPIC_API_KEY not set

**Solution**:
```bash
export ANTHROPIC_API_KEY=your_key_here
```

### "Web search tool not available"

**Cause**: TAVILY_API_KEY not set (this is optional)

**Solution**:
```bash
export TAVILY_API_KEY=your_key_here
```

Or continue without web search - Wikipedia and Calculator will still work.

### Dashboard won't start

**Check**:
1. Are you in the virtual environment? Run `source venv/bin/activate`
2. Are dependencies installed? Run `pip install -r requirements.txt`
3. Is port 8000 already in use? Try a different port:
   ```bash
   uvicorn src.dashboard.backend.app:app --port 8001
   ```

### Evaluation is slow

**Normal behavior**: Each question runs 10 times, with tool calls to external APIs.

**Speed tips**:
- Use `--max-questions 3` for testing
- Use `--category geography` to test just one category
- Web search is slower than Wikipedia/Calculator

---

## Project Structure Overview

```
.
├── src/
│   ├── agent/           # Agent with tool calling
│   ├── evaluation/      # Evaluation harness with pass^k
│   ├── dashboard/       # Web UI
│   └── shared/          # Common models and config
│
├── data/
│   ├── dataset.json     # 20 evaluation questions
│   └── results/         # Evaluation run results
│
├── start_dashboard.py   # Start web UI
├── run_evaluation.py    # Run evaluation
└── test_agent.py        # Quick testing
```

---

## Next Steps

1. **Try the dashboard**: `python start_dashboard.py`
2. **Run a quick eval**: `python run_evaluation.py --max-questions 3`
3. **View results**: Check `data/results/` for detailed JSON outputs
4. **Explore the code**: Start with `src/agent/agent.py`

---

## API Endpoints (for developers)

If you're building on top of this system:

- `POST /api/chat` - Chat with the agent
- `GET /api/evaluations` - List all evaluation runs
- `GET /api/evaluations/{run_id}` - Get detailed evaluation results
- `GET /api/dataset` - Get the evaluation dataset
- `GET /api/health` - Check agent status

Full API docs: http://localhost:8000/docs (when dashboard is running)

---

## Questions?

- Check the main [README.md](README.md) for detailed documentation
- View the dataset: `cat data/dataset.json`
- Inspect evaluation results: `cat data/results/eval_*.json`

Enjoy using the Research Assistant! 🔬
