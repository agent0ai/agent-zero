# Sandbox Image DOX

## Purpose

- Own the small OCI image used for agent code execution inside PRoot.

## Ownership

- `install.sh` owns Python/IPython and Node/npm setup and runtime checks, shared by Docker builds and the lazy PRoot builder.
- `Dockerfile` builds the standalone image from matching official Python and Node images.
- `README.md` owns default-image delivery, recovery and optional standalone builds.
- `proot/` owns the pinned PRoot build and its source-update installer.

## Local Contracts

- Use official Python and Node images with the same Debian release.
- Keep Python and pip in the global `/usr/local` environment; do not create a venv.
- Include IPython for the existing Python code execution tool, and npm/npx for Node.
- Keep shared-library dependencies needed by Node on both amd64 and arm64.
- Do not copy Agent Zero source, credentials, user data, or the framework's dependencies into this image.
- The bundled OCI layout supplies a shared base. PRoot overlays a per-guest sparse directory in userspace using the existing Docker permissions.
- Image selection, digest pinning, unpacking and lifecycle belong to `plugins/_sandboxing/`.

## Work Guidance

- Keep project-specific libraries out of the base; install them in the sandbox as needed.
- Docker distributes the OCI bundle with zstd compression. The cache import requests gzip from Skopeo for the Trixie umoci unpacker. Lazy local builds skip recompression for distribution.
- The built-in reference is `agent-zero-sandbox:3`; bump its recipe version deliberately when changing the runtime contract. It is resolved locally, not pulled from Docker Hub.
- Keep the Python and Node base references in the root Dockerfile and `plugins/_sandboxing/helpers/builtin_image.py` synchronized.

## Verification

- Build `docker/sandbox`; its build checks verify global Python and each command.
- Run `A0_PROOT_INTEGRATION=1 pytest tests/test_proot_runtime.py` with the rebuilt PRoot to check empty uppers, merged enumeration, deletion persistence and peer isolation.
- Exercise Python/IPython, global pip installation, Node and npm inside a real PRoot sandbox.

## Child DOX Index

No child DOX files.
