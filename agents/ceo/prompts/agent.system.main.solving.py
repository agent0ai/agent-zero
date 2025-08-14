from typing import Any
from python.helpers.files import VariablesPlugin, get_subdirectories, read_file, exists
from python.helpers import settings


class CeoSolvingVariables(VariablesPlugin):
    def get_variables(self, file: str, backup_dirs: list[str] | None = None) -> dict[str, Any]:
        current = settings.get_settings()

        # Collect names from settings profiles and agent folders
        settings_profile_names = ["default"] + list(current.get("settings_profiles", {}).keys())
        agent_folder_names = [
            name for name in get_subdirectories("agents") if name and name != "_example"
        ]

        # Union of names
        all_names = sorted({*settings_profile_names, *agent_folder_names})

        # Utilities
        def read_context_for_agent(agent_name: str) -> str:
            try:
                ctx_rel = f"agents/{agent_name}/_context.md"
                if exists(ctx_rel):
                    content = read_file(ctx_rel)
                    return content.strip()
            except Exception:
                pass
            return ""

        def summarize(text: str, max_len: int = 200) -> str:
            if not text:
                return ""
            one_line = " ".join(text.split())
            return one_line[: max_len - 1] + ("…" if len(one_line) > max_len else "")

        # Build list lines with description selection logic
        lines_list: list[str] = []
        base_default_agent = current.get("agent_profile", "agent0") or "agent0"

        for name in all_names:
            # Case 1: If an agent folder with this exact name exists, use its _context.md
            if name in agent_folder_names:
                desc = summarize(read_context_for_agent(name))
                lines_list.append(f"- {name}{(": " + desc) if desc else ''}")
                continue

            # Case 2: Name exists only as a settings profile
            if name in settings_profile_names:
                if name == "default":
                    # Use the agent profile set in base settings
                    agent_for_profile = base_default_agent
                else:
                    # Use the agent_profile referenced by this settings profile if present, else fall back to base default
                    overrides = current.get("settings_profiles", {}).get(name, {})
                    agent_for_profile = overrides.get("agent_profile") or base_default_agent
                # Read description from that agent profile's _context.md
                desc = summarize(read_context_for_agent(agent_for_profile))
                lines_list.append(f"- {name}{(": " + desc) if desc else ''}")

        # Join lines
        lines = "\n".join(lines_list)
        return {
            "agent_profiles": lines,
        }
