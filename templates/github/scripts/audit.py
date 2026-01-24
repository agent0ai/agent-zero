#!/usr/bin/env python3
"""
Agent Zero GitHub Audit Script
==============================
Audits an existing project against GitHub best practices templates.

Usage:
    python audit.py [OPTIONS] [TARGET_DIR]

Options:
    --tier TIER     Compare against tier: minimal, standard, full (default: standard)
    --fix           Automatically fix missing files (copies from template)
    --json          Output results as JSON
    -h, --help      Show this help message
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

TEMPLATE_BASE = Path(__file__).parent.parent / "tiers"
TIERS = ["minimal", "standard", "full"]

CHECKS = {
    "minimal": {
        "required": [".gitignore"],
        "recommended": [".pre-commit-config.yaml"],
        "optional": []
    },
    "standard": {
        "required": [".gitignore", ".pre-commit-config.yaml"],
        "recommended": [".flake8", ".github/workflows/ci.yml"],
        "optional": []
    },
    "full": {
        "required": [".gitignore", ".pre-commit-config.yaml", ".flake8", ".pylintrc"],
        "recommended": [".markdownlint.json", ".github/workflows/ci.yml"],
        "optional": ["pyproject.toml", "Makefile"]
    }
}

def log(msg, level="info"):
    colors = {"info": "\033[94m", "success": "\033[92m", "warning": "\033[93m", "error": "\033[91m", "reset": "\033[0m"}
    prefix = {"info": "i", "success": "✓", "warning": "!", "error": "✗"}
    print(f"{colors.get(level, '')}{prefix.get(level, '')} {msg}{colors['reset']}")

def audit_project(target, tier):
    results = {
        "tier": tier,
        "target": str(target),
        "required": {"present": [], "missing": []},
        "recommended": {"present": [], "missing": []},
        "optional": {"present": [], "missing": []},
        "score": 0,
        "max_score": 0
    }
    
    checks = CHECKS.get(tier, CHECKS["standard"])
    
    for f in checks["required"]:
        results["max_score"] += 3
        if (target / f).exists():
            results["required"]["present"].append(f)
            results["score"] += 3
        else:
            results["required"]["missing"].append(f)
    
    for f in checks["recommended"]:
        results["max_score"] += 2
        if (target / f).exists():
            results["recommended"]["present"].append(f)
            results["score"] += 2
        else:
            results["recommended"]["missing"].append(f)
    
    for f in checks["optional"]:
        results["max_score"] += 1
        if (target / f).exists():
            results["optional"]["present"].append(f)
            results["score"] += 1
        else:
            results["optional"]["missing"].append(f)
    
    results["git_initialized"] = (target / ".git").exists()
    results["hooks_installed"] = (target / ".git" / "hooks" / "pre-commit").exists()
    
    return results

def fix_missing(target, tier, results):
    tier_path = TEMPLATE_BASE / tier
    fixed = []
    all_missing = results["required"]["missing"] + results["recommended"]["missing"]
    
    for f in all_missing:
        src = tier_path / f
        dest = target / f
        if src.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            fixed.append(f)
            log(f"Fixed: {f}", "success")
        else:
            log(f"Template not found for: {f}", "warning")
    return fixed

def print_report(results):
    print(f"\n📊 GitHub Best Practices Audit Report")
    print(f"   Target: {results['target']}")
    print(f"   Tier: {results['tier']}")
    print(f"   Score: {results['score']}/{results['max_score']}")
    print()
    
    print("Required Files:")
    for f in results["required"]["present"]:
        log(f, "success")
    for f in results["required"]["missing"]:
        log(f"MISSING: {f}", "error")
    
    print("\nRecommended Files:")
    for f in results["recommended"]["present"]:
        log(f, "success")
    for f in results["recommended"]["missing"]:
        log(f"MISSING: {f}", "warning")
    
    if results["optional"]["present"] or results["optional"]["missing"]:
        print("\nOptional Files:")
        for f in results["optional"]["present"]:
            log(f, "success")
        for f in results["optional"]["missing"]:
            log(f"Not present: {f}", "info")
    
    print("\nGit Status:")
    if results["git_initialized"]:
        log("Repository initialized", "success")
    else:
        log("Repository NOT initialized", "error")
    
    if results["hooks_installed"]:
        log("Pre-commit hooks installed", "success")
    else:
        log("Pre-commit hooks NOT installed", "warning")
    
    pct = (results["score"] / results["max_score"] * 100) if results["max_score"] > 0 else 0
    grade = "A" if pct >= 90 else "B" if pct >= 80 else "C" if pct >= 70 else "D" if pct >= 60 else "F"
    print(f"\n📈 Grade: {grade} ({pct:.0f}%)")

def main():
    parser = argparse.ArgumentParser(description="Audit a project against Agent Zero GitHub templates")
    parser.add_argument("target", nargs="?", default=".", help="Target directory")
    parser.add_argument("--tier", choices=TIERS, default="standard", help="Template tier")
    parser.add_argument("--fix", action="store_true", help="Fix missing files")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    target = Path(args.target).resolve()
    
    if not target.exists():
        log(f"Target directory does not exist: {target}", "error")
        sys.exit(1)
    
    results = audit_project(target, args.tier)
    
    if args.fix:
        fixed = fix_missing(target, args.tier, results)
        results = audit_project(target, args.tier)
        results["fixed"] = fixed
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_report(results)

if __name__ == "__main__":
    main()
