"""Memory initialization extension - implementation provided by the memory plugin."""
from python.helpers.plugins import import_plugin_module

# Import the actual implementation from the plugin
_mod = import_plugin_module("memory", "extensions/monologue_start/_10_memory_init.py")

# Re-export all public names
globals().update({k: v for k, v in vars(_mod).items() if not k.startswith('_')})
