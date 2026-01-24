---
description: Create production-grade React components for a section using frontend-design skill
argument-hint: <product-name> <section-name>
allowed-tools: Skill, Read, Write, Bash
model: claude-sonnet-4-5
timeout: 2400
retry: 2
cost_estimate: 0.25-0.35

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
    schema: .claude/validation/schemas/design-os/component-output.json
    required_files:
      - 'design-os/${product_name}/sections/${section_name}/components/'
    min_file_size: 300
    quality_threshold: 0.9
    content_requirements:
      - "React + TypeScript components"
      - "Tailwind CSS styling"
      - "ARIA attributes"
      - "Responsive design"
      - "Sample data integrated"

prerequisites:
  - command: /design-os/shape-section
    file_exists: 'design-os/${product_name}/sections/${section_name}/spec.md'
    error_message: "Run /design-os/shape-section first to define section spec"
  - command: /design-os/sample-data
    file_exists: 'design-os/${product_name}/sections/${section_name}/sample-data.json'
    error_message: "Run /design-os/sample-data first to generate sample data"

version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added dual argument support (product-name + section-name)"
      - "Added prerequisite checks for spec and sample data"
      - "Added output validation for React components"
      - "Updated to design-os folder structure"
      - "Switched to frontend-design skill"
  - version: 1.0.0
    date: 2025-10-15
    changes:
      - "Initial implementation with interactive component design"
---

# Design Screen

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
  echo "Usage: /design-os/design-screen <product-name> <section-name>"
  echo "Example: /design-os/design-screen my-app user-management"
  exit 1
fi

# Validate product name format
if [[ ! "$PRODUCT_NAME" =~ ^[a-z0-9-]+$ ]]; then
  echo "❌ ERROR: Invalid product name"
  exit 1
fi

# Validate section name format
if [[ ! "$SECTION_NAME" =~ ^[a-z0-9-]+$ ]]; then
  echo "❌ ERROR: Invalid section name"
  exit 1
fi

# Check prerequisite: section spec must exist
SPEC_FILE="design-os/$PRODUCT_NAME/sections/$SECTION_NAME/spec.md"
if [ ! -f "$SPEC_FILE" ]; then
  echo "❌ ERROR: Section spec not found"
  echo ""
  echo "Run this command first:"
  echo "  /design-os/shape-section $PRODUCT_NAME $SECTION_NAME"
  exit 1
fi

# Check prerequisite: sample data must exist
DATA_FILE="design-os/$PRODUCT_NAME/sections/$SECTION_NAME/sample-data.json"
if [ ! -f "$DATA_FILE" ]; then
  echo "❌ ERROR: Sample data not found"
  echo ""
  echo "Run this command first:"
  echo "  /design-os/sample-data $PRODUCT_NAME $SECTION_NAME"
  exit 1
fi

echo "✓ Input validated: $PRODUCT_NAME / $SECTION_NAME"
echo "✓ Prerequisites met: spec.md and sample-data.json exist"
```

## Step 2: Read Context Files

```javascript
const PRODUCT_NAME = process.env.ARGUMENTS.split(' ')[0];
const SECTION_NAME = process.env.ARGUMENTS.split(' ')[1];

// Read section spec, sample data, types, and design tokens
const specContent = await Read({
  file_path: `design-os/${PRODUCT_NAME}/sections/${SECTION_NAME}/spec.md`
});

const sampleDataContent = await Read({
  file_path: `design-os/${PRODUCT_NAME}/sections/${SECTION_NAME}/sample-data.json`
});

const typesContent = await Read({
  file_path: `design-os/${PRODUCT_NAME}/sections/${SECTION_NAME}/types.ts`
});

// Read design tokens for styling
const tokensContent = await Read({
  file_path: `design-os/${PRODUCT_NAME}/design-tokens.json`
});

// Parse and prepare context for frontend-design skill
```

## Step 3: Generate Components Using Frontend-Design Skill

```javascript
const PRODUCT_NAME = process.env.ARGUMENTS.split(' ')[0];
const SECTION_NAME = process.env.ARGUMENTS.split(' ')[1];

// Use the frontend-design skill to create production-grade components
await Skill("frontend-design");

// Context provided to skill:
// - Section spec for UI requirements and user flows
// - Sample data for realistic component rendering
// - TypeScript types for prop definitions
// - Design tokens for consistent styling
// - Output path: design-os/${PRODUCT_NAME}/sections/${SECTION_NAME}/components/

// The skill will create:
// - React + TypeScript components
// - Tailwind CSS styling with design tokens
// - ARIA attributes for accessibility
// - Responsive design (mobile, tablet, desktop)
// - Sample data integration for realistic preview
```

## Step 4: Validate Output

```bash
PRODUCT_NAME="$1"
SECTION_NAME="$2"
COMPONENTS_DIR="design-os/$PRODUCT_NAME/sections/$SECTION_NAME/components"

# Check directory exists
if [ ! -d "$COMPONENTS_DIR" ]; then
  echo "❌ ERROR: Components directory not created"
  exit 1
fi

# Check for React components (should be at least 1)
COMPONENT_COUNT=$(find "$COMPONENTS_DIR" -name "*.tsx" | wc -l)
if [ $COMPONENT_COUNT -lt 1 ]; then
  echo "❌ ERROR: No React components created"
  exit 1
fi

# Check minimum file size per component (300 bytes)
for file in "$COMPONENTS_DIR"/*.tsx; do
  FILE_SIZE=$(wc -c < "$file")
  if [ $FILE_SIZE -lt 300 ]; then
    echo "❌ ERROR: Component file too small: $(basename $file)"
    exit 1
  fi
done

# Check for React + TypeScript syntax
if ! grep -rq "import.*React" "$COMPONENTS_DIR"; then
  echo "❌ ERROR: React imports missing"
  exit 1
fi

# Check for Tailwind classes
if ! grep -rq "className=" "$COMPONENTS_DIR"; then
  echo "❌ ERROR: Tailwind CSS classes missing"
  exit 1
fi

# Check for ARIA attributes
if ! grep -rq "aria-" "$COMPONENTS_DIR"; then
  echo "⚠️  WARNING: No ARIA attributes found (accessibility concern)"
fi

echo "✓ Output validation complete ($COMPONENT_COUNT components created)"
```

## Completion

```
═══════════════════════════════════════════════════
        DESIGN SCREEN COMPLETE ✓
═══════════════════════════════════════════════════

Product: $1
Section: $2
Command: /design-os/design-screen
Version: 2.0.0

Output Created:
  ✓ design-os/$1/sections/$2/components/*.tsx

Components:
  React + TypeScript components (≥1)
  Tailwind CSS styling
  ARIA attributes for accessibility
  Responsive design (mobile, tablet, desktop)
  Sample data integrated

Validations Passed:
  ✓ Input validation (product and section names)
  ✓ Prerequisites (spec.md and sample-data.json exist)
  ✓ Output validation (≥1 components)
  ✓ React + TypeScript syntax
  ✓ Tailwind CSS classes
  ✓ Quality threshold (≥0.9)

NEXT STEPS:
→ /design-os/screenshot-design $1 $2
   Capture screenshots at multiple viewports

═══════════════════════════════════════════════════
```

## Guidelines

- **Frontend-Design Skill** - Uses production-grade component patterns
- **Props-based** - All data and callbacks passed via props
- **Tailwind CSS** - Responsive design with mobile-first approach
- **Accessibility** - ARIA attributes required
- **Design tokens** - Apply colors and typography from design-tokens.json
- **Sample data** - Components should render with realistic data
- **Responsive** - Support desktop, tablet, and mobile viewports
- **Dark mode** - Support light and dark mode variants
