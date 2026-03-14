# Continue TDD Swarm Development - Team Guidance

**Status**: Infrastructure complete, foundation established, ready to scale
**Teams**: Team A (active), Team B (ready to start)
**Execution Model**: TDD (Test-Driven Development)

---

## 🚀 For Team A: Calendar Hub Integration (CONTINUE FROM HERE)

### Your Current Position

✅ **Completed**:

- CalendarSyncService class created
- Event sync method implemented
- Calendar formatting methods working
- 8 tests passing (TestCalendarSyncServiceInitialization + 2 from TestCalendarEventCreation)
- EventBus integration working
- Error handling established

⏳ **Next**:

- Complete remaining 4 tests in TestCalendarEventCreation
- Implement TestCalendarEventUpdates (4 tests)
- Implement TestBlockedDatesSync (5 tests)
- Total: 55 tests pending

### Step-by-Step Continuation

#### Step 1: See Current Status

```bash
cd /home/webemo-aaron/projects/agent-jumbo

# Run current tests
pytest tests/test_pms_calendar_sync.py -v

# You should see:
# - 8 passed ✅
# - 55 skipped (pending)
```

#### Step 2: Continue with Next Tests

**For each remaining test class:**

```python
# 1. Open the test file
nano tests/test_pms_calendar_sync.py

# 2. Find the test class (e.g., TestCalendarEventUpdates)
# 3. Replace pytest.skip() with actual test code
# 4. Implement the test assertions

# Example:
@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_event_on_status_change(self, sample_reservation):
    """Test updating event when reservation status changes"""
    from instruments.custom.pms_hub.calendar_sync import CalendarSyncService
    from unittest.mock import patch

    service = CalendarSyncService()

    # Your test implementation here
    # ...assert statements...
```

#### Step 3: Add Implementation Methods

When tests require new methods in CalendarSyncService:

```python
# In instruments/custom/pms_hub/calendar_sync.py
# Add methods like:

async def update_calendar_event(self, event_id: str, updates: Dict) -> bool:
    """Update existing calendar event with new data"""
    # Implementation

async def delete_calendar_event(self, event_id: str) -> bool:
    """Delete calendar event when reservation cancelled"""
    # Implementation

def _calculate_pricing_adjustments(self, reservation: Reservation) -> Decimal:
    """Calculate dynamic pricing adjustments"""
    # Implementation
```

#### Step 4: Run Tests and Iterate

```bash
# Run your specific test class
pytest tests/test_pms_calendar_sync.py::TestCalendarEventUpdates -v

# See failures (RED)
# Add implementation code
# Run again (GREEN) ✅

# Run full calendar sync tests
pytest tests/test_pms_calendar_sync.py -v

# Commit progress
git add instruments/custom/pms_hub/calendar_sync.py tests/test_pms_calendar_sync.py
git commit -m "feat(calendar): implement event updates with 4 tests"
```

### Recommended Schedule for Team A

```
Day 1 (Today):
├─ Review this guidance (30 min)
├─ Review current implementation (30 min)
├─ Continue with TestCalendarEventUpdates (2-3 hours)
└─ Stop at 18:00

Day 2:
├─ Implement TestCalendarEventDeletion (1-2 hours)
├─ Implement TestMultiCalendarAccounts (2 hours)
├─ Implement TestBlockedDatesSync (2 hours)
└─ Git commits for each section

Day 3:
├─ Implement TestMinStayRequirements (1-2 hours)
├─ Implement TestOverlappingReservations (1-2 hours)
├─ Implement TestDynamicPricingRules (2-3 hours)
└─ Review code, ensure 95%+ coverage

Day 4:
├─ Implement TestCalendarHubIntegration (2-3 hours)
├─ Implement TestBatchSynchronization (1-2 hours)
├─ Implement TestSyncStatusReporting (1 hour)
├─ Performance and error handling optimization
└─ Code review

Day 5:
├─ Final test implementation (TestEventBusIntegration, TestPerformance)
├─ Ensure all 45+ tests passing
├─ Final refactoring and documentation
├─ Merge to main
└─ Celebrate! 🎉
```

### Success Metrics for Team A

Complete by Day 5:

- ✅ 45+ tests passing (100%)
- ✅ >95% code coverage
- ✅ All methods implemented
- ✅ EventBus integration working
- ✅ Calendar Hub tool integration working
- ✅ Dynamic pricing rules implemented
- ✅ Availability blocking implemented
- ✅ All documentation updated
- ✅ Ready for merge

---

## 🚀 For Team B: Guest Communication Automation (READY TO START)

### Your Starting Position

✅ **Prepared**:

- 53 test placeholders written
- Test organization complete
- Test specifications documented
- Example patterns available from Team A
- All infrastructure ready

⏳ **Your task**:

- Implement CommunicationWorkflow class
- Implement MessageTemplate system
- Write and implement 53 tests
- Create API endpoints
- Integrate with PMS Hub

### How to Get Started

#### Step 1: Review Examples

```bash
# Understand the pattern from Team A
cat instruments/custom/pms_hub/calendar_sync.py | head -100

# Review test structure from Team A
cat tests/test_pms_calendar_sync.py | head -50

# Review available fixtures
cat tests/conftest.py | grep "@pytest.fixture"
```

#### Step 2: Create Your Implementation File

```bash
# Start your workflow service
cat > instruments/custom/pms_hub/communication_workflows.py << 'EOF'
"""
Guest Communication Automation Workflows
Manages pre-arrival, post-checkout, issue resolution, and review workflows
"""

import sys
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass

# Add imports path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .canonical_models import Reservation, Guest
from .provider_registry import ProviderRegistry


@dataclass
class MessageTemplate:
    """Template for guest communication messages"""
    id: str
    name: str
    channel: str  # 'sms', 'email', 'platform_message'
    subject: str = ""
    body: str = ""
    variables: List[str] = None
    language: str = "en"


class CommunicationWorkflow:
    """
    Manages guest communication workflows
    Coordinates pre-arrival, post-checkout, issues, and reviews
    """

    def __init__(self):
        """Initialize communication workflow service"""
        self.registry = ProviderRegistry()

        # Import event bus
        try:
            from python.helpers.event_bus import EventBus, EventStore
            import tempfile

            temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
            event_store = EventStore(temp_db.name)
            self.event_bus = EventBus(event_store)
        except (ImportError, Exception) as e:
            print(f"Warning: EventBus not available: {e}")
            self.event_bus = None

    async def trigger_pre_arrival_workflow(self, reservation: Reservation) -> Optional[Dict]:
        """Trigger pre-arrival messaging workflow (48 hours before check-in)"""
        # TODO: Implement
        pass

    async def trigger_post_checkout_workflow(self, reservation: Reservation) -> Optional[Dict]:
        """Trigger post-checkout messaging workflow"""
        # TODO: Implement
        pass

    async def trigger_issue_workflow(self, issue_type: str, reservation: Reservation) -> Optional[Dict]:
        """Trigger issue resolution workflow"""
        # TODO: Implement
        pass


if __name__ == "__main__":
    print("Communication workflow module loaded")
EOF
```

#### Step 3: Start with Initialization Tests

```bash
# Update your test file with first implementation
# Replace pytest.skip() in TestCommunicationWorkflowInitialization

nano tests/test_pms_communication_workflows.py

# Replace:
# pytest.skip("Implementation pending - Team B to implement")

# With actual test code:
def test_workflow_service_creation(self):
    """Test creating communication workflow service"""
    from instruments.custom.pms_hub.communication_workflows import CommunicationWorkflow

    service = CommunicationWorkflow()
    assert service is not None
    assert hasattr(service, "registry")
    assert hasattr(service, "event_bus")
```

#### Step 4: Run and Iterate

```bash
# cd to your worktree
cd /home/webemo-aaron/projects/agent-jumbo/.worktrees/pms-messaging

# Run initialization tests
pytest tests/test_pms_communication_workflows.py::TestCommunicationWorkflowInitialization -v

# Should see same pattern as Team A:
# RED (failures) → fix implementation → GREEN (passing)

# Continue with next test class
pytest tests/test_pms_communication_workflows.py::TestPreArrivalWorkflows -v

# Iterate until all tests in class pass
```

### Recommended Schedule for Team B

```
Day 1 (Tomorrow after Team A starts):
├─ Review guidance and Team A patterns (1-2 hours)
├─ Create communication_workflows.py file (30 min)
├─ Implement TestCommunicationWorkflowInitialization (1-2 hours)
└─ Get first 2-3 tests passing ✅

Day 2:
├─ Implement TestPreArrivalWorkflows (2-3 hours)
├─ Implement TestPostCheckoutWorkflows (2-3 hours)
├─ Start TestMessageTemplates (1-2 hours)
└─ Commit progress

Day 3:
├─ Complete TestMessageTemplates (1-2 hours)
├─ Implement TestMultiChannelDelivery (2-3 hours)
├─ Implement TestReviewManagement (1-2 hours)
└─ Code quality check

Day 4:
├─ Implement TestIssueResolutionWorkflows (2-3 hours)
├─ Implement TestWorkflowTriggers (1-2 hours)
├─ Implement TestWorkflowErrorHandling (1-2 hours)
├─ Add API endpoints (1-2 hours)
└─ Integration testing

Day 5:
├─ Final test implementation (remaining classes)
├─ Ensure all 53+ tests passing
├─ Performance and edge cases
├─ Documentation completion
├─ Merge preparation
└─ Celebrate! 🎉
```

### Success Metrics for Team B

Complete by Day 5:

- ✅ 53+ tests passing (100%)
- ✅ >95% code coverage
- ✅ All workflow types implemented
- ✅ Multi-channel delivery working
- ✅ Template system complete
- ✅ Issue resolution workflows working
- ✅ Review automation implemented
- ✅ EventBus integration working
- ✅ All documentation updated
- ✅ Ready for merge

---

## 🔄 Parallel Development Tips

### For Both Teams

#### Daily Sync (5 minutes)

```
09:00 - Daily standup
├─ How many tests passed today?
├─ What blockers came up?
├─ Any patterns to share?
└─ Any help needed?
```

#### Code Pattern Sharing

- Team A: Share patterns as you discover them
- Team B: Ask questions about Team A's patterns
- Both: Use each other's code as reference

#### Branch Management

```bash
# Team A
git status
git branch  # Should be: feature/pms-calendar-sync

# Team B
git status
git branch  # Should be: feature/pms-messaging-automation

# Never merge to main until Day 5!
# Keep features isolated
```

#### Handling Conflicts

- Test in your feature branch first
- Only merge when tests pass 100%
- Merge to main only on Day 5
- If conflicts, resolve together with architecture review

---

## 📊 Progress Tracking

### Team A Checklist

```
Day 1:
- [ ] Review current implementation
- [ ] Implement 3-4 more test classes (12+ tests)
- [ ] Commit progress
- [ ] Daily standup

Day 2:
- [ ] Implement 4-5 test classes (15+ tests)
- [ ] Total: 20+ tests passing
- [ ] Code coverage check
- [ ] Commit progress
- [ ] Daily standup

Day 3:
- [ ] Implement 3-4 test classes (10+ tests)
- [ ] Total: 30+ tests passing
- [ ] Refactor for quality
- [ ] Commit progress
- [ ] Daily standup

Day 4:
- [ ] Implement remaining core tests (10+ tests)
- [ ] Total: 40+ tests passing
- [ ] Performance optimization
- [ ] Commit progress
- [ ] Daily standup

Day 5:
- [ ] Finalize all tests (5+ tests)
- [ ] Total: 45+ tests passing
- [ ] Full test suite validation
- [ ] Documentation complete
- [ ] Ready for merge
- [ ] Celebration
```

### Team B Checklist

```
Day 1 (Start after Team A):
- [ ] Review Team A patterns
- [ ] Create communication_workflows.py
- [ ] Implement initialization tests (2+ tests)
- [ ] Daily standup

Day 2:
- [ ] Implement workflow tests (15+ tests)
- [ ] Create template system
- [ ] Commit progress
- [ ] Daily standup

Day 3:
- [ ] Implement template and delivery tests (15+ tests)
- [ ] Create API endpoints
- [ ] Commit progress
- [ ] Daily standup

Day 4:
- [ ] Implement issue and review workflows (15+ tests)
- [ ] Integration testing
- [ ] Commit progress
- [ ] Daily standup

Day 5:
- [ ] Finalize remaining tests
- [ ] All 53+ tests passing
- [ ] Full test suite validation
- [ ] Documentation complete
- [ ] Ready for merge
- [ ] Celebration
```

---

## 🎯 Key Principles to Remember

### TDD Approach

1. **RED**: Write test, see it fail
2. **GREEN**: Write minimal code to pass test
3. **REFACTOR**: Clean up code while keeping tests green

### Code Quality

- Type hints on all methods
- Docstrings on all public methods
- Error handling in all I/O operations
- >95% code coverage target

### Git Workflow

- Commit frequently (every test class)
- Use clear commit messages
- Reference test counts in messages
- Push to origin regularly

### Testing Strategy

- Use fixtures from conftest.py
- Mock external services
- Test both success and failure paths
- Async tests with @pytest.mark.asyncio

---

## 💡 Resources Available

### Code References

- `instruments/custom/pms_hub/calendar_sync.py` - Working example
- `instruments/custom/pms_hub/sync_service.py` - Another example
- `tests/test_pms_calendar_sync.py` - Test structure reference

### Documentation

- `TDD_SWARM_GUIDE.md` - Testing patterns
- `TDD_SWARM_EXECUTION_STATUS.md` - Current progress
- `TDD_SWARM_FEATURE_TEAMS.md` - Detailed specifications
- `TEAM_QUICKSTART.md` - Quick reference

### Fixtures

- `tests/conftest.py` - All available fixtures
- `sample_reservation` - Pre-configured test data
- `sample_property` - Property test data
- `event_bus` - EventBus with temp storage

---

## ✅ Quality Checklist

Before each commit, verify:

- [ ] All tests in current class passing (100%)
- [ ] New code has docstrings
- [ ] New code has type hints
- [ ] Error handling in place
- [ ] Code formatted (ruff)
- [ ] No import errors
- [ ] Fixtures being used correctly

---

## 🚀 You Are Ready

**Team A**: Continue from 8 passing tests to 45+
**Team B**: Start with initialization and build systematically

Both teams have:
✅ Clear test specifications
✅ Working examples to follow
✅ Proper infrastructure setup
✅ Documentation and guidance
✅ Test fixtures ready
✅ Timeline and milestones

**Let's build great features using TDD!**

---

**Questions?** Check:

1. TDD_SWARM_EXECUTION_STATUS.md (current progress)
2. Test examples in test_pms_*.py files
3. Implementation reference in calendar_sync.py
4. Fixture documentation in conftest.py

**Ready to code?** 🎉
