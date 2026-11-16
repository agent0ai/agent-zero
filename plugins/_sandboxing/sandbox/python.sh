#!/bin/sh
set -eu
# Debian fontconfig otherwise tries to chown this directory to an unmapped group.
mkdir -p /usr/local/share/fonts
if [ ! -x /opt/runtime/bin/python ]; then
    python -m pip install --no-cache-dir uv
    # Parser/model pins retain 3.12; compatible workers opt into their image Python.
    uv venv --python "${WORKER_PYTHON:-3.12}" /opt/runtime
fi
export PATH=/opt/runtime/bin:$PATH
export UV_PYTHON=/opt/runtime/bin/python
export PIP_NO_CACHE_DIR=1
export UV_NO_CACHE=1
