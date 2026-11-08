# Docker DOX

## Purpose

- Own Docker build contexts and runtime container definitions.
- Keep the shared Python runtime, exposed ports, mounted paths, and image build assumptions explicit.

## Ownership

- `base/` owns the base image context.
- `run/` owns the runnable image context and compose file.
- `sandbox/` owns the Python and Node image used inside gVisor sandboxes.
- Root `DockerfileLocal` is owned by the root contract but must stay compatible with this directory.

## Local Contracts

- Base the outer image on `python:3.12-slim-trixie`; do not add Kali repositories, pyenv, or a virtual environment.
- Install WebUI, API, scheduler, framework, plugin-hook, and local agent/user dependencies into the image's global Python environment.
- Verify backend imports, plugin hooks, and local code execution with `/usr/local/bin/python`.
- Keep build-time apt transactions self-contained: update, install or upgrade, and remove `/var/lib/apt/lists/*` in the same Docker `RUN`.
- Do not bake secrets, local `.env` values, or user data into images.
- Keep compose mounts aligned with `usr/` and other runtime-state expectations.
- Image changes that affect GitHub publishing must stay synchronized with `.github/workflows/docker-publish.yml`.

## Work Guidance

- Keep Dockerfile steps cache-friendly and explicit about which runtime they target.
- Avoid broad copies of ignored runtime folders.
- Update setup docs when ports, volumes, startup commands, or runtime layout change.

## Verification

- Build the affected Docker context when Docker behavior changes.
- Run Docker-related tests or startup smoke checks when changing runtime entrypoints.

## Child DOX Index

Direct child DOX files:

| Child | Scope |
| --- | --- |
| [base/AGENTS.md](base/AGENTS.md) | Base image Dockerfile, copied filesystem, and installation scripts. |
| [run/AGENTS.md](run/AGENTS.md) | Runnable image Dockerfile, compose example, entrypoints, and install scripts. |
| [sandbox/AGENTS.md](sandbox/AGENTS.md) | Sandbox image with global Python, IPython, Node.js and npm. |
