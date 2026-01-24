---
description: Start Stripe webhook listener and forward events to local development server
argument-hint: "[--port <port>] [--events <event1,event2>] [--forward-to <url>]"
model: claude-3-5-haiku-20241022
allowed-tools:
  - Bash
  - Read
  - Write
---

# Stripe Webhook Listener Command

## Overview

Starts Stripe CLI webhook listener to forward Stripe events to your local development server. Essential for testing webhooks during development.

## What This Command Does

- ✅ Starts Stripe CLI listener in background
- ✅ Forwards webhook events to local server
- ✅ Optionally filters specific events
- ✅ Logs all events for debugging
- ✅ Provides webhook signing secret for verification
- ✅ Auto-restarts on connection loss

## Usage

```bash
# Listen and forward to default (localhost:3000/webhook)
/stripe:listen

# Forward to specific port
/stripe:listen --port 4000

# Forward to custom endpoint
/stripe:listen --forward-to http://localhost:3000/api/stripe/webhook

# Listen for specific events only
/stripe:listen --events payment_intent.succeeded,customer.subscription.created

# Listen with verbose logging
/stripe:listen --verbose
```

## Implementation

```bash
#!/bin/bash

# Configuration
PORT=${1:-3000}
FORWARD_URL=${2:-"http://localhost:${PORT}/webhook"}
EVENTS=${3:-""}
LOG_FILE="$HOME/.stripe/webhook-listener.log"

# Ensure log directory exists
mkdir -p "$HOME/.stripe"

echo "🎧 Starting Stripe webhook listener..."
echo "📍 Forwarding to: $FORWARD_URL"

# Build stripe listen command
STRIPE_CMD="stripe listen --forward-to $FORWARD_URL"

# Add event filtering if specified
if [ -n "$EVENTS" ]; then
    STRIPE_CMD="$STRIPE_CMD --events $EVENTS"
    echo "🔍 Filtering events: $EVENTS"
fi

# Start listener in background
echo "Starting listener (logs: $LOG_FILE)..."
$STRIPE_CMD > "$LOG_FILE" 2>&1 &
LISTENER_PID=$!

# Save PID for later stopping
echo $LISTENER_PID > "$HOME/.stripe/listener.pid"

# Wait for webhook signing secret
sleep 2

# Extract webhook signing secret from logs
WEBHOOK_SECRET=$(grep "whsec_" "$LOG_FILE" | head -1 | grep -oP 'whsec_[a-zA-Z0-9]+')

echo ""
echo "✅ Stripe webhook listener started"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Webhook Signing Secret:"
echo "   $WEBHOOK_SECRET"
echo ""
echo "   Add to your .env file:"
echo "   STRIPE_WEBHOOK_SECRET=$WEBHOOK_SECRET"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔄 Forwarding events to: $FORWARD_URL"
echo "📊 View logs: tail -f $LOG_FILE"
echo "🛑 Stop listener: /stripe:stop-listener"
echo ""
echo "Listener PID: $LISTENER_PID"
```

## Example Output

```
🎧 Starting Stripe webhook listener...
📍 Forwarding to: http://localhost:3000/webhook
Starting listener (logs: /home/user/.stripe/webhook-listener.log)...

✅ Stripe webhook listener started
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Webhook Signing Secret:
   whsec_1234567890abcdefghijklmnopqrstuvwxyz

   Add to your .env file:
   STRIPE_WEBHOOK_SECRET=whsec_1234567890abcdefghijklmnopqrstuvwxyz

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔄 Forwarding events to: http://localhost:3000/webhook
📊 View logs: tail -f /home/user/.stripe/webhook-listener.log
🛑 Stop listener: /stripe:stop-listener

Listener PID: 12345
```

## Event Filtering Examples

```bash
# Payment events only
/stripe:listen --events payment_intent.succeeded,payment_intent.failed

# Subscription events
/stripe:listen --events customer.subscription.created,customer.subscription.updated,customer.subscription.deleted

# Checkout events
/stripe:listen --events checkout.session.completed,checkout.session.expired

# Customer events
/stripe:listen --events customer.created,customer.updated,customer.deleted
```

## Common Event Types

**Payment Events**:

- `payment_intent.succeeded`
- `payment_intent.failed`
- `payment_intent.canceled`
- `charge.succeeded`
- `charge.failed`

**Subscription Events**:

- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `customer.subscription.trial_will_end`

**Checkout Events**:

- `checkout.session.completed`
- `checkout.session.expired`
- `checkout.session.async_payment_succeeded`
- `checkout.session.async_payment_failed`

**Customer Events**:

- `customer.created`
- `customer.updated`
- `customer.deleted`

**Invoice Events**:

- `invoice.created`
- `invoice.payment_succeeded`
- `invoice.payment_failed`

## Troubleshooting

### Listener Not Starting

```bash
# Check if Stripe CLI is installed
stripe --version

# If not installed:
# macOS
brew install stripe/stripe-cli/stripe

# Linux
# Download from https://github.com/stripe/stripe-cli/releases
```

### Events Not Being Received

```bash
# Check listener is running
ps aux | grep "stripe listen"

# View real-time logs
tail -f ~/.stripe/webhook-listener.log

# Test with Stripe dashboard (send test event)
```

### Wrong Webhook Secret

```bash
# Stop listener
/stripe:stop-listener

# Restart listener (generates new secret)
/stripe:listen

# Update your .env with new secret
```

## Related Commands

- `/stripe:stop-listener` - Stop the webhook listener
- `/stripe:trigger` - Trigger test webhook events
- `/stripe:test-payment` - Create test payment
- `/stripe:logs` - View Stripe API logs

## Notes

**Development Only**: This is for local development. Production uses Stripe dashboard webhooks.

**Signing Secret**: Changes each time listener restarts. Update .env accordingly.

**Background Process**: Listener runs in background. Remember to stop it when done.

---

*Essential for testing Stripe webhooks locally during development*
