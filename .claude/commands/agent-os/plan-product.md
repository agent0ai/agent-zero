---
description: Create product documentation including mission, roadmap, and tech stack
argument-hint: [product-name]
allowed-tools: Task, Read, Write, AskUserQuestion
---

# Plan Product

Product: **$ARGUMENTS**

## Overview

This command creates comprehensive product documentation:

- Mission statement and vision
- Development roadmap with phases
- Technology stack documentation

## Step 1: Launch Product Planner

Use the **product-planner** agent to guide the planning process:

```javascript
await Task({
  subagent_type: 'general-purpose',
  description: 'Plan product documentation',
  prompt: `
You are a product planning specialist. Help create product documentation for: ${ARGUMENTS}

Follow the product-planner agent workflow:

1. GATHER REQUIREMENTS
   Ask about:
   - Product name and core concept
   - Target users and their needs
   - Key features (prioritized)
   - Technical constraints or preferences
   - Competitive landscape

2. CREATE MISSION DOCUMENT
   Create agent-os/product/mission.md with:
   - Vision statement
   - Mission statement
   - Core values
   - Target users
   - Key differentiators

3. CREATE ROADMAP
   Create agent-os/product/roadmap.md with:
   - Phase 1: Foundation features
   - Phase 2: Core features
   - Phase 3: Enhancements
   - Future considerations

4. DOCUMENT TECH STACK
   Create agent-os/product/tech-stack.md with:
   - Framework & Runtime
   - Frontend stack
   - Backend stack
   - Infrastructure

Reference standards from .claude/standards/ for alignment.
  `
})
```

## Step 2: Verification

After the agent completes, verify files were created:

```bash
ls -la agent-os/product/
```

Expected files:

- `mission.md` - Product vision and mission
- `roadmap.md` - Development phases
- `tech-stack.md` - Technology decisions

## Completion

```
═══════════════════════════════════════════════════
        PRODUCT PLANNING COMPLETE
═══════════════════════════════════════════════════

Product: [Product Name]

Files Created:
  → agent-os/product/mission.md
  → agent-os/product/roadmap.md
  → agent-os/product/tech-stack.md

NEXT STEPS:
→ Run /agent-os/init-spec [feature] to start a feature
→ Or review documentation in agent-os/product/

═══════════════════════════════════════════════════
```
