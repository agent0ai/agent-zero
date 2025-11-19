#!/bin/bash
echo "Starting Electron desktop shell for Agent Zero..."

# Navigate to the Electron application directory
# Note: In the container, the code is mounted/copied to /a0
cd /a0/desktop/electron || { echo "ERROR: /a0/desktop/electron directory not found."; exit 1; }

# Install Node.js dependencies (including electron).
echo "Installing Node.js dependencies..."
npm install || { echo "ERROR: Failed to install Node.js dependencies."; exit 1; }

# Execute the Electron application.
echo "Launching Electron..."
# Fix permissions if needed (Docker volume issue)
# Try to locate the binary and chmod it
ELECTRON_BIN=$(find ./node_modules -name electron -type f -path "*/dist/*")
if [ -n "$ELECTRON_BIN" ]; then
    chmod +x "$ELECTRON_BIN"
fi
chmod -R +x ./node_modules/.bin/

# Explicitly use the found binary if possible, or fallback
if [ -n "$ELECTRON_BIN" ]; then
  echo "Launching found binary: $ELECTRON_BIN"
  exec "$ELECTRON_BIN" . \
      --no-sandbox \
      --disable-gpu \
      --enable-logging=stderr \
      --remote-debugging-port=9222 \
      || { echo "ERROR: Failed to launch Electron."; exit 1; }
else
  echo "Launching via node_modules/.bin/electron..."
  exec ./node_modules/.bin/electron . \
      --no-sandbox \
      --disable-gpu \
      --enable-logging=stderr \
      --remote-debugging-port=9222 \
      || { echo "ERROR: Failed to launch Electron."; exit 1; }
fi

echo "Electron process exited."
