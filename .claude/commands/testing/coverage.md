---
description: Analyze and improve test coverage with AI assistance
argument-hint: [file-path or --generate-missing]
model: claude-sonnet-4-5-20250929
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, AskUserQuestion
---

Analyze test coverage for: **${ARGUMENTS:-entire project}**

## What This Command Does

This command analyzes your test coverage, identifies gaps in testing, and automatically generates tests for uncovered code. It provides detailed insights into which lines, branches, functions, and files lack test coverage, then uses AI to create comprehensive tests that improve coverage while maintaining quality.

**Key Capabilities**:

- Generates coverage reports (line, branch, function, statement)
- Identifies critical uncovered code paths
- Prioritizes coverage gaps by risk/importance
- Automatically generates tests for uncovered code
- Tracks coverage trends over time
- Enforces coverage thresholds

## Step 1: Detect Test Framework and Coverage Tool

**Identify coverage tooling**:

```bash
# Check package.json for coverage tools
if grep -q "jest" package.json; then
  FRAMEWORK="jest"
  COVERAGE_CMD="npm test -- --coverage"
elif grep -q "vitest" package.json; then
  FRAMEWORK="vitest"
  COVERAGE_CMD="npm run test:coverage"
elif grep -q "c8\|nyc" package.json; then
  FRAMEWORK="mocha"
  COVERAGE_CMD="nyc npm test"
elif grep -q "pytest-cov" requirements.txt; then
  FRAMEWORK="pytest"
  COVERAGE_CMD="pytest --cov=src --cov-report=html --cov-report=term"
elif grep -q "coverage" go.mod; then
  FRAMEWORK="go"
  COVERAGE_CMD="go test -coverprofile=coverage.out ./..."
else
  echo "No coverage tool detected. Would you like to install one?"
  echo "1) Jest (JavaScript/TypeScript)"
  echo "2) pytest-cov (Python)"
  echo "3) go test -cover (Go)"
fi
```

## Step 2: Generate Coverage Report

**Run tests with coverage**:

```bash
echo "Running tests with coverage analysis..."

# JavaScript/TypeScript (Jest)
npm test -- --coverage --coverage-reporters=text --coverage-reporters=json --coverage-reporters=lcov

# Python
pytest --cov=src --cov-report=term-missing --cov-report=json --cov-report=html

# Go
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out -o coverage.html

# Save coverage data
COVERAGE_FILE="coverage/coverage-final.json"
```

## Step 3: Analyze Coverage Data

**Parse coverage report**:

```javascript
const coverageData = await Read({
  file_path: 'coverage/coverage-final.json'
})

const coverage = JSON.parse(coverageData)

// Calculate overall coverage
const summary = {
  lines: {
    covered: 0,
    total: 0,
    percentage: 0
  },
  branches: {
    covered: 0,
    total: 0,
    percentage: 0
  },
  functions: {
    covered: 0,
    total: 0,
    percentage: 0
  },
  statements: {
    covered: 0,
    total: 0,
    percentage: 0
  }
}

// Aggregate across all files
for (const [filePath, fileCoverage] of Object.entries(coverage)) {
  summary.lines.covered += fileCoverage.lines.covered
  summary.lines.total += fileCoverage.lines.total
  summary.branches.covered += fileCoverage.branches.covered
  summary.branches.total += fileCoverage.branches.total
  // ... etc
}

// Calculate percentages
summary.lines.percentage = (summary.lines.covered / summary.lines.total) * 100
summary.branches.percentage = (summary.branches.covered / summary.branches.total) * 100
```

## Step 4: Identify Coverage Gaps

**Find uncovered code**:

```javascript
const gaps = {
  critical: [],    // Critical business logic uncovered
  important: [],   // Important features uncovered
  moderate: [],    // Standard code uncovered
  low: []         // Utility/simple code uncovered
}

for (const [filePath, fileCoverage] of Object.entries(coverage)) {
  // Skip test files and generated code
  if (filePath.includes('.test.') || filePath.includes('generated/')) {
    continue
  }

  const uncoveredLines = []
  const uncoveredBranches = []

  // Find uncovered lines
  for (const [lineNum, hits] of Object.entries(fileCoverage.s)) {
    if (hits === 0) {
      uncoveredLines.push(parseInt(lineNum))
    }
  }

  // Find uncovered branches
  for (const [branchId, branch] of Object.entries(fileCoverage.b)) {
    const uncoveredPaths = branch.filter(hits => hits === 0)
    if (uncoveredPaths.length > 0) {
      uncoveredBranches.push(branchId)
    }
  }

  if (uncoveredLines.length > 0 || uncoveredBranches.length > 0) {
    // Categorize by priority
    const priority = determineFilePriority(filePath)

    gaps[priority].push({
      file: filePath,
      uncoveredLines,
      uncoveredBranches,
      coverage: fileCoverage.lines.pct
    })
  }
}

function determineFilePriority(filePath) {
  // Critical: payment, auth, security
  if (/payment|auth|security|billing/i.test(filePath)) {
    return 'critical'
  }

  // Important: core business logic
  if (/service|controller|repository|api/i.test(filePath)) {
    return 'important'
  }

  // Moderate: UI components, utilities
  if (/component|util|helper/i.test(filePath)) {
    return 'moderate'
  }

  return 'low'
}
```

## Step 5: Display Coverage Report

**Generate comprehensive report**:

```
═══════════════════════════════════════════════════
              COVERAGE ANALYSIS REPORT
═══════════════════════════════════════════════════

OVERALL COVERAGE:
  Lines:      847 / 1,023  (82.8%)  ████████░░
  Branches:   312 / 428    (72.9%)  ███████░░░
  Functions:  156 / 167    (93.4%)  █████████░
  Statements: 845 / 1,021  (82.8%)  ████████░░

TARGET: 80% line coverage  ✓ ACHIEVED

COVERAGE TREND:
  Last week:  78.3% (+4.5%)  ↗
  Last month: 75.1% (+7.7%)  ↗

═══════════════════════════════════════════════════

COVERAGE BY CATEGORY:

  🔴 CRITICAL (< 80% coverage):
     src/services/paymentService.ts         45.2%
     src/services/authService.ts            67.3%
     src/security/encryption.ts             58.9%

  🟡 IMPORTANT (80-90% coverage):
     src/services/userService.ts            85.7%
     src/controllers/orderController.ts     82.1%
     src/api/webhooks.ts                    88.3%

  🟢 WELL COVERED (> 90% coverage):
     src/utils/validator.ts                 96.2%
     src/models/user.ts                     94.8%
     src/middleware/auth.ts                 92.5%

═══════════════════════════════════════════════════

UNCOVERED CODE BY PRIORITY:

  🚨 CRITICAL GAPS (3 files):

     1. src/services/paymentService.ts (45.2% coverage)
        Uncovered lines: 45-52, 67-89, 102-110
        Uncovered branches: 3, 7, 12
        Risk: HIGH - Handles financial transactions
        Recommendation: URGENT - Add tests immediately

     2. src/services/authService.ts (67.3% coverage)
        Uncovered lines: 23-28, 41-43
        Uncovered branches: 2, 5
        Risk: HIGH - Security-critical code
        Recommendation: URGENT - Add auth flow tests

     3. src/security/encryption.ts (58.9% coverage)
        Uncovered lines: 15-22, 34-39
        Uncovered branches: 1, 4
        Risk: HIGH - Data protection
        Recommendation: URGENT - Add encryption tests

  ⚠️  IMPORTANT GAPS (6 files):

     4. src/services/userService.ts (85.7% coverage)
        Uncovered lines: 156-162
        Uncovered branches: 8
        Risk: MEDIUM - User management
        Recommendation: Add edge case tests

     5. src/controllers/orderController.ts (82.1% coverage)
        Uncovered lines: 78-82, 95-98
        Uncovered branches: 5, 9
        Risk: MEDIUM - Order processing
        Recommendation: Add error scenario tests

     ... (4 more files)

  📝 MODERATE GAPS (12 files):
     src/utils/formatter.ts (75.3%)
     src/components/UserCard.tsx (72.8%)
     ... (10 more files)

═══════════════════════════════════════════════════

RECOMMENDATIONS:

  🎯 Quick Wins (Easy improvements):
     • Add 5 tests to paymentService.ts → +15% coverage
     • Add 3 tests to authService.ts → +12% coverage
     • Add 4 tests to encryption.ts → +10% coverage
     Expected total improvement: +37% → 85.7% coverage

  📊 Branch Coverage Needs Attention:
     • 116 uncovered branches (27.1%)
     • Focus on conditional logic and error handling
     • Priority files: paymentService, authService, webhooks

  🔄 Suggested Next Steps:
     1. Generate tests for critical gaps (3 files)
     2. Add error scenario tests (6 files)
     3. Improve branch coverage in conditionals
     4. Set up coverage enforcement (fail below 80%)

═══════════════════════════════════════════════════

WOULD YOU LIKE TO AUTO-GENERATE TESTS?

Options:
  [1] Generate tests for ALL critical gaps (3 files)
  [2] Generate tests for specific file
  [3] Generate tests for uncovered lines only
  [4] Show detailed coverage for specific file
  [5] Export coverage report (HTML, JSON, LCOV)
  [6] Exit

Select option: _
```

## Step 6: Auto-Generate Missing Tests

**Generate tests for uncovered code**:

```javascript
async function generateMissingTests(file, uncoveredLines) {
  // Read source file
  const sourceCode = await Read({ file_path: file })

  // Extract uncovered code sections
  const uncoveredSections = extractUncoveredCode(sourceCode, uncoveredLines)

  // Generate tests using AI
  const prompt = `
Analyze this file and generate tests for uncovered code:

FILE: ${file}
CURRENT COVERAGE: ${fileCoverage}%
TARGET COVERAGE: 80%+

SOURCE CODE:
\`\`\`typescript
${sourceCode}
\`\`\`

UNCOVERED LINES: ${uncoveredLines.join(', ')}

UNCOVERED CODE SECTIONS:
${uncoveredSections.map((section, idx) => `
Section ${idx + 1} (lines ${section.start}-${section.end}):
\`\`\`typescript
${section.code}
\`\`\`
`).join('\n')}

Please generate comprehensive tests that:
1. Cover all uncovered lines
2. Test all branches (if/else, switch, ternary)
3. Test error scenarios
4. Test edge cases
5. Use appropriate mocks for dependencies
6. Follow existing test patterns in the project

Requirements:
- Generate tests that increase coverage to 80%+
- Focus on meaningful tests (not just coverage for coverage's sake)
- Include clear test names and comments
- Test both happy path and error scenarios
  `

  const generatedTests = await generateWithAI(prompt)

  return generatedTests
}
```

## Step 7: Validate Coverage Improvement

**Run tests and verify coverage increased**:

```bash
# Run tests again with coverage
npm test -- --coverage

# Calculate coverage difference
echo "Coverage before: ${BEFORE_COVERAGE}%"
echo "Coverage after: ${AFTER_COVERAGE}%"
echo "Improvement: +$(bc <<< "$AFTER_COVERAGE - $BEFORE_COVERAGE")%"

# Verify target reached
if (( $(bc <<< "$AFTER_COVERAGE >= 80") )); then
  echo "✓ Target coverage (80%) achieved!"
else
  echo "⚠ Coverage still below target. Need additional tests."
fi
```

## Step 8: Set Up Coverage Enforcement

**Configure coverage thresholds**:

```json
// jest.config.js
module.exports = {
  coverageThreshold: {
    global: {
      branches: 75,
      functions: 80,
      lines: 80,
      statements: 80
    },
    // Per-file thresholds
    './src/services/paymentService.ts': {
      branches: 90,
      functions: 95,
      lines: 90,
      statements: 90
    },
    './src/services/authService.ts': {
      branches: 90,
      functions: 95,
      lines: 90,
      statements: 90
    }
  }
}
```

**Add pre-commit hook**:

```bash
#!/bin/bash
# .husky/pre-commit

echo "Running tests with coverage..."
npm test -- --coverage --coverageReporters=text-summary

# Extract coverage percentage
COVERAGE=$(npm test -- --coverage --coverageReporters=json-summary 2>&1 | grep -o '"lines":{"total":[0-9]*,"covered":[0-9]*,"skipped":[0-9]*,"pct":[0-9.]*' | grep -o 'pct":[0-9.]*' | cut -d: -f2)

if (( $(bc <<< "$COVERAGE < 80") )); then
  echo "❌ Coverage is below 80% ($COVERAGE%)"
  echo "Please add tests before committing."
  exit 1
fi

echo "✓ Coverage check passed ($COVERAGE%)"
```

## Step 9: Track Coverage Over Time

**Store coverage history**:

```bash
# Save coverage snapshot
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p coverage/history

cp coverage/coverage-summary.json "coverage/history/coverage_${TIMESTAMP}.json"

# Generate trend report
node scripts/generateCoverageTrend.js
```

**Generate trend visualization**:

```javascript
// scripts/generateCoverageTrend.js
const fs = require('fs')
const path = require('path')

const historyDir = 'coverage/history'
const files = fs.readdirSync(historyDir)

const trend = files.map(file => {
  const data = JSON.parse(fs.readFileSync(path.join(historyDir, file)))
  const timestamp = file.match(/coverage_(\d{8}_\d{6})/)[1]

  return {
    timestamp,
    coverage: data.total.lines.pct
  }
}).sort((a, b) => a.timestamp.localeCompare(b.timestamp))

console.log('Coverage Trend:')
console.log('===============')
trend.forEach(({ timestamp, coverage }) => {
  const date = `${timestamp.slice(0, 4)}-${timestamp.slice(4, 6)}-${timestamp.slice(6, 8)}`
  const bars = '█'.repeat(Math.floor(coverage / 5))
  console.log(`${date}: ${coverage.toFixed(1)}% ${bars}`)
})
```

## Step 10: Generate Final Report

```
═══════════════════════════════════════════════════
         COVERAGE IMPROVEMENT SUMMARY
═══════════════════════════════════════════════════

BEFORE:
  Lines: 82.8%
  Branches: 72.9%
  Functions: 93.4%

AFTER:
  Lines: 89.2% (+6.4%)  ✓
  Branches: 81.5% (+8.6%)  ✓
  Functions: 95.8% (+2.4%)  ✓

TESTS GENERATED:
  ✓ paymentService.test.ts (12 new tests)
  ✓ authService.test.ts (8 new tests)
  ✓ encryption.test.ts (6 new tests)

TOTAL: 26 new tests added

TIME TO GENERATE: 8 minutes
TIME SAVED vs MANUAL: ~3 hours (95% reduction)

═══════════════════════════════════════════════════

COVERAGE STATUS:
  🎯 Target: 80%
  ✓ ACHIEVED: 89.2%
  📈 Above target by 9.2%

CRITICAL FILES NOW COVERED:
  ✓ paymentService.ts: 45.2% → 91.3% (+46.1%)
  ✓ authService.ts: 67.3% → 88.7% (+21.4%)
  ✓ encryption.ts: 58.9% → 87.2% (+28.3%)

═══════════════════════════════════════════════════

ENFORCEMENT CONFIGURED:
  ✓ Coverage thresholds set in jest.config.js
  ✓ Pre-commit hook installed
  ✓ CI pipeline will fail below 80%
  ✓ Coverage trend tracking enabled

NEXT STEPS:
  1. Review generated tests
  2. Commit new tests
  3. Monitor coverage in CI
  4. Continue improving branch coverage

═══════════════════════════════════════════════════
```

## Usage Examples

**Analyze overall coverage**:

```bash
/testing:coverage
```

**Analyze specific file**:

```bash
/testing:coverage src/services/paymentService.ts
```

**Generate tests for uncovered code**:

```bash
/testing:coverage --generate-missing
```

**Show coverage trend**:

```bash
/testing:coverage --trend
```

**Export coverage report**:

```bash
/testing:coverage --export html
```

## Business Value / ROI

**Risk Mitigation**:

- Uncovered critical code = potential production bugs
- Payment processing bug: $100,000+ in lost revenue
- Security vulnerability: $500,000+ in damages
- **High coverage reduces risk by 70-80%**

**Time Savings**:

- Manual coverage analysis: 2-4 hours
- AI-assisted analysis: 5-10 minutes
- **ROI: 95% time reduction**

**Quality Improvements**:

- Identifies blind spots in testing
- Ensures critical paths are tested
- Catches edge cases
- **Reduces production bugs by 60-80%**

**Developer Confidence**:

- Safe refactoring with high coverage
- Faster iteration cycles
- Less fear of breaking changes
- **30% increase in development velocity**

## Success Metrics

**Coverage Targets**:

- [ ] Line coverage: ≥ 80%
- [ ] Branch coverage: ≥ 75%
- [ ] Function coverage: ≥ 80%
- [ ] Critical files: ≥ 90%

**Coverage Quality**:

- [ ] No false coverage (tests that don't validate behavior)
- [ ] All critical paths tested
- [ ] Error scenarios covered
- [ ] Edge cases tested

**Process Metrics**:

- [ ] Coverage enforced in CI
- [ ] Pre-commit hook prevents low coverage
- [ ] Coverage trend tracked over time
- [ ] Team reviews coverage reports regularly

**Continuous Improvement**:

- [ ] Coverage increases over time
- [ ] New code has 80%+ coverage
- [ ] Legacy code coverage improving
- [ ] No coverage regressions

## Integration with Development Workflow

**During Development**:

- Run coverage locally before committing
- Focus on covering new code
- Review uncovered critical paths

**Code Review**:

- Verify new code has tests
- Check coverage reports in PR
- Ensure no coverage regression

**CI/CD Pipeline**:

- Run coverage on every commit
- Block merge if below threshold
- Track coverage trends
- Report coverage to team dashboard

---

**Model**: Sonnet (intelligent coverage analysis and test generation)
**Estimated time**: 10-20 minutes for full analysis
**Tip**: Focus on critical files first - 80% coverage on critical code is better than 100% on utilities!
