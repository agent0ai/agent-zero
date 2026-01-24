---
description: Setup CI/CD pipeline infrastructure
argument-hint: [--platform <github|gitlab|circleci>]
allowed-tools: Task, Bash, Write
model: claude-sonnet-4-5
timeout: 1200
cost_estimate: 0.25-0.40
validation:
  output:
    schema: .claude/validation/schemas/cicd/setup-output.json
    quality_threshold: 0.85
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes: ["Migrated to modern pattern with validation"]
---
# CI/CD Setup

Platform: **${ARGUMENTS:-github}**
Execute CI/CD setup using Task agent with validation.
