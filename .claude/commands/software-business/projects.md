---
description: "Manage projects, track timelines, deliverables, and measure profitability against life/business goals"
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
argument-hint: "[create|list|track|complete|analyze] [--client <name>] [--goal <goal-id>] [--export]"
---

# /software-business:projects - Project Management System

Track all projects with timelines, deliverables, time tracking, and profitability analysis aligned to business and life goals.

## Quick Start

**Create a new project:**

```bash
/software-business:projects create
```

**List all projects:**

```bash
/software-business:projects list
```

**Track project progress:**

```bash
/software-business:projects track
```

**Complete a project:**

```bash
/software-business:projects complete
```

**Analyze project profitability:**

```bash
/software-business:projects analyze
```

---

## System Overview

This command implements **project-centric business management** where every project is:

1. Linked to a specific client
2. Measured for profitability (revenue vs. time)
3. Evaluated against business goals
4. Aligned with life goals (work-life balance)

**Key Principle**: A project is only "successful" if it:

- Delivers value to client (on time, on budget)
- Generates profit (revenue > cost)
- Aligns with business goals ($200K/year, build product, etc.)
- Respects life goals (≤40 hrs/week, high autonomy, etc.)

---

## Mode 1: CREATE - Define New Project

Create a new project with all essential parameters.

### Project Information

**Basic Details**:

- Project name
- Client name (from CRM)
- Project description
- Project type (custom dev, product, support, consulting)
- Status (backlog, planning, in-progress, on-hold, completed)

**Timeline**:

- Start date
- Target completion date
- Estimated hours
- Actual hours (tracked as you work)

**Financial**:

- Contract value (revenue)
- Estimated cost (time * hourly rate)
- Expected profit (revenue - cost)
- Payment terms (upfront, milestone-based, post-completion)

**Deliverables**:

- List of specific deliverables
- Acceptance criteria for each
- Delivery date for each

**Goals Alignment**:

- Which business goal does this serve? (e.g., "Build $200K/year business")
- Which life goal? (e.g., "Financial Independence", "Career growth")
- Alignment score (0-100)

### Project Template

```
PROJECT: E-commerce Platform Redesign
├── Client: TechCorp Solutions
├── Description: Redesign and rebuild TechCorp's e-commerce platform for better UX and mobile
├── Type: Custom Development
├── Status: Planning
│
├── TIMELINE:
│   ├── Start: Jan 15, 2025
│   ├── Target completion: Mar 31, 2025
│   ├── Estimated hours: 200
│   └── Actual hours: 0 (not started)
│
├── FINANCIAL:
│   ├── Contract value: $35,000
│   ├── Estimated cost: 200 hrs × $75/hr = $15,000
│   ├── Expected profit: $20,000
│   └── Payment: 50% upfront ($17.5K), 50% on completion
│
├── DELIVERABLES:
│   ├── Design mockups (20 hrs) - Due: Jan 31
│   ├── Frontend development (80 hrs) - Due: Mar 15
│   ├── Backend integration (60 hrs) - Due: Mar 20
│   ├── Testing & QA (25 hrs) - Due: Mar 28
│   └── Deployment & training (15 hrs) - Due: Mar 31
│
└── GOALS ALIGNMENT:
    ├── Business Goal: Build $200K/year software business
    │   └── Alignment: 9/10 (High-value project)
    ├── Life Goal: Financial Independence
    │   └── Alignment: 8/10 (Good profit margin, 200 hrs)
    └── Life Goal: Work-Life Balance
        └── Alignment: 7/10 (Fits in ~40 hrs/week for 5 weeks)
```

### Project Selection Criteria

Before accepting a project, evaluate:

**FINANCIAL CRITERIA**:

- Revenue: ≥$3K (minimum to be worth it)
- Profit margin: ≥40% (costs <60% of revenue)
- Hourly rate: ≥$75/hr ($35K / 200 hrs = $175/hr effective)
- Timeline: Realistic and achievable

**BUSINESS CRITERIA**:

- Supports business goal? (e.g., builds product, gets testimonial, etc.)
- Client quality? (Good communication, values your work)
- Potential for recurring revenue or referrals?
- Adds to portfolio or case study?

**LIFE GOAL CRITERIA**:

- Work hours: ≤40 hrs/week (doesn't overload)
- Project length: ≤3 months (doesn't drag on)
- Autonomy: ≥7/10 (you have decision-making power)
- Alignment: Serves your financial independence goal

**DECISION MATRIX**:

Rate each project on 5 dimensions (1-10 each):

1. **Profitability** (hours vs. revenue)
2. **Goal alignment** (business impact)
3. **Client quality** (communication, values)
4. **Work enjoyment** (interesting problem?)
5. **Life goal impact** (supports financial/career/balance goals)

**Total score** = Average of 5 dimensions

- 9-10: Strong YES (pursue immediately)
- 7-8: Good fit (discuss with client)
- 5-6: Moderate fit (only if no better projects)
- 3-4: Weak fit (pass or renegotiate)
- 1-2: Strong NO (decline)

Example:

```
E-commerce Platform Redesign Evaluation
├── Profitability: 9/10 ($175/hr effective rate)
├── Goal alignment: 9/10 (Builds business, builds product)
├── Client quality: 8/10 (Good communication history)
├── Work enjoyment: 8/10 (Interesting technical problem)
└── Life goal impact: 7/10 (Good profit, fits time budget)

SCORE: 8.2/10 → STRONG YES - Pursue immediately
```

---

## Mode 2: LIST - View All Projects

See all projects with key metrics and status.

### Project Dashboard

```
ACTIVE PROJECTS (3 total)
├── E-commerce Platform Redesign (TechCorp) - IN PROGRESS
│   ├── Progress: 45% (90/200 hrs)
│   ├── Status: On track (started Jan 15)
│   ├── Revenue: $35,000
│   ├── Profit estimate: $18,750 (50% complete)
│   └── Next deadline: Mar 15 (Frontend due)
│
├── Website Redesign (SmallBiz Inc.) - IN PROGRESS
│   ├── Progress: 80% (40/50 hrs)
│   ├── Status: Slightly behind (started Feb 1)
│   ├── Revenue: $8,000
│   ├── Profit estimate: $4,000 (low margin)
│   └── Next deadline: Mar 5 (Completion)
│
└── Mobile App Development (StartupXYZ) - PLANNING
    ├── Progress: 0% (0/300 hrs)
    ├── Status: Starting next week
    ├── Revenue: $60,000
    ├── Profit estimate: $30,000 (50% margin)
    └── Start date: Mar 10

COMPLETED PROJECTS (8 total this year)
├── Landing Page (TechStartup) - Completed 2 weeks ago
│   ├── Revenue: $5,000
│   └── Actual profit: $4,250 (85% margin - quick project)
│
├── API Integration (B2B Client) - Completed 1 month ago
│   ├── Revenue: $12,000
│   └── Actual profit: $7,200 (60% margin)
│
└── [6 more completed projects...]
    ├── Total 2025 revenue: $187,500
    └── Total 2025 profit: $98,750 (52% average margin)

PAUSED/ON-HOLD (2 total)
├── Custom CRM Implementation (LargeEnt) - On hold (awaiting client feedback)
└── API Redesign (OldClient) - Paused (awaiting budget approval)

BACKLOG (5 total opportunities)
├── Website Redesign Phase 2 (TechCorp) - Estimated $25K
├── Database Optimization (Various) - Estimated $8K
└── [3 more opportunities...]

METRICS
├── This month: 2 projects active, $43K revenue
├── This quarter: 4 projects completed, $98K revenue
├── This year: 8 projects completed, $187K revenue (on track for $250K+)
├── Average profit margin: 52%
├── Average client satisfaction: 4.7/5
└── Revenue per hour: $142 (improving)
```

### Filter & Sort Options

```bash
/software-business:projects list --status active
/software-business:projects list --client TechCorp
/software-business:projects list --status completed --sort revenue
/software-business:projects list --sort profitability
/software-business:projects list --goal "Build $200K business"
```

---

## Mode 3: TRACK - Log Time & Progress

Track hours spent and update deliverable status.

### Daily Time Logging

For each project, log:

- Date
- Hours worked
- Work description
- Deliverable progress
- Any blockers or risks

**Example**:

```
PROJECT: E-commerce Platform Redesign
DATE: Mar 1, 2025

Time log:
├── Morning: 3 hours (Frontend: User authentication)
├── Afternoon: 2 hours (Code review, bug fixes)
└── Total: 5 hours (Total so far: 95/200 hrs = 47.5% complete)

Deliverables:
├── Frontend development: 80% complete (64/80 hrs)
└── On track for Mar 15 delivery

Blockers:
├── Waiting on design assets from designer (1 day delay expected)
└── Action: Reached out to TechCorp, expecting assets by Mar 3

Risks:
├── Testing phase might take longer than estimated (est. 25 hrs)
└── Contingency: Will add 2 buffer days to schedule
```

### Weekly Project Status

Every Friday, update project status:

```
E-COMMERCE PLATFORM REDESIGN
┌─ PROGRESS THIS WEEK
├── Hours logged: 20/week
├── Total progress: 45% → 55% (10% increase)
├── On track? YES
└── Expected completion: Mar 28 (3 days early)

┌─ DELIVERABLES STATUS
├── Design mockups: ✅ COMPLETE
├── Frontend development: 80% IN PROGRESS (due Mar 15)
├── Backend integration: 15% STARTING (due Mar 20)
├── Testing & QA: 0% (due Mar 28)
└── Deployment & training: 0% (due Mar 31)

┌─ HOURS TRACKING
├── Budgeted: 200 hours
├── Logged so far: 95 hours (47.5%)
├── Estimated remaining: 100 hours
├── Efficiency: On track (no overruns yet)
└── Profit forecast: $18,750 (unchanged)

┌─ RISKS & BLOCKERS
├── Design assets delay (1 day) - MANAGED
├── Testing complexity (might need +10 hrs) - MONITORING
└── Client change requests (2 small requests this week) - TRACKED

┌─ NEXT WEEK GOALS
├── Complete frontend development by Mar 15 ✅
├── Start backend integration
└── Address any design asset gaps
```

### Capacity Planning

Track project load vs. life goal targets:

```
THIS WEEK'S CAPACITY
├── Target hours/week (from /life:goals): 40 hours
├── Hours budgeted to projects: 35 hours
├── Remaining capacity: 5 hours (buffer)

PROJECT ALLOCATION
├── E-commerce Redesign: 20 hours (57%)
├── Website Redesign: 10 hours (29%)
├── Admin/Overhead: 5 hours (14%)
└── Total: 35 hours ✅ (within 40-hour target)

✅ LIFE GOAL CHECK
├── Work hours: 35/40 budgeted (87.5%) ✅
├── Deep work blocks: 4/4 protected ✅
├── Client calls: Clustered Tue/Thu ✅
└── Status: ALIGNED with life goals
```

---

## Mode 4: COMPLETE - Mark Project Done

Close out completed project with final analysis.

### Project Completion Checklist

Before marking complete:

- [ ] All deliverables completed and delivered
- [ ] Client acceptance confirmed
- [ ] Payment received or scheduled
- [ ] Final invoice sent
- [ ] Code documented and archived
- [ ] Lessons learned documented
- [ ] Case study or testimonial request sent
- [ ] Project archived in system

### Project Closeout Summary

```
PROJECT: E-commerce Platform Redesign
STATUS: COMPLETED ✅

┌─ FINANCIAL SUMMARY
├── Contract value: $35,000
├── Actual hours: 195 (vs. 200 estimated)
├── Actual cost: $14,625 (at $75/hr)
├── Actual profit: $20,375 (58% margin) ✅
├── Profit per hour: $104.49
└── Result: BETTER THAN EXPECTED (5 hours saved, higher profit)

┌─ TIMELINE SUMMARY
├── Start date: Jan 15, 2025
├── Target completion: Mar 31, 2025
├── Actual completion: Mar 28, 2025
├── Status: 3 DAYS EARLY ✅
└── Result: AHEAD OF SCHEDULE

┌─ QUALITY SUMMARY
├── Deliverables quality: 9.5/10
├── Client satisfaction: 5/5 ⭐
├── Code quality: 8.5/10
└── Defects found post-delivery: 1 (minor, fixed in 30 min)

┌─ GOALS ALIGNMENT
├── Business goal impact: Contributes $20,375 toward $200K/year
│   └── YTD progress: $187,500 (93.75% of annual goal)
├── Life goal impact: Generated significant profit in 5 weeks
│   └── Fits within work-life balance targets
└── Overall: STRONG ALIGNMENT ✅

┌─ LESSONS LEARNED
├── What went well:
│   ├── Good communication with client (daily standups)
│   ├── Clear scope definition prevented scope creep
│   ├── Test-driven development caught bugs early
│   └── Extra 5-hour buffer was unnecessary (only used 1 hour)
│
├── What could be better:
│   ├── Designer delays were somewhat expected - buffer more next time
│   ├── Client had 2 change requests mid-project (negotiate stricter scope)
│   └── Testing took less time than estimated (can reduce future estimates)
│
└── Action for next projects:
    ├── Reduce testing estimate from 25 to 20 hours
    ├── Add 3-day designer buffer to timeline
    └── Include change-request process in contract upfront

┌─ REFERRAL & CASE STUDY
├── Case study requested: YES (TechCorp agreed)
├── Testimonial: YES (5-star review provided)
├── Referral potential: HIGH (Client expressed interest in Phase 2)
├── Revenue opportunity: $25,000+ (Phase 2 redesign)
└── Action: Send case study outline to client this week

PROJECT ARCHIVED ✅
```

---

## Mode 5: ANALYZE - Project Profitability

Analyze profitability trends and optimize pricing.

### Profitability Metrics

```
2025 YEAR-TO-DATE PROJECT ANALYSIS

REVENUE SUMMARY
├── Total revenue: $187,500 (through current month)
├── Completed projects: 8
├── Average revenue/project: $23,438
├── On track for: $250K+ annual revenue (125% of goal)
└── Status: STRONG ✅

PROFITABILITY SUMMARY
├── Total costs: $98,750
├── Total profit: $88,750 (47% margin)
├── Average profit/project: $11,094
├── Best margin project: 85% (Landing Page - $4,250 profit)
├── Worst margin project: 40% (Website Redesign - $4,000 profit on $10K)
└── Status: 47% margin (target: 50%+) - Close

EFFICIENCY METRICS
├── Total hours worked: 1,183 hours (YTD)
├── Revenue per hour: $158.49
├── Profit per hour: $74.97
├── Average project duration: 4.7 weeks
└── Status: High efficiency ✅

COMPARISON TO TARGETS
├── Annual revenue goal: $200,000
├── YTD actual: $187,500
├── % of goal: 93.75% (on track for 125%+)
├── Profit per hour target: $70
├── YTD actual: $74.97 ($4.97 better)
└── Status: EXCEEDING TARGETS ✅

TRENDS
├── Revenue trend: Increasing (avg project value growing)
├── Profit margin trend: Stable (47% average)
├── Hours efficiency: Improving (hours per project decreasing)
└── Client satisfaction: 4.7/5 average ✅
```

### Project Profitability Ranking

```
TOP 5 MOST PROFITABLE PROJECTS
1. Landing Page (TechStartup)
   ├── Revenue: $5,000
   ├── Profit: $4,250 (85% margin)
   ├── Time: 10 hours
   └── Profit/hour: $425

2. E-commerce Platform Redesign (TechCorp)
   ├── Revenue: $35,000
   ├── Profit: $20,375 (58% margin)
   ├── Time: 195 hours
   └── Profit/hour: $104

3. API Integration (B2B Client)
   ├── Revenue: $12,000
   ├── Profit: $7,200 (60% margin)
   ├── Time: 80 hours
   └── Profit/hour: $90

4. Consulting Project (Various)
   ├── Revenue: $15,000
   ├── Profit: $8,250 (55% margin)
   ├── Time: 100 hours
   └── Profit/hour: $82.50

5. Database Optimization (Various)
   ├── Revenue: $8,000
   ├── Profit: $4,160 (52% margin)
   ├── Time: 50 hours
   └── Profit/hour: $83.20

LOW MARGIN PROJECTS TO AVOID
├── Website Redesign: 40% margin (too many revisions)
└── Support Projects: 35% margin (time-intensive, low billable hours)

RECOMMENDATION
├── Focus on projects similar to #1 and #2 (high profit/hour)
├── Negotiate better rates for support-type work
├── Set stricter revision/change request limits
└── Target: Increase overall margin from 47% to 55%+
```

### Pricing Optimization

```
CURRENT PRICING ANALYSIS

By Project Type:
├── Custom Development: $75-150/hr
│   ├── Current average: $110/hr
│   ├── Market rate: $100-200/hr
│   ├── Recommendation: Increase to $125/hr (+13%)
│   └── Impact: +$25K/year in profit (on $200K revenue)
│
├── Consulting: $85/hr
│   ├── Market rate: $150-250/hr
│   ├── Recommendation: Increase to $150/hr (+76%)
│   └── Impact: +$8K/year
│
└── Support/Maintenance: $60/hr
    ├── Market rate: $75-100/hr
    ├── Recommendation: Increase to $85/hr (+42%)
    └── Impact: +$5K/year

TOTAL PRICING OPTIMIZATION OPPORTUNITY
├── Potential additional profit: $38K/year (23% increase)
├── Strategy: Gradually increase rates on new projects
├── Timeline: Phase in over 6 months (test market response)
└── Action: Raise rates for new contracts starting next month

RISK MITIGATION
├── Will existing clients accept higher rates? Limited (mostly fixed-price)
├── Market acceptance? Good (competitor rates are higher)
├── Implementation: Increase on new projects, grandfather existing clients
└── Expected adoption: 60-70% of new projects at new rates
```

---

## Data Storage

Project data is saved in:

**JSON File** (CLI):

```
.claude/data/projects.json
├── Project definitions (timeline, deliverables, financials)
├── Time logs (hours tracked per day/week)
├── Status updates (progress, blockers, risks)
├── Completion summaries (actual vs. estimated)
└── Profitability analysis
```

**PostgreSQL** (Analytics):

```
projects table
├── project_id, name, client_id
├── start_date, target_completion, actual_completion
├── contract_value, actual_cost, actual_profit
├── status, alignment_score
└── created_at, updated_at

project_deliverables table
├── deliverable_id, project_id
├── description, hours_estimated, hours_actual
├── target_completion, actual_completion
└── acceptance_criteria, status

time_logs table
├── log_id, project_id, date
├── hours, description, deliverable_id
└── created_at, updated_at
```

---

## Integration with Life Goals

Each project should ladder back to business and life goals:

```
LIFE GOAL: Financial Independence
├── Business Goal: Build $200K/year software business
│   └── Projects:
│       ├── E-commerce Platform Redesign: $35K revenue ($20K profit)
│       ├── Website Redesign Phase 2: $25K revenue
│       ├── Mobile App Development: $60K revenue
│       └── Various: $80K+ revenue
│           └── Total on track for $200K+ annual revenue ✅
│
├── Key Result: Hit $200K MRR by end of year
│   └── Requires: 8-10 projects of $20-60K each
│       ├── YTD: 8 completed projects ($187K) ✅
│       └── Forecast: 10-12 projects by year-end ✅
│
└── Supports: Financial Independence in 10 years
    ├── Annual profit: $100K+ (at 50% margin)
    ├── Invested annually: $80K (80% of profit)
    ├── 10-year compounding: $1.2M+ (at 8% return)
    └── Status: On track for $2M+ net worth by 35 ✅
```

---

## Success Criteria

**After creating first project:**

- ✅ Project timeline established
- ✅ Deliverables clearly defined
- ✅ Financial parameters set
- ✅ Goal alignment calculated (score >7/10)

**After 1 month of tracking:**

- ✅ Time logs consistent (every project tracked)
- ✅ Weekly status updates completed
- ✅ Project progress visible (% complete accurate)
- ✅ Capacity within life goal targets (<40 hrs/week)

**After completing first project:**

- ✅ Actual hours vs. estimate accuracy (within 10%)
- ✅ Profit margin achieved (>40%)
- ✅ Client satisfaction (≥4/5)
- ✅ Lessons learned captured

**System Health**:

- ✅ Average profit margin 50%+
- ✅ Revenue per hour $100+
- ✅ Project selection score 8+/10 (strong alignment)
- ✅ Work hours ≤40/week (respecting life goals)
- ✅ Client satisfaction 4.5+/5

---

## Tips for Success

**Project Selection**:

- Evaluate every project against decision matrix
- Only accept projects scoring 7+/10
- Negotiate scope/rate if needed

**Time Tracking**:

- Log hours daily (not weekly)
- Be honest about time spent
- Track for accuracy (improves estimates)

**Profitability Optimization**:

- Review margin every month
- Increase prices on new projects
- Reduce low-margin work

**Life Goal Alignment**:

- Respect 40-hour/week target
- Avoid overcommitting (current projects vs. capacity)
- Maintain deep work time for product building

---

## ROI & Impact

**Time Investment**: 30 min/week (project tracking + analysis)
**Annual ROI**: Part of overall business model

**Key Benefits**:

- Visibility into project profitability
- Data-driven pricing decisions
- Predictable revenue (project pipeline)
- Alignment with business and life goals
- Better capacity planning

---

**Created with the goal-centric life management system**
**Track your projects to build a profitable business aligned with your goals**
