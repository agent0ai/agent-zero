---
name: "code-review"
description: "Comprehensive code review skill for analyzing code quality, identifying issues, and suggesting improvements. Use when reviewing PRs or checking code quality."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["review", "quality", "security", "best-practices", "pr"]
trigger_patterns:
  - "review"
  - "check code"
  - "code quality"
  - "pull request"
  - "PR"
---

# Code Review Skill

**Goal**: Provide actionable, constructive feedback that improves code quality.

## Review Categories

### 1. Correctness
- Does the code do what it's supposed to?
- Are there logic errors?
- Are edge cases handled?

### 2. Security
- Input validation
- Authentication/authorization
- SQL injection, XSS prevention
- Secrets exposure

### 3. Performance
- Algorithmic complexity
- Database query efficiency
- Memory usage
- Caching opportunities

### 4. Maintainability
- Code readability
- Naming conventions
- Documentation
- Single responsibility

### 5. Testing
- Test coverage
- Test quality
- Edge case testing

## Review Process

### Phase 1: Understand Context

Before reviewing:
1. What is the purpose of this change?
2. What problem is it solving?
3. What are the requirements?
4. Are there related changes elsewhere?

### Phase 2: High-Level Review

Look at:
1. **Architecture**: Does the approach make sense?
2. **Design patterns**: Are appropriate patterns used?
3. **File organization**: Is code in the right place?
4. **Dependencies**: Are new dependencies justified?

### Phase 3: Line-by-Line Review

For each file:
1. Read through understanding intent
2. Check for issues in each category
3. Note both problems and good practices

### Phase 4: Provide Feedback

Structure feedback clearly:

```markdown
## Review Summary

### Must Fix (Blockers)
- [ ] **Security**: SQL injection vulnerability in line 42
- [ ] **Bug**: Off-by-one error in loop at line 78

### Should Fix (Important)
- [ ] **Performance**: N+1 query problem in user loader
- [ ] **Maintainability**: Function too long (150+ lines)

### Consider (Suggestions)
- [ ] **Style**: Variable naming could be more descriptive
- [ ] **Testing**: Add test for empty input case

### Positives
- Good use of error handling
- Clear separation of concerns
```

## Code Smells to Watch For

### Complexity
- **Long methods**: > 20-30 lines
- **Deep nesting**: > 3-4 levels
- **Too many parameters**: > 4-5 params
- **God classes**: Classes doing too much

### Duplication
- Copy-pasted code blocks
- Similar logic in multiple places
- Magic numbers repeated

### Coupling
- Tight coupling between modules
- Circular dependencies
- Inappropriate intimacy

### Naming
- Single-letter variables (except loops)
- Misleading names
- Inconsistent conventions

## Security Checklist

```markdown
- [ ] Input validation on all user input
- [ ] Parameterized queries (no string concatenation for SQL)
- [ ] Output encoding (prevent XSS)
- [ ] Authentication checked on protected routes
- [ ] Authorization checked for resource access
- [ ] Sensitive data not logged
- [ ] Secrets not hardcoded
- [ ] HTTPS enforced for sensitive data
- [ ] Rate limiting on authentication endpoints
- [ ] CORS properly configured
```

## Feedback Guidelines

### Be Constructive
```markdown
# Bad
"This code is terrible"

# Good
"This approach works, but consider using X for better
performance because [specific reason]"
```

### Be Specific
```markdown
# Bad
"Fix the naming"

# Good
"Rename `d` to `document_count` for clarity.
Single-letter variables make the code harder to understand"
```

### Explain Why
```markdown
# Bad
"Don't use global variables"

# Good
"Global variables can cause issues because:
1. They make testing difficult
2. They create hidden dependencies
3. They can be modified from anywhere

Consider passing this as a parameter instead."
```

### Offer Solutions
```markdown
# Instead of just:
"This is inefficient"

# Provide:
"This is O(n²) due to the nested loops. Consider using
a Set for the lookup to achieve O(n):

```python
seen = set(processed_ids)
for item in items:
    if item.id in seen:  # O(1) lookup
        continue
```"
```

## Review Checklist Template

```markdown
## Code Review: [PR Title]

### Context Understanding
- [ ] I understand the purpose of this change
- [ ] I've reviewed related documentation/tickets

### Correctness
- [ ] Logic is correct
- [ ] Edge cases handled
- [ ] Error handling appropriate

### Security
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] Authentication/authorization correct
- [ ] No secrets exposed

### Performance
- [ ] No obvious performance issues
- [ ] Database queries efficient
- [ ] No memory leaks

### Maintainability
- [ ] Code is readable
- [ ] Functions are focused
- [ ] Good naming
- [ ] Appropriate comments

### Testing
- [ ] Adequate test coverage
- [ ] Tests are meaningful
- [ ] Edge cases tested

### Verdict
- [ ] Approved
- [ ] Approved with comments
- [ ] Request changes
```

## Example Review

```markdown
## Review: Add user registration endpoint

### Summary
Generally good implementation! A few security concerns to address.

### Must Fix
1. **Security (line 45)**: Password stored in plain text
   ```python
   # Current
   user.password = request.password

   # Fix
   user.password_hash = hash_password(request.password)
   ```

2. **Validation (line 38)**: Email not validated
   Add email format validation before saving

### Should Fix
1. **Error Handling (line 52)**: Bare except catches too much
   ```python
   # Current
   except:
       return error_response()

   # Fix
   except ValidationError as e:
       return error_response(str(e))
   ```

### Consider
1. Add rate limiting to prevent spam registrations
2. Send confirmation email async to improve response time

### Positives
- Good use of transactions
- Clear API response structure
- Comprehensive logging
```
