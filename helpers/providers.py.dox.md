# providers.py DOX

## Purpose

- Own the `providers.py` helper module.
- This module loads model provider configuration and provider metadata.
- Keep this file-level DOX profile synchronized with `providers.py` because this directory is intentionally flat.

## Ownership

- `providers.py` owns the runtime implementation.
- `providers.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `FieldOption` (`TypedDict`)
- `ProviderManager` (no explicit base class)
  - `get_instance(cls)`
  - `reload(cls)`
  - `get_providers(self, provider_type: ModelType) -> List[FieldOption]`
  - `get_raw_providers(self, provider_type: ModelType) -> List[Dict[str, str]]`
  - `get_provider_config(self, provider_type: ModelType, provider_id: str) -> Optional[Dict[str, str]]`
- Top-level functions:
- `get_providers(provider_type: ModelType) -> List[FieldOption]`: Convenience function to get providers of a specific type.
- `get_raw_providers(provider_type: ModelType) -> List[Dict[str, str]]`: Return full metadata for providers of a given type.
- `get_provider_config(provider_type: ModelType, provider_id: str) -> Optional[Dict[str, str]]`: Return metadata for a single provider (None if not found).
- `reload_providers()`: Re-merge base + plugin provider configs. Call after plugin changes.
- Notable constants/configuration names: `PROVIDER_MANAGER_CACHE_AREA`, `PROVIDER_MANAGER_CACHE_KEY`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem deletion, plugin state, settings/state persistence.
- Imported dependency areas include: `helpers`, `typing`, `yaml`.

## Key Concepts

- Important called helpers/classes observed in the source: `ProviderManager.get_instance.get_providers`, `ProviderManager.get_instance.get_raw_providers`, `ProviderManager.get_instance.get_provider_config`, `ProviderManager.reload`, `cache.remove`, `cls.get_instance`, `inst._load_providers`, `files.get_abs_path`, `self._normalise_yaml`, `get_enabled_plugin_paths`, `provider_id.lower`, `self.get_raw_providers`, `cls`, `cache.add`, `self._load_providers`, `self._load_yaml`, `items.sort`, `ProviderManager.get_instance`, `lower`, `yaml.safe_load`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_fastmcp_openapi_security.py`
  - `tests/test_model_config_api_keys.py`
  - `tests/test_oauth_codex.py`
  - `tests/test_oauth_gemini_api.py`
  - `tests/test_oauth_github_copilot.py`
  - `tests/test_oauth_providers.py`
  - `tests/test_oauth_xai_grok.py`
  - `tests/test_onboarding_static.py`

## Child DOX Index

No child DOX files.
