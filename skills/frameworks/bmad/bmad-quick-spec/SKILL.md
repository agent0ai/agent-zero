---
name: "bmad-quick-spec"
description: "Analyze codebase and produce tech-spec with stories for quick tasks."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["bmad", "quick", "specification", "stories"]
trigger_patterns:
  - "quick spec"
  - "quick path"
  - "simple feature"
  - "bug fix spec"
---

# BMAD: Quick Spec

Fast-track specification for small features and bug fixes.

## When to Use

The Quick Path is for:
- Bug fixes
- Small features with clear scope
- Configuration changes
- Minor enhancements

**NOT for:**
- New products or platforms
- Complex features requiring architecture
- Work spanning multiple sprints

## The Quick Path

```
quick-spec → dev-story → code-review
```

Just 3 commands instead of the full 6+ step BMAD process.

## Process

### 1. Analyze the Request

Understand what needs to be done:
- What is the problem or requirement?
- What files might be affected?
- Are there existing patterns to follow?

### 2. Codebase Analysis

Examine relevant parts of the codebase:

```markdown
## Codebase Analysis

### Affected Areas
- [File/module 1]: [What it does]
- [File/module 2]: [What it does]

### Existing Patterns
- [Pattern 1]: [How it's used]
- [Pattern 2]: [How it's used]

### Dependencies
- [Dependency 1]: [Relevance]
```

### 3. Generate Tech Spec

Create a lightweight technical specification:

```markdown
# Tech Spec: {Feature/Fix Name}

## Summary
[One sentence description]

## Problem
[What issue this solves]

## Solution
[High-level approach]

## Implementation Details

### Changes Required
1. [Change 1]
2. [Change 2]

### Files Affected
- `path/to/file1.ts` - [What changes]
- `path/to/file2.ts` - [What changes]

## Testing
- [ ] [Test case 1]
- [ ] [Test case 2]

## Acceptance Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
```

### 4. Generate Stories

Break the spec into implementable stories:

```markdown
## Stories

### Story 1: {Name}
**As a** [user type]
**I want** [capability]
**So that** [benefit]

**Tasks:**
- [ ] Task 1
- [ ] Task 2

**Acceptance Criteria:**
- [ ] Criterion 1
```

## Output

**Creates:**
- `QUICK-SPEC.md` - Technical specification
- Stories ready for `/bmad:dev-story`

## Next Steps

After quick-spec:
1. `/bmad:dev-story` - Implement each story
2. `/bmad:code-review` - Validate quality

## Integration with Full Path

If during quick-spec you discover the task is more complex:
- Stop the quick path
- Switch to full BMAD path starting with `/bmad:product-brief`
