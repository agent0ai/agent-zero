---
description: Track key performance indicators with trends and benchmarks
argument-hint: "[--period month|quarter|year|all] [--business <name>] [--format ascii|json] [--export <filename>]"
model: claude-3-5-haiku-20241022
allowed-tools: ["Read", "Bash", "Write", "AskUserQuestion"]
---

# Key Performance Indicators (KPI) Dashboard

Comprehensive KPI tracking system showing current performance against targets, historical trends, and predictive insights for all key business metrics.

## What This Command Does

Tracks and visualizes all critical KPIs:

- **Financial KPIs**: Revenue, profit, margin, cash flow, burn rate
- **Occupancy KPIs**: Fill rate, turnover, vacancy rate, days to fill
- **Operational KPIs**: Maintenance response time, quality scores, customer satisfaction
- **Growth KPIs**: Revenue growth rate, tenant acquisition cost, retention rate
- **Health Indicators**: Trend analysis, projections, variance from target
- **Benchmarking**: Performance vs industry standards and historical baselines
- **Actionable Insights**: What's working, what needs attention, forecast

## Why This Matters

Managing multiple businesses without KPI tracking means you're operating blind. You can't optimize what you don't measure. This dashboard surfaces the metrics that actually drive business success and shows whether you're winning or losing in each area.

## Usage

```bash
# Show all KPIs for active context
/dashboard:kpi

# Show KPIs for specific period
/dashboard:kpi --period month
/dashboard:kpi --period quarter
/dashboard:kpi --period year

# Show KPIs for specific business
/dashboard:kpi --business "Main St Rentals"

# Export data for analysis
/dashboard:kpi --format json --export kpi-data.json

# Show all-time performance
/dashboard:kpi --period all
```

## Dashboard Structure

```
╔═════════════════════════════════════════════════════════════════════════════╗
║                      KEY PERFORMANCE INDICATORS (KPI) DASHBOARD             ║
║                                                                             ║
║  Business: All Properties | Period: This Month (Jan 2025)                   ║
║  Generated: 2025-01-22T14:35:00Z | Dashboard Health: ✅ All Systems OK      ║
╚═════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│ 💰 FINANCIAL KPIs                                                           │
├─────────────────────────────────┬──────────┬──────────┬──────────┬──────────┤
│ KPI                             │ Current  │ Target   │ Variance │ Trend    │
├─────────────────────────────────┼──────────┼──────────┼──────────┼──────────┤
│ MONTHLY REVENUE                 │          │          │          │          │
│ Total Monthly Revenue           │ $54,250  │ $50,000  │ +$4,250  │ ↗ Up 9%  │
│ Revenue per Unit                │ $3,014   │ $2,778   │ +$236    │ ↗ Up 4%  │
│ Revenue Growth (YoY)            │ +9%      │ +8%      │ +1%      │ ✅ Exceeding
│ Revenue Growth (MoM)            │ +2.1%    │ +1.5%    │ +0.6%    │ ✅ Exceeding
│                                 │          │          │          │          │
│ PROFITABILITY                   │          │          │          │          │
│ Net Profit                      │ $18,450  │ $15,000  │ +$3,450  │ ↗ Up 28% │
│ Profit Margin                   │ 34%      │ 35%      │ -1%      │ ↗ Improving
│ Operating Margin (NOI)          │ 42%      │ 40%      │ +2%      │ ✅ Excellent
│ Profit per Unit                 │ $1,538   │ $1,250   │ +$288    │ ↗ Up 15% │
│                                 │          │          │          │          │
│ EXPENSE MANAGEMENT              │          │          │          │          │
│ Operating Expense Ratio         │ 64%      │ 65%      │ -1%      │ ✅ Improving
│ Expense per Unit/Month          │ $1,476   │ $1,500   │ -$24     │ ✅ Below target
│ Expense Growth (YoY)            │ +3%      │ +4%      │ -1%      │ ✅ Controlled
│                                 │          │          │          │          │
│ CASH FLOW                       │          │          │          │          │
│ Monthly Cash Generated          │ $15,250  │ $12,000  │ +$3,250  │ ↗ Strong
│ Cash Reserve                    │ $125,800 │ $150,000 │ -$24,200 │ ⚠️ Below  │
│ Cash Runway (months)            │ 10.1     │ 12.0     │ -1.9     │ ⚠️ Caution│
│ Monthly Burn Rate               │ $12,400  │ $18,000  │ -$5,600  │ ✅ Healthy
│                                 │          │          │          │          │
│ RETURN ON INVESTMENT (ROI)      │          │          │          │          │
│ Overall ROI (Annualized)        │ 18.4%    │ 15%      │ +3.4%    │ ✅ Strong │
│ Cap Rate (Portfolio)            │ 8.1%     │ 7.5%     │ +0.6%    │ ✅ Solid  │
│ Cash-on-Cash Return             │ 4.2%     │ 4.0%     │ +0.2%    │ ✅ Meeting
│ Debt Service Coverage           │ 1.5x     │ 1.25x    │ +0.25x   │ ✅ Strong │
│                                 │          │          │          │          │
│ PRICING & RATES                 │          │          │          │          │
│ Average Rent per Unit           │ $225.40  │ $230.00  │ -$4.60   │ ⚠️ Slightly low
│ Year-over-Year Rent Growth      │ +6.2%    │ +6%      │ +0.2%    │ ✅ Meeting
│ Rent Increase Implementation    │ 100%     │ 100%     │ 0%       │ ✅ On-time
│ Market Rent for Similar Units   │ $240-250 │ —        │ -$15-25  │ ⚠️ Below market
│
└─────────────────────────────────┴──────────┴──────────┴──────────┴──────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 🏘️ OCCUPANCY & OPERATIONAL KPIs                                            │
├─────────────────────────────────┬──────────┬──────────┬──────────┬──────────┤
│ KPI                             │ Current  │ Target   │ Variance │ Trend    │
├─────────────────────────────────┼──────────┼──────────┼──────────┼──────────┤
│ OCCUPANCY RATES                 │          │          │          │          │
│ Portfolio Occupancy Rate        │ 94.4%    │ 95%      │ -0.6%    │ ↗ Stable  │
│ Main St Rentals Occupancy       │ 100%     │ 95%      │ +5%      │ ✅ Excellent
│ Elm Court Apts Occupancy        │ 100%     │ 95%      │ +5%      │ ✅ Excellent
│ Oak Park Homes Occupancy        │ 50%      │ 90%      │ -40%     │ ⚠️ Problem │
│ Occupied Units                  │ 17/18    │ 17/18    │ 0        │ ↔️ Stable  │
│ Vacant Units                    │ 1        │ <1       │ +1       │ ↔️ Stable  │
│                                 │          │          │          │          │
│ TURNOVER & VACANCY              │          │          │          │          │
│ Annual Turnover Rate            │ 4.5%     │ 6%       │ -1.5%    │ ✅ Below target (good)
│ Average Vacancy Duration        │ 8.2 days │ 10 days  │ -1.8 days│ ✅ Fast turnaround
│ Days to Fill (New Unit)         │ 8.2 days │ 12 days  │ -3.8 days│ ✅ Quick filling
│ Lease Renewal Rate              │ 92%      │ 90%      │ +2%      │ ✅ High retention
│ Voluntary Moves Out             │ 4.2%/yr  │ 5%/yr    │ -0.8%    │ ✅ Low churn
│ Involuntary Moves Out           │ 0.3%/yr  │ 1%/yr    │ -0.7%    │ ✅ Low evictions
│                                 │          │          │          │          │
│ CUSTOMER METRICS                │          │          │          │          │
│ Total Tenants (Active)          │ 17       │ 18       │ -1       │ ↔️ Stable  │
│ Average Tenant Tenure           │ 3.2 yrs  │ 3 yrs    │ +0.2 yrs │ ✅ Stable  │
│ Tenant Satisfaction (NPS)       │ 72       │ 70       │ +2       │ ✅ Good    │
│ Average Tenant Rating           │ 4.7/5    │ 4.5/5    │ +0.2     │ ✅ High    │
│ New Tenant Acquisition Cost     │ $450     │ $500     │ -$50     │ ✅ Efficient
│ Cost to Retain vs Acquire Ratio │ 0.3x     │ 0.5x     │ -0.2x    │ ✅ Favorable
│                                 │          │          │          │          │
│ MAINTENANCE & QUALITY           │          │          │          │          │
│ Avg Maintenance Response Time   │ 2.1 days │ 2 days   │ +0.1 days│ ↔️ Stable  │
│ Emergency Response Time         │ 4.3 hrs  │ 4 hrs    │ +0.3 hrs │ ✅ Good    │
│ Maintenance Cost per Unit/Month │ $10.00   │ $12.00   │ -$2.00   │ ✅ Below   │
│ Maintenance Cost as % Revenue   │ 4.4%     │ 5%       │ -0.6%    │ ✅ Efficient
│ Unit Condition Score            │ 9.2/10   │ 9/10     │ +0.2     │ ✅ Excellent
│ Complaint Resolution Rate       │ 95%      │ 90%      │ +5%      │ ✅ High    │
│                                 │          │          │          │          │
│ PAYMENT & COLLECTIONS           │          │          │          │          │
│ Rent Collection Rate            │ 99%      │ 99%      │ 0%       │ ✅ Excellent
│ Days Sales Outstanding (DSO)    │ 0.5 days │ 1 day    │ -0.5 days│ ✅ Fast    │
│ Late Payment Rate               │ 1%       │ 1%       │ 0%       │ ✅ Low     │
│ Bad Debt Ratio                  │ 0.2%     │ 0.5%     │ -0.3%    │ ✅ Very low
│ Payment Methods Accepted        │ 5        │ 4        │ +1       │ ↗ Improving
│
└─────────────────────────────────┴──────────┴──────────┴──────────┴──────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 📈 GROWTH & STRATEGIC KPIs                                                  │
├─────────────────────────────────┬──────────┬──────────┬──────────┬──────────┤
│ KPI                             │ Current  │ Target   │ Variance │ Trend    │
├─────────────────────────────────┼──────────┼──────────┼──────────┼──────────┤
│ GROWTH METRICS                  │          │          │          │          │
│ Revenue Growth (12-Month)       │ +9%      │ +8%      │ +1%      │ ✅ Exceeding
│ Portfolio Value Appreciation    │ +6.8%    │ +5%      │ +1.8%    │ ✅ Exceeding
│ Market Share Growth             │ +4.2%    │ +3%      │ +1.2%    │ ✅ Growing │
│ Customer Base Growth            │ +8%      │ +6%      │ +2%      │ ✅ Expanding
│ Unit Acquisition Rate           │ 0 units  │ 2 units  │ -2       │ — On hold  │
│                                 │          │          │          │          │
│ COMPETITIVE POSITIONING         │          │          │          │          │
│ Price vs Market Average         │ -$15-25  │ At market│ -$20     │ ⚠️ Slightly underpriced
│ Quality vs Competitors          │ Above avg│ Average+ │ +        │ ✅ Competitive advantage
│ Tenant Retention vs Market      │ 92%      │ 85%      │ +7%      │ ✅ Better  │
│ Occupancy vs Market Average     │ 94.4%    │ 92%      │ +2.4%    │ ✅ Better  │
│                                 │          │          │          │          │
│ SCALE & EFFICIENCY              │          │          │          │          │
│ Revenue per Employee/Manager    │ $27,125  │ $25,000  │ +$2,125  │ ✅ Efficient
│ Administrative Cost Ratio       │ 8%       │ 10%      │ -2%      │ ✅ Lean    │
│ Technology Investment           │ $1,200/yr│ $1,500/yr│ -$300    │ ⚠️ Below   │
│ Staff Productivity Index        │ 94%      │ 90%      │ +4%      │ ✅ High    │
│
└─────────────────────────────────┴──────────┴──────────┴──────────┴──────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 📊 TREND ANALYSIS - Last 6 Months                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Monthly Revenue Trend                                                       │
│ $60K │                                                                     │
│      │                                              ●                      │
│ $55K │                                          ●       ●                  │
│      │                                      ●               ●              │
│ $50K │                                  ●                       ●          │
│      │                              ●                               ●      │
│ $45K │                          ●                                           │
│      │                                                                     │
│      └────────────────────────────────────────────────────────────────    │
│        Aug   Sep   Oct   Nov   Dec   Jan                                   │
│                                                                             │
│ Trend: ↗ STRONGLY POSITIVE | Growth: +9% | Status: ✅ EXCELLENT            │
│                                                                             │
│ Occupancy Rate Trend                                                        │
│ 100% │  ●●● ●●● ●●● ●●● ●●●                                              │
│      │                  ●                                                  │
│  95% │                                                                     │
│      │                                                                     │
│  90% │                                                                     │
│      │                                                                     │
│  85% │                                                                     │
│      └────────────────────────────────────────────────────────────────    │
│        Aug   Sep   Oct   Nov   Dec   Jan                                   │
│                                                                             │
│ Trend: ↗ STABLE WITH SPIKE | Avg: 93% | Status: ✅ STRONG                 │
│                                                                             │
│ Net Profit Margin Trend                                                     │
│  40% │                                              ●                      │
│      │                                          ●       ●                  │
│  35% │                                      ●               ●              │
│      │                                  ●                       ●          │
│  30% │                              ●                               ●      │
│      │                                                                     │
│  25% │                                                                     │
│      └────────────────────────────────────────────────────────────────    │
│        Aug   Sep   Oct   Nov   Dec   Jan                                   │
│                                                                             │
│ Trend: ↗ IMPROVING | Change: +8% | Status: ✅ POSITIVE                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 🎯 PERFORMANCE MATRIX                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ EXCEEDING TARGET (35% of KPIs)          ✅ MEETING TARGET (45% of KPIs)    │
│                                                                             │
│ ✅ Revenue Growth                        ✅ Operating Expense Ratio         │
│ ✅ Net Profit Growth                     ✅ Occupancy Rate                  │
│ ✅ Operating Margin                      ✅ Tenant Satisfaction             │
│ ✅ Cash Flow                             ✅ Rent Collection Rate            │
│ ✅ Turnover Rate                         ✅ Maintenance Response Time       │
│ ✅ Tenant Retention                      ✅ Staff Productivity              │
│ ✅ ROI Performance                       ✅ Market Positioning              │
│                                                                             │
│                                                                             │
│ ⚠️ BELOW TARGET (20% of KPIs)           — NO DATA (0% of KPIs)             │
│                                                                             │
│ ⚠️ Cash Reserve Level (-$24.2K)         [None]                             │
│ ⚠️ Oak Park Occupancy (-40%)                                                │
│ ⚠️ Average Rent vs Market                                                   │
│ ⚠️ Capital Reserve Funding                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 🚀 FORECASTING & PROJECTIONS                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Q1 2025 PROJECTIONS (Based on Current Trajectory)                          │
│                                                                             │
│ Revenue Forecast:                    $54,250/mo → $56,850/mo by Mar 2025   │
│ Estimated Quarterly Total:           ~$165,950 (assuming growth continues) │
│ Variance from Target:                +$9,950 (6% above budget)              │
│ Confidence Level:                    85% (stable trends, no major issues)  │
│                                                                             │
│ Profit Forecast:                     $18,450/mo → $19,200/mo by Mar 2025   │
│ Estimated Quarterly Total:           ~$56,050                              │
│ Variance from Target:                +$5,050 (9% above budget)              │
│                                                                             │
│ Occupancy Forecast:                  94.4% → 96% by Mar 2025               │
│ Key Driver:                          Oak Park property fill-up expected    │
│ Risk:                                If Oak Park remains vacant, drops to ~92%
│                                                                             │
│ Cash Reserve Forecast:               $125,800 → $142,250 by Mar 2025       │
│ Status:                              Will reach $150K target by May 2025    │
│ Action:                              Continue current spending patterns     │
│                                                                             │
│ Year-End 2025 PROJECTIONS            (9-12 Month Forecast)                │
│                                                                             │
│ Full Year Revenue:                   ~$675,000 (assuming +9% growth)        │
│ Annual Profit:                       ~$230,000 (assuming 34% margins)      │
│ Portfolio Value:                     ~$1,320,000 (6.8% appreciation)       │
│ ROI:                                 18.4% annualized                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 💡 KEY INSIGHTS & RECOMMENDATIONS                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ TOP PERFORMERS:                                                             │
│ 🏆 Main St Rentals - 100% occupancy, strong growth trajectory               │
│ 🏆 Revenue Growth - Exceeding targets by 1% (+9% vs +8% target)             │
│ 🏆 Tenant Retention - 92% renewal rate well above 85% market avg            │
│                                                                             │
│ AREAS FOR IMPROVEMENT:                                                      │
│ ⚠️ Oak Park Property - 50% occupancy vs 90% target (-40% variance)          │
│    Action: Aggressive marketing + rent optimization for Q1                  │
│    Impact Potential: +$350/month if filled                                  │
│                                                                             │
│ ⚠️ Cash Reserve - $24.2K below target                                       │
│    Action: Continue current positive cash flow to rebuild                   │
│    Timeline: Reach target by May 2025 (4 months)                            │
│                                                                             │
│ ⚠️ Market Rent Positioning - $15-25 below comparable units                  │
│    Action: Implement 8-10% increase at lease renewals                       │
│    Opportunity: +$180-225/month annual revenue (if implemented)             │
│                                                                             │
│ STRATEGIC OPPORTUNITIES:                                                    │
│ → Portfolio Expansion: Current cash flow and ROI support acquisition         │
│ → Operational Leverage: Systems in place for faster scaling                 │
│ → Market Penetration: Strong brand + tenant satisfaction for growth         │
│                                                                             │
│ RISK MITIGATION:                                                            │
│ ✓ Diversification: Consider 2-3 additional properties to reduce dependency  │
│ ✓ Technology: Upgrade property management system (currently at 8%/budget)   │
│ ✓ Staffing: Hire dedicated maintenance coordinator for maintenance backlog  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 📋 EXECUTIVE SUMMARY                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ OVERALL BUSINESS HEALTH:        ✅ EXCELLENT (88/100)                       │
│                                                                             │
│ Portfolio performing above expectations with strong revenue growth, solid   │
│ profitability, and excellent tenant metrics. Two properties performing     │
│ exceptionally well (Main St, Elm Court). One property (Oak Park) needs     │
│ attention for occupancy optimization.                                      │
│                                                                             │
│ Financial position strong with positive cash flow. Reserve below target    │
│ but trajectory shows recovery by May 2025.                                 │
│                                                                             │
│ Recommendations: Fill Oak Park vacancy, implement rent optimization at    │
│ lease renewals, and continue current operational discipline.               │
│                                                                             │
│ Outlook: Positive. Q1 2025 projections show continued growth (+9% revenue, │
│ +28% profit). Full year 2025 expected to deliver $675K revenue and        │
│ $230K profit, maintaining 18.4% ROI.                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Generated: 2025-01-22T14:35:00Z | Report Period: January 2025
Calculated from: Active Context + Historical Data | Next Update: 2025-02-22
```

## Export Formats

### JSON Export

```json
{
  "generated": "2025-01-22T14:35:00Z",
  "period": "month",
  "summary": {
    "overall_health_score": 88,
    "status": "EXCELLENT"
  },
  "kpis": {
    "financial": {
      "monthly_revenue": {
        "current": 54250,
        "target": 50000,
        "variance": 4250,
        "trend": "UP_9_PERCENT"
      },
      "net_profit": {
        "current": 18450,
        "target": 15000,
        "variance": 3450,
        "trend": "UP_28_PERCENT"
      }
    },
    "occupancy": {
      "portfolio_rate": 0.944,
      "target": 0.95,
      "variance": -0.006,
      "trend": "STABLE"
    }
  },
  "forecasts": {
    "q1_2025": {
      "revenue": 165950,
      "profit": 56050,
      "confidence": 0.85
    }
  }
}
```

## KPI Categories

### Financial KPIs

- Monthly revenue and growth
- Net profit and margins
- Operating expense ratio
- Cash flow and burn rate
- Return on investment

### Operational KPIs

- Occupancy rates
- Tenant turnover
- Maintenance response time
- Payment collection rate
- Customer satisfaction

### Growth KPIs

- Year-over-year growth
- Market share changes
- Portfolio expansion
- Competitive positioning
- Unit acquisition rate

## Success Metrics

- ✓ All KPIs displayed with current values
- ✓ Targets and variances clearly shown
- ✓ Trend indicators accurate
- ✓ Forecasts generated with confidence levels
- ✓ Industry benchmarks provided
- ✓ Actionable insights delivered
- ✓ Export functionality working
- ✓ Visual trends visible

## Dashboard Features

- **Real-time Updates**: KPIs refresh as data changes
- **Custom Targets**: Set individual targets per metric
- **Benchmarking**: Compare against industry standards
- **Alerting**: Get notified when KPI thresholds breached
- **Forecasting**: Predictive analytics for planning
- **Trending**: 6+ month historical trend analysis
- **Drill-Down**: Click metrics for detailed analysis

## Related Commands

- `/dashboard:overview` - Full portfolio status
- `/dashboard:property <id>` - Property-specific KPIs
- `/dashboard:alerts` - KPI threshold alerts
- `/finance:report` - Detailed financial analysis

---

*Track what matters. Know exactly how your business is performing against targets, benchmarks, and forecasts. Make data-driven decisions confidently.*
