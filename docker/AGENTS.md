# Docker DOX

## Purpose

- Own Docker build contexts and runtime container definitions.
- Keep framework runtime, agent execution runtime, exposed ports, mounted paths, and image build assumptions explicit.

## Ownership

- `base/` owns the base image context.
- `run/` owns the runnable image context and compose file.
- Root `DockerfileLocal` is owned by the root contract but must stay compatible with this directory.

## Local Contracts

- Preserve the two-runtime model: the Python 3.12 framework runtime under `/opt/venv-a0` runs the WebUI, APIs, scheduler, framework imports, and plugin hooks; the Python 3.13 agent execution runtime under `/opt/venv` runs agent terminal tasks and user code.
- Verify backend imports and plugin hooks with `/opt/venv-a0`; packages installed into `/opt/venv` do not prove framework compatibility.
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
