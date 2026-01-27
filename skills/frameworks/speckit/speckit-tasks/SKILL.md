---
name: "speckit-tasks"
description: "Break plan into actionable tasks with clear specifications."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["speckit", "tasks", "breakdown"]
trigger_patterns:
  - "create tasks"
  - "break down"
  - "generate tasks"
---

# Spec Kit: Tasks

Break the implementation plan into specific, actionable tasks.

## When to Use

- Plan is approved
- Ready to start implementation
- Need discrete work items

## Task Format

Create `TASKS.md`:

```markdown
# Tasks: [Phase Name]

## Task 1: [Title]
**Spec Reference**: [REQ-XXX]
**Status**: [ ] Not Started
**Files**:
- Create: `path/to/new.py`
- Modify: `path/to/existing.py`
**Steps**:
1. [Specific step]
2. [Specific step]
**Verification**: [How to verify complete]

## Task 2: [Title]
...
```

## Output

```markdown
## Tasks Generated: [Phase Name]

**Total Tasks**: [X]
**Ready to Start**: [Y]
**Blocked**: [Z]

Tasks saved to `TASKS.md`

Ready to implement? Use `speckit-implement`.
```
