#!/bin/bash
set -eu

uv pip install --no-cache --python /usr/local/bin/python -r /a0/requirements.txt

/usr/local/bin/python -m compileall -q --invalidation-mode checked-hash /usr/local/lib/python3.12/site-packages
