---
description: Generate cost reports and budget analysis for marketing content generation
argument-hint: [--days=30] [--projection] [--budget daily monthly]
model: claude-3-5-haiku-20241022
allowed-tools: Bash, Read
---

Cost report: **$ARGUMENTS**

## Overview

This command generates cost tracking reports for marketing content generation, helping you monitor API usage, track spending, and stay within budget. It wraps the cost tracking system built during Session 3.

## Step 1: Parse Arguments

Extract report configuration from arguments:

```javascript
// Parse ARGUMENTS string
const parts = ARGUMENTS.trim().split(/\s+/);
let reportType = 'report';  // Default: generate report
let days = 30;              // Default: 30 days
let dailyBudget = 10;       // Default: $10/day
let monthlyBudget = 300;    // Default: $300/month

// Determine report type
if (parts.includes('--projection')) {
  reportType = 'projection';
} else if (parts.includes('--budget')) {
  reportType = 'budget';

  // Extract budget values (positional arguments after --budget)
  const budgetIndex = parts.indexOf('--budget');
  const positionals = parts.slice(budgetIndex + 1).filter(p => !p.startsWith('--'));
  if (positionals.length >= 1) dailyBudget = parseFloat(positionals[0]);
  if (positionals.length >= 2) monthlyBudget = parseFloat(positionals[1]);
}

// Extract --days flag (for report mode)
const daysFlag = parts.find(p => p.startsWith('--days='));
if (daysFlag) {
  days = parseInt(daysFlag.split('=')[1]);
}
```

## Step 2: Display Configuration

Show what report will be generated:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    MARKETING COST TRACKING REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 REPORT TYPE: [reportType]

[If report mode:]
   Period: Last [days] days

[If projection mode:]
   Projecting monthly costs based on current usage

[If budget mode:]
   Daily Budget: $[dailyBudget]
   Monthly Budget: $[monthlyBudget]

🚀 Generating report...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Step 3: Execute Cost Tracking Script

Navigate to backend and run cost tracking script:

```bash
# Navigate to marketing showcase backend
cd /home/webemo-aaron/projects/prompt-blueprint/shopify-dashboard/backend

# Build command based on report type
case "$reportType" in
  "report")
    command="npx tsx src/scripts/track-costs.ts report $days"
    ;;
  "projection")
    command="npx tsx src/scripts/track-costs.ts projection"
    ;;
  "budget")
    command="npx tsx src/scripts/track-costs.ts budget $dailyBudget $monthlyBudget"
    ;;
esac

# Execute with short timeout (cost reports are fast)
```

Execute using Bash tool:

```javascript
Bash({
  command: commandString,
  description: "Generate cost tracking report",
  timeout: 10000  // 10 seconds (reports are fast)
})
```

## Step 4: Display Results

The track-costs.ts script outputs formatted reports. Display them directly, then add additional context.

### Report Mode Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 COST TRACKING REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 PERIOD: Last [days] days

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 OVERALL STATISTICS:

   Total Cost: $[X.XX]
   Total Generations: [N]
   Average Cost: $[X.XXXX]
   Avg Generation Time: [X.X]s
   Avg Quality Score: [X.X]/10

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 MODEL USAGE:

   Haiku: [N] ([X]%) - $[Y.YY]
   Sonnet: [N] ([X]%) - $[Y.YY]
   Opus: [N] ([X]%) - $[Y.YY]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👥 AUDIENCE BREAKDOWN:

   B2C: [N] generations
   B2B: [N] generations
   Investor: [N] generations
   Internal: [N] generations

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 COST SAVINGS:

   Saved vs all Sonnet: $[X.XX]
   Savings percentage: [X.X]%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 NEXT STEPS:

1. Review cost trends:
   /marketing:cost-report --days=7   # Last week
   /marketing:cost-report --days=90  # Last quarter

2. Check monthly projection:
   /marketing:cost-report --projection

3. Set budget alerts:
   /marketing:cost-report --budget 10 300  # $10/day, $300/month

4. Optimize costs:
   • Use Haiku model for 90% cost savings
   • Use --mock flag for development/testing
   • Cache generated content (avoid regeneration)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 COST OPTIMIZATION TIPS:

✓ Default to Haiku: $0.10/page vs Sonnet $1.00/page (90% savings)
✓ Use mock mode for testing: Zero cost, instant results
✓ Generate once, reuse often: Cache generated HTML
✓ Batch audiences: Generate 'all' at once instead of individually

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Projection Mode Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 MONTHLY COST PROJECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 CURRENT MONTH: [Month Year]

💰 PROJECTION:

   Current Spending (month-to-date): $[X.XX]
   Days Elapsed: [N] days
   Daily Average: $[X.XX]/day

   PROJECTED MONTHLY TOTAL: $[XXX.XX]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 TREND ANALYSIS:

   [If increasing:]
   ⚠️  Spending trending UP
   • Current rate: $[X.XX]/day
   • Last week rate: $[Y.YY]/day
   • Increase: [Z]%

   [If decreasing:]
   ✅ Spending trending DOWN
   • Current rate: $[X.XX]/day
   • Last week rate: $[Y.YY]/day
   • Decrease: [Z]%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 RECOMMENDATIONS:

[If projected > $300:]
⚠️  Projected monthly cost ($[XXX]) exceeds typical budget ($300)

   Ways to reduce costs:
   1. Switch to Haiku model (90% cheaper than Sonnet)
   2. Use --mock flag more often for development
   3. Regenerate less frequently (cache existing content)
   4. Review cost report to identify high-cost operations:
      /marketing:cost-report --days=30

[If projected < $50:]
✅ Well within typical budget ($300/month)
   Current usage is cost-efficient!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 NEXT STEPS:

1. View detailed breakdown:
   /marketing:cost-report --days=30

2. Set budget alerts:
   /marketing:cost-report --budget 10 300

3. Continue generating content efficiently:
   /marketing:generate [path] [audience] --model=haiku

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Budget Mode Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 BUDGET COMPLIANCE CHECK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 BUDGET THRESHOLDS:

   Daily Budget: $[dailyBudget]
   Monthly Budget: $[monthlyBudget]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ DAILY STATUS:

   Today's Spending: $[X.XX]
   Daily Budget: $[dailyBudget]

   [If under budget:]
   ✅ Within budget ($[remaining] remaining today)

   [If over budget:]
   ⚠️  OVER BUDGET by $[excess]
   • Exceeded at: [time]
   • Operations after threshold: [N]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 MONTHLY STATUS:

   Month-to-Date: $[XX.XX]
   Projected Total: $[XXX.XX]
   Monthly Budget: $[monthlyBudget]

   [If projected under budget:]
   ✅ On track ($[remaining] remaining this month)

   [If projected over budget:]
   ⚠️  PROJECTED TO EXCEED by $[excess]
   • At current rate, will exceed on: [date]
   • Days until over budget: [N]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[If any budget alerts:]
⚠️  BUDGET ALERTS:

   • [Alert 1: Daily budget exceeded by $X.XX]
   • [Alert 2: Monthly projection exceeds budget by $Y.YY]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 RECOMMENDATIONS:

[If over budget:]
   IMMEDIATE ACTIONS:
   1. Switch to mock mode for non-production work:
      /marketing:generate [path] [audience] --mock

   2. Use Haiku model exclusively (90% cheaper):
      /marketing:generate [path] [audience] --model=haiku

   3. Review recent high-cost operations:
      /marketing:cost-report --days=7

   4. Consider increasing budget or reducing generation frequency

[If within budget:]
   ✅ Current usage is within budget

   Continue best practices:
   • Use Haiku for regular content
   • Use mock mode for testing
   • Monitor weekly: /marketing:cost-report --days=7

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Error Handling

### Example 1: No Cost Data Available

```bash
/marketing:cost-report --days=30
```

**Output** (if cost-tracking.csv doesn't exist):

```
⚠️  NO COST DATA FOUND

The cost tracking file does not exist yet.
This is normal if you haven't generated any content yet.

TO START TRACKING COSTS:
1. Generate content with AI mode (not --mock):
   /marketing:generate [path] [audience] --model=haiku

2. Costs are automatically logged to:
   cost-tracking.csv

3. Then run this command again:
   /marketing:cost-report --days=7
```

### Example 2: Invalid Budget Values

```bash
/marketing:cost-report --budget abc xyz
```

**Output**:

```
❌ Invalid budget values: abc, xyz

Budget values must be numbers (dollars).

EXAMPLES:
  /marketing:cost-report --budget 10 300     # $10/day, $300/month
  /marketing:cost-report --budget 5 150      # $5/day, $150/month
  /marketing:cost-report --budget 20 600     # $20/day, $600/month
```

### Example 3: Invalid Days Value

```bash
/marketing:cost-report --days=abc
```

**Output**:

```
❌ Invalid --days value: abc

Days must be a positive integer.

EXAMPLES:
  /marketing:cost-report --days=7    # Last week
  /marketing:cost-report --days=30   # Last month
  /marketing:cost-report --days=90   # Last quarter
```

## Usage Examples

### Example 1: Weekly Cost Summary

```bash
/marketing:cost-report --days=7
```

**Result**: Shows costs for the last 7 days with model breakdown

### Example 2: Monthly Projection

```bash
/marketing:cost-report --projection
```

**Result**: Projects monthly costs based on current usage pattern

### Example 3: Budget Compliance Check

```bash
/marketing:cost-report --budget 10 300
```

**Result**: Checks if daily spending is under $10 and monthly projection under $300

### Example 4: Quarter Review

```bash
/marketing:cost-report --days=90
```

**Result**: Shows costs for the last 90 days (quarterly review)

### Example 5: Custom Budget Check

```bash
/marketing:cost-report --budget 5 150
```

**Result**: Checks against tighter budget ($5/day, $150/month)

## Integration with Other Commands

### Workflow 1: Cost-Conscious Development

```bash
# 1. Use mock mode for development (zero cost)
/marketing:generate ~/projects/MyApp b2c --mock

# 2. Generate with AI when ready (incurs cost)
/marketing:generate ~/projects/MyApp b2c --model=haiku

# 3. Check costs immediately
/marketing:cost-report --days=1

# 4. Monitor weekly
/marketing:cost-report --days=7
```

### Workflow 2: Budget Management

```bash
# 1. Set budget thresholds at start of month
/marketing:cost-report --budget 10 300

# 2. Generate content throughout month
/marketing:generate [path] [audience] --model=haiku

# 3. Check budget compliance weekly
/marketing:cost-report --budget 10 300

# 4. If approaching limit, switch to mock mode
/marketing:generate [path] [audience] --mock
```

### Workflow 3: Cost Optimization Analysis

```bash
# 1. Generate baseline report
/marketing:cost-report --days=30

# 2. Identify high-cost patterns
# Look for:
# - Too many Sonnet/Opus generations
# - Frequent regenerations
# - High audience count per generation

# 3. Switch to more cost-effective approach
/marketing:generate [path] [audience] --model=haiku --mock

# 4. Compare costs after changes
/marketing:cost-report --days=7
```

## Cost Tracking Details

**CSV Log Location**: `cost-tracking.csv` (in backend directory)

**Logged Information**:

- Timestamp
- Model used (haiku, sonnet, opus)
- Audience generated
- Project name
- Input tokens
- Output tokens
- Estimated cost
- Generation time
- Quality score

**Report Calculations**:

- **Total Cost**: Sum of all estimated costs
- **Average Cost**: Total cost / number of generations
- **Model Usage**: Percentage of generations per model
- **Savings**: Comparison vs. all-Sonnet baseline

**Projection Methodology**:

1. Calculate daily average: Total cost / days elapsed this month
2. Project to month end: Daily average × days in month
3. Trend analysis: Compare current week vs previous week

**Budget Alerts**:

- **Daily**: Triggered if today's spending exceeds daily threshold
- **Monthly**: Triggered if projected monthly cost exceeds monthly threshold

## Best Practices

1. **Check Costs Weekly**

   ```bash
   /marketing:cost-report --days=7
   ```

   Regular monitoring helps catch unexpected spending early

2. **Set Realistic Budgets**
   - Typical usage: $10/day, $300/month
   - Light usage: $5/day, $150/month
   - Heavy usage: $20/day, $600/month

3. **Use Projections for Planning**

   ```bash
   /marketing:cost-report --projection
   ```

   Helps predict monthly costs and adjust usage accordingly

4. **Review Model Distribution**
   - Goal: 80-90% Haiku, 10-20% Sonnet, <5% Opus
   - If too much Sonnet/Opus, consider switching to Haiku

5. **Compare Periods**

   ```bash
   /marketing:cost-report --days=7   # This week
   /marketing:cost-report --days=14  # Last 2 weeks
   ```

   Identify trends and optimize accordingly

## Technical Notes

**Script Location**: `/home/webemo-aaron/projects/prompt-blueprint/shopify-dashboard/backend/src/scripts/track-costs.ts`

**Cost Calculation**:

- **Haiku**: $0.25/1M input tokens, $1.25/1M output tokens
- **Sonnet**: $3.00/1M input tokens, $15.00/1M output tokens
- **Opus**: $15.00/1M input tokens, $75.00/1M output tokens

**Typical Token Usage**:

- Input: ~10,000 tokens (README + prompt)
- Output: ~5,000 tokens (generated content)

**Estimated Costs per Page**:

- Haiku: ~$0.10
- Sonnet: ~$1.00
- Opus: ~$5.00

**Report Generation Speed**: < 1 second (reading CSV is fast)

## Success Criteria

✅ Command executed successfully when:

- Cost tracking CSV file is readable (or properly handles if missing)
- Report type is valid (report, projection, budget)
- Budget values are valid numbers (if in budget mode)
- Days value is valid positive integer (if in report mode)
- Output is formatted and displayed correctly

---

**Related Commands**:

- `/marketing:generate` - Generate content (costs tracked automatically)
- `/marketing:validate-quality` - Quality validation

**Documentation**:

- Cost Tracking: `docs/guides/OPERATIONALIZATION_PLAN.md`
- Model Pricing: `docs/features/DEFAULT_MODEL_CHANGE_HAIKU.md`
- Session Summary: `docs/SESSION_3_COMPLETE_SUMMARY.md`
