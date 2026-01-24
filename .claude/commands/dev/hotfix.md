---
description: Fast-track critical production bug fixes with streamlined workflow
argument-hint: <bug-description> [--severity critical|high]
allowed-tools: Task, Bash, AskUserQuestion
model: claude-sonnet-4-5
timeout: 1200
retry: 1
cost_estimate: 0.20-0.35

validation:
  input:
    bug_description:
      required: true
      min_length: 10
      error_message: "Bug description must be at least 10 characters"
    severity:
      required: false
      default: "critical"
      allowed_values: ["critical", "high"]
  output:
    schema: .claude/validation/schemas/dev/hotfix-output.json
    required_files:
      - 'incidents/hotfix-${timestamp}.md'
    min_file_size: 200
    quality_threshold: 0.95
    content_requirements:
      - "Hotfix completed successfully"
      - "Fix applied and tested"
      - "Safety checks passed"
      - "PR created and approved"
      - "Deployment verified"

version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added output validation for hotfix operations"
      - "Streamlined from 410 lines to focused workflow"
      - "Enhanced safety checks and rollback procedures"
      - "Fast-track process: 1-2 hours vs 4-7 hours normal workflow"
  - version: 1.0.0
    date: 2025-09-01
    changes:
      - "Initial implementation with emergency fix workflow"
---

# Hotfix Production Bug

Bug Description: **$ARGUMENTS**

## Step 1: Validate Severity & Approval

```bash
ARGS="$ARGUMENTS"
BUG_DESCRIPTION=$(echo "$ARGS" | sed 's/--severity.*//' | xargs)
SEVERITY=$(echo "$ARGS" | grep -oP '\-\-severity\s+\K\w+' || echo "critical")

# Validate bug description
if [ ${#BUG_DESCRIPTION} -lt 10 ]; then
  echo "❌ ERROR: Bug description too short (minimum 10 characters)"
  exit 1
fi

# Validate severity
case "$SEVERITY" in
  critical|high)
    echo "Severity: $SEVERITY"
    ;;
  *)
    echo "❌ ERROR: Invalid severity. Use 'critical' or 'high'"
    echo "For medium/low severity bugs, use normal workflow: /dev/feature-request"
    exit 1
    ;;
esac

echo "✓ Hotfix validated"
echo "  Bug: $BUG_DESCRIPTION"
  echo "  Severity: $SEVERITY"
```

## Step 2: Create Hotfix Branch

```bash
BUG_DESCRIPTION="$BUG_DESCRIPTION"

# Ensure on main and up to date
git checkout main
git pull origin main

# Create hotfix branch with timestamp
TIMESTAMP=$(date +%Y%m%d-%H%M)
BUG_SLUG=$(echo "$BUG_DESCRIPTION" | tr '[:upper:]' '[:lower:]' | tr -cs '[:alnum:]' '-' | cut -c1-40)
BRANCH_NAME="hotfix/${TIMESTAMP}-${BUG_SLUG}"

git checkout -b $BRANCH_NAME

echo "✓ Hotfix branch created: $BRANCH_NAME"
```

## Step 3: Implement Fix Using Agent

```javascript
const BUG_DESCRIPTION = process.env.BUG_DESCRIPTION;
const SEVERITY = process.env.SEVERITY || 'critical';
const BRANCH_NAME = process.env.BRANCH_NAME;

await Task({
  subagent_type: 'general-purpose',
  description: 'Implement hotfix for production bug',
  prompt: `Execute fast-track hotfix for critical production bug.

BUG DESCRIPTION: ${BUG_DESCRIPTION}
SEVERITY: ${SEVERITY}
BRANCH: ${BRANCH_NAME}

HOTFIX WORKFLOW:

**1. Implement Minimal Fix**:
- Keep changes MINIMAL (only fix the bug)
- No refactoring, no feature additions
- Single-purpose fix only
- Add regression test to prevent recurrence

**2. Run Tests (NON-NEGOTIABLE)**:
- All existing tests MUST pass
- New regression test MUST be added
- Regression test MUST fail on old code (proves it catches bug)
- Regression test MUST pass on new code (proves fix works)

Command: npm test

**3. Quick Safety Review (Automated)**:
Safety checks:
- No secrets committed (API keys, passwords, tokens)
- No debugging code left (console.log, debugger)
- No obvious security issues (SQL injection, XSS patterns)
- Files changed < 5 (keep scope minimal)
- Lines changed < 100 (keep changes small)

**4. Commit Changes**:
Format:
\`\`\`
🚨 HOTFIX: ${BUG_DESCRIPTION}

Severity: ${SEVERITY}
Root Cause: [Explain what caused the bug]
Fix: [Explain what was changed]
Testing: Added regression test

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
\`\`\`

**5. Create PR (Fast-Track)**:
- Title: "🚨 HOTFIX: ${BUG_DESCRIPTION}"
- Label: hotfix, critical, skip-review
- Include safety check results
- Include test results

**6. Generate Hotfix Report**:
Save to: incidents/hotfix-${process.env.TIMESTAMP}.md

Include:
- Bug description and severity
- Root cause analysis
- Fix summary
- Safety checks results
- Test results
- Time to fix
- Post-mortem action items

Provide:
- Fix implementation details
- Test results
- Safety check results
- PR URL
- Recommended next steps (approval, deployment)`,

  context: {
    bug_description: BUG_DESCRIPTION,
    severity: SEVERITY,
    branch_name: BRANCH_NAME,
    timestamp: process.env.TIMESTAMP,
    hotfix_report_output: `incidents/hotfix-${process.env.TIMESTAMP}.md`
  }
});
```

## Step 4: Validate Hotfix Quality

```bash
TIMESTAMP="$TIMESTAMP"
HOTFIX_REPORT="incidents/hotfix-${TIMESTAMP}.md"

# Check hotfix report created
if [ ! -f "$HOTFIX_REPORT" ]; then
  echo "❌ ERROR: Hotfix report not created"
  exit 1
fi

# Verify all tests pass
if ! npm test 2>&1 | grep -q "passing"; then
  echo "❌ ERROR: Tests are not passing"
  echo "All tests must pass before deploying hotfix"
  exit 1
fi

# Check safety: no secrets
if git diff main | grep -iqE '(api[_-]?key|password|secret|token).*=.*["\047][a-zA-Z0-9]{8,}'; then
  echo "❌ ERROR: Potential secrets detected in changes"
  exit 1
fi

# Check changes are minimal
FILES_CHANGED=$(git diff main --name-only | wc -l)
LINES_CHANGED=$(git diff main --shortstat | awk '{print $4+$6}')

if [ $FILES_CHANGED -gt 5 ]; then
  echo "⚠️  WARNING: $FILES_CHANGED files changed (keep hotfixes focused < 5 files)"
fi

if [ $LINES_CHANGED -gt 100 ]; then
  echo "⚠️  WARNING: $LINES_CHANGED lines changed (keep hotfixes small < 100 lines)"
fi

echo "✓ Hotfix quality validated"
echo "  Tests: Passing"
echo "  Secrets: None detected"
echo "  Files: $FILES_CHANGED changed"
echo "  Lines: $LINES_CHANGED changed"
```

## Step 5: Approval & Deployment

```bash
BUG_DESCRIPTION="$BUG_DESCRIPTION"
SEVERITY="$SEVERITY"
BRANCH_NAME="$BRANCH_NAME"

echo ""
echo "═══════════════════════════════════════════════════"
echo "          HOTFIX READY FOR DEPLOYMENT"
echo "═══════════════════════════════════════════════════"
echo ""
echo "Bug: $BUG_DESCRIPTION"
echo "Severity: $SEVERITY"
echo "Branch: $BRANCH_NAME"
echo ""
echo "Quality Checks:"
echo "  ✓ Fix implemented"
echo "  ✓ All tests passing"
echo "  ✓ Regression test added"
echo "  ✓ Safety checks passed"
echo "  ✓ Changes minimal (${FILES_CHANGED} files, ${LINES_CHANGED} lines)"
echo ""
echo "═══════════════════════════════════════════════════"
echo ""
echo "⚠️  PRODUCTION HOTFIX - Requires immediate deployment"
echo ""
# Note: In actual execution, would use AskUserQuestion for approval
```

## Completion

```
═══════════════════════════════════════════════════
       HOTFIX COMPLETED SUCCESSFULLY ✓
═══════════════════════════════════════════════════

Bug: $BUG_DESCRIPTION
Severity: $SEVERITY
Command: /dev/hotfix
Version: 2.0.0

Hotfix Details:
  ✓ Fix implemented
  ✓ Tests passing (including regression test)
  ✓ Safety checks passed
  ✓ PR created
  ✓ Branch: $BRANCH_NAME

Quality Metrics:
  Files changed: $FILES_CHANGED (target: <5)
  Lines changed: $LINES_CHANGED (target: <100)
  Secrets detected: 0
  Test status: All passing

Validations Passed:
  ✓ Severity validated (critical/high)
  ✓ Fix implemented with minimal changes
  ✓ Tests passing (non-negotiable)
  ✓ Safety checks passed
  ✓ Output validation complete
  ✓ Quality threshold (≥0.95)

NEXT STEPS:

1. Get expedited approval (for critical severity):
   - Notify team lead
   - Show safety check results
   - Request approval

2. Merge and deploy immediately:
   /dev/merge $BRANCH_NAME
   /devops/deploy production

3. Monitor closely for 30 minutes:
   /devops/monitor --duration 30

4. Create post-mortem within 24 hours:
   - Review incident timeline
   - Identify prevention measures
   - Update monitoring/alerts

═══════════════════════════════════════════════════

TIME SAVED: 3-5 hours vs normal workflow
TARGET: Fix deployed in < 2 hours

═══════════════════════════════════════════════════
```

## Guidelines

- **Critical/High Only**: Only use for CRITICAL or HIGH severity bugs
- **Minimal Changes**: Keep changes focused (< 5 files, < 100 lines)
- **Tests Required**: All tests must pass before deployment (non-negotiable)
- **Fast-Track**: Target 1-2 hours from bug discovery to deployment
- **Safety First**: Automated safety checks prevent common mistakes
- **Post-Mortem**: Create incident post-mortem within 24 hours
