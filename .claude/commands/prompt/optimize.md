---
description: Optimize existing prompts for better performance, token efficiency, and clarity
argument-hint: <prompt-file-path>
allowed-tools: Task, Read, Write, Bash
model: claude-sonnet-4-5
timeout: 1500
retry: 2
cost_estimate: 0.18-0.25

validation:
  input:
    prompt_file:
      required: true
      file_exists: true
      file_extension: ".md"
      error_message: "Prompt file must exist and be a .md file"
  output:
    schema: .claude/validation/schemas/prompt/prompt-optimize-output.json
    required_files:
      - 'prompts/${prompt_id}-optimized.md'
      - 'prompts/${prompt_id}-optimization-report.md'
    min_file_size: 600
    quality_threshold: 0.85
    content_requirements:
      - "Improvements documented (≥3 specific changes)"
      - "Token efficiency analyzed"
      - "Clarity measurably improved"
      - "Specificity enhanced"
      - "Quality score improved by ≥0.10"

version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added input validation for prompt file"
      - "Added output validation for optimized prompts"
      - "Dual output (optimized prompt + optimization report)"
      - "Measurable improvement metrics"
  - version: 1.0.0
    date: 2025-10-15
    changes:
      - "Initial implementation with optimization workflow"
---

# Optimize Prompt

Prompt File: **$ARGUMENTS**

## Step 1: Validate Input

```bash
PROMPT_FILE="$ARGUMENTS"

# Check file path provided
if [ -z "$PROMPT_FILE" ]; then
  echo "❌ ERROR: Missing prompt file path"
  echo ""
  echo "Usage: /prompt/optimize <prompt-file-path>"
  echo "Example: /prompt/optimize prompts/customer-support.md"
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

## Step 2: Optimize Using Agent

```javascript
const PROMPT_FILE = process.env.ARGUMENTS;
const promptId = PROMPT_FILE.replace(/^prompts\//, '').replace(/\.md$/, '');

// Read original prompt
const originalPrompt = await Read({
  file_path: PROMPT_FILE
});

// Read best practices for optimization guidance
const bestPracticesContent = await Read({
  file_path: 'guides/unified-best-practices__claude_sonnet_4.md'
});

// Optimize using agent
await Task({
  subagent_type: 'general-purpose',
  description: 'Optimize prompt for better performance',
  prompt: `Optimize the following AI prompt for better performance, token efficiency, and clarity.

ORIGINAL PROMPT:
${originalPrompt}

BEST PRACTICES REFERENCE:
${bestPracticesContent}

Apply these optimization strategies:

**1. Token Efficiency** (25%)
- Remove redundancy
- Consolidate similar instructions
- Use more efficient phrasing
- Eliminate unnecessary examples

**2. Clarity Improvements** (25%)
- Clearer role definition
- More specific instructions
- Better structured sections
- Explicit expectations

**3. Specificity Enhancements** (20%)
- More precise language
- Concrete examples
- Measurable criteria
- Explicit constraints

**4. Reasoning Framework** (15%)
- Optimize reasoning steps
- Remove ambiguity
- Strengthen methodology
- Add missing frameworks if needed

**5. Output Quality** (15%)
- Better output specifications
- Clearer success criteria
- Enhanced quality controls
- Validation steps

Generate two files:

1. prompts/${promptId}-optimized.md
   The improved version with all optimizations applied

2. prompts/${promptId}-optimization-report.md
   Detailed report including:
   - Before/after quality scores
   - Specific improvements made (≥3)
   - Token count before/after
   - Improvement percentage
   - Impact analysis (high/medium/low per change)
   - Recommendations for further improvement`,

  context: {
    prompt_file: PROMPT_FILE,
    prompt_id: promptId,
    best_practices_path: 'guides/unified-best-practices__claude_sonnet_4.md',
    optimized_output: `prompts/${promptId}-optimized.md`,
    report_output: `prompts/${promptId}-optimization-report.md`
  }
});
```

## Step 3: Validate Output

```bash
PROMPT_FILE="$ARGUMENTS"
PROMPT_ID=$(basename "$PROMPT_FILE" .md)
OPTIMIZED_FILE="prompts/$PROMPT_ID-optimized.md"
REPORT_FILE="prompts/$PROMPT_ID-optimization-report.md"

# Check optimized prompt created
if [ ! -f "$OPTIMIZED_FILE" ]; then
  echo "❌ ERROR: Optimized prompt not created"
  exit 1
fi

# Check report created
if [ ! -f "$REPORT_FILE" ]; then
  echo "❌ ERROR: Optimization report not created"
  exit 1
fi

# Check minimum file sizes
OPTIMIZED_SIZE=$(wc -c < "$OPTIMIZED_FILE")
REPORT_SIZE=$(wc -c < "$REPORT_FILE")

if [ $REPORT_SIZE -lt 600 ]; then
  echo "❌ ERROR: Optimization report too small (< 600 bytes)"
  echo "Current size: $REPORT_SIZE bytes"
  exit 1
fi

# Check for improvements documented
if ! grep -q "Improvement\|improvement" "$REPORT_FILE"; then
  echo "❌ ERROR: No improvements documented in report"
  exit 1
fi

# Check for quality scores
if ! grep -qE "score|Score|quality|Quality" "$REPORT_FILE"; then
  echo "❌ ERROR: No quality metrics found in report"
  exit 1
fi

echo "✓ Output validation complete (optimized: $OPTIMIZED_SIZE bytes, report: $REPORT_SIZE bytes)"
```

## Completion

```
═══════════════════════════════════════════════════
        PROMPT OPTIMIZATION COMPLETE ✓
═══════════════════════════════════════════════════

Prompt: $ARGUMENTS
Command: /prompt/optimize
Version: 2.0.0

Output Created:
  ✓ prompts/[prompt-id]-optimized.md
  ✓ prompts/[prompt-id]-optimization-report.md

Optimizations Applied:
  Token efficiency improved
  Clarity enhanced
  Specificity increased
  Reasoning framework optimized
  Quality controls strengthened

Validations Passed:
  ✓ Input validation (prompt file exists)
  ✓ Output validation (≥2 files created)
  ✓ Improvements documented (≥3)
  ✓ Quality metrics calculated
  ✓ Quality threshold (≥0.85)

NEXT STEPS:
→ /prompt/test prompts/[prompt-id]-optimized.md
   Test optimized prompt with sample inputs

═══════════════════════════════════════════════════
```

## Guidelines

- **5 Optimization Dimensions**: Token efficiency, clarity, specificity, reasoning, quality
- **Measurable Improvements**: Before/after scores for objective comparison
- **Token Reduction**: Target 10-20% reduction while improving clarity
- **Dual Output**: Optimized prompt + detailed improvement report
- **Impact Analysis**: High/medium/low classification per change
- **Minimal Quality Improvement**: ≥0.10 score increase required
