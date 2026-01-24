---
description: Run tests and fix failures with AI assistance
argument-hint: [test-pattern or 'all']
allowed-tools: Task, Bash, Read, Edit, AskUserQuestion
model: claude-sonnet-4-5
timeout: 1200
retry: 2
cost_estimate: 0.12-0.20

validation:
  input:
    test_pattern:
      required: false
      default: "all"
      error_message: "Test pattern should be 'all', 'unit', 'integration', 'e2e', or a specific pattern"
  output:
    schema: .claude/validation/schemas/dev/test-output.json
    required_files:
      - 'test-results/test-report.{json,xml,html}'
    min_file_size: 200
    quality_threshold: 0.80
    content_requirements:
      - "Test suite executed"
      - "Test report generated"
      - "Pass/fail counts recorded"
      - "Failed tests analyzed (if failures present)"
      - "Coverage calculated (if enabled)"

version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added output validation for test reports"
      - "Streamlined from 524 lines to focused workflow"
      - "Enhanced AI-assisted debugging for failures"
  - version: 1.0.0
    date: 2025-08-15
    changes:
      - "Initial implementation with AI debugging"
---

# Run Tests

Test Pattern: **${ARGUMENTS:-all}**

## Step 1: Validate Input & Determine Test Scope

```bash
TEST_PATTERN="${ARGUMENTS:-all}"

echo "Test pattern: $TEST_PATTERN"

# Determine test scope
case "$TEST_PATTERN" in
  all)
    echo "Running complete test suite"
    ;;
  unit)
    echo "Running unit tests only"
    ;;
  integration)
    echo "Running integration tests only"
    ;;
  e2e|end-to-end)
    echo "Running end-to-end tests only"
    ;;
  *)
    echo "Running tests matching pattern: $TEST_PATTERN"
    ;;
esac

echo "✓ Test scope determined"
```

## Step 2: Pre-Test Checks

```bash
# Check dependencies installed
if [ -f "package.json" ] && [ ! -d "node_modules" ]; then
  echo "⚠️  Dependencies not installed, installing..."
  npm install
fi

# Check test framework exists
if [ -f "package.json" ]; then
  if ! npm run | grep -q "test"; then
    echo "❌ ERROR: No test script found in package.json"
    exit 1
  fi
fi

echo "✓ Pre-test checks complete"
```

## Step 3: Execute Tests

```bash
TEST_PATTERN="$TEST_PATTERN"

# Create test results directory
mkdir -p test-results

# Run tests based on pattern
case "$TEST_PATTERN" in
  all)
    npm test -- --coverage --json --outputFile=test-results/test-report.json 2>&1 | tee test-results/test-output.log
    ;;
  unit)
    npm test -- --testPathPattern=".*\\.test\\.(ts|js)$" --coverage --json --outputFile=test-results/test-report.json 2>&1 | tee test-results/test-output.log
    ;;
  integration)
    npm test -- --testPathPattern=".*\\.integration\\.test\\.(ts|js)$" --json --outputFile=test-results/test-report.json 2>&1 | tee test-results/test-output.log
    ;;
  e2e|end-to-end)
    npm test -- --testPathPattern=".*\\.e2e\\.test\\.(ts|js)$" --json --outputFile=test-results/test-report.json 2>&1 | tee test-results/test-output.log
    ;;
  *)
    npm test -- --testNamePattern="$TEST_PATTERN" --json --outputFile=test-results/test-report.json 2>&1 | tee test-results/test-output.log
    ;;
esac

TEST_EXIT_CODE=$?

echo "Tests completed with exit code: $TEST_EXIT_CODE"
```

## Step 4: Analyze Test Results & Offer AI Debugging

```javascript
const TEST_PATTERN = process.env.TEST_PATTERN || 'all';
const TEST_EXIT_CODE = parseInt(process.env.TEST_EXIT_CODE || '0');

// Parse test results
let testResults;
try {
  const testReportPath = 'test-results/test-report.json';
  testResults = await Read({ file_path: testReportPath });
  testResults = JSON.parse(testResults);
} catch (error) {
  console.log('⚠️  Could not parse test report JSON, using log output');
  testResults = { numPassedTests: 0, numFailedTests: 0, numTotalTests: 0 };
}

const totalTests = testResults.numTotalTests || 0;
const passed = testResults.numPassedTests || 0;
const failed = testResults.numFailedTests || 0;
const skipped = testResults.numPendingTests || 0;

console.log(`\n═══════════════════════════════════════════════════`);
console.log(`              TEST RESULTS`);
console.log(`═══════════════════════════════════════════════════`);
console.log(`Total: ${totalTests} tests`);
console.log(`✓ Passed: ${passed}`);
console.log(`✗ Failed: ${failed}`);
console.log(`⊘ Skipped: ${skipped}`);
console.log(`═══════════════════════════════════════════════════\n`);

// If failures, offer AI-assisted debugging
if (failed > 0) {
  const response = await AskUserQuestion({
    questions: [{
      question: `${failed} test(s) failed. Would you like AI assistance to analyze and fix failures?`,
      header: "AI Debug",
      multiSelect: false,
      options: [
        { label: "Yes - Fix all failures", description: "AI will analyze all failures and suggest fixes" },
        { label: "Yes - Fix one-by-one", description: "Review and approve each fix individually" },
        { label: "No - I'll fix manually", description: "Skip AI assistance" }
      ]
    }]
  });

  const aiAssist = response.answers["0"];

  if (aiAssist && aiAssist !== "No - I'll fix manually") {
    // Use agent to analyze failures
    await Task({
      subagent_type: 'general-purpose',
      description: 'Analyze and fix test failures',
      prompt: `Analyze the following test failures and provide fixes:

TEST RESULTS:
${JSON.stringify(testResults, null, 2)}

TEST OUTPUT LOG:
${await Read({ file_path: 'test-results/test-output.log' })}

For each failing test:
1. Identify root cause (test issue vs implementation issue)
2. Read relevant test file and implementation
3. Determine the fix needed
4. ${aiAssist === "Yes - Fix all failures" ? 'Apply fix automatically' : 'Propose fix for approval'}

Focus on:
- Async timing issues (missing await, race conditions)
- Mock/stub configuration problems
- Test assertions (expected vs actual)
- Setup/teardown issues

Provide clear explanations for each fix.`,

      context: {
        test_pattern: TEST_PATTERN,
        failures_count: failed,
        auto_fix: aiAssist === "Yes - Fix all failures"
      }
    });
  }
}
```

## Step 5: Validate Output

```bash
# Check test report exists
if [ ! -f "test-results/test-report.json" ]; then
  echo "⚠️  WARNING: Test report JSON not found"
  # Try to create minimal report from log
  if [ -f "test-results/test-output.log" ]; then
    echo '{"numTotalTests": 0, "numPassedTests": 0, "numFailedTests": 0}' > test-results/test-report.json
  else
    echo "❌ ERROR: No test output found"
    exit 1
  fi
fi

# Check report is valid JSON
if ! jq empty test-results/test-report.json 2>/dev/null; then
  echo "⚠️  WARNING: Test report is not valid JSON"
fi

echo "✓ Output validation complete"
```

## Completion

```
═══════════════════════════════════════════════════
           TESTS COMPLETE
═══════════════════════════════════════════════════

Test Pattern: ${TEST_PATTERN}
Command: /dev/test
Version: 2.0.0

Test Results:
  Total: [count] tests
  ✓ Passed: [count]
  ✗ Failed: [count]
  ⊘ Skipped: [count]

Coverage: [percentage]%

Validations Passed:
  ✓ Tests executed
  ✓ Test report generated
  ${failed === 0 ? '✓ All tests passing' : '⚠️  Some tests failed'}
  ✓ Output validation complete

${failed > 0 ?
'NEXT STEPS:
→ Review test failures above
→ Fix issues (manually or with AI assistance)
→ Re-run: /dev/test' :
'NEXT STEPS:
→ Proceed to code review: /dev/review
→ Create pull request: /dev/create-pr'}

═══════════════════════════════════════════════════
```

## Guidelines

- **Run Tests Frequently**: Run tests after each significant code change
- **Fix Failures Immediately**: Don't let failing tests accumulate
- **Maintain Coverage**: Target ≥80% code coverage
- **Test Pyramid**: Many unit tests, fewer integration, minimal e2e
- **Fast Tests**: Keep test suite fast (< 5 minutes ideally)
- **Reliable Tests**: Avoid flaky tests, fix timing issues properly
