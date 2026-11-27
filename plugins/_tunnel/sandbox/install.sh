#!/bin/sh
set -eu
provider="${1:-cloudflared}"
mkdir -p /opt/a0-tunnel /var/lib/a0-tunnel
cp -a /plugin/sandbox/. /opt/a0-tunnel/
case "$provider" in
  cloudflared)
    python /opt/a0-tunnel/install_cloudflare.py
    ;;
  microsoft|serveo|tailscale)
    python -m pip install --disable-pip-version-check --no-cache-dir -r /opt/a0-tunnel/requirements.txt -c /opt/a0-tunnel/constraints.txt
    if [ "$provider" = serveo ] && ! command -v ssh >/dev/null 2>&1; then
      apt-get update
      apt-get install -y --no-install-recommends openssh-client
      rm -rf /var/lib/apt/lists/*
    fi
    ;;
  *) echo 'Unsupported tunnel provider' >&2; exit 2 ;;
esac
