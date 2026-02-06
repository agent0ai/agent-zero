"""Memorize solutions extension - implementation provided by the memory plugin."""
from python.helpers.plugins import import_plugin_module

# Import the actual implementation from the plugin
_mod = import_plugin_module("memory", "extensions/monologue_end/_51_memorize_solutions.py")

# Re-export all public names
globals().update({k: v for k, v in vars(_mod).items() if not k.startswith('_')})
