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

Temporary sandboxes use `--overlay2=root:memory` for their live upper layer.
They retain atomic recovery snapshots and expire after the configured number
of days since last execution (seven days by default). Permanent sandboxes use
a private `root:dir=...` disk-backed upper layer and never expire.

Every sandbox receives the configured shared exchange folder at `/shared`.
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
or `/shared`. Ownership metadata reserves `chat_id`, `project_id`, and
`agent_id`; the prototype lists all managed sandboxes without filtering.

## Runtime images

Sandbox root filesystems are resolved at runtime from the configured
Docker/OCI image reference. `skopeo` copies the selected platform image
without a Docker daemon, and `umoci` unpacks it into the private image cache.
New sandboxes resolve tags and pin both the reference and immutable digest in
their metadata. Existing sandboxes always restart from that digest, even when
the tag later moves.

The default reference is `docker.io/library/python:3.13-slim-bookworm` and can
be changed in plugin settings or per sandbox. A usable image must provide
`/bin/sh` and `/bin/bash`; Python, Node.js, Git, and other tools are available
only when the selected image includes them. Image `ENTRYPOINT`, `CMD`, working
directory, and user are intentionally ignored because Agent Zero supplies a
controlled root process, `/workspace`, and runtime environment.

Cached images show their size, platform, digest, last use, and referencing
sandboxes on the management screen. Manual deletion refuses referenced images.
The hourly cleanup removes only unreferenced images unused for 30 days by
default. An optional containers-auth JSON path supports private registries
without putting credentials in command arguments or plugin metadata.

## gVisor runtime

The base build installs the signed gVisor apt package in a throwaway stage and
copies only `runsc` plus its required `gvisor_sentry` sidecar into the final
image. The containerd shim, remote-checkpoint gofer, and optional metric server
are omitted. `skopeo` and `umoci` remain available, and no sandbox rootfs is
baked into the image. The local Compose example keeps the outer container
unprivileged with `no-new-privileges`, uses an init reaper for detached
runtimes, and relaxes its seccomp profile for nested systrap. Native
deployments must provide the equivalent `CAP_SYS_CHROOT` and kernel policy;
the Doctor action reports missing prerequisites and never falls back to an
unsandboxed runtime.

Persistent state and `/shared` must live on durable storage. Private state is
never mounted into `/shared`, and private snapshots are replaced atomically.

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
