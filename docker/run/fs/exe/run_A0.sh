#!/bin/bash

. "/ins/copy_A0.sh" "$@"

echo "Starting A0 bootstrap manager..."
cd /a0
exec /usr/local/bin/python /exe/self_update_manager.py docker-run-ui
