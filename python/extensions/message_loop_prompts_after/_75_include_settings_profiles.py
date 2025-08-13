from python.helpers.extension import Extension
from agent import LoopData
from python.helpers import settings


class IncludeSettingsProfiles(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        # Collect available settings profiles including 'default'
        current = settings.get_settings()
        profiles = ["default"] + list(current.get("settings_profiles", {}).keys())
        profiles_sorted = sorted(set([p for p in profiles if p]))
        # As comma-separated and newline list variants
        csv = ", ".join(profiles_sorted)
        lines = "\n".join(f"- {p}" for p in profiles_sorted)
        loop_data.extras_temporary["agent_profiles"] = lines
        loop_data.extras_temporary["settings_profiles"] = lines
        loop_data.extras_temporary["settings_profiles_csv"] = csv
