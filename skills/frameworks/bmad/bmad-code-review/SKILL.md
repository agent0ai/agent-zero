---
name: "bmad-code-review"
description: "Validate code quality and completeness against stories."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["bmad", "review", "quality", "validation"]
trigger_patterns:
  - "code review"
  - "review code"
  - "validate implementation"
---

# BMAD: Code Review

Validate implementation quality and completeness.

## When to Use

- After completing `/bmad:dev-story`
- Before merging feature branches
- As part of sprint completion

## Review Framework

### 1. Story Compliance

Check against the original story:

```markdown
## Story Compliance Check

### Story: {Story Name}

**Acceptance Criteria:**
- [ ] Criterion 1: [PASS/FAIL] - [Notes]
- [ ] Criterion 2: [PASS/FAIL] - [Notes]

**Implementation Tasks:**
- [ ] Task 1: [COMPLETE/INCOMPLETE]
- [ ] Task 2: [COMPLETE/INCOMPLETE]
```

### 2. Code Quality

Evaluate against BMAD standards:

| Aspect | Check | Status |
|--------|-------|--------|
| **Readability** | Clear naming, logical structure | ✓/✗ |
| **Maintainability** | DRY, single responsibility | ✓/✗ |
| **Error Handling** | Edge cases covered | ✓/✗ |
| **Security** | No vulnerabilities | ✓/✗ |
| **Performance** | No obvious issues | ✓/✗ |
| **Testing** | Adequate coverage | ✓/✗ |

### 3. Architecture Alignment

If architecture doc exists, verify alignment:

```markdown
## Architecture Compliance

- [ ] Follows defined patterns
- [ ] Uses approved technologies
- [ ] Respects module boundaries
- [ ] Adheres to data flow design
```

### 4. Documentation

Check documentation updates:

```markdown
## Documentation Review

- [ ] Code comments where needed
- [ ] README updated if applicable
- [ ] API docs updated if applicable
- [ ] Change log updated
```

## Review Output

```markdown
# Code Review: {Story/Feature Name}

## Summary
[Overall assessment: APPROVED / NEEDS CHANGES / REJECTED]

## Findings

### Must Fix
1. [Critical issue]
2. [Critical issue]

### Should Fix
1. [Important improvement]
2. [Important improvement]

### Suggestions
1. [Nice to have]
2. [Nice to have]

## Metrics
- Files changed: X
- Lines added: Y
- Lines removed: Z
- Test coverage: N%

## Decision
[APPROVE / REQUEST CHANGES / REJECT]

[If changes requested: specific actions needed]
```

## Review Checklist

```markdown
## Pre-Merge Checklist

- [ ] All acceptance criteria met
- [ ] Tests pass
- [ ] No security issues
- [ ] No performance regressions
- [ ] Documentation complete
- [ ] Code follows project conventions
```

## Integration with BMAD Workflow

**Quick Path:**
```
quick-spec → dev-story → code-review ← YOU ARE HERE
```

**Full Path:**
```
product-brief → create-prd → create-architecture →
create-epics → sprint-planning → dev-story → code-review ← YOU ARE HERE
```
