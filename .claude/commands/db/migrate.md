---
description: Execute database migrations
argument-hint: <up|down|create> [name]
allowed-tools: Bash
model: claude-sonnet-4-5
timeout: 600
cost_estimate: 0.10-0.15
validation:
  output:
    schema: .claude/validation/schemas/db/migrate-output.json
    quality_threshold: 0.95
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes: ["Migrated to modern pattern with validation"]
---
# Database Migration

Action: **${ARGUMENTS}**
Execute migration with validation.
