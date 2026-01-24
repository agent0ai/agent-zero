---
description: Test CI/CD pipeline configuration with validation and dry-run
argument-hint: [--platform <github|gitlab|circleci>]
allowed-tools: Task, Bash, Read, Write
model: claude-sonnet-4-5
timeout: 600
retry: 2
cost_estimate: 0.10-0.18

validation:
  input:
    platform:
      required: false
      default: "github"
      allowed_values: ["github", "gitlab", "circleci"]
  output:
    schema: .claude/validation/schemas/cicd/test-pipeline-output.json
    required_files:
      - 'cicd-tests/pipeline-test-report.{json,html}'
    min_file_size: 200
    quality_threshold: 0.90
    content_requirements:
      - "Pipeline syntax validated"
      - "Required secrets verified"
      - "Stages tested (≥1)"
      - "Test report generated"

version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added output validation for pipeline tests"
      - "Streamlined from 742 lines to focused workflow"
      - "Multi-platform support (GitHub/GitLab/CircleCI)"
  - version: 1.0.0
    date: 2025-09-15
    changes:
      - "Initial implementation with GitHub Actions support"
---

# Test CI/CD Pipeline

Platform: **${ARGUMENTS:-github}**

## Step 1: Validate Input & Detect Platform

```bash
PLATFORM=$(echo "$ARGUMENTS" | grep -oP '\-\-platform\s+\K\w+' || echo "github")

# Validate platform
case "$PLATFORM" in
  github|gitlab|circleci)
    echo "Platform: $PLATFORM"
    ;;
  *)
    echo "❌ ERROR: Invalid platform: $PLATFORM"
    echo "Valid platforms: github, gitlab, circleci"
    exit 1
    ;;
esac

echo "✓ Platform validated: $PLATFORM"
```

## Step 2: Detect Pipeline Configuration Files

```bash
PLATFORM="$PLATFORM"

# Find pipeline config files
case "$PLATFORM" in
  github)
    PIPELINE_FILES=$(find .github/workflows -name "*.yml" -o -name "*.yaml" 2>/dev/null || echo "")
    ;;
  gitlab)
    PIPELINE_FILES=".gitlab-ci.yml"
    ;;
  circleci)
    PIPELINE_FILES=".circleci/config.yml"
    ;;
esac

if [ -z "$PIPELINE_FILES" ]; then
  echo "❌ ERROR: No pipeline configuration files found for $PLATFORM"
  exit 1
fi

echo "Pipeline files found:"
echo "$PIPELINE_FILES"
echo "✓ Pipeline files detected"
```

## Step 3: Test Pipeline Using Agent

```javascript
const PLATFORM = process.env.PLATFORM || 'github';
const PIPELINE_FILES = process.env.PIPELINE_FILES || '';

await Task({
  subagent_type: 'general-purpose',
  description: 'Test CI/CD pipeline configuration',
  prompt: `Test and validate CI/CD pipeline configuration for ${PLATFORM}.

PIPELINE FILES:
${PIPELINE_FILES}

TESTING WORKFLOW:

**1. Syntax Validation**:
- Parse YAML/workflow files
- Check for syntax errors
- Validate job/stage definitions
- Check for required fields
- Verify proper indentation

**2. Structure Validation**:
- Verify job dependencies (needs/depends_on)
- Check for circular dependencies
- Validate job names (unique, valid characters)
- Verify stage ordering
- Check for unreachable jobs

**3. Secrets/Variables Check**:
Required secrets typically include:
- Cloud provider credentials
- Container registry credentials
- Deployment keys
- API tokens
- Notification webhooks

Verify all referenced secrets are:
- Listed in documentation
- Properly referenced in workflow
- Not hardcoded (security check)

**4. Platform-Specific Validation**:

${PLATFORM === 'github' ? `
**GitHub Actions**:
- Validate workflow triggers (on: push, pull_request, etc.)
- Check runner compatibility (ubuntu-latest, etc.)
- Verify action versions (@v2, @v3, etc.)
- Check for deprecated actions
- Validate cache strategies
- Test with: gh workflow view --yaml
` : ''}

${PLATFORM === 'gitlab' ? `
**GitLab CI**:
- Validate stage definitions
- Check runner tags
- Verify artifact paths
- Check cache configuration
- Validate before_script/after_script
- Test with: gitlab-ci-lint
` : ''}

${PLATFORM === 'circleci' ? `
**CircleCI**:
- Validate executor types
- Check resource classes
- Verify workflow jobs
- Check caching strategies
- Validate orb usage
- Test with: circleci config validate
` : ''}

**5. Dry-Run Testing** (non-destructive):
- Test build stage (without actually building)
- Test test stage (syntax only)
- Test deployment stage (--dry-run mode)
- Verify environment variables available
- Check for missing dependencies

**6. Generate Test Report**:
Save to: cicd-tests/pipeline-test-report.json
{
  "platform": "${PLATFORM}",
  "pipeline_status": "success|failed|partial",
  "stages_tested": 0,
  "stages_passed": 0,
  "syntax_valid": true|false,
  "secrets_verified": true|false,
  "issues_found": [],
  "recommendations": []
}

Provide detailed validation results with any issues found.`,

  context: {
    platform: PLATFORM,
    pipeline_files: PIPELINE_FILES,
    test_report_output: 'cicd-tests/pipeline-test-report.json'
  }
});
```

## Step 4: Validate Output

```bash
TEST_REPORT="cicd-tests/pipeline-test-report.json"

# Check test report created
if [ ! -f "$TEST_REPORT" ]; then
  echo "❌ ERROR: Pipeline test report not created"
  exit 1
fi

# Validate JSON
if ! jq empty "$TEST_REPORT" 2>/dev/null; then
  echo "❌ ERROR: Test report is not valid JSON"
  exit 1
fi

# Check pipeline status
PIPELINE_STATUS=$(jq -r '.pipeline_status' "$TEST_REPORT")
SYNTAX_VALID=$(jq -r '.syntax_valid' "$TEST_REPORT")

if [ "$SYNTAX_VALID" != "true" ]; then
  echo "❌ ERROR: Pipeline syntax validation failed"
  jq -r '.issues_found[]' "$TEST_REPORT"
  exit 1
fi

echo "✓ Output validation complete"
echo "  Status: $PIPELINE_STATUS"
echo "  Syntax: Valid"
```

## Completion

```
═══════════════════════════════════════════════════
      CI/CD PIPELINE TESTING COMPLETE ✓
═══════════════════════════════════════════════════

Platform: $PLATFORM
Command: /cicd/test-pipeline
Version: 2.0.0

Pipeline Test Results:
  ✓ Syntax validated
  ✓ Structure checked
  ✓ Secrets verified
  ✓ Stages tested: [count]
  ${PIPELINE_STATUS === 'success' ? '✓ All tests passed' : '⚠️  Some issues found'}

Validations Passed:
  ✓ Input validation (platform valid)
  ✓ Output validation (test report created)
  ✓ Pipeline syntax valid
  ✓ Quality threshold (≥0.90)

NEXT STEPS:
${PIPELINE_STATUS === 'success' ?
'→ Pipeline ready for deployment
→ Test actual pipeline run
→ Monitor first production run' :
'→ Fix issues identified in test report
→ Re-test: /cicd/test-pipeline
→ Review recommendations'}

═══════════════════════════════════════════════════
```

## Guidelines

- **Test Before Deploy**: Always test pipeline changes before deploying
- **Validate Secrets**: Ensure all required secrets are documented and configured
- **Check Dependencies**: Verify all actions/orbs/images are accessible
- **Dry-Run Deploys**: Test deployment stages in dry-run mode
- **Version Pinning**: Pin action/orb versions to avoid breaking changes
- **Monitor First Run**: Closely monitor first run after pipeline changes
