from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read(*parts: str) -> str:
    return PROJECT_ROOT.joinpath(*parts).read_text(encoding="utf-8")


def test_model_config_text_buttons_have_shared_primitive() -> None:
    buttons_css = read("webui", "css", "buttons.css")
    preset_modal = read("plugins", "_model_config", "webui", "main.html")
    overview = read("plugins", "_model_config", "webui", "preset-overview.html")

    assert ".text-button {" in buttons_css
    assert "appearance: none;" in buttons_css
    assert ".text-button:hover:not(:disabled)" in buttons_css
    assert ".text-button .material-symbols-outlined" in buttons_css
    assert 'class="text-button"' in preset_modal
    assert 'class="model-preset-actions"' in overview


def test_model_preset_rows_keep_stable_identity_after_middle_delete() -> None:
    preset_modal = read("plugins", "_model_config", "webui", "main.html")
    preset_store = read("plugins", "_model_config", "webui", "model-config-store.js")

    assert 'x-data="$store.modelConfig.createPresetEditor($store.modelConfig.presetEditorInitialName)"' in preset_modal
    assert ':key="preset._key"' in preset_modal
    assert 'x-model.number="selectedKey"' in preset_modal
    assert "createPresetEditor(initialName = '')" in preset_store
    assert "preparePresetEditor($store.chats?.selected || '')" in preset_modal
    assert "_key: nextPresetKey++" in preset_store
    assert "removeSelectedPreset()" in preset_store
    assert "selectedKey" in preset_store
    assert ':key="idx"' not in preset_modal
    assert "JSON.parse(JSON.stringify" not in preset_modal
    assert "presets.splice" not in preset_store


def test_model_preset_editor_can_reset_to_bundled_defaults() -> None:
    preset_modal = read("plugins", "_model_config", "webui", "main.html")
    preset_store = read("plugins", "_model_config", "webui", "model-config-store.js")

    assert '$confirmClick($event, () => resetPresets())' in preset_modal
    assert "Restore bundled presets" in preset_modal
    assert "async resetPresets()" in preset_store
    assert "if (!await store.resetGlobalPresets()) return;" in preset_store
    assert "this.refreshPresets();" in preset_store


def test_default_preset_is_locked_and_shared_overview_is_reused() -> None:
    preset_modal = read("plugins", "_model_config", "webui", "main.html")
    config_modal = read("plugins", "_model_config", "webui", "config.html")
    settings_summary = read("plugins", "_model_config", "webui", "models-summary.html")
    helper = read("plugins", "_model_config", "helpers", "model_config.py")

    assert '<template x-if="canRenameSelected">' in preset_modal
    assert "get canRenameSelected()" in read(
        "plugins", "_model_config", "webui", "model-config-store.js"
    )
    assert "Default cannot be renamed or deleted." not in preset_modal
    assert ":readonly=" not in preset_modal
    assert "The Default preset cannot be deleted or renamed." in helper
    assert "preserveImplicitDefaults" in read(
        "plugins", "_model_config", "webui", "model-config-store.js"
    )
    component_path = "/plugins/_model_config/webui/preset-overview.html"
    assert component_path in config_modal
    assert component_path in settings_summary
    assert "Per-project / agent" in read(
        "plugins", "_model_config", "webui", "preset-overview.html"
    )


def test_preset_editor_uses_standard_modal_footer_buttons() -> None:
    preset_modal = read("plugins", "_model_config", "webui", "main.html")
    api_keys_modal = read("plugins", "_model_config", "webui", "api-keys.html")

    for content in (preset_modal, api_keys_modal):
        assert '<div class="modal-footer" data-modal-footer>' in content
        assert 'class="btn btn-ok"' in content
        assert 'class="btn btn-cancel"' in content

    assert "preset-editor-footer" not in preset_modal


def test_plugin_settings_reset_is_explicit_and_does_not_capture_toast_early() -> None:
    settings_modal = read("webui", "components", "plugins", "plugin-settings.html")
    settings_store = read("webui", "components", "plugins", "plugin-settings-store.js")

    assert "Reset to default" in settings_modal
    assert "const justToast = globalThis.justToast" not in settings_store
    assert 'globalThis.justToast?.("Settings reset to default.", "info")' in settings_store
