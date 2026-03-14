#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

IMAGE_TAG="${IMAGE_TAG:-agent-jumbo-local:latest}"
CACHE_DIR="${CACHE_DIR:-.buildx-cache}"
BUILDER_NAME="${BUILDER_NAME:-agent-jumbo-builder}"
if [[ -n "${BASE_IMAGE:-}" ]]; then
  BASE_IMAGE="${BASE_IMAGE}"
elif docker image inspect agent-zero-base:local >/dev/null 2>&1; then
  BASE_IMAGE="agent-zero-base:local"
else
  BASE_IMAGE="agent0ai/agent-zero-base:latest"
fi
USE_CACHE_BUSTER="${USE_CACHE_BUSTER:-0}"

if ! docker buildx inspect "$BUILDER_NAME" >/dev/null 2>&1; then
  docker buildx create --name "$BUILDER_NAME" --use >/dev/null
else
  docker buildx use "$BUILDER_NAME" >/dev/null
fi

CACHE_BUSTER_ARG=()
if [[ "$USE_CACHE_BUSTER" == "1" ]]; then
  CACHE_BUSTER_ARG=(--build-arg "CACHE_BUSTER=$(date +%Y-%m-%d:%H:%M:%S)")
fi

docker buildx build \
  --load \
  -f DockerfileLocal \
  -t "$IMAGE_TAG" \
  --build-arg "BASE_IMAGE=$BASE_IMAGE" \
  "${CACHE_BUSTER_ARG[@]}" \
  --cache-from=type=local,src="$CACHE_DIR" \
  --cache-to=type=local,dest="$CACHE_DIR",mode=max \
  .

echo "Built $IMAGE_TAG with local cache at $CACHE_DIR"
