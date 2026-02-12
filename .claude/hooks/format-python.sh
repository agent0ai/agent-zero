#!/usr/bin/env bash
# PostToolUse hook: Auto-format Python files after Edit/Write
# Reads JSON from stdin, extracts file_path, runs ruff format if .py

set -euo pipefail

# Read JSON payload from stdin
INPUT=$(cat)

# Extract file_path from tool_input using python3 (guaranteed available)
FILE_PATH=$(python3 -c "
import json, sys
data = json.loads(sys.argv[1])
print(data.get('tool_input', {}).get('file_path', ''))
" "$INPUT" 2>/dev/null) || exit 0

# Only format Python files
if [[ "$FILE_PATH" == *.py ]]; then
    uv run ruff format --force-exclude "$FILE_PATH" 2>/dev/null || true
fi

exit 0
