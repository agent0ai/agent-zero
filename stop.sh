#!/bin/bash

# Stop script for agent-zero application

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.app.pid"

# Function to find process by name
find_process() {
    # Look for the run_ui.py process
    ps aux | grep "[p]ython.*run_ui.py" | awk '{print $2}'
}

# Function to stop process gracefully
stop_process() {
    local pid=$1
    local force=${2:-false}
    
    if [ -z "$pid" ]; then
        return 1
    fi
    
    if ! ps -p "$pid" > /dev/null 2>&1; then
        return 1
    fi
    
    if [ "$force" = true ]; then
        echo "Force killing process $pid..."
        kill -9 "$pid" 2>/dev/null
    else
        echo "Stopping process $pid gracefully..."
        kill "$pid" 2>/dev/null
        
        # Wait for the process to stop (max 10 seconds)
        for i in {1..10}; do
            if ! ps -p "$pid" > /dev/null 2>&1; then
                return 0
            fi
            sleep 1
        done
        
        # If still running, force kill
        echo "Process did not stop gracefully, force killing..."
        kill -9 "$pid" 2>/dev/null
    fi
    
    # Wait a moment to ensure it's stopped
    sleep 1
    
    if ps -p "$pid" > /dev/null 2>&1; then
        return 1
    fi
    
    return 0
}

# Check if PID file exists
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Found application process (PID: $PID)"
        if stop_process "$PID"; then
            echo "Application stopped successfully."
            rm -f "$PID_FILE"
            exit 0
        else
            echo "Failed to stop process $PID"
            rm -f "$PID_FILE"
            exit 1
        fi
    else
        echo "PID file exists but process is not running. Cleaning up..."
        rm -f "$PID_FILE"
    fi
fi

# Try to find the process by name
FOUND_PIDS=$(find_process)

if [ -n "$FOUND_PIDS" ]; then
    echo "Found running application processes: $FOUND_PIDS"
    for pid in $FOUND_PIDS; do
        if stop_process "$pid"; then
            echo "Stopped process $pid"
        else
            echo "Failed to stop process $pid"
        fi
    done
    
    # Clean up PID file if it exists
    rm -f "$PID_FILE"
    echo "Application stopped."
    exit 0
else
    echo "No running application found."
    # Clean up stale PID file if it exists
    rm -f "$PID_FILE"
    exit 0
fi
