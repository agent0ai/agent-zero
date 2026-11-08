# Desktop Plugin DOX

## Purpose

- Embed the actual Tuxee terminal/file/GUI runtime in Agent Zero's Desktop surface.

## Ownership

- `build/` pins Tuxee source and Go checksums, applies the relative-URL patch, builds its static PIE terminal guardian, and reuses upstream minimal VNC/window-manager recipe. `runtime-packages.txt` owns outer native runtime libraries.
- `helpers/runtime.py` owns lazy loopback server lifecycle and private state under `usr/plugins/_desktop/tuxee`; `helpers/install.py` builds missing/stale runtime assets in a disposable child sandbox for source-only upgrades.
- `helpers/gateway.py` streams HTTP and binary/text WebSockets at `/desktop/tuxee/` through the existing A0 listener and holds the automatic PAM session in memory. `api/desktop_session.py`, hooks and startup migration register/control that runtime.
- `webui/` keeps one Tuxee iframe across modal/canvas handoffs; no Office tabs or Office tools remain.

- `build/gui.sh` pins the minimal TigerVNC/Xorg build; `build/bundle-gui.sh` packages its tools, ELF loader/library closure and XKB data at `/usr/local/lib/tuxee-gui` for read-only guest mounts. Build tools remain in the builder.

## Local Contracts

- Enforce the configured A0 login policy and same-origin checks before starting or contacting Tuxee. Keep real Linux PAM authentication, CSRF headers and WebSocket checks. Forward only Tuxee cookies and allowlisted request headers (including the required upload byte-size header), scope response cookies to the proxy prefix, and allow framing only by the same origin.
- Bind Tuxee's managed listener to `127.0.0.1` on an allocated port with a private empty config and cleared inherited Tuxee environment overrides. No new published port is required. Browser shares the minimal native display bundle and noVNC sources, with its own sandbox and authenticated gateway.
- In the managed Docker runtime with `ROOT_PASSWORD` set, opening Desktop attempts root login through Tuxee's normal API. Keep the shared cookie server-side and inject it into HTTP/WebSocket requests; never substitute CSRF tokens. Revalidate on page loads and renew expired/restarted sessions. Missing credentials, non-Docker runtimes or login failures show normal Linux login; failed attempts have a 60-second cooldown. Preserve existing browser Tuxee sessions. Successful explicit logout suppresses automatic login for that browser session with a private, prefix-scoped cookie; revoking the shared login makes other automatic clients reconnect. Keep the existing A0 policy when WebUI login is unconfigured.
- Build the guardian as static PIE with no ELF interpreter. Bookworm musl needs an explicit relocation CRT; the build checks both properties.
- Update Tuxee with Agent Zero's pinned recipe; reject its in-app update endpoint. Recipe changes invalidate the build marker. Source-only installation requires root and network access, preserves a working binary until the build succeeds and publishes the marker last.
- Stop the owned server on disable/uninstall/parent exit. Preserve Tuxee user settings and upstream guardian survival semantics; never delete user documents or old Office history.
- Use the existing surface modal sizing and one attached iframe. Preserve terminal identity and GUI geometry during docking/resizing.

## Verification

- Run `pytest tests/test_tuxee_gateway.py tests/test_retire_outer_features.py tests/test_surface_setup.py`.
- In a built image, exercise real PAM login, terminal input/output, GUI input, resize and dock handoff through A0. Check unauthorized/cross-site/missing-CSRF rejection and inspect listeners/published ports.
- Verify Docker automatic login from a fresh browser context through the gateway, including an authenticated session without entering Linux credentials; keep the password and shared session cookie out of browser responses.

## Child DOX Index

No child DOX files.
