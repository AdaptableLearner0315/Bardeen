### Product Requirements Document (PRD)
# B2B Account Intelligence Agent

**Version**: 3.0
**Date**: February 1, 2026
**Author**: Engineering Team
**Status**: Implementation Complete

> **What's New in v3.0**: B2B-aligned evaluation dataset (24 questions), LLM-as-Judge with 4-dimension scoring, depth-aware metrics for long-horizon planning, per-step pass^k consistency metrics, updated dashboard with B2B examples.

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
| **Multi-Tool Orchestration** | 6 integrated tools with intelligent selection |
| **Auto Mode Detection** | AI automatically detects query complexity (Normal vs Deep) |
| **Strict Response Guidelines** | 50-60 words (Normal), Summary + Details (Deep) |
| **Perplexity Integration** | Deep research with sonar/sonar-pro models |
| **Memory Architecture** | Short-term + Long-term memory with SQLite persistence |
| **Trace Storage** | All tool calls persisted for analysis and debugging |
| **B2B-Aligned Evaluation** | 24 domain-specific questions across 4 B2B categories |
| **LLM-as-Judge** | 4-dimension scoring (Tool Selection, Execution, Reasoning, Answer) |
| **Depth-Aware Metrics** | Per-step pass^k for long-horizon planning evaluation |
| **Production-Ready** | Real Gmail/Calendar integration via Google OAuth |

### 1.3 Success Criteria

| Metric | Target | Description |
|--------|--------|-------------|
| pass^5 | ≥ 80% | Consensus accuracy with 5 attempts |
| pass^10 | ≥ 85% | Consensus accuracy with 10 attempts |
| Tool Precision | ≥ 80% | Correct tools / Total tools used |
| Tool Recall | ≥ 70% | Correct tools / Expected tools |
| Accuracy Score | ≥ 7.5/10 | LLM judge accuracy rating |
| Completeness Score | ≥ 7.0/10 | LLM judge completeness rating |
| Avg Depth | ≥ 2.0 | Average reasoning steps per query |
| pass^5_step1 | ≥ 70% | First tool consistency across attempts |
| Overall Pass Rate | ≥ 75% | Questions passing all criteria |
| Response Latency | < 15s | P95 latency (Deep mode) |

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
| **Tool Precision** | Correct tools / Used tools | ≥ 80% |
| **Tool Recall** | Correct tools / Expected tools | ≥ 70% |
| **Reliability** | Tool success rate | ≥ 90% |
| **Performance** | P95 latency (Deep mode) | < 20s |

### 3.2 B2B-Specific Goals

| Goal | Metric | Target |
|------|--------|--------|
| **Company Research Accuracy** | Category pass rate | ≥ 80% |
| **Financial Analysis Accuracy** | Category pass rate | ≥ 75% |
| **Competitive Intelligence** | Category pass rate | ≥ 75% |
| **Action Execution** | Category pass rate | ≥ 70% |
| **Planning Depth** | Average reasoning steps | ≥ 2.0 |
| **Step Consistency** | pass^5_step1 | ≥ 70% |

### 3.3 Secondary Goals

| Goal | Metric | Target |
|------|--------|--------|
| **User Experience** | Successful query completion | ≥ 95% |
| **Graceful Degradation** | Partial results on tool failure | 100% |
| **Memory Utilization** | Context relevance in follow-ups | ≥ 80% |

### 3.4 Out of Scope for MVP

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
| FR-5.4 | Perplexity | Deep research with citations | P0 |

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
| FR-9.5 | Dashboard SHALL show B2B-aligned example queries | P0 |
| FR-9.6 | Dashboard SHALL display depth metrics after multi-tool queries | P1 |

#### FR-10: Evaluation Viewer

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-10.1 | Dashboard SHALL display all evaluation runs | P0 |
| FR-10.2 | Dashboard SHALL show pass^5, pass^10, Tool Precision, Tool Recall | P0 |
| FR-10.3 | Dashboard SHALL show LLM Judge scores (4 dimensions) | P0 |
| FR-10.4 | Dashboard SHALL show depth metrics (max depth, avg step score) | P0 |
| FR-10.5 | Dashboard SHALL allow filtering by date, category, metric | P0 |
| FR-10.6 | Dashboard SHALL support drill-down into individual question results | P1 |

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
| NFR-1.5 | LLM Judge evaluation time | < 5s per question |

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
│  │  │ [Normal│Deep]│  │  B2B Metrics │  │  By Category │  │             │  │    │
│  │  │   Toggle     │  │  Depth Stats │  │  By Date     │  │             │  │    │
│  │  │ B2B Examples │  │  LLM Judge   │  │              │  │             │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ HTTP/REST
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              API GATEWAY (FastAPI)                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ POST /chat  │  │ GET /evals  │  │ GET /export │  │ GET /b2b-evaluations   │ │
│  │             │  │ GET /b2b-   │  │             │  │ GET /b2b-dataset       │ │
│  └──────┬──────┘  │   dataset   │  └──────┬──────┘  └───────────┬─────────────┘ │
│         └─────────┴─────────────┴─────────┴─────────────────────┘               │
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
│  │  Claude Sonnet 4  │  │  Normal │ Deep    │  │  Short-term │ Long-term     │  │
│  └─────────┬─────────┘  └─────────┬─────────┘  └──────────────┬──────────────┘  │
│            └──────────────────────┼───────────────────────────┘                  │
│                                   │                                              │
│                                   ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         Tool Registry                                    │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │    │
│  │  │ CORE: Web Search │ Wikipedia │ Calculator │ Perplexity          │    │    │
│  │  ├─────────────────────────────────────────────────────────────────┤    │    │
│  │  │ ACTION: Gmail │ Google Calendar                                 │    │    │
│  │  └─────────────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            EVALUATION LAYER                                      │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌───────────────────────┐  │
│  │   Evaluation Harness │  │   LLM Judge          │  │   Metrics Engine      │  │
│  │  - EvaluationHarness │  │  - 4-dim scoring     │  │  - pass^k             │  │
│  │  - B2BEvalHarness    │  │  - Tool Selection    │  │  - B2B Metrics        │  │
│  │                      │  │  - Tool Execution    │  │  - Depth Metrics      │  │
│  │                      │  │  - Reasoning         │  │  - Per-Step pass^k    │  │
│  │                      │  │  - Answer Quality    │  │                       │  │
│  └──────────────────────┘  └──────────────────────┘  └───────────────────────┘  │
│  ┌──────────────────────┐  ┌──────────────────────┐                             │
│  │   Tracers            │  │   Dataset            │                             │
│  │  - ToolTracer        │  │  - b2b_dataset.json  │                             │
│  │  - ErrorTracer       │  │  - 24 questions      │                             │
│  │  - StepTracer        │  │  - 4 categories      │                             │
│  └──────────────────────┘  └──────────────────────┘                             │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            STORAGE LAYER                                         │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌───────────────────────┐  │
│  │   SQLite Database    │  │   In-Memory Cache    │  │    File Storage       │  │
│  │  - conversations     │  │  - Tool responses    │  │  - eval_results/      │  │
│  │  - tool_traces       │  │  - Rate limit state  │  │  - exports/           │  │
│  │  - eval_runs         │  │  - Session data      │  │  - b2b_dataset.json   │  │
│  │  - b2b_eval_results  │  │                      │  │                       │  │
│  └──────────────────────┘  └──────────────────────┘  └───────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Technology Stack

| Layer | Technology | Version | Rationale |
|-------|------------|---------|-----------|
| **LLM** | Claude Sonnet 4 | Latest | Best tool calling, reasoning |
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
| Model | claude-sonnet-4-20250514 |
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
| Total Tools | 6 |
| Core Tools | 4 (Web Search, Wikipedia, Calculator, Perplexity) |
| Action Tools | 2 (Gmail, Calendar) |
| Fallback Chains | web_search → wikipedia |
| Max Retries | 2 per tool |

#### 8.2.2 Tool Configuration

| Tool | Mode | Rate Limit | Timeout | Fallback |
|------|------|------------|---------|----------|
| Web Search | Core | 1 req/sec | 10s | Wikipedia |
| Wikipedia | Core | 10 req/sec | 5s | None |
| Calculator | Core | Unlimited | 1s | None |
| Perplexity | Extended | 2 req/sec | 30s | Web Search |
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

### 8.3 Module: LLM Judge

#### 8.3.1 Specification

| Attribute | Value |
|-----------|-------|
| Model | Claude (same as agent) |
| Dimensions | 4 (Tool Selection, Tool Execution, Reasoning, Answer) |
| Score Range | 0-25 per dimension (100 total) |
| Timeout | 30 seconds |

#### 8.3.2 Scoring Dimensions

| Dimension | Weight | Criteria |
|-----------|--------|----------|
| Tool Selection | 25% | Right tool for query type, avoided unnecessary tools |
| Tool Execution | 25% | Good parameters, result used correctly |
| Reasoning | 25% | Explained tool choice, logical flow to answer |
| Answer Quality | 25% | Factually correct, well-structured, appropriate length |

#### 8.3.3 Edge Cases

| Edge Case | Scenario | Expected Behavior | Business Impact |
|-----------|----------|-------------------|-----------------|
| EC-LJ-01 | Judge API timeout | Retry once, then mark as "evaluation_failed" | Results flagged for review |
| EC-LJ-02 | Malformed judge response | Parse available scores, flag missing dimensions | Partial scoring available |
| EC-LJ-03 | Judge disagrees with ground truth | Log discrepancy, use ground truth for pass/fail | Human review enabled |
| EC-LJ-04 | No tool calls in response | Score Tool Selection/Execution as 0 | Accurate penalty for missing tools |

---

### 8.4 Module: Depth Metrics

#### 8.4.1 Specification

| Attribute | Value |
|-----------|-------|
| Max Tracked Depth | 10 steps |
| Pass^k Threshold | 60% consensus |
| Depth Multiplier | 1.0 + 0.1 × (depth - 1) |

#### 8.4.2 Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| Max Depth | max(steps per query) | ≥ 4 |
| Avg Depth | sum(steps) / total queries | ≥ 2.0 |
| Avg Step Score | sum(step_scores) / total steps | ≥ 20/25 |
| Depth-Weighted Score | avg_step_score × depth_multiplier | ≥ 80/100 |
| pass^k_stepN | % attempts with same tool at step N | ≥ 60% |

#### 8.4.3 Edge Cases

| Edge Case | Scenario | Expected Behavior | Business Impact |
|-----------|----------|-------------------|-----------------|
| EC-DM-01 | Single-tool query | Depth = 1, no depth bonus | Simple queries scored fairly |
| EC-DM-02 | Inconsistent step count across attempts | Use max depth, pad with None | Comparable metrics |
| EC-DM-03 | Tool order varies but same tools used | Track by step index, not tool name | Order matters for pass^k |
| EC-DM-04 | Very deep chain (>10 steps) | Cap at 10, flag for review | Prevent infinite metrics |

---

### 8.5 Module: Step Tracer

#### 8.5.1 Specification

| Attribute | Value |
|-----------|-------|
| Storage | In-memory per query, persisted to SQLite |
| Tracked Fields | tool_name, params, reasoning, score, timestamp |
| Context Manager | Supports with statement |

#### 8.5.2 Edge Cases

| Edge Case | Scenario | Expected Behavior | Business Impact |
|-----------|----------|-------------------|-----------------|
| EC-ST-01 | Nested tool calls | Flatten to sequential steps | Accurate depth tracking |
| EC-ST-02 | Tool call fails mid-execution | Record failure, include in trace | Complete execution record |
| EC-ST-03 | Parallel tool calls | Record as same depth level | Accurate representation |
| EC-ST-04 | Missing reasoning | Default to "No reasoning provided" | Complete traces always |

---

### 8.6 Module: B2B Metrics

#### 8.6.1 Specification

| Attribute | Value |
|-----------|-------|
| Categories | 4 (Company, Financial, Competitive, Action) |
| Metrics per Category | Precision, Recall, F1, Pass Rate |
| Aggregation | Weighted average by category |

#### 8.6.2 Category Targets

| Category | Pass Rate Target | Tool Precision Target |
|----------|------------------|----------------------|
| Company Research | ≥ 80% | ≥ 85% |
| Financial Analysis | ≥ 75% | ≥ 80% |
| Competitive Intelligence | ≥ 75% | ≥ 75% |
| Action Execution | ≥ 70% | ≥ 70% |

---

## 9. API Specifications

### 9.1 Chat API

#### POST /api/chat

**Request:**
```json
{
  "message": "string (required, max 2000 chars)",
  "session_id": "string (optional, UUID)",
  "mode": "normal | deep | auto (default: auto)",
  "stream": "boolean (default: false)"
}
```

**Response:**
```json
{
  "answer": "string",
  "session_id": "string",
  "mode": "normal | deep",
  "is_auto_detected": "boolean",
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
  "latency_ms": "number",
  "depth_metrics": {
    "max_depth": "number",
    "avg_step_score": "number",
    "depth_weighted_score": "number"
  }
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
        "tool_precision": "number",
        "tool_recall": "number"
      }
    }
  ],
  "total": "number",
  "limit": "number",
  "offset": "number"
}
```

---

### 9.3 B2B Evaluation API

#### GET /api/b2b-dataset

**Response:**
```json
{
  "questions": [
    {
      "id": "string",
      "question": "string",
      "category": "company_research | financial_analysis | competitive_intelligence | action_execution",
      "expected_tools": ["string"],
      "evaluation_criteria": "string",
      "difficulty": "easy | medium | hard"
    }
  ],
  "total": "number",
  "categories": {
    "company_research": 6,
    "financial_analysis": 6,
    "competitive_intelligence": 6,
    "action_execution": 6
  }
}
```

#### GET /api/b2b-evaluations

**Response:**
```json
{
  "evaluations": [
    {
      "id": "string",
      "timestamp": "ISO datetime",
      "dataset": "b2b_dataset.json",
      "metrics": {
        "pass_5": "number",
        "pass_10": "number",
        "tool_precision": "number",
        "tool_recall": "number",
        "accuracy_score": "number",
        "completeness_score": "number"
      },
      "depth_metrics": {
        "avg_depth": "number",
        "max_depth": "number",
        "avg_step_score": "number",
        "depth_weighted_score": "number"
      },
      "category_metrics": {
        "company_research": {"pass_rate": "number", "precision": "number"},
        "financial_analysis": {"pass_rate": "number", "precision": "number"},
        "competitive_intelligence": {"pass_rate": "number", "precision": "number"},
        "action_execution": {"pass_rate": "number", "precision": "number"}
      }
    }
  ]
}
```

---

### 9.4 Export API

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
| include_depth | boolean | Include depth metrics (default: true) |

**Response:**
- CSV: `Content-Type: text/csv`
- PDF: `Content-Type: application/pdf`

---

### 9.5 Health API

#### GET /api/health

**Response:**
```json
{
  "status": "healthy | degraded | unhealthy",
  "agent_initialized": "boolean",
  "components": {
    "database": "ok | error",
    "llm": "ok | error",
    "tools": {
      "web_search": "ok | error",
      "wikipedia": "ok | error",
      "calculator": "ok | error",
      "perplexity": "ok | error",
      "gmail": "ok | error | not_configured",
      "google_calendar": "ok | error | not_configured"
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
    step_index INTEGER,  -- For depth tracking
    reasoning TEXT,      -- Why tool was chosen
    step_score REAL,     -- Score for this step
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id),
    INDEX idx_session_tool (session_id, tool_name)
);

-- B2B Evaluation runs table
CREATE TABLE b2b_evaluation_runs (
    id TEXT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    dataset_path TEXT,
    config TEXT,  -- JSON
    metrics TEXT,  -- JSON (includes pass^k, B2B metrics, depth metrics)
    depth_metrics TEXT,  -- JSON
    category_metrics TEXT,  -- JSON
    status TEXT,  -- 'running' | 'completed' | 'failed'
    questions_completed INTEGER DEFAULT 0,
    total_questions INTEGER
);

-- B2B Evaluation results table
CREATE TABLE b2b_evaluation_results (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    question_text TEXT,
    category TEXT,
    expected_tools TEXT,  -- JSON array
    evaluation_criteria TEXT,
    attempts TEXT,  -- JSON array
    consensus_answer TEXT,
    pass_5 BOOLEAN,
    pass_10 BOOLEAN,
    judge_scores TEXT,  -- JSON (4 dimension scores)
    depth_metrics TEXT,  -- JSON (per-question depth)
    tool_precision REAL,
    tool_recall REAL,
    FOREIGN KEY (run_id) REFERENCES b2b_evaluation_runs(id)
);

-- Step traces table (for depth tracking)
CREATE TABLE step_traces (
    id TEXT PRIMARY KEY,
    query_id TEXT NOT NULL,
    attempt_index INTEGER,
    step_index INTEGER,
    tool_name TEXT,
    tool_params TEXT,  -- JSON
    reasoning TEXT,
    step_score REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_query_step (query_id, step_index)
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
    mode: Literal["normal", "deep", "auto"] = "auto"
    stream: bool = False

class ToolCall(BaseModel):
    tool: str
    input: Dict[str, Any]
    output: Dict[str, Any]
    latency_ms: int
    success: bool
    error: Optional[str] = None

class DepthMetrics(BaseModel):
    max_depth: int
    avg_step_score: float
    depth_weighted_score: float

class ChatResponse(BaseModel):
    answer: str
    session_id: str
    mode: Literal["normal", "deep"]
    is_auto_detected: bool
    tool_calls: List[ToolCall]
    sources: List[str]
    latency_ms: int
    depth_metrics: Optional[DepthMetrics] = None

# LLM Judge Models
class DimensionScore(BaseModel):
    dimension: Literal["tool_selection", "tool_execution", "reasoning", "answer_quality"]
    score: int = Field(..., ge=0, le=25)
    reasoning: str

class JudgeResult(BaseModel):
    total_score: int = Field(..., ge=0, le=100)
    dimensions: List[DimensionScore]
    overall_feedback: str

# B2B Evaluation Models
class CategoryMetrics(BaseModel):
    pass_rate: float
    precision: float
    recall: float
    f1_score: float
    avg_judge_score: float

class B2BMetrics(BaseModel):
    overall_pass_rate: float
    overall_accuracy: float
    overall_completeness: float
    tool_precision: float
    tool_recall: float
    tool_f1: float
    categories: Dict[str, CategoryMetrics]

class AggregateDepthMetrics(BaseModel):
    avg_depth: float
    max_depth: int
    avg_step_score: float
    depth_weighted_score: float
    per_step_consistency: Dict[str, float]  # pass^k per step

class B2BEvaluationResult(BaseModel):
    id: str
    timestamp: datetime
    dataset: str
    pass_k_metrics: Dict[str, float]
    b2b_metrics: B2BMetrics
    depth_metrics: AggregateDepthMetrics
    questions: List[Dict[str, Any]]
```

---

## 11. Evaluation Framework

### 11.1 B2B Dataset Specification

**Total Questions**: 24
**Categories**: 4 (6 questions each)
**Attempts per Question**: 10

#### Category 1: Company Research (6 questions)

| ID | Question | Expected Tools | Evaluation Criteria |
|----|----------|----------------|---------------------|
| company_001 | "When was Stripe founded and who are the founders?" | web_search, wikipedia | Must include 2010 and Patrick & John Collison |
| company_002 | "What is Datadog's headquarters location and when did they IPO?" | web_search, perplexity | Must include NYC and 2019 IPO |
| company_003 | "What products and services does Snowflake offer?" | web_search, perplexity | Must mention data cloud, warehousing |
| company_004 | "Who is the CEO of Salesforce and when did they take the role?" | web_search, wikipedia | Must include Marc Benioff |
| company_005 | "What is Notion's primary product and target market?" | web_search, perplexity | Must mention workspace and teams |
| company_006 | "When was OpenAI founded and what is their flagship product?" | web_search, wikipedia | Must include 2015 and ChatGPT |

#### Category 2: Financial Analysis (6 questions)

| ID | Question | Expected Tools | Evaluation Criteria |
|----|----------|----------------|---------------------|
| finance_001 | "What is Apple's current market capitalization?" | web_search, perplexity | Must provide recent figure (trillions) |
| finance_002 | "Compare the market caps of Microsoft, Apple, and Google" | web_search, perplexity, calculator | Must rank all three |
| finance_003 | "What was Tesla's revenue in their most recent fiscal year?" | web_search, perplexity | Must provide revenue figure |
| finance_004 | "Calculate the P/E ratio if stock price $150 and EPS $5" | calculator | Must calculate 30 |
| finance_005 | "What is NVIDIA's year-over-year revenue growth rate?" | web_search, perplexity, calculator | Must provide growth percentage |
| finance_006 | "How much funding has Anthropic raised and at what valuation?" | web_search, perplexity | Must include funding and valuation |

#### Category 3: Competitive Intelligence (6 questions)

| ID | Question | Expected Tools | Evaluation Criteria |
|----|----------|----------------|---------------------|
| compete_001 | "Compare Slack vs Microsoft Teams for enterprise" | web_search, perplexity | Must compare features, market position |
| compete_002 | "Who are Stripe's main competitors in payment processing?" | web_search, perplexity | Must list PayPal, Square, Adyen |
| compete_003 | "How does Snowflake compare to Databricks?" | web_search, perplexity | Must compare architecture, use cases |
| compete_004 | "What are pros and cons of AWS vs GCP for startups?" | web_search, perplexity | Must list advantages/disadvantages |
| compete_005 | "Compare Figma vs Sketch vs Adobe XD" | web_search, perplexity | Must compare collaboration, features |
| compete_006 | "Who are main competitors to Notion in productivity?" | web_search, perplexity | Must list Coda, Confluence, etc. |

#### Category 4: Action Execution (6 questions)

| ID | Question | Expected Tools | Evaluation Criteria |
|----|----------|----------------|---------------------|
| action_001 | "Summarize my unread emails from today" | gmail | Must attempt Gmail access |
| action_002 | "What meetings do I have scheduled this week?" | google_calendar | Must attempt Calendar access |
| action_003 | "Draft an email to schedule a product demo" | gmail | Must generate email draft |
| action_004 | "Check if I'm free tomorrow at 2pm" | google_calendar | Must check availability |
| action_005 | "Calculate my meeting load for this week" | google_calendar, calculator | Must count and calculate |
| action_006 | "Find emails from last week mentioning 'proposal'" | gmail | Must search with criteria |

### 11.2 LLM-as-Judge Specification

#### 4-Dimension Scoring

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         4-DIMENSION SCORING                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   QUERY: "What is Apple's current market cap?"                              │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  1. TOOL SELECTION (25 pts)                                         │   │
│   │     ✓ Chose perplexity_search (good for financial data)     +15    │   │
│   │     ✓ Avoided irrelevant tools (gmail, calendar)            +10    │   │
│   │     Score: 25/25                                                    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  2. TOOL EXECUTION (25 pts)                                         │   │
│   │     ✓ Parameters: {"query": "Apple market cap"}             +15    │   │
│   │     ✓ Handled result correctly                              +10    │   │
│   │     Score: 25/25                                                    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  3. REASONING QUALITY (25 pts)                                      │   │
│   │     ✓ Explained why tool was chosen                         +10    │   │
│   │     ✓ Connected tool result to answer                       +10    │   │
│   │     ✗ Could cite source in reasoning                         -5    │   │
│   │     Score: 20/25                                                    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  4. ANSWER QUALITY (25 pts)                                         │   │
│   │     ✓ Factually correct ($3.2T in range)                    +15    │   │
│   │     ✓ Appropriate length (~50 words)                        +5     │   │
│   │     ✓ Direct and clear                                      +5     │   │
│   │     Score: 25/25                                                    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   ═══════════════════════════════════════════════════════════════════════   │
│   TOTAL: 95/100                                                             │
│   ═══════════════════════════════════════════════════════════════════════   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Score Thresholds

```
  90-100  ████████████████████  EXCELLENT - Ship it
  75-89   ███████████████░░░░░  GOOD - Minor tweaks needed
  60-74   ██████████░░░░░░░░░░  ACCEPTABLE - Needs improvement
  Below 60 █████░░░░░░░░░░░░░░░  FAILING - Significant issues
```

### 11.3 Depth-Aware Metrics Specification

#### Per-Step pass^k Calculation

```
┌────────────────────────────────────────────────────────────────────────┐
│              PER-STEP pass^k CONSISTENCY MEASUREMENT                   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  QUERY: "What is Apple's market cap and P/E ratio?"                   │
│  K = 5 attempts                                                        │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  STEP 1: First Tool Selection                                    │  │
│  │                                                                  │  │
│  │    Attempt 1: perplexity_search ─┐                               │  │
│  │    Attempt 2: perplexity_search ─┼─ 4/5 chose perplexity        │  │
│  │    Attempt 3: web_search ────────┘  (80% consensus)             │  │
│  │    Attempt 4: perplexity_search ─┐                               │  │
│  │    Attempt 5: perplexity_search ─┘                               │  │
│  │                                                                  │  │
│  │    pass^5_step1 = ✓ (majority consistent)                       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                              ↓                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  STEP 2: Second Tool Selection                                   │  │
│  │                                                                  │  │
│  │    Attempt 1: calculator ────────┐                               │  │
│  │    Attempt 2: calculator ────────┼─ 3/5 chose calculator        │  │
│  │    Attempt 3: calculator ────────┘  (60% consensus)             │  │
│  │    Attempt 4: perplexity_search ─┐                               │  │
│  │    Attempt 5: web_search ────────┘                               │  │
│  │                                                                  │  │
│  │    pass^5_step2 = ✓ (60% threshold met)                         │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ════════════════════════════════════════════════════════════════════  │
│  AGGREGATED PASS^K METRICS:                                            │
│    • pass^5_step1: 80% (PASS)                                         │
│    • pass^5_step2: 60% (PASS)                                         │
│    • Overall pass^5: 2/2 = 100%                                       │
│  ════════════════════════════════════════════════════════════════════  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### 11.4 Metrics Summary

#### Core Quality Metrics
| Metric | Formula | Target |
|--------|---------|--------|
| **pass^5** | Consensus correct / Total (k=5) | ≥ 80% |
| **pass^10** | Consensus correct / Total (k=10) | ≥ 85% |
| **Tool Precision** | Correct tools / Total used | ≥ 80% |
| **Tool Recall** | Correct tools / Expected tools | ≥ 70% |
| **Accuracy Score** | Avg LLM judge accuracy | ≥ 7.5/10 |
| **Completeness** | Avg LLM judge completeness | ≥ 7.0/10 |

#### Depth & Planning Metrics
| Metric | Formula | Target |
|--------|---------|--------|
| **Avg Depth** | Sum(steps) / Total queries | ≥ 2.0 |
| **Max Depth** | Max steps in any query | ≥ 4 |
| **Avg Step Score** | Sum(step_scores) / Total steps | ≥ 20/25 |
| **Depth-Weighted** | Step scores × depth multiplier | ≥ 80/100 |
| **pass^5_step1** | First tool consistency | ≥ 70% |
| **pass^5_step2** | Second tool consistency | ≥ 60% |

#### Category-Specific Targets
| Category | Pass Rate | Tool Precision |
|----------|-----------|----------------|
| Company Research | ≥ 80% | ≥ 85% |
| Financial Analysis | ≥ 75% | ≥ 80% |
| Competitive Intel | ≥ 75% | ≥ 75% |
| Action Execution | ≥ 70% | ≥ 70% |

### 11.5 Evaluation Process

```
1. Load B2B dataset (24 questions)
2. For each question:
   a. Initialize StepTracer
   b. Run k attempts (default k=10) with temperature=0.6
   c. For each attempt:
      - Record answer and all tool calls
      - Track step-by-step reasoning (tool, params, reasoning)
      - Calculate per-step scores
   d. Compute consensus answer (majority vote)
   e. Compute pass^5 and pass^10
   f. Run LLM Judge on each attempt (4-dimension scoring)
   g. Calculate tool precision and recall
   h. Aggregate depth metrics
3. Calculate aggregate metrics:
   a. Overall pass rates
   b. B2B category metrics
   c. Aggregate depth metrics
   d. Per-step pass^k
4. Save results to database and JSON
5. Generate reports (CSV, PDF with depth visualizations)
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
| Evaluation runs | All metrics and traces |

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
python start_dashboard.py --port 8002
```

### 13.2 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| ANTHROPIC_API_KEY | Yes | Claude API key |
| PERPLEXITY_API_KEY | No | Perplexity API key (enables deep research) |
| TAVILY_API_KEY | No | Fallback search API |
| GOOGLE_CLIENT_ID | No | Google OAuth client ID |
| GOOGLE_CLIENT_SECRET | No | Google OAuth client secret |
| DATABASE_PATH | No | SQLite path (default: data/agent.db) |
| LOG_LEVEL | No | Logging level (default: INFO) |

### 13.3 Running Evaluations

```bash
# Full B2B evaluation
python run_evaluation.py --dataset data/b2b_dataset.json

# Quick test (3 questions)
python run_evaluation.py --max-questions 3

# Category-specific
python run_evaluation.py --category company_research
python run_evaluation.py --category financial_analysis

# With specific k value
python run_evaluation.py --k 5
```

### 13.4 Health Monitoring

**Health Check Endpoint**: `GET /api/health`

**Monitoring Points**:
- Database connectivity
- LLM API availability
- Tool availability (sample check)
- OAuth token validity

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
| Email/calendar privacy | Medium | High | Minimal scopes, clear permissions |
| Evaluation gaming | Low | Medium | Multiple metrics, LLM judge, human review |
| User expects perfection | High | Medium | Set expectations, show confidence levels |

### 14.3 Evaluation-Specific Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM Judge inconsistency | Medium | Medium | Use same model, multiple judge runs |
| Depth metric gaming | Low | Low | Cap depth, flag anomalies |
| Category imbalance | Low | Medium | Equal questions per category |
| Ground truth staleness | Medium | Medium | Use LLM judge for dynamic data |

---

## 15. Timeline & Milestones

### 15.1 Development Phases

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **Phase 1: Core Agent** | Week 1 | LLM client, 4 core tools, basic chat |
| **Phase 2: Extended Tools** | Week 2 | Gmail, Calendar, mode switching |
| **Phase 3: Memory & Auth** | Week 3 | Short/long-term memory, Google OAuth |
| **Phase 4: Basic Evaluation** | Week 4 | pass^k harness, original dataset |
| **Phase 5: B2B Alignment** | Week 5 | B2B dataset, LLM Judge, depth metrics |
| **Phase 6: Dashboard** | Week 6 | Full UI, B2B metrics display, export |

### 15.2 Milestones

| Milestone | Target | Criteria |
|-----------|--------|----------|
| M1: MVP Agent | End Week 2 | 6 tools working, basic chat |
| M2: Basic Evaluation | End Week 4 | Can run pass^k evaluation |
| M3: B2B Aligned | End Week 5 | 24 B2B questions, LLM Judge, depth metrics |
| M4: Production Ready | End Week 6 | All features, documentation complete |

### 15.3 Definition of Done

- [x] All functional requirements implemented
- [x] B2B evaluation dataset (24 questions, 4 categories)
- [x] LLM-as-Judge with 4-dimension scoring
- [x] Depth-aware metrics and per-step pass^k
- [x] pass^5 ≥ 80%, pass^10 ≥ 85% targets defined
- [x] Dashboard with B2B examples and depth metrics
- [x] Export working (CSV + PDF)
- [x] Documentation complete

---

## 16. Appendix

### 16.1 Glossary

| Term | Definition |
|------|------------|
| **pass^k** | Consensus-based accuracy metric using k attempts |
| **Tool Precision** | Ratio of correct tools to total tools used |
| **Tool Recall** | Ratio of correct tools to expected tools |
| **LLM-as-Judge** | Using LLM to evaluate answer quality |
| **Depth Metrics** | Metrics measuring reasoning chain length and quality |
| **Per-Step pass^k** | Consistency of tool choice at each reasoning step |
| **Normal Mode** | Research using 2-3 core tools |
| **Deep Mode** | Research using 4-6 tools |
| **Short-term Memory** | In-session conversation context |
| **Long-term Memory** | Persisted facts and history |

### 16.2 File Structure

```
bardeen-agent/
├── data/
│   ├── b2b_dataset.json        # B2B evaluation questions (24)
│   └── agent.db                # SQLite database
├── src/
│   ├── agent/                  # Core agent code
│   ├── evaluation/
│   │   ├── harness.py          # EvaluationHarness, B2BEvaluationHarness
│   │   ├── llm_judge.py        # LLM-as-Judge (4 dimensions)
│   │   ├── dataset.py          # Dataset loading
│   │   ├── visualizer.py       # ASCII visualization
│   │   ├── metrics/
│   │   │   ├── pass_k.py       # pass^k calculation
│   │   │   ├── b2b_metrics.py  # B2B-specific metrics
│   │   │   └── depth_metrics.py # Depth and per-step pass^k
│   │   └── tracers/
│   │       ├── tool_tracer.py  # Tool call tracing
│   │       ├── error_tracer.py # Error tracking
│   │       └── step_tracer.py  # Step-by-step reasoning
│   ├── dashboard/              # FastAPI + Vanilla JS
│   ├── storage/                # SQLite repositories
│   └── shared/                 # Config, models
├── PRD.md                      # This document
├── CLAUDE.md                   # Developer guidance
└── requirements.txt            # Dependencies
```

### 16.3 References

- Claude API Documentation: https://docs.anthropic.com
- Google OAuth 2.0: https://developers.google.com/identity/protocols/oauth2
- Perplexity API: https://docs.perplexity.ai

### 16.4 Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-30 | Initial PRD |
| 2.0 | 2026-02-01 | Added auto mode, Perplexity, strict response guidelines |
| 3.0 | 2026-02-01 | B2B-aligned evaluation (24 questions), LLM-as-Judge, depth metrics, per-step pass^k |

---

**Document Status**: Complete
**Last Updated**: February 1, 2026
**Approvers**: Engineering Team
