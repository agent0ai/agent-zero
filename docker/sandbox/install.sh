#!/bin/sh
set -eu

# /node is the official Node image's read-only /usr/local directory.
apt-get update
apt-get install -y --no-install-recommends libstdc++6 libatomic1
rm -rf /var/lib/apt/lists/*
cp /node/bin/node /usr/local/bin/node
cp -a /node/lib/node_modules /usr/local/lib/
ln -sf ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm
ln -sf ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx
PIP_ROOT_USER_ACTION=ignore python -m pip install --no-cache-dir 'ipython==9.18.1'
mkdir -p /workspace

python -c 'import sys; assert sys.prefix == sys.base_prefix'
python -m pip check
ipython --version
node --version
npm --version
npx --version
