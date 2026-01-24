---
description: Generate API endpoints from specification
argument-hint: <spec-file>
allowed-tools: Task, Write
model: claude-sonnet-4-5
timeout: 900
cost_estimate: 0.20-0.30
validation:
  output:
    schema: .claude/validation/schemas/dev/generate-api-output.json
    quality_threshold: 0.85
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes: ["Migrated to modern pattern with validation"]
---
# Generate API

Specification: **${ARGUMENTS}**
Execute API generation with validation.
