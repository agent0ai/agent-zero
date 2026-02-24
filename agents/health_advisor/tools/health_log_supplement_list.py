"""Read Supplements.md and format as section 08 (Supplements/Medication) for health log."""
import os
import importlib.util
from python.helpers.tool import Tool, Response

_tools_dir = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("_health_log_utils", os.path.join(_tools_dir, "_health_log_utils.py"))
_utils = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_utils)
get_workdir_path = _utils.get_workdir_path
path_supplements_md = _utils.path_supplements_md


class HealthLogSupplementList(Tool):
    async def execute(self, workdir: str = "", **kwargs):
        workdir_path = get_workdir_path(workdir)
        supplements_path = path_supplements_md(workdir_path)

        if not os.path.exists(supplements_path):
            return Response(
                message=f"Error: Supplements.md not found at {supplements_path}",
                break_loop=False,
            )

        with open(supplements_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse Day Pack, Night Pack, Other sections - extract Supplement: # cap mg Dosage only
        lines = content.split("\n")
        sections = {"Day Pack": [], "Night Pack": [], "Other": []}
        current_section = None

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith("#"):
                continue
            if "## Day Pack" in line or "Day Pack (morning" in line:
                current_section = "Day Pack"
                continue
            if "## Night Pack" in line or "Night Pack (evening" in line:
                current_section = "Night Pack"
                continue
            if "## Conditional" in line or "## Notes" in line or "## Other" in line:
                current_section = "Other"
                continue
            if current_section and line_stripped.startswith("-"):
                # Parse: - Supplement: X cap (Y mg) or - Supplement: X g
                item = line_stripped.lstrip("- ").strip()
                if ":" in item and not item.lower().startswith("note"):
                    sections[current_section].append(item)

        # Build output
        out_lines = ["## Supplements / Medication", "**Full Day Pack:**", ""]
        if sections["Day Pack"]:
            out_lines.append("**Day Pack**")
            for item in sections["Day Pack"]:
                out_lines.append(f"- {item}")
            out_lines.append("")
        if sections["Night Pack"]:
            out_lines.append("**Night Pack**")
            for item in sections["Night Pack"]:
                out_lines.append(f"- {item}")
            out_lines.append("")
        if sections["Other"]:
            out_lines.append("**Other**")
            for item in sections["Other"]:
                out_lines.append(f"- {item}")

        result = "\n".join(out_lines) if any(sections.values()) else "No supplements parsed."
        return Response(message=result, break_loop=False)
