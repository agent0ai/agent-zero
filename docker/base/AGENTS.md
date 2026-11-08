# Docker Base Image DOX

## Purpose

- Own the Agent Zero base image build context.
- Build the operating system, package, Python, SSH, and bootstrap layers reused by runnable images.

## Ownership

- `Dockerfile` owns base image layering and installation order.
- `build.txt` owns maintainer build and push command notes.
- `fs/ins/` owns installation scripts copied into the image.
- Files under `fs/` are copied to container root during the base build.

## Local Contracts

- Preserve cache-friendly package and runtime installation stages.
- Keep the outer image based on `python:3.12-slim-trixie` and install Python packages into its global environment.
- Do not install another Python through apt or pyenv, and do not create a virtual environment.
- Copy Node and bundled npm from the matching official `node:22-trixie-slim` build stage; do not install Debian's unbundled `nodejs` or `npm` packages.
- Install the signed gVisor apt package in a throwaway stage and copy `runsc` plus its Sentry, Sentry prewarmer, proc umounter and file-descriptor parking sidecars into the final image; do not include its containerd shim, checkpoint gofer, or metric server.
- Copy daemonless `skopeo` and `umoci` plus `/etc/containers` and `/usr/share/containers` defaults from the tool stage. Install their shared libraries and GPG explicitly; do not inherit Debian's unused CNI/network-stack dependency. Verify registry copy, OCI unpack and rootless use after changing this boundary.
- Keep pip, uv and IPython for dependency installation and explicit local execution, and pipx for launching configured MCP servers. Pin pipx to 1.16.7 until newer releases support the framework's filelock/packaging bounds.
- Use `uv pip install --no-cache` so temporary wheels/build artifacts are removed in the installing layer; installed packages and embedding model assets remain intact.
- Keep compilers, Make, CMake and development headers out of the outer runtime. Native builds belong in disposable build stages or requesting plugin sandboxes. Preserve `libstdc++6` and `libatomic1` for Node/native runtime loading.
- Do not preinstall unused wget/unzip or ALSA libraries. Keep curl and 7-Zip, which serve runtime downloads and archive extraction.
- Disable implicit Python bytecode generation before installation/preload, and pass `--no-compile` to pip; runtime services already run without writing bytecode.
- The runnable image bundles the default sandbox OCI layout; writable sandbox roots and image-cache lifecycle remain owned by `plugins/_sandboxing/`.
- Do not install SearXNG, create its service user or virtualenv, or copy its configuration into the base image; the placeholder integration is owned by `plugins/_searxng/`.
- Do not install Tesseract, OCR language packs, or Poppler in the base image; `plugins/_document_query/` installs those system packages inside its sandbox when a legacy OCR fallback reaches its first use.
- Use Debian's built-in `C.UTF-8` locale without installing or generating locale data, and keep the timezone set to UTC.
- Do not add secrets, user data, or local environment files to the image context.
- Installation scripts must be noninteractive and suitable for multi-architecture buildx runs.

## Work Guidance

- Keep base dependencies here only when they are common to runnable Agent Zero images.
- Coordinate Python runtime changes with root Docker documentation and runnable image setup.

## Verification

- Build `docker/base` when changing Dockerfile or install scripts.
- Run a runnable image smoke check when base runtime behavior changes.

## Child DOX Index

No child DOX files.
