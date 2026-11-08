#!/bin/sh
set -eu
. /worker/python.sh
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends libmagic1 libgl1 libglib2.0-0
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
uv pip install -c /worker/constraints.txt -r /plugin/sandbox/requirements.txt
mkdir -p /app/plugins
ln -sfn /plugin /app/plugins/_document_query
rm -rf /var/lib/apt/lists/*
