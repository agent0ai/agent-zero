---
description: Define product vision, problems, solutions, and key features through guided conversation
argument-hint: <product-name>
allowed-tools: Read, Write, Edit, AskUserQuestion, Bash
model: claude-sonnet-4-5
timeout: 1200
retry: 2
cost_estimate: 0.12-0.18

# Validation
validation:
  input:
    product_name:
      schema: .claude/validation/schemas/common/spec-name.json
      required: true
      error_template: INVALID_SPEC_NAME

  output:
    schema: .claude/validation/schemas/design-os/product-vision-output.json
    required_files:
      - 'design-os/${product_name}/vision.md'
    min_file_size: 1500
    quality_threshold: 0.9
    content_requirements:
      - "Product Overview section"
      - "Problem Statement section"
      - "Solution section"
      - "Target Users section"
      - "Key Features section (≥5 features)"
      - "Success Metrics section"

# Prerequisites
prerequisites: []

# Version
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added input validation for product name"
      - "Added output quality thresholds"
      - "Added structured context and retry logic"
      - "Updated to design-os folder structure"
  - version: 1.0.0
    date: 2025-10-15
    changes:
      - "Initial implementation with AskUserQuestion workflow"
---

# Product Vision

Product name: **$ARGUMENTS**

## Step 1: Validate Input

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

# Create design-os directory structure
mkdir -p "design-os/$PRODUCT_NAME"

echo "✓ Input validated: $PRODUCT_NAME"
```

## Step 2: Interactive Vision Gathering

Start the conversation warmly:

> "Let's define the vision for **$ARGUMENTS**. I'll ask you a few questions to understand your product deeply. Don't worry about structure - just share your thoughts naturally."

### Question Set 1: Core Definition

Ask these questions using AskUserQuestion or natural conversation:

1. **Product Description** - "In one sentence, what is $ARGUMENTS?"
2. **Core Value** - "What's the main value it provides to users?"

### Question Set 2: Problems & Solutions

3. **Problems** - "What are the top 3-5 problems this product solves? (Be specific)"
4. **Solutions** - "How does your product solve each of these problems uniquely?"

### Question Set 3: Users & Features

5. **Target Users** - "Who are the primary users? What are their characteristics?"
6. **Key Features** - "What are the 5-7 most important features or capabilities?"

### Question Set 4: Success & Competition

7. **Success Metrics** - "How will you measure if this product is successful?"
8. **Competitive Landscape** - "What alternatives exist? How is this different/better?"

**Guidelines:**

- Ask questions in pairs or small groups (not all at once)
- Probe vague answers with follow-ups like "Tell me more about that..."
- Keep the tone conversational, not robotic
- Ensure each section has sufficient depth before proceeding

## Step 3: Draft & Refine

Present a structured summary:

```markdown
# Product Vision: [Product Name]

## Product Overview

[2-3 paragraph description that captures the essence, core value proposition, and unique positioning]

## Problem Statement

**Problem 1: [Problem Name]**
- Description: [Specific problem description]
- Impact: [Who it affects and how]

**Problem 2: [Problem Name]**
- Description: [Specific problem description]
- Impact: [Who it affects and how]

**Problem 3: [Problem Name]**
- Description: [Specific problem description]
- Impact: [Who it affects and how]

## Solution

[2-3 paragraphs explaining how the product solves the problems above, focusing on the unique approach and key differentiators]

## Target Users

**Primary Persona: [Persona Name]**
- Demographics: [Age, role, industry, etc.]
- Characteristics: [Behaviors, pain points, goals]
- Use case: [How they'll use the product]

**Secondary Persona: [Persona Name]** (if applicable)
- Demographics: [Details]
- Characteristics: [Details]
- Use case: [Details]

## Key Features

1. **[Feature 1]** - [Description and value]
2. **[Feature 2]** - [Description and value]
3. **[Feature 3]** - [Description and value]
4. **[Feature 4]** - [Description and value]
5. **[Feature 5]** - [Description and value]
6. **[Feature 6]** - [Description and value] (if applicable)
7. **[Feature 7]** - [Description and value] (if applicable)

## Success Metrics

1. **[Metric 1]** - [Target/goal]
2. **[Metric 2]** - [Target/goal]
3. **[Metric 3]** - [Target/goal]

## Competitive Landscape

**Existing Solutions:**
- [Alternative 1]: [Strengths and limitations]
- [Alternative 2]: [Strengths and limitations]

**Our Differentiation:**
- [Key differentiator 1]
- [Key differentiator 2]
- [Key differentiator 3]
```

Ask: "Does this capture your vision? Would you like to adjust anything?"

Iterate until the user is satisfied.

## Step 4: Create Vision Document

Once approved, create the file:

```javascript
const PRODUCT_NAME = process.env.ARGUMENTS;
const visionPath = `design-os/${PRODUCT_NAME}/vision.md`;

// Write the vision document
await Write({
  file_path: visionPath,
  content: `# Product Vision: [Product Name]

## Product Overview

[Content from conversation]

## Problem Statement

[Content from conversation]

## Solution

[Content from conversation]

## Target Users

[Content from conversation]

## Key Features

[Content from conversation]

## Success Metrics

[Content from conversation]

## Competitive Landscape

[Content from conversation]
`
});
```

## Step 5: Validate Output

```bash
VISION_FILE="design-os/$PRODUCT_NAME/vision.md"

# Check file exists
if [ ! -f "$VISION_FILE" ]; then
  echo "❌ ERROR: Vision file not created"
  exit 1
fi

# Check minimum file size (1500 bytes)
FILE_SIZE=$(wc -c < "$VISION_FILE")
if [ $FILE_SIZE -lt 1500 ]; then
  echo "❌ ERROR: Vision document too short (< 1500 bytes)"
  echo "Current size: $FILE_SIZE bytes"
  exit 1
fi

# Check required sections exist
REQUIRED_SECTIONS=("Product Overview" "Problem Statement" "Solution" "Target Users" "Key Features" "Success Metrics")
for section in "${REQUIRED_SECTIONS[@]}"; do
  if ! grep -q "$section" "$VISION_FILE"; then
    echo "❌ ERROR: Missing required section: $section"
    exit 1
  fi
done

echo "✓ Output validation complete"
```

## Completion

```
═══════════════════════════════════════════════════
        PRODUCT VISION COMPLETE ✓
═══════════════════════════════════════════════════

Product: $ARGUMENTS
Command: /design-os/product-vision
Version: 2.0.0

Output Created:
  ✓ design-os/$ARGUMENTS/vision.md

Validations Passed:
  ✓ Input validation (product name format)
  ✓ File created with required sections
  ✓ Minimum content threshold (≥1500 bytes)
  ✓ Quality threshold (≥0.9)

NEXT STEPS:
→ /design-os/product-roadmap $ARGUMENTS
   Create 3-5 buildable sections ordered by priority

→ /design-os/data-model $ARGUMENTS
   Define core data entities and relationships

═══════════════════════════════════════════════════
```

## Guidelines

- **Be warm and conversational** - not robotic or formal
- **Probe vague answers** - "Tell me more about that..."
- **Keep it focused** - Product vision, not implementation details
- **Ensure completeness** - Don't skip sections (≥5 features, ≥3 problems, ≥3 metrics)
- **Match the format exactly** - Required for proper parsing
- **Validate thoroughly** - All required sections must be present
