# SYSTEM DESIGN

> **Version**: 1.0.0 | **Last Updated**: 2026-02-02  
> **B2B Account Intelligence Agent - Technical Architecture**

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Design](#component-design)
3. [Data Flow](#data-flow)
4. [File Structure](#file-structure)
5. [Refactoring Architecture](#refactoring-architecture)
6. [Implementation Details](#implementation-details)

---

## Architecture Overview

### System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface Layer                    │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ Dashboard  │  │  REST API  │  │   CLI      │            │
│  │ (Port 8002)│  │ (/api/*)   │  │(test_agent)│            │
│  └─────┬──────┘  └──────┬─────┘  └──────┬─────┘            │
└────────┼─────────────────┼────────────────┼──────────────────┘
         │                 │                │
┌────────▼─────────────────▼────────────────▼──────────────────┐
│                      Agent Layer                              │
│  ┌─────────────────────────────────────────────────────┐     │
│  │ ResearchAssistant (src/agent/agent.py)             │     │
│  │  • ask() method - Main entry point                 │     │
│  │  • Mode detection (auto/normal/deep)                │     │
│  │  • Conversation history management                  │     │
│  └───────────────────────┬─────────────────────────────┘     │
│                          │                                    │
│  ┌───────────────────────▼─────────────────────────────┐     │
│  │ LLM Client (src/agent/llm_client.py - 709 lines)   │     │
│  │  • Claude 4.5 Sonnet API integration                │     │
│  │  • Tool calling loop (max 15 calls)                 │     │
│  │  • Response recovery (truncation handling)          │     │
│  │  • QueryClassifier → PromptManager                  │     │
│  └───────────────────────┬─────────────────────────────┘     │
│                          │                                    │
│  ┌───────────────────────▼─────────────────────────────┐     │
│  │ Tool Registry (src/agent/tool_registry.py)         │     │
│  │  • Tool availability per mode                       │     │
│  │  • Fallback chains (web_search → wikipedia)         │     │
│  │  • Error handling and recovery                      │     │
│  └───────────────────────┬─────────────────────────────┘     │
└──────────────────────────┼────────────────────────────────────┘
                           │
┌──────────────────────────▼────────────────────────────────────┐
│                       Tool Layer                              │
│  All tools inherit from ToolBase (Phase 1 refactoring)       │
│                                                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │Calculator│ │Wikipedia │ │WebSearch │ │Perplexity│       │
│  │ (AST)    │ │ (Free)   │ │(DuckDuck)│ │ (Deep)   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                                                               │
│  ┌──────────┐ ┌──────────┐                                  │
│  │  Gmail   │ │ Calendar │   (Deep mode only)               │
│  └──────────┘ └──────────┘                                  │
└──────────────────────────┬────────────────────────────────────┘
                           │
┌──────────────────────────▼────────────────────────────────────┐
│                     Storage Layer                             │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ SQLite Database (data/agent.db)                     │    │
│  │  • tool_traces - All tool calls with timing         │    │
│  │  • evaluations - Evaluation run results             │    │
│  │  • conversations - Chat history                     │    │
│  │  • long_term_memory - User preferences              │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ Repositories (Repository Pattern)                   │    │
│  │  • BaseRepository - Common CRUD operations           │    │
│  │  • ToolTraceRepository - Tool call storage           │    │
│  │  • EvaluationRepository - Evaluation results         │    │
│  │  • ConversationRepository - Chat persistence         │    │
│  └──────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              Evaluation & Multi-Agent Systems                │
│  (Parallel to main agent flow)                               │
│                                                               │
│  ┌────────────────────────────────────────────────────┐      │
│  │ Evaluation Harness (src/evaluation/harness.py)    │      │
│  │  • B2BEvaluationHarness (600+ lines)               │      │
│  │  • LLM-as-Judge integration                        │      │
│  │  • pass^k consensus metrics                        │      │
│  └────────────────────────────────────────────────────┘      │
│                                                               │
│  ┌────────────────────────────────────────────────────┐      │
│  │ Multi-Agent System (src/multi_agent/)             │      │
│  │  • Router → 5 Specialists → Synthesizer            │      │
│  │  • Guardrails (input/output validation)            │      │
│  └────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. Agent Layer

#### ResearchAssistant (`src/agent/agent.py`)
**Purpose**: Main user-facing interface

**Key Methods**:
```python
ask(query: str, mode: str = "auto", reset_conversation: bool = False) 
    → tuple[str, List[ToolTrace], List[ErrorTrace]]
```

**Responsibilities**:
- Mode detection (auto → normal/deep based on QueryClassifier)
- Conversation history management (last 20 messages)
- Tool call orchestration via LLM Client
- Trace collection (tool traces, error traces)

**Dependencies**:
- `llm_client.ClaudeLLMClient` - LLM interactions
- `tool_registry.ToolRegistry` - Tool management
- `memory.Memory` - Conversation storage

#### LLM Client (`src/agent/llm_client.py` - 709 lines)
**Purpose**: Claude API communication and tool calling loop

**Key Components**:
- `QueryClassifier` - Auto-detects normal vs deep mode
- `chat()` method - Main tool calling loop (167 lines)
- `_recover_from_truncation()` - Handles truncated responses
- System prompts - NORMAL and DEEP mode prompts

**Tool Calling Loop**:
```
1. Build conversation context
2. Call Claude API with tools
3. If tool_use → Execute tool → Add result to context → Repeat
4. If text response → Extract answer → Return
5. Max 15 iterations to prevent loops
```

**Refactored (Phase 2)**:
- `src/agent/llm/prompts.py` - PromptManager
- `src/agent/llm/query_classifier.py` - QueryClassifier (moved)
- Future: `src/agent/llm/response_recovery.py` - ResponseRecovery

#### Tool Registry (`src/agent/tool_registry.py`)
**Purpose**: Tool management and mode-based availability

**Features**:
- Mode-based filtering (normal: 3 tools, deep: 6+ tools)
- Fallback chains (`web_search → wikipedia`)
- Error handling and retry logic
- Tool definition generation for Claude API

**Fallback Logic**:
```python
def execute_tool_with_fallback(tool_name, params):
    try:
        return primary_tool.execute(params)
    except Exception:
        if fallback_tool:
            return fallback_tool.execute(params)
        raise
```

### 2. Tool Layer

#### ToolBase (`src/agent/tools/base_tool.py`) ⭐ Phase 1
**Purpose**: Abstract base class for all tools

**Standard Interface**:
```python
class ToolBase(ABC):
    def __init__(self, name: str, timeout: int)
    def get_tool_definition(self) -> Dict  # Abstract
    def _execute_internal(self, **kwargs) -> Any  # Abstract
    def __call__(self, **kwargs) -> Dict  # Standard wrapper
```

**Standard Error Handling**:
- TimeoutError → `{"success": False, "error_type": "timeout"}`
- ValueError → `{"success": False, "error_type": "invalid_input"}`
- ConnectionError → `{"success": False, "error_type": "connection_error"}`
- General Exception → `{"success": False, "error_type": "execution_error"}`

**Benefits**:
- Eliminates 20-30 lines of duplicated error handling per tool
- Standardizes result format
- Centralized logging
- Timeout management

#### Tool Implementations

**Calculator** (`src/agent/tools/calculator.py`):
- AST-based evaluation (no eval/exec)
- Supports: +, -, *, /, **, parentheses
- Secure: No variables, functions, or imports

**Wikipedia** (`src/agent/tools/wikipedia.py`):
- Free, no API key required
- Fallback for web_search
- Returns: title, summary, URL

**Web Search** (`src/agent/tools/duckduckgo_search.py` + `web_search.py`):
- DuckDuckGo (free) + Tavily (optional, requires API key)
- Returns: title, snippet, URL per result
- Fallback to Wikipedia on failure

**Perplexity** (`src/agent/tools/perplexity.py`):
- Deep mode only
- Models: sonar, sonar-pro, sonar-reasoning
- Returns: answer with citations

**Gmail** (`src/agent/tools/gmail.py`):
- Deep mode only
- Actions: search, read, send
- OAuth2 authentication

**Google Calendar** (`src/agent/tools/google_calendar.py`):
- Deep mode only
- Actions: list events, create event
- OAuth2 authentication

### 3. Evaluation Layer

#### Evaluation Harness (`src/evaluation/harness.py`)
**Purpose**: Run and evaluate agent performance

**Classes**:
- `EvaluationHarness` - Base harness
- `B2BEvaluationHarness` - B2B-specific with LLM judge

**B2B Evaluation Flow**:
```
1. Load dataset (19 questions)
2. For each question:
   a. Run agent k times (k=5 default)
   b. Collect traces (tools, errors, steps)
   c. Calculate consensus (pass^k)
   d. LLM judge scoring (4 dimensions)
   e. Depth metrics (per-step pass^k)
3. Aggregate metrics
4. Save results to JSON
```

#### LLM-as-Judge (`src/evaluation/llm_judge.py`)
**Purpose**: Automated quality scoring

**4 Dimensions** (25% each):
1. **Tool Selection**: Did it choose the right tools?
2. **Tool Execution**: Were parameters correct?
3. **Reasoning**: Was the logic sound?
4. **Answer Quality**: Is it factually correct?

**Scoring Process**:
```python
for dimension in [tool_selection, execution, reasoning, answer]:
    score = llm_judge.score(question, answer, traces, dimension)
    # Returns 0-25 points
total_score = sum(scores)  # 0-100
```

#### Metrics

**pass^k** (`src/evaluation/metrics/pass_k.py` - 400+ lines):
- Consensus voting (not pass@k best-case)
- Ground truth validation with tolerance
- Answer normalization for comparison

**B2B Metrics** (`src/evaluation/metrics/b2b_metrics.py`):
- Tool precision/recall/F1
- Category-specific breakdowns
- Error recovery rate

**Depth Metrics** (`src/evaluation/metrics/depth_metrics.py`):
- Max depth, avg depth
- Per-step pass^k (step1, step2, ...)
- Depth-weighted score

**MetricsCalculator** (`src/evaluation/metrics/calculator.py`) ⭐ Phase 1:
- Centralized calculations
- Eliminates ~180 lines of duplication
- Methods: precision_recall_f1, consensus, normalize_answer

**ReportFormatter** (`src/evaluation/metrics/report_formatter.py`) ⭐ Phase 1:
- Standardized report formatting
- ASCII charts, tables, sections
- Color-coded values

#### Tracers

**TracerBase** (`src/evaluation/tracers/base.py`) ⭐ Phase 1:
- Abstract base for all tracers
- Common interface: get_traces(), reset(), enable(), disable()
- Generic typing for type safety

**Tool Tracer** (`src/evaluation/tracers/tool_tracer.py`):
- Captures: tool_name, input, output, latency, status, error

**Error Tracer** (`src/evaluation/tracers/error_tracer.py`):
- Captures: error type, message, recovery attempts, success

**Step Tracer** (`src/evaluation/tracers/step_tracer.py`):
- Captures: step-by-step reasoning
- Depth metrics calculation
- Per-step scoring

### 4. Multi-Agent System

#### Router (`src/multi_agent/router.py`)
**Purpose**: Route queries to appropriate specialist

**Categories**:
1. Company Research
2. Financial Analysis
3. Competitive Intelligence
4. Strategic Reasoning (causal, forecasting, optimization)
5. General Fallback

**Routing Logic**:
```python
def route(query: str) -> str:
    # LLM-based classification
    # Returns category name
    # Confidence threshold: 0.7
```

#### Specialists (`src/multi_agent/specialists/`)

**Base Specialist** (`base_specialist.py`):
- Abstract base for all specialists
- Standard interface: process(), validate_output()
- Tool access control

**5 Specialists**:
1. **CompanyResearchSpecialist** - Founding dates, structure, key people
2. **FinancialAnalystSpecialist** - Revenue, metrics, trends
3. **CompetitiveIntelSpecialist** - Market comparison, positioning
4. **ActionExecutorSpecialist** - Gmail, Calendar actions (deprecated in v3.1)
5. **GeneralFallbackSpecialist** - Ambiguous queries

**Orchestrator** (`src/multi_agent/orchestrator.py`):
- Multi-agent coordination
- Parallel execution (when possible)
- Response synthesis

#### Guardrails (`src/multi_agent/guardrails/`)

**Input Validator** (`input_validator.py`):
- Query length limits
- Character sanitization
- SQL injection prevention

**Output Validator** (`output_validator.py`):
- Response completeness check
- Citation validation
- Hallucination detection

**Tool Access** (`tool_access.py`):
- Specialist-specific tool restrictions
- Permission enforcement

### 5. Dashboard Layer

#### Backend (`src/dashboard/backend/app.py` - 600+ lines)
**Framework**: FastAPI

**Key Endpoints**:
```
POST /api/chat - Chat with agent
GET /api/health - Health check
GET /api/evaluations - List evaluation runs
GET /api/evaluations/{run_id} - Detailed results
GET /api/dataset - Get evaluation dataset
GET /api/b2b-dataset - Get B2B dataset
GET /api/b2b-evaluations - Get B2B evaluation results
```

**Service Layer** (`services.py`) ⭐ Phase 2:
- `DatasetService` - Load datasets
- `EvaluationService` - Manage evaluation results
- `StaticFileService` - Serve frontend files

**Features**:
- Async support
- Pydantic validation
- CORS enabled
- Error handling

#### Frontend (`src/dashboard/frontend/`)

**index.html**:
- Single-page application
- 3 tabs: Chat, Evaluations, Dataset

**app.js** (800+ lines):
- Vanilla JavaScript (no frameworks)
- Real-time chat
- ASCII trace visualization
- Evaluation results display

**style.css** (500+ lines):
- Modern gradient design
- Responsive layout
- Animations and transitions

### 6. Storage Layer

#### Database (`src/storage/database.py`)
**Type**: SQLite

**Schema**:
```sql
CREATE TABLE tool_traces (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    tool_name TEXT,
    input_data TEXT,
    output_data TEXT,
    status TEXT,
    error_message TEXT,
    latency_ms INTEGER,
    timestamp DATETIME
);

CREATE TABLE evaluations (
    id INTEGER PRIMARY KEY,
    run_id TEXT UNIQUE,
    dataset_name TEXT,
    k_value INTEGER,
    results TEXT,  -- JSON
    metrics TEXT,  -- JSON
    timestamp DATETIME
);

CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    role TEXT,
    content TEXT,
    timestamp DATETIME
);

CREATE TABLE long_term_memory (
    id INTEGER PRIMARY KEY,
    user_id TEXT,
    key TEXT,
    value TEXT,
    timestamp DATETIME
);
```

#### Repositories (`src/storage/repositories/`)

**BaseRepository** (`base.py`):
- Common CRUD operations
- Transaction management
- Error handling

**Tool Trace Repository** (`tool_traces.py`):
- Save tool calls
- Query by session, tool, status
- Latency statistics

**Evaluation Repository** (`evaluations.py`):
- Save evaluation results
- List evaluations
- Get detailed results

**Conversation Repository** (`conversations.py`):
- Save messages
- Get conversation history
- Manage session

---

## Data Flow

### Query Processing Flow

```
User Query
    │
    ▼
ResearchAssistant.ask(query, mode="auto")
    │
    ├─→ QueryClassifier.is_deep_research(query)
    │   └─→ Returns: "normal" or "deep"
    │
    ├─→ ToolRegistry.get_tools_for_mode(mode)
    │   └─→ Returns: List of available tools
    │
    ▼
ClaudeLLMClient.chat(messages, tools)
    │
    ├─→ Build conversation context
    │   └─→ System prompt (normal/deep) + history
    │
    ├─→ Call Claude API
    │   └─→ Response: text OR tool_use
    │
    ├─→ If tool_use:
    │   ├─→ ToolRegistry.execute_tool(name, params)
    │   │   ├─→ Tool.execute(**params)
    │   │   ├─→ On error: Try fallback
    │   │   └─→ Return: {"success": bool, "result": Any}
    │   │
    │   ├─→ Add tool result to context
    │   └─→ Loop (max 15 times)
    │
    ├─→ If text:
    │   ├─→ Check truncation (stop_reason == "max_tokens")
    │   ├─→ If truncated: _recover_from_truncation()
    │   └─→ Return answer
    │
    ▼
ToolTracer.save_trace(tool_call) → SQLite
    │
    ▼
Return: (answer, tool_traces, error_traces)
```

### Evaluation Flow

```
run_evaluation.py --dataset data/b2b_dataset.json
    │
    ▼
B2BEvaluationHarness.run_b2b_evaluation(k=5)
    │
    ├─→ Load dataset (19 questions)
    │
    ├─→ For each question:
    │   │
    │   ├─→ Run agent k times (k=5)
    │   │   └─→ Collect: answers, tool_traces, step_traces
    │   │
    │   ├─→ Calculate consensus (pass^k)
    │   │   └─→ MetricsCalculator.calculate_consensus()
    │   │
    │   ├─→ LLM Judge scoring
    │   │   ├─→ Tool Selection: 0-25 pts
    │   │   ├─→ Tool Execution: 0-25 pts
    │   │   ├─→ Reasoning: 0-25 pts
    │   │   └─→ Answer Quality: 0-25 pts
    │   │
    │   └─→ Depth metrics
    │       ├─→ Max depth, avg depth
    │       └─→ Per-step pass^k
    │
    ├─→ Aggregate metrics
    │   ├─→ Overall pass rate
    │   ├─→ Category breakdowns
    │   ├─→ Tool precision/recall
    │   └─→ Avg scores
    │
    ├─→ Format report
    │   └─→ ReportFormatter.section()
    │
    └─→ Save to JSON
        └─→ data/results/b2b_eval_{timestamp}.json
```

---

## File Structure

### Complete File Tree

```
Bardeen/  (183 Python files)
│
├── src/  (94 source files)
│   │
│   ├── agent/  (32 files) ───────────────┐
│   │   ├── agent.py                      │ Main Agent
│   │   ├── llm_client.py (709 lines)     │ LLM Communication
│   │   ├── tool_registry.py              │ Tool Management
│   │   ├── planner.py                    │ Execution Planning
│   │   │                                 │
│   │   ├── core/                         │
│   │   │   ├── llm_client.py             │ Core LLM
│   │   │   ├── memory.py                 │ Conversation Memory
│   │   │   └── orchestrator.py           │ Multi-step Orchestration
│   │   │                                 │
│   │   ├── llm/  ⭐ NEW (Phase 2)        │
│   │   │   ├── prompts.py (75 lines)     │ PromptManager
│   │   │   └── query_classifier.py (68)  │ QueryClassifier
│   │   │                                 │
│   │   └── tools/                        │
│   │       ├── base_tool.py ⭐ (220)     │ ToolBase (Phase 1)
│   │       ├── calculator.py (165)       │ AST Calculator
│   │       ├── wikipedia.py              │ Wikipedia API
│   │       ├── web_search.py             │ Tavily
│   │       ├── duckduckgo_search.py      │ DuckDuckGo
│   │       ├── perplexity.py             │ Perplexity API
│   │       ├── gmail.py                  │ Gmail API
│   │       └── google_calendar.py        │ Calendar API
│   │                                     │
│   ├── evaluation/  (16 files) ──────────┤
│   │   ├── harness.py (600+ lines)       │ Evaluation Harness
│   │   ├── llm_judge.py                  │ LLM-as-Judge
│   │   ├── dataset.py                    │ Dataset Loading
│   │   ├── visualizer.py                 │ ASCII Visualization
│   │   │                                 │
│   │   ├── metrics/                      │
│   │   │   ├── pass_k.py (400+ lines)    │ pass^k Consensus
│   │   │   ├── b2b_metrics.py (250+)     │ B2B Metrics
│   │   │   ├── depth_metrics.py (300+)   │ Depth Metrics
│   │   │   ├── calculator.py ⭐ (290)    │ MetricsCalculator
│   │   │   └── report_formatter.py ⭐(320)│ ReportFormatter
│   │   │                                 │
│   │   └── tracers/                      │
│   │       ├── base.py ⭐ (128)          │ TracerBase (Phase 1)
│   │       ├── tool_tracer.py            │ Tool Call Tracing
│   │       ├── error_tracer.py           │ Error Tracking
│   │       └── step_tracer.py            │ Step-by-Step Tracing
│   │                                     │
│   ├── multi_agent/  (28 files) ─────────┤
│   │   ├── router.py (300+ lines)        │ Query Routing
│   │   ├── orchestrator.py               │ Multi-Agent Orchestration
│   │   ├── executor.py                   │ Agent Execution
│   │   ├── synthesizer.py                │ Response Synthesis
│   │   ├── api_integration.py            │ API Integration
│   │   │                                 │
│   │   ├── specialists/                  │
│   │   │   ├── base_specialist.py        │ Base Specialist
│   │   │   ├── company_research.py       │ Company Specialist
│   │   │   ├── financial_analyst.py      │ Financial Specialist
│   │   │   ├── competitive_intel.py      │ Competitive Specialist
│   │   │   ├── action_executor.py        │ Action Specialist
│   │   │   └── general_fallback.py       │ Fallback Specialist
│   │   │                                 │
│   │   ├── prompts/                      │
│   │   │   ├── company_prompt.py         │ Company Prompts
│   │   │   ├── financial_prompt.py       │ Financial Prompts
│   │   │   ├── competitive_prompt.py     │ Competitive Prompts
│   │   │   ├── action_prompt.py          │ Action Prompts
│   │   │   ├── general_prompt.py         │ General Prompts
│   │   │   └── orchestrator_prompt.py    │ Orchestrator Prompts
│   │   │                                 │
│   │   ├── guardrails/                   │
│   │   │   ├── input_validator.py        │ Input Validation
│   │   │   ├── output_validator.py       │ Output Validation
│   │   │   └── tool_access.py            │ Tool Access Control
│   │   │                                 │
│   │   └── evaluation/                   │
│   │       ├── multi_agent_harness.py    │ Multi-Agent Evaluation
│   │       ├── routing_metrics.py        │ Routing Metrics
│   │       └── utilization_metrics.py    │ Utilization Metrics
│   │                                     │
│   ├── dashboard/  (4 files + frontend) ─┤
│   │   ├── backend/                      │
│   │   │   ├── app.py (600+ lines)       │ FastAPI Application
│   │   │   └── services.py ⭐ (110)      │ Service Layer (Phase 2)
│   │   │                                 │
│   │   └── frontend/                     │
│   │       ├── index.html (400+ lines)   │ Main UI
│   │       ├── app.js (800+ lines)       │ JavaScript Logic
│   │       └── style.css (500+ lines)    │ Styling
│   │                                     │
│   ├── storage/  (8 files) ──────────────┤
│   │   ├── database.py                   │ SQLite Connection
│   │   ├── cache.py                      │ In-Memory Cache
│   │   │                                 │
│   │   └── repositories/                 │
│   │       ├── base.py                   │ BaseRepository
│   │       ├── tool_traces.py            │ Tool Trace Storage
│   │       ├── evaluations.py            │ Evaluation Storage
│   │       └── conversations.py          │ Conversation Storage
│   │                                     │
│   └── shared/  (5 files) ───────────────┘
│       ├── config.py (293 lines) ⭐      Enhanced Config (Phase 1)
│       ├── models.py                     Pydantic Models
│       ├── exceptions.py                 Custom Exceptions
│       └── utils.py                      Utility Functions
│
├── tests/  (83 test files)
│   ├── unit/  (27 files) ⭐ +3 new
│   │   ├── agent/
│   │   ├── evaluation/ ⭐               Phase 1 tests
│   │   ├── shared/
│   │   └── storage/
│   ├── integration/  (2 files)
│   ├── multi_agent/  (19 files)
│   ├── dashboard/  (16 files)
│   └── e2e/  (2 files)
│
├── scripts/  (1 file)
│   └── validate_refactoring.py ⭐       Phase 5 Validation
│
├── data/
│   ├── dataset.json                     Original dataset
│   ├── b2b_dataset.json                 B2B v3.1 (19 questions)
│   ├── agent.db                         SQLite database
│   └── results/                         Evaluation results
│
└── Root files
    ├── run_evaluation.py                Evaluation runner
    ├── start_dashboard.py               Dashboard startup
    ├── test_agent.py                    Quick test
    ├── validate_dataset.py              Dataset validation
    └── verify_v31.py                    Version check
```

---

## Refactoring Architecture

### Phase 1: Foundation (Complete ✅)

**Goal**: Create base classes and utilities to eliminate duplication

**New Files**:
1. `src/evaluation/tracers/base.py` (128 lines)
   - TracerBase abstract class
   - Generic typing for type safety
   - Common interface: get_traces(), reset(), enable(), disable()

2. `src/agent/tools/base_tool.py` (220 lines)
   - ToolBase abstract class
   - Standard error handling (TimeoutError, ValueError, ConnectionError)
   - Result formatting: _format_success(), _format_error()

3. `src/evaluation/metrics/calculator.py` (290 lines)
   - MetricsCalculator utility
   - Methods: precision_recall_f1, consensus, normalize_answer
   - Eliminates ~180 lines of duplication

4. `src/evaluation/metrics/report_formatter.py` (320 lines)
   - ReportFormatter utility
   - Methods: section, metric_table, color_value
   - Eliminates ~60 lines of duplication

**Enhanced Files**:
- `src/shared/config.py` (+75 lines)
  - RESPONSE_LIMITS (7 values)
  - TOKEN_LIMITS (7 values)
  - TIMEOUTS (10 values)
  - CONVERSATION (2 values)
  - QUERY_PATTERNS (19 patterns)

**Tests**:
- `tests/unit/evaluation/tracers/test_tracer_base.py` (7 tests)
- `tests/unit/agent/tools/test_tool_base.py` (6 tests)
- `tests/unit/evaluation/metrics/test_calculator.py` (10 tests)
- **Total**: 23 tests, 100% passing

**Impact**:
- Eliminated ~240 lines of error handling duplication
- Eliminated ~180 lines of metrics calculation duplication
- Centralized 45+ configuration values
- Foundation for refactoring 8 tools and 3 tracers

### Phase 2: Modularization (Skeleton Complete ✅)

**Goal**: Break down monolithic classes

**LLM Client Modularization**:
- `src/agent/llm/__init__.py`
- `src/agent/llm/prompts.py` (75 lines) - PromptManager
- `src/agent/llm/query_classifier.py` (68 lines) - QueryClassifier
- Future: `src/agent/llm/response_recovery.py` - ResponseRecovery
- Future: `src/agent/llm/client.py` - Refactored LLM client

**Dashboard Service Layer**:
- `src/dashboard/backend/services.py` (110 lines)
  - DatasetService - Generic dataset loading
  - EvaluationService - Evaluation management
  - StaticFileService - Static file serving

**Impact**:
- Foundation for breaking down 709-line llm_client.py
- Eliminates ~200 lines of duplicated endpoint logic

### Phase 5: Validation (Complete ✅)

**Goal**: Automated validation workflow

**New File**:
- `scripts/validate_refactoring.py` (204 lines)
  - 4 validation checks: imports, tests, coverage, baseline
  - Color-coded terminal output
  - Exit code for CI/CD integration

**Results**:
- ✅ Imports: All resolve correctly
- ✅ Tests: 630/652 passing (96.6%)
- ✅ Coverage: Within target range
- ✅ Baseline: No regressions in evaluation

### Refactoring Patterns

**Tool Refactoring Pattern**:
```python
# Before (Calculator original - 159 lines with duplication)
class Calculator:
    def __call__(self, expression: str) -> Dict:
        try:
            result = self.calculate(expression)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

# After (Calculator refactored - inherits from ToolBase)
class Calculator(ToolBase):
    def __init__(self):
        super().__init__(name="calculator", timeout=TIMEOUTS["calculator"])
    
    def _execute_internal(self, expression: str) -> Union[float, int]:
        return self.calculate(expression)  # Errors handled by ToolBase
```

**Benefits**:
- Eliminates 20-30 lines of error handling per tool
- Standardizes result format
- Centralizes timeout configuration
- Consistent logging

---

## Implementation Details

### Configuration Management

All configurable values in `src/shared/config.py`:

```python
# Response format limits (Phase 1)
RESPONSE_LIMITS = {
    "normal_mode_words_min": 50,
    "normal_mode_words_max": 60,
    "deep_mode_summary_words": 100,
    "table_max_rows": 4,
    "body_truncation_chars": 5000,
    "wikipedia_summary_chars": 1000,
    "duckduckgo_result_chars": 100,
}

# Token limits for LLM requests (Phase 1)
TOKEN_LIMITS = {
    "simple_query": 512,
    "comparison_query": 1024,
    "complex_query": 2048,
    "plan_creation": 1024,
    "recovery_deep": 2048,
    "recovery_normal": 512,
    "minimal_summary": 256,
}

# Timeout configuration in seconds (Phase 1)
TIMEOUTS = {
    "gmail": 10,
    "calendar": 10,
    "perplexity": 60,
    "web_search": 10,
    "duckduckgo": 10,
    "default_tool": 10,
    "wikipedia": 5,
    "calculator": 1,
}

# Conversation limits (Phase 1)
CONVERSATION = {
    "max_short_term_messages": 20,
    "max_history_for_context": 10,
}

# Query classification patterns (Phase 1)
QUERY_PATTERNS = {
    "deep_indicators": [
        r"research|analyze|comprehensive|detailed",
        r"compare|contrast|evaluate|assess",
        # ... 10 patterns total
    ],
    "simple_indicators": [
        r"^what is |^who is |^when was ",
        r"^calculate |^compute ",
        # ... 9 patterns total
    ]
}
```

### Error Handling Strategy

**Layered Error Handling**:

1. **Tool Layer** (ToolBase):
   - TimeoutError → timeout error response
   - ValueError → invalid_input error response
   - ConnectionError → connection_error response
   - General Exception → execution_error response

2. **Registry Layer** (ToolRegistry):
   - Tool failure → Try fallback tool
   - All tools fail → Return error with explanation
   - Log all failures

3. **Agent Layer** (ResearchAssistant):
   - Collect error traces
   - Return partial answer if possible
   - Never crash the system

4. **API Layer** (Dashboard):
   - HTTP exceptions with status codes
   - Error messages sanitized
   - Logged for debugging

### Testing Strategy

**Test Pyramid**:
```
     /\
    /E2E\     10% - End-to-end (35 tests)
   /──────\
  /  INT   \  30% - Integration (53 tests)
 /──────────\
/   UNIT     \ 60% - Unit (542 tests)
──────────────
```

**Coverage**:
- Overall: 96.6% (630/652 tests passing)
- Unit tests: 542 tests
- Integration tests: 53 tests  
- E2E tests: 35 tests

**Key Test Files**:
- `tests/unit/agent/test_agent.py` - Agent core
- `tests/unit/evaluation/test_harness.py` - Evaluation
- `tests/multi_agent/test_e2e.py` - Multi-agent E2E
- `tests/dashboard/test_app.py` - API endpoints
- `tests/test_response_truncation.py` - Truncation prevention

### Performance Characteristics

**Latency Breakdown**:
```
User Query → ResearchAssistant.ask()
    │
    ├─ Mode detection: ~1ms (regex matching)
    │
    ├─ LLM API call: ~500-800ms (Claude Sonnet 4.5)
    │   └─ Includes tool definition overhead: ~50ms
    │
    ├─ Tool execution:
    │   ├─ Calculator: ~5ms (AST parsing)
    │   ├─ Wikipedia: ~300ms (API call)
    │   ├─ Web Search: ~800ms (DuckDuckGo/Tavily)
    │   └─ Perplexity: ~2-5s (deep research)
    │
    ├─ Database save: ~10ms (SQLite insert)
    │
    └─ Total: ~1-2s (normal), ~3-6s (deep with Perplexity)
```

**Scalability**:
- Single-threaded evaluation (sequential)
- No rate limiting (relies on API rate limits)
- Database: SQLite (suitable for < 10k requests/day)
- Future: Redis for caching, Postgres for production

### Security Considerations

**Calculator Safety**:
```python
# AST-based evaluation (no eval/exec)
SAFE_OPERATORS = {
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow,
    ast.USub, ast.UAdd
}
# NO variables, functions, imports allowed
```

**API Key Management**:
- Environment variables only
- Never logged or displayed
- Not committed to git (.env in .gitignore)

**Input Validation**:
- Pydantic models on all API endpoints
- SQL injection prevention (prepared statements)
- XSS prevention (HTML escaping in frontend)

**Timeout Protection**:
- All tools have max execution time
- Prevents hanging requests
- LLM API timeout: 60s

---

**Document End** | **Version**: 1.0.0 | **Last Updated**: 2026-02-02
