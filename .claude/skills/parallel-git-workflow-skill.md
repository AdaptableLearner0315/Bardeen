# Parallel Git Workflow Skill

A structured approach to parallel development using Git worktrees for efficient multi-module development.

---

## Skill Overview

This skill enables parallel development of multiple modules using Git worktrees, allowing simultaneous work on different features while maintaining clean separation and merge strategies.

---

## Git Repository Setup

Before starting, ask:
> "Please provide the git repository URL, or confirm I should initialize a new repo."

## Worktree Strategy

Use **3-4 git worktrees** for parallel development:

```bash
# Create worktrees for parallel development
git worktree add -b feature/module-a ../worktree-a main
git worktree add -b feature/module-b ../worktree-b main
git worktree add -b feature/module-c ../worktree-c main
```

## Worktree Management Commands

```bash
# List all worktrees
git worktree list

# Remove a worktree
git worktree remove ../worktree-name

# Prune stale worktree information
git worktree prune
```

## Module Development Flow

### 1. Create Feature Branch
```bash
git worktree add -b feature/module-name ../worktree-module main
cd ../worktree-module
```

### 2. Develop Module
- Implement functionality
- Write unit tests
- Ensure all tests pass

### 3. Commit Changes
```bash
git add .
git commit -m "feat: implement module-name

- Add core functionality
- Include unit tests for 5 edge cases
- Add comprehensive docstrings"
```

### 4. Merge to Main
```bash
# Switch to main branch
cd ../main-repo
git checkout main

# Merge feature branch
git merge feature/module-name --no-ff

# Delete feature branch
git branch -d feature/module-name
```

### 5. Clean Up Worktree
```bash
git worktree remove ../worktree-module
```

## Parallel Development Best Practices

### Module Independence
- Ensure modules can be developed independently
- Minimize inter-module dependencies during development
- Use interfaces/contracts for module communication

### Merge Strategy
- Merge completed modules to main frequently
- Use `--no-ff` for clear history
- Resolve conflicts immediately

### Progress Tracking

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

## Module Completion Requirements

Before merging to main:

```
┌─────────────────────────────────────────────────────────────────┐
│              MODULE MERGE CHECKLIST                             │
├─────────────────────────────────────────────────────────────────┤
│ ☐ All unit tests pass in worktree                               │
│ ☐ No merge conflicts with main                                  │
│ ☐ Code review completed (if applicable)                         │
│ ☐ Documentation updated                                         │
│ ☐ CLAUDE.md updated with module status                          │
│ ☐ notes/CHANGELOG.md updated                                    │
└─────────────────────────────────────────────────────────────────┘
```

## Permission Gates

**ALWAYS** ask for permission before:
- Starting a new module
- Merging to main
- Removing worktrees

Example:
> "Module X is complete with Y tests passing. Do I have permission to merge to main and proceed with Module Z?"

## Handling Merge Conflicts

When conflicts occur:

1. **Identify conflicts**:
   ```bash
   git status
   # Shows conflicted files
   ```

2. **Resolve conflicts**:
   - Edit conflicted files
   - Remove conflict markers
   - Test the resolution

3. **Complete merge**:
   ```bash
   git add .
   git commit
   ```

## Branch Naming Convention

Follow consistent naming:
- `feature/module-name` - For new modules
- `fix/issue-description` - For bug fixes
- `refactor/component-name` - For refactoring

## Quick Reference

```bash
# Create new worktree
git worktree add -b feature/name ../worktree-name main

# List worktrees
git worktree list

# Switch between worktrees
cd ../worktree-name

# Merge feature to main
git checkout main
git merge feature/name --no-ff

# Remove worktree
git worktree remove ../worktree-name

# Clean up
git worktree prune
git branch -d feature/name
```

---

## Invocation

To use this skill, say:
> "Use the parallel-git-workflow skill for multi-module development"

Or:
> "Set up git worktrees for parallel development"