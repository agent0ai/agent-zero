#!/bin/bash

. "/ins/setup_venv.sh" "$@"
. "/ins/copy_A0.sh" "$@"

echo "Starting A0 bootstrap manager..."
exec python /exe/self_update_manager.py docker-run-ui
