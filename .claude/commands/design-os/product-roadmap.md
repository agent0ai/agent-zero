---
description: Create or update product roadmap with 3-5 buildable sections ordered by priority
argument-hint: <product-name>
allowed-tools: Read, Write, Edit, AskUserQuestion, Glob, Bash
model: claude-sonnet-4-5
timeout: 1200
retry: 2
cost_estimate: 0.10-0.15

# Validation
validation:
  input:
    product_name:
      schema: .claude/validation/schemas/common/spec-name.json
      required: true
      error_template: INVALID_SPEC_NAME

  output:
    schema: .claude/validation/schemas/design-os/product-roadmap-output.json
    required_files:
      - 'design-os/${product_name}/roadmap.md'
    min_file_size: 1000
    quality_threshold: 0.9
    content_requirements:
      - "Roadmap Overview section"
      - "Buildable Sections (3-8 sections)"
      - "Priority Order defined"
      - "Dependencies mapped"

# Prerequisites
prerequisites:
  - command: /design-os/product-vision
    file_exists: 'design-os/${product_name}/vision.md'
    error_message: "Run /design-os/product-vision first to define product vision"

# Version
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added input validation for product name"
      - "Added prerequisite check for vision.md"
      - "Added output quality thresholds"
      - "Updated to design-os folder structure"
  - version: 1.0.0
    date: 2025-10-15
    changes:
      - "Initial implementation with AskUserQuestion workflow"
---

# Product Roadmap

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

# Check prerequisite: vision.md must exist
VISION_FILE="design-os/$PRODUCT_NAME/vision.md"
if [ ! -f "$VISION_FILE" ]; then
  echo "❌ ERROR: Product vision not found"
  echo ""
  echo "Run this command first:"
  echo "  /design-os/product-vision $PRODUCT_NAME"
  exit 1
fi

echo "✓ Input validated: $PRODUCT_NAME"
echo "✓ Prerequisites met: vision.md exists"
```

## Step 2: Read Product Vision

Read the product vision to understand:

- Core functionality and value proposition
- Problems being solved
- Key features listed
- Target users and use cases

```javascript
const PRODUCT_NAME = process.env.ARGUMENTS;
const visionContent = await Read({
  file_path: `design-os/${PRODUCT_NAME}/vision.md`
});

// Analyze the vision to extract key themes for sections
```

## Step 3: Propose Buildable Sections

Based on the vision, propose 3-5 (up to 8) logical, **independently buildable** sections:

> "Based on your product vision for **$ARGUMENTS**, here are the sections I'm proposing for the roadmap. Each section is a buildable chunk that will become a navigation item in your app."

```markdown
### Proposed Sections

**1. [Foundation Section Name]**
One sentence description of what this section covers and why it's first.

**2. [Core Feature Section Name]**
One sentence description focusing on the main user value.

**3. [Supporting Feature Section Name]**
One sentence description of secondary but important functionality.

**4. [Advanced Feature Section Name]** (if applicable)
One sentence description of advanced capabilities.

**5. [Analytics/Admin Section Name]** (if applicable)
One sentence description of admin/reporting features.
```

**Section Guidelines:**

- Each section should be **independently buildable** (can work standalone)
- Sections become **navigation items** in the final app
- Order by **development priority** (foundations first, advanced features later)
- Keep to **3-8 sections** (3-5 is ideal for most products)
- Descriptions are **one sentence only** - brief and clear
- Consider **dependencies** - build prerequisite sections first

**Ask:** "Does this breakdown make sense? Would you like to adjust any sections, add new ones, or change the order?"

## Step 4: Iterate & Refine

Refine based on user feedback:

- Add/remove sections as requested
- Adjust ordering based on priorities or dependencies
- Clarify descriptions
- Ensure each section is self-contained and buildable independently
- Verify dependencies are properly ordered

## Step 5: Create Roadmap Document

Once approved, create the roadmap file:

```javascript
const PRODUCT_NAME = process.env.ARGUMENTS;
const roadmapPath = `design-os/${PRODUCT_NAME}/roadmap.md`;

// Write the roadmap document
await Write({
  file_path: roadmapPath,
  content: `# Product Roadmap

## Roadmap Overview

This roadmap breaks down [Product Name] into [N] independently buildable sections, ordered by development priority and dependencies.

## Buildable Sections

### 1. [Section Title]
[One sentence description]

**Dependencies:** None (foundation)
**Priority:** High
**Estimated Complexity:** Medium

### 2. [Section Title]
[One sentence description]

**Dependencies:** Section 1
**Priority:** High
**Estimated Complexity:** Medium

### 3. [Section Title]
[One sentence description]

**Dependencies:** Section 1, Section 2
**Priority:** Medium
**Estimated Complexity:** Low

### 4. [Section Title]
[One sentence description]

**Dependencies:** Section 1
**Priority:** Medium
**Estimated Complexity:** High

### 5. [Section Title]
[One sentence description]

**Dependencies:** All previous sections
**Priority:** Low
**Estimated Complexity:** Medium

## Priority Order

**Phase 1 (Foundation):**
- Section 1: [Name]

**Phase 2 (Core Features):**
- Section 2: [Name]
- Section 3: [Name]

**Phase 3 (Advanced Features):**
- Section 4: [Name]
- Section 5: [Name]

## Dependencies

\`\`\`mermaid
graph TD
    S1[Section 1: Foundation] --> S2[Section 2: Feature A]
    S1 --> S3[Section 3: Feature B]
    S2 --> S4[Section 4: Advanced A]
    S3 --> S4
    S4 --> S5[Section 5: Analytics]
\`\`\`

## Timeline Estimates

Based on section complexity and dependencies:

- **Week 1-2:** Section 1 (Foundation)
- **Week 3-4:** Section 2 (Feature A)
- **Week 5:** Section 3 (Feature B)
- **Week 6-7:** Section 4 (Advanced A)
- **Week 8:** Section 5 (Analytics)

*Note: These are rough estimates and will be refined during spec and task creation.*
`
});
```

**Important:** Use the exact numbered format (`### 1. Title`) - required for proper parsing and workflow automation.

## Step 6: Validate Output

```bash
ROADMAP_FILE="design-os/$PRODUCT_NAME/roadmap.md"

# Check file exists
if [ ! -f "$ROADMAP_FILE" ]; then
  echo "❌ ERROR: Roadmap file not created"
  exit 1
fi

# Check minimum file size (1000 bytes)
FILE_SIZE=$(wc -c < "$ROADMAP_FILE")
if [ $FILE_SIZE -lt 1000 ]; then
  echo "❌ ERROR: Roadmap document too short (< 1000 bytes)"
  echo "Current size: $FILE_SIZE bytes"
  exit 1
fi

# Check required sections exist
REQUIRED_SECTIONS=("Roadmap Overview" "Buildable Sections" "Priority Order" "Dependencies")
for section in "${REQUIRED_SECTIONS[@]}"; do
  if ! grep -q "$section" "$ROADMAP_FILE"; then
    echo "❌ ERROR: Missing required section: $section"
    exit 1
  fi
done

# Count buildable sections (should be 3-8)
SECTION_COUNT=$(grep -c "^### [0-9]" "$ROADMAP_FILE")
if [ $SECTION_COUNT -lt 3 ] || [ $SECTION_COUNT -gt 8 ]; then
  echo "❌ ERROR: Invalid section count: $SECTION_COUNT (must be 3-8)"
  exit 1
fi

echo "✓ Output validation complete ($SECTION_COUNT sections defined)"
```

## Completion

```
═══════════════════════════════════════════════════
        PRODUCT ROADMAP COMPLETE ✓
═══════════════════════════════════════════════════

Product: $ARGUMENTS
Command: /design-os/product-roadmap
Version: 2.0.0

Output Created:
  ✓ design-os/$ARGUMENTS/roadmap.md

Sections Defined: [N sections]
  1. [Section 1]
  2. [Section 2]
  3. [Section 3]
  ...

Validations Passed:
  ✓ Input validation (product name format)
  ✓ Prerequisites (vision.md exists)
  ✓ File created with required sections
  ✓ Section count valid (3-8 sections)
  ✓ Dependencies mapped
  ✓ Quality threshold (≥0.9)

NEXT STEPS:
→ /design-os/data-model $ARGUMENTS
   Define core data entities and relationships

→ /design-os/design-tokens $ARGUMENTS
   Set colors (Tailwind) and typography (Google Fonts)

═══════════════════════════════════════════════════
```

## Guidelines

- **Keep sections minimal** - 3-5 is ideal, maximum 8
- **Order by priority** - Foundation first, advanced features later
- **Map dependencies** - Show how sections relate to each other
- **Self-contained sections** - Each should be buildable independently
- **One sentence descriptions** - Brief and clear
- **Use numbered format** - Required for parsing (`### 1. Title`)
- **Include complexity estimates** - Helps with planning
- **Add timeline estimates** - Rough guidance for development
