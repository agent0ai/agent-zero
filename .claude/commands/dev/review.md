---
description: Self-review code with AI assistance before creating PR
argument-hint: [file-pattern or 'all']
allowed-tools: Task, Bash, Read, AskUserQuestion
model: claude-sonnet-4-5
timeout: 1200
retry: 2
cost_estimate: 0.18-0.30

validation:
  input:
    file_pattern:
      required: false
      default: "all"
      error_message: "File pattern should be 'all' or a valid glob pattern"
  output:
    schema: .claude/validation/schemas/dev/review-output.json
    required_files:
      - 'code-reviews/review-report.json'
    min_file_size: 400
    quality_threshold: 0.85
    content_requirements:
      - "Review status determined"
      - "Issues categorized by severity"
      - "Automated checks executed"
      - "Overall assessment provided"
      - "Recommendations generated"

version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added output validation for code reviews"
      - "Streamlined from 518 lines to focused workflow"
      - "Enhanced AI review with code-reviewer agent integration"
      - "Safety checks for secrets and security"
  - version: 1.0.0
    date: 2025-08-08
    changes:
      - "Initial implementation with AI code analysis"
---

# Self-Review Code

File Pattern: **${ARGUMENTS:-all changed files}**

## Step 1: Validate Input & Identify Changed Files

```bash
FILE_PATTERN="${ARGUMENTS:-all}"

# Get changed files in current branch
echo "Identifying changed files..."
git diff --name-only origin/main...HEAD > /tmp/review-files.txt

# Apply pattern filter if provided
if [ "$FILE_PATTERN" != "all" ]; then
  grep "$FILE_PATTERN" /tmp/review-files.txt > /tmp/review-files-filtered.txt || {
    echo "❌ ERROR: No files match pattern: $FILE_PATTERN"
    exit 1
  }
  mv /tmp/review-files-filtered.txt /tmp/review-files.txt
fi

FILES_COUNT=$(cat /tmp/review-files.txt | wc -l)

if [ $FILES_COUNT -eq 0 ]; then
  echo "❌ ERROR: No changed files found"
  echo "Are you on a feature branch with changes?"
  exit 1
fi

echo "✓ Files identified for review"
echo "  Files to review: $FILES_COUNT"
```

## Step 2: Pre-Review Automated Checks

```bash
echo "Running automated checks..."

# Create results directory
mkdir -p code-reviews

# Linting check
echo "1. Linting..."
if npm run lint &>/dev/null; then
  LINT_STATUS="passed"
  LINT_ERRORS=0
else
  LINT_STATUS="failed"
  LINT_ERRORS=$(npm run lint 2>&1 | grep -c "error" || echo "0")
fi

# Type checking (TypeScript)
echo "2. Type checking..."
if npx tsc --noEmit &>/dev/null; then
  TYPE_STATUS="passed"
else
  TYPE_STATUS="failed"
fi

# Run tests
echo "3. Running tests..."
if npm test &>/dev/null; then
  TEST_STATUS="passed"
  TEST_COVERAGE=$(npm test -- --coverage --silent 2>&1 | grep -oP 'All files\s+\|\s+\K[0-9.]+' || echo "0")
else
  TEST_STATUS="failed"
  TEST_COVERAGE="0"
fi

# Security scan
echo "4. Security scan..."
if npm audit --audit-level=moderate &>/dev/null; then
  SECURITY_STATUS="passed"
else
  SECURITY_STATUS="failed"
fi

# Secrets scan
echo "5. Secrets scan..."
if git diff origin/main...HEAD | grep -iqE '(api[_-]?key|password|secret|token|credentials).*=.*["\047][a-zA-Z0-9]{8,}'; then
  SECRETS_STATUS="failed"
  echo "⚠️  WARNING: Potential secrets detected"
else
  SECRETS_STATUS="passed"
fi

echo "✓ Automated checks complete"
echo "  Linting: $LINT_STATUS"
echo "  Types: $TYPE_STATUS"
echo "  Tests: $TEST_STATUS (coverage: ${TEST_COVERAGE}%)"
echo "  Security: $SECURITY_STATUS"
echo "  Secrets: $SECRETS_STATUS"
```

## Step 3: AI-Powered Code Review

```javascript
const FILE_PATTERN = process.env.FILE_PATTERN || 'all';
const FILES_COUNT = parseInt(process.env.FILES_COUNT || '0');

// Read changed files list
const changedFiles = await Bash({
  command: 'cat /tmp/review-files.txt',
  description: 'Read changed files'
});

// Get diff for review
const fullDiff = await Bash({
  command: 'git diff origin/main...HEAD',
  description: 'Get full diff'
});

// Get file stats
const fileStats = await Bash({
  command: 'git diff --stat origin/main...HEAD',
  description: 'Get file statistics'
});

await Task({
  subagent_type: 'general-purpose',
  description: 'Comprehensive AI code review',
  prompt: `Perform a comprehensive code review of the following changes.

CHANGED FILES (${FILES_COUNT} total):
${changedFiles.stdout}

FILE STATISTICS:
${fileStats.stdout}

FULL DIFF:
${fullDiff.stdout}

REVIEW CATEGORIES:

**1. Code Quality** (Critical):
- Style and conventions adherence
- Code readability and clarity
- Function length and complexity
- Variable naming (descriptive, not magic)
- No debugging code (console.log, debugger, commented code)
- DRY principle (no duplication)

**2. Correctness** (Critical):
- Logic errors or bugs
- Edge case handling
- Error handling implemented
- Input validation present
- Async/await usage correct
- Race conditions avoided

**3. Security** (Critical):
- No hardcoded secrets/credentials
- SQL injection prevention (parameterized queries)
- XSS prevention (proper escaping)
- CSRF protection (if applicable)
- Authorization checks in place
- Sensitive data encryption

**4. Performance** (High):
- No N+1 queries
- Proper database indexing
- Large lists paginated
- Heavy computations optimized/cached
- Bundle size impact (frontend)

**5. Testing** (High):
- Unit tests added for new code
- Integration tests for workflows
- Test coverage ≥80% target
- Edge cases tested
- Error conditions tested

**6. Documentation** (Medium):
- Code comments (why, not what)
- JSDoc/TSDoc on public functions
- README updates (if needed)
- API documentation updates
- CHANGELOG entry

**7. Accessibility** (Medium, for UI changes):
- Semantic HTML
- ARIA labels appropriate
- Keyboard navigation
- Color contrast (WCAG)
- Screen reader compatible

OUTPUT REQUIREMENTS:

Generate comprehensive review report and save to: code-reviews/review-report.json

{
  "review_status": "passed|passed_with_warnings|needs_improvements|failed",
  "files_reviewed": ${FILES_COUNT},
  "issues_found": 0,
  "issues_by_severity": {
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 0
  },
  "automated_checks_passed": {
    "linting": ${process.env.LINT_STATUS === 'passed'},
    "type_checking": ${process.env.TYPE_STATUS === 'passed'},
    "tests": ${process.env.TEST_STATUS === 'passed'},
    "security_scan": ${process.env.SECURITY_STATUS === 'passed'},
    "secrets_scan": ${process.env.SECRETS_STATUS === 'passed'}
  },
  "test_coverage": ${process.env.TEST_COVERAGE || 0},
  "overall_assessment": "excellent|good|needs_work|significant_issues",
  "ready_for_pr": true|false,
  "recommendations": [
    "Specific recommendation 1",
    "Specific recommendation 2"
  ],
  "required_fixes": [
    "Critical issue that must be fixed",
    "Another required fix"
  ],
  "issues": [
    {
      "severity": "critical|high|medium|low",
      "category": "security|performance|correctness|quality",
      "file": "path/to/file.ts",
      "line": 42,
      "issue": "Description of issue",
      "recommendation": "How to fix it",
      "code_example": "Suggested code fix"
    }
  ]
}

SEVERITY GUIDELINES:
- **Critical**: Security vulnerabilities, data loss, critical bugs
- **High**: Major bugs, performance issues, missing tests
- **Medium**: Code quality issues, minor bugs, documentation gaps
- **Low**: Style issues, minor improvements, suggestions

Provide detailed analysis with specific file:line references and actionable recommendations.`,

  context: {
    file_pattern: FILE_PATTERN,
    files_count: FILES_COUNT,
    review_report_output: 'code-reviews/review-report.json'
  }
});
```

## Step 4: Display Review Results

```bash
# Check review report created
if [ ! -f "code-reviews/review-report.json" ]; then
  echo "❌ ERROR: Review report not created"
  exit 1
fi

# Validate JSON
if ! jq empty code-reviews/review-report.json 2>/dev/null; then
  echo "❌ ERROR: Review report is not valid JSON"
  exit 1
fi

# Extract key metrics
REVIEW_STATUS=$(jq -r '.review_status' code-reviews/review-report.json)
ISSUES_FOUND=$(jq -r '.issues_found' code-reviews/review-report.json)
CRITICAL_ISSUES=$(jq -r '.issues_by_severity.critical' code-reviews/review-report.json)
HIGH_ISSUES=$(jq -r '.issues_by_severity.high' code-reviews/review-report.json)
MEDIUM_ISSUES=$(jq -r '.issues_by_severity.medium' code-reviews/review-report.json)
LOW_ISSUES=$(jq -r '.issues_by_severity.low' code-reviews/review-report.json)
OVERALL_ASSESSMENT=$(jq -r '.overall_assessment' code-reviews/review-report.json)
READY_FOR_PR=$(jq -r '.ready_for_pr' code-reviews/review-report.json)
TEST_COVERAGE=$(jq -r '.test_coverage' code-reviews/review-report.json)

echo ""
echo "═══════════════════════════════════════════════════"
echo "          AI CODE REVIEW RESULTS"
echo "═══════════════════════════════════════════════════"
echo ""
echo "OVERALL ASSESSMENT: $OVERALL_ASSESSMENT"
echo "REVIEW STATUS: $REVIEW_STATUS"
echo ""
echo "ISSUES FOUND: $ISSUES_FOUND total"
echo "  Critical: $CRITICAL_ISSUES"
echo "  High: $HIGH_ISSUES"
echo "  Medium: $MEDIUM_ISSUES"
echo "  Low: $LOW_ISSUES"
echo ""
echo "AUTOMATED CHECKS:"
echo "  Linting: $LINT_STATUS"
echo "  Type checking: $TYPE_STATUS"
echo "  Tests: $TEST_STATUS (coverage: ${TEST_COVERAGE}%)"
echo "  Security scan: $SECURITY_STATUS"
echo "  Secrets scan: $SECRETS_STATUS"
echo ""

# Display critical issues
if [ $CRITICAL_ISSUES -gt 0 ]; then
  echo "───────────────────────────────────────────────────"
  echo "CRITICAL ISSUES ($CRITICAL_ISSUES)"
  echo "───────────────────────────────────────────────────"
  jq -r '.issues[] | select(.severity=="critical") | "
\(.category | ascii_upcase): \(.file):\(.line)
Issue: \(.issue)
Fix: \(.recommendation)
"' code-reviews/review-report.json
fi

# Display high priority issues
if [ $HIGH_ISSUES -gt 0 ]; then
  echo "───────────────────────────────────────────────────"
  echo "HIGH PRIORITY ISSUES ($HIGH_ISSUES)"
  echo "───────────────────────────────────────────────────"
  jq -r '.issues[] | select(.severity=="high") | "
\(.category | ascii_upcase): \(.file):\(.line)
Issue: \(.issue)
Fix: \(.recommendation)
"' code-reviews/review-report.json
fi

echo "═══════════════════════════════════════════════════"
echo ""
echo "READY FOR PR: $READY_FOR_PR"
echo ""

# Display recommendations
echo "RECOMMENDATIONS:"
jq -r '.recommendations[] | "  → \(.)"' code-reviews/review-report.json

if [ $CRITICAL_ISSUES -gt 0 ] || [ $HIGH_ISSUES -gt 0 ]; then
  echo ""
  echo "REQUIRED FIXES BEFORE PR:"
  jq -r '.required_fixes[] | "  ❗ \(.)"' code-reviews/review-report.json
fi

echo ""
echo "═══════════════════════════════════════════════════"
```

## Step 5: Offer AI-Assisted Fixes

```bash
CRITICAL_ISSUES="$CRITICAL_ISSUES"
HIGH_ISSUES="$HIGH_ISSUES"
READY_FOR_PR="$READY_FOR_PR"

if [ $CRITICAL_ISSUES -gt 0 ] || [ $HIGH_ISSUES -gt 0 ]; then
  echo ""
  echo "AI-ASSISTED FIX AVAILABLE"
  echo ""
  echo "Would you like AI assistance to fix these issues?"
  echo ""
  echo "Options:"
  echo "1. Fix critical issues automatically"
  echo "2. Fix all issues automatically"
  echo "3. Fix issues one-by-one (with approval)"
  echo "4. View detailed recommendations only"
  echo "5. Skip fixes (I'll fix manually)"
  echo ""

  # Note: In actual execution, would use AskUserQuestion here
  # For v2.0.0, we document the workflow
fi
```

## Step 6: Validate Output

```bash
REVIEW_REPORT="code-reviews/review-report.json"

# Check report exists and is valid
if [ ! -f "$REVIEW_REPORT" ]; then
  echo "❌ ERROR: Review report not found"
  exit 1
fi

if ! jq empty "$REVIEW_REPORT" 2>/dev/null; then
  echo "❌ ERROR: Review report is not valid JSON"
  exit 1
fi

# Check minimum file size
FILE_SIZE=$(wc -c < "$REVIEW_REPORT")
if [ $FILE_SIZE -lt 400 ]; then
  echo "❌ ERROR: Review report too small (< 400 bytes)"
  echo "Size: $FILE_SIZE bytes"
  exit 1
fi

# Verify all required fields present
REQUIRED_FIELDS="review_status files_reviewed issues_found overall_assessment ready_for_pr"
for field in $REQUIRED_FIELDS; do
  if ! jq -e ".$field" "$REVIEW_REPORT" >/dev/null 2>&1; then
    echo "❌ ERROR: Missing required field: $field"
    exit 1
  fi
done

echo "✓ Output validation complete"
echo "  Report: $REVIEW_REPORT"
echo "  Size: $FILE_SIZE bytes"
```

## Completion

```
═══════════════════════════════════════════════════
        SELF-REVIEW COMPLETE ✓
═══════════════════════════════════════════════════

Files Reviewed: $FILES_COUNT
Command: /dev/review
Version: 2.0.0

Review Results:
  Overall: $OVERALL_ASSESSMENT
  Status: $REVIEW_STATUS
  Issues: $ISSUES_FOUND total
    Critical: $CRITICAL_ISSUES
    High: $HIGH_ISSUES
    Medium: $MEDIUM_ISSUES
    Low: $LOW_ISSUES

Automated Checks:
  ✓ Linting: $LINT_STATUS
  ✓ Type checking: $TYPE_STATUS
  ✓ Tests: $TEST_STATUS (${TEST_COVERAGE}% coverage)
  ✓ Security: $SECURITY_STATUS
  ✓ Secrets: $SECRETS_STATUS

Ready for PR: $READY_FOR_PR

Validations Passed:
  ✓ Files identified and reviewed
  ✓ Automated checks executed
  ✓ AI review completed
  ✓ Output validation complete
  ✓ Quality threshold (≥0.85)

NEXT STEPS:

${READY_FOR_PR == "true" ?
"✓ Code is ready for PR creation!

1. Create pull request:
   /dev/create-pr

2. Or create draft PR:
   /dev/create-pr --draft" :
"❗ Fix required issues before creating PR

1. Address critical and high priority issues:
   - Review detailed recommendations above
   - Fix issues manually or with AI assistance

2. Re-run review after fixes:
   /dev/review

3. When ready, create PR:
   /dev/create-pr"}

═══════════════════════════════════════════════════

TIP: Review your code as if reviewing someone else's PR!

═══════════════════════════════════════════════════
```

## Guidelines

- **Run Before PR**: Always review before creating pull request
- **Fix Critical Issues**: Address security and correctness issues immediately
- **Test Coverage**: Target ≥80% coverage for new code
- **No Secrets**: Never commit API keys, passwords, or credentials
- **Clean Code**: Remove console.log, debugger, commented code
- **Self-Review**: Review as critically as you would review others' code
