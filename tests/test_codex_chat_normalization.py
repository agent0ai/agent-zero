import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import models
from python.helpers import dirty_json


def test_normalize_plain_text_wraps_response_tool():
    out = models._normalize_codex_chat_message("Hi! How can I help?")
    parsed = dirty_json.try_parse(out)
    assert isinstance(parsed, dict)
    assert parsed.get("tool_name") == "response"
    assert isinstance(parsed.get("tool_args"), dict)
    assert parsed["tool_args"].get("text") == "Hi! How can I help?"


def test_normalize_existing_tool_request_keeps_tool_name_and_args():
    raw = '{"tool_name":"response","tool_args":{"text":"ok"}}'
    out = models._normalize_codex_chat_message(raw)
    parsed = dirty_json.try_parse(out)
    assert isinstance(parsed, dict)
    assert parsed.get("tool_name") == "response"
    assert parsed.get("tool_args", {}).get("text") == "ok"

