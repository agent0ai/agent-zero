from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers import plugins
from plugins._commands.extensions.python.startup_migration._20_migrate_legacy_commands import (
    migrate_legacy_commands,
)


def test_migrate_legacy_commands_copies_user_data_and_disables_old_plugin(tmp_path: Path):
    legacy_root = tmp_path / "usr" / "plugins" / "commands"
    legacy_commands = legacy_root / "commands"
    legacy_skills = legacy_root / "skills" / "custom-skill"
    project_commands = (
        tmp_path
        / "usr"
        / "projects"
        / "demo"
        / ".a0proj"
        / "plugins"
        / "commands"
        / "commands"
    )
    new_commands = tmp_path / "usr" / "plugins" / "_commands" / "commands"

    legacy_commands.mkdir(parents=True)
    legacy_skills.mkdir(parents=True)
    project_commands.mkdir(parents=True)
    new_commands.mkdir(parents=True)

    (legacy_root / "plugin.yaml").write_text("name: commands\n", encoding="utf-8")
    (legacy_root / plugins.ENABLED_FILE_NAME).write_text("", encoding="utf-8")
    (legacy_commands / "demo.command.yaml").write_text(
        "name: demo\ndescription: Demo\ntype: text\ntemplate_path: demo.txt\n",
        encoding="utf-8",
    )
    (legacy_commands / "demo.txt").write_text("legacy demo\n", encoding="utf-8")
    (legacy_commands / "keep.command.yaml").write_text(
        "name: keep\ndescription: Keep\ntype: text\ntemplate_path: keep.txt\n",
        encoding="utf-8",
    )
    (new_commands / "keep.command.yaml").write_text("existing\n", encoding="utf-8")
    (project_commands / "project.command.yaml").write_text(
        "name: project\ndescription: Project\ntype: text\ntemplate_path: project.txt\n",
        encoding="utf-8",
    )
    (legacy_skills / "SKILL.md").write_text("---\nname: custom-skill\n---\n", encoding="utf-8")

    result = migrate_legacy_commands(tmp_path)

    assert result["copied_commands"] == 3
    assert result["copied_skills"] == 1
    assert result["disabled_roots"] == 2

    assert (new_commands / "demo.command.yaml").read_text(encoding="utf-8").startswith(
        "name: demo"
    )
    assert (new_commands / "demo.txt").read_text(encoding="utf-8") == "legacy demo\n"
    assert (new_commands / "keep.command.yaml").read_text(encoding="utf-8") == "existing\n"
    assert (
        tmp_path
        / "usr"
        / "projects"
        / "demo"
        / ".a0proj"
        / "plugins"
        / "_commands"
        / "commands"
        / "project.command.yaml"
    ).exists()
    assert (
        tmp_path
        / "usr"
        / "plugins"
        / "_commands"
        / "skills"
        / "custom-skill"
        / "SKILL.md"
    ).exists()
    assert not (legacy_root / plugins.ENABLED_FILE_NAME).exists()
    assert (legacy_root / plugins.DISABLED_FILE_NAME).exists()
    assert (
        tmp_path
        / "usr"
        / "projects"
        / "demo"
        / ".a0proj"
        / "plugins"
        / "commands"
        / plugins.DISABLED_FILE_NAME
    ).exists()
