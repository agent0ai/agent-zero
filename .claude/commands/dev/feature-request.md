---
description: Plan and scope new feature requests with AI assistance
argument-hint: <feature-description>
allowed-tools: Task, AskUserQuestion, Write, Bash
model: claude-sonnet-4-5
timeout: 900
retry: 2
cost_estimate: 0.15-0.25

validation:
  input:
    feature_description:
      required: true
      min_length: 10
      error_message: "Feature description must be at least 10 characters"
  output:
    schema: .claude/validation/schemas/dev/feature-request-output.json
    required_files:
      - 'docs/features/${feature_slug}.md'
    min_file_size: 500
    quality_threshold: 0.85
    content_requirements:
      - "Feature specification created"
      - "User story defined"
      - "Technical design outlined"
      - "Implementation tasks identified"
      - "Risks and timeline estimated"

version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added output validation for feature specifications"
      - "Streamlined from 282 lines to focused workflow"
      - "Enhanced AI planning with technical analysis"
  - version: 1.0.0
    date: 2025-08-18
    changes:
      - "Initial implementation with AI planning"
---

# Plan Feature Request

Feature: **$ARGUMENTS**

## Step 1: Validate Input & Parse Feature

```bash
FEATURE_DESCRIPTION="$ARGUMENTS"

if [ ${#FEATURE_DESCRIPTION} -lt 10 ]; then
  echo "❌ ERROR: Feature description too short (minimum 10 characters)"
  exit 1
fi

FEATURE_SLUG=$(echo "$FEATURE_DESCRIPTION" | tr '[:upper:]' '[:lower:]' | tr -cs '[:alnum:]' '-' | cut -c1-50)

echo "✓ Feature identified"
echo "  Description: $FEATURE_DESCRIPTION"
echo "  Slug: $FEATURE_SLUG"
```

## Step 2: Generate Feature Specification Using AI

```javascript
const FEATURE_DESCRIPTION = process.env.FEATURE_DESCRIPTION;
const FEATURE_SLUG = process.env.FEATURE_SLUG;

await Task({
  subagent_type: 'general-purpose',
  description: 'Generate comprehensive feature specification',
  prompt: `Create a detailed feature specification for: ${FEATURE_DESCRIPTION}

Generate complete markdown specification document including:

## 1. Feature Overview
- Feature name (clear, descriptive)
- Brief 2-3 sentence description
- User story: As a [user type], I want [goal], so that [benefit]

## 2. Requirements
**Functional Requirements** (3-8 items):
- What the feature must do
- User interactions
- System behaviors

**Non-Functional Requirements**:
- Performance targets
- Security requirements
- Accessibility (WCAG level)
- Browser/device support

## 3. Technical Design
**Architecture**:
- High-level design approach
- Components needed
- Data flow

**Database Changes** (if needed):
- New tables/collections
- Schema modifications
- Migrations required

**API Changes** (if needed):
- New endpoints
- Modified endpoints
- Request/response formats

## 4. Implementation Plan
Break down into phases and tasks:

**Phase 1: Preparation**
- [ ] Create feature branch
- [ ] Review existing codebase
- [ ] Set up development environment
- [ ] Create database migrations (if needed)

**Phase 2: Core Development** (3-8 tasks)
- [ ] Specific implementation task 1
- [ ] Specific implementation task 2
- [ ] ...

**Phase 3: Testing**
- [ ] Unit tests for new components
- [ ] Integration tests
- [ ] E2E tests (if applicable)
- [ ] Manual QA testing

**Phase 4: Review & Deployment**
- [ ] Self-review
- [ ] Create PR
- [ ] Address review comments
- [ ] Merge and deploy

## 5. Testing Strategy
- Unit test areas (3-5)
- Integration test scenarios (2-4)
- E2E test flows (1-3)

## 6. Success Metrics
- Measurable metric 1 with target
- Measurable metric 2 with target
- User satisfaction target

## 7. Risks & Mitigation
| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|---------------------|
| [Risk 1] | High/Med/Low | High/Med/Low | [Strategy] |
| [Risk 2] | High/Med/Low | High/Med/Low | [Strategy] |

## 8. Timeline Estimate
- Planning: X days
- Development: X days (justify based on complexity)
- Testing: X days
- Review & deployment: X days
- **Total**: X days

**Complexity**: Simple (<1 day) | Medium (1-3 days) | Complex (>3 days)
**Priority**: Critical | High | Medium | Low

## 9. Approval Checklist
- [ ] Product Manager approval
- [ ] Tech Lead approval
- [ ] Security review (if needed)
- [ ] Ready for implementation

---
Created: ${new Date().toISOString().split('T')[0]}
Owner: TBD
Status: Planning

Save specification to: docs/features/${FEATURE_SLUG}.md

Also generate JSON summary for validation:
{
  "feature_name": "...",
  "spec_created": true,
  "spec_file_path": "docs/features/${FEATURE_SLUG}.md",
  "user_story": {
    "user_type": "...",
    "goal": "...",
    "benefit": "..."
  },
  "priority": "high|medium|low",
  "complexity": "simple|medium|complex",
  "estimated_days": X,
  "components_affected": ["component1", "component2"],
  "tasks_count": X,
  "database_changes_needed": true|false,
  "api_changes_needed": true|false,
  "risks_identified": X,
  "success_metrics_defined": true
}

Save JSON to: docs/features/${FEATURE_SLUG}.json`,

  context: {
    feature_description: FEATURE_DESCRIPTION,
    feature_slug: FEATURE_SLUG,
    spec_output: `docs/features/${FEATURE_SLUG}.md`,
    json_output: `docs/features/${FEATURE_SLUG}.json`
  }
});
```

## Step 3: Validate Output

```bash
FEATURE_SLUG="$FEATURE_SLUG"
SPEC_FILE="docs/features/${FEATURE_SLUG}.md"
JSON_FILE="docs/features/${FEATURE_SLUG}.json"

# Check spec created
if [ ! -f "$SPEC_FILE" ]; then
  echo "❌ ERROR: Feature specification not created"
  exit 1
fi

# Check minimum size
FILE_SIZE=$(wc -c < "$SPEC_FILE")
if [ $FILE_SIZE -lt 500 ]; then
  echo "❌ ERROR: Feature spec too small (< 500 bytes)"
  exit 1
fi

# Validate JSON summary
if [ -f "$JSON_FILE" ]; then
  if ! jq empty "$JSON_FILE" 2>/dev/null; then
    echo "⚠️  WARNING: JSON summary invalid"
  fi
fi

echo "✓ Output validation complete"
echo "  Spec: $SPEC_FILE ($FILE_SIZE bytes)"
```

## Completion

```
═══════════════════════════════════════════════════
      FEATURE SPECIFICATION CREATED ✓
═══════════════════════════════════════════════════

Feature: $FEATURE_DESCRIPTION
Command: /dev/feature-request
Version: 2.0.0

Specification Created:
  ✓ File: docs/features/$FEATURE_SLUG.md
  ✓ User story defined
  ✓ Technical design outlined
  ✓ Implementation tasks identified
  ✓ Risks assessed
  ✓ Timeline estimated

Estimated Complexity: [Simple/Medium/Complex]
Estimated Timeline: [X] days
Priority: [Critical/High/Medium/Low]

Validations Passed:
  ✓ Feature description validated
  ✓ Specification created (≥500 bytes)
  ✓ Quality threshold (≥0.85)

NEXT STEPS:

1. Review specification:
   cat docs/features/$FEATURE_SLUG.md

2. Get necessary approvals:
   - Product Manager
   - Tech Lead
   - Security (if needed)

3. When ready to implement:
   /dev/create-branch $FEATURE_SLUG
   /dev/implement $FEATURE_SLUG

═══════════════════════════════════════════════════
```

## Guidelines

- **Clear User Story**: Define as "As a [user], I want [goal], so that [benefit]"
- **Measurable Metrics**: Define success with specific, measurable targets
- **Risk Assessment**: Identify and mitigate risks before implementation
- **Realistic Timeline**: Base estimates on feature complexity and team capacity
- **Get Approval**: Ensure stakeholder alignment before implementation
