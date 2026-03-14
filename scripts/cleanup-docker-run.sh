#!/bin/bash
# Cleanup script for docker/run directory with permission issues
# This fixes the dev container build error: "permission denied" on docker/run files

set -e

DOCKER_RUN_PATH="$(cd "$(dirname "$0")/../docker/run" 2>/dev/null && pwd)" || DOCKER_RUN_PATH="$(dirname "$0")/../docker/run"

if [ ! -d "$DOCKER_RUN_PATH" ]; then
    echo "✓ docker/run directory does not exist. Nothing to clean."
    exit 0
fi

echo "Cleaning up docker/run directory..."
echo "  Path: $DOCKER_RUN_PATH"

# Check if we have any root-owned files
if find "$DOCKER_RUN_PATH" -type f -user root -o -type d -user root 2>/dev/null | grep -q .; then
    echo "⚠ Found root-owned files in docker/run. Attempting to fix permissions..."

    # Try to remove the directory using various methods
    if rm -rf "$DOCKER_RUN_PATH" 2>/dev/null; then
        echo "✓ Successfully removed docker/run"
    else
        echo "⚠ Could not remove docker/run (may require elevated permissions)"
        echo ""
        echo "Try one of these solutions:"
        echo "  1. Run: sudo rm -rf $DOCKER_RUN_PATH"
        echo "  2. Or create an empty placeholder:"
        echo "     mkdir -p $DOCKER_RUN_PATH && touch $DOCKER_RUN_PATH/.gitkeep"
        exit 1
    fi
else
    # No root-owned files, safe to remove
    if rm -rf "$DOCKER_RUN_PATH"; then
        echo "✓ Successfully removed docker/run"
    else
        echo "✗ Failed to remove docker/run"
        exit 1
    fi
fi

echo ""
echo "Dev container should now build successfully!"
