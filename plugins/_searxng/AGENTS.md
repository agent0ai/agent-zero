# SearXNG Plugin DOX

## Purpose

- Own on-demand sandboxed SearXNG behind the web-search skill CLI.

## Ownership

- `webui/thumbnail.jpg` owns the 256×256 plugin catalog artwork, kept below 20 KB.

- `search.py` owns the CLI, status, process lock and sandbox lifecycle through the shared `helpers.sandbox` Python/CLI API.
- `sandbox/` owns pinned source installation, bootstrap requirements, settings and the guest query script.
- `hooks.py` owns lazy installation metadata and locked shutdown/removal.
- `_search_engine/skills/web-search/` owns agent-facing discovery and usage; no search tool or tool prompt is registered.

## Local Contracts

- Install only in `service-searxng`, using the image's existing global Python. Never install SearXNG in the outer environment or download another Python.
- Serialize the entire create/start/install/query/stop sequence with the persistent process lock under the instance-scoped `.searxng-cli` directory. Hooks use the same lock. Never unlink the lock file while waiters may exist.
- `--status` is nonblocking and never starts a sandbox. Atomic status reports starting/installing/searching/idle/error and lock ownership; unfinished state without an owner is interrupted and retryable. Never persist queries in status.
- Installer success atomically publishes its fingerprint only after dependency validation. Failed/killed setup retries; changing installer/requirements/shared constraints invalidates it.
- Use the sandbox manager for create/start/exec/stop, child lifetime, private service storage and read-only plugin/support mounts; do not share usr. Stop on completion/failure, retain installed files. Existing worker sandboxes migrate their command/mounts under the CLI lock.
- Queries are nonempty strings up to 8192 characters, passed as argv without shell interpolation. Guest calls WSGI `/search` in-process, without a listener, and returns up to ten title/URL/content results plus unavailable-engine details.
- Stdout contains JSON; first-use/wait notices go to stderr. Disable stops; uninstall removes only this sandbox.

## Work Guidance

- Keep engine settings and dependencies plugin-owned. No outer service or additional runtime.
- Keep the skill command, status/error behavior and CLI tests synchronized.

## Verification

- Run `pytest tests/test_searxng_plugin.py tests/test_search_cli.py tests/test_plugin_skills.py tests/test_skills_runtime.py`.
- Verify simultaneous first-use calls, nonblocking status, retry after interrupted setup, warm reuse, and real search responses in a disposable container. Check existing image Python and no outer SearXNG import.

## Child DOX Index

No child DOX files.
