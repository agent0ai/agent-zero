---
name: "sp-finishing-branch"
description: "Complete development branch with proper git workflow, review, and merge preparation."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["superpowers", "git", "review", "completion"]
trigger_patterns:
  - "finish branch"
  - "wrap up"
  - "prepare for merge"
  - "create pr"
---

# Superpowers: Finishing Branch

Complete a development branch with proper verification, documentation, and git workflow.

## When to Use

- Implementation is complete
- Ready to merge or create PR
- Need to clean up before submission

## Finishing Checklist

### 1. Verify All Tests Pass

```bash
# Run full test suite
pytest tests/
# or npm test, cargo test, etc.
```

```markdown
## Test Results
**Total**: [X] tests
**Passed**: [X]
**Failed**: 0
**Coverage**: [X]%

All tests passing.
```

### 2. Code Quality Check

- [ ] No linting errors
- [ ] No type errors (if applicable)
- [ ] No debug code left in
- [ ] No hardcoded values that should be config
- [ ] Error handling is present
- [ ] No security issues

### 3. Documentation Review

- [ ] README updated if needed
- [ ] API documentation current
- [ ] Comments explain non-obvious code
- [ ] CHANGELOG updated

### 4. Clean Git History

Review commits:
```bash
git log --oneline -10
```

Ensure commits are:
- [ ] Logical and atomic
- [ ] Well-described
- [ ] No WIP or temp commits

### 5. Create/Update PR Description

```markdown
## Summary
[1-3 sentence description of changes]

## Changes
- [Change 1]
- [Change 2]
- [Change 3]

## Testing
- [How this was tested]
- [What to test during review]

## Screenshots (if applicable)
[Add screenshots for UI changes]

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No breaking changes (or noted below)
```

### 6. Final Verification

```markdown
## Pre-Merge Checklist

**Branch**: [branch-name]
**Target**: [main/develop]

### Automated Checks
- [ ] All tests pass
- [ ] Linting passes
- [ ] Build succeeds

### Manual Verification
- [ ] Feature works as expected
- [ ] Edge cases handled
- [ ] No regressions in related features

### Documentation
- [ ] README current
- [ ] API docs updated
- [ ] Inline comments adequate

### Git
- [ ] Commits are clean
- [ ] No merge conflicts
- [ ] Branch is up to date with target
```

## Output

After finishing process:

```markdown
## Branch Ready: [branch-name]

**Status**: Ready for review/merge
**Tests**: All passing
**Commits**: [X] clean commits

### Summary of Changes
- [Main change 1]
- [Main change 2]

### PR/MR Ready
[Link or instructions to create]

What's next?
- Create pull request
- Request review
- Merge (if self-merge allowed)
```

## Git Commands Reference

```bash
# Update branch with latest target
git fetch origin
git rebase origin/main

# Interactive rebase to clean commits
git rebase -i origin/main

# Push (force if rebased)
git push --force-with-lease

# Create PR via CLI (GitHub)
gh pr create --title "Feature: X" --body "..."
```

## Anti-Patterns

- Merging with failing tests
- Skipping code review
- Poor commit messages
- Leaving TODO comments
- Not updating documentation
