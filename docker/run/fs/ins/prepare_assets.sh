#!/bin/bash
set -eu

cd /a0
/usr/local/bin/python -m helpers.local_embeddings
/usr/local/bin/python preload.py --dockerized=true

/usr/local/bin/python -m compileall -q --invalidation-mode checked-hash /a0
