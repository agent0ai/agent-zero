---
name: "agentos-standards"
description: "Apply and verify AgentOS coding standards across the project."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["agentos", "standards", "quality"]
trigger_patterns:
  - "apply standards"
  - "check standards"
  - "verify standards"
---

# AgentOS: Standards

Apply and verify AgentOS coding standards across the project.

## When to Use

- After project install
- Before committing code
- During code review
- Periodic quality checks

## Standards Categories

### 1. Code Style
- Consistent formatting
- Naming conventions
- File organization

### 2. Documentation
- Function/method documentation
- README completeness
- API documentation

### 3. Testing
- Test coverage requirements
- Test naming conventions
- Test organization

### 4. Security
- No hardcoded secrets
- Input validation
- Error handling

## Standards Check Process

```markdown
## Standards Verification: [Project Name]

### Code Style
- [ ] Formatting: [Tool] passing
- [ ] Linting: [Tool] passing
- [ ] Naming: Conventions followed

### Documentation
- [ ] README: Complete and current
- [ ] Functions: Documented
- [ ] API: Documented

### Testing
- [ ] Coverage: [X]% (minimum: 80%)
- [ ] Tests: All passing
- [ ] Structure: Follows conventions

### Security
- [ ] Secrets: None hardcoded
- [ ] Validation: Input validated
- [ ] Errors: Properly handled

### Result
**Status**: PASS/FAIL
**Issues**: [Count]
```

## Fixing Violations

For each violation:
1. Identify the standard
2. Locate the violation
3. Apply the fix
4. Verify the fix

## Output

```markdown
## Standards Check: [Project Name]

**Status**: PASS/FAIL
**Violations**: [X]
**Coverage**: [Y]%

[List of issues if any]

All standards met? Ready for commit/review.
```
