---
description: "Track MRR/ARR, cash flow forecasting, profitability analysis, and measure progress toward financial goals"
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
argument-hint: "[track|forecast|analyze|goals] [--month] [--quarter] [--compare]"
---

# /software-business:revenue - Financial Tracking & Analysis

Track monthly recurring revenue (MRR), annual recurring revenue (ARR), cash flow, profitability, and measure progress toward financial independence.

## Quick Start

**Track this month's revenue:**

```bash
/software-business:revenue track
```

**Forecast next 90 days:**

```bash
/software-business:revenue forecast
```

**Analyze profitability:**

```bash
/software-business:revenue analyze
```

**Check progress toward goals:**

```bash
/software-business:revenue goals
```

---

## System Overview

This command implements **revenue-centric business tracking** where every dollar is:

1. Tracked by source (projects, retainers, products)
2. Measured for profitability (revenue vs. cost)
3. Linked to business goals ($200K/year, recurring revenue, etc.)
4. Evaluated for sustainability (can you maintain this?)

**Key Principle**: Revenue isn't profit. A $100K project might only generate $30K profit. The goal is to maximize profit while maintaining sustainable work hours.

---

## Mode 1: TRACK - Record Revenue & Expenses

Log revenue and expenses as they occur or monthly.

### Revenue Sources

**Project Revenue** (Non-recurring):

- Custom development projects
- One-time consulting engagements
- Implementation projects
- Training/workshops

**Retainer Revenue** (Recurring):

- Monthly maintenance contracts
- Retainer agreements
- Support contracts
- Ongoing advisory

**Product Revenue** (Recurring/one-time):

- SaaS product subscriptions
- Digital products (courses, templates, etc.)
- Affiliate revenue
- Sponsorships

### Revenue Log Template

```
REVENUE TRACKING - JANUARY 2025
═════════════════════════════════════════════════════════════

PROJECT REVENUE (Non-recurring)
├── E-commerce Platform Redesign (TechCorp)
│   ├── Invoice date: Jan 15
│   ├── Invoice amount: $35,000
│   ├── Status: Accepted, payment received
│   ├── Profit: $20,375 (58% margin)
│   └── Hours: 195
│
└── Website Redesign (SmallBiz Inc.)
    ├── Invoice date: Jan 20
    ├── Invoice amount: $12,000
    ├── Status: Pending payment (due Feb 20)
    ├── Profit: $4,800 (40% margin)
    └── Hours: 120

PROJECT REVENUE TOTAL: $47,000

RETAINER REVENUE (Recurring)
├── Consulting Client Inc.
│   ├── Monthly retainer: $2,000
│   ├── Due date: Jan 5
│   ├── Status: Received
│   └── Profit: $1,600 (80% margin - very high)
│
└── Support Contract (Various)
    ├── Monthly: $800
    ├── Due date: Jan 10
    ├── Status: Received
    └── Profit: $400 (50% margin)

RETAINER REVENUE TOTAL: $2,800 (recurring monthly)

PRODUCT REVENUE
├── Course sales (Design Principles 101)
│   ├── Units sold this month: 3
│   ├── Revenue: $300 (3 × $99)
│   └── Profit: $270 (90% margin - digital, minimal cost)
│
└── Affiliate commissions
    ├── Revenue: $150
    └── Profit: $150 (100% margin)

PRODUCT REVENUE TOTAL: $450

EXPENSES
├── Contractor fees: $5,000 (freelancer for project overflow)
├── Software subscriptions: $600 (AWS, GitHub, etc.)
├── Marketing: $200 (conference sponsorship)
└── Other: $100 (misc)

TOTAL EXPENSES: $5,900

JANUARY SUMMARY
├── Total Revenue: $50,250
├── Total Profit: $26,525 (52.8% margin)
├── Recurring Revenue (MRR): $2,800
└── Non-recurring Revenue: $47,450
```

### Monthly Revenue Tracking

At the end of each month, summarize:

```
MONTHLY SUMMARY - JANUARY 2025
═════════════════════════════════════════════════════════════

REVENUE BY SOURCE
├── Projects: $47,000 (93.5%)
├── Retainers: $2,800 (5.6%)
├── Products: $450 (0.9%)
└── Total: $50,250 ✅

COST BREAKDOWN
├── Contractor cost: $5,000 (auto-scaled with project load)
├── Software: $600 (fixed)
├── Marketing: $200 (discretionary)
└── Other: $100
└── Total: $5,900

PROFITABILITY
├── Total profit: $26,525
├── Profit margin: 52.8% (target: 50%+) ✅
├── Profit per hour: $89 (target: $75+) ✅
└── Billable hours: 315

CASH FLOW
├── Money in (received): $48,000
├── Money out (paid): $5,900
├── Net cash: $42,100
├── Accounts receivable (pending): $2,250 (SmallBiz invoice)
└── Cash position: Strong ✅

RECURRING vs. ONE-time
├── Recurring (retainers): $2,800/month (baseline)
├── Non-recurring (projects): $47,450 (additional)
├── Total: $50,250
└── Recurring %: 5.6% (should increase to 20%+)
```

---

## Mode 2: FORECAST - 90-Day Cash Flow

Project revenue and expenses for next 90 days.

### 90-Day Cash Flow Forecast

```
90-DAY CASH FLOW FORECAST
═════════════════════════════════════════════════════════════

FEBRUARY 2025 PROJECTION
├── Confirmed projects: $12,000 (Website Redesign completion)
├── Expected projects: $20,000 (Mobile App phase 1)
├── Retainer revenue: $2,800 (recurring)
├── Product revenue: $300 (estimated)
├── Total projected: $35,100
│
├── Costs (estimated): $6,500 (contractor + software)
├── Profit estimate: $28,600
└── Status: ON TRACK

MARCH 2025 PROJECTION
├── Confirmed projects: $30,000 (Mobile App milestone)
├── Expected projects: $15,000 (New proposal likely to close)
├── Retainer revenue: $2,800 (recurring)
├── Product revenue: $400 (holiday season, higher sales)
├── Total projected: $48,200
│
├── Costs (estimated): $7,000 (high project load)
├── Profit estimate: $41,200
└── Status: STRONG

APRIL 2025 PROJECTION
├── Confirmed projects: $25,000 (Mobile App final phase)
├── Expected projects: $10,000 (Renewal contracts)
├── Retainer revenue: $2,800 (recurring)
├── Product revenue: $300 (normal)
├── Total projected: $38,100
│
├── Costs (estimated): $5,500 (slower period)
├── Profit estimate: $32,600
└── Status: GOOD

90-DAY SUMMARY
├── Total revenue: $121,400
├── Total profit: $102,400 (84% average margin)
├── Average monthly revenue: $40,467
├── Average monthly profit: $34,133
└── Forecast: Q1 revenue $121K, profit $102K ✅

CASH FLOW COMPARISON
├── Jan actual: $50,250 revenue
├── Feb forecast: $35,100 revenue
├── Mar forecast: $48,200 revenue
├── Apr forecast: $38,100 revenue
│
├── Pattern: Typical variation for project-based business
├── Risk: Feb is lower (New Year slower period) - EXPECTED
├── Opportunity: Mar is peak quarter (maximize March projects)
└── Sustainability: Solid base with project volatility
```

### Confidence Levels

For each forecast item, rate confidence:

- **Confirmed** (90-100% confidence): Already signed contracts, payment terms set
- **Expected** (60-80% confidence): Proposals sent, awaiting decision or early-stage projects
- **Possible** (30-60% confidence): Leads in pipeline, not yet proposed
- **Speculative** (<30% confidence): Long-term opportunities, very early

Example:

```
FEBRUARY REVENUE BREAKDOWN
├── Confirmed (95%): $12,000 (Website completion - in contract)
├── Expected (75%): $20,000 (Mobile App - proposal sent, 75% likely)
├── Possible (40%): $5,000 (Conference lead - early stage)
└── Total: $37,000 (weighted for 95% + 75% of expected = ~$27K likely)
```

---

## Mode 3: ANALYZE - Profitability Deep Dive

Analyze profit margins, efficiency, and trends.

### Profitability Analysis

```
2025 PROFITABILITY ANALYSIS (Year-to-date)
═════════════════════════════════════════════════════════════

OVERALL METRICS
├── Total revenue: $187,500 (8 completed projects + retainers)
├── Total costs: $98,750
├── Total profit: $88,750 (47.3% margin)
├── Average profit/hour: $74.97
├── Billable hours: 1,183
└── Revenue/hour: $158.49

PROFIT MARGIN BREAKDOWN BY SOURCE
├── Projects (93.5% of revenue)
│   ├── Average margin: 52% (best at 85%, worst at 40%)
│   ├── Total: $82,500 profit on $155K revenue
│   └── Analysis: Solid margins, improving with experience
│
├── Retainers (5.6% of revenue)
│   ├── Average margin: 75% (high because recurring, lower overhead)
│   ├── Total: $5,250 profit on $7K revenue
│   └── Analysis: Very high margin, but small scale
│
└── Products (0.9% of revenue)
    ├── Average margin: 90% (digital, minimal cost)
    ├── Total: $1,000 profit on $1.1K revenue
    └── Analysis: High margin, but negligible scale

PROFIT TREND
├── Month 1 (Jan): $26,525 profit (52.8% margin)
├── Month 2 (Feb-projected): $28,600 (81.4% margin - lower revenue = better margin)
├── Month 3 (Mar-projected): $41,200 (85.4% margin - peak)
├── Month 4 (Apr-projected): $32,600 (85.5% margin)
│
├── Trend: Improving margins as you optimize
├── YTD average: 52.8% margin
└── Q1 forecast: 84.8% margin (significantly better)

EFFICIENCY METRICS
├── Billable hours/month (average): 296
├── Revenue/hour: $158.49
├── Profit/hour: $74.97
├── Target profit/hour: $70+ ✅ (exceeding)
└── Status: EXCELLENT EFFICIENCY ✅

COST STRUCTURE
├── Contractor fees: 35% of costs (variable with project load)
├── Software/tools: 15% of costs (fixed)
├── Marketing: 10% of costs (discretionary)
├── Other: 5% of costs
└── Your time: 35% of costs (implicit - profit you keep)

OPPORTUNITIES TO INCREASE PROFIT
├── Increase prices: +13% on new projects = +$25K/year
├── Reduce contractor costs: Hire cheaper freelancers = +$8K/year
├── Increase product sales: 10x current = +$4.5K/year
├── Increase retainers: Double from 5% to 10% of revenue = +$9K/year
└── Total opportunity: +$46K+ (52% increase in profit)
```

### Profit Per Project Analysis

```
PROFIT PER PROJECT RANKING (2025 YTD)
═════════════════════════════════════════════════════════════

TOP 5 BY PROFIT AMOUNT
1. E-commerce Platform (TechCorp): $20,375 profit
2. Mobile App Phase 1 (StartupXYZ): $18,750 profit (estimate)
3. API Integration (B2B): $7,200 profit
4. Consulting (Various): $8,250 profit
5. Database Optimization: $4,160 profit

TOP 5 BY PROFIT MARGIN %
1. Landing Page (TechStartup): 85% margin
2. Course Sales: 90% margin (product, not project)
3. E-commerce Platform: 58% margin
4. API Integration: 60% margin
5. Retainer Consulting: 75%+ margin

TOP 5 BY PROFIT PER HOUR
1. Landing Page: $425/hour (high-margin project, short duration)
2. Course Sales: $300+/hour (digital product)
3. Consulting: $82.50/hour
4. E-commerce: $104/hour
5. API Integration: $90/hour

INSIGHT
├── Best projects by margin: Product-based (90%) and small projects (85%)
├── Best projects by total profit: Large projects ($15K+)
├── Best projects by hourly: Small, specialized projects ($400+/hr)
│
└── RECOMMENDATION: Mix of all three types
    ├── 1-2 large projects per quarter ($15K+ = $25K/quarter)
    ├── 2-3 retainer contracts (recurring $2-3K/month = $24-36K/year)
    └── 4-5 small specialized projects (high margin, quick turnaround)
```

---

## Mode 4: GOALS - Measure Progress Toward Targets

Track progress toward business and life financial goals.

### Business Goal Progress

```
BUSINESS GOAL: Build $200K/year software business
═════════════════════════════════════════════════════════════

TARGET: $200,000 annual revenue
CURRENT (YTD): $187,500 (9 months of data)
PROGRESS: 93.75% of annual target ✅

ANNUALIZED PROJECTION
├── YTD revenue: $187,500 (based on 9 months work)
├── Annualized: $250,000+ (on track)
├── vs. target: +25% above goal ✅
└── Status: EXCEEDING TARGET

QUARTERLY BREAKDOWN
├── Q1 (forecast): $121,400
├── Q2 (estimate): $140,000
├── Q3 (estimate): $135,000
├── Q4 (estimate): $130,000
└── Total: $526,400 (if all quarters similar to Q1)

MONTHLY TARGETS
├── Current: $20,854/month average (to hit $200K)
├── Actual Q1: $42,467/month average
├── Status: 2.04x monthly target ✅
└── Implication: If maintain this pace, will hit $500K+

RISKS & OPPORTUNITIES
├── Risk: Q1 may be anomaly (holiday season boosted sales)
├── Opportunity: New retainers (+$5-10K/month recurring)
├── Opportunity: Product launch (could add $500+/month)
├── Conservative estimate: $280-300K annual (still 40% above goal)
└── Status: STRONG, even with conservative estimate

NEXT MILESTONE
├── Reach $250K revenue: Projected by July 2025 ✅
├── Achieve $100K profit: Projected by July 2025 ✅
└── Establish $10K/month recurring revenue: Target by Q4
```

### Life Goal - Financial Independence

```
LIFE GOAL: Financial Independence (in 10 years)
═════════════════════════════════════════════════════════════

BUSINESS REVENUE TARGET: $200K/year (generates $100K+ profit)

CURRENT PROGRESS
├── Current annual revenue: $250K+ (on pace)
├── Current annual profit: $125K+ (at 50% margin)
├── Time invested: 9 months (on accelerated timeline)
└── Status: AHEAD OF SCHEDULE ✅

FINANCIAL INDEPENDENCE MATH
├── Annual profit: $125,000 (conservative estimate)
├── Annual savings: $100,000 (80% of profit)
├── Annual investment return: 8% = $8,000
│
├── Year 1 assets: $100K (savings) + $8K (returns) = $108K
├── Year 5 assets: $600K+ (compounding)
├── Year 10 assets: $1.2M+ (path to financial independence)
│
└── MILESTONE CHECK
    ├── 1-year target: Save $100K ✓ (on pace)
    ├── 3-year target: Net worth $400K ✓ (on pace)
    ├── 5-year target: Net worth $800K → $1M ✓ (on pace)
    └── 10-year target: Net worth $2M+ ✓ (on pace)

FINANCIAL INDEPENDENCE NUMBER
├── Required annual expenses: $60K (estimate)
├── Safe withdrawal rate: 4% = $2.4M needed
├── Current on-pace assets at year 10: $1.2M
├── Additional sources (real estate, products): $1.2M+
├── Total path to FI: $2.4M+ ✓ (feasible by year 10-12)

LEVERS TO ACCELERATE
├── Increase profit margin from 50% to 60% = +$25K/year
├── Increase revenue from $250K to $400K = +$75K/year
├── Launch product: +$50K/year (additional revenue stream)
├── Real estate: +$60K/year (investment income)
│
├── Total potential: +$210K/year (doubling current savings rate)
└── New timeline: Achieve FI in 5-7 years (vs. 10 years)
```

### Key Financial Metrics Dashboard

```
FINANCIAL METRICS SCORECARD
═════════════════════════════════════════════════════════════

REVENUE HEALTH
├── MRR (Monthly Recurring): $2,800 (target: $10K+)
│   └── Progress toward goal: 28% (opportunity to grow)
├── ARR (Annual Recurring): $33,600 (target: $120K+)
│   └── Progress toward goal: 28% (same as MRR)
├── Project revenue: $155,000 (strong, but non-recurring)
└── Overall revenue: $188,600 ✅

PROFIT HEALTH
├── Overall margin: 47.3% (target: 50%+)
│   └── Close to target, room to improve ✅
├── Project margin: 52% (excellent)
├── Retainer margin: 75% (excellent)
└── Product margin: 90% (excellent, but small scale)

EFFICIENCY HEALTH
├── Revenue/hour: $158.49 (target: $150+) ✅
├── Profit/hour: $74.97 (target: $75+) ✅
├── Hours/week: 35 (target: ≤40) ✅
└── Status: EXCELLENT EFFICIENCY ✅

SUSTAINABILITY HEALTH
├── Recurring revenue ratio: 5.6% (target: 25%+)
│   └── OPPORTUNITY: Grow retainers 4-5x
├── Client concentration: 30% from top 2 clients
│   └── RISK: Diversify client base
├── Revenue stability: Improving (more projects in pipeline)
└── Ability to maintain: High ✅ (under budget on hours)

CASH FLOW HEALTH
├── Accounts receivable: Good (98% collected on time)
├── Average payment cycle: 30 days (standard)
├── Cash reserves: Strong (6+ months runway)
└── Status: HEALTHY ✅

OVERALL FINANCIAL HEALTH: 8.2/10 ✅
├── Strengths: High revenue, good profit margin, efficient
├── Opportunities: Grow recurring revenue, increase prices
└── Risks: Client concentration, limited products
```

---

## Revenue Optimization Recommendations

```
3-MONTH OPTIMIZATION PLAN

MONTH 1: INCREASE PRICES (Potential +$25K/year)
├── Action: Increase dev rates from $110/hr to $125/hr
├── Strategy: Apply to new projects only (grandfather existing)
├── Expected adoption: 60% of new projects at new rate
├── Timeline: Start next proposals immediately
└── Impact: +$13K+ in profit (new high-margin projects)

MONTH 2: GROW RECURRING REVENUE (Potential +$60K/year)
├── Action: Create 3-month "value package" for retainers
├── Strategy: Upsell existing clients on maintenance/support
├── Timeline: Pitch to 3 largest clients
├── Expected: 1-2 clients agree to $500-1K/month retainer
└── Impact: +$6-12K annual recurring revenue

MONTH 3: LAUNCH PRODUCT (Potential +$50K/year)
├── Action: Package one of your specializations as product
├── Idea: "Advanced API Design Course" ($99-199)
├── Strategy: Sell to your existing network + marketing
├── Timeline: Launch by end of month
└── Impact: +$3-5K initial, scaling to $50K+ potential

TOTAL 90-DAY IMPACT: +$22-30K additional profit potential
```

---

## Data Storage

Revenue data is saved in:

**JSON File** (CLI):

```
.claude/data/revenue.json
├── Monthly revenue logs (projects, retainers, products)
├── Cash flow forecasts (90-day projections)
├── Profitability by source and project
├── Recurring vs. non-recurring breakdown
└── Goal progress tracking
```

**PostgreSQL** (Analytics):

```
revenue table
├── revenue_id, source_type, amount, date
├── project_id, client_id (if applicable)
├── profit, margin_percentage
└── created_at, updated_at

cash_flow_forecast table
├── month, projected_revenue, projected_costs
├── confidence_level, actual (after month ends)
└── updated_at

financial_goals table
├── goal_id, goal_description, target_amount
├── progress_amount, target_date, status
└── updated_at
```

---

## Integration with Life Goals

Revenue directly supports financial independence:

```
LIFE GOAL: Financial Independence (10-year plan)
├── Business Goal: $200K/year revenue → $100K+ profit
│   └── Current: $250K+ revenue → $125K+ profit ✅
│
├── Annual savings target: $100K/year (80% of profit)
│   └── Current trajectory: $100K/year ✅
│
├── 10-year net worth target: $2M+
│   └── Current on-pace assets: $1.2M (+ real estate, products)
│
└── Path to FI: On track for 10-12 year timeline ✅
```

---

## Success Criteria

**After 1 month:**

- ✅ Revenue tracked (all sources logged)
- ✅ Expenses tracked
- ✅ Profitability calculated (margin %)
- ✅ Monthly summary complete

**After 3 months:**

- ✅ Trend analysis possible (revenue patterns emerging)
- ✅ Profit margin baseline established
- ✅ Forecast accuracy improving
- ✅ First optimization implemented

**After 6 months:**

- ✅ 50%+ profit margin achieved
- ✅ Revenue/hour $100+ consistently
- ✅ Recurring revenue growing (aiming for 10%+)
- ✅ Clear path to $200K+ annual revenue visible

**System Health**:

- ✅ Overall profit margin 50%+
- ✅ Revenue per hour $100+
- ✅ Monthly recurring revenue $5K+ (aiming for $10K+)
- ✅ Cash position strong (6+ months runway)
- ✅ Goal progress tracking visible

---

## ROI & Impact

**Time Investment**: 15 min/week (tracking + analysis)
**Annual ROI**: Better pricing decisions, optimized project mix, accelerated financial independence

**Key Benefits**:

- Visibility into profitability by source
- Data-driven pricing adjustments
- Cash flow forecasting
- Clear progress toward goals
- Identify optimization opportunities

---

**Created with the goal-centric life management system**
**Track revenue to build wealth and achieve financial independence**
