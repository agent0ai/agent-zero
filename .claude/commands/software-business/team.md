---
description: "Manage team capacity, task delegation, performance tracking, and team alignment with business goals"
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
argument-hint: "[capacity|delegate|track|performance|goals] [--team-member <name>] [--sprint]"
---

# /software-business:team - Team Coordination & Capacity Management

Delegate tasks, track team member capacity, manage sprints, and measure team alignment with business goals.

## Quick Start

**Check team capacity:**

```bash
/software-business:team capacity
```

**Delegate a task:**

```bash
/software-business:team delegate
```

**Track task progress:**

```bash
/software-business:team track
```

**Review team performance:**

```bash
/software-business:team performance
```

**Align team with goals:**

```bash
/software-business:team goals
```

---

## System Overview

This command implements **team-centric task management** where:

1. Every task has a DRI (Directly Responsible Individual)
2. Capacity is tracked and managed (prevent burnout)
3. Performance is measured (quality, velocity, delivery)
4. Team work is aligned with business goals

**Key Principle**: A team is only as good as their ability to execute while maintaining quality and avoiding burnout. The goal is to maximize capacity without sacrificing happiness or output quality.

---

## Mode 1: CAPACITY - Track Team Member Availability

Monitor capacity, manage workload, and prevent overcommitment.

### Team Member Profile

```
TEAM MEMBER: John Developer
═════════════════════════════════════════════════════════════

BASIC INFO
├── Role: Senior Developer
├── Full-time / Part-time: Full-time (40 hrs/week)
├── Hire date: Jan 2024
├── Cost: $6,000/month ($75/hour)
└── Location: Remote (same timezone)

CAPACITY ALLOCATION THIS SPRINT
├── Total hours available: 40 hours/week
├── Project 1 (E-commerce Redesign): 20 hours (50%)
├── Project 2 (API Redesign): 15 hours (37.5%)
├── Admin/Meetings: 5 hours (12.5%)
└── Total allocated: 40 hours (100% - fully allocated) ⚠️

CAPACITY ANALYSIS
├── Current utilization: 100% (at capacity)
├── Available for new work: 0 hours
├── Overallocation risk: NONE (exactly at limit)
├── Burnout risk: MODERATE (no buffer for emergencies)
└── Recommendation: Monitor closely, add buffer if possible

PROJECT ASSIGNMENTS
├── E-commerce Redesign (TechCorp)
│   ├── Assigned work: 20 hrs/week
│   ├── Actual hours (this week): 18 hrs
│   ├── Status: On track
│   ├── Estimated completion: Mar 15
│   └── Performance: Strong (high quality)
│
└── API Redesign (Internal Project)
    ├── Assigned work: 15 hrs/week
    ├── Actual hours (this week): 16 hrs
    ├── Status: Ahead of schedule (extra motivation)
    ├── Estimated completion: May 1
    └── Performance: Excellent

PERFORMANCE METRICS
├── Velocity: 16.5 hours/week average (vs. 35 assigned)
├── Quality: 9/10 (minimal bugs, clean code)
├── Reliability: 10/10 (always meets deadlines)
├── Communication: 9/10 (responsive to questions)
├── Overall rating: 9.3/10 ⭐⭐⭐
└── Recommendation: KEEP/PROMOTE (excellent performer)

CAREER DEVELOPMENT
├── Strengths: Frontend development, clean architecture, mentoring
├── Growth areas: Backend performance optimization
├── Training needs: Advanced SQL optimization
├── Growth plan: Senior → Lead Developer (3-6 months)
└── Retention risk: LOW (engaged, growing)
```

### Team Capacity Dashboard

```
TEAM CAPACITY OVERVIEW
═════════════════════════════════════════════════════════════

TEAM MEMBERS (3 total)
├── John Developer (Senior Dev)
│   ├── Capacity: 40 hrs/week
│   ├── Allocated: 40 hrs (100%)
│   ├── Status: At capacity ⚠️
│   └── Utilization: Healthy
│
├── Maria Designer (Senior Designer)
│   ├── Capacity: 40 hrs/week
│   ├── Allocated: 30 hrs (75%)
│   ├── Status: Under capacity ✅
│   ├── Available: 10 hrs/week
│   └── Utilization: Healthy
│
└── Alex Contractor (Junior Dev, Part-time)
    ├── Capacity: 20 hrs/week
    ├── Allocated: 15 hrs (75%)
    ├── Status: Under capacity ✅
    ├── Available: 5 hrs/week
    └── Utilization: Healthy

TOTAL TEAM CAPACITY
├── Available: 100 hours/week
├── Allocated: 85 hours/week
├── Remaining: 15 hours/week
├── Utilization: 85% (healthy - 15% buffer)
└── Status: HEALTHY ✅

CAPACITY ALLOCATION BY PROJECT
├── E-commerce Redesign (TechCorp): 20 hrs/week
│   ├── Team members: John (20 hrs)
│   └── Status: On track
│
├── API Redesign (Internal): 15 hrs/week
│   ├── Team members: John (15 hrs)
│   └── Status: Ahead of schedule
│
├── Mobile App Dev (StartupXYZ): 40 hrs/week
│   ├── Team members: Maria (20 hrs), Alex (20 hrs)
│   └── Status: Starting next sprint
│
└── Admin/Overhead: 10 hrs/week
    ├── Meetings, planning, code review
    └── Healthy allocation

FORECASTED BOTTLENECKS
├── Q1: John at 100% capacity (monitor closely)
├── Q2: All developers at ~80% capacity (good buffer)
├── Q3: New project starts (will need to hire or reduce scope)
└── Action: Start recruiting for Q3 expansion (2+ month lead time)
```

### Capacity Rules & Best Practices

**Golden Rules**:

- Never allocate someone to 100% (need 15-20% buffer for:
  - Code review, mentoring, learning
  - Emergency firefighting
  - Unexpected delays
  - Well-being & burnout prevention

- Track actual hours vs. estimated (improves future estimates)
- Respect time zone boundaries (no 2am commits)
- Protect focused work time (no meeting-heavy days)

**Escalation Triggers**:

- Team member at 100%+ allocation → Immediate action
- Person working >50 hrs/week consistently → Talk to them
- Velocity dropping >15% → Check for burnout, blockers
- Quality issues appearing → Likely overloaded

---

## Mode 2: DELEGATE - Assign Work

Create tasks, delegate to team members, track progress.

### Task Template

```
TASK: Implement user authentication for E-commerce Platform
═════════════════════════════════════════════════════════════

BASIC INFO
├── Task ID: TECH-542
├── Project: E-commerce Platform Redesign (TechCorp)
├── Description: Implement OAuth 2.0 + JWT-based authentication
├── Type: Development (backend)
└── Priority: HIGH (blocking frontend work)

ASSIGNMENT
├── Assigned to: John Developer
├── DRI (Directly Responsible Individual): John ✓
├── Backup (if John unavailable): (none assigned - risk)
├── Assigned date: Jan 22, 2025
└── Assigned by: You

SCOPE & REQUIREMENTS
├── Requirements:
│   ├── OAuth 2.0 with Google & GitHub providers
│   ├── JWT token generation & refresh logic
│   ├── Session management (logout, expiration)
│   ├── Rate limiting on login attempts
│   └── Database schema updates (users table)
│
├── Acceptance Criteria:
│   ├── Login with Google/GitHub works end-to-end
│   ├── JWT tokens valid and refreshable
│   ├── Rate limiting blocks after 5 failed attempts
│   ├── All tests passing (100% coverage)
│   └── Code review approved
│
└── Non-requirements:
    ├── 2FA (out of scope for v1)
    └── Social profile data sync (future version)

TIMELINE & ESTIMATES
├── Estimated effort: 12 hours
├── Target completion date: Jan 29, 2025
├── Sprint: Week 1-2 (Jan 22 - Feb 5)
├── Blocker dependencies: None (can start immediately)
└── Blocking work: Frontend auth integration (waits on this)

RESOURCES PROVIDED
├── Reference materials:
│   ├── OAuth 2.0 best practices guide
│   └── JWT implementation example
│
├── Access:
│   ├── Google OAuth API credentials (configured)
│   └── GitHub OAuth app (configured)
│
└── Support:
    ├── You available for questions
    └── Slack #auth-implementation channel

TRACKING
├── Status: IN PROGRESS
├── Actual hours (so far): 4 hours
├── Estimated remaining: 8 hours
├── Completion forecast: Jan 27 (2 days early) ✓
├── Last updated: Jan 25
└── Risk level: LOW ✅
```

### Delegation Best Practices

**Before delegating**:

1. Task is clear and scoped (not vague)
2. Person has capacity (not overloaded)
3. Person has skills (or clear growth opportunity)
4. Resources are provided (no blockers)
5. Success criteria are defined (how they know they're done)

**When delegating**:

1. Have 1-on-1 conversation (not just Slack)
2. Confirm understanding (ask them to repeat back)
3. Set clear timeline (due date is important)
4. Define DRI (who's responsible if it slips?)
5. Clarify communication (how often you'll sync)

**After delegating**:

1. Check in regularly (weekly for multi-week tasks)
2. Remove blockers (don't let them get stuck)
3. Provide feedback (positive & corrective)
4. Update status tracking (actual vs. estimated)

---

## Mode 3: TRACK - Monitor Progress

Track task status, sprint velocity, and team performance.

### Sprint Planning

```
SPRINT 2 PLANNING (Jan 22 - Feb 5)
═════════════════════════════════════════════════════════════

SPRINT GOALS
├── Complete E-commerce Platform frontend (80% done → 100%)
├── Implement user authentication backend (0% → 100%)
├── Deploy to staging environment
└── Get client sign-off on Phase 1

TASKS THIS SPRINT (8 total)
├── User authentication backend (John) - 12 hrs
│   ├── Status: In progress (4/12 hrs complete)
│   ├── Deadline: Jan 29
│   └── Risk: LOW
│
├── Frontend authentication integration (Maria) - 16 hrs
│   ├── Status: Ready to start (waiting on backend)
│   ├── Deadline: Feb 1
│   └── Risk: LOW (John on track)
│
├── Payment integration (Alex) - 10 hrs
│   ├── Status: Planning (needs Stripe setup)
│   ├── Deadline: Feb 3
│   └── Risk: MEDIUM (waiting on Stripe account approval)
│
├── Testing & QA (John + Maria) - 8 hrs
│   ├── Status: Not started
│   ├── Deadline: Feb 4
│   └── Risk: LOW
│
├── Client training (You) - 4 hrs
│   ├── Status: Not started
│   ├── Deadline: Feb 5
│   └── Risk: LOW
│
└── [3 smaller tasks...]

SPRINT CAPACITY ANALYSIS
├── Team available: 85 hours total
├── Sprint allocation: 70 hours
├── Buffer: 15 hours (17.6% - healthy) ✅
├── Overallocation: None
└── Status: BALANCED ✅

SPRINT FORECAST
├── Velocity (based on last 3 sprints): 68 hours
├── This sprint planned: 70 hours
├── Prediction: On track to complete all sprint goals ✓
├── Confidence: HIGH (85%)
└── Contingency: 15 hours available if needed
```

### Sprint Standup

```
SPRINT 2 STANDUP - WEDNESDAY JAN 24
═════════════════════════════════════════════════════════════

JOHN DEVELOPER
├── What I did yesterday:
│   ├── Completed OAuth 2.0 provider setup (4 hrs)
│   └── Implemented JWT generation logic (in progress)
│
├── What I'm doing today:
│   ├── Finish JWT implementation
│   ├── Add token refresh logic
│   └── Write unit tests for auth module
│
├── Blockers: None
├── Timeline: On track for Jan 29 delivery
└── Confidence: HIGH

MARIA DESIGNER
├── What I did yesterday:
│   ├── Completed design mockups (done)
│   └── Prepared handoff for frontend developers
│
├── What I'm doing today:
│   ├── Waiting on backend auth implementation
│   ├── Can start with UI polish work (non-blocking)
│   └── Prepare testing checklist
│
├── Blockers: Blocked on John's auth work (expected, on track)
├── Timeline: Ready to start frontend once John reaches checkpoint
└── Confidence: HIGH

ALEX CONTRACTOR
├── What I did yesterday:
│   ├── Set up Stripe test account
│   └── Reviewed payment API documentation
│
├── What I'm doing today:
│   ├── Implement Stripe integration
│   ├── Add webhook handling
│   └── Test sandbox transactions
│
├── Blockers: None (good to go)
├── Timeline: On track for Feb 3 delivery
└── Confidence: MEDIUM (first time with Stripe, but confident)

SPRINT PROGRESS
├── Start of sprint: 0/70 hours complete
├── Current: 4/70 hours (5.7%)
├── Expected velocity: ~20-23 hours/week
├── Forecast: On track to complete sprint ✓
├── Overall sprint health: GOOD ✅
```

### Task Status Tracking

```
TASK STATUS BOARD
═════════════════════════════════════════════════════════════

TO DO (2 tasks)
├── [ ] Frontend auth integration (Maria) - Blocked waiting on John
└── [ ] Payment integration (Alex) - Ready to start

IN PROGRESS (2 tasks)
├── [████░░░░] User auth backend (John) - 4/12 hrs (33% complete)
│   ├── Deadline: Jan 29 (5 days)
│   ├── Forecast: Complete Jan 27 (2 days early) ✓
│   └── Risk: LOW
│
└── [██░░░░░░] Testing prep (Maria) - 1/8 hrs (12% complete)
    ├── Deadline: Feb 4 (11 days)
    └── Risk: LOW

READY TO REVIEW (0 tasks)

DONE (2 tasks)
├── [✓] Design mockups (Maria) - Completed Jan 20
└── [✓] Stripe setup (Alex) - Completed Jan 23

SPRINT SUMMARY
├── Completed: 2/8 tasks (25%)
├── In progress: 2/8 tasks (25%)
├── Not started: 4/8 tasks (50%)
├── At-risk tasks: 0
├── Blocked tasks: 1 (Maria, waiting on John - expected)
└── Overall health: ON TRACK ✅
```

---

## Mode 4: PERFORMANCE - Team Member Metrics

Review performance, provide feedback, plan growth.

### Performance Review

```
PERFORMANCE REVIEW: John Developer
REVIEW PERIOD: Q1 2025 (Jan - Mar)
═════════════════════════════════════════════════════════════

PERFORMANCE METRICS
├── Technical Quality: 9/10
│   ├── Code cleanliness: 9/10 (well-structured, good patterns)
│   ├── Test coverage: 10/10 (comprehensive unit tests)
│   ├── Bug rate: 1% (excellent, most found in code review)
│   └── Performance optimization: 8/10 (good, sometimes needs guidance)
│
├── Delivery & Reliability: 9/10
│   ├── On-time delivery: 100% (never missed deadline)
│   ├── Estimate accuracy: 85% (generally accurate)
│   ├── Velocity: 35 hrs/week (consistent, predictable)
│   └── Emergency response: 10/10 (always helps with crises)
│
├── Communication: 9/10
│   ├── Status updates: 10/10 (weekly updates without reminder)
│   ├── Code review responsiveness: 9/10 (quick feedback)
│   ├── Receptiveness to feedback: 9/10 (takes direction well)
│   └── Proactivity: 8/10 (suggests improvements, sometimes too quiet)
│
├── Leadership & Mentoring: 7/10
│   ├── Mentoring others: 7/10 (helps junior devs when asked)
│   ├── Taking initiative: 6/10 (waits for direction)
│   ├── Problem-solving: 8/10 (good debugging, thinks through issues)
│   └── Documentation: 6/10 (could be more thorough)
│
└── Overall Rating: 8.5/10 ⭐⭐⭐ (Strong Performer)

COMPENSATION & PROMOTION
├── Current salary: $6,000/month ($75/hr)
├── Market rate: $6,500/month (15% higher)
├── Recommendation: Raise to $6,500/month (keep competitive)
├── Promotion path: Senior Dev → Lead Developer (6 months)
└── Action: Discuss promotion in next 1-on-1

GOALS ACHIEVED THIS QUARTER
├── [✓] Deliver E-commerce platform on time
├── [✓] Mentor 1 junior developer (onboarded Alex)
├── [✓] Improve test coverage to 100%
└── [✓] Learn new payment API integration (Stripe)

NEXT QUARTER GOALS
├── [ ] Lead architecture design for API redesign project
├── [ ] Mentor 2 team members (deeper involvement)
├── [ ] Reduce bug rate to 0.5% (from current 1%)
├── [ ] Document 3 core systems (better knowledge sharing)
└── [ ] Contribute to hiring process (interview candidates)

GROWTH OPPORTUNITIES
├── Strength: Technical excellence, reliability
├── Growth area: Leadership skills, initiative
├── Training needed: System design, architecture patterns
├── Stretch goal: Lead a team project (promotion to Lead Dev)
└── Timeline: Ready for leadership role in 3-6 months

RETENTION SCORE: 9/10 (Very likely to stay)
├── Engagement: HIGH (excited about projects)
├── Compensation: Fair (slight raise recommended)
├── Growth: Clear path to Lead Developer
├── Team fit: Excellent (great with team)
└── Recommendation: Prioritize retention (key person)
```

### Team Performance Dashboard

```
TEAM PERFORMANCE SCORECARD
═════════════════════════════════════════════════════════════

INDIVIDUAL PERFORMANCE
├── John Developer: 8.5/10 (Strong performer, leadership track)
├── Maria Designer: 8.2/10 (Excellent designer, good communication)
└── Alex Contractor: 7.8/10 (Good performer, still ramping up)

TEAM VELOCITY
├── Sprint 1: 64 hours completed
├── Sprint 2 (in progress): 20/70 forecast (on track)
├── Average velocity: 66 hours/sprint
├── Trend: Stable (consistent output) ✓

QUALITY METRICS
├── Bug rate: 1% (1 bug per 100 hours of work)
├── Code review time: 24 hours (acceptable)
├── Test coverage: 95% (good)
├── Post-delivery defects: 0.5% (excellent)
└── Overall: EXCELLENT ✅

DELIVERY METRICS
├── On-time delivery: 97% (all sprints on time except 1 minor slip)
├── Scope creep: 5% (requests added mid-sprint, managed well)
├── Estimate accuracy: 87% (fairly accurate, improves with experience)
└── Overall: STRONG ✅

TEAM SATISFACTION
├── Team NPS (Net Promoter Score): 8.5/10
├── Work satisfaction: 8/10 (happy with projects, pace)
├── Manager satisfaction: 9/10 (happy with you as leader)
├── Work-life balance: 7/10 (could improve - John at 100% capacity)
└── Overall morale: GOOD ✅

TEAM HEALTH
├── Burnout risk: MODERATE (John at capacity, monitor closely)
├── Turnover risk: LOW (all engaged, good compensation)
├── Skill gaps: LOW (diverse skills, good coverage)
├── Capacity to scale: MEDIUM (would need hiring for Q3)
└── Overall: HEALTHY ✅
```

---

## Mode 5: GOALS - Align Team with Business Goals

Connect team work to business objectives.

### Business Goal Alignment

```
BUSINESS GOAL: Build $200K/year software business
═════════════════════════════════════════════════════════════

TEAM'S ROLE IN GOAL
├── Generate revenue through project delivery: YES ✅
├── Build repeatable product/processes: IN PROGRESS
├── Scale without proportional time increase: IN PROGRESS
└── Overall contribution: CRITICAL ✅

CURRENT IMPACT ON REVENUE
├── Projects completed this quarter: 4 projects
├── Total revenue generated: $125,000 (50% of Q1 target)
├── Revenue per team member: $41,667
├── Team capacity remaining: 15 hours/week (could do 1 more small project)
└── Assessment: Team is productive ✅

TEAM GOALS SUPPORTING BUSINESS
├── John's goals:
│   ├── Improve architecture skills → Better system design
│   ├── Lead API redesign project → High-value internal work
│   ├── Mentor others → Improves team capability
│   └── Revenue impact: Enables more complex projects ($30K+)
│
├── Maria's goals:
│   ├── Improve design systems → Faster design turnaround
│   ├── Learn UX research → Better product decisions
│   ├── Build design library → Reusable components
│   └── Revenue impact: Can handle more design work (parallel projects)
│
└── Alex's goals:
    ├── Master payment integrations → Valuable service
    ├── Learn backend optimization → Reduces bottlenecks
    ├── Become independent contributor → Less onboarding burden
    └── Revenue impact: Can handle full-stack projects solo

RESOURCE ALLOCATION FOR BUSINESS GOALS
├── External projects (revenue-generating): 70 hours/week
│   └── Generates $200K+ annual revenue (primary focus)
│
├── Internal projects (product/automation): 10 hours/week
│   └── Reduces future delivery time (improves margins)
│
├── Admin/Overhead: 5 hours/week
│   └── Necessary for team function
│
└── Total: 85 hours/week (optimal allocation) ✅

PATH TO $200K GOAL
├── Current trajectory: $250K+ (on track)
├── Team's contribution: 100% (all work is through team)
├── Growth needed: Hire 1-2 more people by Q3
├── Team readiness: Good (John can manage/mentor)
└── Recommendation: Start recruitment in Q2
```

---

## Data Storage

Team and task data is saved in:

**JSON File** (CLI):

```
.claude/data/team.json
├── Team member profiles (capacity, performance, salary)
├── Tasks and assignments (status, deadlines, DRI)
├── Sprint planning (goals, allocation, velocity)
├── Performance reviews and feedback
└── Team goals and alignment with business
```

**PostgreSQL** (Analytics):

```
team_members table
├── member_id, name, role, salary, capacity
├── hire_date, performance_score
├── current_tasks, availability
└── created_at, updated_at

tasks table
├── task_id, project_id, assigned_to (DRI)
├── title, description, status
├── estimated_hours, actual_hours, deadline
├── priority, blocker_dependencies
└── created_at, updated_at

sprints table
├── sprint_id, start_date, end_date
├── goals, planned_hours, actual_hours
├── velocity, on_track (bool)
└── created_at, updated_at
```

---

## Integration with Life Goals

Team capacity should respect personal life goals:

```
LIFE GOAL: Work-Life Balance (Work ≤40 hrs/week)
├── John's allocation: 40 hrs/week (at limit)
│   └── No buffer for emergency requests (RISK)
│
├── Maria's allocation: 30 hrs/week (comfortable)
│   └── 10-hour buffer for growth work (GOOD)
│
└── Alex's allocation: 15 hrs/week part-time (sustainable)
    └── Perfect part-time arrangement (GOOD)

TEAM HEALTH SUPPORTS BUSINESS GOALS
├── Happy team → Better code quality → Better clients
├── Rested team → Higher productivity → More revenue
├── Trusted team → Can delegate more → You focus on sales/strategy
└── Growing team → Can scale → Path to $500K+ revenue
```

---

## Success Criteria

**After 1 month:**

- ✅ Team member capacities documented
- ✅ First sprint planned and tracked
- ✅ Task tracking system in place
- ✅ Weekly standups established

**After 3 months:**

- ✅ Sprint velocity established (predictable)
- ✅ Team member performance baseline set
- ✅ Growth goals defined for each person
- ✅ No burnout incidents (team healthy)

**After 6 months:**

- ✅ Team velocity consistent (±10%)
- ✅ Performance reviews completed (growth plans)
- ✅ Attrition: 0 (team stability)
- ✅ Team satisfaction 8+/10

**System Health**:

- ✅ Team utilization 75-85% (healthy, not overloaded)
- ✅ Delivery on-time 95%+ (reliable)
- ✅ Quality metrics strong (low bug rate)
- ✅ Team morale high (NPS 8+)

---

## ROI & Impact

**Time Investment**: 5 hours/week (planning, 1-on-1s, reviews)
**Annual ROI**: Better team productivity, lower turnover, higher quality

**Key Benefits**:

- Predictable capacity planning (know what team can deliver)
- Lower turnover (happy, growing team)
- Better code quality (focused, not burnt out)
- Scalable team (systems, delegation, mentoring)
- Higher profit margins (efficient team = higher profit per project)

---

**Created with the goal-centric life management system**
**Build a strong team to scale your business beyond yourself**
