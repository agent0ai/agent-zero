# Tests DOX

## Purpose

- Own pytest regression, security, integration, and contract tests.
- Keep tests focused on behavior that should remain stable across framework changes.

## Ownership

- Test files live directly under `tests/` and are named for the behavior or subsystem they cover.
- Shared fixtures should be added only when multiple tests need them.
- Runtime artifacts created during tests should use pytest temporary directories or existing isolated test helpers.

## Local Contracts

- UI bundle inventory regressions cover deterministic order, recursive and shallow traversal, contained and escaping symlinks, and avoidance of repeated resolution for ordinary files.
- Tests must not require real API keys, network-only services, private user data, or local `usr/` runtime state. Manual provider demos must guard model creation and requests behind their executable entry point so collection never runs them.
- Root `pytest.ini` selects `tests` and `plugins` with importlib import mode; root `conftest.py` keeps `tests/` importable and ignores plugin API handler modules whose names match `test_*.py`.
- Socket handler modules named `test_*.py` are also excluded from collection. `test_socket_api.py` covers real Unix-socket requests, temporary core/plugin/user handler discovery, permissions, lifecycle and CLI subprocess behavior; it also runs with stdlib unittest. `test_socket_handlers.py` exercises shared message/installer operations, explicit contexts, error normalization, worker concurrency and cancellation with isolated dependencies.
- Tests that reimport project modules under stubs, swap `files._base_dir`, or populate extension/plugin caches must restore them so later test files see pristine modules and caches.
- Keep tests deterministic and isolated from existing chats, uploads, downloads, plugin state, and settings.
- Prefer exercising public helper/API contracts over fragile implementation details when practical.
- Security regression tests should assert the protected behavior directly.
- `test_telegram_config_scope.py` covers scoped bot ownership, token conflicts, current access rules, activation, connection revocation, outbound delivery, and session isolation using temporary plugin configuration.
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

- File destination changes need the tool, connector permission, and text freshness checks in `test_destination_files.py` and the real guest path and read-only mount check in `test_proot_runtime.py`.

- Install root `requirements.txt` for application dependencies and suite tooling; plugin sandboxes still install their own runtime requirements. `test_browser_cdp.py` and `test_browser_cdp_actions.py` exercise the guest transport and captured form controls in a disposable profile. Set `CHROMIUM_BINARY` to the installed full executable when it is outside PATH. `test_browser_dom_security.py` uses the same native pipe and a loopback fixture for both origins. Keep Chromium site isolation enabled when checking page and isolated worlds.
- Run `pytest` for broad changes.
- Run `node --test tests/test_canvas_modes.mjs tests/test_component_moves.mjs` for workspace routing, close guards and retained component and extension moves; verify shared modal and isolated Save As rendering in a real browser.
- Run `node --test tests/test_file_browser_views.mjs` for independent chat/embedded views, selection, and shared browser configuration. Run `pytest tests/test_file_browser_actions.py tests/test_file_browser_navigation.py` for local Trash, ZIP, exact names, concurrent uploads and picker contracts.
- Run `node --test tests/test_canvas_resize.mjs tests/test_canvas_rail_drag.mjs` for deferred canvas resizing, drag pointer ownership and cancellation cleanup; iframe interception also needs a real-browser drag check.
- Run `pytest tests/test_name.py` for narrow changes and mention any broader test gaps at closeout.
- Plugin Hub compatibility: `python -m unittest discover -s tests -p test_plugin_compatibility.py` and `node --test tests/test_plugin_compatibility.mjs tests/test_plugin_hub_welcome.mjs` cover manifest/version parsing and advisory install filtering/confirmation without installing plugins.
- Run `python -m unittest discover -s tests -p test_upload_filenames.py` for the dependency-free shared upload-name checks; `pytest tests/test_telegram_media_delivery.py` also covers attachment destination confinement.
- Run `node --test tests/test_onboarding.mjs` for onboarding defaults and completion staying in the original chat.
- Run `pytest tests/test_litellm_sdk.py -q` for LiteLLM/OpenAI upgrades. Its loopback provider exercises the installed SDK's sync/async calls, streaming, tool/state preservation, fallback, embeddings, and Anthropic cache markers without real keys or external requests.
- Run `pytest tests/test_framework_dependencies.py -q` for dependency migration changes; verify stale self-update environments, process restart, and already-current image installs.
- Self-update hooks and critical updater handoff: `pytest tests/test_self_update_hooks.py tests/test_self_update_runtime_sync.py tests/test_self_update_tag_filter.py`. Hook tests use isolated Git releases and real script subprocesses; they also run with `python -m unittest discover -s tests -p test_self_update_hooks.py` when pytest is unavailable.
- Run `pytest tests/test_boot_imports.py tests/test_migration_dotenv.py -q` for lightweight preparation, checked password persistence, lazy protocol imports and first-request access checks.
- Run `pytest tests/test_docker_python_runtime.py -q` for global Python installation, production bytecode and Node stripping, direct service launchers, and entrypoints without import-time dependency activation.
- Tuxee release integration: `test_tuxee_install.py` covers download/checksum/version failures, standard layout/locking and preservation of newer binaries; `test_tuxee_gateway.py` covers update JSON, authentication/CSRF, stale-cookie recovery and logout/reopen session renewal; `node --test tests/test_desktop_lifecycle.mjs` covers tab/canvas/modal reloads, docking and startup races. Pair with upstream's real update/restart browser fixture through the A0 gateway before shipping a release pin.
- `test_native_memory_store.py` covers model-change rebuild, transactional replacement, stale writers and failure-safe legacy recovery.
- ONNX changes require `test_local_embeddings.py`, `test_onnx_migration.py`, preload/factory tests and `integration_onnx_compatibility.py`: create synthetic fixtures with the old runtime, compare migrated records, float32 vectors and retrieval scores, test new inserts, then restart in a separate process. Never use private live databases.
- Image slimming requires a fresh base/application build, dependency checks, offline embeddings, archive extraction, Tuxee binary loading and a real OCI pull/unpack/guest execution check. Inspect the image before installing test dependencies so fixtures cannot hide missing runtime libraries.
- `test_worker_python_bootstrap.py` covers default/pinned interpreter selection and preserving existing worker environments. Verify image-Python workers with real SDK imports and `integration_guest_smoke.py` in fresh Docker/PRoot guests.
- Run `pytest tests/test_sandboxing.py tests/test_sandbox_builtin_image.py -q` for image pulls/imports, bundled defaults, lazy builds, cache validation, digest pinning, and sandbox lifecycle contracts.
- `test_proot_runtime.py` exercises host binding permission preservation, new workspace creation and cross-UID exchange, sparse guest creation, copy-up, merged directory cursors, whiteouts and stopped Files reads in a disposable Linux container. `test_sandbox_builtin_image.py` checks the stopped merged root used for OCI packaging.
- Sandbox data coverage in `test_sandboxing.py` and `test_time_travel.py` includes the instance `fs/` and `data` paths, workspace binds, retained files, per-guest history and explicit storage overrides. `test_backup_large_archives.py` checks default backups omit the runtime tree during traversal.
- Storage reporting: `pytest tests/test_sandbox_storage.py` and `node --test tests/test_sandbox_storage.mjs` verify scan-free lifecycle/status, explicit asynchronous measurement, ownership validation and independent UI controls.

- Run `pytest tests/test_sandbox_services.py tests/test_tunnel_plugin.py tests/test_tunnel_remote_link.py tests/test_csrf_tunnel_origins.py tests/test_sandboxing.py tests/test_code_execution_destinations.py tests/test_ws_csrf.py` for service sandbox/tunnel changes. Real PRoot/Cloudflare checks are separate from deterministic tests.

- SearXNG: `test_searxng_plugin.py` and `test_search_cli.py` cover guest responses, CLI lifecycle, process locking, nonblocking status and interrupted-install retry. Verify concurrent first-use queries, warm reuse and image-Python reuse separately in a disposable container; external engines may return CAPTCHA or rate-limit errors.

- Plugin worker coverage: `test_sandbox_workers.py`, Document Query, Whisper PCM, Kokoro/Paradee, browser regression and native desktop tests. Live guest installers/model inference/browser rendering are checked separately in disposable containers.
- Run `node --test tests/test_tts_service.mjs` for backend-triggered cold speech feedback, quiet warm playback, cancellation, provider rediscovery and fallback. Verify both real voices and saved speeds in a fresh container through the response Speak button.
- Run `test_browser_guest_policy.py` with the provisioned Browser guest’s image Python and `PYTHONPATH=/app`. It checks the effective policy in Chromium. Inspect the Xvnc startup window to verify visible infobar changes.
- Browser startup progress requires worker boot/lock-isolation tests, `test_browser_pipe.py` for real guest stage messages and context-scoped pending requests, and `node --test tests/test_browser_cold_start.mjs` for numbered stages, first-run subtitles, idle checks, duplicate clicks, lost-acknowledgement recovery, confirmed failure/retry, cleanup and late replies. `test_browser_tool_output.py` covers internal startup hints and watcher cleanup on success, failure and cancellation, without adding hints to agent-facing results. Live UI checks must observe the Start button throughout a launch and viewer handoff. Installer dependency changes also need a fresh guest and real Chromium/HTML5 viewer check.

- `integration_guest_smoke.py` runs inside provisioned Telegram/mail guests with their real SDK/parser and mocked network transports, and in the Local TTS guest to exercise Paradee WAV encoding with SoundFile. WhatsApp callback, authentication and media bounds are covered by the Node bridge suite; live pairing/account behavior requires separate authorization.

- `test_browser_vnc.py` checks signed-session/origin admission, private credentials, asset traversal, binary proxy teardown and authenticated Xvnc launch. Native changes also require real noVNC input/clipboard/resize/dialog and fresh/warm sandbox measurements.
- Browser window changes require a live user-created tab handoff to a second chat and a window switch through the header. Clipboard changes require repeated text transfers through the interactive iframe and coverage of macOS Command shortcuts.
- Browser audio: `test_browser_audio.py` checks private sink/capture subprocess lifetime with stdlib unittest; `node --test tests/test_browser_audio.mjs` checks stereo samples, gain, buffering, mute and autoplay cleanup. Live checks measure playback through the viewer and verify mute survives iframe replacement. `test_browser_vnc.py` covers authenticated audio admission, silent gaps and capture teardown. Real Chromium audio requires the built native runtime.
- Browser performance changes also verify the image Python, reuse of a provisioned Chromium, the Debian package path on first use, no-op display sizing, retained GTK/font behavior, and fresh plus existing guest installers. Directfs changes need real non-root lifecycle/read-only/masked-mount checks in addition to the manager tests.
- Raw CDP regression coverage in `test_browser_cdp_actions.py` exercises browser, tab and nested target commands, event buffering and chat-scoped cleanup on the private pipe.
- `test_tool_action_policy.py` checks Browser skill access and verifies that execution follows the actual tool after import fallback. `test_host_browser_connector.py` covers Browser contract registration, routing, and cancellation.
- `test_tool_policy.py` checks that ordinary prompt assembly leaves Browser tabs and page content on demand.
- `test_a0_connector_prompt_gating.py` covers Host Computer Use skill loading, connector readiness, saved whole-tool and action rules, and native action enums.
- `test_a2a_chat_tool.py` covers A2A skill loading and saved Tool Access IDs, plus remote discovery, explicit credentials, and conversation reuse.
- `test_tool_action_policy.py` covers callable tools and host editor permission checks. `test_remote_input_policy.py` exercises saved connector permissions through unified host execution, including an output request with reset.

## Child DOX Index

No child DOX files.

Real PRoot checks: `A0_PROOT_INTEGRATION=1 pytest tests/test_proot_runtime.py` in a disposable built image. Run them with default seccomp and no added capabilities. Check writes, renames and unlinks against both the peer guest and the immutable base.
