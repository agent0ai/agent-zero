# PMS Hub TDD Swarm - Feature Team Parallel Development Plan

## 🎯 Mission Overview

Implement two major feature enhancements using **parallel TDD Swarm teams** with isolated git worktrees:

| Team | Feature | Scope | Duration | Status |
|------|---------|-------|----------|--------|
| **Team A: Calendar** | Calendar Hub Integration + Dynamic Pricing | Feature | Parallel | Ready |
| **Team B: Messaging** | Guest Communication Automation | Feature | Parallel | Ready |

---

## 📋 Team A: Calendar Hub Integration

### Feature Scope

- Sync PMS calendar availability to Google/Outlook calendars
- Dynamic pricing rule synchronization to calendar events
- Availability blocking management (min stay, cleaning days)
- Real-time calendar updates when reservations change

### Implementation Files

#### New Files to Create

```
instruments/custom/pms_hub/calendar_sync.py          # Calendar sync service
python/tools/pms_calendar_sync.py                    # Calendar sync tool
python/api/pms_calendar_sync.py                      # Calendar sync API
tests/test_pms_calendar_sync.py                      # 25+ tests
tests/test_pms_calendar_pricing.py                   # 20+ tests
```

#### Integration Points

```
PMS Reservation → Canonical Model → Calendar Sync Service
    ↓
EventBus (pms.reservation.*)
    ↓
Calendar Hub Manager → Google Calendar API
    ↓
Store pricing rules as calendar event metadata
```

### Test Suite Specification

#### Test Category 1: Calendar Sync Service (15 tests)

```python
class TestCalendarSyncService:
    - test_sync_service_initialization
    - test_create_calendar_event_from_reservation
    - test_update_calendar_event_on_status_change
    - test_delete_calendar_event_on_cancellation
    - test_handle_multiple_calendar_accounts
    - test_sync_blocked_days
    - test_sync_min_stay_requirements
    - test_handle_overlapping_reservations
    - test_calendar_event_metadata_storage
    - test_pricing_rule_in_event_description
    - test_handle_calendar_api_errors
    - test_batch_sync_reservations
    - test_sync_status_reporting
    - test_event_deduplication
    - test_calendar_sync_audit_trail
```

#### Test Category 2: Dynamic Pricing Rules (12 tests)

```python
class TestDynamicPricingRules:
    - test_apply_percentage_adjustment
    - test_apply_absolute_adjustment
    - test_seasonal_pricing_rules
    - test_occupancy_based_pricing
    - test_advance_booking_discount
    - test_last_minute_premium
    - test_multiple_rules_stacking
    - test_rule_priority_ordering
    - test_rule_date_range_validation
    - test_update_calendar_prices
    - test_pricing_rule_export
    - test_pricing_rule_import
```

#### Test Category 3: Availability Blocking (8 tests)

```python
class TestAvailabilityBlocking:
    - test_create_blocked_dates
    - test_mark_cleaning_days
    - test_maintenance_blocks
    - test_block_weekdays_only
    - test_recurring_blocks
    - test_remove_blocks
    - test_block_conflict_detection
    - test_block_export_to_pms
```

#### Test Category 4: Calendar Hub Integration (10 tests)

```python
class TestCalendarHubIntegration:
    - test_calendar_hub_connection
    - test_sync_to_google_calendar
    - test_sync_to_outlook_calendar
    - test_create_multiple_calendars
    - test_calendar_color_coding_status
    - test_event_description_formatting
    - test_attendee_management (guests)
    - test_calendar_permissions
    - test_handle_calendar_auth_failures
    - test_bi_directional_sync_updates
```

### Key Implementation Details

**Calendar Sync Service (`instruments/custom/pms_hub/calendar_sync.py`)**

```python
class CalendarSyncService:
    async def sync_reservation_to_calendar(reservation: Reservation) -> bool
    async def sync_blocked_dates(property_id: str, blocked_dates: List[date]) -> bool
    async def update_pricing_in_event(calendar_event_id: str, pricing: PricingRule) -> bool
    async def handle_reservation_status_change(reservation: Reservation) -> bool
    async def batch_sync_property_calendar(property_id: str) -> Tuple[int, int]
    def _format_event_description(reservation: Reservation) -> str
    def _extract_pricing_rules(event_description: str) -> List[PricingRule]
```

**EventBus Subscribers**

```python
# In sync_service.py __init__
self.event_bus.subscribe("pms.reservation.created", self._on_reservation_created)
self.event_bus.subscribe("pms.reservation.updated", self._on_reservation_updated)
self.event_bus.subscribe("pms.reservation.cancelled", self._on_reservation_cancelled)
self.event_bus.subscribe("pms.pricing_rule.updated", self._on_pricing_updated)
```

---

## 🗣️ Team B: Guest Communication Automation

### Feature Scope

- Pre-arrival messages (check-in instructions, house rules)
- Post-checkout messages (thank you, review requests)
- Automated review requests with templates
- Issue resolution workflows (damage, noise, cleanliness)
- Multi-channel support (SMS, email, messaging platform)

### Implementation Files

#### New Files to Create

```
instruments/custom/pms_hub/communication_workflows.py # Workflow engine
python/tools/pms_communication.py                     # Communication tool
python/api/pms_communication_send.py                  # Send API
python/api/pms_communication_templates.py             # Templates API
tests/test_pms_communication_workflows.py             # 25+ tests
tests/test_pms_message_templates.py                   # 20+ tests
```

#### Integration Points

```
PMS Reservation Event → Workflow Trigger
    ↓
Communication Service → Message Template Rendering
    ↓
Multi-channel Gateway (SMS/Email/Messaging)
    ↓
Delivery Status Tracking → EventBus
```

### Test Suite Specification

#### Test Category 1: Workflow Engine (15 tests)

```python
class TestCommunicationWorkflows:
    - test_workflow_initialization
    - test_create_pre_arrival_workflow
    - test_create_post_checkout_workflow
    - test_create_issue_workflow
    - test_workflow_trigger_on_reservation_created
    - test_workflow_trigger_on_check_in
    - test_workflow_trigger_on_check_out
    - test_workflow_conditional_execution
    - test_workflow_delay_scheduling
    - test_workflow_cancellation
    - test_multi_step_workflows
    - test_workflow_error_handling
    - test_workflow_status_tracking
    - test_workflow_audit_trail
    - test_workflow_performance_load
```

#### Test Category 2: Message Templates (12 tests)

```python
class TestMessageTemplates:
    - test_load_template
    - test_render_template_variables
    - test_personalization_tokens
    - test_guest_language_selection
    - test_property_specific_templates
    - test_template_validation
    - test_template_import_export
    - test_conditional_template_sections
    - test_template_formatting
    - test_template_character_limits (SMS)
    - test_template_html_email_formatting
    - test_template_attachments
```

#### Test Category 3: Multi-Channel Delivery (10 tests)

```python
class TestMultiChannelDelivery:
    - test_send_via_sms
    - test_send_via_email
    - test_send_via_platform_messaging
    - test_delivery_status_tracking
    - test_failure_retry_logic
    - test_do_not_disturb_hours
    - test_opt_out_handling
    - test_delivery_confirmation
    - test_channel_routing_logic
    - test_throttle_rate_limiting
```

#### Test Category 4: Issue Resolution (10 tests)

```python
class TestIssueResolution:
    - test_damage_report_workflow
    - test_noise_complaint_workflow
    - test_cleanliness_issue_workflow
    - test_guest_communication_escalation
    - test_host_notification
    - test_resolution_tracking
    - test_issue_resolution_closure
    - test_automatic_compensation_offers
    - test_issue_documentation
    - test_resolution_workflow_statistics
```

#### Test Category 5: Review Management (8 tests)

```python
class TestReviewManagement:
    - test_review_request_timing
    - test_review_template_rendering
    - test_review_collection_tracking
    - test_review_response_handling
    - test_public_review_management
    - test_private_feedback_collection
    - test_review_analytics
    - test_review_incentive_management
```

### Key Implementation Details

**Communication Workflows (`instruments/custom/pms_hub/communication_workflows.py`)**

```python
class CommunicationWorkflow:
    async def trigger_pre_arrival_workflow(reservation: Reservation) -> WorkflowExecution
    async def trigger_post_checkout_workflow(reservation: Reservation) -> WorkflowExecution
    async def trigger_issue_workflow(issue_type: str, reservation: Reservation) -> WorkflowExecution
    async def send_message(recipient: Guest, template: MessageTemplate) -> MessageDelivery
    async def schedule_delayed_message(recipient: Guest, delay_hours: int, template: MessageTemplate)
    def render_template(template: MessageTemplate, context: dict) -> str
    async def get_delivery_status(message_id: str) -> DeliveryStatus
```

**Message Template Model**

```python
@dataclass
class MessageTemplate:
    id: str
    name: str
    channel: str  # 'sms', 'email', 'platform_message'
    subject: str  # Email only
    body: str
    variables: List[str]  # e.g., ['guest_name', 'check_in_time', 'house_rules_url']
    language: str
    min_chars: int
    max_chars: int
    requires_approval: bool
```

**EventBus Integration**

```python
self.event_bus.subscribe("pms.reservation.created", self._on_pre_arrival_trigger)
self.event_bus.subscribe("pms.reservation.checked_in", self._on_check_in_trigger)
self.event_bus.subscribe("pms.reservation.checked_out", self._on_post_checkout_trigger)
self.event_bus.subscribe("pms.issue.reported", self._on_issue_reported)
```

---

## 🔧 Team Structure & Workflow

### Development Process

```
Sprint Timeline:
├── Day 1: Setup & Test Writing (TDD)
│   ├── Create feature branch + worktree
│   ├── Write comprehensive test suite
│   ├── Create fixtures and mocks
│   └── Verify tests fail (red phase)
│
├── Days 2-3: Implementation (TDD)
│   ├── Implement features to pass tests
│   ├── Achieve 100% test pass rate
│   ├── Code review within team
│   └── Performance validation
│
├── Day 4: Integration Testing
│   ├── Test EventBus integration
│   ├── Test PropertyManager sync
│   ├── Test API endpoints
│   └── Error scenario validation
│
└── Day 5: Merge & Validation
    ├── Merge to main branch
    ├── Run full test suite
    ├── Document changes
    └── Create deployment checklist
```

### Parallel Execution

**Terminal 1 - Team A (Calendar)**

```bash
cd /home/webemo-aaron/projects/agent-jumbo/.worktrees/pms-calendar
# Create tests, implement, iterate
./scripts/run_pms_tests.sh calendar
```

**Terminal 2 - Team B (Messaging)**

```bash
cd /home/webemo-aaron/projects/agent-jumbo/.worktrees/pms-messaging
# Create tests, implement, iterate
./scripts/run_pms_tests.sh messaging
```

**Terminal 3 - Main (Integration)**

```bash
cd /home/webemo-aaron/projects/agent-jumbo
# Monitor changes, prepare merge strategy
git log --oneline
```

---

## 📊 Success Criteria

### Team A: Calendar Hub Integration

- ✅ 45+ tests written and passing
- ✅ 95%+ code coverage
- ✅ EventBus integration working
- ✅ Google Calendar sync validated
- ✅ Dynamic pricing rules applied
- ✅ Performance: <500ms per event sync

### Team B: Guest Communication Automation

- ✅ 53+ tests written and passing
- ✅ 95%+ code coverage
- ✅ All workflow types implemented
- ✅ Multi-channel delivery working
- ✅ Template rendering validated
- ✅ Performance: <1s per message send

### Overall

- ✅ Zero conflicts on merge
- ✅ Full test suite passes (100+ existing + 100+ new)
- ✅ Documentation updated
- ✅ Zero security vulnerabilities
- ✅ No performance regressions

---

## 🚀 Merge Strategy

### Pre-Merge Checklist (Each Team)

```
Feature Branch: feature/pms-calendar-sync
├── [ ] All tests passing (local)
├── [ ] 95%+ code coverage
├── [ ] No linting errors (ruff)
├── [ ] Type checking passes (mypy)
├── [ ] Documentation updated
├── [ ] No sensitive data in commits
└── [ ] Rebased on main (no conflicts)

Feature Branch: feature/pms-messaging-automation
├── [ ] All tests passing (local)
├── [ ] 95%+ code coverage
├── [ ] No linting errors (ruff)
├── [ ] Type checking passes (mypy)
├── [ ] Documentation updated
├── [ ] No sensitive data in commits
└── [ ] Rebased on main (no conflicts)
```

### Merge Order

1. **Team A** → Main (Calendar Hub Integration)
2. **Team B** → Main (Guest Communication Automation)
3. **Merge validation** - Run full test suite
4. **Documentation** - Update README and API docs
5. **Tag release** - Create v2.0.0 tag

---

## 📁 Worktree Structure

```
.worktrees/
├── pms-calendar/
│   ├── instruments/custom/pms_hub/calendar_sync.py
│   ├── python/tools/pms_calendar_sync.py
│   ├── python/api/pms_calendar_sync.py
│   ├── tests/
│   │   ├── test_pms_calendar_sync.py (25 tests)
│   │   ├── test_pms_calendar_pricing.py (20 tests)
│   │   ├── test_pms_calendar_availability.py (8 tests)
│   │   └── test_pms_calendar_hub_integration.py (10 tests)
│   └── [all shared files...]
│
└── pms-messaging/
    ├── instruments/custom/pms_hub/communication_workflows.py
    ├── python/tools/pms_communication.py
    ├── python/api/pms_communication_send.py
    ├── python/api/pms_communication_templates.py
    ├── tests/
    │   ├── test_pms_communication_workflows.py (15 tests)
    │   ├── test_pms_message_templates.py (12 tests)
    │   ├── test_pms_multi_channel.py (10 tests)
    │   ├── test_pms_issue_resolution.py (10 tests)
    │   └── test_pms_review_management.py (8 tests)
    └── [all shared files...]
```

---

## 🎓 Learning Outcomes

### Architecture Patterns

- Event-driven architecture with EventBus
- Service-oriented design (Calendar Sync, Communication Services)
- Plugin-based template system
- Workflow engine patterns

### TDD Best Practices

- Test-first development
- Fixture reuse across teams
- Parallel development coordination
- Git worktree workflow

### Integration Testing

- Multi-service integration validation
- EventBus event flow testing
- API endpoint integration testing
- External service mocking (Google Calendar, SMS providers)

---

## 📞 Support & Communication

### Team Sync Points

- **Daily**: Team status check
- **End of Day**: Merge conflict resolution if needed
- **Day 5**: Joint validation and merge ceremony

### Documentation

- Update `/home/webemo-aaron/projects/agent-jumbo/README.md` with new features
- Add API documentation for new endpoints
- Create troubleshooting guide for new workflows

---

**Status**: Ready for team assignment and execution
**Complexity**: High (100+ new tests, 6 new files, significant integration)
**Risk**: Low (isolated worktrees, comprehensive testing, clear merge strategy)
**Timeline**: 5 working days with parallel execution
