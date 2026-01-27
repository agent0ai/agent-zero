---
name: "gsd-verify-work"
description: "Validate completed implementation against requirements and acceptance criteria."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["gsd", "verification", "testing", "quality"]
trigger_patterns:
  - "verify"
  - "check work"
  - "validate"
  - "review implementation"
---

# GSD: Verify Work

Use this skill to validate that the implementation meets all requirements and acceptance criteria.

## When to Use

- After completing the execute phase
- Before marking a feature as done
- When user asks to verify or check work

## Verification Process

### 1. Load Acceptance Criteria

Read from `.gsd/plan.md` and list all acceptance criteria:

```markdown
## Verification: [Feature Name]

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
- [ ] Tests pass
```

### 2. Run Automated Tests

Execute the test suite:

```bash
# Run relevant tests
pytest tests/
# or npm test, cargo test, etc.
```

Report results:
```markdown
### Test Results
**Total**: 24 tests
**Passed**: 24
**Failed**: 0
**Skipped**: 0
```

### 3. Manual Verification Checklist

Walk through each acceptance criterion:

```markdown
### Criterion 1: [Description]
**Check**: [How to verify]
**Result**: PASS/FAIL
**Evidence**: [What was observed]

### Criterion 2: [Description]
**Check**: [How to verify]
**Result**: PASS/FAIL
**Evidence**: [What was observed]
```

### 4. Code Quality Check

Review the implementation for:

- [ ] No obvious bugs or errors
- [ ] Consistent with existing code style
- [ ] No security vulnerabilities
- [ ] Error handling in place
- [ ] No hardcoded secrets or debug code

### 5. Documentation Check

Verify:
- [ ] README updated if needed
- [ ] Comments for complex logic
- [ ] API documentation if applicable

### 6. Generate Verification Report

```markdown
## Verification Report: [Feature Name]

### Summary
**Status**: PASSED / FAILED
**Date**: [Date]

### Acceptance Criteria
| Criterion | Status | Notes |
|-----------|--------|-------|
| Criterion 1 | PASS | |
| Criterion 2 | PASS | |
| Tests pass | PASS | 24/24 |

### Code Quality
- Style: Consistent
- Security: No issues
- Error handling: Present

### Issues Found
[None / List of issues]

### Recommendation
Ready for deployment / Needs fixes
```

## If Verification Fails

When criteria are not met:

```markdown
### Verification Failed

**Failed criteria:**
1. [Criterion that failed]
   - Expected: [what was expected]
   - Actual: [what was observed]

**Recommended fixes:**
1. [Fix for issue 1]

Return to execute phase to address these issues?
```

## Completion

When all criteria pass:

```markdown
## Feature Complete: [Feature Name]

All acceptance criteria verified.
All tests passing.
Code quality checks passed.

**Next steps:**
- Commit changes
- Create pull request (if applicable)
- Move to next feature

Would you like me to help with the commit?
```

## Anti-Patterns

- Don't skip verification
- Don't mark as complete with failing tests
- Don't ignore edge cases in verification
- Don't approve without checking acceptance criteria
