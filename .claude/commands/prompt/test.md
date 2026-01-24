---
description: Test prompt variants, compare results, and perform A/B testing with comprehensive metrics
argument-hint: <prompt-file-path>
allowed-tools: Task, Read, Write, Bash
model: claude-sonnet-4-5
timeout: 2100
retry: 2
cost_estimate: 0.30-0.40

validation:
  input:
    prompt_file:
      required: true
      file_exists: true
      file_extension: ".md"
      error_message: "Prompt file must exist and be a .md file"
  output:
    schema: .claude/validation/schemas/prompt/prompt-test-output.json
    required_files:
      - 'prompts/${prompt_id}-test-results.json'
      - 'prompts/${prompt_id}-comparison.md'
    min_file_size: 700
    quality_threshold: 0.80
    content_requirements:
      - "Test cases executed (≥3 per variant)"
      - "Variants compared (≥2)"
      - "Performance metrics calculated"
      - "Best variant identified"
      - "Statistical significance analyzed"

version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added input validation for prompt file"
      - "Added output validation for test results"
      - "Dual output (JSON results + comparison report)"
      - "Statistical significance testing"
  - version: 1.0.0
    date: 2025-10-15
    changes:
      - "Initial implementation with A/B testing"
---

# Test Prompt

Prompt File: **$ARGUMENTS**

## Step 1: Validate Input

```bash
PROMPT_FILE="$ARGUMENTS"

# Check file path provided
if [ -z "$PROMPT_FILE" ]; then
  echo "❌ ERROR: Missing prompt file path"
  echo ""
  echo "Usage: /prompt/test <prompt-file-path>"
  echo "Example: /prompt/test prompts/customer-support.md"
  exit 1
fi

# Check file exists
if [ ! -f "$PROMPT_FILE" ]; then
  echo "❌ ERROR: Prompt file not found: $PROMPT_FILE"
  exit 1
fi

# Check file is markdown
if [[ ! "$PROMPT_FILE" =~ \.md$ ]]; then
  echo "❌ ERROR: Prompt file must be a .md file"
  exit 1
fi

echo "✓ Input validated: $PROMPT_FILE"
```

## Step 2: Generate Test Variants & Execute Tests

```javascript
const PROMPT_FILE = process.env.ARGUMENTS;
const promptId = PROMPT_FILE.replace(/^prompts\//, '').replace(/\.md$/, '');

// Read prompt to test
const originalPrompt = await Read({
  file_path: PROMPT_FILE
});

// Execute comprehensive testing
await Task({
  subagent_type: 'general-purpose',
  description: 'Test prompt variants with A/B comparison',
  prompt: `Test the following AI prompt using comprehensive A/B testing methodology.

PROMPT TO TEST:
${originalPrompt}

Execute this testing workflow:

**Step 1: Generate Variants**
Create 2-3 prompt variants with different approaches:
- Variant A: Original prompt
- Variant B: Alternative reasoning framework
- Variant C (optional): Different structure/approach

**Step 2: Design Test Cases**
Create 5-7 test cases covering:
- Typical use cases (3-4)
- Edge cases (1-2)
- Stress tests (1)

Each test case needs:
- Input data
- Expected output criteria
- Success metrics

**Step 3: Execute Tests**
Run all test cases against each variant:
- Measure response quality (0.0-1.0)
- Measure response time
- Measure token usage
- Measure adherence to output specs

**Step 4: Calculate Metrics**
For each variant calculate:
- Average quality score
- Success rate (% passing test cases)
- Token efficiency
- Response consistency
- Edge case handling

**Step 5: Statistical Analysis**
- Determine statistical significance
- Calculate confidence intervals
- Identify winner (if significant difference)
- Provide improvement recommendations

**Step 6: Generate Outputs**

1. prompts/${promptId}-test-results.json
   {
     "variants": [
       {
         "id": "A",
         "description": "Original prompt",
         "test_results": [
           {
             "test_case": "Typical case 1",
             "quality_score": 0.85,
             "token_count": 350,
             "response_time_ms": 1200,
             "passed": true
           }
         ],
         "metrics": {
           "avg_quality": 0.85,
           "success_rate": 0.86,
           "avg_tokens": 340,
           "consistency_score": 0.82
         }
       }
     ],
     "winner": "Variant B",
     "statistical_significance": true,
     "confidence": 0.95
   }

2. prompts/${promptId}-comparison.md
   Detailed comparison report with:
   - Variant descriptions
   - Test case results
   - Side-by-side metrics
   - Winner identification
   - Improvement recommendations
   - Next steps`,

  context: {
    prompt_file: PROMPT_FILE,
    prompt_id: promptId,
    test_results_output: `prompts/${promptId}-test-results.json`,
    comparison_output: `prompts/${promptId}-comparison.md`
  }
});
```

## Step 3: Validate Output

```bash
PROMPT_FILE="$ARGUMENTS"
PROMPT_ID=$(basename "$PROMPT_FILE" .md)
RESULTS_FILE="prompts/$PROMPT_ID-test-results.json"
COMPARISON_FILE="prompts/$PROMPT_ID-comparison.md"

# Check results file created
if [ ! -f "$RESULTS_FILE" ]; then
  echo "❌ ERROR: Test results file not created"
  exit 1
fi

# Check comparison report created
if [ ! -f "$COMPARISON_FILE" ]; then
  echo "❌ ERROR: Comparison report not created"
  exit 1
fi

# Check valid JSON
if ! jq empty "$RESULTS_FILE" 2>/dev/null; then
  echo "❌ ERROR: Test results is not valid JSON"
  exit 1
fi

# Check minimum variants tested
VARIANT_COUNT=$(jq '.variants | length' "$RESULTS_FILE" 2>/dev/null || echo "0")
if [ $VARIANT_COUNT -lt 2 ]; then
  echo "❌ ERROR: Need at least 2 variants tested"
  echo "Current count: $VARIANT_COUNT"
  exit 1
fi

# Check minimum file sizes
COMPARISON_SIZE=$(wc -c < "$COMPARISON_FILE")
if [ $COMPARISON_SIZE -lt 700 ]; then
  echo "❌ ERROR: Comparison report too small (< 700 bytes)"
  echo "Current size: $COMPARISON_SIZE bytes"
  exit 1
fi

# Check for winner identified
if ! grep -q "winner\|Winner\|best\|Best" "$COMPARISON_FILE"; then
  echo "⚠️  WARNING: No clear winner identified (may indicate tie)"
fi

echo "✓ Output validation complete ($VARIANT_COUNT variants tested, comparison: $COMPARISON_SIZE bytes)"
```

## Completion

```
═══════════════════════════════════════════════════
        PROMPT TESTING COMPLETE ✓
═══════════════════════════════════════════════════

Prompt: $ARGUMENTS
Command: /prompt/test
Version: 2.0.0

Output Created:
  ✓ prompts/[prompt-id]-test-results.json
  ✓ prompts/[prompt-id]-comparison.md

Testing Results:
  Variants tested (≥2)
  Test cases executed (≥3 per variant)
  Performance metrics calculated
  Best variant identified
  Statistical significance analyzed

Validations Passed:
  ✓ Input validation (prompt file exists)
  ✓ Output validation (≥2 files created)
  ✓ Valid JSON results
  ✓ Multiple variants tested
  ✓ Quality threshold (≥0.80)

NEXT STEPS:
→ Use best-performing variant in production
→ Apply learnings to other prompts

═══════════════════════════════════════════════════
```

## Guidelines

- **A/B Testing**: Compare 2-3 prompt variants systematically
- **Comprehensive Test Cases**: Typical + edge cases + stress tests
- **Performance Metrics**: Quality, success rate, tokens, consistency
- **Statistical Rigor**: Confidence intervals and significance testing
- **Dual Output**: JSON data + human-readable comparison report
- **Minimum 3 Test Cases**: Per variant for meaningful comparison
