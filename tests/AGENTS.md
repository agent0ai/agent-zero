# Tests DOX

## Purpose

- Own pytest regression, security, integration, and contract tests.
- Keep tests focused on behavior that should remain stable across framework changes.

## Ownership

- Test files live directly under `tests/` and are named for the behavior or subsystem they cover.
- Shared fixtures should be added only when multiple tests need them.
- Runtime artifacts created during tests should use pytest temporary directories or existing isolated test helpers.

## Local Contracts

- Tests must not require real API keys, network-only services, private user data, or local `usr/` runtime state. Manual provider demos must guard model creation and requests behind their executable entry point so collection never runs them.
- Root `pytest.ini` selects `tests` and `plugins` with importlib import mode; root `conftest.py` keeps `tests/` importable and ignores plugin API handler modules whose names match `test_*.py`.
- Tests that reimport project modules under stubs, swap `files._base_dir`, or populate extension/plugin caches must restore them so later test files see pristine modules and caches.
- Keep tests deterministic and isolated from existing chats, uploads, downloads, plugin state, and settings.
- Prefer exercising public helper/API contracts over fragile implementation details when practical.
- Security regression tests should assert the protected behavior directly.
- Launcher gateway tests must cover feature negotiation, authenticated and
  CSRF-protected control, acknowledgement timeout, identity lifecycle,
  context-bound CLI routing precedence, duplicate/multiple-host behavior,
  scope-driven availability, and emergency disconnect without a live host.
- Composer control tests use unrelated fake extensions and verify scoped dispatch, capability negotiation, authentication/CSRF requirements, invalid input rejection, and unchanged plugin error responses without depending on optional plugins.

## Work Guidance

- Add focused tests near the affected subsystem's existing tests.
- Use descriptive test names that state the regression or contract.
- Avoid broad sleeps or real-time dependencies; use monkeypatching or controlled clocks where possible.
- Multiprocess contention tests wait for child readiness before measuring lock behavior; cold imports must not consume the contention deadline. Always release and join children on assertion failure.

## Verification

- Install root `requirements.txt` for application dependencies, suite tooling and the SoundFile WAV fixtures; plugin sandboxes still install their own runtime requirements. Real DOM/upload checks run in a provisioned browser guest with `PYTHONPATH=/app` and `PLAYWRIGHT_BROWSERS_PATH=/opt/browsers`.
- Run `pytest` for broad changes.
- Run `node --test tests/test_file_browser_views.mjs` for independent chat/embedded views and shared browser configuration.
- Run `pytest tests/test_name.py` for narrow changes and mention any broader test gaps at closeout.
- Run `node --test tests/test_onboarding.mjs` for onboarding defaults and completion staying in the original chat.
- Run `pytest tests/test_litellm_sdk.py -q` for LiteLLM/OpenAI upgrades. Its loopback provider exercises the installed SDK's sync/async calls, streaming, tool/state preservation, fallback, embeddings, and Anthropic cache markers without real keys or external requests.
- Run `pytest tests/test_framework_dependencies.py -q` for dependency migration changes; verify stale self-update environments, process restart, and already-current image installs.
- Run `pytest tests/test_docker_python_runtime.py -q` for global Python installation, direct service launchers, and entrypoints without import-time dependency activation.
- ONNX changes require `test_local_embeddings.py`, `test_onnx_migration.py`, preload/factory tests and `integration_onnx_compatibility.py`: create synthetic fixtures with the old runtime, test new queries/inserts against identical persisted indexes, then restart in a separate process. Never use private live databases.
- Image slimming requires a fresh base/application build, dependency checks, offline embeddings, archive extraction, Tuxee binary loading and a real OCI pull/unpack/guest execution check. Inspect the image before installing test dependencies so fixtures cannot hide missing runtime libraries.
- Run `pytest tests/test_sandboxing.py tests/test_sandbox_builtin_image.py -q` for image pulls/imports, bundled defaults, lazy builds, cache validation, digest pinning, and sandbox lifecycle contracts.
- Storage reporting: `pytest tests/test_sandbox_storage.py` and `node --test tests/test_sandbox_storage.mjs` verify scan-free lifecycle/status, explicit asynchronous measurement, ownership validation and independent UI controls.

- Run `pytest tests/test_sandbox_services.py tests/test_tunnel_plugin.py tests/test_tunnel_remote_link.py tests/test_csrf_tunnel_origins.py tests/test_sandboxing.py tests/test_code_execution_destinations.py tests/test_ws_csrf.py` for service sandbox/tunnel changes. Real gVisor/Cloudflare checks are separate from deterministic tests.

- Plugin worker coverage: `test_sandbox_workers.py`, Document Query, Whisper PCM, Kokoro/Paradee, browser regression and native desktop tests. Live guest installers/model inference/browser rendering are checked separately in disposable containers.
- Browser startup progress requires worker boot/lock-isolation tests and `node --test tests/test_browser_cold_start.mjs` for request-local elapsed time, ticking through stale ready states/delayed polls, polling cleanup, late responses and first-install deadlines. Installer dependency changes also need a fresh guest and real Chromium/HTML5 viewer check.

- `integration_guest_smoke.py` runs inside provisioned Telegram/mail guests with their real SDK/parser and mocked network transports. WhatsApp callback, authentication and media bounds are covered by the Node bridge suite; live pairing/account behavior requires separate authorization.

- `test_browser_vnc.py` checks signed-session/origin admission, private credentials, asset traversal, binary proxy teardown and authenticated Xvnc launch. Native changes also require real noVNC input/clipboard/resize/dialog and fresh/warm sandbox measurements.
- Browser performance changes also verify reuse/migration of the image Python, duplicate Node removal, no-op display sizing, retained GTK/font behavior, and fresh plus existing guest installers. Directfs changes need real non-root lifecycle/read-only/masked-mount checks in addition to the manager tests.

## Child DOX Index

No child DOX files.
