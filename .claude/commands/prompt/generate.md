---
description: Generate professional AI prompts using PromptCraft∞ Elite agent
argument-hint: <prompt-purpose>
allowed-tools: Task, Read, Write, AskUserQuestion, Bash
model: claude-sonnet-4-5
timeout: 1800
retry: 2
cost_estimate: 0.20-0.30

validation:
  input:
    prompt_purpose:
      required: true
      min_length: 10
      error_message: "Prompt purpose must be at least 10 characters describing what the prompt should accomplish"
  output:
    schema: .claude/validation/schemas/prompt/prompt-generate-output.json
    required_files:
      - 'prompts/${prompt_id}.md'
    min_file_size: 1000
    quality_threshold: 0.85
    content_requirements:
      - "Role and expertise definition"
      - "Mission critical objective"
      - "Input processing protocol"
      - "Reasoning methodology specified"
      - "Output specifications defined"
      - "Quality control checklist"
      - "Execution protocol"

version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added input validation for prompt purpose"
      - "Added output validation for generated prompts"
      - "Updated to use PromptCraft∞ Elite agent"
      - "Streamlined to 7-stage professional workflow"
  - version: 1.0.0
    date: 2025-10-15
    changes:
      - "Initial implementation with PromptCraft∞ Elite"
---

# Generate Prompt

Prompt Purpose: **$ARGUMENTS**

## Step 1: Validate Input

```bash
PROMPT_PURPOSE="$ARGUMENTS"

# Check purpose provided
if [ -z "$PROMPT_PURPOSE" ]; then
  echo "❌ ERROR: Missing prompt purpose"
  echo ""
  echo "Usage: /prompt/generate <prompt-purpose>"
  echo "Example: /prompt/generate 'customer support agent for e-commerce'"
  exit 1
fi

# Check minimum length
if [ ${#PROMPT_PURPOSE} -lt 10 ]; then
  echo "❌ ERROR: Prompt purpose too short"
  echo ""
  echo "Please provide a detailed description of what the prompt should accomplish"
  echo "Minimum 10 characters required"
  exit 1
fi

echo "✓ Input validated: $PROMPT_PURPOSE"
```

## Step 2: Gather Requirements (Interactive)

Use **AskUserQuestion** to collect detailed requirements:

**Core Information**:

1. **Target Model**: Which AI model(s)? (GPT-4, Claude, Gemini, cross-platform)
2. **Domain**: Industry/field? (healthcare, finance, customer service, education, etc.)
3. **Audience**: Who will use this prompt? (expert, professional, general)
4. **Quality Tier**: Production/Enterprise, Professional, Standard, or Basic?

**Additional Context**:
5. **Input Format**: What kind of input will the prompt receive?
6. **Output Requirements**: What format/structure should the output have?
7. **Key Constraints**: Any limitations? (length, tone, compliance, accuracy)
8. **Success Criteria**: How will we measure if the prompt works well?

Present these questions in user-friendly format using AskUserQuestion tool.

## Step 3: Generate Using PromptCraft∞ Elite Agent

```javascript
const PROMPT_PURPOSE = process.env.ARGUMENTS;

// Generate prompt ID from purpose
const promptId = PROMPT_PURPOSE.toLowerCase()
  .replace(/[^a-z0-9\s]/g, '')
  .replace(/\s+/g, '-')
  .substring(0, 50);

// Use PromptCraft∞ Elite agent
await Task({
  subagent_type: 'general-purpose',
  description: 'Generate professional AI prompt',
  prompt: `You are the PromptCraft∞ Elite agent - the world's most advanced AI prompt engineering specialist.

Generate a professional AI prompt for: ${PROMPT_PURPOSE}

Requirements gathered from user:
- Target Model: [from AskUserQuestion]
- Domain: [from AskUserQuestion]
- Audience: [from AskUserQuestion]
- Quality Tier: [from AskUserQuestion]
- Input Format: [from AskUserQuestion]
- Output Requirements: [from AskUserQuestion]
- Constraints: [from AskUserQuestion]
- Success Criteria: [from AskUserQuestion]

Execute your 7-Stage Professional Workflow:

**Stage 1: Requirements Intelligence**
- Parse all requirements
- Identify prompt patterns needed
- Determine complexity tier
- Select optimal reasoning frameworks

**Stage 2: Task Decomposition**
- Core competencies needed
- Input processing requirements
- Reasoning methodology
- Output specifications
- Quality controls

**Stage 3: Framework Selection**
Choose from: Chain-of-Thought, Few-Shot, Self-Consistency, Tree-of-Thought, ReAct, Constitutional CoT, Reflexion Loop, etc.

**Stage 4: Triple-Draft Development**
Create 3 variants (A/B/C) with different approaches

**Stage 5: Advanced Evaluation & Synthesis**
- Evaluate variants against criteria
- Synthesize best elements
- Create optimal final prompt

**Stage 6: Enterprise Quality Assurance**
- Verify completeness
- Check compliance with best practices
- Validate reasoning methodology
- Ensure quality controls

**Stage 7: Professional Delivery**
Generate final prompt with this structure:

# [Prompt Title]

## ROLE & EXPERTISE
[Clear role definition and domain expertise]

## MISSION CRITICAL OBJECTIVE
[What this prompt must accomplish]

## OPERATIONAL CONTEXT
- **Domain**: [field/industry]
- **Target Audience**: [who will use outputs]
- **Quality Tier**: [production/professional/standard]

## INPUT PROCESSING PROTOCOL
[How to handle input data/requests]

## REASONING METHODOLOGY
[Chain-of-Thought, ReAct, or other framework]

## OUTPUT SPECIFICATIONS
[Format, structure, requirements for output]

## QUALITY CONTROL CHECKLIST
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## EXECUTION PROTOCOL
[Step-by-step execution instructions]

Save to: prompts/${promptId}.md`,

  context: {
    prompt_purpose: PROMPT_PURPOSE,
    prompt_id: promptId,
    output_path: `prompts/${promptId}.md`,
    best_practices_path: 'guides/unified-best-practices__claude_sonnet_4.md'
  }
});
```

## Step 4: Validate Output

```bash
PROMPT_PURPOSE="$ARGUMENTS"
PROMPT_ID=$(echo "$PROMPT_PURPOSE" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | cut -c1-50)
PROMPT_FILE="prompts/$PROMPT_ID.md"

# Check file exists
if [ ! -f "$PROMPT_FILE" ]; then
  echo "❌ ERROR: Prompt file not created"
  exit 1
fi

# Check minimum file size (1000 bytes for completeness)
FILE_SIZE=$(wc -c < "$PROMPT_FILE")
if [ $FILE_SIZE -lt 1000 ]; then
  echo "❌ ERROR: Prompt too small (< 1000 bytes)"
  echo "Current size: $FILE_SIZE bytes"
  echo "A complete professional prompt should be comprehensive"
  exit 1
fi

# Check required sections
REQUIRED_SECTIONS=(
  "## ROLE & EXPERTISE"
  "## MISSION CRITICAL OBJECTIVE"
  "## INPUT PROCESSING PROTOCOL"
  "## REASONING METHODOLOGY"
  "## OUTPUT SPECIFICATIONS"
  "## QUALITY CONTROL CHECKLIST"
)

for section in "${REQUIRED_SECTIONS[@]}"; do
  if ! grep -q "$section" "$PROMPT_FILE"; then
    echo "❌ ERROR: Missing required section: $section"
    exit 1
  fi
done

# Check has reasoning methodology
if ! grep -qE "(Chain-of-Thought|CoT|ReAct|Few-Shot|Tree-of-Thought)" "$PROMPT_FILE"; then
  echo "❌ ERROR: No reasoning methodology specified"
  exit 1
fi

echo "✓ Output validation complete (prompt is $FILE_SIZE bytes)"
```

## Completion

```
═══════════════════════════════════════════════════
        PROMPT GENERATION COMPLETE ✓
═══════════════════════════════════════════════════

Purpose: $ARGUMENTS
Command: /prompt/generate
Version: 2.0.0

Output Created:
  ✓ prompts/[prompt-id].md

Prompt Structure:
  ✓ Role & expertise defined
  ✓ Mission objective clear
  ✓ Input protocol specified
  ✓ Reasoning methodology (CoT/ReAct/etc.)
  ✓ Output specifications defined
  ✓ Quality checklist included
  ✓ Execution protocol documented

Validations Passed:
  ✓ Input validation (purpose provided)
  ✓ Output validation (≥1000 bytes)
  ✓ All required sections present
  ✓ Reasoning methodology specified
  ✓ Quality threshold (≥0.85)

NEXT STEPS:
→ /prompt/review prompts/[prompt-id].md
   Review prompt against best practices

→ /prompt/test prompts/[prompt-id].md
   Test prompt with sample inputs

═══════════════════════════════════════════════════
```

## Guidelines

- **PromptCraft∞ Elite**: Uses 7-stage professional workflow
- **Best Practices**: Complies with OpenAI, Anthropic, and Google guidelines
- **Reasoning Frameworks**: CoT, ReAct, Few-Shot, Tree-of-Thought, etc.
- **Quality Tiers**: Production/Enterprise, Professional, Standard, Basic
- **Comprehensive Structure**: All 7 required sections for professional prompts
- **Reusability**: Prompts designed to be reused across similar use cases
