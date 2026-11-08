#!/bin/bash

. "/ins/copy_A0.sh" "$@"

echo "Starting A0 bootstrap manager..."
cd /a0
exec depfix run /exe/self_update_manager.py docker-run-ui
