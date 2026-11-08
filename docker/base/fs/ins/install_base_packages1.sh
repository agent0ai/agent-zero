#!/bin/bash
set -e

echo "====================BASE PACKAGES1 START===================="

apt-get update && apt-get upgrade -y

apt-get install -y --no-install-recommends \
    sudo curl git cron 7zip libstdc++6 libatomic1

rm -rf /var/lib/apt/lists/*

echo "====================BASE PACKAGES1 END===================="
