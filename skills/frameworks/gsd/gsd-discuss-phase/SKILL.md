---
name: "gsd-discuss-phase"
description: "Capture implementation decisions and user preferences before planning begins."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["gsd", "discussion", "planning", "elicitation"]
trigger_patterns:
  - "discuss phase"
  - "capture decisions"
  - "implementation preferences"
---

# GSD: Discuss Phase

Shape the implementation before research and planning begins.

## When to Use

- After `gsd-new-project` has created the roadmap
- Before `gsd-plan-phase` for a specific phase
- When you need to capture user preferences for how something should be built

## Purpose

Your roadmap has a sentence or two per phase. That's not enough context to build something the way the user imagines it. This step captures preferences before anything gets researched or planned.

## Process

### 1. Analyze the Phase

Identify gray areas based on what's being built:

| Feature Type | Questions to Explore |
|-------------|---------------------|
| **Visual features** | Layout, density, interactions, empty states |
| **APIs/CLIs** | Response format, flags, error handling, verbosity |
| **Content systems** | Structure, tone, depth, flow |
| **Organization tasks** | Grouping criteria, naming, duplicates, exceptions |

### 2. Interactive Discussion

For each area the user selects:
- Ask targeted questions
- Drill deeper on important decisions
- Stop when user is satisfied

### 3. Create CONTEXT.md

Document all decisions in a structured format:

```markdown
# Phase {N} Context: {Phase Name}

## Decisions Made

### {Area 1}
- **Decision**: [What was decided]
- **Rationale**: [Why this choice]

### {Area 2}
...

## Constraints Identified
- [Constraint 1]
- [Constraint 2]

## Open Questions (for Research)
- [Question 1]
- [Question 2]
```

## Output

**Creates:** `{phase}-CONTEXT.md`

This file feeds directly into:
1. **Researcher** — Knows what patterns to investigate
2. **Planner** — Knows what decisions are locked

## Best Practices

- Keep discussions focused on one phase at a time
- Document preferences even if they seem obvious
- Distinguish between firm decisions and preferences
- Note any constraints that affect implementation choices

## Usage

```
/gsd:discuss-phase 1
```

Replace `1` with the phase number from your roadmap.
