"""Parse health_log_archives, compute Today's Delta, 7-Day Avg/Delta, 14-Day Avg/Delta per HealthLogRules."""
import os
import re
import importlib.util
from python.helpers.tool import Tool, Response

_tools_dir = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("_health_log_utils", os.path.join(_tools_dir, "_health_log_utils.py"))
_utils = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_utils)
get_workdir_path = _utils.get_workdir_path
path_today_md = _utils.path_today_md
path_archives_dir = _utils.path_archives_dir


def _parse_int_from_text(text: str) -> int | None:
    """Extract first integer from text (handles commas, negatives)."""
    m = re.search(r"-?\d[\d,]*", text.replace(",", ""))
    return int(m.group(0)) if m else None


def _parse_range_midpoint(text: str) -> int | None:
    """Parse '~2,050–2,150' or '2,050-2,150' -> midpoint."""
    nums = re.findall(r"\d[\d,]*", text.replace(",", ""))
    if len(nums) >= 2:
        try:
            a, b = int(nums[0]), int(nums[1])
            return (a + b) // 2
        except ValueError:
            pass
    if len(nums) == 1:
        try:
            return int(nums[0])
        except ValueError:
            pass
    return None


def _parse_archive_md(path: str) -> tuple[int | None, int | None]:
    """Parse archive: return (intake_kcal, burn_kcal)."""
    if not os.path.exists(path):
        return None, None
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    intake = None
    burn = None
    in_macros = False
    in_activity = False
    for line in content.split("\n"):
        if "## Macros Total" in line or "### Macros Total" in line:
            in_macros = True
            in_activity = False
        elif "## Activity Summary" in line:
            in_activity = True
            in_macros = False
        if in_macros and ("Calories:" in line or "kcal" in line) and "Notes" not in line:
            v = _parse_range_midpoint(line) or _parse_int_from_text(line)
            if v is not None and 100 < v < 10000:
                intake = v
        if in_activity and "Total burned" in line:
            v = _parse_int_from_text(line)
            if v is not None and 500 < v < 5000:
                burn = v
    return intake, burn


def _parse_today_md(path: str) -> tuple[int | None, int | None]:
    """Parse Today.md for today's intake and burn."""
    return _parse_archive_md(path)


class HealthLogEnergyDelta(Tool):
    async def execute(self, workdir: str = "", **kwargs):
        workdir_path = get_workdir_path(workdir)
        today_path = path_today_md(workdir_path)
        archives_dir = path_archives_dir(workdir_path)

        if not os.path.exists(archives_dir):
            return Response(
                message="Error: health_log_archives/ not found",
                break_loop=False,
            )

        # Collect archives: (date_str, intake, burn)
        archive_data: list[tuple[str, int, int]] = []
        for fname in os.listdir(archives_dir):
            if not fname.endswith(".md") or "Health Log" not in fname:
                continue
            m = re.search(r"(\d{8})", fname)
            if not m:
                continue
            date_str = m.group(1)
            path = os.path.join(archives_dir, fname)
            intake, burn = _parse_archive_md(path)
            if intake is not None and burn is not None:
                archive_data.append((date_str, intake, burn))

        archive_data.sort(key=lambda x: x[0], reverse=True)

        # Today's intake/burn from Today.md
        today_intake, today_burn = _parse_today_md(today_path)
        today_delta = None
        if today_intake is not None and today_burn is not None:
            today_delta = today_intake - today_burn

        # 7-day and 14-day from archives
        last7 = archive_data[:7]
        last14 = archive_data[:14]

        def _avg_delta(items: list) -> tuple[float | None, int | None]:
            if not items:
                return None, None
            deltas = [i - b for _, i, b in items]
            avg = sum(deltas) / len(deltas)
            total = sum(deltas)
            return avg, total

        avg7, delta7 = _avg_delta(last7)
        avg14, delta14 = _avg_delta(last14)

        out = ["## Energy Delta"]
        out.append(f"- Today's Delta: {today_delta if today_delta is not None else 'Pending'} kcal")
        out.append(f"- 7-Day Average: {f'{avg7:.0f}' if avg7 is not None else 'Pending'} kcal/day")
        out.append(f"- 7-Day Delta: {delta7 if delta7 is not None else 'Pending'} kcal")
        out.append(f"- 14-Day Average: {f'{avg14:.0f}' if avg14 is not None else 'Pending'} kcal/day")
        out.append(f"- 14-Day Delta: {delta14 if delta14 is not None else 'Pending'} kcal")
        if last7:
            dates = [d[0] for d in last7]
            out.append(f"\n(based on {len(last7)} archived days: {dates[0]}–{dates[-1]})")

        return Response(message="\n".join(out), break_loop=False)
