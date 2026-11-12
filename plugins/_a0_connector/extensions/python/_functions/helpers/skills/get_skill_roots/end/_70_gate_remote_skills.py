from helpers import files
from helpers.extension import Extension
from plugins._a0_connector.helpers import ws_runtime


class GateRemoteSkills(Extension):
    def execute(self, data: dict, **kwargs):
        if not self.agent or not isinstance(data.get("result"), list):
            return

        candidates = ws_runtime.remote_tool_sids_for_context(self.agent.context.id)
        if any(
            metadata(sid) is not None
            for sid in candidates
            for metadata in (
                ws_runtime.remote_file_metadata_for_sid,
                ws_runtime.remote_exec_metadata_for_sid,
                ws_runtime.computer_use_metadata_for_sid,
                ws_runtime.host_browser_metadata_for_sid,
            )
        ):
            return

        root = files.get_abs_path("plugins", "_a0_connector", "skills")
        data["result"] = [path for path in data["result"] if path != root]
