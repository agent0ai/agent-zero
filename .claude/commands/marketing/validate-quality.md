---
description: Validate marketing content quality against thresholds
argument-hint: [project-path] [--all] [--audiences=b2c,b2b] [--models=haiku,sonnet] [--mock]
model: claude-sonnet-4-5-20250929
allowed-tools: Bash, Read
---

Validate quality: **$ARGUMENTS**

## Overview

This command validates the quality of generated marketing content against minimum thresholds (8.0/10). It can test different audiences and models to help you choose the best cost/quality balance for your needs.

## Step 1: Parse Arguments

Extract configuration from arguments:

```javascript
// Parse ARGUMENTS string
const parts = ARGUMENTS.trim().split(/\s+/);
let projectPath = null;
let testAll = false;
let audiences = ['b2c'];  // Default
let models = ['haiku'];    // Default
let useMock = false;

// Extract positional arguments
const positionals = parts.filter(p => !p.startsWith('--'));
if (positionals.length >= 1) projectPath = positionals[0];

// Extract flags
if (parts.includes('--all')) testAll = true;
if (parts.includes('--mock')) useMock = true;

// Extract audiences flag
const audiencesFlag = parts.find(p => p.startsWith('--audiences='));
if (audiencesFlag) {
  audiences = audiencesFlag.split('=')[1].split(',');
} else if (testAll) {
  audiences = ['b2c', 'b2b', 'investor', 'internal'];
}

// Extract models flag
const modelsFlag = parts.find(p => p.startsWith('--models='));
if (modelsFlag) {
  models = modelsFlag.split('=')[1].split(',');
}

// Default projectPath to current directory
if (!projectPath) projectPath = '.';

// Auto-use mock if no API key
if (!process.env.ANTHROPIC_API_KEY && !process.env.CLAUDE_CODE_OAUTH_TOKEN) {
  useMock = true;
}
```

## Step 2: Verify Project Path

Check if the specified project path exists:

```bash
# Expand path if needed
if [ "$projectPath" = "." ]; then
  projectPath=$(pwd)
elif [[ "$projectPath" == "~"* ]]; then
  projectPath="${projectPath/#\~/$HOME}"
fi

# Check if path exists
if [ ! -d "$projectPath" ]; then
  echo "❌ Project path does not exist: $projectPath"
  exit 1
fi
```

Use Bash tool to verify:

```javascript
Bash({ command: `ls -d "${projectPath}"` })
```

## Step 3: Display Validation Configuration

Show what will be tested:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    MARKETING CONTENT QUALITY VALIDATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 PROJECT: [projectName]
📂 PATH: [projectPath]

🎯 VALIDATION CONFIGURATION:
   • Audiences: [audiences.join(', ')]
   • Models: [models.join(', ')]
   • Mode: [AI-powered | Mock]
   • Quality Threshold: 8.0/10 (minimum)

📊 TESTS TO RUN:
   Total: [audiences.length × models.length] combinations

   [For each audience in audiences]
     [For each model in models]
       ✓ Test: [audience] + [model]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏱️  ESTIMATED TIME:
   • Mock Mode: < 10 seconds
   • AI Mode: [audiences.length × models.length × 2] minutes

🚀 Starting validation...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Step 4: Execute Quality Validation

Navigate to backend and run validation script:

```bash
# Navigate to marketing showcase backend
cd /home/webemo-aaron/projects/prompt-blueprint/shopify-dashboard/backend

# Build command
command="npx tsx src/scripts/validate-quality.ts \"$projectPath\""

# Add --all flag if specified
if [ "$testAll" = true ]; then
  command="$command --all"
fi

# Add --audiences flag
if [ "$testAll" = false ]; then
  command="$command --audiences=$(echo ${audiences[@]} | tr ' ' ',')"
fi

# Add --models flag
command="$command --models=$(echo ${models[@]} | tr ' ' ',')"

# Add --mock flag if needed
if [ "$useMock" = true ]; then
  command="$command --mock"
fi

# Execute with timeout (5 minutes for AI, 30 seconds for mock)
timeout=$([ "$useMock" = true ] && echo "30000" || echo "300000")
```

Execute using Bash tool:

```javascript
Bash({
  command: commandString,
  description: "Validate marketing content quality",
  timeout: timeout  // 30s for mock, 300s (5min) for AI
})
```

## Step 5: Parse and Display Results

The validate-quality.ts script outputs formatted results. Display them directly, then add additional context:

### Success Output Format

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 QUALITY VALIDATION REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 PROJECT: [projectName]
📂 PATH: [projectPath]
🎯 MODE: [AI-powered | Mock]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 OVERALL RESULTS:

   Total Tests: [X]
   Passed: [Y] ([pass%]%)
   Failed: [N] ([fail%]%)
   Average Quality Score: [avgScore]/10

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 RESULTS BY AUDIENCE:

   [For each audience tested:]
   ✅ B2C: [score]/10
      • Benefit-Focused: [X]/10
      • Concrete Metrics: [X]/10
      • SEO Optimization: [X]/10
      • Visual Appeal: [X]/10
      • Call-to-Action: [X]/10

   ✅ B2B: [score]/10
      [... breakdown ...]

   ✅ INVESTOR: [score]/10
      [... breakdown ...]

   ✅ INTERNAL: [score]/10
      [... breakdown ...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 RESULTS BY MODEL:

   [If multiple models tested:]
   • Haiku: [avgScore]/10 ([count] tests)
   • Sonnet: [avgScore]/10 ([count] tests)
   • Opus: [avgScore]/10 ([count] tests)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[If avgScore >= 8.0:]
✅ VALIDATION PASSED

Average quality meets minimum threshold (8.0/10)
All tested combinations are production-ready.

[If avgScore < 8.0:]
❌ VALIDATION FAILED

Average quality below minimum threshold (8.0/10)

FAILED TESTS ([count]):
[For each failed test:]
  • [audience] ([model]): [score]/10
    Recommendations:
      - [recommendation 1]
      - [recommendation 2]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 RECOMMENDATIONS:

[If using Haiku and quality < 8.5:]
• Consider upgrading to Sonnet model for ~10% quality improvement
  /marketing:generate [path] [audience] --model=sonnet

[If all tests passed with Haiku:]
• Excellent! Haiku provides production-quality content at 90% cost savings
• Continue using Haiku for all audience types

[If failures exist:]
• Regenerate failed audiences with higher-quality model:
  /marketing:generate [path] [failed-audience] --model=sonnet

• Review README and ensure project has:
  - Clear value proposition
  - Concrete metrics/features
  - Target audience description

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 NEXT STEPS:

1. If quality is satisfactory:
   • Generate production content:
     /marketing:generate [path] all --model=haiku

2. If quality needs improvement:
   • Use higher-quality model:
     /marketing:generate [path] [audience] --model=sonnet

   • Improve project documentation (README.md)

   • Re-validate after changes:
     /marketing:validate-quality [path] --all

3. Track costs:
   /marketing:cost-report --days=7

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 COST-QUALITY ANALYSIS:

Model Comparison:
• Haiku: $0.10/page, ~8.8/10 quality (⚡ Best value)
• Sonnet: $1.00/page, ~9.2/10 quality (⚖️ Balanced)
• Opus: $5.00/page, ~10/10 quality (🏆 Premium)

Recommendation: Use Haiku for 80-90% of content, Sonnet for critical 10-20%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Error Handling

### Example 1: Project Not Found

```bash
/marketing:validate-quality /nonexistent/path --all
```

**Output**:

```
❌ Project path does not exist: /nonexistent/path

TROUBLESHOOTING:
  • Verify path is correct: ls /nonexistent/path
  • Use '.' for current directory
  • Use absolute path
```

### Example 2: No API Key (Auto-switches to Mock)

```bash
/marketing:validate-quality ~/projects/MyApp --all
```

**Output** (if no ANTHROPIC_API_KEY):

```
⚠️  No API key found - using Mock mode
   Set ANTHROPIC_API_KEY in .env for AI-powered validation

[Proceeds with mock validation...]
```

### Example 3: Invalid Model

```bash
/marketing:validate-quality . --models=gpt4,haiku
```

**Output**:

```
❌ Invalid model: gpt4
   Valid options: haiku, sonnet, opus

Proceeding with valid models: haiku
```

## Usage Examples

### Example 1: Validate All Audiences (Mock Mode)

```bash
/marketing:validate-quality ~/projects/RestaurantHive --all --mock
```

**Result**: Tests all 4 audiences (B2C, B2B, Investor, Internal) using mock data

### Example 2: Validate Specific Audience with AI

```bash
/marketing:validate-quality ~/projects/MyApp --audiences=b2c,investor
```

**Result**: Tests only B2C and Investor audiences using real AI generation (if API key available)

### Example 3: Compare Models for B2C Audience

```bash
/marketing:validate-quality . --audiences=b2c --models=haiku,sonnet,opus --mock
```

**Result**: Generates B2C content with all 3 models and compares quality scores

### Example 4: Quick Validation (Current Directory)

```bash
cd ~/projects/MyApp
/marketing:validate-quality . --all --mock
```

**Result**: Validates all audiences for project in current directory using mock mode

### Example 5: Production Validation Before Launch

```bash
# Test with real AI before production deployment
/marketing:validate-quality ~/projects/MyApp --all --models=haiku

# Expected output: All audiences should score ≥ 8.0/10
```

## Integration with Other Commands

### Workflow 1: Development Cycle

```bash
# 1. Generate with mock mode (fast iteration)
/marketing:generate ~/projects/MyApp b2c --mock

# 2. Validate quality
/marketing:validate-quality ~/projects/MyApp --audiences=b2c --mock

# 3. If satisfied, generate with AI
/marketing:generate ~/projects/MyApp b2c --model=haiku
```

### Workflow 2: Model Selection

```bash
# 1. Compare models with mock data
/marketing:validate-quality ~/projects/MyApp --audiences=b2c --models=haiku,sonnet,opus --mock

# 2. Based on results, choose best cost/quality model
# Example: If Haiku scores 8.7/10 vs Sonnet 9.1/10
# Decision: Use Haiku (save 90% cost for only 4% quality difference)

# 3. Generate production content with chosen model
/marketing:generate ~/projects/MyApp all --model=haiku
```

### Workflow 3: Quality Assurance

```bash
# 1. Generate content
/marketing:generate ~/projects/MyApp all --model=haiku

# 2. Validate meets production standards
/marketing:validate-quality ~/projects/MyApp --all

# 3. Check for failures and regenerate if needed
# If Investor audience failed (scored 7.5/10):
/marketing:generate ~/projects/MyApp investor --model=sonnet

# 4. Re-validate
/marketing:validate-quality ~/projects/MyApp --audiences=investor
```

## Quality Thresholds

**Minimum Acceptable**: 8.0/10
**Good**: 8.5-9.0/10
**Excellent**: 9.0-9.5/10
**Outstanding**: 9.5+/10

**By Model** (typical averages):

- Haiku: 8.8/10
- Sonnet: 9.2/10
- Opus: 10/10

**By Audience** (typical):

- B2C: 8.5-9.0/10 (consumer-focused, simple)
- B2B: 8.5-9.0/10 (professional, detailed)
- Investor: 8.8-9.2/10 (metrics-heavy, strategic)
- Internal: 9.0-9.5/10 (technical, comprehensive)

## Technical Notes

**Script Location**: `/home/webemo-aaron/projects/prompt-blueprint/shopify-dashboard/backend/src/scripts/validate-quality.ts`

**Quality Scoring Criteria**:

1. **Benefit-Focused** (20%): Clear value propositions and benefits
2. **Concrete Metrics** (20%): Specific, quantifiable claims
3. **SEO Optimization** (20%): Keywords, meta descriptions, structure
4. **Visual Appeal** (20%): Layout, formatting, readability
5. **Call-to-Action** (20%): Clear CTAs with proper placement

**Testing Modes**:

- **Mock Mode**: Uses MockMarketingContentGenerator (zero cost, ~9.6/10 quality baseline)
- **AI Mode**: Uses real Claude API (costs API credits, variable quality by model)

**Exit Codes**:

- `0`: All tests passed (avgScore >= 8.0)
- `1`: Validation failed (avgScore < 8.0 or errors)

## Performance

**Mock Mode**:

- Speed: < 10 seconds for all 4 audiences
- Cost: $0.00
- Quality: 9.6/10 (mock baseline)

**AI Mode**:

- Speed: ~2 minutes per audience per model
- Cost: $0.10/page (Haiku), $1.00/page (Sonnet), $5.00/page (Opus)
- Quality: Variable by model (8.8-10/10)

**Example**: Testing all 4 audiences with 3 models in AI mode

- Total Tests: 12
- Time: ~24 minutes
- Cost: ~$7.20 (if all with Sonnet), ~$0.72 (if all with Haiku)

**Tip**: Always start with mock mode to test workflow, then use AI mode sparingly for final validation.

## Success Criteria

✅ Command executed successfully when:

- Project path exists and is readable
- Specified audiences are valid
- Specified models are valid
- Quality validation script runs without errors
- Results are parsed and displayed correctly
- Quality scores are calculated for all tests

---

**Related Commands**:

- `/marketing:generate` - Generate marketing content
- `/marketing:cost-report` - Track API costs and budget

**Documentation**:

- Quality Validation: `docs/guides/OPERATIONALIZATION_PLAN.md`
- Model Selection: `docs/features/MODEL_SELECTION_IMPLEMENTATION.md`
- Quality Criteria: `docs/features/DEFAULT_MODEL_CHANGE_HAIKU.md`
