---
description: Stop the running Stripe webhook listener
argument-hint: ""
model: claude-3-5-haiku-20241022
allowed-tools:
  - Bash
---

# Stop Stripe Listener Command

## Overview

Stops the Stripe CLI webhook listener that was started with `/stripe:listen`.

## Usage

```bash
/stripe:stop-listener
```

## Implementation

```bash
#!/bin/bash

PID_FILE="$HOME/.stripe/listener.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "❌ No running listener found"
    echo ""
    echo "PID file not found: $PID_FILE"
    echo ""
    echo "Listener may not be running, or was started manually."
    exit 1
fi

PID=$(cat "$PID_FILE")

if ! ps -p $PID > /dev/null 2>&1; then
    echo "⚠️  Listener process not found (PID: $PID)"
    echo ""
    echo "Removing stale PID file..."
    rm "$PID_FILE"
    exit 0
fi

echo "🛑 Stopping Stripe webhook listener..."
echo "   PID: $PID"
echo ""

kill $PID

# Wait for process to terminate
sleep 1

if ps -p $PID > /dev/null 2>&1; then
    echo "⚠️  Process didn't stop gracefully. Force killing..."
    kill -9 $PID
    sleep 1
fi

# Clean up PID file
rm "$PID_FILE"

echo "✅ Stripe webhook listener stopped"
echo ""
echo "📊 Listener logs preserved at: ~/.stripe/webhook-listener.log"
echo ""
echo "To start again: /stripe:listen"
```

## Example Output

```
🛑 Stopping Stripe webhook listener...
   PID: 12345

✅ Stripe webhook listener stopped

📊 Listener logs preserved at: ~/.stripe/webhook-listener.log

To start again: /stripe:listen
```

## Related Commands

- `/stripe:listen` - Start webhook listener
- `/stripe:logs` - View webhook listener logs

---

*Always stop the listener when done with development*
