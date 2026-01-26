---
name: "sp-executing-plans"
description: "Systematically implement plan steps with verification at each stage."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["superpowers", "implementation", "execution"]
trigger_patterns:
  - "execute plan"
  - "implement plan"
  - "start building"
  - "follow plan"
---

# Superpowers: Executing Plans

Systematically work through a plan, verifying each step before proceeding.

## When to Use

- Plan has been created and approved
- User is ready to start implementation
- Need to resume work on an existing plan

## Execution Flow

```
Load Plan → Start Step → Implement → Verify → Update Status → Next Step
```

## Execution Process

### 1. Load and Display Plan

```markdown
## Executing: [Feature Name]

**Plan**: [path/to/plan.md]
**Progress**: [X]/[Total] steps complete

### Remaining Steps:
- Step [N]: [Title]
- Step [N+1]: [Title]
...

Starting Step [N]...
```

### 2. Execute Each Step

For each step:

#### a) Announce Intent
```markdown
### Step [N]: [Title]
**Goal**: [What this achieves]
**Starting...**
```

#### b) Implement Changes
- Make the code changes
- Follow existing patterns
- Add tests if specified

#### c) Verify
- Run specified verification
- Check for regressions
- Confirm goal is met

#### d) Report Completion
```markdown
**Step [N] Complete**
- Modified: `file1.py`, `file2.py`
- Tests: Passing
- Verification: [How verified]

Proceeding to Step [N+1]...
```

### 3. Handle Deviations

When plan needs adjustment:

```markdown
### Plan Deviation Needed

**Step**: [N]
**Issue**: [What was discovered]
**Impact**: [How this affects the plan]

**Options**:
A) [Adjustment option]
B) [Alternative option]

How would you like to proceed?
```

Wait for user input before continuing.

### 4. Progress Checkpoints

Every 2-3 steps or at natural breaks:

```markdown
## Checkpoint

**Progress**: [X]/[Total] steps
**Completed**:
- Step 1: [Title]
- Step 2: [Title]

**Status**: On track / Adjustments made

Continue with remaining steps?
```

### 5. Handle Failures

If a step fails:

```markdown
### Step [N] Failed

**Error**: [What went wrong]
**Attempted**: [What was tried]

**Options**:
1. Debug and fix
2. Skip step (with consequences)
3. Revise plan

How would you like to proceed?
```

### 6. Completion

```markdown
## Execution Complete: [Feature Name]

**Steps**: [Total]/[Total] complete
**Files created**: [count]
**Files modified**: [count]
**Tests**: [status]

### Summary of Changes
- `file1.py`: [what changed]
- `file2.py`: [what changed]

Ready for final review? Use `sp-finishing-branch` to wrap up.
```

## Best Practices

- **Small commits**: Commit after each step or logical group
- **Run tests frequently**: Don't let failures accumulate
- **Stay focused**: Only implement what's in the plan
- **Document deviations**: Note any changes to the plan

## Anti-Patterns

- Skipping verification
- Making unplanned changes
- Continuing past failures without resolving
- Large commits with multiple steps
- Not updating plan with actual changes
