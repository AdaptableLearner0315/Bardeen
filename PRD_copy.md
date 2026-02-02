### Product Requirements Document (PRD)
# B2B Account Intelligence Agent

**Version**: 1.0
**Date**: January 30, 2025
**Author**: Engineering Team
**Status**: Draft for Review

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Goals & Success Metrics](#3-goals--success-metrics)
4. [User Personas](#4-user-personas)
5. [Functional Requirements](#5-functional-requirements)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [System Architecture](#7-system-architecture)
8. [Module Specifications & Edge Cases](#8-module-specifications--edge-cases)
9. [API Specifications](#9-api-specifications)
10. [Data Models](#10-data-models)
11. [Evaluation Framework](#11-evaluation-framework)
12. [Security & Compliance](#12-security--compliance)
13. [Deployment & Operations](#13-deployment--operations)
14. [Risks & Mitigations](#14-risks--mitigations)
15. [Timeline & Milestones](#15-timeline--milestones)
16. [Appendix](#16-appendix)

---

## 1. Executive Summary

### 1.1 Product Vision

Build an LLM-powered conversational agent that helps users research companies, analyze markets, and perform limited actions (email summarization, calendar scheduling) through natural language interaction. The system demonstrates sophisticated tool orchestration relevant to B2B workflow automation.

### 1.2 Key Differentiators

| Aspect | Description |
|--------|-------------|
| **Multi-Tool Orchestration** | 10 integrated tools with intelligent selection |
| **Adaptive Depth** | User-controlled Normal (2-3 tools) vs Deep (5-10 tools) research modes |
| **Memory Architecture** | Short-term + Long-term memory with domain partitioning |
| **Comprehensive Evaluation** | pass^k consensus metrics + tool efficiency metrics |
| **Production-Ready** | Real Gmail/Calendar integration, not mocked |

### 1.3 Success Criteria

- pass^5 score ≥ 80%
- pass^10 score ≥ 85%
- Tool Efficiency Score ≥ 75%
- Tool Success Rate ≥ 90%
- Average response latency < 15 seconds (Deep mode)

---

## 2. Problem Statement

### 2.1 Current State

Sales, BD, and research teams spend 30%+ of their time manually gathering information about companies from disparate sources:
- Google searches for basic company info
- LinkedIn for employee data
- SEC filings for financials
- News sites for recent events
- Multiple tabs, copy-paste workflows

### 2.2 Pain Points

| Pain Point | Impact |
|------------|--------|
| Time-consuming | 15-30 min per account research |
| Inconsistent | Different team members find different info |
| Incomplete | Often miss key signals (funding, hiring, tech stack) |
| Not actionable | Raw data requires synthesis |
| Context switching | Jumping between 5-10 different sites |

### 2.3 Opportunity

An AI agent that:
- Consolidates research into a single conversational interface
- Intelligently selects and orchestrates multiple data sources
- Synthesizes findings into actionable insights
- Learns from conversation context for better results
- Integrates with existing workflows (email, calendar)

---

## 3. Goals & Success Metrics

### 3.1 Primary Goals

| Goal | Metric | Target |
|------|--------|--------|
| **Accuracy** | pass^5 consensus score | ≥ 80% |
| **Consistency** | pass^10 consensus score | ≥ 85% |
| **Efficiency** | Tool calls vs optimal | ≥ 75% |
| **Reliability** | Tool success rate | ≥ 90% |
| **Performance** | P95 latency (Deep mode) | < 20s |

### 3.2 Secondary Goals

| Goal | Metric | Target |
|------|--------|--------|
| **User Experience** | Successful query completion | ≥ 95% |
| **Graceful Degradation** | Partial results on tool failure | 100% |
| **Memory Utilization** | Context relevance in follow-ups | ≥ 80% |

### 3.3 Out of Scope for MVP

- Real-time collaboration features
- Mobile application
- Third-party CRM integrations (Salesforce, HubSpot)
- Custom tool creation by users
- Multi-language support

---

## 4. User Personas

### 4.1 Primary Persona: Sales Development Rep (SDR)

**Name**: Alex
**Role**: SDR at B2B SaaS company
**Goals**: Research accounts before outreach, find talking points
**Pain Points**: Spends 2+ hours daily on manual research
**Tech Savvy**: Medium

**Typical Queries**:
- "Tell me about Stripe's recent funding and growth"
- "What's Datadog's tech stack?"
- "Compare Notion vs Coda for enterprise"

### 4.2 Secondary Persona: Business Analyst

**Name**: Jordan
**Role**: Strategy & Operations Analyst
**Goals**: Competitive intelligence, market research
**Pain Points**: Data scattered across multiple sources
**Tech Savvy**: High

**Typical Queries**:
- "What's Snowflake's revenue growth YoY?"
- "Who are the top players in observability space?"
- "Summarize SEC filing highlights for Cloudflare"

### 4.3 Tertiary Persona: Executive Assistant

**Name**: Sam
**Role**: EA to VP of Sales
**Goals**: Schedule meetings, summarize communications
**Pain Points**: Context switching between email/calendar/research
**Tech Savvy**: Medium

**Typical Queries**:
- "Summarize my last 5 emails from Acme Corp"
- "Schedule a 30-min call with John next Tuesday"
- "What should I know before the Figma meeting?"

---

## 5. Functional Requirements

### 5.1 Core Chat Functionality

#### FR-1: Natural Language Query Processing

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1.1 | System SHALL accept free-form natural language queries | P0 |
| FR-1.2 | System SHALL support queries up to 2000 characters | P0 |
| FR-1.3 | System SHALL handle ambiguous queries by asking clarifying questions | P1 |
| FR-1.4 | System SHALL support follow-up questions with conversation context | P0 |

#### FR-2: Research Mode Selection

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.1 | System SHALL provide UI toggle for Normal vs Deep research mode | P0 |
| FR-2.2 | Normal mode SHALL use 2-3 core tools (Search, Wikipedia, Calculator) | P0 |
| FR-2.3 | Deep mode SHALL use 5-10 tools based on query relevance | P0 |
| FR-2.4 | System SHALL display estimated completion time based on mode | P2 |

#### FR-3: Tool Orchestration

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-3.1 | System SHALL intelligently select tools based on query type | P0 |
| FR-3.2 | System SHALL execute up to 10 tool calls per query | P0 |
| FR-3.3 | System SHALL retry failed tools up to 2 times before fallback | P0 |
| FR-3.4 | System SHALL prompt user "Search more?" or "End" after 2-3 consecutive failures | P0 |
| FR-3.5 | System SHALL provide reasoning trace for tool selection | P1 |

#### FR-4: Response Generation

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-4.1 | System SHALL generate free-form text responses | P0 |
| FR-4.2 | System SHALL include source block at end of response | P0 |
| FR-4.3 | System SHALL add disclaimer when accuracy is within 5-10% tolerance | P0 |
| FR-4.4 | System SHALL support streaming responses for better UX | P1 |

### 5.2 Tool Capabilities

#### FR-5: Research Tools

| ID | Tool | Capability | Priority |
|----|------|------------|----------|
| FR-5.1 | Web Search | General web search via DuckDuckGo | P0 |
| FR-5.2 | Wikipedia | Factual information lookup | P0 |
| FR-5.3 | Calculator | Mathematical computations | P0 |
| FR-5.4 | Yahoo Finance | Stock data, market cap, financials | P0 |
| FR-5.5 | SEC EDGAR | Public company filings (10-K, 10-Q) | P1 |
| FR-5.6 | GitHub API | Repository stats, tech signals | P1 |
| FR-5.7 | HackerNews | Developer sentiment, tech discussions | P1 |
| FR-5.8 | Website Scraper | Company website analysis | P1 |

#### FR-6: Action Tools

| ID | Tool | Capability | Priority |
|----|------|------------|----------|
| FR-6.1 | Gmail | Summarize emails from specified sender/thread | P0 |
| FR-6.2 | Google Calendar | Schedule meetings with specified parameters | P0 |

### 5.3 Memory & Context

#### FR-7: Short-Term Memory

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-7.1 | System SHALL maintain conversation context within session | P0 |
| FR-7.2 | System SHALL support up to 20 messages in active context | P0 |
| FR-7.3 | System SHALL automatically summarize older messages when limit exceeded | P1 |

#### FR-8: Long-Term Memory

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-8.1 | System SHALL persist conversation history to SQLite | P0 |
| FR-8.2 | System SHALL partition memory by: conversations, tool_traces, domain_context | P0 |
| FR-8.3 | System SHALL retrieve relevant past conversations for context | P1 |
| FR-8.4 | System SHALL allow users to clear their conversation history | P1 |

### 5.4 Dashboard & Evaluation

#### FR-9: Chat Interface

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-9.1 | Dashboard SHALL provide real-time chat interface | P0 |
| FR-9.2 | Dashboard SHALL display tool calls as they happen | P1 |
| FR-9.3 | Dashboard SHALL show Normal/Deep mode toggle | P0 |
| FR-9.4 | Dashboard SHALL display connection status and available tools | P1 |

#### FR-10: Evaluation Viewer

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-10.1 | Dashboard SHALL display all evaluation runs | P0 |
| FR-10.2 | Dashboard SHALL show pass^5, pass^10, Tool Efficiency, Tool Success Rate | P0 |
| FR-10.3 | Dashboard SHALL allow filtering by date, category, metric | P0 |
| FR-10.4 | Dashboard SHALL support drill-down into individual question results | P1 |

#### FR-11: Export

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-11.1 | System SHALL export evaluation results to CSV | P0 |
| FR-11.2 | System SHALL export evaluation results to PDF | P0 |
| FR-11.3 | Export SHALL include all metrics, traces, and metadata | P0 |

---

## 6. Non-Functional Requirements

### 6.1 Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1.1 | Response latency (Normal mode) | P95 < 8s |
| NFR-1.2 | Response latency (Deep mode) | P95 < 20s |
| NFR-1.3 | Dashboard load time | < 2s |
| NFR-1.4 | API response time (non-chat) | < 500ms |

### 6.2 Scalability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-2.1 | Concurrent users | 20 simultaneous |
| NFR-2.2 | Daily active users | 100 |
| NFR-2.3 | Queries per second | 20 |
| NFR-2.4 | Database size | 10GB max |

### 6.3 Reliability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-3.1 | System uptime | 99% |
| NFR-3.2 | Data durability | No data loss on crash |
| NFR-3.3 | Graceful degradation | Partial results on tool failure |

### 6.4 Security

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-4.1 | OAuth tokens | Encrypted at rest |
| NFR-4.2 | API keys | Environment variables only |
| NFR-4.3 | User data | Session-isolated |
| NFR-4.4 | Input sanitization | All user inputs validated |

---

## 7. System Architecture

### 7.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   FRONTEND                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         Vanilla JS SPA                                   │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │    │
│  │  │   Chat UI    │  │  Eval Viewer │  │   Filters    │  │   Export    │  │    │
│  │  │              │  │              │  │              │  │  CSV | PDF  │  │    │
│  │  │ [Normal│Deep]│  │  pass^k      │  │  By Date     │  │             │  │    │
│  │  │   Toggle     │  │  Tool Metrics│  │  By Category │  │             │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ HTTP/REST
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              API GATEWAY (FastAPI)                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ POST /chat  │  │ GET /evals  │  │ GET /export │  │ GET/POST /auth/google   │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘ │
│         └────────────────┴────────────────┴─────────────────────┘               │
│                                    │                                             │
│         ┌──────────────────────────┴──────────────────────────┐                 │
│         │              Middleware Layer                        │                 │
│         │  [Rate Limiter] [Session Manager] [Error Handler]   │                 │
│         └─────────────────────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                               AGENT CORE                                         │
│  ┌───────────────────┐  ┌───────────────────┐  ┌─────────────────────────────┐  │
│  │   LLM Client      │  │  Strategy Engine  │  │     Memory Manager          │  │
│  │  Claude Sonnet 4.5│  │  Normal │ Deep    │  │  Short-term │ Long-term     │  │
│  └─────────┬─────────┘  └─────────┬─────────┘  └──────────────┬──────────────┘  │
│            └──────────────────────┼───────────────────────────┘                  │
│                                   │                                              │
│                                   ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         Tool Registry                                    │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │    │
│  │  │ CORE: Web Search │ Wikipedia │ Calculator                       │    │    │
│  │  ├─────────────────────────────────────────────────────────────────┤    │    │
│  │  │ EXTENDED: Yahoo Finance │ SEC EDGAR │ GitHub │ HackerNews │     │    │    │
│  │  │           Website Scraper │ Gmail │ Google Calendar             │    │    │
│  │  └─────────────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            STORAGE LAYER                                         │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌───────────────────────┐  │
│  │   SQLite Database    │  │   In-Memory Cache    │  │    File Storage       │  │
│  │  - conversations     │  │  - Tool responses    │  │  - eval_results/      │  │
│  │  - tool_traces       │  │  - Rate limit state  │  │  - exports/           │  │
│  │  - eval_runs         │  │  - Session data      │  │  - oauth_tokens/      │  │
│  └──────────────────────┘  └──────────────────────┘  └───────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Technology Stack

| Layer | Technology | Version | Rationale |
|-------|------------|---------|-----------|
| **LLM** | Claude Sonnet 4.5 | Latest | Best tool calling, reasoning |
| **Backend** | FastAPI | 0.109+ | Async, OpenAPI, fast |
| **Database** | SQLite | 3.x | MVP-appropriate, WAL mode |
| **Cache** | cachetools | 5.3+ | TTL dict, simple |
| **Frontend** | Vanilla JS | ES6+ | No build step |
| **PDF Export** | WeasyPrint | 60+ | HTML→PDF |
| **Auth** | Google OAuth 2.0 | - | Gmail/GCal access |

---

## 8. Module Specifications & Edge Cases

### 8.1 Module: LLM Client

#### 8.1.1 Specification

| Attribute | Value |
|-----------|-------|
| Model | claude-sonnet-4-5-20250514 |
| Temperature | 0.6 (balances consistency & diversity) |
| Max Tokens | 4096 |
| Timeout | 60 seconds |
| Tool Calling | Enabled with parallel tool use |

#### 8.1.2 Responsibilities

- Format messages for Claude API
- Execute tool calling loop
- Handle streaming responses
- Manage token limits

#### 8.1.3 Edge Cases

| Edge Case | Scenario | Expected Behavior | Business Impact |
|-----------|----------|-------------------|-----------------|
| EC-LLM-01 | API rate limit exceeded | Retry with exponential backoff (3 attempts), then return error with retry suggestion | User sees "Service busy, please retry in X seconds" |
| EC-LLM-02 | API timeout (>60s) | Cancel request, return partial results if any tools completed | User gets partial info rather than nothing |
| EC-LLM-03 | Invalid tool call from LLM | Log error, skip tool, continue with other tools | Graceful degradation, user unaware |
| EC-LLM-04 | Context window exceeded | Summarize older messages, retry with condensed context | Conversation continues without hard failure |
| EC-LLM-05 | Malformed API response | Parse what's possible, log anomaly, return best-effort response | User gets response, engineering alerted |
| EC-LLM-06 | Tool calling loop (>10 calls) | Force stop, synthesize answer from collected data | Prevent infinite loops, user gets answer |
| EC-LLM-07 | Empty response from LLM | Retry once with slight prompt modification | User sees response, not blank |
| EC-LLM-08 | API key invalid/expired | Return clear error, prompt admin action | "Service configuration error, contact admin" |

---

### 8.2 Module: Tool Registry

#### 8.2.1 Specification

| Attribute | Value |
|-----------|-------|
| Total Tools | 10 |
| Core Tools | 3 (Web Search, Wikipedia, Calculator) |
| Extended Tools | 7 (Yahoo, SEC, GitHub, HN, Scraper, Gmail, Calendar) |
| Fallback Chains | web_search → wikipedia |
| Max Retries | 2 per tool |

#### 8.2.2 Tool Configuration

| Tool | Mode | Rate Limit | Timeout | Fallback |
|------|------|------------|---------|----------|
| Web Search | Core | 1 req/sec | 10s | Wikipedia |
| Wikipedia | Core | 10 req/sec | 5s | None |
| Calculator | Core | Unlimited | 1s | None |
| Yahoo Finance | Extended | 2 req/sec | 10s | Web Search |
| SEC EDGAR | Extended | 10 req/sec | 15s | Web Search |
| GitHub API | Extended | 83 req/min | 10s | Web Search |
| HackerNews | Extended | 10 req/sec | 5s | Web Search |
| Website Scraper | Extended | 1 req/sec | 15s | None |
| Gmail | Extended | 10 req/sec | 10s | None |
| Google Calendar | Extended | 10 req/sec | 10s | None |

#### 8.2.3 Edge Cases

| Edge Case | Scenario | Expected Behavior | Business Impact |
|-----------|----------|-------------------|-----------------|
| EC-TR-01 | Tool not found in registry | Log error, skip tool, continue with available tools | Agent adapts, user unaware |
| EC-TR-02 | All tools for query type fail | Prompt user: "Unable to find information. Search more or end?" | User controls next step |
| EC-TR-03 | Rate limit hit on critical tool | Queue request, apply backoff, use fallback if available | Slight delay, user gets results |
| EC-TR-04 | Tool returns empty result | Mark as "no data found", try fallback or alternative query | User informed data unavailable |
| EC-TR-05 | Tool returns error response | Log error, retry once, then use fallback | Transparent to user |
| EC-TR-06 | Mode mismatch (Normal mode requests Extended tool) | Silently skip, use available Core tools only | User gets results from allowed tools |
| EC-TR-07 | Circular fallback detected | Break chain, return partial results | Prevent infinite fallback loop |
| EC-TR-08 | Tool schema mismatch with LLM expectation | Validate and transform input, log discrepancy | Tool executes correctly |

---

### 8.3 Module: Web Search Tool (DuckDuckGo)

#### 8.3.1 Specification

| Attribute | Value |
|-----------|-------|
| Provider | DuckDuckGo (duckduckgo-search) |
| Max Results | 10 |
| Timeout | 10 seconds |
| Rate Limit | 1 request/second |

#### 8.3.2 Edge Cases

| Edge Case | Scenario | Expected Behavior | Business Impact |
|-----------|----------|-------------------|-----------------|
| EC-WS-01 | DuckDuckGo blocks request | Implement delay, retry with different user-agent | Slight delay, search completes |
| EC-WS-02 | Query returns 0 results | Return empty with message "No results found for query" | User informed, can rephrase |
| EC-WS-03 | Query too long (>500 chars) | Truncate to key terms, log original | Search executes with core terms |
| EC-WS-04 | Special characters in query | URL-encode, sanitize input | Search works correctly |
| EC-WS-05 | Network timeout | Retry once, then fallback to Wikipedia | User gets alternative source |
| EC-WS-06 | Results contain non-English content | Return as-is, let LLM handle translation context | Multilingual results included |
| EC-WS-07 | Duplicate results | Deduplicate by URL before returning | Clean results list |
| EC-WS-08 | Results from unreliable sources | Include all, let LLM evaluate credibility | User sees source attribution |

---

### 8.4 Module: Wikipedia Tool

#### 8.4.1 Specification

| Attribute | Value |
|-----------|-------|
| Provider | Wikipedia API (wikipedia-api) |
| Max Summary Length | 2000 characters |
| Language | English (en) |
| Timeout | 5 seconds |

#### 8.4.2 Edge Cases

| Edge Case | Scenario | Expected Behavior | Business Impact |
|-----------|----------|-------------------|-----------------|
| EC-WK-01 | Page not found | Return "No Wikipedia page found for [topic]" | User informed, can try alternative |
| EC-WK-02 | Disambiguation page returned | Return top 3 options, let LLM choose or ask user | Accurate result after clarification |
| EC-WK-03 | Page exists but is a stub | Return content with note "Limited information available" | User knows info is sparse |
| EC-WK-04 | API rate limited | Implement backoff, retry after delay | Slight delay, request succeeds |
| EC-WK-05 | Page content too long | Truncate to first 2000 chars of summary | Consistent response size |
| EC-WK-06 | Non-English page title | Search with English Wikipedia, return closest match | English results prioritized |
| EC-WK-07 | Page recently updated (may be vandalized) | Return content, include last-edit timestamp | User sees recency indicator |
| EC-WK-08 | Multiple pages match query | Return most relevant (by page views or exact match) | Best match returned |

---

### 8.5 Module: Calculator Tool

#### 8.5.1 Specification

| Attribute | Value |
|-----------|-------|
| Implementation | AST-based safe evaluator |
| Allowed Operations | +, -, *, /, **, (), sqrt, log, sin, cos, tan |
| Number Types | int, float |
| Max Expression Length | 500 characters |

#### 8.5.2 Edge Cases

| Edge Case | Scenario | Expected Behavior | Business Impact |
|-----------|----------|-------------------|-----------------|
| EC-CA-01 | Division by zero | Return error "Division by zero is undefined" | Clear error message |
| EC-CA-02 | Overflow (result > MAX_FLOAT) | Return "Result too large to compute" | User understands limitation |
| EC-CA-03 | Invalid expression syntax | Return "Invalid expression: [specific error]" | User can fix expression |
| EC-CA-04 | Injection attempt (exec, import) | Reject with "Invalid operation", log attempt | Security maintained |
| EC-CA-05 | Expression too complex | Return "Expression too complex, simplify" | Prevent resource exhaustion |
| EC-CA-06 | Negative square root | Return "Cannot compute square root of negative number" or use complex | Clear mathematical error |
| EC-CA-07 | Very small numbers (underflow) | Return 0 with note "Result rounded to zero" | User understands precision limit |
| EC-CA-08 | Non-numeric input in expression | Extract numbers if possible, else return error | Best-effort parsing |

---

### 8.6 Module: Yahoo Finance Tool

#### 8.6.1 Specification

| Attribute | Value |
|-----------|-------|
| Provider | yfinance library |
| Data Types | Stock price, market cap, P/E, revenue, earnings |
| Timeout | 10 seconds |
| Rate Limit | 2 requests/second |

#### 8.6.2 Edge Cases

| Edge Case | Scenario | Expected Behavior | Business Impact |
|-----------|----------|-------------------|-----------------|
| EC-YF-01 | Invalid ticker symbol | Return "Ticker [X] not found. Did you mean [suggestions]?" | Helpful error with alternatives |
| EC-YF-02 | Private company (no ticker) | Return "Company is not publicly traded" | User informed, no false data |
| EC-YF-03 | Market closed, stale data | Return data with timestamp "As of [date/time]" | User knows data freshness |
| EC-YF-04 | Delisted company | Return "Company was delisted on [date]" with last known data | Historical context provided |
| EC-YF-05 | Data field unavailable (e.g., no P/E for loss-making) | Return available fields, note "P/E not applicable (negative earnings)" | Partial data with explanation |
| EC-YF-06 | Currency mismatch (foreign stock) | Return with currency label "Revenue: ¥1.2T (JPY)" | Clear currency attribution |
| EC-YF-07 | API temporarily unavailable | Retry once, then fallback to web search | User gets data from alternative |
| EC-YF-08 | Multiple tickers match company name | Return most relevant (by market cap) or ask for clarification | Accurate ticker selection |

---

### 8.7 Module: SEC EDGAR Tool

#### 8.7.1 Specification

| Attribute | Value |
|-----------|-------|
| Provider | SEC EDGAR API |
| Filing Types | 10-K, 10-Q, 8-K |
| Rate Limit | 10 requests/second |
| Timeout | 15 seconds |

#### 8.7.2 Edge Cases

| Edge Case | Scenario | Expected Behavior | Business Impact |
|-----------|----------|-------------------|-----------------|
| EC-SE-01 | Company not registered with SEC | Return "Company does not file with SEC (non-US or private)" | User informed of data limitation |
| EC-SE-02 | No recent filings | Return "Most recent filing: [date]" with that filing | User gets available data |
| EC-SE-03 | Filing document too large | Extract key sections (risk factors, financials) only | Relevant excerpts provided |
| EC-SE-04 | CIK (company ID) not found | Search by company name, return best match or error | Flexible company lookup |
| EC-SE-05 | Filing in XBRL format parsing error | Fall back to HTML version of filing | Data extracted from alternative format |
| EC-SE-06 | Rate limit from SEC | Implement mandatory delay, queue request | Compliant with SEC requirements |
| EC-SE-07 | Foreign company (20-F instead of 10-K) | Detect filing type, parse accordingly | Correct form processed |
| EC-SE-08 | Recent IPO, limited filing history | Return available filings, note "Company recently went public" | Context about data availability |

---

### 8.8 Module: GitHub API Tool

#### 8.8.1 Specification

| Attribute | Value |
|-----------|-------|
| Provider | GitHub REST API |
| Auth | Token (optional, increases rate limit) |
| Rate Limit | 60/hr (unauth), 5000/hr (auth) |
| Timeout | 10 seconds |

#### 8.8.2 Edge Cases

| Edge Case | Scenario | Expected Behavior | Business Impact |
|-----------|----------|-------------------|-----------------|
| EC-GH-01 | Organization not found | Return "No GitHub organization found for [company]" | User informed, can try alternative name |
| EC-GH-02 | No public repositories | Return "Organization has no public repositories" | Indicates closed-source company |
| EC-GH-03 | Rate limit exceeded | If unauth, prompt for token; else backoff and retry | Graceful handling of limits |
| EC-GH-04 | API timeout | Retry once, then return partial data or skip | User gets available data |
| EC-GH-05 | Company uses different GitHub org name | Search by company name in org description | Better matching logic |
| EC-GH-06 | Very large org (>1000 repos) | Return top 10 by stars, note "Showing top repositories" | Representative sample |
| EC-GH-07 | Repo stats unavailable (e.g., forks) | Return available stats, note missing fields | Partial data with transparency |
| EC-GH-08 | Private organization | Return "Organization profile is private" | User understands limitation |

---

### 8.9 Module: HackerNews API Tool

#### 8.9.1 Specification

| Attribute | Value |
|-----------|-------|
| Provider | HackerNews Algolia API |
| Search Types | Stories, comments |
| Max Results | 20 |
| Timeout | 5 seconds |

#### 8.9.2 Edge Cases

| Edge Case | Scenario | Expected Behavior | Business Impact |
|-----------|----------|-------------------|-----------------|
| EC-HN-01 | No mentions found | Return "No HackerNews discussions found for [company]" | User informed of low visibility |
| EC-HN-02 | Only old mentions (>2 years) | Return with note "Most recent mention: [date]" | User knows recency |
| EC-HN-03 | Ambiguous company name | Filter by context (e.g., "Apple" + "tech" not "fruit") | Relevant results |
| EC-HN-04 | Highly negative sentiment | Return objectively, let LLM summarize sentiment | Unbiased reporting |
| EC-HN-05 | API rate limited | Backoff and retry | Slight delay, request succeeds |
| EC-HN-06 | Comment thread very long | Return top-level comments and top replies only | Manageable data size |
| EC-HN-07 | Search returns jobs posts only | Filter to stories/comments, note if only jobs found | Relevant content type |
| EC-HN-08 | Non-tech company with no presence | Return "Limited tech community discussion" | Sets appropriate expectations |

---

### 8.10 Module: Website Scraper Tool

#### 8.10.1 Specification

| Attribute | Value |
|-----------|-------|
| Method | HTTP GET + BeautifulSoup |
| Target Pages | Homepage, About, Careers, Products |
| Max Page Size | 1MB |
| Timeout | 15 seconds |

#### 8.10.2 Edge Cases

| Edge Case | Scenario | Expected Behavior | Business Impact |
|-----------|----------|-------------------|-----------------|
| EC-SC-01 | Website blocks scraping (403/robots.txt) | Return "Website restricts automated access" | User informed, alternative sources used |
| EC-SC-02 | JavaScript-rendered content | Note "Limited extraction (JS-rendered site)" | User knows limitation |
| EC-SC-03 | HTTPS certificate error | Skip with warning, try HTTP if available | Security maintained |
| EC-SC-04 | Website timeout | Retry once with longer timeout, then skip | Best effort attempt |
| EC-SC-05 | Redirect loop | Detect after 5 redirects, abort with error | Prevent infinite loops |
| EC-SC-06 | Non-HTML content (PDF, video) | Return "URL points to non-HTML content" | Clear error message |
| EC-SC-07 | Very large page (>1MB) | Truncate, parse what's retrieved | Resource limits respected |
| EC-SC-08 | No useful content extracted | Return "Unable to extract structured content" | Honest about limitations |
| EC-SC-09 | Paywall detected | Return "Content behind paywall" | User knows limitation |
| EC-SC-10 | CAPTCHA challenge | Return "Website requires human verification" | Clear explanation |

---

### 8.11 Module: Gmail Tool

#### 8.11.1 Specification

| Attribute | Value |
|-----------|-------|
| Provider | Google Gmail API |
| Auth | OAuth 2.0 |
| Scopes | gmail.readonly |
| Max Emails | 10 per request |

#### 8.11.2 Edge Cases

| Edge Case | Scenario | Expected Behavior | Business Impact |
|-----------|----------|-------------------|-----------------|
| EC-GM-01 | User not authenticated | Return "Please connect your Gmail account" with OAuth link | Clear call to action |
| EC-GM-02 | OAuth token expired | Attempt refresh, if fails prompt re-authentication | Seamless token refresh |
| EC-GM-03 | No emails match criteria | Return "No emails found from [sender] in last [period]" | User informed, can adjust criteria |
| EC-GM-04 | Too many emails match | Return most recent 10, note "Showing 10 of [X] emails" | Manageable result set |
| EC-GM-05 | Email contains sensitive data | Summarize without exposing PII, note "Sensitive content redacted" | Privacy protected |
| EC-GM-06 | Email in non-English | Return content, let LLM handle translation | Multilingual support |
| EC-GM-07 | Attachment-only email (no body) | Return "Email contains attachment: [filename]" | User knows email content type |
| EC-GM-08 | User revokes OAuth permission | Detect 401, prompt re-authorization | Clear recovery path |
| EC-GM-09 | Rate limit from Google | Backoff, retry, inform user of delay | Graceful rate limit handling |
| EC-GM-10 | Thread vs single email ambiguity | Default to full thread, allow "only last email" option | Flexible email retrieval |

---

### 8.12 Module: Google Calendar Tool

#### 8.12.1 Specification

| Attribute | Value |
|-----------|-------|
| Provider | Google Calendar API |
| Auth | OAuth 2.0 |
| Scopes | calendar.events |
| Actions | Create event, list events |

#### 8.12.2 Edge Cases

| Edge Case | Scenario | Expected Behavior | Business Impact |
|-----------|----------|-------------------|-----------------|
| EC-GC-01 | User not authenticated | Return "Please connect your Google Calendar" with OAuth link | Clear call to action |
| EC-GC-02 | OAuth token expired | Attempt refresh, if fails prompt re-authentication | Seamless token refresh |
| EC-GC-03 | Time slot conflict | Return "Conflict with [existing event]. Suggest alternative?" | User-friendly conflict resolution |
| EC-GC-04 | Invalid date/time format | Parse flexibly, confirm interpretation with user | "Did you mean Tuesday at 2pm?" |
| EC-GC-05 | Attendee email invalid | Validate format, warn if not valid email | Prevent failed invites |
| EC-GC-06 | Past date requested | Return "Cannot schedule in the past. Did you mean [future date]?" | Helpful correction |
| EC-GC-07 | Very far future (>1 year) | Allow but confirm "Scheduling for [date]. Confirm?" | Prevent accidental far-future events |
| EC-GC-08 | No calendar access | Check permissions, request appropriate scope | Clear permission error |
| EC-GC-09 | Recurring event complexity | Support basic recurrence, reject complex patterns with explanation | "Weekly events supported, complex rules not yet available" |
| EC-GC-10 | Timezone ambiguity | Default to user's calendar timezone, allow override | Correct timezone handling |
| EC-GC-11 | Meeting duration not specified | Default to 30 min, confirm with user | Sensible default |
| EC-GC-12 | Rate limit from Google | Backoff, retry, inform user | Graceful handling |

---

### 8.13 Module: Memory Manager

#### 8.13.1 Specification

| Attribute | Value |
|-----------|-------|
| Short-term Capacity | 20 messages |
| Long-term Storage | SQLite |
| Partitions | conversations, tool_traces, domain_context |
| TTL (short-term) | Session lifetime |

#### 8.13.2 Edge Cases

| Edge Case | Scenario | Expected Behavior | Business Impact |
|-----------|----------|-------------------|-----------------|
| EC-MM-01 | Short-term memory full (>20 msgs) | Summarize oldest 10, keep summary + recent 10 | Conversation continues seamlessly |
| EC-MM-02 | SQLite write failure | Retry, if persists use in-memory only, warn | No data loss during session |
| EC-MM-03 | Corrupted database file | Detect, backup corrupt file, create fresh | Recovery with data preservation attempt |
| EC-MM-04 | Very long conversation (>100 messages) | Aggressive summarization, keep key facts | Performance maintained |
| EC-MM-05 | Conflicting information in memory | Prefer recent over old, note discrepancy | Accurate context |
| EC-MM-06 | User requests memory clear | Clear all session data, confirm action | User control over data |
| EC-MM-07 | Cross-session context retrieval | Query by entity/topic, return relevant past conversations | Intelligent context |
| EC-MM-08 | Concurrent writes (multiple requests) | Use SQLite WAL mode, handle locks | Data integrity maintained |
| EC-MM-09 | Memory retrieval timeout | Return empty context, proceed without history | Graceful degradation |
| EC-MM-10 | Sensitive data in memory | Do not persist OAuth tokens, PII in long-term | Security maintained |

---

### 8.14 Module: Strategy Engine

#### 8.14.1 Specification

| Mode | Tools Available | Max Tool Calls | Timeout |
|------|-----------------|----------------|---------|
| Normal | Web Search, Wikipedia, Calculator | 5 | 30s |
| Deep | All 10 tools | 15 | 90s |

#### 8.14.2 Edge Cases

| Edge Case | Scenario | Expected Behavior | Business Impact |
|-----------|----------|-------------------|-----------------|
| EC-ST-01 | Mode switch mid-conversation | Apply new mode to next query, keep context | Flexible mode switching |
| EC-ST-02 | Deep mode but query only needs 1 tool | Use minimal tools, don't force all 10 | Efficient tool usage |
| EC-ST-03 | Normal mode but query needs Extended tool | Return best effort with Core tools, suggest Deep mode | User guided to appropriate mode |
| EC-ST-04 | Unknown query type | Default to Normal, escalate to Deep if insufficient | Progressive enhancement |
| EC-ST-05 | All relevant tools fail in Deep mode | Exhaust retries, offer user choice to continue or end | User control |
| EC-ST-06 | Timeout approaching | Synthesize answer from collected data, note incomplete | Partial results over timeout |

---

### 8.15 Module: Evaluation Harness

#### 8.15.1 Specification

| Attribute | Value |
|-----------|-------|
| Questions | 20 |
| Attempts per Question | 10 |
| Metrics | pass^5, pass^10, Tool Efficiency, Tool Success Rate |
| Output | JSON + CSV + PDF |

#### 8.15.2 Edge Cases

| Edge Case | Scenario | Expected Behavior | Business Impact |
|-----------|----------|-------------------|-----------------|
| EC-EH-01 | Evaluation interrupted mid-run | Save progress, allow resume from last completed question | No lost evaluation work |
| EC-EH-02 | Ground truth ambiguous | Allow multiple valid answers, use fuzzy matching | Fair evaluation |
| EC-EH-03 | Agent gives correct answer with wrong reasoning | Mark as correct (outcome-based), flag for review | Practical correctness |
| EC-EH-04 | All 10 attempts timeout | Record as failed, note timeout pattern | Identifies performance issues |
| EC-EH-05 | Answer within tolerance (5-10%) | Mark as correct, note approximation | Tolerance applied consistently |
| EC-EH-06 | Tool called but not needed | Penalize in Tool Efficiency metric | Identifies unnecessary calls |
| EC-EH-07 | Needed tool not called | Penalize in Tool Efficiency metric | Identifies missing tool usage |
| EC-EH-08 | Export fails mid-generation | Retry, if persists provide JSON fallback | User gets results |
| EC-EH-09 | Inconsistent answers across attempts | Low pass^k score, flag for investigation | Identifies reliability issues |
| EC-EH-10 | Database full during evaluation | Clean old runs, compress data | Evaluation completes |

---

### 8.16 Module: Dashboard Frontend

#### 8.16.1 Specification

| Component | Technology |
|-----------|------------|
| Framework | Vanilla JS |
| Styling | CSS3 with gradients |
| State | Local (sessionStorage) |
| API Calls | Fetch API |

#### 8.16.2 Edge Cases

| Edge Case | Scenario | Expected Behavior | Business Impact |
|-----------|----------|-------------------|-----------------|
| EC-DF-01 | API unreachable | Show "Connection error", retry button | Clear error state |
| EC-DF-02 | Slow response (>10s) | Show loading spinner with elapsed time | User knows request is processing |
| EC-DF-03 | Session expired | Redirect to login, preserve last state if possible | Minimal user friction |
| EC-DF-04 | Large evaluation result (>1000 entries) | Paginate, load on demand | Performance maintained |
| EC-DF-05 | Filter returns no results | Show "No results match filters", clear filters button | Clear empty state |
| EC-DF-06 | Export fails | Show error, offer retry, fallback to JSON | User gets data |
| EC-DF-07 | Mobile viewport | Responsive layout, hide non-essential elements | Usable on mobile |
| EC-DF-08 | Browser back button | Maintain state, don't break SPA routing | Natural navigation |
| EC-DF-09 | Copy response to clipboard | Show "Copied!" confirmation | User feedback |
| EC-DF-10 | Very long response text | Collapsible sections, "Show more" | Readable output |

---

### 8.17 Module: Dashboard Backend (API)

#### 8.17.1 Specification

| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/chat | POST | Send message, receive response |
| /api/evaluations | GET | List all evaluation runs |
| /api/evaluations/{id} | GET | Get specific evaluation details |
| /api/export/{format} | GET | Export results (csv/pdf) |
| /api/auth/google | GET/POST | OAuth flow |
| /api/health | GET | System health check |

#### 8.17.2 Edge Cases

| Edge Case | Scenario | Expected Behavior | Business Impact |
|-----------|----------|-------------------|-----------------|
| EC-DB-01 | Invalid JSON in request | Return 400 with validation error details | Developer-friendly errors |
| EC-DB-02 | Request body too large (>1MB) | Return 413, "Request too large" | Prevent resource exhaustion |
| EC-DB-03 | Missing required field | Return 422 with missing field name | Clear validation error |
| EC-DB-04 | Rate limit exceeded (API level) | Return 429 with Retry-After header | Standard rate limit response |
| EC-DB-05 | Internal server error | Return 500, log full traceback, show generic message | Security (no leak), debugging enabled |
| EC-DB-06 | Database connection lost | Attempt reconnect, return 503 if fails | Clear service unavailable |
| EC-DB-07 | Concurrent evaluation requests | Queue requests, max 1 concurrent evaluation | Prevent resource contention |
| EC-DB-08 | OAuth callback with error | Parse error, show user-friendly message | Clear OAuth failure handling |
| EC-DB-09 | Export of empty results | Return 404, "No data to export" | Clear empty state |
| EC-DB-10 | CORS preflight | Return appropriate headers | Cross-origin requests work |

---

### 8.18 Module: Authentication (Google OAuth)

#### 8.18.1 Specification

| Attribute | Value |
|-----------|-------|
| Provider | Google OAuth 2.0 |
| Scopes | gmail.readonly, calendar.events |
| Token Storage | Encrypted file |
| Token Refresh | Automatic |

#### 8.18.2 Edge Cases

| Edge Case | Scenario | Expected Behavior | Business Impact |
|-----------|----------|-------------------|-----------------|
| EC-AU-01 | User denies permission | Show "Permission required for [feature]", allow partial use | Graceful degradation |
| EC-AU-02 | OAuth state mismatch (CSRF) | Reject callback, show security error | Security maintained |
| EC-AU-03 | Refresh token expired | Prompt full re-authentication | Clear recovery path |
| EC-AU-04 | Multiple Google accounts | Allow selection, store per-account tokens | Multi-account support |
| EC-AU-05 | Token file corrupted | Delete and re-authenticate | Recovery from corruption |
| EC-AU-06 | OAuth provider down | Show "Google authentication unavailable", disable Gmail/Calendar tools | Graceful feature degradation |
| EC-AU-07 | Scope escalation needed | Request additional scopes incrementally | Minimal permission ask |
| EC-AU-08 | Token encryption key lost | Tokens unusable, require re-authentication | Security over convenience |

---

### 8.19 Module: Rate Limiter

#### 8.19.1 Specification

| Attribute | Value |
|-----------|-------|
| Algorithm | Token bucket |
| Scope | Per-tool |
| Storage | In-memory |
| Overflow Behavior | Queue with timeout |

#### 8.19.2 Edge Cases

| Edge Case | Scenario | Expected Behavior | Business Impact |
|-----------|----------|-------------------|-----------------|
| EC-RL-01 | Burst of requests | Queue excess, process at rate limit | No requests lost |
| EC-RL-02 | Queue full (>100 pending) | Reject new requests with 429 | Prevent memory exhaustion |
| EC-RL-03 | Server restart | Rate limit state lost, start fresh | Brief burst possible, acceptable for MVP |
| EC-RL-04 | Tool-specific rate limit hit | Only that tool affected, others continue | Isolated impact |
| EC-RL-05 | Clock skew | Use monotonic clock for timing | Accurate rate limiting |

---

### 8.20 Module: Cache

#### 8.20.1 Specification

| Attribute | Value |
|-----------|-------|
| Type | In-memory TTL cache |
| TTL | 15 minutes |
| Max Size | 1000 entries |
| Eviction | LRU |

#### 8.20.2 Edge Cases

| Edge Case | Scenario | Expected Behavior | Business Impact |
|-----------|----------|-------------------|-----------------|
| EC-CH-01 | Cache full | Evict LRU entries | Most recent data retained |
| EC-CH-02 | Stale data requested | Return stale if within TTL, else refetch | Balance freshness vs speed |
| EC-CH-03 | Cache key collision | Use hash of full request, not just query | Correct cache hits |
| EC-CH-04 | Server restart | Cache lost, cold start | Acceptable for MVP |
| EC-CH-05 | Negative caching (not found) | Cache "not found" for 5 min | Prevent repeated failures |

---

## 9. API Specifications

### 9.1 Chat API

#### POST /api/chat

**Request:**
```json
{
  "message": "string (required, max 2000 chars)",
  "session_id": "string (optional, UUID)",
  "mode": "normal | deep (default: normal)",
  "stream": "boolean (default: false)"
}
```

**Response:**
```json
{
  "response": "string",
  "session_id": "string",
  "tool_calls": [
    {
      "tool": "string",
      "input": {},
      "output": {},
      "latency_ms": "number",
      "success": "boolean"
    }
  ],
  "sources": ["string"],
  "disclaimer": "string | null",
  "user_action_required": {
    "type": "search_more | authenticate | clarify",
    "message": "string"
  } | null
}
```

**Error Responses:**
| Code | Condition |
|------|-----------|
| 400 | Invalid request format |
| 413 | Message too long |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 503 | Service unavailable |

---

### 9.2 Evaluations API

#### GET /api/evaluations

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| limit | int | Max results (default: 20) |
| offset | int | Pagination offset |
| category | string | Filter by category |
| date_from | ISO date | Start date filter |
| date_to | ISO date | End date filter |

**Response:**
```json
{
  "evaluations": [
    {
      "id": "string",
      "timestamp": "ISO datetime",
      "total_questions": "number",
      "metrics": {
        "pass_5": "number",
        "pass_10": "number",
        "tool_efficiency": "number",
        "tool_success_rate": "number"
      }
    }
  ],
  "total": "number",
  "limit": "number",
  "offset": "number"
}
```

#### GET /api/evaluations/{id}

**Response:**
```json
{
  "id": "string",
  "timestamp": "ISO datetime",
  "config": {},
  "metrics": {},
  "questions": [
    {
      "id": "string",
      "question": "string",
      "category": "string",
      "attempts": [
        {
          "answer": "string",
          "correct": "boolean",
          "tool_calls": [],
          "latency_ms": "number"
        }
      ],
      "consensus_answer": "string",
      "pass_5": "boolean",
      "pass_10": "boolean"
    }
  ]
}
```

---

### 9.3 Export API

#### GET /api/export/{format}

**Path Parameters:**
| Param | Values |
|-------|--------|
| format | csv, pdf |

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| evaluation_id | string | Specific evaluation (optional) |
| category | string | Filter by category |

**Response:**
- CSV: `Content-Type: text/csv`
- PDF: `Content-Type: application/pdf`

---

### 9.4 Auth API

#### GET /api/auth/google

Initiates OAuth flow, redirects to Google.

#### GET /api/auth/google/callback

**Query Parameters:**
| Param | Description |
|-------|-------------|
| code | Authorization code |
| state | CSRF token |

**Response:**
Redirects to dashboard with session established.

---

### 9.5 Health API

#### GET /api/health

**Response:**
```json
{
  "status": "healthy | degraded | unhealthy",
  "components": {
    "database": "ok | error",
    "llm": "ok | error",
    "tools": {
      "web_search": "ok | error",
      "wikipedia": "ok | error",
      ...
    }
  },
  "google_auth": "connected | not_connected"
}
```

---

## 10. Data Models

### 10.1 Database Schema (SQLite)

```sql
-- Conversations table
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'user' | 'assistant'
    content TEXT NOT NULL,
    mode TEXT,  -- 'normal' | 'deep'
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id),
    INDEX idx_timestamp (timestamp)
);

-- Tool traces table
CREATE TABLE tool_traces (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    conversation_id TEXT,
    tool_name TEXT NOT NULL,
    input_data TEXT,  -- JSON
    output_data TEXT,  -- JSON
    latency_ms INTEGER,
    success BOOLEAN,
    error_message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id),
    INDEX idx_session_tool (session_id, tool_name)
);

-- Domain context table (for long-term memory)
CREATE TABLE domain_context (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    entity_type TEXT,  -- 'company' | 'person' | 'topic'
    entity_name TEXT,
    facts TEXT,  -- JSON array of facts
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_entity (entity_type, entity_name)
);

-- Evaluation runs table
CREATE TABLE evaluation_runs (
    id TEXT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    config TEXT,  -- JSON
    metrics TEXT,  -- JSON
    status TEXT,  -- 'running' | 'completed' | 'failed'
    questions_completed INTEGER DEFAULT 0,
    total_questions INTEGER
);

-- Evaluation results table
CREATE TABLE evaluation_results (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    question_text TEXT,
    category TEXT,
    ground_truth TEXT,
    attempts TEXT,  -- JSON array
    consensus_answer TEXT,
    pass_5 BOOLEAN,
    pass_10 BOOLEAN,
    tool_efficiency REAL,
    FOREIGN KEY (run_id) REFERENCES evaluation_runs(id)
);

-- OAuth tokens table
CREATE TABLE oauth_tokens (
    id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,  -- 'google'
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,
    expires_at DATETIME,
    scopes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 10.2 Pydantic Models

```python
# shared/models.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=2000)
    session_id: Optional[str] = None
    mode: Literal["normal", "deep"] = "normal"
    stream: bool = False

class ToolCall(BaseModel):
    tool: str
    input: Dict[str, Any]
    output: Dict[str, Any]
    latency_ms: int
    success: bool
    error: Optional[str] = None

class UserAction(BaseModel):
    type: Literal["search_more", "authenticate", "clarify"]
    message: str

class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_calls: List[ToolCall]
    sources: List[str]
    disclaimer: Optional[str] = None
    user_action_required: Optional[UserAction] = None

class EvaluationMetrics(BaseModel):
    pass_5: float
    pass_10: float
    tool_efficiency: float
    tool_success_rate: float

class EvaluationSummary(BaseModel):
    id: str
    timestamp: datetime
    total_questions: int
    metrics: EvaluationMetrics

class QuestionAttempt(BaseModel):
    answer: str
    correct: bool
    tool_calls: List[ToolCall]
    latency_ms: int

class QuestionResult(BaseModel):
    id: str
    question: str
    category: str
    ground_truth: str
    attempts: List[QuestionAttempt]
    consensus_answer: str
    pass_5: bool
    pass_10: bool
    tool_efficiency: float

class EvaluationDetail(BaseModel):
    id: str
    timestamp: datetime
    config: Dict[str, Any]
    metrics: EvaluationMetrics
    questions: List[QuestionResult]

class HealthStatus(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    components: Dict[str, str]
    google_auth: Literal["connected", "not_connected"]
```

---

## 11. Evaluation Framework

### 11.1 Dataset Specification

**Total Questions**: 20
**Categories**: 4 (5 questions each)
**Attempts per Question**: 10

#### Category 1: Company Research (5 questions)

| ID | Question | Expected Tools | Ground Truth |
|----|----------|----------------|--------------|
| CR-01 | "When was Stripe founded and who are the founders?" | Wikipedia, Web Search | 2010, Patrick & John Collison |
| CR-02 | "What is Databricks' primary product offering?" | Wikipedia, Web Search, Website Scraper | Unified Analytics Platform, Lakehouse |
| CR-03 | "Where is Figma headquartered?" | Wikipedia, Web Search | San Francisco, CA |
| CR-04 | "Who is the CEO of Notion?" | Wikipedia, Web Search | Ivan Zhao |
| CR-05 | "What industry does Cloudflare operate in?" | Wikipedia, Web Search | CDN, Internet Security, DDoS protection |

#### Category 2: Financial Analysis (5 questions)

| ID | Question | Expected Tools | Ground Truth |
|----|----------|----------------|--------------|
| FA-01 | "What is Snowflake's current market cap?" | Yahoo Finance | ~$50-60B (with tolerance) |
| FA-02 | "What was Apple's revenue in fiscal year 2023?" | Yahoo Finance, SEC EDGAR | ~$383B |
| FA-03 | "What is Microsoft's P/E ratio?" | Yahoo Finance | ~35-40 (with tolerance) |
| FA-04 | "Calculate Salesforce's revenue growth rate YoY" | Yahoo Finance, Calculator | ~10-15% |
| FA-05 | "What is Amazon's gross profit margin?" | Yahoo Finance, SEC EDGAR, Calculator | ~45-47% |

#### Category 3: Competitive Intelligence (5 questions)

| ID | Question | Expected Tools | Ground Truth |
|----|----------|----------------|--------------|
| CI-01 | "Compare Slack vs Microsoft Teams user base" | Web Search, Wikipedia | Teams: ~300M, Slack: ~20M |
| CI-02 | "Who are the main competitors to Datadog?" | Web Search, Wikipedia | New Relic, Dynatrace, Splunk |
| CI-03 | "Which is larger by revenue: Oracle or SAP?" | Yahoo Finance | Oracle > SAP |
| CI-04 | "Compare GitHub vs GitLab primary differences" | Wikipedia, Web Search | GitHub: Microsoft-owned, GitLab: DevOps platform |
| CI-05 | "What is Zoom's market share in video conferencing?" | Web Search | ~15-20% (with tolerance) |

#### Category 4: Action Execution (5 questions)

| ID | Question | Expected Tools | Ground Truth |
|----|----------|----------------|--------------|
| AE-01 | "Summarize my last email from [test sender]" | Gmail | Correct summary of email content |
| AE-02 | "What meetings do I have tomorrow?" | Google Calendar | Correct list of events |
| AE-03 | "Schedule a 30-minute meeting titled 'Test' for next Monday at 2pm" | Google Calendar | Event created correctly |
| AE-04 | "How many unread emails do I have from [domain]?" | Gmail, Calculator | Correct count |
| AE-05 | "What is my next free 1-hour slot this week?" | Google Calendar | Correct available slot |

### 11.2 Metrics Specification

#### Metric 1: pass^k (Consensus Voting)

**Definition**: Run k attempts, take majority vote, check if majority answer is correct.

**Formula**:
```
pass^k = (questions where majority_answer == ground_truth) / total_questions
```

**Implementation**:
```python
def compute_pass_k(attempts: List[str], ground_truth: str, k: int) -> bool:
    # Take first k attempts
    k_attempts = attempts[:k]

    # Count answer frequencies
    answer_counts = Counter(normalize_answer(a) for a in k_attempts)

    # Get majority answer (most common)
    majority_answer, count = answer_counts.most_common(1)[0]

    # Check if majority (>50%) and correct
    is_majority = count > k / 2
    is_correct = fuzzy_match(majority_answer, ground_truth, tolerance=0.1)

    return is_majority and is_correct
```

**Targets**:
- pass^5 ≥ 80%
- pass^10 ≥ 85%

#### Metric 2: Tool Efficiency

**Definition**: Ratio of optimal tool calls to actual tool calls.

**Formula**:
```
tool_efficiency = min(optimal_tools, actual_tools) / max(optimal_tools, actual_tools)
```

**Interpretation**:
- 1.0 = Perfect (used exactly the right tools)
- <1.0 = Suboptimal (too many or too few tools)

**Target**: ≥ 75%

#### Metric 3: Tool Success Rate

**Definition**: Percentage of tool calls that returned useful data.

**Formula**:
```
tool_success_rate = successful_tool_calls / total_tool_calls
```

**What counts as successful**:
- Tool returned non-empty, relevant data
- No error occurred
- Response was used in final answer

**Target**: ≥ 90%

### 11.3 Evaluation Process

```
1. Load dataset (20 questions)
2. For each question:
   a. Run 10 attempts with temperature=0.6
   b. For each attempt:
      - Record answer
      - Record all tool calls (input, output, latency, success)
      - Record total latency
   c. Compute consensus answer (majority vote)
   d. Compute pass^5 (using first 5 attempts)
   e. Compute pass^10 (using all 10 attempts)
   f. Compute tool efficiency (compare to expected tools)
   g. Compute tool success rate
3. Aggregate metrics across all questions
4. Save results to database and JSON file
5. Generate reports (CSV, PDF)
```

---

## 12. Security & Compliance

### 12.1 Data Security

| Aspect | Implementation |
|--------|----------------|
| API Keys | Environment variables only, never logged |
| OAuth Tokens | AES-256 encrypted at rest |
| User Data | Session-isolated, no cross-user access |
| Database | File permissions restricted (600) |
| HTTPS | Enforced in production |

### 12.2 Input Validation

| Input | Validation |
|-------|------------|
| Chat message | Max 2000 chars, sanitized |
| Session ID | UUID format enforced |
| File paths | No path traversal allowed |
| Tool inputs | Schema-validated per tool |

### 12.3 Rate Limiting

| Level | Limit |
|-------|-------|
| API (global) | 100 req/min per IP |
| Chat endpoint | 20 req/min per session |
| Tool (individual) | Per-tool limits (see 8.2.2) |

### 12.4 Logging & Audit

| Event | Logged |
|-------|--------|
| API requests | Method, path, status, latency |
| Tool calls | Tool name, success/failure, latency |
| Auth events | Login, logout, token refresh |
| Errors | Full traceback (not exposed to user) |

**Excluded from logs**:
- API keys
- OAuth tokens
- Email content
- User PII

---

## 13. Deployment & Operations

### 13.1 Local Development

```bash
# Clone repository
git clone [repo]
cd bardeen-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with API keys

# Run database migrations
python -m src.storage.migrate

# Start development server
python start_dashboard.py --port 8000
```

### 13.2 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| ANTHROPIC_API_KEY | Yes | Claude API key |
| GOOGLE_CLIENT_ID | Yes | Google OAuth client ID |
| GOOGLE_CLIENT_SECRET | Yes | Google OAuth client secret |
| GITHUB_TOKEN | No | Increases GitHub rate limit |
| DATABASE_PATH | No | SQLite path (default: data/agent.db) |
| LOG_LEVEL | No | Logging level (default: INFO) |
| ENCRYPTION_KEY | Yes | For OAuth token encryption |

### 13.3 Health Monitoring

**Health Check Endpoint**: `GET /api/health`

**Monitoring Points**:
- Database connectivity
- LLM API availability
- Tool availability (sample check)
- OAuth token validity

### 13.4 Backup & Recovery

| Data | Backup Strategy |
|------|-----------------|
| SQLite database | Daily file copy |
| Evaluation results | Retained indefinitely |
| OAuth tokens | Encrypted backup |

---

## 14. Risks & Mitigations

### 14.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM API rate limiting | Medium | High | Implement backoff, queue requests |
| Tool API changes | Medium | Medium | Abstract tool interfaces, version pin |
| DuckDuckGo blocking | Medium | Medium | Implement delays, fallback to Wikipedia |
| OAuth token expiry | Low | Medium | Automatic refresh, clear re-auth UX |
| Database corruption | Low | High | WAL mode, regular backups |

### 14.2 Business Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Inaccurate financial data | Medium | High | Disclaimers, tolerance bands, source attribution |
| Email/calendar privacy concerns | Medium | High | Minimal scopes, clear permissions |
| Evaluation metrics gaming | Low | Medium | Multiple metrics, human review |
| User expects perfection | High | Medium | Set expectations, show confidence levels |

### 14.3 Dependency Risks

| Dependency | Risk | Mitigation |
|------------|------|------------|
| Claude API | Service outage | Cache recent responses, graceful error |
| Google APIs | OAuth changes | Monitor deprecation notices |
| yfinance | Unofficial, may break | Have web search fallback |
| duckduckgo-search | Unofficial | Rate limit, have Wikipedia fallback |

---

## 15. Timeline & Milestones

### 15.1 Development Phases

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **Phase 1: Core Agent** | Week 1 | LLM client, 3 core tools, basic chat |
| **Phase 2: Extended Tools** | Week 2 | 7 additional tools, mode switching |
| **Phase 3: Memory & Auth** | Week 3 | Short/long-term memory, Google OAuth |
| **Phase 4: Evaluation** | Week 4 | Harness, metrics, dataset |
| **Phase 5: Dashboard** | Week 5 | Full UI, export, filters |
| **Phase 6: Polish** | Week 6 | Edge cases, testing, documentation |

### 15.2 Milestones

| Milestone | Target | Criteria |
|-----------|--------|----------|
| M1: MVP Agent | End Week 2 | 10 tools working, basic chat |
| M2: Evaluation Ready | End Week 4 | Can run full evaluation |
| M3: Dashboard Complete | End Week 5 | All UI features working |
| M4: Production Ready | End Week 6 | All edge cases handled, documented |

### 15.3 Definition of Done

- [ ] All functional requirements implemented
- [ ] All edge cases handled
- [ ] pass^5 ≥ 80%, pass^10 ≥ 85%
- [ ] Tool Efficiency ≥ 75%, Success Rate ≥ 90%
- [ ] Dashboard fully functional
- [ ] Export working (CSV + PDF)
- [ ] Documentation complete
- [ ] Code reviewed

---

## 16. Appendix

### 16.1 Glossary

| Term | Definition |
|------|------------|
| **pass^k** | Consensus-based accuracy metric using k attempts |
| **Tool Efficiency** | Ratio of optimal to actual tool usage |
| **Tool Success Rate** | Percentage of tool calls returning useful data |
| **Normal Mode** | Research using 2-3 core tools |
| **Deep Mode** | Research using 5-10 tools |
| **Short-term Memory** | In-session conversation context |
| **Long-term Memory** | Persisted facts and history |

### 16.2 References

- Claude API Documentation: https://docs.anthropic.com
- Google OAuth 2.0: https://developers.google.com/identity/protocols/oauth2
- SEC EDGAR API: https://www.sec.gov/developer
- GitHub REST API: https://docs.github.com/en/rest
- HackerNews API: https://hn.algolia.com/api

### 16.3 Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-30 | Initial PRD |

---

**Document Status**: Draft for Review
**Next Review Date**: [TBD]
**Approvers**: [TBD]
