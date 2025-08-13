from typing import Any
from python.helpers.files import VariablesPlugin
from python.helpers import settings


class CallSubordinateVariables(VariablesPlugin):
    def get_variables(self, file: str, backup_dirs: list[str] | None = None) -> dict[str, Any]:
        current = settings.get_settings()
        profiles = ["default"] + list(current.get("settings_profiles", {}).keys())
        # unique and sorted
        profiles = sorted({p for p in profiles if p})
        lines = "\n".join(f"- {p}" for p in profiles)
        return {
            "agent_profiles": lines,
        }
