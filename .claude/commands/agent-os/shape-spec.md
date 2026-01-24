---
description: Gather detailed requirements through targeted questions and visual analysis
argument-hint: <spec-name>
allowed-tools: Task, Read, Write, AskUserQuestion
model: claude-sonnet-4-5
timeout: 1800
retry: 3
cost_estimate: 0.18

# Validation
validation:
  input:
    spec_name:
      schema: .claude/validation/schemas/common/spec-name.json
      required: true
      description: "Feature/spec name (lowercase, alphanumeric, hyphens)"

  output:
    schema: .claude/validation/schemas/agent-os/requirements-output.json
    required_files:
      - 'agent-os/specs/${spec_name}/requirements.md'
    min_file_size: 1000
    quality_threshold: 0.9
    content_requirements:
      - "Overview section"
      - "User Stories section"
      - "Acceptance Criteria section"
      - "Technical Requirements section"
      - "Non-Functional Requirements section"
      - "Standards References"
      - "At least 3 user stories"
      - "At least 5 acceptance criteria"
      - "Reference to at least 1 standard from .claude/standards/"

# Prerequisites
prerequisites:
  - command: /agent-os/init-spec
    file_exists: 'agent-os/specs/${spec_name}/idea.md'
    error_message: "Run /agent-os/init-spec ${spec_name} first to create the spec folder"

# Version
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to named agent reference (spec-shaper)"
      - "Added comprehensive input/output validation"
      - "Added retry logic with exponential backoff (max 3 attempts)"
      - "Added cost limit ($0.25) and budget alerts"
      - "Added context preservation for session continuity"
      - "Enhanced error messages with recovery hints"
      - "Added quality score validation (minimum 0.9)"
  - version: 1.0.0
    date: 2025-10-15
    changes:
      - "Initial command implementation with generic agent"
---

# Shape Spec

Spec: **$ARGUMENTS**

## Overview

This command:

1. Analyzes the initial idea and any visual assets
2. Asks targeted questions to gather requirements
3. Creates comprehensive requirements.md

## Step 1: Validate Input

```bash
SPEC_NAME="$ARGUMENTS"

# Validate spec name format
if [[ ! "$SPEC_NAME" =~ ^[a-z0-9-]+$ ]]; then
  echo "❌ ERROR: Invalid spec name '$SPEC_NAME'"
  echo "   Spec names must be lowercase, alphanumeric, and hyphens only."
  echo "   Examples: user-authentication, payment-flow, dashboard-ui"
  exit 1
fi

echo "✓ Spec name validated: $SPEC_NAME"
```

## Step 2: Check Prerequisites

```bash
SPEC_NAME="$ARGUMENTS"
SPEC_PATH="agent-os/specs/$SPEC_NAME"

if [ ! -f "$SPEC_PATH/idea.md" ]; then
    echo "❌ ERROR: No idea.md found at $SPEC_PATH/idea.md"
    echo "   Run /agent-os/init-spec $SPEC_NAME first to create the spec folder"
    exit 1
fi

if [ ! -d "$SPEC_PATH" ]; then
    echo "❌ ERROR: Spec folder not found: $SPEC_PATH"
    echo "   Run /agent-os/init-spec $SPEC_NAME first"
    exit 1
fi

echo "✓ Prerequisites validated"
```

## Step 3: Launch Spec Shaper Agent

Use the **spec-shaper** agent (named agent from registry):

```javascript
await Task({
  subagent: 'spec-shaper',  // ✅ Named agent from registry
  description: 'Shape spec requirements',

  // Structured context object
  context: {
    spec_name: ARGUMENTS,
    spec_path: `agent-os/specs/${ARGUMENTS}`,
    idea_file: `agent-os/specs/${ARGUMENTS}/idea.md`,
    visuals_path: `agent-os/specs/${ARGUMENTS}/visuals/`,
    standards_path: '.claude/standards/',
    output_file: `agent-os/specs/${ARGUMENTS}/requirements.md`
  },

  // Output validation
  validation: {
    required_outputs: ['requirements.md'],
    schema: '.claude/validation/schemas/agent-os/requirements-output.json',
    quality_threshold: 0.9,
    content_checks: [
      { type: 'section_exists', section: 'Overview' },
      { type: 'section_exists', section: 'User Stories' },
      { type: 'section_exists', section: 'Acceptance Criteria' },
      { type: 'section_exists', section: 'Technical Requirements' },
      { type: 'section_exists', section: 'Non-Functional Requirements' },
      { type: 'min_count', item: 'user_stories', count: 3 },
      { type: 'min_count', item: 'acceptance_criteria', count: 5 },
      { type: 'references_standards', min_count: 1 }
    ]
  },

  // Retry logic
  retry: {
    max_attempts: 3,
    on_failure: 'notify-user',
    backoff: 'exponential',
    retry_on: ['timeout', 'validation_failure', 'quality_threshold_not_met']
  },

  // Cost controls
  cost_limit: 0.25,
  alert_threshold: 0.85,

  // Context preservation
  preserve_context: true,
  session_id: `shape-spec-${ARGUMENTS}-${Date.now()}`
})
```

## Step 4: Validate Output

```bash
SPEC_NAME="$ARGUMENTS"
REQUIREMENTS_FILE="agent-os/specs/$SPEC_NAME/requirements.md"
VALIDATION_PASSED=true

echo ""
echo "Validating outputs..."

# Check requirements.md exists
if [ ! -f "$REQUIREMENTS_FILE" ]; then
  echo "❌ ERROR: requirements.md not created at $REQUIREMENTS_FILE"
  echo "   Agent should have created this file. Check agent logs."
  VALIDATION_PASSED=false
  exit 1
fi

echo "✓ requirements.md created"

# Check file size (minimum 1000 chars)
FILE_SIZE=$(wc -c < "$REQUIREMENTS_FILE" | tr -d ' ')
if [ "$FILE_SIZE" -lt 1000 ]; then
  echo "⚠️  WARNING: requirements.md is small ($FILE_SIZE chars). Expected at least 1000."
  echo "   The file may be incomplete. Review for completeness."
fi

# Check for required sections
REQUIRED_SECTIONS=(
  "Overview"
  "User Stories"
  "Acceptance Criteria"
  "Technical Requirements"
  "Non-Functional Requirements"
)

for section in "${REQUIRED_SECTIONS[@]}"; do
  if grep -q "## $section" "$REQUIREMENTS_FILE"; then
    echo "✓ Section found: $section"
  else
    echo "❌ Missing section: $section"
    VALIDATION_PASSED=false
  fi
done

# Check for standards references
if grep -q ".claude/standards/" "$REQUIREMENTS_FILE"; then
  echo "✓ Standards referenced"
else
  echo "⚠️  WARNING: No standards referenced from .claude/standards/"
fi

if [ "$VALIDATION_PASSED" = false ]; then
  echo ""
  echo "❌ VALIDATION FAILED: requirements.md is incomplete"
  echo "   Review the file and re-run if necessary"
  exit 1
fi

echo "✓ All validations passed"
```

## Completion

```
═══════════════════════════════════════════════════
        REQUIREMENTS SHAPED ✓
═══════════════════════════════════════════════════

Spec: $ARGUMENTS
Agent: spec-shaper v2.0.0
Version: 2.0.0

File Created:
  ✓ agent-os/specs/$ARGUMENTS/requirements.md

Validations Passed:
  ✓ Input validation (spec name format)
  ✓ Prerequisites (idea.md exists)
  ✓ Output validation (all required sections)
  ✓ Quality threshold (≥0.9)
  ✓ Standards referenced

NEXT STEPS:
→ Review the requirements document
→ Run /agent-os/write-spec $ARGUMENTS

═══════════════════════════════════════════════════
```
