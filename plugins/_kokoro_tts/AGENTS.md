# Kokoro TTS Plugin DOX

## Purpose

- Own local Paradee/Kokoro text-to-speech integration and browser TTS fallback coordination under the stable `_kokoro_tts` plugin identity.

## Ownership

- `api/` owns synthesize and status endpoints.
- `helpers/runtime.py` owns voice normalization and sandbox dispatch; `sandbox/paradee.py`, `voices.py` and `worker.py` own CPU inference and voice blends.
- `helpers/migration.py` preserves the legacy `tts_kokoro` enable/disable setting.
- `hooks.py` owns config hooks and idempotent Paradee dependency setup. Plugin-owned startup and enable extensions invoke the same `ensure_dependencies` hook.
- `webui/` owns settings and speech UI integration.
- `default_config.yaml`, `plugin.yaml`, and `README.md` own defaults, metadata, and behavior notes.

## Local Contracts

- Dependencies belong to `sandbox/install.sh` and install on first use inside the guest. Startup, install hooks and config reads never install host packages or load models. Failures retain browser fallback. Stop the child worker after 120 seconds of inactivity and on disable; keep dependency/model files on disk.
- Preserve browser-native fallback when the plugin is disabled or unavailable.
- Do not expose generated speech artifacts outside intended response paths.
- Preserve `voice` and `speed` configuration compatibility; weighted blends stay in memory and use positive finite weights.
- `voice: paradee` selects the single American English Heart voice and is the default for unconfigured settings. Saved Kokoro voices, blends, speed, and enable/disable choices remain unchanged; no provider-choice migration or dialog is needed.
- Valid Kokoro weights take precedence over the voice string. Paradee is never a weighted voice; mixed expressions discard its reserved token and retain the Kokoro selection.
- Paradee assets stay under `/var/lib/a0-models/paradee` in the private sandbox disk root, pinned to Hugging Face `v1.0`. Long text is split without dropping phonemes. Private IPC envelopes are cleared after acknowledgement; generated audio is returned through the existing API.
- Model preload and status must describe the selected engine. The frontend voice picker replaces the selection when crossing between Paradee and Kokoro.

## Work Guidance

- Coordinate status endpoint behavior with frontend fallback decisions.

## Verification

- Run `pytest tests/test_kokoro_tts.py tests/test_paradee_tts.py tests/test_speech_plugin_split.py tests/test_framework_dependencies.py`.
- Smoke-test both engines, voice-picker transitions, speed, status, and disabled browser fallback after changes.

## Child DOX Index

No child DOX files.
