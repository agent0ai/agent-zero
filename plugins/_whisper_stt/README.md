# Whisper STT

Built-in speech-to-text plugin backed by Whisper.

## Responsibilities

- Registers Whisper as the active STT provider when the plugin is enabled.
- Owns the microphone runtime, device selector UI, plugin prompt injection, and plugin APIs.
- Keeps dependency installation and model bootstrap on the Docker/bootstrap path.

## Config

- `model_size`: Whisper model name
- `language`: language hint or `auto`
- `silence_threshold`: frontend threshold before recording starts
- `silence_duration`: silence window before waiting state
- `waiting_timeout`: delay before transcription dispatch

## API

- `POST /api/plugins/_whisper_stt/transcribe`
- `POST /api/plugins/_whisper_stt/status`
