# PMS Hub: Comprehensive Authentication and System Integration Analysis

**Analysis Date:** 2026-01-17
**Scope:** Complete PMS Hub implementation in `/home/webemo-aaron/projects/agent-jumbo/instruments/custom/pms_hub/`

---

## EXECUTIVE SUMMARY

The PMS Hub is a multi-provider property management system integration layer supporting Hostaway, Lodgify, Hostify, and iCal. The architecture consists of:

1. **Provider Adapters** - PMS-specific API clients with standardized interface
2. **Provider Registry** - Configuration management and lifecycle control
3. **Sync Service** - Bi-directional synchronization with property_manager
4. **API Endpoints** - Webhook handlers and configuration REST endpoints
5. **Event Bus Integration** - Event-driven architecture for webhook processing

---

## PART 1: PROVIDER AUTHENTICATION METHODS

### 1.1 HOSTAWAY AUTHENTICATION

**Authentication Type:** OAuth 2.0 Bearer Token + API Key
**Files:** `/home/webemo-aaron/projects/agent-jumbo/instruments/custom/pms_hub/providers/hostaway.py`

#### Configuration Requirements

```python
# Line 42-55: Configuration Loading
config = {
    "user_id": str,          # Hostaway user ID
    "api_key": str,          # Primary API key
    "access_token": str      # OAuth 2.0 access token
}
```

#### Token Storage & Management

- **Location:** Memory (`self.access_token`, `self.api_key`) - Line 49-55
- **Provider Registry:** `~/.pms_hub/providers.json` (credentials dict)
- **Flow:** Registry loads from JSON → passes to HostawayProvider constructor

#### Authentication Flow

```
HostawayProvider.authenticate() (Line 57-75)
├─ _get_headers() builds Bearer token header
├─ GET /v1/user with Authorization: Bearer {token}
└─ Status 200 → _authenticated = True

_get_headers() (Line 504-510)
└─ Authorization: Bearer {access_token OR api_key}
```

#### Token Refresh Mechanism

- **Status:** NOT IMPLEMENTED
- **Issue:** No token expiration handling or refresh logic
- **Risk:** Long-lived tokens could become invalid

#### Webhook Verification

- **Method:** Default implementation returns True (Line 228-240 in pms_provider.py)
- **Status:** NOT IMPLEMENTED for Hostaway
- **Supported Events:** reservation.new, reservation.confirmed, reservation.updated, reservation.cancelled, message.new, review.new, calendar.updated (Line 490-500)

---

### 1.2 LODGIFY AUTHENTICATION

**Authentication Type:** API Key (Bearer Token) + HMAC-SHA256 Webhook Verification
**Files:** `/home/webemo-aaron/projects/agent-jumbo/instruments/custom/pms_hub/providers/lodgify.py`

#### Configuration Requirements

```python
# Line 42-52: Configuration Loading
config = {
    "api_key": str,          # API key for authorization
    "api_secret": str,       # Secret for webhook signature verification
    "account_id": str        # Lodgify account ID
}
```

#### Token Storage & Management

- **Location:** Memory (`self.api_key`, `self.api_secret`)
- **Provider Registry:** `~/.pms_hub/providers.json` (credentials dict)
- **api_secret:** Used for HMAC signature verification only (not for API calls)

#### Authentication Flow

```
LodgifyProvider.authenticate() (Line 54-72)
├─ _get_headers() builds Bearer token header
├─ GET /account with Authorization: Bearer {api_key}
└─ Status 200 → _authenticated = True

_get_headers() (Line 543-549)
└─ Authorization: Bearer {api_key}
```

#### Webhook Signature Verification

**Method:** HMAC-SHA256 with sorted JSON payload
**Code:** `verify_webhook()` (Line 513-539)

```python
# Line 513-539: Webhook Verification
def verify_webhook(self, payload: Dict[str, Any], signature: str) -> bool:
    """
    Args:
        payload: Webhook payload dict
        signature: ms-signature header value
    Returns:
        True if hmac.compare_digest(signature, expected_signature)
    """
    if not self.api_secret:
        return False

    payload_str = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    expected_signature = hmac.new(
        self.api_secret.encode(),
        payload_str.encode(),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)
```

#### Webhook Events

- reservation.created, reservation.updated, reservation.cancelled
- message.created, review.created
- **Verification Required:** Yes - via ms-signature header

#### Pagination & Rate Limiting

- **Method:** Cursor-based pagination
- **Rate Limiting:** NOT IMPLEMENTED
- **Issue:** No backoff/retry mechanism

---

### 1.3 HOSTIFY AUTHENTICATION

**Authentication Type:** API Key (Bearer Token)
**Files:** `/home/webemo-aaron/projects/agent-jumbo/instruments/custom/pms_hub/providers/hostify.py`

#### Configuration Requirements

```python
# Line 36-45: Configuration Loading
config = {
    "api_key": str,          # API key for authorization
    "account_id": str        # Account identifier
}
```

#### Token Storage & Management

- **Location:** Memory (`self.api_key`)
- **Provider Registry:** `~/.pms_hub/providers.json` (credentials dict)
- **No secret key for webhook verification**

#### Authentication Flow

```
HostifyProvider.authenticate() (Line 47-56)
├─ _get_headers() builds Bearer token header
├─ GET /v2/accounts/me with Authorization: Bearer {api_key}
└─ Status 200 → _authenticated = True

_get_headers() (Line 351-356)
└─ Authorization: Bearer {api_key}
```

#### Webhook Verification

- **Method:** Not implemented (returns default True)
- **Status:** INCOMPLETE
- **Risk:** No signature verification means potential spoofing

#### Supported Webhook Events

- reservation.created, reservation.updated, reservation.cancelled
- message.created, review.created
- **Verification:** NOT IMPLEMENTED

---

### 1.4 iCAL AUTHENTICATION

**Authentication Type:** URL-based (HTTP GET with optional auth headers)
**Files:** `/home/webemo-aaron/projects/agent-jumbo/instruments/custom/pms_hub/providers/ical.py`

#### Configuration Requirements

```python
# Line 35-45: Configuration Loading
config = {
    "ical_url": str,         # URL to iCal feed
    "property_id": str,      # Property identifier
    "property_name": str     # Display name
}
```

#### Authentication Flow

```
ICalProvider.authenticate() (Line 47-58)
├─ Verify iCal feed is accessible
├─ GET {ical_url} with follow_redirects=True
└─ Status 200 → _authenticated = True
```

#### Limitations

- **No credentials support** - relies on public URLs
- **No messaging** - calendar synchronization only
- **Read-only** - cannot update calendar at source
- **No webhook support** - polling only
- **No authentication mechanism** for feeds requiring credentials

---

## PART 2: CREDENTIAL STORAGE & SECURITY

### 2.1 File Locations

| Component | Path | Format | Security |
|-----------|------|--------|----------|
| Provider Config | `~/.pms_hub/providers.json` | JSON plaintext | User-readable |
| Event Store | `~/.pms_hub/events.db` | SQLite | Audit logs only |
| Hostaway Token | Memory + JSON | Plaintext | Exposed in config |
| Lodgify Credentials | Memory + JSON | Plaintext | Exposed in config |
| Hostify API Key | Memory + JSON | Plaintext | Exposed in config |

**Configuration File Location:** `/home/webemo-aaron/projects/agent-jumbo/instruments/custom/pms_hub/provider_registry.py:63`

```python
self.config_path = config_path or Path.home() / ".pms_hub" / "providers.json"
```

### 2.2 Security Issues

**CRITICAL FINDINGS:**

1. **Plaintext Credential Storage** (Line 63, provider_registry.py)
   - Credentials stored in JSON without encryption
   - File permissions: User-readable only
   - No encryption at rest

2. **No Credential Masking in API Responses** (pms_settings_get.py:49)

   ```python
   # GOOD: Credentials not exposed
   "has_credentials": bool(config.credentials)  # Only boolean flag
   ```

   - API responses hide credential values
   - But file system exposure remains

3. **Token Lifecycle Management**
   - Hostaway: No refresh logic
   - Lodgify: Static API key (no token refresh)
   - Hostify: Static API key
   - iCal: No credentials

4. **Recommendations:**
   - Use environment variables for sensitive credentials
   - Implement credential encryption using cryptography library
   - Add credential rotation mechanism
   - Use OS-level key storage (keyring)

---

## PART 3: WEBHOOK SECURITY & VERIFICATION

### 3.1 Webhook Architecture

**Entry Point:** `/home/webemo-aaron/projects/agent-jumbo/python/api/pms_webhook_receive.py`

```
External Webhook (POST /api/pms/webhook/{provider}/{provider_id})
    ↓
PMSWebhookReceive.process() (Line 36-113)
    ├─ Extract: provider, provider_id, signature, payload
    ├─ Validate: provider exists and enabled
    ├─ Verify: _verify_webhook() (Line 115-142)
    └─ Emit: EventBus event (pms.webhook.{provider}.{event})
    ↓
EventBus (python/helpers/event_bus.py:78-98)
    └─ Store event + trigger subscribers
```

### 3.2 Signature Verification Flow

**File:** `pms_webhook_receive.py:76-81`

```python
async def process(self, input: dict, request: Request) -> dict | Response:
    # ...
    if not await self._verify_webhook(provider_id, payload, signature):
        return {
            "status": "error",
            "message": "Invalid webhook signature",
            "code": 401,
        }
```

**Verification Logic:** `_verify_webhook()` (Line 115-142)

```python
async def _verify_webhook(
    self, provider_id: str, payload: Dict[str, Any], signature: str
) -> bool:
    """
    Delegates to provider's verify_webhook method
    """
    if not signature:
        # No signature provided - some providers don't require it
        return True  # SECURITY ISSUE: Accepts unsigned payloads

    try:
        provider = await self.registry.get_provider_async(provider_id)
        if not provider:
            return False

        # Use provider's verify_webhook method
        return provider.verify_webhook(payload, signature)
    except Exception as e:
        print(f"Webhook verification error: {e}")
        return False
```

### 3.3 Provider-Specific Verification

| Provider | Method | Implementation | Status |
|----------|--------|-----------------|--------|
| **Hostaway** | Custom | Default returns True | NOT IMPLEMENTED |
| **Lodgify** | HMAC-SHA256 | Full implementation | COMPLETE |
| **Hostify** | Custom | Default returns True | NOT IMPLEMENTED |
| **iCal** | N/A | No webhooks (polling) | N/A |

### 3.4 Webhook Signature Methods

#### Lodgify: HMAC-SHA256

**Location:** `lodgify.py:513-539`

```
Header: X-Signature or ms-signature
Body: JSON payload
Secret: api_secret (configuration)
Algorithm: SHA256
Format: Hex digest
```

**Exact Implementation:**

```python
payload_str = json.dumps(payload, separators=(",", ":"), sort_keys=True)
expected_signature = hmac.new(
    self.api_secret.encode(),
    payload_str.encode(),
    hashlib.sha256,
).hexdigest()
```

**Verification:** `hmac.compare_digest()` for timing-attack resistance

#### Hostaway & Hostify

- **Current Status:** Stubbed implementation returns True
- **Expected:** Likely custom signature headers (not documented)
- **Gap:** Implementation missing

### 3.5 Webhook Event Handling

**Event Flow:**

```
webhook_receive.py:85-92
    └─ event_bus.emit(f"pms.webhook.{provider}.{event_type}", {...})
        ↓
        EventBus.emit() (event_bus.py:91-98)
            ├─ EventStore.add_event() → SQLite database
            └─ Execute registered handlers
                ├─ Sync handlers for specific event type
                └─ Wildcard handlers (*)
```

**Event Structure:**

```python
{
    "provider": "hostaway|lodgify|hostify",
    "provider_id": "registered_id",
    "payload": {...},  # Provider-specific payload
    "webhook_timestamp": "ISO datetime"
}
```

**No Event Consumer Registered** ⚠️

- Events are emitted but no handlers subscribed
- Gap in implementation: webhook events not processed to sync

---

## PART 4: SYSTEM INTEGRATION POINTS

### 4.1 Provider Registry ↔ Sync Service Connection

**Files:**

- Provider Registry: `provider_registry.py:53-327`
- Sync Service: `sync_service.py:19-361`

**Integration Points:**

```
PMSSyncService.__init__() (Line 25-39)
    └─ self.registry = ProviderRegistry()
        ├─ Loads from ~/.pms_hub/providers.json
        └─ Creates provider instances on demand

PMSSyncService.sync_all_reservations() (Line 308-340)
    ├─ provider = await registry.get_provider_async(provider_id)
    ├─ reservations = await provider.get_reservations()
    └─ For each: sync_reservation_to_property_manager(reservation)
```

**Data Flow:**

```
Registry Config (JSON)
    ↓
ProviderConfig objects
    ↓
create_provider() factory (providers/__init__.py:10-47)
    ├─ Authenticate provider
    └─ Return PMSProvider instance
    ↓
Sync Service (uses provider)
    └─ Fetch data via provider methods
```

### 4.2 EventBus Integration

**Files:**

- EventBus: `python/helpers/event_bus.py:1-99`
- EventStore: `python/helpers/event_bus.py:12-75`
- Webhook Receiver: `pms_webhook_receive.py:1-142`

**Event Emission:**

```
pms_webhook_receive.py:85-92
    └─ self.event_bus.emit(
        "pms.webhook.hostaway.reservation.new",
        {
            "provider": "hostaway",
            "provider_id": "main_hostaway",
            "payload": {...},
            "webhook_timestamp": "2026-01-17T..."
        }
    )
```

**Event Storage:**

```
EventStore.add_event() (event_bus.py:34-53)
    ├─ Hash event using hash_event() (audit.py)
    ├─ Store in SQLite: events table
    │   ├─ id (autoincrement)
    │   ├─ type (string)
    │   ├─ payload (JSON)
    │   ├─ event_hash (audit hash)
    │   └─ created_at (ISO timestamp)
    └─ Return event dict
```

**Event Subscription:**

```
EventBus.subscribe() (event_bus.py:83-84)
    └─ self._handlers.setdefault(event_type, []).append(handler)

EventBus.emit() (event_bus.py:91-98)
    ├─ Store event
    ├─ Get handlers for specific event type
    ├─ Get wildcard handlers ("*")
    └─ Execute all handlers
```

**ISSUE:** No subscribers registered for PMS webhook events

- Events are emitted and stored but never processed
- Gap: Need handlers to call sync_service on webhook events

### 4.3 PropertyManager Sync Integration

**Files:**

- Sync Service: `sync_service.py:41-361`

**Sync Chain:**

```
sync_reservation_to_property_manager(reservation) (Line 41-94)
    ├─ Step 1: _sync_property() → Property created in manager
    ├─ Step 2: _sync_unit() → Unit created (optional)
    ├─ Step 3: _sync_guest_to_tenant() → Tenant created
    ├─ Step 4: _sync_reservation_to_lease() → Lease created
    └─ Step 5: _record_payment() → Payment recorded
```

**Property Manager API Calls:**

```python
# Line 139: Add property
result = await self.pm.add_property(property_data)

# Line 170: Add unit
result = await self.pm.add_units(property_id, unit_data)

# Line 205: Add tenant
result = await self.pm.add_tenant(tenant_data)

# Line 249: Create lease
result = await self.pm.create_lease(lease_data)

# Line 280: Record payment
result = await self.pm.record_payment(payment_data)
```

**Mapping Logic:**

```
PMS Data → PropertyManager Data
├─ Reservation.status → Lease.status (Line 286-306)
│   ├─ PENDING → pending
│   ├─ CONFIRMED → active
│   ├─ CHECKED_IN → active
│   ├─ CHECKED_OUT → expired
│   └─ CANCELLED → terminated
├─ Guest → Tenant (Line 181-212)
├─ Reservation → Lease (Line 214-256)
└─ Payment recording (Line 258-284)
```

**Dependency:** PropertyManager import (Line 30-39)

```python
try:
    from property_manager.property_manager import PropertyManager as PM
    from property_manager.property_db import PropertyDatabase

    self.pm = PM()
    self.pm_db = PropertyDatabase()
except ImportError:
    print("Warning: PropertyManager not available for sync")
    self.pm = None
    self.pm_db = None
```

### 4.4 API Endpoints Integration

**Files:**

- Webhook Receiver: `python/api/pms_webhook_receive.py`
- Settings Get: `python/api/pms_settings_get.py`
- Settings Set: `python/api/pms_settings_set.py`

#### pms_webhook_receive (POST /api/pms/webhook/{provider}/{provider_id})

```
Input:
├─ provider: hostaway|lodgify|hostify|ical
├─ provider_id: registered provider ID
├─ signature: webhook signature
├─ payload: event payload
└─ timestamp: webhook timestamp

Processing:
├─ Validate provider exists
├─ Verify signature (provider-specific)
└─ Emit EventBus event

Output:
├─ success: 200 with event_id
├─ error: 401 invalid signature
├─ error: 404 provider not found
└─ error: 400 missing parameters
```

#### pms_settings_get (GET /api/pms/settings)

```
Input:
└─ provider_id (optional): specific provider

Output:
├─ All providers:
│   ├─ List of {id, type, name, enabled, has_credentials}
│   └─ total, enabled_count
└─ Single provider:
    └─ {id, type, name, enabled, has_credentials}

Security:
├─ Credentials NOT exposed (only boolean flag)
└─ Safe for untrusted callers
```

**Implementation:** `pms_settings_get.py:14-81`

#### pms_settings_set (POST /api/pms/settings)

```
Actions:
├─ add: Register new provider
├─ update: Update credentials/options
├─ remove: Unregister provider
├─ enable: Enable provider
└─ disable: Disable provider

Add Parameters:
├─ action: "add"
├─ provider_id: unique ID
├─ provider_type: hostaway|lodgify|hostify|ical
├─ name: display name
└─ credentials: {api_key, access_token, ...}

Validation:
├─ provider_id required
├─ provider_type required and valid
├─ credentials required and is dict

Output:
├─ success: provider registered/updated
└─ error: validation or registration failure
```

**Implementation:** `pms_settings_set.py:14-206`

### 4.5 PMSHub Tool Integration with agent-jumbo

**File:** `/home/webemo-aaron/projects/agent-jumbo/python/tools/pms_hub_tool.py`

**Tool Class:** `PMSHub(Tool)` (Line 16-75)

**Actions:**

| Action | Purpose | Returns |
|--------|---------|---------|
| `status` | Get PMS Hub status | providers count, enabled count |
| `list_providers` | List all registered | List of {id, type, name, enabled} |
| `register_provider` | Add new provider | success message, provider_id |
| `unregister_provider` | Remove provider | success message |
| `get_reservations` | Fetch reservations | List with dates, guest, price |
| `get_properties` | Fetch properties | List with details |
| `get_calendar` | Get availability | Calendar days with status/price |
| `send_message` | Send to guest | success/failure |
| `sync_reservations` | Sync to property_manager | synced count, error count |
| `sync_status` | Get sync info | providers enabled, last sync |

**Integration Pattern:**

```
Agent-zero Tool Call
    ↓
pms_hub_tool.py:execute(**kwargs)
    ├─ Dispatch by action
    └─ Call _action() method
        ├─ Get registry/sync service
        ├─ Execute operation
        └─ Return Response(status, data)
```

**Example: Get Reservations** (Line 189-251)

```python
async def _get_reservations(self, kwargs) -> Response:
    provider_id = kwargs.get("provider_id")

    provider = await registry.get_provider_async(provider_id)
    reservations = await provider.get_reservations(
        property_id=kwargs.get("property_id"),
        start_date=parse(kwargs.get("start_date")),
        end_date=parse(kwargs.get("end_date"))
    )

    return Response(status="success", data={
        "reservations": [
            {
                "id": r.provider_id,
                "guest": r.guest_name,
                "check_in": r.check_in_date.isoformat(),
                ...
            }
            for r in reservations
        ]
    })
```

---

## PART 5: DATA FLOW PATHS

### 5.1 External Webhook → EventBus → Sync Service Flow

```
1. WEBHOOK RECEPTION (pms_webhook_receive.py)
   POST /api/pms/webhook/hostaway/main
   Headers: X-Signature: {...}
   Body: {
       "action": "reservation.new",
       "data": {...}
   }

2. SIGNATURE VERIFICATION (pms_webhook_receive.py:115-142)
   provider = await registry.get_provider_async("main")
   provider.verify_webhook(payload, signature)
   ├─ Hostaway: Default True (NOT IMPLEMENTED)
   └─ Lodgify: HMAC-SHA256 verify

3. EVENT EMISSION (pms_webhook_receive.py:85-92)
   event_bus.emit(
       "pms.webhook.hostaway.reservation.new",
       {
           "provider": "hostaway",
           "provider_id": "main",
           "payload": {...},
           "webhook_timestamp": "..."
       }
   )

4. EVENT STORAGE (event_bus.py:34-53)
   SQLite: INSERT INTO events (type, payload, event_hash, created_at)
   └─ Audit hash generated from event

5. EVENT DISTRIBUTION (event_bus.py:91-98)
   For each handler in _handlers.get("pms.webhook.hostaway.reservation.new", []):
       await handler(event)

6. GAP: NO SYNC HANDLER REGISTERED ⚠️
   ├─ Events stored but not processed
   ├─ Sync service not triggered
   └─ Requires: EventBus subscriber for sync events
```

### 5.2 Agent-zero Tool Calls → API → Registry → Provider Flow

```
1. AGENT TOOL CALL (pms_hub_tool.py)
   pms_hub.execute(
       action="get_reservations",
       provider_id="main_hostaway",
       start_date="2026-01-01",
       end_date="2026-12-31"
   )

2. ACTION DISPATCH (pms_hub_tool.py:22-75)
   _get_reservations(kwargs)

3. REGISTRY LOOKUP (pms_hub_tool.py:189-251)
   provider = await registry.get_provider_async("main_hostaway")
   ├─ Check instances cache
   ├─ If not cached:
   │   ├─ Get config from registry.providers
   │   ├─ Call create_provider(type, credentials)
   │   └─ Authenticate provider
   └─ Return cached instance

4. PROVIDER API CALL (hostaway.py, lodgify.py, etc.)
   reservations = await provider.get_reservations(
       property_id="prop_123",
       start_date=date(2026, 1, 1),
       end_date=date(2026, 12, 31)
   )

5. API REQUEST (hostaway.py:145-208)
   ├─ Build headers with Authorization: Bearer {token}
   ├─ Paginate through results (offset-based)
   ├─ Transform to canonical models
   └─ Return List[Reservation]

6. RESPONSE (pms_hub_tool.py:227-240)
   return Response(
       status="success",
       data={
           "reservations": [
               {
                   "id": r.provider_id,
                   "guest": r.guest_name,
                   "check_in": r.check_in_date.isoformat(),
                   "status": r.status.value,
                   ...
               }
           ]
       }
   )
```

### 5.3 Bi-directional Sync Coordination

```
PULL (PMS → PropertyManager):

1. MANUAL TRIGGER
   pms_hub.execute(
       action="sync_reservations",
       provider_id="main_hostaway"
   )

2. SYNC SERVICE (sync_service.py:308-340)
   sync_all_reservations(provider_id)
   ├─ Get provider instance
   ├─ provider.get_reservations()
   └─ For each:
       sync_reservation_to_property_manager(reservation)

3. PROPERTY MANAGER SYNC (sync_service.py:41-94)
   ├─ Ensure property exists (or create)
   ├─ Ensure unit exists (optional)
   ├─ Create tenant from guest
   ├─ Create lease from reservation
   ├─ Record payment
   └─ Store manager IDs in reservation


PUSH (PropertyManager → PMS):

1. NO IMPLEMENTATION
   Gap: Bidirectional sync not implemented
   ├─ Cannot update PMS from property_manager
   ├─ No reverse mapping logic
   └─ Requires: New sync direction implementation
```

---

## PART 6: MISSING OR INCOMPLETE INTEGRATIONS

### 6.1 Critical Gaps

#### Gap 1: Webhook Event Handlers Not Connected

**Severity:** HIGH
**File:** `pms_webhook_receive.py` and `sync_service.py`
**Issue:** Webhooks are received and events emitted, but no handlers subscribed

```python
# Event is emitted but never handled
event_bus.emit("pms.webhook.hostaway.reservation.new", {...})
    ↓
# No subscribers registered for this event type
# Sync service never called
```

**Fix Required:**

```python
# In sync_service.py or separate handler module:
event_bus.subscribe("pms.webhook.*", handle_pms_webhook)

async def handle_pms_webhook(event):
    provider_id = event['payload']['provider_id']
    await sync_service.sync_all_reservations(provider_id)
```

#### Gap 2: Hostaway Webhook Signature Verification

**Severity:** HIGH
**Files:** `hostaway.py:228-240` (default implementation)
**Issue:** No actual signature verification - always returns True

**Current Code:**

```python
async def verify_webhook(self, payload: Dict[str, Any], signature: str) -> bool:
    # Default implementation - override in provider if needed
    return True  # UNSAFE!
```

**Missing:** Hostaway signature algorithm documentation and implementation

#### Gap 3: Hostify Webhook Verification

**Severity:** HIGH
**Files:** `hostify.py` (uses default)
**Issue:** No signature verification implemented

**Missing:** Hostify-specific signature header and algorithm

#### Gap 4: Token Refresh Mechanism

**Severity:** MEDIUM
**All Providers**
**Issue:** No token expiration handling

**Hostaway OAuth:**

- access_token expires after configured duration
- No refresh token handling
- Failed API calls when token expires

**Recommendations:**

1. Store refresh token (if available)
2. Detect 401 responses
3. Attempt refresh before failing
4. Re-try request with new token

#### Gap 5: Reverse Sync (PropertyManager → PMS)

**Severity:** MEDIUM
**File:** `sync_service.py`
**Issue:** One-way sync only (PMS to PropertyManager)

**Missing:**

- Sync lease changes back to PMS
- Update reservation status in PMS
- Update pricing from property_manager

#### Gap 6: Error Handling & Retry Logic

**Severity:** MEDIUM
**All Providers**
**Issue:** Minimal error handling, no retry mechanism

**Missing:**

- Rate limit handling (HTTP 429)
- Network timeout retry
- Partial sync recovery
- Transaction rollback on failure

#### Gap 7: Pagination Edge Cases

**Severity:** LOW
**Files:** `hostaway.py`, `lodgify.py`, `hostify.py`
**Issue:** Assumed pagination works but no validation

**Hostaway:** Offset-based (Line 90-114)
**Lodgify:** Cursor-based (Line 87-112)
**Hostify:** Offset-based (Line 64-81)

**Missing:**

- Max limit enforcement
- Infinite loop prevention
- Empty result handling (already done)

#### Gap 8: iCal Feed Credentials

**Severity:** MEDIUM
**File:** `ical.py`
**Issue:** No support for authenticated iCal feeds

**Current:** Only public URLs
**Missing:**

- HTTP Basic Auth support
- Query parameter auth
- Bearer token support

---

### 6.2 Configuration Dependencies

**Dependency Chain:**

```
Agent-Zero Process
    ↓
Tool Execution (pms_hub_tool.py)
    ↓
Registry (provider_registry.py)
    ├─ Load: ~/.pms_hub/providers.json
    ├─ Parse: ProviderConfig objects
    └─ Cache: provider instances
    ↓
Create Provider (providers/__init__.py:create_provider)
    ├─ Get credentials dict
    ├─ Instantiate: HostawayProvider(config)
    ├─ Authenticate: await provider.authenticate()
    └─ Return: authenticated provider
    ↓
Use Provider (hostaway.py, etc.)
    ├─ Make API calls with headers
    ├─ Transform responses
    └─ Return canonical models
```

**Dependency Issues:**

1. **Configuration File Missing**
   - If `~/.pms_hub/providers.json` doesn't exist
   - Registry creates empty providers dict
   - All operations fail with "provider not found"

2. **Credentials Missing from Config**
   - Configuration exists but credentials empty
   - Provider instantiation succeeds
   - Authentication fails
   - Error: "Failed to authenticate with {provider_type}"

3. **PropertyManager Missing**
   - Sync service imports PropertyManager
   - If ImportError occurs (module not found)
   - Silently disabled with warning
   - Sync operations return False

---

## PART 7: FILE LOCATIONS & INTER-FILE DEPENDENCIES

### 7.1 Directory Structure

```
instruments/custom/pms_hub/
├── __init__.py                 # Package initialization
├── canonical_models.py         # Data models (Reservation, Property, etc.)
├── pms_provider.py            # Abstract base class
├── provider_registry.py        # Configuration management
├── sync_service.py            # PMS ↔ PropertyManager sync
└── providers/
    ├── __init__.py            # Factory function
    ├── hostaway.py            # Hostaway adapter
    ├── lodgify.py             # Lodgify adapter
    ├── hostify.py             # Hostify adapter
    └── ical.py                # iCal adapter

python/api/
├── pms_webhook_receive.py     # Webhook endpoint
├── pms_settings_get.py        # Configuration GET
└── pms_settings_set.py        # Configuration POST

python/tools/
└── pms_hub_tool.py            # Agent-zero tool interface

python/helpers/
└── event_bus.py               # Event emission and storage
```

### 7.2 Import Dependencies

```
pms_hub_tool.py
    ├─ imports: pms_hub.provider_registry
    ├─ imports: pms_hub.sync_service
    ├─ imports: pms_hub.pms_provider.ProviderType
    ├─ calls: registry.get_provider_async()
    ├─ calls: sync.sync_all_reservations()
    └─ returns: Response objects

sync_service.py
    ├─ imports: pms_hub.canonical_models
    ├─ imports: pms_hub.provider_registry
    ├─ imports: property_manager (optional)
    ├─ calls: registry.get_provider_async()
    ├─ calls: provider.get_property()
    ├─ calls: provider.get_reservations()
    └─ calls: self.pm.add_property() [PropertyManager]

provider_registry.py
    ├─ imports: pms_hub.pms_provider.ProviderType
    ├─ imports: pms_hub.providers.create_provider
    ├─ reads: ~/.pms_hub/providers.json
    ├─ writes: ~/.pms_hub/providers.json
    └─ caches: provider instances

providers/__init__.py (factory)
    ├─ imports: .hostaway.HostawayProvider
    ├─ imports: .lodgify.LodgifyProvider
    ├─ imports: .hostify.HostifyProvider
    ├─ imports: .ical.ICalProvider
    └─ calls: provider.authenticate()

hostaway.py (provider adapter)
    ├─ imports: pms_hub.pms_provider.PMSProvider
    ├─ imports: pms_hub.canonical_models.*
    ├─ inherits: PMSProvider
    ├─ uses: httpx.AsyncClient
    ├─ implements: authenticate(), get_reservations(), etc.
    └─ transforms: API responses → canonical models

lodgify.py (provider adapter)
    ├─ (same as hostaway, plus:)
    ├─ imports: hmac, hashlib
    └─ implements: verify_webhook() [HMAC-SHA256]

pms_webhook_receive.py
    ├─ imports: pms_hub.provider_registry
    ├─ imports: event_bus.EventBus, EventStore
    ├─ calls: registry.get_provider_config()
    ├─ calls: registry.get_provider_async()
    ├─ calls: provider.verify_webhook()
    ├─ calls: event_bus.emit()
    └─ reads: ~/.pms_hub/events.db [EventStore]

event_bus.py
    ├─ imports: audit.hash_event
    ├─ stores: SQLite events database
    ├─ emits: events to subscribers
    └─ writes: ~/.pms_hub/events.db

pms_settings_get.py
    ├─ imports: pms_hub.provider_registry
    ├─ calls: registry.list_providers()
    ├─ calls: registry.get_provider_config()
    └─ returns: provider metadata (no credentials)

pms_settings_set.py
    ├─ imports: pms_hub.provider_registry
    ├─ imports: pms_hub.pms_provider.ProviderType
    ├─ calls: registry.register_provider()
    ├─ calls: registry.update_provider_config()
    ├─ calls: registry.unregister_provider()
    └─ writes: ~/.pms_hub/providers.json
```

### 7.3 Data Flow Between Files

```
Configuration Path:
pms_settings_set.py
    → registry.register_provider()
    → ~/.pms_hub/providers.json (write)
    → pms_hub_tool.py reads it
    → registry.get_provider_async()
    → providers/__init__.py:create_provider()
    → hostaway.py authenticated instance

Webhook Path:
External Webhook
    → pms_webhook_receive.py
    → registry.get_provider_config()
    → hostaway.py:verify_webhook()
    → event_bus.emit()
    → ~/.pms_hub/events.db (write)
    → (no subscribers currently)

Sync Path:
pms_hub_tool.py:_sync_reservations()
    → registry.get_provider_async()
    → hostaway.py:get_reservations()
    → sync_service.py:sync_reservation_to_property_manager()
    → property_manager API calls
```

---

## PART 8: AUTHENTICATION SEQUENCE DIAGRAMS

### 8.1 Hostaway Authentication & API Call

```
┌─────────────┐           ┌──────────────────────┐      ┌──────────────────┐
│ Agent/Tool  │           │ HostawayProvider     │      │ Hostaway API     │
└─────────────┘           └──────────────────────┘      └──────────────────┘
      │                            │                              │
      ├─ execute(action="get_reservations") ──>
      │                            │
      │  ┌─ _get_reservations() ──>
      │  │                         │
      │  │  ┌─ _get_headers() ────>
      │  │  │                      │
      │  │  │  return {
      │  │  │    "Authorization": "Bearer {access_token}",
      │  │  │    "Content-Type": "application/json"
      │  │  │  }
      │  │  <──────────────────────
      │  │
      │  │  ┌─ GET /v1/reservations ──────────────>
      │  │  │  Headers: Authorization: Bearer {token}
      │  │  │  Query: limit=100, offset=0
      │  │  │
      │  │  │                                  ┌─ Validate Bearer token
      │  │  │                                  ├─ Check user permissions
      │  │  │                                  └─ Return reservations
      │  │  │
      │  │  <───────────── 200 OK ────────────
      │  │  │  {
      │  │  │    "result": {
      │  │  │      "reservations": [...]
      │  │  │    }
      │  │  │  }
      │  │
      │  │  ┌─ _transform_reservation() ────>
      │  │  │  Convert to canonical Reservation
      │  │  <──────────────────────
      │  │
      │  │  return [Reservation, ...]
      │  <──────────────────────
      │
      <── Response(status="success", reservations=[...])
```

### 8.2 Lodgify Webhook Verification & Processing

```
┌──────────────────┐     ┌─────────────────────┐     ┌───────────────┐
│ Lodgify Service  │     │ pms_webhook_receive │     │ LodgifyProv   │
└──────────────────┘     └─────────────────────┘     └───────────────┘
      │                          │                           │
      │  POST /api/pms/webhook   │                           │
      │  /lodgify/main           │                           │
      ├─────────────────────────>│                           │
      │  Headers:                │                           │
      │    X-Signature: abc123.. │                           │
      │  Body:                   │                           │
      │    {                     │                           │
      │      "event": "...       │                           │
      │      "data": {...}       │                           │
      │    }                     │                           │
      │                          │                           │
      │                          ├─ Get config ────────────>│
      │                          │  (find registry entry)
      │                          <─────────────────────────
      │                          │  ProviderConfig with
      │                          │  api_secret
      │                          │
      │                          ├─ verify_webhook() ──────>│
      │                          │  payload, signature
      │                          │
      │                          │  payload_str = json.dumps(
      │                          │    payload, sorted_keys
      │                          │  )
      │                          │  expected = hmac_sha256(
      │                          │    api_secret,
      │                          │    payload_str
      │                          │  ).hexdigest()
      │                          │
      │                          │  compare_digest(
      │                          │    signature,
      │                          │    expected
      │                          │  )
      │                          <─────────────────────────
      │                          │  True (valid signature)
      │                          │
      │                          ├─ event_bus.emit() ──────>
      │                          │  "pms.webhook.lodgify.x"
      │                          │
      │                          │  ├─ Store in events.db
      │                          │  └─ Call handlers (none)
      │                          <──────────────────────────
      │                          │
      │  <───────────────────────┤
      │  200 OK
      │  {
      │    "status": "success",
      │    "event_id": 42
      │  }
```

### 8.3 iCal Feed Authentication

```
┌──────────────────┐     ┌──────────────────────┐     ┌─────────────┐
│ Airbnb/VRBO      │     │ ICalProvider         │     │ HTTP Client │
└──────────────────┘     └──────────────────────┘     └─────────────┘
      │                          │                           │
      │  ical_url =              │                           │
      │  https://airbnb.com/     │                           │
      │  calendar/abc123         │                           │
      │                          │                           │
      │                          ├─ authenticate() ────────>│
      │                          │
      │                          ├─ GET {ical_url} ────────>│
      │                          │  follow_redirects=True
      │                          │
      │                          │<───────────────────────
      │                          │   200 OK
      │                          │   (iCal content)
      │                          │
      │                          ├─ parse iCal ────────────>│
      │                          │  icalendar.Calendar
      │                          │    .from_ical()
      │                          │
      │                          │<───────────────────────
      │                          │   Calendar object
      │                          │
      │                          ├─ Walk VEVENT components ─>
      │                          │
      │                          ├─ Extract dates ───────────>
      │                          │  dtstart → Calendar.date
      │                          │
      │                          ├─ Create Calendar objects ─>
      │                          │  status="booked"
      │                          │
      │                          <── return [Calendar, ...]
```

---

## PART 9: SUMMARY OF IMPLEMENTATION STATUS

### Complete Implementations

- ✅ Provider adapter interface (PMSProvider abstract class)
- ✅ Hostaway API integration (full CRUD)
- ✅ Lodgify API integration (full CRUD)
- ✅ Hostify API integration (full CRUD)
- ✅ iCal feed parsing (calendar only)
- ✅ Provider Registry (JSON file-based)
- ✅ Provider factory (create_provider)
- ✅ API endpoints (webhook, settings GET/SET)
- ✅ EventBus with event storage
- ✅ PropertyManager sync (PMS → PropertyManager)
- ✅ Canonical data models
- ✅ PMSHub tool for agent-jumbo

### Partial/Incomplete Implementations

- 🟡 Webhook verification (only Lodgify fully implemented)
- 🟡 Webhook event processing (events emitted, no handlers)
- 🟡 Credential storage (plaintext JSON, no encryption)
- 🟡 Error handling (minimal, no retry)
- 🟡 Rate limiting (none implemented)

### Missing Implementations

- ❌ Token refresh mechanism
- ❌ Reverse sync (PropertyManager → PMS)
- ❌ Hostaway webhook signature verification
- ❌ Hostify webhook signature verification
- ❌ iCal feed authentication support
- ❌ Webhook event subscribers
- ❌ Partial sync recovery
- ❌ Credential encryption

---

## RECOMMENDATIONS

### Priority 1: Security (CRITICAL)

1. Implement webhook signature verification for Hostaway and Hostify
2. Add credential encryption at rest
3. Implement webhook event handlers for automatic sync
4. Validate webhook origins

### Priority 2: Reliability (HIGH)

1. Implement token refresh mechanism
2. Add comprehensive error handling and retry logic
3. Implement rate limiting detection
4. Add transaction rollback on sync failure

### Priority 3: Features (MEDIUM)

1. Implement reverse sync (PropertyManager → PMS)
2. Add iCal feed authentication support
3. Implement webhook signature validation for all providers
4. Add comprehensive logging

### Priority 4: Operations (LOW)

1. Add monitoring and alerting
2. Implement health checks
3. Add performance metrics
4. Create admin dashboard

---

## TESTING COVERAGE ASSESSMENT

**Existing Tests:**

- ✅ test_pms_providers.py - Unit tests for adapters
- ✅ test_pms_registry.py - Registry tests
- ✅ test_pms_sync_service.py - Sync service tests
- ✅ test_pms_canonical_models.py - Model validation

**Missing Tests:**

- ❌ Webhook signature verification (end-to-end)
- ❌ Webhook event handling
- ❌ Token refresh flows
- ❌ Error conditions (network failures, auth failures)
- ❌ Sync service with property_manager
- ❌ API endpoint integration tests

---

END OF ANALYSIS
