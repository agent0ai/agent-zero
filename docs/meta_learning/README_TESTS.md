# Meta-Learning Tests

This directory contains tests for the Agent Zero meta-learning system, including prompt evolution and versioning.

## Test Files

### manual_test_prompt_evolution.py
Comprehensive manual test for the prompt evolution (meta-analysis) tool.

**What it tests:**
- Meta-analysis execution on conversation history
- Pattern detection (failures, successes, gaps)
- Prompt refinement suggestions
- Tool suggestions
- Auto-apply functionality
- Confidence threshold filtering
- Memory storage of analysis results
- Integration with prompt version manager
- Edge cases and error handling

**How to run:**

```bash
# From the project root directory

# Option 1: If dependencies are already installed
python3 tests/meta_learning/manual_test_prompt_evolution.py

# Option 2: Using a virtual environment
python3 -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate
pip install -r requirements.txt
python tests/meta_learning/manual_test_prompt_evolution.py
deactivate

# Option 3: If the project has a development environment setup
# Follow the installation guide in docs/installation.md first, then:
python tests/meta_learning/manual_test_prompt_evolution.py
```

**Expected output:**
The test creates a temporary directory with sample prompts, simulates an agent with conversation history, and runs through 17 comprehensive test scenarios. All tests should pass with green checkmarks.

### manual_test_versioning.py
Manual test for the prompt versioning system.

**What it tests:**
- Snapshot creation
- Version listing
- Diff between versions
- Rollback functionality
- Change application with automatic versioning
- Old version cleanup
- Version export

**How to run:**
```bash
python3 tests/meta_learning/manual_test_versioning.py
```

## Test Coverage Summary

### manual_test_prompt_evolution.py

**Basic Functionality Tests (13 tests):**
1. ✓ Insufficient history detection
2. ✓ Disabled meta-learning detection
3. ✓ Full analysis execution
4. ✓ Utility model integration
5. ✓ Memory storage
6. ✓ Confidence threshold filtering
7. ✓ Auto-apply functionality
8. ✓ History formatting
9. ✓ Summary generation
10. ✓ Storage formatting
11. ✓ Default prompt structure
12. ✓ Version manager integration
13. ✓ Rollback functionality

**Edge Case Tests (3 tests):**
1. ✓ Empty history handling
2. ✓ Malformed LLM response handling
3. ✓ LLM error handling

**Total: 16 test scenarios**

## Mock Agent Structure

The test creates a realistic mock agent with:

- **Conversation history** with 28 messages including:
  - Successful code execution (fibonacci calculator)
  - Search engine timeout failures (pattern detection)
  - Missing capability detection (email tool)
  - Successful web browsing
  - Memory operations
  - Tool selection ambiguity

- **Simulated meta-analysis JSON** including:
  - 2 failure patterns
  - 2 success patterns
  - 2 missing instruction gaps
  - 2 tool suggestions
  - 3 prompt refinements (with varying confidence levels)

## Environment Variables Tested

The test verifies behavior with different configurations:

- `ENABLE_PROMPT_EVOLUTION` - Enable/disable meta-learning
- `PROMPT_EVOLUTION_MIN_INTERACTIONS` - Minimum history size
- `PROMPT_EVOLUTION_MAX_HISTORY` - Maximum messages to analyze
- `PROMPT_EVOLUTION_CONFIDENCE_THRESHOLD` - Minimum confidence for suggestions
- `AUTO_APPLY_PROMPT_EVOLUTION` - Auto-apply high-confidence changes

## Integration with Version Manager

The test verifies that:
1. Meta-learning creates automatic backups before applying changes
2. Prompt refinements are correctly applied to files
3. Changes can be rolled back if needed
4. Version metadata includes change descriptions

## Troubleshooting

**ModuleNotFoundError**: Install dependencies with:
```bash
pip install -r requirements.txt
```

**Test fails at cleanup**: Check file permissions in temp directory.

**Mock LLM not returning JSON**: The mock is designed to return valid JSON. If this fails, check the `call_utility_model` method in the MockAgent class.

**Integration test fails**: Ensure write permissions in the test directory.

## Contributing

When adding new meta-learning features, update this test to cover:
1. New analysis patterns
2. New refinement types
3. New auto-apply logic
4. New edge cases

Keep the mock conversation history realistic and diverse to ensure robust testing.
