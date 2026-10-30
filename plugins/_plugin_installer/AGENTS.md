# Plugin Installer DOX

## Purpose

- Own installing and updating plugins from ZIP uploads, Git repositories, and the community Plugin Index.

## Ownership

- `helpers/install.py` owns archive extraction, Git install/update, validation, hook execution, and install finalization.
- `api/plugin_install.py` owns install/update/index API dispatch.
- `webui/` owns Plugin Hub, ZIP, Git, detail, and shared install UI.
- `plugin.yaml` and `README.md` own metadata and behavior notes.

## Local Contracts

- Install third-party plugins into `usr/plugins/`, not bundled `plugins/`.
- Reject unsafe archive paths, missing manifests, invalid manifests, and plugin name conflicts.
- Run plugin install hooks and refresh plugin state after successful changes.
- Download fallback thumbnails only when no supported thumbnail exists; repository-provided images change through Git updates.
- Browse tag filters match every tag on a plugin, counting each plugin once per tag. Keep Welcome available even with zero results so the welcome-screen shortcut has a visible selected filter.
- Rebase local commits during Git updates; on conflicts restore the checkout and report the conflicting files through the existing structured error, persistent toast, and detail view.

## Work Guidance

- Keep installer validation aligned with plugin contracts and Plugin Index expectations.

## Verification

- Smoke-test ZIP install, Git install, Plugin Hub install, and Git update paths after changes.

## Child DOX Index

No child DOX files.
