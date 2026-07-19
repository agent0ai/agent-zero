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
- Do not expose raw audio or transcriptions beyond intended UI/API paths.

## Work Guidance

- Coordinate status endpoint behavior with frontend microphone and transcription state.

## Verification

- Smoke-test status, transcription, model/language settings, send/draft modes, and silence handling after changes.

## Child DOX Index

No child DOX files.
