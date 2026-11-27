# Sandbox worker types

`SandboxMount` and `SandboxError` live outside the reloadable plugin namespace. Existing workers and reloaded managers share their class identities. The manager still validates every mount before use. Both types remain importable from `helpers.sandbox` and the plugin manager module.

Run `pytest tests/test_sandbox_workers.py` to exercise a worker mount across a bundled plugin reload.
