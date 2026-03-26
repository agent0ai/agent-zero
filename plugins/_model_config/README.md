# Model Configuration

Manage which models Agent Zero uses for chat, utility, and embeddings, with support for scoped overrides and reusable presets.

## What It Does

This plugin centralizes model selection and model-related settings for the application. It provides helpers and APIs for:

- selecting chat, utility, and embedding models
- reading and saving model presets
- checking for missing API keys
- allowing optional per-chat model overrides
- resolving config at global, project, agent, and chat scope

## Main Behavior

- **Scoped configuration**
  - Reads plugin config through the standard plugin config system with project and agent overrides.
- **Preset management**
  - Loads presets from a user file when present and falls back to bundled defaults.
- **Per-chat override**
  - Allows a chat context to store a temporary override or preset reference in context data.
- **Model object construction**
  - Builds `ModelConfig` objects and the runtime chat, utility, and embedding wrappers used elsewhere in the app.
  - Note: Browser model wiring now lives in the `_browser_agent` plugin.
- **API key validation**
  - Reports configured providers that still require API keys.

## Key Files

- **Core helper**
  - `helpers/model_config.py` resolves config, presets, overrides, and runtime model objects.
- **APIs**
  - `api/model_config_get.py`
  - `api/model_config_set.py`
  - `api/model_override.py`
  - `api/model_presets.py`
  - `api/model_search.py`
  - `api/api_keys.py`
- **Hooks**
  - `hooks.py` exposes plugin-level integration hooks.

## Configuration Scope

- **Settings section**: `agent`
- **Per-project config**: `true`
- **Per-agent config**: `true`
- **Always enabled**: `true`

## Plugin Metadata

- **Name**: `_model_config`
- **Title**: `Model Configuration`
- **Description**: Manages LLM model selection and configuration for chat, utility, and embedding models. Supports per-project and per-agent overrides with optional per-chat model switching.
