---
name: "prp-generate"
description: "Generate a comprehensive Prompt-Response Protocol specification for a task."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["prp", "prompt-engineering", "specification"]
trigger_patterns:
  - "generate prp"
  - "create prompt"
  - "prp specification"
---

# PRP: Generate

Generate a comprehensive Prompt-Response Protocol for a development task.

## When to Use

- Well-defined, repeatable tasks
- Need consistent execution
- Creating reusable prompts

## PRP Structure

A PRP contains everything needed for task execution:

```markdown
# PRP: [Task Name]

## Context
[Background and environment information]

## Objective
[Clear statement of what must be accomplished]

## Inputs
- [Input 1]: [Description and format]
- [Input 2]: [Description and format]

## Constraints
- [Constraint 1]
- [Constraint 2]

## Process Steps
1. [Step 1 - specific action]
2. [Step 2 - specific action]
3. [Step 3 - specific action]

## Expected Outputs
- [Output 1]: [Format and content]
- [Output 2]: [Format and content]

## Quality Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]

## Examples

### Example 1
**Input**: [Sample]
**Process**: [Brief walkthrough]
**Output**: [Expected result]

## Error Handling
| Condition | Response |
|-----------|----------|
| [Error 1] | [Action] |

## Validation
[How to verify the output is correct]
```

## Generation Process

1. **Understand the Task**: What needs to be done?
2. **Identify Inputs**: What information is needed?
3. **Define Steps**: What's the process?
4. **Specify Outputs**: What should be produced?
5. **Add Examples**: Concrete illustrations
6. **Define Validation**: How to check correctness

## Output

```markdown
## PRP Generated: [Task Name]

**Steps**: [X] defined
**Inputs**: [Y] required
**Outputs**: [Z] specified

PRP saved to `prp/[task-name].md`

Ready to execute? Use `prp-execute`.
```
