# Model Configuration Plugin DOX

## Purpose

- Own global LLM preset definitions, scoped preset selection, API-key checks, chat overrides, migration, and model settings UI.

## Ownership

- `helpers/model_config.py` owns config resolution, presets, overrides, and runtime model object construction.
- `api/` owns model config, override, preset, search, and API-key endpoints.
- `webui/` owns model settings, summaries, switcher, and API-key UI.
- `extensions/python/startup_migration/` owns conversion from legacy full configs and project presets, followed by first-launch preset initialization.
- `default_config.yaml`, `mode_presets_fallback.yaml`, `provider_metadata.yaml`, `hooks.py`, and `plugin.yaml` own plugin defaults, offline presets, metadata, hooks, and manifest.

## Local Contracts

- `Default` is the first global preset and cannot be deleted or renamed. It owns the complete main, utility, and embedding baseline.
- Preset definitions are global. Global, project, agent-profile, and project/profile plugin configs persist only `model_preset`; chats may persist a preset reference as their explicit override.
- Preserve scoped plugin resolution order and fall back invalid or missing scope/chat references to `Default`.
- Project Settings `llm` payloads are owned here through the generic `helpers.projects` project extension-data hooks; keep project helper code agnostic to `_model_config` paths, presets, and inheritance rules.
- Keep provider metadata and API-key checks safe around secrets.
- Coordinate OAuth-backed providers with `_oauth` instead of hardcoding provider-specific auth here.
- `model_config_get` exposes `model_configured` as a derived chat-model readiness flag from provider, model name, and API-key availability.
- Non-default presets may inherit omitted slots or durable tuning from `Default`, but must replace or clear per-slot `kwargs` so provider-specific extra params never leak across model providers.
- Changing a model provider in the settings UI must clear `api_base` and `kwargs` because both may be provider-specific.
- Repair provider-specific model-config aliases at the model-config read/build boundary; keep provider-specific repairs out of provider-agnostic core wrappers such as `models.py`.
- `modelConfig.createPresetEditor()` owns local preset drafts, row actions, and stable UI-only row keys so deletion or renaming cannot rebind nested model fields.
- The preset editor maps each model provider's API-key field to the shared API-key store; saving the editor persists dirty keys separately and never writes secrets into preset YAML.
- The compact chat selector label combines the effective preset with only the leaf name of its main model; utility and provider text stay out of the closed selector.
- Preset editor reset actions must remove the user override through the preset API and refresh the open draft from bundled defaults.
- Preset rename, delete, and reset actions must repair scoped config and durable/live chat references; removed definitions fall back to `Default`.
- Migration must preserve existing definitions and distinct scoped model choices, back up replaced user files once, strip inline secrets, and remain idempotent.
- On every startup after migration, short-circuit when `usr/plugins/_model_config/presets.yaml` exists. Only a missing collection may fetch `agent0ai/a0-presets`; parse remote and plugin-local fallback YAML through the same validator, strip secrets before persistence, and persist `mode_presets_fallback.yaml` when download or validation fails.
- Model-name catalogs open below the input from either a field click or the embedded magnifier.

## Work Guidance

- Keep backend model config shape and frontend settings fields synchronized.

## Verification

- Run model-config and onboarding-related tests when model provider, preset, or API-key behavior changes.

## Child DOX Index

No child DOX files.
