# PMS Hub: Complete File Index with Line References

## Core PMS Hub Implementation Files

### Base Classes & Abstract Interfaces

- **`/home/webemo-aaron/projects/agent-jumbo/instruments/custom/pms_hub/pms_provider.py`** (256 lines)
  - `PMSProvider` abstract base class (Line 31-256)
  - `ProviderType` enum (Line 21-29)
  - `authenticate()` abstract method (Line 49-57)
  - `verify_webhook()` default implementation (Line 228-240)
  - All provider interface definitions

### Canonical Data Models

- **`/home/webemo-aaron/projects/agent-jumbo/instruments/custom/pms_hub/canonical_models.py`**
  - `Reservation` model with ReservationStatus enum
  - `Property` model
  - `Unit` model
  - `Guest` model
  - `Message` model with MessageType enum
  - `Review` model
  - `Calendar` model
  - `PaymentStatus` enum

### Provider Registry (Configuration Management)

- **`/home/webemo-aaron/projects/agent-jumbo/instruments/custom/pms_hub/provider_registry.py`** (327 lines)
  - `ProviderConfig` dataclass (Line 15-50)
  - `ProviderRegistry` class (Line 53-327)
    - Config file path: `~/.pms_hub/providers.json` (Line 63)
    - `register_provider()` (Line 94-136)
    - `get_provider_async()` (Line 184-206)
    - `list_providers()` (Line 208-223)
    - `update_provider_config()` (Line 229-271)
    - `_validate_provider()` (Line 273-293)

### Provider Adapters

#### Hostaway Provider

- **`/home/webemo-aaron/projects/agent-jumbo/instruments/custom/pms_hub/providers/hostaway.py`** (645 lines)
  - `HostawayProvider` class (Line 33-645)
  - Configuration (Line 42-55): user_id, api_key, access_token
  - Authentication (Line 57-75): GET /v1/user
  - `_get_headers()` (Line 504-510): Bearer token header construction
  - `get_reservations()` (Line 145-208): Offset-based pagination
  - `get_properties()` (Line 77-119): Property fetching
  - `get_calendar()` (Line 234-275): Calendar fetch
  - `get_messages()` (Line 277-326): Message fetch
  - `send_message()` (Line 328-359): Guest messaging
  - `get_reviews()` (Line 361-411): Review fetch
  - `update_calendar()` (Line 413-444): Calendar update
  - `update_pricing()` (Line 446-484): Price update
  - Data transformation methods (Line 512-636)
  - Webhook events (Line 490-500): 7 supported events
  - **Webhook verification:** NOT IMPLEMENTED (uses default True)

#### Lodgify Provider

- **`/home/webemo-aaron/projects/agent-jumbo/instruments/custom/pms_hub/providers/lodgify.py`** (666 lines)
  - `LodgifyProvider` class (Line 33-666)
  - Configuration (Line 42-52): api_key, api_secret (for webhook), account_id
  - Authentication (Line 54-72): GET /account
  - `_get_headers()` (Line 543-549): Bearer token header
  - `get_reservations()` (Line 143-202): Cursor-based pagination
  - `get_properties()` (Line 74-117): Property fetching
  - `get_calendar()` (Line 228-269): Calendar fetch
  - `get_messages()` (Line 271-322): Message fetch
  - `send_message()` (Line 324-354): Guest messaging
  - `get_reviews()` (Line 356-408): Review fetch
  - `update_calendar()` (Line 410-457): Calendar update (grouped by property)
  - `update_pricing()` (Line 459-497): Price update
  - `verify_webhook()` (Line 513-539): HMAC-SHA256 signature verification
    - JSON normalized with sorted keys (Line 529)
    - `hmac.compare_digest()` for timing-safe comparison (Line 536)
  - Webhook events (Line 503-511): 5 supported events
  - Data transformation methods (Line 541-657)

#### Hostify Provider

- **`/home/webemo-aaron/projects/agent-jumbo/instruments/custom/pms_hub/providers/hostify.py`** (448 lines)
  - `HostifyProvider` class (Line 28-448)
  - Configuration (Line 36-45): api_key, account_id
  - Authentication (Line 47-56): GET /v2/accounts/me
  - `_get_headers()` (Line 351-356): Bearer token header
  - `get_reservations()` (Line 102-142): Offset-based pagination
  - `get_properties()` (Line 58-86): Property fetching
  - `get_calendar()` (Line 158-185): Calendar fetch
  - `get_messages()` (Line 187-222): Message fetch
  - `send_message()` (Line 224-240): Guest messaging
  - `get_reviews()` (Line 242-276): Review fetch
  - `update_calendar()` (Line 278-310): Calendar update
  - `update_pricing()` (Line 312-337): Price update
  - `verify_webhook()`: NOT IMPLEMENTED (uses default True)
  - Webhook events (Line 342-349): 5 supported events
  - Data transformation methods (Line 358-441)

#### iCal Provider

- **`/home/webemo-aaron/projects/agent-jumbo/instruments/custom/pms_hub/providers/ical.py`** (198 lines)
  - `ICalProvider` class (Line 28-198)
  - Configuration (Line 35-45): ical_url, property_id, property_name
  - Authentication (Line 47-58): GET {ical_url} with redirects
  - `get_calendar()` (Line 95-142): Parse iCal feed with icalendar library
    - Extracts VEVENT components (Line 116-137)
    - Filters by date range (Line 122-126)
    - Creates Calendar objects with status="booked" (Line 129-136)
  - **Limitations** (Line 28-33):
    - No credentials support
    - Read-only (update_calendar returns False)
    - No webhook support
    - Calendar synchronization only

#### Provider Factory

- **`/home/webemo-aaron/projects/agent-jumbo/instruments/custom/pms_hub/providers/__init__.py`** (48 lines)
  - `create_provider()` async factory function (Line 10-47)
  - Dispatches on ProviderType (Line 24-40)
  - Authenticates provider before returning (Line 44-45)

### Synchronization Service

- **`/home/webemo-aaron/projects/agent-jumbo/instruments/custom/pms_hub/sync_service.py`** (362 lines)
  - `PMSSyncService` class (Line 19-361)
  - PropertyManager integration (Line 30-39)
  - `sync_reservation_to_property_manager()` (Line 41-94):
    1. `_sync_property()` (Line 96-146): Create property
    2. `_sync_unit()` (Line 148-179): Create unit
    3. `_sync_guest_to_tenant()` (Line 181-212): Create tenant
    4. `_sync_reservation_to_lease()` (Line 214-256): Create lease
    5. `_record_payment()` (Line 258-284): Record payment
  - Status mapping (Line 286-306)
  - `sync_all_reservations()` (Line 308-340): Batch sync
  - `get_sync_status()` (Line 342-361): Status retrieval

---

## API Endpoints

### Webhook Receiver

- **`/home/webemo-aaron/projects/agent-jumbo/python/api/pms_webhook_receive.py`** (142 lines)
  - `PMSWebhookReceive` class (Line 16-142)
  - `process()` async method (Line 36-113):
    - Extract webhook parameters (Line 52-56)
    - Validate provider (Line 58-73)
    - Verify signature (Line 75-81)
    - Emit EventBus event (Line 85-92)
  - `_verify_webhook()` async (Line 115-142): Delegates to provider
  - EventStore initialization (Line 31-34): SQLite at `~/.pms_hub/events.db`
  - **Security Issue:** Accepts unsigned payloads if no signature (Line 131)

### Settings Get Endpoint

- **`/home/webemo-aaron/projects/agent-jumbo/python/api/pms_settings_get.py`** (81 lines)
  - `PMSSettingsGet` class (Line 14-81)
  - `process()` async method (Line 15-80)
  - Returns provider list without credentials (Line 49-50)
  - Specific provider query support (Line 32-40)

### Settings Set Endpoint

- **`/home/webemo-aaron/projects/agent-jumbo/python/api/pms_settings_set.py`** (207 lines)
  - `PMSSettingsSet` class (Line 14-206)
  - `process()` async dispatcher (Line 15-59)
  - `_add_provider()` (Line 61-120): Register new provider
  - `_update_provider()` (Line 122-153): Update config
  - `_remove_provider()` (Line 155-179): Unregister provider
  - `_enable_provider()` (Line 181-206): Toggle enabled status

---

## Agent-Zero Integration

### PMS Hub Tool

- **`/home/webemo-aaron/projects/agent-jumbo/python/tools/pms_hub_tool.py`** (436 lines)
  - `PMSHub` class extending `Tool` (Line 16-436)
  - `execute()` async dispatcher (Line 22-75)
  - `_get_status()` (Line 77-92)
  - `_list_providers()` (Line 94-112)
  - `_register_provider()` (Line 114-164)
  - `_unregister_provider()` (Line 166-187)
  - `_get_reservations()` (Line 189-251)
  - `_get_properties()` (Line 253-296)
  - `_get_calendar()` (Line 298-355)
  - `_send_message()` (Line 357-397)
  - `_sync_reservations()` (Line 399-422)
  - `_get_sync_status()` (Line 424-435)

---

## Event Bus & Auditing

### Event Bus

- **`/home/webemo-aaron/projects/agent-jumbo/python/helpers/event_bus.py`** (99 lines)
  - `EventStore` class (Line 12-75):
    - SQLite database at specified path (Line 13)
    - `_ensure_schema()` (Line 20-32): Creates events table
    - `add_event()` (Line 34-53): Store event with hash
    - `list_events()` (Line 55-75): Query events
  - `EventBus` class (Line 78-98):
    - `subscribe()` (Line 83-84): Register event handler
    - `emit()` (Line 91-98): Emit event and call handlers
  - Event storage: `~/.pms_hub/events.db` (by default)
  - Audit integration: `hash_event()` from `python/helpers/audit.py`

---

## Test Files

### Provider Tests

- **`/home/webemo-aaron/projects/agent-jumbo/tests/test_pms_providers.py`**
  - `TestHostawayProvider`: Authentication, headers, transformation tests
  - `TestLodgifyProvider`: Webhook signature verification tests
  - Provider name and webhook event tests

### Registry Tests

- **`/home/webemo-aaron/projects/agent-jumbo/tests/test_pms_registry.py`**
  - `TestProviderConfig`: Serialization/deserialization tests
  - `TestProviderRegistry`: Load/save/register/unregister tests

### Sync Service Tests

- **`/home/webemo-aaron/projects/agent-jumbo/tests/test_pms_sync_service.py`**
  - `TestSyncServiceInitialization`: Creation tests
  - `TestReservationSync`: Sync flow tests
  - `TestPropertySync`: Property sync tests

### Canonical Models Tests

- **`/home/webemo-aaron/projects/agent-jumbo/tests/test_pms_canonical_models.py`**
  - Model validation and serialization tests

---

## Configuration Files

### Provider Configuration

- **Location:** `~/.pms_hub/providers.json`
- **Format:** JSON with ProviderConfig schema
- **Created by:** `provider_registry.py` line 67
- **Written by:** Registry `_save_config()` method
- **Read by:** Registry `_load_config()` method

### Event Database

- **Location:** `~/.pms_hub/events.db`
- **Format:** SQLite database
- **Schema:** events table with (id, type, payload, event_hash, created_at)
- **Created by:** EventStore `_ensure_schema()` method
- **Used by:** EventBus for event storage and audit

---

## Key Implementation References (Line Numbers)

### Authentication Flows

- Hostaway: `hostaway.py:57-75`
- Lodgify: `lodgify.py:54-72`
- Hostify: `hostify.py:47-56`
- iCal: `ical.py:47-58`

### Webhook Verification

- Lodgify HMAC-SHA256: `lodgify.py:513-539`
- Default (unused): `pms_provider.py:228-240`

### Data Synchronization

- Main sync flow: `sync_service.py:41-94`
- Property sync: `sync_service.py:96-146`
- Tenant sync: `sync_service.py:181-212`
- Lease sync: `sync_service.py:214-256`

### API Endpoints

- Webhook receive: `pms_webhook_receive.py:36-113`
- Settings get: `pms_settings_get.py:15-80`
- Settings set: `pms_settings_set.py:15-59`

### Registry Operations

- Load config: `provider_registry.py:70-79`
- Save config: `provider_registry.py:81-92`
- Get provider: `provider_registry.py:160-182`
- Register: `provider_registry.py:94-136`

---

## Absolute File Paths (Complete List)

```
/home/webemo-aaron/projects/agent-jumbo/instruments/custom/pms_hub/
├── __init__.py
├── pms_provider.py                                 (256 lines)
├── provider_registry.py                            (327 lines)
├── sync_service.py                                 (362 lines)
├── canonical_models.py
└── providers/
    ├── __init__.py                                 (48 lines)
    ├── hostaway.py                                 (645 lines)
    ├── lodgify.py                                  (666 lines)
    ├── hostify.py                                  (448 lines)
    └── ical.py                                     (198 lines)

/home/webemo-aaron/projects/agent-jumbo/python/api/
├── pms_webhook_receive.py                          (142 lines)
├── pms_settings_get.py                             (81 lines)
└── pms_settings_set.py                             (207 lines)

/home/webemo-aaron/projects/agent-jumbo/python/tools/
└── pms_hub_tool.py                                 (436 lines)

/home/webemo-aaron/projects/agent-jumbo/python/helpers/
└── event_bus.py                                    (99 lines)

/home/webemo-aaron/projects/agent-jumbo/tests/
├── test_pms_providers.py
├── test_pms_registry.py
├── test_pms_sync_service.py
└── test_pms_canonical_models.py
```

---

**Total PMS Hub Implementation: ~4,000+ lines of code**
**Configuration Storage: ~/.pms_hub/ (providers.json, events.db)**
**Analysis Documents: PMS_HUB_ANALYSIS.md (1326 lines), PMS_HUB_QUICK_REFERENCE.md, PMS_HUB_FILE_INDEX.md**
