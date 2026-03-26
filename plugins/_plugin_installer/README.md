# Plugin Installer

Install and update Agent Zero plugins from ZIP uploads, Git repositories, or the community Plugin Index surfaced through the Plugin Hub.

## What It Does

This plugin provides the built-in installation workflow for third-party plugins. It validates plugin manifests, prevents naming conflicts, installs plugins into `usr/plugins/`, optionally updates Git-based plugins, and exposes a UI for browsing and installing community plugins.

## Main Behavior

- **ZIP install**
  - Accepts an uploaded archive, extracts it safely, locates `plugin.yaml`, validates metadata, and moves the plugin into `usr/plugins/`.
- **Git install**
  - Clones a repository to a temporary directory, validates the plugin, then installs it into `usr/plugins/`.
- **Plugin update**
  - Updates already installed Git-backed custom plugins and re-runs installation hooks.
- **Safety checks**
  - Rejects archives with unsafe paths.
  - Rejects missing or invalid `plugin.yaml` files.
  - Rejects plugin name conflicts.
- **Install hooks and refresh**
  - Runs the plugin install hook when present and calls `after_plugin_change(...)` so the app refreshes plugin state.
- **Plugin Hub UI**
  - The web UI store handles browsing Plugin Index entries, showing README content, prompting about third-party plugin risk, and launching install/update actions.

## Key Files

- **API**
  - `api/plugin_install.py` dispatches install, update, and index fetch actions.
- **Installer logic**
  - `helpers/install.py` contains archive extraction, Git install, update, validation, and hook execution.
- **Frontend**
  - `webui/pluginInstallStore.js` manages the installer modal state and community index interactions.

## Configuration Scope

- **Settings sections**: none
- **Always enabled**: `true`

## Plugin Metadata

- **Name**: `_plugin_installer`
- **Title**: `Plugin Installer`
- **Description**: Install plugins from ZIP files, Git repositories, or the community index.
