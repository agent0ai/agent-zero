#!/bin/bash
set -eu

apt-get update
apt-get upgrade -y
apt-get install -y --no-install-recommends \
    tzdata sudo curl git cron 7zip libstdc++6 libatomic1 openssh-server supervisor \
    ca-certificates util-linux procps iproute2 gpg libgpgme11t64 libsqlite3-0 \
    libtalloc2 libseccomp2 acl
ln -sf /usr/share/zoneinfo/UTC /etc/localtime
echo UTC > /etc/timezone
dpkg-reconfigure -f noninteractive tzdata
apt-get clean
rm -rf /var/lib/apt/lists/*

# Node and bundled npm come from the official Node image.
node --version
npm --version
