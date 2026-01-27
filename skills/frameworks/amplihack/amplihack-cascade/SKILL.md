---
name: "amplihack-cascade"
description: "Multi-agent cascade pattern for complex sequential tasks."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["amplihack", "cascade", "multi-agent"]
trigger_patterns:
  - "cascade"
  - "sequential workflow"
  - "multi-step"
---

# AMPLIHACK: Cascade

Execute complex tasks using a cascade of specialized agents.

## When to Use

- Multi-step tasks with dependencies
- Different expertise needed at each stage
- Quality gates between phases

## Cascade Pattern

```
[Input] → [Agent 1] → [Output 1] → [Agent 2] → [Output 2] → [Final Output]
```

Each agent:
- Has specialized expertise
- Receives previous output as input
- Produces structured output for next agent
- Can validate and fail-fast

## Cascade Stages

### Stage 1: Requirements
- Parse and validate input
- Identify scope and constraints
- Output: Structured requirements

### Stage 2: Design
- Receive requirements
- Create implementation design
- Output: Technical specification

### Stage 3: Implementation
- Receive specification
- Write code
- Output: Implementation with tests

### Stage 4: Verification
- Receive implementation
- Run tests and checks
- Output: Verified code or failures

## Execution

```markdown
## Cascade Execution: [Task]

### Stage 1: Requirements
**Input**: [User request]
**Agent**: Requirements Analyst
**Output**: Structured requirements
**Status**: Complete

### Stage 2: Design
**Input**: Requirements from Stage 1
**Agent**: Architect
**Output**: Technical spec
**Status**: In Progress

...
```

## Failure Handling

If a stage fails:
1. Report failure
2. Allow retry or revision
3. Don't proceed until resolved
