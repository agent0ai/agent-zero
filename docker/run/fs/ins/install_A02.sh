#!/bin/bash
set -e

# cachebuster script, this helps speed up docker builds

# remove repo (if not local branch)
if [ "$1" != "local" ]; then
    rm -rf /git/agent-zero
fi

# Refresh the branch and re-resolve once against the already populated Depfix
# store. Runtime assets are deliberately installed only on this final pass.
bash /ins/install_A0.sh "$@"
bash /ins/install_playwright.sh "$@"
depfix run /git/agent-zero/preload.py --dockerized=true
