"""Exercise the reset endpoint with external framework services replaced."""
import asyncio
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch


class ChatResetTests(unittest.TestCase):
    def test_reset_clears_queued_input_before_persisting_and_notifies_clients(self):
        events = []
        context = SimpleNamespace(reset=lambda: events.append("reset"))
        use_context = Mock(return_value=context)
        cancel = Mock(side_effect=lambda *_args, **_kwargs: events.append("cancel"))
        remove = Mock(side_effect=lambda _: events.append("queue"))
        save = Mock(side_effect=lambda _: events.append("save"))
        remove_files = Mock(side_effect=lambda _: events.append("files"))
        dirty = Mock(side_effect=lambda **_: events.append("notify"))
        dependencies = {
            "helpers": {
                "message_queue": SimpleNamespace(remove=remove),
                "persist_chat": SimpleNamespace(save_tmp_chat=save, remove_msg_files=remove_files),
            },
            "helpers.api": {
                "ApiHandler": type("ApiHandler", (), {}),
                "Input": dict, "Output": dict, "Request": object, "Response": object,
            },
            "helpers.task_scheduler": {
                "TaskScheduler": SimpleNamespace(get=lambda: SimpleNamespace(cancel_tasks_by_context=cancel)),
            },
            "helpers.state_monitor_integration": {"mark_dirty_all": dirty},
        }
        modules = {}
        for name, attributes in dependencies.items():
            modules[name] = ModuleType(name)
            modules[name].__dict__.update(attributes)
        source = Path(__file__).resolve().parents[1] / "api/chat_reset.py"
        spec = importlib.util.spec_from_file_location("chat_reset_under_test", source)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, modules):
            spec.loader.exec_module(module)
            endpoint = module.Reset()
            endpoint.use_context = use_context
            result = asyncio.run(endpoint.process({"context": "chat-a"}, None))

        self.assertEqual(result, {"message": "Agent restarted."})
        self.assertEqual(events, ["cancel", "reset", "queue", "save", "files", "notify"])
        cancel.assert_called_once_with("chat-a", terminate_thread=True)
        use_context.assert_called_once_with("chat-a")
        remove.assert_called_once_with(context)
        save.assert_called_once_with(context)
        remove_files.assert_called_once_with("chat-a")
        dirty.assert_called_once_with(reason="api.chat_reset.Reset")


if __name__ == "__main__":
    unittest.main()
