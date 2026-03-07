#!/bin/bash
set -e

echo "====================SEARXNG2 START===================="


# clone SearXNG repo with retries for transient network failures
repo_url="https://github.com/searxng/searxng"
repo_dir="/usr/local/searxng/searxng-src"
for attempt in 1 2 3 4 5; do
    if git clone "$repo_url" "$repo_dir"; then
        break
    fi
    if [ "$attempt" -eq 5 ]; then
        echo "Failed to clone SearXNG after $attempt attempts"
        exit 1
    fi
    echo "Clone failed (attempt $attempt/5), retrying in 5s..."
    sleep 5
done

echo "====================SEARXNG2 VENV===================="

# create virtualenv:
python3.13 -m venv "/usr/local/searxng/searx-pyenv"

# make it default
echo ". /usr/local/searxng/searx-pyenv/bin/activate" \
                   >>  "/usr/local/searxng/.profile"

# activate venv
source "/usr/local/searxng/searx-pyenv/bin/activate"

echo "====================SEARXNG2 INST===================="

# update pip's boilerplate and preinstall runtime import deps needed by setup metadata
pip install --no-cache-dir -U pip setuptools wheel pyyaml lxml msgspec

# jump to SearXNG's working tree and install SearXNG into virtualenv
cd "/usr/local/searxng/searxng-src"
pip install --no-cache-dir --use-pep517 --no-build-isolation -e .

# cleanup cache
pip cache purge

echo "====================SEARXNG2 END===================="
