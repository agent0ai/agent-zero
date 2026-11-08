# SearXNG Plugin DOX

## Purpose

- Own the unavailable SearXNG search placeholder and the migration record needed for a future sandboxed implementation.

## Ownership

- `tools/search_engine.py` owns the agent-facing placeholder tool.
- `helpers/searxng.py` owns the shared not-implemented response used by the placeholder.
- `prompts/agent.system.tool.search_engine.md` owns the agent-facing tool contract.
- `README.md` owns the historical installation, runtime, dependency, and configuration record.
- `plugin.yaml` owns bundled-plugin metadata and activation.

## Local Contracts

- Every tool call returns exactly `the searxng plugin is not yet fully implemented` with `break_loop=False`.
- The plugin must not make network requests, install packages, start processes, create a virtualenv, or write SearXNG configuration.
- SearXNG must not be installed or launched in the outer Agent Zero image.
- Any future implementation must isolate SearXNG through the sandboxing plugin and update this contract and the README.

## Work Guidance

- Treat the README commands and configuration as a historical reconstruction record, not an instruction to restore host-level installation.
- Keep the public tool name `search_engine` stable while the placeholder remains bundled.

## Verification

- Run `pytest tests/test_searxng_plugin.py`.
- Confirm Docker contexts contain no SearXNG installer, launcher, supervisor entry, configuration, virtualenv path, service user, or dependency-only install step.

## Child DOX Index

No child DOX files.
