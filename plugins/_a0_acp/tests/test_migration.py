from pathlib import Path

from plugins._a0_acp.extensions.python.startup_migration._10_migrate_legacy_acp import (
    migrate_legacy_acp,
)


def test_migrate_legacy_acp_removes_all_stale_plugin_roots(tmp_path: Path) -> None:
    stale_roots = [
        tmp_path / "usr" / "plugins" / "a0_acp",
        tmp_path / "usr" / "projects" / "demo" / ".a0proj" / "plugins" / "a0_acp",
        tmp_path / "usr" / "agents" / "reviewer" / "plugins" / "a0_acp",
    ]
    bundled_config = tmp_path / "usr" / "plugins" / "_a0_acp" / "config.json"

    for root in stale_roots:
        (root / ".git").mkdir(parents=True)
        (root / "plugin.yaml").write_text("name: a0_acp\n", encoding="utf-8")
        (root / ".git" / "config").write_text("[core]\n", encoding="utf-8")
    bundled_config.parent.mkdir(parents=True)
    bundled_config.write_text('{"enabled": true}\n', encoding="utf-8")

    result = migrate_legacy_acp(tmp_path)

    assert len(result["removed_roots"]) == len(stale_roots)
    assert result["errors"] == []
    assert all(not root.exists() for root in stale_roots)
    assert bundled_config.read_text(encoding="utf-8") == '{"enabled": true}\n'
    assert migrate_legacy_acp(tmp_path) == {"removed_roots": [], "errors": []}
