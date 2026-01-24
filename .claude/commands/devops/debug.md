---
description: Debug infrastructure and application issues
argument-hint: <issue-description>
allowed-tools: Task, Bash
model: claude-sonnet-4-5
timeout: 1200
cost_estimate: 0.20-0.35
validation:
  output:
    schema: .claude/validation/schemas/devops/debug-output.json
    quality_threshold: 0.85
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes: ["Migrated to modern pattern with validation"]
---
# Debug Infrastructure

Issue: **${ARGUMENTS}**
Execute debugging workflow using Task agent with validation.
