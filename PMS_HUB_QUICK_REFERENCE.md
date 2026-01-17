# PMS Hub: Quick Reference Guide

## File Structure
```
instruments/custom/pms_hub/
├── pms_provider.py                 # Abstract PMSProvider base class
├── provider_registry.py            # Config management (~/.pms_hub/providers.json)
├── sync_service.py                 # PMS ↔ PropertyManager sync
├── canonical_models.py             # Reservation, Property, Unit, etc.
└── providers/
    ├── hostaway.py                 # Hostaway OAuth2 Bearer token
    ├── lodgify.py                  # Lodgify API Key + HMAC-SHA256 webhooks
    ├── hostify.py                  # Hostify API Key
    └── ical.py                     # iCal calendar feed (read-only)

python/api/
├── pms_webhook_receive.py          # POST /api/pms/webhook/{provider}/{provider_id}
├── pms_settings_get.py             # GET provider configs (no credentials exposed)
└── pms_settings_set.py             # POST add/update/remove providers

python/tools/
└── pms_hub_tool.py                 # Agent-zero integration tool

python/helpers/
└── event_bus.py                    # Event emission & SQLite storage
```

## Authentication Summary

| Provider | Type | Token Storage | Refresh | Webhook Verify | Supported Events |
|----------|------|---|---|---|---|
| **Hostaway** | OAuth2 Bearer | Memory + JSON | ❌ NO | ❌ NOT IMPL | reservation.*, message.*, review.*, calendar.* |
| **Lodgify** | API Key Bearer | Memory + JSON | N/A | ✅ HMAC-SHA256 | reservation.*, message.*, review.* |
| **Hostify** | API Key Bearer | Memory + JSON | N/A | ❌ NOT IMPL | reservation.*, message.*, review.* |
| **iCal** | HTTP GET | None | N/A | N/A (polling) | None (calendar only) |

## Credential Storage
- **Location:** `~/.pms_hub/providers.json` (plaintext JSON)
- **Security:** ⚠️ NOT ENCRYPTED - plaintext credentials on disk
- **Access Control:** User-readable only
- **Recommendations:** Use environment variables or encryption

## Webhook Flow
```
1. External Webhook POST /api/pms/webhook/{provider}/{provider_id}
2. pms_webhook_receive.py verifies signature (if required)
3. event_bus.emit("pms.webhook.{provider}.{event}")
4. Event stored in SQLite: ~/.pms_hub/events.db
5. ⚠️ NO HANDLERS - events stored but never processed
6. ❌ Sync service NOT triggered automatically
```

## API Endpoints

### POST /api/pms/webhook/{provider}/{provider_id}
```
Headers: X-Signature (optional)
Body: { provider, provider_id, event, payload, timestamp }
Response: { status, event_id } or { status: error, code }
```

### GET /api/pms/settings
```
Query: provider_id (optional)
Response: 
- All: { providers: [{id, type, name, enabled, has_credentials}], total, enabled_count }
- Single: { provider: {id, type, name, enabled, has_credentials} }
```

### POST /api/pms/settings
```
Body:
- add: { action, provider_id, provider_type, name, credentials }
- update: { action, provider_id, credentials, options }
- remove: { action, provider_id }
- enable/disable: { action, provider_id }

Response: { status, message, provider_id }
```

## Tool Actions (pms_hub_tool.py)

```python
# Status & Configuration
pms_hub.execute(action="status")
pms_hub.execute(action="list_providers")
pms_hub.execute(action="register_provider", provider_type, name, credentials)
pms_hub.execute(action="unregister_provider", provider_id)

# Data Operations
pms_hub.execute(action="get_reservations", provider_id, property_id, start_date, end_date)
pms_hub.execute(action="get_properties", provider_id)
pms_hub.execute(action="get_calendar", provider_id, property_id, start_date, end_date)
pms_hub.execute(action="send_message", provider_id, reservation_id, subject, body)

# Synchronization
pms_hub.execute(action="sync_reservations", provider_id)
pms_hub.execute(action="sync_status")
```

## Key Code References

### Hostaway Authentication (Line 57-75)
```python
GET /v1/user with Authorization: Bearer {access_token}
```

### Lodgify Webhook Verification (Line 513-539)
```python
payload_str = json.dumps(payload, separators=(",", ":"), sort_keys=True)
hmac.new(api_secret.encode(), payload_str.encode(), hashlib.sha256).hexdigest()
hmac.compare_digest(signature, expected_signature)
```

### Registry Config File (Line 63)
```python
self.config_path = Path.home() / ".pms_hub" / "providers.json"
```

### Sync Service (Line 41-94)
```python
sync_reservation_to_property_manager(reservation)
├─ _sync_property() → add_property()
├─ _sync_unit() → add_units()
├─ _sync_guest_to_tenant() → add_tenant()
├─ _sync_reservation_to_lease() → create_lease()
└─ _record_payment() → record_payment()
```

## Critical Issues & Gaps

### 🔴 CRITICAL
1. **Webhook Event Handlers Missing** - Events emitted but no subscribers
2. **Hostaway Webhook Verification** - No signature verification (always True)
3. **Hostify Webhook Verification** - No signature verification (always True)
4. **Plaintext Credentials** - JSON file not encrypted

### 🟠 HIGH
1. **No Token Refresh** - OAuth2 tokens expire
2. **No Reverse Sync** - PropertyManager → PMS not implemented
3. **Minimal Error Handling** - No retry/backoff logic
4. **No Rate Limiting** - No handling for HTTP 429

### 🟡 MEDIUM
1. **iCal Authentication** - No support for authenticated feeds
2. **Pagination Edge Cases** - Limited validation
3. **Configuration Dependencies** - Silent failures

## Event Bus Architecture

```python
# Webhook received
event_bus.emit("pms.webhook.hostaway.reservation.new", {
    "provider": "hostaway",
    "provider_id": "main_hostaway",
    "payload": {...},
    "webhook_timestamp": "..."
})

# Stored in SQLite
# SELECT * FROM events WHERE type LIKE 'pms.webhook.%'

# No subscribers currently registered ⚠️
# event_bus.subscribe("pms.webhook.*", handler_func)
```

## Configuration Example

**~/.pms_hub/providers.json**
```json
{
  "providers": {
    "main_hostaway": {
      "provider_type": "hostaway",
      "name": "Main Hostaway Account",
      "enabled": true,
      "credentials": {
        "user_id": "12345",
        "api_key": "secret_key",
        "access_token": "oauth_token"
      },
      "options": {}
    },
    "main_lodgify": {
      "provider_type": "lodgify",
      "name": "Lodgify Account",
      "enabled": true,
      "credentials": {
        "api_key": "api_key_here",
        "api_secret": "secret_for_webhook_verification",
        "account_id": "acc_123"
      },
      "options": {}
    }
  }
}
```

## Integration Points

```
Agent-Zero
    ↓
pms_hub_tool.execute()
    ↓
ProviderRegistry (load from ~/.pms_hub/providers.json)
    ↓
Provider Instance (Hostaway/Lodgify/Hostify/iCal)
    ↓
API Request (with authentication headers)
    ↓
Canonical Models (Reservation, Property, etc.)
    ↓
PropertyManager Sync (if enabled)
```

## Testing

**Existing Tests:**
- ✅ test_pms_providers.py - Unit tests
- ✅ test_pms_registry.py - Registry tests
- ✅ test_pms_sync_service.py - Sync tests

**Missing Tests:**
- ❌ Webhook signature verification (end-to-end)
- ❌ Webhook event handling
- ❌ Error conditions
- ❌ PropertyManager integration

---

For complete analysis, see: **PMS_HUB_ANALYSIS.md** (1326 lines)
