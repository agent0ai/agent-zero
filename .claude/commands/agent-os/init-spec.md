---
description: Initialize a new spec folder structure and capture initial idea
argument-hint: <feature-name>
allowed-tools: Task, Read, Write, Bash, AskUserQuestion
model: haiku
timeout: 300
retry: 2
cost_estimate: 0.02

# Validation
validation:
  input:
    spec_name:
      schema: .claude/validation/schemas/common/spec-name.json
      required: true
      description: "Feature/spec name (lowercase, alphanumeric, hyphens)"

  output:
    required_files:
      - 'agent-os/specs/${spec_name}/idea.md'
      - 'agent-os/specs/${spec_name}/requirements.md'
      - 'agent-os/specs/${spec_name}/spec.md'
      - 'agent-os/specs/${spec_name}/tasks.md'
    required_directories:
      - 'agent-os/specs/${spec_name}/visuals'
      - 'agent-os/specs/${spec_name}/verification/screenshots'
    min_idea_file_size: 100
    quality_threshold: 0.9

# Prerequisites
prerequisites: []

# Version
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Added validation for spec name (must be lowercase, alphanumeric, hyphens)"
      - "Added output validation for required files and directories"
      - "Added retry logic (max 2 attempts)"
      - "Added cost estimate and timeout"
      - "Improved error messages with helpful hints"
  - version: 1.0.0
    date: 2025-10-15
    changes:
      - "Initial command implementation"
---

# Initialize Spec

Feature: **$ARGUMENTS**

## Overview

This command:

1. **Validates** the spec name
2. **Creates** the spec folder structure
3. **Captures** the initial feature idea
4. **Prepares** placeholder files for the workflow

## Step 0: Validate Input

```bash
SPEC_NAME="$ARGUMENTS"

# Validate spec name format (lowercase, alphanumeric, hyphens only)
if [[ ! "$SPEC_NAME" =~ ^[a-z0-9-]+$ ]]; then
  echo "❌ ERROR: Invalid spec name '$SPEC_NAME'"
  echo "   Spec names must be lowercase, alphanumeric, and hyphens only."
  echo "   Examples: user-authentication, payment-flow, dashboard-ui"
  exit 1
fi

# Check length (3-50 characters)
SPEC_LENGTH=${#SPEC_NAME}
if [ "$SPEC_LENGTH" -lt 3 ]; then
  echo "❌ ERROR: Spec name too short ($SPEC_LENGTH chars). Minimum: 3 characters"
  exit 1
fi
if [ "$SPEC_LENGTH" -gt 50 ]; then
  echo "❌ ERROR: Spec name too long ($SPEC_LENGTH chars). Maximum: 50 characters"
  exit 1
fi

# Check if spec already exists
if [ -d "agent-os/specs/$SPEC_NAME" ]; then
  echo "❌ ERROR: Spec '$SPEC_NAME' already exists at agent-os/specs/$SPEC_NAME"
  echo "   Choose a different name or delete the existing spec"
  exit 1
fi

echo "✓ Spec name validated: $SPEC_NAME"
```

## Step 1: Create Folder Structure

```bash
SPEC_NAME="$ARGUMENTS"
mkdir -p "agent-os/specs/$SPEC_NAME/visuals"
mkdir -p "agent-os/specs/$SPEC_NAME/verification/screenshots"
echo "✓ Created spec folder: agent-os/specs/$SPEC_NAME"
```

## Step 2: Capture Initial Idea

Ask the user:
> "Describe your idea for **$ARGUMENTS**. Don't worry about structure - just share what's on your mind. Include any goals, user stories, or features you're thinking about."

## Step 3: Create Idea Document

Create `agent-os/specs/$ARGUMENTS/idea.md`:

```markdown
# $ARGUMENTS - Initial Idea

## Raw Concept
[User's unstructured description]

## Initial Thoughts
- [Key point 1]
- [Key point 2]
- [Key point 3]

## Questions to Explore
- [Question that needs clarification]
- [Another question]

---
*Captured on: [date]*
*Status: Ready for shaping*
```

## Step 4: Create Placeholder Files

```bash
SPEC_NAME="$ARGUMENTS"

# Requirements placeholder
cat > "agent-os/specs/$SPEC_NAME/requirements.md" << 'EOF'
# Requirements

*To be filled by /agent-os/shape-spec*
EOF

# Spec placeholder
cat > "agent-os/specs/$SPEC_NAME/spec.md" << 'EOF'
# Specification

*To be filled by /agent-os/write-spec*
EOF

# Tasks placeholder
cat > "agent-os/specs/$SPEC_NAME/tasks.md" << 'EOF'
# Implementation Tasks

*To be filled by /agent-os/create-tasks*
EOF

echo "✓ Created placeholder files"
```

## Step 5: Prompt for Visuals

Ask the user:
> "Do you have any visual references (screenshots, mockups, wireframes) for this feature? If so, add them to `agent-os/specs/$ARGUMENTS/visuals/`"

## Step 6: Validate Output

```bash
SPEC_NAME="$ARGUMENTS"
SPEC_PATH="agent-os/specs/$SPEC_NAME"
VALIDATION_PASSED=true

echo ""
echo "Validating outputs..."

# Check required files exist
REQUIRED_FILES=(
  "$SPEC_PATH/idea.md"
  "$SPEC_PATH/requirements.md"
  "$SPEC_PATH/spec.md"
  "$SPEC_PATH/tasks.md"
)

for file in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "$file" ]; then
    echo "❌ Missing required file: $file"
    VALIDATION_PASSED=false
  else
    echo "✓ Created: $file"
  fi
done

# Check required directories exist
REQUIRED_DIRS=(
  "$SPEC_PATH/visuals"
  "$SPEC_PATH/verification/screenshots"
)

for dir in "${REQUIRED_DIRS[@]}"; do
  if [ ! -d "$dir" ]; then
    echo "❌ Missing required directory: $dir"
    VALIDATION_PASSED=false
  else
    echo "✓ Created: $dir/"
  fi
done

# Check idea.md has content (minimum 100 chars)
IDEA_SIZE=$(wc -c < "$SPEC_PATH/idea.md" | tr -d ' ')
if [ "$IDEA_SIZE" -lt 100 ]; then
  echo "⚠️  WARNING: idea.md is very small ($IDEA_SIZE chars). Did you capture the user's description?"
fi

if [ "$VALIDATION_PASSED" = false ]; then
  echo ""
  echo "❌ VALIDATION FAILED: Some required files/directories were not created"
  exit 1
fi

echo "✓ All outputs validated"
```

## Completion

```
═══════════════════════════════════════════════════
        SPEC INITIALIZED ✓
═══════════════════════════════════════════════════

Feature: $ARGUMENTS
Location: agent-os/specs/$ARGUMENTS/
Version: 2.0.0

Files Created:
  ✓ idea.md (your initial concept)
  ✓ requirements.md (placeholder)
  ✓ spec.md (placeholder)
  ✓ tasks.md (placeholder)
  ✓ visuals/ (for screenshots, mockups)
  ✓ verification/screenshots/ (for verification)

NEXT STEPS:
→ Add any visual references to visuals/
→ Run /agent-os/shape-spec $ARGUMENTS

═══════════════════════════════════════════════════
```
