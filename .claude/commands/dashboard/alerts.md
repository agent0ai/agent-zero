---
description: Cross-business alerts and notifications
argument-hint: "[--severity critical|high|medium|low] [--type maintenance|financial|occupancy|tenant] [--resolved] [--export <filename>]"
model: claude-3-5-haiku-20241022
allowed-tools: ["Read", "Bash", "Write", "AskUserQuestion"]
---

# Cross-Business Alerts Dashboard

Unified alert system showing critical issues, warnings, and notifications across all business contexts with severity levels, impact assessment, and recommended actions.

## What This Command Does

Aggregates and prioritizes alerts from all businesses:

- **Critical Alerts**: Urgent issues requiring immediate action
- **High Priority Alerts**: Important issues needing attention this week
- **Medium Priority Alerts**: Issues to address in next 30 days
- **Low Priority Alerts**: Informational items and updates
- **Impact Assessment**: Financial and operational impact of each alert
- **Action Tracking**: Recommended steps and owner assignment
- **Alert History**: Resolved alerts and closure tracking

## Why This Matters

Multi-business operators face alert fatigue from scattered notifications across multiple systems. This unified alert system ensures critical issues don't slip through the cracks while filtering out noise. Alerts are smart-prioritized by actual impact on business.

## Usage

```bash
# Show all active alerts
/dashboard:alerts

# Show only critical alerts
/dashboard:alerts --severity critical

# Filter by alert type
/dashboard:alerts --type maintenance
/dashboard:alerts --type financial

# Show resolved alerts (for learning)
/dashboard:alerts --resolved

# Export for backup/analysis
/dashboard:alerts --export alerts-export.json
```

## Dashboard Structure

```
╔═════════════════════════════════════════════════════════════════════════════╗
║                         CROSS-BUSINESS ALERTS DASHBOARD                     ║
║                                                                             ║
║  Active Alerts: 12 | Critical: 3 | High: 5 | Medium: 3 | Low: 1            ║
║  Last Updated: 2025-01-22T14:35:00Z                                         ║
╚═════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│ 🚨 CRITICAL ALERTS (Immediate Action Required)                             │
├─────────────────────────────────────────────────────────────────────────────┤

│ ALERT #1: Payment System Down - Main St Rentals                            │
├──────────────────────────────────────────────────────────────────────────────┤
│ Severity: 🔴 CRITICAL                                                       │
│ Type: Financial/Operational                                                 │
│ Created: 2025-01-22T08:15:00Z                                               │
│ Status: ACTIVE (5 hours 20 minutes)                                         │
│                                                                             │
│ ISSUE:                                                                      │
│ Online payment portal is down. Tenants cannot submit rent payments online.  │
│ Currently impacting 12 units generating $2,400/month in rental income.      │
│                                                                             │
│ IMPACT ASSESSMENT:                                                          │
│ • Daily Revenue Loss: $80                                                   │
│ • Affected Units: 12/12 (100% of property)                                  │
│ • Affected Tenants: 12                                                      │
│ • Potential Monthly Loss: $2,400+ (if unresolved)                           │
│ • Customer Experience: ⚠️ Negative impact (3 calls already received)        │
│                                                                             │
│ ROOT CAUSE:                                                                 │
│ Server maintenance by hosting provider was supposed to be 2 hours but      │
│ discovered critical issue requiring additional 4+ hours to resolve.        │
│                                                                             │
│ ACTIONS TAKEN:                                                              │
│ ✓ Notified all tenants of issue via SMS + email                            │
│ ✓ Provided manual payment instructions                                      │
│ ✓ Escalated to hosting provider Level 2 support                            │
│ → Estimated restoration: 2025-01-22T15:00:00Z (15 minutes)                 │
│                                                                             │
│ RECOMMENDED NEXT STEPS:                                                     │
│ 1. IMMEDIATE: Monitor hosting provider progress                             │
│ 2. WITHIN 1 HOUR: Follow up with hosting provider if still down            │
│ 3. BY EOD: Send follow-up communication confirming system restored         │
│ 4. NEXT 24H: Review why backup payment system wasn't triggered             │
│ 5. WITHIN 1 WEEK: Implement redundant payment processor                     │
│                                                                             │
│ Owner: Aaron | Priority: FIX IMMEDIATELY                                   │
│ Escalation Contact: Hosting Provider CEO direct line                        │
│
│─────────────────────────────────────────────────────────────────────────────│

│ ALERT #2: Roof Leak - Oak Park Property                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│ Severity: 🔴 CRITICAL                                                       │
│ Type: Maintenance/Property Damage                                           │
│ Created: 2025-01-20T16:45:00Z                                               │
│ Status: IN PROGRESS (1 day 21 hours)                                        │
│                                                                             │
│ ISSUE:                                                                      │
│ Water damage detected in Unit 204 ceiling from roof leak. Leak appears to   │
│ originate from roof section installed in 2019 (6-year-old section).        │
│                                                                             │
│ IMPACT ASSESSMENT:                                                          │
│ • Property Damage: Extensive (ceiling, walls, flooring)                     │
│ • Repair Cost Estimate: $8,500-12,000                                       │
│ • Unit Out of Service: 2-3 weeks while repairs completed                   │
│ • Monthly Revenue Loss: $600 (Unit 204 rent lost)                           │
│ • Water Damage to Unit Below: Minimal but monitor                           │
│ • Insurance Claim Coverage: 85% (after $1,000 deductible)                   │
│ • Health/Safety Risk: Low (but humidity concerns)                           │
│                                                                             │
│ ROOT CAUSE:                                                                 │
│ Normal roof degradation. 2019 section showing premature wear. Evidence of  │
│ improper drainage installation contributing to water pooling.               │
│                                                                             │
│ ACTIONS TAKEN:                                                              │
│ ✓ Tenant relocated temporarily (costs covered by landlord insurance)        │
│ ✓ Emergency water extraction completed                                      │
│ ✓ Mold prevention treatment applied                                         │
│ ✓ Insurance claim filed - Claim #INS-2025-45823                            │
│ ✓ Obtained 3 contractor quotes (ranging $8,500-12,000)                      │
│ → Recommended contractor: Apex Roofing (best value + 10-yr warranty)        │
│ → Scheduled start date: 2025-01-25                                          │
│                                                                             │
│ RECOMMENDED NEXT STEPS:                                                     │
│ 1. IMMEDIATE: Approve contractor quote ($10,200 from Apex Roofing)         │
│ 2. TODAY: Notify tenant of estimated completion (3 weeks)                  │
│ 3. TOMORROW: Schedule daily progress checks                                 │
│ 4. DURING WORK: Document before/after photos for insurance                 │
│ 5. POST-REPAIR: Full roof inspection and preventive maintenance             │
│ 6. WITHIN 30 DAYS: Entire roof replacement evaluation (end-of-life?)        │
│                                                                             │
│ Owner: Property Manager | Priority: APPROVE & SCHEDULE                     │
│ Budget Impact: $10,200 capex (85% covered by insurance after deductible)  │
│
│─────────────────────────────────────────────────────────────────────────────│

│ ALERT #3: Tenant Eviction Proceeding - Elm Court Apts Unit 102             │
├──────────────────────────────────────────────────────────────────────────────┤
│ Severity: 🔴 CRITICAL                                                       │
│ Type: Tenant/Legal                                                          │
│ Created: 2025-01-15T10:30:00Z                                               │
│ Status: IN PROGRESS (7 days)                                                │
│                                                                             │
│ ISSUE:                                                                      │
│ Tenant "Marcus Johnson" (Unit 102) has failed to pay rent for 2 months     │
│ (December 2024 + January 2025). Total owed: $400 + late fees ($75).        │
│ Eviction proceedings initiated on 1/15/25.                                  │
│                                                                             │
│ IMPACT ASSESSMENT:                                                          │
│ • Monthly Revenue Loss: $200/month (Unit 102)                               │
│ • Total Amount Owed: $475 (rent + late fees)                                │
│ • Days Behind: 37 days                                                      │
│ • Eviction Timeline: 30-60 days (court dependent)                           │
│ • Estimated Legal Costs: $1,200-2,000                                       │
│ • Recovery Probability: Low (tenant has insufficient funds)                 │
│ • Unit Turnover Time: 1-2 weeks after vacate                                │
│ • Lost Revenue During Eviction: $200-400                                    │
│ • Reputational Risk: None (tenant non-responsive)                           │
│                                                                             │
│ ROOT CAUSE:                                                                 │
│ Tenant experienced job loss in December (stated reason). Did not proactively│
│ communicate or work out payment plan. Ignored payment notices/calls.        │
│                                                                             │
│ ACTIONS TAKEN:                                                              │
│ ✓ Written payment demand issued 12/15/24 (returned unopened)               │
│ ✓ Phone attempts made (voicemail left - no response)                       │
│ ✓ Eviction notice filed with local court                                   │
│ ✓ Legal attorney assigned (Morrison Legal Group)                           │
│ → Court date scheduled: 2025-02-20T09:00:00Z                                │
│ → Status: Waiting for court hearing                                         │
│                                                                             │
│ RECOMMENDED NEXT STEPS:                                                     │
│ 1. IMMEDIATE: Confirm legal proceedings on track with attorney             │
│ 2. BY 2/15: Begin pre-marketing for unit (online listings, etc.)            │
│ 3. COURT DATE: Ensure attorney has all documentation                       │
│ 4. POST-JUDGMENT: Secure unit and perform turnover preparations             │
│ 5. AFTER VACATE: Deep clean, repairs, lease new tenant                     │
│ 6. FOLLOW-UP: Small claims action for unpaid rent/damages                   │
│                                                                             │
│ Owner: Legal Team | Priority: MONITOR LEGAL PROCEEDINGS                    │
│ Financial Recovery: Low probability - estimated 20% recovery                │
│
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 🟠 HIGH PRIORITY ALERTS (Address This Week)                                │
├─────────────────────────────────────────────────────────────────────────────┤

│ ALERT #4: Maintenance Request Backlog - Main St Rentals                    │
│ Severity: 🟠 HIGH  |  Created: 2025-01-18  |  Status: ACTIVE               │
│ Issue: 7 maintenance requests pending (avg 4 days waiting). HVAC,           │
│        plumbing, door lock issues across property.                          │
│ Impact: Tenant satisfaction risk, potential retention issues                │
│ Action: Schedule maintenance coordinator call TODAY to prioritize           │
│ Timeline: All requests completed by 2025-01-25                              │
├──────────────────────────────────────────────────────────────────────────────┤

│ ALERT #5: Insurance Premium Increase - All Properties                       │
│ Severity: 🟠 HIGH  |  Created: 2025-01-21  |  Status: PENDING APPROVAL     │
│ Issue: Annual insurance renewal notice. Premiums increased 18% YoY.         │
│ Impact: Additional $2,800/year in expenses across portfolio                 │
│ Action: Review options with insurance broker, evaluate coverage             │
│ Timeline: Decision needed by 2025-02-15 (renewal deadline)                  │
├──────────────────────────────────────────────────────────────────────────────┤

│ ALERT #6: Lease Expiration Approaching - Elm Court Unit 104                │
│ Severity: 🟠 HIGH  |  Created: 2025-01-10  |  Status: PLANNING             │
│ Issue: Tenant lease expires 2025-06-30 (5 months 8 days). No renewal       │
│        discussion initiated yet.                                            │
│ Impact: Unit vacancy risk, potential $200/month revenue loss                │
│ Action: Initiate renewal discussion by 2025-02-01                           │
│ Timeline: Confirmation of renewal/vacation by 2025-03-31                    │
├──────────────────────────────────────────────────────────────────────────────┤

│ ALERT #7: Cash Reserve Below Minimum - Portfolio                            │
│ Severity: 🟠 HIGH  |  Created: 2025-01-20  |  Status: MONITORING           │
│ Issue: Combined business cash reserve dropped to $125,800 vs target $150k.  │
│ Impact: Limited cushion for emergencies, reduced opportunities              │
│ Action: Review expense budget and identify cost reduction opportunities     │
│ Timeline: Restore to target within 90 days                                  │
├──────────────────────────────────────────────────────────────────────────────┤

│ ALERT #8: Tenant Complaint - Noise/Disturbance - Main St Unit 203          │
│ Severity: 🟠 HIGH  |  Created: 2025-01-21  |  Status: INVESTIGATING        │
│ Issue: Unit 203 reporting noise from Unit 204 after 11 PM (2 complaints).   │
│ Impact: Potential tenant conflict, lease compliance issue                   │
│ Action: Property manager to mediate and document incident                   │
│ Timeline: Investigation complete by 2025-01-24                              │
│
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 🟡 MEDIUM PRIORITY ALERTS (Address in 30 Days)                             │
├─────────────────────────────────────────────────────────────────────────────┤

│ ALERT #9: Capital Reserve Below Target - Main St Rentals                   │
│ Severity: 🟡 MEDIUM  |  Created: 2025-01-15  |  Status: MONITORING          │
│ Issue: Property capital reserve at 83% of recommended level.                │
│ Impact: Limited funds for unexpected major repairs                          │
│ Action: Increase monthly funding by $250 to reach target in 6 months        │
│ Timeline: Adjustment starts February 2025                                   │
├──────────────────────────────────────────────────────────────────────────────┤

│ ALERT #10: Utilities Trending Up - Oak Park Property                       │
│ Severity: 🟡 MEDIUM  |  Created: 2025-01-12  |  Status: INVESTIGATING      │
│ Issue: Utility costs increased 11% YoY. Root cause unknown.                 │
│ Impact: $20-25/month additional expense                                     │
│ Action: HVAC audit and thermostat programming review                        │
│ Timeline: Complete by 2025-02-28                                            │
├──────────────────────────────────────────────────────────────────────────────┤

│ ALERT #11: Tenant Screening Improvement - Elm Court Apts                   │
│ Severity: 🟡 MEDIUM  |  Created: 2025-01-08  |  Status: PLANNING            │
│ Issue: 2 recent tenants with late payments. Current screening not strong.   │
│ Impact: Risk of rent defaults, collection issues                            │
│ Action: Upgrade tenant screening tool (credit + background verification)    │
│ Timeline: Implementation by 2025-03-01                                      │
│
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 🟢 LOW PRIORITY ALERTS (Informational/Minor Issues)                        │
├─────────────────────────────────────────────────────────────────────────────┤

│ ALERT #12: Rent Increase Opportunity - Main St Rentals                     │
│ Severity: 🟢 LOW  |  Created: 2025-01-10  |  Status: PLANNING               │
│ Issue: Property rent-to-value ratio 0.20% vs market average 0.8-1.1%.       │
│ Impact: Potential to increase revenue 8-10% at next lease renewal           │
│ Action: Conduct rent market analysis for Q2 2025 lease renewals             │
│ Timeline: Analysis by 2025-02-15, implementation at lease renewals          │
│ Estimated Impact: +$180-225/month additional revenue                         │
│
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 📊 ALERT STATISTICS & TRENDS                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Active Alerts by Severity:                                                  │
│ 🔴 CRITICAL:  3 alerts  (25%)  │████████░░░░░░░░░░░░░░░░░░░░░░░░          │
│ 🟠 HIGH:      5 alerts  (42%)  │██████████████░░░░░░░░░░░░░░░░░░          │
│ 🟡 MEDIUM:    3 alerts  (25%)  │████████░░░░░░░░░░░░░░░░░░░░░░░░          │
│ 🟢 LOW:       1 alert   (8%)   │███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░          │
│                                                                             │
│ Alert Breakdown by Type:                                                    │
│ Financial/Operational: 3 (25%)                                              │
│ Maintenance/Property:  3 (25%)                                              │
│ Tenant/Occupancy:      4 (33%)                                              │
│ Legal/Compliance:      1 (8%)                                               │
│ Other:                 1 (8%)                                               │
│                                                                             │
│ Alert Statistics:                                                           │
│ Total Alerts (All Time):    267                                             │
│ Resolved This Month:        18                                              │
│ Avg Resolution Time:        5.2 days                                        │
│ Alerts < 24h Old:           7 (58% of active)                               │
│ Overdue Alerts:             0 (all on schedule)                             │
│                                                                             │
│ Critical Alert History:                                                     │
│ - Last 30 days: 4 critical alerts (this is 3)                              │
│ - Last 90 days: 8 critical alerts                                           │
│ - Last year:    24 critical alerts (avg 2/month)                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 📋 ALERT ACTION SUMMARY (What You Need to Do Today)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ 🔴 IMMEDIATE (Next 2 Hours):                                               │
│ 1. Monitor payment system restoration (ETA 15 min)                          │
│ 2. Approve roof repair contractor quote ($10,200)                           │
│ 3. Check on legal proceedings status                                        │
│                                                                             │
│ 🟠 TODAY (Before EOD):                                                     │
│ 4. Call maintenance coordinator (maintenance backlog)                       │
│ 5. Review insurance premium options with broker                             │
│ 6. Contact Unit 203 tenant about noise investigation                        │
│                                                                             │
│ 🟡 THIS WEEK (By Friday):                                                  │
│ 7. Property manager mediation report on noise complaint                     │
│ 8. Cash reserve expense reduction plan                                      │
│ 9. Lease renewal discussion with Unit 104 tenant                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Generated: 2025-01-22T14:35:00Z
Active Alerts: 12 | Last Review: 2025-01-22 | Next Review: 2025-01-24
Alert System Status: ✅ OPERATIONAL | Escalation Status: 2 PENDING
```

## Export Formats

### JSON Export

```json
{
  "generated": "2025-01-22T14:35:00Z",
  "summary": {
    "total_alerts": 12,
    "critical": 3,
    "high": 5,
    "medium": 3,
    "low": 1
  },
  "alerts": [
    {
      "id": "ALERT_001",
      "severity": "CRITICAL",
      "type": "FINANCIAL_OPERATIONAL",
      "title": "Payment System Down",
      "property": "Main St Rentals",
      "created": "2025-01-22T08:15:00Z",
      "status": "ACTIVE",
      "description": "Online payment portal is down...",
      "impact": {
        "daily_loss": 80,
        "affected_units": 12,
        "monthly_potential_loss": 2400
      },
      "actions_taken": [...],
      "recommended_actions": [...],
      "owner": "Aaron",
      "priority": "FIX_IMMEDIATELY"
    }
  ],
  "statistics": {
    "avg_resolution_time_days": 5.2,
    "alerts_resolved_this_month": 18,
    "overdue_alerts": 0
  }
}
```

## Success Metrics

- ✓ All active alerts displayed
- ✓ Severity levels correctly assessed
- ✓ Impact estimates provided
- ✓ Action items clearly listed
- ✓ Owner assignments defined
- ✓ Timeline expectations set
- ✓ Resolution tracking functional
- ✓ Escalation paths clear

## Alert Categories

**Financial & Operational**

- Payment system issues
- Cash flow problems
- Expense anomalies
- Income disruptions

**Maintenance & Property**

- Roof/structure damage
- HVAC/utilities
- Plumbing issues
- Preventive maintenance

**Tenant & Occupancy**

- Lease expirations
- Complaints/disputes
- Payment defaults
- Screening failures

**Legal & Compliance**

- Eviction proceedings
- Insurance issues
- Code violations
- License renewals

## Alert Configuration

Configure alert thresholds:

- **Critical**: Property damage, payment system down, eviction
- **High**: Lease expirations, insurance changes, tenant complaints
- **Medium**: Capital reserve levels, expense trends, screening issues
- **Low**: Optimization opportunities, informational items

## Related Commands

- `/dashboard:overview` - Full portfolio status
- `/dashboard:property <id>` - Property-specific details
- `/dashboard:kpi` - Performance tracking
- `/context:switch` - Business context switching

---

*Never miss a critical issue again. Intelligent alerting keeps you informed without overwhelming you with noise.*
