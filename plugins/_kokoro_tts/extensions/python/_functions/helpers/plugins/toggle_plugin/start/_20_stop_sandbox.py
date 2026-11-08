from helpers.extension import Extension


class StopDisabledSandbox(Extension):
    def execute(self, data: dict, **kwargs):
        args, values = data['args'], data['kwargs']
        name = values.get('plugin_name', args[0] if args else '')
        enabled = values.get('enabled', args[1] if len(args) > 1 else False)
        if name == '_kokoro_tts' and not enabled:
            from plugins._kokoro_tts import hooks
            hooks.disable()
