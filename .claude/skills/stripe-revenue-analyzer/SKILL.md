---
name: stripe-revenue-analyzer
description: Analyzes Stripe revenue data for trends, growth patterns, top customers, churn rates, payment success metrics, and subscription health. Provides AI-powered insights and actionable recommendations. Use when analyzing Stripe payment data, subscription metrics, revenue patterns, or financial performance.
---

# Stripe Revenue Analyzer Skill

## What This Skill Does

Provides comprehensive Stripe revenue analysis including:

- **Revenue trends** - Growth/decline patterns over time
- **Top customers** - High-value customers by total spend
- **Payment metrics** - Success rates, failure analysis, dispute patterns
- **Subscription health** - Churn detection, MRR/ARR calculations
- **Customer lifetime value** - LTV predictions and segmentation
- **Seasonal patterns** - Identify recurring patterns and anomalies
- **Anomaly detection** - Flag unusual spikes, drops, or behaviors
- **Actionable recommendations** - Prioritized improvement opportunities

## When This Skill Activates

This skill automatically activates for requests like:

- "Analyze my Stripe revenue"
- "Show me my top Stripe customers"
- "What's my subscription churn rate?"
- "Identify revenue patterns in my Stripe data"
- "How much MRR did we add this quarter?"
- "Which customers are at risk of churning?"
- "Analyze payment success rates"

## Instructions

When activated, follow these steps:

### 1. Data Collection

Request access to Stripe data for the specified time period:

**Required data sources:**

- Charges (successful payments, failures, refunds)
- Subscriptions (active, canceled, past_due)
- Customers (metadata, created dates, total spend)
- Invoices (paid, unpaid, failed)
- Payment intents (status, amounts, currencies)

**Validate data:**

- Confirm time range is clear (default: last 30 days)
- Check for data completeness
- Handle missing or null values gracefully

### 2. Revenue Trend Analysis

**Calculate key metrics:**

- Total revenue for period
- Revenue growth rate (vs previous period)
- Average transaction value
- Transaction count
- Revenue by day/week/month

**Identify trends:**

- Growth acceleration or deceleration
- Week-over-week momentum
- Month-over-month comparisons
- Quarter-over-quarter if applicable

**Format output:**

```
Total Revenue: $X (+Y% vs last period)
Avg Transaction: $Z
Transaction Count: N
Growth Trend: [Accelerating|Steady|Declining]
```

### 3. Top Customers Analysis

**Identify high-value customers:**

- Sort by total spend (all-time)
- Calculate percentage of total revenue
- Identify top 10% (whales)
- Flag recent high-value customers

**Calculate customer metrics:**

- Customer lifetime value (LTV)
- Average order value per customer
- Purchase frequency
- Days since last purchase

**Format output:**

```
Top 10 Customers:
1. [Name/ID]: $X (Y% of revenue)
   - Transactions: N
   - Avg Order: $Z
   - LTV: $A
   - Status: [Active|At Risk|Churned]
```

### 4. Subscription Health Analysis

**Calculate subscription metrics:**

- Monthly Recurring Revenue (MRR)
- Annual Recurring Revenue (ARR)
- Churn rate (monthly and annual)
- New MRR vs churned MRR
- Upgrade vs downgrade rates

**Identify at-risk subscriptions:**

- Past due invoices
- Payment failures
- Upcoming trial expirations
- Downgrade patterns

**Format output:**

```
MRR: $X (+Y% vs last month)
ARR: $Z
Churn Rate: A% (target: <5%)
New MRR: $B
Churned MRR: $C
Net MRR Growth: $D
```

### 5. Payment Success Analysis

**Calculate payment metrics:**

- Overall success rate
- Failure reasons breakdown
- Dispute rate
- Refund rate
- Average time to payment

**Identify issues:**

- Declining cards needing update
- Fraud patterns
- Geographic payment issues
- Currency-specific problems

**Format output:**

```
Payment Success Rate: X% (target: >94%)
Top Failure Reasons:
1. Card declined: Y%
2. Insufficient funds: Z%
3. Expired card: A%

Recommended Actions:
- Update X cards before next billing
- Contact Y customers with payment issues
```

### 6. Anomaly Detection

**Identify unusual patterns:**

- Revenue spikes (>30% above average)
- Revenue drops (>30% below average)
- Sudden churn increases
- Geographic concentration changes
- Product mix shifts

**Correlate with events:**

- Marketing campaigns
- Product launches
- Pricing changes
- Seasonal events
- External factors

**Format output:**

```
Anomalies Detected:
🚨 Revenue spike on [Date]: +X% vs daily average
   Correlation: [Event/Campaign]
   Recommendation: [Action to replicate or investigate]
```

### 7. Insights Generation

**Provide AI-powered insights:**

**Positive signals:**

- What's working well
- Growth drivers
- Successful patterns to replicate

**Areas of concern:**

- What needs attention
- Risk factors
- Declining metrics

**Opportunities:**

- Upsell potential
- New market segments
- Product improvements
- Retention strategies

**Format insights clearly:**

```
✅ Positive Signals:
- [Insight 1 with data]
- [Insight 2 with data]

⚠️ Areas of Concern:
- [Concern 1 with severity]
- [Concern 2 with impact]

💡 Opportunities:
- [Opportunity 1 with potential impact]
- [Opportunity 2 with effort estimate]
```

### 8. Actionable Recommendations

**Prioritize recommendations:**

**Priority 1 (High Impact, Low Effort):**

- Quick wins that move the needle
- Estimated impact in $ or %
- Clear action steps

**Priority 2 (High Impact, High Effort):**

- Strategic initiatives
- Resource requirements
- Timeline estimates

**Priority 3 (Long-term):**

- Research and experimentation
- Future opportunities

**Format recommendations:**

```
Priority 1: Reduce Pro plan churn
- Root cause: [Analysis finding]
- Action: [Specific steps]
- Potential impact: +$X MRR
- Effort: [Low|Medium|High]
- Timeline: [Days/weeks]
```

### 9. Output Formatting

**Structure the complete analysis:**

```markdown
# Stripe Revenue Analysis
Period: [Date Range]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📊 Key Metrics

[Revenue, MRR, transactions, success rate with comparisons]

## 📈 Revenue Trend

[Week-by-week or month-by-month visualization]
[Trend analysis with growth rates]

## 💎 Top Revenue Sources

[Top customers, subscription tiers, products]
[Concentration analysis]

## 🔍 AI Insights

### Positive Signals
[What's working]

### Areas of Concern
[What needs attention]

### Opportunities
[What could be improved]

### Anomalies Detected
[Unusual patterns with explanations]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🎯 Actionable Recommendations

### Priority 1 (High Impact)
[Top recommendations with impact estimates]

### Priority 2 (Quick Wins)
[Low-effort improvements]

### Priority 3 (Long-term)
[Strategic initiatives]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 💰 Projected Impact

Current MRR: $X

Potential MRR (90 days):
  [Rec 1]: +$Y
  [Rec 2]: +$Z
  ─────────────────
  Total Potential: $A (+B%)

Conservative Estimate (50% success):
  New MRR: $C (+D%)
  Annual Impact: +$E

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Quality Standards

**Data accuracy:**

- Verify calculations against Stripe dashboard
- Cross-check totals and percentages
- Handle edge cases (refunds, disputes, credits)

**Insight quality:**

- Base insights on actual data patterns
- Avoid speculation without data support
- Quantify impact whenever possible
- Provide specific, actionable recommendations

**Clarity:**

- Use clear section headers
- Include visual separators (━━━)
- Highlight key numbers with formatting
- Explain technical terms if needed

**Actionability:**

- Every insight should have a recommendation
- Every recommendation should have impact estimate
- Prioritize by impact and effort
- Provide clear next steps

## Example Analysis Triggers

**High-level overview:**

- "Analyze my Stripe revenue for Q4"
- "How's my Stripe business doing?"

**Specific metrics:**

- "What's my current MRR?"
- "Show me subscription churn rate"
- "Which customers spend the most?"

**Problem investigation:**

- "Why did revenue drop last week?"
- "What's causing payment failures?"
- "Which subscriptions are at risk?"

**Strategic planning:**

- "Where should I focus to grow revenue?"
- "How can I reduce churn?"
- "What upsell opportunities exist?"

## Integration with Slash Commands

This skill automatically enhances these commands:

- `/stripe:analyze-revenue` - Provides the core analysis
- `/stripe:test-payment` - Adds success rate context
- Any command working with Stripe data

No explicit invocation needed - skill activates based on request context.

---

*This skill makes Stripe data analysis automatic and comprehensive*
