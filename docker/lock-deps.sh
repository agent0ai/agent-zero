#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install uv first."
  exit 1
fi

uv pip compile requirements.txt --output-file requirements.lock.txt
echo "Updated requirements.lock.txt"
