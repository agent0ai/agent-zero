---
name: life-business-operator
version: 1.0.0
author: agent-jumbo
tier: 1
trust_level: local
categories:
  - operations
  - planning
  - project-management
capabilities:
  - intake
  - knowledge-decomposition
  - lifecycle-planning
  - scheduling
  - validation
description: Run Agent Jumbo as a practical life and business operating system. Use when the goal is to intake raw project content, decompose it into structured knowledge, generate execution plans, and schedule repeatable automation loops.
---

# Life Business Operator

## Purpose

Convert unstructured inputs into an executable operating cadence across projects, knowledge, planning, and automation.

## Core workflow

1. Intake and scope

- Create or select a project.
- Set lifecycle phase and ownership boundaries.
- Define desired outcomes and timeline.

2. Decompose and ingest

- Ingest documents, notes, and links into project knowledge.
- Normalize into concise facts, decisions, and next actions.
- Separate source-of-truth facts from synthesized summaries.

3. Plan and prioritize

- Generate a phased plan (design, development, testing, validation, agent evaluation).
- Produce weekly and daily execution queues.
- Link tasks to project lifecycle runs.

4. Automate cadence

- Schedule recurring planning and review loops.
- Run visual/browser validation where configured.
- Track execution status and update plans from outcomes.

5. Close the loop

- Persist outcomes to project knowledge and memory.
- Capture decisions as reusable patterns.
- Re-plan based on drift, blockers, and new inputs.

## Tool mapping

- `projects` / `project_lifecycle`: project setup, phase control, and run history.
- `knowledge_ingest`: structured ingestion of files and sources.
- `life_os`: dashboard and daily planning rollups.
- `scheduler`: recurring execution and review cadence.
- `project_validation` / `visual_validation`: validation gates for planned work.

## Operating guardrails

- Prefer deterministic workflows over free-form one-off prompts.
- Keep project data isolated by project context unless explicitly shared.
- Every plan item must map to a project phase and measurable completion signal.
- Preserve an auditable trail: inputs, transformations, decisions, and outcomes.
- If runtime performance degrades, reduce optional context injectors before reducing core execution flow.

## Success criteria

- New project can be created and activated in chat context.
- Intake content appears in project knowledge with traceable source metadata.
- A phase-structured execution plan is generated and persisted.
- At least one recurring scheduler job is active for plan/review cadence.
- Validation run records are attached to the project lifecycle history.
