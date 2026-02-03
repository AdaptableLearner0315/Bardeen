# Bardeen B2B Intelligence Agent - Complete File Structure

**Last Updated**: 2026-02-02
**Total Python Files**: 183 (94 source, 83 tests)
**Lines of Code**: ~15,000+

---

## 📁 Project Root

```
Bardeen/
├── README.md                          # Project overview and quick start
├── CLAUDE.md                          # Instructions for Claude Code (project guide)
├── PRD.md                             # Product Requirements Document
├── REFACTORING_COMPLETION_REPORT.md   # Refactoring progress report ⭐ NEW
├── requirements.txt                   # Python dependencies
├── credentials.json                   # Google API credentials
├── pytest.ini                         # Pytest configuration
├── .gitignore                         # Git ignore rules
│
├── run_evaluation.py                  # Main evaluation runner
├── start_dashboard.py                 # Dashboard startup script
├── test_agent.py                      # Quick agent test
├── validate_dataset.py                # Dataset validation
└── verify_v31.py                      # Dataset version verification
```

---

## 📦 src/ - Source Code (94 files)

### src/agent/ - Main Agent (32 files)
**Purpose**: Core research assistant implementation with LLM interaction and tool calling

```
src/agent/
├── __init__.py                        # Package initialization
├── agent.py                           # ResearchAssistant main class (400+ lines)
├── llm_client.py                      # Claude API client (709 lines - TO REFACTOR)
├── planner.py                         # Execution planning logic
├── tool_registry.py                   # Tool management and registration
│
├── core/                              # Core agent components
│   ├── __init__.py
│   ├── llm_client.py                  # Core LLM interaction
│   ├── memory.py                      # Short/long-term memory (150+ lines)
│   └── orchestrator.py                # Multi-step orchestration
│
├── llm/ ⭐ NEW (Phase 2)              # LLM modularization
│   ├── __init__.py
│   ├── prompts.py                     # PromptManager (75 lines)
│   └── query_classifier.py            # QueryClassifier (68 lines)
│
└── tools/                             # Tool implementations
    ├── __init__.py
    ├── base.py                        # Legacy base (deprecated)
    ├── base_tool.py ⭐ NEW             # ToolBase abstract class (220 lines)
    ├── calculator.py                  # Safe AST calculator (165 lines)
    ├── wikipedia.py                   # Wikipedia lookup
    ├── web_search.py                  # Tavily fallback search
    ├── duckduckgo_search.py          # Primary search
    ├── perplexity.py                 # Deep research (sonar/sonar-pro)
    ├── gmail.py                      # Email actions
    ├── google_calendar.py            # Calendar actions
    └── registry.py                   # Tool registry (legacy)
```

**Key Files**:
- **agent.py**: Main `ResearchAssistant` class with `ask()` method
- **llm_client.py**: 709 lines - handles LLM communication, tool calling loop, response recovery
- **tool_registry.py**: Manages tool availability per mode, fallback chains
- **base_tool.py** ⭐: New abstract base for all tools (Phase 1)

---

### src/evaluation/ - Evaluation Framework (16 files)
**Purpose**: B2B evaluation harness, metrics calculation, LLM-as-Judge

```
src/evaluation/
├── __init__.py
├── dataset.py                         # Dataset loading and validation
├── harness.py                         # Evaluation harnesses (600+ lines)
├── llm_judge.py                       # LLM-as-Judge (4-dimension scoring)
├── visualizer.py                      # ASCII visualization
│
├── metrics/                           # Metrics calculation
│   ├── __init__.py
│   ├── pass_k.py                      # pass^k consensus (400+ lines)
│   ├── b2b_metrics.py                 # B2B-specific metrics (250+ lines)
│   ├── depth_metrics.py               # Depth-aware metrics (300+ lines)
│   ├── calculator.py ⭐ NEW           # MetricsCalculator utility (290 lines)
│   └── report_formatter.py ⭐ NEW     # ReportFormatter utility (320 lines)
│
└── tracers/                           # Tracing infrastructure
    ├── __init__.py
    ├── base.py ⭐ NEW                  # TracerBase abstract class (128 lines)
    ├── tool_tracer.py                 # Tool call tracing
    ├── error_tracer.py                # Error tracking
    └── step_tracer.py                 # Step-by-step reasoning tracer
```

**Key Files**:
- **harness.py**: `EvaluationHarness` and `B2BEvaluationHarness` classes
- **llm_judge.py**: 4-dimension scoring (Tool Selection, Execution, Reasoning, Answer Quality)
- **pass_k.py**: pass^k consensus metrics with ground truth validation
- **calculator.py** ⭐: Centralized metrics calculations (Phase 1)
- **base.py** ⭐: Base class for all tracers (Phase 1)

---

### src/multi_agent/ - Multi-Agent System (28 files)
**Purpose**: Advanced multi-agent orchestration for complex B2B queries

```
src/multi_agent/
├── __init__.py
├── router.py                          # Category routing (300+ lines)
├── orchestrator.py                    # Multi-agent orchestration
├── executor.py                        # Agent execution
├── synthesizer.py                     # Response synthesis
├── api_integration.py                 # API integration layer
│
├── specialists/                       # Domain specialists
│   ├── __init__.py
│   ├── base_specialist.py             # BaseSpecialist abstract class
│   ├── company_research.py            # Company research specialist
│   ├── financial_analyst.py           # Financial analysis specialist
│   ├── competitive_intel.py           # Competitive intelligence specialist
│   ├── action_executor.py             # Action execution specialist
│   └── general_fallback.py            # Fallback for ambiguous queries
│
├── prompts/                           # Specialist prompts
│   ├── __init__.py
│   ├── company_prompt.py              # Company research prompts
│   ├── financial_prompt.py            # Financial analysis prompts
│   ├── competitive_prompt.py          # Competitive intel prompts
│   ├── action_prompt.py               # Action execution prompts
│   ├── general_prompt.py              # General fallback prompts
│   └── orchestrator_prompt.py         # Orchestrator prompts
│
├── guardrails/                        # Safety and validation
│   ├── __init__.py
│   ├── input_validator.py             # Input validation
│   ├── output_validator.py            # Output validation
│   └── tool_access.py                 # Tool access control
│
└── evaluation/                        # Multi-agent evaluation
    ├── __init__.py
    ├── multi_agent_harness.py         # Multi-agent evaluation harness
    ├── routing_metrics.py             # Routing accuracy metrics
    └── utilization_metrics.py         # Agent utilization metrics
```

**Key Files**:
- **router.py**: Routes queries to appropriate specialist based on category
- **specialists/**: 5 domain specialists + base class
- **guardrails/**: Input/output validation and tool access control

---

### src/dashboard/ - Web Dashboard (4 files + frontend)
**Purpose**: FastAPI backend + Vanilla JS frontend for interactive testing

```
src/dashboard/
├── __init__.py
│
├── backend/
│   ├── __init__.py
│   ├── app.py                         # FastAPI application (600+ lines)
│   └── services.py ⭐ NEW             # Service layer (110 lines)
│
└── frontend/
    ├── index.html                     # Main UI (400+ lines)
    ├── app.js                         # JavaScript logic (800+ lines)
    └── style.css                      # Styling (500+ lines)
```

**Endpoints**:
- `/` - Main UI
- `/api/chat` - Chat endpoint
- `/api/evaluations` - List evaluations
- `/api/b2b-evaluations` - B2B evaluations
- `/api/dataset` - Dataset info
- `/api/health` - Health check

**Key Files**:
- **app.py**: FastAPI routes and logic
- **services.py** ⭐: Service layer for business logic (Phase 2)

---

### src/storage/ - Data Persistence (8 files)
**Purpose**: SQLite database, caching, repository pattern

```
src/storage/
├── __init__.py
├── database.py                        # Database connection and schema
├── cache.py                           # In-memory caching
│
└── repositories/                      # Repository pattern
    ├── __init__.py
    ├── base.py                        # BaseRepository abstract class
    ├── tool_traces.py                 # Tool trace storage
    ├── evaluations.py                 # Evaluation results storage
    └── conversations.py               # Conversation history storage
```

**Database Tables**:
- `tool_traces` - All tool calls with timing
- `evaluations` - Evaluation run results
- `conversations` - Chat history
- `long_term_memory` - User preferences

---

### src/shared/ - Shared Utilities (5 files)
**Purpose**: Configuration, models, utilities shared across modules

```
src/shared/
├── __init__.py
├── config.py                          # Configuration management (293 lines)
├── models.py                          # Pydantic models
├── exceptions.py                      # Custom exceptions
└── utils.py                           # Utility functions
```

**config.py** includes:
- `LLMConfig` - LLM settings
- `ToolConfig` - Tool-specific configs
- `ModeConfig` - Normal/Deep mode settings
- `MemoryConfig` - Memory limits
- `EvaluationConfig` - Evaluation settings
- **RESPONSE_LIMITS** ⭐ NEW (Phase 1)
- **TOKEN_LIMITS** ⭐ NEW (Phase 1)
- **TIMEOUTS** ⭐ NEW (Phase 1)
- **QUERY_PATTERNS** ⭐ NEW (Phase 1)

---

## 🧪 tests/ - Test Suite (83 files)

### tests/unit/ - Unit Tests (27 files)
**Purpose**: Fast, isolated tests for individual functions

```
tests/unit/
├── __init__.py
│
├── agent/                             # Agent unit tests
│   ├── test_agent.py
│   ├── test_planner.py
│   ├── test_query_classifier.py
│   ├── test_system_prompt.py
│   ├── test_llm_integration.py
│   ├── test_perplexity.py
│   ├── test_tool_cache.py
│   ├── test_critical_extraction.py
│   └── tools/
│       ├── test_base.py
│       ├── test_tool_base.py ⭐ NEW   # ToolBase tests (6 tests)
│       ├── test_registry.py
│       ├── test_research.py
│       ├── test_web_search.py
│       └── test_gmail_calendar.py
│
├── evaluation/                        # Evaluation unit tests
│   ├── metrics/
│   │   └── test_calculator.py ⭐ NEW  # MetricsCalculator tests (10 tests)
│   └── tracers/
│       └── test_tracer_base.py ⭐ NEW # TracerBase tests (7 tests)
│
├── shared/                            # Shared utilities tests
│   ├── test_config.py
│   ├── test_exceptions.py
│   ├── test_models.py
│   └── test_utils.py
│
└── storage/                           # Storage tests
    ├── test_database.py
    ├── test_cache.py
    └── test_repositories.py
```

**New Phase 1 Tests** ⭐:
- 23 tests added (100% passing)
- Full coverage of new base classes

---

### tests/integration/ - Integration Tests (2 files)
**Purpose**: Test component interactions

```
tests/integration/
├── __init__.py
└── test_memory_integration.py         # Memory system integration
```

---

### tests/multi_agent/ - Multi-Agent Tests (19 files)
**Purpose**: Test multi-agent system

```
tests/multi_agent/
├── __init__.py
├── test_router.py                     # Routing tests
├── test_orchestrator.py               # Orchestration tests
├── test_executor.py                   # Execution tests
├── test_synthesizer.py                # Synthesis tests
├── test_api_integration.py            # API integration tests
│
├── test_company_research.py           # Company specialist tests
├── test_financial_analyst.py          # Financial specialist tests
├── test_competitive_intel.py          # Competitive specialist tests
├── test_action_executor.py            # Action executor tests
├── test_general_fallback.py           # Fallback tests
├── test_base_specialist.py            # Base specialist tests
│
├── test_input_validator.py            # Input validation tests
├── test_output_validator.py           # Output validation tests
├── test_tool_access.py                # Tool access tests
├── test_prompts.py                    # Prompt tests
│
├── test_evaluation.py                 # Multi-agent evaluation tests
├── test_integration.py                # Integration tests
└── test_e2e.py                        # End-to-end tests
```

---

### tests/dashboard/ - Dashboard Tests (16 files)
**Purpose**: Test web UI and API endpoints

```
tests/dashboard/
├── __init__.py
├── backend/
│   └── test_app.py                    # API endpoint tests
│
├── test_evaluation_endpoints.py      # Evaluation API tests
├── test_frontend_evaluations.py      # Frontend evaluation tests
├── test_question_results_display.py   # Question results UI tests
├── test_routing.py                    # Route tests
├── test_safe_number_formatting.py     # Number formatting tests
├── test_score_tooltip.py              # Tooltip tests
├── test_send_button.py                # Send button tests
├── test_thinking_indicator.py         # Thinking indicator tests
├── test_tools_display.py              # Tools display tests
├── test_mode_toggle.py                # Mode toggle tests
├── test_low_confidence.py             # Low confidence tests
├── test_reasoning_traces.py           # Reasoning traces tests
└── test_explainability.py             # Explainability tests
```

---

### tests/e2e/ - End-to-End Tests (2 files)
**Purpose**: Full user workflow tests

```
tests/e2e/
├── __init__.py
└── test_dashboard.py                  # Dashboard E2E tests
```

---

### tests/ - Other Tests
```
tests/
├── test_frontend_ui.py                # Frontend UI tests
└── test_response_truncation.py        # Response truncation tests
```

---

## 📊 data/ - Data Files

```
data/
├── dataset.json                       # Original evaluation dataset
├── b2b_dataset.json                   # B2B dataset v3.1 (19 questions)
├── b2b_dataset_v1_backup.json         # Backup
├── b2b_dataset_v3.0_backup.json       # Backup
├── agent.db                           # SQLite database
│
└── results/                           # Evaluation results
    ├── b2b_eval_*.json                # B2B evaluation results
    └── eval_*.json                    # Standard evaluation results
```

---

## 🔧 scripts/ - Utility Scripts

```
scripts/
└── validate_refactoring.py ⭐ NEW     # Validation script (204 lines)
```

**Validation Checks**:
1. Import resolution
2. Test suite (630+ tests)
3. Code coverage (85% target)
4. Baseline evaluation (no regressions)

---

## 📚 Documentation Files

```
.
├── README.md                          # Main documentation
├── CLAUDE.md                          # Claude Code instructions (v3.1.0)
├── PRD.md                             # Product requirements
├── PROJECT_SUMMARY.md                 # Project overview
├── GETTING_STARTED.md                 # Quick start guide
│
├── REFACTORING_COMPLETION_REPORT.md ⭐ # Phase 1-2 completion report (598 lines)
├── IMPLEMENTATION_SUMMARY.md          # Implementation details
├── PHASE2_COMPLETION.md               # Phase 2 completion
├── STRATEGIC_REASONING_IMPLEMENTATION.md # Strategic reasoning
│
├── PILOT_README.md                    # Pilot documentation
├── PILOT_QUICKSTART.md                # Pilot quick start
├── PILOT_IMPLEMENTATION.md            # Pilot implementation
│
├── DATASET_COMPARISON.md              # Dataset comparison
├── CATEGORY_REPLACEMENT.md            # Category replacement notes
├── EVALUATION_DETAIL_FIX.md           # Evaluation fixes
├── EVALUATION_UI_FIX.md               # UI fixes
└── QUESTION_RESULTS_FIX.md            # Question results fixes
```

---

## 🌲 Directory Tree (Condensed)

```
Bardeen/
│
├── src/                               # Source code (94 files)
│   ├── agent/                         # Agent implementation (32 files)
│   │   ├── core/                      # Core components
│   │   ├── llm/ ⭐                    # LLM modules (Phase 2)
│   │   └── tools/                     # Tool implementations
│   ├── evaluation/                    # Evaluation framework (16 files)
│   │   ├── metrics/                   # Metrics calculation
│   │   └── tracers/ ⭐                # Tracing (Phase 1)
│   ├── multi_agent/                   # Multi-agent system (28 files)
│   │   ├── specialists/               # Domain specialists
│   │   ├── prompts/                   # Specialist prompts
│   │   ├── guardrails/                # Validation
│   │   └── evaluation/                # Multi-agent evaluation
│   ├── dashboard/                     # Web dashboard (4 files)
│   │   ├── backend/                   # FastAPI
│   │   └── frontend/                  # Vanilla JS
│   ├── storage/                       # Data persistence (8 files)
│   │   └── repositories/              # Repository pattern
│   └── shared/                        # Shared utilities (5 files)
│
├── tests/                             # Test suite (83 files)
│   ├── unit/                          # Unit tests (27 files)
│   │   ├── agent/
│   │   ├── evaluation/ ⭐             # Phase 1 tests
│   │   ├── shared/
│   │   └── storage/
│   ├── integration/                   # Integration tests (2 files)
│   ├── multi_agent/                   # Multi-agent tests (19 files)
│   ├── dashboard/                     # Dashboard tests (16 files)
│   └── e2e/                           # E2E tests (2 files)
│
├── scripts/                           # Utility scripts
│   └── validate_refactoring.py ⭐     # Validation (Phase 5)
│
├── data/                              # Data files
│   ├── dataset.json
│   ├── b2b_dataset.json
│   ├── agent.db
│   └── results/
│
└── [documentation files]              # 15+ markdown files
```

---

## 📊 Statistics

| Category | Count | Notes |
|----------|-------|-------|
| **Total Python Files** | 183 | Entire project |
| **Source Files** | 94 | src/ directory |
| **Test Files** | 83 | tests/ directory |
| **Documentation Files** | 15+ | Markdown files |
| **New Files (Phase 1)** | 7 | Base classes & utilities ⭐ |
| **New Files (Phase 2)** | 4 | Modularization ⭐ |
| **Lines of Code (est.)** | 15,000+ | Python only |

---

## 🎯 Key Architectural Components

### 1. Agent Layer
- **ResearchAssistant** - Main interface
- **LLM Client** - Claude API communication
- **Tool Registry** - Tool management
- **Memory System** - Conversation tracking

### 2. Evaluation Layer
- **Evaluation Harness** - Test execution
- **LLM Judge** - Quality scoring
- **Metrics** - pass^k, depth, B2B metrics
- **Tracers** - Tool, error, step tracing

### 3. Multi-Agent Layer
- **Router** - Query categorization
- **Specialists** - Domain experts (5 types)
- **Orchestrator** - Multi-agent coordination
- **Synthesizer** - Response combination

### 4. Dashboard Layer
- **Backend** - FastAPI REST API
- **Frontend** - Vanilla JS SPA
- **Services** - Business logic (Phase 2) ⭐

### 5. Storage Layer
- **Database** - SQLite persistence
- **Repositories** - Data access patterns
- **Cache** - In-memory caching

---

## 🆕 Refactoring Additions (Phase 1-2)

**Phase 1 - Foundation** ⭐:
- `src/evaluation/tracers/base.py` - TracerBase (128 lines)
- `src/agent/tools/base_tool.py` - ToolBase (220 lines)
- `src/evaluation/metrics/calculator.py` - MetricsCalculator (290 lines)
- `src/evaluation/metrics/report_formatter.py` - ReportFormatter (320 lines)
- `tests/unit/evaluation/tracers/test_tracer_base.py` - 7 tests
- `tests/unit/agent/tools/test_tool_base.py` - 6 tests
- `tests/unit/evaluation/metrics/test_calculator.py` - 10 tests

**Phase 2 - Modularization** ⭐:
- `src/agent/llm/prompts.py` - PromptManager (75 lines)
- `src/agent/llm/query_classifier.py` - QueryClassifier (68 lines)
- `src/dashboard/backend/services.py` - Service layer (110 lines)

**Phase 5 - Validation** ⭐:
- `scripts/validate_refactoring.py` - Validation script (204 lines)

**Total New Code**: ~1,400 lines across 11 files

---

## 🔄 Files Modified (Phase 1-2)

- `src/shared/config.py` - Added RESPONSE_LIMITS, TOKEN_LIMITS, TIMEOUTS, QUERY_PATTERNS (+75 lines)
- `src/agent/tools/calculator.py` - Refactored to use ToolBase

---

## 📖 Usage Examples

### Run Agent
```bash
python test_agent.py
```

### Start Dashboard
```bash
python start_dashboard.py --port 8002
```

### Run Evaluation
```bash
python run_evaluation.py --dataset data/b2b_dataset.json
```

### Run Tests
```bash
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v
```

### Run Validation
```bash
python scripts/validate_refactoring.py
```

---

**Document End** | **Total Files**: 183 Python + 15+ docs | **Last Updated**: 2026-02-02
