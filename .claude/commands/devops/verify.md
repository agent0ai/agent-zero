---
description: Verify infrastructure health and deployment status
argument-hint: [--critical-path-only]
allowed-tools: Task, Bash
model: claude-sonnet-4-5
timeout: 600
cost_estimate: 0.15-0.25
validation:
  output:
    schema: .claude/validation/schemas/devops/verify-output.json
    quality_threshold: 0.90
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes: ["Migrated to modern pattern with validation"]
---
# Verify Infrastructure

Options: **${ARGUMENTS}**
Execute comprehensive verification checks using Task agent with validation.
