---
description: "Evaluate investment opportunities with financial analysis, cash-on-cash return calculations, and deal scoring"
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
argument-hint: "[analyze|evaluate|compare|pipeline] [--roi-target <percentage>] [--location <city>]"
---

# /real-estate:deals - Investment Analysis & Deal Evaluation

Analyze potential property deals with cash flow projections, ROI calculations, and decision scoring.

## Quick Start

**Analyze a new deal:**

```bash
/real-estate:deals analyze
```

**Evaluate multiple properties:**

```bash
/real-estate:deals compare
```

**Track deal pipeline:**

```bash
/real-estate:deals pipeline
```

**Calculate returns:**

```bash
/real-estate:deals calc
```

---

## System Overview

This command implements **deal-centric real estate analysis** where:

1. Every potential property is evaluated systematically
2. Financial projections are calculated (cash flow, ROI, IRR)
3. Deals are scored against investment criteria
4. Decisions are data-driven (not emotion-driven)

**Key Principle**: You must systematically evaluate every deal. Most deals won't meet your criteria. A few exceptional deals will.

---

## Mode 1: ANALYZE - Evaluate Single Deal

Comprehensive analysis of a potential property investment.

### Deal Analysis Template

```
DEAL ANALYSIS: 456 Elm Avenue, Austin TX
═════════════════════════════════════════════════════════════

PROPERTY DETAILS
├── Address: 456 Elm Avenue, Austin, TX 78702
├── Type: Duplex (2 units - 2bd/1ba each)
├── Year built: 1995 (renovated 2015)
├── Lot size: 6,000 sq ft
├── Unit 1: Rented ($1,400/month)
├── Unit 2: Vacant (available for rent)
└── Status: Off-market (agent referral)

ACQUISITION TERMS
├── Asking price: $320,000
├── Inspection: Passed (minor issues only)
├── Days on market: 18 days
├── Negotiation: Willing to negotiate
├── Financing: 80% LTV (80% loan, 20% down)
├── Proposed offer: $310,000 (3% below ask)

FINANCIAL ANALYSIS
┌─ PURCHASE & FINANCING
├── Proposed purchase: $310,000
├── Down payment (20%): $62,000
├── Loan amount: $248,000
├── Interest rate: 4.5% (estimated)
├── Loan term: 30 years
├── Monthly payment: $1,255
└── Total invested: $62,000 (cash needed)

┌─ INCOME ANALYSIS
├── Unit 1 rent: $1,400/month (occupied)
├── Unit 2 rent: $1,400/month (vacant, opportunity!)
├── Gross rental: $2,800/month (if fully rented)
├── Annual gross: $33,600
├── Vacancy assumption: 5% = -$1,680
├── Effective rental: $31,920

┌─ EXPENSE ANALYSIS
├── Mortgage: $1,255/month
├── Property tax: $260/month
├── Insurance: $100/month
├── Maintenance (5% of rent): $140/month
├── Property management (10%): $280/month
├── HOA/utilities: $0
├── Total expenses: $2,035/month
├── Annual expenses: $24,420

┌─ CASH FLOW ANALYSIS
├── Gross monthly rent: $2,800 (both occupied)
├── Total monthly expense: $2,035
├── Monthly cash flow: $765
├── Annual cash flow: $9,180
├── Per unit annual cash flow: $4,590
└── Status: POSITIVE CASH FLOW ✅

┌─ ROI ANALYSIS
├── Initial investment: $62,000
├── Annual cash flow: $9,180
├── Cash-on-cash return: 14.8% ($9,180 / $62,000) ⭐
├── Status: EXCELLENT (>8% target) ✅

┌─ APPRECIATION ANALYSIS
├── Conservative appreciation: 1.5%/year
├── Annual appreciation: $4,650 (on $310K value)
├── 5-year appreciation: $23,250
├── Equity build from paydown: $20,000+ (in 5 years)
├── Total equity growth (5 years): $43,250+

┌─ CAPITALIZATION RATE
├── NOI (Net Operating Income): $7,500 (annual, excluding mortgage)
├── Property value: $310,000
├── Cap Rate: 2.4% (NOI / Value)
├── Note: Low cap rate is normal (rates vary by market)
└── Benchmark: Austin average is 3-4%

┌─ INTERNAL RATE OF RETURN (IRR)
├── Year 1 cash flow: $9,180
├── Year 5 total return: $45,900 (cash flow) + appreciation + equity paydown
├── IRR over 5 years: ~18% (cash flow + appreciation + paydown combined)
└── Status: STRONG (exceeds 10% target) ✅

DEAL SCORING
┌─ INVESTMENT CRITERIA
├── Cash-on-cash return (14.8% vs 8% target): 9/10 ⭐
├── Market strength (Austin growing): 9/10
├── Property condition (recently renovated): 9/10
├── Rental demand (strong, unit 1 rented): 8/10
├── Financing available (yes, good terms): 9/10
├── Appreciation potential (1.5%+ annually): 7/10
└── TOTAL SCORE: 8.5/10 (STRONG BUY)

RISK ASSESSMENT
├── Market risk: LOW (Austin strong market)
├── Tenant risk: LOW (one unit rented, strong demand)
├── Financing risk: LOW (fixed-rate mortgage, LTV 80%)
├── Liquidity risk: MEDIUM (2-3 months to sell)
└── Overall risk: LOW-MEDIUM ✅

DECISION: STRONG BUY ✅
├── Score: 8.5/10 (above 7.0 threshold)
├── ROI: 14.8% (well above 8% target)
├── Cash flow: Positive (+$765/month)
├── Alignment: YES (supports FI goal)
└── Action: Make offer at $310,000
```

---

## Mode 2: COMPARE - Evaluate Multiple Deals

Compare potential properties side-by-side.

### Deal Comparison

```
DEAL COMPARISON (3 properties)
═════════════════════════════════════════════════════════════

OPTION 1: 456 Elm Avenue (Duplex)
├── Purchase price: $310,000
├── Down payment: $62,000
├── Monthly cash flow: $765 (+$9,180/year)
├── Cash-on-cash return: 14.8% ⭐
├── Cap rate: 2.4%
├── Appreciation: 1.5%/year
├── Score: 8.5/10 (STRONG BUY)
└── Recommendation: STRONG - Good cash flow, excellent ROI

OPTION 2: 789 Main Street (Triplex)
├── Purchase price: $450,000
├── Down payment: $90,000
├── Monthly cash flow: $980 (+$11,760/year)
├── Cash-on-cash return: 13.1%
├── Cap rate: 2.1%
├── Appreciation: 1.5%/year
├── Score: 7.8/10 (GOOD BUY)
└── Recommendation: Good alternative, but less efficient capital use

OPTION 3: 321 Oak Drive (Single Family)
├── Purchase price: $280,000
├── Down payment: $56,000
├── Monthly cash flow: $420 (+$5,040/year)
├── Cash-on-cash return: 9.0%
├── Cap rate: 2.5%
├── Appreciation: 1.5%/year
├── Score: 6.5/10 (WEAK BUY)
└── Recommendation: Lower cash flow, mediocre ROI - PASS

RECOMMENDATION
├── Best overall: Option 1 (Elm Avenue) - Best ROI
├── Best cash flow: Option 2 (Main Street) - More cash but less efficient
├── Avoid: Option 3 (Oak Drive) - Poor ROI
└── ACTION: Make offer on Option 1, keep Option 2 as backup
```

---

## Mode 3: PIPELINE - Track Deal Opportunities

Monitor properties in your deal pipeline.

### Pipeline Dashboard

```
DEAL PIPELINE (6 opportunities)
═════════════════════════════════════════════════════════════

ANALYSIS IN PROGRESS (2 deals)
├── 456 Elm Avenue: Score 8.5/10
│   ├── Status: Analyzing (will make offer this week)
│   ├── Expected purchase: $310,000
│   ├── Timeline: Close by May 15
│   └── Action: Get appraisal, finalize financing
│
└── 789 Main Street: Score 7.8/10
    ├── Status: Secondary option (waiting on Elm)
    ├── Expected purchase: $450,000
    └── Timeline: Only if Elm falls through

OFFERS PENDING (1 deal)
├── 321 Oak Drive: Score 6.5/10 (WITHDRAWN)
│   ├── Status: Pulled offer (scored too low)
│   └── Reason: Poor cash-on-cash return

POTENTIAL (3 deals)
├── 555 Cedar Lane: Score pending
│   ├── Status: Need more info (awaiting appraisal)
│   └── Timeline: 2 weeks
│
├── 777 Birch Road: Score pending
│   ├── Status: Market too high (negotiating)
│   └── Timeline: 1 week
│
└── 888 Pine Street: Score pending
    ├── Status: Awaiting inspection
    └── Timeline: 3 days

ANNUAL PIPELINE SUMMARY
├── Deals analyzed: 15 total
├── Offers made: 3
├── Accepted: 1 (the property you bought)
├── Closed: 1
├── Win rate: 6.7% (1 closed / 15 analyzed)
└── Note: Low win rate is normal (most deals don't meet criteria)
```

---

## Mode 4: CALC - Financial Calculators

Quick calculations for deal evaluation.

### Key Calculations

**Cash-on-Cash Return**:

```
= Annual cash flow / Initial cash investment
= $9,180 / $62,000
= 14.8%

Target: 8%+
```

**Cap Rate**:

```
= Net Operating Income / Property Value
= $7,500 / $310,000
= 2.4%

Note: Lower in appreciating markets, higher in cash-heavy markets
```

**Internal Rate of Return (IRR)**:

```
Combines cash flow + appreciation + equity paydown
Typical target: 10%+ annually
```

**Cash Flow Formula**:

```
Monthly = Gross Rent - (Mortgage + Taxes + Insurance + Maintenance + Mgmt)
Annual = Monthly × 12
```

---

## Deal Selection Criteria

**Financial Thresholds**:

- Cash-on-cash return: ≥8% (target 10%+)
- Cap rate: ≥2.5% (market dependent)
- Positive cash flow: YES (never cash flow negative)
- Down payment available: YES (don't stretch)

**Market Criteria**:

- Growing economy/population
- Strong rental demand
- Appreciating values (1%+ annually)
- Good schools (if residential)

**Property Criteria**:

- Good condition (avoid major repairs)
- Good bones (newer is not necessary)
- Tenant-ready or easily renovated
- Clear title, no liens

**Seller Criteria**:

- Motivated (willing to negotiate)
- Flexible (open to owner financing if needed)
- Honest about property condition

---

## Data Storage

Deal data is saved in:

**JSON File** (CLI):

```
.claude/data/deals.json
├── Deal analyses (all properties evaluated)
├── Scoring results (decision data)
├── Financial projections (cash flow, ROI)
├── Pipeline status (tracking opportunities)
└── Closed deals (acquisition history)
```

---

## Integration with Life Goals

Each deal must support financial independence:

```
LIFE GOAL: Financial Independence
├── Real estate generates passive income: YES
│   ├── Target: $60K/year passive income
│   ├── Each deal must generate $15K+ annually
│   ├── ROI: 8%+ cash-on-cash return minimum
│   └── Path: 4 properties @ $15K each = $60K
└── Decision framework: Only buy deals that hit targets
```

---

## Success Criteria

**After analyzing first deal:**

- ✅ Systematic evaluation completed
- ✅ Financial projections calculated
- ✅ Score determined (above/below 7.0 threshold)
- ✅ Clear decision: BUY or PASS

**After 5 deals analyzed:**

- ✅ Deal criteria refined (know what to look for)
- ✅ Win rate improving (better at spotting good deals)
- ✅ Pipeline established (consistent flow)
- ✅ 1-2 offers made (getting close)

**System Health**:

- ✅ Deal score threshold: 7.0+ (disciplined)
- ✅ Cash-on-cash minimum: 8% (profitable)
- ✅ Win rate: 5-10% (realistic)
- ✅ Closed deals: On track (1-2 per year)

---

**Created with the goal-centric life management system**
**Evaluate deals systematically to build wealth efficiently**
