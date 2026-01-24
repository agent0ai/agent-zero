---
description: Define core data entities and relationships for the product
argument-hint: <product-name>
allowed-tools: Read, Write, Edit, AskUserQuestion, Glob, Bash
model: claude-sonnet-4-5
timeout: 1500
retry: 2
cost_estimate: 0.14-0.20

# Validation
validation:
  input:
    product_name:
      schema: .claude/validation/schemas/common/spec-name.json
      required: true
      error_template: INVALID_SPEC_NAME

  output:
    schema: .claude/validation/schemas/design-os/data-model-output.json
    required_files:
      - 'design-os/${product_name}/data-model.md'
    min_file_size: 1200
    quality_threshold: 0.9
    content_requirements:
      - "Entity Definitions section"
      - "Relationships section"
      - "ERD Diagram (Mermaid)"
      - "Data Flow section"
      - "At least 3 entities defined"
      - "At least 2 relationships defined"

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
      - "Added ERD diagram requirement (Mermaid)"
      - "Added output quality thresholds"
      - "Updated to design-os folder structure"
  - version: 1.0.0
    date: 2025-10-15
    changes:
      - "Initial implementation with AskUserQuestion workflow"
---

# Data Model

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

Read the product vision and roadmap (if available) to understand the domain:

```javascript
const PRODUCT_NAME = process.env.ARGUMENTS;

// Read vision for context
const visionContent = await Read({
  file_path: `design-os/${PRODUCT_NAME}/vision.md`
});

// Read roadmap if it exists
const roadmapExists = await fileExists(`design-os/${PRODUCT_NAME}/roadmap.md`);
if (roadmapExists) {
  const roadmapContent = await Read({
    file_path: `design-os/${PRODUCT_NAME}/roadmap.md`
  });
}
```

## Step 3: Initial Entity Analysis

Based on the vision, present candidate entities:

> "Based on your product vision for **$ARGUMENTS**, here are the core entities I'm identifying:
>
> **Primary Entities:**
>
> - **User** - People who use the system
> - **[Entity 2]** - [What it represents based on key features]
> - **[Entity 3]** - [What it represents]
> - **[Entity 4]** - [What it represents]
>
> **Supporting Entities:**
>
> - **[Entity 5]** - [What it represents]
>
> Does this capture your domain? What would you add, remove, or clarify?"

## Step 4: Clarifying Questions

Ask targeted questions to deepen understanding:

1. **Core Data**: "What are the main things users will create or manage in your system?"
2. **Key Attributes**: "For each entity, what information is most critical to capture?"
3. **Relationships**: "How do these entities relate to each other? Which ones 'own' or 'contain' others?"
4. **Data Flow**: "How does data move through your system? What triggers create or update these entities?"

Keep questions conversational - ask in pairs, not all at once.

## Step 5: Draft Entity Definitions

Present detailed entity structure:

```markdown
## Entities

### User
**Description**: People who use the system. Manages authentication, preferences, and user-specific data.

**Key Characteristics**:
- Authentication credentials
- Profile information
- Preferences/settings
- Relationship to other entities

### [Entity Name]
**Description**: [Plain-language description of what this represents and its purpose]

**Key Characteristics**:
- [Important attribute 1]
- [Important attribute 2]
- [Relationship to other entities]

### [Entity Name]
**Description**: [Plain-language description]

**Key Characteristics**:
- [Important attributes]
- [Relationships]
```

## Step 6: Draft Relationships

```markdown
## Relationships

**User ↔ [Entity]:**
- A User can have many [Entities]
- Each [Entity] belongs to one User
- Cascade delete: When User deleted, their [Entities] are also deleted

**[Entity] ↔ [Entity]:**
- A [Entity] can reference many [Entities]
- Each [Entity] can belong to one [Entity]
- Optional relationship

**[Entity] ↔ [Entity]:**
- Many-to-many relationship
- [Entities] can have multiple [Entities]
- Join table: [EntityEntity]
```

Ask: "Does this accurately represent your data model? Would you like to adjust any entities or relationships?"

Iterate until approved.

## Step 7: Create Data Model Document

```javascript
const PRODUCT_NAME = process.env.ARGUMENTS;
const dataModelPath = `design-os/${PRODUCT_NAME}/data-model.md`;

await Write({
  file_path: dataModelPath,
  content: `# Data Model

## Entity Definitions

### [Entity Name]
**Description**: [Brief description of what this entity represents and its purpose]

**Key Characteristics**:
- [Attribute 1]
- [Attribute 2]
- [Relationship notes]

### [Entity Name]
**Description**: [Brief description]

**Key Characteristics**:
- [Attributes]
- [Relationships]

### [Entity Name]
**Description**: [Brief description]

**Key Characteristics**:
- [Attributes]
- [Relationships]

## Relationships

**[Entity] ↔ [Entity]:**
- A [Entity] has many [Entities]
- Each [Entity] belongs to one [Entity]
- [Cascade behavior, constraints]

**[Entity] ↔ [Entity]:**
- A [Entity] can reference many [Entities]
- [Relationship notes]

**[Entity] ↔ [Entity]:**
- Many-to-many relationship via [JoinEntity]
- [Details]

## ERD Diagram

\`\`\`mermaid
erDiagram
    User ||--o{ Entity2 : "has many"
    User ||--o{ Entity3 : "manages"
    Entity2 }o--|| Entity3 : "belongs to"
    Entity2 ||--o{ Entity4 : "contains"
    Entity3 }o--o{ Entity5 : "references"
\`\`\`

## Data Flow

**Entity Creation:**
1. User action triggers entity creation
2. System validates data
3. Entity created with relationships
4. Related entities notified/updated

**Entity Updates:**
1. User modifies entity
2. Validation rules applied
3. Relationships maintained
4. Audit trail recorded

**Entity Deletion:**
1. User initiates delete
2. System checks dependencies
3. Cascade rules applied
4. Related entities updated

## Validation Rules

**[Entity Name]:**
- [Validation rule 1]
- [Validation rule 2]
- [Business constraints]

**[Entity Name]:**
- [Validation rules]
- [Constraints]

## Notes

- [Important constraints or business rules]
- [Edge cases to consider]
- [Data migration considerations]
- [Performance considerations]
`
});
```

## Step 8: Validate Output

```bash
DATA_MODEL_FILE="design-os/$PRODUCT_NAME/data-model.md"

# Check file exists
if [ ! -f "$DATA_MODEL_FILE" ]; then
  echo "❌ ERROR: Data model file not created"
  exit 1
fi

# Check minimum file size (1200 bytes)
FILE_SIZE=$(wc -c < "$DATA_MODEL_FILE")
if [ $FILE_SIZE -lt 1200 ]; then
  echo "❌ ERROR: Data model document too short (< 1200 bytes)"
  echo "Current size: $FILE_SIZE bytes"
  exit 1
fi

# Check required sections exist
REQUIRED_SECTIONS=("Entity Definitions" "Relationships" "ERD Diagram" "Data Flow")
for section in "${REQUIRED_SECTIONS[@]}"; do
  if ! grep -q "$section" "$DATA_MODEL_FILE"; then
    echo "❌ ERROR: Missing required section: $section"
    exit 1
  fi
done

# Check minimum entities (should be at least 3)
ENTITY_COUNT=$(grep -c "^### " "$DATA_MODEL_FILE" | head -1)
if [ $ENTITY_COUNT -lt 3 ]; then
  echo "❌ ERROR: Need at least 3 entities defined, found: $ENTITY_COUNT"
  exit 1
fi

# Check ERD diagram present
if ! grep -q "erDiagram" "$DATA_MODEL_FILE"; then
  echo "❌ ERROR: ERD diagram (Mermaid) missing"
  exit 1
fi

echo "✓ Output validation complete ($ENTITY_COUNT entities defined)"
```

## Completion

```
═══════════════════════════════════════════════════
        DATA MODEL COMPLETE ✓
═══════════════════════════════════════════════════

Product: $ARGUMENTS
Command: /design-os/data-model
Version: 2.0.0

Output Created:
  ✓ design-os/$ARGUMENTS/data-model.md

Entities Defined: [N entities]
  - [Entity 1]
  - [Entity 2]
  - [Entity 3]
  ...

Relationships: [N relationships]
ERD Diagram: ✓ Included (Mermaid format)

Validations Passed:
  ✓ Input validation (product name format)
  ✓ Prerequisites (vision.md exists)
  ✓ Minimum 3 entities defined
  ✓ Relationships documented
  ✓ ERD diagram included
  ✓ Data flow documented
  ✓ Quality threshold (≥0.9)

NEXT STEPS:
→ /design-os/design-tokens $ARGUMENTS
   Set colors (Tailwind) and typography (Google Fonts)

→ /design-os/shape-section $ARGUMENTS <section-name>
   Define detailed spec for a specific section

═══════════════════════════════════════════════════
```

## Guidelines

**Keep It Minimal:**

- Focus on **what** each entity represents, not every field
- Use **singular names** (User, not Users)
- Describe in **plain language** anyone can understand
- 3-6 core entities is typical for most products

**Stay Conceptual:**

- Don't define database schemas or field types yet
- Don't specify validation rules in detail
- Leave implementation details for agent-os/spec phase
- This is shared vocabulary and domain model

**Relationships:**

- Use simple language: "has many", "belongs to", "references"
- Don't use database notation (foreign keys, indexes)
- Focus on logical connections
- Include cascade behavior (delete, update)

**ERD Diagram:**

- Use Mermaid erDiagram syntax
- Show cardinality (||--o{, }o--||, etc.)
- Keep it readable - don't show every detail
- Use descriptive relationship labels

**Consistency:**

- Entity names should match across all design-os documents
- If you define "Invoice" here, use "Invoice" everywhere
- Maintain naming consistency with vision and roadmap
