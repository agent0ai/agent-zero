---
description: Analyze subscription churn patterns and predict at-risk customers
argument-hint: [--period 12m|6m|3m] [--create-tasks] [--export csv|json]
model: claude-sonnet-4-5-20250929
allowed-tools: [Bash, Read, Write, Task, WebFetch]
---

# /stripe:analyze-churn

Analyze churn: **${ARGUMENTS:-last 12 months}**

## Step 1: Fetch Stripe Data

```javascript
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

const subscriptions = await stripe.subscriptions.list({ limit: 100 });
const customers = await stripe.customers.list({ limit: 100 });
const events = await stripe.events.list({
  type: 'customer.subscription.deleted',
  created: { gte: startDate }
});
```

## Step 2: Calculate Churn Metrics

```javascript
// Monthly churn rate
const churnRate = (cancelledSubs / totalSubs) * 100;

// Revenue churn
const revenueChurn = (lostMRR / totalMRR) * 100;

// Customer lifetime
const avgLifetime = totalSubscriptionDays / totalCustomers;

// Cohort retention
const cohorts = groupBy(customers, c => getSignupMonth(c));
const retention = cohorts.map(calculateRetention);
```

## Step 3: Identify Churn Patterns

Analyze:

- Time to churn (days from signup)
- Plan-specific churn rates
- Cancellation reasons (if captured)
- Usage patterns before churn
- Failed payments correlation

## Step 4: Predict At-Risk Customers

Flag customers with:

- No usage in X days
- Failed payments
- Downgraded plans
- Support tickets
- Low engagement score

```javascript
const atRiskCustomers = customers.filter(c => {
  const riskScore = calculateRiskScore(c);
  return riskScore > 0.7; // 70% churn risk
});
```

## Step 5: Generate Report

```markdown
# 📉 Churn Analysis Report (${period})

## Overview
- **Churn Rate**: ${churnRate}% (${trend})
- **Revenue Churn**: ${revenueChurn}%
- **Avg Customer Lifetime**: ${avgLifetime} days
- **Total Churned**: ${churnedCount} customers
- **Lost MRR**: $${lostMRR}

## Churn by Plan
| Plan | Churn Rate | Customers Lost | Revenue Impact |
|------|------------|----------------|----------------|
${planChurn.map(p => `| ${p.name} | ${p.rate}% | ${p.count} | -$${p.revenue} |`).join('\n')}

## Time to Churn Distribution
- 0-30 days: ${churn30}%
- 31-90 days: ${churn90}%
- 91-180 days: ${churn180}%
- 180+ days: ${churn180plus}%

## At-Risk Customers (${atRiskCount})
| Customer | Plan | Risk Score | Reason |
|----------|------|------------|--------|
${atRiskCustomers.map(c => `| ${c.name} | ${c.plan} | ${c.riskScore}% | ${c.reason} |`).join('\n')}

## Recommendations
${recommendations.map(r => `- ${r}`).join('\n')}
```

## Step 6: Create CRM Tasks (if requested)

```javascript
if (createTasks) {
  for (const customer of atRiskCustomers) {
    await createZohoCRMTask({
      subject: `At-risk customer: ${customer.name}`,
      description: `Customer shows ${customer.riskScore}% churn risk`,
      priority: 'High'
    });
  }
}
```

**Command Complete** 📉
