"""Write or replace a section in Today.md. Section 0-11 per HealthLogRules."""
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

# Section headers that may appear (0-11)
SECTION_PATTERNS = {
    0: [r"# Health Log \d{8}", r"## Date"],
    1: [r"## Sleep"],
    2: [r"## Morning Notes"],
    3: [r"## Nutrition"],
    4: [r"## Macros Total", r"### Macros Total"],
    5: [r"## Energy Delta"],
    6: [r"## Exercise"],
    7: [r"## Activity Summary"],
    8: [r"## Supplements", r"## Supplements / Medication", r"## Supplements/Medication"],
    9: [r"## Notes"],
    10: [r"## Monitoring Closely"],
    11: [r"## Day Closure"],
}


class HealthLogSectionWrite(Tool):
    async def execute(
        self,
        workdir: str = "",
        section_number: int = 0,
        content: str = "",
        **kwargs,
    ):
        if section_number not in SECTION_PATTERNS:
            return Response(
                message="Error: section_number must be 0-11",
                break_loop=False,
            )

        workdir_path = get_workdir_path(workdir)
        today_path = path_today_md(workdir_path)

        if not os.path.exists(today_path):
            return Response(
                message=f"Error: Today.md not found at {today_path}",
                break_loop=False,
            )

        with open(today_path, "r", encoding="utf-8") as f:
            full = f.read()

        patterns = SECTION_PATTERNS[section_number]
        pattern = "|".join(patterns)
        match = re.search(rf"^({pattern}).*$", full, re.MULTILINE)
        if not match:
            return Response(
                message=f"Error: Section {section_number} header not found in Today.md",
                break_loop=False,
            )

        start = match.start()
        # Find next ## or ### header
        next_match = re.search(r"\n##? ", full[start + 3 :])
        if next_match:
            end = start + 3 + next_match.start()
        else:
            end = len(full)

        # Content may include header or not; ensure we have section body
        new_section = content.strip()
        if not new_section.startswith("#"):
            # Prepend the matched header
            matched_header = match.group(1).strip()
            new_section = f"{matched_header}\n\n{new_section}"
        new_section = new_section.rstrip() + "\n\n"
        new_full = full[:start] + new_section + full[end:].lstrip()

        with open(today_path, "w", encoding="utf-8") as f:
            f.write(new_full)

        size = len(new_full)
        return Response(
            message=f"Updated section {section_number} in Today.md ({size} bytes)",
            break_loop=False,
        )
