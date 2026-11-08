# Tunnel sandbox PoC

Remote Control now owns its UI, providers and installer in `plugins/_tunnel`.
No outer tunnel API server is started. Its authenticated API forwards control
to the shared sandbox manager; normal Agent Zero HTTP/WebSocket handling stays
in place. Cloudflare runs as a native daemon in its sandbox.

## Shared Python interface

```python
from helpers.sandbox import get_manager, SandboxMount
from pathlib import Path

manager = get_manager()
manager.create(
    "my-service",
    image="",  # configured system image
    sandbox_type="permanent",
    standalone=True,
    service=True,
    share_usr=False,
    network="host",
    ownership={"plugin_id": "my-plugin"},
    mounts=[SandboxMount(Path("/absolute/plugin"), "/plugin", True)],
    command=["/bin/sh", "/plugin/boot.sh"],
)
manager.list()
manager.stop("my-service")
manager.start("my-service")
manager.restart("my-service")
manager.delete("my-service")
```

The boot script runs an idempotent installer and then execs its service. Default
image: `docker.io/library/python:3.13-slim-bookworm`; registry image overrides
are supported. There is no Dockerfile builder: plugins supply installer scripts.

## CLI

Run from the Agent Zero checkout using its installed Python:

```sh
python -m helpers.sandbox list
python -m helpers.sandbox create demo --standalone
python -m helpers.sandbox exec demo sh -c 'echo retained > /workspace/example'
python -m helpers.sandbox restart demo
python -m helpers.sandbox exec demo cat /workspace/example
python -m helpers.sandbox stop demo
python -m helpers.sandbox delete demo --yes
```

Without `--standalone`, create/start/restart stay attached to the child. Closing
the parent pipe terminates the guest, including on an abrupt parent exit.
Standalone processes survive Agent Zero exits. On Docker/container or host
restart, processes die; Agent Zero automatically restores standalone instances
whose desired running state was not cleared by Stop.

## Files, networking and identity

New sandboxes have a writable disk root, copied from the cached image using
reflinks where supported. Restart reuses it without tar snapshots or rebuilding.
Temporary/permanent controls expiry, independently of child/standalone lifetime.

`/a0/usr` shares this installation's usr/ by default (`--no-usr` disables it).
`--host-root` explicitly exposes the outer root at `/host`. In Docker these are
container paths, not the desktop host's root. The tunnel opts out of usr sharing.

`--network host` is the default and provides internet and host loopback access.
`--network none` is offline. Separate internet-only networking is not implemented.

The existing persistent runtime ID namespaces instance storage, runsc roots/IDs,
and OCI annotations. Separate installations must have distinct persistent IDs.
Service sandboxes are excluded from agent execution destinations and tool actions.

## Verification

Focused tests cover disk recovery without snapshots, instance separation,
parent lifetimes, scoped mounts, bounded no-symlink status reads, plugin API
protection, origin handling, providers and Supervisor retirement. The watcher
regression reproduces an event arriving during registration; scheduling never
holds the registry lock while waiting for watchdog's dispatch lock.

Live checks use a dedicated container with the existing gVisor PoC settings
(`--init --security-opt no-new-privileges --security-opt seccomp=unconfined`).
These settings remain necessary for this tested environment; this work does not
establish compatibility with every default Docker seccomp profile. Run the same
checks on another kernel/architecture before claiming support there.

The amd64 PoC passed a real Cloudflare connection through Agent Zero login,
protected plugin API calls, invalid-CSRF rejection, and WebSockets. Disk writes
survived abrupt Docker restart and the startup hook restored standalone services;
child sandboxes remained stopped. A UID 1001 check also passed create, shared usr
access, private disk writes, and restart. One warm lifecycle restart took 0.52 s.
An active Cloudflare sandbox's two host processes accounted for approximately
35 MiB PSS in one snapshot; the earlier idle Python controller measured 222 MiB.
These are snapshots, not cross-platform resource guarantees.
