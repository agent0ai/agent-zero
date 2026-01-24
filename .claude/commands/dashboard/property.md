---
description: Single property P&L and performance metrics
argument-hint: "<property-id> [--period month|quarter|year] [--format ascii|json|csv] [--export <filename>]"
model: claude-3-5-haiku-20241022
allowed-tools: ["Read", "Bash", "Write", "AskUserQuestion"]
---

# Property Performance Dashboard

Deep-dive analysis of a single property with complete P&L, tenant metrics, maintenance history, and profitability analysis.

## What This Command Does

Generates comprehensive property-level metrics:

- **Profit & Loss Statement**: Revenue, expenses, and net profit
- **Occupancy Analysis**: Unit status, tenant turnover, vacancy trends
- **Tenant Details**: Contact info, lease terms, payment history
- **Maintenance History**: Completed work, upcoming needs, cost tracking
- **Profitability Ratios**: ROI, expense ratio, cap rate
- **Year-over-Year Comparison**: Performance trends
- **Recommendations**: Optimization suggestions for this property

## Why This Matters

Managing individual properties requires understanding their individual profitability and performance. A property that looks profitable at portfolio level might be underperforming when analyzed in detail. This dashboard identifies optimization opportunities per property.

## Usage

```bash
# Display property dashboard (interactive selection)
/dashboard:property

# Display specific property
/dashboard:property 123-main-st

# Different time periods
/dashboard:property 123-main-st --period quarter
/dashboard:property 123-main-st --period year

# Export formats
/dashboard:property 123-main-st --format json
/dashboard:property 123-main-st --format csv
/dashboard:property 123-main-st --export /path/to/export.pdf
```

## Dashboard Structure

```
╔═════════════════════════════════════════════════════════════════════════════╗
║                        PROPERTY PERFORMANCE DASHBOARD                       ║
║                                                                             ║
║  Property: 123 Main Street, Austin TX 78704                                 ║
║  Period: January 2025 | Comparison: January 2024                            ║
╚═════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│ 🏢 PROPERTY OVERVIEW                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Property Type: Multi-Family Residential        Purchase Price: $1,200,000  │
│ Units: 12                                       Acquisition Date: 2019-03   │
│ Year Built: 1995                               Land Area: 0.85 acres       │
│ Building Area: 18,500 SF                       Total Units: 12             │
│                                                                             │
│ Current Status: ✅ PERFORMING WELL                                          │
│ Overall Health: 95% | Stability: Stable | Trend: Up 8% YoY                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 💰 PROFIT & LOSS STATEMENT                                                  │
├────────────────────────────────┬──────────────┬──────────────┬─────────────┤
│ Line Item                      │ This Month   │ Last Year    │ Change      │
├────────────────────────────────┼──────────────┼──────────────┼─────────────┤
│ REVENUE                        │              │              │             │
│   Rental Income                │ $2,400.00    │ $2,200.00    │ +$200 (+9%) │
│   Parking Income               │ $200.00      │ $200.00      │ $0          │
│   Laundry Income               │ $125.00      │ $100.00      │ +$25        │
│ TOTAL REVENUE                  │ $2,725.00    │ $2,500.00    │ +$225 (+9%) │
├────────────────────────────────┼──────────────┼──────────────┼─────────────┤
│ OPERATING EXPENSES             │              │              │             │
│   Mortgage Payment              │ $650.00      │ $650.00      │ $0          │
│   Property Taxes                │ $280.00      │ $260.00      │ +$20        │
│   Insurance                     │ $145.00      │ $140.00      │ +$5         │
│   Utilities (Property)          │ $200.00      │ $180.00      │ +$20        │
│   Maintenance & Repairs         │ $120.00      │ $150.00      │ -$30        │
│   Management Fee (8%)           │ $218.00      │ $200.00      │ +$18        │
│   Tenant Screening              │ $50.00       │ $75.00       │ -$25        │
│   HOA/Common Area               │ $85.00       │ $80.00       │ +$5         │
│ TOTAL OPERATING EXPENSES        │ $1,748.00    │ $1,735.00    │ +$13        │
├────────────────────────────────┼──────────────┼──────────────┼─────────────┤
│ NET OPERATING INCOME (NOI)      │ $977.00      │ $765.00      │ +$212 (+28%)│
│ DEBT SERVICE (if financed)      │ -$650.00     │ -$650.00     │ $0          │
│ NET PROFIT (After Debt)         │ $327.00      │ $115.00      │ +$212      │
├────────────────────────────────┼──────────────┼──────────────┼─────────────┤
│ CASH FLOW METRICS              │              │              │             │
│ Operating Expense Ratio         │ 64%          │ 69%          │ -5% ✅      │
│ Profit Margin                   │ 12%          │ 5%           │ +7% ✅      │
│ NOI Margin                      │ 36%          │ 31%          │ +5% ✅      │
└────────────────────────────────┴──────────────┴──────────────┴─────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 🏘️ OCCUPANCY & TENANT ANALYSIS                                             │
├──────────────┬──────────────┬──────────────┬──────────────┬─────────────────┤
│ Metric       │ Current      │ Previous Mo  │ 12-Mo Avg    │ Status          │
├──────────────┼──────────────┼──────────────┼──────────────┼─────────────────┤
│ Occupancy    │ 100% (12/12) │ 100% (12/12) │ 98.5%        │ ✅ Excellent    │
│ Vacant Units │ 0            │ 0            │ 0.18         │ ✅ None         │
│ Days to Fill │ N/A          │ N/A          │ 8.2 days     │ ✅ Fast         │
│ Turnover %   │ 0%           │ 0%           │ 4.5%/year    │ ✅ Low          │
│ Renewal Rate │ 100%         │ 100%         │ 92%          │ ✅ Excellent    │
└──────────────┴──────────────┴──────────────┴──────────────┴─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 👥 TENANT ROSTER                                                            │
├─────┬────────────┬──────────────┬──────────────┬──────────────┬────────────┤
│ Apt │ Tenant     │ Lease End    │ Rent/Month   │ Payment Hist │ Rating     │
├─────┼────────────┼──────────────┼──────────────┼──────────────┼────────────┤
│ 101 │ J. Smith   │ 2025-12-31   │ $200.00      │ ✅ On-time   │ 5/5 ⭐    │
│ 102 │ M. Johnson │ 2025-08-31   │ $200.00      │ ✅ On-time   │ 4.5/5     │
│ 103 │ S. Williams│ 2026-03-31   │ $200.00      │ ✅ On-time   │ 5/5 ⭐    │
│ 104 │ R. Brown   │ 2025-06-30   │ $200.00      │ ✅ On-time   │ 4/5       │
│ 201 │ E. Davis   │ 2025-11-30   │ $200.00      │ ✅ On-time   │ 5/5 ⭐    │
│ 202 │ [VACANT]   │ —            │ —            │ —            │ —         │
│ 203 │ K. Miller  │ 2026-02-28   │ $200.00      │ ✅ On-time   │ 4.5/5     │
│ 204 │ L. Moore   │ 2025-09-30   │ $200.00      │ ✅ On-time   │ 5/5 ⭐    │
│ 301 │ J. Taylor  │ 2025-10-31   │ $200.00      │ ✅ On-time   │ 4.5/5     │
│ 302 │ P. Anderson│ 2026-01-31   │ $200.00      │ ✅ On-time   │ 5/5 ⭐    │
│ 303 │ N. Thomas  │ 2025-07-31   │ $200.00      │ ✅ On-time   │ 3.5/5     │
│ 304 │ C. Jackson │ 2026-05-31   │ $200.00      │ ✅ On-time   │ 5/5 ⭐    │
│     │ 12 UNITS   │ —            │ $2,400/mo    │ 99% Collected│ Avg: 4.7/5│
└─────┴────────────┴──────────────┴──────────────┴──────────────┴────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔧 MAINTENANCE & CAPITAL PROJECTS                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ RECENT COMPLETED WORK (Last 90 Days)                                       │
│ ✓ Roof repair - Building A [Cost: $2,500]  [Date: 2024-11-15]             │
│ ✓ HVAC maintenance - All units [Cost: $800]  [Date: 2024-12-20]           │
│ ✓ Lobby painting [Cost: $1,200]  [Date: 2025-01-10]                       │
│                                                                             │
│ UPCOMING PLANNED WORK (Next 90 Days)                                       │
│ → Landscaping refresh [Est. Cost: $3,500]  [Scheduled: 2025-03-15]        │
│ → Fire safety inspection & updates [Est. Cost: $1,200]  [Scheduled: 2025-02] │
│ → Parking lot sealcoat [Est. Cost: $2,800]  [Scheduled: 2025-04-01]       │
│                                                                             │
│ CAPITAL RESERVE                                                             │
│ Funded: $15,000 | Recommended (12-mo): $18,000 | Funded %: 83%             │
│ Annual Contribution: $2,000/year | Status: ⚠️ Below target                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 📊 FINANCIAL RATIOS & KEY METRICS                                           │
├──────────────────────────────────┬──────────┬──────────┬─────────────────────┤
│ Metric                           │ Value    │ Benchmark│ Status              │
├──────────────────────────────────┼──────────┼──────────┼─────────────────────┤
│ Cap Rate                         │ 8.1%     │ 7-8%     │ ✅ Excellent        │
│ Cash-on-Cash Return              │ 4.2%     │ 3-5%     │ ✅ Good             │
│ Operating Expense Ratio          │ 64%      │ 50-65%   │ ✅ Healthy          │
│ Debt Service Coverage Ratio      │ 1.5x     │ 1.2-1.5x │ ✅ Strong           │
│ Break-even Occupancy             │ 58%      │ 60-70%   │ ✅ Low (Good)       │
│ Rent-to-Value Ratio              │ 0.20%    │ 0.8-1.1% │ ⚠️ Below market     │
│ Average Unit Value               │ $100,000 │ —        │ —                   │
│ Purchase Price per Unit          │ $100,000 │ —        │ —                   │
│ Monthly Revenue per Unit         │ $225.40  │ $200-250 │ ✅ Competitive      │
│ Monthly Expense per Unit         │ $145.70  │ $100-150 │ ✅ Healthy          │
│ Net Profit per Unit              │ $27.25   │ $20-40   │ ✅ Good             │
└──────────────────────────────────┴──────────┴──────────┴─────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 📈 YEAR-OVER-YEAR PERFORMANCE TREND                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Revenue Trend (Last 12 Months)                                             │
│                                                                             │
│ $2,800 │         ●                                                         │
│        │       ●   ●                                                       │
│ $2,600 │     ●       ●                                                     │
│        │   ●           ●                                                   │
│ $2,400 │ ●               ●●●●●●●●●●                                        │
│        │                                                                   │
│ $2,200 │                                                                   │
│        └────────────────────────────────────────────────────────────────   │
│        Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep  Oct  Nov  Dec         │
│                                                                             │
│ 12-Month Trend: +9% (Growth from $2,500 to $2,725)                         │
│ Trajectory: Positive - Property appreciation in value                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 💡 ANALYSIS & RECOMMENDATIONS                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ STRENGTHS:                                                                  │
│ ✓ Exceptional occupancy (100%) - Perfect tenant retention                 │
│ ✓ Strong profit growth (+212% net profit YoY)                              │
│ ✓ Low turnover (4.5%/year) - Stable tenant base                           │
│ ✓ Excellent tenant quality (4.7/5 avg rating)                              │
│ ✓ Improving expense management (64% ratio down from 69%)                   │
│                                                                             │
│ OPPORTUNITIES:                                                              │
│ 1. RENT OPTIMIZATION: Current rent-to-value ratio 0.20% vs market 0.8-1.1%│
│    → Could increase rents 8-10% at lease renewal                           │
│    → Estimated additional monthly revenue: $180-225                         │
│    → Recommendation: Implement gradual increases starting next renewal      │
│                                                                             │
│ 2. CAPITAL RESERVE: Currently funded at 83% vs recommended 100%            │
│    → Increase annual contribution by $250/month                             │
│    → Timeline: 6 months to reach fully funded status                       │
│                                                                             │
│ 3. UNIT 202 VACANCY: Currently vacant - fill quickly                       │
│    → Implement aggressive marketing (3 platforms)                           │
│    → Consider short-term discount (1st mo 10% off)                         │
│    → Estimated fill time: 10-14 days                                        │
│    → Monthly revenue recovery: $200                                         │
│                                                                             │
│ 4. EXPENSE OPTIMIZATION: Utilities trending up 11% YoY                      │
│    → Review HVAC programming and thermostat settings                       │
│    → Potential savings: $15-20/month                                        │
│                                                                             │
│ RISK MITIGATION:                                                            │
│ ⚠ Rent-to-value ratio below market - May indicate underpricing            │
│ ⚠ One lease expiration Q2 2025 (Unit 104) - Begin renewal outreach        │
│ ⚠ Capital reserve trending low - Prioritize funding increases              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 🎯 ACTION ITEMS (Prioritized)                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ 🔴 URGENT (This Month)                                                    │
│ 1. Fill Unit 202 vacancy (Active listing started 1/15)                     │
│    Timeline: 10-14 days target                                              │
│    Owner: Property Manager                                                  │
│                                                                             │
│ 🟡 HIGH PRIORITY (Next 30 Days)                                            │
│ 2. Conduct rent market analysis for Q2 2025 increases                      │
│    Timeline: Complete by Feb 15                                             │
│    Owner: Accountant/Market Analyst                                         │
│                                                                             │
│ 3. Schedule lease renewal discussions (Unit 104 expires 6/30)              │
│    Timeline: March 1st outreach                                             │
│    Owner: Property Manager                                                  │
│                                                                             │
│ 🟢 MEDIUM PRIORITY (Next 90 Days)                                          │
│ 4. Implement utility reduction plan                                         │
│    Timeline: Complete by March 31                                           │
│    Owner: Maintenance + Property Manager                                    │
│                                                                             │
│ 5. Schedule landscaping refresh (Q2 project)                                │
│    Timeline: Book vendor by Feb 28                                          │
│    Owner: Property Manager                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Generated: 2025-01-22T14:35:00Z | Property ID: MAIN-ST-001
Data Source: Property Management System + Zoho CRM
Next Review: 2025-02-22T14:35:00Z (Monthly Cycle)
```

## Export Formats

### JSON Export

```json
{
  "property": {
    "id": "MAIN-ST-001",
    "address": "123 Main Street, Austin TX 78704",
    "units": 12,
    "purchase_price": 1200000,
    "acquisition_date": "2019-03-15"
  },
  "financial": {
    "revenue": 2725.00,
    "expenses": 1748.00,
    "noi": 977.00,
    "net_profit": 327.00,
    "margins": {
      "expense_ratio": 0.64,
      "profit_margin": 0.12,
      "noi_margin": 0.36
    }
  },
  "occupancy": {
    "occupied_units": 12,
    "vacant_units": 0,
    "occupancy_rate": 1.0,
    "average_rent": 200.0
  },
  "tenants": [
    {
      "unit": "101",
      "name": "J. Smith",
      "lease_end": "2025-12-31",
      "rent_monthly": 200.0,
      "rating": 5.0
    }
  ],
  "maintenance": {
    "recent_work": [...],
    "upcoming_work": [...],
    "capital_reserve": 15000
  }
}
```

## Success Metrics

- ✓ Complete P&L statement generated
- ✓ All tenant information displayed
- ✓ Occupancy metrics calculated
- ✓ Maintenance history tracked
- ✓ Financial ratios computed
- ✓ YoY comparisons shown
- ✓ Recommendations provided
- ✓ Export to JSON/CSV/PDF successful

## Recommended Frequency

- **Monthly Review**: Full dashboard review with P&L (10-15 min)
- **Quarterly Analysis**: Comprehensive trend analysis (20-30 min)
- **Annual Planning**: Strategic review and goal setting (1 hour)

## Related Commands

- `/dashboard:overview` - All properties at a glance
- `/dashboard:alerts` - Property-specific alerts
- `/dashboard:kpi` - Property KPI tracking
- `/finance:report` - Detailed financial statements
- `/context:switch [property-id]` - Switch to property context

---

*Complete property financial analysis at your fingertips. Know exactly what each property is earning and what opportunities exist for optimization.*
