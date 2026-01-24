---
description: Perform mutation testing to validate test quality and effectiveness
argument-hint: [file-path or --report]
model: claude-sonnet-4-5-20250929
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, AskUserQuestion
---

Run mutation testing for: **${ARGUMENTS:-entire project}**

## What This Command Does

Mutation testing validates the quality of your tests by introducing deliberate bugs (mutations) into your code and verifying that your tests catch them. If a mutant survives (tests still pass), it indicates weak or missing test coverage. This command uses AI to perform mutation testing, analyze results, and generate tests that kill surviving mutants.

**Key Capabilities**:

- Introduces code mutations (change operators, values, logic)
- Runs test suite against each mutation
- Identifies surviving mutants (tests didn't catch the bug)
- Calculates mutation score (killed / total mutants)
- Generates tests to kill surviving mutants
- Improves test effectiveness, not just coverage

## Step 1: Detect Mutation Testing Framework

**Check for mutation testing tools**:

```bash
# JavaScript/TypeScript
if grep -q "stryker" package.json; then
  FRAMEWORK="stryker"
  echo "Using Stryker Mutator"
elif grep -q "@stryker-mutator" package.json; then
  FRAMEWORK="stryker"
  echo "Using Stryker Mutator"

# Python
elif grep -q "mutpy\|cosmic-ray\|mutmut" requirements.txt; then
  FRAMEWORK="mutpy"
  echo "Using mutation testing for Python"

# Java
elif grep -q "pitest" pom.xml; then
  FRAMEWORK="pitest"
  echo "Using PITest"

else
  echo "No mutation testing framework detected."
  echo "Would you like to install one?"
  echo "1) Stryker (JavaScript/TypeScript) - Recommended"
  echo "2) MutPy (Python)"
  echo "3) PITest (Java)"

  # Install Stryker for JS/TS projects
  npm install -D @stryker-mutator/core @stryker-mutator/jest-runner
  npx stryker init
fi
```

## Step 2: Configure Mutation Testing

**Create Stryker configuration**:

```javascript
// stryker.conf.json
{
  "mutator": {
    "plugins": ["@stryker-mutator/jest-runner"],
    "excludedMutations": [
      "StringLiteral",  // Don't mutate string literals (usually logging)
      "ObjectLiteral"   // Don't mutate object literals
    ]
  },
  "testRunner": "jest",
  "coverageAnalysis": "perTest",
  "mutate": [
    "src/**/*.ts",
    "!src/**/*.test.ts",
    "!src/**/*.spec.ts",
    "!src/generated/**"
  ],
  "thresholds": {
    "high": 80,    // Excellent mutation score
    "low": 60,     // Minimum acceptable
    "break": 50    // Fail build if below this
  },
  "timeoutMS": 60000,
  "concurrency": 4,
  "reporters": ["html", "clear-text", "progress", "json"]
}
```

## Step 3: Understanding Mutation Types

**Common mutation operators**:

### 3a. Arithmetic Operators

```javascript
// Original
const total = price + tax

// Mutant 1: Change + to -
const total = price - tax

// Mutant 2: Change + to *
const total = price * tax

// Mutant 3: Change + to /
const total = price / tax
```

### 3b. Relational Operators

```javascript
// Original
if (age >= 18) {
  return 'adult'
}

// Mutant 1: Change >= to >
if (age > 18) {
  return 'adult'
}

// Mutant 2: Change >= to <=
if (age <= 18) {
  return 'adult'
}

// Mutant 3: Change >= to ==
if (age == 18) {
  return 'adult'
}
```

### 3c. Logical Operators

```javascript
// Original
if (isLoggedIn && hasPermission) {
  grantAccess()
}

// Mutant 1: Change && to ||
if (isLoggedIn || hasPermission) {
  grantAccess()
}

// Mutant 2: Remove first condition
if (hasPermission) {
  grantAccess()
}
```

### 3d. Conditional Boundaries

```javascript
// Original
if (count > 0) {
  process()
}

// Mutant 1: Change > to >=
if (count >= 0) {
  process()
}

// Mutant 2: Negate condition
if (count <= 0) {
  process()
}
```

### 3e. Return Values

```javascript
// Original
function isValid() {
  return true
}

// Mutant: Flip return value
function isValid() {
  return false
}
```

### 3f. Array/Object Mutations

```javascript
// Original
const items = array.filter(x => x > 0)

// Mutant 1: Change filter to map
const items = array.map(x => x > 0)

// Mutant 2: Empty array
const items = []
```

## Step 4: Run Mutation Testing

**Execute mutation testing**:

```bash
echo "Running mutation testing..."
echo "This may take several minutes..."

# Stryker (JavaScript/TypeScript)
npx stryker run

# MutPy (Python)
mutpy --target src/ --unit-test tests/ --report html

# PITest (Java)
mvn org.pitest:pitest-maven:mutationCoverage

# Save results
REPORT_DIR="reports/mutation"
mkdir -p "$REPORT_DIR"
```

## Step 5: Analyze Mutation Results

**Parse mutation report**:

```javascript
const mutationReport = await Read({
  file_path: 'reports/mutation/mutation-report.json'
})

const report = JSON.parse(mutationReport)

// Calculate mutation score
const stats = {
  totalMutants: 0,
  killed: 0,        // Tests caught the mutation
  survived: 0,      // Tests didn't catch the mutation (BAD)
  timeout: 0,       // Mutation caused infinite loop
  noCoverage: 0,    // No tests run for this code
  error: 0          // Mutation caused compilation/runtime error
}

// Analyze each file
const fileResults = {}

for (const [filePath, mutations] of Object.entries(report.files)) {
  fileResults[filePath] = {
    score: 0,
    killed: 0,
    survived: 0,
    survivingMutants: []
  }

  for (const mutation of mutations.mutants) {
    stats.totalMutants++

    switch (mutation.status) {
      case 'Killed':
        stats.killed++
        fileResults[filePath].killed++
        break
      case 'Survived':
        stats.survived++
        fileResults[filePath].survived++
        fileResults[filePath].survivingMutants.push(mutation)
        break
      case 'Timeout':
        stats.timeout++
        break
      case 'NoCoverage':
        stats.noCoverage++
        break
      case 'CompileError':
      case 'RuntimeError':
        stats.error++
        break
    }
  }

  // Calculate mutation score for file
  const total = fileResults[filePath].killed + fileResults[filePath].survived
  fileResults[filePath].score = (fileResults[filePath].killed / total) * 100
}

// Calculate overall mutation score
const overallScore = (stats.killed / (stats.killed + stats.survived)) * 100
```

## Step 6: Display Mutation Testing Report

```
═══════════════════════════════════════════════════
          MUTATION TESTING REPORT
═══════════════════════════════════════════════════

MUTATION SCORE: 76.3%  ███████▓░░

Interpretation:
  🟢 Excellent: 80%+  - Very strong tests
  🟡 Good: 60-80%     - Decent test quality
  🔴 Poor: < 60%      - Weak tests, needs improvement

YOUR SCORE: 76.3% (GOOD)  🟡
Target: 80%+
Gap: -3.7%

═══════════════════════════════════════════════════

MUTATION STATISTICS:

  Total Mutants Created:      325
  ✓ Killed (tests caught):    248  (76.3%)
  ✗ Survived (tests missed):  52   (16.0%)
  ⏱ Timeout:                  15   (4.6%)
  ⊘ No Coverage:              8    (2.5%)
  ⚠ Error:                    2    (0.6%)

EFFECTIVENESS:
  ✓ Your tests caught 76.3% of intentional bugs
  ✗ Your tests missed 16.0% of intentional bugs

═══════════════════════════════════════════════════

RESULTS BY FILE:

  🔴 WEAK TEST COVERAGE (< 60%):

     1. src/services/paymentService.ts
        Score: 45.2%  ████▓░░░░░
        Killed: 19 | Survived: 23
        Critical: HIGH - Payment processing
        Action: URGENT - Strengthen tests

     2. src/utils/validator.ts
        Score: 58.3%  █████▓░░░░
        Killed: 35 | Survived: 25
        Critical: MEDIUM - Input validation
        Action: Add edge case tests

  🟡 MODERATE TEST COVERAGE (60-80%):

     3. src/services/userService.ts
        Score: 72.1%  ███████░░░
        Killed: 52 | Survived: 20
        Critical: MEDIUM - User management
        Action: Improve boundary tests

     4. src/controllers/orderController.ts
        Score: 68.5%  ██████▓░░░
        Killed: 48 | Survived: 22
        Critical: HIGH - Order processing
        Action: Add error scenario tests

  🟢 STRONG TEST COVERAGE (80%+):

     5. src/middleware/auth.ts
        Score: 91.3%  █████████░
        Killed: 63 | Survived: 6
        Critical: HIGH - Authentication
        Status: Excellent test quality

     6. src/models/user.ts
        Score: 88.7%  ████████▓░
        Killed: 71 | Survived: 9
        Critical: MEDIUM - Data models
        Status: Very good test quality

═══════════════════════════════════════════════════

SURVIVING MUTANTS (Tests need improvement):

  📍 src/services/paymentService.ts

     Mutant #1: Line 47 (SURVIVED)
     Original:  if (amount > 0)
     Mutated:   if (amount >= 0)
     Why it survived: No test checks amount === 0 edge case

     Mutant #2: Line 52 (SURVIVED)
     Original:  status = 'completed'
     Mutated:   status = 'pending'
     Why it survived: Tests don't verify exact status value

     Mutant #3: Line 67 (SURVIVED)
     Original:  return result.data
     Mutated:   return null
     Why it survived: No test validates return value

     ... (20 more surviving mutants)

  📍 src/utils/validator.ts

     Mutant #4: Line 23 (SURVIVED)
     Original:  return email.includes('@')
     Mutated:   return true
     Why it survived: Tests don't check invalid emails

     Mutant #5: Line 28 (SURVIVED)
     Original:  if (password.length >= 8)
     Mutated:   if (password.length > 8)
     Why it survived: No test for exactly 8 characters

     ... (22 more surviving mutants)

═══════════════════════════════════════════════════

MUTATION TYPES BREAKDOWN:

  Conditional Boundary:   85 mutants (72% killed)
  Relational Operator:    67 mutants (78% killed)
  Logical Operator:       52 mutants (81% killed)
  Arithmetic Operator:    43 mutants (69% killed)
  Return Value:           38 mutants (74% killed)
  Boolean Literal:        25 mutants (88% killed)
  String Literal:         15 mutants (60% killed)

═══════════════════════════════════════════════════

RECOMMENDATIONS:

  🎯 Priority Actions:

     1. Fix paymentService.ts (23 surviving mutants)
        - Add boundary tests (amount === 0, amount < 0)
        - Verify exact return values
        - Test all status transitions

     2. Fix validator.ts (25 surviving mutants)
        - Test invalid inputs
        - Test boundary conditions (length === 8)
        - Add negative test cases

     3. Strengthen orderController.ts (22 surviving mutants)
        - Add error scenario tests
        - Test all conditional branches
        - Verify side effects

  📊 Quick Wins (High impact, low effort):

     • Add 3 boundary tests → Kill 15 mutants → +4.6% score
     • Add 5 negative tests → Kill 12 mutants → +3.7% score
     • Verify return values → Kill 8 mutants → +2.5% score

     Expected improvement: +10.8% → 87.1% mutation score

═══════════════════════════════════════════════════

WOULD YOU LIKE TO AUTO-GENERATE TESTS?

Options:
  [1] Generate tests to kill ALL surviving mutants
  [2] Generate tests for specific file
  [3] Generate tests for critical files only
  [4] Show detailed analysis for specific mutant
  [5] Export mutation report (HTML, JSON)
  [6] Exit

Select option: _
```

## Step 7: Generate Tests to Kill Mutants

**AI-assisted test generation for surviving mutants**:

```javascript
async function generateMutantKillingTests(file, survivingMutants) {
  // Read source file
  const sourceCode = await Read({ file_path: file })

  // Read existing tests
  const testFile = file.replace(/\.ts$/, '.test.ts')
  const existingTests = await Read({ file_path: testFile })

  // Generate tests for each surviving mutant
  for (const mutant of survivingMutants) {
    const prompt = `
Generate a test that would kill this surviving mutant:

FILE: ${file}
LINE: ${mutant.location.start.line}

ORIGINAL CODE:
${mutant.originalCode}

MUTATED CODE:
${mutant.mutatedCode}

MUTATION TYPE: ${mutant.mutatorName}

WHY IT SURVIVED:
${analyzeSurvival(mutant)}

EXISTING TESTS:
\`\`\`typescript
${existingTests}
\`\`\`

Please generate a test that:
1. Would PASS with the original code
2. Would FAIL with the mutated code
3. Specifically targets this mutation
4. Follows existing test patterns
5. Has a descriptive name explaining what it tests

Example structure:
\`\`\`typescript
it('should reject payment when amount is exactly zero', () => {
  // This test would kill the mutant that changes > to >=
  const result = processPayment({ amount: 0 })
  expect(result.status).toBe('rejected')
  expect(result.error).toContain('Amount must be positive')
})
\`\`\`
    `

    const newTest = await generateWithAI(prompt)

    // Add to test file
    await Edit({
      file_path: testFile,
      old_string: '})  // End of test suite',
      new_string: `
  ${newTest}
})  // End of test suite`
    })
  }
}

function analyzeSurvival(mutant) {
  // Analyze why mutant survived
  switch (mutant.mutatorName) {
    case 'ConditionalBoundary':
      return 'Tests likely don\'t check the exact boundary condition'
    case 'RelationalOperator':
      return 'Tests may only check one side of the condition'
    case 'LogicalOperator':
      return 'Tests don\'t verify both conditions independently'
    case 'ReturnValue':
      return 'Tests don\'t verify the exact return value'
    case 'BooleanLiteral':
      return 'Tests don\'t check both true and false cases'
    default:
      return 'Tests don\'t adequately cover this code path'
  }
}
```

## Step 8: Re-run Mutation Testing

**Verify improvements**:

```bash
echo "Re-running mutation testing with new tests..."

# Run mutation testing again
npx stryker run

# Compare results
echo "BEFORE: Mutation score: ${BEFORE_SCORE}%"
echo "AFTER:  Mutation score: ${AFTER_SCORE}%"
echo "IMPROVEMENT: +$(bc <<< "$AFTER_SCORE - $BEFORE_SCORE")%"

# Check if target reached
if (( $(bc <<< "$AFTER_SCORE >= 80") )); then
  echo "✓ Target mutation score (80%) achieved!"
else
  echo "⚠ Mutation score still below target. Continue improving tests."
fi
```

## Step 9: Set Up Mutation Testing in CI

**Add to CI pipeline**:

```yaml
# .github/workflows/mutation-testing.yml
name: Mutation Testing

on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * 0'  # Run weekly on Sunday at 2 AM

jobs:
  mutation-testing:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Run mutation testing
        run: npx stryker run

      - name: Check mutation score threshold
        run: |
          SCORE=$(jq '.metrics.mutationScore' reports/mutation/mutation-report.json)
          if (( $(bc <<< "$SCORE < 80") )); then
            echo "❌ Mutation score below threshold: $SCORE%"
            exit 1
          fi
          echo "✓ Mutation score: $SCORE%"

      - name: Upload mutation report
        uses: actions/upload-artifact@v3
        with:
          name: mutation-report
          path: reports/mutation/

      - name: Comment on PR
        uses: actions/github-script@v6
        with:
          script: |
            const report = require('./reports/mutation/mutation-report.json')
            const comment = `
            ## Mutation Testing Results

            **Mutation Score:** ${report.metrics.mutationScore}%
            **Mutants Killed:** ${report.metrics.killed}
            **Mutants Survived:** ${report.metrics.survived}

            ${report.metrics.mutationScore >= 80 ? '✅ Passed' : '❌ Below threshold (80%)'}
            `

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            })
```

## Step 10: Final Report

```
═══════════════════════════════════════════════════
        MUTATION TESTING IMPROVEMENT SUMMARY
═══════════════════════════════════════════════════

BEFORE:
  Mutation Score: 76.3%
  Killed: 248 / 325
  Survived: 52

AFTER:
  Mutation Score: 85.7% (+9.4%)  ✓
  Killed: 293 / 325
  Survived: 7

IMPROVEMENT:
  ✓ Killed 45 additional mutants
  ✓ Reduced surviving mutants by 86.5%
  ✓ Exceeded target (80%) by 5.7%

═══════════════════════════════════════════════════

TESTS GENERATED:
  ✓ paymentService.test.ts (+18 tests)
  ✓ validator.test.ts (+15 tests)
  ✓ orderController.test.ts (+12 tests)

TOTAL: 45 new mutation-killing tests

TIME TO GENERATE: 25 minutes
TIME SAVED vs MANUAL: ~6 hours (93% reduction)

═══════════════════════════════════════════════════

REMAINING WORK:

  7 surviving mutants remain:
  • 3 in error handling (non-critical)
  • 2 in logging (cosmetic)
  • 2 in edge cases (low risk)

  Recommended: Address in future iteration

═══════════════════════════════════════════════════

CI/CD INTEGRATION:
  ✓ Mutation testing configured
  ✓ Runs weekly and on PRs
  ✓ Blocks merge if score < 80%
  ✓ Reports to PR comments

═══════════════════════════════════════════════════
```

## Usage Examples

**Run mutation testing on entire project**:

```bash
/testing:mutation
```

**Run on specific file**:

```bash
/testing:mutation src/services/paymentService.ts
```

**Generate report only**:

```bash
/testing:mutation --report
```

**Generate tests for surviving mutants**:

```bash
/testing:mutation --fix-survivors
```

## Business Value / ROI

**Test Quality Assurance**:

- 80% code coverage doesn't mean 80% test quality
- Mutation testing validates test effectiveness
- **Finds weak tests that give false confidence**

**Cost of Weak Tests**:

- False confidence leads to production bugs
- Production bug: $10,000-$100,000+
- Weak tests: illusion of safety
- **Mutation testing reveals true test quality**

**Time Savings**:

- Manual mutation analysis: 8-16 hours
- AI-assisted mutation testing: 30-60 minutes
- **ROI: 95% time reduction**

**Quality Improvements**:

- Identifies exactly where tests are weak
- Generates targeted tests that catch bugs
- Improves overall code quality
- **Reduces production bugs by 70-85%**

## Success Metrics

**Mutation Score Targets**:

- [ ] Overall score: ≥ 80%
- [ ] Critical files: ≥ 90%
- [ ] No surviving mutants in payment/auth code
- [ ] Score improves over time

**Test Quality**:

- [ ] Tests catch intentional bugs
- [ ] No false sense of security from coverage
- [ ] Boundary conditions tested
- [ ] Error scenarios validated

**Process Integration**:

- [ ] Mutation testing in CI pipeline
- [ ] Score tracked over time
- [ ] Team reviews mutation reports
- [ ] Surviving mutants prioritized in backlog

---

**Model**: Sonnet (complex mutation analysis and test generation)
**Estimated time**: 30-60 minutes for full analysis
**Tip**: Mutation testing is expensive - run on critical code first, then expand!
