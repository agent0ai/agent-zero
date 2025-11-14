from initialize import initialize_agent
from python.helpers import dirty_json, files
from python.helpers.extension import Extension


class LoadProfileSettings(Extension):
    
    async def execute(self, **kwargs) -> None:

        if not self.agent or not self.agent.config.profile:
            return

        settings_path = files.get_abs_path("agents", self.agent.config.profile, "settings.json")
        if files.exists(settings_path):
            try:
                override_settings_str = files.read_file(settings_path)
                override_settings = dirty_json.parse(override_settings_str)

                if isinstance(override_settings, dict):
                    # Preserve the original memory_subdir unless it's explicitly overridden
                    current_memory_subdir = self.agent.config.memory_subdir

                    new_config = initialize_agent(override_settings=override_settings)

                    if (
                        "agent_memory_subdir" not in override_settings
                        and current_memory_subdir != "default"
                    ):
                        new_config.memory_subdir = current_memory_subdir

                    self.agent.config = new_config

                    self.agent.context.log.log(
                        type="info",
                        content=(
                            "Loaded custom settings for agent "
                            f"{self.agent.number} with profile '{self.agent.config.profile}'."
                        ),
                    )
                else:
                    raise Exception(
                        f"Subordinate settings in {settings_path} "
                        "must be a JSON object."
                    )

            except Exception as e:
                self.agent.context.log.log(
                    type="error",
                    content=(
                        "Error loading subordinate settings for "
                        f"profile '{self.agent.config.profile}': {e}"
                    ),
                )
