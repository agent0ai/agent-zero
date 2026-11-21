# Browser

The internal browser runs Chromium, its Patchright driver and Tuxee’s minimal Xvnc in an on-demand child sandbox. Every chat sees the same Chromium windows and tabs. Use the Browser header to switch windows or open another one. Within each window, use Chromium’s own tabs, address bar and settings. DuckDuckGo is the initial homepage and can be changed in Chromium.

The agent can call `list` to find a tab you opened, then select its `browser_id`. It can also open a tab in a specific `window_id` or request a new window. Resetting a chat preserves the shared browser. Bring Your Own Browser uses the host connector.

PRoot presents the internal browser as root, so Patchright launches Chromium with
`--no-sandbox`. Chromium’s renderer sandbox is disabled. A managed policy inside
the Browser guest hides command-line flag warnings in the viewer. You can inspect
the effective setting at `chrome://policy`.

The sandbox persists installed packages and exposes only the browser profile,
download directory and selected extensions. Uploads transfer selected bytes.
See the [plugin sandbox guide](../../docs/developer/plugin-sandboxes.md) for
lifecycle, sharing, upgrade behavior and runtime requirements.

Browser logins and settings live in `usr/plugins/_browser/profile`, alongside the
persistent user data. First use migrates an existing `tmp/browser/sessions` profile.
When switching an old full `/a0` mount to `/a0/usr`, run the updated Browser once
before recreating the container, or copy the old `tmp/browser/sessions/shared`
folder to `usr/plugins/_browser/profile` while Browser is stopped.

Launch reports six numbered stages: preparing the sandbox, installing dependencies,
installing Chromium, starting the display, launching Chromium, and preparing tabs /
connecting the viewer. The label describes the current operation within each stage.
Installed files remain on disk, so later launches skip cached installation stages.
Checking an existing session is shown separately from launching a browser.
During launch, a subtitle explains that first use takes a little while to install
dependencies. The same explanation appears in the browser tool's Browser setup
hint while the internal runtime starts; there is no elapsed timer.
The Start button stays hidden while launch is pending. If a reply is lost, the panel
checks the original operation and attaches when it finishes without opening another
tab. Confirmed failures allow retry; a disconnected status channel shows reconnecting.

Authenticated clients can poll the `/ws` event `browser_startup_status` with `{"context_id":"…"}`
or POST `/api/plugins/_browser/status` with the usual session and CSRF token. Both
return `startup` with `state`, `stage`, `message`, `step`, `steps`, and `pending`.
These reads do not start a sandbox or wait for installation. `ready` describes the
running Chromium runtime; `pending` stays true until that context's open/subscription
requests finish, including viewer preparation. The viewer then shows its connection
stage until VNC connects. Raw install logs remain private inside the sandbox.

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
