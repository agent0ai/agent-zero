# What's New Plugin DOX

## Purpose

- Own the built-in version-gated "What's New" modal for showcasing Agent Zero features after updates, dormant when no cards are configured.

## Ownership

- `plugin.yaml` owns metadata and always-enabled status.
- `webui/main.html` owns the canonical modal opened by startup and the Builtin Plugins `Open` button.
- `webui/whats-new.html` is a compatibility redirect to `webui/main.html`.
- `webui/whats-new-slides.js` owns the current card list; an empty list disables automatic display.
- `webui/` owns the Alpine store, copy, and showcase media assets.
- `extensions/webui/initFw_end/` owns the startup trigger that opens the modal once per newer installed version when cards exist unless the user has permanently opted out.

## Local Contracts

- Closing, Skip, or Done records only the current installed version as seen.
- Future updates with cards should auto-open the modal again unless the user checks the modal's permanent opt-out checkbox.
- Do not auto-open the modal when `webui/whats-new-slides.js` exports no cards.
- Before scheduling automatic display or modal-close retries, check the global `model_configured` flag. Unconfigured users mark the current version as seen and skip its showcase permanently, including after onboarding; future releases remain eligible. A failed readiness check skips display for that page load without marking the version seen.
- The permanent opt-out is stored in browser-local state under `a0_whats_new_never_show`.
- Honor the legacy `a0_whats_new_seen_version` browser-local marker as the last seen version.
- Keep the modal copy concise, left-aligned, and paired with feature media.
- Card bullets pair a bold `title` with plain `text`; render both with `x-text`.
- Keep modal actions in the pinned footer using the shared Agent Zero button classes.
- Store seen-version and opt-out markers in browser-local state only; do not persist this under `usr/`.

## Work Guidance

- Add showcase cards in `webui/whats-new-slides.js`; add assets under `webui/assets/` and reference them through `/plugins/_whats_new/webui/assets/...`.
- The first card introduces A0Cleaner with its supplied screenshot, default Monday 9 AM cleanup, manual review, custom folders, and plugin entry point.
- The second card introduces scheduled-task catch-up after downtime with its supplied screenshot. Describe missed recurring runs catching up once; tasks interrupted while running still need attention.
- Keep the startup extension idempotent and tolerant of missing or non-comparable version labels.
- Prefer release-line comparisons over development commit-distance comparisons so local development builds do not reopen the modal on every commit.
- Preserve `webui/main.html` so the plugin list exposes the standard `Open` action.

## Verification

- Run `pytest tests/test_whats_new_static.py` after changing the modal, trigger, or assets.
- Run `node --test tests/test_whats_new.mjs` for first-run suppression across onboarding/reloads, configured users, future updates, and readiness failures.
- When the card list is empty, smoke-test no startup modal and the manual Builtin Plugins `Open` empty state when practical.
- When cards exist, smoke-test startup display, slide navigation, dismissal, same-version reload behavior, newer-version display behavior, opt-out behavior, and manual Builtin Plugins `Open` behavior in the WebUI.

## Child DOX Index

No child DOX files.
