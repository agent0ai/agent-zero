# Docker Base Image DOX

## Purpose

- Own the Agent Zero base image build context.
- Build the operating system, package, Python, SearXNG, SSH, and bootstrap layers reused by runnable images.

## Ownership

- `Dockerfile` owns base image layering and installation order.
- `build.txt` owns maintainer build and push command notes.
- `fs/ins/` owns installation scripts copied into the image.
- Files under `fs/` are copied to container root during the base build.

## Local Contracts

- Preserve cache-friendly package and runtime installation stages.
- Keep locale and timezone defaults compatible with the root Docker contract.
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
