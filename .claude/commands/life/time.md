---
description: "Audit and optimize time allocation with Eisenhower matrix, time blocking, and goal alignment scoring"
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
argument-hint: "[audit|block|matrix|optimize] [--goal <goal-id>] [--week] [--export]"
---

# /life:time - Calendar Optimization System

Audit your time, identify misalignment with goals, and create protected time blocks for deep work.

## Quick Start

**Audit your time usage:**

```bash
/life:time audit
```

**Create time blocks for deep work:**

```bash
/life:time block
```

**Analyze using Eisenhower matrix:**

```bash
/life:time matrix
```

**Get optimization recommendations:**

```bash
/life:time optimize
```

---

## System Overview

This command implements **time auditing and optimization** where every hour is evaluated against your life goals.

**Key Principle**: You have 168 hours/week. Every hour is either:

1. **Protected** (aligned with life goals)
2. **Productive** (efficient work toward goals)
3. **Waste** (misaligned or untracked)

The system's job: Maximize protected + productive hours, eliminate waste.

---

## Mode 1: AUDIT - Track Where Your Time Goes

Audit your current time usage and calculate goal alignment percentage.

### Weekly Time Audit Workflow (30 minutes)

1. **Collect Time Data**: How did you spend time last week?
   - Prompt user for major activities and hours
   - Examples: Work (40h), Exercise (5h), Sleep (56h), Social media (10h), Family (12h), Learning (3h), Rest (42h)

2. **Categorize Time**: Which life goals does each activity serve?
   - Work → Financial Independence, Career
   - Exercise → Health & Wellness
   - Family time → Relationships
   - Learning → Personal Growth
   - Sleep → Health & Wellness
   - Social media → Waste (unaligned)

3. **Calculate Alignment Score**:

**Total Weekly Hours**: 168
**Goal-Aligned Hours**: Sum of time on activities that serve your top life goals
**Alignment Percentage**: Goal-Aligned Hours / 168 * 100

**Example**:

```
WEEKLY TIME AUDIT
├── Sleep: 56h (Health) ✅ PROTECTED
├── Work: 40h (Financial + Career) ✅ PROTECTED
├── Exercise: 5h (Health) ✅ PROTECTED
├── Family time: 12h (Relationships) ✅ PROTECTED
├── Learning: 3h (Personal Growth) ✅ PROTECTED
├── Meals: 5h (Health) ✅ PROTECTED
├── Commute: 5h (Neutral)
├── Social media: 10h ❌ WASTE
├── TV/Entertainment: 15h (Leisure goal - acceptable)
└── Other: 2h (Untracked)

GOAL-ALIGNED HOURS: 121 / 168 = 72% alignment
TARGET: 75%+ alignment
GAP: Need to reclaim 5 hours/week
```

### Time Categories

**PROTECTED TIME** (Goal-aligned, non-negotiable):

- Sleep: 7-8 hours/night (56 hours/week) → Health
- Work/Business: Core hours focused on business goals
- Exercise: 5-10 hours/week → Health & Wellness
- Family/Relationships: 10+ hours/week → Relationships
- Deep Learning: 3-5 hours/week → Personal Growth
- Meals: 4-5 hours/week → Health & Wellness

**PRODUCTIVE TIME** (Efficient, aligned with goals):

- Focused work sessions (90 min blocks)
- Project work toward business/life goals
- Administrative tasks supporting goals

**LEISURE TIME** (Optional, aligns with Leisure goal):

- Entertainment: TV, movies, gaming
- Social activities for enjoyment
- Hobbies and creative pursuits

**WASTE TIME** (Unaligned, should eliminate):

- Endless scrolling (social media without purpose)
- Unproductive meetings
- Context switching
- Commute time (consider optimization)
- Task switching without focus

### Audit Questions

Answer these questions to understand your time:

1. **What activities consumed the most time last week?**
   - Top 3 activities (likely: sleep, work, leisure)

2. **Which activities directly serve your top 3 life goals?**
   - Identify the strongest alignments

3. **What time felt wasted?**
   - Social media, inefficient meetings, procrastination
   - Quantify: How many hours?

4. **What's missing from your week?**
   - Desired vs. actual for health, relationships, learning
   - Where are you underinvesting?

5. **If you could reclaim 5 hours/week, what would you do with them?**
   - This reveals your true priorities

---

## Mode 2: BLOCK - Create Deep Work Time Blocks

Design your ideal week with protected time blocks.

### Deep Work Blocks (3-hour protected sessions)

**Why 3 hours?**

- First 30 min: Context switching, warm-up
- Next 120 min: Deep flow state
- Last 30 min: Documentation and wrap-up
- Total: 3 hours = ~2 hours of true deep work

**Weekly Structure**:

```
MONDAY
├── 6-7am: Exercise (1h) → Health goal
├── 7-8am: Morning routine + breakfast
├── 8am-12pm: Deep Work Block #1 (Business)
├── 12-1pm: Lunch
├── 1-5pm: Meetings/Admin (or Block #2 if urgent)
└── 5-7pm: Family time

TUESDAY
├── 6-7am: Exercise (1h)
├── 8am-12pm: Deep Work Block #2 (Business)
├── 12-1pm: Lunch
├── 1-5pm: Client calls/meetings
└── 5-7pm: Family time

WEDNESDAY
├── 6-7am: Exercise (1h)
├── 8am-12pm: Deep Work Block #3 (Learning/Personal)
├── 1-5pm: Administrative tasks
└── 5-7pm: Family time

THURSDAY
├── 6-7am: Exercise (1h)
├── 8am-12pm: Deep Work Block #4 (Business)
├── 1-5pm: Meetings/Client work
└── 5-7pm: Family time

FRIDAY
├── 6-7am: Exercise (1h)
├── 8am-12pm: Deep Work Block #5 (Planning/Learning)
├── 1-3pm: Weekly review + planning
└── Afternoon: Flexible/Light work

WEEKEND
├── Saturday morning: Planning/Admin (2h)
├── Saturday afternoon: Family time (4h)
├── Saturday evening: Personal projects
├── Sunday: Family + Rest
```

### Time Block Rules

**Sacred Rules** (non-negotiable):

1. **Deep work blocks start at full hour** (8am, not 8:15am)
2. **No meetings during deep work** - All meetings 1-5pm
3. **No notifications during deep work** - Phone off, Slack/email closed
4. **Minimum 3 deep work blocks per week** - For business/learning
5. **Exercise protected** - 5+ hours per week, non-negotiable
6. **Sleep protected** - 7-8 hours per night, consistent bedtime
7. **Family time protected** - 10+ hours per week, phones off

**Flexibility Zones**:

- Afternoons (1-5pm): Flexible for meetings, calls, administrative work
- Friday afternoons: Lighter work, planning, flexibility
- Weekend: Flexible schedule (but protect family time)

### Creating Your Ideal Week

Step 1: List fixed commitments

- Work hours (9-5 or whatever)
- Sleep (56 hours/week = 8/night)
- Commute (if required)
- Family obligations

Step 2: Schedule protected activities

- Exercise: 5-10 hours/week
- Family time: 10+ hours/week
- Learning: 3-5 hours/week
- Meals: 4-5 hours/week

Step 3: Block deep work sessions

- 3-4 hours minimum for focused work
- Spread across 3-5 days
- Protect from meetings and interruptions

Step 4: Schedule meetings and admin

- Cluster meetings (e.g., all 1-5pm)
- Leave admin time (30 min/day for email, Slack)
- Plan for unexpected interruptions

Step 5: Identify remaining hours

- Are you at 75%+ goal alignment?
- If not, what can you eliminate, delegate, or batch?

---

## Mode 3: MATRIX - Eisenhower Matrix Analysis

Categorize activities into 4 quadrants: Urgent/Important.

### The Four Quadrants

**Quadrant 1: URGENT & IMPORTANT** 🔴

- Crisis management
- Deadlines (day before)
- Health emergencies
- Client emergencies
- Action: **Do immediately**

Examples:

- Dealing with angry client
- Fixing production bug
- Health crisis
- Family emergency

Time allocation: **5-10% of week** (ideal)

**Quadrant 2: NOT URGENT & IMPORTANT** 🟢 (THE WINNER'S QUADRANT)

- Strategic work on business goals
- Building relationships
- Health and fitness
- Learning and development
- Planning and reflection
- Action: **Schedule deep work blocks here**

Examples:

- Building new product feature
- Strategic business planning
- Regular exercise
- Reading and learning
- Family time
- Weekly goal review

Time allocation: **50-60% of week** (GOAL)

**Quadrant 3: URGENT & NOT IMPORTANT** 🟡

- Interruptions
- Many emails and messages
- Some meetings
- Other people's priorities
- Action: **Delegate or batch**

Examples:

- Non-critical Slack messages
- Unnecessary meetings
- Approval requests
- Administrative tasks
- Other people's deadlines

Time allocation: **10-20% of week** (minimize)

**Quadrant 4: NOT URGENT & NOT IMPORTANT** ⚫

- Time wasters
- Social media
- Mindless entertainment
- Procrastination
- Action: **Eliminate or severely limit**

Examples:

- Endless social media scrolling
- Non-productive TV watching
- Procrastination activities
- Gossip
- Complaining

Time allocation: **5-10% of week** (minimize)

### Your Quadrant Distribution

Answer these questions:

1. **Quadrant 2 time**: How many hours/week do you spend on strategic work?
   - Target: 40-50 hours/week
   - If less: You're too reactive

2. **Quadrant 1 time**: How many hours/week in crisis mode?
   - Target: 5-10 hours/week (maybe less)
   - If more: Your planning is weak

3. **Quadrant 3 time**: How much time on other people's urgencies?
   - Target: 10-20 hours/week
   - If more: You're saying "yes" too much

4. **Quadrant 4 time**: How many hours wasted?
   - Target: 5-10 hours/week (leisure/rest)
   - If much more: This is your biggest opportunity

### Optimization Strategy

**Reduce Quadrant 1** (Crises):

- Better planning prevents crises
- Systems reduce firefighting
- Set customer expectations upfront

**Maximize Quadrant 2** (Strategic):

- Schedule deep work blocks (protected)
- Say "no" to non-strategic requests
- Batch interruptions (specific meeting times)

**Minimize Quadrant 3** (Other's urgency):

- Delegate or decline requests
- Block time for async work
- Set communication boundaries

**Eliminate Quadrant 4** (Waste):

- Delete apps causing endless scrolling
- Set time limits on entertainment
- Replace with Quadrant 2 activities

---

## Mode 4: OPTIMIZE - Get Recommendations

Get specific, actionable recommendations for optimizing your week.

### Time Optimization Analysis

The system analyzes your time and suggests:

1. **Hours to Eliminate** (Quick wins)
   - Social media: 10 hours/week → 1 hour/week = **9 hours gained**
   - TV: 15 hours/week → 5 hours/week = **10 hours gained**
   - Unproductive meetings: 3 hours/week = **3 hours gained**
   - Total: **22 hours/week** can be reclaimed

2. **Hours to Delegate** (Leverage your time)
   - Admin tasks: 5 hours/week → hire VA = **5 hours gained**
   - Email management: 3 hours/week → assistant = **3 hours gained**
   - Total: **8 hours/week** can be delegated

3. **Hours to Protect** (Move to calendar)
   - Deep work: 15 hours/week (3 × 5h blocks)
   - Exercise: 7 hours/week
   - Family: 12 hours/week
   - Learning: 4 hours/week
   - Total: **38 hours/week** protected for goals

4. **Hours Remaining** (Flexibility)
   - Sleep: 56 hours (protected)
   - Meals: 5 hours
   - Work/business: 40 hours (protected)
   - Travel: 3 hours
   - Miscellaneous: 5 hours
   - Total: **109 hours** (after above protections)

**Recommendation Priority**:

**Week 1: Eliminate (Quick wins)**

- Delete social media apps (or use app limiters: 15 min/day)
- Set "no TV before 8pm" rule
- Cancel 1-2 unnecessary meetings
- **Impact**: Reclaim 10-15 hours

**Week 2-3: Protect (Calendar changes)**

- Schedule 3 deep work blocks (8-12pm Mon/Wed/Fri)
- Schedule exercise (6-7am, 5 days/week)
- Schedule family time (Sat/Sun + weeknight dinners)
- **Impact**: Make goals achievable

**Week 4: Delegate (Outsource)**

- Hire VA for admin tasks ($500/month)
- Automate email management (filters, templates)
- Delegate approval workflows
- **Impact**: Free 5-8 hours/week for high-value work

---

## Time Audit Form

Track your actual time for 1 week and categorize.

### Daily Log Template

```
MONDAY (Dec 9, 2024)
├── 6:00-7:00am - Exercise (1h) → [Health goal]
├── 7:00-8:00am - Breakfast + morning routine (1h)
├── 8:00-12:00pm - Deep work on product (4h) → [Business goal]
├── 12:00-1:00pm - Lunch (1h)
├── 1:00-3:00pm - Client calls (2h) → [Business goal]
├── 3:00-5:00pm - Email + admin (2h)
├── 5:00-6:00pm - Commute (1h)
├── 6:00-8:00pm - Family dinner (2h) → [Relationships goal]
├── 8:00-10:00pm - Personal time (2h)
└── 10:00-6:00am - Sleep (8h) → [Health goal]

TOTAL: 24 hours
GOAL-ALIGNED: 17 hours (71%)
```

### Weekly Summary

After 7 days:

- Total hours tracked: 168
- Goal-aligned hours: ___
- Alignment percentage: ___ %
- Target: 75%+

If below target:

- Which activities can be eliminated? (waste)
- Which can be delegated? (not highest-value)
- What's missing? (underinvested in important areas)

---

## Data Storage

Time data is saved in:

**JSON File** (CLI):

```
.claude/data/time-tracking.json
├── Time blocks (schedule)
├── Weekly audits (historical)
├── Eisenhower matrix (categorization)
├── Optimization recommendations
└── Goal alignment scores per activity
```

**PostgreSQL** (Analytics):

```
time_blocks table
├── block_id, day_of_week, start_time, end_time
├── activity_name, goal_id, alignment_score
├── is_protected, quadrant (1-4)
└── created_at, updated_at
```

---

## Integration with Life Goals

Each time block should ladder back to `/life:goals`:

```
GOAL: Financial Independence
├── Business Goal: Build $200K/year software product
│   └── Deep work blocks: Mon/Wed/Fri 8am-12pm (12h/week)
│       └── Tracks: Progress on product features
└── Time protection: 40 hours/week minimum on business

GOAL: Health & Wellness
├── Fitness: Complete 3 workouts/week
│   └── Protected time: 6-7am Mon/Wed/Fri (3h/week)
└── Sleep: 8 hours/night
    └── Protected time: 11pm-7am every night (56h/week)
```

---

## Success Criteria

**After running `/life:time audit`:**

- ✅ Last week's time tracked and categorized
- ✅ Goal alignment percentage calculated
- ✅ Major time wasters identified
- ✅ Opportunities to reclaim 10+ hours found

**After creating time blocks:**

- ✅ Ideal week designed with protected activities
- ✅ 3+ deep work blocks scheduled
- ✅ Exercise, family, sleep protected
- ✅ All time blocks linked to life goals
- ✅ 75%+ goal alignment achieved

**After Eisenhower analysis:**

- ✅ Activities categorized into 4 quadrants
- ✅ Quadrant 2 (strategic) time identified
- ✅ Time wasters in Quadrant 4 quantified
- ✅ Reduction plan created

**After optimization:**

- ✅ 10+ hours/week can be reclaimed
- ✅ Elimination targets identified
- ✅ Delegation opportunities found
- ✅ New schedule shows 75%+ goal alignment

**System Health**:

- ✅ No goal left without dedicated time
- ✅ 3-4 deep work blocks scheduled per week
- ✅ Exercise, family, learning all protected
- ✅ Quadrant 2 activities dominate schedule (50%+)

---

## Integration with Other Commands

After optimizing time, use these commands:

- `/life:habits` - Fill protected time blocks with high-impact habits
- `/life:wellness` - Track health metrics in protected exercise time
- `/life:goals` - Link time blocks to specific goals and key results
- `/software-business:projects` - Schedule deep work blocks for projects

---

## Tips for Success

**Week 1: Audit**

- Track actual time for 7 days
- Be honest about time wasters
- Identify your biggest opportunity

**Week 2: Protect**

- Schedule 3 deep work blocks
- Protect exercise and sleep
- Block off family time
- Turn off notifications during deep work

**Week 3: Eliminate**

- Delete time-wasting apps
- Decline non-aligned meetings
- Batch email/messages (check 3x/day, not continuously)
- Start one Quadrant 2 habit

**Week 4+: Optimize**

- Review what's working
- Delegate where possible
- Add 1-2 more deep work blocks
- Increase goal alignment percentage
- Aim for 80%+ alignment

---

## ROI & Impact

**Time Investment**: 1 hour/week (audit + optimization)
**Annual ROI**: $591,400 (based on reclaiming 20 hours/week @ $285/hr)

**Key ROI Drivers**:

1. **Reclaimed time**: 15-20 hours/week = $221K/year
2. **Increased productivity**: 25% more output in deep work = $142K/year
3. **Better sleep**: Impact on energy/health = $150K/year
4. **Fewer sick days**: Better health = $45K/year
5. **Reduced stress**: Better balance = $33K/year

---

**Created with the goal-centric life management system**
**Optimize your time to align with what matters most**
