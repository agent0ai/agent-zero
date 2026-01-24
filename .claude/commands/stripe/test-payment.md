---
description: Create a test payment with Stripe test cards for local development testing
argument-hint: "[--amount <cents>] [--currency <code>] [--card <test-card-type>]"
model: claude-3-5-haiku-20241022
allowed-tools:
  - Bash
  - Read
  - Write
---

# Stripe Test Payment Command

## Overview

Creates test payments using Stripe CLI for local development. Supports various test card scenarios (success, decline, 3D Secure, etc.).

## What This Command Does

- ✅ Creates test payment with specified amount
- ✅ Uses Stripe test cards (success, decline, etc.)
- ✅ Triggers appropriate webhook events
- ✅ Tests payment flow end-to-end
- ✅ Supports 3D Secure / SCA testing
- ✅ Logs payment intent details

## Usage

```bash
# Create successful test payment ($10.00)
/stripe:test-payment

# Custom amount
/stripe:test-payment --amount 5000 --currency usd

# Test declined payment
/stripe:test-payment --card declined

# Test 3D Secure payment
/stripe:test-payment --card 3ds

# Test insufficient funds
/stripe:test-payment --card insufficient_funds
```

## Implementation

```bash
#!/bin/bash

# Configuration
AMOUNT=${1:-1000}  # Default $10.00
CURRENCY=${2:-usd}
CARD_TYPE=${3:-success}

# Stripe test card numbers
declare -A TEST_CARDS
TEST_CARDS[success]="4242424242424242"
TEST_CARDS[declined]="4000000000000002"
TEST_CARDS[insufficient_funds]="4000000000009995"
TEST_CARDS[lost_card]="4000000000009987"
TEST_CARDS[stolen_card]="4000000000009979"
TEST_CARDS[expired]="4000000000000069"
TEST_CARDS[incorrect_cvc]="4000000000000127"
TEST_CARDS[processing_error]="4000000000000119"
TEST_CARDS[3ds]="4000002500003155"
TEST_CARDS[3ds_required]="4000002760003184"

CARD_NUMBER="${TEST_CARDS[$CARD_TYPE]}"

if [ -z "$CARD_NUMBER" ]; then
    echo "❌ Unknown card type: $CARD_TYPE"
    echo ""
    echo "Available card types:"
    for card in "${!TEST_CARDS[@]}"; do
        echo "  • $card: ${TEST_CARDS[$card]}"
    done
    exit 1
fi

echo "💳 Creating test payment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Amount: $((AMOUNT / 100)).$((AMOUNT % 100)) ${CURRENCY^^}"
echo "Card Type: $CARD_TYPE"
echo "Card Number: $CARD_NUMBER"
echo ""

# Create Payment Intent
echo "Creating Payment Intent..."
PAYMENT_INTENT=$(stripe payment_intents create \
    --amount=$AMOUNT \
    --currency=$CURRENCY \
    --payment-method-types=card \
    --description="Test payment via /stripe:test-payment" \
    --format=json)

PAYMENT_INTENT_ID=$(echo "$PAYMENT_INTENT" | jq -r '.id')
CLIENT_SECRET=$(echo "$PAYMENT_INTENT" | jq -r '.client_secret')

echo "✓ Payment Intent created: $PAYMENT_INTENT_ID"
echo ""

# Create Payment Method
echo "Creating Payment Method..."
PAYMENT_METHOD=$(stripe payment_methods create \
    --type=card \
    --card[number]=$CARD_NUMBER \
    --card[exp_month]=12 \
    --card[exp_year]=2030 \
    --card[cvc]=123 \
    --format=json)

PAYMENT_METHOD_ID=$(echo "$PAYMENT_METHOD" | jq -r '.id')

echo "✓ Payment Method created: $PAYMENT_METHOD_ID"
echo ""

# Confirm Payment
echo "Confirming payment..."
CONFIRM_RESULT=$(stripe payment_intents confirm \
    $PAYMENT_INTENT_ID \
    --payment-method=$PAYMENT_METHOD_ID \
    --format=json)

STATUS=$(echo "$CONFIRM_RESULT" | jq -r '.status')

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$STATUS" == "succeeded" ]; then
    echo "✅ Payment Succeeded!"
    echo ""
    echo "Payment Intent: $PAYMENT_INTENT_ID"
    echo "Amount: $((AMOUNT / 100)).$((AMOUNT % 100)) ${CURRENCY^^}"
    echo "Status: $STATUS"
    echo ""
    echo "🎉 Webhook event triggered: payment_intent.succeeded"
elif [ "$STATUS" == "requires_action" ]; then
    echo "🔐 3D Secure Required"
    echo ""
    echo "Payment Intent: $PAYMENT_INTENT_ID"
    echo "Status: $STATUS"
    echo ""
    echo "Next step: Complete 3D Secure authentication"
    echo "Client Secret: $CLIENT_SECRET"
elif [ "$STATUS" == "requires_payment_method" ]; then
    echo "❌ Payment Failed"
    echo ""
    echo "Payment Intent: $PAYMENT_INTENT_ID"
    echo "Status: $STATUS"
    echo ""
    LAST_ERROR=$(echo "$CONFIRM_RESULT" | jq -r '.last_payment_error.message')
    echo "Error: $LAST_ERROR"
    echo ""
    echo "🔔 Webhook event triggered: payment_intent.payment_failed"
else
    echo "⚠️  Unexpected Status: $STATUS"
    echo ""
    echo "Payment Intent: $PAYMENT_INTENT_ID"
    echo ""
    echo "Full response:"
    echo "$CONFIRM_RESULT" | jq '.'
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 View in Stripe Dashboard:"
echo "   https://dashboard.stripe.com/test/payments/$PAYMENT_INTENT_ID"
echo ""
echo "🔍 View webhook events:"
echo "   tail -f ~/.stripe/webhook-listener.log"
```

## Test Card Scenarios

### Successful Payments

```bash
# Standard success
/stripe:test-payment --card success
# Card: 4242 4242 4242 4242

# Visa success
/stripe:test-payment --card success
# Card: 4242 4242 4242 4242

# Mastercard success
/stripe:test-payment --card success
# Card: 5555 5555 5555 4444
```

### Failed Payments

```bash
# Generic decline
/stripe:test-payment --card declined
# Card: 4000 0000 0000 0002

# Insufficient funds
/stripe:test-payment --card insufficient_funds
# Card: 4000 0000 0000 9995

# Lost card
/stripe:test-payment --card lost_card
# Card: 4000 0000 0000 9987

# Stolen card
/stripe:test-payment --card stolen_card
# Card: 4000 0000 0000 9979

# Expired card
/stripe:test-payment --card expired
# Card: 4000 0000 0000 0069

# Incorrect CVC
/stripe:test-payment --card incorrect_cvc
# Card: 4000 0000 0000 0127

# Processing error
/stripe:test-payment --card processing_error
# Card: 4000 0000 0000 0119
```

### 3D Secure / SCA Testing

```bash
# 3D Secure supported (optional)
/stripe:test-payment --card 3ds
# Card: 4000 0025 0000 3155

# 3D Secure required
/stripe:test-payment --card 3ds_required
# Card: 4000 0027 6000 3184
```

## Example Output (Success)

```
💳 Creating test payment...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Amount: 10.00 USD
Card Type: success
Card Number: 4242424242424242

Creating Payment Intent...
✓ Payment Intent created: pi_1234567890abcdef

Creating Payment Method...
✓ Payment Method created: pm_1234567890abcdef

Confirming payment...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Payment Succeeded!

Payment Intent: pi_1234567890abcdef
Amount: 10.00 USD
Status: succeeded

🎉 Webhook event triggered: payment_intent.succeeded

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 View in Stripe Dashboard:
   https://dashboard.stripe.com/test/payments/pi_1234567890abcdef

🔍 View webhook events:
   tail -f ~/.stripe/webhook-listener.log
```

## Example Output (Declined)

```
💳 Creating test payment...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Amount: 10.00 USD
Card Type: declined
Card Number: 4000000000000002

Creating Payment Intent...
✓ Payment Intent created: pi_1234567890abcdef

Creating Payment Method...
✓ Payment Method created: pm_1234567890abcdef

Confirming payment...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ Payment Failed

Payment Intent: pi_1234567890abcdef
Status: requires_payment_method

Error: Your card was declined.

🔔 Webhook event triggered: payment_intent.payment_failed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 View in Stripe Dashboard:
   https://dashboard.stripe.com/test/payments/pi_1234567890abcdef

🔍 View webhook events:
   tail -f ~/.stripe/webhook-listener.log
```

## Testing Full Checkout Flow

```bash
# 1. Start webhook listener
/stripe:listen

# 2. Create test payment
/stripe:test-payment --amount 2500

# 3. Verify webhook received
tail -f ~/.stripe/webhook-listener.log

# 4. Check your local server logs
tail -f logs/development.log

# 5. Verify payment in Stripe Dashboard
# https://dashboard.stripe.com/test/payments
```

## Common Test Scenarios

### Subscription Payment

```bash
# Test successful subscription payment
/stripe:test-payment --amount 999 --card success

# Test failed subscription payment
/stripe:test-payment --amount 999 --card insufficient_funds
```

### Refund Testing

```bash
# Create successful payment first
PAYMENT_ID=$(/stripe:test-payment --amount 1000 | grep "pi_" | awk '{print $NF}')

# Then refund it
stripe refunds create --payment-intent=$PAYMENT_ID
```

### Dispute Testing

```bash
# Create payment that will be disputed
/stripe:test-payment --amount 1000 --card success

# Dispute it (use Stripe Dashboard test mode)
```

## Related Commands

- `/stripe:listen` - Start webhook listener
- `/stripe:trigger` - Trigger specific webhook events
- `/stripe:create-customer` - Create test customer
- `/stripe:create-subscription` - Create test subscription

## Notes

**Test Mode Only**: These are test payments using Stripe test API keys.

**Test Cards**: Use only Stripe's official test cards. Never use real card numbers.

**Webhooks**: Ensure listener is running to receive webhook events.

**Dashboard**: All test payments visible in Stripe Dashboard (test mode).

---

*Essential for testing payment flows during development*
