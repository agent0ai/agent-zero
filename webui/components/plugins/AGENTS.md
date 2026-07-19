# Plugin Components DOX

## Purpose

- Own core WebUI plugin settings, info, list, execution, and toggle components.

## Ownership

- Root plugin component files own shared plugin settings and info screens.
- `list/` owns plugin list and execute modal components.
- `toggle/` owns scoped plugin activation UI.
- Store files own plugin modal and settings state.

## Local Contracts

- Keep plugin settings modals bound through `$store.pluginSettingsPrototype` conventions.
- Preserve global and scoped toggle semantics using `.toggle-1` and `.toggle-0`.
- Use notification helpers for plugin UI feedback.
- Label reset actions `Reset to default` and resolve notification globals when the action runs so late WebUI initialization cannot abort the reset lifecycle.

## Work Guidance

- Coordinate plugin API payload changes with `helpers/plugins.py` and plugin API handlers.

## Verification

- Smoke-test plugin list, settings, scoped toggles, plugin info, and execute modal after changes.

## Child DOX Index

No child DOX files.
