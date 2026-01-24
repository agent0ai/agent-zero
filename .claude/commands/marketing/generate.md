---
description: Generate AI-powered marketing showcase content for any project
argument-hint: [project-path] [audience] [--model=haiku|sonnet|opus] [--mock] [--preview-only]
model: claude-sonnet-4-5-20250929
allowed-tools: Bash, Read, AskUserQuestion, Write
---

Generate marketing showcase content: **$ARGUMENTS**

## Overview

This command generates AI-powered marketing showcase content for any software project. It analyzes your project's README, package.json, and codebase to create professional landing page content tailored for specific audiences (B2C, B2B, Investor, Internal).

## Step 1: Parse and Validate Arguments

Parse the arguments to extract configuration:

```javascript
// Parse ARGUMENTS string
const parts = ARGUMENTS.trim().split(/\s+/);
let projectPath = null;
let audience = null;
let model = 'haiku';  // Default to Haiku (90% cheaper)
let useMock = false;
let previewOnly = false;

// Extract positional arguments
const positionals = parts.filter(p => !p.startsWith('--'));
if (positionals.length >= 1) projectPath = positionals[0];
if (positionals.length >= 2) audience = positionals[1];

// Extract flags
if (parts.includes('--mock')) useMock = true;
if (parts.includes('--preview-only')) previewOnly = true;

// Extract model flag
const modelFlag = parts.find(p => p.startsWith('--model='));
if (modelFlag) {
  model = modelFlag.split('=')[1];
}

// Default values
if (!projectPath) projectPath = '.';  // Current directory
if (!audience) audience = 'b2c';      // Default to B2C

// Validate audience
const validAudiences = ['b2c', 'b2b', 'investor', 'internal', 'all'];
if (!validAudiences.includes(audience.toLowerCase())) {
  console.log(`❌ Invalid audience: ${audience}`);
  console.log(`   Valid options: ${validAudiences.join(', ')}`);
  throw new Error('Invalid audience');
}

// Validate model
const validModels = ['haiku', 'sonnet', 'opus'];
if (!validModels.includes(model.toLowerCase())) {
  console.log(`❌ Invalid model: ${model}`);
  console.log(`   Valid options: ${validModels.join(', ')}`);
  throw new Error('Invalid model');
}
```

## Step 2: Verify Project Path Exists

Check if the specified project path is valid:

```bash
# Expand path if needed (handle ~ and .)
if [ "$projectPath" = "." ]; then
  projectPath=$(pwd)
elif [[ "$projectPath" == "~"* ]]; then
  projectPath="${projectPath/#\~/$HOME}"
fi

# Check if path exists
if [ ! -d "$projectPath" ]; then
  echo "❌ Project path does not exist: $projectPath"
  echo ""
  echo "TROUBLESHOOTING:"
  echo "  • Verify the path is correct"
  echo "  • Use '.' for current directory"
  echo "  • Use absolute path: /home/user/projects/MyProject"
  echo "  • Use ~ for home: ~/projects/MyProject"
  exit 1
fi

# Get project name from path
projectName=$(basename "$projectPath")
```

Use Bash tool to verify the path:

```bash
Bash: ls -d [projectPath]
```

If the path doesn't exist, display error and exit:

```
❌ PROJECT PATH NOT FOUND

Path: [projectPath]

TROUBLESHOOTING:
  • Verify the path is correct: ls [projectPath]
  • Use '.' for current directory
  • Use absolute path: /home/user/projects/MyProject
  • Use ~ for home directory: ~/projects/MyProject

EXAMPLES:
  /marketing:generate ~/projects/RestaurantHive b2c
  /marketing:generate . b2c --mock
  /marketing:generate /home/user/MyProject investor --model=sonnet
```

## Step 3: Display Configuration Preview

Show the user what will be generated:

```
═══════════════════════════════════════════════════
    MARKETING SHOWCASE CONTENT GENERATION
═══════════════════════════════════════════════════

📁 PROJECT: [projectName]
📂 PATH: [projectPath]
👥 AUDIENCE: [audience]
🤖 MODEL: [model]
💰 COST:
   • Haiku: ~$0.10/page (⚡ Fast, 90% cheaper)
   • Sonnet: ~$1.00/page (⚖️ Balanced)
   • Opus: ~$5.00/page (🏆 Highest quality)

🎯 MODE: [AI-powered | Mock (zero cost)]

WHAT WILL BE GENERATED:
  ✓ Professional landing page HTML
  ✓ SEO-optimized content
  ✓ Audience-specific messaging
  ✓ Call-to-action sections
  ✓ Feature highlights
  ✓ Quality scoring and analysis

ESTIMATED:
  • Generation Time: [Haiku: 30-60s | Sonnet: 5-10min | Opus: 10-20min]
  • Cost per audience: [based on model]
  • Quality Expected: [Haiku: 8.8/10 | Sonnet: 9.2/10 | Opus: 10/10]

═══════════════════════════════════════════════════
```

## Step 4: Request User Approval

For AI-powered mode (not mock), request approval using AskUserQuestion:

```javascript
if (!useMock) {
  AskUserQuestion({
    questions: [{
      question: `Ready to generate marketing content for ${projectName}?`,
      header: "Confirm",
      multiSelect: false,
      options: [
        {
          label: "Proceed",
          description: `Generate ${audience} content with ${model} model (~$${modelCost}/page)`
        },
        {
          label: "Use Mock Mode",
          description: "Generate with mock data (zero cost, instant results)"
        },
        {
          label: "Change Settings",
          description: "Modify audience, model, or other options"
        },
        {
          label: "Cancel",
          description: "Do not generate content"
        }
      ]
    }]
  })
}
```

Handle user response:

- **"Proceed"** → Continue to Step 5
- **"Use Mock Mode"** → Set `useMock = true`, continue to Step 5
- **"Change Settings"** → Ask what to change, modify parameters, return to Step 3
- **"Cancel"** → Exit with message "Content generation cancelled. No API calls made."

## Step 5: Execute Marketing Workflow

Navigate to backend directory and execute the marketing workflow:

```bash
# Navigate to marketing showcase backend
cd /home/webemo-aaron/projects/prompt-blueprint/shopify-dashboard/backend

# Build command
command="npx tsx test-marketing-workflow.ts \"$projectPath\" $audience"

# Add model flag (not needed for mock mode)
if [ "$useMock" = false ]; then
  command="$command --model=$model"
fi

# Add flags
if [ "$useMock" = true ]; then
  command="$command --mock"
fi

if [ "$previewOnly" = true ]; then
  command="$command --preview-only"
fi

# Display command being executed
echo ""
echo "🚀 Executing: $command"
echo ""

# Execute with timeout (10 minutes for AI, 1 minute for mock)
timeout=$([ "$useMock" = true ] && echo "60000" || echo "600000")
```

Execute using Bash tool:

```javascript
Bash({
  command: commandString,
  description: "Generate marketing showcase content",
  timeout: timeout  // 60s for mock, 600s (10min) for AI
})
```

## Step 6: Parse and Display Results

### On Success

Parse the output to extract key information:

```javascript
// Look for success indicators in output
// - "✅ END-TO-END TEST COMPLETE"
// - "Content generated: N audiences"
// - "HTML rendered: N files"
// - Quality scores
// - Generation time
// - Estimated cost

// Extract generated files
const outputPattern = /output\/[^/]+\/showcase-[^\.]+\.html/g;
const generatedFiles = output.match(outputPattern) || [];

// Extract quality score
const qualityPattern = /Quality Score: ([\d\.]+)\/10/;
const qualityMatch = output.match(qualityPattern);
const qualityScore = qualityMatch ? qualityMatch[1] : 'N/A';

// Extract generation time
const timePattern = /Generation Time: ([\d]+)s/;
const timeMatch = output.match(timePattern);
const genTime = timeMatch ? timeMatch[1] : 'N/A';

// Extract cost
const costPattern = /Estimated Cost: \$([\d\.]+)/;
const costMatch = output.match(costPattern);
const cost = costMatch ? costMatch[1] : '0.00';
```

Display success message:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ MARKETING CONTENT GENERATION COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 PROJECT: [projectName]
👥 AUDIENCE: [audience]
🤖 MODEL: [model]
⏱️  GENERATION TIME: [genTime]s
💰 ESTIMATED COST: $[cost]
⭐ QUALITY SCORE: [qualityScore]/10

📄 GENERATED FILES:
[For each generated file:]
  ✓ [filename]
     Preview: file://[absolute-path]

📊 QUALITY BREAKDOWN:
  • Benefit-Focused: [score]/10
  • Concrete Metrics: [score]/10
  • SEO Optimization: [score]/10
  • Visual Appeal: [score]/10
  • Call-to-Action: [score]/10

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 NEXT STEPS:

1. 📖 Preview HTML in browser:
   open [first-generated-file]

2. ✅ Validate quality scores:
   /marketing:validate-quality [projectPath] --all

3. 📊 View cost report:
   /marketing:cost-report --days=7

4. 🚀 Publish (coming soon):
   /marketing:publish [projectPath] [audience]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 TIPS:

• Use --mock flag for zero-cost testing during development
• Use --model=haiku for 90% cost savings (still excellent quality)
• Use --model=sonnet for balanced quality/cost
• Use --model=opus only for critical, high-value content

• Generate for all audiences: /marketing:generate [path] all
• Compare models: /marketing:validate-quality [path] --models=haiku,sonnet

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### On Failure

Parse error message and provide troubleshooting:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ MARKETING CONTENT GENERATION FAILED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 PROJECT: [projectName]
👥 AUDIENCE: [audience]
🤖 MODEL: [model]

❌ ERROR: [error message from output]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 TROUBLESHOOTING:

COMMON ISSUES:

1. API Authentication Failed (401 error)
   • Check: CLAUDE_CODE_OAUTH_TOKEN or ANTHROPIC_API_KEY set in .env
   • Fix: Add valid API key to .env file
   • Alternative: Use --mock flag for zero-cost testing

2. Project Not Found
   • Check: ls [projectPath]
   • Fix: Verify path is correct
   • Tip: Use '.' for current directory

3. Invalid Model Selection
   • Valid models: haiku, sonnet, opus
   • Default: haiku (best cost/quality)

4. Out of Memory / Timeout
   • Try: --model=haiku (faster, less memory)
   • Try: Generate one audience at a time instead of 'all'

5. Marketing System Not Found
   • Check: File exists at /home/webemo-aaron/projects/prompt-blueprint/shopify-dashboard/backend/test-marketing-workflow.ts
   • Fix: Run from correct directory or check installation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 NEED HELP?

• Documentation: /home/webemo-aaron/projects/prompt-blueprint/shopify-dashboard/backend/docs/guides/MARKETING_SHOWCASE_QUICKSTART.md
• API Setup: /home/webemo-aaron/projects/prompt-blueprint/shopify-dashboard/backend/docs/features/MODEL_SELECTION_IMPLEMENTATION.md
• Try mock mode: /marketing:generate [projectPath] [audience] --mock

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Error Handling Examples

### Example 1: Invalid Path

```bash
/marketing:generate /nonexistent/path b2c
```

**Output**:

```
❌ PROJECT PATH NOT FOUND

Path: /nonexistent/path

TROUBLESHOOTING:
  • Verify the path is correct: ls /nonexistent/path
  • Use '.' for current directory
  • Use absolute path: /home/user/projects/MyProject
  • Use ~ for home directory: ~/projects/MyProject
```

### Example 2: Invalid Audience

```bash
/marketing:generate ~/projects/MyApp enterprise
```

**Output**:

```
❌ Invalid audience: enterprise
   Valid options: b2c, b2b, investor, internal, all
```

### Example 3: Invalid Model

```bash
/marketing:generate ~/projects/MyApp b2c --model=gpt4
```

**Output**:

```
❌ Invalid model: gpt4
   Valid options: haiku, sonnet, opus
```

## Usage Examples

### Example 1: Basic Generation (Current Directory, Default Settings)

```bash
cd ~/projects/RestaurantHive
/marketing:generate . b2c
```

**Result**: Generates B2C content using Haiku model for current directory project

### Example 2: Generate for All Audiences

```bash
/marketing:generate ~/projects/RestaurantHive all --mock
```

**Result**: Generates content for B2C, B2B, Investor, and Internal audiences using mock data (zero cost)

### Example 3: High-Quality Investor Content

```bash
/marketing:generate ~/projects/MyStartup investor --model=sonnet
```

**Result**: Generates investor-focused content using Sonnet model (higher quality, ~$1/page)

### Example 4: Development Testing (Mock Mode)

```bash
/marketing:generate ~/projects/MyApp b2b --mock
```

**Result**: Instant mock generation (zero cost, ~9.6/10 quality for testing)

### Example 5: Preview Only (No File Writing)

```bash
/marketing:generate ~/projects/MyApp b2c --preview-only --mock
```

**Result**: Generates content and displays preview without writing output files

## Integration with Other Commands

This command integrates seamlessly with other marketing slash commands:

**Quality Validation**:

```bash
# Generate content
/marketing:generate ~/projects/MyApp b2c

# Validate quality meets thresholds
/marketing:validate-quality ~/projects/MyApp --all
```

**Cost Tracking**:

```bash
# Generate content (uses real API)
/marketing:generate ~/projects/MyApp b2c --model=haiku

# Check cost report
/marketing:cost-report --days=7
```

**Full Workflow**:

```bash
# 1. Test with mock mode first
/marketing:generate ~/projects/MyApp b2c --mock

# 2. If satisfied, generate with AI
/marketing:generate ~/projects/MyApp all --model=haiku

# 3. Validate quality
/marketing:validate-quality ~/projects/MyApp --all

# 4. Check costs
/marketing:cost-report --projection
```

## Cost Optimization Tips

**Best Practices**:

1. **Use Mock Mode for Development**
   - Zero cost, instant results
   - Perfect for testing templates and structure
   - Quality: 9.6/10 (very good for mock)

   ```bash
   /marketing:generate ~/projects/MyApp b2c --mock
   ```

2. **Default to Haiku for Production**
   - 90% cheaper than Sonnet ($0.10 vs $1.00/page)
   - Quality: 8.8/10 (excellent for most use cases)
   - Speed: 30-60 seconds

   ```bash
   /marketing:generate ~/projects/MyApp b2c  # Haiku is default
   ```

3. **Use Sonnet for Critical Content**
   - Reserve for investor pitches, high-stakes launches
   - Quality: 9.2/10
   - Cost: ~$1.00/page

   ```bash
   /marketing:generate ~/projects/MyApp investor --model=sonnet
   ```

4. **Avoid Opus Unless Absolutely Necessary**
   - 50x more expensive than Haiku
   - Quality: 10/10 (marginal improvement over Sonnet)
   - Cost: ~$5.00/page

## Technical Notes

**Backend Location**: `/home/webemo-aaron/projects/prompt-blueprint/shopify-dashboard/backend/`

**CLI Wrapper**: This command wraps `test-marketing-workflow.ts`

**Environment Variables**:

- `ANTHROPIC_API_KEY`: Anthropic API key (preferred)
- `CLAUDE_CODE_OAUTH_TOKEN`: Claude Code OAuth token (alternative)

**Output Directory**: `output/[project-name]/`

**File Format**:

- HTML: `showcase-[audience].html`
- JSON: `content-[audience].json`

**Quality Threshold**: 8.0/10 minimum for production use

## Success Criteria

✅ Command executed successfully when:

- Project path exists and is readable
- Audience is valid (b2c, b2b, investor, internal, all)
- Model is valid (haiku, sonnet, opus)
- API credentials valid (for AI mode) or --mock flag used
- Marketing system backend is accessible
- Generated files created in output directory
- Quality scores meet minimum threshold (8.0/10)

---

**Related Commands**:

- `/marketing:validate-quality` - Validate content quality
- `/marketing:cost-report` - Track API costs
- `/product:define` - Define product before generating marketing content

**Documentation**:

- Quickstart: `docs/guides/MARKETING_SHOWCASE_QUICKSTART.md`
- Model Selection: `docs/features/MODEL_SELECTION_IMPLEMENTATION.md`
- Operationalization: `docs/guides/OPERATIONALIZATION_PLAN.md`
