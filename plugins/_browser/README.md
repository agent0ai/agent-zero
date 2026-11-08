# Browser

The internal browser installs and runs Chromium, its Patchright driver and Tuxee’s minimal Xvnc in an on-demand child sandbox. The existing tool, settings, tab ownership,
sign-in profile and authenticated viewer stay integrated with Agent Zero.
Bring Your Own Browser continues through the host connector.

The sandbox persists installed packages and exposes only the browser profile,
download directory and selected extensions. Uploads transfer selected bytes.
See the [plugin sandbox guide](../../docs/developer/plugin-sandboxes.md) for
lifecycle, sharing, upgrade behavior and runtime requirements.

First launch reports sandbox initialization, Python/display/viewer setup, browser
driver installation and Chromium download in the Browser panel. It also shows
elapsed time for the current launch, starting at zero and continuing through
Chromium startup even if a status poll is delayed. Periods without installer output
are shown only during installation; silence alone does not prove it is stuck. Installed files remain on disk for subsequent launches.

Authenticated clients can poll the `/ws` event `browser_startup_status` with `{}`
or POST `/api/plugins/_browser/status` with the usual session and CSRF token. Both
return `startup` with `state`, `stage`, `message`, `elapsed_seconds`, `stage_seconds`
and `quiet_seconds`. These reads do not start a sandbox or wait for installation.
`ready` describes the dependency worker; the panel then shows Chromium startup
until its viewer connects. Raw install logs remain private inside the sandbox.

The noVNC viewer uses Agent Zero's authenticated WebSocket bridge. Docker builds
provide `/usr/local/lib/tuxee-gui`; guests mount this public display bundle read-only,
sharing its binaries, loader, libraries and keyboard data without downloading or
copying them per sandbox. A plain host symlink cannot cross the guest filesystem.
Source installations without the bundle build it once inside their browser guest;
this slower fallback requires network access but no host root or package installation.
Browser owns window placement, so it does not need Tuxee's terminal session or window
manager. GTK file/save dialogs use private, display-sized settings. Chromium still
downloads its own runtime and libraries (including GTK) on first use.

Browser reuses the image's Python in a lightweight virtual environment; it does
not download Python 3.12 or uv. An available Node 22+ replaces the SDK's duplicate
Node binary through a symlink; other images retain the bundled driver runtime.
GTK and international fonts remain available. The pinned Chromium runtime
manifest omits Xvfb and its unnecessary Mesa/LLVM dependency tree; APT resolves
only the libraries actually requested. Keep this manifest aligned with SDK upgrades.
An installer update removes the old guest Python bootstrap and obsolete viewer
dependencies without touching browser profiles/downloads.
Repeated viewer requests at the same size do not launch resize clients or rewrite
GTK settings.

The bundled noVNC sources and licenses are in `webui/vendor/novnc/`; they match
Tuxee's noVNC 1.6.0 with its resize validation and H.264 probe cleanup fixes.
