# PMS Hub Feature Teams - Deployment & Execution Plan

## 🚀 Status: Ready for Team Execution

**Date**: 2026-01-17
**Phase**: Feature Development - Parallel TDD Swarm
**Teams**: 2 (Calendar Hub, Guest Communication)
**Duration**: 5 working days (estimated)
**Status**: ✅ Infrastructure Ready for Teams

---

## 📊 Project Structure

```
/home/webemo-aaron/projects/agent-jumbo
├── Main Branch (main)
│   ├── [Core PMS Hub System] ✓ Complete
│   ├── [TDD Test Infrastructure] ✓ Complete
│   ├── [4 Provider Adapters] ✓ Complete
│   └── [Sync Service] ✓ Complete
│
├── Team A Worktree (.worktrees/pms-calendar)
│   ├── feature/pms-calendar-sync branch
│   ├── tests/test_pms_calendar_sync.py (45+ test specs)
│   ├── tests/test_pms_calendar_pricing.py (20+ test specs)
│   ├── tests/test_pms_calendar_availability.py (8+ test specs)
│   └── tests/test_pms_calendar_hub_integration.py (10+ test specs)
│
└── Team B Worktree (.worktrees/pms-messaging)
    ├── feature/pms-messaging-automation branch
    ├── tests/test_pms_communication_workflows.py (53+ test specs)
    ├── tests/test_pms_message_templates.py (20+ test specs)
    ├── tests/test_pms_multi_channel.py (10+ test specs)
    ├── tests/test_pms_issue_resolution.py (10+ test specs)
    └── tests/test_pms_review_management.py (8+ test specs)
```

---

## 🎯 Team A: Calendar Hub Integration

### Worktree Location

```bash
/home/webemo-aaron/projects/agent-jumbo/.worktrees/pms-calendar
```

### Git Branch

```
feature/pms-calendar-sync (created at commit b0417ed)
```

### Objectives (Complete in 5 Days)

**Day 1: Setup & Test Writing (TDD Red Phase)**

- [ ] Read documentation (TDD_SWARM_FEATURE_TEAMS.md, TEAM_QUICKSTART.md)
- [ ] Understand calendar_hub API and canonical models
- [ ] Implement first 15 test cases (failing/skipped)
- [ ] Set up CalendarSyncService class structure
- [ ] Verify pytest can discover and run tests

**Day 2: Core Implementation (TDD Green Phase)**

- [ ] Implement CalendarSyncService.**init**()
- [ ] Implement sync_reservation_to_calendar()
- [ ] Implement sync_blocked_dates()
- [ ] Pass first 20 tests
- [ ] Add EventBus integration

**Day 3: Advanced Features (TDD Refactor Phase)**

- [ ] Implement dynamic pricing rule sync
- [ ] Implement availability blocking logic
- [ ] Implement multi-calendar support
- [ ] Pass 35+ tests
- [ ] Code coverage >90%

**Day 4: Integration & Testing (Quality Assurance)**

- [ ] Integrate with calendar_hub tool
- [ ] Implement error handling
- [ ] Add performance optimizations
- [ ] Pass 45+ tests (100%)
- [ ] Code coverage >95%

**Day 5: Merge & Validation (Production Readiness)**

- [ ] Final code review
- [ ] Run full test suite with main branch
- [ ] Resolve any conflicts
- [ ] Merge to main
- [ ] Tag release

### Files to Implement

```python
# instruments/custom/pms_hub/calendar_sync.py (300-400 lines)
class CalendarSyncService:
    async def sync_reservation_to_calendar(reservation: Reservation) -> bool
    async def sync_blocked_dates(property_id: str, dates: List[date]) -> bool
    async def update_pricing_in_event(event_id: str, pricing: PricingRule) -> bool
    async def handle_reservation_status_change(reservation: Reservation) -> bool
    async def batch_sync_property_calendar(property_id: str) -> Tuple[int, int]
    def _format_event_description(reservation: Reservation) -> str
    def _extract_pricing_rules(event_description: str) -> List[PricingRule]

# python/tools/pms_calendar_sync.py (100-150 lines)
class CalendarSync(Tool):
    async def execute(self, **kwargs) -> Response
    # Actions: connect_calendar, sync_property, sync_pricing, status

# python/api/pms_calendar_sync.py (150-200 lines)
class PMSCalendarSync(APIHandler):
    async def POST_sync_property()
    async def POST_sync_blocked_dates()
    async def GET_sync_status()
```

### Success Criteria

- ✅ 45+ tests implemented and passing (100%)
- ✅ 95%+ code coverage for calendar_sync.py
- ✅ EventBus integration working
- ✅ Google/Outlook calendar sync validated
- ✅ Performance: <500ms per event sync
- ✅ Zero merge conflicts
- ✅ Documentation updated
- ✅ Ready for production deployment

### Test Execution Commands

```bash
# Navigate to Team A worktree
cd /home/webemo-aaron/projects/agent-jumbo/.worktrees/pms-calendar

# Run all calendar sync tests
pytest tests/test_pms_calendar_sync.py -v

# Run with coverage report
pytest tests/test_pms_calendar_*.py --cov=instruments.custom.pms_hub.calendar_sync --cov-report=html

# Run specific test class
pytest tests/test_pms_calendar_sync.py::TestCalendarEventCreation -v

# Run tests by marker
pytest tests/test_pms_calendar_*.py -m asyncio -v
```

---

## 🗣️ Team B: Guest Communication Automation

### Worktree Location

```bash
/home/webemo-aaron/projects/agent-jumbo/.worktrees/pms-messaging
```

### Git Branch

```
feature/pms-messaging-automation (created at commit b0417ed)
```

### Objectives (Complete in 5 Days)

**Day 1: Setup & Test Writing (TDD Red Phase)**

- [ ] Read documentation (TDD_SWARM_FEATURE_TEAMS.md, TEAM_QUICKSTART.md)
- [ ] Understand message templates and workflows
- [ ] Implement first 15 test cases (failing/skipped)
- [ ] Set up CommunicationWorkflow class structure
- [ ] Set up MessageTemplate dataclass
- [ ] Verify pytest can discover and run tests

**Day 2: Core Implementation (TDD Green Phase)**

- [ ] Implement CommunicationWorkflow.**init**()
- [ ] Implement trigger_pre_arrival_workflow()
- [ ] Implement trigger_post_checkout_workflow()
- [ ] Implement MessageTemplate system
- [ ] Pass first 20 tests
- [ ] Add EventBus integration

**Day 3: Advanced Features (TDD Refactor Phase)**

- [ ] Implement trigger_issue_workflow()
- [ ] Implement multi-channel delivery (SMS, Email, Messaging)
- [ ] Implement template rendering
- [ ] Implement review request workflow
- [ ] Pass 40+ tests
- [ ] Code coverage >90%

**Day 4: Integration & Testing (Quality Assurance)**

- [ ] Implement error handling and retries
- [ ] Integrate with PMS tools
- [ ] Implement delivery status tracking
- [ ] Add performance optimizations
- [ ] Pass 53+ tests (100%)
- [ ] Code coverage >95%

**Day 5: Merge & Validation (Production Readiness)**

- [ ] Final code review
- [ ] Run full test suite with main branch
- [ ] Resolve any conflicts
- [ ] Merge to main
- [ ] Tag release

### Files to Implement

```python
# instruments/custom/pms_hub/communication_workflows.py (400-500 lines)
class CommunicationWorkflow:
    async def trigger_pre_arrival_workflow(reservation: Reservation) -> WorkflowExecution
    async def trigger_post_checkout_workflow(reservation: Reservation) -> WorkflowExecution
    async def trigger_issue_workflow(issue_type: str, reservation: Reservation) -> WorkflowExecution
    async def send_message(recipient: Guest, template: MessageTemplate) -> MessageDelivery
    async def schedule_delayed_message(recipient, delay_hours, template)
    def render_template(template: MessageTemplate, context: dict) -> str
    async def get_delivery_status(message_id: str) -> DeliveryStatus

# instruments/custom/pms_hub/message_templates.py (150-200 lines)
@dataclass
class MessageTemplate:
    id: str
    name: str
    channel: str  # 'sms', 'email', 'platform_message'
    subject: str
    body: str
    variables: List[str]
    language: str

class TemplateEngine:
    def render(template: MessageTemplate, context: dict) -> str
    def validate(template: MessageTemplate) -> bool

# python/tools/pms_communication.py (150-200 lines)
class Communication(Tool):
    async def execute(self, **kwargs) -> Response
    # Actions: send_message, list_templates, get_status

# python/api/pms_communication_send.py (150-200 lines)
# python/api/pms_communication_templates.py (150-200 lines)
```

### Success Criteria

- ✅ 53+ tests implemented and passing (100%)
- ✅ 95%+ code coverage for communication_workflows.py
- ✅ EventBus integration working
- ✅ All workflow types (pre-arrival, post-checkout, issues, reviews) working
- ✅ Multi-channel delivery validated
- ✅ Performance: <1s per message send
- ✅ Zero merge conflicts
- ✅ Documentation updated
- ✅ Ready for production deployment

### Test Execution Commands

```bash
# Navigate to Team B worktree
cd /home/webemo-aaron/projects/agent-jumbo/.worktrees/pms-messaging

# Run all communication tests
pytest tests/test_pms_communication_workflows.py -v

# Run with coverage report
pytest tests/test_pms_communication_*.py --cov=instruments.custom.pms_hub.communication_workflows --cov-report=html

# Run specific test class
pytest tests/test_pms_communication_workflows.py::TestPreArrivalWorkflows -v

# Run tests by type
pytest tests/test_pms_communication_*.py -m asyncio -v
```

---

## 🔄 Parallel Execution Timeline

### Day 1: Setup & Analysis

```
09:00 - Team Setup & Documentation Review
10:00 - Test Suite Planning
11:00 - Test Writing (Red Phase)
14:00 - First Test Runs (Expected to Fail)
16:00 - EOD Sync - Quick Status Check
```

### Days 2-3: Implementation

```
09:00 - Implementation (Green Phase)
11:00 - Test Status Check
13:00 - Lunch Break
14:00 - Continue Implementation
16:00 - Code Review & Refactoring
17:00 - EOD Sync - Coverage & Blockers
```

### Day 4: Integration

```
09:00 - Integration Testing
11:00 - Error Handling & Edge Cases
13:00 - Lunch Break
14:00 - Performance Optimization
16:00 - Final Testing
17:00 - EOD Sync - Merge Preparation
```

### Day 5: Merge & Validation

```
09:00 - Final Code Review
10:00 - Conflict Resolution (if needed)
11:00 - Merge to Main
12:00 - Full Test Suite Validation
13:00 - Documentation Updates
14:00 - Release Tagging
15:00 - Celebration 🎉
```

---

## 📋 Daily Sync Checklist

### Each Team Reports

- [ ] Tests implemented since yesterday
- [ ] Tests passing count vs. target
- [ ] Major blockers or issues
- [ ] Code coverage percentage
- [ ] Expected completion status
- [ ] Resource needs

### Questions for the Group

- Are any shared services needed?
- Are there integration points we need to coordinate?
- Any dependencies blocking progress?
- Do we need to adjust the timeline?

---

## ✅ Pre-Merge Validation Checklist

### Code Quality

- [ ] Linting passes: `ruff check instruments/custom/pms_hub/`
- [ ] Formatting correct: `ruff format .`
- [ ] Type checking: `mypy instruments/custom/pms_hub/`
- [ ] No import errors
- [ ] All docstrings present

### Testing

- [ ] All new tests passing (100%)
- [ ] Code coverage >95%
- [ ] Integration tests passing
- [ ] EventBus tests passing
- [ ] Performance tests passing
- [ ] Edge cases tested

### Documentation

- [ ] README updated with new features
- [ ] API documentation added
- [ ] Implementation guide created
- [ ] Examples provided
- [ ] Troubleshooting guide added

### Git Hygiene

- [ ] Rebased on main
- [ ] No merge conflicts
- [ ] Clean commit history
- [ ] Meaningful commit messages
- [ ] No sensitive data in commits

### Integration

- [ ] Full test suite passes with main
- [ ] No regressions in existing tests
- [ ] EventBus integration working
- [ ] Tool integration working
- [ ] API endpoints working

---

## 🚨 Critical Paths & Dependencies

### Team A → Team B Dependencies

- Team B's message delivery system can be used by Team A to notify about calendar updates
- Team A's pricing rules can be exposed through Team B's messages
- Both teams depend on EventBus being available

### Main Branch Dependencies

- Both teams depend on existing PMS Hub infrastructure
- Both teams must maintain backwards compatibility
- No breaking changes to canonical models allowed

### External Dependencies

- Calendar Hub tool (already implemented)
- EventBus system (already implemented)
- PropertyManager tool (for context, not required)

---

## 🎯 Success Metrics

### Code Coverage

```
Baseline (Main Branch): ~98%
Target (After Features): >98% overall
  - Team A: >95% calendar_sync.py
  - Team B: >95% communication_workflows.py
```

### Test Coverage

```
Baseline: 91 tests (from PMS Hub)
Additions: 100+ new tests
  - Team A: 45+ tests
  - Team B: 53+ tests
Target: 200+ tests total passing
```

### Performance

```
Team A: <500ms per calendar event sync
Team B: <1s per message send
Integration: <2s for full sync cycle
```

### Quality Gate

```
✅ 100% test pass rate
✅ >95% code coverage
✅ Zero security issues
✅ Zero merge conflicts
✅ Deployment ready
```

---

## 📞 Communication Channels

### Synchronous

- **Daily Standup**: 09:00 (5 minutes)
- **Team Breakouts**: As needed
- **Project Lead**: Available for blockers

### Asynchronous

- **GitHub**: Issues, PRs, discussions
- **Commit Messages**: Detailed context
- **Documentation**: Technical decisions

### Escalation Path

1. Team Lead (whoever is available)
2. Project Lead
3. Technical Architecture Review

---

## 📚 Reference Documentation

### For All Teams

- `/home/webemo-aaron/projects/agent-jumbo/TDD_SWARM_FEATURE_TEAMS.md` - Comprehensive feature specs
- `/home/webemo-aaron/projects/agent-jumbo/TEAM_QUICKSTART.md` - Quick start guide
- `/home/webemo-aaron/projects/agent-jumbo/TDD_SWARM_GUIDE.md` - Testing guide

### Team A (Calendar)

- `/home/webemo-aaron/projects/agent-jumbo/python/tools/calendar_hub.py` - Calendar API reference
- `/home/webemo-aaron/projects/agent-jumbo/instruments/custom/pms_hub/README.md` - PMS Hub API

### Team B (Messaging)

- Canonical models: `/home/webemo-aaron/projects/agent-jumbo/instruments/custom/pms_hub/canonical_models.py`
- Sync service: `/home/webemo-aaron/projects/agent-jumbo/instruments/custom/pms_hub/sync_service.py`

### Testing

- Existing tests: `/home/webemo-aaron/projects/agent-jumbo/tests/test_pms_*.py`
- Conftest: `/home/webemo-aaron/projects/agent-jumbo/tests/conftest.py`

---

## 🔧 Commands Quick Reference

### Worktree Navigation

```bash
# Team A
cd /home/webemo-aaron/projects/agent-jumbo/.worktrees/pms-calendar

# Team B
cd /home/webemo-aaron/projects/agent-jumbo/.worktrees/pms-messaging

# Main
cd /home/webemo-aaron/projects/agent-jumbo
```

### Git Branch Management

```bash
# Check current branch
git branch

# View all branches
git branch -a

# Switch branches
git checkout feature/pms-calendar-sync

# View branch log
git log --oneline -n 10
```

### Testing

```bash
# Run team's tests
pytest tests/test_pms_calendar_*.py -v
pytest tests/test_pms_communication_*.py -v

# Run with coverage
pytest --cov=instruments.custom.pms_hub --cov-report=html

# Run full suite
pytest tests/test_pms_*.py -v
```

### Git Operations

```bash
# Stage changes
git add instruments/custom/pms_hub/ tests/ python/

# Commit
git commit -m "feat(calendar): implement calendar sync"

# Push
git push origin feature/pms-calendar-sync

# Rebase
git rebase origin/main
```

---

## 📊 Expected Deliverables

### Team A: Calendar Hub Integration

```
New Files:
- instruments/custom/pms_hub/calendar_sync.py (350 lines)
- python/tools/pms_calendar_sync.py (120 lines)
- python/api/pms_calendar_sync.py (180 lines)
- tests/test_pms_calendar_sync.py (450 lines, 45+ tests)
- tests/test_pms_calendar_pricing.py (300 lines, 20+ tests)
- tests/test_pms_calendar_availability.py (200 lines, 8+ tests)
- tests/test_pms_calendar_hub_integration.py (250 lines, 10+ tests)

Documentation:
- Updated README with calendar sync features
- API reference for new endpoints
- Integration guide
```

### Team B: Guest Communication Automation

```
New Files:
- instruments/custom/pms_hub/communication_workflows.py (450 lines)
- instruments/custom/pms_hub/message_templates.py (180 lines)
- python/tools/pms_communication.py (150 lines)
- python/api/pms_communication_send.py (180 lines)
- python/api/pms_communication_templates.py (180 lines)
- tests/test_pms_communication_workflows.py (600 lines, 53+ tests)
- tests/test_pms_message_templates.py (350 lines, 20+ tests)
- tests/test_pms_multi_channel.py (250 lines, 10+ tests)
- tests/test_pms_issue_resolution.py (250 lines, 10+ tests)
- tests/test_pms_review_management.py (200 lines, 8+ tests)

Documentation:
- Updated README with messaging features
- API reference for new endpoints
- Workflow templates guide
- Integration guide
```

---

## 🎓 Learning Outcomes

### Architecture Patterns

- Event-driven architecture (EventBus)
- Service-oriented design
- Plugin-based systems (templates)
- Workflow engines
- Multi-channel delivery patterns

### Best Practices

- Test-driven development
- Parallel development with worktrees
- Fixture reuse and composition
- Async/await patterns
- Error handling and recovery

### Integration Patterns

- EventBus subscription and publishing
- API integration (calendar_hub, external services)
- Tool integration with agent-jumbo
- Database operations (SQLite)

---

## ✨ Next Steps After Merge

### Day 6: Post-Launch

1. Monitor for any production issues
2. Collect feedback from users
3. Plan optimization iterations
4. Document lessons learned

### Future Enhancements

1. Calendar conflict detection and resolution
2. Smart message scheduling (optimal send times)
3. AI-powered review response generation
4. Predictive availability forecasting
5. Machine learning-based pricing optimization

---

## 🎉 Ready to Launch

The infrastructure is complete and teams are ready to begin. This comprehensive setup ensures:

✅ Clear objectives and scope for each team
✅ Isolated development with git worktrees
✅ Comprehensive test specifications ready
✅ Parallel execution without conflicts
✅ Professional quality standards enforced
✅ Documentation and knowledge sharing
✅ Production-ready delivery process

**Teams can start immediately with:**

1. Read TEAM_QUICKSTART.md
2. Navigate to your worktree
3. Start implementing tests (TDD Red phase)
4. Begin the 5-day sprint

---

**Good luck, teams! 🚀**

*Questions? Check the reference documentation or reach out to the project lead.*
