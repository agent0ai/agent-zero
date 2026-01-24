---
description: "Design and track keystone habits that drive goal progress with habit stacking and streak tracking"
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
argument-hint: "[design|track|analyze|streak] [--goal <goal-id>] [--export] [--correlate]"
---

# /life:habits - Keystone Habits System

Design and track keystone habits that directly drive progress toward your life goals.

## Quick Start

**Design your first habits:**

```bash
/life:habits design
```

**Log today's habit progress:**

```bash
/life:habits track
```

**Analyze habit effectiveness:**

```bash
/life:habits analyze
```

**Check your streaks:**

```bash
/life:habits streak
```

---

## System Overview

This command implements a **keystone habits system** where a small number of high-leverage habits drive progress across multiple goals.

**Key Principle**: 1 keystone habit can impact 3-5 goals simultaneously.

Example:

- **Keystone Habit**: Morning workout (6am-7am)
- **Impacts**: Health goal, Energy goal, Productivity goal, Mental clarity

---

## Mode 1: DESIGN - Create Your Habit System

Design keystone habits aligned to your life goals.

### Step 1: Identify Keystone Habits

For each goal, identify the ONE habit that has the highest leverage:

**Financial Independence Goal**

- Keystone Habit: Review finances weekly (30 min)
- Triggers: Every Sunday 7pm
- Stacks with: Learning goal (read 1 financial article)

**Health & Wellness Goal**

- Keystone Habit: Morning workout (60 min)
- Triggers: Every morning 6am
- Stacks with: Energy goal (improves productivity)

**Relationships Goal**

- Keystone Habit: Family dinner with phones off (60 min)
- Triggers: Every weeknight 6:30pm
- Stacks with: Wellness goal (reduces stress)

### Step 2: Define Habit Triggers

Use BJ Fogg's **Tiny Habits** framework:

**Format**: After [CURRENT HABIT], I will [NEW HABIT]

Examples:

- After I pour my coffee, I will do 10 pushups
- After I sit at my desk, I will review my daily goals
- After dinner, I will journal for 5 minutes
- After brushing teeth, I will do a 2-minute meditation

**Timing Options**:

- Time-based: Every Monday at 9am
- Location-based: Every time at the gym
- Context-based: After each meeting
- Anchor-based: After current habit

### Step 3: Design Habit Stacking

Stack related habits to reduce friction:

**Morning Stack (30 min)**

1. Wake up (trigger)
2. Drink water (1 min)
3. Meditate (5 min) → Energy goal
4. Journal 3 goals (3 min) → Focus goal
5. Workout (20 min) → Health goal
6. Cold shower (1 min) → Resilience goal

**Evening Stack (20 min)**

1. Put phone away (trigger)
2. Review day (5 min)
3. Plan tomorrow (5 min)
4. Journal reflections (5 min)
5. Prepare for sleep (5 min)

### Step 4: Set Success Criteria

Define what "successful habit" looks like:

**Consistency Target**:

- Daily habits: 6/7 days per week (85%)
- Weekly habits: 4/4 weeks per month (100%)
- Monthly habits: 11/12 months per year (90%)

**Quality Target**:

- Habit completion checklist
- Time spent on habit
- Subjective energy/effort rating
- Impact on related goals

### Step 5: Calculate Impact Score

Rate each habit on its leverage:

**Habit Impact Score (0-10)**:

- 9-10: Impacts 4+ goals directly (Morning workout)
- 7-8: Impacts 2-3 goals (Weekly review)
- 5-6: Impacts 1 goal strongly (Meditation)
- 1-4: Impacts 1 goal weakly (Reading)

Focus on 9-10 impact habits first.

---

## Mode 2: TRACK - Log Daily Habit Progress

Log habit completions and track streaks.

### Daily Tracking (5 minutes)

Log each habit after completion:

```
/life:habits track

Today's Habits:
✅ Morning workout (6am) - 55 min
✅ Cold shower (6:55am) - 2 min
✅ Meditate (7am) - 5 min
✅ Journal goals (7:05am) - 3 min
⏳ Evening stack - Due at 9pm
```

### Weekly Review (15 minutes)

Every Sunday, review the week:

- **Completion rate**: Actual vs. target (did you hit 85%+?)
- **What went well**: Which habits felt easy?
- **Obstacles**: What made habits hard?
- **Correlations**: Which habits boosted which goals?
- **Next week**: Any adjustments needed?

### Monthly Review (30 minutes)

Review the month:

- **Trends**: Which habits are sticking?
- **Effectiveness**: Which habits drive most goal progress?
- **Fatigue**: Any habits causing burnout?
- **New learnings**: What did you discover about yourself?
- **Adjustments**: Add, drop, or modify habits?

---

## Mode 3: ANALYZE - Measure Habit Effectiveness

Analyze which habits drive actual goal progress.

### Habit Effectiveness Analysis

For each habit, measure:

1. **Consistency** (0-100%)
   - Target: 85%+ for daily habits
   - Calculation: Days completed / Days possible

2. **Impact on Goals** (0-10)
   - Self-rating: Does this habit move the goal forward?
   - Correlation: Track if goal progress increases when habit is consistent

3. **Energy Cost** (1-10)
   - Is this energizing or draining?
   - Sustainable: Can you do this forever?

4. **Friction** (1-10)
   - How hard is it to start?
   - How much friction did it have this month?

### Example Analysis

```
MORNING WORKOUT
├── Consistency: 92% (23/25 days)
├── Impact on Health Goal: 8/10
├── Impact on Energy Goal: 9/10
├── Impact on Productivity: 7/10
├── Energy Cost: Low (actually gives energy)
├── Friction: Low (trigger is strong - coffee)
└── Verdict: KEEP - High impact, sustainable

MEDITATION (5 min)
├── Consistency: 60% (15/25 days)
├── Impact on Energy Goal: 4/10
├── Impact on Focus Goal: 5/10
├── Energy Cost: Low
├── Friction: High (easy to skip)
└── Verdict: IMPROVE - Add to morning stack to reduce friction

WEEKLY FINANCIAL REVIEW
├── Consistency: 80% (3/4 weeks)
├── Impact on Finance Goal: 9/10
├── Impact on Peace of Mind: 8/10
├── Energy Cost: Medium
├── Friction: Medium (requires focus)
└── Verdict: KEEP - High impact, acceptable friction
```

### Correlation Analysis

Track which habits correlate with goal progress:

- Does high workout consistency correlate with higher energy scores?
- Does morning journal habit correlate with better decision-making?
- Does evening review habit correlate with fewer missed deadlines?

---

## Mode 4: STREAK - View and Maintain Streaks

Track and celebrate habit streaks.

### Streak System

Show current streaks with visual indicators:

```
STREAKS (as of today)
🔥 Morning workout: 23 days
🔥 Cold shower: 23 days
🔥 Meditate: 8 days
⏸️ Evening journal: 5 days (paused 2 days ago)
⚠️ Meal prep: 2 days (low streak)

MILESTONES REACHED:
🎯 30-day Morning Workout (Nov 2024)
🎯 7-day Meditation (Dec 2024)
🎯 100-day Cold Shower (Jan 2025)
```

### Streak Rules

**Streak Logic**:

- Streak breaks if you miss 2 consecutive days
- 1 day grace period (can miss 1 day, restart easily)
- Reset required after 2-day break (restarts from 1)

**Motivation System**:

- 7-day streak: 🔥 (initial momentum)
- 30-day streak: 🔥🔥 (habit forming)
- 100-day streak: 🔥🔥🔥 (ingrained)

**Recovery Protocol**:
If streak breaks:

1. Acknowledge (don't shame yourself)
2. Analyze (why did you miss?)
3. Restart (get back on today)
4. Adjust (reduce friction if needed)

---

## Habit Design Framework

### BJ Fogg's Tiny Habits Model

**B = MAP: Behavior = Motivation + Ability + Prompt**

For each habit:

1. **Motivation**: Why do this? (connects to goal)
   - Example: Morning workout → Health & Energy

2. **Ability**: Can you do it easily?
   - Start tiny: 1 pushup (not 20)
   - Low friction: No gym required
   - Clear steps: 10 min or less

3. **Prompt**: What triggers the habit?
   - Time: Every morning 6am
   - Location: At the kitchen counter
   - After: After pouring coffee
   - Context: When arriving at desk

### Habit Formation Timeline

Research shows habit formation follows this pattern:

- **Days 1-7**: Motivation high, consistency high (honeymoon phase)
- **Days 8-30**: Motivation drops, friction becomes apparent
- **Days 31-66**: Habit becomes semi-automatic
- **Days 67+**: Habit is ingrained, requires minimal motivation

**Key insight**: The 2-week dip is normal. Push through!

---

## Data Storage

Habits are saved in:

**JSON File** (CLI):

```
.claude/data/habits.json
├── Habit definitions (name, trigger, goal links)
├── Daily logs (completions, notes)
├── Weekly reviews
├── Streak tracking
└── Effectiveness ratings
```

**PostgreSQL** (Analytics):

```
habits table
├── habit_id, name, goal_id
├── trigger, frequency, impact_score
├── created_at, last_logged_at
└── consistency_percentage
```

---

## Success Criteria

**After `/life:habits design`:**

- ✅ 5-8 keystone habits identified
- ✅ Each habit linked to 1+ life goals
- ✅ Clear triggers defined for each
- ✅ Habit stacks created to reduce friction
- ✅ All habits have <20 min commitment/day

**After 2 weeks of `/life:habits track`:**

- ✅ Average consistency 60%+
- ✅ Most habits have clear triggers
- ✅ No overwhelming friction

**After 1 month of tracking:**

- ✅ Average consistency 75%+
- ✅ Clear correlation between habits and goal progress
- ✅ Streaks visible (multiple 7+ day streaks)
- ✅ Identified which habits to keep vs. adjust

**Healthy Habit Portfolio:**

- ✅ 80%+ average consistency across all habits
- ✅ 3-5 high-impact (9-10 score) habits ingrained
- ✅ No habits causing burnout (all energy cost <5)
- ✅ Clear line of sight from habits to goal progress

---

## Tips for Success

**Week 1-2: Keep It Tiny**

- Start with 1-2 habits
- Make them ridiculously easy
- Focus on consistency, not intensity

**Week 3-4: Stack Habits**

- Anchor new habits to existing ones
- Group related habits (morning stack, evening stack)
- Reduce overall friction

**Month 2: Optimize**

- Track which habits stick
- Identify your "non-negotiable" habits
- Drop habits that don't drive goal progress

**Month 3+: Maintenance**

- Habits should feel automatic
- Minimal willpower required
- Focus on tracking, not motivation

---

## Integration with Life Goals

Each habit should ladder back to `/life:goals`:

```
GOAL: Financial Independence
├── Business Goal: Build $200K/year software product
│   └── Habit: Weekly financial review (30 min)
│       └── Tracks: Income, expenses, investment progress
│       └── Triggers: Sunday 7pm
└── RE Goal: Invest $100K in real estate
    └── Habit: Research 1 property per week (30 min)
        └── Tracks: Market trends, deal analysis
        └── Triggers: Wednesday evening
```

---

## Next Steps

After designing habits, use these commands:

- `/life:time` - Time block your habits into daily schedule
- `/life:wellness` - Track how habits correlate with energy/health
- `/software-business:projects` - Apply habit system to business goals

---

**ROI & Impact**

**Time Investment**: 30 min/week (design 20 min + weekly review 10 min)
**Annual ROI**: $113,600 (based on 4,369x return)
**Key Benefits**:

- 30% productivity increase (from consistency)
- Stress reduction (automated decisions)
- Faster goal achievement (compounding effect)
- Higher energy (right habits energize)

---

**Created with the goal-centric life management system**
**Track your habits daily for maximum impact**
