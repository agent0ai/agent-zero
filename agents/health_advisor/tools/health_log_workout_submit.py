"""Parse filled workout table, append to Exercise Progression, write section 06 in Today.md."""
import os
import re
from datetime import datetime

import importlib.util
from python.helpers.tool import Tool, Response

_tools_dir = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "_health_log_utils", os.path.join(_tools_dir, "_health_log_utils.py")
)
_utils = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_utils)
get_workdir_path = _utils.get_workdir_path
path_today_md = _utils.path_today_md
path_exercise_progression_md = _utils.path_exercise_progression_md
path_todays_routine_md = _utils.path_todays_routine_md


def _parse_fillable_table(content: str) -> list[dict]:
    """
    Parse fillable table: Exercise | Sets | Target Reps | Weight | Actual Reps | Notes
    Return list of {exercise, sets, target_reps, weight, actual_reps, notes}
    """
    rows = []
    # Skip header and separator
    for m in re.finditer(
        r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.*?)\s*\|",
        content,
        re.MULTILINE,
    ):
        ex = m.group(1).strip()
        sets = m.group(2).strip()
        target = m.group(3).strip()
        weight = m.group(4).strip()
        actual = m.group(5).strip()
        notes = m.group(6).strip()
        # Skip header/separator rows
        if ex.lower().startswith("exercise") or ex.startswith("-"):
            continue
        if not ex:
            continue
        rows.append({
            "exercise": ex,
            "sets": sets,
            "target_reps": target,
            "weight": weight,
            "actual_reps": actual,
            "notes": notes,
        })
    return rows


def _append_to_exercise_progression(ep_path: str, date_str: str, rows: list[dict]) -> None:
    """Append completed rows to Exercise Progression table."""
    with open(ep_path, "r", encoding="utf-8") as f:
        content = f.read()

    table_header = "| Exercise                              | Date        | Sets | Reps                  | Weight (kg/lb)      | Notes"
    idx = content.find(table_header)
    if idx == -1:
        idx = content.find("| Exercise")
    if idx == -1:
        raise ValueError("Exercise table not found")

    sep_idx = content.find("\n", idx) + 1
    insert_idx = content.find("\n", sep_idx) + 1

    new_rows = []
    for r in rows:
        sets = r.get("sets") or ""
        actual = r.get("actual_reps") or ""
        if not sets and not actual:
            continue
        reps = actual if actual else r.get("target_reps") or ""
        weight = r.get("weight") or ""
        notes = r.get("notes") or ""
        ex = r["exercise"][:38].ljust(38)
        dt = date_str[:10].ljust(10)
        st = sets[:6].ljust(6)
        rp = reps[:22].ljust(22)
        wt = weight[:20].ljust(20)
        nt = notes[:50]
        new_rows.append(f"| {ex} | {dt} | {st} | {rp} | {wt} | {nt} |\n")

    if not new_rows:
        return

    insert_content = "".join(new_rows)
    new_content = content[:insert_idx] + insert_content + content[insert_idx:]
    with open(ep_path, "w", encoding="utf-8") as f:
        f.write(new_content)


def _format_section_06(rows: list[dict], routine_label: str = "") -> str:
    """Format exercise summary for Today.md section 06."""
    completed = [r for r in rows if r.get("sets") or r.get("actual_reps")]
    if not completed:
        return "Pending."

    lines = []
    if routine_label:
        lines.append(f"**{routine_label}:**")
    for r in completed:
        ex = r["exercise"]
        sets = r.get("sets") or "-"
        reps = r.get("actual_reps") or r.get("target_reps") or ""
        weight = r.get("weight") or ""
        note = r.get("notes") or ""
        parts = [f"{sets}×{reps}" if reps else str(sets)]
        if weight:
            parts.append(f"@{weight}")
        if note:
            parts.append(f"({note})")
        lines.append(f"- {ex}: {' '.join(parts)}")
    return "\n".join(lines)


class HealthLogWorkoutSubmit(Tool):
    async def execute(
        self,
        workdir: str = "",
        filled_table_content: str = "",
        date_yyyymmdd: str = "",
        routine_label: str = "",
        use_todays_routine_file: bool = False,
        **kwargs,
    ):
        workdir_path = get_workdir_path(workdir)
        ep_path = path_exercise_progression_md(workdir_path)
        today_path = path_today_md(workdir_path)
        routine_path = path_todays_routine_md(workdir_path)

        if not os.path.exists(ep_path):
            return Response(
                message=f"Error: Exercise Progression.md not found at {ep_path}",
                break_loop=False,
            )
        if not os.path.exists(today_path):
            return Response(
                message=f"Error: Today.md not found at {today_path}",
                break_loop=False,
            )

        date_str = date_yyyymmdd or datetime.now().strftime("%Y-%m-%d")
        if len(date_str) == 8:
            date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

        if use_todays_routine_file and os.path.exists(routine_path):
            with open(routine_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Extract table from file
            table_start = content.find("| Exercise")
            if table_start == -1:
                return Response(
                    message="Error: Fillable table not found in Today's Routine.md",
                    break_loop=False,
                )
            table_end = content.find("\n\n", table_start)
            if table_end == -1:
                table_end = len(content)
            filled_table_content = content[table_start:table_end]

        if not filled_table_content or "|" not in filled_table_content:
            return Response(
                message="Error: filled_table_content required (markdown table) or use use_todays_routine_file=true",
                break_loop=False,
            )

        rows = _parse_fillable_table(filled_table_content)
        completed = [r for r in rows if r.get("sets") or r.get("actual_reps")]

        if not completed:
            return Response(
                message="Error: No completed rows (Sets or Actual Reps filled). Nothing to submit.",
                break_loop=False,
            )

        _append_to_exercise_progression(ep_path, date_str, completed)

        section_content = _format_section_06(completed, routine_label)

        # Write section 06 using health_log_section_write logic
        with open(today_path, "r", encoding="utf-8") as f:
            full = f.read()

        match = re.search(r"^## Exercise.*$", full, re.MULTILINE)
        if not match:
            return Response(
                message="Appended to Exercise Progression but section 06 header not found in Today.md",
                break_loop=False,
            )
        start = match.start()
        next_match = re.search(r"\n##? ", full[start + 3:])
        if next_match:
            end = start + 3 + next_match.start()
        else:
            end = len(full)

        new_section = f"## Exercise\n\n{section_content}\n\n"
        new_full = full[:start] + new_section + full[end:].lstrip()
        with open(today_path, "w", encoding="utf-8") as f:
            f.write(new_full)

        return Response(
            message=f"Submitted {len(completed)} exercises: updated Exercise Progression and Today.md section 06",
            break_loop=False,
        )
