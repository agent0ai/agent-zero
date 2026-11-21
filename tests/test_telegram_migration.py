import hashlib
import json
from pathlib import Path
import re

import pytest

from helpers import files, plugins
from plugins._telegram_integration.helpers import migration, scopes
from plugins._telegram_integration.helpers.constants import STATE_FILE
from test_telegram_config_scope import PLUGIN, SCOPES, telegram_config


def write_config(project, profile, config):
    path = Path(plugins.determine_plugin_asset_path(PLUGIN, project, profile, plugins.CONFIG_FILE_NAME))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config))
    return path


def backup_files():
    root = Path(files.get_abs_path(migration.BACKUP_DIR))
    manifest = json.loads((root / "manifest.json").read_bytes())
    result = {}
    for entry in manifest["files"]:
        path = root / entry["backup"]
        contents = path.read_bytes()
        assert hashlib.sha256(contents).hexdigest() == entry["sha256"]
        assert path.stat().st_mode & 0o777 == 0o600
        result[entry["path"]] = contents
    assert root.stat().st_mode & 0o777 == 0o700
    assert (root / "manifest.json").stat().st_mode & 0o777 == 0o600
    return result


@pytest.mark.parametrize("project,profile", SCOPES)
def test_upgrade_preserves_every_setting_activation_and_session_mapping(telegram_config, project, profile):
    config = {"custom_top_level": {"retained": True}, "bots": [{
        "name": "My bot & caffè ", "token": "654321:existing", "enabled": True,
        "mode": "polling", "allowed_users": [111], "admin_users": [111],
        "group_mode": "mention", "agent_instructions": "Keep my instructions",
        "default_project": project, "user_projects": {"111": project},
        "welcome_enabled": True, "attachment_max_age_hours": 24, "future_field": [1, 2],
    }]}
    path = write_config(project, profile, config)
    plugins.toggle_plugin(PLUGIN, False)
    plugins.toggle_plugin(PLUGIN, True, project, profile)
    state = Path(files.get_abs_path(STATE_FILE))
    state.write_text(json.dumps({"chats": {"scope_test:111:111": "existing-chat"}, "other": {"kept": True}}))
    sources = [entry["path"] for pattern in (plugins.CONFIG_FILE_NAME, plugins.TOGGLE_FILE_PATTERN)
               for entry in plugins.find_plugin_assets(pattern, plugin_name=PLUGIN)] + [str(state)]
    originals = {files.deabsolute_path(path): Path(path).read_bytes() for path in sources}
    migration.prepare_upgrade()
    assert backup_files() == originals
    for relative, contents in originals.items():
        assert Path(files.get_abs_path(relative)).read_bytes() == contents
    assert json.loads(path.read_bytes()) == config
    assert scopes.configured_bots()[0].key == "scope_test"
    assert next(bot for bot in scopes.configured_bots() if bot.project == project and bot.profile == profile).config["name"] == "My bot & caffè "
    # Later saves must never replace the pre-upgrade backup or be undone on restart.
    config["bots"][0]["allowed_users"] = [222]
    path.write_text(json.dumps(config))
    migration.prepare_upgrade()
    assert backup_files() == originals
    assert json.loads(path.read_bytes()) == config


@pytest.mark.parametrize("secret", [None, "", "old-short-secret", "x" * 32])
def test_legacy_webhooks_gain_a_secure_secret_without_resetting_configuration(telegram_config, secret):
    config = {"other": "preserved", "bots": [{
        "name": "Old bot", "token": "123456:fake", "enabled": True,
        "mode": "webhook", "webhook_url": "https://example.invalid", "allowed_users": [111],
    }]}
    if secret is not None:
        config["bots"][0]["webhook_secret"] = secret
    path = write_config("", "", config)
    original = path.read_bytes()
    migration.prepare_upgrade()
    upgraded = json.loads(path.read_bytes())
    new_secret = upgraded["bots"][0]["webhook_secret"]
    assert re.fullmatch(r"[A-Za-z0-9_-]{32,256}", new_secret)
    expected = {**config, "bots": [{**config["bots"][0], "webhook_secret": new_secret}]}
    assert upgraded == expected
    assert "admin_users" not in upgraded["bots"][0]
    assert backup_files()[files.deabsolute_path(str(path))] == original
    if secret == "x" * 32:
        assert path.read_bytes() == original
    migration.prepare_upgrade()
    assert json.loads(path.read_bytes()) == upgraded


def test_migration_resumes_after_partial_write_without_losing_original_backups(telegram_config, monkeypatch):
    old = {"bots": [{"name": "old", "token": "123456:fake", "mode": "webhook", "enabled": True}]}
    first = write_config("", "", old)
    second = write_config("project", "profile", {"bots": [{**old["bots"][0], "token": "654321:scoped"}]})
    originals = {files.deabsolute_path(str(path)): path.read_bytes() for path in (first, second)}
    write = migration._write_private
    def fail_second(path, data):
        if path == second:
            raise OSError("Simulated interrupted migration")
        write(path, data)
    monkeypatch.setattr(migration, "_write_private", fail_second)
    with pytest.raises(OSError):
        migration.prepare_upgrade()
    root = Path(files.get_abs_path(migration.BACKUP_DIR))
    assert not (root / "complete.json").exists()
    first_secret = json.loads(first.read_bytes())["bots"][0]["webhook_secret"]
    assert second.read_bytes() == originals[files.deabsolute_path(str(second))]
    assert backup_files() == originals
    monkeypatch.setattr(migration, "_write_private", write)
    migration.prepare_upgrade()
    assert (root / "complete.json").exists()
    assert json.loads(first.read_bytes())["bots"][0]["webhook_secret"] == first_secret
    assert json.loads(second.read_bytes())["bots"][0]["webhook_secret"]
    assert backup_files() == originals


def test_upgrade_preserves_symlinked_configuration(telegram_config, tmp_path):
    path = write_config("", "", {"bots": [{"name": "old", "token": "123456:fake", "mode": "webhook"}]})
    target = tmp_path / "telegram-config.json"
    path.rename(target)
    path.symlink_to(target)
    original = target.read_bytes()
    migration.prepare_upgrade()
    assert path.is_symlink()
    assert path.resolve() == target
    assert json.loads(target.read_bytes())["bots"][0]["webhook_secret"]
    assert backup_files()[files.deabsolute_path(str(path))] == original


def test_snapshot_failure_does_not_change_any_configuration(telegram_config, monkeypatch):
    path = write_config("", "", {"bots": [{"name": "old", "token": "123456:fake", "mode": "webhook"}]})
    original = path.read_bytes()
    monkeypatch.setattr(migration, "_write_private", lambda *args: (_ for _ in ()).throw(OSError("disk full")))
    with pytest.raises(OSError):
        migration.prepare_upgrade()
    assert path.read_bytes() == original
    assert not Path(files.get_abs_path(migration.BACKUP_DIR, "complete.json")).exists()
