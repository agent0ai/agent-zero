# Fast Docker Build Workflow

## One-time setup

1. Build reusable base image:

```bash
./docker/build-base-local.sh
```

1. (Optional) Generate a pinned lock file:

```bash
./docker/lock-deps.sh
```

1. (Optional) Build a local wheelhouse:

```bash
./docker/build-wheelhouse.sh
```

## Daily build

Use BuildKit/buildx with local cache export/import:

```bash
./docker/build-fast.sh
```

## Cache controls

- Normal builds keep cache warm.
- Force dependency reinstall only when needed:

```bash
USE_CACHE_BUSTER=1 ./docker/build-fast.sh
```

## Key optimizations implemented

1. Dependency manifests copied before app source.
2. Dependency install done in dedicated cached layer.
3. BuildKit cache mounts for apt/pip/uv.
4. Large directories excluded in `.dockerignore`.
5. Optional `requirements.lock.txt` path.
6. Reusable local base image support (`BASE_IMAGE` arg).
7. buildx local cache persistence (`.buildx-cache`).
8. Optional wheelhouse offline install path.
