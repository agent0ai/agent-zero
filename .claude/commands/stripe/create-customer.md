---
description: Create a test customer in Stripe for development and testing
argument-hint: "[--email <email>] [--name <name>] [--payment-method]"
model: claude-3-5-haiku-20241022
allowed-tools:
  - Bash
---

# Stripe Create Customer Command

## Overview

Quickly creates test customers in Stripe for development. Optionally attaches payment methods for immediate testing.

## Usage

```bash
# Create customer with random email
/stripe:create-customer

# Create with specific email
/stripe:create-customer --email john@example.com

# Create with name and email
/stripe:create-customer --email john@example.com --name "John Doe"

# Create with payment method attached
/stripe:create-customer --email john@example.com --payment-method

# Create and save customer ID for later use
CUSTOMER_ID=$(/stripe:create-customer --email test@example.com)
```

## Implementation

```bash
#!/bin/bash

# Parse arguments
EMAIL=""
NAME=""
ATTACH_PAYMENT_METHOD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --email)
            EMAIL="$2"
            shift 2
            ;;
        --name)
            NAME="$2"
            shift 2
            ;;
        --payment-method)
            ATTACH_PAYMENT_METHOD=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Generate random email if not provided
if [ -z "$EMAIL" ]; then
    EMAIL="test-$(date +%s)@example.com"
fi

# Generate name if not provided
if [ -z "$NAME" ]; then
    NAME="Test Customer $(date +%s)"
fi

echo "👤 Creating Stripe test customer..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Email: $EMAIL"
echo "Name: $NAME"
echo ""

# Create customer
CUSTOMER=$(stripe customers create \
    --email="$EMAIL" \
    --name="$NAME" \
    --description="Test customer created via /stripe:create-customer" \
    --format=json)

CUSTOMER_ID=$(echo "$CUSTOMER" | jq -r '.id')

echo "✓ Customer created: $CUSTOMER_ID"
echo ""

# Attach payment method if requested
if [ "$ATTACH_PAYMENT_METHOD" = true ]; then
    echo "💳 Attaching payment method..."

    # Create payment method (test card)
    PAYMENT_METHOD=$(stripe payment_methods create \
        --type=card \
        --card[number]=4242424242424242 \
        --card[exp_month]=12 \
        --card[exp_year]=2030 \
        --card[cvc]=123 \
        --format=json)

    PAYMENT_METHOD_ID=$(echo "$PAYMENT_METHOD" | jq -r '.id')

    # Attach to customer
    stripe payment_methods attach $PAYMENT_METHOD_ID \
        --customer=$CUSTOMER_ID > /dev/null

    # Set as default
    stripe customers update $CUSTOMER_ID \
        --invoice_settings[default_payment_method]=$PAYMENT_METHOD_ID > /dev/null

    echo "✓ Payment method attached: $PAYMENT_METHOD_ID"
    echo "   Card: •••• 4242 (Visa)"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Customer ready for testing"
echo ""
echo "Customer ID: $CUSTOMER_ID"
echo "Email: $EMAIL"
echo "Name: $NAME"
if [ "$ATTACH_PAYMENT_METHOD" = true ]; then
    echo "Payment Method: Attached (Visa •••• 4242)"
fi
echo ""
echo "📊 View in Stripe Dashboard:"
echo "   https://dashboard.stripe.com/test/customers/$CUSTOMER_ID"
echo ""
echo "Next Steps:"
echo "  • Create subscription: stripe subscriptions create --customer=$CUSTOMER_ID --price=price_xxx"
echo "  • Create payment: stripe payment_intents create --customer=$CUSTOMER_ID --amount=1000"
echo ""

# Output just the customer ID for scripting
echo "$CUSTOMER_ID"
```

## Example Output

```
👤 Creating Stripe test customer...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Email: john@example.com
Name: John Doe

✓ Customer created: cus_1234567890abcdef

💳 Attaching payment method...
✓ Payment method attached: pm_1234567890abcdef
   Card: •••• 4242 (Visa)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Customer ready for testing

Customer ID: cus_1234567890abcdef
Email: john@example.com
Name: John Doe
Payment Method: Attached (Visa •••• 4242)

📊 View in Stripe Dashboard:
   https://dashboard.stripe.com/test/customers/cus_1234567890abcdef

Next Steps:
  • Create subscription: stripe subscriptions create --customer=cus_1234567890abcdef --price=price_xxx
  • Create payment: stripe payment_intents create --customer=cus_1234567890abcdef --amount=1000

cus_1234567890abcdef
```

## Use Cases

### Quick Customer for Testing

```bash
# Create and use immediately
CUSTOMER=$(/stripe:create-customer --email test@example.com)
stripe subscriptions create --customer=$CUSTOMER --price=price_xxx
```

### Batch Customer Creation

```bash
# Create 10 test customers
for i in {1..10}; do
    /stripe:create-customer --email "customer$i@example.com" --name "Customer $i"
done
```

### Customer with Payment Method

```bash
# Ready to charge immediately
/stripe:create-customer \
    --email paying-customer@example.com \
    --name "Paying Customer" \
    --payment-method
```

## Testing Scenarios

### Successful Subscription Flow

```bash
# 1. Create customer with payment method
CUSTOMER=$(/stripe:create-customer --payment-method)

# 2. Create subscription
stripe subscriptions create \
    --customer=$CUSTOMER \
    --items[0][price]=price_xxx

# 3. Verify in dashboard
echo "https://dashboard.stripe.com/test/customers/$CUSTOMER"
```

### Failed Payment Scenario

```bash
# 1. Create customer
CUSTOMER=$(/stripe:create-customer --email declined@example.com)

# 2. Attach declining card
PAYMENT_METHOD=$(stripe payment_methods create \
    --type=card \
    --card[number]=4000000000000002 \  # Declining card
    --card[exp_month]=12 \
    --card[exp_year]=2030 \
    --card[cvc]=123 \
    --format=json | jq -r '.id')

stripe payment_methods attach $PAYMENT_METHOD --customer=$CUSTOMER

# 3. Try to charge (will fail)
stripe payment_intents create \
    --customer=$CUSTOMER \
    --payment-method=$PAYMENT_METHOD \
    --amount=1000 \
    --currency=usd \
    --confirm=true
```

## Related Commands

- `/stripe:create-subscription` - Create subscription for customer
- `/stripe:test-payment` - Create test payment
- `/stripe:list-customers` - List all test customers

## Notes

**Test Mode**: Creates customers in test mode only

**Cleanup**: Remember to delete test customers periodically

**Payment Methods**: Default attaches Visa 4242... (success card)

---

*Essential for quickly setting up test customers during development*
