# Test Architecture Diagram

## Overview

Visual representation of the `manual_test_prompt_evolution.py` test architecture.

## Component Hierarchy

```
manual_test_prompt_evolution.py
│
├── MockAgent Class
│   ├── __init__()
│   │   └── Initialize test state
│   │
│   ├── _create_test_history()
│   │   └── Returns 28-message conversation
│   │       ├── User requests
│   │       ├── Agent responses
│   │       ├── Tool executions
│   │       └── Tool results
│   │
│   ├── call_utility_model()
│   │   └── Returns mock meta-analysis JSON
│   │       ├── failure_patterns (2)
│   │       ├── success_patterns (2)
│   │       ├── missing_instructions (2)
│   │       ├── tool_suggestions (2)
│   │       └── prompt_refinements (3)
│   │
│   └── read_prompt()
│       └── Returns empty string (triggers default)
│
├── test_basic_functionality()
│   │
│   ├── Setup Phase
│   │   ├── Create temp directory
│   │   ├── Create sample prompt files
│   │   └── Initialize MockAgent
│   │
│   ├── Test Scenarios (16)
│   │   ├── Test 1: Environment setup
│   │   ├── Test 2: Mock agent creation
│   │   ├── Test 3: Tool initialization
│   │   ├── Test 4: Insufficient history check
│   │   ├── Test 5: Disabled meta-learning check
│   │   ├── Test 6: Full meta-analysis execution
│   │   ├── Test 7: Utility model verification
│   │   ├── Test 8: Analysis storage
│   │   ├── Test 9: Confidence threshold filtering
│   │   ├── Test 10: Auto-apply functionality
│   │   ├── Test 11: History formatting
│   │   ├── Test 12: Summary generation
│   │   ├── Test 13: Storage formatting
│   │   ├── Test 14: Default prompt structure
│   │   ├── Test 15: Version manager integration
│   │   └── Test 16: Rollback functionality
│   │
│   └── Cleanup Phase
│       └── Remove temp directory
│
└── test_edge_cases()
    │
    ├── Test 1: Empty history
    ├── Test 2: Malformed LLM response
    └── Test 3: LLM error handling
```

## Data Flow Diagram

```
┌─────────────────┐
│  Test Runner    │
│   (main)        │
└────────┬────────┘
         │
         ├─────────────────────────────────┐
         │                                 │
         ▼                                 ▼
┌────────────────────┐          ┌─────────────────────┐
│ test_basic_        │          │ test_edge_cases()   │
│ functionality()    │          │                     │
└─────────┬──────────┘          └──────────┬──────────┘
          │                                │
          │                                │
          ▼                                ▼
┌─────────────────────────────────────────────────────┐
│                  MockAgent                          │
│  ┌──────────────────────────────────────────────┐  │
│  │ history: List[Dict] (28 messages)            │  │
│  │   - User messages                            │  │
│  │   - Assistant responses                      │  │
│  │   - Tool calls and results                   │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ call_utility_model()                         │  │
│  │   └─> Returns JSON analysis                  │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│            PromptEvolution Tool                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ execute()                                    │  │
│  │   ├─> _analyze_history()                    │  │
│  │   ├─> _store_analysis()                     │  │
│  │   ├─> _apply_suggestions()                  │  │
│  │   └─> _generate_summary()                   │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│         PromptVersionManager                        │
│  ┌──────────────────────────────────────────────┐  │
│  │ create_snapshot()                            │  │
│  │ apply_change()                               │  │
│  │ rollback()                                   │  │
│  │ list_versions()                              │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Test Execution Flow

```
START
  │
  ▼
┌──────────────────────────────────────┐
│ Create temporary test directory      │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────┐
│ Create sample prompt files           │
│  - agent.system.main.md              │
│  - agent.system.tools.md             │
│  - agent.system.tool.search_eng.md   │
│  - agent.system.main.solving.md      │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────┐
│ Initialize MockAgent                 │
│  - Load test history (28 msgs)       │
│  - Setup mock methods                │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────┐
│ Run Test Scenarios (Loop)            │
│                                      │
│  For each configuration:             │
│    ├─> Set environment variables     │
│    ├─> Create PromptEvolution tool   │
│    ├─> Execute tool                  │
│    ├─> Verify results                │
│    └─> Assert expectations           │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────┐
│ Integration Tests                    │
│  - Version manager operations        │
│  - File modifications                │
│  - Rollback operations               │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────┐
│ Edge Case Tests                      │
│  - Empty history                     │
│  - Malformed responses               │
│  - Error conditions                  │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────┐
│ Cleanup                              │
│  - Remove temporary directory        │
│  - Reset state                       │
└────────────────┬─────────────────────┘
                 │
                 ▼
              SUCCESS
```

## Mock Meta-Analysis JSON Structure

```json
{
  "failure_patterns": [
    {
      "pattern": "Search engine timeout failures",
      "frequency": 2,
      "severity": "high",
      "affected_prompts": ["agent.system.tool.search_engine.md"],
      "example_messages": [5, 7]
    }
  ],
  "success_patterns": [
    {
      "pattern": "Effective code execution",
      "frequency": 1,
      "confidence": 0.9,
      "related_prompts": ["agent.system.tool.code_exe.md"]
    }
  ],
  "missing_instructions": [
    {
      "gap": "No email capability",
      "impact": "high",
      "suggested_location": "agent.system.tools.md",
      "proposed_addition": "Add email tool"
    }
  ],
  "tool_suggestions": [
    {
      "tool_name": "email_tool",
      "purpose": "Send emails",
      "use_case": "User email requests",
      "priority": "high",
      "required_integrations": ["smtplib"]
    }
  ],
  "prompt_refinements": [
    {
      "file": "agent.system.tool.search_engine.md",
      "section": "Error Handling",
      "proposed": "Implement retry logic...",
      "reason": "Repeated timeout failures",
      "confidence": 0.88
    }
  ],
  "meta": {
    "timestamp": "2026-01-05T...",
    "monologue_count": 5,
    "history_size": 28,
    "confidence_threshold": 0.7
  }
}
```

## Test Configuration Matrix

| Test # | ENABLE | MIN_INTER | THRESHOLD | AUTO_APPLY | Expected Result |
|--------|--------|-----------|-----------|------------|-----------------|
| 1      | false  | *         | *         | *          | Disabled message |
| 2      | true   | 100       | *         | *          | Insufficient history |
| 3      | true   | 10        | 0.7       | false      | Analysis complete, no apply |
| 4      | true   | 10        | 0.7       | true       | Analysis + auto-apply |
| 5      | true   | 10        | 0.95      | false      | High threshold filtering |

## Assertion Coverage Map

```
┌─────────────────────────────────────────────────────┐
│              Assertions (30+)                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Configuration Checks (5)                           │
│    ├─ Tool initialization                           │
│    ├─ Environment variable reading                  │
│    ├─ History size validation                       │
│    ├─ Enable/disable detection                      │
│    └─ Threshold configuration                       │
│                                                     │
│  Execution Validation (8)                           │
│    ├─ Execute returns Response                      │
│    ├─ Message content validation                    │
│    ├─ Analysis completion                           │
│    ├─ LLM call verification                         │
│    ├─ Memory storage attempt                        │
│    ├─ Summary generation                            │
│    ├─ Storage format validation                     │
│    └─ Default prompt structure                      │
│                                                     │
│  Integration Tests (10)                             │
│    ├─ Version creation                              │
│    ├─ File modification                             │
│    ├─ Content verification                          │
│    ├─ Rollback success                              │
│    ├─ Content restoration                           │
│    ├─ Backup ID generation                          │
│    ├─ Metadata storage                              │
│    ├─ Version counting                              │
│    ├─ Snapshot listing                              │
│    └─ Export functionality                          │
│                                                     │
│  Data Validation (7)                                │
│    ├─ History formatting                            │
│    ├─ JSON structure                                │
│    ├─ Confidence filtering                          │
│    ├─ Pattern detection                             │
│    ├─ Suggestion generation                         │
│    ├─ Summary content                               │
│    └─ Storage text format                           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## File Organization

```
tests/meta_learning/
│
├── manual_test_prompt_evolution.py  (533 lines)
│   └── Main test implementation
│
├── manual_test_versioning.py        (157 lines)
│   └── Version control tests
│
├── README_TESTS.md
│   └── Test documentation
│
├── TEST_SUMMARY.md
│   └── Test coverage summary
│
└── TEST_ARCHITECTURE.md (this file)
    └── Visual test structure
```

## Key Design Patterns

### 1. Arrange-Act-Assert (AAA)
```python
# Arrange
mock_agent = MockAgent()
tool = PromptEvolution(mock_agent, "prompt_evolution", {})

# Act
result = asyncio.run(tool.execute())

# Assert
assert isinstance(result, Response)
assert "Meta-Learning" in result.message
```

### 2. Test Isolation
- Each test creates its own temporary directory
- No shared state between tests
- Guaranteed cleanup via try/finally

### 3. Mock Objects
- MockAgent replaces real Agent
- Mock methods track calls
- Realistic test data

### 4. Configuration Testing
- Environment variable patches
- Multiple configuration scenarios
- Isolated per test

## Dependencies

```
Direct:
├── asyncio          (async operations)
├── unittest.mock    (mocking)
├── tempfile         (temp directories)
├── json             (JSON handling)
└── pathlib          (path operations)

Indirect:
├── python.tools.prompt_evolution
├── python.helpers.prompt_versioning
├── python.helpers.tool
└── python.helpers.log
```

## Success Criteria

```
✅ All 19 scenarios pass
✅ 30+ assertions succeed
✅ Zero errors or warnings
✅ Cleanup completes
✅ No side effects
✅ Deterministic results
```
