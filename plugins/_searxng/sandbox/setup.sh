#!/bin/sh
set -eu
mkdir -p /var/lib/a0-worker
sh /plugin/sandbox/install.sh > /var/lib/a0-worker/install.log 2>&1 || {
    tail -c 6000 /var/lib/a0-worker/install.log >&2
    exit 1
}
printf '%s\n' "$1" > /var/lib/a0-worker/installed.tmp
mv /var/lib/a0-worker/installed.tmp /var/lib/a0-worker/installed
