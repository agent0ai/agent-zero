# Docker DOX

## Purpose

- Own Docker runtime layout, build inputs and sandbox recipes.

## Ownership

- The root `Dockerfile` builds the local and published images on pinned Tuxee.
- `run/` owns runtime files, Compose and release self-update hooks.
- `sandbox/` owns the Trixie Python and Node sandbox recipe and the PRoot build.

## Local Contracts

- Install framework, hooks and local agent/user packages into official Python's global `/usr/local` environment. Do not add pyenv or a virtual environment.
- Strip unneeded symbols from the official Node binary for the outer image and copy its bundled npm. Link npm and npx from that copy and leave Corepack in the build stage. Build checksum-pinned PRoot in a disposable stage and retain only its runtime binary. Copy Skopeo and umoci with the registry defaults and shared libraries they need.
- Keep compilers and plugin-only document, Browser and speech packages out of the outer runtime. Compile app and dependency bytecode with checked hashes and line numbers only. Ship tests as source. The Python build stage strips wheel debug sections and updates installed RECORD hashes, preserving the reviewed LiteLLM files. Runtime Python suppresses bytecode writes to avoid a startup watcher lock inversion.
- Build-time APT steps remove package lists in the same layer. Exclude secrets, local environments and runtime data from the context.
- Use the repository root as the build context. Local builds use the working tree without Git metadata. Published builds clone the selected branch with commit ancestry and tracking for self-update. An optional `SOURCE_COMMIT` pins its contents. Refresh the source stage in the publishing workflow.
- Prepare the checksum-pinned ONNX model and default token encoding in image-owned caches under `/opt/agent-zero`. Tuxee declares `/root` as a volume, so replacing a container may reuse its previous contents. Local builds validate offline inference and token counting during asset preparation.
- Bundle the sandbox OCI layout outside `/a0` at `/opt/agent-zero/sandbox-image-v4` using a read-only stage mount. Keep it readable by rootless callers and import it on demand.

## Work Guidance

- Synchronize Docker changes with `.github/workflows/docker-publish.yml`. Update setup docs when ports, mounts or build commands change.

## Verification

- Build from the root and smoke-test startup, local Python, OCI unpack and guest execution after changing the runtime.

## Child DOX Index

| Child | Scope |
| --- | --- |
| [run/AGENTS.md](run/AGENTS.md) | Runtime files, Compose and self-update. |
| [sandbox/AGENTS.md](sandbox/AGENTS.md) | Sandbox image and PRoot build. |
