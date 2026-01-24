---
description: AI-powered pricing analysis and strategy recommendations
argument-hint: <product-name> [--strategy value|cost-plus|competitive|freemium]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, WebSearch
---

Analyze pricing for: **${ARGUMENTS}**

## Pricing Analysis

**Competitor Research** - Analyze competitor pricing
**Value-Based Pricing** - Calculate based on ROI to customer
**Price Elasticity** - Estimate demand at different price points
**Tier Recommendations** - Suggest Free/Pro/Team/Enterprise tiers
**Psychological Pricing** - $99 vs $100 optimization

Routes to **prompt-engineering-agent**:

```javascript
await Task({
  subagent_type: 'prompt-engineering-agent',
  description: 'Pricing analysis and recommendations',
  prompt: `Analyze pricing strategy for: ${PRODUCT_NAME}

Read product definition from: products/${PRODUCT_NAME}-definition.md

Execute comprehensive pricing analysis:

## 1. Competitor Pricing Research

Search and analyze top 5-10 competitors:
- What do they charge?
- What features at each tier?
- Free trial offerings?
- Annual vs monthly pricing?
- Usage-based vs seat-based?

Create comparison table.

## 2. Value-Based Pricing Calculation

Calculate customer ROI:
- What problem does product solve?
- What's the cost of current solution?
- Time/money saved per month?
- Value delivered = Willingness to pay

Example:
- Current cost: $500/month (manual process)
- Our solution: Automates 80% of work
- Savings: $400/month
- Value-based price: $100-200/month (20-40% of savings)

## 3. Cost-Plus Analysis

Calculate costs:
- Infrastructure costs per customer
- Support costs
- Development amortization
- Target margin (60-80% for SaaS)

Example:
- Infrastructure: $5/customer/month
- Support: $10/customer/month
- Total cost: $15/month
- Target margin: 70%
- Minimum price: $50/month

## 4. Pricing Tier Recommendations

Based on analysis, suggest tiers:

**Free Tier** (Lead Generation):
- Price: $0
- Purpose: Attract users, viral growth
- Limitations: [What's restricted]
- Conversion target: 2-5% to paid

**Starter/Pro** (Primary Revenue):
- Price: $[X]/month
- Target: Individual users, small teams
- Sweet spot for most customers

**Team/Business** (Expansion):
- Price: $[X]/user or $[X] flat
- Target: Growing teams (5-50 users)
- Collaboration features

**Enterprise** (High-value):
- Price: Custom (starting $[X])
- Target: Large orgs (50+ users)
- SSO, SLA, dedicated support

## 5. Psychological Pricing

Test price points:
- $99 vs $100 (charm pricing)
- $49 vs $50 vs $47
- Annual discount (2 months free = 17% off)

## 6. Price Elasticity Simulation

Estimate demand at different prices:
- At $29/month: 1,000 customers = $29,000 MRR
- At $49/month: 600 customers = $29,400 MRR ← Optimal
- At $99/month: 250 customers = $24,750 MRR

## 7. Competitive Positioning

Based on features and market:
- Premium positioning (20% above market)
- Mid-market (at market average)
- Value positioning (20% below market)

Recommend positioning based on differentiation.

## 8. Pricing Strategy Recommendation

Generate final pricing strategy document.
  `
})
```

## Success Criteria

- ✓ Competitor pricing analyzed (5-10 competitors)
- ✓ Value-based pricing calculated
- ✓ Cost-plus validation performed
- ✓ Tier recommendations provided
- ✓ Psychological pricing tested
- ✓ Price elasticity estimated
- ✓ Competitive positioning determined
- ✓ Final pricing strategy document generated

---
**Uses**: prompt-engineering-agent
**Output**: Pricing strategy document (products/[name]-pricing.md)
**Next Commands**: `/product/positioning`, `/landing/create`
