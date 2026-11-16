# SearXNG Plugin DOX

## Purpose

- Own on-demand sandboxed SearXNG web search.

## Ownership

- `helpers/searxng.py` owns lazy worker startup, query validation and search handoff.
- `sandbox/` owns the pinned source installer, bootstrap requirements, settings and guest WSGI adapter.
- `hooks.py` owns lazy installation metadata, worker shutdown and sandbox removal.
- `tools/search_engine.py` retains the legacy tool entry point using `_search_engine` presentation.
- `README.md`, `plugin.yaml` and `prompts/` own documentation, metadata and the agent-facing contract.

## Local Contracts

- Install dependencies only on first search inside `service-searxng`, using the sandbox image's existing global Python. Never install SearXNG in the outer environment or download another Python.
- Reuse `SandboxWorker` for persistent installation, private request transport, cancellation, retries and idle shutdown. Installer fingerprints trigger updates on existing instances.
- Pin the SearXNG source revision in `sandbox/install.sh`; retain shared worker dependency constraints.
- Call SearXNG's WSGI `/search` endpoint in-process; expose no listening port. Return its JSON dictionary unchanged to the presentation layer.
- Validate nonempty queries up to 8192 characters before startup and in the guest. Show first-use setup progress in the tool log, then restore its original arguments.
- Disable stops the worker; uninstall removes only its sandbox. Installation is retained across idle stops/restarts.

## Work Guidance

- Keep engine selection/settings in the plugin. No extra service framework or outer dependencies are needed.
- Coordinate response formatting with `_search_engine`; upstream blocks and empty results must remain visible.

## Verification

- Run `pytest tests/test_searxng_plugin.py tests/test_search_engine_tool.py tests/test_sandbox_workers.py`.
- In a disposable Docker container, verify first-use installation, a live search response, warm searches and restart reuse. Verify the guest uses image Python and the outer environment cannot import SearXNG.
- Keep Docker contexts free of SearXNG installers, launchers, configuration and service dependencies.

## Child DOX Index

No child DOX files.
