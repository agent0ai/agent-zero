---
description: Seed database with sample data
argument-hint: [--environment <dev|staging>]
allowed-tools: Task, Bash
model: claude-sonnet-4-5
timeout: 600
cost_estimate: 0.15-0.20
validation:
  output:
    schema: .claude/validation/schemas/db/seed-output.json
    quality_threshold: 0.85
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes: ["Migrated to modern pattern with validation"]
---
# Database Seed

Environment: **${ARGUMENTS:-dev}**
Execute seeding with validation.
