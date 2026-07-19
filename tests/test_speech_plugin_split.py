from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from helpers import plugins, settings


def test_builtin_speech_plugins_are_discoverable_and_toggleable() -> None:
    discovered = {
        item.name: item
        for item in plugins.get_enhanced_plugins_list(
            custom=True,
            builtin=True,
            plugin_names=["_kokoro_tts", "_whisper_stt"],
        )
    }

    assert "_kokoro_tts" in discovered
    assert "_whisper_stt" in discovered

    assert discovered["_kokoro_tts"].always_enabled is False
    assert discovered["_whisper_stt"].always_enabled is False
    assert "agent" in discovered["_kokoro_tts"].settings_sections
    assert "agent" in discovered["_whisper_stt"].settings_sections


def test_legacy_core_speech_artifacts_are_removed() -> None:
    removed_paths = [
        "api/synthesize.py",
        "api/transcribe.py",
        "helpers/kokoro_tts.py",
        "helpers/whisper.py",
        "webui/components/chat/speech/speech-store.js",
        "webui/components/settings/agent/speech.html",
        "webui/components/settings/speech/microphone-setting-store.js",
        "webui/components/settings/speech/microphone.html",
        "webui/css/speech.css",
        "webui/js/speech_browser.js",
    ]

    for relative_path in removed_paths:
        assert not (PROJECT_ROOT / relative_path).exists(), relative_path


def test_plugin_owned_voice_files_exist() -> None:
    expected_paths = [
        "plugins/_kokoro_tts/plugin.yaml",
        "plugins/_kokoro_tts/api/synthesize.py",
        "plugins/_kokoro_tts/extensions/webui/page-head/runtime.html",
        "plugins/_kokoro_tts/extensions/webui/voice-settings-main/kokoro-card.html",
        "plugins/_whisper_stt/plugin.yaml",
        "plugins/_whisper_stt/api/transcribe.py",
        "plugins/_whisper_stt/extensions/webui/page-head/runtime.html",
        "plugins/_whisper_stt/extensions/webui/chat-input-box-end/microphone-button.html",
        "plugins/_whisper_stt/extensions/webui/voice-settings-main/whisper-card.html",
        "plugins/_whisper_stt/webui/whisper-stt-store.js",
    ]

    for relative_path in expected_paths:
        assert (PROJECT_ROOT / relative_path).exists(), relative_path


def test_core_settings_no_longer_expose_legacy_speech_keys() -> None:
    defaults = settings.get_default_settings()
    output = settings.convert_out(defaults)

    legacy_keys = {
        "tts_kokoro",
        "stt_model_size",
        "stt_language",
        "stt_silence_threshold",
        "stt_silence_duration",
        "stt_waiting_timeout",
    }

    assert legacy_keys.isdisjoint(defaults.keys())
    assert legacy_keys.isdisjoint(output["settings"].keys())
    assert "stt_models" not in output["additional"]


def test_voice_prefix_prompt_rule_is_removed() -> None:
    core_prompt = (PROJECT_ROOT / "prompts/agent.system.main.communication_additions.md").read_text(
        encoding="utf-8"
    )
    whisper_store = (
        PROJECT_ROOT / "plugins/_whisper_stt/webui/whisper-stt-store.js"
    ).read_text(encoding="utf-8")
    voice_surface = (PROJECT_ROOT / "webui/components/settings/agent/voice.html").read_text(
        encoding="utf-8"
    )

    assert "if starts (voice) then transcribed can contain errors consider compensation" not in core_prompt
    assert "(voice)" not in whisper_store
    assert not (
        PROJECT_ROOT / "plugins/_whisper_stt/prompts/agent.system.voice_transcription.md"
    ).exists()
    assert not (
        PROJECT_ROOT
        / "plugins/_whisper_stt/extensions/python/system_prompt/_20_voice_transcription.py"
    ).exists()
    assert '<x-extension id="voice-settings-start"></x-extension>' in voice_surface
    assert '<x-extension id="voice-settings-main"></x-extension>' in voice_surface
    assert '<x-extension id="voice-settings-end"></x-extension>' in voice_surface


def test_whisper_message_mode_defaults_to_send_and_supports_draft() -> None:
    sys.modules.setdefault(
        "whisper",
        types.SimpleNamespace(load_model=lambda *args, **kwargs: None),
    )
    runtime = importlib.import_module("plugins._whisper_stt.helpers.runtime")

    assert runtime.normalize_config({})["message_mode"] == "send"
    assert runtime.normalize_config({"message_mode": "draft"})["message_mode"] == "draft"
    assert runtime.normalize_config({"message_mode": "DRAFT"})["message_mode"] == "draft"
    assert runtime.normalize_config({"message_mode": "invalid"})["message_mode"] == "send"

    default_config = (
        PROJECT_ROOT / "plugins/_whisper_stt/default_config.yaml"
    ).read_text(encoding="utf-8")
    migration = (
        PROJECT_ROOT / "plugins/_whisper_stt/helpers/migration.py"
    ).read_text(encoding="utf-8")
    config_ui = (
        PROJECT_ROOT / "plugins/_whisper_stt/webui/config.html"
    ).read_text(encoding="utf-8")
    status_ui = (
        PROJECT_ROOT / "plugins/_whisper_stt/webui/main.html"
    ).read_text(encoding="utf-8")
    voice_card = (
        PROJECT_ROOT
        / "plugins/_whisper_stt/extensions/webui/voice-settings-main/whisper-card.html"
    ).read_text(encoding="utf-8")
    whisper_store = (
        PROJECT_ROOT / "plugins/_whisper_stt/webui/whisper-stt-store.js"
    ).read_text(encoding="utf-8")

    assert "message_mode: send" in default_config
    assert '"message_mode": "send"' in migration
    assert '<option value="send">Send immediately</option>' in config_ui
    assert '<option value="draft">Draft in composer</option>' in config_ui
    assert "messageModeLabel" in status_ui
    assert "messageModeLabel" in voice_card
    assert 'message_mode: "send"' in whisper_store
    assert 'status?.config?.message_mode === "draft" ? "draft" : "send"' in whisper_store
    assert "updateChatInput(message)" in whisper_store
    assert "sendMessage()" in whisper_store


def test_browser_tool_speech_action_uses_shared_tts_service() -> None:
    browser_handler = (
        PROJECT_ROOT
        / "plugins/_browser/extensions/webui/get_tool_message_handler/browser-tool-handler.js"
    ).read_text(encoding="utf-8")

    assert "/components/chat/speech/speech-store.js" not in browser_handler
    assert "/js/tts-service.js" in browser_handler
    assert "ttsService.speak(contentText)" in browser_handler


def test_chat_bar_keeps_existing_send_and_mic_icon_contract() -> None:
    chat_bar = (
        PROJECT_ROOT / "webui/components/chat/input/chat-bar-input.html"
    ).read_text(encoding="utf-8")
    mic_extension = (
        PROJECT_ROOT
        / "plugins/_whisper_stt/extensions/webui/chat-input-box-end/microphone-button.html"
    ).read_text(encoding="utf-8")
    whisper_store = (
        PROJECT_ROOT / "plugins/_whisper_stt/webui/whisper-stt-store.js"
    ).read_text(encoding="utf-8")
    whisper_css = (
        PROJECT_ROOT / "plugins/_whisper_stt/webui/whisper-stt.css"
    ).read_text(encoding="utf-8")

    assert 'id="send-button"' in chat_bar
    assert 'x-text="$store.chatInput.sendButtonIcon"' in chat_bar
    assert ':class="$store.chatInput.sendButtonClass"' in chat_bar
    assert ':title="$store.chatInput.sendButtonTitle"' in chat_bar

    assert 'id="microphone-button"' in mic_extension
    assert "<svg" in mic_extension
    assert "material-symbols-outlined" not in mic_extension
    assert "buttonIcon" not in mic_extension
    assert 'title=' not in mic_extension
    assert 'x-effect="$store.whisperStt.updateMicrophoneButtonUI()"' in mic_extension
    assert 'x-init="$store.whisperStt.updateMicrophoneButtonUI()"' in mic_extension
    assert "updateMicrophoneButtonUI()" in whisper_store
    assert "data-status" in whisper_store
    assert 'setAttribute("title"' not in whisper_store
    assert 'removeAttribute("title")' in whisper_store
    assert 'removeAttribute("data-bs-original-title")' in whisper_store
    assert "this.updateMicrophoneButtonUI();" in whisper_store
    assert "sttService.emitStatusChange(this.micStatus)" in whisper_store

    for state in [
        "disabled",
        "inactive",
        "activating",
        "listening",
        "recording",
        "waiting",
        "processing",
    ]:
        assert f'"mic-{state}"' in whisper_store
        assert f"#microphone-button.mic-{state}" in whisper_css
        assert f"#microphone-button.mic-{state}" in mic_extension

    assert "border-radius: 12px;" in whisper_css
    assert "background-color: transparent;" in whisper_css
    assert "#microphone-button.mic-inactive {\n  color: grey;" in whisper_css
    assert "background-color: grey;" not in whisper_css
    assert "#microphone-button.mic-listening {\n  color: red;" in whisper_css
    assert "#microphone-button.mic-recording {\n  color: green;" in whisper_css
    assert "#microphone-button.mic-waiting {\n  color: teal;" in whisper_css
    assert "#microphone-button.mic-processing {\n  color: darkcyan;" in whisper_css
    assert "#microphone-button.mic-activating svg" in whisper_css
    assert "#microphone-button.mic-processing svg" in whisper_css
    assert "#microphone-button:not(.mic-disabled):hover svg" in whisper_css
    assert "#microphone-button:not(.mic-disabled):active svg" in whisper_css
    assert "box-shadow: none;" in whisper_css
    assert "order: 1;" in mic_extension
    assert "whisper-stt-mic-pulse 0.8s infinite" in mic_extension
    assert "whisper-stt-mic-pulse 0.8s infinite" in whisper_css
