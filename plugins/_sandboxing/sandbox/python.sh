#!/bin/sh
set -eu
# Debian fontconfig otherwise tries to chown this directory to an unmapped group.
mkdir -p /usr/local/share/fonts
if [ ! -x /opt/runtime/bin/python ]; then
    python -m pip install --no-cache-dir uv
    # Existing parser/model pins support Python 3.12, independently of the OCI base.
    uv venv --python 3.12 /opt/runtime
fi
export PATH=/opt/runtime/bin:$PATH
export UV_PYTHON=/opt/runtime/bin/python
export PIP_NO_CACHE_DIR=1
export UV_NO_CACHE=1
