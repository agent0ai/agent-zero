from helpers.extension import Extension
from plugins._browser.helpers.runtime import close_all_runtimes_sync


class StopBrowserOnDisable(Extension):
    def execute(self, data: dict, **kwargs):
        args = data.get("args", ())
        values = dict(zip(("plugin_name", "enabled", "project_name", "agent_profile"), args))
        values.update(data.get("kwargs", {}))
        if (
            values.get("plugin_name") == "_browser"
            and values.get("enabled") is False
            and not values.get("project_name")
            and not values.get("agent_profile")
        ):
            close_all_runtimes_sync()
