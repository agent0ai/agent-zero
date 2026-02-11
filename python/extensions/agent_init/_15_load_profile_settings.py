from initialize import initialize_agent
from python.helpers import dirty_json, files, projects, subagents
from python.helpers.extension import Extension


class LoadProfileSettings(Extension):
    async def execute(self, **kwargs) -> None:

        if not self.agent or not self.agent.config.profile:
            return

        config_files = subagents.get_paths(
            self.agent, "settings.json", include_default=False, include_user=False
        )
        settings_override = {}
        for settings_path in config_files:
            if files.exists(settings_path):
                try:
                    override_settings_str = files.read_file(settings_path)
                    override_settings = dirty_json.try_parse(override_settings_str)
                    if isinstance(override_settings, dict):
                        settings_override.update(override_settings)
                    else:
                        raise Exception(
                            f"Subordinate settings in {settings_path} must be a JSON object."
                        )
                except Exception as e:
                    self.agent.context.log.log(
                        type="error",
                        content=(
                            f"Error loading subordinate settings from {settings_path} for "
                            f"profile '{self.agent.config.profile}': {e}"
                        ),
                    )

        if settings_override:
            current_config = self.agent.config
            new_config = initialize_agent(override_settings=settings_override)

            for override_key, config_attr in (
                ("agent_profile", "profile"),
                ("agent_memory_subdir", "memory_subdir"),
                ("mcp_servers", "mcp_servers"),
                ("browser_http_headers", "browser_http_headers"),
            ):
                if override_key not in settings_override:
                    setattr(
                        new_config, config_attr, getattr(current_config, config_attr)
                    )
            self.agent.config = new_config
            # self.agent.context.log.log(
            #     type="info",
            #     content=(
            #         "Loaded custom settings for agent "
            #         f"{self.agent.number} with profile '{self.agent.config.profile}'."
            #     ),
            # )
