---
description: Create app navigation shell and layout components with React and Tailwind
argument-hint: <product-name>
allowed-tools: Task, Read, Write, Edit, Bash, Skill
model: claude-sonnet-4-5
timeout: 1800
retry: 2
cost_estimate: 0.18-0.25

validation:
  input:
    product_name:
      schema: .claude/validation/schemas/common/spec-name.json
      required: true
      error_template: INVALID_SPEC_NAME
  output:
    schema: .claude/validation/schemas/design-os/design-shell-output.json
    required_files:
      - 'design-os/${product_name}/shell/'
    min_file_size: 200
    quality_threshold: 0.9
    content_requirements:
      - "React + TypeScript components"
      - "Tailwind CSS styling"
      - "Responsive design"
      - "ARIA attributes"
      - "Navigation component"
      - "At least 2 components"

prerequisites:
  - command: /design-os/design-tokens
    file_exists: 'design-os/${product_name}/design-tokens.json'
    error_message: "Run /design-os/design-tokens first to define design system"

version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added input validation for product name"
      - "Added prerequisite check for design-tokens.json"
      - "Added output validation for React components"
      - "Updated to design-os folder structure"
      - "Switched to agent-based generation with frontend-design skill"
  - version: 1.0.0
    date: 2025-10-15
    changes:
      - "Initial implementation with interactive layout selection"
---

# Design Shell

Product name: **$ARGUMENTS**

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
  echo "  • Example: 'my-product' or 'app-v2'"
  exit 1
fi

# Check prerequisite: design-tokens.json must exist
TOKENS_FILE="design-os/$PRODUCT_NAME/design-tokens.json"
if [ ! -f "$TOKENS_FILE" ]; then
  echo "❌ ERROR: Design tokens not found"
  echo ""
  echo "Run this command first:"
  echo "  /design-os/design-tokens $PRODUCT_NAME"
  exit 1
fi

echo "✓ Input validated: $PRODUCT_NAME"
echo "✓ Prerequisites met: design-tokens.json exists"
```

## Step 2: Read Context Files

```javascript
const PRODUCT_NAME = process.env.ARGUMENTS;

// Read product context
const visionContent = await Read({
  file_path: `design-os/${PRODUCT_NAME}/vision.md`
});

const roadmapContent = await Read({
  file_path: `design-os/${PRODUCT_NAME}/roadmap.md`
});

const tokensContent = await Read({
  file_path: `design-os/${PRODUCT_NAME}/design-tokens.json`
});

// Parse roadmap to extract section names for navigation
```

## Step 3: Generate Shell Components Using Frontend-Design Skill

```javascript
const PRODUCT_NAME = process.env.ARGUMENTS;

// Use the frontend-design skill to create production-grade shell components
await Skill("frontend-design");

// Context provided to skill:
// - Product vision for understanding purpose and audience
// - Roadmap sections for navigation structure
// - Design tokens for consistent styling
// - Output path: design-os/${PRODUCT_NAME}/shell/

// The skill will create:
// - AppShell.tsx - Main layout wrapper
// - Navigation.tsx - Navigation component (sidebar or topnav)
// - UserMenu.tsx - User avatar and dropdown
// - Layout responsive patterns (desktop, tablet, mobile)
// - ARIA attributes for accessibility
```

## Step 4: Validate Output

```bash
SHELL_DIR="design-os/$PRODUCT_NAME/shell"

# Check directory exists
if [ ! -d "$SHELL_DIR" ]; then
  echo "❌ ERROR: Shell directory not created"
  exit 1
fi

# Check minimum components (should be at least 2)
COMPONENT_COUNT=$(find "$SHELL_DIR" -name "*.tsx" | wc -l)
if [ $COMPONENT_COUNT -lt 2 ]; then
  echo "❌ ERROR: Need at least 2 React components"
  echo "Current count: $COMPONENT_COUNT"
  exit 1
fi

# Check minimum file size (200 bytes per component)
for file in "$SHELL_DIR"/*.tsx; do
  FILE_SIZE=$(wc -c < "$file")
  if [ $FILE_SIZE -lt 200 ]; then
    echo "❌ ERROR: Component file too small: $(basename $file)"
    exit 1
  fi
done

# Check for React + TypeScript syntax
if ! grep -rq "import.*React" "$SHELL_DIR"; then
  echo "❌ ERROR: React imports missing"
  exit 1
fi

# Check for Tailwind classes
if ! grep -rq "className=" "$SHELL_DIR"; then
  echo "❌ ERROR: Tailwind CSS classes missing"
  exit 1
fi

echo "✓ Output validation complete ($COMPONENT_COUNT components created)"
```

## Completion

```
═══════════════════════════════════════════════════
        DESIGN SHELL COMPLETE ✓
═══════════════════════════════════════════════════

Product: $ARGUMENTS
Command: /design-os/design-shell
Version: 2.0.0

Output Created:
  ✓ design-os/$ARGUMENTS/shell/*.tsx

Components:
  Navigation shell components (≥2)
  React + TypeScript
  Tailwind CSS styling
  Responsive design (desktop, tablet, mobile)
  ARIA accessibility attributes

Validations Passed:
  ✓ Input validation (product name format)
  ✓ Prerequisites (design-tokens.json exists)
  ✓ Output validation (≥2 components)
  ✓ React + TypeScript syntax
  ✓ Tailwind CSS classes
  ✓ Quality threshold (≥0.9)

NEXT STEPS:
→ /design-os/shape-section $ARGUMENTS <section-name>
   Define detailed spec for a specific section

═══════════════════════════════════════════════════
```

## Guidelines

- **Navigation chrome only** - Don't design auth UI here
- **Props-based components** - Portable to any project
- **Tailwind CSS** - For consistent, responsive styling
- **lucide-react icons** - For navigation and UI elements
- **Mobile-first responsive** - sm:, md:, lg: prefixes
- **Light/dark mode** - dark: variants required
- **Design tokens** - Apply colors and typography from design-tokens.json
