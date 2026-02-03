# Planning & Alignment Skill

A structured workflow for planning and designing minimal, differentiated software products before any code is written.

---

## Skill Overview

This skill guides the planning and alignment phase of product development, ensuring clear requirements and system design before implementation begins.

---

## Phase 1: Planning & Alignment

### 1.1 Enter Planning Mode

Before writing any code, enter planning mode to:
- Identify the **minimal set of features** for a differentiated MVP
- Focus on the **wedge** - what makes this product unique
- Answer critical assumptions before building

**DO NOT BUILD** during this phase. Focus entirely on:
- Understanding the problem space
- Defining scope boundaries
- Identifying key risks and assumptions

### 1.2 Critical Questions to Answer

Ask and resolve these questions before proceeding:

```
┌─────────────────────────────────────────────────────────────────┐
│                    CRITICAL ASSUMPTIONS                         │
├─────────────────────────────────────────────────────────────────┤
│ 1. Who is the target user?                                      │
│ 2. What is the core problem being solved?                       │
│ 3. What is the key differentiator (wedge)?                      │
│ 4. What are the must-have vs nice-to-have features?             │
│ 5. What are the technical constraints?                          │
│ 6. What external dependencies exist (APIs, services)?           │
│ 7. What are the success metrics?                                │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Create PRD Document

Create a Product Requirements Document (`PRD.md`) containing:

```markdown
# PRD.md Structure

## 1. Problem Statement
## 2. Target Users
## 3. Core Value Proposition (Wedge)
## 4. MVP Feature Set (Minimal)
## 5. Out of Scope (Explicitly)
## 6. User Stories
## 7. Success Metrics
## 8. Technical Constraints
## 9. Open Questions
```

### 1.4 Tech Stack Discussion

Discuss and document the tech stack covering:

| Category | Decision Points |
|----------|-----------------|
| **Frontend** | Framework, styling, state management |
| **Backend** | Language, framework, API design |
| **Database** | Type (SQL/NoSQL), specific technology |
| **Infrastructure** | Hosting, containerization, CI/CD |
| **Observability** | Logging, monitoring, tracing |
| **Testing** | Unit, integration, E2E frameworks |

### 1.5 System Design Document

Create `SYSTEM_DESIGN.md` with:
- Architecture overview
- Module breakdown
- Data flow diagrams
- API contracts
- Edge cases per module

### 1.6 Display System Diagram (ASCII Art)

Always include an ASCII art system diagram:

```
┌─────────────────────────────────────────────────────────────────┐
│                      SYSTEM ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐               │
│   │ FRONTEND │────▶│   API    │────▶│ BACKEND  │               │
│   └──────────┘     └──────────┘     └────┬─────┘               │
│                                          │                      │
│                    ┌─────────────────────┼─────────────────┐    │
│                    │                     │                 │    │
│                    ▼                     ▼                 ▼    │
│              ┌──────────┐         ┌──────────┐      ┌─────────┐ │
│              │ DATABASE │         │  CACHE   │      │ STORAGE │ │
│              └──────────┘         └──────────┘      └─────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.7 Get Explicit Approval

**STOP** and ask for approval before proceeding to implementation:
> "Planning complete. Do I have permission to proceed with development?"

---

## Deliverables

- `PRD.md` - Product Requirements Document
- `SYSTEM_DESIGN.md` - System Architecture & Design
- Tech stack decisions documented
- ASCII art system diagram
- Explicit approval to proceed

---

## Invocation

To use this skill, say:
> "Use the planning-alignment skill for [project description]"

Or:
> "Start Phase 1 planning for [project]"