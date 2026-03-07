#!/bin/bash
set -e

# Exit immediately if a command exits with a non-zero status.
# set -e

# branch from parameter
if [ -z "$1" ]; then
    echo "Error: Branch parameter is empty. Please provide a valid branch name."
    exit 1
fi
BRANCH="$1"

if [ "$BRANCH" = "local" ]; then
    # For local branch, use the files
    echo "Using local dev files in /git/agent-zero"
    # List all files recursively in the target directory
    # echo "All files in /git/agent-zero (recursive):"
    # find "/git/agent-zero" -type f | sort
else
    # For other branches, clone from GitHub
    echo "Cloning repository from branch $BRANCH..."
    git clone -b "$BRANCH" "https://github.com/agent0ai/agent-zero" "/git/agent-zero" || {
        echo "CRITICAL ERROR: Failed to clone repository. Branch: $BRANCH"
        exit 1
    }
fi

. "/ins/setup_venv.sh" "$@"

# moved to base image
# # Ensure the virtual environment and pip setup
# pip install --upgrade pip ipython requests
# # Install some packages in specific variants
# pip install torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining A0 python packages
if [ "${SKIP_A0_DEPS:-0}" = "1" ]; then
    echo "Skipping dependency installation (SKIP_A0_DEPS=1)"
else
    if [ -f /git/agent-zero/requirements.lock.txt ]; then
        echo "Using pinned lockfile requirements.lock.txt"
        uv pip install -r /git/agent-zero/requirements.lock.txt
    elif [ -d /git/agent-zero/docker/wheelhouse ] && [ "$(find /git/agent-zero/docker/wheelhouse -maxdepth 1 -name '*.whl' | wc -l)" -gt 0 ]; then
        echo "Installing from local wheelhouse"
        uv pip install --no-index --find-links /git/agent-zero/docker/wheelhouse -r /git/agent-zero/requirements.txt
    else
        uv pip install -r /git/agent-zero/requirements.txt
    fi

    # override for packages that have unnecessarily strict dependencies
    uv pip install -r /git/agent-zero/requirements2.txt
fi

# install playwright
bash /ins/install_playwright.sh "$@"

# Preload A0
python /git/agent-zero/preload.py --dockerized=true
