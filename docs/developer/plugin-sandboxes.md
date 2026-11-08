# Sandboxed plugin runtimes

Document Query, Whisper STT, Local TTS, Telegram, WhatsApp, mail and the internal Browser use the shared
gVisor lifecycle manager. Their tools, settings and authenticated APIs stay in
Agent Zero. Heavy execution and dependency installation happen in the guest.

## Choosing dependency location

Prefer these existing sandboxes for plugin-owned Python, Node and native packages,
heavy inference, browser/document/media workers and external integration clients.
Keep lightweight tools, hooks, configuration and authenticated API/UI adapters in
the framework; they call the guest without importing guest-only libraries. Do not
add optional guest packages to root requirements or global pip/npm/apt installs.
Main-environment dependencies are appropriate only for functionality that must
execute there: document the concrete reason in the plugin README and keep them
minimal. Hooks still execute in the framework; worker sandboxing is not total
plugin isolation, and host networking is not a network isolation boundary.

Use [`helpers.sandbox.get_manager()`](../../helpers/sandbox.py) for the configured,
instance-scoped lifecycle rather than building another runtime. The bundled
[`SandboxWorker`](../../helpers/sandbox_worker.py) provides blocking `call`, async
`acall`, explicit `aprepare` and `stop`; construction alone does not provision.
Its current source lookup is `plugins/<plugin>/`, so it is not a drop-in for custom
plugins under `usr/plugins/`. For those, use the same manager with explicit
`SandboxMount` source paths, plugin ownership, `service=True`, `share_usr=False`
and child lifetime (`standalone=False`), following the worker's private input and
bounded result handling. Mount only required plugin-owned or authorized data;
preserve authentication, credential handling and user-data ownership.

Keep manifests/installers with the plugin and execute them inside its persistent
guest. The [Document Query adapter](../../plugins/_document_query/helpers/sandbox.py)
and [installer](../../plugins/_document_query/sandbox/install.sh) show the bundled
pattern. The shared [worker boot script](../../plugins/_sandboxing/sandbox/boot.sh)
uses `sandbox/install.sh` and `sandbox/requirements.txt`, fingerprints setup inputs
and records success only after installation. Preserve idempotent setup, failure
reporting and retry; stopping a guest retains its packages and model caches.

Install/update/uninstall remain owned by `hooks.py` and framework management APIs.
Hooks may delegate guest provisioning to automatic worker setup on first actual
use. Early-needed features and configured inbound listeners must instead prepare
at enablement/startup before they are needed; do not wait for a message the
unstarted receiver cannot receive. Respect disabled state. Disable stops owned
workers; uninstall removes owned sandboxes/resources while preserving shared
dependencies and unrelated or separately mounted user data. Never require
`execute.py` or a user-run post-install command.

Developer/reviewer check: optional guest dependencies stay out of main requirements
and feature import/general boot paths do not eagerly install them. Verify first-use
setup/retry, required enablement/startup readiness and owned cleanup. Lazy provisioning
reduces the shipped/default footprint, but may not reduce total disk after use.

## Existing runtime behavior

| Runtime | Starts | Stops | Persistent files |
| --- | --- | --- | --- |
| Document parsing/OCR | First parse or PDF/HTML knowledge import | After the request | Packages and parser model caches |
| Whisper STT | First transcription or explicit preload | After 120 seconds idle, disable or parent exit | Packages and Whisper models |
| Paradee/Kokoro TTS | First synthesis or explicit preload | After 120 seconds idle, disable or parent exit | Packages and speech models |
| Internal Browser | First browser use | Runtime shutdown, configuration change, disable or parent exit | Packages, Chromium, existing profile and downloads |
| Telegram | Enabled bot job-loop startup or connection test | Disable, shutdown or transport recovery | Packages; configuration stays in A0 |
| WhatsApp | Enabled job-loop startup or explicit pairing | Disable, shutdown or configuration change | Packages and mounted existing login/session/media directories |
| Mail | Configured polling, connection test or send | After 120 seconds idle, disable or shutdown | Packages; UID checkpoints and configuration stay in A0 |

All use child lifetime and instance-scoped service names. Configured inbound integrations start from their existing job-loop hooks on enablement/startup; disabled integrations do not provision. Other feature guests remain cold until needed. The tunnel separately uses standalone
lifetime. Installation reuses the configured OCI image and prepares Python 3.12
inside the guest for compatibility with existing package pins. These installers
require a Debian-compatible image with Python and apt. Initial setup requires
internet access and can take several minutes; later starts reuse the disk root.
CPU Torch wheels are selected explicitly.

The shared `helpers.sandbox_worker.SandboxWorker` uses private, read-only request
mounts and bounded result reads with symlink protection. Requests/results are
cleared after acknowledgement. Cancellation and request errors stop the worker;
setup has a separate 30-minute bound. No outer worker server or new listening
port is introduced. Service sandboxes do not share the agent `/shared` exchange
or Agent Zero's whole `usr/` directory. Network mode currently remains `host`,
which permits both internet and host loopback access.

The browser exposes only its existing profile, downloads directory and selected
extension directories. Uploads pass selected file bytes through Patchright;
screenshots return through its normal protocol. The complete automation runtime (including Patchright Python and its Node driver) runs inside the guest. A browser-specific multiplexed pipe carries operations, frames and cancellation acknowledgements; no host browser SDK is imported. Tuxee’s minimal Xvnc remains on loopback behind the authenticated, token-scoped noVNC
virtual-desktop gateway. Browser directory pickers see the guest filesystem;
arbitrary host folders are not implicitly mounted.

`python -m helpers.sandbox list` lists these services alongside other instance
sandboxes. Stop retains dependencies and models; delete removes the private
disk root. Browser profile/download mounts remain owned by the browser and are
not deleted with the sandbox. Uninstall removes the owned sandbox; disable stops it.

Fresh outer images omit Patchright/Playwright, their bundled drivers, optional
transport packages (aiogram, IMAPClient, Exchange), WhatsApp node_modules and the
retired Office/Xfce/Xpra stack. Shared memory/embedding libraries and the cached
embedding model remain included. Office tools and separate Office tabs are absent.
Editor retains the existing Office text/history store and backups without deleting
the source. User documents, configurations, browser profiles and login state remain.

Desktop embeds the pinned Tuxee runtime directly in the outer image. Its native
minimal VNC session and window manager use the existing Desktop panel, with HTTP
and WebSockets proxied at `/desktop/tuxee/`. The internal listener binds to loopback;
publish only the usual A0 WebUI port. A0 authentication and same-origin gating run
before Tuxee's own PAM/session/CSRF checks. In the managed Docker runtime, Desktop
automatically signs in as root when `ROOT_PASSWORD` is configured. The proxy keeps
that shared session cookie in memory; the browser retains its normal CSRF checks.
Other runtimes, missing credentials or failed login attempts show Tuxee's normal
Linux login page. Failed automatic attempts retry after a 60-second cooldown on
the next page load. Existing manual sessions take precedence. Explicit logout
returns that browser to manual login for its browser session; other clients sharing
the automatic session reconnect. This follows the existing A0 access policy,
including instances with WebUI login unconfigured. The iframe retains its terminal
when docked; Office applications are not installed.

Both supported image recipes build Tuxee from pinned, checksum-verified sources
with a small relative-URL patch. The patch intentionally changes login public
bytes to support the embedding prefix without bypassing authentication. Tuxee's
in-app updater is disabled; its pinned version follows Agent Zero. Source-only
upgrades build missing/stale Tuxee assets in a disposable sandbox on first Desktop
use (administrator access and network required), publishing the binary after a
successful build. The startup retirement migration uninstalls only replaced outer
Python distributions and named installer caches. It defers native package/service
retirement while old GUI processes may contain unsaved work, then retries on the
next restart. Service declarations retain a reversible backup. Rebuild the image
to reclaim immutable old layers. Existing speech model caches are preserved and
may be downloaded again into the guests.

Guest installation failures leave no success marker; subsequent use retries.
Stopping retains each private disk root, while disable hooks stop the corresponding
workers. WhatsApp uses a per-process token on its loopback bridge; Telegram/mail
carry credential input only in private transient IPC. Guest networking still uses
host mode, so it is not a network isolation boundary. No live account or external
message is needed for the fixture checks in `tests/integration_guest_smoke.py`.

These changes inherit the gVisor launch requirements in the
[sandbox runtime guide](../../plugins/_sandboxing/README.md#gvisor-runtime). They do not establish compatibility with
every Docker default seccomp profile.

## Python runtimes and image cleanup

The outer image has one global Python 3.12 environment for the framework, plugin
hooks and explicit `local` code execution. There is no separate host code-execution
venv or pyenv. Debian's Python 3.13 belongs to Supervisor and its event listener;
it is not an alternative framework environment. Outer IPython and Node remain
available for explicit local execution. SSH and connected-host destinations keep
their existing routing; the default destination is the isolated sandbox.

The bundled sandbox base has global Python 3.13, IPython and Node. Feature guests
also prepare Python 3.12 in `/opt/runtime` for their existing package pins; this
venv points to a guest-owned uv-managed interpreter and does not reuse the host
framework's site-packages. These isolated runtimes are intentional. Stopping a
guest preserves its installed packages and model caches.

Base and both application installation passes disable uv's wheel/build cache,
while preserving installed files and the included embedding model. New images
omit Newspaper, jieba3k, pyreqwest-impersonate and the exclusive feed/parser
dependencies. Framework HTML fetching uses HTTPX and document parsing uses the
existing Document Query guest. Shared Pillow, lxml, BeautifulSoup, requests, YAML
and NLTK (including its security floor) remain.

Custom plugins using these scraper libraries must declare/install them explicitly;
implicit outer availability is no longer supported. Source-update retirement
preserves packages required by other installed distributions, but cannot detect
undeclared imports in user scripts. A rebuilt image is needed to reclaim old
cache/dependency layers; a source-only update cannot shrink the underlying image.

The outer image does not include GCC/G++, Make, CMake, compiler development headers,
wget, unzip or speech-device/audio-codec libraries. Native compilation
belongs in a build stage or a plugin's install script inside its sandbox. Curl,
7-Zip, IPython, Node, pipx (for MCP servers) and the native runtime libraries remain. Skopeo and Umoci
are copied with their registry configuration and shared-library dependencies,
without Debian's unused CNI network stack. Image builds also skip Python bytecode
generation and omit Torch's native test runners while retaining its shared-memory
manager. Existing installations retain their tools and user-installed packages;
rebuild both base and application images to obtain these savings. Source-only
updates do not automatically purge generic system tools or shared libraries.
