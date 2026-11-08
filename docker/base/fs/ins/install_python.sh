#!/bin/bash
set -e

echo "====================PYTHON START===================="

apt-get update
apt-get -y upgrade
rm -rf /var/lib/apt/lists/*

# Newer pipx requires filelock/packaging versions incompatible with LiteLLM/LangChain.
python -m pip install --no-cache-dir --no-compile --upgrade \
    pip ipython pipx==1.16.7 uv

# clean up pip cache
python -m pip cache purge

echo "====================PYTHON END===================="
