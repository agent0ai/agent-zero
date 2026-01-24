---
description: Analyze cloud infrastructure costs
argument-hint: [--period <30d|90d|12m>]
allowed-tools: Task, Bash
model: claude-sonnet-4-5
timeout: 600
cost_estimate: 0.15-0.25
validation:
  output:
    schema: .claude/validation/schemas/devops/cost-analyze-output.json
    quality_threshold: 0.85
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes: ["Migrated to modern pattern with validation"]
---
# Cost Analysis

Period: **${ARGUMENTS:-30d}**
Execute cost analysis using Task agent with validation.
