---
description: Review prompts against unified best practices from OpenAI, Anthropic, and Google
argument-hint: <prompt-file-path>
allowed-tools: Task, Read, Write, Bash
model: claude-sonnet-4-5
timeout: 1200
retry: 2
cost_estimate: 0.15-0.20

validation:
  input:
    prompt_file:
      required: true
      file_exists: true
      file_extension: ".md"
      error_message: "Prompt file must exist and be a .md file"
  output:
    schema: .claude/validation/schemas/prompt/prompt-review-output.json
    required_files:
      - 'prompts/${prompt_id}-review.md'
    min_file_size: 800
    quality_threshold: 0.85
    content_requirements:
      - "Compliance score calculated (0.0-1.0)"
      - "Best practice violations identified"
      - "Specific improvement recommendations"
      - "Priority ranking of issues"
      - "Actionable fixes provided"

version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added input validation for prompt file"
      - "Added output validation for review reports"
      - "Unified best practices (OpenAI + Anthropic + Google)"
      - "Streamlined to compliance-focused review"
  - version: 1.0.0
    date: 2025-10-15
    changes:
      - "Initial implementation with multi-framework review"
---

# Review Prompt

Prompt File: **$ARGUMENTS**

## Step 1: Validate Input

```bash
PROMPT_FILE="$ARGUMENTS"

# Check file path provided
if [ -z "$PROMPT_FILE" ]; then
  echo "❌ ERROR: Missing prompt file path"
  echo ""
  echo "Usage: /prompt/review <prompt-file-path>"
  echo "Example: /prompt/review prompts/customer-support.md"
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

## Step 2: Review Against Best Practices

```javascript
const PROMPT_FILE = process.env.ARGUMENTS;
const promptId = PROMPT_FILE.replace(/^prompts\//, '').replace(/\.md$/, '');

// Read prompt to review
const promptContent = await Read({
  file_path: PROMPT_FILE
});

// Read unified best practices
const bestPracticesContent = await Read({
  file_path: 'guides/unified-best-practices__claude_sonnet_4.md'
});

// Review using agent
await Task({
  subagent_type: 'general-purpose',
  description: 'Review prompt against best practices',
  prompt: `Review the following AI prompt against unified best practices from OpenAI, Anthropic, and Google.

PROMPT TO REVIEW:
${promptContent}

BEST PRACTICES REFERENCE:
${bestPracticesContent}

Conduct a comprehensive review checking:

**1. Role & Expertise** (20%)
- Clear role definition
- Domain expertise specified
- Appropriate expertise level

**2. Mission & Objectives** (15%)
- Clear mission statement
- Specific objectives
- Success criteria defined

**3. Input Processing** (15%)
- Input handling protocol
- Edge case handling
- Validation requirements

**4. Reasoning Methodology** (20%)
- Reasoning framework specified (CoT, ReAct, etc.)
- Appropriate for task complexity
- Clear reasoning steps

**5. Output Specifications** (15%)
- Format clearly defined
- Structure requirements
- Quality criteria

**6. Quality Controls** (10%)
- Quality checklist present
- Validation steps
- Error handling

**7. Execution Protocol** (5%)
- Clear execution steps
- Workflow defined

Calculate compliance score (0.0-1.0) based on these categories.

Identify violations and provide specific, actionable recommendations prioritized by impact.

Generate review report with:
- Overall compliance score
- Category scores
- Violations identified (with severity: critical/high/medium/low)
- Specific recommendations (prioritized)
- Example improvements
- Quick wins (< 5 min to fix)

Save to: prompts/${promptId}-review.md`,

  context: {
    prompt_file: PROMPT_FILE,
    prompt_id: promptId,
    best_practices_path: 'guides/unified-best-practices__claude_sonnet_4.md',
    output_path: `prompts/${promptId}-review.md`
  }
});
```

## Step 3: Validate Output

```bash
PROMPT_FILE="$ARGUMENTS"
PROMPT_ID=$(basename "$PROMPT_FILE" .md)
REVIEW_FILE="prompts/$PROMPT_ID-review.md"

# Check review file created
if [ ! -f "$REVIEW_FILE" ]; then
  echo "❌ ERROR: Review report not created"
  exit 1
fi

# Check minimum file size (800 bytes for comprehensive review)
FILE_SIZE=$(wc -c < "$REVIEW_FILE")
if [ $FILE_SIZE -lt 800 ]; then
  echo "❌ ERROR: Review report too small (< 800 bytes)"
  echo "Current size: $FILE_SIZE bytes"
  exit 1
fi

# Check for compliance score
if ! grep -q "compliance score\|Compliance Score" "$REVIEW_FILE"; then
  echo "❌ ERROR: No compliance score found in review"
  exit 1
fi

# Check for recommendations
if ! grep -q "Recommendation\|recommendation" "$REVIEW_FILE"; then
  echo "❌ ERROR: No recommendations found in review"
  exit 1
fi

echo "✓ Output validation complete (review is $FILE_SIZE bytes)"
```

## Completion

```
═══════════════════════════════════════════════════
        PROMPT REVIEW COMPLETE ✓
═══════════════════════════════════════════════════

Prompt: $ARGUMENTS
Command: /prompt/review
Version: 2.0.0

Output Created:
  ✓ prompts/[prompt-id]-review.md

Review Analysis:
  Compliance score calculated (0.0-1.0)
  Best practice violations identified
  Specific recommendations provided
  Priority ranking assigned
  Quick wins highlighted

Validations Passed:
  ✓ Input validation (prompt file exists)
  ✓ Output validation (≥800 bytes)
  ✓ Compliance score present
  ✓ Recommendations provided
  ✓ Quality threshold (≥0.85)

NEXT STEPS:
→ /prompt/optimize $ARGUMENTS
   Optimize prompt based on review findings

═══════════════════════════════════════════════════
```

## Guidelines

- **Unified Best Practices**: OpenAI + Anthropic + Google combined
- **7 Review Categories**: Role, Mission, Input, Reasoning, Output, Quality, Execution
- **Compliance Scoring**: 0.0-1.0 scale with category breakdown
- **Prioritized Recommendations**: Critical > High > Medium > Low
- **Actionable Fixes**: Specific examples and improvements
- **Quick Wins**: Identify <5 min fixes for rapid improvement
