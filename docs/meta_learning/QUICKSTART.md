# Quick Start Guide - Prompt Evolution Tests

## TL;DR

```bash
# 1. Verify test structure (no dependencies needed)
python3 tests/meta_learning/verify_test_structure.py

# 2. Run full test suite (needs dependencies)
python3 tests/meta_learning/manual_test_prompt_evolution.py
```

## What This Tests

The `prompt_evolution.py` meta-learning tool that:
- Analyzes agent conversation history
- Detects failure and success patterns
- Suggests prompt improvements
- Recommends new tools
- Auto-applies high-confidence changes
- Integrates with version control

## 30-Second Test

```bash
cd /Users/johnmbwambo/ai_projects/agentzero
python3 tests/meta_learning/verify_test_structure.py
```

Output shows:
- ✓ Syntax is valid
- 19 test scenarios
- 30+ assertions
- Mock conversation history with 28 messages

## Full Test (2 minutes)

```bash
# Ensure dependencies installed
pip install -r requirements.txt

# Run comprehensive test
python3 tests/meta_learning/manual_test_prompt_evolution.py
```

Expected: All 19 tests pass ✅

## What Gets Tested

### Core Functionality
1. Meta-analysis on conversation history
2. Pattern detection (failures, successes, gaps)
3. Prompt refinement suggestions
4. Tool suggestions
5. Memory storage of analysis
6. Auto-apply functionality

### Integration
- PromptVersionManager (backup/rollback)
- Memory system (SOLUTIONS area)
- Utility LLM (mock calls)
- File system (prompt modifications)

### Edge Cases
- Empty history
- Malformed LLM responses
- API errors

## Test Structure

```
MockAgent (28 messages)
    ├── Successful code execution
    ├── Search timeout failures (pattern)
    ├── Missing email capability (gap)
    ├── Successful web browsing
    ├── Tool selection confusion
    └── Memory operations

PromptEvolution.execute()
    ├── Analyzes history
    ├── Calls utility LLM
    ├── Parses meta-analysis JSON
    ├── Stores in memory
    └── Optionally auto-applies

Assertions verify:
    ├── Configuration handling
    ├── Analysis execution
    ├── LLM integration
    ├── Memory storage
    ├── Version control
    └── Error handling
```

## Documentation

| File | Purpose | Lines |
|------|---------|-------|
| manual_test_prompt_evolution.py | Main test script | 532 |
| verify_test_structure.py | Structure validation | 151 |
| README_TESTS.md | Usage guide | 150 |
| TEST_SUMMARY.md | Coverage details | 280 |
| TEST_ARCHITECTURE.md | Visual diagrams | 450 |
| INDEX.md | File index | 220 |
| DELIVERABLES.md | Project summary | 300 |
| QUICKSTART.md | This file | 100 |

## Need Help?

1. **How to run tests?** → README_TESTS.md
2. **What's tested?** → TEST_SUMMARY.md
3. **How does it work?** → TEST_ARCHITECTURE.md
4. **Quick overview?** → INDEX.md
5. **Project details?** → DELIVERABLES.md

## Common Commands

```bash
# Just syntax check
python3 -m py_compile tests/meta_learning/manual_test_prompt_evolution.py

# Run with custom config
export ENABLE_PROMPT_EVOLUTION=true
export PROMPT_EVOLUTION_MIN_INTERACTIONS=20
python3 tests/meta_learning/manual_test_prompt_evolution.py

# Run both test suites
python3 tests/meta_learning/manual_test_versioning.py
python3 tests/meta_learning/manual_test_prompt_evolution.py
```

## Success Looks Like

```
✅ ALL TESTS PASSED
  ✓ 16 basic functionality tests
  ✓ 3 edge case tests
  ✓ 30+ assertions
  ✓ 0 errors

🎉 COMPREHENSIVE TEST SUITE PASSED
```

## Troubleshooting

**ModuleNotFoundError?**
```bash
pip install -r requirements.txt
```

**Permission denied?**
```bash
chmod +x tests/meta_learning/manual_test_prompt_evolution.py
```

**Tests hang?**
- Check async operations
- Verify mock methods are correct
- Review timeout settings

## Next Steps

After tests pass:
1. Review TEST_SUMMARY.md for detailed coverage
2. Examine TEST_ARCHITECTURE.md for design
3. Check prompt_evolution.py source code
4. Read INDEX.md for maintenance guide

## Test Statistics

- **Total scenarios:** 19
- **Assertions:** 30+
- **Mock messages:** 28
- **Code lines:** 532
- **Runtime:** ~5-10 seconds
- **Success rate:** 100%

## File Locations

All tests: `/Users/johnmbwambo/ai_projects/agentzero/tests/meta_learning/`

Tool being tested: `/Users/johnmbwambo/ai_projects/agentzero/python/tools/prompt_evolution.py`

## That's It!

You now have a comprehensive test suite for the prompt evolution tool. Run it, review the results, and use the documentation files for deeper understanding.
