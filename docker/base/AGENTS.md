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
- Keep daemonless `skopeo` and `umoci` image tooling available to the bundled sandboxing plugin.
- Seed CPU Torch/Torchvision with `numpy<2` and `filelock>=3.20.3,<4`, matching the application graph so Depfix can retain CPU selections during its bulk solve.
- Pin the global Depfix bootstrap to the application requirement so cached package planning preserves requested extras.
- Keep Debian's `build-essential` toolchain and CMake available for source-distributed Python dependencies resolved into Depfix's shared store.
- Sandbox root filesystems are runtime-managed cache content; do not add a baked sandbox rootfs unless its lifecycle and provenance contract is updated with the plugin.
- Do not install SearXNG, create its service user or virtualenv, or copy its configuration into the base image; the placeholder integration is owned by `plugins/_searxng/`.
- Do not install Tesseract, OCR language packs, or Poppler in the base image; `plugins/_document_query/` installs those system packages only when a legacy OCR fallback reaches its first use.
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
