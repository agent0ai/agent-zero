#!/bin/sh
set -eu
mkdir -p /var/lib/a0-tunnel
printf '%s' "$1" > /var/lib/a0-tunnel/provider
: > /var/lib/a0-tunnel/tunnel.log
rm -f /var/lib/a0-tunnel/status.json
sh /plugin/sandbox/install.sh "$1" > /var/lib/a0-tunnel/install.log 2>&1
exec sh /opt/a0-tunnel/start.sh "$@"
