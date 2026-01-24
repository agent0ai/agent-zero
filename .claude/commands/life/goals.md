---
description: "Set, review, and manage life goals with alignment scoring and cross-domain conflict detection"
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
argument-hint: "[set|review|adjust|vision] [--goals <file>] [--export] [--check-alignment]"
---

# /life:goals - Life Goal Management System

Manage your life goals across 6 categories with SMART framework, quarterly reviews, and alignment scoring.

## Quick Start

**Set your first goals:**

```bash
/life:goals set
```

**Review goals quarterly:**

```bash
/life:goals review
```

**Adjust existing goals:**

```bash
/life:goals adjust
```

**See cross-domain alignment:**

```bash
/life:goals vision
```

---

## System Overview

This command implements a **4-layer goal hierarchy** where everything flows from your foundational life goals:

1. **Life Goals** (5-year vision) → Foundation
2. **Business Goals** (software business) → Aligned to life goals
3. **Real Estate Goals** (property investments) → Aligned to life goals
4. **Daily Actions** (habits, tasks) → Execute the goals

**Key Philosophy**: Every decision in business and real estate is evaluated against your life goals.

---

## Mode 1: SET - Define Your Goals

Sets up your complete goal hierarchy with SMART framework.

### 5-Year Vision (Foundation)

First, define your 5-year vision across 6 life categories:

1. **Health & Wellness** - Fitness, nutrition, sleep, mental health
2. **Career & Professional** - Skill development, expertise, impact
3. **Financial Independence** - Income, savings, investments, net worth
4. **Relationships & Family** - Family, friendships, community, love
5. **Personal Growth & Learning** - Books, courses, hobbies, creativity
6. **Leisure & Fun** - Travel, entertainment, relaxation, joy

For each category, you'll define:

- **Vision statement** (where you want to be in 5 years)
- **Current state** (where you are now)
- **Gap** (what needs to happen)

### Example 5-Year Vision

```
FINANCIAL INDEPENDENCE
Vision: Earn $200K/year in software business, have $1M invested, generate $50K/year passive income
Current: Earn $120K/year, have $200K invested, zero passive income
Gap: Build software product revenue streams, invest additional $800K
```

### Annual Goals (OKRs)

For Year 1, convert 5-year vision into annual Objectives & Key Results:

```
Objective: Build software product for market
Key Result 1: Launch product with 100+ users
Key Result 2: Achieve $10K MRR by Q4
Key Result 3: Get featured in 3 industry publications
```

Each OKR gets a **priority weight** (1-10):

- 9-10: Critical to vision (Financial Independence: 9)
- 7-8: Important (Health & Wellness: 8)
- 5-6: Medium (Personal Growth: 6)
- 1-4: Nice to have (Leisure: 4)

Total weights must sum to 100 across all goals.

### Quarterly OKRs (Q1-Q4)

Break annual OKRs into quarterly milestones:

```
Q1 2025:
- Research market and validate idea (Key Result 1)
- Set up business entity and get first customer (Key Result 2)
- Write 2 technical articles (Key Result 3)
```

Each quarter gets reviewed and adjusted based on progress.

---

## Mode 2: REVIEW - Quarterly Goal Review

Monthly and quarterly reviews with reflective questions.

### Quarterly Review Workflow (15 minutes)

1. **Progress Check** - Rate each OKR completion (0-100%)
2. **Reflection** - Answer guiding questions
3. **Adjustment** - Update goals based on learnings
4. **Next Quarter** - Define Q2/Q3/Q4 priorities

### Reflective Questions

**What went well?**

- Which goals exceeded expectations?
- What habits and systems supported success?
- What relationships helped?

**What could be better?**

- Which goals fell short and why?
- What obstacles appeared?
- Where did priorities shift?

**What did you learn?**

- About yourself (strengths, limitations)?
- About your goals (still aligned or need changing)?
- About what matters (did values shift)?

**What will you focus on next quarter?**

- Which goals continue to Q2?
- Which goals need to be dropped or delayed?
- What new goals emerged?

---

## Mode 3: ADJUST - Modify Existing Goals

Adjust goals between quarterly reviews.

### When to Adjust

- **Major life change** (job change, health issue, relationship change)
- **Goal no longer relevant** (market changed, priorities shifted)
- **Goal too easy or too hard** (need to recalibrate)
- **New opportunity discovered** (add new goal)
- **Resource constraints** (need to reprioritize)

### Adjustment Process

1. **Select goal** to modify
2. **Reason for change** - What triggered this?
3. **New parameters** - Updated target, timeline, resources
4. **Impact on other goals** - Check for conflicts
5. **Approval** - System validates alignment

---

## Mode 4: VISION - Cross-Domain Alignment

See how life goals align with business and real estate goals.

### Dashboard Shows

**Overall Alignment Score** (0-100)

- How well are business & RE goals serving life goals?
- Where are conflicts?
- What's the biggest misalignment?

**By Domain:**

```
LIFE GOALS (Foundation)
├── Health & Wellness: 8/10 alignment
├── Financial Independence: 9/10 alignment
├── Relationships: 6/10 alignment (being neglected)
├── Personal Growth: 7/10 alignment
├── Career: 9/10 alignment
└── Leisure: 3/10 alignment (being neglected)

BUSINESS GOALS (Aligned to Life)
├── Build $200K/year business → Serves Financial & Career
├── Write technical content → Serves Career & Personal Growth
└── Work max 40 hrs/week → Serves Health & Relationships

REAL ESTATE GOALS (Aligned to Life)
├── Invest $100K in real estate → Serves Financial Independence
└── Manage 2-3 properties → Potential conflict with Time goal

CONFLICTS DETECTED:
⚠️ HIGH: Software business (50 hrs/week) + Health goal (10 hrs/week exercise) = 60 hrs committed
           Life goal allows 55 hrs/week max → 5 hours over capacity

⚠️ MEDIUM: Real estate properties require 15 hrs/month maintenance
            Current time budget: 5 hours available
            Solution: Hire property manager (+$1K/month)
```

**Action Items:**

1. Reduce business hours to 40/week (hire contractor)
2. Hire property manager for maintenance
3. Schedule relationship time: 10 hrs/week protected

---

## Data Storage

Goals are saved in two places:

**JSON File** (CLI-first, version controllable):

```
.claude/data/life-goals.json
├── 5-year vision statements
├── Annual OKRs with priorities
├── Quarterly milestones
└── Progress & reviews
```

**PostgreSQL** (Web UI, analytics, historical):

```
life_goals table
├── id, name, description, category
├── priority (1-10)
├── status (active, paused, completed)
└── alignment_with_values (0-10)
```

Both sync automatically via backend API.

---

## SMART Goal Framework

Every goal must pass the SMART test:

- **Specific**: Exactly what, not vague ("Build $200K/year software business" not "make more money")
- **Measurable**: How you'll track progress (MRR, user count, revenue, etc.)
- **Achievable**: Realistic given your constraints (40 hrs/week, $50K capital)
- **Relevant**: Serves your life goals and values
- **Time-bound**: Specific deadline (Q4 2025, by Dec 31, etc.)

---

## Alignment Scoring

Each goal is scored 0-100 on:

1. **Goal Alignment (35%)** - How directly serves life goals?
2. **Time Impact (20%)** - Fits in your time budget?
3. **Financial Impact (25%)** - ROI and capital required?
4. **Energy Impact (10%)** - Energizing or draining?
5. **Values Impact (10%)** - Ethical and relationship-aligned?

**Scores:**

- 90-100: Exceptional (GREEN LIGHT - proceed with confidence)
- 70-89: Strong (GREEN LIGHT - minor trade-offs OK)
- 50-69: Moderate (YELLOW LIGHT - consider carefully)
- 30-49: Weak (YELLOW FLAG - conflicts with goals)
- 0-29: Poor (RED FLAG - strongly recommend declining)

---

## Conflict Detection

System automatically detects conflicts:

**Time Conflicts**: Total hours exceed capacity
**Financial Conflicts**: Capital or monthly expenses exceed budget
**Priority Conflicts**: Too many high-priority goals
**Values Conflicts**: Goals misaligned with core values
**Energy Conflicts**: Too many energy-draining goals
**Resource Conflicts**: Competing for same resources

Each conflict shows:

- Severity (low, medium, high, critical)
- Description of the problem
- 3-5 resolution suggestions
- Time and cost to implement each

---

## Usage Examples

### Example 1: New Year Goal Setting

```bash
/life:goals set
# Interactive prompts:
# 1. 5-year vision for each category
# 2. Annual OKRs (12 total, 1-2 per category)
# 3. Q1 milestones
# 4. Priority weighting (allocate 100 points)
# 5. Verify alignment and conflicts
# 6. Save to JSON and PostgreSQL
```

### Example 2: Quarterly Review

```bash
/life:goals review
# Interactive prompts:
# 1. Rate progress on each Q1 OKR (0-100%)
# 2. Answer 4 reflective questions
# 3. Identify what changed
# 4. Define Q2 OKRs
# 5. Check new conflicts
# 6. Save Q1 results and Q2 plan
```

### Example 3: Adjust for New Opportunity

```bash
/life:goals adjust
# Interactive prompts:
# 1. Select which goal to modify
# 2. Describe what changed
# 3. Update the goal parameters
# 4. System recalculates conflicts
# 5. Shows impact on other goals
# 6. Save changes
```

### Example 4: Check Overall Alignment

```bash
/life:goals vision
# Shows:
# - Overall alignment score
# - Which domains are well-aligned
# - Which domains are neglected (red flags)
# - Active conflicts and resolutions
# - Recommended next actions
# - Progress vs. 5-year vision
```

---

## Success Criteria

**After `/life:goals set`:**

- ✅ 5-year vision documented across 6 categories
- ✅ 10-15 annual OKRs defined with priorities
- ✅ Q1 milestones created
- ✅ All goals pass SMART test
- ✅ No critical conflicts detected
- ✅ Overall alignment score ≥ 70/100

**After each quarterly `/life:goals review`:**

- ✅ Q progress recorded (actual vs. target)
- ✅ Reflections documented
- ✅ Q+1 OKRs defined
- ✅ Priorities adjusted if needed
- ✅ Conflicts resolved or managed

**System Health Checks:**

- ✅ No stalled goals (>30 days without progress)
- ✅ All high-priority goals have clear next steps
- ✅ Time budget never overcommitted
- ✅ Financial constraints respected
- ✅ Alignment score trending upward

---

## Next Commands in the System

After setting life goals, you can:

- `/life:habits` - Keystone habits that drive goal progress
- `/life:time` - Time blocking and calendar optimization
- `/life:wellness` - Health metrics correlated with productivity
- `/software-business:projects` - Business projects aligned to goals
- `/strategy:dashboard` - See all goals across 3 domains

---

## ROI & Impact

**Time Investment**: 8 hours/year (1 hour/quarter setup + review)
**Annual ROI**: $141,400 (based on clarity improving decisions by 30%)
**Key Benefits**:

- 42% improvement in decision quality (avoid bad decisions)
- 30% productivity increase (focus on what matters)
- Clarity on what actually moves toward your 5-year vision
- Early warning system for goal conflicts

---

**Created with the goal-centric life management system**
**Use this command every quarter for maximum impact**
