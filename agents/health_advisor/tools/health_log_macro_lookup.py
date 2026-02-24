"""Look up macro (kcal | P C F) for an item from MacrosAndRecipes.md. Fuzzy match, return 'Did you mean?' if ambiguous."""
import os
import re
import importlib.util
from python.helpers.tool import Tool, Response

_tools_dir = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("_health_log_utils", os.path.join(_tools_dir, "_health_log_utils.py"))
_utils = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_utils)
get_workdir_path = _utils.get_workdir_path
path_macros_md = _utils.path_macros_md


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower().strip())


def _parse_macros_line(line: str) -> tuple[str, str] | None:
    """Parse line like '- item: Xkcal | PXg CXg FXg' or '- per 5g: 20kcal | P5g C0g F0g'. Returns (item_key, macro_str)."""
    line = line.strip()
    if not line.startswith("-"):
        return None
    line = line.lstrip("- ").strip()
    if ":" not in line:
        return None
    parts = line.split(":", 1)
    item = parts[0].strip()
    rest = parts[1].strip()
    # Match kcal | P C F pattern
    if "kcal" in rest.lower() and "|" in rest:
        return (item, rest)
    return None


class HealthLogMacroLookup(Tool):
    async def execute(
        self,
        workdir: str = "",
        item_name: str = "",
        serving_size: str = "",
        **kwargs,
    ):
        if not item_name or not str(item_name).strip():
            return Response(
                message="Error: item_name required (e.g. 'Post Workout Shake', 'Hydrolyzed Collagen')",
                break_loop=False,
            )

        workdir_path = get_workdir_path(workdir)
        macros_path = path_macros_md(workdir_path)

        if not os.path.exists(macros_path):
            return Response(
                message=f"Error: MacrosAndRecipes.md not found at {macros_path}",
                break_loop=False,
            )

        with open(macros_path, "r", encoding="utf-8") as f:
            content = f.read()

        query = _normalize(item_name)
        items: list[tuple[str, str]] = []
        current_item = None

        for line in content.split("\n"):
            parsed = _parse_macros_line(line)
            if parsed:
                key, macro = parsed
                key_norm = _normalize(key)
                items.append((key, macro))
                if key_norm == query:
                    # Exact match
                    return Response(
                        message=f"**{key}**: {macro}",
                        break_loop=False,
                    )

        # Fuzzy match: query as substring
        matches = [(k, m) for k, m in items if query in _normalize(k)]
        if len(matches) == 1:
            k, m = matches[0]
            return Response(message=f"**{k}**: {m}", break_loop=False)
        if len(matches) > 1:
            options = "\n".join(f"- {k}: {m}" for k, m in matches)
            return Response(
                message=f"Did you mean?\n{options}\n\n(Or say 'Record new item' to add.)",
                break_loop=False,
            )

        # No match
        return Response(
            message=f"No match for '{item_name}'. Record new item in MacrosAndRecipes.md.",
            break_loop=False,
        )
