---
description: Monitor Shopify product performance + campaign metrics (views, conversions, revenue, ROI)
argument-hint: --product-id <shopify-id> [--period <7d|30d|90d>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Bash, Read
---

Monitor Shopify product performance: **${ARGUMENTS}**

## Shopify Product Performance Monitoring

**Real-Time Metrics** - Views, add-to-cart rate, conversion rate, revenue
**Campaign Performance** - Impressions, clicks, CTR, CPC, ROAS
**Combined Analytics** - Cost-per-acquisition, customer lifetime value
**Trend Analysis** - Performance over time, identify opportunities

## Metrics Tracked

### Shopify Metrics (from Shopify Admin API)

- Product views (last 7/30/90 days)
- Add-to-cart events
- Conversion rate (views → purchases)
- Revenue generated
- Average order value
- Units sold

### Campaign Metrics (from ad platforms)

- Impressions (total reach)
- Clicks (traffic driven)
- CTR (click-through rate)
- CPC (cost per click)
- Conversions (trial signups, purchases)
- CPA (cost per acquisition)
- ROAS (return on ad spend)

### Combined KPIs

- **Cost-per-Acquisition**: Total ad spend ÷ Conversions
- **Customer Lifetime Value**: Average order value × repeat purchase rate × customer lifespan
- **LTV:CAC Ratio**: Customer lifetime value ÷ Cost per acquisition (target: 3:1 or higher)
- **Profit Margin**: (Revenue - Ad Spend - COGS) ÷ Revenue

## Implementation

```javascript
const args = parseArguments(ARGUMENTS)
const productId = args['--product-id']
const period = args['--period'] || '7d'

if (!productId) {
  console.error('Missing required: --product-id')
  console.log('Usage: /shopify:monitor --product-id 1234567890 --period 7d')
  return
}

// Fetch Shopify product data
const product = await fetchShopifyProduct(productId)

// Fetch analytics (Shopify Admin API + Google Analytics)
const shopifyMetrics = await fetchShopifyAnalytics(productId, period)
const campaignMetrics = await fetchCampaignAnalytics(productId, period) // If campaign exists

// Display performance dashboard
displayPerformanceDashboard({
  product,
  shopify: shopifyMetrics,
  campaign: campaignMetrics,
  period
})
```

## Performance Dashboard Output

```markdown
═══════════════════════════════════════════════════
         PRODUCT PERFORMANCE DASHBOARD
═══════════════════════════════════════════════════

PRODUCT: AI Email Assistant
PRODUCT ID: 1234567890
PRODUCT URL: https://yourstore.com/products/ai-email-assistant
PERIOD: Last 7 days

───────────────────────────────────────────────────
SHOPIFY METRICS
───────────────────────────────────────────────────

Views: 1,245
Add to Cart: 98 (7.9% of views)
Purchases: 23 (1.8% of views, 23.5% of add-to-cart)
Revenue: $11,477
Average Order Value: $499
Units Sold: 23

───────────────────────────────────────────────────
CAMPAIGN METRICS
───────────────────────────────────────────────────

Impressions: 45,230
Clicks: 1,389 (3.1% CTR)
Conversions: 23 trial signups
CPC: $3.60
CPA: $10.87
Ad Spend: $5,000
ROAS: 2.3x ($11,477 revenue ÷ $5,000 spend)

Platform Breakdown:
  • Facebook: $2,000 spend → 12 conversions ($166 CPA)
  • Google: $1,500 spend → 8 conversions ($187 CPA)
  • LinkedIn: $1,000 spend → 2 conversions ($500 CPA)
  • Twitter: $500 spend → 1 conversion ($500 CPA)

───────────────────────────────────────────────────
COMBINED KPIs
───────────────────────────────────────────────────

Cost-per-Acquisition: $217.39 (ad spend ÷ conversions)
Customer Lifetime Value: $1,497 (3 months @ $499/mo)
LTV:CAC Ratio: 6.9:1 ✓ (target: >3:1)
Profit Margin: 56% ($6,477 profit ÷ $11,477 revenue)

───────────────────────────────────────────────────
INSIGHTS & RECOMMENDATIONS
───────────────────────────────────────────────────

✓ Strong Performance:
  • LTV:CAC ratio of 6.9:1 exceeds 3:1 target
  • Facebook has best CPA ($166) → Increase budget
  • Add-to-cart rate of 7.9% is above industry average (5%)

⚠️  Optimization Opportunities:
  • LinkedIn CPA is high ($500) → Pause or optimize targeting
  • Twitter CPA is high ($500) → Consider reallocating budget
  • Conversion rate of 1.8% → Test new product page variants

📈 Growth Recommendations:
  1. Increase Facebook budget by 30% ($2,000 → $2,600)
  2. Reallocate LinkedIn/Twitter budgets to Facebook/Google
  3. A/B test product page copy (focus on benefits over features)
  4. Add customer testimonials to product page (increase social proof)
  5. Launch retargeting campaign for add-to-cart abandoners

═══════════════════════════════════════════════════
```

## Success Criteria

- [ ] Fetches real-time Shopify product metrics
- [ ] Combines Shopify + campaign data
- [ ] Calculates LTV:CAC ratio
- [ ] Provides actionable recommendations

---

**Uses**: Shopify Admin API, Google Analytics, Ad Platform APIs
**Update Frequency**: Real-time (run daily or weekly)
