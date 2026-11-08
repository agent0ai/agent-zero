#!/bin/sh
set -eu
. /worker/python.sh
# Baileys' locked dependencies include a Git source package.
apt-get update
apt-get install -y --no-install-recommends git ca-certificates
rm -rf /var/lib/apt/lists/*
