---
description: Optimize cloud infrastructure costs
argument-hint: [--auto-apply]
allowed-tools: Task, Bash, AskUserQuestion
model: claude-sonnet-4-5
timeout: 900
cost_estimate: 0.20-0.30
validation:
  output:
    schema: .claude/validation/schemas/devops/cost-optimize-output.json
    quality_threshold: 0.85
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes: ["Migrated to modern pattern with validation"]
---
# Cost Optimization

Options: **${ARGUMENTS}**
Execute cost optimization using Task agent with validation.
