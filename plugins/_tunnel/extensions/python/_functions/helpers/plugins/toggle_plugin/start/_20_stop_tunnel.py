from helpers.extension import Extension
from plugins._tunnel.helpers.runtime import stop


class StopDisabledTunnel(Extension):
    def execute(self, data: dict, **kwargs):
        args, values = data['args'], data['kwargs']
        name = values.get('plugin_name', args[0] if args else '')
        enabled = values.get('enabled', args[1] if len(args) > 1 else False)
        if name == '_tunnel' and not enabled:
            stop()
