# Modular Development Skill

A structured approach to building minimal, well-tested code modules with proper documentation and edge case handling.

---

## Skill Overview

This skill guides the development of individual modules with emphasis on:
- Minimal, single-responsibility code
- Comprehensive docstrings and type hints
- Edge case identification
- Unit testing for all functionality

---

## Development Principles

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

## Module Structure Template

Each module should follow this structure:

```
module_name/
├── __init__.py          # Public exports only
├── component1.py        # Single responsibility
├── component2.py        # Single responsibility
└── schemas.py           # Data models (if needed)
```

## Docstring Format

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

## High-Frequency Edge Cases

For each module, identify and document **5 edge cases**:

| # | Edge Case | Expected Behavior |
|---|-----------|-------------------|
| 1 | Empty input | Return empty/raise ValueError |
| 2 | Invalid type | Raise TypeError with message |
| 3 | Boundary conditions | Handle gracefully |
| 4 | Network/DB failures | Retry or graceful degradation |
| 5 | Concurrent access | Thread-safe handling |

## Unit Test Requirements

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

## Module Completion Criteria

A module is **ONLY** considered complete when ALL of these are true:

```
┌─────────────────────────────────────────────────────────────────┐
│                  MODULE COMPLETION CHECKLIST                    │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Code is built and functional                                  │
│ ☐ Unit tests for core functionality written                     │
│ ☐ Unit tests for 5 edge cases written                           │
│ ☐ ALL unit tests pass                                           │
│ ☐ Docstrings for all functions                                  │
│ ☐ Type hints throughout                                         │
│ ☐ Single responsibility per component                           │
└─────────────────────────────────────────────────────────────────┘
```

## Update Documentation

After each module completion, update:
- `CLAUDE.md` - Mark module as complete
- `notes/CHANGELOG.md` - Track changes
- `notes/BUILD_LOG.md` - Detailed build decisions

## Best Practices

### Avoid Over-Engineering
- Don't add features, refactor code, or make "improvements" beyond what was asked
- A bug fix doesn't need surrounding code cleaned up
- A simple feature doesn't need extra configurability
- Don't add docstrings, comments, or type annotations to code you didn't change
- Only add comments where the logic isn't self-evident

### Error Handling
- Don't add error handling, fallbacks, or validation for scenarios that can't happen
- Trust internal code and framework guarantees
- Only validate at system boundaries (user input, external APIs)
- Don't use feature flags or backwards-compatibility shims when you can just change the code

### Code Organization
- Don't create helpers, utilities, or abstractions for one-time operations
- Don't design for hypothetical future requirements
- The right amount of complexity is the minimum needed for the current task
- Three similar lines of code is better than a premature abstraction

## Quick Reference Commands

```bash
# Run unit tests for a module
cd backend && pytest tests/unit/test_module/ -v

# Check test coverage
pytest --cov=module_name tests/unit/test_module/

# Run linting
pylint module_name/
```

---

## Invocation

To use this skill, say:
> "Use the modular-development skill for [module name]"

Or:
> "Build [module] following modular development principles"