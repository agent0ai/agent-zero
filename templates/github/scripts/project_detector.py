#!/usr/bin/env python3
"""Project GitHub Setup Detector

Quick utility to check if a project needs GitHub setup.
Designed for agent integration - returns structured output.
"""

import os
import sys
import json
from pathlib import Path


def detect_project_status(project_path: str = ".") -> dict:
    """Analyze a project directory for GitHub setup status."""
    path = Path(project_path).resolve()
    
    if not path.exists():
        return {
            "error": f"Path does not exist: {path}",
            "needs_setup": False
        }
    
    # Check for key files
    checks = {
        ".git": path / ".git",
        ".gitignore": path / ".gitignore",
        ".pre-commit-config.yaml": path / ".pre-commit-config.yaml",
        ".github/workflows": path / ".github" / "workflows",
        ".flake8": path / ".flake8",
        "pyproject.toml": path / "pyproject.toml",
    }
    
    existing = [name for name, p in checks.items() if p.exists()]
    missing = [name for name, p in checks.items() if not p.exists()]
    
    has_git = ".git" in existing
    has_gitignore = ".gitignore" in existing
    has_precommit = ".pre-commit-config.yaml" in existing
    
    # Determine if setup is needed
    needs_setup = not has_gitignore or not has_precommit
    
    # Recommend tier based on project characteristics
    is_a0_project = ".a0proj" in os.listdir(path) if path.exists() else False
    has_tests = (path / "tests").exists() or (path / "test").exists()
    has_src = (path / "src").exists()
    file_count = len(list(path.glob("**/*.py")))
    
    if file_count > 20 or has_tests or has_src:
        recommended_tier = "full"
    elif file_count > 5 or is_a0_project:
        recommended_tier = "standard"
    else:
        recommended_tier = "minimal"
    
    # Generate suggestion
    if not has_git:
        suggestion = f"Project not under Git control. Run: git init && a0-github init --tier {recommended_tier} {path}"
    elif needs_setup:
        suggestion = f"Project needs GitHub setup. Run: a0-github init --tier {recommended_tier} {path}"
    else:
        suggestion = f"Project appears configured. Run: a0-github audit --tier {recommended_tier} {path}"
    
    return {
        "path": str(path),
        "needs_setup": needs_setup,
        "has_git": has_git,
        "missing_files": missing,
        "existing_files": existing,
        "recommended_tier": recommended_tier,
        "suggestion": suggestion,
        "is_a0_project": is_a0_project,
        "python_file_count": file_count
    }


def main():
    """CLI entry point."""
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    result = detect_project_status(path)
    
    # Output as JSON for easy parsing
    print(json.dumps(result, indent=2))
    
    # Also print human-readable summary
    print("\n" + "="*50)
    if result.get("error"):
        print(f"Error: {result['error']}")
    elif result["needs_setup"]:
        print(f"Project needs GitHub setup")
        print(f"   Missing: {', '.join(result['missing_files'])}")
        print(f"   Recommended: {result['recommended_tier']} tier")
        print(f"\nSuggestion: {result['suggestion']}")
    else:
        print(f"Project appears configured")
        print(f"   Has: {', '.join(result['existing_files'])}")
        print(f"\nSuggestion: {result['suggestion']}")


if __name__ == "__main__":
    main()
