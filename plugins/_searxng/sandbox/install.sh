#!/bin/sh
set -eu
export DEBIAN_FRONTEND=noninteractive
python /worker/progress.py python 'Preparing SearXNG in image Python'
apt-get update
apt-get install -y --no-install-recommends ca-certificates git
python -m pip install --no-cache-dir --disable-pip-version-check -c /worker/constraints.txt -r /plugin/sandbox/requirements.txt
python /worker/progress.py searxng 'Installing SearXNG (first use may take a little while)'
source_dir=$(mktemp -d)
trap 'rm -rf "$source_dir"' EXIT
cd "$source_dir"
git init -q
git remote add origin https://github.com/searxng/searxng.git
git fetch --depth 1 origin 2d500cb6b8e98b5f57fb446786e91f8de03be89f:refs/remotes/origin/master
git checkout -q -b master --track origin/master
python searx/version.py freeze
python -m pip install --no-cache-dir --disable-pip-version-check --no-build-isolation -c /worker/constraints.txt .
python -m pip check
rm -rf /var/lib/apt/lists/*
