---
name: "gsd-complete-milestone"
description: "Archive completed milestone, tag release, and prepare for next iteration."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["gsd", "milestone", "release", "completion"]
trigger_patterns:
  - "complete milestone"
  - "finish milestone"
  - "archive milestone"
  - "tag release"
---

# GSD: Complete Milestone

Archive the milestone and prepare for the next development cycle.

## When to Use

- After all phases in the current milestone are verified
- When ready to tag a release
- Before starting `gsd-new-milestone` for the next version

## Prerequisites

- All phases in the milestone should be complete
- All verification steps should pass
- No critical issues remaining

## Process

### 1. Milestone Audit

Before completing, verify:

```markdown
## Milestone Audit Checklist

- [ ] All planned phases are complete
- [ ] Verification passed for each phase
- [ ] No critical bugs or blockers
- [ ] Documentation is current
- [ ] All changes are committed
```

### 2. Archive Milestone

Move milestone files to archive:

```
.planning/
├── archive/
│   └── v{version}/
│       ├── PROJECT.md
│       ├── REQUIREMENTS.md
│       ├── ROADMAP.md
│       ├── phases/
│       │   ├── 1-CONTEXT.md
│       │   ├── 1-RESEARCH.md
│       │   ├── 1-*-PLAN.md
│       │   └── ...
│       └── STATE.md
```

### 3. Tag Release

Create a git tag for the milestone:

```bash
git tag -a v{version} -m "Milestone: {milestone_name}"
```

### 4. Generate Summary

Create a milestone summary:

```markdown
## Milestone Summary: {name}

### Delivered
- [Feature 1]
- [Feature 2]

### Metrics
- Phases completed: X
- Plans executed: Y
- Total commits: Z

### Key Decisions
- [Decision 1]: [Rationale]
- [Decision 2]: [Rationale]

### Lessons Learned
- [Lesson 1]
- [Lesson 2]

### Next Steps
- [Suggestion for next milestone]
```

## Output

**Creates:**
- Archive folder with milestone artifacts
- Git tag for the release
- `MILESTONE-SUMMARY.md`

## Usage

```
/gsd:complete-milestone
```

After completion, use `/gsd:new-milestone` to start the next version.
