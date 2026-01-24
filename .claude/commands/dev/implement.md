---
description: AI-assisted feature implementation with intelligent agent routing
argument-hint: <feature-name>
allowed-tools: Task, Bash, Read, Edit, Write, AskUserQuestion
model: claude-sonnet-4-5
timeout: 1800
retry: 2
cost_estimate: 0.30-0.50

validation:
  input:
    feature_name:
      required: true
      min_length: 3
      error_message: "Feature name must be at least 3 characters"
  output:
    schema: .claude/validation/schemas/dev/implement-output.json
    required_files:
      - 'implementation-reports/${feature_slug}-report.json'
    min_file_size: 300
    quality_threshold: 0.85
    content_requirements:
      - "Implementation completed"
      - "Tests added"
      - "Documentation updated"
      - "Ready for testing"

version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added output validation for implementations"
      - "Streamlined from 438 lines to focused workflow"
      - "Enhanced multi-agent routing and coordination"
  - version: 1.0.0
    date: 2025-08-20
    changes:
      - "Initial implementation with AI routing"
---

# Implement Feature

Feature: **$ARGUMENTS**

## Step 1: Validate Input & Load Specification

```bash
FEATURE_NAME="$ARGUMENTS"

if [ ${#FEATURE_NAME} -lt 3 ]; then
  echo "❌ ERROR: Feature name too short (minimum 3 characters)"
  exit 1
fi

FEATURE_SLUG=$(echo "$FEATURE_NAME" | tr '[:upper:]' '[:lower:]' | tr -cs '[:alnum:]' '-' | cut -c1-50)

# Check for feature spec
SPEC_FILE=$(find docs/features -name "*${FEATURE_SLUG}*.md" 2>/dev/null | head -1)

if [ -n "$SPEC_FILE" ]; then
  echo "✓ Feature spec found: $SPEC_FILE"
else
  echo "⚠️  No feature spec found - will gather requirements interactively"
fi

echo "✓ Feature validated"
echo "  Name: $FEATURE_NAME"
echo "  Slug: $FEATURE_SLUG"
```

## Step 2: Implement Feature Using AI Agents

```javascript
const FEATURE_NAME = process.env.FEATURE_NAME;
const FEATURE_SLUG = process.env.FEATURE_SLUG;
const SPEC_FILE = process.env.SPEC_FILE || '';

// Read spec if exists
let featureSpec = '';
if (SPEC_FILE) {
  featureSpec = await Read({ file_path: SPEC_FILE });
}

await Task({
  subagent_type: 'general-purpose',
  description: `Implement feature: ${FEATURE_NAME}`,
  prompt: `Implement the feature: ${FEATURE_NAME}

${featureSpec ? `FEATURE SPECIFICATION:
${featureSpec}

Follow the spec's technical design and implementation plan.` :
`No specification found. Gather requirements interactively and implement.`}

IMPLEMENTATION WORKFLOW:

**1. Analyze Scope & Route to Agents**:
Determine what needs to be built:
- Frontend components → Use appropriate React/Vue patterns
- Backend API → Implement REST endpoints
- Database changes → Create migrations
- Authentication → Add auth middleware
- Infrastructure → Update deployment configs

**2. Implement Core Functionality**:
For each component:
a) Read relevant existing files to understand patterns
b) Implement new functionality following project conventions
c) Add proper error handling
d) Include inline documentation (JSDoc/TSDoc)
e) Commit progressively with clear messages

**3. Add Comprehensive Tests**:
- Unit tests for new functions/components (target: 80%+ coverage)
- Integration tests for workflows
- E2E tests for user flows (if UI)
- Test edge cases and error conditions

**4. Update Documentation**:
- Code comments (why, not what)
- README updates (if needed)
- API documentation (if API changes)
- CHANGELOG entry

**5. Database Migrations** (if needed):
- Create migration files
- Implement up/down migrations
- Test migrations (up, down, up)
- Update schema documentation

**6. Track Implementation**:
Generate implementation report: implementation-reports/${FEATURE_SLUG}-report.json
{
  "implementation_status": "completed|partial|failed",
  "feature_name": "${FEATURE_NAME}",
  "files_created": X,
  "files_modified": X,
  "lines_added": X,
  "lines_removed": X,
  "tests_added": X,
  "commits_made": X,
  "components_implemented": ["component1", "component2"],
  "database_migrations_created": true|false,
  "api_endpoints_added": X,
  "documentation_updated": true|false,
  "code_quality_score": X,
  "agents_used": ["agent1", "agent2"],
  "implementation_time_minutes": X,
  "ready_for_testing": true|false
}

QUALITY STANDARDS:
- Follow project coding conventions
- Add proper error handling
- Validate all inputs
- Use parameterized queries (SQL injection prevention)
- Sanitize outputs (XSS prevention)
- Add security checks for sensitive operations
- Keep functions small and focused (<50 lines ideal)
- Use clear, descriptive variable names
- No magic numbers (use named constants)

COMMIT STRATEGY:
Commit after each logical change:
- "feat: add UserProfile component"
- "feat: implement user API endpoints"
- "test: add UserProfile tests"
- "docs: update API documentation"

Each commit should be atomic and reversible.

Provide comprehensive summary of implementation with file changes and next steps.`,

  context: {
    feature_name: FEATURE_NAME,
    feature_slug: FEATURE_SLUG,
    has_spec: !!SPEC_FILE,
    report_output: `implementation-reports/${FEATURE_SLUG}-report.json`
  }
});
```

## Step 3: Validate Implementation

```bash
FEATURE_SLUG="$FEATURE_SLUG"
IMPL_REPORT="implementation-reports/${FEATURE_SLUG}-report.json"

# Check report created
if [ ! -f "$IMPL_REPORT" ]; then
  echo "❌ ERROR: Implementation report not created"
  exit 1
fi

# Validate JSON
if ! jq empty "$IMPL_REPORT" 2>/dev/null; then
  echo "❌ ERROR: Implementation report invalid JSON"
  exit 1
fi

# Extract metrics
IMPL_STATUS=$(jq -r '.implementation_status' "$IMPL_REPORT")
FILES_CREATED=$(jq -r '.files_created' "$IMPL_REPORT")
FILES_MODIFIED=$(jq -r '.files_modified' "$IMPL_REPORT")
TESTS_ADDED=$(jq -r '.tests_added' "$IMPL_REPORT")
READY_FOR_TESTING=$(jq -r '.ready_for_testing' "$IMPL_REPORT")

echo "✓ Implementation validated"
echo "  Status: $IMPL_STATUS"
echo "  Files created: $FILES_CREATED"
echo "  Files modified: $FILES_MODIFIED"
echo "  Tests added: $TESTS_ADDED"
echo "  Ready for testing: $READY_FOR_TESTING"
```

## Completion

```
═══════════════════════════════════════════════════
      IMPLEMENTATION COMPLETE ✓
═══════════════════════════════════════════════════

Feature: $FEATURE_NAME
Command: /dev/implement
Version: 2.0.0

Implementation Summary:
  ✓ Status: $IMPL_STATUS
  ✓ Files created: $FILES_CREATED
  ✓ Files modified: $FILES_MODIFIED
  ✓ Tests added: $TESTS_ADDED
  ✓ Documentation updated: Yes
  ✓ Commits made: [X]

Ready for Testing: $READY_FOR_TESTING

Validations Passed:
  ✓ Feature name validated
  ✓ Implementation completed
  ✓ Report generated
  ✓ Quality threshold (≥0.85)

NEXT STEPS:

1. Run full test suite:
   /dev/test

2. Self-review code:
   /dev/review

3. Create pull request:
   /dev/create-pr

4. Or continue development if needed

═══════════════════════════════════════════════════
```

## Guidelines

- **Follow Spec**: Implement according to feature specification
- **Commit Frequently**: Commit after each logical change
- **Test As You Go**: Run tests after each component
- **Document Inline**: Add comments and documentation as you code
- **Use Agents**: Route specialized tasks to appropriate agents
- **Quality First**: Follow coding standards and best practices
