---
name: "sp-writing-plans"
description: "Create detailed implementation plans with clear steps and verification criteria."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["superpowers", "planning", "documentation"]
trigger_patterns:
  - "write plan"
  - "create plan"
  - "make plan"
  - "planning"
---

# Superpowers: Writing Plans

Create a detailed, actionable implementation plan after brainstorming.

## When to Use

- After completing brainstorming phase
- User has selected an approach
- Ready to formalize the implementation strategy

## Plan Document Structure

Create a plan file (e.g., `PLAN.md` or `.plan/current.md`):

```markdown
# Implementation Plan: [Feature Name]

## Context
[Brief background and why this is being built]

## Objective
[Clear, measurable goal statement]

## Approach
[Selected approach from brainstorming with rationale]

## Steps

### Step 1: [Title]
**Goal**: What this step achieves
**Actions**:
- Specific action 1
- Specific action 2
**Verification**: How to confirm step is complete
**Files**: Files to create/modify

### Step 2: [Title]
...

## Test Plan
- [ ] Unit tests for X
- [ ] Integration tests for Y
- [ ] Manual verification of Z

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] All tests pass
- [ ] No regressions

## Dependencies
- [List external dependencies]

## Risks
- [Potential issues and mitigations]
```

## Plan Writing Guidelines

### Steps Should Be

1. **Atomic**: One clear action per step
2. **Verifiable**: Has a way to confirm completion
3. **Ordered**: Dependencies are clear
4. **Scoped**: Not too large, not too small

### Each Step Includes

- Clear goal statement
- Specific file changes
- Verification method
- Estimated size (small/medium/large)

### Good Step Example

```markdown
### Step 3: Add validation to user input
**Goal**: Ensure email addresses are valid format
**Actions**:
- Create `validators/email.py` with email regex
- Import validator in `forms/user_form.py`
- Add validation call in `handle_submit()`
**Verification**:
- Unit test with valid/invalid emails
- Form rejects "notanemail" input
**Files**: `validators/email.py`, `forms/user_form.py`
```

### Bad Step Example

```markdown
### Step 3: Implement validation
- Add validation
```

## Plan Review Checklist

Before finalizing:
- [ ] Each step has a clear goal
- [ ] Dependencies between steps are noted
- [ ] Test plan covers main scenarios
- [ ] Acceptance criteria are measurable
- [ ] No steps are too large (break down if needed)

## Output

After plan is written:

```markdown
## Plan Complete: [Feature Name]

**Steps**: [X] implementation steps
**Test cases**: [Y] planned
**Files affected**: [Z] files

Plan saved to `[path]`

Ready to execute? Use `sp-executing-plans` to begin.
```

## Anti-Patterns

- Steps that are too vague
- Missing verification criteria
- Forgetting test planning
- Plans that can't be followed by someone else
- Overly rigid plans (leave room for discovery)
