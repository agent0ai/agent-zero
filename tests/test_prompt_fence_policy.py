import sys
import json
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent import Agent


class _DummyContext:
    def get_data(self, key: str, recursive: bool = True):
        return None


def _dummy_agent(profile: str = "agent0"):
    # Agent.read_prompt only needs config.profile and context.get_data() to resolve prompt paths.
    return SimpleNamespace(config=SimpleNamespace(profile=profile), context=_DummyContext())


def test_agent_read_prompt_preserves_embedded_fenced_examples_in_markdown_prompts():
    dummy = _dummy_agent()
    text = Agent.read_prompt(dummy, "agent.system.tool.response.md")

    assert "usage:" in text
    assert "~~~json" in text
    assert "~~~" in text


def test_agent_read_prompt_strips_full_json_template_fences_for_json_consumers():
    dummy = _dummy_agent()
    text = Agent.read_prompt(dummy, "fw.initial_message.md")

    assert "```" not in text
    assert "~~~" not in text

    parsed = json.loads(text)
    assert parsed.get("tool_name") == "response"
