---
name: "amplihack-fix"
description: "Systematic error resolution with pattern-specific context and workflow."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["amplihack", "fix", "debugging", "error-resolution"]
trigger_patterns:
  - "fix"
  - "debug"
  - "resolve error"
  - "troubleshoot"
---

# AMPLIHACK: Fix

Systematic error resolution using the DEFAULT_WORKFLOW pattern.

## When to Use

- When encountering errors or bugs
- When tests are failing
- When behavior doesn't match expectations
- For systematic troubleshooting

## The Fix Workflow

The fix workflow follows a structured 22-step process for robust error resolution:

### Phase 1: Understand

1. **Reproduce** - Confirm the error occurs consistently
2. **Isolate** - Identify minimal reproduction case
3. **Document** - Capture error messages, stack traces, context

### Phase 2: Analyze

4. **Root Cause Analysis** - Trace error to origin
5. **Impact Assessment** - Understand scope of issue
6. **Pattern Matching** - Check for known error patterns

### Phase 3: Fix

7. **Design Solution** - Plan the fix approach
8. **Implement Fix** - Make code changes
9. **Verify Fix** - Confirm error is resolved

### Phase 4: Harden

10. **Add Tests** - Prevent regression
11. **Document** - Update relevant documentation
12. **Review** - Ensure fix is complete

## Pattern-Specific Context

The fix workflow adapts to error patterns:

| Pattern | Focus |
|---------|-------|
| **Type Error** | Check types, interfaces, contracts |
| **Runtime Error** | Trace execution path, check state |
| **Logic Error** | Verify business logic, edge cases |
| **Integration Error** | Check boundaries, APIs, data flow |
| **Performance Issue** | Profile, measure, optimize |

## Fix Output Format

```markdown
## Fix Report: {Error Description}

### Error Summary
- **Type:** [Error type/pattern]
- **Location:** [File:line or component]
- **Impact:** [Scope of issue]

### Root Cause
[Description of why the error occurs]

### Solution
[Description of the fix]

### Changes Made
1. `file1.ts:45` - [Change description]
2. `file2.ts:89` - [Change description]

### Verification
- [ ] Error no longer occurs
- [ ] Tests pass
- [ ] No new errors introduced

### Regression Prevention
- [ ] Test added: [test description]
```

## Best Practices

1. **Reproduce first** - Never fix what you can't reproduce
2. **One fix at a time** - Don't combine multiple fixes
3. **Test the fix** - Verify before declaring success
4. **Add regression tests** - Prevent future occurrences
5. **Document the root cause** - Help future debugging

## Integration with AMPLIHACK

The fix workflow can be triggered from:
- `amplihack-auto` - When errors are detected
- Direct invocation for known issues
- Cascade workflows when a step fails
