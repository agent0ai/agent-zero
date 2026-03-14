# Phase 4 Technical Deployment Guide

**Last Updated**: 2026-01-17
**Deployment Status**: READY
**Target Commit**: ee1a67c

---

## Quick Start Checklist

- [ ] Verify commit ee1a67c is on main branch
- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Review DEPLOYMENT_READINESS_BRIEF.md
- [ ] Choose deployment strategy (Immediate, Phased, or Hybrid)
- [ ] Execute deployment steps below

---

## Pre-Deployment Verification

### 1. Verify Test Suite Status

```bash
# Run Phase 4 tests only
pytest tests/test_specialist_agent_framework.py \
        tests/test_reasoning_planning_engine.py \
        tests/test_learning_improvement_system.py -v

# Expected: 137/137 PASSED in <1s
```

### 2. Verify Cross-Phase Compatibility

```bash
# Run Phase 3 Google Voice tests with Phase 4 integrated
pytest tests/test_google_voice_system.py -v

# Expected: 35/35 PASSED in ~18s
```

### 3. Verify Code Quality

```bash
# Run linting (should show 0 warnings)
ruff check instruments/custom/specialist_agent_framework \
               instruments/custom/reasoning_planning_engine \
               instruments/custom/learning_improvement_system

# Check documentation completeness
grep -r "TODO\|FIXME\|XXX" instruments/custom/ || echo "No TODOs found"
```

### 4. Verify Performance

```bash
# Performance baseline test
python -m pytest tests/test_specialist_agent_framework.py::TestAgentPerformance -v
python -m pytest tests/test_reasoning_planning_engine.py::TestReasoningPerformance -v
python -m pytest tests/test_learning_improvement_system.py::TestLearningPerformance -v

# All should show: <50ms, <200ms, <100ms respectively
```

---

## Installation & Configuration

### 1. Verify Dependencies

Phase 4 requires these core dependencies (already in requirements):

```python
# Core framework
dataclasses-json  # Data serialization
typing-extensions # Type hints support
pydantic         # Configuration validation

# Testing (for validation)
pytest >= 7.0
pytest-asyncio   # Async test support
pytest-mock      # Mocking support
```

### 2. Environment Configuration

Create or update `.env` with Phase 4 settings:

```bash
# Phase 4 Configuration
PHASE4_ENABLED=true
SPECIALIST_AGENTS_ENABLED=true
REASONING_ENGINE_ENABLED=true
LEARNING_SYSTEM_ENABLED=true

# Agent Configuration
MAX_AGENTS=10
AGENT_INIT_TIMEOUT_MS=100
MESSAGE_QUEUE_SIZE=1000

# Reasoning Configuration
MAX_REASONING_DEPTH=5
REASONING_TIMEOUT_MS=500
CONFIDENCE_THRESHOLD=0.8

# Learning Configuration
LEARNING_BATCH_SIZE=100
PATTERN_THRESHOLD=0.75
DRIFT_THRESHOLD=0.85
```

### 3. Database Initialization

No additional database schema required for Phase 4.
Learning system uses JSON files for experience storage:

```bash
# Create learning data directory
mkdir -p data/learning/experiences
mkdir -p data/learning/patterns
mkdir -p data/learning/adaptations

# Ensure proper permissions
chmod 755 data/learning/*
```

---

## Deployment Strategies

### Strategy A: Immediate Full Deployment

**Timeline**: 1 hour
**Risk**: LOW (all tests passing)
**Best for**: Development/Staging environments

```bash
# 1. Verify all tests pass
pytest tests/ -k "phase4 or google_voice" -v

# 2. Check git status
git status  # Should be clean

# 3. Verify commit is on main
git log --oneline -1  # Should show ee1a67c

# 4. Initialize Phase 4 services
# (Configure agent initialization, reasoning parameters, learning system)

# 5. Start monitoring
# (Check logs for initialization messages)
```

### Strategy B: Canary Deployment (Recommended)

**Timeline**: 1 week
**Risk**: MINIMAL (phased rollout)
**Best for**: Production environments

```bash
# Week 1: Canary Phase (10% traffic)
# ─────────────────────────────────

# Step 1: Deploy Phase 4 to canary environment
# - Deploy ee1a67c to staging
# - Route 10% of requests through Phase 4 agents
# - Monitor: Agent initialization, reasoning accuracy, learning metrics

# Key metrics to monitor
# - Agent init time: <50ms (target)
# - Reasoning chain: <200ms (target)
# - Pattern learning: <100ms (target)
# - Error rate: <0.1%

# Step 2: Validate 1 week of metrics
# - No critical errors
# - Performance within targets
# - Learning system capturing data

# Week 2: Ramp to 50% Traffic
# ─────────────────────────────

# Increase traffic to 50% based on canary metrics
# - Monitor for any degradation
# - Continue collecting performance data
# - Adjust agent configuration if needed

# Week 3: Full Production Deployment
# ───────────────────────────────────

# Deploy Phase 4 to 100% of traffic
# - All agents operational
# - Full monitoring active
# - Learning system at full capacity
```

### Strategy C: Hybrid (Parallel with Phase 5)

**Timeline**: 1 week (Phase 4 canary) + Q3 2026 (Phase 5 dev)
**Risk**: LOW (managed rollout + isolated Phase 5 dev)
**Best for**: Continuous delivery organizations

```bash
# Week 1: Phase 4 Canary Deployment
# (Same as Strategy B Week 1)

# Weeks 2-4: Phase 4 Ramp + Phase 5 Development
# ──────────────────────────────────────────────

# Phase 4 monitoring
# - Increase traffic 10% → 50% → 100%
# - Collect real-world data

# Phase 5 development (separate branch)
# - Create feature/phase5-human-ai-collab branch
# - Begin Phase 5 RED phase (350 tests)
# - Use Phase 4 data to inform Phase 5 design
```

---

## Module Initialization

### Phase 4 Modules Location

All Phase 4 code is in `instruments/custom/`:

```
instruments/custom/
├── specialist_agent_framework/
│   ├── __init__.py
│   ├── specialist_agent_framework.py
│   └── tests/ (if running locally)
├── reasoning_planning_engine/
│   ├── __init__.py
│   ├── reasoning_planning_engine.py
│   └── tests/
└── learning_improvement_system/
    ├── __init__.py
    ├── learning_improvement_system.py
    └── tests/
```

### Initialization Code Example

```python
# Initialize Phase 4 components
from instruments.custom.specialist_agent_framework import SpecialistAgent, AgentLifecycle
from instruments.custom.reasoning_planning_engine import ReasoningEngine, PlanningEngine
from instruments.custom.learning_improvement_system import ExperienceManager, ContinuousImprovement

# Create specialist agents
agent_lifecycle = AgentLifecycle()
agents = []
for i in range(5):
    agent = SpecialistAgent(
        id=f"agent_{i}",
        name=f"Specialist Agent {i}",
        role="research",  # Can be: research, writing, operations, analysis, coordination
    )
    agents.append(agent)

# Initialize reasoning engine
reasoning_engine = ReasoningEngine(max_depth=5)

# Initialize learning system
experience_manager = ExperienceManager()
continuous_improvement = ContinuousImprovement()
```

---

## Monitoring & Observability

### Key Metrics to Track

1. **Agent Initialization** (Target: <50ms)

   ```python
   # Log initialization time
   import time
   start = time.time()
   agent = SpecialistAgent(...)
   init_time = (time.time() - start) * 1000
   logger.info(f"Agent init: {init_time:.2f}ms")
   ```

2. **Reasoning Performance** (Target: <200ms)

   ```python
   # Log reasoning chain execution
   start = time.time()
   result = reasoning_engine.chain_of_thought(...)
   exec_time = (time.time() - start) * 1000
   logger.info(f"Reasoning: {exec_time:.2f}ms")
   ```

3. **Learning System** (Target: <100ms)

   ```python
   # Log pattern learning performance
   start = time.time()
   patterns = experience_manager.learn_patterns(experiences)
   learn_time = (time.time() - start) * 1000
   logger.info(f"Pattern learning: {learn_time:.2f}ms")
   ```

### Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Agent Init | >75ms | >100ms |
| Reasoning | >300ms | >500ms |
| Learning | >150ms | >200ms |
| Error Rate | >0.5% | >1% |
| Memory Usage | >80% | >95% |

---

## Rollback Procedure

If issues occur during deployment:

### Immediate Rollback

```bash
# 1. Identify issue
# Check logs: docker logs agent-jumbo | grep ERROR

# 2. Stop current deployment
# Kill Phase 4 agent processes if needed
# pkill -f "phase4_agents"

# 3. Rollback to previous commit
git checkout <previous-working-commit>

# 4. Restart services
# (Your standard restart procedure)

# 5. Verify rollback
pytest tests/ -v  # Verify old tests pass
```

### Known Issues & Solutions

**Issue 1**: Agent initialization timeout

- **Solution**: Increase AGENT_INIT_TIMEOUT_MS to 150ms
- **Check**: Log files for deadlock conditions

**Issue 2**: Reasoning chain exceeds timeout

- **Solution**: Reduce MAX_REASONING_DEPTH to 3
- **Check**: Verify reasoning complexity in use case

**Issue 3**: Learning system consuming too much memory

- **Solution**: Reduce LEARNING_BATCH_SIZE to 50
- **Check**: Monitor `data/learning/` directory size

---

## Post-Deployment Validation

### Week 1 Validation Checklist

- [ ] Agent initialization <50ms (check logs)
- [ ] Reasoning chains <200ms (check metrics)
- [ ] Pattern learning <100ms (check logs)
- [ ] No critical errors (check error rate)
- [ ] Learning data accumulating (check file count)
- [ ] Memory usage stable (check memory trends)
- [ ] No performance degradation (compare with baseline)

### Success Criteria

✅ **ALL** of the following:

- 0 critical errors in logs
- Agent initialization: <50ms (100% of requests)
- Reasoning performance: <200ms (99% of requests)
- Learning performance: <100ms (99% of requests)
- Error rate: <0.1%
- Memory stable: No memory leaks
- Learning system: >1000 experiences captured

---

## Support & Escalation

### Phase 4 Specific Issues

**Issue**: Agent communication failing

- Check: EventBus is running
- Check: Agent IDs are unique
- Check: Message queue is not full

**Issue**: Reasoning engine producing invalid decisions

- Check: Confidence threshold is appropriate
- Check: Max reasoning depth is sufficient
- Check: Input data is valid

**Issue**: Learning system not improving

- Check: Sufficient experiences collected (>100)
- Check: Pattern threshold is realistic (0.5-0.8)
- Check: Data quality in experiences

### Escalation Path

1. Check logs: `docker logs agent-jumbo | grep phase4`
2. Review metrics dashboard
3. Run diagnostic tests: `pytest tests/test_*phase4* -v`
4. Consult DEPLOYMENT_READINESS_BRIEF.md
5. Contact: (your support contact)

---

## Phase 5 Preparation (If pursuing Hybrid approach)

For those planning Phase 5 after Phase 4 deployment:

```bash
# Phase 5 setup (parallel with Phase 4)
git checkout -b feature/phase5-human-ai-collab
mkdir -p tests/phase5
mkdir -p instruments/custom/human_oversight_framework
mkdir -p instruments/custom/explainability_engine

# Begin Phase 5 RED phase (350 tests planned)
# See PHASE5_IMPLEMENTATION_PLAN.md
```

---

**Deployment Ready**: ✅ YES
**Risk Level**: LOW
**Recommended Strategy**: Hybrid (Canary + Parallel Phase 5)
**Expected Timeline**: 1 week (Phase 4 canary) + Q3 2026 (Phase 5 dev)

For questions, refer to DEPLOYMENT_READINESS_BRIEF.md or PHASE4_VALIDATION_COMPLETE.md
