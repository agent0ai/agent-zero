"""Build Today's Routine.md from a named routine or freestyle (all exercises)."""
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
path_exercise_progression_md = _utils.path_exercise_progression_md
path_todays_routine_md = _utils.path_todays_routine_md


def _parse_exercise_table(content: str) -> dict:
    """Parse Exercise Progression table; return {exercise_name: (date, sets, reps, weight, notes)}."""
    rows = {}
    # Match table rows: | Exercise | Date | Sets | Reps | Weight | Notes |
    for m in re.finditer(
        r"^\|\s*(.+?)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.*?)\s*\|",
        content,
        re.MULTILINE,
    ):
        ex = m.group(1).strip()
        dt = m.group(2)
        sets = m.group(3).strip()
        reps = m.group(4).strip()
        weight = m.group(5).strip()
        notes = m.group(6).strip()
        # Keep most recent per exercise
        if ex not in rows or dt > rows[ex][0]:
            rows[ex] = (dt, sets, reps, weight, notes)
    return rows


def _parse_routine_block(content: str, routine_name: str) -> list[tuple[str, str]]:
    """
    Find routine by name (case-insensitive partial match), return list of (sets_reps, exercise_name).
    Bullets like: "5×~12 Incline DB press + bent-over supported DB rows"
    """
    routine_name = (routine_name or "").strip().lower()
    if not routine_name:
        return []

    # Find "Routine Name: X" blocks
    block_re = re.compile(r"Routine Name:\s*(.+?)(?:\s*\([^)]*\))?\s*$", re.MULTILINE)
    bullet_re = re.compile(r"^-\s+(.+)$", re.MULTILINE)

    blocks = list(block_re.finditer(content))
    for i, block_match in enumerate(blocks):
        name_part = block_match.group(1).strip().lower()
        if routine_name in name_part or name_part in routine_name:
            # This is our routine; content until next Routine Name or ##
            start = block_match.end()
            end = len(content)
            for next_block in blocks[i + 1 :]:
                if next_block.start() > start:
                    end = next_block.start()
                    break
            # Also stop at ## Section
            section_match = re.search(r"\n##\s+", content[start:end])
            if section_match:
                end = start + section_match.start()

            block_text = content[start:end]
            result = []
            for line in block_text.splitlines():
                m = bullet_re.match(line.strip())
                if not m:
                    continue
                bullet = m.group(1).strip()
                # Parse "5×~12 Incline DB press + bent-over supported DB rows"
                prefix_match = re.match(r"^(\d+[×x]\S+)\s+(.+)$", bullet)
                if prefix_match:
                    sets_reps = prefix_match.group(1)
                    rest = prefix_match.group(2)
                else:
                    sets_reps = ""
                    rest = bullet
                # Split by " + " for supersets
                for ex in re.split(r"\s+\+\s+", rest):
                    ex = ex.strip()
                    if ex:
                        result.append((sets_reps, ex))
            return result
    return []


def _normalize_exercise_name(name: str) -> str:
    """Normalize for fuzzy matching (lowercase, collapse spaces)."""
    return " ".join(name.lower().split())


def _best_match(exercise: str, table: dict) -> tuple | None:
    """Find best matching row in table by exercise name."""
    ex_norm = _normalize_exercise_name(exercise)
    # Exact match first
    for k, v in table.items():
        if _normalize_exercise_name(k) == ex_norm:
            return (k, v)
    # Partial match (ex in key or key in ex)
    for k, v in table.items():
        kn = _normalize_exercise_name(k)
        if ex_norm in kn or kn in ex_norm:
            return (k, v)
    return None


def _build_fillable_table(
    exercises: list[tuple[str, str]], table: dict, date_str: str
) -> str:
    """Build markdown table: Exercise | Sets | Target Reps | Weight | Actual Reps | Notes."""
    lines = [
        "| Exercise                              | Sets | Target Reps | Weight (kg/lb)      | Actual Reps | Notes |",
        "|---------------------------------------|------|-------------|---------------------|-------------|-------|",
    ]
    for sets_reps, ex_name in exercises:
        match = _best_match(ex_name, table)
        if match:
            key, (_, sets, reps, weight, notes) = match
            target = sets_reps if sets_reps else reps
        else:
            key = ex_name
            target = sets_reps or "-"
            sets = ""
            reps = ""
            weight = ""
            notes = ""
        ex_pad = key[:38].ljust(38)
        st_pad = str(sets)[:6].ljust(6)
        rp_pad = str(target)[:22].ljust(22)
        wt_pad = str(weight)[:20].ljust(20)
        lines.append(f"| {ex_pad} | {st_pad} | {rp_pad} | {wt_pad} |             |       |")
    return "\n".join(lines)


class HealthLogRoutineBuild(Tool):
    async def execute(
        self,
        workdir: str = "",
        routine_name: str = "",
        date_yyyymmdd: str = "",
        session_notes: str = "",
        **kwargs,
    ):
        workdir_path = get_workdir_path(workdir)
        ep_path = path_exercise_progression_md(workdir_path)
        routine_path = path_todays_routine_md(workdir_path)

        if not os.path.exists(ep_path):
            return Response(
                message=f"Error: Exercise Progression.md not found at {ep_path}",
                break_loop=False,
            )

        date_str = date_yyyymmdd or datetime.now().strftime("%Y-%m-%d")
        if len(date_str) == 8:
            date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

        with open(ep_path, "r", encoding="utf-8") as f:
            content = f.read()

        table = _parse_exercise_table(content)

        if routine_name and routine_name.strip():
            exercises = _parse_routine_block(content, routine_name)
            if not exercises:
                return Response(
                    message=f"Error: Routine '{routine_name}' not found in Exercise Progression.md",
                    break_loop=False,
                )
            routine_label = routine_name.strip()
            notes_section = f"## {routine_label} Notes\n- Fill the table during your session\n- Record actual reps and notes for each exercise\n"
        else:
            # Freestyle: use all unique exercises from table, most recent first
            seen = set()
            exercises = []
            for ex in sorted(table.keys(), key=lambda x: table[x][0], reverse=True):
                ex_norm = _normalize_exercise_name(ex)
                if ex_norm not in seen:
                    seen.add(ex_norm)
                    _, sets, reps, weight, _ = table[ex]
                    exercises.append((f"{sets}×{reps}" if sets and reps else "", ex))
            routine_label = "Freestyle Session"
            notes_section = (
                "## Freestyle Session Notes\n"
                "- No specific routine — free styling today\n"
                "- Fill the table with all exercises you perform\n"
                "- Use latest weights from Exercise Progression.md as starting reference\n"
                "- Record actuals for every exercise completed\n"
                "- Sauna optional post-workout\n"
            )

        table_md = _build_fillable_table(exercises, table, date_str)

        body = f"""# Today's Routine.md

# {date_str} – {routine_label}

Date: {date_str}
Session time: Pending
Feeling: Pending

{notes_section}

## Fillable Table for Today's Session

{table_md}

## Notes
- Fill Actual Reps and Notes during session
- Report completed table back for Exercise Progression update
"""
        with open(routine_path, "w", encoding="utf-8") as f:
            f.write(body)

        return Response(
            message=f"Built Today's Routine.md with {len(exercises)} exercises ({routine_label})",
            break_loop=False,
        )
