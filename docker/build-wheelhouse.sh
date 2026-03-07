#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

WHEEL_DIR="docker/wheelhouse"
mkdir -p "$WHEEL_DIR"

python3 -m pip wheel -r requirements.txt -w "$WHEEL_DIR"
python3 -m pip wheel -r requirements2.txt -w "$WHEEL_DIR"

echo "Wheelhouse populated at $WHEEL_DIR"
