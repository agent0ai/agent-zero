---
description: Deploy application through CI/CD pipeline
argument-hint: <environment>
allowed-tools: Task, Bash
model: claude-sonnet-4-5
timeout: 1800
cost_estimate: 0.30-0.45
validation:
  output:
    schema: .claude/validation/schemas/cicd/deploy-pipeline-output.json
    quality_threshold: 0.90
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes: ["Migrated to modern pattern with validation"]
---
# Deploy via Pipeline

Environment: **${ARGUMENTS}**
Execute pipeline deployment using Task agent with validation.
