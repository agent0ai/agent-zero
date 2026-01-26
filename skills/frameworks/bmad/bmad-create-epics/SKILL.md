---
name: "bmad-create-epics"
description: "Break architecture into manageable epics for iterative development."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["bmad", "epics", "agile", "planning"]
trigger_patterns:
  - "create epics"
  - "break down work"
  - "define epics"
---

# BMAD: Create Epics

Break the architecture into deliverable epics for iterative development.

## When to Use

- Architecture is approved
- Need to plan sprints/iterations
- Before creating developer stories

## Epic Structure

Create `docs/epics/` directory with one file per epic:

```markdown
# Epic: [Epic Name]

## Overview
[What this epic delivers]

## Business Value
[Why this matters to users/business]

## Dependencies
- [Prior epics or external dependencies]

## User Stories
- US-001: [Title]
- US-002: [Title]
- US-003: [Title]

## Acceptance Criteria
- [ ] [Criteria 1]
- [ ] [Criteria 2]

## Technical Scope
- Components affected: [List]
- APIs: [List]
- Data: [List]

## Estimated Effort
- Story Points: [X]
- Duration: [Y weeks]

## Risks
- [Risk 1]
- [Risk 2]
```

## Epic Planning Process

1. **Identify Deliverables**: What user value can be shipped?
2. **Define Boundaries**: Clear start and end
3. **Order by Dependencies**: What must come first?
4. **Size Appropriately**: 1-4 weeks of work
5. **Assign Stories**: Group related user stories

## Epic Ordering

```markdown
## Epic Roadmap

### Phase 1: Foundation
1. Epic: Core Infrastructure
2. Epic: Authentication

### Phase 2: Core Features
3. Epic: [Feature A]
4. Epic: [Feature B]

### Phase 3: Enhancement
5. Epic: [Feature C]
```

## Output

```markdown
## Epics Defined: [Product Name]

**Total Epics**: [X]
**Phases**: [Y]
**Estimated Duration**: [Z weeks]

### Epic Summary
| Epic | Stories | Points | Phase |
|------|---------|--------|-------|
| [Name] | [X] | [Y] | 1 |

Epics saved to `docs/epics/`

Ready to start development? Use `bmad-dev-story` for implementation.
```
