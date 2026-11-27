# Sandboxing

The bundled `_sandboxing` plugin runs named OCI filesystems through patched
PRoot, separate Linux users, and file-level copy-on-write. It does not use Docker child containers, a Docker socket,
SSH, a nested daemon, or KVM.

## Agent behavior

`code_execution_tool` now accepts `destination`:

- `default` creates or wakes the configured default sandbox. With the automatic type setting, this sandbox is permanent and other new sandboxes are temporary. You can choose a type explicitly at creation.
- A listed sandbox name targets that sandbox; `sandbox:<name>` is always an
  unambiguous form.
- `local` targets the operating system running Agent Zero and should be used
  only when Agent Zero or its core files must be changed.
- `host` appears only while an A0 CLI or Launcher host with remote execution
  enabled is connected. It reuses the existing authenticated connector.

Terminal session ids are isolated per destination. Commands, `input`, output
polls, and resets must use the same destination and session id.

The `sandbox` tool and the plugin's main screen support list, doctor, create,
inspect, save, stop, start, expiry cleanup, and exact-name delete operations.
They also pull, list, inspect, clean, and delete cached sandbox images.
In chat, the `SBX` step shows the action and the name when supplied.

Use **Browse files** on a sandbox row to open its persistent filesystem in Files,
including while the sandbox is stopped. You can browse folders and download files.
The managed `/workspace` is visible here. This view excludes guest symlinks, extra mounts, transient paths such as `/tmp` and
`/run`, and plugin service sandboxes.

## Storage policy

On a fresh installation each sandbox has the following host paths.

| Path | Contents |
| --- | --- |
| `/a0/sandboxes/images/<image-digest>/` | Cached image shared by guests |
| `/a0/sandboxes/instances/<name>/fs/` | Private changes to the guest image |
| `/a0/sandboxes/instances/<name>/cow/whiteouts/` | Deletions that hide inherited paths |
| `/a0/sandboxes/instances/<name>/data` | Relative symlink to `/a0/usr/sandbox_data/<name>/` |
| `/a0/usr/sandbox_data/<name>/workspace/` | Writable files mounted at guest `/workspace` |

For additional persistent data, create a sibling of `workspace/` and bind it to the
desired guest path. An explicit `/workspace` bind uses the selected source.
Deleting or expiring a guest preserves its data. Recreating the same name
reattaches it. Select **Sandbox — <name>** in Time Travel to restore that guest’s
user files. Project and workdir binds use their own workspace history.

The runtime tree is excluded from Git, Docker build contexts, default user
backups and filesystem observation by Time Travel and the plugin watchdog.
Explicit storage settings override the default paths.

A new guest starts with an empty `fs/`. PRoot resolves reads and directory
listings against that directory and the shared, digest-pinned image. Writing an
inherited file copies it into `fs/` on demand. Deleting an inherited name records
a whiteout. Renaming an inherited directory materializes its visible subtree.
Stop and restart reuse the same base, private files, and whiteouts. The image
cache and guest directories can reside on separate filesystems. The guest
store needs POSIX ACLs and hardlink support for private file aliases. A custom
image with files in `/workspace` still seeds the managed workspace once.
Existing disk roots keep their data. Legacy tar-overlay snapshots require
export on the previous version. Temporary sandboxes expire after the configured inactivity period
(seven days by default); permanent sandboxes never expire.

Storage reporting never scans files during start, stop, list, inspect or status
polling. Use **Calculate** beside Private data to measure asynchronously while
the controls remain usable. The last result stays visible until recalculated;
it is an estimate if files change during the scan. API status returns
`size_bytes: null`; the separate `disk_usage` action returns the requested size.
Python async callers can use `await asyncio.to_thread(manager.disk_usage, name)`;
the CLI command is `python -m helpers.sandbox disk-usage NAME`.
Cached image sizes come from import/pull metadata; unavailable sizes remain
unknown without scanning. Image-import size-limit checks still apply.

On Linux, guests share a numeric group for `/shared`. New workspaces use
their guest's group. On older installations the original guest UID keeps
its access to retained private files. Agent Zero repairs traversal on the
common `usr/sandbox_data` directory and converts recognized legacy permissions
inside the built-in `/shared` exchange. Existing private workspaces and custom
mounts retain their host permissions. Docker bind mounts use these same numeric IDs.
The manager tracks and stops processes by their distinct Linux UIDs.

Every sandbox receives `/shared` and, by default, Agent Zero's `usr/` at
`/a0/usr`. Private manager state, image caches and the per-sandbox data directory are masked inside broad user-folder
mounts. Services can disable usr sharing while keeping the common exchange. Host-root bindings are
unsupported; bind only the directories the sandbox needs.

Creation APIs also accept optional folder binds:

```json
{
  "source": "/absolute/host/folder",
  "destination": "/mnt/data",
  "read_only": true
}
```

Sources must be existing absolute non-symlink directories. Destinations must
be absolute sandbox paths and cannot overlap `/proc`, `/dev`, `/sys`, `/etc`,
or `/shared`. Metadata records instance and optional chat/project/agent/plugin
ownership. Plugin services are excluded from agent execution destinations.

## Runtime images

Sandbox root filesystems are resolved at runtime from the configured
Docker/OCI image reference. `skopeo` copies the selected platform image
without a Docker daemon, and `umoci` unpacks it into the private image cache.
New sandboxes resolve tags and pin both the reference and immutable digest in
their metadata. Existing sandboxes always restart from that digest, even when
the tag later moves.

The default reference is `agent-zero-sandbox:4`, providing Git, ripgrep, global Python 3.13,
pip, IPython, Node.js 22, npm and npx. Docker builds bundle it at
`/opt/agent-zero/sandbox-image-v4`, so a fresh installation can create its first
sandbox offline. The first use unpacks it into the disk cache; subsequent
starts reuse the cache and each sandbox's private disk filesystem.

Native installations, older images, or a missing/damaged bundle build the same
recipe on first use through PRoot. This requires working `a0-proot`, `skopeo`,
`umoci` and internet access for the official Python/Node images, apt and pip.
The build is serialized and cached; it does not run during ordinary WebUI
startup or install packages into the host Python environment. Failed builds
leave no ready image. If a lost pinned image cannot be reproduced with its
original digest, recovery reports an error instead of changing that sandbox's
base. Keep persistent image cache and sandbox state together when backing up.

The default can be changed in plugin settings or per sandbox; explicit user
settings and existing sandboxes are preserved. A usable image must provide
`/bin/sh` and `/bin/bash`; Python, Node.js, Git, and other tools are available
only when the selected image includes them. Image `ENTRYPOINT`, `CMD`, working
directory, and user are intentionally ignored because Agent Zero supplies a
controlled root process, `/workspace`, and runtime environment.

See the [sandbox image recipe](../../docker/sandbox/README.md) for optional
standalone builds. Other local images can be imported with
`python -m helpers.sandbox import-image ARCHIVE REFERENCE`, then selected in
**Sandboxing → Default image**. Arbitrary cache-only images must be reimported
if removed; registry references can be pulled again.

Cached images show their size, platform, digest, last use, and referencing
sandboxes on the management screen. Manual deletion refuses referenced images.
The hourly cleanup removes only unreferenced images unused for 30 days by
default. An optional containers-auth JSON path supports private registries
without putting credentials in command arguments or plugin metadata.

## Runtime requirements and isolation

Docker supplies the root manager; guest processes run as distinct leased UIDs.
PRoot presents UID 0 inside the guest so apt/pip installers keep working. The
manager requires Linux, the patched `a0-proot`, libtalloc, libseccomp and POSIX ACLs.
Fresh images include these and Compose uses default Docker seccomp with
`no-new-privileges` and an init reaper. No AppArmor profile, user namespaces,
FUSE device or mount capability is required by this implementation.

Source updates stop old sandboxes before switching and build the runtime once
through the release hook; startup also checks it. Debian-based native root
installations use `docker/sandbox/proot/install.sh`. Rebuild the Docker image
to reclaim old gVisor image layers. Custom host security policies may still block
ptrace; test on the actual host.

This isolates dependencies and ordinary file changes, not hostile native code.
PRoot shares the host kernel and PID/network environment and is not equivalent
to gVisor's security boundary. Use one A0 instance per outer container and keep
its persistent UID registry with its sandbox state. Never reassign leased UIDs.
`network=none` blocks creation of non-Unix sockets with seccomp; it is not a
network namespace and Unix sockets in explicit bindings remain accessible.

Copy-on-write preserves user xattrs and hardlink aliases within a guest. As with
OverlayFS copy-up, previously opened read descriptors keep the old inode.
Metadata changes through a replaced or deleted lower file descriptor return
`ESTALE`. Reopen a lower directory descriptor after renaming or deleting its
path.
Image ownership/modes are normalized for shared immutable files; host ACLs and
file capabilities are not copied into guest-private files.

## Linux smoke test

After building the base and runnable images, use the UI or Python manager to:

1. Run Doctor and verify it passes under the final service identity.
2. Pull the configured image and verify its platform and digest in the UI.
3. Create `alpha` and `beta`; check that `/workspace` changes are private.
4. Exchange a probe through `/shared`.
5. Save and stop `alpha`, start it again, and verify its private file survives.
6. Refresh a moved tag and verify existing sandboxes keep their old digest while a new sandbox uses the refreshed digest.
7. Verify a `network=none` sandbox cannot reach an external address.
8. Delete `alpha` and verify `beta` and the shared probe remain.
9. Verify image deletion refuses `beta`'s digest, then delete `beta` and exercise unused-image cleanup with a controlled clock.

Run `A0_PROOT_INTEGRATION=1 pytest tests/test_proot_runtime.py` inside a
disposable built image for real CoW, read-only bindings, lifecycle, timeout and
offline-network checks. Also verify browser rendering with its real installer.
Unit mocks alone do not establish compatibility with a host security policy.

## Process lifetime and CLI

`helpers.sandbox.get_manager()` is the shared Python API. Run
`python -m helpers.sandbox --help` for list/create/inspect/start/stop/restart/delete
and exec commands. Names/runtime state are scoped to the existing persistent
Agent Zero instance ID.

Child lifetime is the default. A parent pipe terminates the sandbox when its
creating process exits; the CLI stays attached for children. Use `--standalone`
for services which must remain after the caller exits. Standalone sandboxes
marked as running restore automatically at startup after Docker/container or
host restarts. Stopping clears the desired running state.

See [the tunnel PoC](../../docs/developer/tunnel-sandbox-poc.md) for the installer
script pattern and verification scope.

Transient `/tmp`, `/run` and PRoot scratch data live below short, private
`/run/a0-proot/<uid>` directories to keep Unix socket paths within Linux limits.
They are cleared on stop; persistent guest files remain in the CoW root.
