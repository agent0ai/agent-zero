from __future__ import annotations

import asyncio
import importlib
import sys
import types
from dataclasses import dataclass
from pathlib import Path


@dataclass
class _FakeResponse:
    message: str
    break_loop: bool
    additional: dict | None = None


class _FakeTool:
    def __init__(
        self,
        agent,
        name: str,
        method: str | None,
        args: dict | None,
        message: str,
        loop_data=None,
        **kwargs,
    ) -> None:
        self.agent = agent
        self.name = name
        self.method = method
        self.args = args or {}
        self.message = message
        self.loop_data = loop_data


class _FakeAgent:
    def __init__(self) -> None:
        self.data = {}
        self.context = types.SimpleNamespace(id="ctx")

    def read_prompt(self, _name: str, **kwargs) -> str:
        return f"deleted {kwargs.get('memory_count', 0)}"


@dataclass
class _FakeSkill:
    name: str
    description: str
    path: Path
    version: str = ""
    tags: list[str] | None = None


def _install_tool_stub(monkeypatch) -> None:
    tool_stub = types.ModuleType("helpers.tool")
    tool_stub.Tool = _FakeTool
    tool_stub.Response = _FakeResponse
    monkeypatch.setitem(sys.modules, "helpers.tool", tool_stub)


def _load_skills_tool(monkeypatch, skill_root: Path):
    _install_tool_stub(monkeypatch)

    skills_stub = types.ModuleType("helpers.skills")
    skills_stub.AGENT_DATA_NAME_LOADED_SKILLS = "loaded_skills"
    skills_stub.MAX_ACTIVE_SKILLS = 20
    fake_skill = _FakeSkill(
        name="browser-form-workflows",
        description="Use for complex browser forms.",
        path=skill_root,
        tags=[],
    )
    skills_stub.list_skills = lambda *args, **kwargs: [fake_skill]
    skills_stub.search_skills = lambda *args, **kwargs: [fake_skill]
    skills_stub.find_skill = lambda *args, **kwargs: fake_skill
    monkeypatch.setitem(sys.modules, "helpers.skills", skills_stub)

    print_style_stub = types.ModuleType("helpers.print_style")
    print_style_stub.PrintStyle = lambda *args, **kwargs: types.SimpleNamespace(
        print=lambda *a, **k: None
    )
    monkeypatch.setitem(sys.modules, "helpers.print_style", print_style_stub)

    sys.modules.pop("tools.skills_tool", None)
    return importlib.import_module("tools.skills_tool")


def test_skills_tool_accepts_action_alias_for_search(monkeypatch, tmp_path: Path):
    module = _load_skills_tool(monkeypatch, tmp_path)
    tool = module.SkillsTool(
        _FakeAgent(),
        "skills_tool",
        None,
        {"action": "search", "query": "browser forms"},
        "",
        None,
    )

    response = asyncio.run(tool.execute(**tool.args))

    assert "browser-form-workflows" in response.message


def test_skills_tool_read_file_action_reads_inside_skill_dir(
    monkeypatch, tmp_path: Path
):
    skill_root = tmp_path / "browser-form-workflows"
    skill_root.mkdir()
    (skill_root / "notes.md").write_text("Use labels before typing.\n", encoding="utf-8")
    module = _load_skills_tool(monkeypatch, skill_root)
    tool = module.SkillsTool(
        _FakeAgent(),
        "skills_tool",
        None,
        {
            "action": "read_file",
            "skill_name": "browser-form-workflows",
            "file_path": "notes.md",
        },
        "",
        None,
    )

    response = asyncio.run(tool.execute(**tool.args))

    assert "Skill file: browser-form-workflows/notes.md" in response.message
    assert "Use labels before typing." in response.message


def test_memory_forget_tool_imports_plugin_memory_load(monkeypatch):
    _install_tool_stub(monkeypatch)
    monkeypatch.syspath_prepend(str(Path.cwd()))

    class FakeDb:
        def __init__(self) -> None:
            self.calls = []

        async def delete_documents_by_query(self, **kwargs):
            self.calls.append(kwargs)
            return ["memory-1"]

    fake_db = FakeDb()

    async def get_memory(_agent):
        return fake_db

    memory_stub = types.ModuleType("plugins._memory.helpers.memory")
    memory_stub.Memory = types.SimpleNamespace(get=get_memory)
    monkeypatch.setitem(sys.modules, "plugins._memory.helpers.memory", memory_stub)

    sys.modules.pop("plugins._memory.tools.memory_load", None)
    sys.modules.pop("plugins._memory.tools.memory_forget", None)
    module = importlib.import_module("plugins._memory.tools.memory_forget")
    tool = module.MemoryForget(
        _FakeAgent(),
        "memory_forget",
        None,
        {
            "query": "codex memory forget token",
            "threshold": 0.99,
            "filter": "area=='codex_sweep'",
        },
        "",
        None,
    )

    response = asyncio.run(tool.execute(**tool.args))

    assert response.message == "deleted 1"
    assert fake_db.calls == [
        {
            "query": "codex memory forget token",
            "threshold": 0.99,
            "filter": "area=='codex_sweep'",
            "include_exact": True,
            "cascade": True,
        }
    ]


def test_behaviour_adjustment_normalizes_duplicate_rules(monkeypatch):
    _install_tool_stub(monkeypatch)
    monkeypatch.syspath_prepend(str(Path.cwd()))

    agent_stub = types.ModuleType("agent")
    agent_stub.Agent = object
    monkeypatch.setitem(sys.modules, "agent", agent_stub)

    log_stub = types.ModuleType("helpers.log")
    log_stub.LogItem = object
    monkeypatch.setitem(sys.modules, "helpers.log", log_stub)

    memory_stub = types.ModuleType("plugins._memory.helpers.memory")
    memory_stub.get_memory_subdir_abs = lambda agent: "/tmp"
    monkeypatch.setitem(sys.modules, "plugins._memory.helpers.memory", memory_stub)

    sys.modules.pop("plugins._memory.tools.behaviour_adjustment", None)
    module = importlib.import_module("plugins._memory.tools.behaviour_adjustment")

    rules = module.normalize_ruleset(
        "## Behavioral rules\n"
        "* Favor Linux commands.\n"
        "* Token rule.## Behavioral rules\n"
        "* Favor Linux commands.\n"
        "* Token rule."
    )

    assert rules == "## Behavioral rules\n* Favor Linux commands.\n* Token rule.\n"


def test_behaviour_prompts_preserve_exact_rules_and_avoid_promptinclude():
    behaviour_prompt = Path("prompts/agent.system.tool.behaviour.md").read_text(
        encoding="utf-8"
    )
    merge_prompt = Path("prompts/behaviour.merge.sys.md").read_text(
        encoding="utf-8"
    )
    promptinclude_prompt = Path(
        "plugins/_promptinclude/prompts/agent.system.promptinclude.md"
    ).read_text(encoding="utf-8")

    assert "exact-response rules" in behaviour_prompt
    assert "preserve it verbatim" in behaviour_prompt
    assert "respond exactly with a phrase" in merge_prompt
    assert "use behaviour_adjustment, not promptinclude files" in promptinclude_prompt


def _load_a2a_chat_tool(monkeypatch):
    _install_tool_stub(monkeypatch)
    sys.modules.pop("tools.a2a_chat", None)
    return importlib.import_module("tools.a2a_chat")


def test_a2a_extracts_latest_assistant_text_from_history(monkeypatch):
    module = _load_a2a_chat_tool(monkeypatch)

    final = {
        "result": {
            "history": [
                {
                    "role": "user",
                    "parts": [{"kind": "text", "text": "what is 2+2?"}],
                },
                {
                    "role": "assistant",
                    "parts": [{"kind": "text", "text": "4"}],
                },
            ]
        }
    }

    assert module._extract_latest_assistant_text(final) == "4"


def test_a2a_extracts_status_or_artifact_text_when_history_is_empty(monkeypatch):
    module = _load_a2a_chat_tool(monkeypatch)

    status_final = {
        "result": {
            "status": {
                "message": {
                    "parts": [{"kind": "text", "text": "status answer"}]
                }
            }
        }
    }
    artifact_final = {
        "result": {
            "artifacts": [
                {"parts": [{"kind": "text", "text": "artifact answer"}]}
            ]
        }
    }

    assert module._extract_latest_assistant_text(status_final) == "status answer"
    assert module._extract_latest_assistant_text(artifact_final) == "artifact answer"


def test_a2a_session_key_normalizes_explicit_a2a_path(monkeypatch):
    module = _load_a2a_chat_tool(monkeypatch)

    assert module._session_key("http://localhost:32080/a2a") == "http://localhost:32080"
    assert module._session_key("http://localhost:32080") == "http://localhost:32080"


def test_a2a_empty_response_message_is_explicit_failure(monkeypatch):
    module = _load_a2a_chat_tool(monkeypatch)

    assert module._extract_latest_assistant_text({"result": {"history": []}}) == ""
    assert "failed" in module.A2A_EMPTY_RESPONSE_ERROR
    assert "not success" in module.A2A_EMPTY_RESPONSE_ERROR


def test_notify_user_prompt_documents_numeric_priority_values():
    prompt = Path("prompts/agent.system.tool.notify_user.md").read_text(
        encoding="utf-8"
    )

    assert "priority values: `20` high urgency, `10` normal urgency" in prompt


def test_tool_prompts_prevent_top_level_multi_tool():
    tools_prompt = Path("prompts/agent.system.tools.md").read_text(encoding="utf-8")
    communication_prompt = Path("prompts/agent.system.main.communication.md").read_text(
        encoding="utf-8"
    )
    browser_prompt = Path("plugins/_browser/prompts/agent.system.tool.browser.md").read_text(
        encoding="utf-8"
    )

    assert "There is no top-level `multi` or batch tool" in tools_prompt
    assert "never an action name such as `read`, `write`, `terminal`, or `multi`" in communication_prompt
    assert 'Never use `tool_name: "multi"`' in browser_prompt


def _load_scheduler_tool(monkeypatch):
    _install_tool_stub(monkeypatch)

    scheduler_stub = types.ModuleType("helpers.task_scheduler")
    scheduler_stub.TaskScheduler = object
    scheduler_stub.ScheduledTask = type("ScheduledTask", (), {})
    scheduler_stub.AdHocTask = type("AdHocTask", (), {})
    scheduler_stub.PlannedTask = type("PlannedTask", (), {})
    scheduler_stub.serialize_task = lambda task: {}
    scheduler_stub.parse_datetime = lambda value: None
    scheduler_stub.parse_task_plan = lambda value: None
    scheduler_stub.serialize_datetime = lambda value: value
    scheduler_stub.TaskState = types.SimpleNamespace(
        IDLE="idle",
        RUNNING="running",
    )
    scheduler_stub.TaskSchedule = type("TaskSchedule", (), {})
    scheduler_stub.TaskPlan = type("TaskPlan", (), {})
    monkeypatch.setitem(sys.modules, "helpers.task_scheduler", scheduler_stub)

    agent_stub = types.ModuleType("agent")
    agent_stub.AgentContext = types.SimpleNamespace(
        get=lambda *args, **kwargs: None,
        remove=lambda *args, **kwargs: None,
    )
    monkeypatch.setitem(sys.modules, "agent", agent_stub)

    persist_chat_stub = types.ModuleType("helpers.persist_chat")
    persist_chat_stub.remove_chat = lambda *args, **kwargs: None
    monkeypatch.setitem(sys.modules, "helpers.persist_chat", persist_chat_stub)

    projects_stub = types.ModuleType("helpers.projects")
    projects_stub.get_context_project_name = lambda context: ""
    projects_stub.load_basic_project_data = lambda project: {}
    monkeypatch.setitem(sys.modules, "helpers.projects", projects_stub)

    sys.modules.pop("tools.scheduler", None)
    return importlib.import_module("tools.scheduler")


def test_scheduler_accepts_action_alias(monkeypatch):
    module = _load_scheduler_tool(monkeypatch)
    tool = module.SchedulerTool(
        _FakeAgent(),
        "scheduler",
        None,
        {"action": "list_tasks"},
        "",
        None,
    )

    async def list_tasks(**kwargs):
        return module.Response("listed", False)

    tool.list_tasks = list_tasks

    response = asyncio.run(tool.execute(**tool.args))

    assert response.message == "listed"


def test_scheduler_requires_action_field(monkeypatch):
    module = _load_scheduler_tool(monkeypatch)
    tool = module.SchedulerTool(
        _FakeAgent(),
        "scheduler",
        "list_tasks",
        {},
        "",
        None,
    )

    response = asyncio.run(tool.execute(**tool.args))

    assert "Unknown scheduler action" in response.message


def test_scheduler_create_defaults_to_dedicated_context(monkeypatch):
    module = _load_scheduler_tool(monkeypatch)

    class FakeTaskSchedule:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

        def to_crontab(self):
            return f"{self.minute} {self.hour} {self.day} {self.month} {self.weekday}"

    class FakeScheduledTask:
        @classmethod
        def create(cls, **kwargs):
            task = cls()
            task.uuid = "task-1"
            task.context_id = kwargs.get("context_id")
            task.schedule = kwargs.get("schedule")
            return task

    class FakeScheduler:
        def __init__(self):
            self.added = None

        async def add_task(self, task):
            self.added = task

    fake_scheduler = FakeScheduler()
    module.TaskSchedule = FakeTaskSchedule
    module.ScheduledTask = FakeScheduledTask
    module.TaskScheduler = types.SimpleNamespace(get=lambda: fake_scheduler)
    tool = module.SchedulerTool(
        _FakeAgent(),
        "scheduler",
        None,
        {
            "action": "create_scheduled_task",
            "name": "check stuff",
            "prompt": "tell me if anything changed",
            "schedule": {"minute": "0", "hour": "9", "day": "*", "month": "*", "weekday": "*"},
        },
        "",
        None,
    )

    response = asyncio.run(tool.execute(**tool.args))

    assert "created" in response.message
    assert fake_scheduler.added.context_id is None


def test_scheduler_local_timezone_alias_uses_current_user_timezone(monkeypatch):
    module = _load_scheduler_tool(monkeypatch)

    class FakeTaskSchedule:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    module.TaskSchedule = FakeTaskSchedule
    module.Localization = types.SimpleNamespace(
        get=lambda: types.SimpleNamespace(get_timezone=lambda: "Europe/Rome")
    )

    assert module._schedule_timezone({"schedule": {"timezone": "local"}}) == "Europe/Rome"
    schedule = module._task_schedule_from_input(
        {"minute": "30", "hour": "9", "day": "*", "month": "*", "weekday": "*", "timezone": "current"}
    )

    assert schedule.timezone == "Europe/Rome"


def test_scheduler_invalid_timezone_returns_repairable_message(monkeypatch):
    module = _load_scheduler_tool(monkeypatch)
    tool = module.SchedulerTool(
        _FakeAgent(),
        "scheduler",
        None,
        {
            "action": "create_scheduled_task",
            "name": "bad timezone",
            "prompt": "tell me something",
            "schedule": {
                "minute": "0",
                "hour": "9",
                "day": "*",
                "month": "*",
                "weekday": "*",
                "timezone": "Mars/Base",
            },
        },
        "",
        None,
    )

    response = asyncio.run(tool.execute(**tool.args))

    assert "Invalid timezone: Mars/Base" in response.message


def test_scheduler_prompt_includes_update_timezone_and_dedicated_context():
    project_root = Path(__file__).resolve().parents[1]
    text = (
        project_root / "prompts/agent.system.tool.scheduler.md"
    ).read_text(encoding="utf-8")

    assert "update_task" in text
    assert "timezone" in text
    assert "IANA" in text
    assert "dedicated context" in text


def test_skills_prompt_renders_catalog_placeholder():
    project_root = Path(__file__).resolve().parents[1]
    text = (project_root / "prompts/agent.system.skills.md").read_text(
        encoding="utf-8"
    )

    assert "{{skills}}" in text


def test_corrected_tool_prompts_only_teach_action_contract():
    project_root = Path(__file__).resolve().parents[1]
    prompt_paths = [
        project_root / "plugins/_text_editor/prompts/agent.system.tool.text_editor.md",
        project_root / "prompts/agent.system.tool.skills.md",
        project_root / "prompts/agent.system.tool.scheduler.md",
        project_root / "plugins/_a0_connector/prompts/agent.system.tool.text_editor_remote.md",
        project_root / "plugins/_office/prompts/agent.system.tool.document_artifact.md",
        project_root / "plugins/_office/skills/document-artifacts/SKILL.md",
        project_root / "plugins/_office/skills/markdown-documents/SKILL.md",
        project_root / "plugins/_office/skills/writer-documents/SKILL.md",
        project_root / "plugins/_office/skills/calc-spreadsheets/SKILL.md",
        project_root / "plugins/_office/skills/impress-presentations/SKILL.md",
    ]
    forbidden = (
        "text_editor:",
        "skills_tool:",
        "scheduler:",
        "document_artifact:",
        "`method`",
        "`op`",
        "`operation`",
        "alias",
    )

    for path in prompt_paths:
        text = path.read_text(encoding="utf-8")
        assert "action" in text
        for token in forbidden:
            assert token not in text
        if "document" in path.name or "_office/skills" in str(path):
            assert "faux UI action labels" in text
            assert "Open document" in text
            assert "Download file" in text
            assert "Canvas was not opened automatically" not in text
            assert "Open Document, or Desktop edit actions" not in text


def test_computer_use_remote_is_skill_gated():
    project_root = Path(__file__).resolve().parents[1]
    prompt_path = (
        project_root
        / "plugins/_a0_connector/prompts/agent.system.tool.computer_use_remote.md"
    )
    skill_text = (
        project_root
        / "plugins/_a0_connector/skills/host-computer-use/SKILL.md"
    ).read_text(encoding="utf-8")

    assert not prompt_path.exists()
    assert '"tool_name": "computer_use_remote"' in skill_text
    assert "Beta desktop control" in skill_text
