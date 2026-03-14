# PMS Hub Feature Teams - Quick Start Guide

## 🚀 Getting Started (5 minutes)

### Prerequisites

- Git configured locally
- Python 3.11+ installed
- Virtual environment activated
- Dependencies installed: `pip install -e .`

---

## 📌 Team A: Calendar Hub Integration

### Workspace Setup

```bash
# Your worktree is automatically created at:
cd /home/webemo-aaron/projects/agent-jumbo/.worktrees/pms-calendar

# Verify you're on the correct branch
git branch  # Should show: feature/pms-calendar-sync
```

### Test-Driven Development Approach

**Phase 1: Understand Requirements**

1. Read: `TDD_SWARM_FEATURE_TEAMS.md` (Calendar section)
2. Read: `README.md` for calendar_hub API
3. Study: `instruments/custom/pms_hub/canonical_models.py` (Property, Reservation, Calendar)

**Phase 2: Write Failing Tests**

```bash
cd /home/webemo-aaron/projects/agent-jumbo/.worktrees/pms-calendar

# Open test file
nano tests/test_pms_calendar_sync.py

# Implement first test (replace pytest.skip with actual test)
# Start with TestCalendarSyncServiceInitialization::test_calendar_sync_service_creation

# Run tests to see them fail (RED phase)
pytest tests/test_pms_calendar_sync.py::TestCalendarSyncServiceInitialization::test_calendar_sync_service_creation -v
```

**Phase 3: Implement Features**
Create these files:

```
instruments/custom/pms_hub/calendar_sync.py
    - CalendarSyncService class
    - sync_reservation_to_calendar() method
    - sync_blocked_dates() method
    - update_pricing_in_event() method

python/tools/pms_calendar_sync.py
    - CalendarSync tool integration

python/api/pms_calendar_sync.py
    - API endpoint handlers
```

**Phase 4: Run Tests**

```bash
# Run all calendar sync tests
pytest tests/test_pms_calendar_sync.py -v

# Run with coverage
pytest tests/test_pms_calendar_sync.py --cov=instruments.custom.pms_hub.calendar_sync --cov-report=html

# Run specific test class
pytest tests/test_pms_calendar_sync.py::TestCalendarEventCreation -v
```

**Phase 5: Code Review & Merge**

```bash
# Commit your changes
git add -A
git commit -m "feat(calendar): implement calendar sync service with 45+ tests"

# Push to feature branch
git push origin feature/pms-calendar-sync

# Create Pull Request via GitHub
# Merge when all tests pass (98%+ coverage)
```

### Key Files to Work With

| File | Purpose | Status |
|------|---------|--------|
| `instruments/custom/pms_hub/calendar_sync.py` | Main implementation | Create |
| `tests/test_pms_calendar_sync.py` | Test suite (45+ tests) | ✓ Created |
| `python/tools/pms_calendar_sync.py` | Tool integration | Create |
| `python/api/pms_calendar_sync.py` | API endpoints | Create |

### Integration Points

- **EventBus**: Subscribe to `pms.reservation.*` events
- **Calendar Hub**: Use `CalendarHubManager` for Google/Outlook sync
- **PMS Hub Registry**: Use `ProviderRegistry` to get providers
- **Canonical Models**: Transform to/from PMS data models

### Success Metrics

- ✅ 45+ tests passing (100%)
- ✅ 95%+ code coverage
- ✅ All integration tests passing
- ✅ Performance: <500ms per sync
- ✅ Zero merge conflicts

---

## 🗣️ Team B: Guest Communication Automation

### Workspace Setup

```bash
# Your worktree is automatically created at:
cd /home/webemo-aaron/projects/agent-jumbo/.worktrees/pms-messaging

# Verify you're on the correct branch
git branch  # Should show: feature/pms-messaging-automation
```

### Test-Driven Development Approach

**Phase 1: Understand Requirements**

1. Read: `TDD_SWARM_FEATURE_TEAMS.md` (Messaging section)
2. Study: `instruments/custom/pms_hub/canonical_models.py` (Message, Guest, Reservation)
3. Review: Multi-channel delivery patterns in related tools

**Phase 2: Write Failing Tests**

```bash
cd /home/webemo-aaron/projects/agent-jumbo/.worktrees/pms-messaging

# Open test file
nano tests/test_pms_communication_workflows.py

# Implement first test (replace pytest.skip with actual test)
# Start with TestCommunicationWorkflowInitialization::test_workflow_service_creation

# Run tests to see them fail (RED phase)
pytest tests/test_pms_communication_workflows.py::TestCommunicationWorkflowInitialization::test_workflow_service_creation -v
```

**Phase 3: Implement Features**
Create these files:

```
instruments/custom/pms_hub/communication_workflows.py
    - CommunicationWorkflow class
    - trigger_pre_arrival_workflow() method
    - trigger_post_checkout_workflow() method
    - trigger_issue_workflow() method
    - send_message() method

instruments/custom/pms_hub/message_templates.py
    - MessageTemplate dataclass
    - TemplateEngine class
    - render_template() method

python/tools/pms_communication.py
    - Communication tool integration

python/api/pms_communication_send.py
    - Send message API endpoint

python/api/pms_communication_templates.py
    - Template management API
```

**Phase 4: Run Tests**

```bash
# Run all communication tests
pytest tests/test_pms_communication_workflows.py -v

# Run with coverage
pytest tests/test_pms_communication_workflows.py --cov=instruments.custom.pms_hub.communication_workflows --cov-report=html

# Run specific test class
pytest tests/test_pms_communication_workflows.py::TestPreArrivalWorkflows -v

# Run with detailed output
pytest tests/test_pms_communication_workflows.py::TestMultiChannelDelivery -vv
```

**Phase 5: Code Review & Merge**

```bash
# Commit your changes
git add -A
git commit -m "feat(messaging): implement guest communication workflows with 53+ tests"

# Push to feature branch
git push origin feature/pms-messaging-automation

# Create Pull Request via GitHub
# Merge when all tests pass (95%+ coverage)
```

### Key Files to Work With

| File | Purpose | Status |
|------|---------|--------|
| `instruments/custom/pms_hub/communication_workflows.py` | Workflow engine | Create |
| `instruments/custom/pms_hub/message_templates.py` | Template system | Create |
| `tests/test_pms_communication_workflows.py` | Test suite (53+ tests) | ✓ Created |
| `python/tools/pms_communication.py` | Tool integration | Create |
| `python/api/pms_communication_send.py` | Send API | Create |
| `python/api/pms_communication_templates.py` | Template API | Create |

### Integration Points

- **EventBus**: Subscribe to `pms.reservation.*` and `pms.issue.*` events
- **Template Engine**: Render dynamic templates with variables
- **Multi-channel Gateway**: Send via SMS, Email, Platform Messaging
- **Delivery Tracking**: Monitor message delivery status
- **Canonical Models**: Use Message, Guest, Reservation models

### Success Metrics

- ✅ 53+ tests passing (100%)
- ✅ 95%+ code coverage
- ✅ All workflow types implemented
- ✅ Multi-channel delivery working
- ✅ Zero merge conflicts

---

## 🔄 Parallel Development Workflow

### During Development (Days 1-4)

**Terminal 1: Team A (Calendar)**

```bash
cd /home/webemo-aaron/projects/agent-jumbo/.worktrees/pms-calendar
# Implement tests → features → iterate
pytest tests/test_pms_calendar_sync.py -v --tb=short
```

**Terminal 2: Team B (Messaging)**

```bash
cd /home/webemo-aaron/projects/agent-jumbo/.worktrees/pms-messaging
# Implement tests → features → iterate
pytest tests/test_pms_communication_workflows.py -v --tb=short
```

**Terminal 3: Monitor/Integration**

```bash
cd /home/webemo-aaron/projects/agent-jumbo
# Run full test suite periodically
pytest tests/ -v --tb=short
```

### Communication Checkpoints

- **Daily**: Quick sync on test coverage and blockers
- **End of Day 2**: Share progress updates
- **End of Day 4**: Final validation before merge

---

## 📋 Common Commands

### Setup

```bash
# Initialize worktrees
./scripts/setup_feature_teams.sh create

# List active worktrees
./scripts/setup_feature_teams.sh list

# Clean up worktrees
./scripts/setup_feature_teams.sh clean
```

### Development

```bash
# Run your team's tests
pytest tests/test_pms_calendar_sync.py -v
pytest tests/test_pms_communication_workflows.py -v

# Run with coverage
pytest --cov=instruments.custom.pms_hub --cov-report=html

# Run specific test
pytest tests/test_pms_calendar_sync.py::TestCalendarEventCreation::test_create_event_from_reservation -v

# Run tests matching pattern
pytest tests/test_pms_*.py -k "EventBus" -v
```

### Git

```bash
# Check your branch
git branch

# Stage changes
git add instruments/custom/pms_hub/calendar_sync.py tests/

# Commit
git commit -m "feat(calendar): add calendar sync implementation"

# Push
git push origin feature/pms-calendar-sync

# View commits
git log --oneline --graph -n 10
```

### Testing

```bash
# Run linting
ruff check instruments/custom/pms_hub/

# Format code
ruff format instruments/custom/pms_hub/

# Type checking (if using mypy)
mypy instruments/custom/pms_hub/calendar_sync.py

# Full test suite
pytest tests/test_pms_*.py -v --tb=short

# Performance test
pytest tests/test_pms_*.py -v --durations=10
```

---

## 🆘 Troubleshooting

### Tests Not Finding Modules

```bash
# Ensure you're in the worktree root
cd /home/webemo-aaron/projects/agent-jumbo/.worktrees/pms-calendar

# Install in development mode
pip install -e .

# Run with PYTHONPATH
export PYTHONPATH=/home/webemo-aaron/projects/agent-jumbo:$PYTHONPATH
pytest tests/test_pms_calendar_sync.py -v
```

### Import Errors

```bash
# Make sure all files are created
ls instruments/custom/pms_hub/calendar_sync.py  # Should exist

# Check imports in your file
head -20 instruments/custom/pms_hub/calendar_sync.py
```

### Git Conflicts

```bash
# Check status
git status

# Abort merge
git merge --abort

# Rebase on main
git rebase origin/main

# Force push (use carefully!)
git push origin feature/pms-calendar-sync --force-with-lease
```

### EventBus Issues

```bash
# Check EventBus is available
python -c "from python.helpers.event_bus import EventBus; print('EventBus OK')"

# Check subscription
python -c "
from instruments.custom.pms_hub.sync_service import PMSSyncService
sync = PMSSyncService()
print(sync.event_bus.subscribers)
"
```

---

## 📚 Reference Documentation

### Architecture

- `/home/webemo-aaron/projects/agent-jumbo/PMS_HUB_IMPLEMENTATION.md`
- `/home/webemo-aaron/projects/agent-jumbo/TDD_SWARM_FEATURE_TEAMS.md`

### API Reference

- `/home/webemo-aaron/projects/agent-jumbo/instruments/custom/pms_hub/README.md`
- Calendar Hub: `python/tools/calendar_hub.py` (line 23-100)

### Testing

- `/home/webemo-aaron/projects/agent-jumbo/TDD_SWARM_GUIDE.md`
- Example tests: `tests/test_pms_providers.py`

### Canonical Models

- `/home/webemo-aaron/projects/agent-jumbo/instruments/custom/pms_hub/canonical_models.py`

---

## ✅ Pre-Merge Checklist

Before creating a Pull Request:

- [ ] All tests passing locally
- [ ] 95%+ code coverage achieved
- [ ] Linting passes: `ruff check .`
- [ ] Code formatted: `ruff format .`
- [ ] No import errors
- [ ] EventBus integration working
- [ ] API endpoints tested
- [ ] Documentation updated
- [ ] No sensitive data in commits
- [ ] Rebased on main: `git rebase origin/main`
- [ ] Ready for code review

---

## 🎯 Success Definition

### Team A: Calendar Hub Integration

**Deliverables**:

- Calendar sync service with 45+ tests
- Dynamic pricing rule synchronization
- Availability blocking management
- Google/Outlook calendar integration
- EventBus event handling

**Quality Gate**:

- 100% test pass rate
- 95%+ code coverage
- <500ms per sync operation
- Zero security issues

### Team B: Guest Communication Automation

**Deliverables**:

- Communication workflow engine with 53+ tests
- Pre-arrival workflow implementation
- Post-checkout workflow implementation
- Issue resolution workflows
- Multi-channel message delivery

**Quality Gate**:

- 100% test pass rate
- 95%+ code coverage
- <1s per message send
- Zero security issues

---

**Good luck, teams! 🚀**

For questions or blockers, check the reference documentation or reach out to the project lead.
