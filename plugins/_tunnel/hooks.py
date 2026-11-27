"""Prepare lazily on Start; never install tunnel dependencies into Agent Zero."""
from plugins._tunnel.helpers import runtime


def install():
    return True


def get_plugin_config(default=None, **kwargs):
    value = dict(default or {})
    provider = str(value.get('provider') or 'cloudflared')
    if provider not in runtime.PROVIDERS:
        raise ValueError('Unsupported tunnel provider')
    port = int(value.get('port') or 0)
    if not 0 <= port <= 65535:
        raise ValueError('Invalid tunnel target port')
    return {'provider': provider, 'port': port, 'image': str(value.get('image') or '').strip()}


def save_plugin_config(settings=None, default=None, **kwargs):
    return get_plugin_config(settings or default)


def uninstall():
    from helpers.sandbox import get_manager
    runtime.stop()
    get_manager().delete(runtime.SANDBOX, missing_ok=True)
