---
name: "sp-code-review"
description: "Review implementation against plan, report issues by severity."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["superpowers", "review", "quality", "verification"]
trigger_patterns:
  - "code review"
  - "review code"
  - "check implementation"
---

# Superpowers: Code Review

Review implementation against the plan with severity-based reporting.

## When to Use

- After completing a task or set of tasks
- Before merging a feature branch
- Between implementation phases
- When requesting external review

## Review Process

### 1. Gather Context

- Load the relevant plan(s)
- Identify expected deliverables
- Note any constraints or requirements

### 2. Systematic Review

Check each category:

| Category | What to Check |
|----------|---------------|
| **Plan Compliance** | Does the code match the plan? |
| **Test Coverage** | Are all requirements tested? |
| **Code Quality** | Is it readable and maintainable? |
| **Error Handling** | Are edge cases covered? |
| **Security** | Any vulnerabilities introduced? |
| **Performance** | Any obvious bottlenecks? |

### 3. Issue Classification

Classify findings by severity:

```markdown
## Review Findings

### 🔴 CRITICAL (Blocks merge)
- [Issue description]
- [Location: file:line]
- [Suggested fix]

### 🟡 IMPORTANT (Should fix)
- [Issue description]
- [Location: file:line]
- [Suggested fix]

### 🟢 MINOR (Nice to have)
- [Issue description]
- [Location: file:line]
- [Suggested fix]

### ℹ️ OBSERVATIONS (No action needed)
- [Note or observation]
```

## Severity Guidelines

### 🔴 CRITICAL
- Security vulnerabilities
- Data loss potential
- Crashes or errors in happy path
- Missing required functionality
- **Action**: MUST fix before merge

### 🟡 IMPORTANT
- Missing edge case handling
- Performance issues
- Code that will be hard to maintain
- Missing tests for key paths
- **Action**: Should fix, discuss if blocking

### 🟢 MINOR
- Style inconsistencies
- Minor optimization opportunities
- Documentation gaps
- **Action**: Fix if time permits

## Review Checklist

```markdown
## Pre-Merge Checklist

- [ ] All critical issues resolved
- [ ] Important issues addressed or tracked
- [ ] Tests pass
- [ ] No linting errors
- [ ] Documentation updated if needed
- [ ] Commit messages are clear
```

## Integration with Superpowers Workflow

1. **Brainstorming** → Design
2. **Git Worktrees** → Workspace
3. **Writing Plans** → Tasks
4. **TDD** → Implementation
5. **Code Review** → Quality check ← YOU ARE HERE
6. **Finishing Branch** → Merge

## Best Practices

- Review in small chunks (one task at a time when possible)
- Focus on the plan—does the code deliver what was planned?
- Be specific: include file names and line numbers
- Suggest fixes, don't just identify problems
- Critical issues block; everything else is negotiable
