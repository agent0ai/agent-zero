---
name: "gsd-plan-phase"
description: "Collaborate with user to create a detailed implementation plan before coding."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["gsd", "planning", "collaboration", "design"]
trigger_patterns:
  - "plan"
  - "create plan"
  - "planning phase"
  - "design"
---

# GSD: Plan Phase

Use this skill to create a detailed implementation plan collaboratively with the user before any coding begins.

## When to Use

- After project initialization
- Before starting a new feature
- When requirements need clarification
- User asks to "plan" something

## Core Principle

**No coding without a plan. No plan without user approval.**

## Planning Process

### 1. Understand the Goal

Ask clarifying questions:
- What specific outcome do you want?
- What does success look like?
- Are there constraints (time, tech, compatibility)?
- What's the scope boundary?

### 2. Research Existing Code

Before proposing solutions:
- Examine relevant existing files
- Identify patterns already in use
- Note integration points
- Check for similar implementations

### 3. Present Options

Provide 2-3 implementation approaches:

```markdown
## Option A: [Name]
**Approach**: Brief description
**Pros**: Benefits list
**Cons**: Drawbacks list
**Effort**: Low/Medium/High

## Option B: [Name]
**Approach**: Brief description
**Pros**: Benefits list
**Cons**: Drawbacks list
**Effort**: Low/Medium/High
```

### 4. Get User Decision

Ask the user to choose an approach. Don't proceed without explicit selection.

### 5. Create Detailed Plan

Once approach is selected, create `.gsd/plan.md`:

```markdown
# Implementation Plan: [Feature Name]

## Objective
[Clear statement of what we're building]

## Chosen Approach
[Selected option with rationale]

## Tasks
1. [ ] Task 1 - Description
   - Subtask 1a
   - Subtask 1b
2. [ ] Task 2 - Description
3. [ ] Task 3 - Description
4. [ ] Task 4 - Integration testing

## Files to Modify/Create
- `path/to/file.py` - Description of changes
- `path/to/new_file.py` - New file for X

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Tests pass
```

### 6. Confirm and Proceed

Present the plan and ask:
> "Here's the implementation plan. Review and let me know if you'd like any changes. Once approved, I'll begin the execute phase."

## Output Format

After planning is complete:

```markdown
## Plan Created: [Feature Name]

**Tasks**: [X] items
**Files affected**: [Y] files
**Estimated complexity**: Low/Medium/High

Plan saved to `.gsd/plan.md`

Ready to start implementation? Use `gsd-execute-phase` to begin.
```

## Anti-Patterns

- Don't start coding without plan approval
- Don't create plans that are too detailed (leave room for discovery)
- Don't skip the options discussion
- Don't assume requirements - always confirm
