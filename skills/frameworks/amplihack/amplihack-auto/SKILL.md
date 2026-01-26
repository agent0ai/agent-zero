---
name: "amplihack-auto"
description: "Automatic workflow selection based on task analysis."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["amplihack", "workflow", "automatic"]
trigger_patterns:
  - "auto workflow"
  - "amplihack auto"
  - "automatic"
---

# AMPLIHACK: Auto

Automatically select the best workflow based on task analysis.

## When to Use

- Starting any task with AMPLIHACK
- Unsure which workflow to use
- Need intelligent workflow routing

## Task Analysis

Analyze the task to determine best workflow:

| Task Type | Indicators | Recommended Workflow |
|-----------|------------|---------------------|
| Complex problem | Multiple valid approaches | `amplihack-debate` |
| Code analysis | Understand existing code | `amplihack-analyze` |
| Multi-step work | Sequential dependencies | `amplihack-cascade` |
| Simple task | Clear requirements | Direct implementation |

## Selection Process

1. **Analyze Request**
   - What is being asked?
   - How complex is it?
   - What's the scope?

2. **Check Indicators**
   - Multiple approaches possible? → Debate
   - Need deep understanding? → Analyze
   - Sequential steps needed? → Cascade

3. **Select Workflow**
   - Route to appropriate skill
   - Explain selection rationale

## Output

```markdown
## Auto Workflow Selection

**Task**: [Summary]
**Analysis**: [Why this workflow]
**Selected**: [Workflow name]

Proceeding with [workflow]...
```
