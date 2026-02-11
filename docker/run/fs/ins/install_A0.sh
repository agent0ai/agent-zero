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
    echo "Using local dev files in /git/apollos-ai"
    # List all files recursively in the target directory
    # echo "All files in /git/apollos-ai (recursive):"
    # find "/git/apollos-ai" -type f | sort
else
    # For other branches, clone from GitHub
    echo "Cloning repository from branch $BRANCH..."
    git clone -b "$BRANCH" "https://github.com/jrmatherly/apollos-ai" "/git/apollos-ai" || {
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
# --override resolves the browser-use==0.5.11 -> openai==1.99.2 conflict,
# matching the [tool.uv] override-dependencies in pyproject.toml.
uv pip install -r /git/apollos-ai/requirements.txt \
    --overrides /git/apollos-ai/overrides.txt

# install playwright
bash /ins/install_playwright.sh "$@"

# Preload A0
python /git/apollos-ai/preload.py --dockerized=true
