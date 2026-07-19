# Kokoro TTS Plugin DOX

## Purpose

- Own built-in Kokoro text-to-speech integration and browser TTS fallback coordination.

## Ownership

- `api/` owns synthesize and status endpoints.
- `helpers/` owns runtime and migration behavior.
- `hooks.py` owns provider registration/lifecycle behavior.
- `webui/` owns settings and speech UI integration.
- `default_config.yaml`, `plugin.yaml`, and `README.md` own defaults, metadata, and behavior notes.

## Local Contracts

- Keep Kokoro dependencies on Docker/bootstrap paths, not opportunistic runtime installs.
- Preserve browser-native fallback when the plugin is disabled or unavailable.
- Do not expose generated speech artifacts outside intended response paths.

## Work Guidance

- Coordinate status endpoint behavior with frontend fallback decisions.

## Verification

- Smoke-test status, synthesis, configured voice/speed, and disabled fallback behavior after changes.

## Child DOX Index

No child DOX files.
