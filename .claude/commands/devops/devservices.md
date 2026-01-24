---
description: Manage development services (Docker, databases, etc)
argument-hint: <start|stop|restart|status>
allowed-tools: Bash
model: claude-sonnet-4-5
timeout: 300
cost_estimate: 0.05-0.10
validation:
  output:
    schema: .claude/validation/schemas/devops/devservices-output.json
    quality_threshold: 0.90
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes: ["Migrated to modern pattern with validation"]
---
# Development Services

Action: **${ARGUMENTS}**
Execute service management using Bash with validation.
