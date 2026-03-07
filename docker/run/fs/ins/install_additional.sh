#!/bin/bash
set -e

# install playwright - moved to install A0
# bash /ins/install_playwright.sh "$@"

# searxng - moved to base image
# bash /ins/install_searxng.sh "$@"

# Install diagram generation dependencies
echo "Installing diagram generation tools..."

# Install Mermaid CLI for diagram export
for attempt in 1 2 3; do
    if npm install -g @mermaid-js/mermaid-cli; then
        break
    fi
    if [ "$attempt" -eq 3 ]; then
        echo "Failed to install Mermaid CLI after $attempt attempts"
        exit 1
    fi
    echo "npm install failed (attempt $attempt/3), retrying in 3s..."
    sleep 3
done

echo "Diagram tools installation complete."
