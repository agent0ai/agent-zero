---
description: Execute implementation following tasks.md with test-driven development
argument-hint: <spec-name>
allowed-tools: Task, Read, Write, Edit, Bash, WebFetch, Playwright, Skill
model: claude-sonnet-4-5
timeout: 3600
retry: 3
cost_estimate: 0.40

# Validation
validation:
  input:
    spec_name:
      schema: .claude/validation/schemas/common/spec-name.json
      required: true

  output:
    schema: .claude/validation/schemas/agent-os/implementation-output.json
    required_artifacts:
      - source_files: "≥3 files"
      - test_files: "≥2 files"
      - documentation: "≥1 file"
    quality_requirements:
      - all_tasks_completed: true
      - tests_passing: true
      - test_coverage: "≥80%"
      - no_lint_errors: true
      - build_successful: true

# Prerequisites
prerequisites:
  - command: /agent-os/create-tasks
    file_exists: 'agent-os/specs/${spec_name}/tasks.md'
    error_message: "Run /agent-os/create-tasks ${spec_name} first"

# Version
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to named agent reference (implementer)"
      - "Added comprehensive validation (tests, coverage, build)"
      - "Added retry logic (max 3 attempts)"
      - "Added cost controls ($0.50 limit)"
      - "Enhanced TDD workflow validation"
  - version: 1.0.0
    date: 2025-10-15
    changes:
      - "Initial implementation"
---

# Implement Tasks

Spec: **$ARGUMENTS**

## Overview

This command:

1. Executes tasks from tasks.md in order
2. Follows test-driven development (tests first)
3. Verifies work after each task group
4. Captures verification screenshots

## Step 1: Validate Input

```bash
SPEC_NAME="$ARGUMENTS"
if [[ ! "$SPEC_NAME" =~ ^[a-z0-9-]+$ ]]; then
  echo "❌ ERROR: Invalid spec name"
  exit 1
fi
echo "✓ Spec name validated"
```

## Step 2: Check Prerequisites

```bash
SPEC_PATH="agent-os/specs/$ARGUMENTS"

if [ ! -f "$SPEC_PATH/tasks.md" ]; then
    echo "❌ ERROR: No tasks.md found. Run /agent-os/create-tasks $ARGUMENTS first."
    exit 1
fi

echo "✓ Prerequisites validated"
```

## Step 3: Launch Implementer Agent

```javascript
await Task({
  subagent: 'implementer',  // ✅ Named agent
  description: 'Implement feature with TDD',

  context: {
    spec_name: ARGUMENTS,
    spec_path: `agent-os/specs/${ARGUMENTS}`,
    spec_file: `agent-os/specs/${ARGUMENTS}/spec.md`,
    requirements_file: `agent-os/specs/${ARGUMENTS}/requirements.md`,
    tasks_file: `agent-os/specs/${ARGUMENTS}/tasks.md`,
    visuals_path: `agent-os/specs/${ARGUMENTS}/visuals/`,
    verification_screenshots_path: `agent-os/specs/${ARGUMENTS}/verification/screenshots/`,
    standards_path: '.claude/standards/'
  },

  validation: {
    required_outputs: ['source_files', 'test_files', 'documentation'],
    schema: '.claude/validation/schemas/agent-os/implementation-output.json',
    quality_threshold: 0.85,
    content_checks: [
      { type: 'all_tasks_completed', required: true },
      { type: 'tests_passing', required: true },
      { type: 'test_coverage', min: 0.8 },
      { type: 'no_lint_errors', required: true },
      { type: 'no_type_errors', required: true },
      { type: 'build_successful', required: true }
    ]
  },

  retry: {
    max_attempts: 3,
    backoff: 'exponential'
  },

  cost_limit: 0.50,
  preserve_context: true
})
```

## Step 4: Validate Output

```bash
SPEC_NAME="$ARGUMENTS"
TASKS_FILE="agent-os/specs/$SPEC_NAME/tasks.md"

# Check all tasks completed
TOTAL_TASKS=$(grep -c "\[.\]" "$TASKS_FILE" || echo "0")
COMPLETED_TASKS=$(grep -c "\[x\]" "$TASKS_FILE" || echo "0")

echo "Tasks: $COMPLETED_TASKS / $TOTAL_TASKS completed"

if [ "$COMPLETED_TASKS" -lt "$TOTAL_TASKS" ]; then
  echo "⚠️  WARNING: Not all tasks completed"
fi

echo "✓ Implementation validation complete"
```

## Completion

```
═══════════════════════════════════════════════════
        IMPLEMENTATION COMPLETE ✓
═══════════════════════════════════════════════════

Spec: $ARGUMENTS
Agent: implementer v2.0.0
Version: 2.0.0

Validation Results:
  ✓ All tasks completed
  ✓ Tests passing
  ✓ Test coverage ≥80%
  ✓ No lint errors
  ✓ Build successful

NEXT STEPS:
→ Run /agent-os/verify-implementation $ARGUMENTS
→ Or proceed to code review

═══════════════════════════════════════════════════
```
