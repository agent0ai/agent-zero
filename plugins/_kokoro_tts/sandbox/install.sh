#!/bin/sh
set -eu
. /worker/python.sh
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends espeak-ng libsndfile1
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
uv pip install -c /worker/constraints.txt -r /plugin/sandbox/requirements.txt
mkdir -p /app/plugins
ln -sfn /plugin /app/plugins/_kokoro_tts
rm -rf /var/lib/apt/lists/*
