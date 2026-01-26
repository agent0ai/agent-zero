---
name: "speckit-specify"
description: "Create detailed specifications for features following constitution principles."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["speckit", "specification", "design"]
trigger_patterns:
  - "specify"
  - "create spec"
  - "specification"
---

# Spec Kit: Specify

Create detailed, unambiguous specifications following the project constitution.

## When to Use

- After constitution is defined
- Before planning implementation
- When feature requirements need detail

## Specification Structure

Create `specs/[feature-name].md`:

```markdown
# Specification: [Feature Name]

## Summary
[One paragraph description]

## Constitution Alignment
- Principle: [How this follows principle X]
- Constraints: [Relevant constraints]

## Requirements

### Functional
1. [REQ-001] [Clear, testable requirement]
2. [REQ-002] [Clear, testable requirement]

### Non-Functional
1. [NFR-001] [Performance/security/etc requirement]

## Interface

### Inputs
- [Input 1]: [Type, validation, description]

### Outputs
- [Output 1]: [Type, format, description]

## Behavior

### Happy Path
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Error Cases
| Condition | Behavior |
|-----------|----------|
| [Error 1] | [Response] |

## Examples

### Example 1: [Name]
**Input**: [Sample input]
**Output**: [Expected output]

## Acceptance Criteria
- [ ] [AC-001] [Criterion]
- [ ] [AC-002] [Criterion]
```

## Output

```markdown
## Specification Complete: [Feature Name]

**Requirements**: [X] functional, [Y] non-functional
**Acceptance Criteria**: [Z] items

Specification saved to `specs/[feature-name].md`

Ready to plan? Use `speckit-plan`.
```
