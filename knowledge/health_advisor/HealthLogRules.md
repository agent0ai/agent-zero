# HealthLogRules.md – Health Log Template & Rules

Last Updated: February 21, 2026

## Purpose
This file defines the exact structure, format, and rules for all health logs.
- Current in-progress log: **Today.md** (always in root)
- Archived at end of day: **Health Log YYYYMMDD.md** (in /health_log_archives/)
- All logs follow this template exactly for consistency and easy parsing.
- Use questions to obtain necessary data at appropriate times during the day according to the data required
 ## Macro Determination
- If supplied with photo of food, perform best estimatation, if the food item is given a name by user, record the estimation in MacrosAndRecipes.md by that name
- If that name is already recorded, ask if it should be updated or if the recorded item should be used
- When supplied with a reference to a specific intake item, check MacrosAndRecipes.md for previous record of item
- When looking up an item in MacrosAndRecipes.md and it's a fuzzy match or multiple items might fit, present a multiple choice "Did you mean?" An option should be "Record new item"

## Core Rules
1. **Date & Header**
   - Title: `# Health Log YYYYMMDD` (e.g., 20260111)
   - Subheader: e.g., `## Sleep (Jan 10 → Jan 11)`

2. **Sleep**
   - Bed time, final wake, sleep time per period, total sleep time notes (wakes, naps if noted, quality, recovery)

3. **Morning Notes**
   - Energy & Mood - ask if not provided during initializing a new day
   - Body Weight / Comp / Progress Photos / Hair Photos **(only present poke/measure days only: Mon/Thu, otherwise 'Next Measure Day: DATE')** (if measured)
   - Notes (cycle day, location, gut status, etc.)

4. **Nutrition**
   - List meals/snacks in order (Morning, Afternoon, Evening, etc.)
   - Include macros (estimated) for each
   - Total macros at end

5. **Macros Total (running total with each nutrition entry throughout day)**
   - Protein / Fat / Carbs / Calories
   - Notes (e.g., high-protein, recovery focus)

6. **Energy Delta**
    - Today's Delta: +/- X kcal (intake range mid vs burn)
    - 7-Day Average: Y kcal/day (average daily delta over last 7 closed days)
    - 7-Day Delta: Z kcal (cumulative surplus/deficit over last 7 days)
    - 14-Day Average: W kcal/day (average over last 14 closed days)
    - 14-Day Delta: V kcal (cumulative over last 14 days)

    Rules:
    - Use midpoints of any intake/burn ranges for calculations
    - Today's Delta is pending/estimated during the day
    - On day closure, fetch last 7 and 14 days from /health_log_archives/Health%20Log%20YYYYMMDD.md
    - If fewer than 7/14 days available, note “(based on X available days)” or “pending more data”
    - If burn or intake is missing/pending in an archive, exclude that day and note why
    - Always use actual archived totals — never invent or estimate historical values
    - Always quote or reference the exact archived files used for each calculation in a small inline note (e.g., ‘based on Feb 1–Feb 6 + Jan 31’) so Peretz can verify.

7. **Exercise**
   - Feeling, notes
   - Completed supersets or exercises with reps/weights
   - Sauna, other activity

8. **Activity Summary (Samsung Health – Full Day)**
   - Samsung activity will be provided before day closure
   - Steps, active time, activity calories, total burned, distance, exercise time, workout calories
   - Notes (e.g., light walk, recovery day)

9. **Supplements/Medication**
   - List all taken (Day Pack, Night Pack, creatine, Optalgin, etc.)

10. **Notes**
    - Today: [weekday, date]
    - Gear: Cycle day XX
    - Next poke/measure: [date]
    - Gut status
    - Hunger
    - Activity summary

11. **Monitoring Closely**
    - Hernia pain
    - Hair thinning (Propecia status)
    - Gut distress (if any)

12. **General Guidelines**
    - Updates via email/other: Update Today.md if health log related (e.g., exercise).
    - Use markdown code blocks for full log output when updating.
    - Macros are estimated — note when approximate.
    - Archive Today.md to health_log_archives/ at end of day (rename to Health Log YYYYMMDD.md).
    - Never invent or assume values — use only provided data.
    - When user pastes previous log or data, update from there.

This file is the single source of truth for log structure.
Reference this before creating or updating any health log.

**Note:** acv lemonade includes half lemon with pulp *(20kcal | P:0.5g C:5g F:0g)* – log per-lineitem.