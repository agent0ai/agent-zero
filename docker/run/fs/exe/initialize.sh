#!/bin/bash

echo "Running initialization script..."

# branch from parameter
if [ -z "$1" ]; then
    echo "Error: Branch parameter is empty. Please provide a valid branch name."
    exit 1
fi
BRANCH="$1"

raise_open_file_limit() {
    local requested="${A0_NOFILE_LIMIT:-65535}"
    local soft
    local hard
    local target

    if ! [[ "$requested" =~ ^[0-9]+$ ]] || [ "$requested" -lt 1 ]; then
        echo "Warning: invalid A0_NOFILE_LIMIT='$requested'; keeping open file limit at $(ulimit -S -n)." >&2
        return
    fi

    soft="$(ulimit -S -n)"
    hard="$(ulimit -H -n)"

    if [ "$soft" = "unlimited" ]; then
        echo "Open file limit is already unlimited."
        return
    fi

    target="$requested"
    if [ "$hard" != "unlimited" ] && [ "$target" -gt "$hard" ]; then
        target="$hard"
    fi

    if [ "$target" -gt "$soft" ]; then
        if ulimit -S -n "$target"; then
            echo "Raised open file soft limit from $soft to $(ulimit -S -n) (hard: $hard)."
        else
            echo "Warning: failed to raise open file soft limit from $soft to $target (hard: $hard)." >&2
        fi
    else
        echo "Open file soft limit is $soft (target: $requested, hard: $hard)."
    fi
}

raise_open_file_limit

# Copy all contents from persistent /per to root directory (/) without overwriting
cp -r --no-preserve=ownership,mode /per/* /

# Ensure upload storage exists before API and connector callers can reference it.
mkdir -p /a0/usr/uploads

# allow execution of /root/.bashrc and /root/.profile
chmod 444 /root/.bashrc
chmod 444 /root/.profile

# update package list to save time later
apt-get update > /dev/null 2>&1 &

# let supervisord handle the services
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
