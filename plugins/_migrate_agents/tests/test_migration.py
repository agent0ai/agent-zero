from __future__ import annotations

import importlib.util
import io
import json
import sqlite3
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("_migrate_agents_core", ROOT / "helpers" / "migration.py")
assert SPEC and SPEC.loader
migration = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = migration
SPEC.loader.exec_module(migration)


def jsonl(*rows) -> bytes:
    return ("\n".join(json.dumps(row) for row in rows) + "\n").encode()


class MigrationTests(unittest.TestCase):
    def test_codex_uses_public_events_tools_and_excludes_reasoning(self):
        upload = migration.Upload(
            "rollout-test.jsonl",
            jsonl(
                {"type": "session_meta", "payload": {"id": "codex-1", "cwd": "/work"}},
                {"type": "event_msg", "timestamp": "2026-01-01T00:00:00Z", "payload": {"type": "user_message", "message": "Fix it"}},
                {"type": "event_msg", "timestamp": "2026-01-01T00:00:01Z", "payload": {"type": "agent_message", "phase": "commentary", "message": "Checking"}},
                {"type": "response_item", "timestamp": "2026-01-01T00:00:02Z", "payload": {"type": "function_call", "call_id": "c1", "name": "shell", "arguments": "{\"api_key\":\"secret-value\"}"}},
                {"type": "response_item", "timestamp": "2026-01-01T00:00:03Z", "payload": {"type": "function_call_output", "call_id": "c1", "output": "done"}},
                {"type": "event_msg", "timestamp": "2026-01-01T00:00:04Z", "payload": {"type": "agent_message", "phase": "final_answer", "message": "Fixed"}},
                {"type": "response_item", "payload": {"type": "reasoning", "text": "hidden"}},
            ),
        )
        bundle = migration.parse_bundle("codex", [upload])
        self.assertEqual(bundle.summary()["chats"], 1)
        self.assertEqual([event.kind for event in bundle.conversations[0].events], ["user", "tool", "assistant"])
        self.assertEqual(bundle.conversations[0].events[1].tool_result, "done")
        self.assertEqual(bundle.conversations[0].events[1].tool_args["api_key"], "[REDACTED]")
        self.assertNotIn('"text": "hidden"', json.dumps(migration.build_a0_chat(bundle.conversations[0], "codex")))

    def test_claude_ignores_thinking_and_sidechains(self):
        upload = migration.Upload(
            "project/session.jsonl",
            jsonl(
                {"type": "user", "sessionId": "claude-1", "timestamp": "2026-01-01T00:00:00Z", "message": {"role": "user", "content": [{"type": "text", "text": "Hello"}]}},
                {"type": "assistant", "sessionId": "claude-1", "timestamp": "2026-01-01T00:00:01Z", "message": {"role": "assistant", "content": [{"type": "thinking", "thinking": "private"}, {"type": "text", "text": "Hi"}]}},
                {"type": "assistant", "isSidechain": True, "sessionId": "claude-1", "message": {"role": "assistant", "content": [{"type": "text", "text": "branch"}]}},
            ),
        )
        bundle = migration.parse_bundle("claude", [upload])
        text = json.dumps(migration.build_a0_chat(bundle.conversations[0], "claude"))
        self.assertIn("Hello", text)
        self.assertIn("Hi", text)
        self.assertNotIn("private", text)
        self.assertNotIn("branch", text)

    def test_opencode_export_keeps_text_and_completed_tool(self):
        data = {
            "info": {"id": "ses_1", "title": "Ship it", "directory": "/repo"},
            "messages": [
                {"info": {"role": "user", "time": {"created": 1000}}, "parts": [{"type": "text", "text": "Build"}]},
                {"info": {"role": "assistant", "time": {"created": 2000}}, "parts": [{"type": "text", "text": "Done"}, {"type": "tool", "tool": "bash", "state": {"status": "completed", "input": {"command": "true"}, "output": "ok"}}]},
            ],
        }
        bundle = migration.parse_bundle("opencode", [migration.Upload("session.json", json.dumps(data).encode())])
        self.assertEqual(bundle.conversations[0].title, "Ship it")
        self.assertEqual([event.kind for event in bundle.conversations[0].events], ["user", "assistant", "tool"])

    def test_hermes_jsonl_and_openclaw_jsonl(self):
        hermes = migration.parse_bundle(
            "hermes",
            [migration.Upload("backup.jsonl", jsonl({"id": "h1", "title": "Hermes", "messages": [{"role": "user", "content": "One"}, {"role": "assistant", "content": "Two"}]}))],
        )
        claw = migration.parse_bundle(
            "openclaw",
            [migration.Upload("trace.jsonl", jsonl({"type": "session", "id": "o1"}, {"type": "message", "message": {"role": "user", "content": "One"}}, {"type": "message", "message": {"role": "assistant", "content": "Two"}}))],
        )
        self.assertEqual(hermes.summary()["chats"], 1)
        self.assertEqual(claw.summary()["chats"], 1)

    def test_hermes_sqlite(self):
        with tempfile.NamedTemporaryFile(suffix=".db") as handle:
            db = sqlite3.connect(handle.name)
            db.executescript(
                "CREATE TABLE sessions (id TEXT, source TEXT, model TEXT, title TEXT, cwd TEXT, started_at REAL);"
                "CREATE TABLE messages (id INTEGER, session_id TEXT, role TEXT, content TEXT, timestamp REAL, tool_calls TEXT, tool_name TEXT, tool_call_id TEXT);"
                "INSERT INTO sessions VALUES ('h1','cli','model','SQLite chat','/repo',1);"
                "INSERT INTO messages VALUES (1,'h1','user','Hello',1,NULL,NULL,NULL);"
                "INSERT INTO messages VALUES (2,'h1','assistant','Hi',2,NULL,NULL,NULL);"
            )
            db.commit()
            data = Path(handle.name).read_bytes()
            db.close()
        bundle = migration.parse_bundle("hermes", [migration.Upload("state.db", data)])
        self.assertEqual(bundle.conversations[0].title, "SQLite chat")

    def test_openclaw_sqlite(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite") as handle:
            db = sqlite3.connect(handle.name)
            db.executescript(
                "CREATE TABLE session_windows (session_id TEXT, session_key TEXT, created_at INTEGER, display_name TEXT, channel TEXT, model TEXT);"
                "CREATE TABLE transcript_events (session_id TEXT, seq INTEGER, event_json TEXT, created_at INTEGER);"
                "INSERT INTO session_windows VALUES ('o1','agent:main:main',1,'Claw chat','web','model');"
            )
            event = json.dumps({"type": "message", "message": {"role": "user", "content": "Hello"}})
            db.execute("INSERT INTO transcript_events VALUES ('o1',1,?,1)", (event,))
            db.commit()
            data = Path(handle.name).read_bytes()
            db.close()
        bundle = migration.parse_bundle("openclaw", [migration.Upload("openclaw-agent.sqlite", data)])
        self.assertEqual(bundle.conversations[0].title, "Claw chat")

    def test_discovers_knowledge_and_complete_skill_folder(self):
        bundle = migration.parse_bundle(
            "claude",
            [
                migration.Upload("project/memory/MEMORY.md", b"Remember api_key=secret"),
                migration.Upload("project/CLAUDE.md", b"Remember password=secret"),
                migration.Upload("project/skills/release/SKILL.md", b"---\nname: release\n---"),
                migration.Upload("project/skills/release/scripts/run.py", b"API_KEY=secret"),
                migration.Upload("project/skills/release/.env", b"API_KEY=never"),
            ],
        )
        self.assertEqual(bundle.summary()["memories"], 1)
        self.assertEqual(bundle.summary()["instructions"], 1)
        self.assertEqual(bundle.summary()["knowledge"], 2)
        self.assertEqual(bundle.summary()["skills"], 1)
        self.assertIn(b"[REDACTED]", bundle.memories[0].data)
        self.assertIn(b"[REDACTED]", bundle.instructions[0].data)
        self.assertEqual(len(next(iter(bundle.skills.values()))), 2)
        self.assertIn(b"[REDACTED]", bundle.skills["release"][1].data)
        self.assertEqual(bundle.summary()["excluded"], 1)

    def test_discovers_projects_from_retained_workspace_context(self):
        data = {
            "info": {"id": "ses_1", "title": "Ship it", "directory": "/work/acme"},
            "messages": [
                {"info": {"role": "user"}, "parts": [{"type": "text", "text": "Build"}]},
            ],
        }
        bundle = migration.parse_bundle(
            "opencode",
            [migration.Upload("session.json", json.dumps(data).encode())],
        )
        self.assertEqual(bundle.summary()["projects"], 1)
        self.assertEqual(bundle.projects[0].title, "acme")
        self.assertEqual(bundle.projects[0].path, "/work/acme")
        self.assertEqual(bundle.projects[0].conversation_ids, ["ses_1"])

    def test_rejects_archive_traversal(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            archive.writestr("../escape.json", "{}")
        with self.assertRaisesRegex(ValueError, "Unsafe archive path"):
            migration.parse_bundle("opencode", [migration.Upload("bad.zip", stream.getvalue())])

    def test_a0_chat_log_and_history_sequences_are_valid(self):
        conversation = migration.Conversation(
            "id",
            "Title",
            [migration.Event("user", "Hi", 1), migration.Event("assistant", "Hello", 2)],
        )
        chat = migration.build_a0_chat(conversation, "test")
        history = json.loads(chat["agents"][0]["history"])
        messages = history["current"]["messages"]
        self.assertEqual(history["counter"], len(messages))
        self.assertEqual([item["sequence"] for item in messages], list(range(1, len(messages) + 1)))
        self.assertEqual([item["no"] for item in chat["log"]["logs"]], list(range(len(chat["log"]["logs"]))))
        self.assertEqual([item["type"] for item in chat["log"]["logs"]], ["user", "agent", "response"])


if __name__ == "__main__":
    unittest.main()
