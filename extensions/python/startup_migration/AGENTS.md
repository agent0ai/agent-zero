# Startup Migration Extensions DOX

## Purpose

- Own backend startup migrations.

## Ownership

- Ordered Python files in this folder own idempotent migration steps that run during startup.

## Local Contracts

- Migrations must be safe to run repeatedly.
- Preserve user data and create backups or reversible paths when changing durable state.
- Keep long-running work bounded and observable.
- `_05_framework_dependencies.py` applies the LiteLLM/OpenAI and ONNX/tokenizer/NumPy pins and shared security floors from root `requirements.txt` on Docker startup. Already-current and non-Docker environments skip installation; failures stop startup. Extend its package scope when future core dependency changes need self-update installation.
- After changing framework packages, reuse `helpers.process.restart_process()` before serving requests so imported SDK modules are refreshed. Keep installation within 60 seconds to leave startup time within older self-updaters' health-check window; Git rollback does not restore Python packages.
- `_21_onnx_embeddings.py` runs after model-config migration (`_10`) and preset bootstrap (`_20`), before preload/chat restoration. It prepares missing immutable ONNX assets in a bounded subprocess, verifies inference before returning, and stops startup on missing/corrupt assets or failed provisioning. Both checks and preparation cover the global configuration, all selectable saved presets and persisted raw chat overrides using their resolved cache/access options through `helpers.local_embeddings.configured_asset_options`; preserve existing cache contents. Ready images need no network. Source upgrades retain previous optional training packages and model cache for declared/private consumers and rollback; only rebuilt images remove this payload. No database/cache identity changes or reindexing belong here.
- `_10_self_update_manager.py` may replace `/exe/self_update_manager.py` from the repository copy when the installed runtime updater is stale; it must validate required safety markers and keep a backup before replacement.
- Required updater capabilities include immutable rollback-stash identity (`get_top_stash_oid`), so runtimes using moving stash selectors are upgraded on startup.
- Runtime markers also require fast, timestamp-tolerant ZIP backups so existing `/exe` managers receive the backup fixes.
- Runtime synchronization also upgrades updaters with the older health timeout to the 600-second default, retaining the environment override.
- After synchronizing a stale self-update manager, `_10_self_update_manager.py` starts that manager's best-effort Codex CLI refresh with `sys.executable` in the background.

- `_25_retire_tunnel_service.py` removes only the legacy run_tunnel_api Supervisor section, retains a backup, and rereads/updates Supervisor without restarting WebUI. Restore the config on failure so startup can retry.

- `_26_retire_outer_features.py` removes only retired outer Python distributions, browser installer caches and bundled WhatsApp node_modules. It preserves browser profiles, credentials, documents and Office/Editor history. Old active GUI applications defer native-package/service retirement to the next restart to protect unsaved work; Supervisor declaration changes retain a backup and restore on failure. Rebuilt images are required to reclaim lower image layers.
- Scraper retirement covers Newspaper, pyreqwest-impersonate and their exclusive dependencies, preserving dependencies (including optional extras) declared by other installed distributions and their closure. It retains shared libraries/security floors. Custom plugins must declare their own scraper dependencies; undeclared implicit availability is no longer supported. Framework dependency upgrades disable uv caching; source updates cannot reclaim old cached image layers.

## Work Guidance

- Add migrations only for durable state changes that cannot be handled lazily elsewhere.

## Verification

- Smoke-test startup on a clean checkout and on representative existing user state when practical.

## Child DOX Index

No child DOX files.
