# Sandboxing Plugin DOX

## Purpose

- Own direct gVisor/runsc sandbox lifecycle, execution, destination discovery, and management UI.

## Ownership

- `helpers/images.py` owns daemonless Docker/OCI pull, unpacking, digest-pinned image cache metadata, image last-use tracking, and safe cache deletion.
- `helpers/manager.py` owns validation, OCI bundles, runtime state, snapshots, mounts, sandbox/image references, expiry, and safe deletion.
- `helpers/runtime.py` owns resolved plugin configuration and the process-local manager.
- `helpers/shell.py` owns interactive `runsc exec` terminal sessions.
- `tools/`, `api/`, `prompts/`, `extensions/`, and `webui/` expose the manager without duplicating lifecycle logic.

## Local Contracts

- Invoke `runsc` directly with argument arrays and `shell=False`; agent-generated shell text is only passed inside the sandbox.
- Never use a Docker socket, nested daemon, SSH server, KVM, or an unvalidated sandbox path.
- Pull images through `skopeo` and unpack them through `umoci` with argument arrays, bounded output, timeouts, and no shell. Registry credentials may only be referenced through a configured auth file.
- Pin every sandbox to an immutable image digest. Tag refreshes affect new sandboxes only; image deletion and cleanup must refuse every digest referenced by sandbox metadata.
- Treat image cache entries as private runtime state. Automatic cleanup removes only unreferenced images whose last-use time exceeds the configured lifetime (30 days by default).
- Keep the shared mount explicit at `/shared`; optional binds must have validated absolute sources and sandbox destinations.
- Temporary sandboxes use the memory-backed root overlay and expire from configurable last-use time. Permanent sandboxes use a private disk-backed overlay and never expire.
- Metadata reserves chat, project, and agent ownership fields without filtering the first-prototype listing.
- Lifecycle mutations must use per-sandbox and image-cache thread/process locks and atomic metadata/snapshot replacement.

## Work Guidance

- Keep framework adapters thin and manager behavior independently testable without a real gVisor installation.
- Treat changes to capabilities, namespaces, mounts, networking, paths, or `runsc` flags as security-contract changes.

## Verification

- Run `pytest tests/test_sandboxing.py tests/test_code_execution_destinations.py` after manager or destination changes.
- Run the documented Linux lifecycle smoke test in an image with gVisor before claiming runtime compatibility.

## Child DOX Index

No child DOX files.
