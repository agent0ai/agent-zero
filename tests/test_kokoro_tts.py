from __future__ import annotations

import asyncio
import base64
import json
from pathlib import Path

from plugins._kokoro_tts.api.synthesize import Synthesize
from plugins._kokoro_tts.helpers import runtime


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_config_keeps_legacy_voice_and_normalizes_weighted_blends() -> None:
    legacy = runtime.normalize_config(
        {"voice": "custom/voice.pt", "speed": 2.2}
    )
    assert legacy == {
        "voice": "custom/voice.pt",
        "voice_weights": {},
        "speed": 2.2,
    }

    weighted = runtime.normalize_config(
        {
            "voice": "ignored_when_weights_are_present",
            "voice_weights": {
                "af_heart": "3",
                "am_puck": 1,
                "../bad.pt": 5,
                "am_onyx": float("nan"),
                "am_echo": 0,
            },
            "speed": float("inf"),
        }
    )
    assert weighted == {
        "voice": "af_heart,am_puck",
        "voice_weights": {"af_heart": 3.0, "am_puck": 1.0},
        "speed": 1.1,
    }


def test_weighted_blend_reuses_the_existing_pipeline() -> None:
    class FakePipeline:
        packs = {"af_heart": 2.0, "am_puck": 10.0}

        def __init__(self) -> None:
            self.loaded: list[str] = []

        def load_single_voice(self, voice: str) -> float:
            self.loaded.append(voice)
            return self.packs[voice]

    pipeline = FakePipeline()
    blend = runtime._resolve_voice(
        pipeline,
        "legacy",
        {"af_heart": 3.0, "am_puck": 1.0},
    )

    assert blend == 4.0
    assert pipeline.loaded == ["af_heart", "am_puck"]
    assert runtime._resolve_voice(pipeline, "am_puck,am_onyx", {}) == (
        "am_puck,am_onyx"
    )


def test_synthesis_forwards_normalized_weights(monkeypatch) -> None:
    captured: dict = {}

    async def fake_synthesize(payload, **kwargs):
        captured.update({"sentences": payload["sentences"], **payload["config"]})
        return {"audio": "audio", "version": "0.9.2"}

    monkeypatch.setattr(runtime.worker, "acall", fake_synthesize)

    result = asyncio.run(
        runtime.synthesize_sentences(
            ["Hello"],
            {
                "voice": "legacy",
                "voice_weights": {"af_heart": 2, "am_puck": 1},
                "speed": 1.4,
            },
        )
    )

    assert result == "audio"
    assert captured == {
        "sentences": ["Hello"],
        "voice": "af_heart,am_puck",
        "voice_weights": {"af_heart": 2.0, "am_puck": 1.0},
        "speed": 1.4,
    }


def test_settings_expose_catalog_weights_and_speed_without_disk_blends() -> None:
    config_ui = (
        PROJECT_ROOT / "plugins/_kokoro_tts/webui/config.html"
    ).read_text(encoding="utf-8")
    store = (
        PROJECT_ROOT / "plugins/_kokoro_tts/webui/kokoro-tts-store.js"
    ).read_text(encoding="utf-8")

    assert "af_heart" in config_ui
    assert "am_puck" in config_ui
    assert "am_onyx" in config_ui
    assert "config.voice_weights" in config_ui
    assert "Use equal weights" in config_ui
    assert 'type="range"' in config_ui
    assert 'min="0.5"' in config_ui
    assert 'max="3"' in config_ui
    assert "create_blend" not in config_ui
    assert "lang_code" not in config_ui
    assert "voiceSummary" in store


def test_custom_voice_passes_selected_bytes_and_restart_invalidates_status(monkeypatch, tmp_path):
    voice = tmp_path / 'custom.pt'
    voice.write_bytes(b'voice pack')
    captured = {}
    async def call(payload, **kwargs):
        captured.update(payload)
        return {'audio': 'audio', 'version': '0.9.2'}
    monkeypatch.setattr(runtime.worker, 'acall', call)
    monkeypatch.setattr(runtime.worker, 'ready', True)
    monkeypatch.setattr(runtime.worker, 'generation', 10)
    asyncio.run(runtime.synthesize_sentences(['Hello'], {'voice': str(voice)}))
    assert base64.b64decode(captured['voice_files'][str(voice)]) == b'voice pack'
    assert asyncio.run(runtime.is_downloaded({'voice': str(voice)}))
    monkeypatch.setattr(runtime.worker, 'generation', 11)
    assert not asyncio.run(runtime.is_downloaded({'voice': str(voice)}))


def test_synthesis_signals_cold_engine_before_audio_and_skips_warm_notifications(monkeypatch):
    config = {"voice": "paradee"}
    calls = []

    async def call(payload, **kwargs):
        calls.append(payload["config"]["voice"])
        return {"audio": "wav", "version": "1"}

    monkeypatch.setattr(runtime, "is_globally_enabled", lambda: True)
    monkeypatch.setattr(runtime, "get_config", lambda: config.copy())
    monkeypatch.setattr(runtime, "_model_generation", -1)
    monkeypatch.setattr(runtime, "_loaded_engines", set())
    monkeypatch.setattr(runtime, "package_versions", {})
    monkeypatch.setattr(runtime.worker, "ready", True)
    monkeypatch.setattr(runtime.worker, "generation", 1)
    monkeypatch.setattr(runtime.worker, "acall", call)
    handler = Synthesize(None, None)

    def request(**options):
        return asyncio.run(handler.process({"text": "Hello", **options}, None))

    def cold():
        before = len(calls)
        response = request(report_initialization=True)
        assert response.headers["X-A0-Speech-Initializing"] == "1"
        chunks = iter(response.response)
        prefix = next(chunks)
        assert len(calls) == before
        assert json.loads(prefix + b"".join(chunks))["audio"] == "wav"
        assert len(calls) == before + 1

    cold()
    assert request(report_initialization=True)["audio"] == "wav"
    config["voice"] = "am_puck"
    cold()
    config["speed"] = 0.8
    assert request(report_initialization=True)["audio"] == "wav"
    monkeypatch.setattr(runtime.worker, "generation", 2)
    cold()
    config["voice"] = "paradee"
    assert request()["audio"] == "wav"  # Existing clients receive the ordinary JSON result.
