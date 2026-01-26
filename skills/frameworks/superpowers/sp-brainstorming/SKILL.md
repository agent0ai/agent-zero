---
name: "sp-brainstorming"
description: "Structured brainstorming for requirements exploration before implementation."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["superpowers", "planning", "design", "requirements"]
trigger_patterns:
  - "brainstorm"
  - "explore options"
  - "design"
  - "think through"
---

# Superpowers: Brainstorming

Use this skill BEFORE any implementation to explore requirements and design options.

## When to Use

- User requests a new feature
- Starting creative work
- Multiple implementation approaches possible
- Requirements are unclear

## Brainstorming Process

### Phase 1: Understanding Intent (Ask 3-5 Questions)

Focus questions on:
1. **Goal Clarity**: What specific outcome do you want?
2. **Context**: What existing code/systems does this interact with?
3. **Constraints**: Performance, security, compatibility requirements?
4. **Edge Cases**: What happens in failure scenarios?
5. **Success Criteria**: How will we know it's working?

### Phase 2: Explore the Codebase

Before proposing solutions:
- Read relevant existing files
- Identify established patterns
- Note integration points
- Check for similar implementations

### Phase 3: Design Options

Present 2-3 approaches with trade-offs:

```markdown
## Option A: [Name]
**Approach**: Brief description
**Pros**: List benefits
**Cons**: List drawbacks
**Best for**: When to choose this

## Option B: [Name]
**Approach**: Brief description
**Pros**: List benefits
**Cons**: List drawbacks
**Best for**: When to choose this
```

### Phase 4: Technical Specification

Once approach is chosen, document:

1. **Files to Create/Modify**: List with descriptions
2. **Dependencies**: External packages or internal modules
3. **Data Flow**: How data moves through the system
4. **API Contracts**: Input/output specifications
5. **Test Strategy**: How this will be tested

### Phase 5: Implementation Plan

Break down into ordered tasks:

```markdown
## Implementation Tasks
1. [ ] Task 1 - Description
2. [ ] Task 2 - Description (depends on 1)
3. [ ] Task 3 - Description
4. [ ] Task 4 - Integration testing
```

## Output Format

After brainstorming:

```markdown
## Summary: [Feature Name]

### Chosen Approach
[Brief description of selected approach]

### Key Decisions
- Decision 1: Rationale
- Decision 2: Rationale

### Implementation Tasks
1. Task 1
2. Task 2
3. Task 3

### Ready to Plan
Confirm with user before proceeding to `sp-writing-plans`.
```

## Anti-Patterns

- Jumping to code without understanding requirements
- Single solution bias (always consider alternatives)
- Ignoring existing codebase patterns
- Over-engineering simple problems
- Under-specifying complex requirements
