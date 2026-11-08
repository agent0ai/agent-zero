# Whisper STT

Built-in speech-to-text plugin backed by Whisper.

## Responsibilities

- Registers Whisper as the active STT provider when the plugin is enabled.
- Owns the microphone runtime, device selector UI, message delivery mode, and plugin APIs.
- Installs dependencies and downloads the selected model inside an on-demand sandbox; startup does not load Whisper.
- Captures mono PCM with `AudioWorklet`, resamples it in the browser, and passes a
  validated float32 array directly to Whisper without a media decoder or temporary file.

## Config

- `model_size`: Whisper model name
- `language`: language hint or `auto`
- `message_mode`: `send` to send final transcriptions immediately, or `draft` to leave them in the composer
- `silence_threshold`: frontend threshold before recording starts
- `silence_duration`: silence window before waiting state
- `waiting_timeout`: delay before transcription dispatch

## API

- `POST /api/plugins/_whisper_stt/transcribe`
- `POST /api/plugins/_whisper_stt/status`

The transcribe request contains `audio` using PCM wire contract v1:

- `version`: integer `1`
- `sample_rate`: integer `16000`
- `channels`: integer `1`
- `sample_format`: `f32le` (normalized IEEE-754 float32, little-endian)
- `frame_count`: positive integer, at most 1,920,000 frames (120 seconds)
- `data`: base64 containing exactly `frame_count * 4` bytes

The backend rejects unsupported metadata, malformed/truncated data, non-finite or
out-of-range samples, and duration/byte-limit violations before loading a model.
Raw PCM is neither written to disk nor logged.

## Sandbox runtime

Heavy execution and dependency installation run inside a child gVisor sandbox on
first use. Root files and model downloads persist; no extra host service starts
at Agent Zero startup. Manage it with `python -m helpers.sandbox list` and the
existing start/stop/delete commands. See [plugin sandbox guide](../../docs/developer/plugin-sandboxes.md)
for sharing, lifecycle and upgrade behavior.
