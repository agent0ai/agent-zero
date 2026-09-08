import json
import re
from pathlib import Path

import pytest

from helpers import skills


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("path", [
    "plugins/_code_execution/prompts/agent.system.tool.code_exe.md",
    "plugins/_code_execution/prompts/agent.system.tool.input.md",
    "agents/agent0/prompts/agent.system.tool.response.md",
])
def test_tool_examples_are_complete_valid_json(path):
    examples = re.findall(r"~~~json\n(.*?)\n~~~", (ROOT / path).read_text(), re.S)
    assert examples
    for example in examples:
        request = json.loads(example)
        assert {"thoughts", "headline", "tool_name", "tool_args"} <= request.keys()
        assert isinstance(request["tool_args"], dict)


def test_default_skill_descriptions_fit_preview_and_remain_searchable(monkeypatch):
    paths = [*ROOT.glob("skills/*/SKILL.md"), *ROOT.glob("plugins/*/skills/*/SKILL.md")]
    candidates = []
    for path in paths:
        if "_a0_connector" in path.parts:  # Host-only skills are outside the default catalog.
            continue
        skill = skills.skill_from_markdown(path)
        assert skill is not None, path
        assert 0 < len(skill.description) <= 100, path
        candidates.append(skill)
    monkeypatch.setattr(skills, "list_skills", lambda *args, **kwargs: candidates)
    for query, name in [
        ("publish plugin", "a0-contribute-plugin"),
        ("plugin not loading", "a0-debug-plugin"),
        ("create agent", "a0-create-agent"),
        ("form validation", "browser-form-workflows"),
        ("Chrome Web Store", "browser-extension-control"),
        ("extension permissions", "browser-extension-control"),
        ("connect local files", "setup-a0-cli"),
        ("Word document", "writer-documents"),
        ("Docker desktop terminal", "linux-desktop"),
        ("framework development", "a0-development"),
    ]:
        assert name in [skill.name for skill in skills.search_skills(query, limit=3)], query
