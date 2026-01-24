---
description: Create detailed specification document for development
argument-hint: <spec-name>
allowed-tools: Task, Read, Write, Grep, Glob
model: claude-sonnet-4-5
timeout: 2400
retry: 3
cost_estimate: 0.22

# Validation
validation:
  input:
    spec_name:
      schema: .claude/validation/schemas/common/spec-name.json
      required: true
      description: "Feature/spec name (lowercase, alphanumeric, hyphens)"

  output:
    schema: .claude/validation/schemas/agent-os/spec-output.json
    required_files:
      - 'agent-os/specs/${spec_name}/spec.md'
    min_file_size: 2000
    quality_threshold: 0.9
    content_requirements:
      - "Overview section"
      - "Architecture section"
      - "API Design section"
      - "Database Schema section"
      - "Frontend Components section"
      - "At least 1 mermaid diagram"
      - "At least 3 API endpoints defined"
      - "At least 2 database tables defined"
      - "Reference to at least 3 standards from .claude/standards/"

# Prerequisites
prerequisites:
  - command: /agent-os/shape-spec
    file_exists: 'agent-os/specs/${spec_name}/requirements.md'
    error_message: "Run /agent-os/shape-spec ${spec_name} first to create requirements"

# Version
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to named agent reference (spec-writer)"
      - "Added comprehensive input/output validation"
      - "Added retry logic with exponential backoff (max 3 attempts)"
      - "Added cost limit ($0.30) and budget alerts"
      - "Added context preservation for session continuity"
      - "Enhanced error messages with recovery hints"
      - "Added quality score validation (minimum 0.9)"
      - "Added diagram and API endpoint validation"
  - version: 1.0.0
    date: 2025-10-15
    changes:
      - "Initial command implementation with generic agent"
---

# Write Spec

Spec: **$ARGUMENTS**

## Overview

This command:

1. Analyzes requirements and visual assets
2. Searches for reusable code in the codebase
3. Creates comprehensive spec.md

## Step 1: Validate Input

```bash
SPEC_NAME="$ARGUMENTS"

# Validate spec name format
if [[ ! "$SPEC_NAME" =~ ^[a-z0-9-]+$ ]]; then
  echo "❌ ERROR: Invalid spec name '$SPEC_NAME'"
  echo "   Spec names must be lowercase, alphanumeric, and hyphens only."
  exit 1
fi

echo "✓ Spec name validated: $SPEC_NAME"
```

## Step 2: Check Prerequisites

```bash
SPEC_NAME="$ARGUMENTS"
SPEC_PATH="agent-os/specs/$SPEC_NAME"

# Check requirements.md exists
if [ ! -f "$SPEC_PATH/requirements.md" ]; then
    echo "❌ ERROR: No requirements.md found at $SPEC_PATH/requirements.md"
    echo "   Run /agent-os/shape-spec $SPEC_NAME first to create requirements"
    exit 1
fi

# Check idea.md exists
if [ ! -f "$SPEC_PATH/idea.md" ]; then
    echo "❌ ERROR: No idea.md found at $SPEC_PATH/idea.md"
    echo "   Run /agent-os/init-spec $SPEC_NAME first"
    exit 1
fi

echo "✓ Prerequisites validated"
```

## Step 3: Launch Spec Writer Agent

Use the **spec-writer** agent (named agent from registry):

```javascript
await Task({
  subagent: 'spec-writer',  // ✅ Named agent from registry
  description: 'Write detailed specification',

  // Structured context object
  context: {
    spec_name: ARGUMENTS,
    spec_path: `agent-os/specs/${ARGUMENTS}`,
    requirements_file: `agent-os/specs/${ARGUMENTS}/requirements.md`,
    idea_file: `agent-os/specs/${ARGUMENTS}/idea.md`,
    visuals_path: `agent-os/specs/${ARGUMENTS}/visuals/`,
    standards_path: '.claude/standards/',
    output_file: `agent-os/specs/${ARGUMENTS}/spec.md`,

    // Codebase search hints
    search_for: [
      'similar_features',
      'ui_components',
      'api_patterns',
      'database_schemas',
      'validation_patterns'
    ]
  },

  // Output validation
  validation: {
    required_outputs: ['spec.md'],
    schema: '.claude/validation/schemas/agent-os/spec-output.json',
    quality_threshold: 0.9,
    content_checks: [
      { type: 'section_exists', section: 'Overview' },
      { type: 'section_exists', section: 'Architecture' },
      { type: 'section_exists', section: 'API Design' },
      { type: 'section_exists', section: 'Database Schema' },
      { type: 'section_exists', section: 'Frontend Components' },
      { type: 'min_count', item: 'mermaid_diagrams', count: 1 },
      { type: 'min_count', item: 'api_endpoints', count: 3 },
      { type: 'min_count', item: 'database_tables', count: 2 },
      { type: 'references_standards', min_count: 3 }
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
  cost_limit: 0.30,
  alert_threshold: 0.85,

  // Context preservation
  preserve_context: true,
  session_id: `write-spec-${ARGUMENTS}-${Date.now()}`
})
```

## Step 4: Validate Output

```bash
SPEC_NAME="$ARGUMENTS"
SPEC_FILE="agent-os/specs/$SPEC_NAME/spec.md"
VALIDATION_PASSED=true

echo ""
echo "Validating outputs..."

# Check spec.md exists
if [ ! -f "$SPEC_FILE" ]; then
  echo "❌ ERROR: spec.md not created at $SPEC_FILE"
  echo "   Agent should have created this file. Check agent logs."
  exit 1
fi

echo "✓ spec.md created"

# Check file size (minimum 2000 chars)
FILE_SIZE=$(wc -c < "$SPEC_FILE" | tr -d ' ')
if [ "$FILE_SIZE" -lt 2000 ]; then
  echo "⚠️  WARNING: spec.md is small ($FILE_SIZE chars). Expected at least 2000."
  echo "   The specification may be incomplete."
fi

# Check for required sections
REQUIRED_SECTIONS=(
  "Overview"
  "Architecture"
  "API Design"
  "Database Schema"
  "Frontend Components"
)

for section in "${REQUIRED_SECTIONS[@]}"; do
  if grep -q "## $section" "$SPEC_FILE"; then
    echo "✓ Section found: $section"
  else
    echo "❌ Missing section: $section"
    VALIDATION_PASSED=false
  fi
done

# Check for mermaid diagrams
if grep -q '```mermaid' "$SPEC_FILE"; then
  DIAGRAM_COUNT=$(grep -c '```mermaid' "$SPEC_FILE")
  echo "✓ Diagrams found: $DIAGRAM_COUNT"
else
  echo "❌ No mermaid diagrams found"
  VALIDATION_PASSED=false
fi

# Check for standards references
if grep -q ".claude/standards/" "$SPEC_FILE"; then
  STANDARDS_COUNT=$(grep -c ".claude/standards/" "$SPEC_FILE")
  echo "✓ Standards referenced: $STANDARDS_COUNT"
  if [ "$STANDARDS_COUNT" -lt 3 ]; then
    echo "⚠️  WARNING: Only $STANDARDS_COUNT standards referenced. Expected at least 3."
  fi
else
  echo "⚠️  WARNING: No standards referenced from .claude/standards/"
fi

# Check references requirements.md
if grep -q "requirements.md" "$SPEC_FILE"; then
  echo "✓ References requirements.md"
else
  echo "⚠️  WARNING: Spec does not reference requirements.md"
fi

if [ "$VALIDATION_PASSED" = false ]; then
  echo ""
  echo "❌ VALIDATION FAILED: spec.md is incomplete"
  echo "   Review the file and re-run if necessary"
  exit 1
fi

echo "✓ All validations passed"
```

## Completion

```
═══════════════════════════════════════════════════
        SPECIFICATION COMPLETE ✓
═══════════════════════════════════════════════════

Spec: $ARGUMENTS
Agent: spec-writer v2.0.0
Version: 2.0.0

File Created:
  ✓ agent-os/specs/$ARGUMENTS/spec.md

Validations Passed:
  ✓ Input validation (spec name format)
  ✓ Prerequisites (requirements.md, idea.md exist)
  ✓ Output validation (all required sections)
  ✓ Diagrams included (mermaid)
  ✓ Quality threshold (≥0.9)
  ✓ Standards referenced (≥3)

NEXT STEPS:
→ Review the specification document
→ Run /agent-os/create-tasks $ARGUMENTS

═══════════════════════════════════════════════════
```
