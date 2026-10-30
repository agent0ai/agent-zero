from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from plugins._migrate_agents.helpers import migration


def entry(entry_id, parent, role, content, **message):
    return {"type": "message", "id": entry_id, "parentId": parent,
            "message": {"role": role, "content": content, "timestamp": 1793400000000, **message}}


def upload(*entries, version=3):
    header = {"type": "session", "id": "pi-session", "cwd": "/work/demo", "version": version}
    return migration.Upload("demo.jsonl", ("\n".join(json.dumps(row) for row in [header, *entries]) + "\n").encode())


class PiMigrationTests(unittest.TestCase):
    def test_provenance_survives_native_chat_persistence(self):
        from helpers import persist_chat

        conversation = migration.parse_bundle("pi", [upload(entry("u", None, "user", "Hello"))]).conversations[0]
        native = migration.build_a0_chat(conversation, "pi")
        context = SimpleNamespace(
            id="test", name=native["name"], config=SimpleNamespace(profile="default"),
            agent0=SimpleNamespace(config=SimpleNamespace(profile="default"), data={}),
            data=native["data"], output_data={}, created_at=None,
            last_message=None, type=SimpleNamespace(value="user"), log=None,
            streaming_agent=None,
        )
        with patch.object(persist_chat, "_serialize_log", return_value={}), patch.object(persist_chat, "_serialize_agent", return_value={}):
            saved = persist_chat._serialize_context(context)
        provenance = json.loads(json.dumps(saved))["data"]["migrate_agents"]
        self.assertEqual(provenance["source"], "pi")
        self.assertEqual(provenance["source_metadata"]["session_id"], "pi-session")
        self.assertFalse(provenance["hidden_reasoning_included"])

    def test_public_text_tool_arguments_results_errors_and_privacy(self):
        data = upload(
            entry("s", None, "system", "private system prompt"),
            entry("u", "s", "user", [{"type": "text", "text": "Read the plan"}]),
            entry("a", "u", "assistant", [
                {"type": "thinking", "thinking": "private reasoning", "signature": "private signature"},
                {"type": "text", "text": "Checking the file", "textSignature": "private text signature"},
                {"type": "toolCall", "id": "call-1", "name": "read", "arguments": '{"path":"plan.md","api_key":"secret-value"}'},
            ]),
            entry("t", "a", "toolResult", [{"type": "text", "text": "token missing; password=hidden-password"}], toolCallId="call-1", toolName="read", isError=True),
            entry("r", "t", "assistant", [{"type": "text", "text": "Please provide the file."}]),
            {"type": "session_info", "id": "n", "parentId": "r", "name": "Plan review"},
        )
        bundle = migration.parse_bundle("pi", [data])
        self.assertEqual(bundle.summary()["chats"], 1)
        chat = bundle.conversations[0]
        self.assertEqual(chat.title, "Plan review")
        self.assertEqual([event.kind for event in chat.events], ["user", "assistant", "tool", "assistant"])
        tool = chat.events[2]
        self.assertEqual(tool.tool_args, {"path": "plan.md", "api_key": "[REDACTED]"})
        self.assertIn("[Pi tool error]", tool.tool_result)
        self.assertIn("password=[REDACTED]", tool.tool_result)
        native = migration.build_a0_chat(chat, "pi")
        self.assertTrue(native["created_at"].startswith("2026-10-30"))
        serialized = json.dumps(native)
        for hidden in ("private system", "private reasoning", "private signature", "private text signature", "secret-value", "hidden-password"):
            self.assertNotIn(hidden, serialized)
        self.assertFalse(native["data"]["migrate_agents"]["historical_tools_are_replayable"])
        self.assertEqual(bundle.projects[0].path, "/work/demo")

    def test_branches_have_separate_tool_results_and_shared_ancestry(self):
        bundle = migration.parse_bundle("pi", [upload(
            entry("u", None, "user", "Read the file"),
            entry("call", "u", "assistant", [{"type": "toolCall", "id": "same-call", "name": "read", "arguments": {"path": "plan.md"}}]),
            entry("left", "call", "toolResult", "left result", toolCallId="same-call", toolName="read"),
            entry("right", "call", "toolResult", "right result", toolCallId="same-call", toolName="read"),
        )])
        self.assertEqual(len(bundle.conversations), 2)
        self.assertEqual([c.events[1].tool_result for c in bundle.conversations], ["left result", "right result"])
        self.assertEqual(len({c.source_id for c in bundle.conversations}), 2)
        for c in bundle.conversations:
            self.assertEqual(c.events[0].text, "Read the file")
            self.assertEqual(c.metadata["branch_count"], 2)
        self.assertEqual(len(bundle.projects), 1)
        self.assertEqual(len(bundle.projects[0].conversation_ids), 2)

    def test_metadata_forks_do_not_duplicate_prefix_chats(self):
        bundle = migration.parse_bundle("pi", [upload(
            entry("u", None, "user", "Hello"),
            {"type": "session_info", "id": "name", "parentId": "u", "name": "A useful title"},
            entry("a", "u", "assistant", [{"type": "text", "text": "Welcome"}]),
            {"type": "session_info", "id": "blank", "parentId": "a", "name": ""},
        )])
        self.assertEqual(len(bundle.conversations), 1)
        self.assertEqual(bundle.conversations[0].title, "A useful title")
        self.assertEqual([e.text for e in bundle.conversations[0].events], ["Hello", "Welcome"])

    def test_context_records_are_skipped_without_breaking_parent_walk(self):
        bundle = migration.parse_bundle("pi", [upload(
            entry("u", None, "user", "Original request"),
            {"type": "compaction", "id": "c", "parentId": "u", "summary": "private summary"},
            {"type": "context_edit", "id": "e", "parentId": "c", "targetId": "u", "replacement": "altered context"},
            {"type": "custom_message", "id": "x", "parentId": "e", "content": "private extension"},
            entry("a", "x", "assistant", [{"type": "text", "text": "Done"}]),
        )])
        self.assertEqual([e.text for e in bundle.conversations[0].events], ["Original request", "Done"])
        self.assertEqual(bundle.conversations[0].metadata["omitted_entries"], {"compaction": 1, "context_edit": 1, "custom_message": 1})
        self.assertTrue(bundle.warnings)

    def test_images_become_markers_and_public_shell_output_is_inert(self):
        bundle = migration.parse_bundle("pi", [upload(
            entry("u", None, "user", [{"type": "image", "data": "PRIVATE_BASE64", "mimeType": "image/png"}]),
            entry("b", "u", "bashExecution", None, command="pwd", output="/work/demo", exitCode=0),
            entry("hidden", "b", "bashExecution", None, command="private command", output="private output", excludeFromContext=True),
        )])
        events = bundle.conversations[0].events
        self.assertEqual(len(events), 2)
        self.assertIn("Image attachment omitted", events[0].text)
        self.assertEqual(events[1].tool_args, {"command": "pwd"})
        self.assertIn("Pi user shell command; exit code 0", events[1].tool_result)
        serialized = json.dumps(migration.build_a0_chat(bundle.conversations[0], "pi"))
        self.assertNotIn("PRIVATE_BASE64", serialized)
        self.assertNotIn("private command", serialized)
        self.assertNotIn("private output", serialized)

    def test_v1_linear_and_v2_multiple_roots(self):
        legacy = upload({"type": "message", "message": {"role": "user", "content": "Legacy"}}, version=1)
        self.assertEqual(migration.parse_bundle("pi", [legacy]).conversations[0].events[0].text, "Legacy")
        missing_version = migration.Upload("old.jsonl", legacy.data.replace(b', "version": 1', b''))
        self.assertEqual(len(migration.parse_bundle("pi", [missing_version]).conversations), 1)
        bundle = migration.parse_bundle("pi", [upload(entry("a", None, "user", "One"), entry("b", None, "user", "Two"), version=2)])
        self.assertEqual(len(bundle.conversations), 2)

    def test_invalid_tree_and_future_versions_are_warned_not_flattened(self):
        cases = [
            upload(entry("a", "missing", "user", "No")),
            upload(entry("a", "a", "user", "No")),
            upload(entry("a", None, "user", "One"), entry("a", None, "user", "Two")),
            upload(entry("a", None, "user", "No"), version=4),
            upload(entry("a", None, "user", "No"), version=True),
            upload(entry("a", None, "user", "No"), ["not an entry"]),
            upload(entry("a", None, ["invalid role"], "No")),
            upload({"type": ["invalid type"], "id": "a", "parentId": None}),
        ]
        for data in cases:
            with self.subTest(data=data.data[:120]):
                bundle = migration.parse_bundle("pi", [data])
                self.assertEqual(bundle.conversations, [])
                self.assertTrue(bundle.warnings)

    def test_branch_amplification_limits_are_checked_before_normalizing(self):
        data = upload(entry("u", None, "user", "x" * 1000), entry("a", "u", "assistant", "A"), entry("b", "u", "assistant", "B"))
        for limit, value in (("MAX_PI_BRANCHES", 1), ("MAX_PI_EXPANDED_ENTRIES", 3), ("MAX_TOTAL_BYTES", len(data.data) + 1)):
            with self.subTest(limit=limit), patch.object(migration, limit, value), patch.object(migration, "_pi_messages", side_effect=AssertionError("normalized before limit")):
                bundle = migration.parse_bundle("pi", [data])
                self.assertEqual(bundle.conversations, [])
                self.assertTrue(bundle.warnings)

    def test_branch_byte_limit_is_shared_across_the_upload(self):
        first = upload(entry("u", None, "user", "x" * 1000), entry("a", "u", "assistant", "A"), entry("b", "u", "assistant", "B"))
        second = migration.Upload("second.jsonl", first.data.replace(b'pi-session', b'session-two'))
        with patch.object(migration, "MAX_TOTAL_BYTES", len(first.data) + len(second.data) + 1), patch.object(migration, "_pi_messages", wraps=migration._pi_messages) as normalize:
            bundle = migration.parse_bundle("pi", [first, second])
        self.assertEqual(normalize.call_count, 4)
        self.assertEqual(len(bundle.conversations), 2)
        self.assertTrue(any("across this upload" in warning for warning in bundle.warnings))

    def test_unicode_line_separators_and_title_redaction(self):
        data = upload(entry("u", None, "user", "password=private-value\u2028next\u2029line"))
        data.data = data.data.replace(b'\\u2028', '\u2028'.encode()).replace(b'\\u2029', '\u2029'.encode())
        bundle = migration.parse_bundle("pi", [data])
        self.assertEqual(len(bundle.conversations), 1)
        self.assertNotIn("private-value", json.dumps(migration.build_a0_chat(bundle.conversations[0], "pi")))
        self.assertIn("\u2028", bundle.conversations[0].events[0].text)

    def test_deep_arguments_and_malformed_nested_json_do_not_abort_bundle(self):
        deep = "[" * 10000
        valid = upload(entry("a", None, "assistant", [{"type": "toolCall", "id": "call", "name": "read", "arguments": deep}]))
        broken = migration.Upload("broken.jsonl", b'{"type":"session","version":3}\n' + b'{"nested":' + deep.encode())
        bundle = migration.parse_bundle("pi", [valid, broken])
        self.assertEqual(len(bundle.conversations), 1)
        self.assertEqual(bundle.conversations[0].events[0].tool_args, {"raw_arguments": deep})
        self.assertTrue(any("broken.jsonl" in warning for warning in bundle.warnings))

    def test_omitted_only_file_is_reported_beside_a_valid_session(self):
        valid = upload(entry("u", None, "user", "Hello"))
        hidden = migration.Upload("hidden.jsonl", upload(entry("s", None, "system", "private")).data)
        bundle = migration.parse_bundle("pi", [valid, hidden])
        self.assertEqual(len(bundle.conversations), 1)
        self.assertTrue(any("hidden.jsonl" in warning for warning in bundle.warnings))

    def test_pi_credentials_and_settings_are_excluded(self):
        bundle = migration.parse_bundle("pi", [
            upload(entry("u", None, "user", "Hello")),
            migration.Upload("auth.json", b'{"token":"private"}'),
            migration.Upload("settings.json", b'{"defaultProvider":"private"}'),
            migration.Upload("models.json", b'{"apiKey":"private"}'),
            migration.Upload("models-store.json", b'{"provider":"private"}'),
        ])
        self.assertEqual(len(bundle.excluded), 4)
        self.assertEqual(len(bundle.conversations), 1)


if __name__ == "__main__":
    unittest.main()
