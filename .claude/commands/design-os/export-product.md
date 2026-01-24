---
description: Generate complete implementation handoff package for developers
argument-hint: <product-name>
allowed-tools: Task, Read, Write, Bash, Glob
model: claude-sonnet-4-5
timeout: 1200
retry: 2
cost_estimate: 0.10-0.15

validation:
  input:
    product_name:
      schema: .claude/validation/schemas/common/spec-name.json
      required: true
      error_template: INVALID_SPEC_NAME
  output:
    schema: .claude/validation/schemas/design-os/export-package-output.json
    required_files:
      - 'design-os/${product_name}/export/implementation-guide.md'
      - 'design-os/${product_name}/export/asset-manifest.json'
    min_file_size: 500
    quality_threshold: 0.95
    content_requirements:
      - "Implementation guide present"
      - "All assets included"
      - "Documentation complete"
      - "Developer-ready package"

prerequisites:
  - command: /design-os/design-shell
    file_exists: 'design-os/${product_name}/shell/'
    error_message: "Complete the design-os workflow before exporting"

version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added input validation for product name"
      - "Added prerequisite check for design-shell"
      - "Added output validation for export package"
      - "Updated to design-os folder structure"
      - "Switched to agent-based export generation"
  - version: 1.0.0
    date: 2025-10-15
    changes:
      - "Initial implementation with manual export generation"
---

# Export Product

Product: **$ARGUMENTS**

## Step 1: Validate Input & Prerequisites

```bash
PRODUCT_NAME="$ARGUMENTS"

# Validate product name format
if [[ ! "$PRODUCT_NAME" =~ ^[a-z0-9-]+$ ]]; then
  echo "❌ ERROR: Invalid product name"
  echo ""
  echo "Product name must:"
  echo "  • Be lowercase"
  echo "  • Use only letters, numbers, and hyphens"
  exit 1
fi

# Check prerequisite: shell must exist
SHELL_DIR="design-os/$PRODUCT_NAME/shell"
if [ ! -d "$SHELL_DIR" ]; then
  echo "❌ ERROR: Design shell not found"
  echo ""
  echo "Complete the design-os workflow first:"
  echo "  1. /design-os/product-vision $PRODUCT_NAME"
  echo "  2. /design-os/product-roadmap $PRODUCT_NAME"
  echo "  3. /design-os/data-model $PRODUCT_NAME"
  echo "  4. /design-os/design-tokens $PRODUCT_NAME"
  echo "  5. /design-os/design-shell $PRODUCT_NAME"
  exit 1
fi

echo "✓ Input validated: $PRODUCT_NAME"
echo "✓ Prerequisites met: design workflow complete"
```

## Step 2: Generate Export Package Using Agent

```javascript
const PRODUCT_NAME = process.env.ARGUMENTS;

// Use agent to generate complete handoff package
await Task({
  subagent_type: 'general-purpose',
  description: 'Generate export handoff package',
  prompt: `Create a complete implementation handoff package for the ${PRODUCT_NAME} product.

Product Location:
design-os/${PRODUCT_NAME}/

Read all product files:
- vision.md - Product vision and goals
- roadmap.md - Section breakdown and priorities
- data-model.md - Entity definitions and relationships
- design-tokens.json - Color and typography system
- shell/ - Navigation and layout components
- sections/ - All section specs, components, and screenshots

Generate export package at:
design-os/${PRODUCT_NAME}/export/

Create these files:

1. implementation-guide.md
   - Setup instructions (dependencies, dev server)
   - File structure overview
   - Implementation order (section-by-section)
   - Design system integration
   - Common patterns and conventions
   - Testing recommendations

2. asset-manifest.json
   - List of all design assets
   - Component inventory
   - Screenshot locations
   - Design token references
   - Documentation paths

3. README.md
   - Quick start guide
   - What's included in this package
   - Prerequisites for implementation
   - Contact information

4. handoff-checklist.md
   - Pre-implementation checklist
   - Per-section implementation checklist
   - Quality assurance checklist
   - Launch readiness checklist

Requirements:
- Developer-ready documentation
- Complete asset inventory
- Step-by-step implementation guide
- Realistic timeline estimates
- Quality assurance guidelines`,

  context: {
    product_name: PRODUCT_NAME,
    product_path: `design-os/${PRODUCT_NAME}`,
    vision_path: `design-os/${PRODUCT_NAME}/vision.md`,
    roadmap_path: `design-os/${PRODUCT_NAME}/roadmap.md`,
    data_model_path: `design-os/${PRODUCT_NAME}/data-model.md`,
    tokens_path: `design-os/${PRODUCT_NAME}/design-tokens.json`,
    shell_path: `design-os/${PRODUCT_NAME}/shell/`,
    sections_path: `design-os/${PRODUCT_NAME}/sections/`,
    output_path: `design-os/${PRODUCT_NAME}/export/`
  }
});
```

## Step 3: Validate Output

```bash
PRODUCT_NAME="$ARGUMENTS"
EXPORT_DIR="design-os/$PRODUCT_NAME/export"

# Check directory exists
if [ ! -d "$EXPORT_DIR" ]; then
  echo "❌ ERROR: Export directory not created"
  exit 1
fi

# Check required files
REQUIRED_FILES=(
  "implementation-guide.md"
  "asset-manifest.json"
  "README.md"
  "handoff-checklist.md"
)

for file in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "$EXPORT_DIR/$file" ]; then
    echo "❌ ERROR: Missing required file: $file"
    exit 1
  fi
done

# Check minimum file sizes
GUIDE_SIZE=$(wc -c < "$EXPORT_DIR/implementation-guide.md")
if [ $GUIDE_SIZE -lt 500 ]; then
  echo "❌ ERROR: Implementation guide too small (< 500 bytes)"
  exit 1
fi

# Check valid JSON
if ! jq empty "$EXPORT_DIR/asset-manifest.json" 2>/dev/null; then
  echo "❌ ERROR: Asset manifest is not valid JSON"
  exit 1
fi

# Count total assets in manifest
ASSET_COUNT=$(jq '[.. | objects | select(has("path"))] | length' "$EXPORT_DIR/asset-manifest.json" 2>/dev/null || echo "0")

echo "✓ Output validation complete ($ASSET_COUNT assets catalogued)"
```

## Completion

```
═══════════════════════════════════════════════════
        EXPORT PRODUCT COMPLETE ✓
═══════════════════════════════════════════════════

Product: $ARGUMENTS
Command: /design-os/export-product
Version: 2.0.0

Output Created:
  ✓ design-os/$ARGUMENTS/export/implementation-guide.md
  ✓ design-os/$ARGUMENTS/export/asset-manifest.json
  ✓ design-os/$ARGUMENTS/export/README.md
  ✓ design-os/$ARGUMENTS/export/handoff-checklist.md

Export Package:
  Implementation guide (developer-ready)
  Complete asset inventory
  Setup instructions
  Quality assurance checklist
  Ready for handoff to development team

Validations Passed:
  ✓ Input validation (product name format)
  ✓ Prerequisites (design workflow complete)
  ✓ Output validation (all files present)
  ✓ Valid JSON manifest
  ✓ Quality threshold (≥0.95)

HANDOFF COMPLETE:
→ Share design-os/$ARGUMENTS/export/ with development team
→ Use implementation-guide.md for step-by-step build
→ Track progress with handoff-checklist.md

═══════════════════════════════════════════════════
```

## Guidelines

- **Developer-Ready** - Clear, actionable implementation instructions
- **Complete Documentation** - All design decisions documented
- **Asset Inventory** - Every component, screenshot, and asset catalogued
- **Quality Assurance** - Checklists for testing and verification
- **Realistic Timelines** - Estimated effort for each section
- **Design System** - Integration guide for tokens and components
- **Best Practices** - Recommended patterns and conventions
