---
description: "Manage client relationships with pipeline tracking, communication logs, contracts, and value scoring"
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
argument-hint: "[add|list|manage|communicate|score] [--status leads|proposals|active|completed] [--sort value]"
---

# /software-business:clients - Client Relationship Management

Track clients through complete lifecycle: lead → proposal → active → completed, with communication history, contracts, and client value scoring.

## Quick Start

**Add a new lead:**

```bash
/software-business:clients add
```

**List all clients:**

```bash
/software-business:clients list
```

**Manage a specific client:**

```bash
/software-business:clients manage
```

**Log communication:**

```bash
/software-business:clients communicate
```

**Score client value:**

```bash
/software-business:clients score
```

---

## System Overview

This command implements **client-centric CRM** where every client is:

1. Tracked through the complete sales pipeline
2. Evaluated for lifetime value (revenue potential)
3. Assessed for alignment with business goals
4. Measured for satisfaction and relationship quality

**Key Principle**: Not all clients are equal. Some clients are:

- Highly profitable (great margins)
- Low maintenance (good communication)
- Aligned with your goals (build product, get testimonials)
- Sources of referrals (network effect)

The system helps you identify high-value clients and nurture those relationships.

---

## Mode 1: ADD - Create New Client Record

Add a prospect or new client to your CRM.

### Client Information

**Contact Details**:

- Name (person or company)
- Email
- Phone
- Company (if person)
- Title/Role
- Location

**Initial Information**:

- How did you meet them? (referral, inbound, outbound, conference)
- What are they looking for?
- Initial budget estimate (if provided)
- Timeline (when do they need it?)
- Status: LEAD, QUALIFIED, PROPOSAL SENT, NEGOTIATING, ACTIVE, COMPLETED

**Relationship Info**:

- Who referred them? (if applicable)
- Previous relationship? (first-time, returning)
- Decision maker identified? (yes/no, who)
- Budget approval status?

### Client Template

```
CLIENT: TechCorp Solutions (Company)

┌─ CONTACT INFORMATION
├── Primary contact: Sarah Johnson
├── Title: VP Product
├── Email: sarah@techcorp.com
├── Phone: (555) 123-4567
├── Company: TechCorp Solutions
├── Location: San Francisco, CA
└── Secondary contacts: (list other stakeholders)

┌─ INITIAL INFORMATION
├── Source: Referral (from John Smith)
├── What they need: E-commerce platform redesign
├── Budget estimate: $30-50K
├── Timeline: Q1 2025
├── Status: QUALIFIED
└── Notes: High-quality referral, already has budget approved

┌─ PROJECT HISTORY
├── Previous projects: None (new client)
├── Relationship length: First contact Jan 2025
├── Total revenue: $0 (yet)
└── Status: NEW OPPORTUNITY

┌─ DECISION MAKERS & APPROVAL
├── VP Product: Sarah Johnson (project sponsor)
├── CTO: Mike Chen (technical approval)
├── Finance: Lisa Wong (budget approval)
└── Status: All 3 stakeholders identified ✅
```

### Lead Qualification Checklist

Before moving to PROPOSAL stage, verify:

- [ ] Budget: Has client confirmed budget? (or credible estimate)
- [ ] Timeline: Do they have a realistic timeline?
- [ ] Decision maker: Have you identified who makes final decision?
- [ ] Fit: Does this project align with your business goals?
- [ ] Profitability: Will it be profitable (40%+ margin)?
- [ ] Resources: Do you have bandwidth?

If all ✅, proceed to PROPOSAL stage.

---

## Mode 2: LIST - View Client Pipeline

See all clients organized by stage in pipeline.

### Client Pipeline Dashboard

```
CLIENT PIPELINE
═════════════════════════════════════════════════════════════

STAGE 1: LEADS (3 prospects)
├── Prospect 1: Small SaaS (Budget: ~$5K, Timeline: 3 months)
│   ├── Status: Initial conversation completed
│   ├── Next step: Send proposal by Jan 31
│   ├── Probability: 40% (early stage)
│   └── Estimated value: $5K
│
├── Prospect 2: Marketing Agency (Budget: ~$15K, Timeline: 6 weeks)
│   ├── Status: Awaiting decision
│   ├── Next step: Follow up Jan 28
│   ├── Probability: 60% (good signals)
│   └── Estimated value: $15K
│
└── Prospect 3: E-commerce Brand (Budget: TBD, Timeline: 2 months)
    ├── Status: Discovery call scheduled Jan 30
    ├── Next step: Learn more about requirements
    ├── Probability: 25% (early, uncertain fit)
    └── Estimated value: $10-20K

STAGE 2: PROPOSALS SENT (2)
├── TechCorp Solutions (E-commerce Redesign)
│   ├── Proposal sent: Jan 15
│   ├── Proposal value: $35,000
│   ├── Expected decision: Feb 5
│   ├── Probability: 85% (warm, referenced decision maker)
│   └── Status: Awaiting client feedback
│
└── SmallBiz Inc. (Website Redesign)
    ├── Proposal sent: Jan 20
    ├── Proposal value: $12,000
    ├── Expected decision: Feb 10
    ├── Probability: 70% (good fit, but comparing other vendors)
    └── Status: Negotiations on scope

STAGE 3: ACTIVE PROJECTS (2)
├── B2B Client Inc. (API Integration)
│   ├── Project start: Jan 8
│   ├── Contract value: $12,000
│   ├── Completion date: Feb 28
│   ├── Status: In progress (60% complete)
│   ├── Client satisfaction: 4.8/5
│   └── Risk: None (on track)
│
└── StartupXYZ (Mobile App Dev)
    ├── Project start: Feb 1
    ├── Contract value: $60,000
    ├── Completion date: May 31
    ├── Status: Just started (5% complete)
    ├── Client satisfaction: 5/5
    └── Risk: Scope creep potential (has requested 2 changes already)

STAGE 4: COMPLETED (8 clients)
├── TechStartup (Landing Page) - Completed 2 months ago
│   ├── Revenue: $5,000
│   ├── Satisfaction: 5/5 ⭐
│   ├── Likelihood of repeat business: 70% (interested in Phase 2)
│   └── Referral opportunity: HIGH (said they'd recommend)
│
├── Consulting Client (Quarterly retainer) - Ongoing
│   ├── Retainer: $2K/month (recurring)
│   ├── Satisfaction: 4.5/5
│   └── Renewal likelihood: 90% (contract renewed 3x)
│
└── [6 more completed clients...]

PIPELINE STATISTICS
├── Total leads in pipeline: 3 (potential: $30K)
├── Proposals pending: 2 (expected: $47K)
├── Active projects: 2 (current: $72K)
├── Completed clients: 8 (total revenue: $187.5K)
├── Winning percentage: 75% (6 of 8 proposals converted)
├── Weighted forecast: $127K (next 90 days)
└── Status: ON TRACK for $250K+ annual revenue
```

### Client Filters & Views

```bash
# View only high-value clients (>$10K projects)
/software-business:clients list --filter high-value

# View only active projects
/software-business:clients list --status active

# View clients by satisfaction (4.5+ stars)
/software-business:clients list --sort satisfaction

# View clients likely to refer (high satisfaction + explicit interest)
/software-business:clients list --filter referral-potential

# View clients for follow-up this week
/software-business:clients list --filter follow-up-this-week
```

---

## Mode 3: MANAGE - Client Details & Actions

View complete client record and manage relationship.

### Client Detail View

```
CLIENT: TechCorp Solutions
═════════════════════════════════════════════════════════════

CURRENT PROJECT
├── E-commerce Platform Redesign
├── Status: IN PROGRESS (45% complete)
├── Revenue: $35,000
├── Timeline: Jan 15 - Mar 31 (on track)
├── Last update: Jan 25 (3 days ago)
└── Next milestone: Frontend complete by Mar 15

COMMUNICATION HISTORY
├── Last contact: Jan 25 (email: Project update)
├── Last meeting: Jan 23 (30-min standup - noted design delays)
├── Next scheduled: Jan 30 (Weekly standup)
└── Communication frequency: 2x/week (healthy)

CONTACT INFORMATION
├── Primary: Sarah Johnson (sarah@techcorp.com)
├── CTO: Mike Chen (mike@techcorp.com)
├── Finance: Lisa Wong (lisa@techcorp.com)
└── Newsletter: Yes (opted in Jan 15)

RELATIONSHIP METRICS
├── Client satisfaction: 9/10 ⭐⭐⭐ (Very satisfied)
├── Communication quality: 4.5/5 (Responsive, clear)
├── Profitability: 58% margin ($20,375 profit)
├── Responsiveness: 4/5 (Usually responds within 24h)
├── Scope adherence: 4/5 (Minor change requests)
└── Overall relationship: EXCELLENT

REPEAT BUSINESS POTENTIAL
├── Phase 2 redesign: $25,000 (mentioned interest)
├── Maintenance contract: $1K/month (potential)
├── Referrals: HIGH (said would recommend)
└── Next opportunity: Follow up on Phase 2 after project close

NEXT ACTIONS
├── [ ] Weekly standup on Jan 30
├── [ ] Review design assets (Mike requested review)
├── [ ] Send invoice for milestone 2 (due this week)
├── [ ] Discuss Phase 2 scope (after Project complete)
└── [ ] Request testimonial/case study (upon completion)

NOTES
├── Jan 25: Design assets delay resolved
├── Jan 20: Change request #2 (small - absorbed in budget)
├── Jan 15: Project kicked off, team great to work with
└── Jan 8: Proposal accepted, contract signed (3 hours early)
```

### Client Actions

**Typical actions to take:**

1. **Send proposal**
   - Review requirements
   - Prepare cost estimate
   - Create formal proposal document
   - Send via email with cover letter

2. **Schedule meeting**
   - Discovery call (initial)
   - Project kickoff (before starting)
   - Weekly standup (during project)
   - Project review (after completion)

3. **Send invoice**
   - Milestone-based (50% upfront, 50% at completion)
   - Post-completion invoicing
   - Retainer invoicing (monthly)
   - Track payment status

4. **Log communication**
   - Every email, call, or message
   - Timestamps and summaries
   - Decisions made
   - Action items

5. **Request testimonial**
   - After project completion
   - Ask specific questions (quality, communication, ROI)
   - Use for marketing/case studies

6. **Follow up on repeat business**
   - Phase 2 projects
   - Maintenance contracts
   - Retainer arrangements

---

## Mode 4: COMMUNICATE - Log Interactions

Track all communication with clients.

### Communication Log Template

```
CLIENT: TechCorp Solutions
DATE: Jan 25, 2025

COMMUNICATION LOG ENTRY
├── Type: Email (project update)
├── Duration: Async (written email)
├── Participants: Sarah Johnson, Mike Chen
├── Topic: Project progress update, design delays
│
├── SUMMARY:
│   ├── Updated on project progress (45% complete)
│   ├── Explained design asset delay (1 day)
│   ├── Confirmed still on track for completion Mar 31
│   └── Addressed Mike's technical questions on API design
│
├── DECISIONS MADE:
│   ├── Frontend timeline confirmed (Mar 15)
│   └── Design review scheduled for Jan 28
│
├── ACTION ITEMS:
│   ├── [ ] TechCorp: Review design mockups by Jan 28
│   └── [ ] Me: Send detailed API documentation by Jan 27
│
└── NEXT FOLLOW-UP: Jan 30 (Weekly standup)

═════════════════════════════════════════════════════════════

RECENT COMMUNICATION TIMELINE
├── Jan 25 (2 days ago): Email - Project update
├── Jan 23 (4 days ago): Call - Weekly standup
├── Jan 20 (7 days ago): Email - Change request response
├── Jan 15 (10 days ago): Email - Project kickoff
└── Jan 8 (17 days ago): Call - Proposal acceptance & contract signing

COMMUNICATION PATTERNS
├── Frequency: 2x/week (healthy)
├── Response time: 24 hours (good)
├── Preferred method: Email (written documentation)
├── Best contact: Sarah Johnson
├── Backup contact: Mike Chen
└── Status: ENGAGED ✅
```

### Communication Types to Log

- **Email**: Project updates, decisions, deliverables
- **Calls**: Meetings, standups, problem-solving
- **Messages**: Slack, Discord, quick questions
- **Meetings**: In-person or video calls
- **Feedback**: Client feedback on deliverables
- **Invoices**: Payment reminders, invoice sent

---

## Mode 5: SCORE - Client Value Assessment

Evaluate each client on multiple dimensions.

### Client Value Scorecard

```
CLIENT: TechCorp Solutions
═════════════════════════════════════════════════════════════

FINANCIAL VALUE (40% weight)
├── Contract size: $35,000 (large project) → 9/10
├── Profit margin: 58% (very profitable) → 9/10
├── Repeat business potential: Phase 2 ($25K) → 9/10
├── Referral potential: Explicit interest in recommending → 9/10
├── Long-term value: 4+ year relationship potential → 8/10
│
└── FINANCIAL SCORE: 8.8/10 (EXCELLENT) ✅

RELATIONSHIP QUALITY (30% weight)
├── Communication: Responsive, clear → 4.5/5
├── Professionalism: Business-like, respectful → 5/5
├── Decision clarity: Quick decisions, clear approvals → 4.5/5
├── Scope adherence: Minimal change requests → 4/5
├── Payment reliability: Pays on time, no disputes → 5/5
│
└── RELATIONSHIP SCORE: 4.6/5 (EXCELLENT) ✅

STRATEGIC ALIGNMENT (20% weight)
├── Goal support: Builds software business → 9/10
├── Testimonial value: High-profile, willing to share → 9/10
├── Product visibility: Industry-relevant case study → 8/10
├── Skill development: Interesting technical challenges → 8/10
├── Network value: Well-connected in industry → 8/10
│
└── STRATEGIC SCORE: 8.4/10 (EXCELLENT) ✅

EFFORT/FRICTION (10% weight - lower is better)
├── Project complexity: Moderate (not too complex) → 7/10
├── Scope creep: Minimal (clear requirements) → 8/10
├── Decision making: Fast decisions → 8/10
├── Responsiveness: Quick feedback loops → 9/10
├── Cultural fit: Easy to work with → 9/10
│
└── FRICTION SCORE: 8.2/10 (LOW FRICTION) ✅

OVERALL CLIENT VALUE SCORE: 8.6/10 ⭐⭐⭐ (A+ CLIENT)

INTERPRETATION
├── Tier: TOP-TIER (A+ client - highly valuable)
├── Priority: HIGH (prioritize this relationship)
├── Recommendation: Maintain excellent service, actively pursue Phase 2
└── Strategy: This is model client - target more like them

COMPARABLE CLIENTS
├── Average value: 6.2/10
├── This client: 8.6/10 (+38% above average)
├── Best client: 9.1/10 (ConsultingCorp)
└── Opportunity: 60% of clients are 5-6/10 (underperforming)
```

### Client Tier System

**A+ CLIENTS** (Score 8.5+)

- Highly profitable (50%+ margin)
- Excellent communication
- Aligned with your goals
- Source of referrals
- Repeat business potential
- Strategy: Nurture aggressively, prioritize their work

**A CLIENTS** (Score 7.5-8.5)

- Profitable (40-50% margin)
- Good communication
- Supportive of your goals
- Some referral potential
- Strategy: Maintain good service, seek repeat business

**B CLIENTS** (Score 6-7.5)

- Adequate profitability (30-40% margin)
- Acceptable communication
- Neutral on goals
- Strategy: Standard service level, look for efficiency gains

**C CLIENTS** (Score 4.5-6)

- Lower profitability (<30% margin)
- Challenging communication
- May conflict with goals
- Strategy: Increase rates, set stricter boundaries, consider dropping

**D CLIENTS** (Score <4.5)

- Unprofitable or very difficult
- Poor communication
- Misaligned with goals
- Strategy: Plan to drop, redirect to other vendors, set end date

### Portfolio Distribution Goal

```
CURRENT CLIENT PORTFOLIO
├── A+ clients (8.5+): 2 (25% of portfolio)
├── A clients (7.5-8.5): 4 (50% of portfolio)
├── B clients (6-7.5): 2 (25% of portfolio)
├── C clients (4.5-6): 1 (12.5% of portfolio) ⚠️
└── D clients (<4.5): 0 ✅

GOAL DISTRIBUTION (Year-end)
├── A+ clients: 4 (50% of portfolio) ← Focus here
├── A clients: 3 (37.5% of portfolio)
├── B clients: 1 (12.5% of portfolio)
├── C clients: 0 ← Drop underperformers
└── D clients: 0

ACTION
├── Upgrade 2 B clients to A (improve service, increase rates)
├── Convert 2 A clients to A+ (nurture, seek Phase 2 projects)
├── Replace 1 C client (find 2-3 new A+ candidates)
└── Timeline: Complete by Q3 2025
```

---

## Data Storage

Client data is saved in:

**JSON File** (CLI):

```
.claude/data/clients.json
├── Client information (contact, company, history)
├── Pipeline status (stage, probability, value)
├── Communication logs (calls, emails, meetings)
├── Contracts and payment status
├── Satisfaction and value scores
└── Repeat business opportunities
```

**PostgreSQL** (Analytics):

```
clients table
├── client_id, name, company, email, phone
├── status (lead, qualified, active, completed)
├── lifetime_value, satisfaction_score
├── alignment_score
└── created_at, updated_at

communication_logs table
├── log_id, client_id, date, type (email/call/meeting)
├── summary, action_items, next_followup
└── created_at

projects table (linked to clients)
├── project_id, client_id
├── revenue, profit, satisfaction
└── repeat_business_potential
```

---

## Integration with Life Goals

Each client relationship should serve business and life goals:

```
BUSINESS GOAL: Build $200K/year software business
├── Client TechCorp: $35,000 project + $25,000 Phase 2 potential
├── Client SmallBiz: $12,000 project + $5,000 retainer
├── Client StartupXYZ: $60,000 project + referral network
└── Total from A+ clients: $137,000+ (68% of annual goal)

LIFE GOAL: Financial Independence
├── A+ clients (8.6+ score): High profitability, less drama
├── B/C clients (4-6 score): Low margin, time-consuming
└── Strategy: Replace C clients with A+ to increase profit while reducing hours
```

---

## Success Criteria

**After adding first client:**

- ✅ Contact information complete
- ✅ Lead qualified (or disqualified)
- ✅ Next action identified

**After 10 clients:**

- ✅ Pipeline established (leads, proposals, active, completed)
- ✅ Winning percentage 70%+ on proposals
- ✅ Communication history logged for all

**After completing first project with client:**

- ✅ Client satisfaction 4+/5
- ✅ Repeat business opportunity identified
- ✅ Testimonial/referral requested

**System Health**:

- ✅ 50%+ of clients are A/A+ tier
- ✅ Communication logged consistently
- ✅ Average client value 6.5+/10
- ✅ Pipeline weighted forecast sufficient for annual goals

---

## Tips for Success

**Building A+ Client Base**:

1. Be selective (score >7/10 before accepting)
2. Deliver exceptional service (earn 4.5+/5 satisfaction)
3. Solve their biggest problems (build trust)
4. Ask for testimonials and referrals
5. Pursue Phase 2 projects (deepen relationship)

**Pipeline Health**:

1. Maintain 3:1 proposal ratio (3 proposals for every 1 signed)
2. Keep proposals pending time <30 days
3. Follow up on "no" decisions (learn why, stay in contact)
4. Nurture leads actively (don't let opportunities die)

**Communication Excellence**:

1. Respond within 24 hours (set expectations)
2. Weekly standups during projects (prevent surprises)
3. Document everything (CRM is source of truth)
4. Over-communicate (better than surprises)

---

## ROI & Impact

**Time Investment**: 30 min/week (CRM management + communication logs)
**Annual ROI**: Improved client satisfaction → more referrals, repeat business, higher margins

**Key Benefits**:

- Predictable pipeline (know what's coming)
- Better relationships (better communication)
- Higher retention (satisfied clients = repeats)
- More referrals (happy clients recommend you)
- Increased profit (focus on A+ clients)

---

**Created with the goal-centric life management system**
**Build your software business through strong client relationships**
