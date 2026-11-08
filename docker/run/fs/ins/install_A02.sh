#!/bin/bash
set -e

# cachebuster script, this helps speed up docker builds

# remove repo (if not local branch)
if [ "$1" != "local" ]; then
    rm -rf /git/agent-zero
fi

# Refresh the branch and reuse installed packages. Runtime assets are
# deliberately installed only on this final pass.
bash /ins/install_A0.sh "$@"
(cd /git/agent-zero && /usr/local/bin/python -m helpers.local_embeddings)
/usr/local/bin/python /git/agent-zero/preload.py --dockerized=true
