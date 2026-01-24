---
description: "Track health metrics and correlate with productivity, energy, and goal progress"
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
argument-hint: "[track|analyze|goals|integrate] [--metric fitness|nutrition|sleep|mental] [--period week|month] [--export]"
---

# /life:wellness - Health & Productivity Dashboard

Track fitness, nutrition, sleep, and mental health while measuring correlation with energy, productivity, and goal progress.

## Quick Start

**Log today's wellness metrics:**

```bash
/life:wellness track
```

**Analyze health correlations:**

```bash
/life:wellness analyze
```

**Connect health to life goals:**

```bash
/life:wellness goals
```

**Integrate wearable data:**

```bash
/life:wellness integrate
```

---

## System Overview

This command implements **health optimization where wellness metrics directly drive productivity and goal achievement**.

**Key Principle**: Your health is not separate from your goals. Sleep quality, exercise, nutrition, and mental health directly impact:

- Energy levels (ability to do deep work)
- Decision quality (cognitive function)
- Stress resilience (ability to handle pressure)
- Goal progress (compound effect of better habits)

The system tracks 4 health domains and measures correlation with productivity and goal progress.

---

## Mode 1: TRACK - Log Your Health Metrics

Daily and weekly health tracking.

### Four Health Domains

**Domain 1: FITNESS**

Track exercise and movement:

- Exercise type (cardio, strength, flexibility, sports, walking)
- Duration (minutes)
- Intensity (low, moderate, high)
- How you felt (energy before/after, motivation, recovery)

**Weekly Target**: 5+ hours of exercise (mix of cardio and strength)

Example daily log:

```
MONDAY EXERCISE
├── Type: Strength training
├── Duration: 60 minutes
├── Intensity: High
├── Exercises: Upper body (bench press, pull-ups, rows)
├── Recovery: Good
└── Energy after: High
```

**Metrics to track**:

- Weekly exercise hours
- Exercise frequency (days/week)
- Average intensity
- Consistency (% of planned workouts completed)
- Personal records (PRs)
- Bodyweight/measurements (weekly)

---

**Domain 2: NUTRITION**

Track eating habits and food quality:

- Meals logged (breakfast, lunch, dinner, snacks)
- Food quality rating (1-10 scale)
- Hydration (glasses of water/day)
- Alcohol consumption
- Supplements taken

**Daily target**: 8-10 glasses of water, 3 nutritious meals

Example daily log:

```
MONDAY NUTRITION
├── Breakfast: Eggs + oatmeal (quality: 8/10)
├── Lunch: Grilled chicken + vegetables (quality: 9/10)
├── Dinner: Salmon + rice + broccoli (quality: 9/10)
├── Snacks: Apple, almonds (quality: 8/10)
├── Water: 10 glasses ✅
└── Alcohol: 0 drinks
```

**Metrics to track**:

- Daily calories (if desired)
- Protein intake
- Vegetable servings/day
- Water consumption
- Caffeine intake (timing)
- Sugar/processed food intake
- Weekly consistency

---

**Domain 3: SLEEP**

Track sleep quality and quantity:

- Bedtime and wake time
- Total sleep duration
- Sleep quality rating (1-10)
- Times woke up during night
- Sleep environment (temperature, darkness, noise)
- Pre-sleep routine

**Nightly target**: 7-8 hours of quality sleep

Example nightly log:

```
MONDAY SLEEP
├── Bedtime: 10:30pm
├── Wake time: 6:30am
├── Total sleep: 8 hours
├── Quality: 8/10
├── Woke up: 1 time (2am, brief)
├── Environment: Cool (68°F), dark, quiet
└── Pre-sleep: 30-min wind-down, no screens after 10pm
```

**Metrics to track**:

- Average sleep per night
- Sleep quality average (1-10)
- Consistency (same bedtime?)
- Interruptions/night
- Time to fall asleep
- Wake time consistency
- Sleep debt (target - actual)

---

**Domain 4: MENTAL HEALTH**

Track mental clarity, stress, and emotional well-being:

- Mood rating (1-10 scale)
- Stress level (1-10 scale)
- Anxiety level (1-10 scale)
- Mental clarity (1-10 scale)
- Meditation/mindfulness minutes
- Journaling/reflection
- Social connection

**Daily target**: Mood 6+, stress <6, mental clarity 7+

Example daily log:

```
MONDAY MENTAL HEALTH
├── Mood: 7/10 (good)
├── Stress: 4/10 (low)
├── Anxiety: 2/10 (minimal)
├── Mental clarity: 8/10 (sharp)
├── Meditation: 10 minutes
├── Journaling: 15 minutes (reflections on day)
├── Social: Coffee with friend (1 hour)
└── Stressors: None major today
```

**Metrics to track**:

- Daily mood average
- Daily stress average
- Anxiety patterns
- Mental clarity
- Meditation frequency
- Journaling frequency
- Social connection (hours/week)

### Daily Wellness Check-In (5 minutes)

Every morning and evening:

**Morning (on waking)**:

- Sleep quality rating
- Current energy level (1-10)
- Mood (1-10)
- Any pain or soreness?
- Mental clarity (1-10)

**Evening (before bed)**:

- Exercise completed? (yes/no, what)
- Nutrition quality (1-10)
- Stress level (1-10)
- Productivity today (1-10)
- Mood (1-10)
- Any wins today?

### Weekly Wellness Summary

Every Sunday, review the week:

**Fitness Summary**:

- Total exercise hours: ___
- Exercise days: ___/7
- Average intensity: ___
- PRs or improvements: ___
- Consistency score: ___%

**Nutrition Summary**:

- Water consistency: ___%
- Meal quality average: ___ /10
- Days with healthy eating: ___/7
- Alcohol days: ___
- Energy related to nutrition: Yes/No

**Sleep Summary**:

- Average sleep: ___ hours
- Sleep quality average: ___ /10
- Consistent bedtime? Yes/No
- Interruptions per night: ___
- Sleep debt: ___ hours (target - actual)

**Mental Health Summary**:

- Average mood: ___ /10
- Average stress: ___ /10
- Meditation days: ___/7
- Journaling days: ___/7
- Best mental day: ___
- Worst mental day: ___

---

## Mode 2: ANALYZE - Find Health Correlations

Measure how wellness metrics correlate with productivity and energy.

### Key Correlations to Track

**Sleep vs. Productivity**

- Hypothesis: More sleep → higher productivity and energy
- Track: Sleep hours vs. Daily productivity rating (1-10)
- Example:

  ```
  Monday: 7 hours sleep → Productivity: 7/10
  Tuesday: 6 hours sleep → Productivity: 5/10
  Wednesday: 8 hours sleep → Productivity: 9/10

  CORRELATION: Strong positive (more sleep = higher productivity)
  ```

**Exercise vs. Energy**

- Hypothesis: Regular exercise → higher energy throughout day
- Track: Exercise hours/week vs. Average daily energy (1-10)
- Example:

  ```
  Week 1: 3 hours exercise → Average energy: 5.5/10
  Week 2: 5 hours exercise → Average energy: 7/10
  Week 3: 7 hours exercise → Average energy: 8/10

  CORRELATION: Strong positive (more exercise = higher energy)
  ```

**Nutrition vs. Mental Clarity**

- Hypothesis: Better nutrition → higher mental clarity
- Track: Daily nutrition quality (1-10) vs. Mental clarity (1-10)
- Example:

  ```
  Monday: Nutrition 7/10 → Mental clarity: 6/10
  Tuesday: Nutrition 9/10 → Mental clarity: 8/10
  Wednesday: Nutrition 5/10 → Mental clarity: 4/10

  CORRELATION: Strong positive (better nutrition = better clarity)
  ```

**Stress vs. Sleep Quality**

- Hypothesis: Lower stress → better sleep
- Track: Daily stress level vs. Night sleep quality
- Example:

  ```
  Monday: Stress 7/10 → Sleep quality: 5/10
  Tuesday: Stress 3/10 → Sleep quality: 9/10
  Wednesday: Stress 5/10 → Sleep quality: 7/10

  CORRELATION: Strong negative (lower stress = better sleep)
  ```

**Meditation vs. Stress**

- Hypothesis: Regular meditation → lower daily stress
- Track: Meditation minutes/day vs. Stress rating
- Example:

  ```
  Monday: 0 min meditation → Stress: 8/10
  Tuesday: 10 min meditation → Stress: 5/10
  Wednesday: 20 min meditation → Stress: 3/10
  Thursday: 0 min meditation → Stress: 7/10

  CORRELATION: Strong negative (more meditation = lower stress)
  ```

### Correlation Analysis Report

After 4 weeks of tracking, analyze:

**Strongest Positive Correlations**:
What wellness actions most strongly increase energy, productivity, and mood?

- Example: "Sleep quality has strongest impact on productivity (+0.87 correlation)"
- Example: "Exercise strongly increases energy levels (+0.82 correlation)"

**Strongest Negative Correlations**:
What factors most strongly decrease performance?

- Example: "Stress strongly decreases sleep quality (-0.74 correlation)"
- Example: "Alcohol reduces next-day energy (-0.65 correlation)"

**Weak/No Correlation**:
What wellness actions don't actually help (surprising findings)?

- Example: "Caffeine intake shows no correlation with productivity"
- Example: "Supplements show minimal benefit"

**Actionable Insights**:

1. Double down on high-impact actions
   - "Sleep is top priority - protect 8 hours/night"
   - "Exercise is energy multiplier - prioritize 5+ hours/week"

2. Eliminate low-impact actions
   - "Meditation not helping stress - try different approach"
   - "Journaling not showing benefit - replace with walks"

3. Test new interventions
   - "Try morning cold shower for energy boost"
   - "Test outdoor exercise vs. gym for mood"

### Goal Progress Correlation

Track how wellness impacts life goal progress:

**Financial Independence Goal**:

- Hypothesis: Better health → Higher productivity → More revenue
- Track: Monthly wellness score vs. Monthly revenue/progress
- Example:

  ```
  Month 1: Wellness score 6/10 → Revenue: $8K → Goal progress: 60%
  Month 2: Wellness score 8/10 → Revenue: $12K → Goal progress: 85%
  Month 3: Wellness score 9/10 → Revenue: $15K → Goal progress: 95%

  INSIGHT: Each point increase in wellness = +$2.3K/month revenue
  ```

**Career/Professional Goal**:

- Hypothesis: Better sleep/exercise → Higher quality work
- Track: Sleep hours vs. Work quality rating
- Example:

  ```
  Week with 6 hrs/night sleep → Work quality: 6/10 → Client satisfaction: 70%
  Week with 7.5 hrs/night sleep → Work quality: 8/10 → Client satisfaction: 85%

  INSIGHT: Additional 1.5 hrs sleep = +20% work quality
  ```

---

## Mode 3: GOALS - Connect Health to Life Goals

Link wellness metrics to your 5-year life vision.

### Health Goal Setting

For each wellness domain, define 3-month targets:

**FITNESS GOALS**:

```
Objective: Build strength and endurance
├── Key Result 1: Exercise 5+ hours/week (target: 80%+ consistency)
├── Key Result 2: Complete 1 workout class per week (consistency: 100%)
├── Key Result 3: Improve max push-ups from 30 → 50
└── Timeline: 12 weeks
```

**NUTRITION GOALS**:

```
Objective: Optimize nutrition for energy and clarity
├── Key Result 1: Drink 8+ glasses water daily (target: 90%+ days)
├── Key Result 2: Eat vegetables with every meal (target: 85%+ meals)
├── Key Result 3: Reduce sugar/processed food to 2x/week (current: 5x/week)
└── Timeline: 12 weeks
```

**SLEEP GOALS**:

```
Objective: Achieve consistent, high-quality sleep
├── Key Result 1: Sleep 7.5-8 hours every night (target: 85%+ nights)
├── Key Result 2: Consistent bedtime (within 30 min): 10:30pm
├── Key Result 3: Sleep quality average 8/10 (current: 6.5/10)
└── Timeline: 8 weeks (easier to change)
```

**MENTAL HEALTH GOALS**:

```
Objective: Reduce stress and increase mental clarity
├── Key Result 1: Daily meditation 10+ minutes (target: 85%+ days)
├── Key Result 2: Stress rating <5 on 80%+ days (current: <50%)
├── Key Result 3: Journaling 5+ days/week (current: 2x/week)
└── Timeline: 12 weeks
```

### How Wellness Serves Life Goals

Connect each wellness goal to broader life goals:

**LIFE GOAL: Financial Independence**

```
├── Business Goal: Build $200K/year software business
│   └── Requires: 40+ hours/week of deep work
│       └── Requires: High energy and mental clarity
│           ├── Sleep: 7.5-8 hours/night (current: 6.5h)
│           └── Exercise: 5 hours/week (current: 3h)
│               └── Wellness Action: Add morning workouts (6-7am)
│
├── Revenue Goal: Hit $10K MRR by end of year
│   └── Requires: 50+ quality deep-work hours/week
│       └── Requires: Peak mental clarity and focus
│           └── Nutrition: Optimize for sustained energy
│               └── Wellness Action: Eliminate caffeine crashes (steady hydration)
│
└── Timeline: 12 months
    └── Milestones:
        ├── Month 3: Sleep consistency 85%, Exercise 5h/week
        ├── Month 6: Wellness score 8/10, Revenue $6K/month
        ├── Month 9: Wellness score 9/10, Revenue $8K/month
        └── Month 12: Wellness score 9+/10, Revenue $10K+/month
```

**LIFE GOAL: Health & Wellness**

```
├── Fitness: Run a half-marathon
│   └── Requires: 5+ hours/week endurance training
│       ├── Current: 3 hours/week
│       ├── Monthly increase: +30 min/week
│       └── Timeline: 12 weeks training
│
├── Mental Health: Reduce stress/anxiety
│   └── Requires: Daily meditation + journaling
│       ├── Current: 2x/week meditation
│       ├── Target: 10+ min daily
│       └── Timeline: 8 weeks to habit
│
└── Nutrition: Optimize diet for energy
    ├── Current: Inconsistent
    ├── Target: 85%+ healthy days
    └── Timeline: 12 weeks
```

### Wellness Scorecard

Track overall wellness on a 0-10 scale:

**Components** (each 0-10):

1. Sleep quality (avg 1-10 rating)
2. Exercise consistency (% of planned workouts)
3. Nutrition quality (1-10 scale)
4. Mental clarity (avg 1-10 rating)
5. Stress level (inverse: 10 - stress rating)

**Overall Wellness Score** = Average of 5 components

**Target**: 8/10 or higher for optimal goal achievement

**Example this month**:

```
Sleep quality: 8/10
Exercise consistency: 85% → 8.5/10
Nutrition quality: 7/10
Mental clarity: 8/10
Stress level: 5/10 → 5/10

OVERALL WELLNESS SCORE: 7.5/10
TARGET: 8+/10
ACTION: Focus on nutrition quality next month
```

---

## Mode 4: INTEGRATE - Wearable Data Integration

Connect wearable devices for automatic health tracking.

### Supported Wearables

**Apple Watch**:

- Steps, active energy, exercise minutes
- Heart rate, heart rate variability (HRV)
- Sleep tracking (total hours, interruptions)
- Workout data (type, duration, intensity)
- Sync: via Health app to dashboard

**Oura Ring**:

- Sleep score (quality metric 0-100)
- Readiness score (recovery potential)
- Activity score (daily movement)
- Body temperature
- Sleep stages (light, deep, REM)
- Sync: via Oura API to dashboard

**Whoop Band**:

- Strain score (daily exertion 0-21)
- Recovery score (readiness 0-100)
- Sleep performance (vs. target)
- Heart rate variability (HRV)
- Resting heart rate (RHR)
- Sync: via Whoop API to dashboard

**Fitbit**:

- Steps, calories, active minutes
- Heart rate zones
- Sleep tracking (duration, quality)
- SpO2 (blood oxygen)
- Sync: via Fitbit API to dashboard

**Garmin**:

- Training load (weekly exertion)
- Recovery time needed
- VO2 max (fitness level)
- Training stress score (TSS)
- Sleep tracking
- Sync: via Garmin API to dashboard

### Setup Integration

For each wearable:

1. **Authorize Connection**:
   - User grants permission via OAuth
   - System stores encrypted API key

2. **Select Metrics**:
   - Choose which data to import
   - Set sync frequency (daily, hourly)

3. **Map to Health Domains**:
   - Apple Watch steps → FITNESS
   - Oura sleep score → SLEEP
   - Whoop recovery → MENTAL HEALTH

4. **Set Targets**:
   - Define daily/weekly goals per metric
   - Configure alerts if below threshold

### Automatic Correlation Analysis

Once wearable data is integrated:

**Daily Correlation Report**:

```
TODAY'S METRICS
├── Sleep: 7.5 hours (quality: 8/10) ✅
├── Heart Rate Variability: 65 (good recovery)
├── Daily Steps: 8,200 (target: 8,000) ✅
├── Workouts: 1 (60 min strength)
└── Resting Heart Rate: 58 (improving)

CORRELATIONS
├── Last night's sleep (7.5h) → Today's productivity: 8.5/10 ✅
├── This week's workouts (4h) → Stress reduction: 32% ✓
└── Daily steps (8K+) → Energy levels: +2 points ✓

RECOMMENDATIONS
1. Keep current sleep schedule - it's working
2. Add 1 more weekly workout to maintain energy
3. Maintain step count - strong productivity correlation
```

**Weekly Correlation Analysis**:

```
THIS WEEK'S METRICS
├── Average sleep: 7.4 hours
├── Average HRV: 62 (stable)
├── Average steps: 7,900
├── Workouts completed: 4/5 (80%)
└── Average resting HR: 58 (down from 62)

HEALTH TRENDS
├── Sleep: Improving (trending up from 6.8h)
├── Heart health: Improving (RHR dropping)
├── Activity: Consistent
└── Recovery: Good (HRV stable)

IMPACT ON GOALS
├── Sleep improvement → +15% productivity
├── Workouts → -20% stress
├── Activity → +1.2 points mood/10

NEXT WEEK
├── Maintain current routine (it's working)
├── Try adding meditation for stress (<4/10)
└── Push workouts to 5/week for even better results
```

### Alerts & Notifications

Configure health alerts:

**Sleep Alerts**:

- Alert if < 6.5 hours tonight
- Alert if sleep quality < 5/10
- Alert if bedtime shifts > 1 hour

**Workout Alerts**:

- Remind if no workout by 2pm
- Alert if weekly total < 4 hours by Friday
- Celebrate when hitting 5+ hours

**Heart Health Alerts**:

- Alert if resting heart rate up 10+ bpm
- Alert if HRV down 15+ points
- Suggest recovery day if recovery score low

**Energy Alerts**:

- Alert if 3+ days with low energy (< 5/10)
- Suggest sleep or workout increase
- Check if stress is high

---

## Wellness Scorecard Integration

Connect wellness metrics to goal alignment score.

### Wellness Impact on Goal Alignment

Each goal gets a **Wellness Multiplier**:

```
Base Goal Alignment Score: 75/100
├── Sleep Quality Bonus: +5 (if 7.5+ hours last night)
├── Exercise Consistency Bonus: +3 (if on track this week)
├── Nutrition Quality Bonus: +2 (if good meals today)
├── Stress/Mental Health Bonus: +5 (if stress <5)
└── Final Alignment Score: 90/100 (with wellness factors)
```

**Example**:

```
BUSINESS GOAL: Build $200K/year software business
├── Base alignment: 75/100
├── Sleep: 7.5h (full +5 bonus) = 80/100
├── Exercise: 4/5 days (+3 bonus) = 83/100
├── Nutrition: 7/10 (+2 bonus) = 85/100
├── Stress: 3/10 (+5 bonus) = 90/100
└── FINAL ALIGNMENT: 90/100 (Exceptional)
    → You're in peak condition for this goal this week
```

If wellness scores are low:

```
FINANCIAL GOAL: Same goal, poor wellness day
├── Base alignment: 75/100
├── Sleep: 5.5h (no bonus, -2 penalty) = 73/100
├── Exercise: 0/5 days (no bonus) = 73/100
├── Nutrition: 4/10 (-2 penalty) = 71/100
├── Stress: 8/10 (no bonus, -3 penalty) = 68/100
└── FINAL ALIGNMENT: 68/100 (Weak alignment)
    → Not a good day for this goal - low energy expected
    → Recommendation: Rest, recover, delay decision-making
```

---

## Data Storage

Wellness data is saved in:

**JSON File** (CLI):

```
.claude/data/wellness.json
├── Daily metrics (fitness, nutrition, sleep, mental)
├── Weekly summaries
├── Correlations (sleep vs. productivity, etc.)
├── Wearable data (if integrated)
└── Goal progress correlation
```

**PostgreSQL** (Analytics):

```
wellness_metrics table
├── date, metric_type (fitness/nutrition/sleep/mental)
├── value, target, quality_rating
├── related_goal_id
└── created_at, updated_at

correlations table
├── metric1, metric2 (e.g., sleep_hours vs. productivity)
├── correlation_coefficient (-1 to +1)
├── sample_size, time_period
└── updated_at
```

---

## Integration with Life Goals

Each wellness goal ladder backs to `/life:goals`:

```
LIFE GOAL: Health & Wellness (Wellness domain)
├── Fitness Objective: Run half-marathon by June
│   └── Requires: 5 hours/week training
│       └── Habit: Morning runs (6am, Mon/Wed/Fri)
│
├── Sleep Objective: Consistent 8-hour nights
│   └── Requires: 10:30pm bedtime, no screens
│       └── Habit: Evening wind-down (30 min tech-free)
│
├── Mental Health Objective: Reduce stress by 40%
│   └── Requires: Daily meditation 10+ minutes
│       └── Habit: Morning meditation (6:45am)
│
└── Supports:
    ├── Financial Independence (more energy for business)
    ├── Career Goal (better focus and decision-making)
    └── Relationships (more patience and presence)
```

---

## Success Criteria

**After 1 week of tracking:**

- ✅ Daily health metrics logged (fitness, nutrition, sleep, mental)
- ✅ Weekly summary completed
- ✅ Energy/productivity baseline established

**After 4 weeks of tracking:**

- ✅ Strong correlations identified (e.g., sleep → productivity)
- ✅ Wellness goals defined
- ✅ Top 2-3 high-impact actions identified

**After 12 weeks:**

- ✅ All wellness habits ingrained
- ✅ Wellness score 8+/10 consistently
- ✅ Clear evidence of goal progress acceleration
- ✅ Wearable data integrated and analyzed

**System Health**:

- ✅ Sleep: 7.5+ hours average (85%+ nights)
- ✅ Exercise: 5+ hours/week consistently
- ✅ Mental clarity: 8/10 average
- ✅ Stress: <5/10 on 75%+ days
- ✅ Goal alignment score boosted by wellness factors

---

## Integration with Other Commands

After optimizing wellness, use these commands:

- `/life:time` - Schedule protected time for exercise/sleep
- `/life:habits` - Create meditation, exercise, nutrition habits
- `/life:goals` - Link wellness progress to life goal achievement
- `/software-business:projects` - Measure productivity impact

---

## Tips for Success

**Week 1: Start Tracking**

- Log 4 health domains daily
- Don't worry about perfection, just data collection
- Identify baseline (current state)

**Week 2: Look for Patterns**

- Notice which days had high energy
- Identify what wellness factors were present
- Start hypothesizing (e.g., "More sleep = better work?")

**Week 3-4: Find Correlations**

- Test specific interventions
- Measure results (did that change help?)
- Identify your top 2-3 impact factors

**Month 2+: Optimize**

- Double down on high-impact actions
- Build habits for each
- Integrate wearable data for automatic tracking

**Ongoing**:

- Check correlations monthly
- Adjust based on what works for you
- Celebrate improvements
- Remember: small changes compound massively

---

## ROI & Impact

**Time Investment**: 10 minutes/day tracking (+ analysis time)
**Annual ROI**: $229,000

**Key ROI Drivers**:

1. **Higher productivity**: Better health = 30% more output = $125K/year
2. **Better decisions**: Clearer mind = fewer bad decisions = $50K/year
3. **Fewer sick days**: Better health = 5+ fewer sick days = $30K/year
4. **Accelerated goals**: Health boost → faster goal achievement = $24K/year
5. **Longevity value**: Health now = reduced future medical costs = $35K/year+ (lifetime)

**Wellness Bonus**:

- Every point improvement in wellness score = ~$3K/year additional impact
- 8/10 wellness (vs. 5/10) = +$9K/year in compounded value

---

**Created with the goal-centric life management system**
**Your health is your wealth - track it to unlock your potential**
