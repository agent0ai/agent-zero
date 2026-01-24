---
description: Generate unit tests for functions/classes with AI assistance
argument-hint: [file-path or function-name]
model: claude-sonnet-4-5-20250929
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, AskUserQuestion
---

Generate unit tests for: **${ARGUMENTS}**

## What This Command Does

This command analyzes your code and automatically generates comprehensive unit tests for functions, classes, and methods. It uses AI to understand your code's behavior, identify edge cases, and create meaningful test coverage that follows testing best practices.

**Key Capabilities**:

- Analyzes function/class logic and generates appropriate test cases
- Identifies edge cases, boundary conditions, and error scenarios
- Creates mock/stub configurations for dependencies
- Follows project's existing test patterns and conventions
- Generates both positive and negative test cases
- Includes setup/teardown when needed

## Step 1: Identify Target Code

Parse arguments to determine what to test:

```bash
# If file path provided
if [[ "$ARGUMENTS" == *.* ]]; then
  TARGET_FILE="$ARGUMENTS"
  echo "Generating tests for file: $TARGET_FILE"

# If function/class name provided
else
  TARGET_NAME="$ARGUMENTS"
  echo "Searching for: $TARGET_NAME"

  # Search codebase for function/class
  grep -r "function $TARGET_NAME" . --include="*.js" --include="*.ts"
  grep -r "class $TARGET_NAME" . --include="*.js" --include="*.ts"
  grep -r "const $TARGET_NAME" . --include="*.js" --include="*.ts"
fi
```

## Step 2: Read and Analyze Target Code

**Read the implementation**:

```javascript
const targetCode = await Read({
  file_path: targetFile
})
```

**Analyze code structure**:

- Function signatures and parameters
- Return types and values
- Dependencies and imports
- Error handling patterns
- State management (if class)
- Side effects (API calls, file I/O, etc.)

## Step 3: Determine Test Framework

**Detect project's test framework**:

```bash
# Check package.json for test framework
if grep -q "jest" package.json; then
  FRAMEWORK="jest"
elif grep -q "vitest" package.json; then
  FRAMEWORK="vitest"
elif grep -q "mocha" package.json; then
  FRAMEWORK="mocha"
elif grep -q "pytest" pyproject.toml; then
  FRAMEWORK="pytest"
else
  # Ask user to select
  echo "Test framework not detected. Please select:"
  echo "1) Jest"
  echo "2) Vitest"
  echo "3) Mocha + Chai"
  echo "4) pytest"
fi
```

## Step 4: Identify Test Patterns

**Find existing tests to match style**:

```bash
# Look for existing test files
find . -name "*.test.ts" -o -name "*.test.js" -o -name "*.spec.ts" | head -3

# Read one example to understand patterns
cat path/to/existing.test.ts | head -50
```

**Extract patterns**:

- Naming conventions (describe/it vs test)
- Assertion style (expect vs assert)
- Mock/stub approach
- Setup/teardown patterns
- File organization

## Step 5: Generate Test Cases

**Create comprehensive test suite**:

### 5a. Happy Path Tests

Test normal execution with valid inputs:

```typescript
describe('calculateTotal', () => {
  it('should calculate total for valid items', () => {
    const items = [
      { price: 10, quantity: 2 },
      { price: 5, quantity: 3 }
    ]
    const result = calculateTotal(items)
    expect(result).toBe(35)
  })

  it('should handle empty array', () => {
    const result = calculateTotal([])
    expect(result).toBe(0)
  })
})
```

### 5b. Edge Cases

Test boundary conditions:

```typescript
describe('Edge Cases', () => {
  it('should handle single item', () => {
    const items = [{ price: 10, quantity: 1 }]
    expect(calculateTotal(items)).toBe(10)
  })

  it('should handle zero price', () => {
    const items = [{ price: 0, quantity: 5 }]
    expect(calculateTotal(items)).toBe(0)
  })

  it('should handle large quantities', () => {
    const items = [{ price: 1, quantity: 1000000 }]
    expect(calculateTotal(items)).toBe(1000000)
  })

  it('should handle decimal prices', () => {
    const items = [{ price: 10.99, quantity: 2 }]
    expect(calculateTotal(items)).toBe(21.98)
  })
})
```

### 5c. Error Cases

Test invalid inputs and error handling:

```typescript
describe('Error Handling', () => {
  it('should throw error for null input', () => {
    expect(() => calculateTotal(null)).toThrow('Items cannot be null')
  })

  it('should throw error for invalid item structure', () => {
    const items = [{ price: 10 }] // missing quantity
    expect(() => calculateTotal(items)).toThrow('Invalid item structure')
  })

  it('should throw error for negative price', () => {
    const items = [{ price: -10, quantity: 2 }]
    expect(() => calculateTotal(items)).toThrow('Price must be positive')
  })
})
```

### 5d. Mock Dependencies

Test with mocked external dependencies:

```typescript
describe('with mocked dependencies', () => {
  let mockDatabase: jest.Mocked<Database>

  beforeEach(() => {
    mockDatabase = {
      getItems: jest.fn(),
      saveTotal: jest.fn()
    }
  })

  it('should fetch items from database', async () => {
    mockDatabase.getItems.mockResolvedValue([
      { price: 10, quantity: 2 }
    ])

    const result = await calculateTotalFromDB(mockDatabase)

    expect(mockDatabase.getItems).toHaveBeenCalledTimes(1)
    expect(result).toBe(20)
  })

  it('should handle database errors', async () => {
    mockDatabase.getItems.mockRejectedValue(new Error('DB Error'))

    await expect(calculateTotalFromDB(mockDatabase))
      .rejects.toThrow('DB Error')
  })
})
```

## Step 6: AI-Assisted Test Generation

**Use AI to generate tests**:

```javascript
const prompt = `
Analyze this code and generate comprehensive unit tests:

FILE: ${targetFile}
\`\`\`${fileExtension}
${targetCode}
\`\`\`

FRAMEWORK: ${testFramework}

Please generate unit tests that cover:
1. Happy path scenarios (valid inputs, expected outputs)
2. Edge cases (boundary conditions, empty/null values)
3. Error scenarios (invalid inputs, exceptions)
4. Mock configurations for dependencies
5. Async behavior (if applicable)

Follow these conventions from existing tests:
${existingTestPatterns}

Requirements:
- Use descriptive test names that explain what is being tested
- Group related tests with describe blocks
- Include setup/teardown if needed
- Add comments explaining complex test scenarios
- Aim for high coverage of code paths
- Test both positive and negative cases
`

// Generate tests using AI
const generatedTests = await generateWithAI(prompt)
```

## Step 7: Create Test File

**Determine test file path**:

```bash
# Convert implementation path to test path
# src/utils/calculator.ts → src/utils/calculator.test.ts
# lib/services/api.js → lib/services/api.spec.js

SOURCE_FILE="src/utils/calculator.ts"
TEST_FILE="${SOURCE_FILE%.ts}.test.ts"
```

**Write test file**:

```javascript
await Write({
  file_path: testFilePath,
  content: generatedTests
})
```

## Step 8: Validate Generated Tests

**Run generated tests**:

```bash
# Run just the new test file
npm test -- calculator.test.ts

# Or with pytest
pytest tests/test_calculator.py -v
```

**Check for issues**:

- Syntax errors
- Import errors
- Failed assertions
- Missing mocks

## Step 9: Refine Tests

**If tests fail, analyze and fix**:

```javascript
// Read test output
const testOutput = /* capture from previous run */

// Identify issues
const issues = parseTestFailures(testOutput)

// For each issue, fix the test
for (const issue of issues) {
  if (issue.type === 'import_error') {
    // Fix import statements
    await Edit({
      file_path: testFile,
      old_string: issue.badImport,
      new_string: issue.fixedImport
    })
  }

  if (issue.type === 'assertion_error') {
    // Adjust expectations
    console.log(`Test expects ${issue.expected} but got ${issue.actual}`)
    // Update test assertion
  }

  if (issue.type === 'mock_error') {
    // Fix mock configuration
    console.log('Mock not properly configured:', issue.mock)
  }
}
```

## Step 10: Generate Test Report

**Display comprehensive summary**:

```
═══════════════════════════════════════════════════
            UNIT TEST GENERATION REPORT
═══════════════════════════════════════════════════

TARGET FILE:
  src/utils/calculator.ts

TEST FILE CREATED:
  src/utils/calculator.test.ts

TEST SUITE SUMMARY:
  ✓ 12 test cases generated
  ✓ 4 describe blocks (organized by scenario)
  ✓ 3 edge cases covered
  ✓ 2 error scenarios tested
  ✓ Dependencies mocked (2 mocks)

TEST BREAKDOWN:

  1. Happy Path Tests (5 tests)
     ✓ should calculate total for valid items
     ✓ should handle empty array
     ✓ should handle single item
     ✓ should calculate with multiple items
     ✓ should preserve decimal precision

  2. Edge Cases (3 tests)
     ✓ should handle zero price
     ✓ should handle large quantities
     ✓ should handle decimal prices

  3. Error Handling (2 tests)
     ✓ should throw for null input
     ✓ should throw for negative price

  4. Async Operations (2 tests)
     ✓ should fetch items from database
     ✓ should handle database errors

COVERAGE ESTIMATE:
  Lines: 94%
  Branches: 88%
  Functions: 100%

TEST RESULTS:
  ✓ All 12 tests passing
  ⏱ Duration: 0.342s

═══════════════════════════════════════════════════

NEXT STEPS:

1. Review generated tests:
   code src/utils/calculator.test.ts

2. Run tests in watch mode:
   npm test -- --watch calculator.test.ts

3. Check coverage:
   npm test -- --coverage calculator.test.ts

4. Add to CI/CD pipeline:
   Ensure test file is committed and runs in CI

═══════════════════════════════════════════════════
```

## Usage Examples

**Generate tests for specific file**:

```bash
/testing:unit src/utils/validator.ts
```

**Generate tests for function by name**:

```bash
/testing:unit calculateTotal
```

**Generate tests for entire class**:

```bash
/testing:unit UserService
```

**Generate tests for module**:

```bash
/testing:unit src/services/auth/
```

## Business Value / ROI

**Time Savings**:

- Manual test writing: 2-4 hours per module
- AI-assisted generation: 5-15 minutes per module
- **ROI: 90% time reduction**

**Quality Improvements**:

- Identifies edge cases developers might miss
- Ensures consistent test patterns across codebase
- Catches bugs before production
- **Reduces post-release bugs by 60-80%**

**Cost Savings**:

- Production bug fix cost: $5,000-$50,000
- Unit test cost: $100-$500 (AI-assisted)
- **ROI: 10-500x cost avoidance**

**Developer Productivity**:

- Developers can focus on complex logic
- Faster iteration cycles
- More confidence in refactoring
- **30% increase in feature velocity**

## Success Metrics

**Test Quality**:

- [ ] Tests cover happy path scenarios
- [ ] Edge cases are tested
- [ ] Error handling is validated
- [ ] Dependencies are properly mocked
- [ ] Tests are readable and maintainable

**Coverage Targets**:

- [ ] Line coverage: ≥ 80%
- [ ] Branch coverage: ≥ 75%
- [ ] Function coverage: 100%
- [ ] No false positives (tests that pass but don't validate behavior)

**Test Execution**:

- [ ] All generated tests pass
- [ ] Tests run in < 5 seconds (unit tests should be fast)
- [ ] No flaky tests (run 5 times, all pass)
- [ ] Tests are isolated (can run in any order)

**Maintainability**:

- [ ] Test names clearly describe what is tested
- [ ] Tests follow project conventions
- [ ] Tests are organized logically (describe blocks)
- [ ] Complex scenarios have explanatory comments

## Integration with Development Workflow

This command integrates with:

**During Development**:

- `/dev:implement` → **`/testing:unit`** → `/dev:test`
- Generate tests as you write code (TDD approach)

**Code Review**:

- Ensure new code has corresponding unit tests
- Verify test quality meets standards

**CI/CD Pipeline**:

- Unit tests run on every commit
- Block merge if tests fail
- Track coverage trends over time

---

**Model**: Sonnet (intelligent test generation and analysis)
**Estimated time**: 5-15 minutes per file
**Tip**: Generate tests as you code for true TDD workflow!
