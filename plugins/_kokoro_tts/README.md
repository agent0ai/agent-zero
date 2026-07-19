# Kokoro TTS

Built-in speech synthesis plugin backed by Kokoro.

## Behavior

- Registers Kokoro as the active TTS provider when the plugin is enabled.
- Keeps browser-native `speechSynthesis` as the fallback path when disabled.
- Keeps Python dependencies on the core Docker/bootstrap path. This plugin does not install packages or binaries on demand.

## Config

- `voice`: Kokoro voice identifier
- `speed`: Kokoro playback speed multiplier

## Routes

- `POST /api/plugins/_kokoro_tts/synthesize`
- `POST /api/plugins/_kokoro_tts/status`
