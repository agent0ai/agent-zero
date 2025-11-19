#!/bin/bash
echo "Setting up Agent Zero Desktop Shell on Host..."

# Ensure we are in the correct directory
cd "$(dirname "$0")" || exit 1

# Check for node
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed on your host. Please install it to run the desktop shell."
    exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

echo "Starting Electron Shell..."
echo "Connecting to http://localhost:80 (Make sure the Docker container is running with '-p 80:80')"

# Start electron
npm start
