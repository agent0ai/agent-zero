---
name: "bmad-sprint-planning"
description: "Initialize sprint tracking and select stories for the sprint."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["bmad", "sprint", "planning", "agile"]
trigger_patterns:
  - "sprint planning"
  - "plan sprint"
  - "initialize sprint"
---

# BMAD: Sprint Planning

Initialize sprint tracking and select stories for implementation.

## When to Use

- After epics and stories are created (`/bmad:create-epics`)
- At the start of each development sprint
- When re-planning mid-sprint

## Prerequisites

- Epics and stories defined
- Story estimates available (or will be created)
- Team capacity known

## Process

### 1. Review Backlog

Examine available stories:

```markdown
## Backlog Review

### High Priority
| Story | Epic | Estimate | Status |
|-------|------|----------|--------|
| Story 1 | Epic A | 3 pts | Ready |
| Story 2 | Epic A | 5 pts | Ready |

### Medium Priority
| Story | Epic | Estimate | Status |
|-------|------|----------|--------|
| Story 3 | Epic B | 2 pts | Ready |

### Needs Refinement
| Story | Epic | Issue |
|-------|------|-------|
| Story 4 | Epic B | Unclear requirements |
```

### 2. Estimate Stories

If stories need estimates:

```markdown
## Story Estimation

### Story: {Name}
**Complexity factors:**
- [ ] Code changes: [Simple/Medium/Complex]
- [ ] Testing needs: [Low/Medium/High]
- [ ] Integration: [None/Some/Heavy]
- [ ] Risk: [Low/Medium/High]

**Estimate:** X points

**Rationale:** [Why this estimate]
```

### 3. Set Sprint Capacity

```markdown
## Sprint Capacity

**Sprint duration:** X days/weeks
**Team velocity:** Y points (based on history or estimate)
**Available capacity:** Z points (accounting for meetings, etc.)
```

### 4. Select Sprint Stories

Choose stories that fit capacity:

```markdown
## Sprint {N} Plan

**Goal:** [Sprint goal in one sentence]

**Selected Stories:**
| # | Story | Epic | Points | Priority |
|---|-------|------|--------|----------|
| 1 | Story 1 | Epic A | 3 | Must have |
| 2 | Story 2 | Epic A | 5 | Must have |
| 3 | Story 3 | Epic B | 2 | Should have |

**Total Points:** X / Y capacity

**Stretch Goals (if time permits):**
- Story 4 (2 pts)
```

### 5. Initialize Sprint Tracking

Create sprint tracking file:

```markdown
# Sprint {N}: {Sprint Name}

**Start:** YYYY-MM-DD
**End:** YYYY-MM-DD
**Goal:** [Sprint goal]

## Progress

| Story | Status | Assigned | Notes |
|-------|--------|----------|-------|
| Story 1 | Not Started | - | |
| Story 2 | Not Started | - | |

## Daily Updates
### Day 1
- Started:
- Completed:
- Blockers:
```

## Output

**Creates:**
- `SPRINT-{N}.md` - Sprint tracking document
- Updated story statuses

## Next Steps

After sprint planning:
1. `/bmad:dev-story` - Work on each selected story
2. Track progress in sprint document
3. `/bmad:code-review` - Review completed work

## Sprint Ceremonies (Reference)

| Ceremony | When | Purpose |
|----------|------|---------|
| **Planning** | Sprint start | Select stories, set goal |
| **Daily standup** | Daily | Sync progress, identify blockers |
| **Review** | Sprint end | Demo completed work |
| **Retrospective** | Sprint end | Improve process |
