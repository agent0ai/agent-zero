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

# --- Self-update persistence check ---
# If a previous self-update was applied and recorded in /a0/usr/, re-apply it
# after container recreation. /a0/usr/ survives recreation because operators
# mount it as a persistent volume. Without this check, self-update changes
# are silently lost when the container is recreated.
# See: https://github.com/MrTrenchTrucker/agent-zero-self-update-rollback
BREADCRUMB="/a0/usr/.a0_self_update_state"
if [ -f "$BREADCRUMB" ]; then
    TARGET_TAG=$(python3 -c "import json; print(json.load(open('$BREADCRUMB')).get('target_tag',''))" 2>/dev/null)
    TARGET_HASH=$(python3 -c "import json; print(json.load(open('$BREADCRUMB')).get('target_hash',''))" 2>/dev/null)
    if [ -n "$TARGET_TAG" ] && [ -n "$TARGET_HASH" ]; then
        CURRENT_HASH=$(git -C /git/agent-zero rev-parse HEAD 2>/dev/null)
        if [ "$CURRENT_HASH" != "$TARGET_HASH" ]; then
            echo "Self-update breadcrumb found: restoring $TARGET_TAG ($TARGET_HASH)..."
            cd /git/agent-zero
            git fetch --all --tags 2>/dev/null
            git checkout "$TARGET_TAG" 2>/dev/null || git checkout "$TARGET_HASH" 2>/dev/null
            if [ $? -eq 0 ]; then
                # Re-run copy_A0.sh to propagate updated code to /a0/
                if [ -f /ins/copy_A0.sh ]; then
                    bash /ins/copy_A0.sh 2>/dev/null
                fi
                echo "Self-update restored successfully to $TARGET_TAG"
            else
                echo "Warning: Failed to restore self-update to $TARGET_TAG. Starting with image defaults."
            fi
            cd /
        fi
    fi
fi

# update package list to save time later
apt-get update > /dev/null 2>&1 &

# let supervisord handle the services
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
