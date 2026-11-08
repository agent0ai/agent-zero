# Whisper STT Plugin DOX

## Purpose

- Own built-in Whisper speech-to-text integration, microphone runtime settings, and transcription delivery behavior.

## Ownership

- `api/` owns transcribe and status endpoints.
- `helpers/` owns runtime and migration behavior.
- `hooks.py` owns provider registration/lifecycle behavior.
- `webui/` owns settings, main speech UI, store, and styling.
- `default_config.yaml`, `plugin.yaml`, and `README.md` own defaults, metadata, and behavior notes.

## Local Contracts

- Keep dependency installation and model bootstrap on Docker/bootstrap paths.
- Preserve configured message mode, language, silence threshold, silence duration, and waiting timeout behavior.
- Keep all `data-whisper-microphone` controls synchronized with the same microphone status.
- Optional final-transcript handlers must receive the configured draft/send mode without changing the main chat microphone's delivery behavior.
- Do not expose raw audio or transcriptions beyond intended UI/API paths.
- Microphone uploads use the bounded PCM v1 contract documented in `README.md`:
  16 kHz mono normalized little-endian float32, at most 120 seconds. Validate
  metadata and bytes before model loading, and pass an ndarray to Whisper so no
  filename decoder, temporary audio file, FFmpeg process, or raw-audio log is used.
- Browser capture uses `AudioWorklet`; report unsupported browsers explicitly and
  keep microphone streams, worklet nodes, timers, and audio contexts disposable.

## Work Guidance

- Coordinate status endpoint behavior with frontend microphone and transcription state.

## Verification

- Smoke-test status, PCM validation/transcription, model/language settings,
  send/draft modes, device selection, repeated recording, teardown, permission
  failures, unsupported browsers, and silence handling after changes.

## Child DOX Index

No child DOX files.
