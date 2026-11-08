#!/bin/bash
set -e

echo "====================BASE PACKAGES2 START===================="

apt-get update
apt-get install -y --no-install-recommends \
    openssh-server supervisor

rm -rf /var/lib/apt/lists/* # for docker layers size

echo "====================BASE PACKAGES2 END===================="
