# CLAUDE.md Changelog

This file tracks all changes made to CLAUDE.md for version control and audit purposes.

---

## [v2.0.0] - 2026-02-01

### Added
- **Perplexity API Integration**: Deep research tool using `sonar` and `sonar-pro` models
- **Auto Mode Detection**: AI automatically detects query complexity (simple vs deep)
- **Research Mode System**: Normal (50-60 words max) vs Deep (100-word summary + details)
- **Strict Response Guidelines**: Casual, conversational tone with hard word limits
- **Trace Storage**: All tool calls saved to SQLite database for analysis
- **Memory Persistence**: Long-term memory with user preferences and corrections

### Changed
- **Model Upgrade**: Updated from `claude-3-5-sonnet-20241022` to `claude-sonnet-4-20250514`
- **System Prompts**: Separate prompts for Normal and Deep modes with strict word limits
- **Tool Registry**: Mode-based filtering (CORE vs EXTENDED tools)
- **Dashboard UI**: Added Auto/Normal/Deep mode toggle with visual indicators

### Technical Updates
- QueryClassifier class for auto-detecting deep research needs
- Dynamic system prompt selection based on research mode
- Tool trace persistence to `tool_traces` table
- Downgraded Anthropic SDK from 0.77.0 to 0.75.0 (Pydantic compatibility fix)

---

## [v1.0.0] - 2026-01-15

### Initial Release
- Core agent with 3 tools: Calculator, Wikipedia, Web Search (DuckDuckGo/Tavily)
- pass^k evaluation harness with consensus metrics
- FastAPI dashboard with real-time chat
- ASCII trace visualization
- Dataset of 20 questions across 4 categories
