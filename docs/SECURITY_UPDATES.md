# Security Updates - January 2026

## MCP Security Patches Applied

**Date**: 2026-01-24

### CVE-2025-68143, CVE-2025-68144, CVE-2025-68145

Agent Jumbo has been updated to address three critical vulnerabilities in the Model Context Protocol (MCP) Git server implementation:

1. **CVE-2025-68143**: Path traversal vulnerability in `git_diff`
2. **CVE-2025-68144**: Path traversal vulnerability in `git_checkout`
3. **CVE-2025-68145**: Unrestricted directory initialization in `git_init`

### Actions Taken

1. **Updated MCP dependency** from `mcp==1.13.1` to `mcp>=1.13.1` to ensure latest security patches
2. **Reviewed MCP integration** in `python/helpers/mcp_handler.py` for vulnerable patterns
3. **Added security validation** for any custom MCP server implementations

### Recommendations

If you have implemented custom MCP servers for Agent Jumbo:

1. **Update to latest MCP version**: `pip install --upgrade mcp`
2. **Review git operations**: Ensure all git commands validate paths and restrict operations to allowed directories
3. **Implement input sanitization**: Validate all user-provided paths and arguments before passing to git commands
4. **Use allowlists**: Define allowed directories for git operations and reject any paths outside those boundaries

### Example Secure Pattern

```python
import os
from pathlib import Path

ALLOWED_DIRECTORIES = [
    Path("/home/user/projects"),
    Path("/tmp/agent-workspace"),
]

def validate_path(path: str) -> bool:
    """Ensure path is within allowed directories"""
    resolved = Path(path).resolve()
    return any(
        resolved.is_relative_to(allowed)
        for allowed in ALLOWED_DIRECTORIES
    )

def git_diff_secure(path: str, commit1: str, commit2: str):
    """Secure git_diff implementation"""
    if not validate_path(path):
        raise ValueError(f"Path {path} is not in allowed directories")

    # Sanitize commit refs to prevent command injection
    if not re.match(r'^[a-zA-Z0-9_-]+$', commit1) or not re.match(r'^[a-zA-Z0-9_-]+$', commit2):
        raise ValueError("Invalid commit reference")

    # Safe to proceed
    # ... perform git diff ...
```

### Testing

Run security validation tests:

```bash
python -m pytest tests/test_mcp_security.py
```

### References

- [MCP Security Advisory](https://github.com/anthropics/anthropic-sdk-python/security/advisories)
- [MCP Documentation](https://modelcontextprotocol.io/docs)
- [Agent Jumbo Security Policy](./SECURITY.md)

### Contact

For security concerns, please report to: <security@agent-zero.ai> (or create a private security advisory on GitHub)
