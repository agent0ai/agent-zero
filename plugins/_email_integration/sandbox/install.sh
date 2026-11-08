#!/bin/sh
set -eu
. /worker/python.sh
uv pip install -c /worker/constraints.txt -r /plugin/sandbox/requirements.txt
