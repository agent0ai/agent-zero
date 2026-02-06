"""Recall memories extension - implementation provided by the memory plugin."""
from python.helpers.plugins import import_plugin_module

# Import the actual implementation from the plugin
_mod = import_plugin_module("memory", "extensions/message_loop_prompts_after/_50_recall_memories.py")

# Re-export all public names
globals().update({k: v for k, v in vars(_mod).items() if not k.startswith('_')})
