# Meta-Learning Test Suite - Index

## Quick Start

```bash
# Verify test structure (no dependencies required)
python3 tests/meta_learning/verify_test_structure.py

# Run full test suite (requires dependencies)
python3 tests/meta_learning/manual_test_prompt_evolution.py
```

## Documentation Files

### 📋 README_TESTS.md
**What it covers:**
- How to run the tests
- Test coverage breakdown
- Environment variables
- Troubleshooting guide

**When to read:**
- First time running tests
- Setting up test environment
- Debugging test failures

### 📊 TEST_SUMMARY.md
**What it covers:**
- Complete test coverage overview
- Test scenario details
- Mock data structure
- Success metrics

**When to read:**
- Understanding test scope
- Evaluating test quality
- Planning test additions

### 🏗️ TEST_ARCHITECTURE.md
**What it covers:**
- Visual component diagrams
- Data flow illustrations
- Test execution flow
- Assertion coverage map

**When to read:**
- Understanding test design
- Modifying test structure
- Adding new test scenarios

## Test Files

### ✅ manual_test_prompt_evolution.py (533 lines)
**Primary test file for prompt evolution tool**

**Components:**
- `MockAgent` class - Simulates Agent with realistic data
- `test_basic_functionality()` - 16 core test scenarios
- `test_edge_cases()` - 3 error handling tests

**Test Coverage:**
- Configuration validation
- Meta-analysis execution
- LLM integration
- Memory storage
- Auto-apply functionality
- Version control integration
- Edge cases and errors

### ✓ verify_test_structure.py
**Standalone verification script**

**Purpose:**
- Validates test file syntax
- Analyzes test structure
- Counts assertions and scenarios
- No dependencies required

**Use Cases:**
- CI/CD validation
- Quick structure check
- Documentation generation

### ✓ manual_test_versioning.py (157 lines)
**Tests for prompt versioning system**

**Coverage:**
- Snapshot creation
- Version comparison
- Rollback operations
- Change application

## Test Statistics

| Metric | Value |
|--------|-------|
| Total Test Files | 2 |
| Test Scenarios | 19 |
| Code Lines | 533 |
| Assertions | 30+ |
| Mock Messages | 28 |
| Environment Variables Tested | 5 |
| Integration Points | 3 |

## Directory Structure

```
tests/meta_learning/
├── manual_test_prompt_evolution.py    # Main test file
├── manual_test_versioning.py          # Versioning tests
├── verify_test_structure.py           # Structure validation
├── README_TESTS.md                    # Usage guide
├── TEST_SUMMARY.md                    # Coverage summary
├── TEST_ARCHITECTURE.md               # Visual diagrams
└── INDEX.md                           # This file
```

## Quick Reference

### Run Specific Test
```bash
# Just structure verification
python3 tests/meta_learning/verify_test_structure.py

# Just versioning tests
python3 tests/meta_learning/manual_test_versioning.py

# Just evolution tests
python3 tests/meta_learning/manual_test_prompt_evolution.py

# Both test suites
python3 tests/meta_learning/manual_test_versioning.py && \
python3 tests/meta_learning/manual_test_prompt_evolution.py
```

### Environment Variables
```bash
# Run with custom configuration
export ENABLE_PROMPT_EVOLUTION=true
export PROMPT_EVOLUTION_MIN_INTERACTIONS=20
export PROMPT_EVOLUTION_CONFIDENCE_THRESHOLD=0.8
export AUTO_APPLY_PROMPT_EVOLUTION=false
python3 tests/meta_learning/manual_test_prompt_evolution.py
```

### Expected Runtime
- **verify_test_structure.py**: < 1 second
- **manual_test_versioning.py**: 2-5 seconds
- **manual_test_prompt_evolution.py**: 5-10 seconds

## Test Scenarios at a Glance

### Basic Functionality (16 tests)
1. Environment setup
2. Mock agent creation
3. Tool initialization
4. Insufficient history detection
5. Disabled meta-learning check
6. Full meta-analysis execution
7. Utility model verification
8. Analysis storage
9. Confidence threshold filtering
10. Auto-apply functionality
11. History formatting
12. Summary generation
13. Storage formatting
14. Default prompt structure
15. Version manager integration
16. Rollback functionality

### Edge Cases (3 tests)
1. Empty history handling
2. Malformed LLM response
3. LLM error handling

## Mock Data Overview

### Conversation History (28 messages)
- **Success patterns:** Code execution, memory operations
- **Failure patterns:** Search timeouts, tool confusion
- **Gaps detected:** Email capability, file vs memory distinction

### Meta-Analysis Response
- **Failure patterns:** 2 detected
- **Success patterns:** 2 identified
- **Missing instructions:** 2 gaps
- **Tool suggestions:** 2 new tools
- **Prompt refinements:** 3 improvements (0.75-0.92 confidence)

## Integration Points

```
PromptEvolution Tool
    ├── Agent.call_utility_model()
    ├── Agent.read_prompt()
    ├── Memory.get()
    ├── Memory.insert_text()
    ├── PromptVersionManager.apply_change()
    └── PromptVersionManager.rollback()
```

## Success Indicators

When all tests pass, you should see:

```
✅ ALL TESTS PASSED
  ✓ 16 basic functionality tests
  ✓ 3 edge case tests
  ✓ 30+ assertions
  ✓ 0 errors
  ✓ Clean cleanup

🎉 COMPREHENSIVE TEST SUITE PASSED
```

## Maintenance Checklist

When updating `prompt_evolution.py`:

- [ ] Add test scenario for new feature
- [ ] Update mock data if needed
- [ ] Add new assertions for validation
- [ ] Update TEST_SUMMARY.md
- [ ] Update environment variables if added
- [ ] Run full test suite
- [ ] Update documentation

## Related Files

### Source Code
- `/python/tools/prompt_evolution.py` - Tool being tested
- `/python/helpers/prompt_versioning.py` - Version manager
- `/python/helpers/tool.py` - Tool base class
- `/python/helpers/memory.py` - Memory system

### Prompts
- `/prompts/meta_learning.analyze.sys.md` - Analysis system prompt
- `/prompts/agent.system.*.md` - Various agent prompts

### Documentation
- `/docs/extensibility.md` - Extension system
- `/docs/architecture.md` - System architecture

## Common Issues

### "ModuleNotFoundError"
**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### "Permission denied" during cleanup
**Solution:** Check temp directory permissions
```bash
chmod -R 755 /tmp/test_prompt_evolution_*
```

### Tests hang or timeout
**Solution:** Check async operations
- Ensure mock methods are async when needed
- Verify asyncio.run() usage

## Contributing

To add new test scenarios:

1. **Add test function** in `manual_test_prompt_evolution.py`
2. **Update documentation** in relevant .md files
3. **Add assertions** to validate behavior
4. **Update TEST_SUMMARY.md** with new coverage
5. **Run full suite** to ensure no regressions

## Version History

- **v1.0** (2026-01-05) - Initial test suite creation
  - 19 test scenarios
  - 30+ assertions
  - Comprehensive documentation

## Contact & Support

For questions about the test suite:
- Review this INDEX.md for overview
- Check README_TESTS.md for usage
- See TEST_ARCHITECTURE.md for design details
- Examine TEST_SUMMARY.md for coverage info
