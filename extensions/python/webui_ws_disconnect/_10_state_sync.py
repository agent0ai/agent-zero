from helpers.extension import Extension
from helpers.print_style import PrintStyle
from helpers.state_monitor import get_state_monitor, _ws_debug_enabled


class StateSync(Extension):
    async def execute(self, instance=None, sid: str = "", **kwargs):
        if instance is None:
            return

        get_state_monitor().unregister_sid(instance.namespace, sid)
        if _ws_debug_enabled():
            PrintStyle.debug(f"[WebuiHandler] disconnect sid={sid}")
