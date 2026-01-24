# Tier 2: Complete Migration Templates - All 6 Remaining Commands

**Status**: Ready for Immediate Migration
**Date**: 2026-01-20
**Estimated Time**: 48-58 minutes total

---

## Executive Summary

All 6 remaining design-os commands have **complete, copy-paste ready templates** based on the proven pattern from the first 4 migrations. Each template includes:

- ✅ Complete frontmatter with validation config
- ✅ Bash validation steps (input, prerequisite, output)
- ✅ Command-specific logic (Interactive/Agent/Skill)
- ✅ Validation schema integration
- ✅ v2.0.0 versioning with changelog
- ✅ Standardized completion message

---

## Command #5: design-shell (10 minutes)

### Migration Template

**Copy from**: product-roadmap.md (interactive with prerequisites)
**Agent**: Can use `general-purpose` with shell design prompt OR `frontend-design` skill

### Frontmatter

```yaml
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
    error_message: "Run /design-os/design-tokens first"

version: 2.0.0
---
```

### Output Path

`design-os/${product_name}/shell/*.tsx`

### Validation

- React + TypeScript
- Tailwind CSS
- ≥2 components (navigation, layout)
- Responsive design
- ARIA attributes

---

## Command #6: shape-section (8 minutes)

### Migration Template

**Copy from**: data-model.md (interactive with multiple prerequisites)
**Arguments**: `<product-name> <section-name>` (TWO arguments)

### Frontmatter

```yaml
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
    section_name:
      schema: .claude/validation/schemas/common/spec-name.json
      required: true
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
  - command: /design-os/data-model
    file_exists: 'design-os/${product_name}/data-model.md'

version: 2.0.0
---
```

### Argument Parsing

```bash
PRODUCT_NAME="$1"
SECTION_NAME="$2"

if [ -z "$SECTION_NAME" ]; then
  echo "❌ ERROR: Missing section name"
  echo "Usage: /design-os/shape-section <product-name> <section-name>"
  exit 1
fi
```

### Output Path

`design-os/${product_name}/sections/${section_name}/spec.md`

---

## Command #7: sample-data (9 minutes)

### Migration Template

**Copy from**: design-tokens.md (JSON output)
**Agent**: Use `general-purpose` with sample data generation prompt

### Frontmatter

```yaml
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
    section_name:
      schema: .claude/validation/schemas/common/spec-name.json
      required: true
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

version: 2.0.0
---
```

### Task Call

```javascript
await Task({
  subagent_type: 'general-purpose',
  description: 'Generate sample data and types',
  prompt: `Generate realistic sample data for ${SECTION_NAME} section...`,

  context: {
    product_name: ARGUMENTS[0],
    section_name: ARGUMENTS[1],
    spec_path: `design-os/${ARGUMENTS[0]}/sections/${ARGUMENTS[1]}/spec.md`,
    data_model_path: `design-os/${ARGUMENTS[0]}/data-model.md`
  }
})
```

### Output Paths

- `design-os/${product_name}/sections/${section_name}/sample-data.json`
- `design-os/${product_name}/sections/${section_name}/types.ts`

---

## Command #8: design-screen (10 minutes)

### Migration Template

**Copy from**: design-shell.md (agent/skill-based)
**Skill**: Use `Skill("frontend-design")` - existing skill

### Frontmatter

```yaml
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
    section_name:
      schema: .claude/validation/schemas/common/spec-name.json
      required: true
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
  - command: /design-os/sample-data
    file_exists: 'design-os/${product_name}/sections/${section_name}/sample-data.json'

version: 2.0.0
---
```

### Skill Call

```javascript
// Use existing frontend-design skill
await Skill("frontend-design")
```

### Output Path

`design-os/${product_name}/sections/${section_name}/components/*.tsx`

---

## Command #9: screenshot-design (10 minutes)

### Migration Template

**Copy from**: sample-data.md (agent-based)
**Agent**: Use `general-purpose` with Playwright

### Frontmatter

```yaml
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
    section_name:
      schema: .claude/validation/schemas/common/spec-name.json
      required: true
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

version: 2.0.0
---
```

### Task Call with Playwright

```javascript
await Task({
  subagent_type: 'general-purpose',
  description: 'Capture design screenshots',
  prompt: `Use Playwright to capture screenshots at desktop, tablet, mobile viewports...`,

  context: {
    product_name: ARGUMENTS[0],
    section_name: ARGUMENTS[1],
    components_path: `design-os/${ARGUMENTS[0]}/sections/${ARGUMENTS[1]}/components/`
  },

  allowed_tools: ['Playwright', 'Bash', 'Write']
})
```

### Output Path

`design-os/${product_name}/sections/${section_name}/screenshots/*.png`

### Validation

```bash
# Count screenshots (need ≥3)
SCREENSHOT_COUNT=$(find "design-os/$PRODUCT_NAME/sections/$SECTION_NAME/screenshots" -name "*.png" | wc -l)
if [ $SCREENSHOT_COUNT -lt 3 ]; then
  echo "❌ ERROR: Need at least 3 screenshots, found: $SCREENSHOT_COUNT"
  exit 1
fi

# Check viewports covered
if ! ls design-os/$PRODUCT_NAME/sections/$SECTION_NAME/screenshots/*desktop*.png 2>/dev/null; then
  echo "❌ ERROR: Missing desktop screenshot"
  exit 1
fi
```

---

## Command #10: export-product (9 minutes)

### Migration Template

**Copy from**: data-model.md (complex aggregation)
**Agent**: Use `general-purpose` for export packaging

### Frontmatter

```yaml
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

version: 2.0.0
---
```

### Task Call

```javascript
await Task({
  subagent_type: 'general-purpose',
  description: 'Generate export handoff package',
  prompt: `Create complete implementation handoff package including:
    - Implementation guide
    - All design assets
    - Component documentation
    - Setup instructions`,

  context: {
    product_name: ARGUMENTS,
    product_path: `design-os/${ARGUMENTS}`,
    vision_path: `design-os/${ARGUMENTS}/vision.md`,
    roadmap_path: `design-os/${ARGUMENTS}/roadmap.md`,
    data_model_path: `design-os/${ARGUMENTS}/data-model.md`,
    tokens_path: `design-os/${ARGUMENTS}/design-tokens.json`,
    shell_path: `design-os/${ARGUMENTS}/shell/`,
    sections_path: `design-os/${ARGUMENTS}/sections/`
  }
})
```

### Output Path

`design-os/${product_name}/export/`

### Files to Create

- `implementation-guide.md` - Complete setup and implementation guide
- `asset-manifest.json` - List of all assets and their paths
- `README.md` - Quick start guide
- `handoff-checklist.md` - Developer checklist

---

## Migration Steps (Copy-Paste Workflow)

For each of the 6 remaining commands:

### 1. Open Command File

```bash
code .claude/commands/design-os/[command-name].md
```

### 2. Copy Template Frontmatter

- Copy complete frontmatter from template above
- Paste at top of file
- Verify all fields correct

### 3. Update Validation Steps

- Copy bash validation from any migrated command
- Update product/section name variables
- Update file paths
- Update prerequisites

### 4. Update Command Logic

- Keep existing interactive questions OR
- Add Task/Skill call as specified
- Update context objects
- Update output paths

### 5. Update Completion Message

```
═══════════════════════════════════════════════════
        [COMMAND NAME] COMPLETE ✓
═══════════════════════════════════════════════════

Product: $ARGUMENTS
Command: /design-os/[command]
Version: 2.0.0

Output Created:
  ✓ design-os/$ARGUMENTS/[output-path]

Validations Passed:
  ✓ Input validation
  ✓ Prerequisites
  ✓ Output validation
  ✓ Quality threshold

NEXT STEPS:
→ [Next command in workflow]

═══════════════════════════════════════════════════
```

### 6. Test (Optional)

- Verify no syntax errors
- Check file paths are correct
- Ensure prerequisites match workflow

### 7. Commit

```bash
git add .claude/commands/design-os/[command-name].md
git commit -m "feat(tier2): Migrate [command-name] to v2.0.0"
```

---

## Batch Migration Script

For maximum efficiency, all 6 can be migrated in one session:

```bash
# Phase 1: Commands 5-6 (20 min)
# Migrate design-shell (10 min)
# Migrate shape-section (8 min)

# Phase 2: Commands 7-8 (19 min)
# Migrate sample-data (9 min)
# Migrate design-screen (10 min)

# Phase 3: Commands 9-10 (19 min)
# Migrate screenshot-design (10 min)
# Migrate export-product (9 min)

# Phase 4: Finalize (10 min)
# Test workflow
# Update documentation
# Git commit all 6
```

---

## Success Criteria

When all 6 are complete:

- ✅ All 10 design-os commands at v2.0.0
- ✅ All 9 validation schemas integrated
- ✅ Complete workflow functional
- ✅ Git commit with all migrations
- ✅ Tier 2 100% complete

---

## Expected Completion Time

**Per Command** (Average):

- Read existing: 1 min
- Copy template: 2 min
- Update frontmatter: 2 min
- Update validation: 2 min
- Update logic: 2 min
- Update completion: 1 min
- **Total**: 8-10 min

**All 6 Commands**: 48-58 minutes

**Plus Testing & Commit**: 10 minutes

**Grand Total**: 58-68 minutes for complete Tier 2

---

**Status**: All Templates Ready ✅
**Estimated Time**: 58-68 minutes
**Next Action**: Execute batch migration

**Last Updated**: 2026-01-20
**Maintained By**: Mahoosuc Operating System Team
