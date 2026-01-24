---
description: Define detailed spec for a specific product section
argument-hint: <product-name> <section-name>
allowed-tools: Read, Write, Edit, AskUserQuestion, Bash
model: claude-sonnet-4-5
timeout: 1500
retry: 2
cost_estimate: 0.14-0.20

validation:
  input:
    product_name:
      schema: .claude/validation/schemas/common/spec-name.json
      required: true
      error_template: INVALID_SPEC_NAME
    section_name:
      schema: .claude/validation/schemas/common/spec-name.json
      required: true
      error_template: INVALID_SPEC_NAME
  output:
    schema: .claude/validation/schemas/design-os/section-spec-output.json
    required_files:
      - 'design-os/${product_name}/sections/${section_name}/spec.md'
    min_file_size: 1000
    quality_threshold: 0.9
    content_requirements:
      - "User flows defined"
      - "UI patterns specified"
      - "Data requirements documented"
      - "At least 1 user flow"

prerequisites:
  - command: /design-os/product-roadmap
    file_exists: 'design-os/${product_name}/roadmap.md'
    error_message: "Run /design-os/product-roadmap first to define sections"
  - command: /design-os/data-model
    file_exists: 'design-os/${product_name}/data-model.md'
    error_message: "Run /design-os/data-model first to define entities"

version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added dual argument support (product-name + section-name)"
      - "Added prerequisite checks for roadmap and data-model"
      - "Added output validation for section specs"
      - "Updated to design-os folder structure"
  - version: 1.0.0
    date: 2025-10-15
    changes:
      - "Initial implementation with interactive flow design"
---

# Shape Section

Product: **$1**
Section: **$2**

## Step 1: Validate Input & Prerequisites

```bash
PRODUCT_NAME="$1"
SECTION_NAME="$2"

# Check both arguments provided
if [ -z "$SECTION_NAME" ]; then
  echo "❌ ERROR: Missing section name"
  echo ""
  echo "Usage: /design-os/shape-section <product-name> <section-name>"
  echo "Example: /design-os/shape-section my-app user-management"
  exit 1
fi

# Validate product name format
if [[ ! "$PRODUCT_NAME" =~ ^[a-z0-9-]+$ ]]; then
  echo "❌ ERROR: Invalid product name"
  echo ""
  echo "Product name must:"
  echo "  • Be lowercase"
  echo "  • Use only letters, numbers, and hyphens"
  exit 1
fi

# Validate section name format
if [[ ! "$SECTION_NAME" =~ ^[a-z0-9-]+$ ]]; then
  echo "❌ ERROR: Invalid section name"
  echo ""
  echo "Section name must:"
  echo "  • Be lowercase"
  echo "  • Use only letters, numbers, and hyphens"
  exit 1
fi

# Check prerequisite: roadmap.md must exist
ROADMAP_FILE="design-os/$PRODUCT_NAME/roadmap.md"
if [ ! -f "$ROADMAP_FILE" ]; then
  echo "❌ ERROR: Product roadmap not found"
  echo ""
  echo "Run this command first:"
  echo "  /design-os/product-roadmap $PRODUCT_NAME"
  exit 1
fi

# Check prerequisite: data-model.md must exist
DATA_MODEL_FILE="design-os/$PRODUCT_NAME/data-model.md"
if [ ! -f "$DATA_MODEL_FILE" ]; then
  echo "❌ ERROR: Data model not found"
  echo ""
  echo "Run this command first:"
  echo "  /design-os/data-model $PRODUCT_NAME"
  exit 1
fi

echo "✓ Input validated: $PRODUCT_NAME / $SECTION_NAME"
echo "✓ Prerequisites met: roadmap.md and data-model.md exist"
```

## Step 2: Read Context Files

```javascript
const PRODUCT_NAME = process.env.ARGUMENTS.split(' ')[0];
const SECTION_NAME = process.env.ARGUMENTS.split(' ')[1];

// Read product context
const roadmapContent = await Read({
  file_path: `design-os/${PRODUCT_NAME}/roadmap.md`
});

const dataModelContent = await Read({
  file_path: `design-os/${PRODUCT_NAME}/data-model.md`
});

// Verify section exists in roadmap
// Extract relevant entities from data model for this section
```

## Step 3: Initial Input

Start the conversation:

> "Let's define the [Section Name] section. What are you thinking for this part of the product? Share any ideas about features, user flows, or UI patterns you have in mind."

If user has nothing prepared:
> "No worries - let me ask some questions to help shape this."

## Step 4: Clarifying Questions

Ask 4-6 targeted questions:

1. "What are the main things a user can **do** in this section?"
2. "What information needs to be **displayed**?"
3. "Walk me through the **key user flows** - what happens step by step?"
4. "Any specific **UI patterns** you're imagining? (tables, cards, forms, etc.)"
5. "What's **out of scope** for this section?"
6. "Any **edge cases** to consider? (empty states, errors, permissions)"

**Guidelines:**

- Ask questions in pairs (not all at once)
- Probe vague answers for specifics
- Focus on UX and UI - not backend or database
- Keep it conversational

## Step 5: Shell Configuration

If app shell exists (`src/shell/components/AppShell.tsx`):

> "Should this section render **inside the app shell** (with navigation visible) or as a **standalone page** (full-screen, no nav)?"

Options:

- **Inside shell** - Standard section within the app
- **Standalone** - Full-screen experience (onboarding, focus modes)

## Step 6: Draft & Refine

Present the specification:

```markdown
# [Section Name] Specification

## Overview
[Brief description of what this section does]

## User Flows

### Flow 1: [Name]
1. User does X
2. System shows Y
3. User can then Z

### Flow 2: [Name]
1. [Steps...]

## UI Requirements

### Main View
- [What the user sees first]
- [Key components and layout]

### [Additional Views]
- [Description of other states/views]

## Components Needed
- [Component 1] - [purpose]
- [Component 2] - [purpose]

## Shell Configuration
Renders: [inside shell / standalone]

## Out of Scope
- [What this section does NOT do]
```

Ask: "Does this capture what you're thinking? Anything to add or change?"

Iterate until approved.

## Step 7: Create Section Spec File

```javascript
const PRODUCT_NAME = process.env.ARGUMENTS.split(' ')[0];
const SECTION_NAME = process.env.ARGUMENTS.split(' ')[1];

const specPath = `design-os/${PRODUCT_NAME}/sections/${SECTION_NAME}/spec.md`;

await Write({
  file_path: specPath,
  content: `# ${SECTION_NAME}

## Overview
[One paragraph description based on user input]

## User Flows

### [Flow Name]
1. [Step 1]
2. [Step 2]
3. [Step 3]

### [Flow Name]
1. [Step 1]
2. [Step 2]

## UI Requirements

### [View Name]
- [Requirement 1]
- [Requirement 2]

### [View Name]
- [Requirement 1]

## Data Requirements
- **Entities Used:** [entities from data model]
- **Operations:** [create, read, update, delete]

## Shell Configuration
- **Renders in shell:** [yes/no]
- **Header visible:** [yes/no]

## Out of Scope
- [Item 1]
- [Item 2]
`
});
```

## Step 8: Validate Output

```bash
PRODUCT_NAME="$1"
SECTION_NAME="$2"
SPEC_FILE="design-os/$PRODUCT_NAME/sections/$SECTION_NAME/spec.md"

# Check file exists
if [ ! -f "$SPEC_FILE" ]; then
  echo "❌ ERROR: Section spec file not created"
  exit 1
fi

# Check minimum file size (1000 bytes)
FILE_SIZE=$(wc -c < "$SPEC_FILE")
if [ $FILE_SIZE -lt 1000 ]; then
  echo "❌ ERROR: Section spec too small (< 1000 bytes)"
  echo "Current size: $FILE_SIZE bytes"
  exit 1
fi

# Check for required sections
REQUIRED_SECTIONS=("## Overview" "## User Flows" "## UI Requirements")
for section in "${REQUIRED_SECTIONS[@]}"; do
  if ! grep -q "$section" "$SPEC_FILE"; then
    echo "❌ ERROR: Missing required section: $section"
    exit 1
  fi
done

# Check at least 1 user flow defined
FLOW_COUNT=$(grep -c "^### " "$SPEC_FILE")
if [ $FLOW_COUNT -lt 1 ]; then
  echo "❌ ERROR: Need at least 1 user flow defined"
  exit 1
fi

echo "✓ Output validation complete ($FLOW_COUNT user flows defined)"
```

## Completion

```
═══════════════════════════════════════════════════
        SECTION SPEC COMPLETE ✓
═══════════════════════════════════════════════════

Product: $1
Section: $2
Command: /design-os/shape-section
Version: 2.0.0

Output Created:
  ✓ design-os/$1/sections/$2/spec.md

Specification:
  User flows defined (≥1)
  UI patterns specified
  Data requirements documented
  Shell configuration set

Validations Passed:
  ✓ Input validation (product and section names)
  ✓ Prerequisites (roadmap.md and data-model.md exist)
  ✓ Output validation (≥1000 bytes)
  ✓ Required sections present
  ✓ Quality threshold (≥0.9)

NEXT STEPS:
→ /design-os/sample-data $1 $2
   Generate realistic sample data for this section

═══════════════════════════════════════════════════
```

## Guidelines

- **Focus on UX/UI** - Don't discuss backend, database, or API details
- **Be specific** - Vague specs lead to vague designs
- **Include only what was discussed** - Don't add extra features
- **Conversational tone** - Not a rigid questionnaire
- **Iterate freely** - Refine until the user is satisfied
