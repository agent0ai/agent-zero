#!/bin/sh
set -eu
. /worker/python.sh
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
uv pip install -c /worker/constraints.txt -r /plugin/sandbox/requirements.txt
