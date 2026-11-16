#!/bin/sh
set -eu
WORKER_PYTHON=$(command -v python)
. /worker/python.sh
uv pip install -c /worker/constraints.txt -r /plugin/sandbox/requirements.txt
