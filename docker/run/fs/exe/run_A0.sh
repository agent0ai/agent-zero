#!/bin/bash

set -e

echo "Starting A0 bootstrap manager..."
cd /a0
exec /usr/local/bin/python /exe/self_update_manager.py docker-run-ui
