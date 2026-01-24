---
description: Trigger specific Stripe webhook events for testing without creating real objects
argument-hint: "<event-type> [--override <field=value>]"
model: claude-3-5-haiku-20241022
allowed-tools:
  - Bash
---

# Stripe Trigger Webhook Command

## Overview

Triggers specific Stripe webhook events instantly for testing. Perfect for testing webhook handlers without creating real Stripe objects.

## What This Command Does

- ✅ Triggers any Stripe webhook event instantly
- ✅ Sends event to local webhook endpoint
- ✅ No need to create real Stripe objects
- ✅ Supports custom data overrides
- ✅ Lists available events

## Usage

```bash
# Trigger payment success
/stripe:trigger payment_intent.succeeded

# Trigger subscription created
/stripe:trigger customer.subscription.created

# Trigger checkout completed
/stripe:trigger checkout.session.completed

# Trigger with custom amount
/stripe:trigger payment_intent.succeeded --override amount=5000

# List all available events
/stripe:trigger --list
```

## Implementation

```bash
stripe trigger "$@"
```

## Common Events to Trigger

### Payment Events

```bash
# Successful payment
/stripe:trigger payment_intent.succeeded

# Failed payment
/stripe:trigger payment_intent.payment_failed

# Charge succeeded
/stripe:trigger charge.succeeded

# Charge failed
/stripe:trigger charge.failed

# Charge refunded
/stripe:trigger charge.refunded
```

### Subscription Events

```bash
# Subscription created
/stripe:trigger customer.subscription.created

# Subscription updated
/stripe:trigger customer.subscription.updated

# Subscription deleted/canceled
/stripe:trigger customer.subscription.deleted

# Trial ending soon
/stripe:trigger customer.subscription.trial_will_end

# Payment failed on subscription
/stripe:trigger invoice.payment_failed
```

### Checkout Events

```bash
# Checkout completed
/stripe:trigger checkout.session.completed

# Checkout expired
/stripe:trigger checkout.session.expired

# Async payment succeeded
/stripe:trigger checkout.session.async_payment_succeeded

# Async payment failed
/stripe:trigger checkout.session.async_payment_failed
```

### Customer Events

```bash
# Customer created
/stripe:trigger customer.created

# Customer updated
/stripe:trigger customer.updated

# Customer deleted
/stripe:trigger customer.deleted
```

### Invoice Events

```bash
# Invoice created
/stripe:trigger invoice.created

# Invoice finalized
/stripe:trigger invoice.finalized

# Invoice paid
/stripe:trigger invoice.paid

# Invoice payment succeeded
/stripe:trigger invoice.payment_succeeded

# Invoice payment failed
/stripe:trigger invoice.payment_failed
```

## With Data Overrides

```bash
# Custom payment amount
/stripe:trigger payment_intent.succeeded --override amount=10000

# Custom currency
/stripe:trigger payment_intent.succeeded --override currency=eur

# Custom customer email
/stripe:trigger customer.created --override email=test@example.com

# Multiple overrides
/stripe:trigger checkout.session.completed \
  --override amount_total=5000 \
  --override customer_email=test@example.com
```

## List All Available Events

```bash
/stripe:trigger --list
```

**Output**:

```
Available Stripe webhook events:

Payment Intents:
  • payment_intent.amount_capturable_updated
  • payment_intent.canceled
  • payment_intent.created
  • payment_intent.partially_funded
  • payment_intent.payment_failed
  • payment_intent.processing
  • payment_intent.requires_action
  • payment_intent.succeeded

Charges:
  • charge.captured
  • charge.expired
  • charge.failed
  • charge.pending
  • charge.refunded
  • charge.succeeded
  • charge.updated

Customers:
  • customer.created
  • customer.deleted
  • customer.updated

Subscriptions:
  • customer.subscription.created
  • customer.subscription.deleted
  • customer.subscription.paused
  • customer.subscription.pending_update_applied
  • customer.subscription.pending_update_expired
  • customer.subscription.resumed
  • customer.subscription.trial_will_end
  • customer.subscription.updated

Invoices:
  • invoice.created
  • invoice.deleted
  • invoice.finalization_failed
  • invoice.finalized
  • invoice.marked_uncollectible
  • invoice.paid
  • invoice.payment_action_required
  • invoice.payment_failed
  • invoice.payment_succeeded
  • invoice.sent
  • invoice.upcoming
  • invoice.updated
  • invoice.voided

Checkout:
  • checkout.session.async_payment_failed
  • checkout.session.async_payment_succeeded
  • checkout.session.completed
  • checkout.session.expired

... and many more

Use: stripe trigger <event> to trigger any event
```

## Testing Workflow

```bash
# 1. Start webhook listener
/stripe:listen

# 2. In another terminal, trigger events
/stripe:trigger payment_intent.succeeded

# 3. Verify webhook received
# Check your local server logs

# 4. Test different scenarios
/stripe:trigger payment_intent.payment_failed
/stripe:trigger customer.subscription.deleted
```

## Example: Testing Subscription Flow

```bash
# 1. Customer subscribes
/stripe:trigger customer.subscription.created

# 2. First payment succeeds
/stripe:trigger invoice.payment_succeeded

# 3. Trial ending warning (7 days before)
/stripe:trigger customer.subscription.trial_will_end

# 4. Subscription updated (plan changed)
/stripe:trigger customer.subscription.updated

# 5. Payment failed (card declined)
/stripe:trigger invoice.payment_failed

# 6. Subscription canceled
/stripe:trigger customer.subscription.deleted
```

## Example Output

```bash
$ /stripe:trigger payment_intent.succeeded

Triggering event: payment_intent.succeeded

✓ Event triggered successfully
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Event ID: evt_1234567890abcdef
Type: payment_intent.succeeded
API Version: 2023-10-16

Sent to webhook endpoint: http://localhost:3000/webhook
Response: 200 OK

View event in Dashboard:
https://dashboard.stripe.com/test/events/evt_1234567890abcdef

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Advantages Over Real Objects

**Speed**: Instant event triggering (vs creating real payments)

**Control**: Trigger exact events you want to test

**Clean**: No test data pollution in Stripe Dashboard

**Comprehensive**: Test edge cases (payment failures, etc.)

**Repeatable**: Trigger same event multiple times easily

## Related Commands

- `/stripe:listen` - Start webhook listener (required first)
- `/stripe:test-payment` - Create real test payment
- `/stripe:logs` - View Stripe API request logs

## Notes

**Listener Required**: Must have `/stripe:listen` running first

**Test Mode**: Only works in Stripe test mode

**Event Data**: Uses Stripe's sample event data (can override specific fields)

---

*Fastest way to test webhook handlers during development*
