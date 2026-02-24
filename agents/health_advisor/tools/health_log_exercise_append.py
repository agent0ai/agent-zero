"""Append a row to Exercise Progression table in Exercise Progression.md."""
import os
import re
from python.helpers.tool import Tool, Response

import importlib.util
_tools_dir = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("_health_log_utils", os.path.join(_tools_dir, "_health_log_utils.py"))
_utils = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_utils)
path_exercise_progression_md = _utils.path_exercise_progression_md
get_workdir_path = _utils.get_workdir_path


class HealthLogExerciseAppend(Tool):
    async def execute(
        self,
        workdir: str = "",
        exercise_name: str = "",
        date_yyyymmdd: str = "",
        sets: str = "",
        reps: str = "",
        weight: str = "",
        notes: str = "",
        **kwargs,
    ):
        if not exercise_name or not date_yyyymmdd:
            return Response(
                message="Error: exercise_name and date_yyyymmdd required",
                break_loop=False,
            )

        dt = str(date_yyyymmdd).strip()
        if len(dt) == 8:
            dt = f"{dt[:4]}-{dt[4:6]}-{dt[6:8]}"

        workdir_path = get_workdir_path(workdir)
        ep_path = path_exercise_progression_md(workdir_path)

        if not os.path.exists(ep_path):
            return Response(
                message=f"Error: Exercise Progression.md not found at {ep_path}",
                break_loop=False,
            )

        with open(ep_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Find the table - look for | Exercise | row
        table_header = "| Exercise                              | Date        | Sets | Reps                  | Weight (kg/lb)      | Notes"
        if table_header not in content:
            # Try alternate header
            table_header = "| Exercise"
        idx = content.find(table_header)
        if idx == -1:
            return Response(message="Error: Exercise table not found in file", break_loop=False)

        # Find separator line, then insert after it (most recent first)
        sep_idx = content.find("\n", idx) + 1
        insert_idx = content.find("\n", sep_idx) + 1

        # Format row - pad columns to align
        ex = str(exercise_name)[:38].ljust(38)
        dt_pad = dt[:10].ljust(10)
        st = str(sets)[:6].ljust(6)
        rp = str(reps)[:22].ljust(22)
        wt = str(weight)[:20].ljust(20)
        nt = str(notes)[:50]
        row = f"| {ex} | {dt_pad} | {st} | {rp} | {wt} | {nt} |\n"

        new_content = content[:insert_idx] + row + content[insert_idx:]
        with open(ep_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return Response(
            message=f"Appended {exercise_name} to Exercise Progression",
            break_loop=False,
        )
