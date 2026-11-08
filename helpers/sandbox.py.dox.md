# Sandbox Access

`get_manager()` returns the configured `_sandboxing` manager for this Agent Zero installation. Its persistent instance ID scopes runtime IDs and state; do not construct a second lifecycle implementation here.

`python -m helpers.sandbox` provides JSON list/create/inspect/start/stop/restart/delete/exec/restore commands. Registry image selection defaults to plugin configuration. Delete requires `--yes`. Child lifetime is default: create/start/restart stay attached for child sandboxes; Ctrl-C stops the child. Use `--standalone` for services that must remain after the command returns. Python callers retain the creating process while child sandboxes are needed.

Status/lifecycle commands return `size_bytes: null` without scanning storage;
child CLI waiting uses `is_running`. Only the explicit `disk-usage NAME` command
waits for a measurement. Async Python callers run `manager.disk_usage(name)`
through `asyncio.to_thread`; it holds no lifecycle locks. The UI requests the
same operation separately through its authenticated API. Verify with
`tests/test_sandbox_storage.py` and `tests/test_sandbox_storage.mjs`.

New filesystems are disk-backed. `/a0/usr` shares the installation's usr directory unless `--no-usr`; host `/` requires `--host-root`. `--network host` (default) includes internet and host loopback, while `none` is offline. This does not expose a Docker Desktop machine's filesystem or loopback beyond the outer container.

The helper imports no tunnel provider dependencies. Verify with sandbox service tests and the documented live lifecycle smoke checks.

`import-image ARCHIVE REFERENCE` imports a local `docker save` archive through the image manager's Skopeo/umoci pipeline and returns public image metadata. It does not contact Docker or change the default image setting. Select the imported reference in Sandboxing settings for new sandboxes; cache-only images must be reimported after cache deletion/expiry. Archive and image errors return JSON with a nonzero exit code.
