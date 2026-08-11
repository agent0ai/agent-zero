import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.plugins import Plugins
from helpers import files, plugins


def test_plugins_list_uses_binary_toggle_instead_of_advanced_dropdown():
    html = (PROJECT_ROOT / "webui/components/plugins/list/plugin-list.html").read_text(
        encoding="utf-8"
    )
    store = (
        PROJECT_ROOT / "webui/components/plugins/list/pluginListStore.js"
    ).read_text(encoding="utf-8")

    assert "plugin-status-toggle" in html
    assert "plugin-status-select" not in html
    assert "Open Advanced" not in html
    assert 'value="advanced"' not in html
    assert "openPluginAdvancedToggle" not in store
    assert "plugin-toggle-advanced.html" not in store


def test_advanced_plugin_toggle_modal_was_removed():
    assert not (
        PROJECT_ROOT / "webui/components/plugins/toggle/plugin-toggle-advanced.html"
    ).exists()


def test_list_toggle_state_is_global_even_when_scoped_rules_exist(monkeypatch):
    monkeypatch.setattr(
        plugins,
        "get_plugin_meta",
        lambda _plugin_name: SimpleNamespace(always_enabled=False),
    )
    monkeypatch.setattr(
        plugins,
        "get_plugin_roots",
        lambda _plugin_name: ["plugins/example", "usr/plugins/example"],
    )
    monkeypatch.setattr(
        plugins,
        "determined_toggle_from_paths",
        lambda _default, _paths: False,
    )

    def fail_on_scoped_lookup(*_args, **_kwargs):
        raise AssertionError("Plugin list toggle state should not inspect scoped rules")

    monkeypatch.setattr(plugins, "find_plugin_assets", fail_on_scoped_lookup)

    assert plugins.get_toggle_state("example") == "disabled"


def test_always_enabled_plugin_ignores_disable_files_at_runtime(monkeypatch):
    monkeypatch.setattr(plugins.cache, "get", lambda *args, **kwargs: None)
    monkeypatch.setattr(plugins.cache, "add", lambda *args, **kwargs: None)
    monkeypatch.setattr(plugins, "get_plugins_list", lambda: ["_required"])
    monkeypatch.setattr(
        plugins,
        "get_plugin_meta",
        lambda _plugin_name: SimpleNamespace(always_enabled=True),
    )

    def fail_on_toggle_lookup(*_args, **_kwargs):
        raise AssertionError("always-enabled plugins must ignore toggle files")

    monkeypatch.setattr(plugins, "determined_toggle_from_paths", fail_on_toggle_lookup)

    assert plugins.get_enabled_plugins(None) == ["_required"]


def test_always_enabled_plugin_rejects_disable_attempt(monkeypatch):
    monkeypatch.setattr(
        plugins,
        "get_plugin_meta",
        lambda _plugin_name: SimpleNamespace(always_enabled=True),
    )

    with pytest.raises(ValueError, match="always enabled"):
        plugins.toggle_plugin.__wrapped__("_required", False)


def test_plugin_api_returns_bad_request_for_rejected_disable(monkeypatch):
    def reject(*_args, **_kwargs):
        raise ValueError('Plugin "_required" is always enabled.')

    monkeypatch.setattr(plugins, "toggle_plugin", reject)

    response = Plugins._toggle_plugin.__wrapped__(
        object.__new__(Plugins),
        {"plugin_name": "_required", "enabled": False},
    )

    assert response.status_code == 400
    assert "always enabled" in response.get_data(as_text=True)


def test_config_scope_activation_toggle_saves_immediately_for_selected_scope():
    html = (PROJECT_ROOT / "webui/components/plugins/plugin-settings.html").read_text(
        encoding="utf-8"
    )
    settings_store = (
        PROJECT_ROOT / "webui/components/plugins/plugin-settings-store.js"
    ).read_text(encoding="utf-8")
    toggle_store = (
        PROJECT_ROOT / "webui/components/plugins/toggle/plugin-toggle-store.js"
    ).read_text(encoding="utf-8")

    assert "@change=\"context.setPluginEnabled($event.target.checked)\"" in html
    assert "projectName: this.projectName || \"\"" in settings_store
    assert "agentProfileKey: this.agentProfileKey || \"\"" in settings_store
    assert (
        "async setEnabled(enabled, { projectName = this.projectName, "
        "agentProfileKey = this.agentProfileKey } = {})"
    ) in toggle_store
    assert "action: \"toggle_plugin\"" in toggle_store


def test_scoped_plugin_without_settings_form_exposes_configuration_index():
    list_html = (
        PROJECT_ROOT / "webui/components/plugins/list/plugin-list.html"
    ).read_text(encoding="utf-8")
    list_store = (
        PROJECT_ROOT / "webui/components/plugins/list/pluginListStore.js"
    ).read_text(encoding="utf-8")
    settings_html = (
        PROJECT_ROOT / "webui/components/plugins/plugin-settings.html"
    ).read_text(encoding="utf-8")
    settings_store = (
        PROJECT_ROOT / "webui/components/plugins/plugin-settings-store.js"
    ).read_text(encoding="utf-8")

    assert "canOpenPluginConfig(plugin)" in list_html
    assert "plugin?.per_project_config" in list_store
    assert "plugin?.per_agent_config" in list_store
    assert "!pluginMeta.per_project_config" in settings_store
    assert "!pluginMeta.per_agent_config" in settings_store
    assert "Scoped configurations" in settings_html
    assert "context.pluginMeta?.has_config_screen" in settings_html


def test_toggle_plugin_writes_project_scope_file_immediately(tmp_path, monkeypatch):
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    monkeypatch.setattr(plugins, "after_plugin_change", lambda *_args, **_kwargs: None)
    monkeypatch.setitem(
        sys.modules,
        "helpers.projects",
        SimpleNamespace(
            get_project_meta=lambda name, *sub_dirs: files.get_abs_path(
                "usr/projects",
                name,
                ".a0proj",
                *sub_dirs,
            )
        ),
    )

    plugins.toggle_plugin.__wrapped__("example", False, project_name="alpha")

    scoped_plugin_dir = (
        tmp_path / "usr/projects/alpha/.a0proj/plugins/example"
    )
    assert (scoped_plugin_dir / ".toggle-0").exists()
    assert not (scoped_plugin_dir / ".toggle-1").exists()

    plugins.toggle_plugin.__wrapped__("example", True, project_name="alpha")

    assert (scoped_plugin_dir / ".toggle-1").exists()
    assert not (scoped_plugin_dir / ".toggle-0").exists()
