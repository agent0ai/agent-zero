---
name: "gsd-execute-phase"
description: "Implement the approved plan with regular checkpoints and progress tracking."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["gsd", "implementation", "execution", "coding"]
trigger_patterns:
  - "execute"
  - "implement"
  - "start coding"
  - "build"
---

# GSD: Execute Phase

Use this skill to implement an approved plan systematically with progress tracking.

## When to Use

- After plan has been approved
- User says "start implementing" or "execute the plan"
- Ready to write code

## Prerequisites

- An approved plan exists in `.gsd/plan.md`
- User has confirmed they want to proceed

## Execution Process

### 1. Load the Plan

Read `.gsd/plan.md` and present the task list:

```markdown
## Starting Execution: [Feature Name]

**Tasks to complete:**
1. [ ] Task 1
2. [ ] Task 2
3. [ ] Task 3

Beginning with Task 1...
```

### 2. Work Through Tasks Sequentially

For each task:

1. **Announce** what you're about to do
2. **Implement** the changes
3. **Verify** the change works (run tests, check syntax)
4. **Update** the checklist
5. **Report** completion before moving on

```markdown
### Task 1: [Description]
**Status**: In Progress

[Implementation details...]

**Result**: Complete
- Created `path/to/file.py`
- Modified `path/to/other.py`
- Tests: Passing

Moving to Task 2...
```

### 3. Handle Issues

When encountering problems:

1. **Stop** and describe the issue clearly
2. **Propose** solutions
3. **Ask** for user input on how to proceed
4. **Don't** silently make major deviations from the plan

```markdown
### Issue Encountered

**Problem**: [Description]
**Impact**: [What this affects]

**Options**:
A) [Solution A]
B) [Solution B]

How would you like to proceed?
```

### 4. Update Progress

After each task, update `.gsd/plan.md`:
- Mark completed tasks with [x]
- Add notes about any deviations
- Track files actually modified

### 5. Checkpoint at Milestones

Every 3-4 tasks, or at natural breakpoints:

```markdown
## Progress Checkpoint

**Completed**: 4/8 tasks
**Files modified**:
- file1.py (200 lines)
- file2.py (50 lines)

**Status**: On track

Continue with remaining tasks?
```

## Completion

When all tasks are done:

```markdown
## Execution Complete: [Feature Name]

**Tasks**: 8/8 complete
**Files created**: 3
**Files modified**: 5
**Tests**: All passing

Ready for verification phase? Use `gsd-verify-work` to validate.
```

## Anti-Patterns

- Don't skip tasks without user approval
- Don't make undocumented changes
- Don't continue past errors without resolving them
- Don't forget to run tests after changes
- Don't implement features not in the plan
