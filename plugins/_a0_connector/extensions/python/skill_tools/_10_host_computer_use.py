from helpers.extension import Extension
from helpers.skill_tools import SkillTool
from plugins._a0_connector.helpers import ws_runtime


def _computer_use(**kwargs):
    from plugins._a0_connector.helpers.host_computer_use import ComputerUseRemote

    return ComputerUseRemote(**kwargs)


def _available(agent) -> bool:
    sid = ws_runtime.select_computer_use_target_sid(agent.context.id)
    metadata = ws_runtime.computer_use_metadata_for_sid(sid) if sid else None
    return bool(
        metadata
        and metadata.get("enabled")
        and str(metadata.get("status") or "").strip().lower() != "rearm required"
    )


_BINDING = SkillTool("_a0_connector", "host-computer-use", _computer_use, available=_available)


class RegisterHostComputerUse(Extension):
    def execute(self, bindings: dict, **kwargs):
        bindings["computer_use_remote"] = _BINDING
