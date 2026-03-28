# Meta-Learning System Documentation

Welcome to Agent Zero's Self-Evolving Meta-Learning system documentation. This directory contains comprehensive guides for using and understanding the meta-learning framework.

## Quick Navigation

### Getting Started
- **[QUICKSTART.md](QUICKSTART.md)** - 2-minute quick start guide
- **[README_TESTS.md](README_TESTS.md)** - How to run the test suite

### Understanding the System
- **[meta_learning.md](meta_learning.md)** - Complete system guide (main reference)
- **[TEST_SUMMARY.md](TEST_SUMMARY.md)** - Test coverage overview
- **[TEST_ARCHITECTURE.md](TEST_ARCHITECTURE.md)** - Visual diagrams and architecture

### Reference
- **[INDEX.md](INDEX.md)** - Comprehensive file index
- **[DELIVERABLES.md](DELIVERABLES.md)** - Project deliverables summary

## What is Meta-Learning?

Agent Zero's meta-learning system is a **self-evolving framework** that:

1. **Analyzes** - Examines conversation patterns to identify successes and failures
2. **Learns** - Detects patterns and gaps in prompts and tools
3. **Suggests** - Proposes improvements with confidence scores
4. **Evolves** - Applies changes with automatic versioning and rollback capability

This makes Agent Zero the only AI framework that learns from its own interactions and improves over time.

## Key Features

✨ **Pattern Detection** - Identifies repeated failures and successes  
🎯 **Smart Suggestions** - Generates specific, actionable improvements  
🔄 **Version Control** - Automatic backups before every change  
↩️ **Safe Rollback** - Revert to any previous version instantly  
🤖 **Auto-Apply (Optional)** - Automatic application with manual review by default  

## Architecture Overview

```
Agent Conversation
    ↓
Meta-Analysis Trigger (every N interactions)
    ↓
Prompt Evolution Tool
    ├─ Detect failure patterns
    ├─ Detect success patterns
    ├─ Identify missing instructions
    └─ Suggest prompt refinements & tools
    ↓
Store in Memory (SOLUTIONS area)
    ↓
Manual Review / Auto-Apply (configurable)
    ↓
Version Control (automatic backup)
    ↓
Prompt Versioning System (backup & rollback)
```

## Configuration

Enable meta-learning in your `.env`:

```bash
# Enable the meta-learning system
ENABLE_PROMPT_EVOLUTION=true

# Run analysis every N monologues
PROMPT_EVOLUTION_FREQUENCY=10

# Minimum conversation history before analysis
PROMPT_EVOLUTION_MIN_INTERACTIONS=20

# Only suggest with confidence ≥ this threshold
PROMPT_EVOLUTION_CONFIDENCE_THRESHOLD=0.7

# Auto-apply high-confidence suggestions (not recommended - use false)
AUTO_APPLY_PROMPT_EVOLUTION=false
```

## Usage Example

### Manual Trigger
```
User: Analyze my recent interactions using meta-learning.

Agent: [Analyzes last 100 messages for patterns]

Output:
- 2 failure patterns detected
- 3 success patterns found
- 4 prompt refinements suggested
- 2 new tools recommended
```

### Query Results
```
User: Show me the meta-learning suggestions from my last session.

Agent: [Retrieves from SOLUTIONS memory area]

Results: Full analysis with:
- Specific improvements recommended
- Confidence scores for each
- Files affected
- Rationale for changes
```

### Apply Changes
```
User: Apply the top 3 suggestions from the meta-learning analysis.

Agent: [Creates backup, applies changes, reports results]
```

## File Structure

```
docs/meta_learning/
├── README.md                    # This file
├── QUICKSTART.md               # Quick start (2 minutes)
├── meta_learning.md            # Complete guide
├── README_TESTS.md             # Test documentation
├── TEST_SUMMARY.md             # Test coverage
├── TEST_ARCHITECTURE.md        # Architecture diagrams
├── INDEX.md                    # Comprehensive index
└── DELIVERABLES.md            # Project summary

Implementation files:
python/
├── tools/
│   └── prompt_evolution.py     # Meta-analysis tool
├── helpers/
│   └── prompt_versioning.py    # Version control
├── api/
│   └── meta_learning.py        # API endpoints
└── extensions/
    └── monologue_end/
        └── _85_prompt_evolution.py  # Auto-trigger

prompts/
└── meta_learning.analyze.sys.md    # Analysis system prompt
```

## Key Components

### 1. Prompt Evolution Tool (`python/tools/prompt_evolution.py`)
The core meta-analysis engine that:
- Analyzes conversation history
- Detects patterns
- Generates suggestions
- Stores results in memory

### 2. Prompt Versioning (`python/helpers/prompt_versioning.py`)
Version control system for prompts:
- Automatic snapshots before changes
- Rollback to any previous version
- Change tracking with metadata
- Diff between versions

### 3. Meta-Learning API (`python/api/meta_learning.py`)
REST endpoints for:
- Triggering analysis
- Listing suggestions
- Applying changes
- Managing versions
- Dashboard queries

### 4. Auto-Trigger Extension (`python/extensions/monologue_end/_85_prompt_evolution.py`)
Automatically triggers analysis:
- Every N monologues (configurable)
- Can be disabled per configuration
- Non-blocking async operation

## Common Workflows

### Workflow 1: Manual Analysis & Review

1. **Trigger** - Use prompt_evolution tool
2. **Analyze** - System analyzes recent interactions
3. **Review** - Examine suggestions in UI
4. **Select** - Choose which changes to apply
5. **Apply** - Changes applied with automatic backup
6. **Monitor** - Track impact of changes

### Workflow 2: Auto-Trigger with Manual Approval

1. **Configure** - Set `PROMPT_EVOLUTION_FREQUENCY=10`
2. **Auto-Run** - Runs every 10 monologues
3. **Review** - Check suggestions dashboard
4. **Apply** - Accept/reject per change
5. **Monitor** - See results over time

### Workflow 3: Autonomous Evolution (Advanced)

1. **Configure** - Set `AUTO_APPLY_PROMPT_EVOLUTION=true`
2. **Auto-Run** - Analyzes regularly
3. **Auto-Apply** - High-confidence changes applied automatically
4. **Monitor** - Review applied changes periodically
5. **Rollback** - Revert if needed

## Best Practices

✅ **Start with manual review** (AUTO_APPLY=false)  
✅ **Run 50+ interactions first** before enabling analysis  
✅ **Review suggestions carefully** before applying  
✅ **Apply changes gradually** (1-2 at a time)  
✅ **Monitor impact** after each change  
✅ **Maintain version history** for rollback capability  
✅ **Check confidence scores** - higher is better  

❌ **Don't enable auto-apply immediately**  
❌ **Don't apply all suggestions at once**  
❌ **Don't ignore low-confidence suggestions**  
❌ **Don't skip the backup step**  

## Safety Features

🔒 **Automatic Versioning** - Every change creates a backup  
✔️ **Confidence Scoring** - Only high-confidence suggestions shown  
📋 **Pattern Validation** - Minimum 2 occurrences required  
↩️ **One-Command Rollback** - Revert to any previous state  
🔍 **Audit Trail** - Full history of all changes  
🧪 **Test Coverage** - Comprehensive test suite included  

## Troubleshooting

### Issue: "Insufficient history"
**Solution:** Run more interactions (default: 20 minimum)
```bash
export PROMPT_EVOLUTION_MIN_INTERACTIONS=5  # Lower threshold
```

### Issue: "No suggestions generated"
**Solution:** Lower confidence threshold
```bash
export PROMPT_EVOLUTION_CONFIDENCE_THRESHOLD=0.5  # Default: 0.7
```

### Issue: "Changes reverted unexpectedly"
**Solution:** Check the rollback feature - you may have rolled back
```bash
# List versions to see what happened
python3 -c "from python.helpers.prompt_versioning import PromptVersionManager as P; print([v['version_id'] for v in P().list_versions()])"
```

### Issue: "Meta-learning not triggering"
**Solution:** Verify it's enabled
```bash
# Check environment
echo $ENABLE_PROMPT_EVOLUTION  # Should be "true"

# Check frequency
echo $PROMPT_EVOLUTION_FREQUENCY  # Default: 10
```

## Testing

The system includes a comprehensive test suite:

```bash
# Quick verification (no dependencies)
python3 tests/meta_learning/verify_test_structure.py

# Full test suite (requires dependencies)
python3 tests/meta_learning/manual_test_prompt_evolution.py
```

See [README_TESTS.md](README_TESTS.md) for detailed test documentation.

## Architecture Deep Dive

For detailed information about:
- Component interactions
- Data flow diagrams
- Test architecture
- Design patterns

See [TEST_ARCHITECTURE.md](TEST_ARCHITECTURE.md)

## Further Reading

| Document | Purpose |
|----------|---------|
| [QUICKSTART.md](QUICKSTART.md) | Get running in 2 minutes |
| [meta_learning.md](meta_learning.md) | Complete system guide |
| [README_TESTS.md](README_TESTS.md) | How to run tests |
| [TEST_SUMMARY.md](TEST_SUMMARY.md) | Test coverage details |
| [TEST_ARCHITECTURE.md](TEST_ARCHITECTURE.md) | Visual diagrams |
| [INDEX.md](INDEX.md) | File reference |
| [DELIVERABLES.md](DELIVERABLES.md) | Project summary |

## Getting Help

1. **Quick questions?** → Check [QUICKSTART.md](QUICKSTART.md)
2. **How to use?** → See [meta_learning.md](meta_learning.md)
3. **How to test?** → Read [README_TESTS.md](README_TESTS.md)
4. **Need details?** → Review [TEST_ARCHITECTURE.md](TEST_ARCHITECTURE.md)
5. **Want overview?** → Look at [INDEX.md](INDEX.md)

## Contributing

To improve the meta-learning system:

1. Review the [test suite](README_TESTS.md)
2. Run tests to establish baseline
3. Make your changes
4. Add test scenarios for new features
5. Update documentation
6. Submit with full test coverage

## Version History

- **v1.0** (2026-01-05) - Initial implementation and test suite
  - Core prompt evolution tool
  - Prompt versioning system
  - Meta-learning API
  - Comprehensive test suite
  - Full documentation

## License

Agent Zero Meta-Learning System is part of the Agent Zero project.
See LICENSE file in project root for details.

---

**Last Updated:** 2026-01-05  
**Status:** Production Ready  
**Test Coverage:** 19 scenarios, 30+ assertions
