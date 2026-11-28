import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from helpers import files, projects, skills, subagents
from tools.skills_tool import SkillsTool


ROOT = Path(__file__).resolve().parents[1]

NOTICE_PROMPTS = [
    ("fw.msg_misformat_response.md", "prompts"),
    ("fw.msg_reasoning_only_response.md", "prompts"),
    ("fw.msg_output_limit_response.md", "prompts"),
    ("fw.msg_thoughts_fallback_response.md", "plugins/_context_doctor/prompts"),
]


@pytest.mark.parametrize("name, directory", NOTICE_PROMPTS)
def test_recovery_notice_prompts_exist(name, directory):
    text = files.read_prompt_file(
        name, _directories=[str(ROOT / directory)], finish_reason="length"
    )

    assert text.strip(), name


def test_same_condition_recovery_notices_stay_in_sync():
    core = files.read_prompt_file(
        "fw.msg_misformat_response.md", _directories=[str(ROOT / "prompts")]
    )
    plugin = files.read_prompt_file(
        "fw.msg_thoughts_fallback_response.md",
        _directories=[str(ROOT / "plugins" / "_context_doctor" / "prompts")],
    )

    assert core.rstrip("\n") == plugin.rstrip("\n")


@pytest.mark.parametrize("project", [None, "demo"])
def test_profile_catalog_keeps_ids_titles_scope_and_routing(monkeypatch, project):
    profiles = {
        "custom-id": SimpleNamespace(
            title="Custom Title", context="Review\ncode", description="Fallback"
        ),
        "fallback": SimpleNamespace(title="Fallback", context=" \n", description="Find facts"),
    }
    scopes = []
    monkeypatch.setattr(projects, "get_context_project_name", lambda _: project)
    monkeypatch.setattr(
        subagents, "get_available_agents_dict", lambda scope: scopes.append(scope) or profiles
    )
    agent = SimpleNamespace(context=object(), config=SimpleNamespace(profile="agent0"))
    prompt = files.read_prompt_file(
        "agent.system.tool.call_sub.md", _directories=[str(ROOT / "prompts")], _agent=agent
    )
    assert scopes == [project]
    assert "available profiles:\n- custom-id (Custom Title): Review code\n- fallback (Fallback): Find facts" in prompt
    profiles.clear()
    prompt = files.read_prompt_file(
        "agent.system.tool.call_sub.md", _directories=[str(ROOT / "prompts")], _agent=agent
    )
    assert "available profiles:" not in prompt


@pytest.mark.parametrize("profile", ["agent0", "developer", "custom-id", ""])
def test_delegation_prompt_identifies_caller_without_hiding_same_profile(monkeypatch, profile):
    monkeypatch.setattr(projects, "get_context_project_name", lambda _: None)
    monkeypatch.setattr(
        subagents,
        "get_available_agents_dict",
        lambda _: {
            "developer": SimpleNamespace(
                title="Developer", context="Implement and review code", description=""
            )
        },
    )
    agent = SimpleNamespace(context=object(), config=SimpleNamespace(profile=profile))
    prompt = files.read_prompt_file(
        "agent.system.tool.call_sub.md", _directories=[str(ROOT / "prompts")], _agent=agent
    )

    assert f"your current profile: {profile or 'default'}" in prompt
    assert "- developer (Developer): Implement and review code" in prompt
    assert "distinct bounded subtasks or independent reviews" in prompt
    assert "always use specialized subordinate agents" not in prompt

    without_agent = files.read_prompt_file(
        "agent.system.tool.call_sub.md", _directories=[str(ROOT / "prompts")]
    )
    assert "your current profile:" not in without_agent
    assert "{{current_profile}}" not in without_agent


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
        ("publish plugin", "a0-create-plugin"),
        ("plugin not loading", "a0-create-plugin"),
        ("create agent", "a0-development"),
        ("form validation", "browser-automation"),
        ("Chrome Web Store", "browser-automation"),
        ("extension permissions", "browser-automation"),
        ("connect local files", "a0-development"),
        ("Word document", "document-query"),
        ("Docker desktop terminal", "linux-desktop"),
        ("framework development", "a0-development"),
    ]:
        assert name in [skill.name for skill in skills.search_skills(query, limit=3)], query


@pytest.mark.asyncio
@pytest.mark.parametrize(("parent", "former_name", "query", "file_path"), [
    ("a0-development", "a0-create-agent", "create agent", "references/a0-create-agent/guide.md"),
    ("a0-development", "setup-a0-cli", "connect local files", "references/setup-a0-cli.md"),
    ("browser-automation", "browser-extension-control", "Chrome Web Store", "references/browser-extension-control.md"),
    ("browser-automation", "browser-form-workflows", "form validation", "references/browser-form-workflows.md"),
])
async def test_bundled_workflows_load_as_parent_skill_references(monkeypatch, parent, former_name, query, file_path):
    roots = [ROOT / "skills", ROOT / "plugins/_browser/skills"]
    monkeypatch.setattr(skills, "get_skill_roots", lambda agent=None: list(map(str, roots)))
    monkeypatch.setattr(files, "normalize_a0_path", str)

    assert skills.find_skill(former_name) is None
    assert skills.search_skills(former_name, limit=1)[0].name == parent
    assert skills.search_skills(query, limit=1)[0].name == parent
    skill = skills.find_skill(parent, include_content=True)
    assert file_path in skill.content
    expected = (skill.path / file_path).read_text(encoding="utf-8")
    assert expected.startswith("# ")

    tool = SkillsTool(None, "skills_tool", None, {}, "", None)
    result = await tool.execute(action="read_file", skill_name=parent, file_path=file_path)
    assert result.message == f"Skill file: {parent}/{file_path}\n\n{expected}"
