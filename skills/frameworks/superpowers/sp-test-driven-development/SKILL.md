---
name: "sp-test-driven-development"
description: "RED-GREEN-REFACTOR cycle: write failing test, minimal code, commit."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["superpowers", "tdd", "testing", "development"]
trigger_patterns:
  - "test driven"
  - "tdd"
  - "red green refactor"
  - "test first"
---

# Superpowers: Test-Driven Development

Enforce strict RED-GREEN-REFACTOR discipline for reliable code.

## The TDD Cycle

```
┌─────────┐     ┌─────────┐     ┌──────────┐
│   RED   │ ──▶ │  GREEN  │ ──▶ │ REFACTOR │
│ (fail) │     │ (pass)  │     │ (clean)  │
└─────────┘     └─────────┘     └──────────┘
     ▲                               │
     └───────────────────────────────┘
```

## The Rules

### 1. RED: Write a Failing Test First

- Write the test BEFORE any implementation
- The test MUST fail initially
- Failure confirms the test is testing something real

```bash
# Run test - expect failure
npm test -- --grep "should validate email"
# FAIL ✗
```

### 2. GREEN: Write Minimal Code to Pass

- Write ONLY enough code to make the test pass
- No extra features, no "while I'm here" additions
- Resist the urge to generalize

```bash
# Run test - expect success
npm test -- --grep "should validate email"
# PASS ✓
```

### 3. REFACTOR: Clean Up (Tests Stay Green)

- Improve code quality without changing behavior
- Tests must remain passing
- Commit after each successful refactor

```bash
# Run all tests - all must pass
npm test
# All PASS ✓
```

### 4. COMMIT: After Each Cycle

- One commit per RED-GREEN-REFACTOR cycle
- Clear commit message describing the test case

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad |
|-------------|--------------|
| Writing code before tests | No proof code works |
| Writing multiple tests at once | Too much change, hard to debug |
| Making tests pass with hacks | Technical debt accumulates |
| Skipping refactor step | Code quality degrades |
| Testing implementation details | Tests become brittle |

## Test Quality Checklist

- [ ] Test describes behavior, not implementation
- [ ] Test has clear arrange-act-assert structure
- [ ] Test fails for the right reason initially
- [ ] Test name explains what it verifies
- [ ] Test is independent (no shared state)

## Integration with Superpowers Workflow

1. **Brainstorming** → Design approved
2. **Git Worktrees** → Isolated workspace
3. **Writing Plans** → Tasks defined
4. **TDD** → For each task: RED → GREEN → REFACTOR ← YOU ARE HERE
5. **Code Review** → Review implementation
6. **Finishing Branch** → Merge

## The Discipline

**DELETE code written before tests.**

If you find yourself writing implementation before the test:
1. Stop immediately
2. Delete the implementation
3. Write the test first
4. Watch it fail
5. THEN write the code

This is not negotiable. The discipline IS the value.
