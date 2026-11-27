# Browser

The internal browser controls full Chromium over a private DevTools pipe and displays it through Tuxee’s minimal Xvnc in an on-demand child sandbox. Every chat sees the same Chromium windows and tabs. Use the Browser header to switch windows or open another one. Within each window, use Chromium’s own tabs, address bar and settings. DuckDuckGo is the initial homepage and can be changed in Chromium.

The agent can call `list` to find a tab you opened, then select its `browser_id`. It can also open a tab in a specific `window_id` or request a new window. Resetting a chat preserves the shared browser. Bring Your Own Browser uses the host connector. On Chromium, enabling Browser in Host Access grants the same raw CDP commands and events as Container mode. Screenshots and uploads also retain their Agent Zero artifact and file handling.

PRoot presents the internal browser as root, so the guest launches Chromium with
`--no-sandbox`. Chromium’s renderer sandbox is disabled. A managed policy inside
the Browser guest hides command-line flag warnings in the viewer. You can inspect
the effective setting at `chrome://policy`.

The sandbox persists installed packages and exposes only the browser profile,
download directory and selected extensions. Uploads transfer selected bytes.
See the [plugin sandbox guide](../../docs/developer/plugin-sandboxes.md) for
lifecycle, sharing, upgrade behavior and runtime requirements.

Browser logins and settings live in `usr/plugins/_browser/profile`, alongside the
persistent user data.

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
running Chromium runtime. The HTTP status includes `chromium.transport` (`cdp-pipe`) and the executable path once the guest is ready. The `pending` flag stays true until that context's open/subscription
requests finish, including viewer preparation. The viewer then shows its connection
stage until VNC connects. Raw install logs remain private inside the sandbox.

The noVNC viewer uses Agent Zero's authenticated WebSocket bridge. Docker builds
provide `/usr/local/lib/tuxee-gui`; guests mount this public display bundle read-only,
sharing its binaries, loader, libraries and keyboard data without downloading or
copying them per sandbox. A plain host symlink cannot cross the guest filesystem.
Source installations without the bundle build it once inside their browser guest;
this slower fallback requires network access but no host root or package installation.
Browser owns window placement, so it does not need Tuxee's terminal session or window
manager. GTK file/save dialogs use private, display-sized settings.

The browser sandbox uses the image’s Python and reuses its installed full Chromium.
If the guest has no browser yet, first use installs Debian’s `chromium` package
for the guest architecture. APT supplies the native libraries. The profile and
downloads live on their own persistent mounts.
Repeated viewer requests at the same size do not launch resize clients or rewrite
GTK settings.

The bundled noVNC sources and licenses are in `webui/vendor/novnc/`; they match
Tuxee's noVNC 1.6.0 with its resize validation and H.264 probe cleanup fixes.

## Updating the internal browser

Normal starts reuse the guest executable offline. Browser security updates are an
administrator operation. Run the commands below from `/a0` in the Agent Zero
container with the Browser service running. Save work in all tabs and use
Chromium's menu to exit before replacing a build. Keep a closed-browser backup
of `usr/plugins/_browser/profile` for rollback across major versions.

Inspect the active binary, its version and Debian package ownership with this command.

```sh
python -m helpers.sandbox exec service-browser sh -ec '
    binary=$(readlink -f /opt/runtime/bin/a0-chromium)
    echo "$binary"
    "$binary" --version
    dpkg-query -S "$binary" || true
'
```

**Debian package.** If the owner is `chromium`, update it inside the same guest.

```sh
python -m helpers.sandbox exec service-browser sh -ec '
    apt-get update
    apt-get install -y --only-upgrade --no-install-recommends chromium
    /opt/runtime/bin/a0-chromium --version
'
```

**Standalone build.** For a browser supplied outside APT, obtain the newer full
bundle from its original distributor for the guest architecture. Verify its
integrity and unpack the whole bundle into a versioned directory on the guest’s
persistent disk. Pass the absolute guest path to its executable as the final
argument below. This publishes the selected build through a single entry point.

```sh
python -m helpers.sandbox exec service-browser sh -ec '
    binary=$(readlink -f "$1")
    "$binary" --version
    entry=/opt/runtime/bin/a0-chromium
    [ "$binary" = "$entry" ] && exit 0
    mkdir -p /opt/runtime/bin
    ln -sfn "$binary" "$entry.next"
    mv -Tf "$entry.next" "$entry"
' sh /absolute/guest/path/to/chrome
```

Open Browser again. In `chrome://version`, check the new version and the profile
path under `usr/plugins/_browser/profile`. Verify the saved browser state you
use. After verification, a superseded standalone bundle can be removed from its
recorded guest installation directory. The profile, downloads and enabled
extensions have separate mounts.
