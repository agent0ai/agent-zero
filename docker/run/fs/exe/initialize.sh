#!/bin/bash

echo "Running initialization script..."

# branch from parameter
if [ -z "$1" ]; then
    echo "Error: Branch parameter is empty. Please provide a valid branch name."
    exit 1
fi
BRANCH="$1"

# Copy all contents from persistent /per to root directory (/) without overwriting
cp -r --no-preserve=ownership,mode /per/* /

# allow execution of /root/.bashrc and /root/.profile
chmod 444 /root/.bashrc
chmod 444 /root/.profile

# update package list to save time later
apt-get update > /dev/null 2>&1 &

# ensure searxng runtime config is present before services start
if [ -f /etc/searxng/settings.yml ] && [ -f /etc/searxng/limiter.toml ]; then
    chmod 644 /etc/searxng/settings.yml /etc/searxng/limiter.toml || true
fi

# let supervisord handle the services
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
