---
name: "prp-execute"
description: "Execute a PRP specification systematically."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["prp", "execution", "implementation"]
trigger_patterns:
  - "execute prp"
  - "run prp"
  - "follow prompt"
---

# PRP: Execute

Execute a Prompt-Response Protocol specification systematically.

## When to Use

- PRP has been generated
- Ready to perform the task
- Following an established protocol

## Execution Process

1. **Load PRP**: Read the protocol specification
2. **Gather Inputs**: Collect all required inputs
3. **Follow Steps**: Execute each step in order
4. **Produce Outputs**: Generate specified outputs
5. **Validate**: Check against quality criteria

## Execution Template

```markdown
## Executing PRP: [Task Name]

### Inputs Collected
- [Input 1]: [Value/Source]
- [Input 2]: [Value/Source]

### Step Execution

#### Step 1: [Name]
**Action**: [What was done]
**Result**: [Outcome]

#### Step 2: [Name]
**Action**: [What was done]
**Result**: [Outcome]

### Outputs Produced
- [Output 1]: [Location/Content]
- [Output 2]: [Location/Content]

### Validation
- [ ] [Criterion 1]: PASS/FAIL
- [ ] [Criterion 2]: PASS/FAIL

### Status
**Result**: SUCCESS/FAILED
```

## Error Handling

When errors occur:
1. Check PRP error handling section
2. Follow prescribed response
3. If not covered, pause and report

## Output

```markdown
## PRP Execution Complete: [Task Name]

**Status**: Success
**Outputs**: [List]
**Validation**: All criteria passed

[Outputs available at specified locations]
```
