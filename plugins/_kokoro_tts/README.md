# Kokoro TTS

Built-in speech synthesis plugin backed by Kokoro.

## Behavior

- Registers Kokoro as the active TTS provider when the plugin is enabled.
- Supports single voices, comma-separated equal blends, and optional in-memory weighted blends.
- Keeps browser-native `speechSynthesis` as the fallback path when disabled.
- Keeps Python dependencies on the core Docker/bootstrap path. This plugin does not install packages or binaries on demand.
- Uses Kokoro's existing voice-pack cache and does not create persistent blend files.

## Config

- `voice`: Kokoro voice identifier or comma-separated equal blend
- `voice_weights`: optional mapping of voice identifiers to positive weights; when present, it defines the active blend
- `speed`: Kokoro playback speed multiplier

## Routes

- `POST /api/plugins/_kokoro_tts/synthesize`
- `POST /api/plugins/_kokoro_tts/status`
