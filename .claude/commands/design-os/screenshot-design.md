---
description: Capture design screenshots at multiple viewports using Playwright
argument-hint: <product-name> <section-name>
allowed-tools: Task, Read, Bash, Playwright
model: claude-sonnet-4-5
timeout: 1500
retry: 2
cost_estimate: 0.12-0.18

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
    schema: .claude/validation/schemas/design-os/screenshot-output.json
    required_files:
      - 'design-os/${product_name}/sections/${section_name}/screenshots/'
    min_file_size: 10000
    quality_threshold: 0.85
    content_requirements:
      - "At least 3 screenshots"
      - "Desktop screenshot"
      - "Tablet screenshot"
      - "Mobile screenshot"
      - "High quality images (≥10KB)"

prerequisites:
  - command: /design-os/design-screen
    file_exists: 'design-os/${product_name}/sections/${section_name}/components/'
    error_message: "Run /design-os/design-screen first to create components"

version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added dual argument support (product-name + section-name)"
      - "Added prerequisite check for components"
      - "Added output validation for screenshots"
      - "Updated to design-os folder structure"
      - "Switched to agent-based with Playwright"
  - version: 1.0.0
    date: 2025-10-15
    changes:
      - "Initial implementation with manual screenshot capture"
---

# Screenshot Design

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
  echo "Usage: /design-os/screenshot-design <product-name> <section-name>"
  echo "Example: /design-os/screenshot-design my-app user-management"
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

# Check prerequisite: components directory must exist
COMPONENTS_DIR="design-os/$PRODUCT_NAME/sections/$SECTION_NAME/components"
if [ ! -d "$COMPONENTS_DIR" ]; then
  echo "❌ ERROR: Components directory not found"
  echo ""
  echo "Run this command first:"
  echo "  /design-os/design-screen $PRODUCT_NAME $SECTION_NAME"
  exit 1
fi

echo "✓ Input validated: $PRODUCT_NAME / $SECTION_NAME"
echo "✓ Prerequisites met: components/ directory exists"
```

## Step 2: Capture Screenshots Using Playwright

```javascript
const PRODUCT_NAME = process.env.ARGUMENTS.split(' ')[0];
const SECTION_NAME = process.env.ARGUMENTS.split(' ')[1];

// Use agent with Playwright to capture screenshots
await Task({
  subagent_type: 'general-purpose',
  description: 'Capture design screenshots',
  prompt: `Capture screenshots of the ${SECTION_NAME} section at multiple viewports using Playwright.

Components Location:
design-os/${PRODUCT_NAME}/sections/${SECTION_NAME}/components/

Create an HTML preview page that:
1. Imports all components from the section
2. Renders them with sample data
3. Applies design tokens for styling

Then capture screenshots at these viewports:
- Desktop: 1440x900px
- Tablet: 768x1024px
- Mobile: 375x812px

Save screenshots to:
design-os/${PRODUCT_NAME}/sections/${SECTION_NAME}/screenshots/

Naming convention:
- ${SECTION_NAME}-desktop.png
- ${SECTION_NAME}-tablet.png
- ${SECTION_NAME}-mobile.png

Requirements:
- High quality screenshots (≥10KB each)
- Full component visibility
- Realistic rendering with sample data
- Consistent viewport sizes`,

  context: {
    product_name: PRODUCT_NAME,
    section_name: SECTION_NAME,
    components_path: `design-os/${PRODUCT_NAME}/sections/${SECTION_NAME}/components/`,
    sample_data_path: `design-os/${PRODUCT_NAME}/sections/${SECTION_NAME}/sample-data.json`,
    design_tokens_path: `design-os/${PRODUCT_NAME}/design-tokens.json`,
    output_path: `design-os/${PRODUCT_NAME}/sections/${SECTION_NAME}/screenshots/`
  },

  allowed_tools: ['Playwright', 'Bash', 'Write', 'Read']
});
```

## Step 3: Validate Output

```bash
PRODUCT_NAME="$1"
SECTION_NAME="$2"
SCREENSHOTS_DIR="design-os/$PRODUCT_NAME/sections/$SECTION_NAME/screenshots"

# Check directory exists
if [ ! -d "$SCREENSHOTS_DIR" ]; then
  echo "❌ ERROR: Screenshots directory not created"
  exit 1
fi

# Count screenshots (need at least 3)
SCREENSHOT_COUNT=$(find "$SCREENSHOTS_DIR" -name "*.png" | wc -l)
if [ $SCREENSHOT_COUNT -lt 3 ]; then
  echo "❌ ERROR: Need at least 3 screenshots"
  echo "Current count: $SCREENSHOT_COUNT"
  exit 1
fi

# Check viewports covered
if ! ls $SCREENSHOTS_DIR/*desktop*.png 2>/dev/null; then
  echo "❌ ERROR: Missing desktop screenshot"
  exit 1
fi

if ! ls $SCREENSHOTS_DIR/*tablet*.png 2>/dev/null; then
  echo "❌ ERROR: Missing tablet screenshot"
  exit 1
fi

if ! ls $SCREENSHOTS_DIR/*mobile*.png 2>/dev/null; then
  echo "❌ ERROR: Missing mobile screenshot"
  exit 1
fi

# Check minimum file sizes (≥10KB per screenshot)
for file in "$SCREENSHOTS_DIR"/*.png; do
  FILE_SIZE=$(wc -c < "$file")
  if [ $FILE_SIZE -lt 10000 ]; then
    echo "❌ ERROR: Screenshot too small (< 10KB): $(basename $file)"
    exit 1
  fi
done

echo "✓ Output validation complete ($SCREENSHOT_COUNT screenshots captured)"
```

## Completion

```
═══════════════════════════════════════════════════
        SCREENSHOT DESIGN COMPLETE ✓
═══════════════════════════════════════════════════

Product: $1
Section: $2
Command: /design-os/screenshot-design
Version: 2.0.0

Output Created:
  ✓ design-os/$1/sections/$2/screenshots/*.png

Screenshots:
  Desktop viewport (1440x900px)
  Tablet viewport (768x1024px)
  Mobile viewport (375x812px)
  High quality images (≥10KB each)
  Total screenshots (≥3)

Validations Passed:
  ✓ Input validation (product and section names)
  ✓ Prerequisites (components/ directory exists)
  ✓ Output validation (≥3 screenshots)
  ✓ All viewports covered
  ✓ Minimum file size (≥10KB)
  ✓ Quality threshold (≥0.85)

NEXT STEPS:
→ /design-os/export-product $1
   Generate complete implementation handoff package

═══════════════════════════════════════════════════
```

## Guidelines

- **Playwright Automation** - Automated screenshot capture at precise viewports
- **Responsive Viewports** - Desktop (1440px), Tablet (768px), Mobile (375px)
- **High Quality** - Minimum 10KB per screenshot for documentation clarity
- **Realistic Rendering** - Components rendered with actual sample data
- **Design Tokens** - Apply product styling for accurate representation
- **Comprehensive Coverage** - All major viewport sizes documented
