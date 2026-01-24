---
description: Generate AI-powered Stripe revenue analysis with trends, insights, and recommendations
argument-hint: "[--period <week|month|quarter|year>] [--format <summary|detailed|executive>]"
model: claude-3-5-sonnet-20241022
allowed-tools:
  - Bash
  - Skill
  - Write
---

# Stripe Revenue Analysis Command

**SKILL-POWERED COMMAND** - Demonstrates Claude Code Skills integration

## Overview

Generates comprehensive revenue analysis from Stripe data using AI-powered skills. This command orchestrates multiple reusable skills to:

- Fetch revenue data from Stripe
- Analyze trends and patterns
- Identify insights and anomalies
- Generate visualizations
- Provide actionable recommendations

## What This Command Does

- ✅ Fetches Stripe revenue data for specified period
- ✅ Analyzes revenue trends (growth/decline)
- ✅ Identifies top revenue sources
- ✅ Calculates key metrics (MRR, churn, LTV)
- ✅ Detects anomalies and unusual patterns
- ✅ Generates AI insights and recommendations
- ✅ Creates visualizations (charts, graphs)
- ✅ Exports formatted reports

## Skills Used

This command demonstrates **Skills composition** - combining multiple reusable capabilities:

1. **stripe-data-fetcher** (if available): Fetches data from Stripe API
2. **data-analyzer** (if available): AI-powered data analysis
3. **chart-generator** (if available): Creates visualizations
4. **report-writer** (if available): Formats professional reports

**Note**: This command works with or without skills. If skills aren't available, uses inline logic.

## Usage

```bash
# Analyze this month's revenue
/stripe:analyze-revenue

# Analyze specific period
/stripe:analyze-revenue --period quarter

# Detailed analysis
/stripe:analyze-revenue --format detailed

# Executive summary
/stripe:analyze-revenue --format executive
```

## Implementation

This command shows two approaches:

### Approach 1: With Skills (Preferred)

```
1. Check if stripe-data-fetcher skill exists
   → If yes: Invoke skill to fetch data
   → If no: Use inline Stripe CLI commands

2. Check if data-analyzer skill exists
   → If yes: Invoke skill for AI analysis
   → If no: Use inline analysis logic

3. Check if chart-generator skill exists
   → If yes: Invoke skill for visualizations
   → If no: Generate ASCII charts inline

4. Check if report-writer skill exists
   → If yes: Invoke skill for formatting
   → If no: Format inline
```

### Approach 2: Inline (Fallback)

If skills aren't available, command has inline fallback logic.

## Example Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 STRIPE REVENUE ANALYSIS
Period: Last 30 Days (Dec 25, 2024 - Jan 24, 2025)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 KEY METRICS

Total Revenue: $45,250
  vs Last Period: +12.5% ↑

Monthly Recurring Revenue (MRR): $12,800
  vs Last Period: +8.3% ↑

Average Transaction Value: $89.50
  vs Last Period: +3.2% ↑

Transaction Count: 506
  vs Last Period: +9.1% ↑

Success Rate: 94.2%
  vs Last Period: +1.1% ↑

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 REVENUE TREND (Last 30 Days)

Week 1: $9,450  ████████████████
Week 2: $10,200 ████████████████████
Week 3: $12,150 ████████████████████████
Week 4: $13,450 ████████████████████████████

Trend: Consistent growth (+42% week 1 vs week 4)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💎 TOP REVENUE SOURCES

1. Enterprise Subscriptions: $18,900 (41.8%)
   • 45 active subscriptions
   • Avg: $420/month
   • Churn: 2.1% (excellent)

2. Pro Subscriptions: $14,200 (31.4%)
   • 142 active subscriptions
   • Avg: $100/month
   • Churn: 5.8% (acceptable)

3. One-time Payments: $8,350 (18.5%)
   • 89 transactions
   • Avg: $93.82/transaction

4. Add-ons & Upgrades: $3,800 (8.4%)
   • 67 transactions
   • Primarily mid-month upgrades

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 AI INSIGHTS (Powered by data-analyzer skill)

Positive Signals:
✅ Revenue growth accelerating (week-over-week)
✅ Enterprise churn at record low (2.1%)
✅ Average transaction value trending up
✅ Payment success rate above target (>94%)

Areas of Concern:
⚠️  Pro plan churn slightly elevated (5.8% vs 4.5% target)
⚠️  One-time payment volume declining (-3% vs last period)

Opportunities:
💡 Mid-month upgrades trending (67 this month vs 45 last month)
   → Consider promoting mid-cycle upgrades more prominently

💡 Enterprise plan showing strong retention
   → Upsell more Pro users to Enterprise (potential +$8K MRR)

Anomalies Detected:
🚨 Revenue spike on Jan 15-17 (+45% vs daily average)
   → Correlated with product launch campaign
   → Consider replicating campaign structure quarterly

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 ACTIONABLE RECOMMENDATIONS

Priority 1 (High Impact):
1. Reduce Pro plan churn
   • Root cause: Analyze exit surveys from churned users
   • Action: Implement win-back campaign for at-risk users
   • Potential Impact: +$1,200 MRR (if churn reduced to 4%)

2. Accelerate Pro → Enterprise upsells
   • Target: Users with >10 team members on Pro
   • Offer: Personal onboarding call + first month 50% off
   • Potential Impact: +$8,000 MRR (if 20 users upgrade)

Priority 2 (Quick Wins):
3. Replicate Jan 15-17 campaign success
   • What worked: Email + social + limited-time offer
   • When: Execute quarterly (next: April 15-17)
   • Potential Impact: +$6,000 revenue per campaign

4. Promote mid-cycle upgrades
   • Add upgrade CTA in product (shown day 10-20 of billing cycle)
   • Highlight value gained by upgrading now vs waiting
   • Potential Impact: +$2,000 MRR (if 20 more upgrades/month)

Priority 3 (Long-term):
5. Investigate one-time payment decline
   • Hypothesis: Users prefer subscriptions (good)
   • Action: Test converting one-time to subscription option
   • Potential Impact: +$3,000 MRR (if 30% convert)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 PROJECTED IMPACT (If Recommendations Implemented)

Current MRR: $12,800

Potential MRR (90 days):
  Reduce Pro churn:        +$1,200
  Pro → Enterprise upsells: +$8,000
  Mid-cycle upgrades:       +$2,000
  One-time conversions:     +$3,000
  ────────────────────────────────
  Total Potential MRR:     $27,000 (+111%)

Conservative Estimate (50% success rate):
  New MRR: $19,900 (+55%)
  Annual Impact: +$85,200

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Full Report Saved To:
  ./stripe-revenue-analysis-2025-01-24.md

📈 Next Steps:
  [1] Review recommendations with team
  [2] Prioritize initiatives
  [3] Track implementation impact
  [4] Re-run analysis next month

🔄 Schedule Monthly:
  Add to calendar: /stripe:analyze-revenue (1st of each month)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ Analysis powered by:
  • stripe-data-fetcher skill (data retrieval)
  • data-analyzer skill (AI insights)
  • chart-generator skill (visualizations)
  • report-writer skill (formatting)
```

## Implementation Details

### Step 1: Fetch Stripe Data

```bash
# Try to use stripe-data-fetcher skill
# If not available, use Stripe CLI directly

# Fetch revenue data for period
stripe charges list \
  --created[gte]=$(date -d "30 days ago" +%s) \
  --limit=1000 \
  --expand=data.customer \
  --format=json > stripe-charges.json

stripe subscriptions list \
  --status=active \
  --limit=1000 \
  --format=json > stripe-subscriptions.json
```

### Step 2: Analyze Data

```bash
# Try to invoke data-analyzer skill
# If not available, use inline analysis

# Calculate key metrics
TOTAL_REVENUE=$(jq '[.data[].amount] | add' stripe-charges.json)
TRANSACTION_COUNT=$(jq '.data | length' stripe-charges.json)
MRR=$(jq '[.data[].plan.amount] | add' stripe-subscriptions.json)

# AI-powered insights (via skill or Claude API)
INSIGHTS=$(invoke data-analyzer skill OR call Claude API with data)
```

### Step 3: Generate Visualizations

```bash
# Try to invoke chart-generator skill
# If not available, generate ASCII charts

# Revenue trend chart (last 4 weeks)
# [Chart generation logic]
```

### Step 4: Format Report

```bash
# Try to invoke report-writer skill
# If not available, format inline

# Combine all sections into formatted report
# Save to file
# Display to user
```

## Skills Integration Fallback

This command demonstrates graceful degradation:

```
if skill_exists("stripe-data-fetcher"); then
    invoke skill
else
    use inline Stripe CLI commands
fi

if skill_exists("data-analyzer"); then
    invoke skill for AI insights
else
    use Claude API directly or basic analysis
fi

# ... and so on for other skills
```

**Result**: Command works with or without skills, but is more powerful with them.

## Benefits of Skills Approach

### Without Skills (This Command Only)

- 400+ lines of code in one command
- All logic inline
- Hard to reuse
- Difficult to maintain

### With Skills (Composable)

- 50 lines of orchestration in command
- 4 reusable skills (used by multiple commands)
- Easy to update (modify skill, all commands benefit)
- Clear separation of concerns

## Related Commands

- `/stripe:churn-analysis` - Also uses data-analyzer skill
- `/stripe:customer-insights` - Also uses stripe-data-fetcher skill
- `/stripe:executive-dashboard` - Combines multiple skills

## Related Skills

- `stripe-data-fetcher`: Fetch Stripe API data
- `data-analyzer`: AI-powered data analysis
- `chart-generator`: Create visualizations
- `report-writer`: Format professional reports

## Notes

**Skills Optional**: Command works without skills (uses inline logic)

**Skills Preferred**: With skills, command is more powerful and maintainable

**Create Skills**: See `docs/SKILLS-INTEGRATION-GUIDE.md` for how to create skills

---

*This command demonstrates the power of composable, skill-powered slash commands*
