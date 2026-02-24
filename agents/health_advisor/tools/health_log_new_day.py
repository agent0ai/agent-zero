"""Initialize Today.md for a new day. Sets header, Cycle Day, location, next measure date."""
import os
import importlib.util
from python.helpers.tool import Tool, Response

_tools_dir = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("_health_log_utils", os.path.join(_tools_dir, "_health_log_utils.py"))
_utils = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_utils)
get_workdir_path = _utils.get_workdir_path
path_today_md = _utils.path_today_md

TEMPLATE = """# Health Log {yyyymmdd}

**Date:** {date_readable}
**Cycle Day:** {cycle_day}
**Location:** {location}
**Next Measure Day:** {next_measure}

## Sleep (Pending)
- Bed time: Pending
- Final wake: Pending
- Additional sleep: Pending
- Total sleep: Pending

## Morning Notes
- Energy & Mood: Pending
- Body Weight / Comp: Pending (next measure {next_measure})
- Progress Photos: Pending (not routine day)
- Notes: Pending.

## Nutrition
**Daily Running Total:** Pending

### Morning Beverages
Pending.

### Post Workout Shake (in Sauna)
Pending.

### Lunch (~1400)
Pending.

### Dinner (~1830)
Pending.

### Evening Snack (~2100)
Pending.

## Macros Total (full day est)
**Pending kcal | P g C g F g**
- Protein: Pending g
- Fat: Pending g
- Carbs: Pending g
- Calories: Pending kcal

## Energy Delta
- Today's Delta: Pending
- 7-Day Average: Pending
- 7-Day Delta: Pending
- 14-Day Average: Pending
- 14-Day Delta: Pending

## Exercise
**Supersets:**
Pending.

## Activity Summary (Samsung Health – Full Day)
- Steps: Pending / 13,500 goal
- Active time: Pending / 90 min goal
- Activity calories: Pending / 800 goal
- Total burned calories: Pending
- Distance (active): Pending km
- Floors: Pending
- Exercise time: Pending min

## Supplements / Medication
**Full Day Pack:**
Pending.

## Notes
Pending: Gut status?, Hunger?, Activity details?

## Monitoring Closely (Propecia / Hair)
- Hair thinning: Pending
- Hernia pain: Pending

## Day Closure
Pending.
"""


def _format_date(yyyymmdd: str) -> str:
    """Convert 20260224 -> Sunday, February 24, 2026"""
    try:
        from datetime import datetime
        dt = datetime.strptime(yyyymmdd, "%Y%m%d")
        return dt.strftime("%A, %B %d, %Y")
    except Exception:
        return yyyymmdd


class HealthLogNewDay(Tool):
    async def execute(
        self,
        workdir: str = "",
        date_yyyymmdd: str = "",
        cycle_day: str = "1",
        location: str = "",
        next_measure: str = "",
        **kwargs,
    ):
        if not date_yyyymmdd or len(date_yyyymmdd) != 8:
            return Response(
                message="Error: date_yyyymmdd required (YYYYMMDD)",
                break_loop=False,
            )

        workdir_path = get_workdir_path(workdir)
        today_path = path_today_md(workdir_path)

        date_readable = _format_date(date_yyyymmdd)
        next_measure = next_measure or date_yyyymmdd

        content = TEMPLATE.format(
            yyyymmdd=date_yyyymmdd,
            date_readable=date_readable,
            cycle_day=cycle_day,
            location=location or "Pending",
            next_measure=next_measure,
        )

        os.makedirs(os.path.dirname(today_path), exist_ok=True)
        with open(today_path, "w", encoding="utf-8") as f:
            f.write(content)

        return Response(
            message=f"Initialized Today.md for {date_yyyymmdd} (Cycle Day {cycle_day})",
            break_loop=False,
        )
