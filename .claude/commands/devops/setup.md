---
description: Setup infrastructure and development environment
argument-hint: [--environment <prod|staging|dev>]
allowed-tools: Task, Bash
model: claude-sonnet-4-5
timeout: 1800
cost_estimate: 0.25-0.40
validation:
  output:
    schema: .claude/validation/schemas/devops/setup-output.json
    quality_threshold: 0.85
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes: ["Migrated to modern pattern with validation"]
---
# DevOps Setup

Environment: **${ARGUMENTS:-all}**
Execute comprehensive infrastructure setup using Task agent with validation.
