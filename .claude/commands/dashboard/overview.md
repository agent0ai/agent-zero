---
description: All businesses at a glance with key metrics
argument-hint: "[--format ascii|json|csv] [--export <filename>] [--refresh]"
model: claude-3-5-haiku-20241022
allowed-tools: ["Read", "Bash", "Write", "AskUserQuestion"]
---

# Business Intelligence Dashboard Overview

Display unified business metrics across all active contexts in a single comprehensive dashboard with real-time status and key performance indicators.

## What This Command Does

Aggregates data from all business contexts and presents:

- **Business Summary**: All businesses with status and health indicators
- **Revenue Overview**: Combined revenue, profit, and growth across all units
- **Occupancy/Customer Metrics**: Aggregate fill rates and customer counts
- **Financial Health**: Cash position, burn rate, runway
- **Top Performers**: Best-performing businesses and properties
- **Critical Alerts**: Issues requiring immediate attention

## Why This Matters

Managing multiple businesses requires understanding the complete picture without drilling into each context. Traditional spreadsheets are slow to update and error-prone. This dashboard refreshes in seconds and shows real-time status.

## Usage

```bash
# Display ASCII dashboard
/dashboard:overview

# Export as JSON for integration
/dashboard:overview --format json

# Export as CSV for spreadsheet
/dashboard:overview --format csv

# Export to file
/dashboard:overview --export /path/to/export.json

# Refresh live data
/dashboard:overview --refresh
```

## Dashboard Structure

```
╔═════════════════════════════════════════════════════════════════════════════╗
║                  UNIFIED BUSINESS INTELLIGENCE DASHBOARD                    ║
║                                                                             ║
║  Context: [Active Context]                    Generated: [timestamp]        ║
╚═════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│ 📊 PORTFOLIO SUMMARY                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Total Businesses: 3           Monthly Revenue: $54,250      Health: ✅    │
│  Total Properties: 18          Net Profit: $18,450           Status: GOOD  │
│  Total Customers: 247          Occupancy: 94%                Alerts: 2     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 💰 REVENUE & PROFITABILITY                                                  │
├──────────────────┬──────────────┬──────────────┬──────────────┬─────────────┤
│ Business         │ Monthly Rev  │ Net Profit   │ Growth       │ Status      │
├──────────────────┼──────────────┼──────────────┼──────────────┼─────────────┤
│ Main St Rentals  │ $28,500      │ $10,200      │ +12% vs prev │ ✅ On Track │
│ Elm Court Apts   │ $18,750      │ $6,300       │ +8% vs prev  │ ✅ On Track │
│ Oak Park Homes   │ $7,000       │ $1,950       │ +2% vs prev  │ ⚠️ Needs TLC│
├──────────────────┼──────────────┼──────────────┼──────────────┼─────────────┤
│ PORTFOLIO TOTAL  │ $54,250      │ $18,450      │ +9% vs prev  │ ✅ Healthy  │
└──────────────────┴──────────────┴──────────────┴──────────────┴─────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 🏢 OCCUPANCY & CUSTOMER METRICS                                             │
├──────────────────┬──────────────┬──────────────┬──────────────┬─────────────┤
│ Business         │ Units/Spots  │ Occupied     │ Occupancy    │ Waitlist    │
├──────────────────┼──────────────┼──────────────┼──────────────┼─────────────┤
│ Main St Rentals  │ 12           │ 12           │ 100%         │ 2           │
│ Elm Court Apts   │ 4            │ 4            │ 100%         │ 0           │
│ Oak Park Homes   │ 2            │ 1            │ 50%          │ 0           │
├──────────────────┼──────────────┼──────────────┼──────────────┼─────────────┤
│ PORTFOLIO TOTAL  │ 18           │ 17           │ 94%          │ 2           │
└──────────────────┴──────────────┴──────────────┴──────────────┴─────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 📈 FINANCIAL HEALTH                                                         │
├──────────────────┬──────────────┬──────────────┬──────────────┬─────────────┤
│ Metric           │ Value        │ Target       │ Variance     │ Status      │
├──────────────────┼──────────────┼──────────────┼──────────────┼─────────────┤
│ Cash Reserve     │ $125,800     │ $150,000     │ -$24,200     │ ⚠️ Low      │
│ Monthly Burn     │ $12,400      │ $18,000      │ -$5,600      │ ✅ Good     │
│ Runway (months)  │ 10.1         │ 12.0         │ -1.9         │ ⚠️ Caution  │
│ Profit Margin    │ 34%          │ 35%          │ -1%          │ ✅ Healthy  │
└──────────────────┴──────────────┴──────────────┴──────────────┴─────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 🚨 CRITICAL ALERTS & ACTION ITEMS                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ⚠️  URGENT: Oak Park Home #1 - Vacant since 2/15 (14 days)                 │
│     Action: Schedule maintenance & marketing blitz                          │
│     Impact: $350/month revenue loss                                         │
│                                                                             │
│ ⚠️  Cash Reserve Below Target                                              │
│     Current: $125,800 vs Target: $150,000 (-$24,200)                       │
│     Action: Review expense optimization opportunities                       │
│     Timeline: Address within 30 days                                        │
│                                                                             │
│ ℹ️  Elm Court Apt #3 - Lease expires 3/31/25                              │
│     Action: Initiate renewal discussion in February                         │
│     Status: Tenant satisfaction high (4.8/5)                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ ⭐ TOP PERFORMERS                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ 1st: Main St Rentals                                                       │
│      Revenue: $28,500 | Occupancy: 100% | Growth: +12%                     │
│      Strength: Consistent high occupancy, strong tenant demand             │
│                                                                             │
│ 2nd: Elm Court Apartments                                                  │
│      Revenue: $18,750 | Occupancy: 100% | Growth: +8%                      │
│      Strength: Premium location, corporate tenant base                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 📅 UPCOMING MILESTONES                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ 2/15/25  → Oak Park Property Maintenance Completion (EST)                  │
│ 2/28/25  → January Financial Close & Analysis                              │
│ 3/15/25  → Quarterly Tax Estimated Payment Due                             │
│ 3/31/25  → Elm Court Apt #3 Lease Expiration (Renewal Needed)             │
│ 4/30/25  → Q1 Financial Review & Planning                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 💡 QUICK INSIGHTS & RECOMMENDATIONS                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ✓ Strong Portfolio Performance: 9% growth across all properties             │
│ ✓ Excellent Occupancy: 94% portfolio occupancy with 2-person waitlist      │
│ ⚠ Portfolio Diversification: Heavy reliance on Main St (52% of revenue)    │
│ ⚠ Cash Flow Management: Reserve approaching minimum threshold               │
│ ⚠ Oak Park Underperformance: Property underutilized - optimize             │
│                                                                             │
│ RECOMMENDATION: Prioritize Oak Park property marketing & fill-up            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Generated: 2025-01-22T14:35:00Z | Last Updated: [5 seconds ago]
Data Source: Active Business Context | Next Refresh: In 4:55 minutes
```

## Data Sources

Dashboard pulls data from:

- **Active Context System**: Current business context (see `/context:switch`)
- **Financial Data**: Monthly revenue, expenses, profit
- **Occupancy Data**: Units/properties, tenant count, vacancy
- **Zoho CRM Integration**: Customer counts and metrics
- **Alert System**: Critical issues from all businesses

## Export Formats

### JSON Export

```json
{
  "generated": "2025-01-22T14:35:00Z",
  "portfolio": {
    "total_businesses": 3,
    "total_properties": 18,
    "total_customers": 247,
    "monthly_revenue": 54250,
    "net_profit": 18450,
    "occupancy_rate": 0.94,
    "health_status": "GOOD"
  },
  "businesses": [
    {
      "name": "Main St Rentals",
      "monthly_revenue": 28500,
      "net_profit": 10200,
      "occupancy": 1.0,
      "growth_rate": 0.12,
      "status": "ON_TRACK"
    }
  ],
  "alerts": [
    {
      "severity": "HIGH",
      "message": "Oak Park Property Vacant",
      "impact": 350,
      "action_required": true
    }
  ]
}
```

### CSV Export

```
Business,Monthly Revenue,Net Profit,Occupancy %,Growth %,Status,Alert Count
Main St Rentals,28500,10200,100,12,ON_TRACK,0
Elm Court Apts,18750,6300,100,8,ON_TRACK,0
Oak Park Homes,7000,1950,50,2,NEEDS_TLC,1
PORTFOLIO_TOTAL,54250,18450,94,9,HEALTHY,2
```

## Refresh Behavior

- **Automatic**: Dashboard refreshes every 5 minutes if running
- **Manual**: Use `--refresh` flag to update immediately
- **Smart Caching**: Frequently accessed data cached for sub-second display
- **Real-time Alerts**: Critical alerts display immediately without waiting for refresh

## Context Integration

Dashboard automatically displays data for:

- **Active Context**: The business currently selected (from `/context:switch`)
- **Related Contexts**: Child properties/units of parent business
- **Full Portfolio**: Optionally show aggregated data across all contexts

## Success Metrics

- ✓ Full portfolio view in <2 seconds
- ✓ ASCII dashboard displays cleanly in terminal
- ✓ Export to JSON/CSV/PDF successful
- ✓ All critical alerts visible and actionable
- ✓ Real-time data refresh functional
- ✓ Mobile-friendly format option available

## Recommended Frequency

- **Daily Review**: Executive summary before daily standup (2 min)
- **Weekly Analysis**: Deep dive on metrics and trends (15 min)
- **Monthly Review**: Comprehensive analysis and planning (30 min)

## Related Commands

- `/dashboard:property <id>` - Single property P&L details
- `/dashboard:alerts` - Cross-business alerts and notifications
- `/dashboard:kpi` - Key performance indicator tracking with trends
- `/context:switch` - Switch between business contexts
- `/finance:report` - Detailed financial reports
- `/sales:pipeline` - Sales pipeline metrics

## Integration Points

- **Zoho CRM**: Customer and revenue data
- **QuickBooks**: Financial and expense data
- **Google Calendar**: Upcoming milestones and deadlines
- **Context System**: Business and property information

---

*Your complete business overview in one glance. Perfect for executive reviews, investor updates, and strategic planning.*
