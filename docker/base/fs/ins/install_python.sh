#!/bin/bash
set -e

echo "====================PYTHON START===================="

apt-get update
apt-get -y upgrade
rm -rf /var/lib/apt/lists/*

# The official Python image provides the global interpreter and pip.
python -m pip install --no-cache-dir --upgrade \
    pip pipx ipython uv 'depfix==0.12.6'

# Install CPU-only variants before the application requirements are resolved.
# Match the application's NumPy and LiteLLM/Filelock bounds so its bulk solve
# can retain these CPU packages instead of dropping all installed preferences.
depfix pip install torch torchvision 'numpy<2' 'filelock>=3.20.3,<4' \
    --index-url https://download.pytorch.org/whl/cpu

# PyTorch wheels include development-only test suites, C++ headers, and helper binaries.
rm -rf \
    /usr/local/lib/python3.12/site-packages/torch/test \
    /usr/local/lib/python3.12/site-packages/torch/include \
    /usr/local/lib/python3.12/site-packages/torch/bin

# clean up pip cache
python -m pip cache purge

echo "====================PYTHON END===================="
