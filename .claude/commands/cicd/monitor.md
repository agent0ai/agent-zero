---
description: Monitor CI/CD pipeline health and status
argument-hint: [--watch]
allowed-tools: Task, Bash
model: claude-sonnet-4-5
timeout: 300
cost_estimate: 0.10-0.15
validation:
  output:
    schema: .claude/validation/schemas/cicd/monitor-output.json
    quality_threshold: 0.85
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes: ["Migrated to modern pattern with validation"]
---
# CI/CD Monitoring

Options: **${ARGUMENTS}**
Execute monitoring with validation.
