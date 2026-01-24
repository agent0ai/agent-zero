---
description: Test API contracts and interfaces
argument-hint: [--provider <service>]
allowed-tools: Task, Bash
model: claude-sonnet-4-5
timeout: 600
cost_estimate: 0.15-0.20
validation:
  output:
    schema: .claude/validation/schemas/dev/contract-test-output.json
    quality_threshold: 0.90
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes: ["Migrated to modern pattern with validation"]
---
# Contract Testing

Provider: **${ARGUMENTS}**
Execute contract tests with validation.
