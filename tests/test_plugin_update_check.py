import asyncio
import datetime
import importlib
import sys
from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers import files, plugins


def test_custom_plugin_list_uses_persisted_update_status(tmp_path, monkeypatch):
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    plugin_dir = tmp_path / "usr/plugins/demo"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.yaml").write_text("name: demo\ntitle: Demo\n", encoding="utf-8")

    plugins.save_custom_plugin_updates(
        [
            plugins.PluginUpdateInfo(
                name="demo",
                path=str(plugin_dir),
                commits_since_local=2,
            )
        ],
        "2026-08-29T12:00:00+00:00",
    )

    item = plugins.get_enhanced_plugins_list(
        custom=True, builtin=False, plugin_names=["demo"]
    )[0]
    assert item.update_available is True
    assert item.update_commits == 2

    plugins.clear_custom_plugin_update("demo")
    item = plugins.get_enhanced_plugins_list(
        custom=True, builtin=False, plugin_names=["demo"]
    )[0]
    assert item.update_available is False
    assert item.update_commits == 0


def test_update_status_cleanup_cannot_fail_a_completed_plugin_update(monkeypatch):
    update = plugins.PluginUpdateInfo(name="demo", path="/a0/usr/plugins/demo")

    def fail_save(*_args):
        raise OSError("read-only state")

    monkeypatch.setattr(
        plugins,
        "get_custom_plugin_update_state",
        lambda: ("2026-08-29T12:00:00+00:00", {"demo": update}),
    )
    monkeypatch.setattr(plugins, "save_custom_plugin_updates", fail_save)

    plugins.clear_custom_plugin_update("demo")


def test_custom_plugin_update_controls_use_the_shared_updater():
    list_html = (PROJECT_ROOT / "webui/components/plugins/list/plugin-list.html").read_text(
        encoding="utf-8"
    )
    list_store = (
        PROJECT_ROOT / "webui/components/plugins/list/pluginListStore.js"
    ).read_text(encoding="utf-8")
    installer_store = (
        PROJECT_ROOT / "plugins/_plugin_installer/webui/pluginInstallStore.js"
    ).read_text(encoding="utf-8")
    update_check = (
        PROJECT_ROOT / "extensions/python/user_message_ui/_10_update_check.py"
    ).read_text(encoding="utf-8")

    assert "plugin.update_available" in list_html
    assert "pluginListStore.updatePlugin(plugin)" in list_html
    assert "pluginInstallStore.updatePlugin(plugin)" in list_store
    assert "window.ensureModalOpen || window.openModal" in list_store
    assert 'action: "update_plugin"' in installer_store
    assert "custom_plugin_updates_available" in update_check
    assert "pluginListStore.open" in update_check


def test_daily_plugin_check_persists_updates_and_notifies(monkeypatch):
    update_check = importlib.import_module(
        "extensions.python.user_message_ui._10_update_check"
    )
    updates = [
        plugins.PluginUpdateInfo(
            name="demo",
            path="/a0/usr/plugins/demo",
            commits_since_local=1,
        )
    ]
    saved = []
    sent = []

    async def fake_to_thread(callback, plugin_names):
        assert callback is plugins.get_custom_plugins_updates
        assert plugin_names is None
        return updates

    monkeypatch.setattr(update_check, "last_plugin_check", datetime.datetime.min.replace(tzinfo=datetime.UTC))
    monkeypatch.setattr(
        update_check.plugins,
        "get_custom_plugin_update_state",
        lambda: ("2026-08-28T00:00:00+00:00", {"demo": updates[0]}),
    )
    monkeypatch.setattr(update_check.plugins, "save_custom_plugin_updates", lambda *args: saved.append(args))
    monkeypatch.setattr(update_check.asyncio, "to_thread", fake_to_thread)
    checker = update_check.UpdateCheck(
        SimpleNamespace(
            context=SimpleNamespace(
                get_notification_manager=lambda: SimpleNamespace(
                    send_notification=lambda **kwargs: sent.append(kwargs)
                )
            )
        )
    )

    asyncio.run(
        checker.check_plugin_updates(
            datetime.datetime(2026, 8, 29, tzinfo=datetime.UTC)
        )
    )

    assert saved == [(updates, "2026-08-29T00:00:00+00:00")]
    assert sent[0]["id"] == "custom_plugin_updates_available"
    assert "pluginListStore.open" in sent[0]["message"]


def test_plugin_check_preserves_good_state_and_retries_only_failures(monkeypatch):
    update_check = importlib.import_module(
        "extensions.python.user_message_ui._10_update_check"
    )
    checked_at = "2026-08-28T00:00:00+00:00"
    previous = plugins.PluginUpdateInfo(
        name="demo",
        path="/a0/usr/plugins/demo",
        commits_since_local=2,
    )
    failed = previous.model_copy(
        update={"commits_since_local": 0, "error": "remote unavailable"}
    )
    recovered = previous.model_copy(update={"commits_since_local": 3})
    state = {"checked_at": checked_at, "updates": {"demo": previous}}
    requested = []
    saved = []

    async def fake_to_thread(callback, plugin_names):
        assert callback is plugins.get_custom_plugins_updates
        requested.append(plugin_names)
        return [failed] if len(requested) == 1 else [recovered]

    def save(updates, saved_checked_at):
        saved.append((updates, saved_checked_at))
        state["checked_at"] = saved_checked_at
        state["updates"] = {update.name: update for update in updates}

    monkeypatch.setattr(
        update_check,
        "last_plugin_check",
        datetime.datetime.min.replace(tzinfo=datetime.UTC),
    )
    monkeypatch.setattr(
        update_check.plugins,
        "get_custom_plugin_update_state",
        lambda: (state["checked_at"], state["updates"]),
    )
    monkeypatch.setattr(update_check.plugins, "save_custom_plugin_updates", save)
    monkeypatch.setattr(update_check.asyncio, "to_thread", fake_to_thread)
    checker = update_check.UpdateCheck(None)

    asyncio.run(
        checker.check_plugin_updates(
            datetime.datetime(2026, 8, 29, 1, tzinfo=datetime.UTC)
        )
    )
    assert requested == [None]
    assert saved[-1][0][0].commits_since_local == 2
    assert saved[-1][0][0].error == "remote unavailable"
    assert saved[-1][1] == checked_at

    asyncio.run(
        checker.check_plugin_updates(
            datetime.datetime(2026, 8, 29, 1, 30, tzinfo=datetime.UTC)
        )
    )
    assert requested == [None]

    asyncio.run(
        checker.check_plugin_updates(
            datetime.datetime(2026, 8, 29, 2, tzinfo=datetime.UTC)
        )
    )
    assert requested == [None, ["demo"]]
    assert saved[-1][0][0].commits_since_local == 3
    assert saved[-1][0][0].error == ""
    assert saved[-1][1] == "2026-08-29T02:00:00+00:00"


def test_plugin_check_is_scheduled_outside_the_user_message_request(monkeypatch):
    update_check = importlib.import_module(
        "extensions.python.user_message_ui._10_update_check"
    )
    scheduled = []

    class FakeDeferredTask:
        def start_task(self, callback, *args):
            scheduled.append((callback, args))

    async def fake_check_version():
        return {}

    monkeypatch.setattr(
        update_check,
        "last_check",
        datetime.datetime.min.replace(tzinfo=datetime.UTC),
    )
    monkeypatch.setattr(update_check, "DeferredTask", FakeDeferredTask)
    monkeypatch.setattr(update_check.update_check, "check_version", fake_check_version)
    monkeypatch.setattr(
        update_check.settings,
        "get_settings",
        lambda: {"update_check_enabled": True},
    )
    checker = update_check.UpdateCheck(SimpleNamespace())

    asyncio.run(checker.execute())

    assert scheduled == [(checker.check_plugin_updates, (update_check.last_check,))]
