# Desktop Plugin DOX

## Purpose

- Embed the actual Tuxee terminal/file/GUI runtime in Agent Zero's Desktop surface.

## Ownership

- `build/version.txt` sets the minimum official Tuxee release. `build/release.sh` resolves GitHub's latest stable release once, requires that minimum, downloads its unmodified architecture-specific binary and verifies the release checksum and reported version. Fail if no compatible release is published; never fall back to a private build. Embedded upstream assets include third-party notices. `runtime-packages.txt` owns outer native runtime libraries.
- `helpers/runtime.py` owns lazy loopback server lifecycle and private state under `usr/plugins/_desktop/tuxee`; `helpers/install.py` builds missing/stale runtime assets in a disposable child sandbox for source-only upgrades.
- `helpers/gateway.py` streams HTTP and binary/text WebSockets at `/desktop/tuxee/` through the existing A0 listener and holds the automatic PAM session in memory. `api/desktop_session.py`, hooks and startup migration register/control that runtime.
- `webui/` keeps one Tuxee iframe across modal/canvas handoffs; no Office tabs or Office tools remain.
- `webui/tuxee-emblem.png` is the monochrome Tuxee emblem used by the `tuxee` surface icon. Shared surface CSS uses its luminance as a mask: the hexagon, belly and eye follow the theme's text color; the outer penguin and background remain transparent.

- `build/gui.sh` pins the minimal TigerVNC/Xorg build; `build/bundle-gui.sh` packages its tools, ELF loader/library closure and XKB data at `/usr/local/lib/tuxee-gui` for read-only guest mounts. Host Xvnc/password entry points are small wrappers around that same bundle, preserving its private loader and avoiding duplicate binaries. Build tools remain in the builder.
- `build/audio.sh` builds upstream's stripped PulseAudio/libsndfile support, including the microphone remap module, at `/usr/local/lib/tuxee-audio`, with relocatable `tuxee-pulseaudio`/`tuxee-pacat` wrappers. Keep the Debian 12 build for Browser's Debian 12 guest; upstream's Debian 13 audio archive cannot replace it without compatibility verification. Both image and source-upgrade builds include it; installation preserves library symlinks. No codecs, sound devices or additional listener ports are required.

## Local Contracts

- New worker environments reuse the sandbox image Python; existing worker environments remain intact.

- Enforce the configured A0 login policy and same-origin checks before starting or contacting Tuxee. Keep real Linux PAM authentication, CSRF headers and WebSocket checks. Forward only Tuxee cookies and allowlisted request headers (including the required upload byte-size header), scope response cookies to the proxy prefix, and allow framing only by the same origin.
- Bind Tuxee's managed listener to `127.0.0.1` on an allocated port with a private empty config and cleared inherited Tuxee environment overrides. No new published port is required. Browser shares the minimal native display bundle and noVNC sources, with its own sandbox and authenticated gateway.
- In the managed Docker runtime with `ROOT_PASSWORD` set, opening Desktop attempts root login through Tuxee's normal API. Keep the shared cookie server-side and inject it into HTTP/WebSocket requests; never substitute CSRF tokens. Revalidate on page loads and renew expired/restarted sessions. Missing credentials, non-Docker runtimes or login failures show normal Linux login; failed attempts have a 60-second cooldown. Preserve existing browser Tuxee sessions. Successful explicit logout suppresses automatic login for that browser session with a private, prefix-scoped cookie; revoking the shared login makes other automatic clients reconnect. Keep the existing A0 policy when WebUI login is unconfigured.
- Forward Tuxee's standard update API unchanged behind the normal A0 authentication/origin gate and upstream PAM/CSRF checks; set the trusted `X-Forwarded-Prefix`. The standard updater replaces the binary and re-execs on the same PID/port; page reload renews automatic login after session revocation.
- Install at `/usr/local/lib/tuxee/tuxee`, with an absolute `/usr/local/bin/tuxee` symlink. Create that link after worker archive extraction (the safe tar filter rejects absolute links). Recipe changes invalidate the build marker. Source-only installation requires root and network access, preserves the working binary until staging succeeds, acquires the standard `.tuxee-update.lock`, preserves equal/newer installed official binaries, and publishes the marker last. Unrecognized installed versions fail explicitly; the legacy `0.0.0-a0` is migratable.
- Treat A0 as a native Tuxee deployment: own system dependencies in this recipe/A0 release hooks; do not impersonate the official Tuxee Docker entrypoint to enable its Docker-only migrations. A0 after hooks may call `tuxee update`; the next Desktop launch uses the new binary. Keep lazy installation when a release does not need a migration. See `README.md`.
- Stop the owned server on disable/uninstall/parent exit. Preserve Tuxee user settings and upstream guardian survival semantics; never delete user documents or old Office history.
- Use the existing surface modal sizing and one attached iframe. Preserve terminal identity and GUI geometry during docking/resizing.

## Verification

- Run `pytest tests/test_tuxee_install.py tests/test_tuxee_gateway.py tests/test_retire_outer_features.py tests/test_surface_setup.py`.
- Verify actual binary replacement/re-exec through this gateway using upstream's isolated update/restart fixture, including terminal identity and editor-draft preservation. Build the native recipe on Debian 12 and smoke-test the result on the outer Debian 13 runtime before raising the minimum version.
- In a built image, exercise real PAM login, terminal input/output, GUI input, resize and dock handoff through A0. Check unauthorized/cross-site/missing-CSRF rejection and inspect listeners/published ports.
- Verify Docker automatic login from a fresh browser context through the gateway, including an authenticated session without entering Linux credentials; keep the password and shared session cookie out of browser responses.

## Child DOX Index

No child DOX files.
