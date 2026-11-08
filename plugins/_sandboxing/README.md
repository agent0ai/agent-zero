# Sandboxing

The bundled `_sandboxing` plugin runs named OCI containers directly with
gVisor's `runsc`. It does not use Docker child containers, a Docker socket,
SSH, a nested daemon, or KVM.

## Agent behavior

`code_execution_tool` now accepts `destination`:

- `default` (the default) creates or wakes the configured default sandbox.
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

## Storage policy

New sandboxes use a private writable disk filesystem, copied with reflinks
when supported. Restart reuses those files without taking or extracting tar
snapshots. Temporary sandboxes expire after the configured inactivity period
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

Every sandbox receives `/shared` and, by default, Agent Zero's `usr/` at
`/a0/usr`. Private manager state and image caches are masked inside user-folder
mounts. Services can disable usr sharing. Host root access at `/host` requires
an explicit `host_root=True` / `--host-root` launch option.

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

The default reference is `agent-zero-sandbox:1`, providing global Python 3.13,
pip, IPython, Node.js 22, npm and npx. Docker builds bundle it at
`/opt/agent-zero/sandbox-image`, so a fresh installation can create its first
sandbox offline. The first use unpacks it into the disk cache; subsequent
starts reuse the cache and each sandbox's private disk filesystem.

Native installations, older images, or a missing/damaged bundle build the same
recipe on first use through gVisor. This requires working `runsc`, `skopeo`,
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

## gVisor runtime

The runtime uses rootless systrap with directfs to reduce filesystem-helper
round trips. Directfs lets the Sentry access the configured filesystem directly
with additional internal filesystem privileges; guest mount restrictions and
instance masks still apply. It does not require adding outer Docker capabilities.
Validate the supported runsc release under the deployment's existing kernel and
seccomp policy; this does not make gVisor compatible with every Docker policy.

The base build installs the signed gVisor apt package in a throwaway stage and
copies `runsc` plus its required Sentry, Sentry prewarmer, proc umounter,
and file-descriptor parking sidecars into the final image. The containerd shim, remote-checkpoint gofer, and optional metric server
are omitted. `skopeo` and `umoci` remain available, and the runnable Docker image
bundles the default OCI image. The local Compose example keeps the outer container
unprivileged with `no-new-privileges`, uses an init reaper for detached
runtimes, and relaxes its seccomp profile for nested systrap. Native
deployments must provide a kernel policy compatible with rootless runsc;
the Doctor action reports missing prerequisites and never falls back to an
unsandboxed runtime.

Persistent state and `/shared` must live on durable storage. Private state is
never mounted into `/shared`; legacy snapshot records remain readable.

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

The unit suite mocks the `runsc` boundary; this Linux smoke test is required to
validate the actual kernel, gVisor release, architecture, and outer-container
security policy.

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
