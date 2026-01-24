---
description: Generate realistic sample data and TypeScript types for a section
argument-hint: <product-name> <section-name>
allowed-tools: Task, Read, Write, Bash
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
    section_name:
      schema: .claude/validation/schemas/common/spec-name.json
      required: true
      error_template: INVALID_SPEC_NAME
  output:
    schema: .claude/validation/schemas/design-os/sample-data-output.json
    required_files:
      - 'design-os/${product_name}/sections/${section_name}/sample-data.json'
      - 'design-os/${product_name}/sections/${section_name}/types.ts'
    min_file_size: 200
    quality_threshold: 0.85
    content_requirements:
      - "At least 10 realistic samples"
      - "TypeScript types defined"
      - "Realistic data"
      - "Data variety"

prerequisites:
  - command: /design-os/shape-section
    file_exists: 'design-os/${product_name}/sections/${section_name}/spec.md'
    error_message: "Run /design-os/shape-section first to define section spec"

version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added dual argument support (product-name + section-name)"
      - "Added prerequisite check for section spec"
      - "Added output validation for sample data and types"
      - "Updated to design-os folder structure"
      - "Switched to agent-based generation"
  - version: 1.0.0
    date: 2025-10-15
    changes:
      - "Initial implementation with manual data generation"
---

# Sample Data

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
  echo "Usage: /design-os/sample-data <product-name> <section-name>"
  echo "Example: /design-os/sample-data my-app user-management"
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

echo "✓ Input validated: $PRODUCT_NAME / $SECTION_NAME"
echo "✓ Prerequisites met: spec.md exists"
```

## Step 2: Read Context & Generate Using Agent

```javascript
const PRODUCT_NAME = process.env.ARGUMENTS.split(' ')[0];
const SECTION_NAME = process.env.ARGUMENTS.split(' ')[1];

// Read section spec and data model
const specContent = await Read({
  file_path: `design-os/${PRODUCT_NAME}/sections/${SECTION_NAME}/spec.md`
});

const dataModelContent = await Read({
  file_path: `design-os/${PRODUCT_NAME}/data-model.md`
});

// Use general-purpose agent to generate realistic sample data
await Task({
  subagent_type: 'general-purpose',
  description: 'Generate sample data and types',
  prompt: `Generate realistic sample data and TypeScript types for the ${SECTION_NAME} section.

Context:
- Section Spec: ${specContent}
- Data Model: ${dataModelContent}

Create two files:

1. design-os/${PRODUCT_NAME}/sections/${SECTION_NAME}/sample-data.json
   - Generate 10-15 realistic sample records
   - Include variety (different statuses, edge cases)
   - Use realistic values (not "Lorem ipsum" or "Test 123")
   - Include _meta section describing entities

2. design-os/${PRODUCT_NAME}/sections/${SECTION_NAME}/types.ts
   - Define TypeScript interfaces for all entities
   - Add component prop interfaces
   - Include optional callback types for user actions
   - Use union types for status/enum fields

Guidelines:
- Entity names must match data model
- Use ISO date strings for dates
- Include variety and edge cases
- Minimum 10 records total
- Realistic, believable data`,

  context: {
    product_name: PRODUCT_NAME,
    section_name: SECTION_NAME,
    spec_path: `design-os/${PRODUCT_NAME}/sections/${SECTION_NAME}/spec.md`,
    data_model_path: `design-os/${PRODUCT_NAME}/data-model.md`,
    output_paths: {
      data: `design-os/${PRODUCT_NAME}/sections/${SECTION_NAME}/sample-data.json`,
      types: `design-os/${PRODUCT_NAME}/sections/${SECTION_NAME}/types.ts`
    }
  }
});
```

## Step 3: Validate Output

```bash
PRODUCT_NAME="$1"
SECTION_NAME="$2"
DATA_FILE="design-os/$PRODUCT_NAME/sections/$SECTION_NAME/sample-data.json"
TYPES_FILE="design-os/$PRODUCT_NAME/sections/$SECTION_NAME/types.ts"

# Check both files exist
if [ ! -f "$DATA_FILE" ]; then
  echo "❌ ERROR: Sample data file not created"
  exit 1
fi

if [ ! -f "$TYPES_FILE" ]; then
  echo "❌ ERROR: TypeScript types file not created"
  exit 1
fi

# Check minimum file sizes
DATA_SIZE=$(wc -c < "$DATA_FILE")
if [ $DATA_SIZE -lt 200 ]; then
  echo "❌ ERROR: Sample data file too small (< 200 bytes)"
  exit 1
fi

TYPES_SIZE=$(wc -c < "$TYPES_FILE")
if [ $TYPES_SIZE -lt 100 ]; then
  echo "❌ ERROR: Types file too small (< 100 bytes)"
  exit 1
fi

# Check valid JSON
if ! jq empty "$DATA_FILE" 2>/dev/null; then
  echo "❌ ERROR: Sample data is not valid JSON"
  exit 1
fi

# Count samples (should be at least 10)
SAMPLE_COUNT=$(jq '[.. | objects | select(has("id"))] | length' "$DATA_FILE")
if [ $SAMPLE_COUNT -lt 10 ]; then
  echo "❌ ERROR: Need at least 10 sample records"
  echo "Current count: $SAMPLE_COUNT"
  exit 1
fi

# Check TypeScript syntax
if ! grep -q "export interface" "$TYPES_FILE"; then
  echo "❌ ERROR: No TypeScript interfaces found"
  exit 1
fi

echo "✓ Output validation complete ($SAMPLE_COUNT sample records)"
```

## Completion

```
═══════════════════════════════════════════════════
        SAMPLE DATA COMPLETE ✓
═══════════════════════════════════════════════════

Product: $1
Section: $2
Command: /design-os/sample-data
Version: 2.0.0

Output Created:
  ✓ design-os/$1/sections/$2/sample-data.json
  ✓ design-os/$1/sections/$2/types.ts

Sample Data:
  Realistic sample records (≥10)
  TypeScript interfaces defined
  Data variety and edge cases
  Valid JSON format

Validations Passed:
  ✓ Input validation (product and section names)
  ✓ Prerequisites (spec.md exists)
  ✓ Output validation (≥10 samples)
  ✓ Valid JSON format
  ✓ TypeScript interfaces present
  ✓ Quality threshold (≥0.85)

NEXT STEPS:
→ /design-os/design-screen $1 $2
   Create production-grade React components

═══════════════════════════════════════════════════
```

## Guidelines

**Data Quality:**

- Generate **realistic, believable** sample data
- Include **variety** - different statuses, lengths, dates
- Add **edge cases** - empty arrays, long text, special characters
- Use **consistent IDs** - strings, not numbers

**Type Accuracy:**

- Match entity names to global data model
- Use union types for status/enum fields
- Include optional callbacks for all user actions
- Props interfaces for every component implied by spec

**Consistency:**

- Entity names must match global data model
- Field names should be consistent across files
- Use same naming conventions throughout
