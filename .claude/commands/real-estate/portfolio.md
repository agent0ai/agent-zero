---
description: "Manage property portfolio with valuations, equity tracking, ROI analysis, and cash flow aggregation"
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
argument-hint: "[add|list|analyze|dashboard] [--sort equity|roi|cashflow] [--compare-market]"
---

# /real-estate:portfolio - Property Portfolio Management

Track all properties with valuations, equity positions, cash flow, and measure ROI against financial independence goals.

## Quick Start

**Add a new property:**

```bash
/real-estate:portfolio add
```

**List all properties:**

```bash
/real-estate:portfolio list
```

**Analyze portfolio performance:**

```bash
/real-estate:portfolio analyze
```

**View portfolio dashboard:**

```bash
/real-estate:portfolio dashboard
```

---

## System Overview

This command implements **portfolio-centric real estate management** where:

1. Every property is tracked for value and cash flow
2. ROI is measured per property and aggregated
3. Properties are evaluated against financial independence goals
4. Portfolio diversification and risk are managed

**Key Principle**: Real estate is a wealth-building tool that generates cash flow (passive income) and appreciation (capital gains). The goal is to build a diversified portfolio generating enough passive income to support financial independence.

---

## Mode 1: ADD - Create Property Record

Add a new property to your portfolio.

### Property Information

**Basic Details**:

- Property address
- Property type (single family, multi-family, commercial, land)
- Acquisition date
- Purchase price
- Current estimated value
- Loan details (if mortgaged)

**Financials**:

- Purchase price
- Down payment
- Loan amount, rate, term
- Annual property tax
- Annual insurance
- Maintenance reserves
- Rental income (if applicable)
- Vacancy rate
- Expenses (property management, repairs, utilities if you pay)

**Performance Metrics**:

- Cash flow (annual)
- Capitalization rate (Cap Rate)
- Cash-on-cash return
- Estimated appreciation
- ROI calculation

### Property Template

```
PROPERTY: Single Family Home - 123 Oak Street
═════════════════════════════════════════════════════════════

BASIC INFORMATION
├── Address: 123 Oak Street, Austin, TX 78701
├── Type: Single Family Home (4 bed, 2 bath, 2,000 sq ft)
├── Acquisition date: Jan 2022
├── Current status: Rented (occupied)
└── Target: Hold for 10+ years (long-term appreciation)

ACQUISITION DETAILS
├── Purchase price: $400,000
├── Down payment: $80,000 (20%)
├── Loan amount: $320,000
├── Loan terms: 30-year mortgage @ 4.5%
├── Monthly payment: $1,619
├── Closing costs: $12,000 (included in basis)
└── Total invested: $92,000 (down payment + closing costs)

CURRENT VALUATION
├── Estimated current value: $450,000 (after 2 years)
├── Appreciation: +$50,000 (+12.5%)
├── Current loan balance: $305,000 (Jan 2025)
├── Equity: $145,000 (32% of value)
├── Equity gain: $65,000 (from initial $80K investment)
└── Status: Appreciating well ✅

RENTAL INCOME (Monthly)
├── Monthly rent: $2,800
├── Annual gross rental: $33,600
└── Occupancy rate: 95% (4% vacancy assumed)

EXPENSES (Monthly)
├── Mortgage: $1,619
├── Property tax: $300
├── Insurance: $120
├── Maintenance reserve (5%): $140
├── Property management: $280 (10% of rent)
├── Utilities (tenant pays): $0
├── HOA: $0
└── Total expenses: $2,459

CASH FLOW ANALYSIS
├── Gross rental income: $2,800
├── Total expenses: $2,459
├── Net cash flow: $341/month ($4,092/year)
├── Cash-on-cash return: 4.4% (annual profit / initial investment)
└── Status: POSITIVE cash flow ✅

VALUATION & EQUITY
├── Property value: $450,000
├── Loan balance: $305,000
├── Equity: $145,000
├── Equity %: 32.2%
└── Years to payoff: ~18 years (at current paydown rate)

APPRECIATION & ROI ANALYSIS
├── Initial investment: $92,000 (down + closing)
├── Annual cash flow: $4,092
├── Appreciation per year: $6,250 (est. 1.5% yearly)
├── Total annual return: $10,342 (cash flow + appreciation)
├── Total ROI: 11.2% ($10,342 / $92K)
└── Status: STRONG ROI ✅

EQUITY BUILD-UP
├── Year 1: Paid down principal ~$7,400 (equity +$7,400)
├── Year 2: Paid down principal ~$7,700 (equity +$7,700 + appreciation)
├── Year 3 (projected): $8,000 (equity growth)
├── 5-year projection: Total equity growth ~$40K+ (combination of paydown + appreciation)
└── 10-year projection: Paid off $80K principal, $80K+ appreciation = $160K+ equity growth

RISK ASSESSMENT
├── Market risk: LOW (Austin market strong, diverse economy)
├── Liquidity risk: MEDIUM (takes 2-3 months to sell)
├── Tenant risk: LOW (long-term tenant, good credit)
├── Maintenance risk: LOW (new roof, well-maintained)
└── Overall: LOW-MEDIUM RISK (stable investment)

GOALS ALIGNMENT
├── Financial Independence: YES (generates passive income)
├── Wealth building: YES (appreciation + equity paydown)
├── Diversification: YES (complements software business income)
└── Timeline: 10-year hold (accumulating equity)

NEXT ACTIONS
├── [ ] Set up property management (currently self-managing)
├── [ ] Review insurance coverage (may need higher limits)
├── [ ] Plan for major repairs (roof has 15 years left)
└── [ ] Consider refinance in 2-3 years (if rates favorable)
```

### Property Selection Criteria

**Financial Criteria**:

- Cash flow: Positive (or near break-even initially)
- Cash-on-cash return: ≥8% (initial return on investment)
- Cap rate: ≥5% (operational income yield)
- Appreciation potential: Good long-term appreciation expected
- Financing: Available with reasonable terms

**Market Criteria**:

- Market strength: Growing economy, population, job market
- Price trends: Stable or appreciating (avoid declining markets)
- Rental demand: Strong rental market (low vacancy)
- Comparables: Good comp data for valuation

**Property Criteria**:

- Condition: Good/excellent (minimize early repairs)
- Tenant quality: Reliable renters or owner-occupied
- Management: Easy to manage or professional management available
- Diversification: Doesn't over-concentrate portfolio

---

## Mode 2: LIST - View Portfolio Overview

See all properties with key metrics.

### Portfolio Dashboard

```
REAL ESTATE PORTFOLIO OVERVIEW
═════════════════════════════════════════════════════════════

PROPERTY SUMMARY (3 properties)
├── Property 1: Single Family Home (123 Oak St)
│   ├── Value: $450,000
│   ├── Equity: $145,000 (32%)
│   ├── Cash flow: $4,092/year
│   ├── ROI: 11.2%
│   └── Status: ✅ Performing well
│
├── Property 2: Duplex (456 Elm Ave)
│   ├── Value: $320,000
│   ├── Equity: $85,000 (27%)
│   ├── Cash flow: $3,600/year
│   ├── ROI: 9.8%
│   └── Status: ✅ Good performance
│
└── Property 3: Multi-Family (789 Main St) - New acquisition
    ├── Value: $600,000
    ├── Equity: $120,000 (20% - recent purchase)
    ├── Cash flow: $8,400/year
    ├── ROI: 7.0% (young property)
    └── Status: ⏳ Ramping up (recent purchase)

PORTFOLIO AGGREGATE METRICS
├── Total portfolio value: $1,370,000
├── Total equity: $350,000 (25.5%)
├── Total loans: $1,020,000
├── Total annual cash flow: $16,092
├── Portfolio cash-on-cash return: 4.6%
└── Combined portfolio ROI: 9.7%

CASH FLOW BY PROPERTY
├── Property 1: $4,092/month ($341)
├── Property 2: $3,600/year ($300)
├── Property 3: $8,400/year ($700)
├── Total: $16,092/year ($1,341/month passive income) ✅
└── Trend: Growing (new property increasing cash flow)

EQUITY POSITION
├── Property 1: $145K equity (32% LTV - good position)
├── Property 2: $85K equity (27% LTV - good position)
├── Property 3: $120K equity (20% LTV - new, normal)
├── Total: $350K equity (25.5% average)
└── Equity growth: ~$30K/year (from paydown + appreciation)

PROPERTY DISTRIBUTION
├── By type: 1 single family + 1 duplex + 1 multi-family
├── By geography: All Austin, TX (concentrated)
├── By financing: All mortgaged (leveraged strategy)
└── Diversification: Moderate (same market, different property types)

PERFORMANCE RANKING
├── Best ROI: Property 1 (11.2%)
├── Best cash flow: Property 3 ($8,400/year)
├── Best equity position: Property 1 (32% equity)
└── Most stable: Property 2 (long-term tenant, established)

PORTFOLIO HEALTH
├── Overall value: $1.37M (strong)
├── Equity: $350K (growing)
├── Cash flow: $16K/year (positive)
├── Risk profile: LOW-MEDIUM (diversified, strong market)
└── Status: HEALTHY ✅
```

### Filter & Sort Options

```bash
# View properties by ROI (best first)
/real-estate:portfolio list --sort roi

# View properties by cash flow (highest first)
/real-estate:portfolio list --sort cashflow

# View properties by equity (highest equity %/)
/real-estate:portfolio list --sort equity

# View only investment properties (exclude owner-occupied)
/real-estate:portfolio list --filter investment

# View high-risk properties
/real-estate:portfolio list --filter high-risk
```

---

## Mode 3: ANALYZE - Detailed Performance Analysis

Analyze portfolio performance and identify optimization opportunities.

### Portfolio Performance Analysis

```
PORTFOLIO PERFORMANCE ANALYSIS (2025 YTD)
═════════════════════════════════════════════════════════════

PORTFOLIO VALUE TRACKING
├── Starting value (Jan 1, 2025): $1,350,000
├── Current value (today): $1,370,000
├── Appreciation: +$20,000 (1.5% YTD)
├── Trend: Steady appreciation ✓
└── Annual projection: +$40K+ (if pace continues)

EQUITY BUILD-UP
├── Principal paid down (YTD): $12,000
├── Appreciation (YTD): $20,000
├── Total equity gain: $32,000 (YTD)
├── Annual projection: $64K+ (at current pace)
└── 5-year projection: $320K+ (equity doubling)

CASH FLOW PERFORMANCE
├── Actual cash flow (YTD): $4,023 (3 months)
├── Expected annual: ~$16,000
├── vs. budget: ON TRACK ✓
├── Trend: Stable month-to-month
└── Risk: LOW (reliable tenants)

INDIVIDUAL PROPERTY ANALYSIS

Property 1: Single Family Home
├── Cash flow: $341/month ($4,092/year) ✓
├── Appreciation: +$1,800/year (0.4%)
├── Principal paydown: $1,900/year
├── Total return: $7,692/year (11.2% ROI) ⭐
├── Status: EXCELLENT - Keep long-term
└── Action: None needed (performing well)

Property 2: Duplex
├── Cash flow: $300/month ($3,600/year) ✓
├── Appreciation: +$1,600/year (0.5%)
├── Principal paydown: $1,700/year
├── Total return: $6,900/year (9.8% ROI) ✓
├── Status: GOOD - Hold long-term
└── Action: Monitor for refinance opportunity

Property 3: Multi-Family
├── Cash flow: $700/month ($8,400/year) ✓
├── Appreciation: +$3,000/year (0.5%)
├── Principal paydown: $3,400/year
├── Total return: $14,800/year (7.0% ROI) ✓
├── Status: RAMPING UP - will improve with vacancy reduction
└── Action: Focus on tenant retention, reduce vacancy

PORTFOLIO-LEVEL INSIGHTS

Market Performance:
├── Austin appreciation: +1.5% YTD (on track with market)
├── Interest rates: Stable at current levels
├── Rental demand: Strong (good occupancy rates)
└── Market outlook: Positive for next 3-5 years ✓

Financing Analysis:
├── Average loan rate: 4.5% (favorable fixed rate)
├── Average LTV: 74.5% (healthy, not overleveraged)
├── Debt paydown: On track (paying principal consistently)
├── Refinance opportunity: Not yet (rates not favorable vs. current 4.5%)
└── Leverage strategy: Good (not over-leveraged, sustainable)

Diversification Analysis:
├── Geographic concentration: HIGH (all Austin) ⚠️
│   └── Recommendation: Add property in different market
├── Property type diversity: GOOD (SF + duplex + multi)
├── Tenant diversity: GOOD (mix of lease lengths)
├── Income stability: GOOD (reliable cash flow)
└── Overall: MODERATE RISK (concentrated geography)

OPTIMIZATION OPPORTUNITIES

Opportunity 1: Reduce Vacancy in Property 3
├── Current occupancy: 85% (vs. 95% market rate)
├── Impact: Could add $4K+ annual cash flow
├── Action: Improve marketing, reduce rent slightly, upgrade amenities
├── Timeline: 3-6 months
├── ROI: 30%+ (quick improvement)

Opportunity 2: Refinance Property 2 in 1-2 Years
├── Current loan: $235K @ 4.5%
├── Current LTV: 73% (good for refinance)
├── Potential: Refinance to 15-year mortgage (pay off faster)
├── Impact: Accelerate equity building by 10+ years
├── Timeline: 18-24 months (wait for better rates)

Opportunity 3: Geographic Diversification
├── Add 1 property outside Austin (different market)
├── Target: Growing market with good appreciation
├── Size: Similar investment ($75-100K down payment)
├── Timeline: 12-18 months
├── Impact: Reduce market concentration risk

RISK ASSESSMENT

Market Risk: LOW-MODERATE
├── Austin market strong, but concentrated
├── Action: Diversify geography ⚠️

Tenant Risk: LOW
├── Long-term tenants, good credit
├── Occupancy rate: 90%+ average
├── Action: Continue tenant retention focus ✓

Financing Risk: LOW
├── Fixed-rate mortgages (not ARM)
├── LTV: 74.5% (healthy)
├── Action: Maintain good LTV, don't over-leverage ✓

Liquidity Risk: MEDIUM
├── Takes 2-3 months to sell property
├── Not liquid like stocks
├── Action: Keep emergency fund separate ✓

OVERALL PORTFOLIO RATING: 8.2/10 ✓
├── Strengths: Strong cash flow, good appreciation, reliable income
├── Weaknesses: Geographic concentration, could optimize occupancy
├── Opportunities: Diversify geography, optimize Property 3
└── Outlook: POSITIVE for next 5-10 years
```

---

## Mode 4: DASHBOARD - Portfolio Summary

View key metrics and financial independence progress.

### Portfolio Dashboard

```
REAL ESTATE PORTFOLIO DASHBOARD
═════════════════════════════════════════════════════════════

WEALTH TRACKING
┌─ NET WORTH CONTRIBUTION
├── Total portfolio value: $1,370,000
├── Total equity: $350,000 (25.5%)
├── vs. initial investment: $350K / $275K = 127% return ✓
├── Annual net worth growth: ~$64,000 (equity + appreciation)
└── Status: STRONG WEALTH BUILDER ✓

PASSIVE INCOME GENERATION
┌─ ANNUAL CASH FLOW
├── Total gross rent: $48,600
├── Total expenses: -$32,508
├── Net cash flow: $16,092 ($1,341/month)
├── Passive income ratio: 33% (of gross rent)
└── Status: BUILDING PASSIVE INCOME ✓

FINANCIAL INDEPENDENCE PROGRESS
┌─ FI MILESTONE TRACKING
├── Target passive income for FI: $60,000/year (living expenses)
├── Current passive income: $16,092
├── % of target: 26.8% (26% toward FI)
├── Growth needed: $43,908 more (need 3 more properties)
├── Timeline at current pace: 6-8 years ✓
└── Status: ON TRACK FOR FI

PROPERTY PORTFOLIO BY VALUE
┌─ BREAKDOWN
├── Property 1 (SF Home): $450K (32.8%)
├── Property 2 (Duplex): $320K (23.4%)
├── Property 3 (Multi): $600K (43.8%)
└── Total: $1,370K

LOAN STATUS
┌─ MORTGAGE DETAILS
├── Total loans: $1,020,000
├── Average rate: 4.5%
├── Total remaining term: ~25 years (blended)
├── Monthly payments: $4,400
├── Principal paydown (annual): ~$30,000
└── Equity growth from paydown: On track ✓

CASH FLOW WATERFALL (Monthly)
┌─ SOURCES
├── Gross rent received: $4,050
│   ├── Property 1: $2,800
│   ├── Property 2: $2,100
│   └── Property 3: $3,000
│
├── USES (in order)
├── Loan payments: -$4,400
├── Property tax: -$250
├── Insurance: -$180
├── Maintenance: -$140
├── Vacancy/Losses: -$202
├── Property management: -$380
└── NET CASH FLOW: $1,341/month ✓

KEY METRICS SUMMARY
┌─ AT A GLANCE
├── Portfolio Value: $1.37M (↑1.5% YTD)
├── Total Equity: $350K (↑9.1% YTD)
├── Monthly Cash Flow: $1,341 (↑5% YTD)
├── Average ROI: 9.7% (solid)
├── Portfolio LTV: 74.5% (healthy)
└── Health: EXCELLENT ✅

GOALS ALIGNMENT
┌─ FINANCIAL INDEPENDENCE
├── Life goal: FI in 10 years (by age 45)
├── Real estate contribution: $16K passive income (26% toward target)
├── On track: YES ✓
├── Path: Add 3 more properties (1-2 per year)
└── Confidence: HIGH

UPCOMING ACTIONS
┌─ THIS QUARTER
├── [ ] Review insurance coverage (Q1)
├── [ ] Plan Q2 property search (Austin or expand)
├── [ ] Evaluate Property 3 refinance (future)
├── [ ] Monitor occupancy trends (monthly)
└── Priority: Add 1 new property by Q4 2025

ALERTS & OPPORTUNITIES
┌─ ATTENTION NEEDED
├── ⚠️ Property 3 occupancy below target (85% vs. 95%)
│   └── Action: Upgrade amenities, improve marketing
│
├── ✓ Property 1 performing excellently (11.2% ROI)
│   └── Action: Hold long-term, consider similar properties
│
└── 💡 Opportunity to geographic diversify
    └── Action: Explore properties in different market (Dallas, Houston)
```

---

## Data Storage

Portfolio data is saved in:

**JSON File** (CLI):

```
.claude/data/portfolio.json
├── Property listings (address, type, value)
├── Financial data (purchase price, loan details, cash flow)
├── Valuation tracking (appreciation history)
├── Equity position (current equity, paydown schedule)
└── Performance metrics (ROI, cap rate, cash-on-cash return)
```

**PostgreSQL** (Analytics):

```
properties table
├── property_id, address, city, state, type
├── purchase_price, current_value, purchase_date
├── loan_amount, loan_rate, loan_term, monthly_payment
├── annual_rent, annual_expenses, net_cashflow
├── equity, appreciation_rate
└── created_at, updated_at

property_valuations table
├── valuation_id, property_id, date
├── estimated_value, basis (for cap gains tax)
└── updated_at

property_cashflow table
├── cashflow_id, property_id, month, year
├── rent_received, expenses_paid, net_cashflow
└── date
```

---

## Integration with Life Goals

Real estate directly supports financial independence:

```
LIFE GOAL: Financial Independence (10-year plan)
├── Real estate target: Generate $60K/year passive income
│   ├── Current: $16K/year ($1,341/month)
│   ├── Progress: 26.8% toward target
│   └── Path: 3 more properties @ $15K each = $60K total
│
├── Wealth target: $2M+ net worth by age 45
│   ├── Current: $350K equity (from $275K initial investment)
│   ├── 5-year projection: $800K+ equity
│   ├── 10-year projection: $1.5M+ equity
│   └── On track: YES ✓
│
└── Timeline: On pace for FI in 10-12 years ✓
```

---

## Success Criteria

**After adding first property:**

- ✅ Property information complete (financials, details)
- ✅ Cash flow calculated
- ✅ ROI baseline established

**After 2 properties:**

- ✅ Positive portfolio cash flow
- ✅ Clear appreciation trend
- ✅ Diversification emerging (different property types)

**After 3+ properties:**

- ✅ $10K+/year passive income
- ✅ $250K+ total equity
- ✅ Clear path to FI visible

**System Health**:

- ✅ Portfolio value $1M+
- ✅ Positive monthly cash flow ($1K+)
- ✅ Average portfolio ROI 8%+
- ✅ LTV healthy (70-80% range)
- ✅ Appreciation on track (1-2%/year)

---

## Tips for Success

**Property Selection**:

- Buy in growing markets (population, job growth)
- Target positive cash flow from day 1
- Don't over-leverage (keep LTV <80%)
- Focus on long-term appreciation

**Portfolio Management**:

- Track all metrics monthly (cash flow, appreciation)
- Review annually and optimize
- Keep emergency fund separate
- Maintain properties well (prevent major repairs)

**Wealth Building**:

- Reinvest cash flow (buy more properties)
- Let equity build (don't extract with HELOCs)
- Focus on long-term hold (10+ years)
- Diversify geography and property types

---

## ROI & Impact

**Time Investment**: 30 min/month (tracking) + property search
**Annual ROI**: Passive income generation + wealth building

**Key Benefits**:

- Passive income ($1K+/month by year 3-4)
- Wealth building (equity + appreciation)
- Leverage (use debt strategically)
- Tax benefits (depreciation, deductions)
- Path to financial independence

---

**Created with the goal-centric life management system**
**Build wealth through real estate while pursuing financial independence**
