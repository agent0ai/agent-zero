---
description: Check dependencies for vulnerabilities
argument-hint: [--fix]
allowed-tools: Task, Bash
model: claude-sonnet-4-5
timeout: 600
cost_estimate: 0.10-0.15
validation:
  output:
    schema: .claude/validation/schemas/dev/dependency-check-output.json
    quality_threshold: 0.90
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes: ["Migrated to modern pattern with validation"]
---
# Dependency Check

Options: **${ARGUMENTS}**
Execute dependency scan with validation.
