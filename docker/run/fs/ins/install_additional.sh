#!/bin/bash
set -e

# install playwright - moved to install A0
# bash /ins/install_playwright.sh "$@"

# searxng - moved to base image
# bash /ins/install_searxng.sh "$@"

# Install diagram generation dependencies
echo "Installing diagram generation tools..."

# Install Mermaid CLI for diagram export
npm install -g @mermaid-js/mermaid-cli

echo "Diagram tools installation complete."