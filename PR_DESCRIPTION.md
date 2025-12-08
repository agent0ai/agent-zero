# VS Code Extension & Parallel Agent Delegation

## Summary

Adds VS Code IDE integration and parallel agent delegation system to improve development workflow and task execution performance.

## Features

### VS Code Extension
- Language Model Provider for VS Code Chat interface
- Real-time streaming responses with progress visibility
- Automatic workspace context mapping (local ↔ container paths)
- VSIX packaging script generator in Developer settings
- Session management per VS Code chat window

### Parallel Agent Delegation
- New `delegate_parallel` tool for simultaneous task execution
- Task dependency management and resolution
- Task queue system with concurrent execution limits
- Improved performance for complex multi-task workflows
- Isolated contexts per parallel agent

## Changes

**New Files:**
- `ide-extensions/vscode/agent-zero-provider/` - Complete VS Code extension
- `python/tools/delegate_parallel.py` - Parallel delegation tool
- `python/helpers/task_queue.py` - Task queue manager
- `python/helpers/requirements_analyzer.py` - Requirements analyzer
- `python/api/vsix_script_generate.py` - VSIX script generator
- `tests/test_parallel_delegation.py` - Test suite
- Documentation files for both features

**Modified:**
- `python/helpers/settings.py` - Added VSIX generator button
- `webui/js/settings.js` - VSIX script handler
- Documentation updates in README and connectivity guide

## Documentation

- VS Code extension: `docs/connectivity.md#vs-code-extension`
- Parallel delegation: `docs/parallel-agent-delegation.md`
- Implementation: `docs/parallel-delegation-implementation.md`
- Testing: `docs/testing-parallel-delegation.md`

## Testing

- Parallel delegation includes comprehensive test suite
- VS Code extension tested with VS Code 1.106.0+
- All features documented with examples

