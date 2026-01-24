---
description: "Track maintenance requests, manage work orders, coordinate vendors, and monitor repair expenses"
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
argument-hint: "[request|track|vendor|expense] [--property <address>] [--priority high|medium|low]"
---

# /real-estate:maintenance - Maintenance & Repair Management

Create work orders, manage vendor relationships, track repair expenses, and maintain property condition records.

## Quick Start

**Create maintenance request:**

```bash
/real-estate:maintenance request
```

**Track work order:**

```bash
/real-estate:maintenance track
```

**Manage vendors:**

```bash
/real-estate:maintenance vendor
```

**Monitor expenses:**

```bash
/real-estate:maintenance expense
```

---

## System Overview

This command implements **maintenance-centric property operations** where:

1. Maintenance requests are tracked systematically (prevent reactive emergencies)
2. Vendors are rated and managed (quality + cost control)
3. Expenses are categorized (repairs vs. improvements)
4. Property condition is monitored (catch issues early)

**Key Principle**: Preventive maintenance costs less than emergency repairs. Regular upkeep extends property life and protects your investment.

---

## Mode 1: REQUEST - Create Work Orders

Submit maintenance requests and create work orders.

### Work Order Template

```
WORK ORDER: 123 Oak Street
═════════════════════════════════════════════════════════════

REQUEST DETAILS
├── Property: 123 Oak Street
├── Date requested: April 15, 2025
├── Priority: MEDIUM
├── Type: Preventive maintenance (HVAC service)
├── Issue: Annual AC inspection and filter change
├── Estimated cost: $150
├── Status: OPEN (awaiting vendor quote)

WORK ORDER INFO
├── WO#: HVAC-001
├── Requested by: You
├── Assigned to: (TBD - pending vendor schedule)
├── Target completion: April 30, 2025
├── Estimated hours: 1-2 hours
└── Emergency: No (scheduled maintenance)

DESCRIPTION
├── Tenant request: "AC running but filters look dirty"
├── Your assessment: Routine maintenance, spring service recommended
├── Scope: Replace filters, inspect coils, test refrigerant charge
└── Safety concern: None

VENDOR COORDINATION
├── Selected vendor: ABC HVAC (regular vendor, good rating)
├── Contact: Mike Johnson (555-222-2222)
├── Quote status: Pending (requested April 15)
├── Approval: Waiting for quote under $200
└── Next step: Follow up if no quote by April 18

EXPENSE TRACKING
├── Estimate: $150 (filter + labor)
├── Actual (pending): TBD
├── Budget category: Maintenance (routine)
├── Account: Operating account
└── Status: PRE-APPROVAL

TENANT COORDINATION
├── Tenant notification: Sent April 15 via email
├── Access: Yes (tenant available weekdays)
├── Preferred dates: Before May 1
└── Communication: Good (tenant responsive)

COMPLETION (upon finish)
├── [ ] Work completed
├── [ ] Inspection/approval
├── [ ] Payment processed
├── [ ] Documentation filed
└── Timeline: Pending contractor availability
```

### Priority Levels

**EMERGENCY** (Address immediately):

- Safety hazard (gas leak, electrical fire)
- Property damage in progress (roof leak during rain)
- Tenant unable to occupy (heat/AC failure in extreme weather)
- Hazardous condition (broken glass, sharp edges)

**HIGH** (Complete within 1-2 weeks):

- Tenant-reported significant issue
- Potential for further damage if not addressed
- Example: Plumbing leak, broken window, HVAC not working

**MEDIUM** (Schedule within 1 month):

- Preventive maintenance (annual inspections)
- Cosmetic issues causing tenant complaints
- Minor functionality issues
- Example: Filter change, caulking, paint touch-up

**LOW** (Schedule within quarter):

- Non-urgent cosmetic (paint, landscaping)
- Planned upgrades (new fixtures, flooring)
- Example: Update lighting, plant new shrubs

---

## Mode 2: TRACK - Monitor Work Orders

View all work orders and track progress.

### Work Order Dashboard

```
WORK ORDER STATUS (Property: 123 Oak Street)
═════════════════════════════════════════════════════════════

OPEN/IN PROGRESS (2 orders)
├── WO#HVAC-001: AC Inspection (Priority: MEDIUM)
│   ├── Requested: April 15
│   ├── Target: April 30
│   ├── Status: Awaiting vendor quote
│   └── Risk: On track (ample time)
│
└── WO#PLUMB-005: Faucet Repair (Priority: MEDIUM)
    ├── Requested: April 10
    ├── Target: April 25
    ├── Status: Approved, scheduled for April 20
    └── Risk: On track

COMPLETED THIS MONTH (3 orders)
├── WO#PAINT-001: Interior Paint Touch-up (Mar 28)
│   ├── Cost: $200
│   ├── Vendor: Local Painter
│   └── Status: ✓ COMPLETE
│
├── WO#ELEC-001: Outlet Replacement (Mar 15)
│   ├── Cost: $75
│   ├── Vendor: ABC Electric
│   └── Status: ✓ COMPLETE
│
└── WO#REPAIR-001: Drywall Patch (Mar 5)
    ├── Cost: $50
    └── Status: ✓ COMPLETE

MONTHLY EXPENSE SUMMARY
├── Completed work (March): $325
├── Pending quotes: $150 (HVAC)
├── Budget: $500/month (maintenance reserve)
├── Used: $325 (65% of budget)
├── Remaining: $175 (for emergency if needed)
└── Annual estimate: $3,900 (maintenance reserve)
```

---

## Mode 3: VENDOR - Manage Vendor Relationships

Track vendors with ratings and contact information.

### Vendor Profile

```
VENDOR: ABC HVAC Services
═════════════════════════════════════════════════════════════

CONTACT INFO
├── Company: ABC HVAC Services
├── Primary contact: Mike Johnson
├── Phone: (555) 222-2222
├── Email: mike@abchvac.com
├── Website: www.abchvac.com
├── License: #HVAC-12345 (verified)
└── Insurance: Commercial liability (current)

HISTORY
├── First service: March 2024
├── Total jobs: 4
├── Total spent: $850
├── Relationship: 13 months

PERFORMANCE RATING: 9/10 ⭐⭐⭐
├── Quality of work: 9/10 (excellent)
├── Timeliness: 9/10 (always on schedule)
├── Professionalism: 10/10 (courteous, clean)
├── Communication: 9/10 (responsive, clear quotes)
├── Pricing: 8/10 (competitive, fair estimates)
└── Recommendation: Preferred vendor - use for all HVAC work

PAST JOBS
├── Annual AC Inspection (Mar 2024): $150 ✓
├── Filter replacement (Jun 2024): $75 ✓
├── Compressor repair (Sep 2024): $625 ✓
└── Filter replacement (Dec 2024): $75 ✓

VENDOR DIRECTORY (5 vendors total)
├── Plumbing: John's Plumbing (9/10 - reliable)
├── Electrical: ABC Electric (8/10 - good work)
├── Roofing: Superior Roofing (8.5/10 - quality)
├── Painting: Local Painter (7/10 - adequate)
└── General: Jack-of-all-trades (6/10 - occasional use)

VENDOR MANAGEMENT
├── Keep pre-screened vendor list (3-4 per trade)
├── Get multiple quotes (>$500)
├── Negotiate volume discounts (regular work)
├── Monitor quality (inspect completed work)
├── Pay on time (builds goodwill, quick service)
└── Communicate clearly (prevent misunderstandings)
```

---

## Mode 4: EXPENSE - Track & Categorize Costs

Monitor maintenance expenses and identify trends.

### Expense Tracking

```
MAINTENANCE EXPENSE SUMMARY (2025)
═════════════════════════════════════════════════════════════

JANUARY
├── Preventive: Filter change ($75)
├── Repair: Faucet fix ($150)
├── Upgrade: New door lock ($200)
├── Total: $425

FEBRUARY
├── Preventive: Inspection ($100)
├── Repair: Window caulking ($75)
├── Total: $175

MARCH
├── Preventive: HVAC service ($150)
├── Repair: Paint touch-up ($200)
├── Repair: Outlet replacement ($75)
├── Total: $425

APRIL (YTD)
├── Pending: AC service ($150)
├── Pending: Faucet repair ($75)
├── Total (estimated): $225

ANNUAL EXPENSE ANALYSIS
├── YTD actual: $1,025 (3 months)
├── Monthly average: $342
├── Annual projection: $4,100
├── Budget: $5,000 (maintenance reserve)
├── Status: Within budget ✅

EXPENSE BREAKDOWN BY TYPE
├── Preventive maintenance: 35% ($1,425)
│   └── Example: Filter changes, inspections, annual services
├── Repairs: 50% ($2,050)
│   └── Example: Fixing broken items, patching damage
├── Upgrades: 15% ($615)
│   └── Example: New fixtures, improvements
└── Total: $4,090 (annual estimate)

EXPENSE BREAKDOWN BY TRADE
├── HVAC: 20% ($820)
├── Plumbing: 15% ($615)
├── Electrical: 10% ($410)
├── General maintenance: 30% ($1,230)
├── Cosmetic: 25% ($1,025)
└── Total: $4,090

KEY INSIGHTS
├── Preventive work is paying off (fewer emergency repairs)
├── HVAC is largest expense (monitor closely)
├── Vendors are being used efficiently
├── Expenses tracking within 5-year average
└── Overall: Healthy maintenance spending level
```

---

## Data Storage

Maintenance data is saved in:

**JSON File** (CLI):

```
.claude/data/maintenance.json
├── Work orders (requests, status, completion)
├── Vendor directory (contacts, ratings, history)
├── Expense tracking (costs, categories)
└── Property condition notes
```

**PostgreSQL** (Analytics):

```
work_orders table
├── wo_id, property_id, priority
├── description, status, completion_date
├── estimated_cost, actual_cost
└── vendor_assigned

vendors table
├── vendor_id, name, trade, contact_info
├── license, insurance, rating
├── total_jobs, total_spent
└── created_at, last_used_date

maintenance_expenses table
├── expense_id, property_id, vendor_id
├── date, amount, category
├── wo_id (linked to work order)
└── created_at
```

---

## Integration with Life Goals

Well-maintained properties = preserved asset value and reliable cash flow:

```
LIFE GOAL: Financial Independence
├── Real estate generates passive income: YES
│   ├── Preventive maintenance = avoid major repairs
│   ├── Property preservation = sustained value
│   └── Tenant satisfaction = low turnover
└── Status: ON TRACK with proactive maintenance
```

---

## Success Criteria

**After first property:**

- ✅ Vendor directory established (3-4 per trade)
- ✅ Annual maintenance plan created
- ✅ Budget allocated ($300-500/month)

**First year:**

- ✅ Work orders tracked consistently
- ✅ All routine maintenance completed
- ✅ No emergency repairs needed (preventive worked)

**System Health**:

- ✅ Expenses within 5-year average
- ✅ Vendor satisfaction high (8+/10)
- ✅ Property condition excellent
- ✅ Tenant satisfaction high (no maintenance complaints)

---

**Created with the goal-centric life management system**
**Preventive maintenance = lower costs, happier tenants, preserved property value**
