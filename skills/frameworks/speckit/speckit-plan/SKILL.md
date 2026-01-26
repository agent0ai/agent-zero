---
name: "speckit-plan"
description: "Generate implementation roadmap from specifications."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["speckit", "planning", "roadmap"]
trigger_patterns:
  - "plan implementation"
  - "create roadmap"
  - "implementation plan"
---

# Spec Kit: Plan

Generate an implementation roadmap from approved specifications.

## When to Use

- Specifications are approved
- Need to plan development sequence
- Before generating tasks

## Plan Structure

Create `PLAN.md`:

```markdown
# Implementation Plan: [Project Name]

## Specifications Covered
- [spec-1.md]: [Brief description]
- [spec-2.md]: [Brief description]

## Implementation Phases

### Phase 1: [Name]
**Goal**: [What this phase achieves]
**Specs**: [Which specifications]
**Dependencies**: [None/Prior phases]

### Phase 2: [Name]
...

## Dependency Graph
```
[Phase 1] → [Phase 2] → [Phase 3]
                    ↘ [Phase 4]
```

## Risk Mitigation
| Risk | Phase | Mitigation |
|------|-------|------------|
| [Risk] | [X] | [Strategy] |

## Success Criteria
- [ ] All specifications implemented
- [ ] All tests pass
- [ ] Constitution compliance verified
```

## Output

```markdown
## Plan Created: [Project Name]

**Phases**: [X]
**Specifications**: [Y] covered

Plan saved to `PLAN.md`

Ready to generate tasks? Use `speckit-tasks`.
```
