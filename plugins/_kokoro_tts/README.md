# Local TTS (Kokoro & Paradee)

Built-in local speech synthesis, retaining the `_kokoro_tts` plugin identity.

## Behavior

- Defaults to [Paradee-8M v1.0](https://huggingface.co/sahilmahendrakar/Paradee-8M-v1.0), a small CPU model with one American English Heart voice.
- Select **Paradee · Heart** in the voice picker or choose a Kokoro voice. Paradee cannot be blended; selecting it replaces the current Kokoro selection.
- Kokoro supports single voices, comma-separated equal blends, and optional in-memory weighted blends.
- Existing saved voices, blends, speed, and enable/disable preferences are preserved. No startup choice dialog is shown.
- Keeps browser-native `speechSynthesis` as the fallback path when disabled or synthesis fails.
- Prepares Paradee's ONNX Runtime and English phonemizer dependencies through `hooks.py` on installation, updates, startup, and re-enable. Already-installed dependencies are reused; speech synthesis never installs packages.
- Uses Kokoro's existing voice-pack cache and does not create persistent blend files. Paradee downloads its pinned ONNX model and vocabulary on first use into `usr/plugins/_kokoro_tts/paradee/`; later use works offline.

## Config

- `voice`: `paradee` (default), a Kokoro voice identifier, or a comma-separated Kokoro blend
- `voice_weights`: optional mapping of voice identifiers to positive weights; when present, it defines the active blend
- `speed`: playback speed multiplier for either model (default `1.1`)

## Routes

- `POST /api/plugins/_kokoro_tts/synthesize`
- `POST /api/plugins/_kokoro_tts/status`
