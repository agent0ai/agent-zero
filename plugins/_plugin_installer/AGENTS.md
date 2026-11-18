# Plugin Installer DOX

## Purpose

- Own installing and updating plugins from ZIP uploads, Git repositories, and the community Plugin Index.

## Ownership

- `helpers/install.py` owns archive extraction, Git install/update, validation, hook execution, and install finalization.
- `helpers/compatibility.py` owns advisory version matching and bounded, read-only GitHub manifest retrieval. It reuses `packaging`, already installed by the framework's LangChain dependency, and safe YAML loading.
- `api/plugin_install.py` owns install/update/index API dispatch.
- `webui/` owns Plugin Hub, ZIP, Git, detail, and shared install UI.
- `plugin.yaml` and `README.md` own metadata and behavior notes.

## Local Contracts

- Install third-party plugins into `usr/plugins/`, not bundled `plugins/`.
- Reject unsafe archive paths, missing manifests, invalid manifests, and plugin name conflicts.
- Run plugin install hooks and refresh plugin state after successful changes.
- Download fallback thumbnails only when no supported thumbnail exists; repository-provided images change through Git updates.
- Browse tag filters match every tag on a plugin, counting each plugin once per tag. Keep Welcome, Provider, and Channels available even with zero results so welcome-screen, model-setup, and channel shortcuts have a visible selected filter.
- Hub details and install preflight read optional `a0_version` from default-branch `plugin.yaml`, independent of Index metadata. Compare against `helpers.git.get_version()`. Mismatches and unavailable/invalid metadata require an advisory popup with the current version, declared requirement and an explicit continue choice; retain the security/scan confirmation. Escape untrusted popup values and ignore stale detail responses. This does not gate direct Git/ZIP APIs, updates, or activation.
- Rebase local commits during Git updates; on conflicts restore the checkout and report the conflicting files through the existing structured error, persistent toast, and detail view.

## Work Guidance

- Keep installer validation aligned with plugin contracts and Plugin Index expectations.

## Verification

- Run `python -m unittest discover -s tests -p test_plugin_compatibility.py` and `node --test tests/test_plugin_compatibility.mjs` for requirement syntax, manifest boundaries, warning/override/cancel behavior, escaping and stale requests.
- Smoke-test ZIP install, Git install, Plugin Hub install, and Git update paths after changes.

## Child DOX Index

No child DOX files.
