---
description: "Manage tenant lifecycle from application through lease renewal, with rent collection and communication tracking"
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
argument-hint: "[apply|screen|lease|manage|communicate] [--property <address>] [--status active|past]"
---

# /real-estate:tenants - Tenant Lifecycle Management

Track tenants from application through screening, leasing, rent collection, and renewal with communication history.

## Quick Start

**Screen a new applicant:**

```bash
/real-estate:tenants apply
```

**List all tenants:**

```bash
/real-estate:tenants list
```

**Manage tenant record:**

```bash
/real-estate:tenants manage
```

**Log communication:**

```bash
/real-estate:tenants communicate
```

**Track rent collection:**

```bash
/real-estate:tenants rent
```

---

## System Overview

This command implements **tenant-centric property management** where:

1. Applicants are screened systematically (credit, background, income)
2. Leases are tracked with clear terms and renewal dates
3. Rent collection is monitored (on-time payments, delinquencies)
4. Communication is logged for legal protection

**Key Principle**: Good tenants = reliable cash flow. Screening and selection is the most important step.

---

## Mode 1: APPLY - Tenant Application & Screening

Screen new applicant with systematic evaluation.

### Application Template

```
TENANT APPLICATION - 123 Oak Street
═════════════════════════════════════════════════════════════

APPLICANT INFORMATION
├── Name: John Smith
├── Email: john@email.com
├── Phone: (555) 123-4567
├── Date of application: Jan 15, 2025
├── Move-in date desired: Feb 1, 2025
└── Lease term: 12 months

SCREENING RESULTS
┌─ CREDIT CHECK (Credit Karma / Equifax)
├── Credit score: 750 (EXCELLENT)
├── Payment history: Clean (no lates)
├── Debt-to-income: 28% (healthy)
└── Status: ✅ PASS

┌─ BACKGROUND CHECK (E-Verify / Checkr)
├── Criminal history: Clean
├── Eviction history: None
├── Sex offender registry: Clear
└── Status: ✅ PASS

┌─ INCOME VERIFICATION
├── Employer: Tech Company Inc.
├── Annual income: $120,000
├── Required income: $48,000 (4x rent check)
├── Income-to-rent ratio: 3.3x (excellent - can easily afford)
└── Status: ✅ PASS

┌─ RENTAL HISTORY
├── Current landlord: Jane Doe (previous property)
├── Reference check: "Excellent tenant, always paid on time"
├── Tenure: 3 years (stable)
├── Reason for move: New job in Austin
└── Status: ✅ PASS

┌─ EMPLOYMENT VERIFICATION
├── Current employer: Tech Company Inc.
├── Job title: Senior Engineer
├── Employment length: 5 years (stable)
├── Expected continuation: Yes
└── Status: ✅ PASS

SCREENING SCORE
├── Credit: 25/25 (excellent)
├── Background: 25/25 (clean)
├── Income: 25/25 (3.3x requirement)
├── Rental history: 23/25 (excellent reference)
├── Employment: 25/25 (stable, good income)
└── TOTAL: 123/125 (98.4%) ⭐⭐⭐ A+ APPLICANT

DECISION
├── Status: APPROVED ✅
├── Confidence: VERY HIGH (accept immediately)
├── Next step: Send lease agreement for signature
└── Timeline: Move-in Feb 1, 2025

TERMS OFFERED
├── Rent: $2,800/month
├── Lease term: 12 months
├── Deposit: $2,800 (one month)
├── Utilities: Tenant pays (electric, water, internet)
├── Pet policy: No pets
└── Move-in: Feb 1, 2025
```

### Screening Checklist

**Step 1: Credit Check**

- Minimum score: 650+ (700+ preferred)
- No recent late payments (last 12 months clean)
- Debt-to-income: <40% (can afford rent)

**Step 2: Background Check**

- No criminal history (drug convictions = auto-reject)
- No eviction history
- No sex offender registry

**Step 3: Income Verification**

- Minimum income: 3-4x monthly rent
- Stable employment (>2 years)
- Can provide pay stubs or tax returns

**Step 4: Rental History**

- Contact previous landlords
- At least 2 years rental history preferred
- No history of property damage or disputes

**Step 5: Employment Verification**

- Verify current employment
- Confirm job stability
- Get contact info for future verification

---

## Mode 2: LEASE - Create & Manage Leases

Create lease agreements and track lease lifecycle.

### Lease Template

```
LEASE AGREEMENT
PROPERTY: 123 Oak Street, Austin, TX 78701
═════════════════════════════════════════════════════════════

PARTIES
├── Landlord: You (Property Owner)
├── Tenant: John Smith
├── Start date: Feb 1, 2025
├── End date: Jan 31, 2026
├── Lease term: 12 months
└── Status: ACTIVE (3 months into lease)

RENTAL TERMS
├── Monthly rent: $2,800
├── Rent due date: 1st of month
├── Payment method: ACH transfer (preferred)
├── Late fee: $100 after 5-day grace period
├── NSF fee: $50 per bad check
└── Rent history: 3/3 on time (excellent) ✓

SECURITY DEPOSIT
├── Deposit amount: $2,800
├── Deposit held in: Separate escrow account
├── Account: [Bank details]
├── Interest accrued: $12
├── Status: Held in trust (not commingled)
└── Refund upon lease end: Full (minus any damages)

PROPERTY RULES
├── No pets (strict)
├── No subletting without written permission
├── Quiet hours: 10pm - 8am
├── Maintenance: Tenant responsible for minor repairs
├── Guest policy: Reasonable duration stays only
├── Smoking: Not permitted (smoking outside only)
└── Utilities: Tenant pays (electric, water, gas, internet)

LANDLORD RESPONSIBILITIES
├── Habitable condition: YES (pass inspection)
├── Maintenance: Landlord provides (major repairs)
├── Insurance: Landlord maintains property insurance
├── Property tax: Landlord pays
├── Utilities: Landlord pays none (tenant pays all)
└── Access: 24-hour notice for non-emergencies

MOVE-IN CHECKLIST
├── [ ] Keys provided and documented
├── [ ] Walk-through inspection completed
├── [ ] Photos taken (condition documentation)
├── [ ] Utility transfer completed
├── [ ] Deposit received and cleared
└── Move-in completed: Feb 1, 2025 ✓

LEASE HISTORY
├── Original start: Feb 1, 2025
├── Lease type: 12-month fixed
├── Renewals: None yet (current lease active)
├── Modifications: None
└── Status: ACTIVE & COMPLIANT ✅

UPCOMING ACTIONS
├── [ ] Schedule lease renewal discussion (Oct 2025)
├── [ ] Send renewal lease offer (Nov 1, 2025)
├── [ ] Collect response (30 days)
└── [ ] Complete renewal (Jan 31, 2026)
```

---

## Mode 3: MANAGE - Tenant Record & Updates

View and update tenant information.

### Tenant Profile

```
TENANT PROFILE: John Smith
Property: 123 Oak Street
═════════════════════════════════════════════════════════════

CONTACT INFORMATION
├── Name: John Smith
├── Email: john@email.com
├── Phone: (555) 123-4567
├── Emergency contact: Jane Smith (wife, 555-999-9999)
└── Lease: 12 months (Feb 1, 2025 - Jan 31, 2026)

RENT PAYMENT HISTORY
├── Month 1 (Feb): $2,800 ✓ Paid on time
├── Month 2 (Mar): $2,800 ✓ Paid on time
├── Month 3 (Apr): $2,800 ✓ Paid on time
├── Payment method: ACH direct deposit (reliable)
├── On-time rate: 100% (3/3 months)
├── Average days late: 0
├── Late payments: 0
├── Delinquent amount: $0
└── Status: EXCELLENT PAYMENT RECORD ✅

COMMUNICATION LOG
├── Jan 15: Application received
├── Jan 20: Approved after screening
├── Jan 25: Lease signed
├── Feb 1: Move-in completed
├── Feb 15: First check-in (all good)
├── Mar 5: Question about water heater (fixed same day)
├── Mar 20: Friendly check-in
├── Apr 10: Rent remittance (on time as usual)
└── Last contact: 2 weeks ago

MAINTENANCE REQUESTS
├── Total requests: 1
├── Resolved: 1
├── Average response: Same day
├── Status: Very responsive tenant ✓

LEASE RENEWAL TIMELINE
├── Lease ends: Jan 31, 2026
├── Renewal offer due: Nov 1, 2025 (170 days away)
├── Tenant feedback: Not yet discussed
├── Recommended action: Offer 12-month renewal at $2,900/month (+3.6%)
└── Strategy: Retain excellent tenant, modest rent increase

TENANT RATING: 9.5/10 ⭐⭐⭐
├── Payment reliability: 10/10 (always on time)
├── Property care: 9/10 (maintains property well)
├── Communication: 9/10 (responsive, respectful)
├── Tenant quality: 9/10 (no issues whatsoever)
└── Recommendation: RETAIN - Excellent tenant

NEXT ACTIONS
├── [ ] Continue monthly check-ins
├── [ ] Schedule annual inspection (Oct 2025)
├── [ ] Prepare renewal offer (Oct 2025)
└── [ ] Discuss renewal (Nov 2025)
```

---

## Mode 4: COMMUNICATE - Log Interactions

Record all tenant communications for legal protection.

### Communication Log

```
COMMUNICATION LOG: John Smith (123 Oak St)
═════════════════════════════════════════════════════════════

MARCH 5, 2025 - MAINTENANCE REQUEST
├── Tenant: John Smith
├── Method: Phone call
├── Topic: Water heater issue (running out of hot water)
├── Details: Tried 3x that week, pressure issue
├── Your response: Called plumber, fixed same day
├── Resolution: Quick fix, part replacement $45
├── Tenant satisfaction: Positive (thanked you)
├── Follow-up: None needed
└── Documented: March 5 ✓

MARCH 20, 2025 - FRIENDLY CHECK-IN
├── Tenant: John Smith
├── Method: Email
├── Topic: General well-being check
├── Message: "Hi John, just checking in. How's everything? Any issues?"
├── Tenant response: "All great! Love the place. Thanks for quick fix last month."
├── Your response: "Happy to help! Let us know if you need anything."
├── Tone: Positive, professional
└── Documented: March 20 ✓

APRIL 10, 2025 - RENT PAYMENT
├── Tenant: John Smith
├── Method: ACH transfer
├── Amount: $2,800
├── Received date: April 1 (on time!)
├── Confirmation: Deposit cleared April 2
└── Status: PAID & VERIFIED ✓

COMMUNICATION BEST PRACTICES
├── Document everything (emails, calls, meetings)
├── Keep professional tone (friendly but formal)
├── Respond promptly (within 24 hours)
├── Keep records (for legal protection)
├── Regular check-ins (builds relationship)
└── Early warning: Address issues before they escalate
```

---

## Mode 5: RENT - Track Rent Collection

Monitor rent payments and collection status.

### Rent Collection Dashboard

```
RENT COLLECTION SUMMARY (Property: 123 Oak St)
═════════════════════════════════════════════════════════════

CURRENT STATUS
├── Lease: Active (John Smith)
├── Monthly rent: $2,800
├── Due date: 1st of month (with 5-day grace period)
├── Payment method: ACH direct deposit
├── Status: UP TO DATE ✅

PAYMENT HISTORY
├── February: $2,800 ✓ Received Feb 1
├── March: $2,800 ✓ Received Mar 1
├── April: $2,800 ✓ Received Apr 1
├── Total collected (YTD): $8,400
├── Expected (YTD): $8,400
├── Collection rate: 100% ✅

ON-TIME PAYMENT RATE
├── Months paid on time: 3
├── Months late: 0
├── Months missing: 0
├── On-time rate: 100% (perfect)
└── Status: EXCELLENT ✅

AGING ANALYSIS
├── Current (due within 5 days): None
├── 0-30 days late: $0
├── 30-60 days late: $0
├── >60 days late: $0
└── Total delinquent: $0

ANNUAL PROJECTION
├── Monthly rent: $2,800
├── Annual rent: $33,600 (if tenant stays full year)
├── Days until lease end: 280 days
├── Expected rent (remaining): $25,200
└── Total expected (full year): $33,600

TENANT RELIABILITY SCORE: 10/10 ⭐⭐⭐
├── Payment punctuality: 10/10 (always on time)
├── Payment method reliability: 10/10 (ACH never fails)
├── Communication on issues: 10/10 (responsive)
├── Lease compliance: 10/10 (no violations)
└── Overall: A+ TENANT - Retain at all costs
```

---

## Data Storage

Tenant data is saved in:

**JSON File** (CLI):

```
.claude/data/tenants.json
├── Tenant profiles (contact, application, screening)
├── Lease agreements (terms, dates, renewals)
├── Rent payment history (monthly tracking)
├── Communication logs (interactions, issues)
└── Maintenance requests (issues, resolutions)
```

**PostgreSQL** (Analytics):

```
tenants table
├── tenant_id, property_id, name, contact_info
├── lease_start, lease_end, rent_amount
├── application_score, payment_history
├── created_at, updated_at

leases table
├── lease_id, tenant_id, property_id
├── start_date, end_date, monthly_rent
├── deposit_amount, renewal_date
└── status (active, ended, renewal_pending)

rent_payments table
├── payment_id, lease_id, month, year
├── amount, date_received, status (paid/late/missing)
└── date_recorded
```

---

## Integration with Life Goals

Good tenant management = reliable passive income toward financial independence:

```
LIFE GOAL: Financial Independence
├── Real estate generates passive income: YES
│   ├── Reliable tenants = consistent rent collection
│   ├── Property maintenance = long-term appreciation
│   └── Low vacancy = maximized cash flow
└── Status: ON TRACK with excellent tenants
```

---

## Success Criteria

**After first tenant:**

- ✅ Screening completed systematically
- ✅ Lease signed and documented
- ✅ First rent payment received

**After 3-6 months:**

- ✅ Rent collection 95%+
- ✅ Communication log maintained
- ✅ Tenant satisfaction high

**System Health**:

- ✅ Occupancy rate 95%+
- ✅ Collection rate 99%+
- ✅ Tenant quality score 8+/10
- ✅ Lease renewal rate 80%+

---

**Created with the goal-centric life management system**
**Excellent tenants = reliable passive income for financial independence**
