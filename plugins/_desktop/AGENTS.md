# Desktop Plugin DOX

## Purpose

- Own the Agent Zero Linux desktop runtime, Xpra/Xfce session integration, and live desktop surface.

## Ownership

- `helpers/` owns desktop routes, session lifecycle, state, and prompt context.
- `api/desktop_session.py` owns desktop session API behavior.
- `hooks.py` owns route registration and plugin lifecycle hooks.
- `prompts/`, `assets/`, `skills/`, `extensions/`, and `webui/` own desktop context, assets, skill guidance, hooks, and panel UI.

## Local Contracts

- Preserve session startup, cleanup, and route protection for desktop access.
- Keep desktop state injected into prompts accurate and bounded.
- Do not expose desktop routes without the expected auth protections.
- Keep Desktop host visibility tied to an attached modal or canvas host; modal cleanup may preserve the iframe in keepalive, but must not leave stale modal mode behind.
- Keep LibreOffice Writer as the default handler for Markdown and plain text files; keep Agent Zero Editor available as a secondary Open With target through the desktop intent bridge.

## Work Guidance

- Coordinate runtime and panel changes so live UI reflects actual desktop session state.

## Verification

- Smoke-test desktop startup, panel connection, route access, and session cleanup after changes.

## Child DOX Index

No child DOX files.
