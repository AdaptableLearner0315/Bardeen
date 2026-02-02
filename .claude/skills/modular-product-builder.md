# Modular Product Builder Skill

A structured workflow for building minimal, differentiated software products with rigorous testing and parallel development.

---

## Skill Overview

This skill guides the development of software products through a phased approach:
- **Phase 1**: Planning & Alignment (no building)
- **Phase 2**: Modular Development with Unit Tests
- **Phase 3**: Parallel Development with Git Worktrees
- **Phase 4**: Integration & E2E Testing
- **Phase 5**: Local Deployment & Git Push

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

**STOP** and ask for approval before proceeding to Phase 2:
> "Planning complete. Do I have permission to proceed with Phase 2 (Modular Development)?"

---

## Phase 2: Modular Development

### 2.1 Development Principles

```
┌─────────────────────────────────────────────────────────────────┐
│                   DEVELOPMENT PRINCIPLES                        │
├─────────────────────────────────────────────────────────────────┤
│ • Keep code MINIMAL - single responsibility per function        │
│ • DOCSTRINGS for every function (Args, Returns, Raises)         │
│ • Type hints throughout                                         │
│ • One class per file, <100 lines preferred                      │
│ • No premature abstractions                                     │
│ • No over-engineering                                           │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Module Structure Template

Each module should follow this structure:

```
module_name/
├── __init__.py          # Public exports only
├── component1.py        # Single responsibility
├── component2.py        # Single responsibility
└── schemas.py           # Data models (if needed)
```

### 2.3 Docstring Format

Every function must have a docstring:

```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """
    Brief description of what this function does.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ExceptionType: When this exception occurs.
    """
    pass
```

### 2.4 High-Frequency Edge Cases

For each module, identify and document **5 edge cases**:

| # | Edge Case | Expected Behavior |
|---|-----------|-------------------|
| 1 | Empty input | Return empty/raise ValueError |
| 2 | Invalid type | Raise TypeError with message |
| 3 | Boundary conditions | Handle gracefully |
| 4 | Network/DB failures | Retry or graceful degradation |
| 5 | Concurrent access | Thread-safe handling |

### 2.5 Unit Test Requirements

For each module, create unit tests covering:
- Happy path (normal operation)
- All 5 edge cases
- Mocked external dependencies

```
tests/unit/
└── test_module_name/
    ├── __init__.py
    └── test_component.py    # 5+ tests per component
```

### 2.6 Update CLAUDE.md

After each module completion, update `CLAUDE.md`:
- Mark module as complete
- Update test count
- Update current sprint section

### 2.7 Update Notes Directory

Maintain `notes/` directory with:
- `notes/CHANGELOG.md` - Track CLAUDE.md changes
- `notes/BUILD_LOG.md` - Detailed build decisions

---

## Phase 3: Parallel Development with Git Worktrees

### 3.1 Git Repository Setup

Before starting Phase 3, ask:
> "Please provide the git repository URL, or confirm I should initialize a new repo."

### 3.2 Worktree Strategy

Use **3-4 git worktrees** for parallel development:

```bash
# Create worktrees for parallel development
git worktree add -b feature/module-a ../worktree-a main
git worktree add -b feature/module-b ../worktree-b main
git worktree add -b feature/module-c ../worktree-c main
```

### 3.3 Module Completion Criteria

A module is **ONLY** considered complete when ALL of these are true:

```
┌─────────────────────────────────────────────────────────────────┐
│                  MODULE COMPLETION CHECKLIST                    │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Code is built and functional                                  │
│ ☐ Unit tests for core functionality written                     │
│ ☐ Unit tests for 5 edge cases written                           │
│ ☐ ALL unit tests pass                                           │
│ ☐ Merged to main WITHOUT conflicts                              │
│ ☐ CLAUDE.md updated                                             │
│ ☐ notes/CHANGELOG.md updated                                    │
└─────────────────────────────────────────────────────────────────┘
```

### 3.4 Progress Display (ASCII Art)

After each module completion, display progress:

```
╔══════════════════════════════════════════════════════════════════╗
║                    BUILD PROGRESS                                ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  Module A    [████████████████████] 100% ✅ COMPLETE             ║
║  Module B    [████████████████████] 100% ✅ COMPLETE             ║
║  Module C    [██████████░░░░░░░░░░]  50% 🔄 IN PROGRESS          ║
║  Module D    [░░░░░░░░░░░░░░░░░░░░]   0% ⏳ PENDING              ║
║                                                                  ║
║  ────────────────────────────────────────────────────────────    ║
║  Overall:    [████████████░░░░░░░░]  62% Complete                ║
║  Tests:      45/72 passing                                       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

### 3.5 Permission Before Next Module

**ALWAYS** ask for permission before building the next module:
> "Module X is complete with Y tests passing. Do I have permission to proceed with Module Z?"

---

## Phase 4: Integration & E2E Testing

### 4.1 Prerequisites

**DO NOT** start Phase 4 until:
- ALL modules are complete (per criteria above)
- ALL unit tests pass
- Code is merged to main

### 4.2 Integration Tests

Test cross-module interactions:

```
tests/integration/
├── __init__.py
├── test_module_a_b_integration.py
├── test_module_b_c_integration.py
└── test_full_flow.py
```

### 4.3 E2E Tests

Test complete user flows:

```
tests/e2e/
├── __init__.py
├── test_user_journey_1.py
├── test_user_journey_2.py
└── test_error_scenarios.py
```

### 4.4 Test Completion Criteria

Phase 4 is complete when:
- All integration tests pass
- All E2E tests pass
- No regressions in unit tests

---

## Phase 5: Local Deployment & Git Push

### 5.1 Local Deployment

Only after ALL tests pass:
1. Build the application locally
2. Run smoke tests
3. Verify all features work

### 5.2 Git Push Protocol

**DO NOT** push to remote until:
- Local deployment successful
- All tests passing
- User explicitly approves

Ask:
> "Application deployed locally and all tests pass. Do you want me to push the code to git?"

### 5.3 Final Checklist

```
┌─────────────────────────────────────────────────────────────────┐
│                    FINAL DEPLOYMENT CHECKLIST                   │
├─────────────────────────────────────────────────────────────────┤
│ ☐ All unit tests pass                                           │
│ ☐ All integration tests pass                                    │
│ ☐ All E2E tests pass                                            │
│ ☐ Local deployment successful                                   │
│ ☐ CLAUDE.md is up to date                                       │
│ ☐ notes/ directory is complete                                  │
│ ☐ User approval for git push                                    │
└─────────────────────────────────────────────────────────────────┘
```

### 5.4 Common Deployment Issues & Fixes

| Issue | Symptom | Fix |
|-------|---------|-----|
| **Missing Tailwind CSS** | `Cannot find module 'tailwindcss'` | `npm install tailwindcss@^3.4.0` (use v3 for PostCSS compatibility) |
| **Tailwind v4 PostCSS Error** | `The PostCSS plugin has moved to a separate package` | Downgrade to Tailwind v3: `npm uninstall tailwindcss && npm install tailwindcss@^3.4.0` |
| **Port in use** | `Port 3000 is in use` | Next.js auto-increments port (3001, 3002...) or kill process: `lsof -ti:3000 \| xargs kill` |
| **Backend port conflict** | `Address already in use` | Use alternate port: `uvicorn app.main:app --port 8001` |
| **Missing npm dependencies** | `sh: next: command not found` | Run `npm install` before `npm run dev` |
| **PostCSS config error** | CSS compilation fails | Ensure `postcss.config.js` has: `{ plugins: { tailwindcss: {}, autoprefixer: {} } }` |

### 5.5 Deployment Verification Steps

After fixing any deployment issues:

1. **Verify backend is running**:
   ```bash
   curl http://localhost:8001/health
   # Should return: {"status": "healthy", ...}
   ```

2. **Verify frontend is running**:
   ```bash
   curl -s -o /dev/null -w "%{http_code}" http://localhost:3003
   # Should return: 200
   ```

3. **Run frontend tests after fixes**:
   ```bash
   cd frontend && npm test
   # All tests should pass
   ```

4. **Manually test in browser**:
   - Open frontend URL (e.g., http://localhost:3003)
   - Verify page loads without errors
   - Test basic functionality

---

## Quick Reference Commands

```bash
# Phase 1: Planning
# (No commands - documentation only)

# Phase 2: Module Development
cd backend && pytest tests/unit/test_module/ -v

# Phase 3: Worktree Management
git worktree add -b feature/name ../worktree-name main
git worktree list
git worktree remove ../worktree-name

# Phase 4: Testing
pytest tests/integration/ -v
pytest tests/e2e/ -v

# Phase 5: Deployment
uvicorn app.main:app --reload  # Backend
npm run dev                     # Frontend
git push origin main            # Only with approval
```

---

## Workflow Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEVELOPMENT WORKFLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PHASE 1: PLANNING                                              │
│  ├── Answer critical assumptions                                │
│  ├── Create PRD.md                                              │
│  ├── Create SYSTEM_DESIGN.md                                    │
│  ├── Discuss tech stack                                         │
│  └── GET APPROVAL ────────────────────────────────────────┐     │
│                                                           │     │
│  PHASE 2: MODULAR DEVELOPMENT                             │     │
│  ├── Minimal code, docstrings                             ▼     │
│  ├── 5 edge cases per module                                    │
│  ├── Unit tests                                                 │
│  └── GET APPROVAL ────────────────────────────────────────┐     │
│                                                           │     │
│  PHASE 3: PARALLEL DEVELOPMENT                            │     │
│  ├── 3-4 git worktrees                                    ▼     │
│  ├── Module completion criteria                                 │
│  ├── ASCII progress display                                     │
│  ├── Update CLAUDE.md & notes/                                  │
│  └── GET APPROVAL (per module) ───────────────────────────┐     │
│                                                           │     │
│  PHASE 4: INTEGRATION & E2E                               │     │
│  ├── Integration tests                                    ▼     │
│  ├── E2E tests                                                  │
│  └── GET APPROVAL ────────────────────────────────────────┐     │
│                                                           │     │
│  PHASE 5: DEPLOYMENT                                      │     │
│  ├── Local deployment                                     ▼     │
│  ├── Final verification                                         │
│  └── GET APPROVAL for git push                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Invocation

To use this skill, say:
> "Use the modular-product-builder skill to build [project description]"

Or reference specific phases:
> "Enter Phase 1 planning for [project]"
> "Start Phase 3 parallel development"
