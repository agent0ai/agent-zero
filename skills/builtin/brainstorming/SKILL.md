---
name: "brainstorming"
description: "Structured brainstorming and requirements exploration before implementation. Use this BEFORE any creative work like building features, creating components, or adding functionality."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["planning", "design", "requirements", "architecture", "creative"]
trigger_patterns:
  - "create"
  - "build"
  - "implement"
  - "add feature"
  - "design"
  - "develop"
---

# Brainstorming Skill

**CRITICAL**: Use this skill BEFORE writing any implementation code. This ensures proper requirements exploration and design alignment.

## When to Use

Activate this skill when you encounter:
- "Create a new feature..."
- "Build a component that..."
- "Implement X functionality..."
- "Add support for..."
- "Design a system that..."

## The Brainstorming Process

### Phase 1: Understanding Intent (5 questions max)

Ask clarifying questions to understand:

1. **Goal Clarity**: What specific outcome does the user want?
2. **Context**: What existing code/systems does this interact with?
3. **Constraints**: Are there performance, security, or compatibility requirements?
4. **Edge Cases**: What happens in failure scenarios?
5. **Success Criteria**: How will we know it's working correctly?

### Phase 2: Design Options

Present 2-3 implementation approaches with trade-offs:

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

### Phase 3: Technical Specification

Once approach is chosen, document:

1. **Files to Create/Modify**: List with brief description
2. **Dependencies**: External packages or internal modules needed
3. **Data Flow**: How data moves through the system
4. **API Contracts**: Input/output specifications
5. **Test Strategy**: How this will be tested

### Phase 4: Implementation Plan

Break down into ordered tasks:

```markdown
## Implementation Tasks
1. [ ] Task 1 - Description
2. [ ] Task 2 - Description (depends on 1)
3. [ ] Task 3 - Description
4. [ ] Task 4 - Integration testing
```

## Anti-Patterns to Avoid

- **Jumping to Code**: Never start coding without understanding requirements
- **Single Solution Bias**: Always consider at least 2 approaches
- **Ignoring Context**: Always examine existing patterns in the codebase
- **Over-Engineering**: Keep solutions proportional to the problem
- **Under-Specifying**: Be specific enough that implementation is clear

## Example Session

**User**: "Add dark mode to the application"

**Agent Response**:
> Before implementing dark mode, let me understand your requirements:
>
> 1. **Scope**: Should this apply to the entire application or specific sections?
> 2. **Toggle**: How should users switch modes? (button, system preference, both?)
> 3. **Persistence**: Should the preference be saved across sessions?
> 4. **Theming Approach**: Do you have existing CSS variables, or should we create a new theme system?
> 5. **Transition**: Should there be smooth transitions when switching modes?

## Output Format

After brainstorming, provide a clear summary:

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

### Ready to Implement
Confirm with user before proceeding to implementation.
```
