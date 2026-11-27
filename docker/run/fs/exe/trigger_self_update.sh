#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

cd /a0
exec /usr/local/bin/python "$SCRIPT_DIR/self_update_manager.py" trigger-update "$@"
