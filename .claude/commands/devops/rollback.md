---
description: Rollback deployment to previous version
argument-hint: [--version <version>]
allowed-tools: Task, Bash, AskUserQuestion
model: claude-sonnet-4-5
timeout: 900
cost_estimate: 0.20-0.30
validation:
  output:
    schema: .claude/validation/schemas/devops/rollback-output.json
    quality_threshold: 0.95
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes: ["Migrated to modern pattern with validation"]
---
# Rollback Deployment

Options: **${ARGUMENTS}**
Execute rollback with safety checks using Task agent with validation.
