---
description: Create strategically organized task list for implementation
argument-hint: <spec-name>
allowed-tools: Task, Read, Write
model: claude-sonnet-4-5
timeout: 1800
retry: 3
cost_estimate: 0.16

# Validation
validation:
  input:
    spec_name:
      schema: .claude/validation/schemas/common/spec-name.json
      required: true

  output:
    schema: .claude/validation/schemas/agent-os/tasks-output.json
    required_files:
      - 'agent-os/specs/${spec_name}/tasks.md'
    min_file_size: 1500
    quality_threshold: 0.9
    content_requirements:
      - "At least 4 task groups (Database, API, Frontend, Integration)"
      - "Dependencies defined for each group"
      - "At least 5 total tasks"
      - "At least 2 testing tasks"
      - "Acceptance criteria per task"

# Prerequisites
prerequisites:
  - command: /agent-os/write-spec
    file_exists: 'agent-os/specs/${spec_name}/spec.md'
    error_message: "Run /agent-os/write-spec ${spec_name} first"

# Version
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to named agent reference (tasks-list-creator)"
      - "Added comprehensive validation"
      - "Added retry logic (max 3 attempts)"
      - "Added cost controls ($0.20 limit)"
      - "Enhanced task quality validation"
  - version: 1.0.0
    date: 2025-10-15
    changes:
      - "Initial implementation"
---

# Create Tasks

Spec: **$ARGUMENTS**

## Overview

This command:

1. Analyzes the specification
2. Creates organized tasks with dependencies
3. Defines focused tests for each task group

## Step 1: Validate Input

```bash
SPEC_NAME="$ARGUMENTS"
if [[ ! "$SPEC_NAME" =~ ^[a-z0-9-]+$ ]]; then
  echo "❌ ERROR: Invalid spec name '$SPEC_NAME'"
  exit 1
fi
echo "✓ Spec name validated"
```

## Step 2: Check Prerequisites

```bash
SPEC_NAME="$ARGUMENTS"
SPEC_PATH="agent-os/specs/$SPEC_NAME"

if [ ! -f "$SPEC_PATH/spec.md" ]; then
    echo "❌ ERROR: No spec.md found. Run /agent-os/write-spec $SPEC_NAME first."
    exit 1
fi

echo "✓ Prerequisites validated"
```

## Step 3: Launch Tasks List Creator Agent

```javascript
await Task({
  subagent: 'tasks-list-creator',  // ✅ Named agent
  description: 'Create implementation tasks',

  context: {
    spec_name: ARGUMENTS,
    spec_path: `agent-os/specs/${ARGUMENTS}`,
    spec_file: `agent-os/specs/${ARGUMENTS}/spec.md`,
    requirements_file: `agent-os/specs/${ARGUMENTS}/requirements.md`,
    standards_path: '.claude/standards/',
    output_file: `agent-os/specs/${ARGUMENTS}/tasks.md`
  },

  validation: {
    required_outputs: ['tasks.md'],
    schema: '.claude/validation/schemas/agent-os/tasks-output.json',
    quality_threshold: 0.9,
    content_checks: [
      { type: 'min_count', item: 'task_groups', count: 4 },
      { type: 'min_count', item: 'total_tasks', count: 5 },
      { type: 'min_count', item: 'testing_tasks', count: 2 },
      { type: 'dependencies_defined', required: true },
      { type: 'acceptance_criteria_per_task', required: true }
    ]
  },

  retry: {
    max_attempts: 3,
    backoff: 'exponential'
  },

  cost_limit: 0.20,
  preserve_context: true
})
```

## Step 4: Validate Output

```bash
SPEC_NAME="$ARGUMENTS"
TASKS_FILE="agent-os/specs/$SPEC_NAME/tasks.md"

if [ ! -f "$TASKS_FILE" ]; then
  echo "❌ ERROR: tasks.md not created"
  exit 1
fi

FILE_SIZE=$(wc -c < "$TASKS_FILE" | tr -d ' ')
if [ "$FILE_SIZE" -lt 1500 ]; then
  echo "⚠️  WARNING: tasks.md is small ($FILE_SIZE chars)"
fi

# Check for required groups
for group in "Database" "API" "Frontend" "Integration"; do
  if grep -q "$group" "$TASKS_FILE"; then
    echo "✓ Group found: $group"
  else
    echo "❌ Missing group: $group"
  fi
done

echo "✓ Validation complete"
```

## Completion

```
═══════════════════════════════════════════════════
        TASKS CREATED ✓
═══════════════════════════════════════════════════

Spec: $ARGUMENTS
Agent: tasks-list-creator v2.0.0
Version: 2.0.0

File Created:
  ✓ agent-os/specs/$ARGUMENTS/tasks.md

Execution Order:
  1. Database Layer
  2. API Layer
  3. Frontend Layer
  4. Integration & Gap Analysis

Validations Passed:
  ✓ Task groups defined (≥4)
  ✓ Dependencies declared
  ✓ Testing tasks included
  ✓ Quality threshold (≥0.9)

NEXT STEPS:
→ Review the task list
→ Run /agent-os/verify-spec $ARGUMENTS (optional)
→ Run /agent-os/implement-tasks $ARGUMENTS

═══════════════════════════════════════════════════
```
