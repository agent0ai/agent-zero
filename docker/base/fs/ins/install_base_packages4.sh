#!/bin/bash
set -e

echo "====================BASE PACKAGES4 START===================="

# sandboxing
apt-get update
apt-get install -y --no-install-recommends \
    ca-certificates util-linux procps iproute2 gpg libgpgme11t64 libsqlite3-0

rm -rf /var/lib/apt/lists/* # for docker layers size

echo "====================BASE PACKAGES4 END===================="
