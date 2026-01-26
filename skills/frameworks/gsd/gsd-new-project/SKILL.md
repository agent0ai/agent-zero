---
name: "gsd-new-project"
description: "Initialize a new GSD (Get Stuff Done) project with proper structure and roadmap."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["gsd", "planning", "initialization", "project-setup"]
trigger_patterns:
  - "start project"
  - "new project"
  - "initialize project"
  - "setup gsd"
---

# GSD: New Project Setup

Use this skill when starting a new project with the GSD (Get Stuff Done) methodology.

## When to Use

- User asks to start a new project
- User wants to set up a structured development workflow
- Beginning work on a greenfield feature or application

## Project Structure

Create the following structure in the project directory:

```
project/
├── docs/
│   ├── roadmap.md         # High-level project roadmap
│   ├── decisions/         # Architecture Decision Records
│   └── specs/             # Feature specifications
├── src/                   # Source code
├── tests/                 # Test files
└── .gsd/
    ├── plan.md            # Current implementation plan
    ├── checklist.md       # Progress checklist
    └── context.md         # Project context for AI
```

## Step-by-Step Process

### 1. Gather Project Requirements

Ask the user:
- What is the project name and purpose?
- What are the primary goals?
- What technologies/stack will be used?
- What are the key constraints or requirements?

### 2. Create Roadmap

In `docs/roadmap.md`, document:
- Project vision (1-2 sentences)
- Key milestones (3-5 major phases)
- Success criteria
- Known risks/dependencies

### 3. Initialize GSD Context

Create `.gsd/context.md` with:
- Project summary
- Tech stack details
- Coding conventions
- Testing approach

### 4. Set Up First Plan

Create `.gsd/plan.md` with the first milestone broken down:
- Clear objective
- Numbered tasks
- Acceptance criteria

## Example Output

After initialization, provide this summary:

```markdown
## Project Initialized: [Project Name]

**Location**: /path/to/project
**Framework**: GSD (Get Stuff Done)

### Next Steps
1. Review the roadmap in `docs/roadmap.md`
2. Start planning phase with `gsd-plan-phase` skill
3. Begin implementation once plan is approved

Ready to proceed to planning phase?
```

## Anti-Patterns

- Don't skip requirements gathering
- Don't create overly detailed plans upfront (plans evolve)
- Don't proceed without user confirmation of goals
