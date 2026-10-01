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


def test_model_preset_editor_select_shows_selected_preset_on_open() -> None:
    preset_modal = read("plugins", "_model_config", "webui", "main.html")

    # x-model syncs the select value before the x-for template renders the
    # <option> elements, so the browser falls back to the first option
    # ("Default") while Alpine's selectedKey still points at the real preset.
    # Selecting that same first option then fires no change event. The :selected
    # binding keeps the DOM selection in sync with the model.
    assert ':selected="preset._key === selectedKey"' in preset_modal


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


def test_preset_editor_nests_one_conditional_vision_selector_in_main() -> None:
    preset_modal = read("plugins", "_model_config", "webui", "main.html")
    model_field = read("plugins", "_model_config", "webui", "model-field.html")
    preset_overview = read("plugins", "_model_config", "webui", "preset-overview.html")
    preset_store = read("plugins", "_model_config", "webui", "model-config-store.js")

    main_start = preset_modal.index('<div class="section-title">Main Model</div>')
    utility_start = preset_modal.index('<div class="section-title">Utility Model</div>')
    selector_start = preset_modal.index('class="vision-sidecar-selector"')
    supports_start = model_field.index('<div class="field-title">Supports Vision</div>')
    override_start = model_field.index('<div class="field-title">Use separate Vision Model</div>')
    context_start = model_field.index('<div class="field-title">Context window size</div>')
    advanced_start = model_field.index('<!-- Advanced Settings (collapsed by default) -->')
    vision_advanced_start = model_field.index('<template x-if="modelType === \'vision\'">')
    vision_advanced_end = model_field.index('<!-- Utility-specific: ctx_input slider -->')
    vision_advanced = model_field[vision_advanced_start:vision_advanced_end]

    assert '<div class="section-title">Vision Model</div>' not in preset_modal
    assert preset_modal.count('class="vision-sidecar-selector"') == 1
    assert main_start < selector_start < utility_start
    assert '!selectedPreset.chat.vision || selectedPreset.vision.override_main' in preset_modal
    assert "get visionModel() { return selectedPreset.vision; }" in preset_modal
    assert "modelType: 'vision'" in preset_modal
    assert preset_modal.count("apiKeyMode: 'store'") == 4
    assert "margin: 0.75rem 0 0;" in preset_modal
    assert "padding: 0.25rem 0 0;" in preset_modal
    assert "border-left: 2px solid var(--color-border);" not in preset_modal
    assert "Use separate Vision Model" in model_field
    assert supports_start < override_start < context_start < advanced_start
    assert "When disabled, vision_load uses this model's native vision." in model_field
    assert "When enabled, vision_load uses the preset's Vision Model" not in model_field
    assert 'x-model="visionModel.override_main"' in model_field
    assert '<div class="advanced-section" x-data="{ advOpen: false }">' in model_field
    assert advanced_start < vision_advanced_start
    assert model_field.count('<div class="field-title">Timeout (seconds)</div>') == 1
    assert model_field.count('<div class="field-title">Max tokens</div>') == 1
    assert 'x-model.number="model.timeout"' in vision_advanced
    assert 'x-model.number="model.max_tokens"' in vision_advanced
    assert "How long to wait for the Vision Model." in vision_advanced
    assert "Maximum output tokens for each delegated vision call." in vision_advanced
    assert "Agent Editor &gt; Advanced &gt; Prompt files" in vision_advanced
    assert "fw.vision_load.md" in vision_advanced
    assert "delegated_system" not in model_field
    assert "vision prompt" not in model_field[:vision_advanced_start].lower()
    assert "timeout: 300" in preset_store
    assert "max_tokens: 2000" in preset_store
    assert "value?.timeout ?? kwargs.timeout ?? 300" in preset_store
    assert "value?.max_tokens ?? kwargs.max_tokens ?? 2000" in preset_store
    assert "delete kwargs.timeout;" in preset_store
    assert "delete kwargs.max_tokens;" in preset_store
    assert "_kwargs_text: kwargsToText(vision.kwargs)" in preset_store
    assert "model-preset-row-nested" in preset_overview
    assert "model.title === 'Vision'" in preset_overview
    assert preset_overview.count("model.title !== 'Vision'") == 2
    assert '<span class="model-preset-role">Vision override</span>' in preset_overview
    assert "'model-preset-identity-vision': model.title === 'Vision'" in preset_overview
    assert "grid-column: 3;" in preset_overview
    assert "padding-top: var(--spacing-xs);" in preset_overview
    assert "margin-left: 2rem;" not in preset_overview
    assert "border-left: 1px solid var(--color-border);" not in preset_overview
    assert "if (slotKey === 'vision') config[sectionKey] = {};" in preset_store
    assert "['chat', 'vision', 'utility']" in preset_store


def test_plugin_settings_reset_is_explicit_and_does_not_capture_toast_early() -> None:
    settings_modal = read("webui", "components", "plugins", "plugin-settings.html")
    settings_store = read("webui", "components", "plugins", "plugin-settings-store.js")

    assert "Reset to default" in settings_modal
    assert "const justToast = globalThis.justToast" not in settings_store
    assert 'globalThis.justToast?.("Settings reset to default.", "info")' in settings_store
