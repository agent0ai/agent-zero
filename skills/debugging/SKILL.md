---
name: "debugging"
description: "Systematic debugging methodology for identifying and fixing bugs. Use when encountering errors, unexpected behavior, or test failures."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["debugging", "troubleshooting", "errors", "testing", "analysis"]
trigger_patterns:
  - "error"
  - "bug"
  - "not working"
  - "fails"
  - "broken"
  - "fix"
  - "debug"
---

# Systematic Debugging Skill

**CRITICAL**: Follow this systematic process. Never guess at fixes without understanding the root cause.

## When to Use

Activate this skill when you encounter:
- Error messages or stack traces
- Unexpected behavior
- Test failures
- Performance issues
- "It was working before" scenarios

## The Debugging Process

### Phase 1: Reproduce the Issue

**Goal**: Confirm you can consistently trigger the bug.

1. **Document the steps** to reproduce
2. **Identify the exact error** message or unexpected behavior
3. **Note the environment**: OS, versions, configuration
4. **Establish baseline**: When did it last work correctly?

```markdown
## Reproduction Steps
1. Step 1
2. Step 2
3. Step 3
Expected: [What should happen]
Actual: [What actually happens]
```

### Phase 2: Gather Evidence

**Goal**: Collect all relevant information before forming hypotheses.

1. **Read the full error message** and stack trace
2. **Check logs** at multiple levels (app, system, network)
3. **Examine recent changes** (git diff, git log)
4. **Review related code** paths
5. **Check dependencies** and their versions

```bash
# Useful commands
git log --oneline -20  # Recent commits
git diff HEAD~5        # Recent changes
cat /var/log/app.log   # Application logs
```

### Phase 3: Form Hypotheses

**Goal**: Generate multiple possible causes ranked by likelihood.

List hypotheses in order of probability:

```markdown
## Hypotheses
1. [Most likely] Description - Evidence supporting this
2. [Likely] Description - Evidence supporting this
3. [Possible] Description - Evidence supporting this
```

### Phase 4: Test Hypotheses

**Goal**: Systematically eliminate possibilities.

For each hypothesis:
1. **Design a test** that would confirm or refute it
2. **Execute the test** with minimal changes
3. **Document results**
4. **Move to next hypothesis** if not confirmed

```markdown
## Testing: Hypothesis 1
Test: [What I'll do to test this]
Result: [Confirmed/Refuted]
Evidence: [What I observed]
```

### Phase 5: Implement Fix

**Goal**: Fix the root cause, not just the symptom.

1. **Isolate the fix**: Make the smallest change that fixes the issue
2. **Verify the fix**: Confirm the original reproduction steps now pass
3. **Check for regressions**: Ensure nothing else broke
4. **Document the fix**: Explain what was wrong and why the fix works

### Phase 6: Prevent Recurrence

**Goal**: Stop this class of bug from happening again.

1. **Add a test** that would have caught this bug
2. **Consider defensive coding** (validation, error handling)
3. **Update documentation** if needed
4. **Share learnings** with team if relevant

## Anti-Patterns to Avoid

- **Random Changes**: Never make changes hoping something works
- **Fix Symptoms**: Always find and fix the root cause
- **Skip Reproduction**: Always confirm you can reproduce before fixing
- **Single Hypothesis**: Consider multiple possibilities
- **No Testing**: Always verify the fix works

## Debugging Tools

### For Python
```python
# Interactive debugging
import pdb; pdb.set_trace()

# Or using ipdb for better experience
import ipdb; ipdb.set_trace()

# Print debugging with context
print(f"DEBUG: {variable=}, {type(variable)=}")
```

### For JavaScript
```javascript
// Debugger statement
debugger;

// Console logging with labels
console.log({ variable, typeof: typeof variable });

// Trace to see call stack
console.trace("How did we get here?");
```

### General
```bash
# Check if process is running
ps aux | grep <process>

# Check port usage
lsof -i :<port>

# Watch file changes
tail -f /path/to/log
```

## Example Session

**User**: "The API endpoint returns 500 error"

**Agent Response**:
> Let me debug this systematically:
>
> ## Phase 1: Reproduction
> - Which endpoint specifically?
> - What request parameters are you sending?
> - Does it fail consistently or intermittently?
>
> ## Phase 2: Gathering Evidence
> Let me check:
> 1. The server error logs
> 2. Recent changes to this endpoint
> 3. The full stack trace
>
> [Proceeds systematically through each phase]
