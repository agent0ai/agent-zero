#!/bin/sh
set -eu
cd /opt/a0-tunnel
mkdir -p /var/lib/a0-tunnel
if [ "$1" = cloudflared ]; then
  exec ./cloudflared tunnel --no-autoupdate --protocol http2 --url "http://127.0.0.1:$2" --metrics 127.0.0.1:0 > /var/lib/a0-tunnel/tunnel.log 2>&1
fi
exec python /opt/a0-tunnel/worker.py "$1" "$2" > /var/lib/a0-tunnel/tunnel.log 2>&1
