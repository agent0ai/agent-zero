# Google Voice Integration Testing Guide

**Document Version**: 1.0
**Last Updated**: 2026-01-17
**Purpose**: Test and manage Google Voice SMS messaging for customer check-ins and notifications

---

## Quick Start

### Send Check-in Messages to Today's Customers (Dry Run)

```bash
# Preview messages without sending
python scripts/test_google_voice_checkin.py
```

Expected output shows:

- Number of customers checking in today
- Message content for each customer
- Phone numbers and property details
- Confirmation prompt to send

### Send Messages for Real

```bash
# Actually send the messages
python scripts/test_google_voice_checkin.py --auto-send
```

⚠️ **Important**: The script will open a browser window for Google Voice authentication if needed.

### List Pending Messages

```bash
# View all pending, draft, and sent messages
python scripts/test_google_voice_checkin.py --list-pending
```

---

## Understanding the System

### What Messages Are Sent?

When customers check in today, they automatically receive:

1. **Check-in Welcome Message**
   - Friendly greeting with guest name
   - Confirmation that check-in is ready
   - Instructions to contact if needed
   - Emoji to make it feel personal

**Example:**

```
Hi John! Welcome to Property prop_001! 🎉

We're excited to host you! Check-in is ready. If you have any questions,
reply here or call. Enjoy your stay!
```

### Message Workflow

```
1. DETECT CHECK-INS
   └─ System queries PMS for today's reservations

2. CREATE DRAFT
   └─ GoogleVoiceManager.draft_outbound(phone, message)
   └─ Status: "draft" (not yet sent)

3. APPROVE & SEND
   └─ GoogleVoiceManager.approve_and_send(message_id)
   └─ Status: "approved" → "sent" or "failed"

4. TRACK
   └─ Message logged with timestamp
   └─ EventBus emits "google_voice.sms.sent" event
   └─ Event store records for audit trail
```

### Database

All messages are stored in SQLite:

```
instruments/custom/google_voice/data/google_voice.db

Tables:
  outbound       - Messages being sent out
  inbound        - Messages received from customers
  events         - Event log for audit trail
```

---

## Testing Workflows

### 1. Full Integration Test (Recommended for First Time)

```bash
python scripts/google_voice_integration_test.py
```

This test:

- ✓ Creates a sample message
- ✓ Lists draft messages
- ✓ Shows database statistics
- ✓ Verifies event bus integration
- ✓ Reports overall system health

**Expected Output:**

```
[1/5] DRAFTING MESSAGE
✓ Drafted message ID: 1
  To: +14155551234
  Message: Hi! This is a test message...
  Status: draft

[2/5] LISTING DRAFT MESSAGES
✓ Found 1 draft message(s)

[3/5] DATABASE STATISTICS
✓ Total messages: 1
  - Sent: 0
  - Failed: 0
  - Draft: 1

[4/5] INBOUND MESSAGES
✓ Inbound messages: 0

[5/5] EVENT BUS STATUS
✓ Event bus connected
```

### 2. Check-in Message Dry Run

```bash
# Preview what will be sent (NO ACTUAL SMS)
python scripts/test_google_voice_checkin.py
```

Shows:

- Customer names and phone numbers
- Full message text
- Property details
- Check-in/check-out dates
- Instructions to send for real

**When to use:** Before running the real send to verify messages look good

### 3. Actually Send Check-in Messages

```bash
python scripts/test_google_voice_checkin.py --auto-send
```

This will:

1. Query today's reservations
2. Create draft messages for each
3. Automatically send each message
4. Report success/failure for each

**When to use:** Daily automated messaging or manual batch send

### 4. Interactive Message Send

```bash
python scripts/google_voice_integration_test.py --interactive
```

Interactive prompts for:

- Phone number to send to
- Message content
- Confirmation before sending

**When to use:** Testing with custom phone numbers or messages

### 5. List Pending Messages

```bash
python scripts/test_google_voice_checkin.py --list-pending
```

Shows:

- Draft messages (waiting for approval)
- Approved messages (waiting to send)
- Sent messages (with timestamps)

**When to use:** Checking status of messages in the system

---

## API Integration

### REST Endpoints

All Google Voice operations are also available via REST API:

#### Create Outbound Message

```bash
curl -X POST http://localhost:8000/google_voice_outbound_create \
  -H "Content-Type: application/json" \
  -d '{
    "to_number": "+14155551234",
    "body": "Hello customer!",
    "auto_send": false
  }'
```

**Response:**

```json
{
  "success": true,
  "message": {
    "id": 1,
    "to_number": "+14155551234",
    "body": "Hello customer!",
    "status": "draft"
  }
}
```

#### Approve & Send Message

```bash
curl -X POST http://localhost:8000/google_voice_outbound_approve \
  -H "Content-Type: application/json" \
  -d {
    "message_id": 1
  }
```

#### List Outbound Messages

```bash
curl http://localhost:8000/google_voice_outbound_list
```

**Response:**

```json
{
  "success": true,
  "messages": [
    {
      "id": 1,
      "to_number": "+14155551234",
      "body": "Hello customer!",
      "status": "sent",
      "sent_at": "2026-01-17T15:30:00"
    }
  ]
}
```

#### List Inbound Messages

```bash
curl http://localhost:8000/google_voice_inbound_list
```

#### Sync Inbound Messages

```bash
curl -X POST http://localhost:8000/google_voice_inbound_sync \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'
```

---

## Troubleshooting

### Problem: "Browser window won't open"

**Cause:** Google Voice authentication session needed

**Solution:**

1. Ensure display server available (SSH: use `ssh -X`)
2. Check Google Voice credentials configured in `data/profile/`
3. Try running with `DISPLAY=:0` on headless systems

```bash
DISPLAY=:0 python scripts/test_google_voice_checkin.py --auto-send
```

### Problem: "No customers found for today"

**Cause:** Sample data is used for testing (not real PMS query)

**Solution:**

- Edit script to modify sample check-in data
- Integrate with real PMS provider query (see Implementation Guide)
- Ensure today's date is correct (`date` command)

### Problem: "Message status stuck in 'draft'"

**Cause:** Auto-send not enabled or send failed silently

**Solution:**

1. Check logs: `tail -50 instruments/custom/google_voice/data/events.db`
2. Try manual send:

   ```bash
   python scripts/google_voice_integration_test.py --interactive
   ```

3. Check Google Voice web UI for messages
4. Verify phone number format (must include country code)

### Problem: "EventBus not connected"

**Cause:** Optional event tracking unavailable

**Solution:**

- This is non-critical; messages still send
- Check Python imports are correct
- Verify event_bus library installed

---

## Automation Setup

### Schedule Daily Check-in Messages

Add to crontab:

```bash
# Send check-in messages every day at 8 AM
0 8 * * * cd /path/to/agent-jumbo && python scripts/test_google_voice_checkin.py --auto-send

# List pending messages every hour
0 * * * * cd /path/to/agent-jumbo && python scripts/test_google_voice_checkin.py --list-pending >> /var/log/google_voice.log
```

### Monitoring

Check recent sends:

```bash
# Last 10 sent messages
sqlite3 instruments/custom/google_voice/data/google_voice.db \
  "SELECT id, to_number, sent_at FROM outbound WHERE status='sent' ORDER BY sent_at DESC LIMIT 10"

# Failed messages
sqlite3 instruments/custom/google_voice/data/google_voice.db \
  "SELECT id, to_number, error FROM outbound WHERE status='failed'"
```

---

## Advanced Usage

### Custom Message Templates

Edit message format in script:

```python
def format_checkin_message(guest_name: str, property_name: str) -> str:
    return f"""Hi {guest_name}! Welcome to {property_name}! 🎉

Your check-in is ready. Wi-Fi password is in the welcome packet."""
```

### Bulk Send from CSV

Create `messages.csv`:

```csv
phone,message
+14155551234,Hi John! Welcome!
+13105555678,Hi Maria! Looking forward to hosting you!
+1212555910,Hi Robert! Welcome to NYC!
```

Then send:

```bash
# Dry run
python scripts/google_voice_bulk_send.py messages.csv --preview

# Send for real
python scripts/google_voice_bulk_send.py messages.csv --send
```

### Filter by Status

```bash
# List only failed messages
sqlite3 instruments/custom/google_voice/data/google_voice.db \
  "SELECT * FROM outbound WHERE status='failed'"

# List messages from today
sqlite3 instruments/custom/google_voice/data/google_voice.db \
  "SELECT * FROM outbound WHERE created_at >= DATE('now')"
```

### Event Bus Integration

Messages trigger events:

```python
# When message is sent:
await event_bus.emit("google_voice.sms.sent", {
    "message_id": 1,
    "to_number": "+14155551234",
    "body": "Message text",
    "sent_at": "2026-01-17T15:30:00"
})

# When inbound message received:
await event_bus.emit("google_voice.sms.inbound", {
    "from_number": "+14155551234",
    "body": "Customer reply",
    "received_at": "2026-01-17T15:35:00"
})
```

Subscribe to these events in your agents:

```python
@event_bus.on("google_voice.sms.sent")
async def handle_sent_message(event):
    print(f"Message sent to {event['to_number']}")
```

---

## Best Practices

### 1. Always Dry-Run First

```bash
# Preview before sending
python scripts/test_google_voice_checkin.py

# Review output
# Then send if looks good
python scripts/test_google_voice_checkin.py --auto-send
```

### 2. Test with Real Numbers Sparingly

Google Voice has rate limits. For testing:

- Use same test number multiple times
- Space out tests by 30+ seconds
- Keep daily test volume <10 messages

### 3. Monitor Message Status

```bash
# Run hourly
python scripts/test_google_voice_checkin.py --list-pending
```

### 4. Keep Audit Trail

All messages are logged to database with:

- Timestamp (when sent)
- Phone number (to/from)
- Message content
- Status (draft/sent/failed)
- Error details (if failed)

### 5. Handle Errors Gracefully

Messages that fail are marked with error details:

```bash
sqlite3 instruments/custom/google_voice/data/google_voice.db \
  "SELECT id, to_number, error FROM outbound WHERE status='failed'"
```

Retry failed messages:

```python
from instruments.custom.google_voice.google_voice_manager import GoogleVoiceManager

manager = GoogleVoiceManager(db_path)
failed_msgs = manager.list_outbound("failed")
for msg in failed_msgs:
    await manager.approve_and_send(msg["id"])
```

---

## FAQ

**Q: Will this actually send SMS messages?**
A: Only if you run with `--auto-send` flag. Default is dry-run (preview only).

**Q: Where are messages stored?**
A: SQLite database: `instruments/custom/google_voice/data/google_voice.db`

**Q: Can I customize the message?**
A: Yes, edit `format_checkin_message()` function in the script.

**Q: How do I handle replies from customers?**
A: Run `python scripts/test_google_voice_checkin.py --list-pending` to sync and view replies.

**Q: Can this integrate with my PMS system?**
A: Yes! Replace sample data with real PMS queries. See TECHNICAL_IMPLEMENTATION_GUIDE.md

**Q: What if Google Voice authentication fails?**
A: Check credentials in `data/profile/`. May need to re-authenticate via browser.

---

## Files Reference

| File | Purpose |
|------|---------|
| `scripts/test_google_voice_checkin.py` | Send check-in messages to today's customers |
| `scripts/google_voice_integration_test.py` | Test message lifecycle and system health |
| `instruments/custom/google_voice/` | Core Google Voice integration |
| `instruments/custom/google_voice/data/` | Messages database and session data |
| `python/api/google_voice_*.py` | REST API endpoints |

---

## Next Steps

1. **Run a dry-run test**: `python scripts/test_google_voice_checkin.py`
2. **Review messages**: Check output and verify looks good
3. **Send to test number**: Use `--interactive` flag with your own number
4. **Schedule automation**: Add cron job for daily sends
5. **Monitor status**: Use `--list-pending` to track message status
6. **Integrate with PMS**: Modify script to query your real PMS data

---

For questions or issues, check the troubleshooting section or review the source code in:

- `instruments/custom/google_voice/google_voice_manager.py`
- `python/api/google_voice_*.py`

---

**Maintained by**: Development Team
**Last Updated**: 2026-01-17
