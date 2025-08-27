#!/bin/bash
set -e

echo "====================BROWSER CONTROL ENVIRONMENT START===================="

# Install Xvfb and related display dependencies
apt-get update
apt-get install -y --no-install-recommends \
    xvfb \
    x11-xserver-utils \
    x11-utils \
    x11vnc \
    websockify \
    fluxbox \
    xterm \
    curl \
    unzip \
    git \
    gnupg \
    python3-numpy \
    python3-setuptools

# Install Google Chrome (stable version with remote debugging support)
echo "Installing Google Chrome..."
ARCH=$(dpkg --print-architecture)
if [ "$ARCH" = "arm64" ]; then
    echo "Installing Chromium for ARM64 architecture..."
    apt-get install -y --no-install-recommends chromium chromium-driver
    # Create symlink for chrome command
    ln -sf /usr/bin/chromium /usr/bin/google-chrome
else
    echo "Installing Google Chrome for AMD64 architecture..."
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /etc/apt/trusted.gpg.d/google-chrome.gpg
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
    apt-get update
    apt-get install -y --no-install-recommends google-chrome-stable
fi

# Install noVNC for web-based VNC access
echo "Installing noVNC..."
cd /opt
git clone https://github.com/novnc/noVNC.git
cd noVNC
git checkout v1.4.0
cd /opt
git clone https://github.com/novnc/websockify.git
cd websockify
python3 setup.py install

# Create chrome wrapper script for better process management
cat > /usr/local/bin/chrome-wrapper.sh << 'EOF'
#!/bin/bash
# Chrome wrapper script for browser control PoC
if [ -x "/usr/bin/google-chrome" ]; then
    exec /usr/bin/google-chrome --no-sandbox --disable-dev-shm-usage "$@"
elif [ -x "/usr/bin/chromium" ]; then
    exec /usr/bin/chromium --no-sandbox --disable-dev-shm-usage "$@"
else
    echo "No Chrome or Chromium browser found!"
    exit 1
fi
EOF
chmod +x /usr/local/bin/chrome-wrapper.sh

# Set up X11 authentication for container environment
touch /root/.Xauthority

# Create browser control startup script
cat > /usr/local/bin/start-browser-control.sh << 'EOF'
#!/bin/bash
# Startup script for browser control environment

DISPLAY=:99
CHROME_PORT=9222
VNC_PORT=5900
WEBSOCKET_PORT=6080
USER_DATA_DIR=/tmp/chrome_profile

echo "Starting Xvfb on display $DISPLAY..."
Xvfb $DISPLAY -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
XVFB_PID=$!

# Wait for Xvfb to initialize
sleep 3

echo "Starting window manager..."
DISPLAY=$DISPLAY fluxbox &
FLUXBOX_PID=$!

echo "Starting Chrome with remote debugging on port $CHROME_PORT..."
mkdir -p $USER_DATA_DIR
DISPLAY=$DISPLAY /usr/local/bin/chrome-wrapper.sh \
    --remote-debugging-port=$CHROME_PORT \
    --remote-debugging-address=0.0.0.0 \
    --user-data-dir=$USER_DATA_DIR \
    --no-first-run \
    --no-default-browser-check \
    --no-sandbox \
    --disable-dev-shm-usage \
    --disable-extensions \
    --disable-web-security \
    --allow-running-insecure-content &
CHROME_PID=$!

echo "Starting VNC server on port $VNC_PORT..."
x11vnc -display $DISPLAY -rfbport $VNC_PORT -forever -shared -bg -noxrecord -noxfixes -noxdamage

echo "Starting WebSocket proxy on port $WEBSOCKET_PORT..."
websockify --web=/opt/noVNC $WEBSOCKET_PORT localhost:$VNC_PORT &
WEBSOCKIFY_PID=$!

echo "Browser control environment started:"
echo "  Xvfb PID: $XVFB_PID"
echo "  Chrome PID: $CHROME_PID" 
echo "  Fluxbox PID: $FLUXBOX_PID"
echo "  WebSocket Proxy PID: $WEBSOCKIFY_PID"
echo "  Chrome Debug: http://localhost:$CHROME_PORT"
echo "  VNC Port: $VNC_PORT"
echo "  WebSocket Port: $WEBSOCKET_PORT"
echo "  noVNC URL: http://localhost:$WEBSOCKET_PORT/vnc.html"

# Keep script running
wait
EOF
chmod +x /usr/local/bin/start-browser-control.sh

# Create browser control stop script
cat > /usr/local/bin/stop-browser-control.sh << 'EOF'
#!/bin/bash
# Stop script for browser control environment

echo "Stopping browser control environment..."

# Kill WebSocket proxy
pkill -f "websockify" || true

# Kill Chrome processes
pkill -f "chrome.*remote-debugging-port" || true

# Kill VNC server
pkill -f "x11vnc" || true

# Kill window manager
pkill -f "fluxbox" || true

# Kill Xvfb
pkill -f "Xvfb :99" || true

echo "Browser control environment stopped."
EOF
chmod +x /usr/local/bin/stop-browser-control.sh

# Create systemd service for browser control (if systemd is available)
if command -v systemctl >/dev/null 2>&1 && systemctl is-system-running >/dev/null 2>&1; then
    cat > /etc/systemd/system/browser-control.service << 'EOF'
[Unit]
Description=Browser Control Environment
After=network.target

[Service]
Type=forking
ExecStart=/usr/local/bin/start-browser-control.sh
ExecStop=/usr/local/bin/stop-browser-control.sh
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload || echo "Systemd not available, skipping service creation"
else
    echo "Systemd not available in container environment, skipping service creation"
fi

# Set up permissions for browser control
chmod 755 /tmp
mkdir -p /tmp/chrome_profile
chmod 755 /tmp/chrome_profile

# Clean up apt cache
apt-get clean
rm -rf /var/lib/apt/lists/*

echo "====================BROWSER CONTROL ENVIRONMENT END===================="