#!/bin/bash
set -eu
apt-get update
mapfile -t packages < /a0/plugins/_desktop/build/runtime-packages.txt
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "${packages[@]}"
rm -rf /var/lib/apt/lists/*
