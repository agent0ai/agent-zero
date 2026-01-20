#!/bin/bash

# Startup script for agent-zero application

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
PID_FILE="$SCRIPT_DIR/.app.pid"
LOG_FILE="$SCRIPT_DIR/logs/app.log"
VENV_DIR="$SCRIPT_DIR/venv"
APP_SCRIPT="$SCRIPT_DIR/run_ui.py"

# Create logs directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Function to check if the application is already running
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            # PID file exists but process is not running, remove stale PID file
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Check if already running
if is_running; then
    PID=$(cat "$PID_FILE")
    echo "Application is already running (PID: $PID)"
    echo "To stop it, run: ./stop.sh"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Please create it first with: python3.12 -m venv venv"
    exit 1
fi

# Check if the application script exists
if [ ! -f "$APP_SCRIPT" ]; then
    echo "Error: Application script not found at $APP_SCRIPT"
    exit 1
fi

# Activate virtual environment and start the application
echo "Starting agent-zero application..."
echo "Logs will be written to: $LOG_FILE"

# Start the application in the background
source "$VENV_DIR/bin/activate"
nohup python "$APP_SCRIPT" > "$LOG_FILE" 2>&1 &
APP_PID=$!

# Save the PID
echo $APP_PID > "$PID_FILE"

# Wait a moment to check if the process started successfully
sleep 2

if ps -p "$APP_PID" > /dev/null 2>&1; then
    echo "Application started successfully!"
    echo "PID: $APP_PID"
    echo "Log file: $LOG_FILE"
    echo ""
    echo "To stop the application, run: ./stop.sh"
    echo "To view logs, run: tail -f $LOG_FILE"
else
    echo "Error: Application failed to start. Check the log file: $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
