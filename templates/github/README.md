# Agent Zero GitHub Templates

> Reusable templates for world-class GitHub repository setup

**Version:** 1.0.0  
**Last Updated:** 2026-01-24

## Overview

This template system provides three tiers of GitHub best practices configurations:

| Tier | Use Case | Includes |
|------|----------|----------|
| **minimal** | Quick scripts, experiments | `.gitignore`, basic pre-commit |
| **standard** | Most projects | + flake8, security scanning, CI workflow |
| **full** | Production projects | + pylint, markdownlint, comprehensive CI/CD |

## Quick Start

### Bootstrap a New Project

```bash
# Standard tier (recommended for most projects)
python /a0/templates/github/scripts/bootstrap.py /path/to/project

# Full tier for production projects
python /a0/templates/github/scripts/bootstrap.py --tier full /path/to/project

# Minimal tier for quick experiments
python /a0/templates/github/scripts/bootstrap.py --tier minimal /path/to/project

# Dry run to see what would be created
python /a0/templates/github/scripts/bootstrap.py --dry-run /path/to/project
```

### Audit an Existing Project

```bash
# Check compliance against standard tier
python /a0/templates/github/scripts/audit.py /path/to/project

# Check against full tier
python /a0/templates/github/scripts/audit.py --tier full /path/to/project

# Auto-fix missing files
python /a0/templates/github/scripts/audit.py --fix /path/to/project

# JSON output for automation
python /a0/templates/github/scripts/audit.py --json /path/to/project
```

## Directory Structure

```
/a0/templates/github/
├── VERSION                    # Template version
├── README.md                  # This file
├── scripts/
│   ├── bootstrap.py          # Initialize new projects
│   └── audit.py              # Audit existing projects
└── tiers/
    ├── minimal/
    │   ├── .gitignore
    │   ├── .pre-commit-config.yaml
    │   └── .github/workflows/README.md
    ├── standard/
    │   ├── .gitignore
    │   ├── .pre-commit-config.yaml
    │   ├── .flake8
    │   └── .github/workflows/ci.yml
    └── full/
        ├── .gitignore
        ├── .pre-commit-config.yaml
        ├── .flake8
        ├── .pylintrc
        ├── .markdownlint.json
        └── .github/workflows/ci.yml
```

## Tier Details

### Minimal Tier

**Best for:** Quick scripts, experiments, learning projects

**Includes:**
- `.gitignore` - A0-specific exclusions, Python basics
- `.pre-commit-config.yaml` - 5 hooks:
  - trailing-whitespace
  - end-of-file-fixer
  - check-yaml
  - check-json
  - check-added-large-files

**No CI/CD workflows** - relies on local pre-commit only.

---

### Standard Tier (Recommended)

**Best for:** Most Agent Zero projects, team collaboration

**Includes everything in Minimal, plus:**
- `.flake8` - Python style configuration
- `.pre-commit-config.yaml` - 8 hooks:
  - All minimal hooks
  - detect-private-key
  - flake8
  - bandit (security)
- `.github/workflows/ci.yml` - GitHub Actions:
  - Python linting (flake8)
  - Security scanning (bandit)

---

### Full Tier

**Best for:** Production projects, open source, enterprise

**Includes everything in Standard, plus:**
- `.pylintrc` - Comprehensive Python linting
- `.markdownlint.json` - Documentation quality
- `.pre-commit-config.yaml` - 11 hooks:
  - All standard hooks
  - pylint
  - markdownlint
  - pytest (pre-commit tests)
- `.github/workflows/ci.yml` - Comprehensive CI:
  - Python linting (flake8 + pylint)
  - Markdown linting
  - Security scanning (bandit)
  - Secret detection (TruffleHog)
  - Test coverage reporting

## Agent Integration

Agents can use these templates programmatically:

```python
# In agent code or subordinate tasks
import subprocess

# Bootstrap a new project
subprocess.run([
    "python", "/a0/templates/github/scripts/bootstrap.py",
    "--tier", "standard",
    "/path/to/new/project"
])

# Audit an existing project
result = subprocess.run([
    "python", "/a0/templates/github/scripts/audit.py",
    "--json",
    "/path/to/project"
], capture_output=True, text=True)

import json
audit_results = json.loads(result.stdout)
```

## Customization

### After Bootstrap

1. **Review generated files** - Adjust paths in `.gitignore` for your project
2. **Customize linting rules** - Edit `.flake8`, `.pylintrc` as needed
3. **Adjust CI workflows** - Modify test paths, coverage thresholds
4. **Add project-specific hooks** - Extend `.pre-commit-config.yaml`

### Template Modifications

To modify templates for all future projects:

1. Edit files in `/a0/templates/github/tiers/<tier>/`
2. Update VERSION file
3. Test with `bootstrap.py --dry-run`

## Troubleshooting

### Pre-commit not found

```bash
pip install pre-commit
```

### Hooks not running

```bash
cd /path/to/project
pre-commit install
```

### CI workflow failing

Check that your project has:
- `tests/` directory for pytest
- `src/` directory for coverage (or adjust paths in workflow)
- `requirements.txt` for dependencies

## Version History

- **1.0.0** (2026-01-24): Initial release
  - Three-tier template system
  - Bootstrap and audit scripts
  - Extracted from quorum_pitch_deck project
