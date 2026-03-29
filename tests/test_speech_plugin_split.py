from __future__ import annotations

import sys
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
        "plugins/_whisper_stt/extensions/python/system_prompt/_20_voice_transcription.py",
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


def test_voice_prompt_rule_moves_to_whisper_plugin() -> None:
    core_prompt = (PROJECT_ROOT / "prompts/agent.system.main.communication_additions.md").read_text(
        encoding="utf-8"
    )
    whisper_prompt = (PROJECT_ROOT / "plugins/_whisper_stt/prompts/agent.system.voice_transcription.md").read_text(
        encoding="utf-8"
    )
    voice_surface = (PROJECT_ROOT / "webui/components/settings/agent/voice.html").read_text(
        encoding="utf-8"
    )

    assert "if starts (voice) then transcribed can contain errors consider compensation" not in core_prompt
    assert "if starts (voice) then transcribed can contain errors consider compensation" in whisper_prompt
    assert '<x-extension id="voice-settings-start"></x-extension>' in voice_surface
    assert '<x-extension id="voice-settings-main"></x-extension>' in voice_surface
    assert '<x-extension id="voice-settings-end"></x-extension>' in voice_surface
